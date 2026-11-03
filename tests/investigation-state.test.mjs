import test from 'node:test';import assert from 'node:assert/strict';
import {readView,viewHash,workspaceHref,legacyChoice,writeView} from '../web/investigation-state.mjs';
test('shared state round trips only supported fields',()=>{
 const v={case:'jamuna_river',date:'2026-08-29T23:21:32Z',mode:'river',overlay:'hh_baseline',footprint:'polygon:[[1,1],[5,1],[5,5]]'};
 assert.deepEqual(readView(viewHash(v)),v);assert.deepEqual(readView('#case=evil&date=tomorrow&overlay=javascript:alert(1)&mode=other'),{});
});
test('legacy navigation explicitly scopes tools to Nepal without carrying Bangladesh dates',()=>{
 const url=workspaceHref('/timeseries.html',{case:'jamuna_river',mode:'river',date:'2026-06-18',footprint:'saved:4'});
 const v=readView(url.split('#')[1]);assert.equal(v.case,'nepal_surface');assert.equal(v.date,undefined);assert.equal(v.footprint,undefined);
});
test('missing and incompatible legacy dates select a real observation with a notice',()=>{
 const observations=[{timestamp:'2026-08-19T00:00:00Z'},{timestamp:'2026-08-31T00:00:00Z'}];
 assert.equal(legacyChoice({date:'2026-08-19'},observations).index,0);
 assert.match(legacyChoice({date:'2026-08-25'},observations).note,/not loaded/);
 assert.match(legacyChoice({case:'tanguar_wetland'},observations).note,/Nepal · Kathmandu/);
});
test('state updates replace history without triggering a page navigation',()=>{
 const calls=[],win={location:{hash:''},history:{replaceState(...a){calls.push(a);}},dispatchEvent(){}};
 writeView({case:'nepal_surface',date:'2026-08-19'},win);assert.equal(calls.length,1);assert.match(calls[0][2],/#case=nepal_surface/);
});
