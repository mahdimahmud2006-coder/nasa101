import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {selection} from '../web/atlas-state.mjs';
import {atlasMakeState} from '../web/atlas-contract.mjs';
import {atlasCreateDossier,atlasDossierSelection,atlasVerifyDossier,atlasDossierSummary,atlasParseDossier,atlasDossierMaxBytes} from '../web/atlas-dossier.mjs';
import {atlasHostedCase,atlasHostedLoader} from '../web/atlas-hosted.mjs';

const load=name=>JSON.parse(fs.readFileSync(new URL('../web/'+name,import.meta.url),'utf8'));
const records=load('atlas-record.json'),catalog=load('atlas-contract-records.json');
const make=(state,notes='')=>atlasCreateDossier(records,state,null,catalog,5,null,notes);

test('replays a wetland footprint and preserves notes without using them as evidence',()=>{
  const s=selection(records,{case:'tanguar_wetland',date:'2026-08-29',layer:'hv',profile:4,split:50});
  const packet=make(s,'Record water depth on a comparable visit.');
  const raw=JSON.stringify(packet),parsed=atlasParseDossier(raw,Buffer.byteLength(raw));
  const replay=atlasDossierSelection(parsed,catalog,true);
  assert.deepEqual(replay,s);
  assert.equal(parsed.dossier.components.dprvic.value,null);
  assert.equal(parsed.dossier.components.los.value,null);
  assert.equal(parsed.dualpol.powerShare.unit,'fraction');
  assert.equal(parsed.chronology.rule.thresholdDb,5);
  assert.ok(atlasDossierSummary(parsed).some(s=>s.startsWith('Record water depth')));
  atlasVerifyDossier(parsed,make(replay),catalog,replay);
  const previous=structuredClone(parsed);
  const prior='c7968b9cb85e9a77ffd136836ca1460ad914bc47b44a7088ba164f74f5af2dac';
  previous.contract.evidenceVersion=prior;
  previous.dossier.source.evidenceVersion=prior;
  assert.deepEqual(atlasDossierSelection(previous,catalog,true),s);
  atlasVerifyDossier(previous,make(s),catalog,s);
  const altered=structuredClone(parsed);
  altered.measurements.hh_reference+=.00001;
  assert.throws(()=>atlasVerifyDossier(altered,make(s),catalog,s),/differs at measurements/);
  altered.measurements.hh_reference=parsed.measurements.hh_reference+1e-7;
  atlasVerifyDossier(altered,make(s),catalog,s);
});

test('keeps exact pair support and saved dated scenario bindings across replay',()=>{
  const pair=selection(records,{case:'nepal_surface',date:'2026-09-12',layer:'coherence',profile:0});
  const p=make(pair);
  const component=p.dossier.components.coherence;
  assert.equal(component.status,'measured');
  assert.equal(component.support.validPixels,53);
  assert.notEqual(component.support.gridId,p.dossier.components.hh.support.gridId);
  assert.equal(component.endpoints.earlier.lastId,component.endpoints.later.firstId);
  assert.equal(component.endpoints.later.lastUtc,p.selected_utc);
  atlasVerifyDossier(p,make(atlasDossierSelection(p,catalog,true)),catalog,pair);
  const date=pair.date,scenario=records.nepal_surface.context.scenarios[date][0].id;
  const model=selection(records,{case:'nepal_surface',date,scenario});
  const packet=make(model);
  assert.equal(packet.context.counterfactual.id,scenario);
  assert.equal(atlasDossierSelection(packet,catalog,true).scenario,scenario);
  atlasVerifyDossier(packet,make(model),catalog,model);
});

test('rejects unknown schemas, stale identifiers, oversized files and nonlocal native replay',()=>{
  const s=selection(records,{case:'jamuna_river',date:'2026-08-29',profile:4});
  const packet=make(s);
  assert.throws(()=>atlasParseDossier('{}',atlasDossierMaxBytes+1),/8 MiB/);
  assert.throws(()=>atlasDossierSelection({...packet,schema:'invented'},catalog,false),/version/);
  assert.throws(()=>atlasDossierSelection({...packet,contract:{...packet.contract,manifestSha256:'wrong'}},catalog,true),/outdated/);
  const native=selection(records,{...s,native:'[[950,950],[951,950],[950,951]]'});
  const contract=atlasMakeState(catalog,native);
  assert.throws(()=>atlasDossierSelection({...packet,contract},catalog,true),/local runtime/);
  assert.equal(atlasDossierSelection({...packet,contract},catalog,false).native,native.native);
  contract.footprint.vertices=Array(201).fill([100,100]);
  assert.throws(()=>atlasDossierSelection({...packet,contract},catalog,false),/invalid/);
});

test('static loader fetches the selected case only and loads terrain separately',async()=>{
  const id='tanguar_wetland',identity=catalog[id],record=structuredClone(records[id]),calls=[];
  const mesh=record.terrain.elevation_m;
  delete record.terrain.elevation_m;
  const cases={[id]:{manifestSha256:identity.manifestSha256,evidenceVersion:identity.evidenceVersion,data:'./wet.json',terrain:'./terrain.json'}};
  const loader=atlasHostedLoader({cases,defaultCase:id},async path=>{
    calls.push(path);
    return {ok:true,json:async()=>path==='./wet.json'?{record,identity}:mesh};
  });
  assert.deepEqual(calls,[]);
  assert.equal(atlasHostedCase('#atlas=1&case=__proto__',cases),null);
  await Promise.all([loader.ensure(id),loader.ensure(id)]);
  assert.deepEqual(calls,['./wet.json']);
  assert.equal(loader.records[id].terrain.elevation_m,undefined);
  await loader.terrain(id);
  assert.deepEqual(calls,['./wet.json','./terrain.json']);
  assert.equal(loader.records[id].terrain.elevation_m.length,41**2);
});
