// Socket-free execution of the actual packaged controller; no claim of browser rendering.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../output/atlas/TerraPulse.html',import.meta.url),'utf8');
const match=(rx)=>{const m=html.match(rx);assert.ok(m);return m[1];};
const records=match(/<script type="application\/json" id="atlas-data">([\s\S]*?)<\/script>/);
const identity=match(/<script type="application\/json" id="atlas-identity">([\s\S]*?)<\/script>/);
const controller=match(/<script type="module">([\s\S]*?)<\/script>/);
assert.doesNotMatch(html,/<(?:script|link|img)\b[^>]+(?:src|href)="(?:\/|https?:)/i);
class Element{
  constructor(){this.children=[];this.attrs={};this.dataset={};this.style={setProperty(){}};}
  append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
  addEventListener(){} setAttribute(k,v){this.attrs[k]=v;} click(){this.onclick?.();}
}
const ids=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element()]));
ids.get('atlas-data').textContent=records;
ids.get('atlas-identity').textContent=identity;
const chapters=['river','wetland','persist'].map(story=>Object.assign(new Element(),{dataset:{story}}));
const document={body:{dataset:{portable:'yes'}},getElementById:k=>ids.get(k),querySelectorAll:()=>chapters,createElement:()=>new Element(),createElementNS:()=>new Element(),addEventListener(){}};
let hash='',blob=null,tick=null,network=0;
const events={};
const context={document,window:{addEventListener(name,fn){events[name]=fn;}},URLSearchParams,Blob,fetch(){network++;throw Error('Network forbidden');},
  history:{replaceState(a,b,v){hash=v;}},location:{get hash(){return hash;}},clearInterval(){tick=null;},setInterval(fn){tick=fn;return 1;},
  setTimeout(){},URL:{createObjectURL(v){blob=v;return 'blob:inspection';},revokeObjectURL(){}}};
