"""Extract observed Bangladesh coherence pairs on their original GUNW grids."""
import hashlib
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from affine import Affine
from rasterio.transform import array_bounds

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_admission import active_manifests
from src.compute.expanded_record import cog, gunw_header, gunw_validity, native_window, preview
from src.export.dualpol_render import load_palettes, palette_rgba

SOURCE = ROOT/'database/extra datasets/jamuna-ground-motion'
PUBLIC = ROOT/'web/public'


def file_sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def extract_pair(source, header, destination, grid, palette, source_receipt):
    pair_id = 'gunw_'+header['timestamps'][-1][:10].replace('-', '')
    pair = {**header, 'pair_id': pair_id, 'source_sha256': source_receipt['sha256'],
            'source_url': source_receipt['url'], 'source_concept_id': source_receipt['granule_concept_id'],
            'layers': {}, 'rasters': {}, 'grids': {}, 'statistics': {}}
    bounds = array_bounds(*grid['shape'], Affine(*grid['affine']))
    with h5py.File(source) as file:
        freq = file['science/LSAR/GUNW/grids/frequencyA']
        for spacing, family in [(20, 'wrappedInterferogram'), (80, 'unwrappedInterferogram')]:
            group = freq[family]
            names = {'coherence': 'HH/coherenceMagnitude', 'mask': 'mask'}
            if spacing == 80:
                names.update(phase='HH/unwrappedPhase', components='HH/connectedComponents')
            values, transform, epsg, window = native_window(group, bounds, names)
            crs = f'EPSG:{epsg}'
            if crs != grid['crs'] or transform.a != spacing:
                raise ValueError('Unexpected native coherence grid')
            valid = gunw_validity(values['coherence'], values['mask'])
            if not valid.any():
                raise ValueError('No valid coherence samples in the study window')
            coherence = np.where(valid, values['coherence'], np.nan).astype('float32')
            pair['grids'][str(spacing)] = {
                'shape': list(coherence.shape), 'affine': list(transform)[:6], 'crs': crs,
                'native_spacing_m': spacing, 'bounds': list(array_bounds(*coherence.shape, transform)),
                'source_window': [int(v) for v in (window.row_off, window.col_off, window.height, window.width)],
            }
            pair['statistics'][str(spacing)] = {
                'valid_pixels': int(valid.sum()), 'total_pixels': valid.size,
                'mean_coherence': float(coherence[valid].mean(dtype='float64')),
                'median_coherence': float(np.median(coherence[valid])),
            }
            for name, array, nodata in [('coherence', coherence, np.nan), ('mask', values['mask'], 2**32-1),
                                       ('coherence_valid', valid.astype('uint8'), 0)]:
                key = f'{name}{spacing}'
                path = destination/f'{pair_id}_{key}.tif'
                cog(path, array, transform, crs, f'Native GUNW {name}, {spacing} m', nodata, name != 'coherence')
                pair['rasters'][key] = '/'+path.relative_to(PUBLIC).as_posix()
            key = f'coherence{spacing}'
            path = destination/f'{pair_id}_{key}.png'
            preview(path, palette_rgba(coherence, [0, 1], palette))
            pair['layers'][key] = '/'+path.relative_to(PUBLIC).as_posix()
            if spacing == 80:
                labels = values['components']
                eligible = valid & np.isfinite(values['phase']) & (labels > 0) & (labels != 65535)
                pair['phase_assessable_pixels'] = int(eligible.sum())
                pair['connected_component_labels'] = np.unique(labels[eligible]).tolist()
    return pair


def build():
    receipts = json.loads((SOURCE/'jamuna-ground-motion-downloads.json').read_text())['sources']
    sources = []
    for entry in sorted(receipts, key=lambda row: row['matched_acquisition_utc']):
        path = SOURCE/entry['file']
        if path.parent != SOURCE or file_sha256(path) != entry['sha256']:
            raise ValueError('Downloaded file differs from the verified source receipt')
        sources.append((path, entry))
    palette = load_palettes(ROOT/'data/palettes/v1')['cividis']
    for case, path in active_manifests(ROOT).items():
        if case not in ('jamuna_river', 'tanguar_wetland'):
            continue
        manifest = json.loads(path.read_text())
        visits = {row['timestamp']: row['source_granule_id'] for row in manifest['observations']}
        destination = path.parent.parent/'coherence-v1'
        destination.mkdir(exist_ok=True)
        pairs = []
        for source, receipt in sources:
            header = gunw_header(source, visits, track=69, frame=14)
            for utc, granules in zip(header['timestamps'], header['source_slc_granules']):
                expected = visits[utc].replace('_L2_PR_GCOV_', '_L1_PR_RSLC_')
                if Path(granules[0]).stem != expected:
                    raise ValueError('Pair source differs from the loaded acquisition')
            pairs.append(extract_pair(source, header, destination, manifest['grid'], palette, receipt))
        assets = [asset for pair in pairs for field in ('layers', 'rasters') for asset in pair[field].values()]
        record = {'schema_version': 1, 'case_id': case, 'radar_manifest_sha256': file_sha256(path),
                  'interferometry': pairs, 'asset_sha256': {
                      asset: file_sha256(PUBLIC/asset.lstrip('/')) for asset in assets}}
        (destination/'manifest.json').write_text(json.dumps(record, indent=2, allow_nan=False)+'\n')
        print(case, [pair['timestamps'] for pair in pairs])


if __name__ == '__main__':
    build()
