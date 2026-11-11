"""Read-only source audit and acquisition queue for Parts 1–3."""
import argparse
from collections import defaultdict
import hashlib
import json
import shutil
import sys
from pathlib import Path

import h5py
import rasterio
from shapely.geometry import box
from shapely.wkt import loads as wkt
from pyproj import Transformer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_imerg_catalog import windows, parse_date
from src.compute.atlas_admission import active_manifests, candidate_gate
from src.compute.atlas_contract import binding
from src.compute.expanded_record import gunw_header
from src.ingest.timeseries import read_observation

PUBLIC=ROOT/'web/public'
CASES=PUBLIC/'cases'
OUT=ROOT/'reports/development'
PROVIDER='NASA Earthdata / ASF DAAC (US)'
LINEAGE='NASA/JPL and ISRO; source-header and declared auxiliary provenance checked for the accepted scope'
PENDING='Candidate only; separate upstream, local header and quality review before admission'

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def public_asset(folder,name):return PUBLIC/name.lstrip('/') if name.startswith('/cases/') else folder/name
def local_assets(assets):
    return [{'path':a['file'],'sha256_expected':a.get('sha256'),'size_bytes':(ROOT/a['file']).stat().st_size if (ROOT/a['file']).is_file() else None,
             'hash_verified':sha(ROOT/a['file'])==a['sha256'] if (ROOT/a['file']).is_file() and a.get('sha256') else None} for a in assets]

def check_raster(path, grid):
    with rasterio.open(path) as ds:
        if list(ds.shape)!=grid['shape'] or list(ds.transform)[:6]!=grid['affine'] or str(ds.crs)!=grid['crs']:
            raise ValueError(f'Raster grid mismatch: {path.name}')
        return {'bytes':path.stat().st_size,'dtype':ds.dtypes[0],'nodata':None if ds.nodata is None or ds.nodata!=ds.nodata else ds.nodata,
                'grid_matches':True}

def intersects(bounds, footprint):
    return bool(footprint and wkt(footprint).intersects(box(*bounds)))

