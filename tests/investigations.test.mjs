import * as navigation from '../web/navigation-model.mjs';
import * as sharedView from '../web/investigation-state.mjs';
/** Controller tests use explicit DOM/canvas/image mocks, not a browser or visual QA. */
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs/promises';
import {createPlayback} from '../web/playback.mjs';
import * as model from '../web/investigation-model.mjs';
import * as timeAxis from '../web/time-axis.mjs';
import * as dualpol from '../web/dualpol.mjs';
import * as contextV2 from '../web/context-v2.mjs';
import * as reasoning from '../web/reasoning.mjs';
const root=new URL('../',import.meta.url);
async function fixture({pendingHydrology=false,search='',missingDualpol=false,hash='',recordVersion=null}={}){
 const html=await fs.readFile(new URL('web/investigations.html',root),'utf8');
 const source=(await fs.readFile(new URL('web/investigations.mjs',root),'utf8')).replace(/^import .*;\n/gm,'');
 const elements=new Map(),nodes=[];
 const parse=text=>Object.fromEntries([...text.matchAll(/([\w:-]+)(?:="([^"]*)")?/g)].map(m=>[m[1],m[2]??'']));
 class Element{
  constructor(attrs={},text=''){this.dataset={};this.attributes=attrs;this.listeners={};this.children=[];this.options=[];this.hidden='hidden'in attrs;this.disabled='disabled'in attrs;this.checked='checked'in attrs;this.value=attrs.value||'';this.textContent=text;this._html='';const classes=new Set((attrs.class||'').split(' '));this.classList={toggle:(v,yes)=>yes?classes.add(v):classes.delete(v)};for(const [k,v]of Object.entries(attrs))if(k.startsWith('data-'))this.dataset[k.slice(5)]=v;nodes.push(this);}
  set innerHTML(value){this._html=value;for(const node of this.children){const at=nodes.indexOf(node);if(at>=0)nodes.splice(at,1);}this.children=[];this.options=[];for(const m of value.matchAll(/<(button|option)\s+([^>]+)>([^<]*)/g)){const child=new Element(parse(m[2]),m[3]);this.children.push(child);if(m[1]==='option')this.options.push(child);}if(this.options.length)this.value=this.options[0].value;}
  get innerHTML(){return this._html;}
  get selectedOptions(){return this.options.filter(o=>o.value===this.value);}
  setAttribute(k,v){this.attributes[k]=v;}removeAttribute(k){delete this.attributes[k];}
  addEventListener(name,callback){(this.listeners[name]||=[]).push(callback);}
  async emit(name,extra={}){for(const callback of this.listeners[name]||[])await callback({target:this,...extra});for(let i=0;i<4;i++)await new Promise(resolve=>setImmediate(resolve));}
  getContext(){return context;}getBoundingClientRect(){return {left:0,top:0,width:600,height:600};}
  showModal(){this.open=true;}close(){this.open=false;}click(){}
 }
 const context=Object.fromEntries(['clearRect','drawImage','save','beginPath','rect','clip','restore','moveTo','lineTo','stroke','closePath','fill','arc'].map(k=>[k,()=>{}]));
 for(const m of html.matchAll(/<[\w-]+\s+([^>]+)>/g)){const attrs=parse(m[1]);if(attrs.id||Object.keys(attrs).some(k=>k.startsWith('data-'))){const el=new Element(attrs);if(attrs.id)elements.set(attrs.id,el);}}
 for(const m of html.matchAll(/<select\s+[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g))elements.get(m[1]).innerHTML=m[2];
 elements.get('split').value='50';
 const document={hidden:false,getElementById:id=>{assert.ok(elements.has(id),'Missing HTML ID '+id);return elements.get(id);},querySelectorAll:selector=>{const match=selector.match(/^\[data-([\w-]+)(?:="([^"]+)")?\]$/);assert.ok(match,'Unsupported selector '+selector);return nodes.filter(n=>n.dataset[match[1]]!==undefined&&(match[2]===undefined||n.dataset[match[1]]===match[2]));},createElement:()=>new Element(),addEventListener(){}};
 const fetched=[],held=new Map();
 function holdUrl(url){let release;const promise=new Promise(resolve=>{release=resolve;});held.set(url,promise);return release;}
 async function fetch(url){fetched.push(url);if(held.has(url))await held.get(url);if(missingDualpol&&url.includes('/dualpol-v1/'))return {ok:false,status:404};let path=url==='/api/investigations'?(recordVersion?'/cases/investigations-'+recordVersion+'.json':'/cases/investigations.json'):url;if(url==='/api/claims')path='/cases/'+JSON.parse(await fs.readFile(new URL('config.claims.json',root),'utf8')).snapshot_version+'.json';if(url.includes('/investigation-probe?')||url.includes('/investigation-reasoning?')){
  const manifest=JSON.parse(await fs.readFile(new URL('web/public/cases/nepal_surface/investigation/manifest.json',root),'utf8'));return {ok:true,json:async()=>({...manifest.profiles[0],label:'Clicked neighborhood',center_row:1,center_col:1})};
 }assert.ok(path.startsWith('/cases/'),'Unexpected fetch '+path);const data=JSON.parse(await fs.readFile(new URL('web/public'+path,root),'utf8'));if(pendingHydrology&&url==='/api/investigations')for(const row of data.cases)if(['river','wetland'].includes(row.module))Object.assign(row,{status:'AWAITING_DATA',local_source_count:0,minimum_observations:3});return {ok:true,json:async()=>data};}
 class ImageMock{set src(url){this.url=url;queueMicrotask(()=>this.onload());}}
 const timers=new Map();let timer=0;
 const location={search,hash};
 const sandbox={...navigation,...sharedView,...model,...timeAxis,...dualpol,...contextV2,...reasoning,writeView:view=>sharedView.writeView(view,{location,history:{replaceState(a,b,hash){location.hash=hash;}}}),createPlayback:options=>createPlayback({...options,setTimer:fn=>{timers.set(++timer,fn);return timer;},clearTimer:id=>timers.delete(id)}),console,document,window:{location,history:{replaceState(a,b,hash){location.hash=hash;}},addEventListener(){}},fetch,Image:ImageMock,URL,URLSearchParams,Blob,setTimeout:()=>1};
 const api=await vm.runInNewContext('(async()=>{'+source+'\nreturn {state,get player(){return player}};})()',sandbox);
 assert.equal(elements.get('investigation-error').hidden,true,elements.get('investigation-error').textContent);
 const until=async predicate=>{const deadline=Date.now()+2000;while(!predicate()&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,2));assert.ok(predicate(),elements.get('investigation-error').textContent||'Controller transition did not complete');};
 return {api,elements,document,fetched,until,holdUrl,location};
}
test('new workspace starts with real saved HH/HV data and the tracked persistence profile',async()=>{
 const f=await fixture();assert.equal(f.api.state.data.case_id,'nepal_surface');assert.equal(f.api.state.index,2);
 assert.equal(f.elements.get('measure-hh').textContent,'-7.08 dB');assert.equal(f.elements.get('measure-hv').textContent,'-2.45 dB');
 assert.ok(f.elements.get('measurement-conclusion').textContent.includes('persists'));assert.equal(f.elements.get('ready-workspace').hidden,false);
});
test('date and layer changes keep measurements and available controls synchronized',async()=>{
 const f=await fixture();f.elements.get('layer-select').value='successive';await f.elements.get('layer-select').emit('change');
 await f.document.querySelectorAll('[data-visit="0"]')[0].emit('click');
 assert.equal(f.api.state.index,0);assert.equal(f.api.state.layer,'hh');assert.equal(f.elements.get('measure-successive').textContent,'Unavailable');
 f.elements.get('layer-select').value='hv';await f.elements.get('layer-select').emit('change');assert.equal(f.api.state.layer,'hv');
});
test('river and wetland modes show download readiness without fabricated observations',async()=>{
 const f=await fixture({pendingHydrology:true});for(const mode of ['river','wetland']){
 await f.document.querySelectorAll('[data-mode="'+mode+'"]')[0].emit('click');
 assert.equal(f.api.state.data,null);assert.equal(f.elements.get('pending').hidden,false);assert.equal(f.elements.get('ready-workspace').hidden,true);
 assert.ok(f.elements.get('download-dates').innerHTML.includes('18 Jun 2026'));assert.equal(f.api.player,null);
 }
});
test('case selection loads the independent outline and its actual native reference profile',async()=>{
 const f=await fixture();f.elements.get('case-select').value='nepal_impact_corridor';await f.elements.get('case-select').emit('change');
 assert.equal(f.api.state.data.case_id,'nepal_impact_corridor');assert.equal(f.elements.get('reference-panel').hidden,false);
 assert.ok(f.elements.get('reference-detail').textContent.includes('6.42 km²'));assert.equal(f.api.state.profile.status,'MEASURED');
});

test('real Bangladesh imports activate both workspaces with six saved visits and a measured profile',async()=>{
 const f=await fixture();
 for(const [mode,id] of [['river','jamuna_river'],['wetland','tanguar_wetland']]){
  await f.document.querySelectorAll('[data-mode="'+mode+'"]')[0].emit('click');
  await f.until(()=>f.api.state.data?.case_id===id&&f.elements.get('map-loading').hidden);
  assert.equal(f.api.state.data.case_id,id);assert.equal(f.api.state.data.observations.length,6);
  assert.equal(f.elements.get('pending').hidden,true);assert.equal(f.elements.get('response-panel').hidden,false);
  assert.equal(f.api.state.profile.status,'MEASURED');assert.equal(f.elements.get('export-dossier').disabled,false);
  f.elements.get('layer-select').value=mode==='river'?'river':'wetland';await f.elements.get('layer-select').emit('change');
  assert.equal(f.api.state.layer,mode==='river'?'river':'wetland');
 }
});
test('river deep link opens the actual Jamuna case directly',async()=>{
 const f=await fixture({search:'?mode=river'});assert.equal(f.api.state.mode,'river');assert.equal(f.api.state.data.case_id,'jamuna_river');
});

test('calendar follows case and selected date; playback offers only observed visits',async()=>{
 const f=await fixture({search:'?mode=river'});
 assert.equal(f.api.state.calendar.slots.length,11);
 assert.equal(f.document.querySelectorAll('[data-visit]').length,6);
 await f.document.querySelectorAll('[data-visit="2"]')[0].emit('click');
 assert.match(f.elements.get('acquisition-calendar').innerHTML,/24 days between recorded visits/);
 assert.match(f.elements.get('successive-note').textContent,/24 days between recorded visits/);
 assert.doesNotMatch(f.elements.get('profile-chart').innerHTML,/instrument-gap-shade/);
 assert.doesNotMatch(f.elements.get('profile-chart').innerHTML,/interval-gap/);
 assert.equal((f.elements.get('profile-chart').innerHTML.match(/class="hh-line"/g)||[]).length,1);
 f.elements.get('layer-select').value='successive';await f.elements.get('layer-select').emit('change');
 assert.match(f.elements.get('map-note').textContent,/24 days between recorded visits/);
 await f.document.querySelectorAll('[data-mode="surface"]')[0].emit('click');
 await f.until(()=>f.api.state.data?.case_id==='jamuna_river'&&f.elements.get('map-loading').hidden);
 assert.equal(f.api.state.country,'bangladesh');
 assert.equal(f.api.state.calendar.series_id,'bangladesh_069_014');
 assert.equal(f.api.state.calendar.slots.length,11);
});
test('River Memory and Wetland Pulse both explain four missing GCOV dates and never connect across them',async()=>{
 for(const [mode,id] of [['river','jamuna_river'],['wetland','tanguar_wetland']]){
  const f=await fixture({search:'?mode='+mode});assert.equal(f.api.state.data.case_id,id);assert.equal(f.api.state.data.observations.length,6);
  const calendar=f.elements.get('acquisition-calendar').innerHTML;assert.doesNotMatch(calendar.split('<details')[0],/05 Aug|not loaded|outage/);assert.match(calendar,/permanent satellite outage/);assert.equal((calendar.match(/NASA GCOV ↓/g)||[]).length,4);
  assert.equal((f.elements.get('profile-chart').innerHTML.match(/class="hh-line"/g)||[]).length,1);
  assert.equal((f.elements.get('profile-chart').innerHTML.match(/class="hv-line"/g)||[]).length,1);
  assert.equal((f.elements.get('cpr-profile-chart').innerHTML.match(/class="cpr-line"/g)||[]).length,1);
  assert.match(f.elements.get('profile-footnote').textContent,/Points show recorded visits/);
 }
});

test('dual-pol layers, footprint CPR, gap warnings and cutoff explorer stay synchronized',async()=>{
 const f=await fixture({search:'?mode=river'});
 assert.ok(f.api.state.dualpol);assert.equal(f.elements.get('dualpol-ready').hidden,false);
 assert.equal(f.elements.get('dualpol-hints-panel').hidden,false);
 f.elements.get('layer-select').value='composite';await f.elements.get('layer-select').emit('change');
 assert.equal(f.api.state.layer,'composite');assert.match(f.elements.get('legend-note').textContent,/identical for every case/);
 await f.document.querySelectorAll('[data-visit="2"]')[0].emit('click');
 f.elements.get('layer-select').value='cpr_successive';await f.elements.get('layer-select').emit('change');
 assert.equal(f.api.state.layer,'cpr_successive');assert.match(f.elements.get('map-note').textContent,/24 days between recorded visits/);
 assert.match(f.elements.get('legend-note').textContent,/exactly 0 dB/);
 f.elements.get('sensitivity-mode').value='hh';await f.elements.get('sensitivity-mode').emit('change');
 assert.match(f.elements.get('sensitivity-chart').innerHTML,/hh sweep/);
 const expected=f.api.state.profile.observations[2].hv_mean_db-f.api.state.profile.observations[2].hh_mean_db;
 assert.equal(f.elements.get('measure-cpr').textContent,expected.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' dB');
 await f.document.querySelectorAll('[data-visit="0"]')[0].emit('click');
 assert.equal(f.api.state.layer,'hh');
 const unavailable=f.elements.get('layer-select').options.filter(o=>['hh_successive','hv_successive','cpr_successive','hint_hh','hint_hv'].includes(o.value));
 assert.ok(unavailable.every(o=>o.disabled));
});


test('missing optional dual-pol products preserve the original investigation and show a notice',async()=>{
 const f=await fixture({missingDualpol:true});
 assert.equal(f.api.state.dualpol,null);assert.equal(f.elements.get('ready-workspace').hidden,false);
 assert.equal(f.elements.get('measure-hh').textContent,'-7.08 dB');
 assert.match(f.elements.get('dualpol-status').textContent,/unavailable or out of date/);
 assert.equal(f.elements.get('dualpol-ready').hidden,true);
 const options=f.elements.get('layer-select').options.filter(o=>o.value==='composite'||o.value==='cpr');
 assert.ok(options.every(o=>o.disabled));
});


test('separate terrain layers stay static and missing scientific rain is explicit',async()=>{
 const f=await fixture({search:'?mode=wetland'});
 assert.equal(f.api.state.contextV2.case_id,'tanguar_wetland');
 assert.match(f.elements.get('context-v2-detail').innerHTML,/unavailable/);
 f.elements.get('layer-select').value='context_slope';await f.elements.get('layer-select').emit('change');
 assert.equal(f.api.state.layer,'context_slope');assert.equal(f.elements.get('map-date').textContent,'STATIC TERRAIN CONTEXT');
 assert.match(f.elements.get('map-coverage').textContent,/30 m terrain/);
});

test('saved DNA footprints and ledger are displayed with scoped rule evidence',async()=>{
 const f=await fixture({search:'?mode=river'});
 assert.equal(f.api.state.evidence.profiles.length,7);assert.match(f.elements.get('reasoning-detail').innerHTML,/observed visits/);
 assert.match(f.elements.get('reasoning-detail').innerHTML,/Mean HH .* dB · criterion ≤ -17 dB<small>Outside criterion/);
 assert.match(f.elements.get('reasoning-detail').innerHTML,/Required context · Scientific IMERG rainfall in the prior 72 h/);
 assert.match(f.elements.get('claims-panel').innerHTML,/TP-PERSIST/);
 f.elements.get('profile-select').value='1';await f.elements.get('profile-select').emit('change');
 assert.equal(f.api.state.selectedEvidence.profile.saved_evidence_index,1);
 assert.match(f.elements.get('reasoning-detail').innerHTML,/No continuous persistence/);
 await f.elements.get('draw-polygon').emit('click');assert.ok(f.api.state.drawing);assert.equal(f.elements.get('finish-polygon').hidden,false);
 await f.elements.get('draw-polygon').emit('click');assert.equal(f.api.state.drawing,false);
});

test('frozen reference selection is scoped to the selected footprint and visit',async()=>{
 const f=await fixture({search:'?mode=river'});
 const index=f.api.state.evidence.profiles.findIndex(p=>p.reference_footprint_id?.endsWith('_target_geographic'));
 assert.ok(index>=0);f.elements.get('profile-select').value=String(index);await f.elements.get('profile-select').emit('change');assert.equal(f.api.state.polygon.length,4);
 await f.document.querySelectorAll('[data-visit="3"]')[0].emit('click');
 assert.match(f.elements.get('matched-reference-detail').innerHTML,/date-matched, descriptive/);
 assert.match(f.elements.get('reasoning-detail').innerHTML,/Matched HLS water-mask context/);
 await f.document.querySelectorAll('[data-visit="0"]')[0].emit('click');
 assert.match(f.elements.get('matched-reference-detail').innerHTML,/Unavailable/);
 assert.doesNotMatch(f.elements.get('reasoning-detail').innerHTML,/Matched HLS water-mask context/);
 f.elements.get('profile-select').value='0';await f.elements.get('profile-select').emit('change');
 assert.match(f.elements.get('matched-reference-detail').innerHTML,/No date-matched reference evaluated/);
});

test('investigations offer the measured pair maps and omit the catalog-only gate',async()=>{
 const f=await fixture({recordVersion:'bangladesh-v2'});assert.match(f.elements.get('interferometry-detail').innerHTML,/MEASURED COHERENCE/);
 for(const [mode,caseId] of [['river','jamuna_river'],['wetland','tanguar_wetland']]){
  await f.document.querySelectorAll('[data-mode="'+mode+'"]')[0].emit('click');
  await f.until(()=>f.api.state.data?.case_id===caseId);
  const panel=f.elements.get('interferometry-detail').innerHTML;
  assert.match(panel,/2026-09-22 → 2026-10-04/);
  assert.match(panel,/2026-10-04 → 2026-10-16/);
  assert.match(panel,/layer=coherence/);
  assert.doesNotMatch(panel,/displacement|gate not open/i);
 }
});

test('late reference responses cannot overwrite a newly selected case',async()=>{
 const f=await fixture(),url='/cases/nepal_impact_corridor/references-v1/manifest.json';
 const release=f.holdUrl(url);f.elements.get('case-select').value='nepal_impact_corridor';
 const pending=f.elements.get('case-select').emit('change');
 await f.until(()=>f.fetched.includes(url));
 await f.document.querySelectorAll('[data-mode="river"]')[0].emit('click');
 await f.until(()=>f.api.state.references?.case_id==='jamuna_river');
 assert.equal(f.api.state.references.case_id,'jamuna_river');
 release();await pending;
 assert.equal(f.api.state.data.case_id,'jamuna_river');assert.equal(f.api.state.references.case_id,'jamuna_river');
 assert.equal(f.api.state.contextV2.case_id,'jamuna_river');
});

test('shared links restore an actual case date layer and saved reference footprint',async()=>{
 const f=await fixture({hash:'#case=jamuna_river&mode=river&date=2026-08-29&footprint=saved%3A4&overlay=river'});
 assert.equal(f.api.state.data.case_id,'jamuna_river');assert.equal(f.api.state.index,3);assert.equal(f.api.state.layer,'river');
 assert.equal(f.api.state.selectedEvidence.reference_footprint_id,'jamuna_river_target_geographic');
 assert.match(f.location.hash,/date=2026-08-29/);
});
test('unloaded shared dates are explicit and never synthesize a visit',async()=>{
 const f=await fixture({hash:'#case=nepal_surface&date=2026-08-25'});
 assert.match(f.elements.get('shared-view-note').textContent,/not loaded/);assert.equal(f.api.state.data.observations.length,3);
});
test('guided movements use the preserved footprint and real observed dates',async()=>{
 const f=await fixture();await f.document.querySelectorAll('[data-movement="1"]')[0].emit('click');
 await f.until(()=>f.api.state.index===1);assert.equal(f.api.state.profile.footprint_pixels,199);
 await f.document.querySelectorAll('[data-movement="2"]')[0].emit('click');
 await f.until(()=>f.api.state.index===2);assert.match(f.elements.get('measure-hh').textContent,/-7.08/);
 await f.document.querySelectorAll('[data-movement="3"]')[0].emit('click');await f.until(()=>f.api.state.data?.case_id==='jamuna_river');
});
test('map keyboard supports cursor movement polygon vertices and cancellation',async()=>{
 const f=await fixture();await f.elements.get('draw-polygon').emit('click');
 await f.elements.get('investigation-map').emit('keydown',{key:'ArrowRight',preventDefault(){}});
 assert.equal(f.api.state.marker.col,1201);
 await f.elements.get('investigation-map').emit('keydown',{key:'Enter',preventDefault(){}});assert.equal(f.api.state.polygon.length,1);
 await f.elements.get('investigation-map').emit('keydown',{key:'Escape',preventDefault(){}});assert.equal(f.api.state.polygon.length,0);assert.equal(f.api.state.drawing,false);
});

test('Bangladesh surface focus exposes both real study areas without changing their scientific module',async()=>{
 const f=await fixture({search:'?country=bangladesh&mode=surface'});
 assert.equal(f.api.state.country,'bangladesh');assert.equal(f.api.state.mode,'surface');assert.equal(f.api.state.data.case_id,'jamuna_river');assert.equal(f.api.state.data.module,'river');
 assert.equal(f.elements.get('case-select').options.length,2);assert.equal(f.elements.get('nepal-record-link').hidden,true);
 f.elements.get('case-select').value='tanguar_wetland';await f.elements.get('case-select').emit('change');
 await f.until(()=>f.api.state.data?.case_id==='tanguar_wetland'&&f.elements.get('map-loading').hidden);
 assert.equal(f.api.state.mode,'surface');assert.equal(f.api.state.data.observations.length,6);assert.match(f.location.hash,/mode=surface/);
});
test('shared Bangladesh surface link restores the wetland footprint in the same geographic focus',async()=>{
 const f=await fixture({search:'?country=nepal',hash:'#case=tanguar_wetland&mode=surface&date=2026-08-17&footprint=saved:0'});
 assert.equal(f.api.state.country,'bangladesh');assert.equal(f.api.state.mode,'surface');assert.equal(f.api.state.data.case_id,'tanguar_wetland');assert.equal(f.api.state.index,2);assert.equal(f.elements.get('case-select').options.length,2);
});

test('active Bangladesh record binds ten visits to matching sidecars in all three focuses',async()=>{
 for(const mode of ['river','wetland','surface']){
  const f=await fixture({search:'?country=bangladesh&mode='+mode,recordVersion:'bangladesh-v2'});
  assert.equal(f.api.state.data.observations.length,10);assert.equal(f.api.state.dualpol.observations.length,10);assert.equal(f.api.state.contextV2.rain.length,10);
  assert.equal(f.api.state.calendar.slots.filter(s=>s.status==='observed').length,10);
  const calendar=f.elements.get('acquisition-calendar').innerHTML;assert.match(calendar,/10 recorded visits/);assert.doesNotMatch(calendar,/Remaining shared GCOV download|NASA GCOV ↓/);assert.match(calendar,/permanent satellite outage/);
  assert.equal(f.document.querySelectorAll('[data-visit]').length,10);
  for(let i=0;i<10;i++){await f.api.player.seek(i);assert.equal(f.api.state.index,i);assert.ok(f.api.state.profile.observations[i].timestamp===f.api.state.data.observations[i].timestamp);}
  assert.ok(f.fetched.some(url=>url.includes('/bangladesh-v2/dualpol-v1/')));assert.ok(f.fetched.some(url=>url.includes('/bangladesh-v2/context-v2/')));
 }
});
test('added Bangladesh date is restored through a shared link and the outage remains unavailable',async()=>{
 const f=await fixture({hash:'#case=tanguar_wetland&mode=surface&date=2026-07-12&footprint=saved:0&overlay=cpr',recordVersion:'bangladesh-v2'});
 assert.equal(f.api.state.data.case_id,'tanguar_wetland');assert.equal(f.api.state.index,2);assert.equal(f.api.state.layer,'cpr');assert.equal(f.api.state.mode,'surface');
 const missing=await fixture({hash:'#case=jamuna_river&mode=river&date=2026-08-05',recordVersion:'bangladesh-v2'});assert.match(missing.elements.get('shared-view-note').textContent,/not loaded/);assert.ok(!missing.api.state.data.observations.some(o=>o.timestamp.startsWith('2026-08-05')));
});

test('all Bangladesh focuses omit unobserved date cards and chart bands without changing values',async()=>{
 for(const mode of ['river','wetland','surface']){
  const f=await fixture({search:'?country=bangladesh&mode='+mode,recordVersion:'bangladesh-v2'});
  const visible=f.elements.get('acquisition-calendar').innerHTML.split('<details class="calendar-provenance">')[0];
  assert.equal((visible.match(/class="nominal-slot observed"/g)||[]).length,10);assert.doesNotMatch(visible,/05 Aug|outage|instrument-gap/);
  for(const id of ['profile-chart','cpr-profile-chart'])assert.doesNotMatch(f.elements.get(id).innerHTML,/instrument-gap-shade/);
  const profile=f.api.state.profile,values=profile.observations.map(r=>[r.hh_mean_db,r.hv_mean_db]);
  await f.api.player.seek(4);assert.equal(f.api.state.data.observations[4].timestamp.slice(0,10),'2026-08-17');
  assert.deepEqual(profile.observations.map(r=>[r.hh_mean_db,r.hv_mean_db]),values);assert.match(f.elements.get('successive-note').textContent,/24 days between recorded visits/);
 }
});
