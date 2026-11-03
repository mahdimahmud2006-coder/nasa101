"""Build a self-contained local-runtime release with explicit file hashes and no raw HDF5/secrets."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import argparse,re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.api.readiness import readiness

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def files(root):
    # Explicit allowlist: no home folders, environment files, Git metadata or raw granules.
    paths=[]
    for folder in ['src','web','tests','docs','rules','claims','reference','scripts']:
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.zip','.h5','.hdf5','.pem','.key') and not p.name.startswith('.env') and p.name!='release_package_qa.json')
    paths.extend(p for p in root.glob('config*.json') if p.is_file())
    ledger=root/'claims/claims.yaml'
    if ledger.is_file():
        for claim in json.loads(ledger.read_text())['claims']:
            evidence=(root/claim['evidence_path']).resolve()
            if not evidence.is_relative_to(root.resolve()) or evidence.suffix not in ['.json','.md','.py','.mjs','.yaml']:raise ValueError('Unsafe/unsupported claim evidence path')
            paths.append(evidence)
    for name in ['data/context/context-v2/terrain/sources.json','data/references/v1/hls-v2/sources.json','data/references/v1/hls-v2/results.json']:
        p=root/name
        if p.is_file():paths.append(p)
    for name in ['input_inventory.json','source_header_audit.json','original_preservation.json','verification_preservation.json']:
        p=root/'reports/extra_2026_11_03'/name
        if p.is_file():paths.append(p)
    for name in ['source_audit.json','covariance_inventory.json','native_validation.json','build.json','activation.json','lineage_review.json']:
        p=root/'reports/bangladesh_import_2026_11_03'/name
        if p.is_file():paths.append(p)
    for name in ['README.md','PROJECT_PROGRESS.md','RELEASE_README.md','LICENSE','requirements.txt','pyproject.toml','Makefile','run.sh','scripts/package_release.py','scripts/verify_release.py','scripts/check_web.py']:
        paths.append(root/name)
    # Runtime counterfactuals use this local component cube, not raw satellites or live APIs.
    for name in ['manifest.json','model.json','components.npz']:
        paths.append(root/'data/derived/nepal_case_01/flood'/name)
    paths.extend((root/'data/derived/nepal_case_01/flood/scenarios').glob('*/result.json'))
    return sorted(set(paths))


def build(root=ROOT,release_id='phase7-20261103-r2'):
    root=Path(root);status=readiness(root)
    if not status['runtime_ready']:raise RuntimeError('Cannot package an incomplete local runtime')
    paths=files(root);records={str(p.relative_to(root)):digest(p) for p in paths}
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,60}',release_id):raise ValueError('Invalid release identifier')
    manifest={'project':status,'release_id':release_id,'files_sha256':records,'packaging_scope':'Local application, current rules/claims, reference design and analytical viewer assets, with the flood runtime component cube. Raw NISAR, NASADEM/Landsat source caches and full offline source reprocessing inputs are not bundled.',
        'scientific_reproduction':'Full-source validators and rebuilding require the separately retained source datasets described in DATASETS.md; runtime integrity can be checked with scripts/verify_release.py.',
        'no_credentials_bundled':True}
    directory=root/'dist';directory.mkdir(exist_ok=True);target=directory/f'terrapulse-{status["version"]}-{release_id}.zip';temporary=target.with_suffix('.zip.tmp')
    if target.exists():raise FileExistsError('Release already exists; choose a new --release-id to preserve it')
    def write(archive,name,content,mode=0o644):
        info=zipfile.ZipInfo(name,(2026,11,3,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100000|mode)<<16
        archive.writestr(info,content,compresslevel=6)
    with zipfile.ZipFile(temporary,'w') as archive:
        for path in paths:
            content=path.read_bytes();name=str(path.relative_to(root))
            if hashlib.sha256(content).hexdigest()!=records[name]:raise RuntimeError('Source changed while packaging: '+name)
            write(archive,name,content,0o755 if path.name=='run.sh' else 0o644)
        write(archive,'RELEASE_MANIFEST.json',(json.dumps(manifest,indent=2)+'\n').encode())
    from scripts.verify_release import verify_archive
    check=verify_archive(temporary)
    if not check['verified']:raise RuntimeError(check)
    temporary.replace(target);archive_digest=digest(target)
    (directory/(target.name+'.sha256')).write_text(archive_digest+'  '+target.name+'\n')
    print(json.dumps({'archive':str(target),'files':len(paths),'bytes':target.stat().st_size,'sha256':archive_digest},indent=2))
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--release-id',default='phase7-20261103-r2');args=parser.parse_args();build(release_id=args.release_id)
