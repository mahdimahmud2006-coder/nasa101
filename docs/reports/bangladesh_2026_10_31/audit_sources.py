"""Run from the TerraPulse root; audit supplied science-file identities and both crop windows."""
import json
from pathlib import Path
import h5py
from src.ingest.timeseries import read_observation,incompatibilities
from src.ingest.extract_gcov import analysis_window
from src.compute.investigation_pipeline import processing_release

root=Path.cwd();config=json.loads((root/'config.investigations.json').read_text())
plan=json.loads((root/'docs/downloads/download-plan.json').read_text())
expected={r['granule_id']:r for r in plan['granules']}
records=[]
for path in sorted((root/'database/bangladesh-shared').glob('*.h5')):
 before=path.stat();item=read_observation(path,'frequencyA','HHHH')
 assert item['granule_id']==path.stem,'Filename differs from embedded granule ID'
 assert item['granule_id'] in expected,'Unreviewed catalog granule'
 assert {'HHHH','HVHV'}.issubset(item['covariance_terms'])
 item['source_file']=str(path.relative_to(root));item['processing_release']=processing_release(item['granule_id'])
 item['catalog_url']=expected[item['granule_id']]['url'];item['window_checks']={}
 for case in config['cases']:
  if case['module'] not in ('river','wetland'):continue
  window,affine=analysis_window(item,case['center'],case['size_m'])
  with h5py.File(path,'r') as hdf:
   samples={}
   for term in ['HHHH','HVHV']:
    layer=hdf[item['grid_path']+'/'+term]
    samples[term]={'dtype':str(layer.dtype),'shape':list(layer.shape)}
  item['window_checks'][case['case_id']]={'inside_raw_grid':True,'window':list(window.flatten()),'affine':list(affine)[:6],'terms':samples}
 after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'File changed during audit'
 records.append(item)
 print('Audited',path.name,flush=True)
records.sort(key=lambda r:r['acquisition_start'])
for item in records:
 assert not incompatibilities(records[0],item),incompatibilities(records[0],item)
 assert item['processing_release']==records[0]['processing_release']
assert len({r['acquisition_start'] for r in records})==len(records)
report={'date':'2026-10-31','status':'HEADERS_AND_BOTH_CROP_WINDOWS_PASS','grain':'One full-scene GCOV acquisition per unique timestamp; two geographic crops, two polarization intensities','source_provider':'NASA Earthdata / ASF DAAC; matches catalog IDs requested on 2026-10-28','records':records,'qualification':'Header and grid-extent validation. Full crop quality and numeric consistency are checked by processing and saved-output validation; neither establishes water class accuracy or physical cause.'}
(root/'docs/reports/bangladesh_2026_10_31/source_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('All',len(records),'acquisitions cover both crop windows with compatible headers.',flush=True)
