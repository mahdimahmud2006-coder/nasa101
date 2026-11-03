/** Honest nominal calendars: no synthesized measurements and no network dependencies. */
const escape=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=v=>new Date(v).toLocaleDateString('en-GB',{day:'2-digit',month:'short',timeZone:'UTC'});
const labels={observed:'Observed',instrument_gap:'Satellite outage · no acquisition',not_in_hand:'GCOV not loaded in this record',unavailable_in_archive:'No compatible archive result'};
export function calendarForCase(bundle,id,observations){
 const calendar=Object.values(bundle?.series||{}).find(c=>c.case_ids.includes(id));
 if(!calendar)return null;
 const loaded=calendar.slots.filter(s=>s.status==='observed');
 if(loaded.length!==observations.length||loaded.some((s,i)=>new Date(s.observed_timestamp).getTime()!==new Date(observations[i].timestamp).getTime()))return null;
 return calendar;
}
export function intervalForVisit(calendar,index){return index>0?calendar?.intervals[index-1]||null:null;}
export function canJoinObservations(calendar,from,to){
 const a=Date.parse(from),b=Date.parse(to);if(!Number.isFinite(a)||!Number.isFinite(b)||b<=a)return false;
 if((calendar?.instrument_gaps||[]).some(g=>a<Date.parse(g.end)&&b>Date.parse(g.start)))return false;
 const interval=calendar?.intervals.find(i=>Date.parse(i.start)===a&&Date.parse(i.end)===b);
 if(interval?.flagged)return false;
 return b-a<=(calendar?.repeat_days||12)*86400000+120000;
}
export function gapRects(calendar,start,end,left,width,top,height){
 if(!calendar||end<=start)return '';
 return calendar.instrument_gaps.map(g=>{
  const a=Math.max(start,new Date(g.start).getTime()),b=Math.min(end,new Date(g.end).getTime());
  if(b<=a)return '';
  return `<rect class="instrument-gap-shade" x="${left+(a-start)/(end-start)*width}" y="${top}" width="${(b-a)/(end-start)*width}" height="${height}"><title>Permanent satellite data gap: ${escape(g.start)} to ${escape(g.end)}. No NISAR acquisition can be downloaded inside this interval.</title></rect>`;
 }).join('');
}
/** Concise presentation label; full interval flags remain in calendar exports. */
export function recordedIntervalLabel(interval){
 if(!interval)return null;
 const days=interval.elapsed_days??(Date.parse(interval.end)-Date.parse(interval.start))/86400000;
 return `${Math.round(days)} days between recorded visits`;
}
export function calendarHTML(calendar,index,downloadPlan=null){
 if(!calendar)return '<p class="note">Recorded dates are listed with the observation playback.</p>';
 const observed=calendar.slots.filter(s=>s.status==='observed');
 if(!observed.length)return '<p class="note">No recorded acquisitions in this calendar.</p>';
 const first=Date.parse(observed[0].observed_timestamp),last=Date.parse(observed.at(-1).observed_timestamp);
 const width=1000,left=32,plot=width-64,x=s=>left+(Date.parse(s.observed_timestamp)-first)/Math.max(1,last-first)*plot;
 const interval=intervalForVisit(calendar,index),missing=calendar.slots.filter(s=>s.status==='not_in_hand'),outages=calendar.slots.filter(s=>s.status==='instrument_gap');
 const plan=missing.length&&downloadPlan?.series_id===calendar.series_id?downloadPlan:null;
 const symbols=observed.map(s=>`<g><circle cx="${x(s)}" cy="32" r="${s.observation_index===index?8:5}" class="slot-dot observed"/><text x="${x(s)}" y="65" text-anchor="middle">${escape(date(s.observed_timestamp))}</text><title>${escape(s.observed_timestamp)}</title></g>`).join('');
 const cards=observed.map(s=>`<li class="nominal-slot observed"${s.observation_index===index?' aria-current="date"':''}><strong>${escape(date(s.observed_timestamp))}</strong><span>Observed</span><small>Acquired ${escape(s.observed_timestamp.slice(11,19))} UTC</small></li>`).join('');
 const availability=calendar.slots.filter(s=>s.status!=='observed').map(s=>`<li>${escape(date(s.nominal_timestamp))}: ${escape(labels[s.status])}.</li>`).join('');
 const downloads=plan?`<p>Remaining shared GCOV download: ${Number(plan.total_gib).toFixed(2)} GiB. These four shared Bangladesh intensity files serve River Memory and Wetland Pulse. GUNW coherence files do not replace GCOV intensity visits.</p><ul>${plan.downloads.map(d=>`<li><a href="${escape(d.url)}" target="_blank" rel="noreferrer">NASA GCOV ↓ · ${escape(date(d.timestamp))} · ${Number(d.size_gib).toFixed(2)} GiB</a></li>`).join('')}</ul>`:'';
 return `<div class="time-axis-heading"><h3>Observation record <small>Recorded acquisitions · UTC</small></h3><span>${observed.length} recorded visits</span></div>
 <div class="slot-scroll"><svg class="slot-axis" viewBox="0 0 1000 78" role="img" aria-label="Recorded acquisition dates on an elapsed-time axis"><line x1="${left}" x2="${width-left}" y1="32" y2="32" class="slot-axis-line"/>${symbols}</svg></div>
 <ul class="nominal-slots recorded-visits">${cards}</ul>
 <p class="interval-note" role="status">${interval?escape(recordedIntervalLabel(interval))+'.':'First recorded visit.'}</p>
 <details class="calendar-provenance"><summary>Observation methods & acquisition coverage</summary><p>The timeline and playback show recorded acquisitions only. Horizontal spacing uses actual elapsed time. Comparisons use the two observed endpoints; surface behavior between them is unresolved. No omitted date is treated as a zero measurement.</p>${availability?`<p>Nominal acquisition coverage:</p><ul>${availability}</ul>`:''}${outages.length?'<p>A nominal visit inside the documented permanent satellite outage has no NISAR acquisition; additional GCOV or GUNW downloads cannot recover it.</p>':''}${calendar.instrument_gaps.map(g=>`<p><a href="${escape(g.source_url)}" target="_blank" rel="noreferrer">NASA / ASF acquisition notice ↗</a>: ${escape(g.start)} → ${escape(g.end)}.</p>`).join('')}${downloads}<p>Archive search: ${calendar.search_complete?'complete':'incomplete'} · ${escape(calendar.queries[0]?.retrieved_at||'unknown')}. Archive absence describes the recorded bounded query.</p><a href="${escape(calendar.metadata_url||'/cases/time-axis-v1/'+calendar.series_id+'.json')}" download>Full acquisition calendar & provenance ↓</a></details>`;
}
