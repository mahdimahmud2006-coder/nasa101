import test from 'node:test';
import assert from 'node:assert/strict';
import {cprProfile,dualpolLayers,extensionMatches,sensitivityRows,sensitivityHTML,cprChart,dualpolDossier,dualpolLegend} from '../web/dualpol.mjs';
const p={observations:[{timestamp:'2026-07-24T23:21:33Z',hh_mean_db:-17,hv_mean_db:-24,hh_baseline_delta_db:0,hv_baseline_delta_db:0,hh_successive_delta_db:null,hv_successive_delta_db:null},{timestamp:'2026-08-17T23:21:32Z',hh_mean_db:-24,hv_mean_db:-26,hh_baseline_delta_db:-7,hv_baseline_delta_db:-2,hh_successive_delta_db:-7,hv_successive_delta_db:-2}]};
const sensitivity={case_id:'test',offsets_db:[-1,0,1],nominal_hh_db:-17,nominal_hv_db:-24,observations:[{common_valid_pixels:100,common_valid_area_km2:.01,hh_cutoffs_db:[-18,-17,-16],hv_cutoffs_db:[-25,-24,-23],candidate_pixels:[[1,2,3],[4,5,6],[7,8,9]],candidate_area_km2:[[.0001,.0002,.0003],[.0004,.0005,.0006],[.0007,.0008,.0009]]}]};
test('fixed-footprint CPR preserves sign, nulls and original evidence',()=>{
 const rows=cprProfile(p).observations;
 assert.equal(rows[0].cpr_mean_db,-7);assert.equal(rows[1].cpr_mean_db,-2);assert.equal(rows[1].cpr_baseline_delta_db,5);
 assert.equal(rows[0].cpr_successive_delta_db,null);assert.equal(p.observations[0].cpr_mean_db,undefined);
 assert.equal(cprProfile(null),null);
});
test('sensitivity slices vary only the intended thresholds and match source cells',()=>{
 assert.deepEqual(sensitivityRows(sensitivity,0,'coupled').map(d=>d.candidate_pixels),[1,5,9]);
 assert.deepEqual(sensitivityRows(sensitivity,0,'hh').map(d=>d.candidate_pixels),[2,5,8]);
 assert.deepEqual(sensitivityRows(sensitivity,0,'hv').map(d=>d.candidate_pixels),[4,5,6]);
 assert.ok(sensitivityRows(sensitivity,0,'hh').every(d=>d.hv_cutoff_db===-24));
 assert.match(sensitivityHTML(sensitivity,0),/fixed common pixels/);
 assert.match(sensitivityHTML(sensitivity,0),/not accuracy/);
 assert.match(sensitivityHTML(null,0),/unavailable/);
});
test('stale extension does not expose unsupported layers',()=>{
 const data={case_id:'test',grid:{shape:[2,2]},observations:[{timestamp:'2026-01-01',source_granule_id:'original'}]};
 const extension={...data,observations:[{...data.observations[0],layers:{cpr:'cpr.png',composite:'composite.png',cpr_successive:null}}]};
 assert.ok(extensionMatches(extension,data));
 assert.deepEqual(dualpolLayers(extension,0),['cpr','composite']);
 assert.equal(extensionMatches({...extension,case_id:'other'},data),false);
 assert.deepEqual(dualpolLayers(null,0),[]);
});
test('CPR trace includes actual dates and cannot turn absent samples into zero',()=>{
 assert.match(cprChart(p,1,null),/Δ CPR/);
 assert.match(cprChart(p,1,null),/17 Aug/);
 assert.match(cprChart({observations:[{timestamp:'2026-01-01',hh_baseline_delta_db:null,hv_baseline_delta_db:null}]},0,null),/insufficient/);
});
test('CPR chart leaves an outage crossing unconnected while keeping both endpoint measurements',()=>{
 const calendar={repeat_days:12,intervals:[{start:p.observations[0].timestamp,end:p.observations[1].timestamp,flagged:true}],instrument_gaps:[{start:'2026-07-27T22:03:25Z',end:'2026-08-10T00:55:27Z'}]};
 const html=cprChart(p,1,calendar);assert.doesNotMatch(html,/instrument-gap-shade/);assert.doesNotMatch(html,/class="cpr-line/);assert.equal((html.match(/<circle /g)||[]).length,2);
});
test('dossier separates crop hints from selected footprint and keeps limitations',()=>{
 const extension={observations:[{hint_statistics:{}}],formulas:{cpr:'HV-HH'},hint_definitions:{hint_low:'candidate'},limits:['uncalibrated'],provenance:{source:'saved'}};
 const exported=dualpolDossier(extension,p,0,sensitivity);
 assert.match(exported.hint_scope,/crop-wide/);assert.equal(exported.selected_footprint.observations[1].cpr_baseline_delta_db,5);
 assert.deepEqual(exported.limitations,['uncalibrated']);assert.equal(exported.sensitivity.observations.length,1);
});
test('legend exposes fixed scales and signed zero-centered change policy',()=>{
 const ext={display_limits:{change:[-8,8],cpr:[-20,0]},palette_css:{vik:'diverging',cividis:'sequential'}};
 const cpr=dualpolLegend(ext,'cpr');assert.match(cpr.note,/sign reversal/);assert.equal(cpr.low,'-20 dB');
 const change=dualpolLegend(ext,'cpr_baseline');assert.match(change.note,/exactly 0 dB/);assert.equal(change.ramp,'diverging');
});
