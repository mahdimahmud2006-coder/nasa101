import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {selection,observationPacket,hashOf} from '../web/atlas.mjs';
import {atlasMakeState,atlasReadHash,atlasVersionedHash,atlasValidateState,atlasMeasurement,atlasNativeProfile} from '../web/atlas-contract.mjs';

const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const records=read('web/atlas-record.json'),catalog=read('web/atlas-contract-records.json'),receipt=read('reports/development/part-01-baseline.json');
test('versioned and legacy links replay all four frozen examples with exact measurements',()=>{
  for(const e of receipt.examples){
    const s=selection(records,atlasReadHash(catalog,e.hash)),v=atlasMakeState(catalog,s);
    assert.deepEqual(selection(records,atlasReadHash(catalog,atlasVersionedHash(v))),s);
    const p=observationPacket(records,s,null,catalog);
    assert.deepEqual(p.measurements,e.measurements);
    assert.equal(p.selected_utc,e.utc);assert.equal(p.common_valid_pixels,e.valid);
    assert.deepEqual(p.pair?.timestamps??null,e.pair);assert.equal(p.optical_reference?.reference_id??null,e.optical);
  }
});

test('preserves thermal and scenario context; rejects cross-case and stale selections',()=>{
  const s=selection(records,{case:'nepal_surface',date:'2026-09-12',thermal:catalog.nepal_surface.context.thermal[2].id,
    scenario:catalog.nepal_surface.context.scenarios.find(x=>x.observationId==='acq_20260912T233918').id});
  const state=atlasMakeState(catalog,s);
  assert.deepEqual(selection(records,atlasReadHash(catalog,atlasVersionedHash(state))),s);
  for(const [change,error] of [
    [{currentId:catalog.jamuna_river.observations[0].id},/Observation/],
    [{recordVersion:'old'},/outdated/],[{gridId:catalog.nepal_impact_corridor.gridId},/grid/],
    [{footprint:{...state.footprint,id:catalog.nepal_impact_corridor.footprints[0].id}},/stale/],
    [{currentId:'acq_20261018T233918'},/Scenario/]
  ])assert.throws(()=>atlasValidateState(catalog,{...state,...change}),error);
  const pair=atlasMakeState(catalog,selection(records,{case:'nepal_surface',date:'2026-09-12',layer:'coherence'}));
  assert.throws(()=>atlasValidateState(catalog,{...pair,pair:{...pair.pair,firstId:'bad'}}),/endpoints/);
  assert.throws(()=>atlasReadHash(catalog,hashOf({...s,date:'2026-08-05'})),/recorded date/);
});

test('point and polygon state preserve coordinate order and reject out-of-grid footprints',()=>{
  for(const caseId of Object.keys(catalog))for(const native of ['600,500','[[500,600],[511,600],[511,611],[500,611]]']){
    const s=selection(records,{case:caseId,native});
    assert.equal(atlasReadHash(catalog,atlasVersionedHash(atlasMakeState(catalog,s))).native,native);
  }
  const state=atlasMakeState(catalog,selection(records,{case:'nepal_surface'}));
  assert.throws(()=>atlasValidateState(catalog,{...state,footprint:{kind:'polygon',gridId:state.gridId,vertices:[[1,1],[2,1],[2500,2]]}}),/out-of-grid/);
});

test('measured zero is distinct from missing, out-of-scope and invalid values',()=>{
  const c=catalog.jamuna_river,p=observationPacket(records,selection(records,{case:c.caseId,date:c.observations[0].utc}),null,catalog);
  const zero=p.measurementRecords.find(x=>x.quantity==='hh_reference');
  assert.equal(zero.value,0);assert.equal(zero.status,'measured');
  assert.equal(p.measurementRecords.find(x=>x.quantity==='hh_successive').status,'out_of_scope');
  for(const status of ['missing','out_of_scope','invalid'])assert.equal(atlasMeasurement({...zero,status,value:null}).status,status);
  assert.throws(()=>atlasMeasurement({...zero,status:'missing'}),/null/);
});

test('native responses must bind to matching grid, record, coordinates and acquisition IDs',()=>{
  const c=catalog.jamuna_river,point={kind:'point',row:600,col:500};
  const b={...Object.fromEntries(['caseId','recordVersion','manifestSha256','gridId'].map(k=>[k,c[k]])),selection:point};
  const data={atlasBinding:b,profile:{observations:c.observations.map(o=>({timestamp:o.utc,observation_id:o.id}))}};
  assert.deepEqual(atlasNativeProfile(c,point,data),data.profile);
  assert.throws(()=>atlasNativeProfile(c,{...point,col:501},data),/footprint/);
  assert.throws(()=>atlasNativeProfile(c,point,{...data,atlasBinding:{...b,gridId:'other'}}),/grid/);
  data.profile.observations[0].observation_id='wrong';
  assert.throws(()=>atlasNativeProfile(c,point,data),/series/);
});

test('custom scenario links bind exact radar observation, model and input digest',()=>{
  const c=catalog.nepal_surface,anchor=c.observations.find(o=>o.utc.startsWith('2026-09-12'));
  const s=selection(records,{case:c.caseId,date:anchor.utc,scenarioRun:{
    anchorUtc:anchor.utc,rainfall_multiplier:1.5,duration_hours:48,wetness:'wet'
  }});
  const state=atlasMakeState(catalog,s);
  assert.deepEqual(atlasReadHash(catalog,atlasVersionedHash(state)).scenarioRun,s.scenarioRun);
  const run=state.contextSelections.scenarioRun;
  for(const change of [{observationId:c.referenceId},{inputsSha256:'different'},{duration_hours:1}]){
    assert.throws(()=>atlasValidateState(catalog,{...state,contextSelections:{...state.contextSelections,scenarioRun:{...run,...change}}}),/accepted observation/);
  }
  assert.equal(selection(records,{...s,date:'2026-10-18'}).scenarioRun,undefined);
});
