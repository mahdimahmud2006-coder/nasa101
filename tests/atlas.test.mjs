import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {selection,observationPacket,hashOf,nativeSelection} from '../web/atlas.mjs';
import {atlasChronology,atlasComparison,atlasTraceSupport,atlasVisitLabel} from '../web/atlas-chronology.mjs';
import {createAtlasProbe} from '../web/atlas-data.mjs';
import {createAtlasScenarios} from '../web/atlas-scenarios.mjs';
import {atlasObservedOccupancy,atlasFieldReview} from '../web/atlas-review.mjs';
import {atlasDisplayToGrid,atlasGridToWorld,atlasMapZoomLimit,atlasWorldToGrid,atlasTerrainPoint,atlasTerrainUV} from '../web/atlas-map.mjs';
const load=file=>fs.readFileSync(new URL('../web/'+file,import.meta.url),'utf8');
const records=JSON.parse(load('atlas-record.json'));
test('adapts choices to measured country, dates, coherence pair endpoints and native domain',()=>{
  let s=selection(records,{case:'nepal_surface',layer:'coherence',date:'2026-10-18'});
  assert.equal(s.date.slice(0,10),'2026-09-12');
  const wetland=selection(records,{case:'tanguar_wetland',layer:'coherence',date:'2026-10-16'});
  assert.equal(wetland.layer,'coherence');
  assert.equal(observationPacket(records,wetland).pair.timestamps[1],wetland.date);
  assert.equal(nativeSelection(records.jamuna_river,'3000,100'),null);
  assert.equal(nativeSelection(records.nepal_surface,'[[0,0],[0,10],[5,5]]'),'[[0,0],[0,10],[5,5]]');
  assert.equal(nativeSelection(records.jamuna_river,'120, 334'),'120,334');
  assert.deepEqual(selection(records,Object.fromEntries(new URLSearchParams(hashOf(s).slice(1)))),s);
});
test('selected Kathmandu measurement, pair and both reference identities stay attached',()=>{
  const s=selection(records,{case:'nepal_surface',layer:'coherence',date:'2026-09-12'}),p=observationPacket(records,s);
  assert.equal(p.common_valid_pixels,199);assert.equal(p.measurements.hh_reference.toFixed(2),'-7.08');
  assert.equal(p.measurements.hh_successive.toFixed(2),'0.45');assert.equal(p.pair.timestamps[1],p.selected_utc);
  assert.equal(p.pair_comparison.common_valid_pixels>0,true);assert.ok(p.reference_granule.includes('20260819'));
  assert.equal(observationPacket(records,selection(records,{case:'nepal_impact_corridor'})).pair,null);
});
test('Bangladesh reference eligibility and hypotheses belong to the selected footprint',()=>{
  const c=records.jamuna_river;
  assert.equal(c.profiles.length,7);
  for(const p of c.profiles)assert.equal(p.fits.length,10);
  const p=c.profiles.findIndex(p=>Object.values(p.reference_matches).some(r=>r.clear_assessable_pixels));
  const date=Object.keys(c.profiles[p].reference_matches).find(d=>c.profiles[p].reference_matches[d].clear_assessable_pixels);
  const s=selection(records,{case:c.case,date,profile:p,layer:'fraction'});
  assert.ok(observationPacket(records,s).optical_reference.clear_assessable_pixels>0);
  assert.equal(observationPacket(records,{...s,profile:0}).optical_reference,null);
});
test('guided route, playback, wipe and native selection share one controller',async()=>{
  class El{
    constructor(){this.children=[];this.dataset={};this.style={setProperty(){}};this.attrs={};this.value='';}
    append(...items){this.children.push(...items);}replaceChildren(...items){this.children=[...items];}
    setAttribute(k,v){this.attrs[k]=v;}addEventListener(){}click(){this.onclick?.();}
  }
  const elements=new Map([...load('index.html').matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new El()]));
  elements.set('atlas-data',Object.assign(new El(),{textContent:JSON.stringify(records)}));
  elements.set('atlas-identity',Object.assign(new El(),{textContent:load('atlas-contract-records.json')}));
  const stories=['river','wetland','persist'].map(story=>Object.assign(new El(),{dataset:{story}}));
  const document={body:new El(),getElementById:k=>elements.get(k),createElement:()=>new El(),createElementNS:()=>new El(),querySelectorAll:()=>stories,addEventListener(){}};
  let tick,hash='',requests=0;
  const events={},catalog=JSON.parse(load('atlas-contract-records.json'));
  const location={get hash(){return hash;}},history={replaceState(_a,_b,v){hash=v;}};
  const ctx={document,window:{addEventListener(name,fn){events[name]=fn;}},location,history,URLSearchParams,console,TP_ATLAS:records,AbortController,
    setInterval:fn=>{tick=fn;return 1;},clearInterval:()=>{tick=null;},fetch:async(url,opts)=>{
      requests++;
      const {selection}=JSON.parse(opts.body),record=catalog[url.split('/')[3]];
      if(selection.kind==='polygon')return {ok:false,json:async()=>({error:'Draw a polygon with a nonzero area and no crossing edges.'})};
      return {ok:true,json:async()=>({atlasBinding:{...record,selection},
        profile:{label:'Native neighborhood',common_valid_pixels:121,common_valid_area_km2:.0121,
          observations:record.observations.map(o=>({timestamp:o.utc,observation_id:o.id,hh_reference_delta_db:.5,hh_successive_delta_db:.25}))}})};
    }};
  const packageHtml=fs.readFileSync(new URL('../output/atlas/TerraPulse.html',import.meta.url),'utf8');
  const controller=packageHtml.match(/<script type="module">([\s\S]*?)<\/script>/)[1];
  vm.runInNewContext(controller.replace(/^export /gm,''),ctx);
  const get=k=>elements.get('at-'+k);
  assert.equal(get('wipe-handle').attrs['aria-valuenow'],'50');
  assert.equal(get('map').dataset.sideBySide,'false');
  stories[1].click();
  assert.equal(get('map').dataset.sideBySide,'true');
  assert.equal(get('reference-stack').hidden,false);
  assert.equal(get('zoom-reset').disabled,true);
  stories[2].click();assert.equal(get('base').textContent,'-7.08 dB');assert.equal(get('recent').textContent,'+0.45 dB');
  const mirror=get('mirror').textContent,active=get('table').children.find(row=>row.attrs['aria-current']==='true');
  for(const [j,cell] of active.children.entries()){
    if(j!==1)assert.ok(mirror.includes((cell.children[0]??cell).textContent));
  }
  assert.equal(active.children[1].textContent,'2026-08-31');
  assert.equal(get('base-endpoints').textContent,'19 Aug → 12 Sept');
  assert.equal(get('base-endpoints').title,'2026-08-19 to 2026-09-12');
  const screens=()=>[...get('fit').children,...get('fit-other').children];
  assert.equal(screens().length,6);
  assert.match(get('fit-coverage').textContent,/full match.*partial match.*6 exploratory screens/);
  assert.match(get('fit-scope').textContent,/2026-09-12.*Reference 2026-08-19.*199 paired pixels/);
  assert.ok(get('chronology').children.some(p=>/right-censored/.test(p.textContent)));
  assert.match(mirror,/2026-09-12 23:39:18 UTC.*199 pixels/);
  assert.match(get('tour-next-check').textContent,/Check field evidence/);
  assert.match(get('tour-reference').textContent,/1.99-hectare zone.*2026-08-19 UTC/);
  const [aug,sep,oct]=get('tour-checkpoints').children;
  assert.equal(sep.attrs['aria-pressed'],'true');
  assert.equal(aug.children[2].textContent,'-7.53 dB from reference');
  assert.equal(sep.children[1].textContent,'+0.45 dB since 2026-08-31');
  oct.click();
  assert.equal(get('date').value.slice(0,10),'2026-10-18');
  assert.equal(get('base').textContent,'-6.57 dB');
  assert.equal(oct.attrs['aria-pressed'],'true');
  assert.equal(sep.attrs['aria-pressed'],'false');
  assert.equal(JSON.parse(new URLSearchParams(hash.slice(1)).get('view')).currentId,'acq_20261018T233918');
  assert.match(get('legend').children[1].textContent,/dB/);
  get('date').value=records.nepal_surface.observations[0].timestamp;get('date').onchange();
  assert.ok([aug,sep,oct].every(button=>button.attrs['aria-pressed']==='false'));
  assert.match(get('mirror').textContent,/No preceding visit/);
  stories[2].click();

  get('play').click();tick();assert.equal(get('date').value.slice(0,10),'2026-09-24');get('play').click();assert.equal(tick,null);
  stories[0].click();get('more').click();assert.equal(get('share').textContent,'60%');assert.equal(JSON.parse(new URLSearchParams(hash.slice(1)).get('view')).caseId,'jamuna_river');
  assert.equal(get('tour-visits').hidden,true);
  assert.equal(screens().length,6);
  assert.ok(get('fit').children.every(h=>['match','partial'].includes(h.dataset.fitStatus)));
  assert.ok(get('fit-other').children.some(h=>h.children[1].children.some(p=>/Required context.*IMERG/.test(p.textContent))));
  const crossing='[[10,10],[20,20],[10,20],[20,10]]';
  const flush=()=>new Promise(resolve=>setImmediate(resolve));
  async function rejectDraft(){
    const before=[hash,get('base').textContent,get('mirror').textContent];
    get('coords').value=crossing;get('probe').click();
    assert.equal(get('base').textContent,before[1]);
    await flush();
    assert.match(get('probe-help').textContent,/no crossing edges.*previous footprint/);
    assert.equal(get('coords').value,crossing);
    assert.deepEqual([hash,get('base').textContent,get('mirror').textContent],before);
    assert.ok(!get('export').disabled);
  }
  await rejectDraft(); // The saved footprint stays selected.
  get('coords').value='2,3';get('probe').click();await flush();
  assert.equal(get('base').textContent,'+0.50 dB');
  await rejectDraft(); // The measured native footprint stays selected too.
  const rejectedLink=new URLSearchParams(hash.slice(1));
  const rejectedView=JSON.parse(rejectedLink.get('view'));
  rejectedView.footprint={kind:'polygon',gridId:rejectedView.gridId,vertices:JSON.parse(crossing)};
  rejectedLink.set('view',JSON.stringify(rejectedView));
  hash='#'+rejectedLink;
  events.popstate();
  events.hashchange();
  await flush();
  assert.match(get('probe-help').textContent,/no crossing edges/);
  assert.equal(get('coords').value,crossing);
  assert.equal(JSON.parse(new URLSearchParams(hash.slice(1)).get('view')).footprint.kind,'saved');
  assert.match(get('base').textContent,/dB/);
  assert.equal(requests,4);
  assert.equal(get('table').children.length,10);
});
test('a small preview cannot zoom past eight display pixels per source pixel',()=>{
  assert.equal(atlasMapZoomLimit(400,100*8),2);
  assert.equal(atlasMapZoomLimit(800,100*8),1);
  assert.equal(atlasMapZoomLimit(400,1100*8),4);
});
test('counterfactual and thermal context are dated independently and never move to another study window',()=>{
  const c=records.nepal_surface,date=c.observations.find(o=>o.timestamp.startsWith('2026-09-12')).timestamp;
  const scenario=c.context.scenarios[date][0],thermal=c.context.thermal[2];
  const s=selection(records,{case:c.case,date,scenario:scenario.id,thermal:thermal.source});
  const packet=observationPacket(records,s);assert.equal(packet.context.thermal.timestamp,thermal.timestamp);
  assert.equal(packet.context.counterfactual.parameters.observation_id,scenario.parameters.observation_id);
  const october=selection(records,{...s,date:'2026-10-18'});
  assert.equal(observationPacket(records,october).context.counterfactual,null);
  assert.equal(observationPacket(records,october).context.rain,null);
  assert.equal(observationPacket(records,selection(records,{...s,case:'jamuna_river'})).context,null);
});

