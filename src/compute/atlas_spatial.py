"""Bounded native raster inspection for the atlas."""
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.crs import CRS
from rasterio.features import rasterize
from rasterio.windows import Window
from shapely.geometry import Polygon

from src.compute.atlas_measurements import footprint_geometry, dualpol_summary
from src.compute.atlas_admission import admitted_pairs
from src.compute.atlas_explanations import (
    MIN_NATIVE_RULE_SUPPORT, evaluate_atlas_visit, explanation_context, footprint_median_slope,
)
from src.compute.expanded_record import profile
from src.compute.atlas_review import radar_review_visit, review_location
from src.compute.atlas_landcover import atlas_landcover_path, landcover_summary

MAX_WINDOW_PIXELS = 250_000


def read_atlas_plane(public, folder, url, grid, window=None):
    public = Path(public).resolve()
    path = (public/url.removeprefix('/cases/') if url.startswith('/cases/') else folder/url).resolve()
    if not path.is_relative_to(public):
        raise RuntimeError('Raster path outside the accepted case records')
    with rasterio.open(path) as raster:
        if raster.crs != CRS.from_string(grid['crs']) or raster.transform != Affine(*grid['affine']) or list(raster.shape) != grid['shape']:
            raise RuntimeError('Native raster grid differs from the accepted record')
        return raster.read(1, window=window, masked=True)


def selection_window(selection, shape):
    """Coordinates are zero-based. Polygon vertices use pixel corners [col,row]."""
    if not isinstance(selection, dict):
        raise ValueError('Specify a point or a polygon.')
    height, width = shape
    kind = selection.get('kind')
    if kind == 'point':
        row, col = selection.get('row'), selection.get('col')
        if type(row) is not int or type(col) is not int or not (0 <= row < height and 0 <= col < width):
            raise ValueError('Enter a zero-based row and column inside this grid.')
        left, top = max(0, col - 5), max(0, row - 5)
        right, bottom = min(width, col + 6), min(height, row + 6)
        return Window(left, top, right-left, bottom-top), np.ones((bottom-top, right-left), bool), None
    vertices = selection.get('vertices')
    if kind != 'polygon' or not isinstance(vertices, list) or not 3 <= len(vertices) <= 200:
        raise ValueError('A polygon needs 3–200 [column,row] vertices.')
    if not all(isinstance(v, list) and len(v) == 2 and all(
        type(coord) in (int, float) and 0 <= coord <= limit for coord, limit in zip(v, (width, height))
    ) for v in vertices):
        raise ValueError('Every polygon vertex must be inside the native grid bounds.')
    polygon = Polygon(vertices)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('Draw a polygon with a nonzero area and no crossing edges.')
    left, top = np.floor(polygon.bounds[:2]).astype(int).tolist()
    right, bottom = np.ceil(polygon.bounds[2:]).astype(int).tolist()
    size = bottom-top, right-left
    if size[0] * size[1] > MAX_WINDOW_PIXELS:
        raise ValueError('Select a smaller polygon. Its bounding window can cover up to 250,000 native cells.')
    mask = rasterize([polygon], out_shape=size, transform=Affine.translation(left, top),
                     all_touched=False, dtype='uint8').astype(bool)
    if not mask.any():
        raise ValueError('The polygon must enclose a native pixel center.')
    return Window(left, top, size[1], size[0]), mask, vertices


def mask_runs(mask):
    """Row-major [start,length] runs in the returned bounding window."""
    edges = np.flatnonzero(np.diff(np.r_[False, mask.ravel(), False]))
    return [[int(a), int(b-a)] for a, b in edges.reshape(-1, 2)]