vm.runInNewContext(controller.replace(/^export /gm,''),context);
const get=k=>ids.get('at-'+k);
const catalog=JSON.parse(identity);
const discovery=()=>get('discovery-content').children;
const [selected,reference]=discovery()[2].children;
assert.match(selected.children[1].textContent,/2026-10-17.*12.7 h after radar/);
assert.match(reference.children[1].textContent,/2026-06-20.*24.7 h after radar/);
assert.match(reference.children[3].textContent,/blank near the study center/);
assert.match(discovery()[2].children[2].children[0].textContent,/Previous visit/);
const comparison=new globalThis.URL(discovery()[3].href);
assert.equal(comparison.hostname,'worldview.earthdata.nasa.gov');
assert.equal(comparison.searchParams.get('t'),'2026-10-17');
assert.equal(comparison.searchParams.get('t1'),'2026-10-05');
for(const chapter of chapters){
  chapter.click();assert.equal(get('probe-panel').hidden,true);assert.equal(get('native').hidden,true);
  if(chapter.dataset.story==='river'){
    const candidate=discovery()[2].children[0];
    assert.match(candidate.children[1].textContent,/No candidate at the study center/);
    const search=new globalThis.URL(candidate.children[2].href);
    assert.equal(search.hostname,'cmr.earthdata.nasa.gov');
    assert.equal(search.searchParams.get('collection_concept_id'),'C2949811996-POCLOUD');
    assert.match(search.searchParams.get('temporal'),/^2026-08-27.*2026-08-31/);
  }
  assert.equal(get('table').children.length,10);assert.equal(get('current').src.startsWith('data:image/webp;base64,'),true);
  get('export').click();const p=JSON.parse(await blob.text());assert.equal(p.view,hash);assert.equal(p.history.length,10);assert.equal(p.contract.schemaVersion,1);assert.equal(p.measurementRecords.length,4);
  const expected=catalog[p.case_id].observations;
  assert.deepEqual(p.history.map(o=>[o.observation_id,o.timestamp]),expected.map(o=>[o.id,o.utc]));
  const current=expected.findIndex(o=>o.utc===p.selected_utc);
  assert.equal(p.comparisons.recent.target.id,expected[current-1].id);
  assert.equal(p.comparisons.reference.target.id,catalog[p.case_id].referenceId);
  assert.equal(p.comparisons.recent.support.validPixels,p.common_valid_pixels);
  assert.equal(p.compatibility.rows.length,6);
  assert.equal(p.compatibility.selectedUtc,p.selected_utc);
  assert.equal(p.compatibility.referenceUtc,p.reference_utc);
  assert.equal(p.compatibility.commonValidPixels,p.common_valid_pixels);
  assert.ok(p.compatibility.rows.every(r=>r.evaluated));
  assert.ok(p.compatibility.rows.find(r=>r.id==='moisture_roughness').missing_inputs.includes('rain_72h_mm'));
  if(chapter.dataset.story==='persist')assert.equal(p.measurements.hh_reference.toFixed(2),'-7.08');
  else {
    assert.equal(p.explanations.length,6);assert.ok(p.optical_reference.clear_assessable_pixels>0);
    assert.equal(get('field-review').hidden,false);
    assert.equal(p.field_review.occurrence.valid,10);
    assert.equal(p.field_review.visits.length,10);
    assert.equal(p.field_review.selected.optical.reference_id,p.optical_reference.reference_id);
    assert.equal(p.independent_validation.heldOutLabels,0);
    assert.equal(p.field_review.area.areaAdjustedKm2,null);
    assert.ok(p.field_review.map.selected.startsWith('data:image/webp'));
    if(chapter.dataset.story==='wetland')assert.equal(p.field_review.occurrence.fraction,.2);
    get('date').value=expected[0].utc;get('date').onchange();
    get('export').click();assert.equal(JSON.parse(await blob.text()).field_review.selected.optical,null);
  }
}
const good=hash;
chapters[0].click();
hash=good;events.hashchange();
assert.equal(get('case').value,'nepal_surface');assert.equal(get('date').value.slice(0,10),'2026-09-12');
const invalid=new URLSearchParams(good.slice(1)),view=JSON.parse(invalid.get('view'));view.recordVersion='stale';invalid.set('view',JSON.stringify(view));
hash='#'+invalid;events.hashchange();
assert.match(get('status').textContent,/Link not opened/);assert.equal(get('case').value,'nepal_surface');
hash=good;events.hashchange();
get('play').click();tick();get('play').click();assert.equal(tick,null);
for(const [chapter,caseId] of [[0,'jamuna_river'],[2,'nepal_surface']]){
  chapters[chapter].click();
  const {observations}=catalog[caseId];
  get('date').value=observations[0].utc;get('date').onchange();
  get('play').click();
  for(const observation of observations.slice(1)){tick();assert.equal(get('date').value,observation.utc);}
  tick();assert.equal(tick,null);
}
chapters[2].click();
get('layer').value='coherence';get('layer').onchange();
assert.equal(get('date-label').textContent,'Coherence pair (UTC)');
assert.equal(get('play').textContent,'Play pairs');
assert.equal(get('pairs').hidden,false);
assert.match(discovery()[2].children[1].children[0].textContent,/Pair start/);
get('export').click();
const pair=JSON.parse(await blob.text()).coherence_evidence;
assert.equal(pair.pair.intervalSeconds,12*86400);
assert.equal(pair.deltaFootprint.assessed,53);
assert.ok(pair.comparison.image.startsWith('data:image/webp'));
assert.equal(pair.gates.damageProxy.status,'unavailable');
assert.equal(pair.gates.displacement.status,'no_go');
get('prev').click();get('export').click();
assert.equal(JSON.parse(await blob.text()).coherence_evidence.comparison,undefined);
for(const [index,caseId] of [[0,'jamuna_river'],[1,'tanguar_wetland']]){
  chapters[index].click();
  get('layer').value='coherence';get('layer').onchange();
  get('date').value='2026-10-16T23:21:32Z';get('date').onchange();
  get('export').click();
  const packet=JSON.parse(await blob.text());
  assert.equal(packet.case_id,caseId);
  assert.deepEqual(packet.pair.timestamps,['2026-10-04T23:21:32Z','2026-10-16T23:21:32Z']);
  assert.ok(packet.coherence_evidence.comparison.crop.assessed>0);
  assert.equal(get('pairs').hidden,false);
}
const recordsObj=JSON.parse(records);
for(const c of Object.values(recordsObj)){
  assert.equal(c.terrain.elevation_m.length,c.terrain.size**2);
  assert.ok(c.terrain.elevation_m.some(Number.isFinite));
}
assert.equal(network,0);
console.log('Portable HTML: three guided selections, dated optical matches, field reviews, coherence pairs, exports, playback, embedded terrain and zero network requests passed in socket-free controller rehearsal.');
