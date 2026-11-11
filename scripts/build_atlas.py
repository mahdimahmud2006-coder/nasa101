"""Build the four-window investigation and a self-contained offline HTML edition."""
from pathlib import Path
from io import BytesIO
import base64
import hashlib
import json
import sys
import numpy as np
import rasterio

from affine import Affine
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.package_atlas import package
from scripts.build_atlas_contracts import write_catalog
from src.compute.atlas_admission import active_manifests, admitted_pairs, require_admitted
from src.compute.atlas_measurements import crosspol_fraction
from src.export.dualpol_render import palette_rgba, load_palettes
from src.compute.atlas_measurements import footprint_geometry
from src.compute.coherence_change import compare_pairs
from src.compute.active_records import registry_path, case_directory

WEB = ROOT/'web'
PUBLIC = WEB/'public'
CASES = PUBLIC/'cases'
def read(path): return json.loads(path.read_text())

def preview(folder, asset):
    path = PUBLIC/asset.lstrip('/') if asset.startswith('/cases/') else folder/asset
    if not path.resolve().is_relative_to(CASES.resolve()): raise ValueError(path)
    with Image.open(path) as im:
        im.thumbnail((340,340),Image.Resampling.NEAREST)
        buf=BytesIO()
        im.save(buf,format='WEBP',quality=65,method=4)
    return 'data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()

def fraction_preview(folder, o, grid):
    h,w=grid['shape']
    height,width=[max(1,round(340*n/max(h,w))) for n in [h,w]]
    rows=(np.arange(height)+0.5)*h/height
    cols=(np.arange(width)+0.5)*w/width
    samples=[]
    for pol in ['hh','hv']:
        name=o['rasters'][pol]
        path=PUBLIC/name.lstrip('/') if name.startswith('/cases/') else folder/name
        with rasterio.open(path) as ds:
            if ds.shape!=(h,w) or ds.transform!=Affine(*grid['affine']) or str(ds.crs)!=grid['crs']:
                raise ValueError('Cross-pol fraction requires the same native grid')
            # Read original pixels (never a potentially averaged overview).
            samples.append(ds.read(1,masked=True).filled(np.nan)[np.ix_(rows.astype(int),cols.astype(int))])
    values=crosspol_fraction(*samples)
    palette=load_palettes(ROOT/'data/palettes/v1')['cividis']
    rgba=palette_rgba(values,(0,1),palette)
    buf=BytesIO();Image.fromarray(rgba).save(buf,format='WEBP',quality=65,method=4)
    return 'data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()

def terrain_mesh(case,folder,grid):
    base=folder.parent/'context-v2'
    context=read(base/'manifest.json')
    if context['case_id']!=case:raise ValueError('Terrain case mismatch')
    h,w=grid['shape'];transform=Affine(*grid['affine'])
    size=41
    with rasterio.open(base/context['layers']['dem']['raster']) as ds:
        if ds.crs.to_string()!=grid['crs']:raise ValueError('Terrain CRS mismatch')
        # Sample centers inside the common crop, not beyond its outer edges.
        xy=[transform @ ((.5+c*(w-1)/(size-1)),(.5+r*(h-1)/(size-1))) for r in range(size) for c in range(size)]
        vals=[None if np.ma.is_masked(v[0]) or not np.isfinite(v[0]) else round(float(v[0]),2)
              for v in ds.sample(xy,masked=True)]
    return {'size':size,'width_m':(w-1)*abs(transform.a),'height_m':(h-1)*abs(transform.e),
            'elevation_m':vals,'median_slope_degrees':context['terrain_summary']['median_slope_degrees'],
            'source_manifest_sha256':hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest()}

