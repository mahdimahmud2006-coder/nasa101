"""Write or verify an immutable processed-output SHA-256 baseline from the repo root.

Default roots include analytical products, viewer assets, historical reports, release
artifacts, and top-level scientific media. Raw sources, code, prose and environments
are excluded. New paths added after a freeze are permitted; frozen files must match.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT_ROOTS=('data/derived','web/public','docs/reports','dist','reports')
MEDIA={'.png','.jpg','.jpeg','.webp','.svg','.pdf'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def output_paths(root,manifest):
    excluded={manifest.resolve(),manifest.with_suffix('.scope.json').resolve()}
    paths={p for folder in OUTPUT_ROOTS for p in (root/folder).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'
           and p.resolve() not in excluded}
    paths.update(p for p in (root/'docs').glob('*') if p.is_file() and p.suffix.lower() in (MEDIA|{'.json'}))
    return sorted(paths,key=lambda p:p.relative_to(root).as_posix())


def freeze(root,manifest):
    if manifest.exists():
        raise FileExistsError('Baseline already exists. Verify it; never replace the frozen baseline.')
    paths=output_paths(root,manifest)
    records=[(digest(p),p.relative_to(root).as_posix()) for p in paths]
    if any('\n' in name or '\\' in name for _,name in records):
        raise ValueError('Unsupported path characters for portable sha256sum manifest')
    manifest.parent.mkdir(parents=True,exist_ok=True)
    with manifest.open('x') as stream:
        stream.write('# TerraPulse processed-output baseline; created for Phase 0, 2026-11-02 Asia/Dhaka.\n')
        stream.write('# Run from repository root: sha256sum --check reports/baseline_2026_11_02.sha256\n')
        for checksum,name in records:stream.write(f'{checksum}  {name}\n')
    scope={'date_local':'2026-11-02','timezone':'Asia/Dhaka','files':len(paths),'bytes':sum(p.stat().st_size for p in paths),
           'output_roots':list(OUTPUT_ROOTS),'additional_scope':'Top-level docs scientific media and JSON outputs; phase evidence under reports is included.',
           'excluded':'Raw HDF5/source caches, src/web code and configuration, documentation prose, virtual environments, Git metadata, this manifest and its scope sidecar.',
           'preservation_policy':'Every listed file must remain byte-identical. New files outside this list may be added. Preserve existing validator timing reports while keeping fresh logs separately.',
           'manifest_sha256':digest(manifest)}
    manifest.with_suffix('.scope.json').write_text(json.dumps(scope,indent=2)+'\n')
    return scope


def verify(root,manifest):
    checked=0;failed=[]
    for line in manifest.read_text().splitlines():
        if not line or line.startswith('#'):continue
        checksum,name=line.split('  ',1)
        target=root/name
        if not target.is_file() or digest(target)!=checksum:failed.append(name)
        checked+=1
    return {'verified':not failed,'checked_files':checked,'mismatches':failed}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=Path('reports/baseline_2026_11_02.sha256'))
    parser.add_argument('--check',action='store_true');args=parser.parse_args()
    manifest=ROOT/args.manifest
    result=verify(ROOT,manifest) if args.check else freeze(ROOT,manifest)
    print(json.dumps(result,indent=2))
    if args.check and not result['verified']:raise SystemExit(1)
