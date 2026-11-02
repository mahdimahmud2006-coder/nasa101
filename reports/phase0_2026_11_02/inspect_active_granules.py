"""Inspect current configured inputs only; never read the large science arrays or rewrite outputs.
Run: PYTHONPATH=. .venv/bin/python reports/phase0_2026_11_02/inspect_active_granules.py
"""
from pathlib import Path
import hashlib,json,re
from datetime import datetime
from zoneinfo import ZoneInfo
import h5py
from src.compute.investigation_pipeline import sources_for,processing_release
from src.ingest.timeseries import read_observation,incompatibilities
from src.ingest.inspect_h5 import native

root=Path.cwd();config=json.loads((root/'config.investigations.json').read_text())
paths={}
for case in config['cases']:
 for path in sources_for(case,root):paths.setdefault(path,[]).append(case['case_id'])
records=[]
for path,cases in sorted(paths.items(),key=lambda item:str(item[0])):
 before=path.stat();item=read_observation(path,'frequencyA','HHHH')
 record={key:item[key] for key in ['granule_id','acquisition_start','acquisition_end','product','level','track','frame','orbit_direction','look_direction','product_version','specification_version','frequency','range_bandwidth_hz','center_frequency_hz','source_polarizations','dithered','doi','crs','shape','spacing','origin_center']}
 record.update(source_file=str(path.relative_to(root)),size_bytes=before.st_size,processing_release=processing_release(item['granule_id']),used_by_cases=cases)
 grids={}
 with h5py.File(path,'r') as source:
  record['has_ssar_group']='/science/SSAR' in source
  for frequency in source['/science/LSAR/GCOV/grids']:
   group=source['/science/LSAR/GCOV/grids/'+frequency]
   if not isinstance(group,h5py.Group):continue
   actual=[name for name in group if re.fullmatch('[HV]{4}',name) and isinstance(group[name],h5py.Dataset)]
   listed=native(group['listOfCovarianceTerms'][()]) if 'listOfCovarianceTerms' in group else None
   grids[frequency]={'group_path':group.name,'listed_terms':listed,'actual_covariance_datasets':{term:{'path':group[term].name,'dtype':str(group[term].dtype),'shape':list(group[term].shape)} for term in actual},'off_diagonal_terms':[term for term in actual if term[:2]!=term[2:]],'listed_vs_present_agree':sorted(listed)==sorted(actual) if isinstance(listed,list) else False}
 record['covariance_grids']=grids
 after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Input changed during read'
 record['file_stat_stable_during_read']=True;records.append(record)
 print(record['source_file'],{freq:list(g['actual_covariance_datasets'])for freq,g in grids.items()},flush=True)
series=[]
for track,frame in sorted({(r['track'],r['frame'])for r in records}):
 rows=sorted([r for r in records if (r['track'],r['frame'])==(track,frame)],key=lambda r:r['acquisition_start'])
 series.append({'track':track,'frame':frame,'observation_count':len(rows),'release_strings':sorted({r['processing_release']for r in rows}),'product_versions':sorted({r['product_version']for r in rows}),'timestamps_utc':[r['acquisition_start']for r in rows]})
off=[{'granule_id':r['granule_id'],'frequency':freq,'terms':g['off_diagonal_terms']}for r in records for freq,g in r['covariance_grids'].items() if g['off_diagonal_terms']]
report={'inspection_date_local':'2026-11-02','timezone':'Asia/Dhaka','inspected_at':datetime.now(ZoneInfo('Asia/Dhaka')).isoformat(),'scope':'Nine unique actively configured GCOV inputs across four cases; other local raw products are outside the active series. Header/dataset existence and dtype inspection, not large-array covariance science.','records':records,'series':series,'off_diagonal_datasets_found':off,'phase_2_branch':'OFF_DIAGONAL_METHOD_CANDIDATES_REQUIRE_FORMULATION_REVIEW' if off else 'DIAGONAL_ONLY_PROXIES_NO_DPRVI_OR_M_CHI','new_datasets_downloaded':0,'source':'User-supplied NASA–ISRO NISAR products, matching the existing NASA Earthdata / ASF record; no new external source queried.','limitation':'Stat stability and schema checks do not constitute full-file cryptographic verification. Large source HDF5 files are inputs and are not included in the processed-output baseline.'}
(root/'reports/phase0_2026_11_02/granule_covariance_inventory.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(report['phase_2_branch'],flush=True)
