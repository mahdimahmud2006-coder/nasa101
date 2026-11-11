import hashlib
import json
from pathlib import Path

import h5py
import pytest

from src.compute.atlas_admission import candidate_gate, require_admitted
from src.compute.atlas_contract import binding
from scripts.audit_imerg_catalog import windows
from scripts.audit_atlas_inputs import intersects
from scripts.audit_phase7 import request

ROOT=Path(__file__).resolve().parents[1]


def test_admission_rejects_a_new_record_without_explicit_review(tmp_path):
    case='test_case'
    manifest=tmp_path/'web/public/cases/test/manifest.json'
    manifest.parent.mkdir(parents=True)
    m={'case_id':case,'version':'accepted-v1','grid':{'crs':'EPSG:32645','shape':[2,2],'affine':[10,0,0,0,-10,0]}}
    manifest.write_text(json.dumps(m))
    report=tmp_path/'reports/development/test.json'
    report.parent.mkdir(parents=True)
    accepted={**binding(case,manifest),'path':str(manifest.relative_to(tmp_path))}
    report.write_text(json.dumps({'accepted_manifest_bindings':{case:accepted}}))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    policy={'schemaVersion':1,'auditReport':str(report.relative_to(tmp_path)), 'auditSha256':digest(report),
            'supportingManifests':{},'cases':{case:{'status':'accepted','binding':{**binding(case,manifest),'path':str(manifest.relative_to(tmp_path))}}}}
    (tmp_path/'config.atlas-admission.json').write_text(json.dumps(policy))
    require_admitted(tmp_path,{case:manifest})
    m['version']='unreviewed-v2'
    manifest.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='not explicitly admitted'):
        require_admitted(tmp_path,{case:manifest})
    policy['cases'][case]['binding']={**binding(case,manifest),'path':accepted['path']}
    (tmp_path/'config.atlas-admission.json').write_text(json.dumps(policy))
    with pytest.raises(ValueError,match='not explicitly admitted'):
        require_admitted(tmp_path,{case:manifest})


def test_candidate_failures_stay_out_of_the_accepted_record(tmp_path):
    complete=tmp_path/'source.h5'
    with h5py.File(complete,'w') as file:file['pixels']=[0,1,2]
    truncated=tmp_path/'truncated.h5'
    truncated.write_bytes(complete.read_bytes()[:32])
    with pytest.raises(OSError):
        with h5py.File(truncated,'r'):pass
    assert candidate_gate(header_ok=False,actual_bytes=truncated.stat().st_size,
                          expected_bytes=complete.stat().st_size,lineage='approved',overlap=True)[0]=='rejected'
    assert candidate_gate(track=149,frame=73,expected_track=98,expected_frame=16,header_ok=True)[0]=='rejected'
    assert candidate_gate(lineage='unverified',header_ok=True,overlap=True)[0]=='excluded'
    overlaps=intersects([89.6,24.3,89.8,24.6],'POLYGON((90 25, 91 25, 91 26, 90 26, 90 25))')
    assert candidate_gate(header_ok=True,lineage='approved',overlap=overlaps)[0]=='rejected'
    assert candidate_gate(header_ok=True,lineage='approved',overlap=True)[0]=='audited'


def test_rainfall_windows_match_saved_source_and_crop_scope():
    r=json.loads((ROOT/'web/atlas-record.json').read_text())
    rows=windows(r)
    catalog=json.loads((ROOT/'reports/development/part-03-imerg-catalog.json').read_text())
    assert len(rows)==20
    assert all(len(w['footprints'])==2 and len(w['expected_bin_starts'])==97 for w in rows)
    for w,saved in zip(rows,catalog['windows'],strict=True):
        assert w=={k:v for k,v in saved.items() if k!='catalog'}
    assert not any(r['end_utc'].startswith(('2026-08-05','2026-08-07')) for r in rows)


@pytest.mark.parametrize('case,path,body,kind',[
    ('jamuna_river','investigation-reasoning?row=600&col=500',None,'point'),
    ('jamuna_river','investigation-polygon',{'vertices':[[600,500],[611,500],[611,511],[600,511]]},'polygon'),
    ('nepal_surface','expanded-probe?row=1000&col=1000',None,'point')
])
def test_actual_native_endpoint_matches_active_catalog(case,path,body,kind):
    status,raw=request(f'/api/cases/{case}/{path}',body)
    assert status==200
    record=json.loads(raw);catalog=json.loads((ROOT/'web/atlas-contract-records.json').read_text())[case]
    assert record['atlasBinding']['selection']['kind']==kind
    for key in ('caseId','recordVersion','manifestSha256','gridId'):
        assert record['atlasBinding'][key]==catalog[key]
    assert [r['observation_id'] for r in record['profile']['observations']]==[r['id'] for r in catalog['observations']]
