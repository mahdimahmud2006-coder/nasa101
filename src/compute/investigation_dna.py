"""Fixed-footprint Change DNA v2 and polygon evaluation on saved canonical inputs."""
from datetime import timedelta
from pathlib import Path
import numpy as np,rasterio
from rasterio.windows import Window
from rasterio.features import rasterize
from affine import Affine
from shapely.geometry import Polygon,mapping
from src.compute.evidence_common import ROOT,load
from src.compute.investigations import fixed_footprint_profile
from src.compute.dualpol import profile_cpr
from src.compute.explanation_fit import explanation_fit
from src.compute.context_v2 import utc,iso

def dna_signature(profile,absolute_hh,threshold=3):
    rows=profile['observations'];valid=[i for i,v in enumerate(absolute_hh) if v is not None and np.isfinite(v)];post=[i for i in valid if i>0];cross=[i for i in post if absolute_hh[i]>=threshold];first=cross[0] if cross else None
    onset=None
    if first is not None:
        preceding=[i for i in valid if i<first and absolute_hh[i]<threshold];prior=preceding[-1] if preceding else None
        onset={'last_observed_below':rows[prior]['timestamp'] if prior is not None else None,'first_observed_above':rows[first]['timestamp'],'left_censored':prior is None,'interpretation':'Threshold-crossing bracket between observed endpoints, not a physical event date.'}
    assessed=[i for i in valid if i>=first] if first is not None else post;k=sum(absolute_hh[i]>=threshold for i in assessed);n=len(assessed)
    peak=max((absolute_hh[i] for i in post),default=None);peak_i=next((i for i in post if absolute_hh[i]==peak),None);latest=absolute_hh[-1] if absolute_hh else None
    recovery=None if peak is None or peak<=0 or latest is None else float(np.clip(1-latest/peak,0,1));recovery_interval=None
    if peak_i is not None and peak>0:
        found=next((i for i in valid if i>peak_i and absolute_hh[i]<=peak/2),None)
        if found is not None:
            prior=max(i for i in valid if i<found);recovery_interval=[rows[prior]['timestamp'],rows[found]['timestamp']]
    return {'threshold_db':threshold,'threshold_status':'UNCALIBRATED','mean_abs_hh_baseline_db':absolute_hh,'onset_interval':onset,'persistence':{'k':int(k),'n':int(n),'fraction':k/n if n else None,'definition':'Threshold-exceeding visits of assessed observed post-onset visits; not continuous duration.'},'recovery_fraction':recovery,'recovery_half_crossing_interval':recovery_interval,'recovery_right_censored':recovery_interval is None,'coherence':None,'coherence_status':'planned','similar_past_cases':{'status':'unavailable','reason':'No independent validated event library; no historical matches inferred.'}}

