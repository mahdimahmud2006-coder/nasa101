import {navigationContext} from '/navigation-model.mjs';
const rail=document.getElementById('workspace-rail');
function sync(){
 if(!rail)return;
 const state=navigationContext(location.pathname,location.search,location.hash);
 for(const link of rail.querySelectorAll('[data-primary]')){
  const key=link.dataset.primary,active=key==='home'?state.home:key==='guide'?state.guide:state.group===key;
  if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
 }
 const sub=document.getElementById('workspace-sections');
 if(sub){sub.hidden=!state.group;sub.innerHTML=(state.group?`<span class="tp-country-label">${state.group==='bangladesh'?'Bangladesh':'Nepal'}</span>`:'')+state.links.map(l=>`<a href="${l.href}"${l.active?' aria-current="page"':''}>${l.label}</a>`).join('');}
 document.body.dataset.country=state.group||'overview';
}
sync();window.addEventListener('hashchange',sync);window.addEventListener('terrapulse:view',sync);

// Legacy analytical controllers restore incoming hashes at boot.
if(["/studio.html","/change-lab.html","/timeseries.html","/comparison.html"].includes(location.pathname))window.addEventListener("hashchange",()=>{if(new URLSearchParams(location.hash.slice(1)).has("case"))location.reload();});
