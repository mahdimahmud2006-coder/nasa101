"""Prepare offline-capable scenario grids from the admitted local NASADEM/NISAR records."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from affine import Affine
from rasterio.features import rasterize
from rasterio.warp import Resampling, reproject
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_admission import active_manifests, admitted_pairs, require_admitted
from src.compute.atlas_spatial import read_atlas_plane
from src.compute.coherence_change import coherence_delta, coherence_plane, comparison_policy
from src.compute.environment import flow_metrics, terrain_derivatives
from src.compute.atlas_landcover import atlas_landcover_path, DOI as WORLDCOVER_DOI
from src.compute.validation_context import SOURCE_URL, official_extent

OUTPUT = ROOT/'output/atlas/simulations'
DRAINAGE_M2 = 1_000_000
BUFFER_CELLS = 60
EXAMPLES = {
    'jamuna_river': [[203, 439], [235, 439], [220, 435]],
    'tanguar_wetland': [[183, 277], [183, 297], [189, 284]],
}


def digest(content):
    return sha256(content).hexdigest()


def align(values, source, target, method=Resampling.nearest, out=None):
    if out is None:
        out = np.full(target['shape'], np.nan, 'float32')
    reproject(values, out, src_transform=Affine(*source['affine']), src_crs=source['crs'],
              src_nodata=np.nan, dst_transform=Affine(*target['affine']), dst_crs=target['crs'],
              dst_nodata=np.nan, resampling=method, init_dest_nodata=False)
    return out


def buffered_dem(case, grid, sources):
    b = BUFFER_CELLS
    affine = Affine(*grid['affine']) * Affine.translation(-b, -b)
    buffer = {**grid, 'affine': tuple(affine)[:6], 'shape': [x+2*b for x in grid['shape']]}
    dem = np.full(buffer['shape'], np.nan, 'float32')
    ids = []
    for source in sources:
        if source['case_id'] != case:
            continue
        path = ROOT/source['file']
        if digest(path.read_bytes()) != source['sha256']:
            raise ValueError('NASADEM source checksum changed')
        ids.append({'id': source['query']['tile'], 'sha256': source['sha256']})
        with rasterio.open(path) as ds:
            values = ds.read(1, masked=True).astype('float32').filled(np.nan)
            align(values, {'affine':tuple(ds.transform)[:6], 'crs':ds.crs}, buffer, Resampling.bilinear, dem)
    if not ids or not np.isfinite(dem).any():
        raise ValueError('No buffered NASADEM source')
    return dem, ids


def buffered_hand(case, grid, sources):
    dem, ids = buffered_dem(case, grid, sources)
    b = BUFFER_CELLS
    slope = terrain_derivatives(dem, grid['resolution_m'])['slope']
    products, receipt = flow_metrics(dem, grid['resolution_m'], slope, drainage_threshold_m2=DRAINAGE_M2, include_hand=True)
    subset = np.s_[b:-b, b:-b]
    return products['hand'][subset], products['flow_accumulation'][subset], ids, float(np.isfinite(dem).mean()), receipt['outlet_count']


def write_case(case, path, admitted, identity, sources):
    raw = path.read_bytes()
    if digest(raw) != identity['manifestSha256']:
        raise ValueError('Radar identity differs from the accepted atlas')
    case_manifest = json.loads(raw)
    public = ROOT/'web/public/cases'
    context_path = next(ROOT/f for f in admitted['supportingManifests'] if f.startswith(f'web/public/cases/{case}/') and f.endswith('/context-v2/manifest.json'))
    context_raw = context_path.read_bytes()
    if digest(context_raw) != admitted['supportingManifests'][str(context_path.relative_to(ROOT))]:
        raise ValueError('Terrain context checksum changed')
    context = json.loads(context_raw)
    grid = context['grid']
    slope = read_atlas_plane(public, context_path.parent, context['layers']['slope']['raster'], grid).filled(np.nan)
    # Exclude the last partial terrain row/column when its center lies outside the radar study window.
    radar = case_manifest['grid']
    if (grid['affine'][2], grid['affine'][5], grid['crs']) != (radar['affine'][2], radar['affine'][5], radar['crs']):
        raise ValueError('Scenario and radar grids do not share the expected origin and CRS')
    inside = [(np.arange(n)+.5)*grid['resolution_m'] < n_radar*abs(posting)
              for n,n_radar,posting in zip(grid['shape'],radar['shape'],(radar['affine'][4],radar['affine'][0]))]
    slope = np.where(inside[0][:,None]&inside[1][None,:],slope,np.nan)
    manifest = {'schema':1,'case':case,'caseSha256':digest(raw),'terrainSha256':digest(context_raw),'grid':grid}
    assets = {}

    def asset(key, values, dtype='u1', **metadata):
        content = values.astype(dtype, copy=False).tobytes()
        name = f'{case}-{key}-{digest(content)[:16]}.bin'
        assets[name] = content
        return {'file':name,'bytes':len(content),'sha256':digest(content),**metadata}

    if case in ('jamuna_river', 'tanguar_wetland'):
        hand, flow, tiles, coverage, outlets = buffered_hand(case, grid, sources)
        support = np.isfinite(hand)&np.isfinite(slope)
        low = support&(slope<=8)
        stage = np.full(slope.shape,255,'uint8')
        stage[support] = 254
        stage[low] = np.minimum(np.ceil(hand[low]*10),101).astype('uint8')
        drainage = (stage==0)&(flow>=DRAINAGE_M2)
        if not drainage.any() or not np.any(stage<=100):
            raise ValueError('No eligible HAND screen or source cells')
        manifest.update(kind='stage', drainageAreaM2=DRAINAGE_M2, bufferM=BUFFER_CELLS*grid['resolution_m'],
                        bufferCoverage=coverage, bufferOutlets=outlets, tiles=tiles,
                        terrain=asset('stage',stage), drainage=asset('drainage',drainage), observations={})
        example = EXAMPLES[case]
        col,row = example[2]
        if drainage[row,col]:
            manifest['example'] = example
        valid = np.zeros(grid['shape'], 'uint16')
        dark = valid.copy()
        for index,visit in enumerate(case_manifest['observations']):
            hh = align(read_atlas_plane(public, path.parent, visit['rasters']['hh'], case_manifest['grid']).filled(np.nan),
                       case_manifest['grid'],grid)
            mask = np.select([np.isfinite(hh)&(hh< -19.5), np.isfinite(hh)&(hh> -11.5), np.isfinite(hh)], [1,3,2])
            manifest['observations'][visit['observation_id']] = asset(
                'hh', mask, sourceId=visit['source_granule_id'], utc=visit['timestamp'])
            if case == 'jamuna_river':
                valid[np.isfinite(hh)] |= 1 << index
                dark[np.isfinite(hh) & (hh <= -17)] |= 1 << index
        if case == 'jamuna_river':
            if not 6 <= len(case_manifest['observations']) <= 16:
                raise ValueError('Transect packing requires 6–16 admitted visits')
            manifest['bank'] = {'series':asset('bank',np.stack((valid,dark)),'<u2'),
                'ids':[v['observation_id'] for v in case_manifest['observations']], 'hhCutoffDb':-17,
                'example':[[416,335],[470,335]]}
            lc = atlas_landcover_path(ROOT,case)
            if lc.is_file():
                receipt = json.loads(lc.with_suffix('.json').read_bytes())
                if receipt['sha256'] != digest(lc.read_bytes()) or receipt['doi'] != WORLDCOVER_DOI:
                    raise ValueError('WorldCover crop does not match its source receipt')
                plane = read_atlas_plane(lc.parent,lc.parent,lc.name,radar).filled(0).astype('float32')
                plane[plane==0] = np.nan
                crop = align(plane,radar,grid)
                manifest['bank']['cover'] = asset('bank-cover',np.select([crop==40,np.isfinite(crop)],[2,1]),
                    year=2021, doi=WORLDCOVER_DOI)
    else:
        manifest.update(kind='slope', terrain=asset('slope',slope,'<f4'), comparisons=[])
        dem, tiles = buffered_dem(case,grid,sources)
        angles = json.loads((ROOT/'data/context/nepal_atlas_look.json').read_bytes())
        geometry = angles['cases'][case]
        if geometry['sourceId'] not in {v['source_granule_id'] for v in case_manifest['observations']}:
            raise ValueError('Look preset must reference an admitted GCOV observation')
        manifest['orbit'] = {'dem':asset('orbit',dem,'<f4'),'bufferCells':BUFFER_CELLS,'tiles':tiles,
                             **geometry}
        native = {p['pair_id']:p for p in admitted_pairs(ROOT,path,case_manifest)}
        for first, later in zip(identity['pairs'], identity['pairs'][1:]):
            if not comparison_policy(first, later):
                continue
            a,b = [coherence_plane(public,path.parent,native[p['id']]) for p in (first,later)]
            aligned = align(coherence_delta(a,b),first['grid'],grid)
            sign = np.select([np.isfinite(aligned)&(aligned<0),np.isfinite(aligned)], [1,2])
            manifest['comparisons'].append(asset('coherence',sign,pairs=[
                {k:p[k] for k in ('startUtc','endUtc','sourceId')} for p in (first,later)]))
        archive = ROOT/'data/context/unosat_20260826_flood_extent.zip'
        if case == 'nepal_impact_corridor' and archive.is_file():
            extent, checksum, _ = official_extent(archive)
            if grid['crs'] != 'EPSG:32645':
                raise ValueError('UNOSAT projection mismatch')
            affine=Affine(*grid['affine'])
            clipped=extent.intersection(box(*rasterio.transform.array_bounds(*grid['shape'],affine)))
            if not clipped.is_empty:
                mask = rasterize([clipped], out_shape=grid['shape'], transform=affine, dtype='uint8')
                manifest['localImpact'] = asset('impact',mask,sourceUrl=SOURCE_URL,sourceSha256=checksum)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name,data in assets.items():
        (OUTPUT/name).write_bytes(data)
    (OUTPUT/f'{case}.json').write_text(json.dumps(manifest, sort_keys=True)+'\n')
    print(case,manifest['kind'],len(assets),'grids',int(np.isfinite(slope).sum()),'terrain cells',flush=True)


if __name__ == '__main__':
    manifests = active_manifests(ROOT)
    require_admitted(ROOT, manifests)
    admitted = json.loads((ROOT/'config.atlas-admission.json').read_text())
    identities = json.loads((ROOT/'web/atlas-contract-records.json').read_text())
    sources = json.loads((ROOT/'data/context/context-v2/terrain/sources.json').read_text())['items']
    for case,path in manifests.items():
        write_case(case,path,admitted,identities[case],sources)
