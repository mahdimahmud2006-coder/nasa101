/** DOM/image doubles exercise controller bindings, not rendered-browser acceptance. */
import test from 'node:test';import assert from 'node:assert/strict';import vm from 'node:vm';import fs from 'node:fs/promises';
import {createPlayback} from '../web/playback.mjs';import * as model from '../web/expanded-model.mjs';
const root=new URL('../',import.meta.url);
async function fixture(hash=''){
 const html=await fs.readFile(new URL('web/expanded.html',root),'utf8');
 const source=(await fs.readFile(new URL('web/expanded.mjs',root),'utf8')).replace(/^import .*;\n/gm,'').replace('selectCase(initial.case,initial).catch(fail);','await selectCase(initial.case,initial).catch(fail);');
 const nodes=[],elements=new Map(),held=new Map(),timers=new Map(),loadTimers=new Map(),failedImages=new Set(),stalledImages=new Set();let timerId=0,loadTimerId=0;
 const attrs=text=>Object.fromEntries([...text.matchAll(/([\w:-]+)(?:="([^"]*)")?/g)].map(m=>[m[1],m[2]??'']));
 class Element{
  constructor(a={},text=''){this.attributes=a;this.value=a.value||'';this.textContent=text;this.hidden='hidden'in a;this.disabled='disabled'in a;this.checked='checked'in a;this.listeners={};this.style={};this.children=[];this.options=[];this.dataset={};this.classList={toggle(){}};for(const [k,v] of Object.entries(a))if(k.startsWith('data-'))this.dataset[k.slice(5)]=v;nodes.push(this);}
  set innerHTML(text){this._html=text;for(const n of this.children){const i=nodes.indexOf(n);if(i>=0)nodes.splice(i,1);}this.children=[];this.options=[];for(const m of text.matchAll(/<(button|option)\s+([^>]+)>([^<]*)/g)){const n=new Element(attrs(m[2]),m[3]);this.children.push(n);if(m[1]==='option')this.options.push(n);}if(this.options.length)this.value=this.options[0].value;}
  get innerHTML(){return this._html||'';}get selectedOptions(){return this.options.filter(n=>n.value===this.value);}
  setAttribute(k,v){this.attributes[k]=v;}removeAttribute(k){delete this.attributes[k];}addEventListener(k,f){(this.listeners[k]||=[]).push(f);}
  async emit(k,more={}){for(const f of this.listeners[k]||[])await f({target:this,preventDefault(){},...more});for(let i=0;i<4;i++)await new Promise(setImmediate);}
  getBoundingClientRect(){return {left:0,top:0,width:600,height:600};}click(){}
 }
 for(const m of html.matchAll(/<[\w-]+\s+([^>]+)>/g)){const a=attrs(m[1]);if(a.id)elements.set(a.id,new Element(a));}
 for(const m of html.matchAll(/<select\s+[^>]*id="([^"]+)"[^>]*>([\s\S]*?)<\/select>/g))elements.get(m[1]).innerHTML=m[2];
 const document={hidden:false,getElementById:id=>{assert.ok(elements.has(id),id);return elements.get(id);},querySelectorAll:()=>nodes.filter(n=>n.dataset.visit!==undefined),createElement:()=>new Element(),addEventListener(){}};
 const location={hash};const history={replaceState(a,b,hash){location.hash=hash;}};
 const fetch=async url=>{if(held.has(url))await held.get(url);if(url.includes('/expanded-probe?')){const id=url.split('/')[3],m=JSON.parse(await fs.readFile(new URL('web/public/cases/'+id+'/expanded-v1/manifest.json',root),'utf8'));return {ok:true,json:async()=>({profile:{...m.profiles[0],label:'Inspected neighborhood'}})};}const data=JSON.parse(await fs.readFile(new URL('web/public'+url,root),'utf8'));return {ok:true,json:async()=>data};};
 class Image{set src(value){this.url=value;if(!stalledImages.has(value))queueMicrotask(()=>failedImages.has(value)?this.onerror():this.onload());}}
 const sandbox={...model,createPlayback:options=>createPlayback({...options,setTimer:fn=>{timers.set(++timerId,fn);return timerId;},clearTimer:id=>timers.delete(id)}),document,location,history,window:{addEventListener(){}},fetch,Image,URL,URLSearchParams,Blob,setTimeout:fn=>{loadTimers.set(++loadTimerId,fn);return loadTimerId;},clearTimeout:id=>loadTimers.delete(id),console};
 const api=await vm.runInNewContext('(async()=>{'+source+'\nreturn {selectCase,show,seekVisit,get state(){return {manifest,index,layer,profile,point,sequence}},get player(){return player}};})()',sandbox);
 assert.equal(elements.get('error').hidden,true,elements.get('error').textContent);
 return {api,elements,location,timers,failImage:url=>failedImages.add(url),stallImage:url=>stalledImages.add(url),expireLoad(){const next=loadTimers.entries().next().value;assert.ok(next,'Expected frame load deadline');loadTimers.delete(next[0]);next[1]();},async tick(){const next=timers.entries().next().value;assert.ok(next,'Expected scheduled playback frame');timers.delete(next[0]);await next[1]();},hold(url){let release;held.set(url,new Promise(r=>release=r));return release;}};
}
test('expanded controller shows actual latest data then explicit unavailable previous difference',async()=>{
 const f=await fixture();assert.equal(f.api.state.index,9);assert.match(f.elements.get('metrics').innerHTML,/-6.566/);assert.equal(f.elements.get('map-image').hidden,false);
 f.elements.get('layer').value='hh_successive';await f.elements.get('layer').emit('change');await f.api.seekVisit(0);
 assert.equal(f.elements.get('map-image').hidden,true);assert.match(f.elements.get('map-empty').textContent,/no previous/);
});
test('coherence selects actual pair, enables pair playback and leaves other dates unavailable',async()=>{
 const f=await fixture();f.elements.get('layer').value='coherence20';await f.elements.get('layer').emit('change');
 assert.equal(f.api.state.index,5);assert.equal(f.elements.get('play').disabled,false);assert.match(f.elements.get('map-image').src,/gunw_0_coherence20/);
 await f.api.seekVisit(9);assert.equal(f.elements.get('map-image').hidden,true);assert.match(f.elements.get('map-empty').textContent,/No available GUNW/);
});
test('case changes cannot be overwritten by a late previous response',async()=>{
 const f=await fixture();const release=f.hold('/cases/nepal_impact_corridor/expanded-v1/manifest.json');
 const pending=f.api.selectCase('nepal_impact_corridor');await f.api.selectCase('nepal_surface');release();await pending;
 assert.equal(f.api.state.manifest.case_id,'nepal_surface');assert.match(f.elements.get('map-image').src,/nepal_surface/);
});
test('saved crop footprint and actual date restore from the expanded link',async()=>{
 const f=await fixture('#case=nepal_impact_corridor&date=2026-07-14T23%3A39%3A20Z&footprint=1&layer=hv');
 assert.equal(f.api.state.manifest.case_id,'nepal_impact_corridor');assert.equal(f.api.state.index,2);assert.equal(f.api.state.profile.label,'Whole study crop · common-valid mean');assert.equal(f.api.state.layer,'hv');assert.match(f.location.hash,/footprint=1/);
});
test('keyboard inspection follows a fixed native neighborhood and updates the share link',async()=>{
 const f=await fixture();await f.elements.get('map').emit('keydown',{key:'ArrowRight'});await f.elements.get('map').emit('keydown',{key:'Enter'});
 assert.equal(f.api.state.profile.label,'Inspected neighborhood');assert.match(f.location.hash,/point=1200%2C1201/);assert.equal(f.elements.get('footprint').value,'');
});
test('unassessed keyboard cursor is not exported as the selected footprint',async()=>{
 const f=await fixture();await f.elements.get('map').emit('keydown',{key:'ArrowRight'});await f.api.player.seek(1);
 assert.doesNotMatch(f.location.hash,/point=/);assert.match(f.api.state.profile.label,/Previously tracked/);
});
test('direct coherence link opens a supplied pair while an explicit missing date gets a notice',async()=>{
 const f=await fixture('#case=nepal_surface&layer=coherence20');assert.equal(f.api.state.index,5);assert.equal(f.elements.get('map-image').hidden,false);
 const missing=await fixture('#date=2026-08-07T23%3A39%3A18Z');assert.equal(missing.api.state.index,9);assert.match(missing.elements.get('inspection-note').textContent,/requested date is not available/);
});
test('measurement and footprint controls ignore inputs while another case is loading',async()=>{
 const f=await fixture();const release=f.hold('/cases/nepal_impact_corridor/expanded-v1/manifest.json');const pending=f.api.selectCase('nepal_impact_corridor');
 f.elements.get('layer').value='coherence20';await f.elements.get('layer').emit('change');
 f.elements.get('footprint').value='1';await f.elements.get('footprint').emit('change');await f.elements.get('pair').emit('change');
 assert.equal(f.elements.get('export').disabled,true);release();await pending;
 assert.equal(f.api.state.manifest.case_id,'nepal_impact_corridor');assert.equal(f.api.state.layer,'hh');assert.match(f.api.state.profile.label,/mapped impact/);
});
test('map Play traverses ten actual frames, skips the outage and synchronizes both buttons',async()=>{
 const f=await fixture();await f.elements.get('map-play').emit('click');assert.equal(f.api.state.index,0);assert.equal(f.api.player.snapshot().playing,true);assert.equal(f.elements.get('play').textContent,'Ⅱ Pause');
 const dates=[f.api.state.manifest.observations[0].timestamp];for(let n=1;n<10;n++){await f.tick();dates.push(f.api.state.manifest.observations[f.api.state.index].timestamp);}
 assert.equal(dates.length,10);assert.ok(dates[3].startsWith('2026-07-26'));assert.ok(dates[4].startsWith('2026-08-19'));assert.ok(!dates.some(d=>d.startsWith('2026-08-07')));assert.equal(f.elements.get('map-image').hidden,false);
 await f.tick();assert.equal(f.api.player.snapshot().playing,false);assert.equal(f.timers.size,0);
});
test('coherence playback traverses only the two supplied pair frames',async()=>{
 const f=await fixture('#layer=coherence20');await f.elements.get('play').emit('click');assert.equal(f.api.state.index,5);await f.tick();assert.equal(f.api.state.index,6);assert.match(f.elements.get('map-image').src,/gunw_1_coherence20/);await f.tick();assert.equal(f.timers.size,0);
});
test('selected playback range and loop stay within actual frames and Pause cancels the clock',async()=>{
 const f=await fixture();f.elements.get('range-start').value='3';await f.elements.get('range-start').emit('change');f.elements.get('range-end').value='4';await f.elements.get('range-end').emit('change');f.elements.get('loop').checked=true;await f.elements.get('loop').emit('change');
 await f.elements.get('map-play').emit('click');assert.equal(f.api.state.index,3);await f.tick();assert.equal(f.api.state.index,4);await f.tick();assert.equal(f.api.state.index,3);await f.elements.get('play').emit('click');assert.equal(f.api.player.snapshot().playing,false);assert.equal(f.timers.size,0);
});
test('missing saved frame stops playback and reports the problem beside the map',async()=>{
 const f=await fixture();f.failImage(f.api.state.manifest.observations[0].layers.hh);await f.elements.get('map-play').emit('click');assert.equal(f.api.player.snapshot().playing,false);assert.equal(f.timers.size,0);assert.match(f.elements.get('playback-status').textContent,/Playback stopped/);assert.equal(f.elements.get('error').hidden,false);
});
test('stalled frame has a bounded timeout and leaves a retry message instead of an endless spinner',async()=>{
 const f=await fixture();f.stallImage(f.api.state.manifest.observations[0].layers.hh);const playing=f.elements.get('map-play').emit('click');assert.equal(f.api.player.snapshot().loading,true);f.expireLoad();await playing;
 assert.equal(f.api.player.snapshot().playing,false);assert.equal(f.timers.size,0);assert.equal(f.elements.get('map').attributes['aria-busy'],'false');assert.match(f.elements.get('playback-status').textContent,/too long to load/);
});
