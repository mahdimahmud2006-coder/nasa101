"""Build and validate a complete additive Bangladesh record before activation.

Preserves June 18 reference, original six COGs, footprint selection and static
terrain. Recomputes time-dependent support, controls, signatures and evidence.
"""
import argparse,copy,json,shutil,os
from pathlib import Path
import numpy as np,rasterio
from affine import Affine
from rasterio.windows import Window
from pyproj import Transformer
import pyarrow as pa,pyarrow.parquet as pq
from src.compute.evidence_common import ROOT,load,save,sha
from src.compute.bangladesh_intensity import build_case
from src.compute.dualpol_record import build as build_dualpol
from src.export.dualpol_render import load_palettes
from src.compute.context_v2 import rain_window
from src.compute.investigation_dna import evaluate_window,polygon_evidence
from src.ingest.nisar_slots import build_calendar

VERSION='bangladesh-v2'
CASES=['jamuna_river','tanguar_wetland']
REPORT=ROOT/'reports/bangladesh_import_2026_11_03'

def stack(base,m):
    result={p:[] for p in ['hh','hv']}
    for obs in m['observations']:
        for p in result:
            with rasterio.open(base/obs['rasters'][p]) as ds:result[p].append(ds.read(1))
    return {p:np.stack(v) for p,v in result.items()}

def calendar(case,m):
    old=load(ROOT/'web/public/cases/time-axis-v1/calendars.json')['series']['bangladesh_069_014']
    metadata=load(ROOT/'data/candidates/bangladesh_gcov_gaps_2026_11_03/bangladesh_069_014.json')
    series=next(s for s in load(ROOT/'config.time-axis.json')['series'] if s['series_id']=='bangladesh_069_014')
    value=build_calendar(series,m['observations'],metadata['candidates'],metadata['queries'],old['instrument_gaps'])
    value.update(record_version=VERSION,metadata_url=f'/cases/{case}/{VERSION}/calendar.json',source_audit_sha256=sha(REPORT/'source_audit.json'))
    return value

def context(case,directory):
    old=ROOT/f'web/public/cases/{case}/context-v2';dest=directory/'context-v2';shutil.copytree(old,dest)
    original=load(old/'manifest.json');m=load(directory/'investigation/manifest.json');channels=stack(directory/'investigation',m)
    with rasterio.open(dest/'stable_targets.tif') as ds:selected=ds.read(1)==1
    common=selected&np.isfinite(channels['hh']).all(0)&np.isfinite(channels['hv']).all(0)
    controls=[];rain=[];hist=[]
    for i,obs in enumerate(m['observations']):
        r={'timestamp':obs['timestamp'],'observation_id':obs['observation_id'],'common_control_pixels':int(common.sum())}
        for p in channels:
            values=channels[p][i][common];r[p+'_median_db']=float(np.median(values)) if len(values) else None
            allvalues=channels[p][i][np.isfinite(channels[p][i])];bins=np.arange(-60,31,1)
            hist.append({'timestamp':obs['timestamp'],'channel':p,'bins_db':bins.tolist(),'counts':np.histogram(allvalues,bins)[0].tolist(),'valid_pixels':len(allvalues),'below_above':[int((allvalues<bins[0]).sum()),int((allvalues>bins[-1]).sum())],'scope':'all canonical crop pixels, filtered log-power; not a full raw scene'})
        controls.append(r)
        previous=original['rain'][0];windows={f'{h}h':rain_window(obs['timestamp'],hours=h) for h in [24,72,168]}
        windows['since_previous']=rain_window(obs['timestamp'],start=m['observations'][i-1]['timestamp']) if i else None
        rain.append({**previous,'timestamp':obs['timestamp'],'observation_id':obs['observation_id'],'windows':windows})
    for r in controls:
        for p in channels:r[p+'_baseline_shift_db']=r[p+'_median_db']-controls[0][p+'_median_db'] if r[p+'_median_db'] is not None and controls[0][p+'_median_db'] is not None else None
    original.update(record_version=VERSION,radiometric_controls=controls,rain=rain,source_manifest_sha256=sha(directory/'investigation/manifest.json'),prior_context_manifest_sha256=sha(old/'manifest.json'),control_support={'prior_six_visit_common_pixels':load(old/'manifest.json')['radiometric_controls'][0]['common_control_pixels'],'ten_visit_common_pixels':int(common.sum()),'selection':'Original June 18 and terrain-only selection mask reused unchanged; common support recomputed across all ten visits. No calibration correction applied.'})
    original['limitations'].append('Static terrain, viewing geometry and original target selection reused on identical grid and reference; controls and rain request windows rebound to the ten observed visits. No new scientific rainfall files were supplied.')
    save(dest/'manifest.json',original)
    save(dest/'h1_controls.json',{'selection':original['stable_target_selection'],'controls':controls,'interpretation':'Putative controls can change physically; offsets are hypotheses, not established calibration errors.'})
    save(dest/'crop_histograms.json',hist)
    previous=load(old/'rain.json');save(dest/'rain.json',{**previous,'observations':rain,'record_version':VERSION})
    pq.write_table(pa.Table.from_pylist([{k:v for k,v in r.items() if k!='windows'} for r in rain]),dest/'context.parquet')
    return original['control_support']

