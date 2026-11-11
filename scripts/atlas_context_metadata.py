"""Attach dated and grid-bound metadata without rewriting the accepted atlas record."""
import hashlib
import json

import numpy as np
from affine import Affine
from rasterio.features import rasterize

from src.compute.atlas_measurements import dualpol_summary
from src.compute.atlas_explanations import evaluate_atlas_visit, explanation_context, footprint_median_slope
from src.compute.atlas_review import radar_review_visit, review_location
from src.compute.atlas_landcover import atlas_landcover_path, landcover_summary
from src.compute.atlas_spatial import read_atlas_plane
from src.compute.context_v2 import utc


def read_json(path):
    return json.loads(path.read_text())


def radar_metadata(public, path, manifest, sources, rules):
    grid = manifest['grid']
    shape = tuple(grid['shape'])
    common = np.ones(shape, bool)
    quality = {}
    visits = manifest['observations']

    def pair(visit):
        return [read_atlas_plane(public, path.parent, visit['rasters'][channel], grid).filled(np.nan)
                for channel in ('hh', 'hv')]

    for visit in visits:
        hh, hv = pair(visit)
        paired = np.isfinite(hh) & np.isfinite(hv)
        common &= paired
        channels = {}
        for name, plane in [('hh', hh), ('hv', hv)]:
            qa = visit['quality'][name]
            count = int(np.isfinite(plane).sum())
            if count != qa['analysis_valid_pixels']:
                raise ValueError('Canonical radar validity differs from its source receipt')
            raster = visit['rasters'][name]
            if not raster.startswith('/cases/'):
                raster = '/cases/'+(path.parent/raster).resolve().relative_to(public.resolve()).as_posix()
            channels[name] = {
                'assessed': count, 'masked': plane.size-count, 'excluded': 0,
                'sourceMasked': qa['masked_pixels'], 'sourceAssessed': qa['valid_pixels'],
                'sourceMaskCodes': qa['mask_values'], 'alignment': qa['alignment'],
                'windowSha256': qa['window_sha256'], 'raster':raster,
            }
        quality[visit['observation_id']] = {**channels, 'pairedValid': int(paired.sum()), 'total': paired.size}

    supports, footprints = [], []
    review = manifest['case_id'] in ('jamuna_river', 'tanguar_wetland')
    for index, (source, evidence) in enumerate(sources):
        profile, mask = evidence['profile'], evidence.get('footprint_raster')
        if mask:
            if hashlib.sha256((source.parent/mask['file']).read_bytes()).hexdigest() != mask['sha256']:
                raise ValueError('Saved footprint raster checksum mismatch')
            window = profile['window']
            row, col, height, width = (window[k] for k in ('row','col','height','width'))
            window_grid = {**grid,'shape':[height,width],
                           'affine':list(Affine(*grid['affine']) @ Affine.translation(col,row))[:6]}
            footprint = np.zeros(shape, bool)
            footprint[row:row+height,col:col+width] = read_atlas_plane(
                public, source.parent, mask['file'], window_grid).filled(0) == 1
        elif profile.get('geometry_pixel'):
            footprint = rasterize([profile['geometry_pixel']], out_shape=shape, transform=Affine.identity(), dtype='uint8').astype(bool)
        elif index == 0:
            footprint = read_atlas_plane(public, path.parent, 'tracked_footprint.tif', grid).filled(0) == 1
        else:
            footprint = np.ones(shape, bool)
        fixed = footprint & common
        if int(footprint.sum()) != profile['footprint_pixels'] or int(fixed.sum()) != profile['common_valid_pixels']:
            raise ValueError('Dual-pol support differs from the accepted saved footprint')
        supports.append(fixed)
        footprints.append(footprint)

    summaries = [{} for _ in supports]
    explanations = [[] for _ in supports]
    derived = [i for i, (_, evidence) in enumerate(sources)
               if 'explanations' not in evidence and supports[i].any()
               and evidence['profile'].get('status', 'MEASURED') == 'MEASURED']
    if derived:
        folder, context_manifest, context = explanation_context(path, manifest)
        terrain_grid = context_manifest['grid']
        slope = read_atlas_plane(public, folder, context_manifest['layers']['slope']['raster'],
                                 terrain_grid).filled(np.nan)
        reference = next(visit for visit in visits if visit['timestamp'] == manifest['reference_timestamp'])
        reference_hh = read_atlas_plane(public, path.parent, reference['rasters']['hh'], grid).filled(np.nan)
        medians = {i: footprint_median_slope(supports[i], grid, terrain_grid, slope) for i in derived}
        reference_values = {i: reference_hh[supports[i]] for i in derived}
    reviews = [{'location': review_location(mask, Affine(*grid['affine']), grid['crs']), 'visits': {}}
               for mask in footprints] if review else []
    for visit_index, visit in enumerate(visits):
        hh, hv = pair(visit)
        for index, fixed in enumerate(supports):
            measured = sources[index][1]['profile'].get('status', 'MEASURED') == 'MEASURED'
            support = fixed if measured else np.zeros_like(fixed)
            summaries[index][visit['observation_id']] = dualpol_summary(hh,hv,support)
            if review:
                reviews[index]['visits'][visit['observation_id']] = radar_review_visit(hh,hv,support)
        for index in derived:
            row = sources[index][1]['profile']['observations'][visit_index]
            if (row['observation_id'], row['timestamp']) != (visit['observation_id'], visit['timestamp']):
                raise ValueError('Explanation profile does not match the accepted acquisition')
            explanations[index].append(evaluate_atlas_visit(
                row, manifest['reference_timestamp'], hh[supports[index]], reference_values[index],
                medians[index], context, rules))
    worldcover = atlas_landcover_path(public.parents[2], manifest['case_id'])
    landcover = [landcover_summary(worldcover, grid, support) for support in supports]
    return quality, summaries, footprints, reviews, explanations, landcover


