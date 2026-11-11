import io
from types import SimpleNamespace

from affine import Affine
import numpy as np
import pytest
from src.api import app
from src.compute.atlas_measurements import footprint_geometry
from src.compute.atlas_measurements import crosspol_fraction
from src.compute.coherence_change import compare_pairs


def test_boundary_geometry_is_distinct_from_pixel_center_support():
    t=Affine(10,0,156520,0,-10,2722450)
    triangle=footprint_geometry([(0,0),(50,0),(0,50)],t,32646)
    assert triangle['projected_km2']==pytest.approx(.125)
    assert .124 < triangle['ellipsoidal_km2'] < .125
    clockwise=footprint_geometry([(0,50),(50,0),(0,0)],t,32646)
    assert clockwise['ellipsoidal_km2']==pytest.approx(triangle['ellipsoidal_km2'])
    with pytest.raises(ValueError):footprint_geometry([(0,0),(1,1),(1,0),(0,1)],t,32646)


def test_crosspol_fraction_masks_invalid_and_keeps_cross_dominant_power():
    fraction=crosspol_fraction([0,0,-10,np.nan],[0,-10,0,0])
    np.testing.assert_allclose(fraction[:3],[.5,1/11,10/11],rtol=1e-6)
    assert np.isnan(fraction[-1])


def test_pair_comparison_rejects_nonconsecutive_without_reading_rasters(tmp_path):
    p={'timestamps':['a','b']}
    with pytest.raises(ValueError,match='consecutive'):compare_pairs([p,p],tmp_path)


@pytest.mark.parametrize('method,value,code,body,content',[
    ('GET','bytes=2-4',206,b'234','bytes 2-4/10'),('GET','bytes=-2',206,b'89','bytes 8-9/10'),
    ('HEAD','bytes=5-',206,b'','bytes 5-9/10'),('GET','bytes=11-',416,b'','bytes */10')])
def test_native_raster_range_response(tmp_path,monkeypatch,method,value,code,body,content):
    path=tmp_path/'cases/test.tif';path.parent.mkdir();path.write_bytes(b'0123456789')
    monkeypatch.setattr(app,'PUBLIC',tmp_path)
    class Connection:
        def __init__(self):
            self.output=bytearray()
        def makefile(self,*args,**kwargs):
            return io.BytesIO(f'{method} /cases/test.tif HTTP/1.0\r\nHost: localhost\r\nRange: {value}\r\n\r\n'.encode())
        def sendall(self,data):self.output.extend(data)
    conn=Connection();app.Handler(conn,('127.0.0.1',1234),SimpleNamespace(server_name='localhost',server_port=8000))
    header,result=bytes(conn.output).split(b'\r\n\r\n',1)
    assert header.startswith(f'HTTP/1.0 {code}'.encode())
    assert f'Content-Range: {content}'.encode() in header and result==body


def test_kathmandu_atlas_comparisons_from_fixed_raster_support():
    import json
    from pathlib import Path

    import rasterio
    from rasterio.windows import Window

    public = Path(__file__).resolve().parents[1] / 'web/public'
    record = public / 'cases/nepal_surface/expanded-v1'
    manifest = json.loads((record/'manifest.json').read_text())
    with rasterio.open(record/'tracked_footprint.tif') as mask:
        yy, xx = np.nonzero(mask.read(1))
    window = Window(int(xx.min()), int(yy.min()), int(xx.max()-xx.min()+1), int(yy.max()-yy.min()+1))
    footprint = np.zeros((int(window.height), int(window.width)), dtype=bool)
    footprint[yy-int(window.row_off), xx-int(window.col_off)] = True
    common = footprint.copy()
    hh, hv = {}, {}
    for visit in manifest['observations']:
        for channel in ('hh', 'hv'):
            with rasterio.open(public/visit['rasters'][channel].lstrip('/')) as dataset:
                pixels = dataset.read(1, window=window, masked=True).filled(np.nan)
            common &= np.isfinite(pixels)
            (hh if channel=='hh' else hv)[visit['timestamp']] = pixels
    assert int(common.sum()) == 199
    selected = '2026-09-12T23:39:18Z'
    means = {date: float(pixels[common].mean(dtype='float64')) for date, pixels in hh.items()}
    assert means[selected]-means['2026-08-31T23:39:18Z'] == pytest.approx(.44969205760476605)
    assert means[selected]-means[manifest['reference_timestamp']] == pytest.approx(-7.076616920341256)

    catalog = json.loads((public.parent/'atlas-contract-records.json').read_text())
    summary = catalog['nepal_surface']['footprints'][0]['dualpol']['acq_20260912T233918']
    h = 10**(hh[selected][common].astype('float64')/10)
    v = 10**(hv[selected][common].astype('float64')/10)
    assert summary['validPixels'] == 199
    assert summary['powerShare'] == pytest.approx(np.mean(v/(h+v)),abs=2e-8)
    assert summary['cprDb'] == pytest.approx(np.mean(10*np.log10(v/h)),abs=2e-8)