def evidence(case,directory):
    old=ROOT/f'web/public/cases/{case}/evidence-v2';prior=load(old/'manifest.json');dest=directory/'evidence-v2';dest.mkdir()
    records=[];supports=[]
    for i,saved in enumerate(prior['profiles']):
        p=saved['profile'];w=p['window'];window=Window(w['col'],w['row'],w['width'],w['height'])
        path=old/saved['footprint_raster']['file']
        with rasterio.open(path) as ds:mask=ds.read(1)==1
        result=evaluate_window(case,mask,window,p['label'],p['selection'],ROOT,directory)
        result['profile']['saved_evidence_index']=i
        # Keep the same saved physical footprint index and selection history.
        shutil.copy2(path,dest/path.name);result['footprint_raster']={'file':path.name,'sha256':sha(path)}
        result['support_comparison']={'prior_six_visit_common_pixels':p['common_valid_pixels'],'ten_visit_common_pixels':result['profile']['common_valid_pixels'],'same_footprint_mask':True}
        supports.append(result['support_comparison']);records.append(result)
    m={'schema_version':2,'record_version':VERSION,'case_id':case,'status':'implemented','profiles':records,'rules_version':prior['rules_version'],'rules_sha256':sha(ROOT/'rules/explanations.yaml'),'source_manifest_sha256':sha(directory/'investigation/manifest.json'),'prior_evidence_manifest_sha256':sha(old/'manifest.json'),'limitations':prior['limitations']+['Original saved footprint masks and indices retained. Common-valid support and temporal metrics recalculated across ten visits; compare aggregate values only on stated support.']}
    save(dest/'manifest.json',m)
    pq.write_table(pa.Table.from_pylist([{'footprint_index':i,'label':r['profile']['label'],'k':r['dna']['persistence']['k'],'n':r['dna']['persistence']['n'],'persistence_fraction':r['dna']['persistence']['fraction'],'recovery_fraction':r['dna']['recovery_fraction'],'recovery_right_censored':r['dna']['recovery_right_censored'],'coherence':None,**v} for i,r in enumerate(records) for v in r['profile']['observations']]),dest/'change_dna_v2.parquet')
    return supports

def references(case,directory):
    old=ROOT/f'web/public/cases/{case}/references-v1';prior=load(old/'manifest.json');m=load(directory/'investigation/manifest.json');dest=directory/'references-v1';dest.mkdir()
    original=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json');newbytime={o['timestamp']:o for o in m['observations']}
    # Retain optical comparisons only when their exact radar endpoint COGs are identical.
    for o in original['observations']:
        new=newbytime[o['timestamp']]
        for p in ['hh','hv']:
            assert sha(ROOT/f'web/public/cases/{case}/investigation'/o['rasters'][p])==sha(directory/'investigation'/new['rasters'][p])
    rows=[]
    for r in prior['results']:
        row=copy.deepcopy(r);row['observation_id']=newbytime[r['radar_timestamp']]['observation_id'];row['record_version']=VERSION
        row['binding_note']='Retained exact frozen-footprint optical comparison: its radar endpoint COG hashes are unchanged. This is not a new-date optical match.'
        rows.append(row)
    oldtimes={o['timestamp'] for o in original['observations']}
    roles={r['footprint_id']:r for r in prior['results']}
    for obs in m['observations']:
        if obs['timestamp'] in oldtimes:continue
        for footprint,template in roles.items():
            rows.append({'case_id':case,'footprint_id':footprint,'footprint_role':template['footprint_role'],'observation_id':obs['observation_id'],'radar_timestamp':obs['timestamp'],'status':'unavailable','reference_status':'none','reference_id':None,'reference_timestamp':None,'clear_assessable_pixels':0,'overlap':{'status':'unavailable','assessable_area_km2':0.,'reference_water_area_km2':None,'intersection_area_km2':None},'thumbnail':None,'scope':'No accepted date-specific optical comparison for this added radar visit. Earlier matches are not inherited.','record_version':VERSION})
    profiles=[];transformer=Transformer.from_crs('EPSG:4326',m['grid']['crs'],always_xy=True);inverse=~Affine(*m['grid']['affine'])
    for feature in load(ROOT/'reference/frozen_footprints.geojson')['features']:
        props=feature['properties']
        if props['case_id']!=case:continue
        vertices=[list(inverse*transformer.transform(*p)) for p in feature['geometry']['coordinates'][0][:-1]]
        r=polygon_evidence(case,vertices,ROOT,directory);r['profile']['label']='Frozen reference: '+props['role'].replace('_',' ');r['profile']['selection']='Frozen before reference inspection; role is not verified event/stability truth.'
        r.update(reference_footprint_id=props['id'],reference_status='none',reference_design_sha256=prior['design_sha256']);profiles.append(r)
    prior.update(record_version=VERSION,profiles=profiles,results=rows,radar_manifest_sha256=sha(directory/'investigation/manifest.json'),prior_reference_manifest_sha256=sha(old/'manifest.json'))
    prior['limitations'].append('Added GCOV visits have no newly accepted optical match. Older results remain bound to the same native COGs and frozen footprints.')
    save(dest/'manifest.json',prior)
    return {'old_comparisons_retained':len(load(old/'manifest.json')['results']),'new_explicitly_unavailable':len(rows)-len(load(old/'manifest.json')['results'])}

