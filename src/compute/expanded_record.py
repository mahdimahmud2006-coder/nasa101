"""Add supplied Nepal observations and native GUNW evidence without replacing a result.

The old investigation and its August-19 reference remain immutable. This extension
also uses August 19 (not the earliest new date) as its explicit change reference.
"""
import argparse
import hashlib
import math
from pathlib import Path
import tempfile
import shutil

from affine import Affine
import h5py
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, Window, transform as window_transform

from src.compute.evidence_common import ROOT, load, save, sha
from src.compute.investigation_pipeline import processing_release
from src.compute.timeseries_pipeline import canonical_observation, cog
from src.export.dualpol_render import load_palettes, palette_rgba, preview, css_gradient
from src.ingest.inspect_h5 import native
from src.ingest.metadata import parse_date
from src.ingest.timeseries import read_observation, incompatibilities

VERSION = 'expanded-v1'
REFERENCE = '2026-08-19T23:39:18Z'
CASES = ('nepal_surface', 'nepal_impact_corridor')
LIMITS = {'hh': [-30, 0], 'hv': [-40, -5], 'cpr': [-20, 0],
          'hh_reference': [-8, 8], 'hv_reference': [-8, 8], 'cpr_reference': [-8, 8],
          'hh_successive': [-8, 8], 'coherence20': [0, 1], 'coherence80': [0, 1]}


def timestamp(value):
    return parse_date(value).isoformat().replace('+00:00', 'Z')


