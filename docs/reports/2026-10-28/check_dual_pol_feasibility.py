from pathlib import Path
import json,copy,sys
sys.path.insert(0,str(Path.cwd()))
import h5py,numpy as np,rasterio
from src.ingest.extract_gcov import extract,analysis_window
from src.compute.preprocess import median_db
config=json.loads(Path('config.json').read_text())
audit=json.loads(Path('data/derived/nepal_case_01/timeseries/source_audit.json').read_text())
with rasterio.open('data/derived/nepal_case_01/timeseries/zone_labels.tif') as ds:zone=ds.read(1)==1
records=[];images=[]
for name in config['source_files']:
 ob=copy.deepcopy(next(r for r in audit['records'] if r['source_file']==name));ob['covariance_term']='HVHV';ob['polarization']='HV';ob['layer_path']=ob['grid_path']+'/HVHV'
 with h5py.File(name,'r') as f:
  if ob['layer_path'] not in f:raise ValueError('HV layer missing')
  dtype=str(f[ob['layer_path']].dtype);shape=list(f[ob['layer_path']].shape)
 window,affine=analysis_window(ob,config['aoi_center_wgs84'],config['aoi_size_m'])
 image,quality=extract(Path(name),ob,window);filtered=median_db(image,config['change']['median_filter_size']);images.append(filtered)
 records.append({'source_file':name,'granule_id':ob['granule_id'],'timestamp':ob['acquisition_start'],'dataset_path':ob['layer_path'],'dtype':dtype,'shape':shape,'valid_fraction':float(np.isfinite(filtered).mean()),'window_sha256':quality['window_sha256']})
 print('HV checked:',name,records[-1]['valid_fraction'],flush=True)
common=zone & np.all(np.isfinite(images),axis=0)
for i,image in enumerate(images):
 delta=(image-images[0])[common]
 records[i]['hh_selected_zone_hv_mean_delta_db']=float(delta.astype('float64').mean()) if delta.size else None
 records[i]['hh_selected_zone_hv_mean_absolute_delta_db']=float(np.abs(delta).astype('float64').mean()) if delta.size else None
result={'status':'ACTUAL_EXISTING_HV_LAYER_AOI_CHECKED','records':records,'zone_common_native_pixels':int(common.sum()),'interpretation':'Feasibility/exploratory summary only. Zone was selected by HH changes, so HV agreement is not an independent event label. No physical cause, confidence or new classification inferred. Both frequency A and B here are L-band subbands, not L-band/S-band pairing.'}
Path('docs/reports/2026-10-28/dual_pol_feasibility.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps(result,indent=2))
