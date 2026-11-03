"""Search-only Gate A: catalog existence is distinct from feasible, accepted interferometry."""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import asf_search as asf

def run():
    output=ROOT/'data/candidates/interferometry_phase6_v1'
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);config=json.loads((ROOT/'config.time-axis.json').read_text());records=[]
    for series in config['series']:
        for product in ['GUNW','GSLC']:
            query={'dataset':'NISAR','processingLevel':product,'relativeOrbit':series['track'],'frame':series['frame'],'flightDirection':'ASCENDING','intersectsWith':series['crops'][0]['wkt'],'start':series['start'],'end':series['end']};record={'series_id':series['series_id'],'product':product,'query':query,'retrieved_at':datetime.now(timezone.utc).isoformat(),'provider':'NASA Earthdata / ASF DAAC, USA','upstream':'NASA–ISRO NISAR, USA/India','license':'NASA open Earth science data; product DOI must accompany any eventual accepted subset','downloaded_files':0}
            try:
                results=asf.search(**query);raw=results.geojson();path=output/f'{series["series_id"]}_{product}.json';path.write_text(json.dumps(raw,indent=2)+'\n');record.update(search_complete=results.searchComplete,count=len(results),response_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),response_path=str(path.relative_to(ROOT)),candidates=[])
                for f in raw['features']:
                    from src.compute.interferometry_gate import screen_candidate
                    record['candidates'].append(screen_candidate(f['properties'],series,product))
                record['status']='catalog_search_complete' if results.searchComplete else 'catalog_search_incomplete'
            except Exception as e:record.update(status='unavailable_query',error=str(e),search_complete=False,candidates=[])
            records.append(record);print(series['series_id'],product,record.get('count'),record['status'],flush=True)
    (output/'gate.json').write_text(json.dumps({'schema_version':1,'records':records,'gate_open':False,'claim_status':'planned','reason':'Search-only gate. No authenticated feasible subset, unwrapping quality, reference point or accepted coherence/displacement product is established. Catalog candidates are not implemented measurements.','coherence':None,'los_displacement_cm':None},indent=2)+'\n')
if __name__=='__main__':run()