test('map coordinates match the same native cell at different sizes and scroll offsets',()=>{
  const shape=[1600,1800],point=[900.5,310.5];
  for(const width of [300,600,1200]){
    const rect={left:-147,top:67,width,height:width*1600/1800};
    const pos=atlasDisplayToGrid(rect,shape,rect.left+rect.width*point[0]/shape[1],rect.top+rect.height*point[1]/shape[0]);
    pos.forEach((x,i)=>assert.ok(Math.abs(x-point[i])<1e-9));
    assert.deepEqual(atlasDisplayToGrid(rect,shape,rect.left,rect.top),[0,0]);
    assert.equal(atlasDisplayToGrid(rect,shape,rect.left+width,rect.top),null);
  }
  const affine=[10,3,100,2,-10,500];
  assert.deepEqual(atlasGridToWorld(affine,[0.5,0.5]),[106.5,496]);
  assert.deepEqual(atlasWorldToGrid(affine,[106.5,496]),[0.5,0.5]);
  assert.throws(()=>atlasWorldToGrid([1,2,3,2,4,5],[0,0]),/singular/);
});

test('terrain samples native pixel centers and uses a 1× vertical scale',()=>{
  const mesh={size:41,width_m:17990,height_m:15990};
  assert.deepEqual(atlasTerrainUV(mesh.size,[1600,1800],0,0),[0.5/1800,0.5/1600]);
  assert.deepEqual(atlasTerrainUV(mesh.size,[1600,1800],40,40),[1799.5/1800,1599.5/1600]);
  const a=atlasTerrainPoint(mesh,20,20,100,100,45),b=atlasTerrainPoint(mesh,20,20,101,100,45);
  assert.deepEqual(a,[0,-0,0]);assert.equal(a[1]-b[1],Math.sqrt(.75));
  assert.equal(atlasTerrainPoint(mesh,20,40,100,100,0)[0]-atlasTerrainPoint(mesh,20,0,100,100,0)[0],17990);
});

