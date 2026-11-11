import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from pyproj import Geod, Transformer
from rasterio.windows import Window
from shapely.geometry import Point, Polygon

from scripts.audit_phase7 import request
from src.compute.atlas_admission import active_manifests

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = active_manifests(ROOT)


@pytest.mark.parametrize('case', MANIFESTS)
@pytest.mark.parametrize('kind', ('edge', 'point', 'polygon'))
def test_native_profile_matches_independent_pixel_read(case, kind):
    center = 0 if kind == 'edge' else 1000
    point = {'kind': 'point', 'row': center, 'col': center}
    vertices = [[797.2, 797.1], [806.1, 798.2], [801.1, 812.1]]
    selection = point if kind != 'polygon' else {'kind': 'polygon', 'vertices': vertices}
    status, body = request('/api/cases/'+case+'/atlas-native', {'selection': selection})
    assert status == 200, body
    data = json.loads(body)
    p, support = data['profile'], data['support']
    assert data['atlasBinding']['selection'] == selection
    manifest = MANIFESTS[case]
    m = json.loads(manifest.read_text())
    if kind != 'polygon':
        top = left = max(0, center - 5)
        height = width = center + 6 - top
        expected = np.ones((height, width), dtype=bool)
    else:
        top, left, height, width = 797, 797, 16, 10
        polygon = Polygon(vertices)
        expected = np.array([[polygon.contains(Point(left+c+.5, top+r+.5))
                              for c in range(width)] for r in range(height)])
    assert support['window'] == dict(row=top, col=left, height=height, width=width)
    raw = []
    for visit in m['observations']:
        row = []
        for k in ('hh', 'hv'):
            url = visit['rasters'][k]
            path = ROOT/'web/public'/url.lstrip('/') if url.startswith('/cases/') else manifest.parent/url
            with rasterio.open(path) as ds:
                values = ds.read(1, window=Window(left, top, width, height), masked=True)
                row.append(values.filled(np.nan))
                assert list(ds.transform)[:2] == support['windowAffine'][:2]
                assert list(ds.xy(top, left, offset='ul')) == support['windowAffine'][2::3]
        raw.append(row)
    raw = np.asarray(raw, dtype='float64')
    paired = np.isfinite(raw).all(axis=1) & expected
    common = paired.all(axis=0)
    for k, mask in [('commonMaskRuns', common), ('footprintMaskRuns', expected)]:
        decoded = np.zeros(height*width, dtype=bool)
        for start, length in support[k]:
            decoded[start:start+length] = True
        np.testing.assert_array_equal(decoded.reshape(height, width), mask)
    assert support['pairedValidCounts'] == paired.sum(axis=(1, 2)).tolist()
    assert p['common_valid_pixels'] == common.sum()
    assert p['common_valid_area_km2'] == pytest.approx(common.sum()*m['grid']['pixel_area_km2'])
    if common.any():
        means = raw[:, :, common].mean(axis=2)
        ref = next(i for i, r in enumerate(m['observations']) if r['timestamp'] == m['reference_timestamp'])
        for i, row in enumerate(p['observations']):
            for j, k in enumerate(('hh', 'hv')):
                assert row[k+'_mean_db'] == pytest.approx(means[i, j], abs=1e-10)
                assert row[k+'_reference_delta_db'] == pytest.approx(means[i, j]-means[ref, j], abs=1e-10)
    else:
        assert all(row['hh_mean_db'] is None and row['hv_reference_delta_db'] is None for row in p['observations'])
    if common.sum() / expected.sum() >= .8:
        fits = data['explanations']
        assert [row['observation_id'] for row in fits] == [row['observation_id'] for row in m['observations']]
        for i, fit in enumerate(fits):
            assert fit['reference_timestamp'] == m['reference_timestamp']
            assert fit['common_valid_pixels'] == common.sum()
            assert len(fit['hypotheses']) == 6
            assert fit['facts']['hh_last_db'] == pytest.approx(means[i, 0])
            assert fit['facts']['mean_abs_hh_change_db'] == pytest.approx(
                np.abs(raw[i, 0][common] - raw[ref, 0][common]).mean())
            assert fit['facts']['rain_72h_mm'] is None
        assert fits[ref]['facts']['control_offset_abs_db'] == 0
        if case.startswith('nepal_'):
            assert fits[-1]['facts']['control_offset_abs_db'] is None
    else:
        assert 'explanations' not in data
    if kind == 'polygon':
        projected = Polygon(support['boundaryProjected'])
        inverse = Transformer.from_crs(support['crs'], 4326, always_xy=True)
        geod_area = Geod(ellps='WGS84').polygon_area_perimeter(*inverse.transform(*projected.exterior.xy))[0]
        assert p['boundary_area']['projected_km2'] == pytest.approx(projected.area/1e6, abs=1e-10)
        assert p['boundary_area']['ellipsoidal_km2'] == pytest.approx(abs(geod_area)/1e6, abs=1e-9)


@pytest.mark.parametrize('selection', [
    {'kind': 'polygon', 'vertices': [[10, 10], [20, 20], [10, 20], [20, 10]]},
    {'kind': 'polygon', 'vertices': [[0, 0], [900, 0], [900, 900], [0, 900]]},
    {'kind': 'polygon', 'vertices': [[0, 0], [0.1, 0], [0.1, 0.1]]},
    {'kind': 'polygon', 'vertices': [[-1, 0], [15, 0], [15, 5]]},
    {'kind': 'polygon', 'vertices': [[4, 5]]*201},
    {'kind': 'point', 'row': True, 'col': 3},
    {'kind': 'point', 'row': 2400, 'col': 3},
])
def test_invalid_footprints_never_return_other_measurements(selection):
    status, body = request('/api/cases/nepal_surface/atlas-native', {'selection': selection})
    assert status == 422
    assert set(json.loads(body)) == {'error'}


def test_terrain_control_points_read_from_each_accepted_dem():
    atlas = json.loads((ROOT/'web/atlas-record.json').read_text())
    for case, p in MANIFESTS.items():
        c = atlas[case]
        height, width = c['grid']['shape']
        terrain = c['terrain']
        n = terrain['size']
        base = p.parent.parent/'context-v2'
        ctx = json.loads((base/'manifest.json').read_text())
        assert ctx['case_id'] == case
        a, b, x0, d, e, y0 = c['grid']['affine']
        assert terrain['width_m'] == (width-1)*abs(a)
        assert terrain['height_m'] == (height-1)*abs(e)
        with rasterio.open(base/ctx['layers']['dem']['raster']) as dem:
            for r, col in [(0, 0), (20, 20), (40, 40), (0, 40)]:
                x = .5+col*(width-1)/(n-1)
                y = .5+r*(height-1)/(n-1)
                rr, cc = dem.index(x0+a*x+b*y, y0+d*x+e*y)
                z = dem.read(1, window=Window(cc, rr, 1, 1), masked=True)
                expected = float(z[0, 0]) if z.size and not np.ma.is_masked(z[0, 0]) and np.isfinite(z[0, 0]) else None
                assert terrain['elevation_m'][r*n+col] == (round(expected, 2) if expected is not None else None)
