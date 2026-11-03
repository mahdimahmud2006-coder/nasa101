"""Synthetic edge cases and saved real-query checks; no network or raw downloads."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import pytest
from src.ingest.nisar_slots import build_calendar, interval_record, screen_candidate, utc, stamp

GAP={'status':'confirmed','start':'2026-07-27T22:03:25Z','end':'2026-08-10T00:55:27Z'}
SERIES={'series_id':'test','case_ids':['test_case'],'start':'2026-07-24T00:00:00Z','end':'2026-08-30T00:00:00Z','track':69,'frame':14,'direction':'A','mode':'4005_DHDH_A','release':'P05023'}
OBS=[{'timestamp':'2026-07-24T23:21:33Z'},{'timestamp':'2026-08-17T23:21:32Z'}]
COMPLETE=[{'status':'complete'}]

def test_gap_slots_are_not_unloaded_or_zero_change():
    c=build_calendar(SERIES,OBS,[],COMPLETE,[GAP])
    assert [s['status'] for s in c['slots']]==['observed','instrument_gap','observed','unavailable_in_archive']
    assert c['slots'][1]['observed_timestamp'] is None
    assert c['slots'][1]['observation_index'] is None
    assert c['intervals'][0]['label']=='24-day interval, spans instrument gap'


def test_failed_search_never_proves_archive_absence():
    for state in ['error','incomplete']:
        c=build_calendar(SERIES,OBS,[],[{'status':state}],[GAP])
        assert c['slots'][-1]['status']=='not_in_hand'
        assert not c['slots'][-1]['archive_checked']


def test_compatible_candidate_is_unloaded_and_incompatible_is_not_available():
    candidate={'timestamp':'2026-08-29T23:21:32Z','granule_id':'test','compatibility':'catalog_compatible'}
    assert build_calendar(SERIES,OBS,[candidate],COMPLETE,[GAP])['slots'][-1]['status']=='not_in_hand'
    candidate['compatibility']='incompatible'
    assert build_calendar(SERIES,OBS,[candidate],COMPLETE,[GAP])['slots'][-1]['status']=='unavailable_in_archive'


def test_clock_drift_and_interval_gap_boundary():
    first={'timestamp':'2026-08-17T23:21:32Z'}
    second={'timestamp':'2026-08-29T23:21:35Z'}
    assert not interval_record(first,second,[GAP])['flagged']
    assert interval_record(OBS[0],OBS[1],[GAP])['spans_instrument_gap']
    assert not interval_record({'timestamp':GAP['end']},first,[GAP])['spans_instrument_gap']
    assert interval_record(first,{'timestamp':'2026-09-10T23:21:32Z'},[GAP])['label']=='24-day interval, intervening visit(s) not loaded'


def test_unconfirmed_gap_and_contradictory_observation_fail_closed():
    with pytest.raises(ValueError,match='confirmed'):
        build_calendar(SERIES,OBS,[],COMPLETE,[{**GAP,'status':'reported'}])
    with pytest.raises(ValueError,match='contradicts'):
        build_calendar(SERIES,OBS+[{'timestamp':'2026-08-05T23:21:33Z'}],[],COMPLETE,[GAP])
    with pytest.raises(ValueError,match='outside'):
        build_calendar(SERIES,OBS+[{'timestamp':'2026-08-06T23:21:33Z'}],[],COMPLETE,[GAP])


def test_actual_anchors_produce_expected_calendar_dates():
    cfg=json.loads(Path('config.time-axis.json').read_text())
    for s in cfg['series']:
        c=build_calendar(s,s['observations'],[],COMPLETE,[GAP])
        assert sum(r['status']=='observed' for r in c['slots'])==len(s['observations'])
        assert len(c['slots'])==(11 if s['track']==69 else 9)
        gap=[r['date'] for r in c['slots'] if r['status']=='instrument_gap']
        assert gap==(['2026-08-05'] if s['track']==69 else ['2026-08-07'])


def feature():
    gid='NISAR_L2_PR_GCOV_029_069_A_014_4005_DHDH_A_20260829T232132_20260829T232206_P05023_N_F_J_001'
    return {'properties':{'sceneName':gid,'startTime':'2026-08-29T23:21:32Z','pathNumber':69,'frameNumber':14,'flightDirection':'ASCENDING','processingLevel':'GCOV','collectionName':'NISAR_L2_GCOV_PROVISIONAL_V1','crid':'P05023','rangeBandwidth':['40+5'],'mainBandPolarization':['HH','HV'],'bytes':{gid+'.h5':{'bytes':2**30}}}}


def test_partial_catalog_overlap_requires_audit_not_false_absence():
    c=screen_candidate(feature(),SERIES,{'test_case':.97})
    assert c['compatibility']=='catalog_compatible'
    assert c['size_gib']==1
    assert c['header_audit_required']
    assert c['product_version'] is None
    assert screen_candidate(feature(),SERIES,{'test_case':0})['compatibility']=='incompatible'


@pytest.mark.parametrize('key,value',[('crid','X05026'),('rangeBandwidth',['20+5']),('mainBandPolarization',['VV','VH']),('pathNumber',98),('frameNumber',16),('flightDirection','DESCENDING'),('startTime','2026-08-30T23:21:32Z'),('collectionName','NISAR_L2_GCOV_UR_V1')])
def test_catalog_metadata_mismatches_rejected(key,value):
    f=feature();f['properties'][key]=value
    assert screen_candidate(f,SERIES,{'test_case':1})['compatibility']=='incompatible'


def test_identifier_release_rejected_even_if_catalog_claims_same_release():
    f=feature();f['properties']['sceneName']=f['properties']['sceneName'].replace('P05023','X05026')
    assert any('release:' in r for r in screen_candidate(f,SERIES,{'test_case':1})['reasons'])


def test_saved_archive_provenance_and_calendar_reproduce():
    import hashlib
    from shapely.geometry import shape
    from shapely import wkt
    cfg=json.loads(Path('config.time-axis.json').read_text())
    source=Path('data/candidates/phase1_2026_11_02_final')
    bundle=json.loads((source/'calendars.json').read_text())
    for series in cfg['series']:
        saved=json.loads((source/(series['series_id']+'.json')).read_text())
        features={}
        for q in saved['queries']:
            path=Path(q['response_path'])
            assert hashlib.sha256(path.read_bytes()).hexdigest()==q['response_sha256']
            assert q['status']=='complete'
            raw=json.loads(path.read_text())
            assert len(raw['features'])==q['count']
            features.update({f['properties']['sceneName']:f for f in raw['features']})
        for candidate in saved['candidates']:
            f=features[candidate['granule_id']]
            coverage={c['case_id']:shape(f['geometry']).intersection(wkt.loads(c['wkt'])).area/wkt.loads(c['wkt']).area for c in series['crops']}
            expected=screen_candidate(f,series,coverage)
            assert all(candidate[k]==v for k,v in expected.items())
        calendar=bundle['series'][series['series_id']]
        rebuilt=build_calendar(series,series['observations'],saved['candidates'],saved['queries'],calendar['instrument_gaps'])
        assert all(calendar[k]==v for k,v in rebuilt.items())
        assert sum(c['compatibility']=='catalog_compatible' and not c['in_hand'] for c in saved['candidates'])==4
    assert Path('web/public/cases/time-axis-v1/calendars.json').read_bytes()==(source/'calendars.json').read_bytes()


def test_search_runner_records_incomplete_results_without_downloading(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace
    from scripts.nisar_slot_search import run
    config=json.loads(Path('config.time-axis.json').read_text())
    class Result(list):
        searchComplete=False
        searchOptions=SimpleNamespace(intersectsWith='POLYGON EMPTY')
        def geojson(self):return {'type':'FeatureCollection','features':[]}
    calls=[]
    def search(**kwargs):calls.append(kwargs);return Result()
    # This fake exposes no download method, login, or session credentials.
    monkeypatch.setitem(sys.modules,'asf_search',SimpleNamespace(search=search,__version__='test fixture'))
    output=tmp_path/'snapshot'
    assert run(config,output)==2
    bundle=json.loads((output/'calendars.json').read_text())
    assert len(calls)==4
    assert all(not c['search_complete'] for c in bundle['series'].values())
    assert not any(s['status']=='unavailable_in_archive' for c in bundle['series'].values() for s in c['slots'])
    with pytest.raises(FileExistsError):run(config,output)
