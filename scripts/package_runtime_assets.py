"""Build size-bounded, content-deduplicated runtime assets, excluding raw inputs."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAX_PART_BYTES=1400*1024**2

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def runtime_files(root):
    for p in sorted((root/'web/public/cases').rglob('*')):
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in {'.png','.webp','.tif','.tiff'}:yield p
    cube=root/'data/derived/nepal_case_01/flood/components.npz'
    if cube.is_file():yield cube

def build(release):
    output=ROOT/'dist'/release
    if output.exists():raise FileExistsError('Choose a new runtime release ID')
    output.mkdir(parents=True)
    unique={};files={}
    for p in runtime_files(ROOT):
        sha=digest(p);relative=p.relative_to(ROOT).as_posix();profile='native' if '/dualpol-v1/' in relative and p.suffix.lower() in {'.tif','.tiff'} else 'core'
        files[relative]={'sha256':sha,'bytes':p.stat().st_size,'profile':profile}
        if sha not in unique:unique[sha]={'path':p,'bytes':p.stat().st_size,'profile':profile}
        elif profile=='core':unique[sha]['profile']='core'
    assets=[]
    for profile in ['core','native']:
        archive=None;part=0;used=0;filename=None
        def close():
            if archive:
                archive.close();path=output/filename;assets.append({'name':filename,'profile':profile,'bytes':path.stat().st_size,'sha256':digest(path)});print('Packed',filename,path.stat().st_size,flush=True)
        for sha,row in sorted(unique.items()):
            if row['profile']!=profile:continue
            if row['bytes']>MAX_PART_BYTES:raise ValueError('Oversized individual runtime file')
            if archive is None or used+row['bytes']>MAX_PART_BYTES:
                close();part+=1;filename=f'terrapulse-runtime-{profile}-{part:02d}.zip';archive=zipfile.ZipFile(output/filename,'w',compression=zipfile.ZIP_STORED,allowZip64=True);used=0
            archive.write(row['path'],'objects/'+sha);used+=row['bytes']
        close()
    manifest={'schema_version':1,'project':'TerraPulse','repository':'mahdimahmud2006-coder/nasa101','release':release,'profiles':{'core':'Interactive views, playback, native probing, Nepal coherence and scenarios','native':'Optional additional full-resolution dual-polarization export rasters'},'assets':assets,'files':files,'scope':'Processed local runtime only; no raw satellite HDF5, credentials or environment.'}
    data=json.dumps(manifest,indent=2,sort_keys=True)+'\n';(output/'runtime-manifest.json').write_text(data);(ROOT/'config.runtime-assets.json').write_text(data)
    print('Runtime inventory:',len(files),'files;',len(unique),'unique objects;',len(assets),'parts',flush=True)
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);build(p.parse_args().release)
