import test from 'node:test';
import assert from 'node:assert/strict';
import {navigationContext,investigationContext,casesForFocus,focusCopy} from '../web/navigation-model.mjs';
import fs from 'node:fs/promises';
const registry=JSON.parse(await fs.readFile(new URL('../web/public/cases/investigations.json',import.meta.url)));
test('country navigation gives Bangladesh three purposes and Nepal its own tools',()=>{
 const bd=navigationContext('/investigations.html','?country=bangladesh&mode=surface');
 assert.equal(bd.group,'bangladesh');assert.equal(bd.links.length,3);assert.equal(bd.links.filter(l=>l.active)[0].label,'Surface change');
 const np=navigationContext('/expanded.html','','#case=nepal_surface');assert.equal(np.group,'nepal');assert.equal(np.links.length,6);assert.equal(np.links.find(l=>l.active).label,'Surface & coherence');
 assert.ok(np.links.some(l=>l.href==='/studio.html#case=nepal_surface&mode=surface'));
});
test('Bangladesh surface focus reuses only the two accepted Bangladesh cases',()=>{
 assert.deepEqual(casesForFocus(registry.cases,'surface','bangladesh').map(c=>c.case_id),['jamuna_river','tanguar_wetland']);
 assert.deepEqual(casesForFocus(registry.cases,'surface','nepal').map(c=>c.case_id),['nepal_surface','nepal_impact_corridor']);
 assert.equal(casesForFocus(registry.cases,'river','nepal')[0].case_id,'jamuna_river');
});
test('shared case geography overrides incompatible query geography',()=>{
 assert.deepEqual(investigationContext('?country=nepal&mode=surface',{case:'tanguar_wetland',mode:'surface'}),{country:'bangladesh',mode:'surface'});
 assert.equal(navigationContext('/investigations.html','?country=bangladesh','#case=nepal_surface&mode=surface').group,'nepal');
 assert.equal(focusCopy('bangladesh','surface').eyebrow,'BANGLADESH / JAMUNA & TANGUAR');
});
test('home and field guide have no misleading Nepal-only secondary tools',()=>{
 for(const path of ['/','/index.html','/guide.html'])assert.equal(navigationContext(path).links.length,0);
});
test('cross-country links do not carry an incompatible footprint or date',()=>{
 const np=navigationContext('/studio.html','','#case=tanguar_wetland&date=2026-10-16&footprint=point:15,20');
 assert.ok(np.links.every(l=>!l.href.includes('point:')&&!l.href.includes('2026-10-16')));
 const n=navigationContext('/timeseries.html','','#case=nepal_surface&date=2026-08-31&footprint=saved:0');
 assert.match(n.links.find(l=>l.label==='Evidence dossiers').href,/date=2026-08-31/);
});