def evaluate_window(case,mask,window,label,selection,root=ROOT,record_directory=None):
    root=Path(root);directory=Path(record_directory) if record_directory else root/f'web/public/cases/{case}'
    base=directory/'investigation';m=load(base/'manifest.json');channels={p:[] for p in ['hh','hv']}
    for obs in m['observations']:
        for p in channels:
            with rasterio.open(base/obs['rasters'][p]) as ds:channels[p].append(ds.read(1,window=window))
    hh,hv=np.stack(channels['hh']),np.stack(channels['hv']);p=profile_cpr(fixed_footprint_profile(hh,hv,mask,m['grid']['pixel_area_km2']))
    p.update(case_id=case,label=label,selection=selection,window={'row':int(window.row_off),'col':int(window.col_off),'height':int(window.height),'width':int(window.width)})
    for row,obs in zip(p['observations'],m['observations']):row.update(observation_id=obs['observation_id'],timestamp=obs['timestamp'])
    common=mask&np.isfinite(hh).all(0)&np.isfinite(hv).all(0);eligible=p['status']=='MEASURED';absolute=[float(np.abs(hh[i][common]-hh[0][common]).astype('float64').mean()) if eligible else None for i in range(len(hh))]
    dna=dna_signature(p,absolute);context_path=directory/'context-v2/manifest.json';context=load(context_path) if context_path.exists() else None;terrain={}
    if context:
        for key in ['rain','radiometric_controls']:
            if [r['timestamp'] for r in context[key]]!=[o['timestamp'] for o in m['observations']]:raise ValueError('Context observation binding is stale')
    rr,cc=np.where(common);rr=(rr+int(window.row_off))//3;cc=(cc+int(window.col_off))//3
    for key in ['slope','dem']:
        path=context_path.parent/(key+'.tif')
        if path.exists() and len(rr):
            with rasterio.open(path) as ds:values=ds.read(1)[rr,cc]
            finite=values[np.isfinite(values)];terrain['median_'+('slope_degrees' if key=='slope' else 'elevation_m')]=float(np.median(finite)) if len(finite) else None
    slope=terrain.get('median_slope_degrees');terrain['class']='unavailable' if slope is None else 'low slope' if slope<5 else 'moderate slope' if slope<15 else 'steep footprint'
    dna['terrain']=terrain;dna['rain_context']=context['rain'] if context else None
    rules=load(root/'rules/explanations.yaml');calendar_path=directory/'calendar.json';calendar=load(calendar_path if calendar_path.exists() else root/'web/public/cases/time-axis-v1/calendars.json');cal=calendar if 'slots' in calendar else next(c for c in calendar['series'].values() if case in c['case_ids']);visits=[]
    for i,row in enumerate(p['observations']):
        dh,dv,dc=row['hh_baseline_delta_db'],row['hv_baseline_delta_db'],row['cpr_baseline_delta_db'];ctrl=context['radiometric_controls'][i] if context else {};offsets=[abs(ctrl[k]) for k in ['hh_baseline_shift_db','hv_baseline_shift_db'] if ctrl.get(k) is not None]
        facts={'hh_last_db':row['hh_mean_db'],'hv_last_db':row['hv_mean_db'],'hh_delta_db':dh,'hv_delta_db':dv,'hh_change_abs_db':abs(dh) if dh is not None else None,'hv_change_abs_db':abs(dv) if dv is not None else None,'cpr_change_abs_db':abs(dc) if dc is not None else None,'mean_abs_hh_change_db':absolute[i],'median_slope_degrees':slope,'rain_72h_mm':context['rain'][i]['imerg_72h_mm'] if context else None,'paired_darkening':dh<=-3 and dv<=-3 if dh is not None and dv is not None else None,'control_offset_abs_db':max(offsets) if offsets else None}
        fit=explanation_fit(facts,rules);future=next((s for s in cal['slots'] if s['nominal_timestamp']>row['timestamp'] and s['status'] not in ['observed','instrument_gap']),None);nextdate=future['date'] if future else iso(utc(cal['slots'][-1]['nominal_timestamp'])+timedelta(days=12))[:10]
        fit.update(observation_id=row['observation_id'],timestamp=row['timestamp'],facts=facts,next_evidence_needed=f'Load/inspect nominal visit {nextdate}, and obtain the independent evidence listed for each hypothesis. Nominal dates are not observations.')
        visits.append(fit)
    return {'profile':p,'record_version':m.get('record_version','original'),'dna':dna,'explanations':visits,'rules_version':rules['model_version'],'claim_status':'measured','explanation_status':'hypothesized','reference_status':'context overlap' if m.get('reference') else 'none','limitations':['Fixed-footprint means can hide opposing local changes; mean absolute HH change is also retained.','Onset and recovery are sampled brackets; persistent observed visits do not mean continuous monitoring.','Rule statuses describe this uncalibrated signature table, not physical truth or a ranked cause.','Rain unavailable remains unknown; no confidence probability is inferred.']}

def polygon_evidence(case,vertices,root=ROOT,record_directory=None):
    root=Path(root);directory=Path(record_directory) if record_directory else root/f'web/public/cases/{case}'
    m=load(directory/'investigation/manifest.json');height,width=m['grid']['shape'];points=np.asarray(vertices,dtype='float64')
    if points.ndim!=2 or points.shape[1]!=2 or not 3<=len(points)<=200 or not np.isfinite(points).all():raise ValueError('Polygon requires 3–200 finite [column,row] vertices')
    if (points[:,0]<0).any() or (points[:,0]>width).any() or (points[:,1]<0).any() or (points[:,1]>height).any():raise ValueError('Polygon outside case grid')
    polygon=Polygon(points)
    if not polygon.is_valid or polygon.is_empty or polygon.area<1:raise ValueError('Polygon must be valid and cover native pixel centers')
    left,top=np.floor(points.min(0)).astype(int);right,bottom=np.ceil(points.max(0)).astype(int);window=Window(left,top,right-left,bottom-top)
    if window.width*window.height>6000000:raise ValueError('Polygon window too large')
    mask=rasterize([(mapping(polygon),1)],out_shape=(int(window.height),int(window.width)),transform=Affine.translation(left,top),fill=0,dtype='uint8').astype(bool)
    if not mask.any():raise ValueError('Polygon contains no native pixel centers')
    result=evaluate_window(case,mask,window,'User-selected fixed polygon','User polygon; native pixel-center inclusion; not an independent reference.',root,directory)
    result['profile']['geometry_pixel']=mapping(polygon);return result
