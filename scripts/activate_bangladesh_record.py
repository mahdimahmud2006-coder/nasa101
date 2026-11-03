"""Activate only a native-validated record via one atomic, reversible local pointer."""
from pathlib import Path
import json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.compute.evidence_common import ROOT,load,save,sha
from src.compute.bangladesh_record import VERSION,CASES,REPORT

def activate():
    qa=load(REPORT/'native_validation.json')
    if qa['status']!='BANGLADESH_TEN_VISIT_NATIVE_CHECKS_PASS':raise ValueError('Native validation required')
    for path,digest in qa['record_manifests_sha256'].items():
        if sha(ROOT/path)!=digest:raise ValueError('Record changed after validation: '+path)
    name='investigations-'+VERSION+'.json';registry=load(ROOT/'web/public/cases'/name)
    for case in CASES:
        row=next(r for r in registry['cases'] if r['case_id']==case)
        if row['record_version']!=VERSION or row['observation_count']!=10:raise ValueError('Registry binding disagrees')
    current=ROOT/'config.records.json'
    if current.exists():raise FileExistsError('An active record pointer already exists; explicitly review the next upgrade')
    tmp=ROOT/'config.records.json.tmp';save(tmp,{'schema_version':1,'investigation_registry':name,'cases':{c:VERSION for c in CASES},'native_validation':'reports/bangladesh_import_2026_11_03/native_validation.json','historical_registry':'investigations.json'})
    os.replace(tmp,current)
    save(REPORT/'activation.json',{'status':'ACTIVE_LOCAL','version':VERSION,'cases':CASES,'pointer_sha256':sha(current),'registry_sha256':sha(ROOT/'web/public/cases'/name),'native_validation_sha256':sha(REPORT/'native_validation.json')})
    print('Activated local',VERSION)
if __name__=='__main__':activate()
