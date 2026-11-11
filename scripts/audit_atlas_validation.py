"""Audit descriptive references and guard future development/holdout splits."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.compute.atlas_admission import active_manifests, require_admitted
from src.compute.context_v2 import utc


def check_reference_split(units):
    """Reject shared scene/visit IDs, blocks and spatial exclusion buffers across splits."""
    development, holdout = [], []
    for row in units:
        if row['split'] not in ('development', 'holdout') or not row['sceneIds'] or not row['visitIds']:
            raise ValueError('Each unit needs an explicit split and all relevant scenes and visits')
        polygon = shape(row['bufferedGeometry'])
        if polygon.geom_type not in ('Polygon', 'MultiPolygon') or not polygon.is_valid or polygon.is_empty:
            raise ValueError('Each unit needs a valid buffered site geometry')
        (development if row['split'] == 'development' else holdout).append((row, polygon))
    for a, area_a in development:
        for b, area_b in holdout:
            if (a['blockId'] == b['blockId'] or set(a['sceneIds']) & set(b['sceneIds'])
                    or set(a['visitIds']) & set(b['visitIds']) or area_a.intersects(area_b)):
                raise ValueError('Development and holdout units leak a block, scene, visit or buffered site')
    return {'developmentUnits': len(development), 'holdoutUnits': len(holdout)}


def audit(root=ROOT):
    active = active_manifests(root)
    require_admitted(root, active)
    protocol = (root/'docs/ATLAS_VALIDATION_PROTOCOL.md').read_bytes()
    report = {'schemaVersion': 1, 'protocolSha256': sha256(protocol).hexdigest(),
              'status': 'insufficient_independent_evidence', 'validatedClaims': [],
              'heldOutLabels': 0, 'metrics': None, 'uncertaintyIntervals': None,
              'areaAdjustedKm2': None, 'exposureEstimate': None, 'cases': {}}
    for case, path in active.items():
        manifest = json.loads(path.read_text())
        current = report['cases'][case] = {
            'recordManifestSha256': sha256(path.read_bytes()).hexdigest(),
            'descriptiveReferenceRows': 0, 'matchedRows': 0, 'unavailableReasons': {},
            'independentLabels': 0, 'byObservation': {}, 'referenceLedger': [],
        }
        for visit in manifest['observations']:
            current['byObservation'][visit['observation_id']] = {
                'utc': visit['timestamp'], 'matched': 0, 'unavailable': 0, 'independentLabels': 0}
        if case not in ('jamuna_river', 'tanguar_wetland'):
            current['reason'] = 'No admitted independent label at expanded-record sites and dates. Historical references remain descriptive.'
            continue
        ref_path = path.parent.parent/'references-v1/manifest.json'
        ref = json.loads(ref_path.read_text())
        if ref['radar_manifest_sha256'] != current['recordManifestSha256']:
            raise ValueError('Optical receipt is bound to a different radar record')
        current['referenceManifestSha256'] = sha256(ref_path.read_bytes()).hexdigest()
        failures = Counter()
        seen = set()
        for row in ref['results']:
            obs_id = row['observation_id']
            key = (obs_id, row['footprint_id'])
            by_obs = current['byObservation'][obs_id]
            if key in seen or row['case_id'] != case or row['radar_timestamp'] != by_obs['utc']:
                raise ValueError('Duplicate or mismatched reference unit')
            seen.add(key)
            current['descriptiveReferenceRows'] += 1
            eligible = row['clear_assessable_pixels']
            reference_utc = row['reference_timestamp']
            offset = (utc(reference_utc)-utc(by_obs['utc'])).total_seconds() if reference_utc else None
            if eligible:
                current['matchedRows'] += 1
                by_obs['matched'] += 1
                reason = 'Descriptive HLS overlap; excluded from holdout'
            else:
                reason = 'No eligible clear support' if reference_utc else 'No matched scene'
                failures[reason] += 1
                by_obs['unavailable'] += 1
            current['referenceLedger'].append({
                'observationId': obs_id, 'footprintId': row['footprint_id'],
                'referenceId': row['reference_id'], 'referenceUtc': reference_utc,
                'offsetSeconds': offset, 'clearAssessablePixels': eligible,
                'totalReferencePixels': row.get('reference_pixels'), 'status': row['status'],
                'adjudication': reason, 'holdout': False,
            })
        current['unavailableReasons'] = dict(failures)
    return report


if __name__ == '__main__':
    target = ROOT/'reports/development/part-13-validation-status.json'
    target.write_text(json.dumps(audit(), indent=2, allow_nan=False)+'\n')
    print(target)