def run():
    paths=active_manifests(ROOT)
    records=load(ROOT/'web/atlas-record.json')
    variants=defaultdict(list)
    for folder in (ROOT/'database',ROOT/'database for imp2'):
        for p in folder.rglob('*.h5'):variants[p.name].append(p)
    raw_headers={}
    pair_headers={}
    product_rows=[]
    expected_sizes={x['filename']:x['size_bytes'] for x in load(ROOT/'reports/bangladesh_import_2026_11_03/source_audit.json')['records']}
    expected_sizes.update({Path(x['file']).name:x['bytes'] for x in load(ROOT/'reports/extra_2026_11_03/input_inventory.json')})
    for case,path in paths.items():
        m=load(path); c=records[case]; bounds=m['grid']['bounds_wgs84']
        if sha(path)!=c['manifest_sha256']:raise ValueError('Atlas uses a different scientific manifest')
        for o in m['observations']:
            oid=o['source_granule_id']
            if oid not in raw_headers:
                file=ROOT/o['source_file']
                if not file.is_file():
                    alternatives=variants[Path(o['source_file']).name]
                    if len(alternatives)!=1:raise ValueError('Missing or ambiguous raw granule '+oid)
                    file=alternatives[0]
                hh=read_observation(file,term='HHHH')
                hv=read_observation(file,term='HVHV')
                if hh['granule_id']!=oid or hv['granule_id']!=oid or parse_date(hh['acquisition_start']+'Z')!=parse_date(o['timestamp']):
                    raise ValueError('Raw identity or acquisition time mismatch '+oid)
                with h5py.File(file,'r') as h:
                    terms=sorted(key for key in h[hh['grid_path']] if key in ('HHHH','HVHV','HHHV','HVHH'))
                raw_headers[oid]=(file,hh,hv,terms)
            file,hh,hv,terms=raw_headers[oid]
            status,reason=candidate_gate(track=hh['track'],frame=hh['frame'],expected_track=o['track'],expected_frame=o['frame'],
                header_ok=True,actual_bytes=file.stat().st_size,expected_bytes=expected_sizes.get(file.name),lineage='approved',
                overlap=intersects(bounds,hh['footprint_wkt']))
            if status!='audited' or hh['look_direction']!='Left' or hh['orbit_direction']!='Ascending' or hh['product_version']!=o['product_version']:
                raise ValueError(f'{case}: {status} {reason}')
            raster={p:check_raster(public_asset(path.parent,o['rasters'][p]),m['grid']) for p in ('hh','hv')}
            product_rows.append({'kind':'GCOV','source_id':oid,'case_id':case,'observation_id':o['observation_id'],'utc':o['timestamp'],
                'provider':PROVIDER,'lineage':LINEAGE,'raw_path':rel(file),'local_bytes':file.stat().st_size,'expected_bytes':expected_sizes.get(file.name),
                'status':'accepted','reason':'Previously accepted product; raw HH/HV headers and native raster grid rechecked',
                'track':hh['track'],'frame':hh['frame'],'orbit':hh['orbit_direction'],'look':hh['look_direction'],'bandwidth_hz':hh['range_bandwidth_hz'],
                'product_version':hh['product_version'],'discovered_covariance_terms':terms,'native_raster':raster,'mask_quality':o['quality'],'manifest':rel(path),
                'redistribution':'Derived preview review pending Part 17; raw product not included'})
        for p in m.get('interferometry',[]):
            oid=p['identification']['granuleId'];file=ROOT/p['source_file']
            if oid not in pair_headers:pair_headers[oid]=gunw_header(file,{o['timestamp'] for o in m['observations']})
            hd=pair_headers[oid]
            if hd['identification']!=p['identification'] or hd['timestamps']!=p['timestamps'] or file.stat().st_size!=p['size_bytes']:
                raise ValueError('GUNW raw identity, date or size mismatch')
            checks={k:check_raster(public_asset(path.parent,p['rasters'][k]),p['grids']['20']) for k in ['coherence20','coherence_valid20']}
            product_rows.append({'kind':'GUNW','source_id':oid,'case_id':case,'endpoints_utc':hd['timestamps'],
                'endpoint_observation_ids':[next(o['observation_id'] for o in m['observations'] if o['timestamp']==t) for t in hd['timestamps']],
                'provider':PROVIDER,'lineage':hd['source_policy'],'auxiliary_inputs':{'dem':hd['dem_source'],'water_mask':hd['water_mask_source']},
                'expected_bytes':p['size_bytes'],'local_bytes':file.stat().st_size,'raw_path':rel(file),
                'status':'accepted','reason':'Both RSLC endpoints, product header and native 20 m rasters verified; descriptive coherence only',
                'native_raster':checks,'mask_quality':p['statistics'],'manifest':rel(path),'redistribution':'Derived preview review pending Part 17'})
        base=path.parent.parent
        context=base/'context-v2/manifest.json'
        for x in load(context)['terrain_sources']:
            source=ROOT/x['file']
            if source.is_file() and sha(source)!=x['sha256']:raise ValueError('Terrain source checksum mismatch')
            product_rows.append({'kind':'DEM','source_id':Path(x['file']).name,'case_id':case,'temporal_scope':'static relief',
                'provider':x.get('provider'),'lineage':x.get('upstream',x.get('producer_organizations','NASA JPL / NASADEM; see source manifest')),
                'expected_bytes':x['size_bytes'],'local_bytes':source.stat().st_size if source.is_file() else None,'manifest':rel(context),
                'status':'accepted','reason':'Accepted historical terrain with source checksum when local; not validated HAND'})
        ref=base/'references-v1/manifest.json'
        for x in load(ref)['results']:
            if x.get('reference_id') is None and x.get('status')=='unavailable':continue
            valid=x.get('clear_assessable_pixels',0)>0
            if valid and x.get('thumbnail_sha256') and sha(public_asset(ref.parent,x['thumbnail']))!=x['thumbnail_sha256']:
                raise ValueError('Optical thumbnail checksum mismatch')
            current=next((o for o in m['observations'] if o['timestamp']==x['radar_timestamp']),None)
            product_rows.append({'kind':'HLS','source_id':x.get('reference_id'),'case_id':case,'observation_id':current['observation_id'] if current else None,
                'radar_utc':x['radar_timestamp'],'source_utc':x.get('reference_timestamp'),'footprint_id':x['footprint_id'],'provider':'Microsoft Planetary Computer (US)',
                'lineage':'NASA HLS: Landsat or Sentinel upstream; see tile ID and archived source manifest','expected_bytes':None,'clear_pixels':x.get('clear_assessable_pixels'),
                'status':('accepted_descriptive' if case in ('jamuna_river','tanguar_wetland') else 'historical_descriptive') if valid else 'unavailable',
                'reason':x['status']+'; optical QA, not ground truth','manifest':rel(ref)})
    legacy=CASES/'nepal_case_01'
    thermal=legacy/'thermal/manifest.json'
    th=load(thermal)
    for t in th['scenes']:
        assets=local_assets(t['assets'])
        if any(a['hash_verified'] is False for a in assets):raise ValueError('Thermal input checksum mismatch')
        product_rows.append({'kind':'Landsat thermal','source_id':t['scene_id'],'case_id':'nepal_surface','source_utc':t['datetime'],
            'provider':th['source']['distributor'],'lineage':th['source']['producer_organizations'],'status':'accepted','reason':'Independently dated; QA-screened, Kathmandu only',
            'expected_bytes':None,'assets':assets,'valid_fraction':t['valid_fraction'],'manifest':rel(thermal)})
    rain=legacy/'context/context.json'; ra=load(rain);power=ra['rainfall_source']
    assets=local_assets(power['source_files'])
    if any(a['hash_verified'] is False for a in assets):raise ValueError('POWER input checksum mismatch')
    for row in ra['observations']:
        product_rows.append({'kind':'POWER','source_id':row['observation_id'],'case_id':'nepal_surface','utc':row['timestamp'],'windows':row['windows'],
            'provider':'NASA POWER (US)','lineage':power['dataset'],'expected_bytes':None,'assets':assets,'status':'accepted',
            'reason':'Existing model-derived context only; coarse support and actual UTC bounds retained','manifest':rel(rain)})
    impact=CASES/'nepal_impact_corridor/investigation/manifest.json'; ref=load(impact)['reference']
    product_rows.append({'kind':'impact outline','source_id':ref['url'],'case_id':'nepal_impact_corridor',
        'temporal_scope':'Historical preliminary event context only; exact outline date not inferred from SAR date','provider':ref['publisher'],
        'lineage':'UNITAR/UNOSAT preliminary satellite interpretation, via UNESCO','expected_bytes':None,'sha256':ref['archive_sha256'],
        'status':'accepted_descriptive','reason':'Context; not field-validated or a damage ground-truth dataset','manifest':rel(impact)})
    queue=[]
    for v in load(CASES/'additional-gunw-downloads-v1.json')['downloads']:
        np=v['series_id']=='nepal_098_016'
        bound=[k for k,c in records.items() if (c['country']=='Nepal')==np]
        queue.append({'priority':2 if np else 3,'part':11,'product':'GUNW','source_id':v['granule_id'],'provider':PROVIDER,'lineage':PENDING,
            'case_ids':bound,'bounds_wgs84':{k:records[k]['grid']['bounds_wgs84'] for k in bound},'endpoints_utc':v['acquisition_starts'],
            'track':98 if np else 69,'frame':16 if np else 14,'look':'Left','pass':'Ascending','polarization':'HH frequency A',
            'version':'L2 PR P05023; verify actual header and source RSLC identity','native_target':'20 m coherence with native valid mask',
            'size_bytes':v['size_bytes'],'url':v['url'],'status':'listed','reason':v['interval_note'] if 'interval_note' in v else PENDING})
    catalog=load(OUT/'part-03-imerg-catalog.json')
    current=windows(records)
    if any({k:v for k,v in x.items() if k!='catalog'}!=y for x,y in zip(catalog['windows'],current,strict=True)):
        raise ValueError('Rainfall catalog is stale for these acquisitions')
    for w in catalog['windows']:
        queue.append({'priority':3,'part':8,'product':'IMERG Final half-hourly V07 HDF5','source_id':'GPM_3IMERGHH.07:'+w['source'],
            'provider':'NASA GES DISC','lineage':'Multisatellite PMW + GEO-IR + gauge blend; per-window upstream contributors not cleared',
            'footprints':w['footprints'],'window_utc':[w['start_utc'],w['end_utc']],'expected_bins':len(w['expected_bin_starts']),
            'catalog_coverage':w['catalog']['coverage'],'catalog_matched_bins':w['catalog']['matched_bins'],'size_bytes':None,
            'status':'excluded','reason':'Unverified upstream lineage; no scientific rain is accepted. Catalog availability is separate.'})
    for case,c in records.items():
        bounds=c['grid']['bounds_wgs84']
        obs=[o['timestamp'] for o in c['observations']]
        # Search bounds, not matching rules; Part 13 must freeze admissible offsets.
        hls_missing=[t for t in obs if not any(p.get('reference_matches',{}).get(t,{}).get('clear_assessable_pixels',0)>0 for p in c['profiles'])]
        if hls_missing:
            queue.append({'priority':1,'part':13,'product':'HLS L30/S30 with Fmask',
                'source_id':'collection-search-needed','case_ids':[case],'bounds_wgs84':bounds,'target_utc':hls_missing,
                'search_radius_hours':72,'provider':'NASA Earthdata / LP DAAC','lineage':'NASA HLS; verify Landsat or Sentinel upstream and distributor',
                'requirements':'Cloud/shadow/snow QA and actual eligible footprint overlap. Freeze acceptable date offsets before tuning. Descriptive unless independently validated.',
                'size_bytes':None,'status':'discovery_needed','reason':'No approved additional reference scenes; coverage depends on cloud and eligible date'})
        if c['country']=='Bangladesh':
            queue.append({'priority':4,'part':8,'product':'Landsat Collection 2 Level-2 surface temperature + QA',
                'source_id':'collection-search-needed','case_ids':[case],'bounds_wgs84':bounds,'target_utc':obs,
                'search_radius_hours':168,'provider':'USGS EarthExplorer / USGS Landsat','lineage':'USGS/NASA; verify asset lineage',
                'requirements':'Native thermal support, quality layer, calibrated units, cloud mask and acquisition UTC; contextual independent dates, not SAR pixel temperature.',
                'size_bytes':None,'status':'discovery_needed','reason':'No accepted Bangladesh thermal context'})
        question={'jamuna_river':'Bank migration: date-stamped bank lines in the same reach, registration control and stable transects at both endpoints',
                  'tanguar_wetland':'Wetland state: dated water/vegetation labels with ambiguity and eligible support; no continuous duration inference',
                  'nepal_surface':'Persistence: independent event chronology, a stable comparison area and dated optical or surveyed field evidence',
                  'nepal_impact_corridor':'Damage proxy: documented event interval and independent mapped/field labels; existing preliminary outline is not ground truth'}[case]
        candidate_times=[obs[0],obs[-1]] if case=='jamuna_river' else obs
        queue.append({'priority':1,'part':{'jamuna_river':14,'tanguar_wetland':15}.get(case,13),'product':'Independent georeferenced labels or surveys',
            'source_id':'source-not-yet-selected','case_ids':[case],'bounds_wgs84':bounds,'target_utc':candidate_times,
            'provider':'Identify approved independent agency, field team or dated product before use','lineage':PENDING,'requirements':question,
            'size_bytes':None,'status':'waiting_reference','reason':'Independent references and a frozen holdout protocol are required'})
    queue.extend([
        {'priority':4,'part':9,'product':'DEM + independent drainage checks for HAND','source_id':'source-not-yet-selected',
         'case_ids':list(records),'crop_bounds_wgs84':{k:c['grid']['bounds_wgs84'] for k,c in records.items()},
         'provider':'Existing NASADEM, plus approved drainage reference','lineage':PENDING,'temporal_scope':'static elevation, source epoch required',
         'requirements':'Derive watershed extents and cross-boundary outlets first; use approved elevation/datum plus QA and drainage geometry across full contributing basins.',
         'size_bytes':None,'status':'waiting_method','reason':'Crop-only preview does not prove complete downstream paths'},
        {'priority':5,'part':10,'product':'Optional covariance descriptors','source_id':'existing GCOV header inventory; method decision pending',
         'case_ids':list(records),'bounds_wgs84':{k:c['grid']['bounds_wgs84'] for k,c in records.items()},
         'target_utc':{k:[o['timestamp'] for o in c['observations']] for k,c in records.items()},
         'provider':PROVIDER,'lineage':PENDING,
         'requirements':'Match the chosen published descriptor to available calibrated terms and valid domain; original DpRVI needs full complex C2. Do not order GSLC or substitute DpRVIc before method review.',
         'size_bytes':None,'status':'waiting_method','reason':'Power share remains the accepted measure'},
        {'priority':5,'part':12,'product':'Optional referenced phase and independent LOS benchmark','source_id':'source-not-yet-selected',
         'case_ids':['nepal_surface','nepal_impact_corridor'],'bounds_wgs84':{k:c['grid']['bounds_wgs84'] for k,c in records.items() if c['country']=='Nepal'},
         'endpoints_utc':[p['dates'] for p in records['nepal_surface']['pairs']],
         'provider':'NASA/ASF for candidate interferometry; independently approved control and benchmark','lineage':PENDING,
         'requirements':'Connected phase, verified orbit/look and corrections, suitable stable reference and time-aligned independent motion benchmarks; expand beyond the two pairs only after feasibility.',
         'size_bytes':None,'status':'deferred','reason':'Existing coherence pairs do not establish a validated displacement product'}
    ])
    queue.sort(key=lambda q:(q['priority'],q['part'],q['source_id']))
    outages=[{'country':'Bangladesh','nominal_date':'2026-08-05','cases':['jamuna_river','tanguar_wetland']},
             {'country':'Nepal','nominal_date':'2026-08-07','cases':['nepal_surface','nepal_impact_corridor']}]
    for row in outages:
        row.update(status='unavailable',reason='Documented outage; no acquisition inside the gap',
            source='https://nisar-docs.asf.alaska.edu/availability-overview/')
        if any(o['timestamp'].startswith(row['nominal_date']) for c in row['cases'] for o in records[c]['observations']):
            raise ValueError('Nominal outage slot appears as an acquired visit')
    rejected=[]
    other=next((ROOT/'database for imp2').glob('*149_D_073*.h5'),None)
    if other:
        h=read_observation(other);s,reason=candidate_gate(track=h['track'],frame=h['frame'],expected_track=98,expected_frame=16,header_ok=True)
        rejected.append({'source_id':h['granule_id'],'path':rel(other),'size_bytes':other.stat().st_size,'track':h['track'],'frame':h['frame'],
                         'utc':h['acquisition_start'],'status':s,'reason':reason,'target_case':'nepal_surface'})
    result={'schemaVersion':1,'scope':'Local accepted inventory; catalog listings are not admissible science. No new datasets downloaded.',
        'raw_header_counts':{'gcov':len(raw_headers),'gunw':len(pair_headers)},'free_bytes':shutil.disk_usage(ROOT).free,
        'accepted_manifest_bindings':{c:{**binding(c,p),'path':rel(p)} for c,p in paths.items()},
        'products':product_rows,'outages':outages,'rejected_examples':rejected,'queue':queue}
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT/'part-03-input-inventory.json')
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():parser.error('Use a new --output path to preserve the prior audit')
    result=run()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('Raw headers:',result['raw_header_counts'],'case/product bindings:',len(result['products']),'queue:',len(result['queue']))
