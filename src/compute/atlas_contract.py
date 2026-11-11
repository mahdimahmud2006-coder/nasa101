"""Stable atlas record and grid identifiers for producers and native responses."""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def grid_identity(case_id, grid):
    geometry = {k:grid[k] for k in ('crs', 'shape', 'affine')}
    return {'id': 'grid:'+digest([case_id,geometry]), **geometry}


def binding(case_id, path):
    raw = path.read_bytes()
    m = json.loads(raw)
    if m.get('case_id') != case_id:
        raise ValueError('Wrong case manifest for native measurement')
    return {'caseId':case_id, 'recordVersion':m.get('record_version',m.get('version','original')),
            'manifestSha256':hashlib.sha256(raw).hexdigest(), 'gridId':grid_identity(case_id,m['grid'])['id']}
