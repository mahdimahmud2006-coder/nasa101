"""Add diagonal-only products from existing canonical COGs to new versioned paths."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import numpy as np
import rasterio
from affine import Affine
import pyarrow as pa
import pyarrow.parquet as pq

from src.compute.dualpol import cpr_db, signed_difference, composite, hint_masks, threshold_sensitivity, profile_cpr
from src.compute.timeseries_pipeline import cog
from src.export.dualpol_render import load_palettes, palette_rgba, preview, rgba_cog, css_gradient

ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write(path,record):
    path.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')


def read_stack(directory,manifest):
    stacks={'hh':[],'hv':[]};inputs={}
    for o in manifest['observations']:
        for pol in stacks:
            path=directory/o['rasters'][pol]
            with rasterio.open(path) as ds:
                if list(ds.shape)!=manifest['grid']['shape'] or ds.transform!=Affine(*manifest['grid']['affine']) or ds.crs.to_string()!=manifest['grid']['crs']:
                    raise ValueError('Canonical input grid mismatch: '+str(path))
                arr=ds.read(1,masked=True).filled(np.nan).astype('float32')
                stacks[pol].append(arr)
            inputs[str(path.relative_to(ROOT))]=sha(path)
    return np.stack(stacks['hh']),np.stack(stacks['hv']),inputs


def summarize(values,limits):
    valid=np.isfinite(values);n=int(valid.sum())
    return {'valid_pixels':n,'valid_fraction':n/valid.size,
            'below_display':int((valid & (values<limits[0])).sum()),
            'above_display':int((valid & (values>limits[1])).sum()),
            'minimum_db':float(values[valid].min()) if n else None,'maximum_db':float(values[valid].max()) if n else None}


def build(case_id,config,destination,palettes,config_path='config.dualpol.json',source_directory=None,audit_path=None):
    source=Path(source_directory) if source_directory else ROOT/f'web/public/cases/{case_id}/investigation'
    original=json.loads((source/'manifest.json').read_text())
    audit_path=Path(audit_path) if audit_path else ROOT/'reports/phase0_2026_11_02/granule_covariance_inventory.json'
    audited=json.loads(audit_path.read_text())['records']
    audited={r['granule_id']:r for r in audited}
    for obs in original['observations']:
        record=audited[obs['source_granule_id']]
        terms=record['covariance_grids']['frequencyA']
        if terms['off_diagonal_terms'] or set(terms['actual_covariance_datasets'])!={'HHHH','HVHV'}:
            raise ValueError('This pipeline requires the audited diagonal-only branch')
        if any(obs[key]!=record[{'processing_release':'processing_release','product_version':'product_version','track':'track','frame':'frame'}[key]] for key in ('processing_release','product_version','track','frame')):
            raise ValueError('Manifest disagrees with raw-file audit')
    hh,hv,inputs=read_stack(source,original)
    paired=np.isfinite(hh)&np.isfinite(hv);common=paired.all(axis=0)
    cpr=cpr_db(hh,hv);grid=original['grid'];area=grid['pixel_area_km2'];affine=Affine(*grid['affine'])
    destination.mkdir(parents=True)
    offsets=np.asarray(config['sensitivity_offsets_db']);settings=config['hints'];limits=config['display_limits']
    sensitivity=[];observations=[]
    for i,obs in enumerate(original['observations']):
        print(case_id,obs['timestamp'],'dual-pol',flush=True)
        row={k:obs[k] for k in ('observation_id','timestamp','source_granule_id')};row.update(layers={},rasters={},display_statistics={})
        fields={'hh_fixed':hh[i],'hv_fixed':hv[i],'cpr':cpr[i]}
        for name,values in [('hh',hh),('hv',hv),('cpr',cpr)]:
            fields[name+'_baseline']=signed_difference(values[i],values[0],paired[i]&paired[0])
            if i:fields[name+'_successive']=signed_difference(values[i],values[i-1],paired[i]&paired[i-1])
        for layer,values in fields.items():
            change=layer.endswith(('_baseline','_successive'))
            scale=limits['change' if change else layer.removesuffix('_fixed')]
            palette=palettes['vik' if change else 'cividis']
            file=f'{layer}_{i}'
            cog(destination/(file+'.tif'),values,affine,grid['crs'],layer+'; filtered log-power dB; paired-valid comparison endpoints' if change else layer+'; filtered log-power dB')
            preview(destination/(file+'.png'),palette_rgba(values,scale,palette))
            row['layers'][layer]=file+'.png';row['rasters'][layer]=file+'.tif'
            row['display_statistics'][layer]=summarize(values,scale)
        rgb=composite(hh[i],hv[i],limits)
        preview(destination/f'composite_{i}.png',rgb);rgba_cog(destination/f'composite_{i}.tif',rgb,affine,grid['crs'])
        row['layers']['composite']=f'composite_{i}.png';row['rasters']['composite']=f'composite_{i}.tif'
        hints=hint_masks(hh[i],hv[i],hh[0] if i else None,hv[0] if i else None,settings)
        cog(destination/f'hint_bits_{i}.tif',hints['bits'],affine,grid['crs'],'Uncalibrated signature flags: 1 low-return, 2 HH rise/stable HV, 4 HV rise; 255 invalid',255,True)
        row['rasters']['hint_bits']=f'hint_bits_{i}.tif';row['hint_statistics']={}
        for name,bit in [('hint_low',1),('hint_hh',2),('hint_hv',4)]:
            support=hints['current_valid'] if bit==1 else hints['change_valid']
            if support is None:
                row['layers'][name]=None;row['hint_statistics'][name]=None;continue
            mask=(hints['bits']!=255)&((hints['bits']&bit)!=0)&support
            n,count=int(support.sum()),int(mask.sum())
            values=np.where(support,mask.astype('float32'),np.nan)
            preview(destination/f'{name}_{i}.png',palette_rgba(values,[0,1],palettes['cividis']))
            row['layers'][name]=f'{name}_{i}.png'
            row['hint_statistics'][name]={'candidate_pixels':count,'candidate_area_km2':count*area if n else None,'assessable_pixels':n,'assessable_area_km2':n*area,'status':'measured' if n else 'unavailable','interpretation_status':'hypothesized'}
        sweep=threshold_sensitivity(hh[i],hv[i],common,area,settings['hh_low_db']+offsets,settings['hv_low_db']+offsets)
        sweep.update(timestamp=obs['timestamp'],observation_id=obs['observation_id']);sensitivity.append(sweep)
        observations.append(row)
    profiles=[profile_cpr(p) for p in original['profiles']]
    rows=[dict(profile_index=i,profile_label=p['label'],profile_status=p['status'],common_valid_pixels=p['common_valid_pixels'],common_valid_area_km2=p['measured_area_km2'],**r) for i,p in enumerate(profiles) for r in p['observations']]
    table=pa.Table.from_pylist(rows)
    table=table.replace_schema_metadata({b'cpr_definition':b'HV_dB-HH_dB; fixed all-visits common-valid mean of filtered log-power ratios',b'status':b'measured; physical explanation remains hypothesized'})
    pq.write_table(table,destination/'profiles.parquet');write(destination/'profiles.json',profiles)
    write(destination/'sensitivity.json',{'schema_version':1,'case_id':case_id,'offsets_db':offsets.tolist(),'nominal_hh_db':settings['hh_low_db'],'nominal_hv_db':settings['hv_low_db'],'calibration_status':'UNCALIBRATED','support':'identical paired-valid pixels across all dates; crop-wide, not selected footprint','observations':sensitivity})
    inputs[str((source/'manifest.json').relative_to(ROOT))]=sha(source/'manifest.json')
    inputs[str(audit_path.relative_to(ROOT))]=sha(audit_path)
    manifest={'schema_version':1,'product_version':config['product_version'],'case_id':case_id,'status':'implemented','grid':grid,'observations':observations,'profiles':profiles,
              'display_limits':limits,'palette_css':{key:css_gradient(value) for key,value in palettes.items()},'composite':config['composite'],'hints':settings,
              'hint_definitions':{'hint_low':'Low-return candidate: HH <= -17 AND HV <= -24 dB. Consistent with smooth/specular surfaces; dry smooth ground and shadow are alternatives.',
                                  'hint_hh':'HH-brightening/stable-HV candidate: baseline delta HH >= 3 dB AND abs(delta HV) <= 1 dB. A double-bounce-like candidate, not an identified scattering mechanism.',
                                  'hint_hv':'HV-rise candidate: baseline delta HV >= 3 dB. Consistent with changed depolarization/vegetation structure, with wetness, geometry and calibration alternatives.'},
              'formulas':{'cpr':'HV_dB - HH_dB = 10 log10(HVHV/HHHH), from independently median-filtered log-powers. Sign reversal of the preserved HH-HV ratio; not independent information.',
                          'baseline':'quantity(t)-quantity(first loaded visit), on paired-valid endpoint intersection',
                          'successive':'quantity(t)-quantity(previous loaded visit), on paired-valid endpoint intersection; unavailable on first visit',
                          'composite':'R=HH [-30,0]; G=HV [-40,-5]; B=HH-HV [0,20] dB. Linear clipped uint8 RGB; alpha is paired-valid.'},
              'limits':['Diagonal-only HH/HV proxies; no off-diagonal covariance, DpRVI or m-chi decomposition.',
                        'All hints are illustrative and uncalibrated, may overlap, and have competing physical explanations. No class or cause is identified.',
                        'Low-return support is current paired-valid pixels; change hints require paired-valid baseline and current endpoints.',
                        'The false-colour RGB channels are not separate physical measurements. Colour is a descriptive composite, not a categorical map.',
                        'Fixed stretches can saturate; display saturation counts are recorded. Full COG numerical values are never clipped.',
                        'Sensitivity sweeps hold the all-visits common-valid footprint fixed; their area can differ from current-visit-valid areas in the preserved original panel.',
                        'Missing values remain unavailable. No coherence, displacement or accuracy is inferred.'],
              'references':['https://nisar-docs.asf.alaska.edu/gcov/','https://science.nasa.gov/mission/nisar/polarimetry/','https://www.fabiocrameri.ch/colourmaps/'],
              'provenance':{'inputs_sha256':inputs,'config_sha256':sha(ROOT/config_path),'source_policy':config['source_policy'],'covariance_audit':str(audit_path.relative_to(ROOT)),'palettes':json.loads((ROOT/config['palette_directory']/'provenance.json').read_text()),
                            'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/compute/dualpol.py',ROOT/'src/export/dualpol_render.py']}}}
    manifest['provenance']['assets_sha256']={p.name:sha(p) for p in sorted(destination.iterdir()) if p.is_file()}
    write(destination/'manifest.json',manifest)
    return {'case_id':case_id,'manifest_url':f'/cases/{case_id}/{config["product_version"]}/manifest.json','observation_count':len(observations)}