def terrain_metadata(public, path, case_id, observations, hand_audit):
    folder = path.parent.parent/'context-v2'
    context = read_json(folder/'manifest.json')
    if context['case_id'] != case_id:
        raise ValueError('Terrain context belongs to another case')
    grid = context['grid']
    if hand_audit['grid']!=grid or hand_audit['contextManifestSha256']!=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest():
        raise ValueError('HAND crop audit is bound to a different terrain record')
    cell_km2 = grid['resolution_m']**2/1e6
    layers = {}
    for name, item in context['layers'].items():
        array = read_atlas_plane(public, folder, item['raster'], grid)
        values = array.compressed()
        values = values[np.isfinite(values)]
        if name == 'geometry_candidates' and not np.isin(values, np.arange(8)).all():
            raise ValueError('Unexpected geometry screening bits')
        flagged = int(np.count_nonzero(values)) if name == 'geometry_candidates' else 0
        masked = array.size-len(values)
        layers[name] = {
            'assessed': len(values)-flagged, 'excluded': flagged, 'masked': masked,
            'assessedKm2': (len(values)-flagged)*cell_km2, 'excludedKm2': flagged*cell_km2,
            'maskedKm2': masked*cell_km2, 'scale': item['limits'],
            'raster':'/cases/'+(folder/item['raster']).resolve().relative_to(public.resolve()).as_posix(),
        }
    dem = read_atlas_plane(public, folder, context['layers']['dem']['raster'], grid).filled(np.nan)
    slope = read_atlas_plane(public, folder, context['layers']['slope']['raster'], grid).filled(np.nan)
    controls = {(x['observation_id'],x['timestamp']):x for x in context['radiometric_controls']}
    control_by_id = {o['id']:controls[(o['id'],o['utc'])] for o in observations if (o['id'],o['utc']) in controls}
    geometry = context['incidence_source']
    return {
        'source': context['terrain_sources'][0]['dataset'], 'verticalDatum':context['terrain_sources'][0]['vertical_reference'],
        'nativeResolution':context['terrain_sources'][0]['native_resolution'], 'grid':grid, 'layers':layers,
        'demVoidCells': int((~np.isfinite(dem)).sum()), 'nearFlatCells': int((np.isfinite(slope)&(slope<.01)).sum()),
        'geometrySource': geometry['file'].rsplit('/',1)[-1], 'geometrySpacingM':geometry['native_metadata_spacing_m'],
        'geometryHeightEllipsoidM':geometry['height_plane_ellipsoid_m'],
        'hydrology': context['hydrology'], 'routingBufferM':2100, 'controls': control_by_id,
        'controlReferenceUtc':context['radiometric_controls'][0]['timestamp'],
        'hand':{'status':'unavailable','reason':'Independent drainage comparison and buffered routing checks are pending.',
                'cropOnlySensitivity':hand_audit['hand_sensitivity']},
    }


