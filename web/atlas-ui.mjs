import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {iso} from './atlas-state.mjs';
import {atlasShortDate} from './atlas-timeline.mjs';

const atlasLayerNames={hh:'HH',hv:'HV',fraction:'HV share',coherence:'Coherence'};
const atlasLayerHelp={
  hh:'Surface return (HH). Radar power returned in the same polarization. Decibels (dB) are a logarithmic power scale.',
  hv:'Cross-polarized return (HV). Radar power returned in the opposite polarization. Canopy and rough surfaces can contribute.',
  fraction:'HV power share. The percentage of the combined HH and HV power returned as HV.',
  coherence:'Pair similarity. How consistently the radar phase matches between two visits, on a scale from 0 to 1.'
};
const atlasLabLabels={surge:'River surge',bank:'Bank retreat',slope:'Slope stability',orbit:'Sensor orbit',radar:'Be the NISAR Sensor'};
const atlasLabAssumptions={
  surge:{label:'High stage',values:{'sim-stage-level':5}},
  slope:{label:'Heavy rain + shaking',values:{'sim-m':.8,'sim-kh':.18}},
  bank:{label:'High discharge',values:{'bank-multiplier':2,'bank-cycles':3}},
  orbit:{label:'Opposite look',values:{'orbit-look':'desc','orbit-angle':47}},
  radar:{label:'Flooded stems',button:'radar-stems-preset'}
};
const atlasLabUnits={
  'sim-stage-level':'m','sim-m':'','sim-kh':'g','sim-cohesion':'kPa','sim-friction':'°',
  'sim-depth':'m','sim-weight':'kN/m³','bank-multiplier':'×','bank-cycles':'cycles',
  'orbit-angle':'°','orbit-motion':'cm','radar-moisture':'%','radar-water':'cm','radar-canopy':''
};

