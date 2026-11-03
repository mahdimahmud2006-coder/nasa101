"""Audit the four supplied Bangladesh files against the accepted physical series."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import h5py
from src.compute.evidence_common import ROOT,load,save,sha
from src.ingest.timeseries import read_observation,incompatibilities
from src.ingest.inspect_h5 import native
from src.compute.investigation_pipeline import processing_release

OUT=ROOT/'reports/bangladesh_import_2026_11_03'
def audit():
    original=load(ROOT/'web/public/cases/jamuna_river/investigation/manifest.json')
    anchor=read_observation(ROOT/'database/bangladesh-shared'/(original['observations'][0]['source_granule_id']+'.h5'))
    expected={r['granule_id']:r for r in load(ROOT/'web/public/cases/bangladesh-missing-gcov-v1.json')['downloads']}
    records=[]
    for path in sorted((ROOT/'database/new').glob('*.h5')):
        before=path.stat();row=read_observation(path);row['source_file']=str(path.relative_to(ROOT))
        reasons=incompatibilities(anchor,row)
        if row['granule_id'] not in expected:reasons.append('Not a requested Bangladesh gap acquisition')
        if processing_release(row['granule_id'])!='P05023':reasons.append('Unexpected processing release')
        with h5py.File(path) as f:
            ident={k:native(v[()]) for k,v in f['science/LSAR/identification'].items() if isinstance(v,h5py.Dataset)}
            grids={}
            for freq in ['frequencyA','frequencyB']:
                g=f['science/LSAR/GCOV/grids/'+freq]
                actual={k:{'path':g[k].name,'dtype':str(g[k].dtype),'shape':list(g[k].shape)} for k in g if k in ['HHHH','HVHV','HHHV','HVHH','HVVV','HHVV','VVVV']}
                off=[k for k in actual if k not in ['HHHH','HVHV']]
                listed=native(g['listOfCovarianceTerms'][()])
                grids[freq]={'group_path':g.name,'listed_terms':listed,'actual_covariance_datasets':actual,'off_diagonal_terms':off,'listed_vs_present_agree':set(listed)==set(actual)}
                if freq=='frequencyA' and (off or set(actual)!={'HHHH','HVHV'}):reasons.append('Unexpected covariance branch')
            inputs={}
            def visit(name,obj):
                if isinstance(obj,h5py.Dataset) and '/metadata/' in name and any(t in name.lower() for t in ['source','dem','watermask']):
                    if obj.size<=16 and obj.dtype.kind in 'OSU':inputs[name]=native(obj[()])
            f.visititems(visit)
        for key in ['hasInputDataException']:
            if ident.get(key)!=0:reasons.append('Input-data exception')
        after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):reasons.append('File changed during metadata read')
        records.append({**row,'size_bytes':before.st_size,'processing_release':processing_release(row['granule_id']),'identification':ident,'covariance_grids':grids,'declared_inputs':inputs,'file_stat_stable_during_read':True,'acceptance_reasons':reasons,'metadata_compatible':not reasons})
        print(path.name,'PASS' if not reasons else reasons,flush=True)
    if len(records)!=4 or any(r['acceptance_reasons'] for r in records) or {r['granule_id'] for r in records}!=set(expected):raise ValueError('Four distinct requested, compatible GCOV files required')
    old=load(ROOT/'reports/phase0_2026_11_02/granule_covariance_inventory.json')
    save(OUT/'source_audit.json',{'schema_version':1,'records':records,'scope':'Actual local headers, physical comparability, covariance schema and stable file stats. Crop coverage checked at extraction. Full raw-file cryptographic integrity and provider authenticity are not certified.','source_policy':'NASA/ASF USA; NASA–ISRO USA/India. Review declared auxiliary lineage retained here; not a certificate of every upstream contributor.'})
    save(OUT/'covariance_inventory.json',{'records':old['records']+records,'prior_inventory_sha256':sha(ROOT/'reports/phase0_2026_11_02/granule_covariance_inventory.json')})
    print('Accepted metadata:',len(records))
if __name__=='__main__':audit()