test('late native request cannot replace the profile for a new case',async()=>{
  const catalog=JSON.parse(load('atlas-contract-records.json')),calls=[];
  const probe=createAtlasProbe({catalog,fetcher:(url,opts)=>new Promise(resolve=>calls.push({url,opts,resolve}))});
  const first=probe.measure(records.jamuna_river,'10,20'),second=probe.measure(records.nepal_surface,'10,20');
  assert.equal(calls.length,2);assert.equal(calls[0].opts.signal.aborted,true);
  const response=id=>({ok:true,json:async()=>({
    atlasBinding:{...catalog[id],selection:{kind:'point',row:10,col:20}},
    profile:{label:id,common_valid_pixels:121,observations:catalog[id].observations.map(o=>({observation_id:o.id,timestamp:o.utc}))}
  })});
  calls[1].resolve(response('nepal_surface'));
  assert.equal((await second).label,'nepal_surface');
  calls[0].resolve(response('jamuna_river'));
  assert.equal(await first,null);
});

test('chronology brackets crossings and censors return at the selected cutoff',()=>{
  const observations=['2026-08-01T00:00:00Z','2026-08-13T00:00:00Z','2026-08-25T00:00:00Z','2026-09-18T00:00:00Z','2026-09-30T00:00:00Z','2026-10-12T00:00:00Z'].map(timestamp=>({timestamp}));
  const c={observations,reference:observations[0].timestamp};
  const p={valid_pixels:7,series:[0,-1,null,-8,-5,-3].map(hh_reference=>({hh_reference}))};
  const censored=atlasChronology(c,p,4,3);
  assert.deepEqual(censored.onset,{lastBelowUtc:observations[1].timestamp,firstAtOrAboveUtc:observations[3].timestamp});
  assert.deepEqual(censored.persistence,{visitsAtOrAbove:2,assessedVisits:2});
  assert.equal(censored.unavailableVisits,1);
  assert.equal(censored.recovery.rightCensored,true);
  const returned=atlasChronology(c,p,5,3);
  assert.equal(returned.recovery.targetDb,4);
  assert.equal(returned.recovery.lastAboveUtc,observations[4].timestamp);
  assert.equal(returned.recovery.firstAtOrBelowUtc,observations[5].timestamp);
  assert.equal(atlasChronology(c,p,5,9).status,'no_threshold_crossing');
  assert.equal(atlasChronology(c,{...p,valid_pixels:0},5).status,'insufficient_evidence');
});

