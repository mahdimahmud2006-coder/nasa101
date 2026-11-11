"""Read NASA CMR catalog metadata only; no login or science-data downloads."""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://cmr.earthdata.nasa.gov/search/granules.json'
COLLECTION = 'GPM_3IMERGHH'
VERSION = '07'


def parse_date(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.utcoffset() != timedelta(0):
        raise ValueError('Expected UTC timestamp')
    return dt


def utc(dt):
    return dt.isoformat().replace('+00:00', 'Z')


def windows(records):
    by_source = {}
    for case_id, c in records.items():
        for obs in c['observations']:
            source = obs['source_granule_id']
            end = parse_date(obs['timestamp'])
            start = end - timedelta(hours=48)
            first = start.replace(minute=(start.minute // 30)*30, second=0, microsecond=0)
            bin_starts = []
            cursor = first
            while cursor < end:
                bin_starts.append(utc(cursor))
                cursor += timedelta(minutes=30)
            row = by_source.setdefault(source, {'source': source, 'country': c['country'], 'start_utc': utc(start),
                'end_utc': utc(end), 'expected_bin_starts': bin_starts, 'footprints': []})
            if row['end_utc'] != utc(end):
                raise ValueError('Conflicting dates for same source acquisition')
            row['footprints'].append({'case_id':case_id, 'bounds_wgs84':c['grid']['bounds_wgs84']})
    return sorted(by_source.values(),key=lambda w:(w['country'],w['end_utc']))


def search(row):
    requested = set(row['expected_bin_starts'])
    # Final is a global raster. A country bounding box is not needed for granule
    # discovery; region-specific QA/coverage is still required after retrieval.
    url = ENDPOINT+'?'+urlencode({'short_name':COLLECTION,'version':VERSION,
        'temporal':min(requested)+','+row['end_utc'],'page_size':200})
    try:
        with urlopen(url, timeout=15) as res:
            if urlsplit(res.geturl()).hostname != 'cmr.earthdata.nasa.gov':
                raise ValueError('Unexpected catalog redirect')
            raw = res.read(6_000_001)
            if len(raw)>6_000_000:
                raise ValueError('Catalog response exceeds metadata limit')
            hits = int(res.headers['CMR-Hits'])
        entries = json.loads(raw)['feed']['entry']
        if hits > len(entries):
            raise ValueError('Catalog response was incomplete; pagination required')
        matches = {}
        for e in entries:
            t = utc(parse_date(e['time_start']))
            if t not in requested:
                continue
            links = [a['href'] for a in e.get('links',[]) if not a.get('inherited',False)
                and urlsplit(a.get('href','')).scheme=='https'
                and urlsplit(a['href']).path.lower().endswith(('.h5','.hdf5'))]
            matches.setdefault(t,[]).append({'id':e['producer_granule_id'],'cmr_id':e['id'],
                'size_mb':e.get('granule_size'),'native_hdf_links':links})
        return {'query':url,'response_sha256':hashlib.sha256(raw).hexdigest(),'hits':hits,
            'coverage':'complete' if requested==matches.keys() else 'partial' if matches else 'not_cataloged',
            'matched_bins':len(matches),'bins_with_native_hdf_links':sum(any(v['native_hdf_links'] for v in a) for a in matches.values()),
            'matched':matches}
    except (OSError,ValueError,KeyError) as exc:
        return {'query':url,'coverage':'unknown','error':str(exc),'matched_bins':None}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'reports/development/part-03-imerg-catalog.json')
    out=parser.parse_args().output
    if out.exists():parser.error('Use a new --output path to preserve the prior catalog receipt')
    rows = windows(json.loads((ROOT/'web/atlas-record.json').read_text()))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(search,rows))
    for row, catalog in zip(rows,results):
        row['catalog'] = catalog
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'queried_utc':utc(datetime.now(timezone.utc)),
        'product':COLLECTION,'version':VERSION,'method':'NASA CMR public catalog metadata; no download',
        'lineage_status':'UNVERIFIED_EXCLUDED','windows':rows},indent=2)+'\n')
    print('Catalog coverage:',{x:sum(r['coverage']==x for r in results) for x in sorted({r['coverage'] for r in results})})


if __name__=='__main__':
    main()
