from src.compute.evidence_common import ROOT,load
from src.compute.interferometry_gate import screen_candidate,gate_verdict

def source():
    series=load(ROOT/'config.time-axis.json')['series'][0]
    raw=load(ROOT/'data/candidates/interferometry_phase6_v1/nepal_098_016_GUNW.json')
    p=next(f['properties'] for f in raw['features'] if '20260819T233918' in f['properties']['sceneName'] and '20260831T233918' in f['properties']['sceneName'] and f['properties']['productionConfiguration']=='PR' and f['properties']['crid']=='P05023')
    return series,p

def test_derived_single_pol_is_not_rejected_as_source_mode_mismatch():
    series,p=source();r=screen_candidate(p,series,'GUNW')
    assert r['catalog_eligible'] and not r['accepted']
    assert 'unverified' in r['source_acquisition_compatibility']

def test_release_track_direction_configuration_and_both_dates_required():
    series,p=source()
    for key,value in [('crid','X05026'),('pathNumber',69),('flightDirection','DESCENDING'),('productionConfiguration','UR')]:
        assert not screen_candidate({**p,key:value},series,'GUNW')['catalog_eligible']
    assert not screen_candidate(p,{**series,'observations':series['observations'][:1]},'GUNW')['catalog_eligible']

def test_catalog_success_does_not_fabricate_science_or_gate_acceptance():
    result=gate_verdict([{'eligible_catalog_count':2,'search_complete':False}],{'http_status':401})
    assert not result['gate_open'] and result['claim_status']=='planned'
    assert result['coherence'] is None and result['los_displacement_cm'] is None
    assert 'not a claim of product absence' in result['reason']

def test_published_gate_reconciles_raw_queries_and_null_measurements():
    from src.compute.validate_interferometry_gate import validate
    assert validate()['catalog_eligible_not_accepted']>0