def gunw_validity(coherence, mask):
    """Reference/secondary subswaths valid, no anomaly bits; water is not invalid.

    Low byte is decimal water/ref/secondary encoding. Bits 8..23 are
    secondary/reference anomaly flags. No coherence cutoff is imposed.
    """
    low = mask.astype('uint32') & 255
    return (np.isfinite(coherence) & (coherence >= 0) & (coherence <= 1)
            & ((low // 10) % 10 > 0) & (low % 10 > 0)
            & ((mask.astype('uint32') & 0x00FFFF00) == 0)
            & (mask != np.iinfo('uint32').max))


def native_window(group, bounds, names):
    """Read an enclosing crop on the product's own grid, never upscale to GCOV."""
    x, y = group['xCoordinates'][:], group['yCoordinates'][:]
    dx, dy = float(group['xCoordinateSpacing'][()]), float(group['yCoordinateSpacing'][()])
    if dx <= 0 or dy >= 0 or not np.allclose(np.diff(x), dx) or not np.allclose(np.diff(y), dy):
        raise ValueError('Irregular GUNW coordinates')
    full = Affine(dx, 0, x[0]-dx/2, 0, dy, y[0]-dy/2)
    floating = from_bounds(*bounds, full)
    col, row = math.floor(floating.col_off), math.floor(floating.row_off)
    end_col, end_row = math.ceil(floating.col_off+floating.width), math.ceil(floating.row_off+floating.height)
    if row < 0 or col < 0 or end_row > len(y) or end_col > len(x):
        raise ValueError('GUNW crop outside source')
    window = Window(col, row, end_col-col, end_row-row)
    arrays = {key: group[path][row:end_row, col:end_col] for key, path in names.items()}
    if any(a.shape != (end_row-row, end_col-col) for a in arrays.values()):
        raise ValueError('GUNW layer grid mismatch')
    return arrays, window_transform(window, full), int(group['projection'][()]), window


def gunw_header(path, accepted):
    with h5py.File(path, 'r') as f:
        g = f['science/LSAR/identification']
        fields = {k: native(g[k][()]) for k in ['granuleId', 'productType', 'productLevel', 'productVersion',
                  'compositeReleaseId', 'trackNumber', 'frameNumber', 'orbitPassDirection', 'lookDirection',
                  'referenceZeroDopplerStartTime', 'secondaryZeroDopplerStartTime',
                  'referenceHasInputDataException', 'secondaryHasInputDataException']}
        expected = {'productType': 'GUNW', 'productLevel': 'L2', 'productVersion': '1.0.11',
                    'compositeReleaseId': 'P05023', 'trackNumber': 98, 'frameNumber': 16,
                    'orbitPassDirection': 'Ascending', 'lookDirection': 'Left',
                    'referenceHasInputDataException': 0, 'secondaryHasInputDataException': 0}
        if any(fields[k] != v for k, v in expected.items()):
            raise ValueError('Incompatible GUNW identification: '+path.name)
        times = [timestamp(fields[k]) for k in ['referenceZeroDopplerStartTime', 'secondaryZeroDopplerStartTime']]
        if any(t not in accepted for t in times) or (parse_date(times[1])-parse_date(times[0])).days != 12:
            raise ValueError('GUNW dates must match accepted GCOV endpoints and a 12-day pair')
        inputs = f['science/LSAR/GUNW/metadata/processingInformation/inputs']
        slcs = [native(inputs[k][()]) for k in ['l1ReferenceSlcGranules', 'l1SecondarySlcGranules']]
        for values, t in zip(slcs, times):
            compact = parse_date(t).strftime('%Y%m%dT%H%M%S')
            if len(values) != 1 or not all(s in values[0] for s in ['_098_A_016_4005_DHDH_A_', compact, '_P05023_']):
                raise ValueError('GUNW source RSLC identity/mode mismatch')
        parameters = f['science/LSAR/GUNW/metadata/processingInformation/parameters']
        for role in ['reference', 'secondary']:
            if float(parameters[f'{role}/frequencyA/rangeBandwidth'][()]) != 40e6:
                raise ValueError('GUNW source range bandwidth mismatch')
        freq = f['science/LSAR/GUNW/grids/frequencyA']
        if native(freq['listOfPolarizations'][()]) != ['HH'] or float(freq['centerFrequency'][()]) != 1239e6:
            raise ValueError('Expected HH frequency-A L-band GUNW')
        return {'identification': fields, 'timestamps': times, 'source_slc_granules': slcs,
                'source_file': str(path.relative_to(ROOT)), 'size_bytes': path.stat().st_size,
                'dem_source': native(inputs['demSource'][()]), 'water_mask_source': native(inputs['waterMaskSource'][()]),
                'phase_corrections': 'Source ionosphere and external correction metadata retained. Not applied by this extension. No LOS displacement published.',
                'source_policy': 'NASA–ISRO, JPL / ASF DAAC; declared DEM ESA/Copernicus, water mask JRC/Google, ESA, OpenStreetMap and NASA MEaSUREs. No Chinese provider identified in these declared inputs.'}


def profile(stacks, footprint, observations, reference_index, label, area):
    common = footprint & np.isfinite(stacks['hh']).all(axis=0) & np.isfinite(stacks['hv']).all(axis=0)
    count = int(common.sum())
    means = {pol: [float(a[common].astype('float64').mean()) if count else None for a in stack]
             for pol, stack in stacks.items()}
    rows = []
    for i, obs in enumerate(observations):
        row = {'timestamp': obs['timestamp'], 'observation_id': obs['observation_id']}
        for pol in ['hh', 'hv']:
            row[pol+'_mean_db'] = means[pol][i]
            row[pol+'_reference_delta_db'] = means[pol][i]-means[pol][reference_index] if count else None
            row[pol+'_successive_delta_db'] = means[pol][i]-means[pol][i-1] if count and i else None
        row['cpr_mean_db'] = means['hv'][i]-means['hh'][i] if count else None
        row['cpr_reference_delta_db'] = row['hv_reference_delta_db']-row['hh_reference_delta_db'] if count else None
        rows.append(row)
    return {'label': label, 'footprint_pixels': int(footprint.sum()), 'common_valid_pixels': count,
            'common_valid_area_km2': count*area, 'reference_timestamp': REFERENCE,
            'support': 'Same HH/HV-valid native pixel centers across every expanded visit; may be smaller than the preserved original three-date support.',
            'observations': rows}


def probe(case, row, col, root=ROOT):
    """A fixed 11x11 (edge-clipped) neighborhood through every expanded visit."""
    if case not in CASES:
        raise ValueError('Unknown expanded case')
    directory = Path(root)/f'web/public/cases/{case}/{VERSION}'
    manifest = load(directory/'manifest.json'); height, width = manifest['grid']['shape']
    if not isinstance(row, int) or not isinstance(col, int) or not (0 <= row < height and 0 <= col < width):
        raise ValueError('Outside native grid')
    top, left = max(0, row-5), max(0, col-5)
    window = Window(left, top, min(width, col+6)-left, min(height, row+6)-top)
    stacks = {pol: [] for pol in ['hh', 'hv']}
    for observation in manifest['observations']:
        for pol in stacks:
            relative = observation['rasters'][pol].removeprefix('/cases/')
            with rasterio.open(Path(root)/'web/public/cases'/relative) as ds:
                stacks[pol].append(ds.read(1, window=window))
    stacks = {k: np.stack(v) for k, v in stacks.items()}
    result = profile(stacks, np.ones(stacks['hh'].shape[1:], dtype=bool), manifest['observations'],
                     manifest['reference_index'], f'Native neighborhood at row {row}, column {col}',
                     manifest['grid']['pixel_area_km2'])
    return {'case_id': case, 'version': VERSION, 'row': row, 'col': col,
            'window': [top, left, int(window.height), int(window.width)], 'profile': result,
            'interpretation': 'Intensity support only. No optical match, cause classification or coherence value inherited by this neighborhood.'}


def build_case(case, gcovs, gunws, destination, palettes):
    original_dir = ROOT/f'web/public/cases/{case}/investigation'
    original = load(original_dir/'manifest.json'); grid = original['grid']
    affine = Affine(*grid['affine']); shape = tuple(grid['shape']); crs = grid['crs']
    target = destination/case; target.mkdir()
    original_by_time = {o['timestamp']: o for o in original['observations']}
    records = sorted(gcovs, key=lambda r: parse_date(r['acquisition_start']))
    observations = []; arrays = {'hh': [], 'hv': []}
    for i, record in enumerate(records):
        t = timestamp(record['acquisition_start']); old = original_by_time.get(t)
        row = {'observation_id': 'acq_'+parse_date(t).strftime('%Y%m%dT%H%M%S'), 'timestamp': t,
               'source_granule_id': record['granule_id'], 'source_file': str(Path(record['source_file']).relative_to(ROOT)),
               'product_version': record['product_version'], 'processing_release': processing_release(record['granule_id']),
               'track': record['track'], 'frame': record['frame'], 'doi': record['doi'],
               'layers': {}, 'rasters': {}, 'quality': {}, 'preserved_original_observation': bool(old)}
        print(case, t, 'reuse preserved COG' if old else 'extract supplied acquisition', flush=True)
        for pol, term in [('hh', 'HHHH'), ('hv', 'HVHV')]:
            if old:
                p = original_dir/old['rasters'][pol]
                with rasterio.open(p) as ds:
                    if ds.transform != affine or ds.crs.to_string() != crs or ds.shape != shape:
                        raise ValueError('Preserved COG grid mismatch')
                    image = ds.read(1)
                row['rasters'][pol] = '/cases/'+case+'/investigation/'+old['rasters'][pol]
                row['quality'][pol] = {**old['quality'][pol], 'preserved_cog_sha256': sha(p)}
            else:
                source = {**record, 'covariance_term': term, 'polarization': term[:2], 'layer_path': record['grid_path']+'/'+term}
                image, quality = canonical_observation(source, affine, crs, shape, 3)
                fraction = float(np.isfinite(image).mean())
                if fraction < .8:
                    raise ValueError(f'{case} {t} {pol} coverage below 80%')
                p = target/f'{pol}_{i}.tif'; cog(p, image, affine, crs, pol.upper()+' median-filtered gamma-0 dB')
                row['rasters'][pol] = f'/cases/{case}/{VERSION}/'+p.name
                row['quality'][pol] = {**quality, 'valid_fraction': fraction}
            arrays[pol].append(image)
        observations.append(row)
    stacks = {k: np.stack(v) for k, v in arrays.items()}; del arrays
    reference_index = next(i for i, o in enumerate(observations) if o['timestamp'] == REFERENCE)
    for i, row in enumerate(observations):
        fields = {'hh': stacks['hh'][i], 'hv': stacks['hv'][i], 'cpr': stacks['hv'][i]-stacks['hh'][i],
                  'hh_reference': stacks['hh'][i]-stacks['hh'][reference_index],
                  'hv_reference': stacks['hv'][i]-stacks['hv'][reference_index],
                  'cpr_reference': (stacks['hv'][i]-stacks['hh'][i])-(stacks['hv'][reference_index]-stacks['hh'][reference_index])}
        if i: fields['hh_successive'] = stacks['hh'][i]-stacks['hh'][i-1]
        for name, a in fields.items():
            filename = f'{name}_{i}.png'
            preview(target/filename, palette_rgba(a, LIMITS[name], palettes['vik' if '_' in name else 'cividis']))
            row['layers'][name] = f'/cases/{case}/{VERSION}/'+filename
    evidence = load(ROOT/f'web/public/cases/{case}/evidence-v2/manifest.json')['profiles'][0]
    with rasterio.open(ROOT/f'web/public/cases/{case}/evidence-v2'/evidence['footprint_raster']['file']) as ds:
        footprint = np.zeros(shape, dtype='uint8')
        reproject(ds.read(1), footprint, src_transform=ds.transform, src_crs=ds.crs,
                  dst_transform=affine, dst_crs=crs, resampling=Resampling.nearest,
                  src_nodata=0, dst_nodata=0)
        footprint = footprint > 0
    profiles = [profile(stacks, footprint, observations, reference_index, evidence['profile']['label'], grid['pixel_area_km2']),
                profile(stacks, np.ones(shape, dtype=bool), observations, reference_index, 'Whole study crop · common-valid mean', grid['pixel_area_km2'])]
    cog(target/'tracked_footprint.tif', footprint.astype('uint8'), affine, crs, 'Preserved original footprint; not independent validation', 0, True)
    del stacks
    bounds = rasterio.transform.array_bounds(*shape, affine); pairs = []
    for number, (path, header) in enumerate(gunws):
        pair = {**header, 'pair_id': f'pair_{number}', 'layers': {}, 'rasters': {}, 'grids': {}, 'statistics': {}}
        with h5py.File(path, 'r') as f:
            for family, spacing, names in [
                ('wrappedInterferogram', 20, {'coherence': 'HH/coherenceMagnitude', 'mask': 'mask'}),
                ('unwrappedInterferogram', 80, {'coherence': 'HH/coherenceMagnitude', 'mask': 'mask',
                  'connected_components': 'HH/connectedComponents', 'phase_radians': 'HH/unwrappedPhase',
                  'ionosphere_radians': 'HH/ionospherePhaseScreen', 'ionosphere_uncertainty_radians': 'HH/ionospherePhaseScreenUncertainty'})]:
                group = f['science/LSAR/GUNW/grids/frequencyA/'+family]
                values, transform, epsg, window = native_window(group, bounds, names)
                if epsg != 32645 or abs(transform.a) != spacing:
                    raise ValueError('Unexpected native GUNW grid')
                valid = gunw_validity(values['coherence'], values['mask'])
                coherence = np.where(valid, values['coherence'], np.nan).astype('float32')
                pair['grids'][str(spacing)] = {'shape': list(coherence.shape), 'affine': list(transform)[:6],
                    'crs': 'EPSG:'+str(epsg), 'native_spacing_m': spacing,
                    'source_window': [int(window.row_off), int(window.col_off), int(window.height), int(window.width)],
                    'bounds': list(rasterio.transform.array_bounds(*coherence.shape, transform)),
                    'window_sha256': hashlib.sha256(b''.join(values[k].tobytes() for k in sorted(values))).hexdigest(),
                    'hash_content_order': sorted(values)}
                pair['statistics'][str(spacing)] = {'valid_pixels': int(valid.sum()), 'total_pixels': valid.size,
                    'valid_fraction': float(valid.mean()), 'mean_coherence': float(coherence[valid].astype('float64').mean()) if valid.any() else None,
                    'median_coherence': float(np.median(coherence[valid])) if valid.any() else None,
                    'below_03_pixels': int((valid & (coherence < .3)).sum()),
                    'below_03_note': 'Illustrative summary only; not a change, damage or phase-reliability classification.'}
                for name, array in {**values, 'coherence': coherence, 'coherence_valid': valid.astype('uint8')}.items():
                    p = target/f'gunw_{number}_{spacing}_{name}.tif'
                    integer = array.dtype.kind in 'ui'
                    nodata = (0 if name == 'coherence_valid' else np.iinfo(array.dtype).max) if integer else np.nan
                    cog(p, array, transform, 'EPSG:'+str(epsg), name+'; native GUNW; phase uncorrected, not displacement', nodata, integer)
                    pair['rasters'][f'{name}{spacing}'] = f'/cases/{case}/{VERSION}/'+p.name
                name = f'coherence{spacing}'; p = target/f'gunw_{number}_{name}.png'
                preview(p, palette_rgba(coherence, [0, 1], palettes['cividis']))
                pair['layers'][name] = f'/cases/{case}/{VERSION}/'+p.name
                if spacing == 80:
                    cc = values['connected_components']; phase_valid = valid & np.isfinite(values['phase_radians']) & (cc > 0) & (cc != 65535)
                    pair['phase_assessable_pixels'] = int(phase_valid.sum())
                    pair['connected_component_labels'] = np.unique(cc[phase_valid]).tolist()
                    cog(target/f'gunw_{number}_80_phase_assessable.tif', phase_valid.astype('uint8'), transform,
                        'EPSG:32645', 'Nonfill connected-component/phase/coherence support only; not displacement validation', 0, True)
        pair['los_displacement_cm'] = None; pairs.append(pair)
    manifest = {'schema_version': 1, 'version': VERSION, 'case_id': case, 'title': original['title'], 'grid': grid,
        'reference_timestamp': REFERENCE, 'reference_index': reference_index, 'observations': observations,
        'profiles': profiles, 'interferometry': pairs, 'display_limits': LIMITS,
        'palette_css': {k: css_gradient(v) for k, v in palettes.items()},
        'original_manifest_url': f'/cases/{case}/investigation/manifest.json',
        'original_manifest_sha256': sha(original_dir/'manifest.json'),
        'instrument_gap': {'start': '2026-07-27T22:03:25Z', 'end': '2026-08-10T00:55:27Z',
                           'unobservable_nominal_date': '2026-08-07', 'source': 'https://nisar-docs.asf.alaska.edu/availability-overview/'},
        'limitations': ['Actual visits only. August-7 outage remains unfilled; no interpolation or continuous duration is inferred.',
            'Reference is August 19, not the first expanded visit and not a verified undisturbed surface.',
            'All-visit support can differ from historical three-date support. Original findings and products remain accessible.',
            'Coherence is pairwise HH phase consistency, not displacement, damage, water truth or a unique physical cause.',
            '20 m and 80 m coherence have different averaging/support. Never compare them as the same estimator or upscale them as 10 m measurements.',
            'Unwrapped phase and ionosphere layers are retained as native downloads, without displacement conversion. Corrections/reference-point/unwrap validation remain pending.',
            'Existing optical matches, terrain controls and Change DNA remain scoped to their original visits; they are not silently assigned to new dates.',
            'No new Bangladesh, rainfall, thermal or independent validation input was supplied in this batch.'],
        'provenance': {'code_sha256': sha(Path(__file__)), 'input_inventory': 'reports/extra_2026_11_03/input_inventory.json',
            'source_organizations': ['NASA / ASF DAAC / JPL (USA)', 'ISRO (India)'],
            'raw_file_hash_scope': 'No full-file digest asserted. Native extraction hashes and exact source identities/sizes retained.',
            'gcov_compatibility': 'L2 PR P05023, v1.0.11, ascending track98/frame16, left-looking, frequencyA HH/HV 40MHz; same original 10m grid.'}}
    manifest['assets_sha256'] = {p.name: sha(p) for p in target.iterdir() if p.is_file()}
    save(target/'manifest.json', manifest)
    return {'case_id': case, 'title': original['title'], 'observations': len(observations), 'coherence_pairs': len(pairs),
            'manifest_url': f'/cases/{case}/{VERSION}/manifest.json'}


def run():
    public = ROOT/'web/public/cases'; targets = [public/c/VERSION for c in CASES]
    registry = public/(VERSION+'.json')
    if registry.exists() or any(p.exists() for p in targets):
        raise FileExistsError('Version already published; choose a new version before rebuilding')
    folder = ROOT/'database/extra datasets'; anchor = read_observation(ROOT/'aug19.h5')
    paths = [ROOT/p for p in ['aug19.h5', 'aug31.h5', 'sept12.h5']] + sorted(folder.glob('*_GCOV_*.h5'))
    gcovs = []; times = set()
    for path in paths:
        r = read_observation(path); issues = incompatibilities(anchor, r)
        if processing_release(r['granule_id']) != 'P05023' or set(r['covariance_terms']) != {'HHHH', 'HVHV'}:
            issues.append('Release or diagonal covariance schema mismatch')
        t = timestamp(r['acquisition_start'])
        if t in times: issues.append('Duplicate acquisition')
        if issues: raise ValueError(path.name+': '+ '; '.join(issues))
        r['source_file'] = str(path); gcovs.append(r); times.add(t)
    gunws = [(p, gunw_header(p, times)) for p in sorted(folder.glob('*_GUNW_*.h5'))]
    palettes = load_palettes(ROOT/'data/palettes/v1')
    with tempfile.TemporaryDirectory(prefix='.expanded-', dir=public) as tmp:
        temp = Path(tmp); rows = [build_case(c, gcovs, gunws, temp, palettes) for c in CASES]
        for case, target in zip(CASES, targets): shutil.move(str(temp/case), str(target))
        save(registry, {'schema_version': 1, 'version': VERSION, 'unique_gcov_granules': len(gcovs),
            'unique_gunw_granules': len(gunws), 'cases': rows,
            'scope': 'Additive Nepal extension. Bangladesh and original investigations remain preserved.'})
    print(rows, flush=True)


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args(); run()
