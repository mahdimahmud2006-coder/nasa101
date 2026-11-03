import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {calendarForCase,calendarHTML,intervalForVisit,gapRects,canJoinObservations,recordedIntervalLabel} from '../web/time-axis.mjs';
const bundle=JSON.parse(fs.readFileSync(new URL('../web/public/cases/time-axis-v1/calendars.json',import.meta.url)));
const bd=bundle.series.bangladesh_069_014,np=bundle.series.nepal_098_016;
test('one shared Bangladesh calendar has six real visits and eleven nominal slots',()=>{
 const observed=bd.slots.filter(s=>s.status==='observed').map(s=>({timestamp:s.observed_timestamp}));
 assert.equal(calendarForCase(bundle,'jamuna_river',observed),bd);
 assert.equal(calendarForCase(bundle,'tanguar_wetland',observed),bd);
 assert.equal(calendarForCase(bundle,'nepal_surface',observed),null);
 assert.equal(calendarForCase(bundle,'jamuna_river',observed.slice(1)),null);
});
test('calendar presents recorded visits only and keeps full coverage inside methods',()=>{
 const before=JSON.stringify(bd),html=calendarHTML(bd,2),visible=html.split('<details class="calendar-provenance">')[0];
 assert.match(visible,/6 recorded visits/);assert.equal((visible.match(/class="nominal-slot observed"/g)||[]).length,6);
 assert.doesNotMatch(visible,/05 Aug|instrument-gap-shade|Satellite outage|nominal slots|calendar-gap-summary/);
 assert.match(visible,/24 days between recorded visits/);assert.equal((visible.match(/aria-current="date"/g)||[]).length,1);
 assert.match(html,/Satellite outage · no acquisition/);assert.match(html,/Observation methods & acquisition coverage/);
 assert.match(calendarHTML(np,0),/No compatible archive result/);assert.match(calendarHTML(null,0),/Recorded dates/);
 assert.equal(JSON.stringify(bd),before,'Presentation must not mutate the scientific calendar');
});
test('download actions and outage provenance remain available under collapsed methods',()=>{
 const plan=JSON.parse(fs.readFileSync(new URL('../web/public/cases/bangladesh-missing-gcov-v1.json',import.meta.url)));
 const html=calendarHTML(bd,5,plan),[visible,methods]=html.split('<details class="calendar-provenance">');
 assert.doesNotMatch(visible,/NASA GCOV|05 Aug|outage|not loaded/);assert.match(methods,/permanent satellite outage/);
 assert.match(methods,/25.05 GiB/);assert.equal((methods.match(/NASA GCOV ↓/g)||[]).length,4);
 assert.doesNotMatch(html,/<li class="nominal-slot instrument_gap"/);assert.match(methods,/GUNW coherence files do not replace GCOV/);
 assert.doesNotMatch(calendarHTML(np,1,plan),/NASA GCOV ↓/);
 assert.equal(recordedIntervalLabel(intervalForVisit(bd,2)),'24 days between recorded visits');
});
test('chart connectors require an observed repeat interval without outage or unloaded slots',()=>{
 assert.equal(canJoinObservations(bd,bd.intervals[0].start,bd.intervals[0].end),false);
 assert.equal(canJoinObservations(bd,bd.intervals[1].start,bd.intervals[1].end),false);
 assert.equal(canJoinObservations(bd,bd.intervals[2].start,bd.intervals[2].end),true);
 assert.equal(canJoinObservations(null,'2026-06-18T00:00:00Z','2026-07-24T00:00:00Z'),false);
 assert.equal(canJoinObservations(null,'2026-08-17T00:00:00Z','2026-08-29T00:00:00Z'),true);
});
test('first date has no comparison and long endpoint intervals stay flagged',()=>{
 assert.equal(intervalForVisit(bd,0),null);
 assert.equal(intervalForVisit(bd,2).spans_instrument_gap,true);
 assert.equal(intervalForVisit(bd,3).flagged,false);
 assert.equal(intervalForVisit(bd,4).longer_than_repeat,true);
});
test('gap shading clips to plotted extent and never adds fake observations',()=>{
 const start=Date.parse('2026-08-01T00:00:00Z'),end=Date.parse('2026-08-17T00:00:00Z');
 assert.match(gapRects(bd,start,end,40,500,10,100),/x="40"/);
 assert.equal(gapRects(np,Date.parse('2026-08-19'),Date.parse('2026-09-12'),40,500,10,100),'');
 assert.equal(gapRects(null,start,end,40,500,10,100),'');
});