export function createAtlasPresentation({portable,standalone,hosted,simulationView,wipe,shortcuts}){
  // Core Atlas selection also runs in the socket-free package verification harness.
  if(!document.querySelector)return {render(){},showTab(){}};
  const $=atlasNode,root=document.getElementById('atlas');
  const handle=$('wipe-handle'),stack=$('image-stack'),stage=$('stage'),inspector=$('evidence-inspector');
  const studies=[...$('studies').querySelectorAll('[data-study]')];
  const names=['evidence','context','quality','text'];
  const layerButtons=Object.entries(atlasLayerNames).map(([id,label])=>{
    const button=atlasElement('button',label);
    button.type='button';button.dataset.layer=id;button.title=atlasLayerHelp[id];
    button.onclick=()=>{
      if(button.getAttribute('aria-disabled')==='true')return;
      $('layer').value=id;$('layer').dispatchEvent(new Event('change'));
    };
    return button;
  });
  $('layers').replaceChildren(...layerButtons);
  $('layers').onkeydown=event=>{
    const options=layerButtons.filter(b=>b.getAttribute('aria-disabled')!=='true');
    const index=options.indexOf(document.activeElement);
    if(index<0||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();
    const next=event.key==='Home'?0:event.key==='End'?options.length-1:
      (index+(event.key==='ArrowRight'?1:-1)+options.length)%options.length;
    options[next]?.click();options[next]?.focus();
  };
  for(const button of studies)button.onclick=()=>{
    $('case').value=button.dataset.study;
    $('case').dispatchEvent(new Event('change'));
  };
  let activeTab='evidence',sheetLevel=0;
  const sheetLabels=['Expand evidence','Show full evidence','Collapse evidence'];
  function showSheet(level){
    sheetLevel=level;
    inspector.dataset.sheet=['collapsed','expanded','full'][level];
    $('sheet').setAttribute('aria-expanded',String(level!==0));
    $('sheet').textContent=sheetLabels[level];
  }
  $('sheet').onclick=()=>showSheet((sheetLevel+1)%3);
  $('sheet').setAttribute('aria-controls','at-answer-body');
  function jumpTo(node){
    node.tabIndex=-1;
    node.focus({preventScroll:true});
    node.scrollIntoView({block:'nearest'});
  }
  $('jump-time').onclick=event=>{
    event.preventDefault();
    $('date-dock').focus({preventScroll:true});
    $('date-dock').scrollIntoView({block:'nearest'});
  };
  const evidenceTarget=simulationView?$('sim-inspector'):inspector;
  $('jump-evidence').href='#'+evidenceTarget.id;
  $('jump-evidence').textContent=simulationView?'Skip to simulation controls':'Skip to evidence';
  $('jump-evidence').onclick=event=>{
    event.preventDefault();
    if(!simulationView&&matchMedia('(max-width:1279px)').matches)showSheet(1);
    jumpTo(evidenceTarget);
  };
  showSheet(0);
  function showTab(name,focus=false){
    activeTab=name;
    for(const tab of names){
      const button=$('view-'+tab),selected=name===tab;
      button.setAttribute('aria-selected',String(selected));button.tabIndex=selected?0:-1;
      $('tab-'+tab).hidden=!selected;
      if(selected&&focus)button.focus();
    }
  }
  for(const name of names){
    $('view-'+name).onclick=()=>showTab(name);
    $('view-'+name).onkeydown=event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();
      const n=names.indexOf(activeTab),index=event.key==='Home'?0:event.key==='End'?names.length-1:
        (n+(event.key==='ArrowRight'?1:-1)+names.length)%names.length;
      showTab(names[index],true);
    };
  }
  $('discovery-open').onclick=()=>{
    if(matchMedia('(max-width:1279px)').matches)showSheet(2);
    showTab('context');
    jumpTo($('discovery-title'));
  };
  function revealDossier(){
    if(simulationView){location.href=$('observations-tab').href;return;}
    showSheet(2);
    $('dossier-tools').open=true;
    $('dossier-tools').querySelector('summary').focus({preventScroll:true});
    $('dossier-tools').scrollIntoView({block:'nearest'});
  }
  $('reopen-jump').onclick=revealDossier;
  const exportMenu=$('export-menu'),exportSummary=exportMenu.querySelector('summary');
  function closeExportMenu(){
    if(!exportMenu.open)return;
    exportMenu.open=false;exportSummary.focus();
  }
  for(const id of ['export','field-export'])$(id).addEventListener('click',closeExportMenu);
  exportMenu.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&exportMenu.open){event.stopPropagation();closeExportMenu();}
  });
  $('shell-evidence').onclick=()=>{document.querySelector('.atlas-more').open=false;revealDossier();};
  $('text-table').onclick=event=>{
    event.preventDefault();
    const table=$('table-view');
    table.open=true;table.scrollIntoView({block:'start'});
    table.querySelector('summary').focus({preventScroll:true});
  };
  $('footprint-tool').onclick=()=>{
    if(!simulationView){showSheet(2);showTab('evidence');}
    $('probe-panel').open=true;
    $('probe-panel').querySelector('summary').focus({preventScroll:true});
    $('probe-panel').scrollIntoView({block:'nearest'});
  };
  $('guide-link').onclick=event=>{
    if(!portable)return;
    event.preventDefault();
    const guide=document.getElementById('atlas-guide-reference');
    guide.open=true;guide.scrollIntoView({block:'start'});
    guide.querySelector('summary').focus({preventScroll:true});
  };
  if(portable)$('guide-link').href='#atlas-guide-reference';
  if(standalone){
    const home=event=>{event.preventDefault();window.scrollTo({top:0});};
    $('observations-tab').onclick=home;
    root.querySelector('.atlas-brand').onclick=home;
  }
  const toolsToggle=$('tools-toggle');
  function showMapTools(open){
    stage.dataset.toolsOpen=String(open);
    toolsToggle.setAttribute('aria-expanded',String(open));
  }
  toolsToggle.onclick=()=>showMapTools(stage.dataset.toolsOpen!=='true');
  $('map-tools').addEventListener('keydown',event=>{
    if(event.key==='Escape'&&stage.dataset.toolsOpen==='true'){
      event.stopPropagation();showMapTools(false);toolsToggle.focus();
    }
  });
  $('map').addEventListener('pointerdown',()=>showMapTools(false));
  $('fullscreen').onclick=async()=>{
    try{
      if(document.fullscreenElement)await document.exitFullscreen();
      else if(stage.requestFullscreen)await stage.requestFullscreen();
      else stage.dataset.wide=String(stage.dataset.wide!=='true');
    }catch{stage.dataset.wide=String(stage.dataset.wide!=='true');}
    $('fullscreen').setAttribute('aria-pressed',String(Boolean(document.fullscreenElement)||stage.dataset.wide==='true'));
  };
  document.addEventListener('fullscreenchange',()=>{
    $('fullscreen').setAttribute('aria-pressed',String(Boolean(document.fullscreenElement)));
  });

  let pointer=null,pending=null,frame=0;
  function wipePosition(event){
    const bounds=stack.getBoundingClientRect();
    return Math.max(0,Math.min(100,Math.round(100*(event.clientX-bounds.left)/bounds.width)));
  }
  handle.onpointerdown=event=>{
    if(event.button!==0)return;
    event.stopPropagation();pointer=event.pointerId;handle.setPointerCapture(pointer);handle.focus();
  };
  handle.onpointermove=event=>{
    if(event.pointerId!==pointer)return;
    pending=wipePosition(event);
    if(!frame)frame=requestAnimationFrame(()=>{frame=0;if(pending!==null)wipe(pending,false);});
  };
  function endWipe(event){
    if(event.pointerId!==pointer)return;
    pointer=null;
    if(frame)cancelAnimationFrame(frame);
    frame=0;
    if(pending!==null)wipe(pending,true);
    pending=null;
  }
  handle.onpointerup=endWipe;handle.onpointercancel=endWipe;
  handle.onclick=event=>event.stopPropagation();
  handle.onkeydown=event=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
    event.preventDefault();event.stopPropagation();
    const current=Number(handle.getAttribute('aria-valuenow')),step=event.shiftKey?10:1;
    wipe(event.key==='Home'?0:event.key==='End'?100:
      current+(['ArrowLeft','ArrowDown'].includes(event.key)?-step:step),true);
  };
  $('date-dock').onkeydown=event=>{
    if(event.defaultPrevented||event.ctrlKey||event.altKey||event.metaKey||event.target.matches('input,select'))return;
    if(event.key===' '&&event.target.matches('button'))return;
    shortcuts(event);
  };
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&sheetLevel){showSheet(0);$('sheet').focus();}
    const menu=event.target.closest?.('.atlas-more[open]')??root.querySelector('.atlas-more[open]');
    if(event.key==='Escape'&&menu){
      event.preventDefault();menu.open=false;menu.querySelector('summary').focus();
    }
  });

  const simulationTools=simulationView?createAtlasSimulationUI():null;
  let scaleGrid;
  function updateScale(){
    if(!scaleGrid?.affine)return;
    const [a,, ,d]=scaleGrid.affine,gridWidth=scaleGrid.shape[1],px=stack.getBoundingClientRect().width;
    if(!px)return;
    const mPerPixel=Math.hypot(a,d)*gridWidth/px;
    const target=mPerPixel*Math.min(95,px/5),power=10**Math.floor(Math.log10(target));
    const length=[5,2,1].map(n=>n*power).find(n=>n<=target)??power;
    $('scale').style.setProperty('--scale-width',length/mPerPixel+'px');
    $('scale').textContent=length>=1000?length/1000+' km':length+' m';
  }
  if(typeof ResizeObserver==='function')new ResizeObserver(updateScale).observe(stack);
  function render(c,o,s,pair,pairGrid,kind,options,edition){
    for(const button of studies)button.setAttribute('aria-pressed',String(s.case===button.dataset.study));
    for(const button of layerButtons){
      const id=button.dataset.layer,enabled=options.includes(id);
      button.setAttribute('aria-pressed',String(s.layer===id));button.setAttribute('aria-disabled',String(!enabled));
      button.tabIndex=id===s.layer||!enabled?0:-1;
      button.title=enabled?atlasLayerHelp[id]:simulationView?'Coherence is available in the Atlas. This tool plays intensity visits.':'Needs an admitted radar pair.';
      if(id==='coherence'&&enabled)button.title+=' · '+c.pairs.length+' admitted pair endings';
    }
    const ordinal=c.observations.indexOf(o)+1,coherence=s.layer==='coherence';
    const sceneDate=coherence?pair.dates.map(atlasShortDate).join(' ↔ ')+' · UTC':
      atlasShortDate(s.date)+' '+iso(s.date).slice(0,4)+' · UTC · '+ordinal+'/'+c.observations.length;
    $('map-date').textContent=coherence?'Coherence · '+sceneDate:
      !simulationView&&s.terrain==='off'?$('scene').textContent+' · '+ordinal+'/'+c.observations.length+' visits':sceneDate;
    $('map-date').title=coherence?'Admitted pair endpoints':'Recorded visit '+ordinal+' of '+c.observations.length;
    $('wipe-flags').hidden=coherence||simulationView||s.terrain==='on';
    $('wipe-ref').textContent='Reference · '+atlasShortDate(c.reference);
    $('wipe-now').textContent='Selected · '+atlasShortDate(s.date);
    $('reference-pane-label').textContent=$('wipe-ref').textContent;
    $('selected-pane-label').textContent=$('wipe-now').textContent;
    handle.hidden=coherence||simulationView||s.terrain==='on';
    $('footprint-tool').hidden=portable;
    $('footprint-tool').disabled=coherence||s.terrain==='on'||simulationView&&kind!=='radar';
    $('outline-key').hidden=coherence||s.terrain==='on';
    $('north').hidden=$('scale').hidden=s.terrain==='on';
    const nextGrid=coherence?pairGrid:c.grid;
    const resolution=$('map-resolution');
    resolution.hidden=s.terrain==='on'||!nextGrid?.affine;
    if(!resolution.hidden){
      const [a,b,,d,e]=nextGrid.affine;
      const x=Math.hypot(a,d),y=Math.hypot(b,e);
      const spacing=x===y?x:x+' × '+y;
      resolution.textContent='Native grid · 1 px ≈ '+spacing+' m · display preview';
    }
    if(scaleGrid!==nextGrid){scaleGrid=nextGrid;updateScale();}
    const chip=$('edition');
    chip.textContent=standalone?'Offline · saved footprints':hosted?'Static preview · saved footprints':'Full local · native measurements';
    chip.title=edition.label;
    $('observations-tab').setAttribute('aria-current',simulationView?'false':'page');
    if(simulationTools){
      $('modeled-badge').hidden=false;
      simulationTools.render(c,kind);
    }
  }
  return {render,showTab,exitBaseline(){simulationTools?.restore();},revealTour(){if(matchMedia('(max-width:1279px)').matches)showSheet(1);}};
}

