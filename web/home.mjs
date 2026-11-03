const $=id=>document.getElementById(id);
const countries=['bangladesh','nepal'];
export function selectCountry(country,{focus=false}={}){
 if(!countries.includes(country))country='bangladesh';
 for(const name of countries){const active=name===country,tab=$('tab-'+name);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;$('panel-'+name).hidden=!active;if(active&&focus)tab.focus();}
 return country;
}
function fromHash(scroll=false){const country=location.hash.slice(1);if(countries.includes(country)){selectCountry(country);if(scroll)$('workspace-title').scrollIntoView({block:'start',behavior:'auto'});}}
for(const country of countries){
 $('tab-'+country).addEventListener('click',()=>{selectCountry(country);history.replaceState(null,'','#'+country);});
 $('tab-'+country).addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?'bangladesh':e.key==='End'?'nepal':countries[1-countries.indexOf(country)];selectCountry(next,{focus:true});history.replaceState(null,'','#'+next);});
}
window.addEventListener('hashchange',()=>fromHash(true));fromHash(true);
$('hero-split').addEventListener('input',()=>{$('observation-wipe').style.setProperty('--split',$('hero-split').value+'%');});
for(const id of ['hero-before','hero-after'])$(id).addEventListener('error',()=>{$('hero-image-status').hidden=false;});
// Older shared studio URLs used the root path. Keep their selected Nepal view usable.
if(new URLSearchParams(location.hash.slice(1)).get('case')==='nepal_surface')location.replace('/studio.html'+location.hash);
// Counts come from accepted local manifests. Downloading files never implies readiness.
try{
 const response=await fetch('/api/investigations');if(!response.ok)throw Error('Registry unavailable');const registry=await response.json();
 for(const el of document.querySelectorAll('[data-record]')){
  const c=registry.cases.find(c=>c.case_id===el.dataset.record);if(!c||c.status!=='OBSERVATIONS_READY')continue;
  const r=await fetch(c.manifest_url);if(!r.ok)continue;const m=await r.json();
  el.textContent=`${m.observations.length} observed visits · ${new Date(m.observations[0].timestamp).toLocaleDateString('en-GB',{month:'short',timeZone:'UTC'})}–${new Date(m.observations.at(-1).timestamp).toLocaleDateString('en-GB',{month:'short',year:'numeric',timeZone:'UTC'})}`;
 }
 const r=await fetch('/cases/expanded-v1.json');if(r.ok){const data=await r.json(),c=data.cases.find(c=>c.case_id==='nepal_surface');if(c)$('nepal-record-summary').textContent=`${c.observations} observed visits · ${c.coherence_pairs} measured coherence pairs`;}
}catch{/* Static descriptions remain usable if the optional summary cannot be read. */}
