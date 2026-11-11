import hashlib
import json
from pathlib import Path
from src.api.readiness import readiness
from scripts.verify_release import verify
from scripts.package_release import files
from scripts.verify_release import verify_archive
import zipfile


def test_readiness_reports_missing_runtime_without_fabricating_ready(tmp_path):
    result=readiness(tmp_path)
    assert not result['runtime_ready'] and result['missing_runtime_files']
    assert result['landslide_validation_status']=='UNAVAILABLE'


def test_release_hash_verifier_detects_tampering(tmp_path):
    (tmp_path/'asset').write_bytes(b'original')
    (tmp_path/'RELEASE_MANIFEST.json').write_text(json.dumps({'files_sha256':{'asset':hashlib.sha256(b'original').hexdigest()}}))
    assert verify(tmp_path)['verified']
    (tmp_path/'asset').write_bytes(b'changed');assert not verify(tmp_path)['verified']


def test_package_allowlist_excludes_credentials_raw_satellites_and_git(tmp_path):
    (tmp_path/'web').mkdir();(tmp_path/'web/index.html').write_text('page')
    (tmp_path/'.env').write_text('sensitive');(tmp_path/'raw.h5').write_bytes(b'raw')
    (tmp_path/'.git').mkdir();(tmp_path/'.git/config').write_text('git')
    (tmp_path/'docs').mkdir();(tmp_path/'docs/VIDEO_STORYBOARD.md').write_text('local notes')
    names={str(p.relative_to(tmp_path)) for p in files(tmp_path)}
    assert 'web/index.html' in names
    assert not any(name in names for name in ['.env','raw.h5','.git/config','docs/VIDEO_STORYBOARD.md'])

def test_current_runtime_rules_claims_and_shared_shell_are_packaged():
    root=Path(__file__).resolve().parents[1];names={str(p.relative_to(root)) for p in files(root)}
    assert {'docs/CREDITS_UI.md','contracts/atlas-case-v1.schema.json','rules/explanations.yaml','claims/claims.yaml','config.claims.json','web/workspace-shell.mjs','web/investigation-state.mjs','reference/design.json','web/expanded.html','web/expanded.mjs','web/public/cases/expanded-v1.json','web/public/cases/supplied-source-audit-v1.json'}.issubset(names)
    assert not any(n.endswith(('.h5','.pem','.key')) or '/.env' in n for n in names)

def test_archive_integrity_checks_every_entry_without_extracting(tmp_path):
    p=tmp_path/'release.zip';content=b'local runtime'
    with zipfile.ZipFile(p,'w') as z:
        z.writestr('asset',content);z.writestr('RELEASE_MANIFEST.json',json.dumps({'files_sha256':{'asset':hashlib.sha256(content).hexdigest()}}))
    assert verify_archive(p)['verified']
    with zipfile.ZipFile(p,'a') as z:z.writestr('unexpected','bad')
    assert not verify_archive(p)['verified']
