"""Create and check an allowlisted, deterministic preview-only release candidate."""
from base64 import b64decode
from gzip import compress
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
from PIL import Image

from package_atlas import ROOT, bundle_atlas_controller, package
from atlas_stac import catalog_documents

FIRST_CASE = 'jamuna_river'
PORTABLE_BUDGET = 8 * 1024**2
FIRST_BUDGET = 495_916
COG_VALIDATOR = '7.0.4'
WEBP_PREFIX = 'data:image/webp;base64,'
PREVIEW_PATHS = (
    (r'observations\.\d+\.images\.(hh|hv|fraction)', 'NASA–ISRO NISAR GCOV'),
    (r'profiles\.\d+\.reference_matches\.[^.]+\.image', 'NASA HLS'),
    (r'pairs\.\d+\.image|coherenceComparisons\.\d+\.image', 'NASA–ISRO NISAR GUNW'),
    (r'context\.thermal\.\d+\.image', 'USGS Landsat'),
    (r'context\.terrain', 'NASA JPL NASADEM'),
    (r'context\.(scenarios\.[^.]+\.\d+|models\.(flood|landslide)\.[^.]+)\.image',
     'TerraPulse model, NASA POWER, NASADEM and NISAR'),
)
HEADERS = '''/*
  Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer
'''


def json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=False,separators=(',',':'),allow_nan=False)+'\n').encode()


def digest(data):
    return sha256(data).hexdigest()


def assert_public_text(data, path):
    deny = rb'(?i)(?:earthdata[_-]password|BEGIN [A-Z ]*PRIVATE KEY|github_pat_[A-Za-z0-9_]+|sk-proj-[A-Za-z0-9_-]+|/home/[^/]+/|file:///|/Downloads/|127\.0\.0\.1|https?://localhost)'
    if re.search(deny,data):
        raise ValueError(f'Private path or credential pattern in {path}')


def detail_frames(public, case, record):
    case_root = (public/'cases'/case).resolve()
    path = (public/record['manifest_path']).resolve()
    if not path.is_relative_to(case_root):
        raise ValueError('Atlas manifest is outside its case')
    raw = path.read_bytes()
    if digest(raw) != record['manifest_sha256']:
        raise ValueError('Atlas preview manifest changed')
    visits = json.loads(raw)['observations']
    if [(o['observation_id'], o['timestamp']) for o in visits] != [
        (o['observation_id'], o['timestamp']) for o in record['observations']
    ]:
        raise ValueError('Atlas preview observation changed')
    frames = {}
    for index, visit in enumerate(visits):
        for layer in ('hh','hv'):
            name = visit['layers'][layer]
            asset = (public/name.lstrip('/') if name.startswith('/cases/') else path.parent/name).resolve()
            if not asset.is_relative_to(case_root) or asset.suffix not in ('.png','.webp'):
                raise ValueError('Unexpected detailed radar image')
            with Image.open(asset) as image:
                if max(image.size) != 1100:
                    raise ValueError('Unexpected detailed radar dimensions')
                buffer = BytesIO()
                image.save(buffer, 'WEBP', quality=82, method=4)
                frames[f'observations.{index}.images.{layer}'] = buffer.getvalue()
    return frames


