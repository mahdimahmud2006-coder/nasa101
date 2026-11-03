import pytest,numpy as np
from src.compute.explanation_fit import explanation_fit
from src.compute.investigation_dna import dna_signature,polygon_evidence
RULES={'model_version':'fixture','status_meaning':'fixture only','hypotheses':[{'id':'a','title':'a','support':[{'field':'a','op':'ge','value':3},{'field':'b','op':'ge','value':3}],'contradict':[{'field':'c','op':'gt','value':0}],'required':['external reference'],'limitation':'synthetic'}]}
@pytest.mark.parametrize('facts,status',[({'a':4,'b':4,'c':0},'consistent'),({'a':4,'b':None,'c':0},'not contradicted'),({'a':4,'b':4,'c':1},'contradicted'),({},'unknown')])
def test_all_fit_statuses_trace_inputs_without_probability(facts,status):
    result=explanation_fit(facts,RULES);assert result['hypotheses'][0]['status']==status;assert result['winner'] is None and result['probabilities'] is None

def test_observed_only_persistence_and_censored_recovery():
    p={'observations':[{'timestamp':f'2026-08-{d:02d}T00:00:00Z'} for d in [1,13,25]]}
    dna=dna_signature(p,[0,7,6.5]);assert dna['persistence']['k']==dna['persistence']['n']==2;assert dna['recovery_right_censored'];assert dna['coherence'] is None
    assert dna['onset_interval']['last_observed_below']==p['observations'][0]['timestamp']
    assert dna['recovery_fraction']==pytest.approx(1-6.5/7)
    none=dna_signature(p,[None,None,None]);assert none['persistence']['fraction'] is None and none['recovery_fraction'] is None

def test_polygon_rejects_outside_self_intersection_and_bad_vertices():
    for points in [[[0,0],[1,0]], [[-1,0],[10,0],[10,10]],[[0,0],[20,20],[20,0],[0,20]]]:
        with pytest.raises(ValueError):polygon_evidence('nepal_surface',points)
