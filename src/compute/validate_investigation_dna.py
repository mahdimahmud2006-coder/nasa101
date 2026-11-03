import json
from src.compute.evidence_common import ROOT,load,sha
from src.compute.explanation_fit import explanation_fit
from src.compute.investigation_dna import dna_signature

def validate():
    result={};rules=load(ROOT/'rules/explanations.yaml')
    for case in load(ROOT/'config.dualpol.json')['source_cases']:
        directory=ROOT/f'web/public/cases/{case}/evidence-v2';m=load(directory/'manifest.json');assert m['rules_sha256']==sha(ROOT/'rules/explanations.yaml')
        for r in m['profiles']:
            assert sha(directory/r['footprint_raster']['file'])==r['footprint_raster']['sha256']
            expected=dna_signature(r['profile'],r['dna']['mean_abs_hh_baseline_db'])
            assert all(r['dna'][k]==v for k,v in expected.items())
            for fit in r['explanations']:
                computed=explanation_fit(fit['facts'],rules);assert computed['hypotheses']==fit['hypotheses'];assert fit['winner'] is None
        result[case]={'footprints':len(m['profiles']),'status':'PASS'}
    from scripts.generate_claims import generate
    generate(check=True)
    return {'status':'DNA_V2_RULES_AND_CLAIMS_PASS','cases':result,'scope':'Deterministic calculation consistency, not mechanism or event validation.'}
if __name__=='__main__':print(json.dumps(validate(),indent=2))
