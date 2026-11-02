/** Controller tests use explicit DOM/canvas/image mocks, not a browser or visual QA. */
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs/promises';
import {createPlayback} from '../web/playback.mjs';
import * as model from '../web/investigation-model.mjs';
const root=new URL('../',import.meta.url);
async function fixture({pendingHydrology=false,search=''}={}){
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
 const fetched=[];
 async function fetch(url){fetched.push(url);let path=url==='/api/investigations'?'/cases/investigations.json':url;if(url.includes('/investigation-probe?')){
  const manifest=JSON.parse(await fs.readFile(new URL('web/public/cases/nepal_surface/investigation/manifest.json',root),'utf8'));return {ok:true,json:async()=>({...manifest.profiles[0],label:'Clicked neighborhood',center_row:1,center_col:1})};
 }assert.ok(path.startsWith('/cases/'),'Unexpected fetch '+path);const data=JSON.parse(await fs.readFile(new URL('web/public'+path,root),'utf8'));if(pendingHydrology&&url==='/api/investigations')for(const row of data.cases)if(['river','wetland'].includes(row.module))Object.assign(row,{status:'AWAITING_DATA',local_source_count:0,minimum_observations:3});return {ok:true,json:async()=>data};}
 class ImageMock{set src(url){this.url=url;queueMicrotask(()=>this.onload());}}
 const timers=new Map();let timer=0;
 const sandbox={...model,createPlayback:options=>createPlayback({...options,setTimer:fn=>{timers.set(++timer,fn);return timer;},clearTimer:id=>timers.delete(id)}),console,document,window:{location:{search},addEventListener(){}},fetch,Image:ImageMock,URL,URLSearchParams,Blob,setTimeout:()=>1};
 const api=await vm.runInNewContext('(async()=>{'+source+'\nreturn {state,get player(){return player}};})()',sandbox);
 assert.equal(elements.get('investigation-error').hidden,true,elements.get('investigation-error').textContent);
 const until=async predicate=>{const deadline=Date.now()+2000;while(!predicate()&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,2));assert.ok(predicate(),elements.get('investigation-error').textContent||'Controller transition did not complete');};
 return {api,elements,document,fetched,until};
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
