import test from 'node:test';import assert from 'node:assert/strict';
import {reasoningHTML,claimsHTML,referenceForSelection,referenceHTML} from '../web/reasoning.mjs';
import {atlasFitGroups} from '../web/atlas-compatibility.mjs';
test('DNA view uses observed denominators and brackets and omits unsupported coherence',()=>{
 const evidence={dna:{persistence:{k:2,n:2,definition:'observed visits only'},recovery_fraction:.1,recovery_right_censored:true,onset_interval:{last_observed_below:'2026-08-19',first_observed_above:'2026-08-31'},terrain:{class:'steep footprint'},coherence:null},explanations:[{next_evidence_needed:'Inspect next nominal visit',hypotheses:[{title:'Moisture',status:'unknown',limitation:'not a cause',supporting_signatures:[],contradicting_signatures:[],missing_inputs:['rain'],evidence_still_required:['scientific rain']}]}]};
 const html=reasoningHTML(evidence,0);assert.match(html,/2 of 2/);assert.match(html,/Right-censored/);assert.doesNotMatch(html,/Coherence|Planned/);
 assert.match(html,/<details class="explanation-more">/);assert.match(html,/Evidence incomplete/);
 assert.match(html,/Required context · rain/);
 assert.match(reasoningHTML(evidence,0,{otherOpen:true}),/<details class="explanation-more" open>/);
});
test('review leads with measured pattern matches and keeps incomplete and excluded screens in details',()=>{
 const supporting_signatures=[{field:'hv_change_abs_db',op:'ge',value:3,observed_value:3.4}];
 const partial={id:'vegetation_structure',status:'not contradicted',supporting_signatures};
 const incomplete={id:'moisture_roughness',status:'not contradicted',supporting_signatures,missing_inputs:['rain_72h_mm']};
 const excluded={id:'steep_source_movement',status:'contradicted',supporting_signatures};
 const full={id:'smooth_low_return',status:'consistent',supporting_signatures};
 const outside={id:'flooded_vegetation_like',status:'not contradicted',supporting_signatures:[]};
 const groups=atlasFitGroups([partial,incomplete,excluded,full,outside]);
 assert.deepEqual(groups.review.map(item=>item.result.kind),['match','partial']);
 assert.deepEqual(groups.additional.map(item=>item.result.kind),['incomplete','excluded','outside']);
 assert.equal(groups.review[1].title,'Cross-polarized response change');
 assert.match(groups.summary,/1 full match · 1 partial match/);
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
