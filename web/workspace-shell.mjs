import {navigationContext} from '/navigation-model.mjs';

const rail=document.getElementById('workspace-rail');
const primary=rail?.querySelector('.tp-primary');
const sub=document.getElementById('workspace-sections');

if(primary){
  const home=primary.querySelector('[data-primary="home"]');
  home.textContent='Atlas';
  const guide=primary.querySelector('[data-primary="guide"]');
  const simulation=primary.querySelector('[data-primary="simulations"]')??document.createElement('a');
  simulation.dataset.primary='simulations';
  simulation.href='/?view=simulations';
  simulation.textContent='Simulations';
  primary.insertBefore(simulation,guide);

  const more=document.createElement('details'),label=document.createElement('summary');
  more.className='tp-more-lenses';label.textContent='More lenses';
  const links=document.createElement('div');links.className='tp-lens-links';
  for(const country of ['bangladesh','nepal']){
    const link=primary.querySelector('[data-primary="'+country+'"]');
    if(link){link.href='/?country='+country;links.append(link);}
  }
  if(sub)links.append(sub);
  more.append(label,links);primary.after(more);
  more.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&more.open){more.open=false;label.focus();}
  });
}

function sync(){
  if(!rail)return;
  const state=navigationContext(location.pathname,location.search,location.hash);
  for(const link of rail.querySelectorAll('[data-primary]')){
    const key=link.dataset.primary;
    const active=key==='home'?state.home:key==='guide'?state.guide:key==='simulations'?state.simulations:state.group===key;
    if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');
  }
  if(sub){
    sub.hidden=!state.group;
    sub.replaceChildren(...state.links.map(l=>{
      const anchor=document.createElement('a');
      anchor.href=l.href;anchor.textContent=l.label;
      if(l.active)anchor.setAttribute('aria-current','page');
      return anchor;
    }));
  }
  document.body.dataset.country=state.group||'overview';
}
sync();
window.addEventListener('hashchange',sync);
window.addEventListener('popstate',sync);
window.addEventListener('terrapulse:view',sync);

// Legacy analytical controllers restore incoming hashes at boot.
if(['/studio.html','/change-lab.html','/timeseries.html','/comparison.html'].includes(location.pathname)){
  window.addEventListener('hashchange',()=>{
    if(new URLSearchParams(location.hash.slice(1)).has('case'))location.reload();
  });
}
