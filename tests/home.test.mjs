/** DOM doubles verify controls and source bindings; these are not rendered browser tests. */
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs/promises';
const root=new URL('../',import.meta.url);
async function home(hash=''){
 const html=await fs.readFile(new URL('web/index.html',root),'utf8');
 const elements=new Map();
 class Element{
  constructor(){this.attrs={};this.listeners={};this.hidden=false;this.value='50';this.props={};this.style={setProperty:(k,v)=>this.props[k]=v};}
  setAttribute(k,v){this.attrs[k]=v;}addEventListener(k,fn){this.listeners[k]=fn;}focus(){this.focused=true;}scrollIntoView(){this.scrolled=true;}
  emit(k,event={}){return this.listeners[k]?.(event);}
 }
 for(const [,id]of html.matchAll(/id="([^"]+)"/g))elements.set(id,new Element());
 const records=['jamuna_river','tanguar_wetland'].map(id=>Object.assign(new Element(),{dataset:{record:id}}));
 const location={hash,replace(v){this.redirect=v;}},history={replaceState(a,b,v){location.hash=v;}},events={};
 const document={getElementById:id=>elements.get(id),querySelectorAll:()=>records};
 const source=(await fs.readFile(new URL('web/home.mjs',root),'utf8')).replace(/^export /gm,'');
 const fetch=async url=>({ok:true,json:async()=>JSON.parse(await fs.readFile(new URL('web/public'+(url==='/api/investigations'?'/cases/'+JSON.parse(await fs.readFile(new URL('config.records.json',root),'utf8')).investigation_registry:url),root),'utf8'))});
 await vm.runInNewContext('(async()=>{'+source+'})()',{document,location,history,window:{addEventListener:(k,v)=>events[k]=v},URLSearchParams,fetch,console});
 return {elements,location,records,events};
}
test('overview selects the requested country and loads measured record counts',async()=>{
 const h=await home('#nepal');assert.equal(h.elements.get('tab-nepal').attrs['aria-selected'],'true');assert.equal(h.elements.get('panel-bangladesh').hidden,true);
 assert.match(h.records[0].textContent,/10 observed visits/);assert.match(h.elements.get('nepal-record-summary').textContent,/10 observed visits · 2 measured coherence pairs/);
});
test('country tabs support keyboard selection, focus and shareable country links',async()=>{
 const h=await home();let prevented=false;
 h.elements.get('tab-bangladesh').emit('keydown',{key:'ArrowRight',preventDefault(){prevented=true;}});
 assert.ok(prevented);assert.equal(h.location.hash,'#nepal');assert.equal(h.elements.get('tab-nepal').focused,true);assert.equal(h.elements.get('panel-nepal').hidden,false);
 h.elements.get('tab-bangladesh').emit('click');assert.equal(h.location.hash,'#bangladesh');assert.equal(h.elements.get('tab-nepal').tabIndex,-1);
});
test('radar comparison controls only the wipe position and exposes failed image loading',async()=>{
 const h=await home();h.elements.get('hero-split').value='72';h.elements.get('hero-split').emit('input');assert.equal(h.elements.get('observation-wipe').props['--split'],'72%');
 h.elements.get('hero-after').emit('error');assert.equal(h.elements.get('hero-image-status').hidden,false);
});
test('previous root studio links retain their selected observation',async()=>{
 const hash='#case=nepal_surface&date=2026-08-31&overlay=thermal';const h=await home(hash);assert.equal(h.location.redirect,'/studio.html'+hash);
});