def study(case, path, country):
    folder=path.parent
    m=read(path)
    frames=m['observations']
    dates=[o['timestamp'] for o in frames]
    if dates!=sorted(set(dates)) or m['reference_timestamp'] not in dates: raise ValueError(f'Invalid dates for {case}')
    profiles=[]
    evidence = [{'profile':p} for p in m['profiles']]
    references = []
    if country=='Bangladesh':
        rules=read(folder.parent/'evidence-v2/manifest.json')
        optical=read(folder.parent/'references-v1/manifest.json')
        source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        if rules['source_manifest_sha256']!=source_hash or optical['radar_manifest_sha256']!=source_hash:
            raise ValueError('Footprints or reference results are bound to a different record')
        evidence=rules['profiles']+optical['profiles']
        references=optical['results']
    for e in evidence:
        p=e['profile']
        if [r['timestamp'] for r in p['observations']]!=dates: raise ValueError('Misaligned profile')
        profiles.append(dict(label=p['label'],valid_pixels=p['common_valid_pixels'],
            area_km2=p.get('measured_area_km2',p.get('common_valid_area_km2')),
            series=[{pol+'_'+key:r.get(pol+'_'+key+'_delta_db',r.get(pol+'_baseline_delta_db') if key=='reference' else None)
                     for pol in ['hh','hv'] for key in ['reference','successive']} for r in p['observations']]))
        if 'explanations' in e:
            explanations=e['explanations']
            if [v['timestamp'] for v in explanations]!=dates or [v['observation_id'] for v in explanations]!=[v['observation_id'] for v in frames]:
                raise ValueError('Explanation/date mismatch')
            profiles[-1]['rules_version']=e['rules_version']
            profiles[-1]['fits']=[[{k:h[k] for k in ('title','status','evidence_still_required','limitation')} for h in v['hypotheses']] for v in explanations]
            profiles[-1]['selection']=p.get('selection')
            profiles[-1]['reference_matches']={}
            for v in references:
                if v['footprint_id']!=e.get('reference_footprint_id') or v['case_id']!=case:continue
                if (v['observation_id'],v['radar_timestamp']) not in [(o['observation_id'],o['timestamp']) for o in frames]:
                    raise ValueError('Optical comparison not bound to a radar visit')
                match={k:v[k] for k in ('status','reference_id','reference_timestamp','clear_assessable_pixels','overlap','scope')}
                if v['clear_assessable_pixels'] and v.get('thumbnail'):match['image']=preview(folder,v['thumbnail'])
                profiles[-1]['reference_matches'][v['radar_timestamp']]=match
    obs=[]
    for o in frames:
        obs.append({k:o[k] for k in ('timestamp','source_granule_id','observation_id','track','frame','processing_release','product_version','doi')} |
             {'images':{k:preview(folder,o['layers'][k]) for k in ['hh','hv']} | {'fraction':fraction_preview(folder,o,m['grid'])},
              'quality':{k:o['quality'][k]['valid_fraction'] for k in ['hh','hv']},
              'response':o.get('response',{})})
    measured_pairs=admitted_pairs(ROOT,path,m)
    pairs=[{'dates':p['timestamps'],'source':p['identification']['granuleId'],
            'image':preview(folder,p['layers']['coherence20'])} for p in measured_pairs]
    h,w=m['grid']['shape']
    area=footprint_geometry([[0,0],[w,0],[w,h],[0,h]],Affine(*m['grid']['affine']),m['grid']['crs'])
    return {'case':case,'country':country,'title':m['title'],'reference':m['reference_timestamp'],
            'grid':m['grid'],'terrain':terrain_mesh(case,folder,m['grid']),'scope_area':area,'limits':m['display_limits'],'observations':obs,'profiles':profiles,
            'pairs':pairs,'pair_comparison':compare_pairs(measured_pairs,PUBLIC),'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'manifest_path':path.relative_to(PUBLIC).as_posix()}

def kathmandu_context():
    root=CASES/'nepal_case_01'
    th=read(root/'thermal/manifest.json')
    rain=read(root/'context/context.json')
    flood=read(root/'flood/manifest.json')
    timestamps={row['observation_id']:row['timestamp'] for row in flood['observations']}
    scenarios={}
    approved=read(ROOT/'config.atlas-admission.json')['supportingManifests']
    for path in sorted((root/'flood/scenarios').glob('*/result.json')):
        if path.relative_to(ROOT).as_posix() not in approved:
            continue
        r=read(path);params=r['parameters']
        if (r['case_id']!='nepal_case_01' or r['model_version']!=flood['model']['model_version']
            or r['inputs_sha256']!=flood['inputs_sha256'] or params['observation_id'] not in timestamps
            or params['duration_hours']!=48 or params['historical_sensitivity']):continue
        if (params['rainfall_multiplier'],params['wetness']) not in [(1.5,'wet'),(2.0,'wet')]:continue
        if not (PUBLIC/r['preview_url'].lstrip('/')).is_file():continue
        scenarios.setdefault(timestamps[params['observation_id']],[]).append({
            'id':r['scenario_id'],'parameters':params,'model_version':r['model_version'],'inputs_sha256':r['inputs_sha256'],
            'summary':r['summary'],'image':preview(path.parent,r['preview_url'])})
    return {'scenarios':scenarios,'thermal':[{'source':s['scene_id'],'timestamp':s['datetime'],'mean_c':s['statistics_celsius']['mean'],
                        'valid_fraction':s['statistics_celsius']['valid_fraction'],'image':preview(root/'thermal',s['preview'])}
                       for s in th['scenes']],
            'rain':{r['timestamp']:{k:{'mean_mm':v['statistics']['mean'],'window':r['windows'][k]}
                                for k,v in r['layers'].items() if k in r['windows']} for r in rain['observations']},
            'terrain':preview(root/'context','dem.png'),
            'models':{name:{o['timestamp']:{'mean_score':o['summary']['mean_score'],'image':preview(root/name,o[key])}
                          for o in read(root/name/'manifest.json')['observations']}
                      for name,key in [('flood','escalation_preview'),('landslide','total_preview')]}}

def build():
    require_admitted(ROOT,active_manifests(ROOT))
    records={}
    for row in read(registry_path(ROOT))['cases']:
        case=row['case_id']
        if case in ('jamuna_river','tanguar_wetland'):
            records[case]=study(case,case_directory(case,ROOT)/'investigation/manifest.json','Bangladesh')
    for row in read(CASES/'expanded-v1.json')['cases']:
        case=row['case_id']
        records[case]=study(case,PUBLIC/row['manifest_url'].lstrip('/'),'Nepal')
    records['nepal_surface']['context']=kathmandu_context()
    encoded=json.dumps(records,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    (WEB/'atlas-record.json').write_text(encoded)
    write_catalog(ROOT)
    package(ROOT)
if __name__=='__main__': build()
