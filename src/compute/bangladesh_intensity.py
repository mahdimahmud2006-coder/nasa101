"""Build additive, multi-case HH/HV investigation artifacts; leave historical outputs intact."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import array_bounds
from shapely.geometry import box, mapping
from shapely.ops import transform
from pyproj import Transformer

from src.ingest.timeseries import read_observation, incompatibilities
from src.ingest.metadata import parse_date
from src.ingest.extract_gcov import analysis_window
from src.compute.timeseries_pipeline import canonical_observation, cog
from src.compute.investigations import radar_responses, fixed_footprint_profile
from src.compute.area import pixel_area_km2
from src.compute.validation_context import official_extent, SOURCE_URL
from src.export.artifacts import preview, write_json
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]


def processing_release(granule):
    match = re.search(r'_([PX]\d{5})_', granule)
    if not match:
        raise ValueError('Missing named processing release')
    return match.group(1)


def sources_for(case, root):
    paths = [root / p for p in case['source_files'] if (root / p).is_file()]
    folder = root / case['source_directory']
    paths += sorted(folder.glob(case['granule_pattern'])) if folder.exists() else []
    return sorted(set(p.resolve() for p in paths))


def categorical_preview(path, arrays, colors):
    shape = arrays[0].shape
    rgba = np.zeros((*shape, 4), dtype=np.uint8)
    for mask, color in zip(arrays, colors):
        rgba[mask] = color
    image = Image.fromarray(rgba)
    image.thumbnail((1100, 1100), Image.Resampling.NEAREST)
    image.save(path)


def profile_record(hh, hv, mask, area, observations, label, provenance):
    data = fixed_footprint_profile(hh, hv, mask, area)
    for row, obs in zip(data['observations'], observations):
        row.update(observation_id=obs['observation_id'], timestamp=obs['timestamp'])
    return {'label': label, 'selection': provenance, **data}


def build_case(config, case, root, destination, preserved_directory=None, stable_ids=False):
    paths = sources_for(case, root)
    if len(paths) < config['minimum_observations']:
        return {**case, 'status': 'AWAITING_DATA', 'local_source_count': len(paths),
                'minimum_observations': config['minimum_observations'],
                'next_step': 'Download the shared Bangladesh files and run make investigations. No observations have been fabricated.'}
    sources = []
    for path in paths:
        item = read_observation(path, config['frequency'], config['terms'][0])
        item['source_file'] = str(path)
        if not all(term in item['covariance_terms'] for term in config['terms']):
            raise ValueError(f'{path.name}: HH/HV terms required')
        sources.append(item)
    sources.sort(key=lambda s: parse_date(s['acquisition_start']))
    anchor = sources[0]
    times = set()
    for item in sources:
        reasons = incompatibilities(anchor, item)
        if processing_release(item['granule_id']) != processing_release(anchor['granule_id']):
            reasons.append('Processing release differs')
        timestamp = parse_date(item['acquisition_start'])
        if timestamp in times:
            reasons.append('Duplicate acquisition timestamp')
        if reasons:
            raise ValueError(f"{Path(item['source_file']).name}: {'; '.join(reasons)}")
        times.add(timestamp)
    _, affine = analysis_window(anchor, case['center'], case['size_m'])
    shape = (round(case['size_m'][1] / abs(anchor['spacing'][1])), round(case['size_m'][0] / anchor['spacing'][0]))
    area = pixel_area_km2(affine, anchor['crs'])
    directory = destination / case['case_id'] / 'investigation'
    directory.mkdir(parents=True, exist_ok=True)
    hh, hv, observations = [], [], []
    preserved = json.loads((preserved_directory/'manifest.json').read_text()) if preserved_directory else None
    prior = {o['timestamp']:o for o in preserved['observations']} if preserved else {}
    if preserved and (preserved['grid']['shape']!=list(shape) or preserved['grid']['affine']!=list(affine)[:6] or preserved['grid']['crs']!=anchor['crs']):
        raise ValueError('New record must preserve the original physical crop grid')
    for i, source in enumerate(sources):
        print(case['case_id'], Path(source['source_file']).name, flush=True)
        obs = {'observation_id': 'visit_' + str(i), 'timestamp': parse_date(source['acquisition_start']).isoformat().replace('+00:00', 'Z'),
               'source_granule_id': source['granule_id'], 'source_file': Path(source['source_file']).name,
               'product_version': source['product_version'], 'processing_release': processing_release(source['granule_id']),
               'track': source['track'], 'frame': source['frame'], 'range_bandwidth_hz': source['range_bandwidth_hz'],
               'doi': source['doi'], 'quality': {}, 'rasters': {}, 'layers': {}}
        if stable_ids:obs['observation_id']='acq_'+parse_date(obs['timestamp']).strftime('%Y%m%dT%H%M%S')
        old=prior.get(obs['timestamp'])
        for term, store, pol in [('HHHH', hh, 'hh'), ('HVHV', hv, 'hv')]:
            record = dict(source, covariance_term=term, polarization=term[:2], layer_path=source['grid_path'] + '/' + term)
            if old:
                if old['source_granule_id']!=source['granule_id']:raise ValueError('Changed identity at preserved acquisition')
                with rasterio.open(preserved_directory/old['rasters'][pol]) as ds:image=ds.read(1)
                quality={**old['quality'][pol], 'preserved_cog_sha256':hashlib.file_digest((preserved_directory/old['rasters'][pol]).open('rb'),'sha256').hexdigest()}
            else:image, quality = canonical_observation(record, affine, anchor['crs'], shape, config['median_filter_size'])
            fraction = float(np.isfinite(image).mean())
            if fraction < config['minimum_valid_fraction']:
                raise ValueError(f'{case["case_id"]}: {pol} valid coverage {fraction:.3f} below minimum')
            store.append(image)
            name = f'{pol}_{i}.tif'
            if old:shutil.copy2(preserved_directory/old['rasters'][pol],directory/name)
            else:cog(directory / name, image, affine, anchor['crs'], f'{pol.upper()} gamma-0, median-filtered dB')
            obs['rasters'][pol] = name
            obs['quality'][pol] = {'valid_fraction': fraction, **quality}
        observations.append(obs)
    hh, hv = np.stack(hh), np.stack(hv)
    response = radar_responses(hh, hv, config['radar_dark_hh_db'], config['radar_dark_hv_db'], config['brightening_db'])
    limits = {}
    for pol, values in [('hh', hh), ('hv', hv)]:
        sample = values[:, ::8, ::8]; finite = sample[np.isfinite(sample)]
        low, high = np.percentile(finite, [2, 98]).tolist()
        limits[pol] = [low, max(high, low + .001)]
    for i, obs in enumerate(observations):
        series = {'hh': hh[i], 'hv': hv[i], 'ratio': hh[i] - hv[i],
                  'baseline': np.where(response['baseline_common'][i], hh[i] - hh[0], np.nan),
                  'successive': hh[i] - hh[i-1] if i else None}
        if case['module'] in ('river', 'wetland'):
            obs['response'] = {'paired_valid_area_km2': int(response['valid'][i].sum()) * area,
                'radar_dark_candidate_area_km2': int(response['dark'][i].sum()) * area,
                'baseline_common_area_km2': int(response['baseline_common'][i].sum()) * area,
                'brightening_candidate_area_km2': int(response['brightening'][i].sum()) * area}
            for key in ('gain', 'loss', 'persistent'):
                obs['response'][key + '_dark_signature_km2'] = int(response['transitions'][i][key].sum()) * area
            transitions = response['transitions'][i]
            categorical_preview(directory / f'water_{i}.png', [response['valid'][i], response['dark'][i]], [[31, 48, 58, 255], [57, 216, 212, 255]])
            categorical_preview(directory / f'river_{i}.png', [transitions['common'], transitions['persistent'], transitions['gain'], transitions['loss']], [[31,48,58,255],[81,146,180,255],[57,216,212,255],[255,193,97,255]])
            categorical_preview(directory / f'wetland_{i}.png', [response['baseline_common'][i], response['brightening'][i], response['dark'][i] & response['baseline_common'][i]], [[31,48,58,255],[220,158,252,255],[57,216,212,255]])
            obs['layers'].update(water=f'water_{i}.png', river=f'river_{i}.png', wetland=f'wetland_{i}.png')
        paired = response['valid'][i]
        base_common = response['baseline_common'][i]
        obs['paired_valid_fraction'] = float(paired.mean())
        obs['baseline_common_fraction'] = float(base_common.mean())
        obs['baseline_disturbance_area_km2'] = int((base_common & (np.abs(hh[i]-hh[0]) >= config['baseline_disturbance_db'])).sum()) * area
        for layer, image in series.items():
            if image is None:
                obs['layers'][layer] = None
                continue
            name = f'{layer}_{i}.webp'
            scale = limits.get(layer, [0., 20.] if layer == 'ratio' else [-8., 8.])
            preview(directory / name, image, scale, 'delta' if layer in ('baseline', 'successive') else 'radar', size=1100)
            obs['layers'][layer] = name
    profiles = []
    if case['module'] in ('river', 'wetland'):
        profile=profile_record(hh,hv,np.ones(shape,dtype=bool),area,observations,
            'Geographic study window · common-valid mean',
            'Geographic window selected before radar inspection, using the same paired-valid pixels across all visits. This is not a water/habitat reference; opposing local changes can cancel in the average. Click the map to inspect a local neighborhood.')
        profile['footprint_kind']='study_window'
        profiles.append(profile)
    if case.get('legacy_zone_raster'):
        with rasterio.open(root / case['legacy_zone_raster']) as source:
            if source.transform != affine or source.crs.to_string() != anchor['crs'] or source.shape != shape:
                raise ValueError('Historical zone grid differs from investigation grid')
            mask = source.read(1) > 0
        profiles.append(profile_record(hh,hv,mask,area,observations,'Previously tracked 1.99-hectare zone',case['selection_note']))
    reference = None
    if case.get('reference_archive'):
        mapped, digest, _ = official_extent(root / case['reference_archive'])
        if anchor['crs'] != 'EPSG:32645':
            raise ValueError('Independent reference requires reviewed EPSG:32645 grid')
        clipped = mapped.intersection(box(*array_bounds(*shape, affine)))
        if not clipped.is_empty:
            mask = rasterize([(mapping(clipped),1)], out_shape=shape, transform=affine, fill=0, dtype='uint8').astype(bool)
            profile = profile_record(hh,hv,mask,area,observations,'Preliminary mapped impact footprint inside this crop',case['selection_note'])
            profiles.append(profile)
            pixel_geom = transform(lambda x,y,z=None: ((np.asarray(x)-affine.c)/affine.a, (np.asarray(y)-affine.f)/affine.e),clipped)
            reference = {'url': SOURCE_URL, 'publisher': 'UNITAR/UNOSAT via UNESCO IHP-WINS',
                         'archive_sha256': digest, 'field_validated': False,
                         'label': 'Preliminary mudflow/rockflow impact mapping',
                         'intersected_geometry_area_km2': clipped.area / 1e6,
                         'mapped_native_center_pixel_area_km2': int(mask.sum()) * area,
                         'geometry_pixel': mapping(pixel_geom),
                         'interpretation': 'Spatial context, not exhaustive water truth or independently established classification accuracy.'}
    limitations = ['PROVISIONAL GCOV intensity; not ground displacement.',
        'HH/HV measurements do not uniquely identify a physical cause.',
        'Only actual acquisitions are shown; missing visits are not interpolated.',
        'Fixed-baseline difference does not establish physical damage or recovery.',
        'Radar-dark and brightening thresholds are illustrative and UNCALIBRATED; not validated water, habitat or flood classifications.',
        'Observed-visit fractions are not continuous inundation duration or seasonal climatology.',
        'A fixed common-valid footprint is required for selected-region profiles.']
    manifest = {'schema_version':1,'case_id':case['case_id'],'module':case['module'],'title':case['title'],
        'question':case['question'],'status':'OBSERVATIONS_READY','collection':config['collection'],
        'grid':{'shape':list(shape),'affine':list(affine)[:6],'crs':anchor['crs'],'pixel_area_km2':area,
                'bounds_wgs84':list(rasterio.warp.transform_bounds(anchor['crs'],'EPSG:4326',*array_bounds(*shape,affine)))},
        'baseline_observation_id':observations[0]['observation_id'],'observations':observations,
        'profiles':profiles,'reference':reference,'display_limits':limits,
        'thresholds':{'baseline_disturbance_db':config['baseline_disturbance_db'],'radar_dark_hh_db':config['radar_dark_hh_db'],
                      'radar_dark_hv_db':config['radar_dark_hv_db'],'brightening_db':config['brightening_db'],'calibration_status':'UNCALIBRATED'},
        'selection_note':case['selection_note'],'limitations':limitations,
        'provenance':{'config_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
                      'model_sha256':hashlib.sha256(Path(__file__).with_name('investigations.py').read_bytes()+Path(__file__).read_bytes()).hexdigest(),
                      'source_policy':config['source_policy']},
        'formulas':{'baseline':'HH(t) - HH(first observed visit), dB','successive':'HH(t) - HH(previous observed visit), dB; unavailable at first visit',
                    'ratio':'HH_dB - HV_dB = 10 log10(HH_power/HV_power); difference of filtered log-power',
                    'dark':'valid HH <= configured HH threshold AND valid HV <= configured HV threshold',
                    'occupancy':'dark valid visits / paired valid visits; only when at least two visits valid',
                    'brightening':'both channels increase by configured dB relative to first observation, on baseline-common pixels'}}
    if case['module'] in ('river','wetland'):
        preview(directory/'occupancy.webp',response['dark_observation_fraction'],[0,1],size=1100)
        manifest['occupancy_preview']='occupancy.webp'
        cog(directory/'valid_visit_count.tif',response['valid_visits'].astype('uint16'),affine,anchor['crs'],'Number of paired-valid observations',0,True)
        cog(directory/'dark_observation_fraction.tif',response['dark_observation_fraction'],affine,anchor['crs'],'Fraction of observed paired-valid visits satisfying uncalibrated radar-dark thresholds')
    write_json(directory/'manifest.json',manifest)
    return {**case,'status':'OBSERVATIONS_READY','observation_count':len(observations),
            'manifest_url':f'/cases/{case["case_id"]}/investigation/manifest.json'}
