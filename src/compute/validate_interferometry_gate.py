import json
from src.compute.evidence_common import ROOT,load,sha
from src.compute.interferometry_gate import screen_candidate

def validate():
    gate=load(ROOT/'web/public/cases/interferometry-v2.json')
    assert gate==load(ROOT/'data/candidates/interferometry_phase6_v2/gate-reviewed.json')
    assert not gate['gate_open'] and gate['coherence'] is None and gate['los_displacement_cm'] is None
    assert gate['claim_status']=='planned' and gate['large_downloads']==0
    assert gate['access_probe']['bytes_read']<=8 and not gate['access_probe']['science_subset_accepted']
    eligible=0
    for record in gate['records']:
        source=ROOT/record['response_path'];assert sha(source)==record['response_sha256']
        series=next(s for s in load(ROOT/'config.time-axis.json')['series'] if s['series_id']==record['series_id'])
        expected=[screen_candidate(f['properties'],series,record['product']) for f in load(source)['features']]
        assert expected==record['candidates']
        assert record['eligible_catalog_count']==sum(c['catalog_eligible'] for c in expected)
        assert not any(c['accepted'] for c in expected)
        eligible+=record['eligible_catalog_count']
    return {'status':'INTERFEROMETRY_GATE_PLANNED_PASS','catalog_eligible_not_accepted':eligible,'coherence':None,'los_displacement_cm':None,'scope':'Metadata consistency and closed gate, not validation of an interferometric measurement.'}

if __name__=='__main__':print(json.dumps(validate(),indent=2))