test('exact acquisition IDs distinguish same-day visits and keep absent data apart from zero',()=>{
  const observations=['2026-08-01T00:00:00Z','2026-08-01T12:00:00Z','2026-08-25T12:00:00Z'].map((timestamp,i)=>({timestamp,observation_id:'visit'+i}));
  const c={observations,reference:observations[0].timestamp};
  const p={valid_pixels:3,series:[{}, {hh_successive:0}, {hh_successive:2}]};
  const gaps=[{start:'2026-08-08T00:00:00Z',end:'2026-08-12T00:00:00Z'}];
  const support=atlasTraceSupport(p,5);
  assert.notEqual(atlasVisitLabel(c,observations[0]),atlasVisitLabel(c,observations[1]));
  const zero=atlasComparison(c,p,1,'successive',support,gaps);
  assert.equal(zero.values.hh,0);
  assert.equal(zero.target.id,'visit0');
  assert.equal(zero.current.id,'visit1');
  assert.equal(zero.elapsedDays,.5);
  assert.equal(zero.values.hv,null);
  assert.equal(atlasComparison(c,p,2,'successive',support,gaps).documentedGap,true);
  assert.equal(atlasComparison(c,p,1,'successive',{...support,validPixels:0}).values.hh,null);
});

test('late scenario responses are discarded after an anchor change',async()=>{
  const pending=[],changes=[];
  const flow=createAtlasScenarios({portable:false,changed:()=>changes.push(flow.get()),fetcher:(url,opts)=>new Promise(resolve=>pending.push({url,opts,resolve}))});
  const o={observation_id:'radar-a',timestamp:'2026-08-19T23:39:18Z'};
  const model={modelVersion:'version',inputsSha256:'inputs',anchors:{'radar-a':'model-a'}};
  const view={case:'nepal_surface',scenarioRun:{anchorUtc:o.timestamp,rainfall_multiplier:1.5,duration_hours:48,wetness:'wet'}};
  flow.select(view,o,model);
  flow.select({case:'jamuna_river'},{observation_id:'different'},null);
  assert.equal(pending[0].opts.signal.aborted,true);
  const response=(call,inputs_sha256)=>({ok:true,json:async()=>({
    case_id:'nepal_case_01',model_version:'version',inputs_sha256,parameters:JSON.parse(call.opts.body),
    scenario_id:'flood-00000000000000000000',preview_url:'/cases/nepal_case_01/flood/scenarios/flood-00000000000000000000/scenario.png'
  })});
  pending[0].resolve(response(pending[0],'inputs'));
  await new Promise(resolve=>setImmediate(resolve));
  assert.deepEqual(changes,[]);
  flow.select(view,o,model);
  pending[1].resolve(response(pending[1],'stale'));
  await new Promise(resolve=>setImmediate(resolve));
  assert.match(flow.select(view,o,model).status,/accepted inputs/);
  flow.retry();flow.select(view,o,model);
  pending[2].resolve(response(pending[2],'inputs'));
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(flow.get().parameters.observation_id,'model-a');
});