def simulation_assets(folder, case, record):
    source=folder/f'{case}.json'
    if not source.is_file():
        return {}
    meta=json.loads(source.read_bytes())
    if (meta['schema']!=1 or meta['case']!=case or meta['caseSha256']!=record['manifest_sha256']
            or meta['terrainSha256']!=record['terrain']['source_manifest_sha256']):
        raise ValueError('Scenario inputs differ from the admitted case')
    # The local UNOSAT archive remains outside the public candidate.
    meta.pop('localImpact',None)
    assets={source.name:json_bytes(meta)}
    references=[meta['terrain'],meta['drainage'],*meta['observations'].values()] if meta['kind']=='stage' else [
        meta['terrain'],*meta['comparisons']]
    if meta.get('bank'):
        references.append(meta['bank']['series'])
        if meta['bank'].get('cover'):
            references.append(meta['bank']['cover'])
    if meta.get('orbit'):
        references.append(meta['orbit']['dem'])
    for ref in references:
        name=ref['file']
        if not re.fullmatch(rf'{case}-(?:stage|drainage|hh|slope|coherence|bank|bank-cover|orbit)-[0-9a-f]{{16}}\.bin',name):
            raise ValueError('Unexpected scenario asset name')
        path=folder/name
        data=path.read_bytes()
        if path.is_symlink() or len(data)!=ref['bytes'] or digest(data)!=ref['sha256']:
            raise ValueError('Scenario asset checksum differs')
        assets[name]=data
    return assets