def native_profile(root, case, manifest, selection):
    manifest = Path(manifest)
    public = (Path(root)/'web/public/cases').resolve()
    m = json.loads(manifest.read_text())
    grid, visits = m['grid'], m['observations']
    window, mask, vertices = selection_window(selection, grid['shape'])
    transform = Affine(*grid['affine'])
    crs = CRS.from_string(grid['crs'])
    stacks = {'hh': [], 'hv': []}
    for visit in visits:
        for channel in stacks:
            plane = read_atlas_plane(public, manifest.parent, visit['rasters'][channel], grid, window)
            stacks[channel].append(plane.astype('float32').filled(np.nan))
    stacks = {channel: np.stack(planes) for channel, planes in stacks.items()}
    paired = np.isfinite(stacks['hh']) & np.isfinite(stacks['hv']) & mask
    common = paired.all(axis=0)
    reference = next(i for i, visit in enumerate(visits) if visit['timestamp'] == m['reference_timestamp'])
    label = ('Drawn native polygon' if vertices else
             f"Native neighborhood at row {selection['row']}, column {selection['col']}")
    measured = profile(stacks, mask, visits, reference, label, grid['pixel_area_km2'])
    measured['reference_timestamp'] = m['reference_timestamp']
    measured['support'] = 'Same paired HH/HV-valid native pixels across all observed visits.'
    measured['dualpol'] = {visit['observation_id']:dualpol_summary(hh,hv,common)
                           for visit,hh,hv in zip(visits,stacks['hh'],stacks['hv'])}
    left, top, width, height = (int(getattr(window, k)) for k in ('col_off', 'row_off', 'width', 'height'))
    support = {
        'window': {'row': top, 'col': left, 'height': height, 'width': width},
        'crs': grid['crs'], 'windowAffine': list((transform @ Affine.translation(left, top))[:6]),
        'rule': ('GDAL polygon rasterization with all_touched=False (pixel-center inclusion with GDAL edge ties).'
                 if vertices else '11 × 11 neighborhood centered on the selected cell and clipped at grid edges.'),
        'pairedValidCounts': [int(valid.sum()) for valid in paired],
        'footprintMaskRuns': mask_runs(mask), 'commonMaskRuns': mask_runs(common),
    }
    if vertices:
        measured['boundary_area'] = footprint_geometry(vertices, transform, crs)
        support['boundaryProjected'] = [list(transform @ tuple(v)) for v in vertices]
    else:
        support['centerProjected'] = list(transform @ (selection['col']+.5, selection['row']+.5))
    result = {'profile': measured, 'support': support}
    location = review_location(mask, transform @ Affine.translation(left, top), crs)
    measured['field_location'] = [location['longitude'], location['latitude']]
    measured['historical_land_cover'] = landcover_summary(atlas_landcover_path(root,case), grid, common, window)
    if case in ('jamuna_river', 'tanguar_wetland'):
        location['row'] += top
        location['col'] += left
        x1,y1,x2,y2 = location['boundsPixel']
        location['boundsPixel'] = [x1+left,y1+top,x2+left,y2+top]
        measured['review'] = {'location': location, 'visits': {
            visit['observation_id']: radar_review_visit(hh,hv,common)
            for visit,hh,hv in zip(visits,stacks['hh'],stacks['hv'])}}
    pairs = admitted_pairs(root, manifest, m)
    if pairs:
        from src.compute.atlas_contract import binding
        from src.compute.coherence_change import native_coherence

        catalog = json.loads((Path(root)/'web/atlas-contract-records.json').read_text()).get(case)
        if catalog and catalog['manifestSha256'] == binding(case, manifest)['manifestSha256']:
            local_grid = {'shape': list(mask.shape), 'affine': support['windowAffine'], 'crs': grid['crs']}
            measured['coherence'] = native_coherence(public, manifest.parent, pairs, catalog, mask, local_grid)
    if measured['common_valid_pixels'] / measured['footprint_pixels'] >= MIN_NATIVE_RULE_SUPPORT:
        folder, context_manifest, context = explanation_context(manifest, m)
        terrain_grid = context_manifest['grid']
        slope = read_atlas_plane(public, folder, context_manifest['layers']['slope']['raster'],
                                 terrain_grid).filled(np.nan)
        median_slope = footprint_median_slope(common, grid, terrain_grid, slope, left, top)
        rules = json.loads((Path(root)/'rules/explanations.yaml').read_text())
        reference_hh = stacks['hh'][reference][common]
        result['explanations'] = [
            evaluate_atlas_visit(row, m['reference_timestamp'], hh[common], reference_hh,
                                 median_slope, context, rules)
            for row, hh in zip(measured['observations'], stacks['hh'])
        ]
    return result
