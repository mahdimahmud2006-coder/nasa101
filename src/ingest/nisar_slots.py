"""Nominal repeat slots and catalog screening; never infer unobserved measurements."""
from datetime import datetime, timedelta, timezone
import re

REPEAT_DAYS = 12
# Small acquisition-clock drift is not a different nominal orbit visit.
MATCH_TOLERANCE_SECONDS = 120
NAME = re.compile(r'^NISAR_L2_PR_GCOV_\d{3}_(\d{3})_([AD])_(\d{3})_(\d{4}_[A-Z]+_[A-Z])_(\d{8}T\d{6})_(\d{8}T\d{6})_([PX]\d{5})_')


def utc(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('UTC timestamp must include a timezone')
    return dt.astimezone(timezone.utc)


def stamp(value):
    return value.isoformat().replace('+00:00', 'Z')


def screen_candidate(feature, series, crop_coverage):
    """Conservative archive metadata screening; downloaded headers still need audit."""
    p = feature['properties']
    gid = p.get('sceneName', p.get('fileID', ''))
    match = NAME.match(gid)
    reasons = []
    parsed = {}
    if not match:
        reasons.append('unrecognized GCOV granule identifier')
    else:
        track, direction, frame, mode, start, end, release = match.groups()
        parsed = dict(track=int(track), frame=int(frame), direction=direction, mode=mode, release=release)
        for key in ('track', 'frame', 'direction', 'mode', 'release'):
            if parsed[key] != series[key]:
                reasons.append(f'{key}: {parsed[key]} != {series[key]}')
        expected_start = datetime.strptime(start, '%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc)
        if not p.get('startTime') or abs((utc(p['startTime'])-expected_start).total_seconds()) > 1:
            reasons.append('catalog timestamp disagrees with granule identifier')
    for key, expected in [('pathNumber', series['track']), ('frameNumber', series['frame']),
                          ('flightDirection', 'ASCENDING'), ('processingLevel', 'GCOV'),
                          ('collectionName', 'NISAR_L2_GCOV_PROVISIONAL_V1'), ('crid', series['release'])]:
        if p.get(key) != expected:
            reasons.append(f'catalog {key}: {p.get(key)} != {expected}')
    if p.get('rangeBandwidth') != ['40+5']:
        reasons.append('catalog bandwidth is not 40+5 MHz')
    if set(p.get('mainBandPolarization') or []) != {'HH', 'HV'}:
        reasons.append('main-band polarization is not HH/HV')
    if not crop_coverage or not all(v > 0 for v in crop_coverage.values()):
        reasons.append('catalog footprint does not intersect every configured crop')
    size = (p.get('bytes') or {}).get(gid+'.h5', {}).get('bytes')
    return {'granule_id': gid, 'timestamp': p.get('startTime'), 'end_timestamp': p.get('stopTime'),
            **parsed, 'size_bytes': size, 'size_gib': size/1024**3 if size is not None else None,
            'url': p.get('url'), 'crop_overlap_fraction': crop_coverage,
            'coverage_note': 'Planar geographic catalog-footprint overlap only, not valid radar-pixel fraction. Partial overlap is allowed for screening; canonical ingest must audit actual masks.',
            'compatibility': 'catalog_compatible' if not reasons else 'incompatible', 'reasons': reasons,
            'product_version': p.get('productVersion'),
            'header_audit_required': True,
            'audit_note': 'Catalog screening only. HDF5 product version, look geometry, channels, quality and native-grid compatibility require the existing ingest audit before use.'}


def interval_record(first, second, gaps):
    start, end = utc(first['timestamp']), utc(second['timestamp'])
    if end <= start:
        raise ValueError('Observation timestamps must increase strictly')
    seconds = (end-start).total_seconds()
    spans = any(start < utc(g['end']) and end > utc(g['start']) for g in gaps if g['status']=='confirmed')
    longer = seconds > REPEAT_DAYS*86400 + MATCH_TOLERANCE_SECONDS
    days = seconds/86400
    label = f'{round(days)}-day interval'
    if spans:
        label += ', spans instrument gap'
    elif longer:
        label += ', intervening visit(s) not loaded'
    return {'start': first['timestamp'], 'end': second['timestamp'], 'elapsed_seconds': seconds,
            'elapsed_days': days, 'longer_than_repeat': longer, 'spans_instrument_gap': spans,
            'flagged': spans or longer, 'label': label}


def build_calendar(series, observations, candidates, queries, gaps):
    observations = sorted(observations, key=lambda r: utc(r['timestamp']))
    anchor = utc(observations[0]['timestamp'])
    start, end = utc(series['start']), utc(series['end'])
    offset = (start-anchor).total_seconds()//(REPEAT_DAYS*86400)
    nominal = anchor+timedelta(days=REPEAT_DAYS*offset)
    while nominal < start:
        nominal += timedelta(days=REPEAT_DAYS)
    complete = bool(queries) and all(q['status']=='complete' for q in queries)
    slots = []
    for g in gaps:
        if g['status'] != 'confirmed':
            raise ValueError('Instrument gaps require confirmed official provenance')
    while nominal <= end:
        matches = [r for r in observations if abs((utc(r['timestamp'])-nominal).total_seconds()) <= MATCH_TOLERANCE_SECONDS]
        if len(matches)>1:
            raise ValueError('Multiple loaded observations in one nominal slot')
        available = [r for r in candidates if r.get('timestamp') and abs((utc(r['timestamp'])-nominal).total_seconds()) <= MATCH_TOLERANCE_SECONDS and r['compatibility']=='catalog_compatible']
        in_gap = any(utc(g['start']) <= nominal < utc(g['end']) for g in gaps)
        if matches:
            if in_gap:
                raise ValueError('Loaded observation contradicts confirmed instrument gap')
            status, why = 'observed', 'Real acquisition loaded in the saved analysis'
        elif in_gap:
            if available:
                raise ValueError('Archive candidate contradicts confirmed instrument gap')
            status, why = 'instrument_gap', 'Nominal slot falls in the official instrument gap'
        elif available:
            status, why = 'not_in_hand', 'Compatible archive candidate; no visit loaded'
        elif complete:
            status, why = 'unavailable_in_archive', 'No compatible candidate in this completed, bounded archive search; not proof of permanent absence'
        else:
            status, why = 'not_in_hand', 'No visit loaded; archive availability unknown because a query did not complete'
        slots.append({'nominal_timestamp': stamp(nominal), 'date': nominal.date().isoformat(), 'status': status,
                      'reason': why, 'observed_timestamp': matches[0]['timestamp'] if matches else None,
                      'observation_index': observations.index(matches[0]) if matches else None,
                      'candidate_ids': [c['granule_id'] for c in available],
                      'archive_checked': complete})
        nominal += timedelta(days=REPEAT_DAYS)
    if sum(s['status']=='observed' for s in slots) != len(observations):
        raise ValueError('Loaded observations fall outside the calendar or nominal slot tolerance')
    return {'schema_version': 1, 'series_id': series['series_id'], 'case_ids': series['case_ids'],
            'status': 'implemented', 'repeat_days': REPEAT_DAYS, 'anchor_timestamp': stamp(anchor),
            'match_tolerance_seconds': MATCH_TOLERANCE_SECONDS, 'slots': slots, 'instrument_gaps': gaps,
            'intervals': [interval_record(a,b,gaps) for a,b in zip(observations,observations[1:])],
            'queries': queries, 'search_complete': complete,
            'limitations': ['Nominal slots are not observations. No interpolation or no-change inference.',
                           'An empty search describes this track/frame/mode/release, crop and time window at retrieval time.',
                           'Elapsed intervals use actual UTC timestamps; rounded day labels allow small orbit-clock drift.',
                           'Candidate header compatibility and pixel validity remain unaudited until ingestion.']}
