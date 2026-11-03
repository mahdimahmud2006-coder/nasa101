"""Bounded scientific IMERG V07 catalog checks for each case's exact requested period."""
import sys,json,hashlib
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.compute.evidence_common import load,save

def run():
    dest=ROOT/'data/context/context-v2/rain_availability.json'
    if dest.exists():raise FileExistsError(dest)
    rows={}
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        m=load(ROOT/f'web/public/cases/{case}/investigation/manifest.json');obs=m['observations'];start=datetime.fromisoformat(obs[0]['timestamp'].replace('Z','+00:00'))-timedelta(hours=168)
        q={'short_name':'GPM_3IMERGHH','version':'07','temporal':start.isoformat().replace('+00:00','Z')+','+obs[-1]['timestamp'],'bounding_box':','.join(map(str,m['grid']['bounds_wgs84'])),'page_size':1}
        url='https://cmr.earthdata.nasa.gov/search/granules.json?'+urlencode(q);record={'query':q,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'provider':'NASA GES DISC / NASA Earthdata (USA)','upstream':'NASA GPM IMERG multisatellite product; individual sensors require provenance review before acceptance','license':'NASA Earth science open data; DOI 10.5067/GPM/IMERG/3B-HH/07'}
        try:
            with urlopen(url,timeout=30) as r:
                b=r.read(3000000);record.update(http_status=r.status,hits=int(r.headers['CMR-Hits']),response_sha256=hashlib.sha256(b).hexdigest())
                response=dest.parent/'sources'/f'{case}_imerg_query.response.json';response.write_bytes(b);record['response_path']=str(response.relative_to(ROOT));record['status']='unavailable';record['reason']='no matching scientific V07 granules in the completed bounded catalog query' if record['hits']==0 else 'scientific granules cataloged; authenticated subset and upstream sensor provenance not yet accepted'
        except Exception as e:record.update(status='unavailable',reason='catalog request failed; availability unknown',error=str(e))
        rows[case]=record;print(case,record.get('hits'),record['reason'],flush=True)
    save(dest,{'dataset':'GPM_3IMERGHH V07 scientific half-hourly','native_resolution_degrees':.1,'source_units':'mm/hr','bin_seconds':1800,'cases':rows,'accepted_scientific_files':0,'excluded':'Earlier IMERG GIS zero-filled diagnostics remain excluded; POWER is not substituted as IMERG.'})
if __name__=='__main__':run()
