"""Compare adjacent measured pairs on their shared valid native 20 m samples."""
import numpy as np
import rasterio

def compare_pairs(pairs, public):
    if len(pairs)!=2:
        return None
    first,second=pairs
    ids=['trackNumber','frameNumber','orbitPassDirection','lookDirection']
    if first['timestamps'][1]!=second['timestamps'][0] or any(first['identification'][k]!=second['identification'][k] for k in ids):
        raise ValueError('Coherence pairs are not consecutive and geometry-compatible')
    arrays=[]
    geometry=None
    for pair in pairs:
        for key in ('coherence20','coherence_valid20'):
            path=(public/pair['rasters'][key].lstrip('/')).resolve()
            if not path.is_relative_to(public.resolve()): raise ValueError('Unexpected raster path')
            with rasterio.open(path) as ds:
                current=(ds.crs,ds.transform,ds.shape)
                if geometry and geometry!=current: raise ValueError('Coherence comparison requires identical grids')
                geometry=current
                arrays.append(ds.read(1))
    a,ma,b,mb=arrays
    common=(ma==1)&(mb==1)&np.isfinite(a)&np.isfinite(b)&(a>=0)&(a<=1)&(b>=0)&(b<=1)
    delta=b[common].astype('float64')-a[common]
    return {'pairs':[p['identification']['granuleId'] for p in pairs],
            'intervals':[p['timestamps'] for p in pairs], 'common_valid_pixels':int(delta.size),
            'total_pixels':int(common.size),'median_later_minus_earlier':float(np.median(delta)) if delta.size else None,
            'scope':'Whole crop on the shared native 20 m valid samples; signed later minus earlier coherence. Not a damage proxy, footprint result or displacement.'}


def comparison_policy(earlier, later):
    """Eligibility for descriptive differencing, never for event attribution."""
    compatible_keys = ('track', 'frame', 'passDirection', 'lookDirection', 'channel', 'frequency',
                       'postingM', 'productVersion', 'release')
    return (earlier['secondId'] == later['firstId']
            and earlier['sourceSlc'][1] == later['sourceSlc'][0]
            and earlier['intervalSeconds'] == later['intervalSeconds'] == 12 * 86400
            and earlier['grid'] == later['grid']
            and all(earlier[k] == later[k] for k in compatible_keys))


def coherence_delta(earlier, later):
    """Signed later minus earlier; invalid cells remain NaN."""
    if earlier.shape != later.shape:
        raise ValueError('Coherence inputs must use the same grid')
    valid = (np.isfinite(earlier) & np.isfinite(later)
             & (earlier >= 0) & (earlier <= 1) & (later >= 0) & (later <= 1))
    return np.subtract(later, earlier, out=np.full(earlier.shape, np.nan, 'float32'), where=valid)


def coherence_summary(values, footprint):
    measured = values[footprint & np.isfinite(values)]
    return {'assessed': int(measured.size), 'footprintPixels': int(footprint.sum()),
            'mean': float(measured.mean(dtype='float64')) if measured.size else None,
            'median': float(np.median(measured)) if measured.size else None}


def coherence_footprint(mask, from_grid, to_grid):
    """Assign footprint membership at GUNW centers; never resample coherence."""
    from affine import Affine
    from rasterio.warp import reproject, Resampling

    target = np.zeros(to_grid['shape'], 'uint8')
    reproject(mask.astype('uint8'), target,
              src_transform=Affine(*from_grid['affine']), src_crs=from_grid['crs'],
              dst_transform=Affine(*to_grid['affine']), dst_crs=to_grid['crs'],
              resampling=Resampling.nearest)
    return target == 1


def coherence_plane(public, folder, pair, window=None):
    from src.compute.atlas_spatial import read_atlas_plane

    grid = pair['grids']['20']
    arrays = [read_atlas_plane(public, folder, pair['rasters'][key], grid, window)
              for key in ('coherence20', 'coherence_valid20')]
    values, mask = arrays[0].filled(np.nan), arrays[1].filled(0)
    if (not np.isin(mask, [0, 1]).all() or
            not np.array_equal(mask == 1, np.isfinite(values) & (values >= 0) & (values <= 1)) or
            window is None and int(mask.sum()) != pair['statistics']['20']['valid_pixels']):
        raise ValueError('Canonical coherence mask or values differ from accepted support')
    return values



def native_coherence(public, folder, pairs, catalog, mask, footprint_grid):
    """Read just the native GUNW window covered by a local user footprint."""
    from rasterio.windows import Window

    measured, deltas, samples = {}, {}, {}
    source = {pair['pair_id']: pair for pair in pairs}
    for pair in catalog['pairs']:
        pair_id = pair['id']
        record = source[pair_id]
        if pair['sourceId'] != record['identification']['granuleId']:
            raise RuntimeError('Stale coherence identity for native footprint')
        grid = record['grids']['20']
        support = coherence_footprint(mask, footprint_grid, grid)
        rows, cols = np.where(support)
        if rows.size:
            top, left, bottom, right = rows.min(), cols.min(), rows.max()+1, cols.max()+1
            window = Window(left, top, right-left, bottom-top)
            support = support[top:bottom, left:right]
            values = coherence_plane(public, folder, record, window)
        else:
            values, support = np.empty((0,0)), np.empty((0,0), bool)
        samples[pair_id] = (pair, values, support)
        measured[pair_id] = coherence_summary(values, support)
    for comparison in catalog['coherenceComparisons']:
        earlier, a, support_a = samples[comparison['earlierId']]
        later, b, support_b = samples[comparison['laterId']]
        if not comparison_policy(earlier, later) or not np.array_equal(support_a, support_b):
            raise RuntimeError('Incompatible pair support for native footprint')
        deltas[later['id']] = coherence_summary(coherence_delta(a,b),support_b)
    return {'pairs': measured, 'deltas': deltas}
