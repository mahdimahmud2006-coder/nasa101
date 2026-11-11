"""Fail closed on unreviewed inputs to the atlas build."""
import json
from hashlib import sha256
from pathlib import Path

from src.compute.active_records import case_directory, registry_path
from src.compute.atlas_contract import binding


def active_manifests(root):
    root=Path(root)
    public=root/'web/public'
    registry=json.loads(registry_path(root).read_text())
    result={r['case_id']:case_directory(r['case_id'],root)/'investigation/manifest.json'
            for r in registry['cases'] if r['case_id'] in ('jamuna_river','tanguar_wetland')}
    for r in json.loads((public/'cases/expanded-v1.json').read_text())['cases']:
        p=(public/r['manifest_url'].lstrip('/')).resolve()
        if not p.is_relative_to((public/'cases').resolve()):
            raise ValueError('Expanded manifest outside the approved case directory')
        result[r['case_id']]=p
    return result


def require_admitted(root, paths):
    """Check explicit approvals before an atlas record is written or verified."""
    root=Path(root).resolve()
    policy=json.loads((root/'config.atlas-admission.json').read_text())
    if policy['schemaVersion']!=1 or paths.keys()!=policy['cases'].keys():
        raise ValueError('Active atlas cases differ from the reviewed case set')
    evidence=(root/policy['auditReport']).resolve()
    if not evidence.is_relative_to((root/'reports/development').resolve()) or not evidence.is_file():
        raise ValueError('Missing atlas admission evidence')
    if sha256(evidence.read_bytes()).hexdigest()!=policy['auditSha256']:
        raise ValueError('Atlas admission evidence was changed without review')
    audited=json.loads(evidence.read_text())['accepted_manifest_bindings']
    for name,digest in policy['supportingManifests'].items():
        p=(root/name).resolve()
        if not p.is_relative_to((root/'web/public/cases').resolve()) or not p.is_file() or sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError('Supporting atlas evidence is missing or unreviewed: '+name)
    for case,p in paths.items():
        row=policy['cases'][case]
        actual={**binding(case,p),'path':p.resolve().relative_to(root).as_posix()}
        if row['status']!='accepted' or row['binding']!=actual or audited.get(case)!=actual:
            raise ValueError(f'{case}: active record is not explicitly admitted; stage a new version and validation receipt')


def admitted_pairs(root, path, manifest):
    """Load pairs embedded in the radar record or in a separately admitted supplement."""
    root = Path(root).resolve()
    path = Path(path).resolve()
    supplement = path.parent.parent/'coherence-v1/manifest.json'
    policy = json.loads((root/'config.atlas-admission.json').read_text())
    checksum = policy['supportingManifests'].get(supplement.relative_to(root).as_posix())
    if checksum is None:
        return manifest.get('interferometry', [])
    raw = supplement.read_bytes()
    data = json.loads(raw)
    if (sha256(raw).hexdigest() != checksum or data['schema_version'] != 1
            or data['case_id'] != manifest['case_id']
            or data['radar_manifest_sha256'] != sha256(path.read_bytes()).hexdigest()):
        raise ValueError('Coherence supplement does not match the admitted radar record')
    return data['interferometry']


def candidate_gate(*, track=None, frame=None, expected_track=None, expected_frame=None,
                   header_ok=None, actual_bytes=None, expected_bytes=None, lineage='unverified', overlap=None):
    """Classify review inputs, never activate an audited candidate automatically."""
    if expected_track is not None and (track,frame)!=(expected_track,expected_frame):
        return 'rejected','Incompatible track/frame'
    if header_ok is False or (actual_bytes is not None and expected_bytes is not None and actual_bytes!=expected_bytes):
        return 'rejected','Unreadable header or size differs from expected complete file'
    if overlap is False:
        return 'rejected','Source has no overlap with the requested footprint'
    if lineage!='approved':
        return 'excluded','Upstream lineage does not pass the provider policy'
    if header_ok is not True or overlap is not True:
        return 'listed','Header and footprint checks not completed'
    return 'audited','Header, lineage and footprint gate passed; release approval still required'
