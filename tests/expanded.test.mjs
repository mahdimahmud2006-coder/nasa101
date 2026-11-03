import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {pairForVisit,sourceFor,playbackIndices,readExpandedView,traceSVG} from '../web/expanded-model.mjs';
import {interferometryHTML} from '../web/reasoning.mjs';
const m=JSON.parse(fs.readFileSync(new URL('../web/public/cases/nepal_surface/expanded-v1/manifest.json',import.meta.url)));
test('ten actual dates and explicit reference preserve pre-reference observations',()=>{
 assert.equal(m.observations.length,10);assert.equal(m.reference_index,4);assert.equal(m.observations[4].timestamp,m.reference_timestamp);
 assert.ok(m.profiles[0].observations[0].hh_reference_delta_db!==0);
 assert.equal(m.profiles[0].observations[4].hh_reference_delta_db,0);
});
test('coherence is available only for the supplied observed pair endpoints',()=>{
 assert.equal(pairForVisit(m,0),null);assert.equal(sourceFor(m,0,'coherence20'),null);
 assert.ok(sourceFor(m,5,'coherence20'));assert.ok(sourceFor(m,6,'coherence80'));
 assert.equal(sourceFor(m,9,'coherence20'),null);assert.equal(sourceFor(m,0,'hh_successive'),null);
});
test('trace records elapsed dates, reference and outage without an invented August 7 sample',()=>{
 const s=traceSVG(m.profiles[0],m,9);assert.doesNotMatch(s,/Satellite data gap|<rect /);assert.doesNotMatch(s,/stroke-dasharray="7 6"/);assert.match(s,/reference August 19/);assert.doesNotMatch(s,/>08-07</);
 assert.equal((s.match(/<circle /g)||[]).length,20);
 assert.equal((s.match(/stroke-width="2.5"/g)||[]).length,16,'Two outage-crossing segments are omitted');
});
test('playback offers available measurements only, including pair-based coherence',()=>{
 assert.equal(playbackIndices(m,'hh').length,10);assert.deepEqual(playbackIndices(m,'coherence20'),[5,6]);assert.deepEqual(playbackIndices(m,'coherence80'),[5,6]);assert.equal(playbackIndices(m,'hh_successive')[0],1);assert.deepEqual(playbackIndices(m,'missing'),[]);
});
test('new coherence status supersedes historical gate only for accepted cases',()=>{
 const gate={expanded_cases:[{case_id:'nepal_surface',coherence_pairs:2}],reason:'old gate',checks_remaining:['headers'],records:[]};
 assert.match(interferometryHTML(gate,'nepal_surface'),/MEASURED COHERENCE/);
 assert.match(interferometryHTML(gate,'jamuna_river'),/GATE NOT OPEN/);
});
test('shared view permits only actual supported case identifiers',()=>{
 assert.equal(readExpandedView('#case=../../secret').case,'nepal_surface');
 assert.deepEqual(readExpandedView('#case=nepal_impact_corridor&layer=coherence20'),{case:'nepal_impact_corridor',date:null,layer:'coherence20',point:null,footprint:0});
});
