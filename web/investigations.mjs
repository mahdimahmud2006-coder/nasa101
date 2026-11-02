import {createPlayback} from '/playback.mjs';
import {availableLayers,safeLayer,canCompare,pixelFromPointer,finding,dossier} from '/investigation-model.mjs';
const $=id=>document.getElementById(id);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,d=2)=>v===null||v===undefined?'Unavailable':Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const day=value=>new Date(value).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
const state={registry:null,plan:null,mode:'surface',case:null,data:null,index:0,layer:'hh',profile:null,profileIndex:0,marker:null,epoch:0,mapEpoch:0,probeEpoch:0};
let player=null,currentImage=null,firstImage=null;
const cache=new Map();
async function json(url){const r=await fetch(url);if(!r.ok)throw new Error('Evidence unavailable ('+r.status+'). Run make investigations, restart the local server if needed, then reload.');return r.json();}
function fail(error){player?.pause();$('investigation-error').hidden=false;$('investigation-error').textContent=error.message||String(error);$('map-loading').hidden=true;}
function image(url){if(!cache.has(url))cache.set(url,new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>{cache.delete(url);reject(new Error('Missing saved map asset: '+url));};img.src=url;}));return cache.get(url);}
function download(name,content,type='text/plain'){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function canvasDraw(){
 if(!currentImage||!state.data)return;
 const canvas=$('investigation-map'),ctx=canvas.getContext('2d'),[height,width]=state.data.grid.shape;
 canvas.width=1100;canvas.height=Math.round(1100*height/width);const w=canvas.width,h=canvas.height;
 ctx.clearRect(0,0,w,h);ctx.drawImage(currentImage,0,0,w,h);
 if($('compare').checked&&canCompare(state.layer)&&firstImage){const split=Number($('split').value)/100*w;ctx.save();ctx.beginPath();ctx.rect(0,0,split,h);ctx.clip();ctx.drawImage(firstImage,0,0,w,h);ctx.restore();ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(split,0);ctx.lineTo(split,h);ctx.stroke();}
 if(state.data.reference&&$('reference').checked){
  const geom=state.data.reference.geometry_pixel,polygons=geom.type==='Polygon'?[geom.coordinates]:geom.coordinates;
  ctx.save();ctx.strokeStyle='#e9ff94';ctx.lineWidth=2;ctx.fillStyle='#e9ff9425';
  for(const polygon of polygons){ctx.beginPath();for(const ring of polygon){ring.forEach(([x,y],i)=>i?ctx.lineTo(x/width*w,y/height*h):ctx.moveTo(x/width*w,y/height*h));ctx.closePath();}ctx.fill('evenodd');ctx.stroke();}ctx.restore();
 }
 if(state.marker){const x=(state.marker.col+.5)/width*w,y=(state.marker.row+.5)/height*h;ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.moveTo(x-18,y);ctx.lineTo(x+18,y);ctx.moveTo(x,y-18);ctx.lineTo(x,y+18);ctx.stroke();}
}
function legend(){
 const data=state.data,layer=state.layer,limits=data.display_limits[layer];
 const definitions={hh:['HH gamma-0 backscatter · dB',fmt(limits?.[0],1),fmt(limits?.[1],1),'Shared HH contrast across observed dates; filtered log-power.'],hv:['HV gamma-0 backscatter · dB',fmt(limits?.[0],1),fmt(limits?.[1],1),'Shared HV contrast across observed dates; distinct from HH contrast.'],ratio:['HH − HV · dB ratio','0 dB','20 dB','Difference of filtered log-power channels. Not a vegetation, moisture or biomass estimate.'],baseline:['HH difference from first observation · dB','−8 dB · decrease','+8 dB · increase','Shared display range; values outside it saturate. Baseline-common valid pixels only.'],successive:['HH difference since preceding observation · dB','−8 dB · decrease','+8 dB · increase','Shared display range; missing comparisons remain unavailable.'],river:['Dark-signature change from first observation','Blue: retained · Cyan: gained','Amber: lost','Baseline-common pixels; these are radar signatures, not confirmed bank migration.'],wetland:['Exploratory wetland radar signatures','Cyan: dark candidate','Purple: paired brightening','Dark and bright responses have multiple physical explanations; no habitat class is inferred.'],water:['Radar-dark candidates','Background: other paired-valid','Cyan: below both thresholds','Illustrative HH/HV cutoffs; smooth dry surfaces can also be dark.'],occupancy:['Fraction of observed valid visits with dark signature','0% of valid visits','100% of valid visits','At least two paired-valid visits. Visit frequency is not inundation duration. This layer summarizes the full series.']};
 const item=definitions[layer];$('legend-title').textContent=item[0];$('legend-low').textContent=item[1];$('legend-high').textContent=item[2];$('legend-note').textContent=item[3];$('legend-ramp').className='ramp '+(['baseline','successive'].includes(layer)?'delta':['river','wetland'].includes(layer)?layer:'');
}
function renderProfile(){
 const p=state.profile,obs=state.data.observations[state.index],row=p?.observations[state.index];
 $('profile-title').textContent=p?.label||'Select a footprint on the map.';
 $('profile-status').textContent=p?`${p.status==='MEASURED'?'Measured':'Insufficient common data'} · ${p.selection}`:'No selected-region interpretation is generated until a footprint is available.';
 $('measure-hh').textContent=row?.hh_baseline_delta_db===null||!row?'Unavailable':fmt(row.hh_baseline_delta_db)+' dB';
 $('measure-hv').textContent=row?.hv_baseline_delta_db===null||!row?'Unavailable':fmt(row.hv_baseline_delta_db)+' dB';
 $('measure-successive').textContent=row?.hh_successive_delta_db===null||!row?'Unavailable':fmt(row.hh_successive_delta_db)+' dB';
 $('successive-note').textContent=state.index?'signed HH difference since prior visit':'no previous visit at baseline';
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
  const key=pol+'_baseline_delta_db';let path='';
  for(let i=1;i<data.length;i++)if(data[i-1][key]!==null&&data[i][key]!==null)path+=`M${x(data[i-1])},${y(data[i-1][key])}L${x(data[i])},${y(data[i][key])}`;
  marks+=`<path class="${pol}-line" d="${path}"/>`;
  marks+=data.filter(r=>r[key]!==null).map(r=>`<circle cx="${x(r)}" cy="${y(r[key])}" r="${r.observation_id===obs.observation_id?6:4}" fill="${pol==='hh'?'#75e3d2':'#ffd091'}"><title>${esc(day(r.timestamp))}: ${fmt(r[key])} dB ${pol.toUpperCase()}</title></circle>`).join('');
 }
 for(const i of [...new Set([0,Math.floor(data.length/2),data.length-1])])marks+=`<text x="${x(data[i])}" y="${h-15}" text-anchor="middle">${esc(day(data[i].timestamp).replace(' 2026',''))}</text>`;
 $('profile-chart').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="HH and HV signed baseline backscatter differences on the same common-valid footprint; dots are actual acquisition dates">${marks}</svg>`;
 $('profile-footnote').textContent=`${data.length} actual observations · ${p.common_valid_pixels} common native pixels · time axis uses elapsed days. Lines connect samples for reading; unobserved daily values are not estimated.`;
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
 state.index=index;state.layer=safeLayer(state.layer,state.data.module,index);$('layer-select').value=state.layer;
 for(const option of $('layer-select').options)option.disabled=!availableLayers(state.data.module,index).includes(option.value);
 const obs=state.data.observations[index],token=++state.mapEpoch,caseEpoch=state.epoch;
 $('map-loading').hidden=false;$('investigation-map').setAttribute('aria-busy','true');
 const base='/cases/'+state.data.case_id+'/investigation/';
 const filename=state.layer==='occupancy'?state.data.occupancy_preview:obs.layers[state.layer];
 const [selected,first]=await Promise.all([image(base+filename),canCompare(state.layer)?image(base+state.data.observations[0].layers[state.layer]):Promise.resolve(null)]);
 if(token!==state.mapEpoch||caseEpoch!==state.epoch)return;
 currentImage=selected;firstImage=first;
 $('map-title').textContent=$('layer-select').selectedOptions[0].textContent;$('map-location').textContent=state.data.title;
 $('map-date').textContent=state.layer==='occupancy'?'FULL OBSERVED SERIES':day(obs.timestamp)+' · NISAR';
 const fraction=state.layer==='hh'||state.layer==='hv'?obs.quality[state.layer].valid_fraction:['baseline','river','wetland'].includes(state.layer)?obs.baseline_common_fraction:obs.paired_valid_fraction;
 $('map-coverage').textContent=state.layer==='occupancy'?'≥ 2 valid visits / pixel':fmt(fraction*100,1)+'% valid support';
 if(state.layer==='successive'){
  const a=state.data.observations[index-1];$('map-coverage').textContent='Validity: both compared HH visits';$('map-note').textContent=`Compared ${day(a.timestamp)} → ${day(obs.timestamp)}. This view shows newly measured HH differences, not all retained differences.`;
 }else $('map-note').textContent=state.layer==='occupancy'?'Summarizes paired-valid visits across the entire series; changing the selected date does not change this full-series layer.':state.data.selection_note;
 $('map-scale').textContent=fmt(state.data.grid.shape[1]*Math.abs(state.data.grid.affine[0])/1000,1)+' km wide · north up';
 $('compare-label').hidden=!canCompare(state.layer);$('split-control').hidden=!canCompare(state.layer)||!$('compare').checked;
 document.querySelectorAll('[data-visit]').forEach(b=>{const active=Number(b.dataset.visit)===index;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','date');else b.removeAttribute('aria-current');});
 $('visit-count').textContent=`${index+1} / ${state.data.observations.length} visits`;
 $('map-loading').hidden=true;$('investigation-map').setAttribute('aria-busy','false');legend();canvasDraw();renderProfile();renderResponse();
}
function methods(){
 const d=state.data;
 $('methods-content').innerHTML=`<p>${esc(d.selection_note)}</p><h3>What the measurements mean</h3><pre>${esc(JSON.stringify(d.formulas,null,2))}</pre><h3>Illustrative thresholds</h3><pre>${esc(JSON.stringify(d.thresholds,null,2))}</pre><h3>Sources and exact granules</h3><p>NASA Earthdata / ASF DAAC · ${esc(d.collection)}. Pixel quality/window hashes are included in the dossier. Both channels here are L-band.</p><ul>${d.observations.map(o=>`<li>${esc(day(o.timestamp))}<br><code>${esc(o.source_granule_id)}</code></li>`).join('')}</ul><h3>Limits</h3><ul>${d.limitations.map(s=>`<li>${esc(s)}</li>`).join('')}</ul><h3>Provenance</h3><pre>${esc(JSON.stringify(d.provenance,null,2))}</pre><p><a href="https://nisar-docs.asf.alaska.edu/gcov/" target="_blank" rel="noreferrer">ASF GCOV guide ↗</a> · <a href="/cases/${esc(d.case_id)}/investigation/manifest.json" download>Full saved manifest ↓</a></p>`;
}
async function selectCase(id){
 const token=++state.epoch;++state.probeEpoch;++state.mapEpoch;player?.destroy();player=null;state.data=null;state.profile=null;state.marker=null;currentImage=null;firstImage=null;
 $('investigation-error').hidden=true;$('ready-workspace').hidden=true;$('pending').hidden=true;$('methods-open').disabled=true;
 const row=state.registry.cases.find(c=>c.case_id===id);state.case=row;$('case-select').value=id;$('case-question').textContent=row.question;
 $('case-state').textContent=row.status==='OBSERVATIONS_READY'?'SAVED OBSERVATIONS':'AWAITING DATA';
 if(row.status!=='OBSERVATIONS_READY'){
  $('pending').hidden=false;$('pending-title').textContent=row.title;$('pending-copy').textContent=`${row.local_source_count} local files found. At least ${row.minimum_observations} compatible dual-polarization observations are required. The analytical modules are built; their maps await actual observations.`;
  $('download-size').textContent=`Six priority files: approximately ${fmt(state.plan.priority_total_gib,1)} GiB. All ten: ${fmt(state.plan.all_total_gib,1)} GiB. One shared download supports both sites.`;
  $('download-dates').innerHTML=state.plan.granules.filter(g=>g.priority==='START_HERE').map(g=>`<li>${esc(day(g.date))} <small>· ${fmt(g.catalog_size_mib/1024,2)} GiB</small></li>`).join('');$('download-folder').textContent=row.source_directory+'/';return;
 }
 const data=await json(row.manifest_url);if(token!==state.epoch)return;
 state.data=data;state.layer='hh';state.index=data.observations.length-1;state.profileIndex=0;state.profile=data.profiles[0]||null;
 $('profile-select').innerHTML=data.profiles.length?data.profiles.map((p,i)=>`<option value="${i}">${esc(p.label)}</option>`).join(''):'<option value="">Click map to select a footprint</option>';
 $('profile-select').disabled=!data.profiles.length;
 $('reference-label').hidden=!data.reference;$('reference-panel').hidden=!data.reference;
 if(data.reference){$('reference-detail').textContent=`${fmt(data.reference.intersected_geometry_area_km2)} km² of preliminary mapped impacts intersects this crop. The selected reference footprint uses native pixel centers; rasterized area can differ from vector area.`;$('reference-source').href=data.reference.url;}
 $('visit-buttons').innerHTML=data.observations.map((obs,i)=>`<button data-visit="${i}">${esc(day(obs.timestamp))}<small>${i===0?'FIRST OBSERVATION':fmt((new Date(obs.timestamp)-new Date(data.observations[i-1].timestamp))/86400000,0)+' DAYS SINCE PRIOR'}</small></button>`).join('');
 player=createPlayback({count:data.observations.length,initialIndex:state.index,show,onState:s=>{$('play').textContent=s.playing?'Ⅱ Pause':'▶ Play visits';$('play').setAttribute('aria-pressed',String(s.playing));},onError:fail});player.setDelay(Number($('playback-speed').value));player.setLoop($('loop').checked);
 document.querySelectorAll('[data-visit]').forEach(b=>b.addEventListener('click',()=>player.seek(Number(b.dataset.visit))));
 $('play').disabled=false;$('ready-workspace').hidden=false;$('methods-open').disabled=false;renderHypotheses();methods();await show(state.index);
}
async function selectMode(mode){
 state.mode=mode;document.querySelectorAll('[data-mode]').forEach(b=>{const active=b.dataset.mode===mode;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});
 const rows=state.registry.cases.filter(c=>c.module===mode);$('case-select').innerHTML=rows.map(c=>`<option value="${esc(c.case_id)}">${esc(c.title)}</option>`).join('');$('case-select').disabled=rows.length<2;await selectCase(rows[0].case_id);
}
async function inspect(point){
 if(!state.data||!point)return;player.pause();const token=++state.probeEpoch,epoch=state.epoch;state.marker=point;canvasDraw();$('profile-status').textContent='Reading the same native neighborhood across all visits…';
 try{const result=await json(`/api/cases/${state.data.case_id}/investigation-probe?`+new URLSearchParams(point));if(token!==state.probeEpoch||epoch!==state.epoch)return;state.profile=result;$('profile-select').value='';renderProfile();}catch(error){if(token===state.probeEpoch&&epoch===state.epoch)fail(error);}
}
$('case-select').addEventListener('change',e=>selectCase(e.target.value).catch(fail));
for(const b of document.querySelectorAll('[data-mode]'))b.addEventListener('click',()=>{if(state.registry)selectMode(b.dataset.mode).catch(fail);});
$('layer-select').addEventListener('change',e=>{if(!state.data)return;player.pause();state.layer=e.target.value;show(state.index).catch(fail);});
$('profile-select').addEventListener('change',e=>{++state.probeEpoch;state.profile=state.data.profiles[Number(e.target.value)];state.marker=null;canvasDraw();renderProfile();});
$('play').addEventListener('click',()=>player?.snapshot().playing?player.pause():player?.play());$('playback-speed').addEventListener('change',e=>player?.setDelay(Number(e.target.value)));$('loop').addEventListener('change',e=>player?.setLoop(e.target.checked));
$('compare').addEventListener('change',()=>{$('split-control').hidden=!$('compare').checked;canvasDraw();});$('split').addEventListener('input',canvasDraw);$('reference').addEventListener('change',canvasDraw);
$('investigation-map').addEventListener('click',e=>{if(state.data)inspect(pixelFromPointer(e.target.getBoundingClientRect(),e.clientX,e.clientY,state.data.grid.shape));});
$('investigation-map').addEventListener('keydown',e=>{if(e.key==='Enter'&&state.data){e.preventDefault();inspect({row:Math.floor(state.data.grid.shape[0]/2),col:Math.floor(state.data.grid.shape[1]/2)});}});
$('methods-open').addEventListener('click',()=>$('methods-dialog').showModal());$('methods-close').addEventListener('click',()=>$('methods-dialog').close());
$('export-dossier').addEventListener('click',()=>{if(state.data&&state.profile)download('terrapulse-'+state.data.case_id+'-'+state.data.observations[state.index].timestamp.slice(0,10)+'.json',JSON.stringify(dossier(state.data,state.profile,state.index,state.layer),null,2),'application/json');});
for(const [id,key] of [['download-list','granule_id'],['download-urls','url']])$(id).addEventListener('click',()=>download('terrapulse-bangladesh-'+key+'.txt',state.plan.granules.filter(g=>g.priority==='START_HERE').map(g=>g[key]).join('\n')+'\n'));
window.addEventListener('pagehide',()=>player?.destroy());document.addEventListener('visibilitychange',()=>{if(document.hidden)player?.pause();});
try{
 const [registry,plan]=await Promise.all([json('/api/investigations'),json('/cases/download-plan.json')]);state.registry=registry;state.plan=plan;
 for(const mode of ['surface','river','wetland']){const rows=registry.cases.filter(c=>c.module===mode),ready=rows.filter(c=>c.status==='OBSERVATIONS_READY').length;$(mode+'-count').textContent=ready?`${ready} measured ${ready===1?'case':'cases'} ready`:'MODULE BUILT · AWAITING DATA';}
 const requestedMode=new URLSearchParams(window.location?.search||'').get('mode');
 await selectMode(['surface','river','wetland'].includes(requestedMode)?requestedMode:'surface');
}catch(error){fail(error);}