def context_metadata(root, case_id, path, observations, atlas_case, imerg_audit):
    by_time = {o['utc']:o['id'] for o in observations}
    imerg = {}
    for row in imerg_audit['windows']:
        if row['end_utc'] in by_time and any(p['case_id']==case_id for p in row['footprints']):
            catalog = row['catalog']
            imerg[by_time[row['end_utc']]] = {
                'status':'unavailable','startUtc':row['start_utc'],'endUtc':row['end_utc'],
                'expectedBins':len(row['expected_bin_starts']),'acceptedBins':0,
                'catalogedBins':catalog['matched_bins'],'coverage':None,'catalogQuery':catalog['query'],
                'catalogReceiptSha256':catalog['response_sha256'],
            }
    result = {'imerg':imerg,'imergAuditedUtc':imerg_audit['queried_utc'],
              'rain':{},'thermal':{},'optical':{},'scenario':None}
    if atlas_case['country']=='Bangladesh':
        optical = read_json(path.parent.parent/'references-v1/manifest.json')
        tolerance = optical['design']['time_tolerance_seconds']['HLS']
        for row in optical['results']:
            if by_time.get(row['radar_timestamp']) != row['observation_id']:
                raise ValueError('Optical context must be tied to the exact radar visit')
            if row['reference_timestamp']:
                delta = abs((utc(row['reference_timestamp'])-utc(row['radar_timestamp'])).total_seconds())
                if delta>tolerance or abs(delta-row['delta_seconds'])>.001:
                    raise ValueError('Optical context exceeds its frozen time tolerance or changed source time')
            columns = ('reference_id','reference_timestamp','delta_seconds','clear_assessable_pixels','reference_pixels','status','scope')
            result['optical'].setdefault(row['footprint_id'],{})[row['observation_id']] = {k:row.get(k) for k in columns}
        result['opticalPolicy'] = {'timeToleranceSeconds':tolerance,'resolutionM':30,'qa':optical['qa_policy']}
    if not atlas_case.get('context'):
        return result

    folder = root/'web/public/cases/nepal_case_01'
    rain = read_json(folder/'context/context.json')
    thermal = read_json(folder/'thermal/manifest.json')
    flood = read_json(folder/'flood/manifest.json')
    result['rainSource'] = {k:rain['rainfall_source'][k] for k in (
        'dataset','source_url','native_resolution_degrees','source_units','bin_duration_seconds','cube_sha256')}
    for visit in rain['observations']:
        timestamp = visit['timestamp']
        if timestamp not in by_time:
            continue
        windows = {}
        for key, window in visit['windows'].items():
            if window['requested_end_utc'] != timestamp or not 0 <= window['end_lag_seconds'] < 3600:
                raise ValueError('Rain context has a mismatched anchor or hour lag')
            stats = visit['layers'][key]['statistics']
            windows[key] = {'window':window,'validCropFraction':stats['valid_fraction'],
                            'meanMm':stats['mean'] if stats['valid_fraction']>0 else None}
        result['rain'][by_time[timestamp]] = windows
    result['thermalPolicy'] = {k:thermal[k] for k in ('qa_rule','native_thermal_resolution_m','analysis_grid_m')}
    result['thermal'] = {s['scene_id']:{'utc':s['datetime'],'validFraction':s['valid_fraction'],'status':s['status'],
                                      'meanC':s['statistics_celsius']['mean']} for s in thermal['scenes']}
    anchors = {by_time[o['timestamp']]:o['observation_id'] for o in flood['observations']
               if o['timestamp'] in by_time and result['rain'].get(by_time[o['timestamp']],{}).get('rain_168h',{}).get('meanMm') is not None}
    result['scenario'] = {'modelVersion':flood['model']['model_version'],'inputsSha256':flood['inputs_sha256'],'anchors':anchors}
    return result