function createAtlasSimulationUI(){
  const $=atlasNode;
  const controls=$('sim-inspector'),defaults=new Map();
  const group={surge:['sim-stage-level','sim-view'],slope:['sim-m','sim-kh','sim-cohesion','sim-friction','sim-depth','sim-weight','sim-view'],
    bank:['bank-multiplier','bank-cycles'],orbit:['orbit-angle','orbit-look','orbit-band','orbit-motion'],
    radar:['radar-moisture','radar-water','radar-canopy']};
  let current='',lastCase='',baseline=null;
  const input=id=>$(id);
  const apply=values=>{
    for(const [id,value] of Object.entries(values)){
      const field=input(id);
      if(!field||value==null)continue;
      field.value=String(value);
      field.dispatchEvent(new Event('input',{bubbles:true}));
      field.dispatchEvent(new Event('change',{bubbles:true}));
    }
  };
  const snapshot=()=>Object.fromEntries(group[current].map(id=>[id,input(id).value]));
  const defaultFor=id=>id==='sim-view'?(current==='surge'?'hh':'terrain'):
    id==='orbit-angle'?(input(id).dataset.baseline||input(id).defaultValue):
    input(id).defaultValue||input(id).querySelector('option[selected]')?.value||input(id).options?.[0]?.value;
  for(const [id,unit] of Object.entries(atlasLabUnits)){
    const field=input(id);
    if(!field)continue;
    defaults.set(id,field.defaultValue);
    const range=atlasElement('div'),bounds=atlasElement('span',
      field.min+'–'+field.max+(unit?' '+unit:''));
    const reset=atlasElement('button','Reset');
    reset.type='button';
    reset.setAttribute('aria-label','Reset '+field.labels?.[0]?.textContent.trim().replace(/\s+/g,' '));
    reset.onclick=()=>{
      apply({[id]:id==='orbit-angle'?defaultFor(id):defaults.get(id)});
      $('sim-input-note').textContent='Control reset to its starting assumption.';
    };
    range.className='atlas-range-bounds';range.append(bounds,reset);
    field.closest('label')?.after(range);
    if(field.type==='range'&&unit)field.addEventListener('input',()=>field.setAttribute('aria-valuetext',field.value+' '+unit));
  }
  $('sim-explain').onclick=()=>{
    const panel=$(['surge','slope'].includes(current)?'simulation':current+'-lab');
    const details=[...panel.querySelectorAll('details')].find(d=>d.firstElementChild?.textContent==='Model and limits');
    if(details){details.open=true;details.firstElementChild.focus();details.scrollIntoView({block:'nearest'});}
  };
  $('sim-preset').onclick=()=>{
    const preset=atlasLabAssumptions[current];
    if(preset.button)$(preset.button).click();else apply(preset.values);
    $('sim-input-note').textContent='Applied example assumptions for '+atlasLabLabels[current]+'.';
  };
  $('sim-reset').onclick=()=>{
    baseline=null;$('sim-baseline').setAttribute('aria-pressed','false');
    apply(Object.fromEntries(group[current].map(id=>[id,defaultFor(id)])));
    $('sim-input-note').textContent='Starting assumptions restored.';
  };
  function restore(){
    if(!baseline)return;
    apply(baseline);baseline=null;
    $('sim-baseline').setAttribute('aria-pressed','false');
    $('sim-input-note').textContent='Scenario assumptions restored.';
  }
  $('sim-baseline').onclick=()=>{
    if(baseline)restore();
    else{
      baseline=snapshot();
      apply(Object.fromEntries(group[current].map(id=>[id,defaultFor(id)])));
      $('sim-baseline').setAttribute('aria-pressed','true');
      $('sim-input-note').textContent='Showing starting assumptions. Select Compare baseline again to restore the scenario.';
    }
  };
  return {restore,render(c,kind){
    if(kind!==current||lastCase!==c.case){
      baseline=null;$('sim-baseline').setAttribute('aria-pressed','false');
      current=kind;lastCase=c.case;
      const dateAware=['surge','bank','radar'].includes(kind);
      $('sim-input-note').textContent=dateAware?'Date-aware comparison · recorded radar updates on playback.':'Fixed model inputs · recorded radar updates on playback.';
    }
    $('sim-preset').textContent=atlasLabAssumptions[kind].label+' · preset';
    $('active-tool').textContent=atlasLabLabels[kind];
    for(const key of Object.keys(atlasLabLabels)){
      const here=key==='radar'||key==='bank'&&c.case==='jamuna_river'||
        key==='surge'&&c.country==='Bangladesh'||['orbit','slope'].includes(key)&&c.country==='Nepal';
      const button=$('launch-'+key);
      button.setAttribute('aria-disabled',String(!here));
      button.title=here?'Available in this study window':key==='bank'?'Choose the Jamuna study window':
        key==='surge'?'Choose Jamuna or Tanguar Haor':'Choose Kathmandu or Rasuwa–Nuwakot';
      button.setAttribute('aria-description',button.title);
    }
    controls.dataset.tool=kind;
  }};
}
