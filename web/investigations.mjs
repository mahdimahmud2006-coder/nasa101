import {countryForCase,casesForFocus,investigationContext,focusCopy} from '/navigation-model.mjs';
import {reasoningHTML,claimsHTML,referenceForSelection,referenceHTML,interferometryHTML} from '/reasoning.mjs';
import {readView,writeView} from '/investigation-state.mjs';
import {contextLayers,contextLegend,contextHTML} from '/context-v2.mjs';
import {dualpolLayers,isDualpolLayer,canCompareDualpol,extensionMatches,cprProfile,cprChart,sensitivityHTML,dualpolLegend,dualpolDossier} from '/dualpol.mjs';
import {calendarForCase,calendarHTML,intervalForVisit,recordedIntervalLabel,canJoinObservations} from '/time-axis.mjs';
import {createPlayback} from '/playback.mjs';
import {availableLayers,safeLayer,canCompare,pixelFromPointer,finding,dossier} from '/investigation-model.mjs';
const $=id=>document.getElementById(id);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=2)=>v===null||v===undefined?'Unavailable':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const day=value=>new Date(value).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
const state={registry:null,plan:null,calendars:null,calendar:null,dualpol:null,sensitivity:null,contextV2:null,evidence:null,selectedEvidence:null,references:null,interferometry:null,claims:null,drawing:false,polygon:[],country:'nepal',mode:'surface',case:null,data:null,index:0,layer:'hh',profile:null,profileIndex:0,marker:null,epoch:0,mapEpoch:0,probeEpoch:0};
let player=null,currentImage=null,firstImage=null;
let restoringView=true,sharedFootprint='saved:0';
const initialView=readView(window.location?.hash||'');
function persistView(){if(!restoringView&&state.data)writeView({case:state.data.case_id,date:state.data.observations[state.index].timestamp,footprint:sharedFootprint,mode:state.mode,overlay:state.layer});}
async function restoreView(view){
 restoringView=true;
 try{
  const row=state.registry.cases.find(c=>c.case_id===view.case);
  if(row){const country=countryForCase(row.case_id),mode=view.mode==='surface'?'surface':row.module;if(state.country!==country||state.mode!==mode||state.data?.case_id!==row.case_id){await selectMode(mode,country,row.case_id);}}
  if(!state.data)return;
  let note='Choose a view, play the observed visits, then inspect a footprint on the map.';
  let index=state.index;
  if(view.date){const found=state.data.observations.findIndex(o=>o.timestamp===view.date||o.timestamp.slice(0,10)===view.date);if(found>=0)index=found;else note='Requested date is not loaded in this case. Showing an explicitly available observation.';}
  if(view.overlay){if(layersForVisit(index).includes(view.overlay))state.layer=view.overlay;else note+=' Requested legacy layer is not available in this workspace; an available radar view is shown.';}
  const f=view.footprint||'saved:0';
  if(/^saved:\d+$/.test(f)){const i=Number(f.slice(6));if(state.evidence?.profiles[i]){state.profile=state.data.profiles[i];state.selectedEvidence=state.evidence.profiles[i];$('profile-select').value=String(i);sharedFootprint=f;state.polygon=state.profile.geometry_pixel?.coordinates?.[0]?.slice(0,-1)||[];}}
  else if(f==='zone:NP-Z4ab9a6118de9'){sharedFootprint='saved:0';state.profile=state.data.profiles[0];state.selectedEvidence=state.evidence?.profiles[0]||null;}
  else if(f.startsWith('point:')){const [row,col]=f.slice(6).split(',').map(Number);await inspect({row,col});}
  else if(f.startsWith('polygon:')){
   const vertices=JSON.parse(f.slice(8));const r=await fetch('/api/cases/'+state.data.case_id+'/investigation-polygon',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vertices})});
   if(!r.ok)throw new Error('Shared polygon cannot be assessed in this case.');const result=await r.json();state.profile=result.profile;state.selectedEvidence=result;state.polygon=vertices;sharedFootprint=f;$('profile-select').value='';
  }
  if(view.footprint&&!/^(saved:|point:|polygon:)/.test(view.footprint)&&view.footprint!=='zone:NP-Z4ab9a6118de9')note+=' Requested legacy footprint is not reproduced here; use its original workspace export. The saved investigation footprint is shown.';
  await player.seek(index);$('shared-view-note').textContent=note;
 }catch(error){$('shared-view-note').textContent=error.message;}
 finally{restoringView=false;persistView();}
}
const cache=new Map();
const canCompareView=layer=>canCompare(layer)||canCompareDualpol(layer);
const layersForVisit=index=>[...availableLayers(state.data.module,index),...dualpolLayers(state.dualpol,index),...contextLayers(state.contextV2)];
async function json(url){const r=await fetch(url);if(!r.ok)throw new Error('Evidence could not be loaded ('+r.status+'). Check the local server and reload this workspace.');return r.json();}
function fail(error){player?.pause();$('investigation-error').hidden=false;$('investigation-error').textContent=error.message||String(error);$('map-loading').hidden=true;}
function image(url){if(!cache.has(url))cache.set(url,new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>{cache.delete(url);reject(new Error('Missing saved map asset: '+url));};img.src=url;}));return cache.get(url);}
function download(name,content,type='text/plain'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function canvasDraw(){
 if(!currentImage||!state.data)return;
 const canvas=$('investigation-map'),ctx=canvas.getContext('2d'),[height,width]=state.data.grid.shape;
 canvas.width=1100;canvas.height=Math.round(1100*height/width);const w=canvas.width,h=canvas.height;
 ctx.clearRect(0,0,w,h);if(state.layer.startsWith('context_')&&state.contextV2){const g=state.contextV2.grid,iw=currentImage.width||g.shape[1],ih=currentImage.height||g.shape[0];ctx.drawImage(currentImage,0,0,iw*width*10/(g.shape[1]*30),ih*height*10/(g.shape[0]*30),0,0,w,h);}else ctx.drawImage(currentImage,0,0,w,h);
 if($('compare').checked&&canCompareView(state.layer)&&firstImage){const split=Number($('split').value)/100*w;ctx.save();ctx.beginPath();ctx.rect(0,0,split,h);ctx.clip();ctx.drawImage(firstImage,0,0,w,h);ctx.restore();ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(split,0);ctx.lineTo(split,h);ctx.stroke();}
 if(state.data.reference&&$('reference').checked){
  const geom=state.data.reference.geometry_pixel,polygons=geom.type==='Polygon'?[geom.coordinates]:geom.coordinates;
  ctx.save();ctx.strokeStyle='#e9ff94';ctx.lineWidth=2;ctx.fillStyle='#e9ff9425';
  for(const polygon of polygons){ctx.beginPath();for(const ring of polygon){ring.forEach(([x,y],i)=>i?ctx.lineTo(x/width*w,y/height*h):ctx.moveTo(x/width*w,y/height*h));ctx.closePath();}ctx.fill('evenodd');ctx.stroke();}ctx.restore();
 }
 if(state.polygon.length){ctx.save();ctx.strokeStyle='#f4d590';ctx.lineWidth=3;ctx.beginPath();state.polygon.forEach(([col,row],i)=>i?ctx.lineTo(col/width*w,row/height*h):ctx.moveTo(col/width*w,row/height*h));if(!state.drawing)ctx.closePath();ctx.stroke();ctx.restore();}
 if(state.marker){const x=(state.marker.col+.5)/width*w,y=(state.marker.row+.5)/height*h;ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.moveTo(x-18,y);ctx.lineTo(x+18,y);ctx.moveTo(x,y-18);ctx.lineTo(x,y+18);ctx.stroke();}
}
function legend(){
 if(state.contextV2&&state.layer.startsWith('context_')){const item=contextLegend(state.contextV2,state.layer);$('legend-title').textContent=item.title;$('legend-low').textContent=item.low;$('legend-high').textContent=item.high;$('legend-note').textContent=item.note;$('legend-ramp').className='ramp';$('legend-ramp').setAttribute('style','background:'+item.ramp);return;}
 if(state.dualpol&&isDualpolLayer(state.layer)){const item=dualpolLegend(state.dualpol,state.layer);$('legend-title').textContent=item.title;$('legend-low').textContent=item.low;$('legend-high').textContent=item.high;$('legend-note').textContent=item.note;$('legend-ramp').className='ramp'+(state.layer==='composite'?' composite':'');if(item.ramp)$('legend-ramp').setAttribute('style','background:'+item.ramp);else $('legend-ramp').removeAttribute('style');return;}
 $('legend-ramp').removeAttribute('style');
 const data=state.data,layer=state.layer,limits=data.display_limits[layer];
 const definitions={hh:['HH gamma-0 backscatter · dB',fmt(limits?.[0],1),fmt(limits?.[1],1),'Shared HH contrast across observed dates; filtered log-power.'],hv:['HV gamma-0 backscatter · dB',fmt(limits?.[0],1),fmt(limits?.[1],1),'Shared HV contrast across observed dates; distinct from HH contrast.'],ratio:['HH − HV · dB ratio','0 dB','20 dB','Difference of filtered log-power channels. Not a vegetation, moisture or biomass estimate.'],baseline:['HH difference from first observation · dB','−8 dB · decrease','+8 dB · increase','Shared display range; values outside it saturate. Baseline-common valid pixels only.'],successive:['HH difference since preceding observation · dB','−8 dB · decrease','+8 dB · increase','Shared display range; missing comparisons remain unavailable.'],river:['Dark-signature change from first observation','Blue: retained · Cyan: gained','Amber: lost','Baseline-common pixels; these are radar signatures, not confirmed bank migration.'],wetland:['Exploratory wetland radar signatures','Cyan: dark candidate','Purple: paired brightening','Dark and bright responses have multiple physical explanations; no habitat class is inferred.'],water:['Radar-dark candidates','Background: other paired-valid','Cyan: below both thresholds','Illustrative HH/HV cutoffs; smooth dry surfaces can also be dark.'],occupancy:['Fraction of observed valid visits with dark signature','0% of valid visits','100% of valid visits','At least two paired-valid visits. Visit frequency is not inundation duration. This layer summarizes the full series.']};
 const item=definitions[layer];$('legend-title').textContent=item[0];$('legend-low').textContent=item[1];$('legend-high').textContent=item[2];$('legend-note').textContent=item[3];$('legend-ramp').className='ramp '+(['baseline','successive'].includes(layer)?'delta':['river','wetland'].includes(layer)?layer:'');
}
function renderDualpol(){
 const extension=state.dualpol;$('dualpol-ready').hidden=!extension;$('dualpol-hints-panel').hidden=!extension;
 $('dualpol-status').textContent=extension?'Measured from the existing canonical HH/HV inputs · fixed display limits across all four cases.':'Dual-polarization products unavailable or out of date. The saved radar investigations remain available.';
 if(!extension)return;
 const profile=cprProfile(state.profile),row=profile?.observations[state.index];
 $('measure-cpr').textContent=Number.isFinite(row?.cpr_mean_db)?fmt(row.cpr_mean_db)+' dB':'Unavailable';
 $('measure-cpr-delta').textContent=Number.isFinite(row?.cpr_baseline_delta_db)?fmt(row.cpr_baseline_delta_db)+' dB':'Unavailable';
 $('cpr-profile-chart').innerHTML=cprChart(state.profile,state.index,state.calendar);
 $('sensitivity-chart').innerHTML=sensitivityHTML(state.sensitivity,state.index,$('sensitivity-mode').value);
 const obs=extension.observations[state.index];
 $('dualpol-hints').innerHTML=Object.entries(extension.hint_definitions).map(([key,text])=>{const value=obs.hint_statistics[key];return `<article class="dualpol-hint"><strong>${esc(key==='hint_low'?'Low-return candidate':key==='hint_hh'?'HH-rise / stable-HV candidate':'HV-rise candidate')}</strong><p>${esc(text)}</p><p>${value?fmt(value.candidate_area_km2)+' km² / '+fmt(value.assessable_area_km2)+' km² assessable':'Unavailable at first visit: baseline change is not assessed.'}</p></article>`;}).join('');
 $('dualpol-method').textContent=extension.formulas.cpr+' '+extension.formulas.composite+' Hints are uncalibrated candidates; full native values are not clipped by display stretches.';
 const base=(state.case.record_base||'/cases/'+state.data.case_id)+'/dualpol-v1/';$('dualpol-manifest').href=base+'manifest.json';$('sensitivity-download').href=base+'sensitivity.json';
}
function renderProfile(){
 if(state.data&&state.profile){const row=state.profile.observations[state.index];$('map-summary').textContent=state.data.title+' · '+state.data.observations[state.index].timestamp+' · '+state.layer+' · '+state.profile.label+'. HH baseline '+(Number.isFinite(row?.hh_baseline_delta_db)?fmt(row.hh_baseline_delta_db)+' dB':'unavailable')+'; HV baseline '+(Number.isFinite(row?.hv_baseline_delta_db)?fmt(row.hv_baseline_delta_db)+' dB':'unavailable')+'. Causes remain unresolved.';}persistView();
 renderDualpol();$('reasoning-detail').innerHTML=reasoningHTML(state.selectedEvidence,state.index);$('interferometry-detail').innerHTML=interferometryHTML(state.interferometry,state.data.case_id);$('matched-reference-detail').innerHTML=referenceHTML(state.references,state.selectedEvidence,state.data.observations[state.index].observation_id);$('context-v2-detail').innerHTML=contextHTML(state.contextV2,state.index);
 const p=state.profile,obs=state.data.observations[state.index],row=p?.observations[state.index];
 $('profile-title').textContent=p?.label||'Select a footprint on the map.';
 $('profile-status').textContent=p?`${p.status==='MEASURED'?'Measured':'Insufficient common data'} · ${p.selection}`:'No selected-region interpretation is generated until a footprint is available.';
 $('measure-hh').textContent=row?.hh_baseline_delta_db===null||!row?'Unavailable':fmt(row.hh_baseline_delta_db)+' dB';
 $('measure-hv').textContent=row?.hv_baseline_delta_db===null||!row?'Unavailable':fmt(row.hv_baseline_delta_db)+' dB';
 $('measure-successive').textContent=row?.hh_successive_delta_db===null||!row?'Unavailable':fmt(row.hh_successive_delta_db)+' dB';
 $('successive-note').textContent=recordedIntervalLabel(intervalForVisit(state.calendar,state.index))||(state.index?'signed HH difference since prior visit':'no previous visit at baseline');
 $('measure-area').textContent=p?fmt(p.measured_area_km2*100,2)+' ha':'—';$('measure-common').textContent=p?fmt(p.common_valid_fraction*100,1)+'% of fixed footprint':'fixed across channels and visits';
 $('measurement-conclusion').textContent=finding(p,state.index,state.data.thresholds.baseline_disturbance_db);
 $('export-dossier').disabled=!p;
 const data=p?.observations||[],valid=data.flatMap(r=>[r.hh_baseline_delta_db,r.hv_baseline_delta_db]).filter(v=>v!==null);
 if(!valid.length){$('profile-chart').textContent='Select a map neighborhood or saved footprint with enough common-valid pixels to inspect its paired trace.';$('profile-footnote').textContent='Unavailable measurements are not plotted as zero.';return;}
 const w=760,h=245,left=65,right=25,top=20,bottom=52,min=Math.min(0,...valid)-.8,max=Math.max(0,...valid)+.8;
 const start=new Date(data[0].timestamp).getTime(),span=Math.max(1,new Date(data.at(-1).timestamp)-start);
 const x=r=>left+(new Date(r.timestamp)-start)/span*(w-left-right),y=v=>top+(max-v)/(max-min)*(h-top-bottom);
 let marks=`<line class="axis" x1="${left}" x2="${w-right}" y1="${y(0)}" y2="${y(0)}"/><text x="8" y="18">Δ dB</text>`;
 for(const v of [min,0,max])marks+=`<text x="9" y="${y(v)+5}">${fmt(v,1)}</text>`;
 for(const pol of ['hh','hv']){
  const key=pol+'_baseline_delta_db';
  for(let i=1;i<data.length;i++)if(data[i-1][key]!==null&&data[i][key]!==null&&canJoinObservations(state.calendar,data[i-1].timestamp,data[i].timestamp))marks+=`<path class="${pol}-line" d="M${x(data[i-1])},${y(data[i-1][key])}L${x(data[i])},${y(data[i][key])}"/>`;
  marks+=data.filter(r=>r[key]!==null).map(r=>`<circle cx="${x(r)}" cy="${y(r[key])}" r="${r.observation_id===obs.observation_id?6:4}" fill="${pol==='hh'?'#75e3d2':'#ffd091'}"><title>${esc(day(r.timestamp))}: ${fmt(r[key])} dB ${pol.toUpperCase()}</title></circle>`).join('');
 }
 for(const i of [...new Set([0,Math.floor(data.length/2),data.length-1])])marks+=`<text x="${x(data[i])}" y="${h-15}" text-anchor="middle">${esc(day(data[i].timestamp).replace(' 2026',''))}</text>`;
 $('profile-chart').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="HH and HV signed baseline backscatter differences on the same common-valid footprint; dots are actual acquisition dates">${marks}</svg>`;
 $('profile-footnote').textContent=`${data.length} actual observations · ${p.common_valid_pixels} common native pixels · time axis uses elapsed days. Points show recorded visits; line segments connect supported comparisons. No daily values are estimated.`;
}
function renderResponse(){
 const data=state.data,obs=data.observations[state.index],r=obs.response;$('response-panel').hidden=!r;if(!r)return;
 $('response-title').textContent=data.module==='river'?'River signature transitions':'Wetland response samples';
 const values=[['Paired-valid area',r.paired_valid_area_km2],['Dark candidates on current valid area',r.radar_dark_candidate_area_km2],['Baseline-common area',r.baseline_common_area_km2],['Gained dark signature vs baseline',r.gain_dark_signature_km2],['Lost dark signature vs baseline',r.loss_dark_signature_km2],['Paired brightening on baseline-common area',r.brightening_candidate_area_km2]];
 $('response-values').innerHTML=values.map(([label,value])=>`<dt>${esc(label)}</dt><dd>${fmt(value)} km²</dd>`).join('');
}
function renderHypotheses(){
 const lines=[['Moisture or surface roughness','HH/HV backscatter differences can be compatible with changed surface conditions.','Radar intensity alone does not separate moisture from roughness or geometry.','Compare independent optical context, rainfall timing and a stable nearby surface.'],['Vegetation or structural disturbance','Different HH and HV responses can help examine scattering changes.','The same pattern can have several explanations; there is no calibrated species, biomass or damage estimate.','Inspect cloud-free optical imagery or a documented field/reference observation.'],['Measurement or terrain effects','Source geometry, common-valid coverage and processing details are recorded.','Quality masks do not eliminate all speckle, calibration, layover or registration effects.','Inspect source QA, threshold sensitivity and stable-area behavior before event attribution.']];
 $('hypotheses').innerHTML=lines.map(([title,support,limit,next])=>`<details><summary>${esc(title)}</summary><p><b>Why consider it:</b> ${esc(support)}</p><p><b>What remains unresolved:</b> ${esc(limit)}</p><p><b>Next check:</b> ${esc(next)}</p></details>`).join('');
}
async function show(index){
 state.index=index;state.layer=layersForVisit(index).includes(state.layer)?state.layer:'hh';$('layer-select').value=state.layer;
 for(const option of $('layer-select').options)option.disabled=!layersForVisit(index).includes(option.value);
 const obs=state.data.observations[index],token=++state.mapEpoch,caseEpoch=state.epoch;
 $('map-loading').hidden=false;$('investigation-map').setAttribute('aria-busy','true');
 const extension=isDualpolLayer(state.layer)&&state.dualpol,terrain=state.layer.startsWith('context_')&&state.contextV2,base=(state.case.record_base||'/cases/'+state.data.case_id)+(terrain?'/context-v2/':extension?'/dualpol-v1/':'/investigation/');
 const filename=terrain?terrain.layers[state.layer.slice(8)].preview:extension?extension.observations[index].layers[state.layer]:state.layer==='occupancy'?state.data.occupancy_preview:obs.layers[state.layer];
 const firstFile=extension?extension.observations[0].layers[state.layer]:state.data.observations[0].layers[state.layer];
 const [selected,first]=await Promise.all([image(base+filename),canCompareView(state.layer)?image(base+firstFile):Promise.resolve(null)]);
 if(token!==state.mapEpoch||caseEpoch!==state.epoch)return;
 currentImage=selected;firstImage=first;
 $('map-title').textContent=$('layer-select').selectedOptions[0].textContent;$('map-location').textContent=state.data.title;
 $('map-date').textContent=terrain?'STATIC TERRAIN CONTEXT':state.layer==='occupancy'?'FULL OBSERVED SERIES':day(obs.timestamp)+' · NISAR';
 const fraction=state.layer==='hh'||state.layer==='hv'?obs.quality[state.layer].valid_fraction:['baseline','river','wetland'].includes(state.layer)?obs.baseline_common_fraction:obs.paired_valid_fraction;
 $('map-coverage').textContent=state.layer==='occupancy'?'≥ 2 valid visits / pixel':fmt(fraction*100,1)+'% valid support';
 if(state.layer==='successive'){
  const a=state.data.observations[index-1];$('map-coverage').textContent='Validity: both compared HH visits';$('map-note').textContent=`Compared ${day(a.timestamp)} → ${day(obs.timestamp)}. This view shows newly measured HH differences, not all retained differences.`;
 }else $('map-note').textContent=state.layer==='occupancy'?'Summarizes paired-valid visits across the entire series; changing the selected date does not change this full-series layer.':state.data.selection_note;
 $('map-scale').textContent=fmt(state.data.grid.shape[1]*Math.abs(state.data.grid.affine[0])/1000,1)+' km wide · north up';
 $('compare-label').hidden=!canCompareView(state.layer);$('split-control').hidden=!canCompareView(state.layer)||!$('compare').checked;
 document.querySelectorAll('[data-visit]').forEach(b=>{const active=Number(b.dataset.visit)===index;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','date');else b.removeAttribute('aria-current');});
 $('visit-count').textContent=`${index+1} / ${state.data.observations.length} visits`;
 $('map-loading').hidden=true;$('investigation-map').setAttribute('aria-busy','false');legend();canvasDraw();renderProfile();renderResponse();$('acquisition-calendar').innerHTML=calendarHTML(state.calendar,index,state.missingGcov);
 if((state.layer==='successive'||state.layer.endsWith('_successive'))&&intervalForVisit(state.calendar,index))$('map-note').textContent+=' '+recordedIntervalLabel(intervalForVisit(state.calendar,index))+'.';
 if(terrain){$('map-coverage').textContent='30 m terrain context · static';$('map-note').textContent='Separately sourced NASADEM terrain for this crop. Native resolution remains approximately 30 m. Viewing-geometry flags are conservative screening candidates, not validated visibility corrections.';}
 if(extension){const stats=extension.observations[index].display_statistics[state.layer],hint=extension.observations[index].hint_statistics[state.layer];if(stats){$('map-coverage').textContent=fmt(stats.valid_fraction*100,1)+'% valid support';$('map-note').textContent+=' Display saturation: '+(stats.below_display+stats.above_display).toLocaleString('en-US')+' of '+stats.valid_pixels.toLocaleString('en-US')+' valid pixels; native values remain available in the COG.';}else if(hint)$('map-coverage').textContent=fmt(hint.assessable_area_km2)+' km² assessable';}
}
function methods(){
 const d=state.data;
 $('methods-content').innerHTML=`<p>${esc(d.selection_note)}</p><h3>What the measurements mean</h3><pre>${esc(JSON.stringify(d.formulas,null,2))}</pre><h3>Illustrative thresholds</h3><pre>${esc(JSON.stringify(d.thresholds,null,2))}</pre><h3>Sources and exact granules</h3><p>NASA Earthdata / ASF DAAC · ${esc(d.collection)}. Pixel quality/window hashes are included in the dossier. Both channels here are L-band.</p><ul>${d.observations.map(o=>`<li>${esc(day(o.timestamp))}<br><code>${esc(o.source_granule_id)}</code></li>`).join('')}</ul><h3>Limits</h3><ul>${d.limitations.map(s=>`<li>${esc(s)}</li>`).join('')}</ul><h3>Provenance</h3><pre>${esc(JSON.stringify(d.provenance,null,2))}</pre><p><a href="https://nisar-docs.asf.alaska.edu/gcov/" target="_blank" rel="noreferrer">ASF GCOV guide ↗</a> · <a href="${esc(state.case.manifest_url)}" download>Full saved manifest ↓</a></p>`;
}
async function selectCase(id){
 const token=++state.epoch;++state.probeEpoch;++state.mapEpoch;player?.destroy();player=null;state.data=null;state.calendar=null;state.dualpol=null;state.sensitivity=null;state.contextV2=null;state.evidence=null;state.selectedEvidence=null;state.references=null;state.drawing=false;state.polygon=[];state.profile=null;state.marker=null;currentImage=null;firstImage=null;
 $('investigation-error').hidden=true;$('ready-workspace').hidden=true;$('pending').hidden=true;$('methods-open').disabled=true;
 const row=state.registry.cases.find(c=>c.case_id===id);state.case=row;$('case-select').value=id;$('case-question').textContent=row.question;
 $('case-state').textContent=row.status==='OBSERVATIONS_READY'?'SAVED OBSERVATIONS':'AWAITING DATA';
 if(row.status!=='OBSERVATIONS_READY'){
  $('pending').hidden=false;$('pending-title').textContent=row.title;$('pending-copy').textContent=`${row.local_source_count} local files found. At least ${row.minimum_observations} compatible dual-polarization observations are required. The analytical modules are built; their maps await actual observations.`;
  $('download-size').textContent=`Six priority files: approximately ${fmt(state.plan.priority_total_gib,1)} GiB. All ten: ${fmt(state.plan.all_total_gib,1)} GiB. One shared download supports both sites.`;
  $('download-dates').innerHTML=state.plan.granules.filter(g=>g.priority==='START_HERE').map(g=>`<li>${esc(day(g.date))} <small>· ${fmt(g.catalog_size_mib/1024,2)} GiB</small></li>`).join('');$('download-folder').textContent=row.source_directory+'/';return;
 }
 const data=await json(row.manifest_url);if(token!==state.epoch)return;
 const recordBase=row.record_base||'/cases/'+id;
 let activeCalendar=null;if(row.calendar_url)activeCalendar=await json(row.calendar_url);if(token!==state.epoch)return;
 let extension=null,sensitivity=null;
 try{[extension,sensitivity]=await Promise.all([json(recordBase+'/dualpol-v1/manifest.json'),json(recordBase+'/dualpol-v1/sensitivity.json')]);if(!extensionMatches(extension,data))extension=null;}catch{extension=null;}
 if(token!==state.epoch)return;
 state.dualpol=extension;state.sensitivity=extension?sensitivity:null;
 let contextV2=null,evidence=null,references=null;
 try{contextV2=await json(recordBase+'/context-v2/manifest.json');}catch{}
 if(token!==state.epoch)return;
 try{evidence=await json(recordBase+'/evidence-v2/manifest.json');}catch{}
 if(token!==state.epoch)return;
 try{references=await json(recordBase+'/references-v1/manifest.json');}catch{}
 if(token!==state.epoch)return;
 state.contextV2=contextV2;state.references=references;
 state.evidence=evidence?{...evidence,profiles:[...evidence.profiles,...(references?.profiles||[])]}:null;
 if(state.evidence){data.profiles=state.evidence.profiles.map(r=>r.profile);state.selectedEvidence=state.evidence.profiles[0]||null;}
 sharedFootprint='saved:0';state.data=data;state.calendar=calendarForCase(activeCalendar?{series:{active:activeCalendar}}:state.calendars,id,data.observations);state.layer='hh';state.index=data.observations.length-1;state.profileIndex=0;state.profile=data.profiles[0]||null;
 $('profile-select').innerHTML=data.profiles.length?data.profiles.map((p,i)=>`<option value="${i}">${esc(p.label)}</option>`).join(''):'<option value="">Click map to select a footprint</option>';
 $('profile-select').disabled=!data.profiles.length;
 $('reference-label').hidden=!data.reference;$('reference-panel').hidden=!data.reference;
 if(data.reference){$('reference-detail').textContent=`${fmt(data.reference.intersected_geometry_area_km2)} km² of preliminary mapped impacts intersects this crop. The selected reference footprint uses native pixel centers; rasterized area can differ from vector area.`;$('reference-source').href=data.reference.url;}
 $('visit-buttons').innerHTML=data.observations.map((obs,i)=>`<button data-visit="${i}">${esc(day(obs.timestamp))}<small>${i===0?'FIRST OBSERVATION':fmt((new Date(obs.timestamp)-new Date(data.observations[i-1].timestamp))/86400000,0)+' DAYS SINCE PRIOR'}</small></button>`).join('');
 player=createPlayback({count:data.observations.length,initialIndex:state.index,show,onState:s=>{$('play').textContent=s.playing?'Ⅱ Pause':'▶ Play visits';$('play').setAttribute('aria-pressed',String(s.playing));},onError:fail});player.setDelay(Number($('playback-speed').value));player.setLoop($('loop').checked);
 document.querySelectorAll('[data-visit]').forEach(b=>b.addEventListener('click',()=>player.seek(Number(b.dataset.visit))));
 $('play').disabled=false;$('ready-workspace').hidden=false;$('methods-open').disabled=false;renderHypotheses();methods();await show(state.index);
}
async function selectMode(mode,country=state.country,preferredCase=null){
 state.mode=mode;state.country=['river','wetland'].includes(mode)?'bangladesh':country;
 const copy=focusCopy(state.country,mode);
 $('focus-title').textContent=copy.title;$('focus-eyebrow').textContent=copy.eyebrow;$('focus-description').textContent=copy.description;
 $('nepal-record-link').hidden=state.country!=='nepal';
 document.querySelectorAll('[data-mode]').forEach(b=>{const active=b.dataset.mode===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
 for(const focus of ['surface','river','wetland']){const n=casesForFocus(state.registry.cases,focus,state.country).filter(c=>c.status==='OBSERVATIONS_READY').length;$(focus+'-count').textContent=`${focus==='surface'&&state.country==='nepal'?'Nepal':'Bangladesh'} · ${n} study ${n===1?'area':'areas'}`;}
 const rows=casesForFocus(state.registry.cases,mode,state.country);
 $('case-select').innerHTML=rows.map(c=>`<option value="${esc(c.case_id)}">${esc(c.title)}</option>`).join('');$('case-select').disabled=rows.length<2;
 await selectCase(rows.find(c=>c.case_id===preferredCase)?.case_id||rows[0].case_id);
}

async function inspect(point){
 if(!state.data||!point)return;player.pause();const token=++state.probeEpoch,epoch=state.epoch;state.marker=point;canvasDraw();$('profile-status').textContent='Reading the same native neighborhood across all visits…';
 try{const result=await json(`/api/cases/${state.data.case_id}/investigation-reasoning?`+new URLSearchParams(point));if(token!==state.probeEpoch||epoch!==state.epoch)return;sharedFootprint='point:'+point.row+','+point.col;state.selectedEvidence=result.profile?result:null;state.profile=result.profile||result;state.polygon=[];$('profile-select').value='';renderProfile();}catch(error){if(token===state.probeEpoch&&epoch===state.epoch)fail(error);}
}

async function showMovement(step,scrollToMap=true){
 player?.pause();
 if(step<3){await selectMode('surface','nepal','nepal_surface');$('profile-select').value='0';sharedFootprint='saved:0';state.profile=state.data.profiles[0];state.selectedEvidence=state.evidence?.profiles[0]||null;state.polygon=[];state.marker=null;state.layer='hh_baseline';await player.seek(step===1?1:2);}
 else{await selectMode('river');state.layer='river';await player.seek(state.data.observations.length-1);}
 document.querySelectorAll('[data-movement]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.movement)===step)));
 $('movement-status').textContent=step===1?'Detect: the first changed visit in the preserved Nepal footprint.':step===2?'Persist: the same footprint at the later observed visit. The alert disappeared; the measured disturbance did not.':'Generalize: real Jamuna observations, competing explanations and next evidence. Wetland Pulse is also available.';
 if(scrollToMap)$('case-workspace').scrollIntoView?.({block:'start',behavior:'auto'});
}
for(const button of document.querySelectorAll('[data-movement]'))button.addEventListener('click',()=>showMovement(Number(button.dataset.movement)).catch(fail));
let storyObserver=null;
$('follow-story-scroll').addEventListener('change',()=>{
 storyObserver?.disconnect();$('three-movements').classList.toggle('follow-scroll',$('follow-story-scroll').checked);
 if(!$('follow-story-scroll').checked)return;
 if(typeof IntersectionObserver==='undefined'||window.matchMedia?.('(prefers-reduced-motion: reduce)').matches){$('follow-story-scroll').checked=false;$('three-movements').classList.toggle('follow-scroll',false);$('movement-status').textContent='Use the story buttons; automatic scroll changes are unavailable or reduced motion is enabled.';return;}
 let busy=false;
 storyObserver=new IntersectionObserver(entries=>{const entry=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(entry&&!busy){busy=true;showMovement(Number(entry.target.dataset.storyCard),false).catch(fail).finally(()=>{busy=false;});}},{threshold:.7});
 document.querySelectorAll('[data-story-card]').forEach(card=>storyObserver.observe(card));
});
$('draw-polygon').addEventListener('click',()=>{if(!state.data)return;player.pause();state.drawing=!state.drawing;state.polygon=[];$('finish-polygon').hidden=!state.drawing;$('polygon-note').textContent=state.drawing?'Click three or more map vertices, then Inspect polygon. Click Draw footprint again to cancel.':'';canvasDraw();});
$('finish-polygon').addEventListener('click',async()=>{if(!state.data||state.polygon.length<3)return;const epoch=state.epoch;try{const response=await fetch('/api/cases/'+state.data.case_id+'/investigation-polygon',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vertices:state.polygon})});if(!response.ok)throw new Error('Polygon could not be assessed. Use a valid nonempty shape inside the map.');const result=await response.json();if(epoch!==state.epoch)return;sharedFootprint='polygon:'+JSON.stringify(state.polygon);state.selectedEvidence=result;state.profile=result.profile;state.drawing=false;$('finish-polygon').hidden=true;$('polygon-note').textContent='Fixed polygon assessed on the same native pixels across visits.';$('profile-select').value='';canvasDraw();renderProfile();}catch(error){fail(error);}});
$('sensitivity-mode').addEventListener('change',()=>{if(state.data)renderDualpol();});
$('case-select').addEventListener('change',e=>selectCase(e.target.value).catch(fail));
for(const b of document.querySelectorAll('[data-mode]'))b.addEventListener('click',()=>{if(state.registry)selectMode(b.dataset.mode).catch(fail);});
$('layer-select').addEventListener('change',e=>{if(!state.data)return;player.pause();state.layer=e.target.value;show(state.index).catch(fail);});
$('profile-select').addEventListener('change',e=>{++state.probeEpoch;sharedFootprint='saved:'+Number(e.target.value);state.profile=state.data.profiles[Number(e.target.value)];state.selectedEvidence=state.evidence?.profiles[Number(e.target.value)]||null;state.marker=null;state.polygon=state.profile?.geometry_pixel?.coordinates?.[0]?.slice(0,-1)||[];canvasDraw();renderProfile();});
$('play').addEventListener('click',()=>player?.snapshot().playing?player.pause():player?.play());$('playback-speed').addEventListener('change',e=>player?.setDelay(Number(e.target.value)));$('loop').addEventListener('change',e=>player?.setLoop(e.target.checked));
$('compare').addEventListener('change',()=>{$('split-control').hidden=!$('compare').checked;canvasDraw();});$('split').addEventListener('input',canvasDraw);$('reference').addEventListener('change',canvasDraw);
$('investigation-map').addEventListener('click',e=>{if(state.data){const point=pixelFromPointer(e.target.getBoundingClientRect(),e.clientX,e.clientY,state.data.grid.shape);if(state.drawing&&point){state.polygon.push([point.col+.5,point.row+.5]);$('polygon-note').textContent=state.polygon.length+' vertices selected';canvasDraw();}else inspect(point);}});
$('investigation-map').addEventListener('keydown',e=>{
 if(!state.data)return;const [h,w]=state.data.grid.shape,p=state.marker||{row:Math.floor(h/2),col:Math.floor(w/2)},step=e.shiftKey?10:1;
 const delta={ArrowUp:[-step,0],ArrowDown:[step,0],ArrowLeft:[0,-step],ArrowRight:[0,step]}[e.key];
 if(delta){e.preventDefault();state.marker={row:Math.max(0,Math.min(h-1,p.row+delta[0])),col:Math.max(0,Math.min(w-1,p.col+delta[1]))};canvasDraw();$('map-summary').textContent='Map cursor row '+state.marker.row+', column '+state.marker.col+'. Enter '+(state.drawing?'adds a footprint vertex.':'inspects this neighborhood.');}
 if(e.key==='Escape'){state.drawing=false;state.polygon=[];$('finish-polygon').hidden=true;$('polygon-note').textContent='Footprint drawing cancelled.';canvasDraw();}
 if(e.key==='Enter'){e.preventDefault();if(state.drawing){state.polygon.push([p.col+.5,p.row+.5]);$('polygon-note').textContent=state.polygon.length+' vertices selected. Move with arrow keys; Enter adds a vertex. Tab to Inspect polygon when ready.';canvasDraw();}else inspect(p);}
});
$('methods-open').addEventListener('click',()=>$('methods-dialog').showModal());$('methods-close').addEventListener('click',()=>$('methods-dialog').close());
$('export-dossier').addEventListener('click',()=>{if(state.data&&state.profile)download('terrapulse-'+state.data.case_id+'-'+state.data.observations[state.index].timestamp.slice(0,10)+'.json',JSON.stringify({...dossier(state.data,state.profile,state.index,state.layer),exploration_focus:state.mode,country:state.country,record_version:state.data.record_version||"original",acquisition_calendar:state.calendar,selected_interval:intervalForVisit(state.calendar,state.index),dualpol:dualpolDossier(state.dualpol,state.profile,state.index,state.sensitivity),case_context:state.contextV2,investigation_evidence:state.selectedEvidence?{...state.selectedEvidence,reference_status:referenceForSelection(state.references,state.selectedEvidence,state.data.observations[state.index].observation_id).status}:null,independent_reference:referenceForSelection(state.references,state.selectedEvidence,state.data.observations[state.index].observation_id),reference_status:referenceForSelection(state.references,state.selectedEvidence,state.data.observations[state.index].observation_id).status,interferometry_gate:state.interferometry?{...state.interferometry,records:state.interferometry.records.filter(r=>r.case_ids.includes(state.data.case_id))}:null,claims:state.claims},null,2),'application/json');});
for(const [id,key] of [['download-list','granule_id'],['download-urls','url']])$(id).addEventListener('click',()=>download('terrapulse-bangladesh-'+key+'.txt',state.plan.granules.filter(g=>g.priority==='START_HERE').map(g=>g[key]).join('\n')+'\n'));
window.addEventListener('pagehide',()=>player?.destroy());document.addEventListener('visibilitychange',()=>{if(document.hidden)player?.pause();});
try{
 const [registry,plan]=await Promise.all([json('/api/investigations'),json('/cases/download-plan.json')]);state.registry=registry;state.plan=plan;
 try{state.interferometry=await json('/cases/interferometry-v2.json');}catch{state.interferometry=null;}
 try{const expanded=await json('/cases/expanded-v1.json');state.interferometry={...(state.interferometry||{records:[]}),expanded_cases:expanded.cases};}catch{}
 try{state.claims=await json('/api/claims');}catch{state.claims=null;}$('claims-panel').innerHTML=claimsHTML(state.claims);const hero=state.claims?.claims.find(c=>c.id==='TP-PERSIST');if(hero){$('movement-detect').textContent=hero.text;$('movement-persist').textContent=hero.limitation;}
 try{state.calendars=await json('/cases/time-axis-v1/calendars.json');}catch{state.calendars=null;}
 try{state.missingGcov=await json('/cases/bangladesh-missing-gcov-v1.json');}catch{state.missingGcov=null;}
 const initialContext=investigationContext(window.location?.search||'',initialView);
 await selectMode(initialContext.mode,initialContext.country,initialView.case);
 await restoreView(initialView);
}catch(error){fail(error);}

window.addEventListener('hashchange',()=>{if(!restoringView)restoreView(readView(window.location.hash)).catch(fail);});