def build_static(root=ROOT):
    web=root/'web'
    raw=(web/'atlas-record.json').read_bytes()
    identities=(web/'atlas-contract-records.json').read_bytes()
    record,catalog=json.loads(raw),json.loads(identities)
    shell=(web/'index.html').read_text().split('<!-- atlas:start -->')[1].split('<!-- atlas:end -->')[0]
    shell=re.sub(r'<!-- local:only -->.*?<!-- local:end -->','',shell,flags=re.S)
    shell=shell.replace('href="/guide.html"','href="#atlas-guide-reference"')
    controller=bundle_atlas_controller(web).encode()
    css_files=('tokens.css','fonts.css','atlas.css','atlas-ui.css')
    fonts={file.name:file.read_bytes() for file in sorted((web/'fonts').iterdir()) if file.suffix in ('.woff2','.txt')}
    style=b'body{margin:0;background:var(--tp-ink-0);color:var(--tp-text)}'+b''.join((web/name).read_bytes() for name in css_files)
    style=re.sub(rb'/\* local-font:start \*/.*?/\* local-font:end \*/',b'',style,flags=re.S)
    rights=(root/'docs/ATLAS_ASSET_REVIEW.md').read_bytes()
    first_frame_script=(web/'atlas-first-frame.js').read_bytes()
    details={case:detail_frames(web/'public',case,data) for case,data in record.items()}
    simulations={case:simulation_assets(root/'output/atlas/simulations',case,data) for case,data in record.items()}
    if any(simulations.values()) and not all(simulations.values()):
        raise ValueError('Build the scenario inputs for all four cases')
    release_inputs=[*fonts.values(), (root/'docs/CREDITS_UI.md').read_bytes()]
    release_inputs.extend((root/f).read_bytes() for f in ('web/atlas-replay.ipynb','claims/claims.yaml',
        'docs/TERRAPULSE_STEP_BY_STEP_PLAN.md','docs/AI_USE.md','LICENSE',
        'data/palettes/v1/cmcrameri_license','data/palettes/v1/matplotlib_license','scripts/package_atlas.py',
        'scripts/atlas_stac.py'))
    release_id=digest(b'\0'.join((raw,identities,shell.encode(),controller,style,rights,first_frame_script,Path(__file__).read_bytes(),
        *(image for images in details.values() for image in images.values()),
        *(data for group in simulations.values() for _,data in sorted(group.items())),*release_inputs)))[:16]
    prefix='v-'+release_id
    files,inventory={},{}
    def add(path, data, role, sources):
        if path in files:
            if files[path]!=data:raise ValueError('Asset key collision')
            inventory[path]['sources'].extend(sources)
            return
        files[path]=data
        inventory[path]={'role':role,'sha256':digest(data),'bytes':len(data),'sources':list(sources),
            'redistribution':'preview candidate reviewed in ATLAS_ASSET_REVIEW.md'}

    def public_fields(value, case, path=''):
        if isinstance(value,dict):
            return {key:public_fields(item,case,(path+'.' if path else '')+key) for key,item in value.items()}
        if isinstance(value,list):
            return [public_fields(item,case,path+'.'+str(i)) for i,item in enumerate(value)]
        if isinstance(value,str) and value.startswith('data:'):
            source=next((name for pattern,name in PREVIEW_PATHS if re.fullmatch(pattern,path)),None)
            if not source or not value.startswith(WEBP_PREFIX):raise ValueError('Unexpected preview: '+case+' '+path)
            image=details[case].get(path) or b64decode(value.removeprefix(WEBP_PREFIX),validate=True)
            if not image.startswith(b'RIFF') or image[8:12]!=b'WEBP' or len(image)>512*1024:
                raise ValueError('Preview is outside the approved WebP limits')
            name=f'{prefix}/previews/{digest(image)[:24]}.webp'
            add(name,image,'preview',[{'case':case,'field':path,'provider':source}])
            return './'+name
        if isinstance(value,str) and value.startswith(('/cases/','cases/')):
            return None
        return value

    cases,public_records={},{}
    if record.keys()!=catalog.keys() or FIRST_CASE not in record:
        raise ValueError('Unexpected saved case catalog')
    for case, data in record.items():
        identity=catalog[case]
        if data['manifest_sha256']!=identity['manifestSha256'] or not re.fullmatch(r'[a-z_]+',case):
            raise ValueError('Case is not bound to the accepted manifest')
        packed=public_fields(data,case)
        public_records[case]=packed
        packed.pop('manifest_path')
        mesh=packed['terrain'].pop('elevation_m')
        terrain=f'{prefix}/{case}-terrain.json'
        add(terrain,json_bytes(mesh),'sampled terrain',[{'case':case,'provider':'NASA JPL NASADEM','manifestSha256':packed['terrain']['source_manifest_sha256']}])
        identity=public_fields(identity,case)
        payload=f'{prefix}/{case}.json'
        add(payload,json_bytes({'record':packed,'identity':identity}),'case evidence',
            [{'case':case,'provider':'Admitted TerraPulse record','manifestSha256':identity['manifestSha256']}])
        cases[case]={'label':data['country']+' · '+data['title'].split(' · ')[0],
                     'data':'./'+payload,'terrain':'./'+terrain,'manifestSha256':identity['manifestSha256'],
                     'evidenceVersion':identity['evidenceVersion']}
        if simulations[case]:
            cases[case]['simulation']=f'./{prefix}/simulations/{case}.json'
            for name,content in simulations[case].items():
                add(f'{prefix}/simulations/{name}',content,'scenario metadata' if name.endswith('.json') else 'scenario grid',
                    [{'case':case,'provider':('ESA WorldCover 2021 v200' if '-bank-cover-' in name else
                        'NASA JPL NASADEM; observed NISAR GCOV/GUNW context')}])

    for name, item in catalog_documents(public_records,catalog).items():
        add('stac/'+name,json_bytes(item),'STAC discovery metadata',[{'file':'web/atlas-contract-records.json'}])
    shell=shell.replace('href="/atlas-replay.ipynb"',f'href="./{prefix}/atlas-replay.ipynb"')
    entry=public_records[FIRST_CASE]
    reference_index=next(i for i,visit in enumerate(entry['observations']) if visit['timestamp']==entry['reference'])
    entry_preview={'case':FIRST_CASE,'date':entry['observations'][-1]['timestamp']}
    for slot,index in (('selected',len(entry['observations'])-1),('reference',reference_index)):
        field=f'observations.{index}.images.hh'
        buffer=BytesIO()
        with Image.open(BytesIO(details[FIRST_CASE][field])) as image:
            image.thumbnail((800,800),Image.Resampling.LANCZOS)
            image.save(buffer,'WEBP',quality=74,method=4)
        data=buffer.getvalue()
        name=f'{prefix}/previews/{digest(data)[:24]}.webp'
        add(name,data,'preview',[{'case':FIRST_CASE,'field':field,'provider':'NASA–ISRO NISAR GCOV'}])
        entry_preview[slot]='./'+name
    config=json_bytes({'defaultCase':FIRST_CASE,'cases':cases,'entryPreview':entry_preview}).decode().replace('<','\\u003c')
    first_map,first_reference=(entry_preview[key][2:] for key in ('selected','reference'))
    preloader=f'{prefix}/atlas-first-frame.js'
    html=(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
          f'content="width=device-width,initial-scale=1"><title>TerraPulse · Saved observations</title>'
          f'<link rel="icon" href="data:,"><script async src="./{preloader}" data-preview="./{first_map}" '
          f'data-reference="./{first_reference}"></script>'
          f'<link rel="stylesheet" href="./{prefix}/atlas.css"></head>'
          f'<body data-atlas-hosted="yes"><main>{shell}</main>'
          f'<script id="atlas-hosted-config" type="application/json">{config}</script>'
          f'<script type="module" src="./{prefix}/atlas.mjs"></script></body></html>').encode()
    add('index.html',html,'entry',[{'file':'web/index.html'}])
    add(preloader,first_frame_script,'controller',[{'file':'web/atlas-first-frame.js'}])
    add(f'{prefix}/atlas.mjs',controller,'controller',[{'file':'web/atlas*.mjs'}])
    add(f'{prefix}/atlas.css',style,'styles',[{'file':'web/'+name} for name in css_files])
    for name,data in fonts.items():
        if name=='source-sans-3.woff2':
            continue
        add(f'{prefix}/fonts/{name}',data,'font' if name.endswith('.woff2') else 'license notice',[{'file':'web/fonts/'+name}])
    add('ui-credits.txt',(root/'docs/CREDITS_UI.md').read_bytes(),'attribution',[{'file':'docs/CREDITS_UI.md'}])
    add(f'{prefix}/atlas-replay.ipynb',(web/'atlas-replay.ipynb').read_bytes(),'replay notebook',[{'file':'web/atlas-replay.ipynb'}])
    add('_headers',(HEADERS+f'/{prefix}/*\n  Cache-Control: public, max-age=31536000, immutable\n').encode(),'hosting policy',[])
    add('sources.txt',rights,'attribution',[{'file':'docs/ATLAS_ASSET_REVIEW.md'}])
    for file in ('LICENSE','data/palettes/v1/cmcrameri_license','data/palettes/v1/matplotlib_license'):
        add(Path(file).name+'.txt',(root/file).read_bytes(),'license notice',[{'file':file}])
    for path,data in files.items():
        if inventory[path]['role'] not in ('preview','scenario grid'):
            assert_public_text(data,path)
    first_view=['index.html',preloader,f'{prefix}/atlas.mjs',f'{prefix}/atlas.css',cases[FIRST_CASE]['data'][2:],
                first_map,first_reference,f'{prefix}/fonts/jetbrains-mono.woff2']
    compressed_bytes=sum(len(compress(files[p],mtime=0)) if not p.endswith(('.webp','.woff2')) else len(files[p]) for p in first_view)
    if compressed_bytes>FIRST_BUDGET:
        raise ValueError('The first view exceeds the 495,916-byte compressed budget')
    return release_id,files,inventory,cases,{'allowedPaths':first_view,'gzipBodyBytes':compressed_bytes,'limitBytes':FIRST_BUDGET}


