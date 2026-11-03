"""Restore checked runtime data for a source checkout; standard-library only.

Uses authenticated GitHub CLI for private releases. Credentials never enter a
manifest or archive. Existing conflicting project files are never overwritten.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile,urllib.request,urllib.error,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def destination(root,name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name:raise ValueError('Unsafe runtime path')
    allowed=name.startswith('web/public/cases/') and p.suffix.lower() in {'.png','.webp','.tif','.tiff'}
    if not allowed and name!='data/derived/nepal_case_01/flood/components.npz':raise ValueError('Unexpected runtime destination')
    target=(root/name).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Runtime path escapes project')
    return target

def download(asset,manifest,cache):
    name=asset['name'];path=cache/name
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.zip',name):raise ValueError('Unsafe runtime asset name')
    if path.exists():
        if digest(path)==asset['sha256']:return path
        raise ValueError('Cached asset checksum mismatch; remove the conflicting runtime-downloads file and retry')
    repository=manifest['repository'];release=manifest['release']
    if repository!='mahdimahmud2006-coder/nasa101' or not re.fullmatch(r'[A-Za-z0-9_.-]+',release):raise ValueError('Unexpected runtime origin')
    print('Downloading',name,flush=True)
    if shutil.which('gh'):
        result=subprocess.run(['gh','release','download',release,'--repo',repository,'--pattern',name,'--dir',str(cache)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError('GitHub download failed. For this private repository run gh auth login and request repository access, then retry.')
    else:
        url=f'https://github.com/{repository}/releases/download/{release}/{name}'
        try:
            with urllib.request.urlopen(url,timeout=60) as source,path.open('wb') as output:shutil.copyfileobj(source,output,1024*1024)
        except (urllib.error.URLError,TimeoutError) as error:
            path.unlink(missing_ok=True)
            raise RuntimeError('Cannot download runtime assets. Private repositories require GitHub CLI (gh auth login) and authorized access.') from error
    if path.stat().st_size!=asset['bytes'] or digest(path)!=asset['sha256']:raise ValueError('Downloaded runtime asset failed integrity check')
    return path

def install_archive(archive,files,root):
    wanted={}
    for name,row in files.items():wanted.setdefault(row['sha256'],[]).append((destination(root,name),row))
    restored=0
    with zipfile.ZipFile(archive) as source:
        names=source.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate runtime objects')
        for name in names:
            if not re.fullmatch(r'objects/[0-9a-f]{64}',name):raise ValueError('Unsafe archive entry')
            key=name.split('/')[1]
            if key not in wanted:continue
            targets=wanted[key];expected=targets[0][1]
            info=source.getinfo(name)
            if info.file_size!=expected['bytes']:raise ValueError('Runtime object size mismatch')
            pending=[]
            for target,row in targets:
                if target.exists():
                    if digest(target)!=key:raise ValueError('Existing file differs; refusing to overwrite: '+str(target))
                else:pending.append(target)
            if not pending:continue
            target=pending[0];target.parent.mkdir(parents=True,exist_ok=True)
            descriptor,tmp=tempfile.mkstemp(prefix='.runtime-',dir=target.parent);os.close(descriptor);tmp=Path(tmp)
            try:
                with source.open(name) as content,tmp.open('wb') as output:shutil.copyfileobj(content,output,1024*1024)
                if digest(tmp)!=key:raise ValueError('Runtime object checksum mismatch')
                # All source data was verified before publishing the first destination.
                for path in pending:
                    path.parent.mkdir(parents=True,exist_ok=True)
                    if path.exists():raise ValueError('Runtime destination appeared during restoration')
                    shutil.copyfile(tmp,path);restored+=1
            finally:tmp.unlink(missing_ok=True)
    return restored

def run(root=ROOT,full=False,verify=False):
    root=Path(root);manifest=json.loads((root/'config.runtime-assets.json').read_text())
    files={p:r for p,r in manifest['files'].items() if full or r['profile']=='core'}
    missing=[]
    for p,row in files.items():
        target=destination(root,p)
        if not target.is_file():missing.append(p)
        elif target.stat().st_size!=row['bytes'] or digest(target)!=row['sha256']:raise ValueError('Existing runtime file differs: '+p)
    if missing and verify:raise FileNotFoundError(f'{len(missing)} runtime files absent; run python3 scripts/fetch_runtime.py'+(' --full' if full else ''))
    if missing:
        cache=root/'runtime-downloads'/manifest['release'];cache.mkdir(parents=True,exist_ok=True)
        for asset in manifest['assets']:
            if not full and asset['profile']!='core':continue
            path=download(asset,manifest,cache);install_archive(path,files,root)
        for p,row in files.items():
            target=destination(root,p)
            if not target.is_file() or digest(target)!=row['sha256']:raise ValueError('Runtime restoration incomplete: '+p)
    print(f'Runtime verified: {len(files)} files · '+('full native exports' if full else 'core application'))
    return len(files)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true',help='Include optional full-resolution dual-polarization export rasters');parser.add_argument('--verify',action='store_true',help='Check local data without downloading');args=parser.parse_args();run(full=args.full,verify=args.verify)
