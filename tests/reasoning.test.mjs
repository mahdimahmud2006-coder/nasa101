import test from 'node:test';import assert from 'node:assert/strict';
import {reasoningHTML,claimsHTML,referenceForSelection,referenceHTML,interferometryHTML} from '../web/reasoning.mjs';
test('DNA view uses observed denominators, brackets and planned coherence',()=>{
 const evidence={dna:{persistence:{k:2,n:2,definition:'observed visits only'},recovery_fraction:.1,recovery_right_censored:true,onset_interval:{last_observed_below:'2026-08-19',first_observed_above:'2026-08-31'},terrain:{class:'steep footprint'},coherence:null},explanations:[{next_evidence_needed:'Inspect next nominal visit',hypotheses:[{title:'Moisture',status:'unknown',limitation:'not a cause',supporting_signatures:[],contradicting_signatures:[],missing_inputs:['rain'],evidence_still_required:['scientific rain']}]}]};
 const html=reasoningHTML(evidence,0);assert.match(html,/2 of 2/);assert.match(html,/Right-censored/);assert.match(html,/Planned/);assert.match(html,/unknown/);assert.match(html,/scientific rain/);
});
test('ledger rendering keeps exact IDs, status, limits and escapes source text',()=>{
 const html=claimsHTML({claims:[{id:'T1',status:'measured',text:'<script>not executable</script>',limitation:'sample only'}]});assert.match(html,/data-claim-id="T1"/);assert.match(html,/&lt;script&gt;/);assert.match(html,/sample only/);assert.match(claimsHTML(null),/unavailable/);
});

test('cloudy reference does not inherit a descriptive status or another footprint match',()=>{
 const bundle={design_sha256:'hash',freeze_commit:'commit',results:[{footprint_id:'frozen',observation_id:'visit_1',reference_status:'none',footprint_role:'target_geographic',reason:'cloudy',scope:'frozen footprint only'}]};
 assert.equal(referenceForSelection(bundle,{reference_footprint_id:'other'},'visit_1').result,null);
 assert.equal(referenceForSelection(bundle,{reference_footprint_id:'frozen'},'visit_1').status,'none');
 assert.match(referenceHTML(bundle,{reference_footprint_id:'frozen'},'visit_1'),/cloudy/);
});
test('interferometry panel leaves science unavailable despite available catalog candidates',()=>{
 const html=interferometryHTML({reason:'subset unverified',checks_remaining:['source headers'],records:[{case_ids:['a'],product:'GUNW',eligible_catalog_count:2,search_complete:false,candidates:[]}]},'a');
 assert.match(html,/GATE NOT OPEN/);assert.match(html,/search incomplete/);assert.match(html,/Unavailable/);assert.match(html,/source headers/);
 assert.match(interferometryHTML(null,'a'),/planned/);
});
