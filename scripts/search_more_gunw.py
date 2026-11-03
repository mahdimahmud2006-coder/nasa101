"""Bounded NASA/ASF metadata search for additional pairs on dates already loaded."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.compute.evidence_common import load, save, sha
from src.compute.interferometry_gate import screen_candidate


def run():
    import asf_search as asf
    output=ROOT/'data/candidates/additional_gunw_2026_11_03'
    if output.exists():raise FileExistsError('Retain prior search; choose a new snapshot directory')
    output.mkdir(parents=True);records=[]
    in_hand={p.stem for p in (ROOT/'database/extra datasets').glob('*GUNW*.h5')}
    for original in load(ROOT/'config.time-axis.json')['series']:
        series=dict(original)
        if series['track']==98:
            series['observations']=load(ROOT/'web/public/cases/nepal_surface/expanded-v1/manifest.json')['observations']
        query={'dataset':'NISAR','processingLevel':'GUNW','relativeOrbit':series['track'],
               'frame':series['frame'],'flightDirection':'ASCENDING','intersectsWith':series['crops'][0]['wkt'],
               'start':'2026-06-17T00:00:00Z','end':'2026-10-20T23:59:59Z'}
        record={'series_id':series['series_id'],'query':query,'retrieved_utc':datetime.now(timezone.utc).isoformat(),
                'provider':'NASA Earthdata / ASF DAAC (USA)','upstream':'NASA–ISRO (USA/India)',
                'search_only':True,'downloaded_science_files':0}
        try:
            results=asf.search(**query);path=output/(series['series_id']+'.json');save(path,results.geojson())
            record.update(search_complete=results.searchComplete,response_path=str(path.relative_to(ROOT)),
                          response_sha256=sha(path),candidates=[])
            for f in results.geojson()['features']:
                c=screen_candidate(f['properties'],series,'GUNW');c['in_hand']=c['granule_id'] in in_hand
                if len(c['acquisition_starts'])==2:
                    c['interval_days']=(datetime.fromisoformat(c['acquisition_starts'][1])-datetime.fromisoformat(c['acquisition_starts'][0])).total_seconds()/86400
                record['candidates'].append(c)
            record['status']='complete' if results.searchComplete else 'incomplete'
        except Exception as e:record.update(status='error',error=str(e),search_complete=False,candidates=[])
        records.append(record);print(series['series_id'],record['status'],len(record['candidates']),flush=True)
    save(output/'search.json',{'records':records,'scope':'Catalog candidates only. Header/native-window verification required after download. None can restore the permanent NISAR outage.'})
    return 0 if all(r['search_complete'] for r in records) else 2


if __name__=='__main__':raise SystemExit(run())
