"""Inventory admitted GUNW phase and baseline metadata without estimating motion."""
import json
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.constants import c as LIGHT_SPEED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_admission import active_manifests, admitted_pairs, require_admitted
from src.compute.atlas_contract import binding
from src.compute.expanded_record import gunw_header


def phase_inventory(root=ROOT):
    paths = active_manifests(root)
    require_admitted(root, paths)
    cases = {}
    for case, path in paths.items():
        manifest = json.loads(path.read_text())
        pairs = {}
        for pair in admitted_pairs(root, path, manifest):
            source = (root/pair['source_file']).resolve()
            if not source.is_relative_to(root.resolve()):
                raise ValueError('Source outside workspace')
            visit = manifest['observations'][0]
            header = gunw_header(source, {o['timestamp'] for o in manifest['observations']},
                                 track=visit['track'], frame=visit['frame'])
            if any(header[key] != pair[key] for key in ('identification', 'timestamps', 'source_slc_granules', 'size_bytes')):
                raise ValueError('GUNW header differs from accepted pair')
            with h5py.File(source) as file:
                gunw = file['science/LSAR/GUNW']
                freq = gunw['grids/frequencyA']
                geometry = gunw['metadata/radarGrid']
                x1, y1, x2, y2 = pair['grids']['20']['bounds']
                x = int(np.abs(geometry['xCoordinates'][:]-(x1+x2)/2).argmin())
                y = int(np.abs(geometry['yCoordinates'][:]-(y1+y2)/2).argmin())
                z = int(np.abs(geometry['heightAboveEllipsoid'][:]).argmin())
                baseline = float(geometry['perpendicularBaseline'][z, y, x])
                columns = np.flatnonzero((geometry['xCoordinates'][:] >= x1) & (geometry['xCoordinates'][:] <= x2))
                rows = np.flatnonzero((geometry['yCoordinates'][:] >= y1) & (geometry['yCoordinates'][:] <= y2))
                samples = geometry['perpendicularBaseline'][z, rows[0]:rows[-1]+1, columns[0]:columns[-1]+1]
                finite = samples[np.isfinite(samples)]
                flags = gunw['metadata/processingInformation/parameters/geocoding']
                unwrapped = freq['unwrappedInterferogram/HH']
                pairs[pair['pair_id']] = {
                    'sourceId': header['identification']['granuleId'],
                    'frequencyHz': float(freq['centerFrequency'][()]),
                    'wavelengthM': LIGHT_SPEED / float(freq['centerFrequency'][()]),
                    'postingM': pair['grids']['80']['native_spacing_m'],
                    'phaseUnits': unwrapped['unwrappedPhase'].attrs['units'].decode(),
                    'phaseAssessablePixels': pair['phase_assessable_pixels'],
                    'connectedComponentLabels': pair['connected_component_labels'],
                    'temporalBaselineDays': int(gunw['metadata/orbit/temporalBaseline'][()]),
                    'sampledPerpendicularBaselineM': baseline if np.isfinite(baseline) else None,
                    'baselineRangeM': [float(finite.min()),float(finite.max())] if finite.size else None,
                    'baselineSampleCount': int(finite.size),
                    'baselineSample': [float(geometry[key][index]) for key, index in
                                       [('xCoordinates', x), ('yCoordinates', y), ('heightAboveEllipsoid', z)]],
                    'geocodingFlags': {k: flags[k][()].decode() for k in flags if k.endswith('CorrectionApplied')},
                    'availablePhaseLayers': [k for k in ('unwrappedPhase', 'connectedComponents',
                        'ionospherePhaseScreen', 'ionospherePhaseScreenUncertainty') if k in unwrapped],
                    'correctionLUTs': [k for k in geometry if k.endswith('Phase') or k.endswith('PhaseScreen')],
                    'geometryLUTs': [k for k in geometry if k.startswith('losUnitVector') or k == 'incidenceAngle'],
                }
        cases[case] = {'manifestSha256': binding(case,path)['manifestSha256'], 'pairs': pairs}
    return {
        'schemaVersion': 1, 'status': 'no_go', 'cases': cases,
        'phaseSign': 'Release-specific phase-to-LOS sign and projection convention need independent verification.',
        'reference': 'Stable reference and control points in common reliable components have not been established.',
        'corrections': 'Geocoding flags describe source processing. ASF documents that external phase screens are not removed from interferometric data. Product-specific phase handling, including the separate ionosphere layer, needs verification before applying corrections or estimating residual uncertainty.',
        'benchmark': 'No admitted time-matched GNSS or other independent motion benchmark.',
        'requiredChecks': ['Resolve correction application and sign against the product version.',
                           'Demonstrate stable-reference residuals, component consistency and uncertainty.',
                           'Compare against independent motion projected into the same LOS.'],
    }


if __name__ == '__main__':
    receipt = ROOT/'reports/development/part-12-los-feasibility.json'
    receipt.write_text(json.dumps(phase_inventory(), indent=2, allow_nan=False)+'\n')
    print(receipt)
