import {createPlayback} from '/playback.mjs';
import {escape,number,isCoherence,pairForVisit,sourceFor,playbackIndices,readExpandedView,traceSVG} from '/expanded-model.mjs';
const $=id=>document.getElementById(id),day=t=>new Date(t).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'UTC'});
let manifest=null,index=0,layer='hh',profile=null,profileIndex=0,player=null,epoch=0,frame=0,probeEpoch=0,point=null,inspectedPoint=null,sequence=[];
async function json(url){const r=await fetch(url);if(!r.ok)throw new Error('Local observation record unavailable ('+r.status+'). Restart TerraPulse after updating and reload this page.');return r.json();}
function fail(error){$('error').hidden=false;$('error').textContent=error.message||String(error);}
function transport(s){
 const pairs=isCoherence(layer),noun=pairs?'pairs':'visits',one=s.start===s.end;
 for(const id of ['play','map-play']){$(id).disabled=one;$(id).textContent=s.playing?'Ⅱ Pause':'▶ Play '+noun;$(id).setAttribute('aria-pressed',String(s.playing));}
 $('speed').disabled=false;$('previous').disabled=s.index<=s.start;$('next').disabled=s.index>=s.end;
 const label=manifest?day(manifest.observations[sequence[s.index]].timestamp):'';
 $('playback-status').textContent=(s.loading?'Loading':s.playing?'Playing':'Ready')+' · '+(s.index-s.start+1)+' / '+(s.end-s.start+1)+' observed '+noun+' · '+label+(one?' · select a wider range to animate':'');
}
function configurePlayback(){
 player?.destroy();sequence=playbackIndices(manifest,layer);
 if(!sequence.length){player=null;for(const id of ['play','map-play','previous','next'])$(id).disabled=true;$('playback-status').textContent='No available frames for this measurement.';return;}
 const options=sequence.map((i,n)=>`<option value="${n}">${isCoherence(layer)?pairForVisit(manifest,i).timestamps.map(day).join(' → '):day(manifest.observations[i].timestamp)}</option>`).join('');
 $('range-start').innerHTML=options;$('range-end').innerHTML=options;$('range-start').value='0';$('range-end').value=String(sequence.length-1);
 player=createPlayback({count:sequence.length,initialIndex:Math.max(0,sequence.indexOf(index)),show:position=>show(sequence[position]),onError:error=>{fail(error);$('playback-status').textContent='Playback stopped: '+error.message;},onState:transport});
 player.setDelay(Number($('speed').value));player.setLoop($('loop').checked);transport(player.snapshot());
}
async function seekVisit(visit){
 if(!manifest)return;const position=sequence.indexOf(visit);
 if(position>=0&&player)return player.seek(position);
 player?.pause();await show(visit);$('playback-status').textContent='No available frame for this date and measurement. Play uses only available '+(isCoherence(layer)?'pairs.':'visits.');
}
function link(){const p=new URLSearchParams({case:manifest.case_id,date:manifest.observations[index].timestamp,layer,footprint:String(profileIndex)});if(inspectedPoint)p.set('point',inspectedPoint.row+','+inspectedPoint.col);history.replaceState(null,'','#'+p);window.dispatchEvent?.(new Event('terrapulse:view'));}
function paintProfile(){
 if(!profile)return;
 $('profile-title').textContent=profile.label;
 $('support').textContent=number(profile.common_valid_pixels)+' of '+number(profile.footprint_pixels)+' footprint pixels are valid in both channels across all visits ('+number(profile.common_valid_area_km2)+' km²).';
 const r=profile.observations[index];
 $('metrics').innerHTML=[['HH · minus August 19',number(r.hh_reference_delta_db)+' dB'],['HV · minus August 19',number(r.hv_reference_delta_db)+' dB'],['CPR · minus August 19',number(r.cpr_reference_delta_db)+' dB'],['HH · previous visit',r.hh_successive_delta_db===null?'Unavailable':number(r.hh_successive_delta_db)+' dB']].map(([k,v])=>`<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join('');
 $('chart').innerHTML=traceSVG(profile,manifest,index);
 const before=profile.observations.slice(0,manifest.reference_index).map(r=>r.hh_reference_delta_db).filter(Number.isFinite);
 $('record-reading').textContent=before.length?'Earlier HH differences range from '+number(Math.min(...before))+' to '+number(Math.max(...before))+' dB relative to August 19. This earlier variability matters: the reference date is not independently established as undisturbed.':'Earlier fixed-footprint measurements are unavailable.';
}
function paintPair(pair){
 const rows=pair?[['Observed pair',day(pair.timestamps[0])+' → '+day(pair.timestamps[1])],...['20','80'].flatMap(res=>[['Mean coherence · '+res+' m',number(pair.statistics[res].mean_coherence)],['Valid support · '+res+' m',number(pair.statistics[res].valid_fraction*100)+'%']])]:[];
 $('coherence-metrics').innerHTML=rows.map(([k,v])=>`<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join('');
}
async function show(next){
 if(!manifest)return;const token=++frame;index=next;const obs=manifest.observations[index],coherence=isCoherence(layer),pair=pairForVisit(manifest,index),src=sourceFor(manifest,index,layer);
 $('map-kind').textContent=coherence?'MEASURED PAIRWISE HH COHERENCE':'ACTUAL ACQUISITION · FREQUENCY A';
 $('map-title').textContent=coherence?(pair?day(pair.timestamps[0])+' → '+day(pair.timestamps[1]):'No coherence pair ending at this visit'):day(obs.timestamp)+' · '+$('layer').selectedOptions[0].textContent;
 $('resolution').textContent=coherence?'Native '+(layer==='coherence20'?'20':'80')+' m grid':'Native 10 m intensity grid';
 $('pair-control').hidden=!coherence;if(pair)$('pair').value=pair.pair_id;
 $('date-slider').value=String(index);
 document.querySelectorAll('[data-visit]').forEach(b=>{const active=Number(b.dataset.visit)===index;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','date');else b.removeAttribute('aria-current');});
 const limits=manifest.display_limits[layer];$('low').textContent=limits[0]+(coherence?'':' dB');$('high').textContent=limits[1]+(coherence?'':' dB');$('gradient').style.background=manifest.palette_css[layer.includes('_')?'vik':'cividis'];
 const image=$('map-image');image.hidden=true;$('map-empty').hidden=false;$('map-empty').textContent=src?'Loading saved measurement…':coherence?'No available GUNW pair ends at this visit. Choose an observed pair above.':'The first observed visit has no previous-visit difference.';
 $('map').setAttribute('aria-busy',String(Boolean(src)));
 $('map-note').textContent=coherence?'Coherence is on its own native grid. Transparent pixels fail finite/range, source-subswath or anomaly checks. Pair summaries describe the full crop; intensity footprint statistics are separate.':'Fixed display limits across all dates. Comparisons use August 19 or the previous actual acquisition, as labeled. Click to inspect a fixed intensity neighborhood.';
 const download=coherence?pair?.rasters[layer]:['hh','hv'].includes(layer)?obs.rasters[layer]:null;
 $('native-download').hidden=!download;if(download)$('native-download').href=download;
 $('cursor').hidden=coherence||!point;paintProfile();paintPair(pair);link();
 if(!src){$('map').setAttribute('aria-busy','false');return;}
 await new Promise((resolve,reject)=>{
  const preload=new Image();
  function failed(message){
   preload.onload=preload.onerror=null;
   if(token!==frame){resolve();return;}
   $('map-empty').textContent=message;$('map').setAttribute('aria-busy','false');reject(new Error(message));
  }
  const timeout=setTimeout(()=>failed('Saved frame took too long to load. Check the local server, then press Play again.'),15000);
  preload.onload=()=>{clearTimeout(timeout);if(token===frame){image.src=src;image.alt=$('map-title').textContent+'; '+$('resolution').textContent;image.hidden=false;$('map-empty').hidden=true;$('map').setAttribute('aria-busy','false');}resolve();};
  preload.onerror=()=>{clearTimeout(timeout);failed('A saved preview is unavailable. Check the local server, then press Play again.');};preload.src=src;
 });
}
async function inspect(row,col){
 if(isCoherence(layer)){$('inspection-note').textContent='This map uses a different native coherence grid. Switch to an intensity layer to inspect a fixed 10 m neighborhood.';return;}
 player.pause();const request=++probeEpoch,caseEpoch=epoch;
 $('inspection-note').textContent='Reading identical native pixels through every visit…';
 try{const result=await json(`/api/cases/${manifest.case_id}/expanded-probe?row=${row}&col=${col}`);if(request!==probeEpoch||caseEpoch!==epoch)return;point={row,col};inspectedPoint={row,col};profile=result.profile;$('footprint').value='';paintProfile();$('inspection-note').textContent='Fixed native intensity neighborhood. No optical match or physical cause is assigned.';cursor();link();}catch(e){if(request===probeEpoch&&caseEpoch===epoch)fail(e);}
}
function cursor(){if(!point||!manifest)return;const [h,w]=manifest.grid.shape;$('cursor').hidden=isCoherence(layer);$('cursor').style.left=(point.col+.5)/w*100+'%';$('cursor').style.top=(point.row+.5)/h*100+'%';}
async function selectCase(id,view={}){
 const request=++epoch;++probeEpoch;++frame;player?.destroy();manifest=null;profile=null;$('error').hidden=true;for(const id of ['play','map-play','previous','next'])$(id).disabled=true;$('export').disabled=true;$('map-image').hidden=true;$('map-empty').hidden=false;$('map-empty').textContent='Loading this crop’s evidence…';$('map').setAttribute('aria-busy','true');
 const data=await json(`/cases/${id}/expanded-v1/manifest.json`);if(request!==epoch)return;manifest=data;point=null;inspectedPoint=null;profileIndex=view.footprint===1?1:0;profile=data.profiles[profileIndex];$('case').value=id;$('footprint').value=String(profileIndex);
 $('record-count').textContent=data.observations.length+' observed visits · '+data.interferometry.length+' coherence pairs';
 $('original-link').href='/investigations.html#'+new URLSearchParams({case:id,mode:'surface'});
 $('pair').innerHTML=data.interferometry.map(p=>`<option value="${escape(p.pair_id)}">${day(p.timestamps[0])} → ${day(p.timestamps[1])}</option>`).join('');
 $('dates').innerHTML=data.observations.map((o,i)=>`<button data-visit="${i}">${day(o.timestamp).replace(' 2026','')}<small>${i===data.reference_index?'CHANGE REFERENCE':pairForVisit(data,i)?'COHERENCE PAIR END':i<data.reference_index?'BEFORE REFERENCE':'LATER OBSERVATION'}</small></button>`).join('');
 const selected=data.observations.findIndex(o=>o.timestamp===view.date);index=selected>=0?selected:data.observations.length-1;
 layer=Object.hasOwn(data.display_limits,view.layer)?view.layer:'hh';$('layer').value=layer;
 if(!view.date&&isCoherence(layer))index=data.observations.findIndex(o=>o.timestamp===data.interferometry[0].timestamps[1]);
 $('inspection-note').textContent=view.date&&selected<0?'The requested date is not available. Showing the latest actual acquisition; no missing observation was synthesized.':'Click the intensity map, or use arrows then Enter, to follow a native neighborhood through every visit.';
 $('date-slider').max=String(data.observations.length-1);$('date-slider').disabled=false;
 $('sources').innerHTML=data.observations.map(o=>`<article><strong>${day(o.timestamp)}</strong><br><code>${escape(o.source_granule_id)}</code><p><a href="${escape(o.rasters.hh)}" download>Native HH COG ↓</a><a href="${escape(o.rasters.hv)}" download>Native HV COG ↓</a></p></article>`).join('')+data.interferometry.map(p=>`<article><strong>GUNW · ${day(p.timestamps[0])} → ${day(p.timestamps[1])}</strong><p><code>${escape(p.identification.granuleId)}</code></p><p>${Object.entries(p.rasters).map(([name,url])=>`<a href="${escape(url)}" download>${escape(name)} ↓</a>`).join('')}</p><p class="note">Phase downloads are in radians, uncorrected. Component labels and masks do not establish displacement validity.</p></article>`).join('')+`<p><a href="/cases/${id}/expanded-v1/manifest.json" download>Full provenance and quality manifest ↓</a></p>`;
 $('limits').innerHTML=data.limitations.map(s=>`<li>${escape(s)}</li>`).join('');
 configurePlayback();
 document.querySelectorAll('[data-visit]').forEach(b=>b.addEventListener('click',()=>seekVisit(Number(b.dataset.visit))));
 $('export').disabled=false;await show(index);
 if(view.point&&/^\d+,\d+$/.test(view.point)){const [row,col]=view.point.split(',').map(Number);if(row<data.grid.shape[0]&&col<data.grid.shape[1])await inspect(row,col);}
}
$('case').addEventListener('change',()=>selectCase($('case').value).catch(fail));
$('layer').addEventListener('change',()=>{if(!manifest)return;player?.pause();layer=$('layer').value;if(isCoherence(layer)&&!pairForVisit(manifest,index)){const p=manifest.interferometry[0];index=manifest.observations.findIndex(o=>o.timestamp===p.timestamps[1]);}configurePlayback();return seekVisit(index).catch(fail);});
$('pair').addEventListener('change',()=>{if(!manifest)return;const p=manifest.interferometry.find(p=>p.pair_id===$('pair').value);if(p)return seekVisit(manifest.observations.findIndex(o=>o.timestamp===p.timestamps[1]));});
$('footprint').addEventListener('change',()=>{if(!manifest)return;++probeEpoch;profileIndex=Number($('footprint').value);profile=manifest.profiles[profileIndex];point=null;inspectedPoint=null;$('cursor').hidden=true;paintProfile();link();});
for(const id of ['play','map-play'])$(id).addEventListener('click',()=>player&&(player.snapshot().playing?player.pause():player.play()));
for(const [id,step] of [['previous',-1],['next',1]])$(id).addEventListener('click',()=>{if(!player)return;const s=player.snapshot();return player.seek(Math.max(s.start,Math.min(s.end,s.index+step)));});
$('loop').addEventListener('change',()=>player?.setLoop($('loop').checked));
for(const id of ['range-start','range-end'])$(id).addEventListener('change',()=>{if(!player)return;let first=Number($('range-start').value),last=Number($('range-end').value);if(first>last){if(id==='range-start')last=first;else first=last;}$('range-start').value=String(first);$('range-end').value=String(last);player.setRange(first,last);return player.seek(first);});
$('speed').addEventListener('change',()=>player?.setDelay(Number($('speed').value)));
$('date-slider').addEventListener('input',()=>seekVisit(Number($('date-slider').value)));
$('map').addEventListener('click',e=>{if(!manifest)return;const r=$('map').getBoundingClientRect(),[h,w]=manifest.grid.shape;const scale=Math.min(r.width/w,r.height/h),left=r.left+(r.width-w*scale)/2,top=r.top+(r.height-h*scale)/2;const row=Math.floor((e.clientY-top)/scale),col=Math.floor((e.clientX-left)/scale);if(row>=0&&row<h&&col>=0&&col<w)inspect(row,col);});
$('map').addEventListener('keydown',e=>{if(!manifest)return;const [h,w]=manifest.grid.shape;if(!point)point={row:Math.floor(h/2),col:Math.floor(w/2)};const step=e.shiftKey?10:1;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Enter'].includes(e.key))e.preventDefault();if(e.key==='ArrowUp')point.row=Math.max(0,point.row-step);if(e.key==='ArrowDown')point.row=Math.min(h-1,point.row+step);if(e.key==='ArrowLeft')point.col=Math.max(0,point.col-step);if(e.key==='ArrowRight')point.col=Math.min(w-1,point.col+step);cursor();if(e.key==='Enter')return inspect(point.row,point.col);});
$('export').addEventListener('click',()=>{const payload={project:'TerraPulse',selected_date:manifest.observations[index].timestamp,selected_layer:layer,selected_intensity_profile:profile,selected_coherence_pair:pairForVisit(manifest,index),manifest,physical_cause:'UNRESOLVED',los_displacement_cm:null};const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='terrapulse-'+manifest.case_id+'-expanded-evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
const initial=readExpandedView(location.hash);selectCase(initial.case,initial).catch(fail);
window.addEventListener('pagehide',()=>player?.destroy());document.addEventListener('visibilitychange',()=>{if(document.hidden)player?.pause();});
