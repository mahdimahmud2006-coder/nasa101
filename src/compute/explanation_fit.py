"""Deterministic traceable hypothesis compatibility, with no winner or probability."""
import operator,math
OPS={'le':operator.le,'lt':operator.lt,'ge':operator.ge,'gt':operator.gt,'eq':operator.eq}
def condition(rule,facts):
    value=facts.get(rule['field'])
    if value is None or isinstance(value,float) and not math.isfinite(value):return None
    return bool(OPS[rule['op']](value,rule['value']))
def explanation_fit(facts,table):
    results=[]
    for rule in table['hypotheses']:
        supports=[(r,condition(r,facts)) for r in rule['support']];contradicts=[(r,condition(r,facts)) for r in rule['contradict']]
        if any(v is True for _,v in contradicts):status='contradicted'
        elif supports and all(v is True for _,v in supports):status='consistent'
        elif any(v is not None for _,v in supports+contradicts):status='not contradicted'
        else:status='unknown'
        record=lambda r:{**r,'observed_value':facts.get(r['field'])}
        results.append({'id':rule['id'],'title':rule['title'],'status':status,'claim_status':'hypothesized','supporting_signatures':[record(r) for r,v in supports if v is True],'contradicting_signatures':[record(r) for r,v in contradicts if v is True],'unmet_signatures':[record(r) for r,v in supports if v is False],'missing_inputs':[r['field'] for r,v in supports+contradicts if v is None],'evidence_still_required':rule['required'],'limitation':rule['limitation']})
    return {'model_version':table['model_version'],'interpretation':table['status_meaning'],'hypotheses':results,'winner':None,'probabilities':None}
