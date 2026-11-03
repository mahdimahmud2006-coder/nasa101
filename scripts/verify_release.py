"""Verify a release's exact runtime files with only the Python standard library."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def verify(root):
    root=Path(root).resolve();manifest=json.loads((root/'RELEASE_MANIFEST.json').read_text());problems=[]
    for filename,expected in manifest['files_sha256'].items():
        path=(root/filename).resolve()
        if not path.is_relative_to(root):raise ValueError('Invalid release manifest path')
        if not path.is_file():problems.append('Missing: '+filename);continue
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected:problems.append('Hash mismatch: '+filename)
    return {'verified':not problems,'files_checked':len(manifest['files_sha256']),'problems':problems,
        'scope':'Packaged source and runtime integrity, not independent scientific or browser validation'}

def verify_archive(path):
    problems=[]
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):problems.append('Duplicate archive paths')
        if any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):problems.append('Unsafe archive paths')
        manifest=json.loads(archive.read('RELEASE_MANIFEST.json'));expected=manifest['files_sha256']
        if set(names)!=set(expected)|{'RELEASE_MANIFEST.json'}:problems.append('Archive inventory differs from manifest')
        for name,digest in expected.items():
            if name not in names:problems.append('Missing: '+name);continue
            with archive.open(name) as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
            if actual!=digest:problems.append('Hash mismatch: '+name)
    return {'verified':not problems,'files_checked':len(expected),'problems':problems,'scope':'Every archive entry streamed and hashed, without extraction. Not a clean-machine/browser/offline rehearsal.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--archive',type=Path);args=parser.parse_args();result=verify_archive(args.archive) if args.archive else verify(args.root);print(json.dumps(result,indent=2));raise SystemExit(0 if result['verified'] else 1)