def build(resume=False):
    audit=load(REPORT/'source_audit.json');assert len(audit['records'])==4 and all(r['metadata_compatible'] for r in audit['records'])
    parent=ROOT/'web/public/cases';stage=parent/('.'+VERSION+'-build')
    if (stage.exists() and not resume) or any((parent/c/VERSION).exists() for c in CASES):raise FileExistsError('Record/staging version exists; inspect it rather than overwrite')
    if shutil.disk_usage(ROOT).free<6*1024**3:raise ValueError('At least 6 GiB free required for this additive build')
    stage.mkdir(exist_ok=resume);config=load(ROOT/'config.investigations.json');palettes=load_palettes(ROOT/'data/palettes/v1');summary={};registry=load(parent/'investigations.json')
    try:
        for case in CASES:
            old=parent/case;oldm=load(old/'investigation/manifest.json');setting=copy.deepcopy(next(c for c in config['cases'] if c['case_id']==case))
            setting['source_files']=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'database/bangladesh-shared').glob('*.h5'))]+[r['source_file'] for r in audit['records']]
            setting['source_directory']='database/no-additional-source-scan'
            if resume and (stage/case/'investigation/manifest.json').exists():
                print('Resume completed intensity:',case,flush=True);row={**setting,'status':'OBSERVATIONS_READY','observation_count':10}
            else:row=build_case(config,setting,ROOT,stage,old/'investigation',True)
            directory=stage/case;m=load(directory/'investigation/manifest.json');assert len(m['observations'])==10 and m['observations'][0]['timestamp']==oldm['observations'][0]['timestamp']
            m.update(record_version=VERSION,reference_timestamp=oldm['observations'][0]['timestamp'],prior_manifest_sha256=sha(old/'investigation/manifest.json'))
            m['provenance']['source_header_audit']='reports/bangladesh_import_2026_11_03/source_audit.json';save(directory/'investigation/manifest.json',m)
            cal=calendar(case,m);save(directory/'calendar.json',cal)
            control_support=context(case,directory)
            build_dualpol(case,load(ROOT/'config.dualpol.json'),directory/'dualpol-v1',palettes,source_directory=directory/'investigation',audit_path=REPORT/'covariance_inventory.json')
            supports=evidence(case,directory);ref=references(case,directory)
            prefix=f'/cases/{case}/{VERSION}'
            row.update(record_version=VERSION,manifest_url=prefix+'/investigation/manifest.json',record_base=prefix,calendar_url=prefix+'/calendar.json')
            # Remove local acquisition discovery fields from the active public registry.
            row['source_files']=[];row['source_directory']='database/bangladesh-shared + database/new'
            registry['cases']=[row if r['case_id']==case else r for r in registry['cases']]
            summary[case]={'observations':10,'reference_timestamp':m['reference_timestamp'],'control_support':control_support,'saved_footprint_support':supports,'references':ref,'calendar_statuses':{k:sum(s['status']==k for s in cal['slots']) for k in ['observed','instrument_gap','not_in_hand','unavailable_in_archive']}}
        # Stage paths are provenance identifiers, rewritten to their permanent locations.
        for case in CASES:
            src=stage/case;oldprefix=str(src.relative_to(ROOT));newprefix=f'web/public/cases/{case}/{VERSION}'
            for path in src.rglob('*.json'):
                text=path.read_text()
                if oldprefix in text:path.write_text(text.replace(oldprefix,newprefix))
        for case in CASES:shutil.move(str(stage/case),str(parent/case/VERSION))
        stage.rmdir()
        registry.update(record_version=VERSION,prior_registry='investigations.json')
        save(parent/('investigations-'+VERSION+'.json'),registry)
        save(REPORT/'build.json',{'version':VERSION,'cases':summary,'status':'BUILT_NOT_ACTIVATED','science_scope':'Four added GCOV dates; no new GUNW, optical, thermal or rain measurements.'})
        print('Built',VERSION,'— validate before activation',flush=True)
    except Exception:
        print('Build failed; staging retained for diagnosis:',stage,flush=True);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args();build(args.resume)