def verify_cogs(folder, inventory):
    cogs=[name for name,item in inventory.items() if item['role']=='COG']
    rasters=[name for name in inventory if Path(name).suffix.lower() in ('.tif','.tiff')]
    if set(cogs)!=set(rasters):
        raise ValueError('GeoTIFFs must be explicitly declared as COGs in this release inventory')
    if not cogs:return {'status':'not applicable: no COGs in this edition','assets':[]}
    if version('rio-cogeo')!=COG_VALIDATOR:raise ValueError('Use rio-cogeo=='+COG_VALIDATOR)
    from rasterio import Env
    from rio_cogeo.cogeo import cog_validate
    reports=[]
    with Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'):
        for name in cogs:
            valid,errors,warnings=cog_validate(str(folder/name),strict=True,quiet=True)
            reports.append({'path':name,'valid':valid,'errors':errors,'warnings':warnings})
    return {'status':'passed' if all(r['valid'] for r in reports) else 'failed','assets':reports}


def verify_folder(folder, inventory):
    if not folder.is_dir():raise ValueError('Static release folder is missing')
    found={p.relative_to(folder).as_posix():p for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
    if found.keys()!=inventory.keys():raise ValueError('Static folder differs from the release allowlist')
    for name,item in inventory.items():
        if found[name].is_symlink():raise ValueError('Symlink in static release')
        data=found[name].read_bytes()
        if len(data)!=item['bytes'] or digest(data)!=item['sha256']:raise ValueError('Checksum mismatch: '+name)


def release(root=ROOT,check=False):
    rid,files,inventory,cases,first_view=build_static(root)
    out=root/'output/atlas'
    target=out/'releases'/rid
    folder=target/'static'
    if not target.exists() and not check:
        target.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent,prefix='.static-') as tmp:
            stage=Path(tmp)/'candidate'
            for name,data in files.items():
                path=stage/'static'/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
            verify_folder(stage/'static',inventory)
            stage.rename(target)
    verify_folder(folder,inventory)
    portable=out/'TerraPulse.html'
    if not check:package(root)
    portable_bytes=portable.read_bytes()
    frozen_portable=target/'TerraPulse.html'
    if not frozen_portable.exists() and not check:frozen_portable.write_bytes(portable_bytes)
    if frozen_portable.read_bytes()!=portable_bytes:raise ValueError('Frozen and working portable editions differ')
    if len(portable_bytes)>PORTABLE_BUDGET:raise ValueError('Portable HTML exceeds the 8 MiB budget')
    cogs=verify_cogs(folder,inventory)
    records={case:{k:item[k] for k in ('manifestSha256','evidenceVersion')} for case,item in cases.items()}
    git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    manifest={'schemaVersion':1,'releaseId':rid,'source':{'gitBase':git_head,
        'revisionScope':'Working-tree release candidate; artifact and input digests bind the build.',
        'claimLedgerSha256':digest((root/'claims/claims.yaml').read_bytes()),
        'partPlanSha256':digest((root/'docs/TERRAPULSE_STEP_BY_STEP_PLAN.md').read_bytes())},
        'edition':'Saved observations and footprints','records':records,
        'static':{'folder':'static','assetInventorySha256':digest(json_bytes(inventory)),'assets':inventory,'firstView':first_view,'cogValidation':cogs},
        'portable':{'path':'TerraPulse.html','bytes':len(portable_bytes),'sha256':digest(portable_bytes),'limitBytes':PORTABLE_BUDGET},
        'scope':{'parts16':'saved replay and matching local native replay','parts17':'verified staging, deployment pending',
                 'parts18':'protocol ready, participant sessions pending','parts19':'local candidate, eligibility and submission pending',
                 'nativeStreaming':'post-event; unavailable in this edition'},
        'deployment':{'state':'not deployed','url':None,'id':None,
                      'rollback':'Reinstate the previous approved production deployment. For an initial release, unpublish the Pages project.'}}
    target_manifest=target/'release-manifest.json'
    manifest_bytes=json_bytes(manifest)
    if check:
        if target_manifest.read_bytes()!=manifest_bytes:raise ValueError('Release manifest is stale')
    else:
        target_manifest.write_bytes(manifest_bytes)
        (out/'release.json').write_bytes(json_bytes({'releaseId':rid,'manifest':target_manifest.relative_to(out).as_posix()}))
    if cogs['status']=='failed':raise ValueError('Strict COG validation failed; see the release manifest')
    print(target_manifest)
    print(f"First view: {first_view['gzipBodyBytes']} gzip body bytes. Portable: {len(portable_bytes)} bytes. {cogs['status']}.")
    return target_manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    release(check=parser.parse_args().check)
