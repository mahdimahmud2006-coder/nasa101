#!/usr/bin/env python3
"""Search ASF metadata only. No authentication or radar download. New output directory required."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ingest.nisar_slots import build_calendar, screen_candidate


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def run(config, output):
    import asf_search as asf
    from shapely.geometry import shape
    from shapely import wkt
    if output.exists():
        raise FileExistsError(f'Refusing to replace an archive snapshot: {output}. Choose a new --output directory.')
    output.mkdir(parents=True)
    gap = json.loads((ROOT/config['gap_source']).read_text())
    snapshot = ROOT/gap['snapshot_path']
    if hashlib.sha256(snapshot.read_bytes()).hexdigest() != gap['sha256']:
        raise ValueError('Official gap-source snapshot checksum mismatch')
    all_calendars = {}
    for series in config['series']:
        features, queries = {}, []
        for crop in series['crops']:
            query = dict(dataset='NISAR', processingLevel='GCOV', relativeOrbit=series['track'],
                         frame=series['frame'], flightDirection='ASCENDING', intersectsWith=crop['wkt'],
                         start=series['start'], end=series['end'])
            record = {'case_id': crop['case_id'], 'parameters': query, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                      'client': 'asf_search', 'client_version': asf.__version__,
                      'provider': 'ASF DAAC, University of Alaska Fairbanks, USA; NASA Earthdata CMR',
                      'upstream': 'NASA–ISRO NISAR (USA/India)',
                      'license': 'NASA Earth science data are openly available; cite NISAR GCOV DOI 10.5067/NIL2GCOV-P1 and ASF DAAC.',
                      'license_url': 'https://earthdata.nasa.gov/s3fs-public/2022-05/2022-03ADMGWorkshop_OSS.pdf',
                      'search_only': True}
            try:
                results = asf.search(**query)
                record['effective_intersectsWith'] = results.searchOptions.intersectsWith
                record['aoi_note'] = 'ASF client may simplify/reverse the polygon for search; overlap screening uses the original densified native crop polygon.'
                raw = results.geojson()
                rawpath = output/'raw'/f'{crop["case_id"]}.json'
                write(rawpath, raw)
                record.update(status='complete' if results.searchComplete else 'incomplete', count=len(results), response_path=str(rawpath.relative_to(ROOT)) if rawpath.is_relative_to(ROOT) else str(rawpath),
                              response_sha256=hashlib.sha256(rawpath.read_bytes()).hexdigest())
                for f in raw['features']:
                    features[f['properties']['sceneName']] = f
            except Exception as error:
                record.update(status='error', error=f'{type(error).__name__}: {error}')
            queries.append(record)
        candidates = []
        for f in features.values():
            coverage = {c['case_id']: shape(f['geometry']).intersection(wkt.loads(c['wkt'])).area / wkt.loads(c['wkt']).area for c in series['crops']}
            row = screen_candidate(f, series, coverage)
            row['in_hand'] = row['granule_id'] in {o['source_granule_id'] for o in series['observations']}
            candidates.append(row)
        candidates.sort(key=lambda r:(r['timestamp'] or '',r['granule_id']))
        record = {'schema_version':1, 'series_id':series['series_id'], 'criteria':{k:series[k] for k in ('track','frame','direction','mode','release')},
                  'queries':queries,'candidates':candidates,'downloaded_files':0}
        write(output/(series['series_id']+'.json'),record)
        calendar = build_calendar(series, series['observations'], candidates, queries, [gap])
        calendar['candidate_snapshot'] = str(output/(series['series_id']+'.json'))
        all_calendars[series['series_id']] = calendar
        write(output/(series['series_id']+'_calendar.json'),calendar)
        print(series['series_id'], len(candidates), 'candidates;', {s:sum(r['status']==s for r in calendar['slots']) for s in ['observed','instrument_gap','not_in_hand','unavailable_in_archive']}, flush=True)
    write(output/'calendars.json', {'schema_version':1, 'series':all_calendars})
    return 0 if all(c['search_complete'] for c in all_calendars.values()) else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config.time-axis.json')
    parser.add_argument('--output',type=Path,default=ROOT/'data/candidates/phase1_2026_11_02_final')
    args=parser.parse_args()
    raise SystemExit(run(json.loads(args.config.read_text()),args.output.resolve()))