test('wetland occurrence uses valid recorded visits and keeps optical evidence on the frozen footprint',()=>{
  assert.deepEqual(atlasObservedOccupancy([{matches:true},{matches:false},{matches:null},{}]),
    {observed:4,valid:2,unknown:2,matching:1,fraction:.5});
  assert.equal(atlasObservedOccupancy([{matches:null}]).fraction,null);
  const c=records.tanguar_wetland,meta=JSON.parse(load('atlas-contract-records.json'))[c.case];
  const s=selection(records,{case:c.case,date:'2026-08-29',profile:4,lens:'wetland'});
  const review=atlasFieldReview(c,meta,c.profiles[4],s);
  assert.equal(review.selected.optical.clear_assessable_pixels,1089);
  assert.deepEqual(review.visits.filter(v=>v.matches).map(v=>v.utc.slice(0,10)),['2026-08-29','2026-09-10']);
  assert.equal(review.occurrence.fraction,.2);
  assert.equal(review.visits.some(v=>v.utc.startsWith('2026-08-05')),false);
  assert.equal(atlasFieldReview(c,meta,c.profiles[6],{...s,profile:6}).selected.optical,null);
  assert.equal(atlasFieldReview(c,meta,c.profiles[0],{...s,profile:0}).selected.optical,null);
  const local=atlasFieldReview(c,meta,{...c.profiles[4],review:meta.footprints[4].review},{...s,native:'799,899'});
  assert.equal(local.selected.optical,null);
});
