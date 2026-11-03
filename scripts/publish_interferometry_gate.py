"""Review staged NASA catalogs and make a bounded unauthenticated access probe."""
import sys,json,os
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.compute.evidence_common import load,save,sha
from src.compute.interferometry_gate import screen_candidate,gate_verdict

def run():
    output=ROOT/'web/public/cases/interferometry-v2.json'
    if output.exists():raise FileExistsError(output)
    original=load(ROOT/'data/candidates/interferometry_phase6_v1/gate.json');records=[]
    for series in load(ROOT/'config.time-axis.json')['series']:
        for product in ['GUNW','GSLC']:
            previous=next(r for r in original['records'] if r['series_id']==series['series_id'] and r['product']==product)
            path=ROOT/previous['response_path'];raw=load(path)
            candidates=[screen_candidate(f['properties'],series,product) for f in raw['features']]
            records.append({'series_id':series['series_id'],'case_ids':series['case_ids'],'product':product,'search_complete':previous['search_complete'],
                'catalog_count':len(candidates),'eligible_catalog_count':sum(c['catalog_eligible'] for c in candidates),
                'response_path':previous['response_path'],'response_sha256':sha(path),'query':previous['query'],'catalog_retrieved_at':previous['retrieved_at'],
                'provider':previous['provider'],'upstream':previous['upstream'],'license':previous['license'],
                'candidates':candidates,'note':'An incomplete search cannot establish absence. Eligibility is a metadata screen, not acceptance.'})
    candidate=next(c for r in records if r['product']=='GUNW' for c in r['candidates'] if c['catalog_eligible'])
    probe={'url':candidate['url'],'request':'GET Range bytes=0-7; at most 8 response bytes read, then connection closed',
           'retrieved_at':datetime.now(timezone.utc).isoformat(),'authentication':'No secrets read or submitted; unauthenticated probe only.',
           'local_auth_configuration_present':(Path.home()/'.netrc').exists() or any(bool(os.environ.get(k)) for k in ['EARTHDATA_TOKEN','EARTHDATA_USERNAME','EARTHDATA_PASSWORD'])}
    cached=ROOT/'data/candidates/interferometry_phase6_v2/access_probe.json'
    if cached.exists():
        probe=load(cached)
    else:
        try:
            assert urlsplit(candidate['url']).hostname=='nisar.asf.earthdatacloud.nasa.gov'
            with urlopen(Request(candidate['url'],headers={'Range':'bytes=0-7'}),timeout=30) as response:
                first=response.read(8)
                probe.update(http_status=response.status,bytes_read=len(first),response_prefix_sha256=__import__('hashlib').sha256(first).hexdigest(),final_host=urlsplit(response.url).hostname,
                             content_type=response.headers.get('Content-Type'),content_range=response.headers.get('Content-Range'),
                             hdf5_signature=first==b'\x89HDF\r\n\x1a\n',science_subset_accepted=False)
        except HTTPError as e:probe.update(http_status=e.code,bytes_read=0,error_type='HTTPError',science_subset_accepted=False)
        except Exception as e:probe.update(http_status=None,bytes_read=0,error_type=type(e).__name__,science_subset_accepted=False)
    result=gate_verdict(records,probe);result['screened_at']=datetime.now(timezone.utc).isoformat()
    save(ROOT/'data/candidates/interferometry_phase6_v2/gate-reviewed.json',result);save(output,result)
    print(json.dumps({'records':[{k:r[k] for k in ['series_id','product','catalog_count','eligible_catalog_count','search_complete']} for r in records], 'probe':probe,'gate_open':False},indent=2))

if __name__=='__main__':run()
