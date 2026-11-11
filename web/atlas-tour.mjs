import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {atlasMakeState} from './atlas-contract.mjs';
import {selection,iso} from './atlas-state.mjs';
import {atlasSignedDb} from './atlas-chronology.mjs';

const atlasChapters=[
  {id:'river',caseId:'jamuna_river',observationId:'acq_20260829T232132',footprint:'Frozen reference: target geographic',layer:'hh',lens:'river',
    question:'Which river signatures recur at the same place?',next:'Check the dated optical match and ask for a bank survey before attributing change to migration.'},
  {id:'wetland',caseId:'tanguar_wetland',observationId:'acq_20260829T232132',footprint:'Frozen reference: target geographic',layer:'hv',lens:'wetland',
    question:'How did the wetland’s radar return change?',next:'Compare the channels and check a dated water-depth or habitat record.'},
  {id:'persist',caseId:'nepal_surface',observationId:'acq_20260912T233918',footprint:'Previously tracked 1.99-hectare zone',layer:'hh',lens:'surface',
    checkpoints:['acq_20260831T233918','acq_20260912T233918','acq_20261018T233918'],
    question:'Did the footprint return to its reference?',next:'Check field evidence or a dated event inventory before assigning a cause.'},
  {id:'corridor',caseId:'nepal_impact_corridor',observationId:'acq_20260912T233918',footprint:'Preliminary mapped impact footprint inside this crop',layer:'coherence',lens:'surface',
    question:'How did pair similarity change in the corridor?',next:'Compare the dated GUNW pairs and check independent observations on the same footprint.'}
];

export function atlasChapter(records,catalog,index){
  const ch=atlasChapters[index],c=catalog[ch.caseId];
  const o=c.observations.find(v=>v.id===ch.observationId),p=c.footprints.find(v=>v.label===ch.footprint);
  if(!o||!p)throw Error('The recorded observation or footprint for this chapter is unavailable.');
  const view=selection(records,{case:c.caseId,date:o.utc,layer:ch.layer,lens:ch.lens,profile:p.ordinal,split:ch.layer==='coherence'?0:50});
  atlasMakeState(catalog,view);
  const record=records[c.caseId],pSeries=record.profiles[p.ordinal].series,k=ch.layer;
  const row=pSeries[c.observations.indexOf(o)];
  const pair=c.pairs.find(p=>p.secondId===o.id);
  const measured=ch.layer==='coherence'&&pair?'HH coherence compares '+iso(pair.startUtc)+' and '+iso(pair.endUtc)+' on the admitted 20 m grid. Open Context to compare with the earlier pair.':'On '+iso(o.utc)+', '+k.toUpperCase()+' changed '+atlasSignedDb(row[k+'_successive'])+' from the preceding visit and '+atlasSignedDb(row[k+'_reference'])+' from the reference.';
  const checkpoints=(ch.checkpoints??[]).flatMap(id=>{
    const i=c.observations.findIndex(visit=>visit.id===id);
    if(i<=0||!Number.isFinite(pSeries[i][k+'_reference'])||!Number.isFinite(pSeries[i][k+'_successive']))return [];
    return [{date:c.observations[i].utc,previous:c.observations[i-1].utc,
      recent:pSeries[i][k+'_successive'],reference:pSeries[i][k+'_reference']}];
  });
  return {...ch,view,measured,reference:record.reference,checkpoints};
}

export function createAtlasTour({records,catalog,current,apply,prepare,reveal}){
  const $=atlasNode;let manual=null,chapter=-1,observer=null,checkpointButtons=[];
  const stops=[...document.querySelectorAll('#atlas [data-story]')];
  let returnFocus;
  if(document.querySelector){
    const studyImages=[...document.querySelectorAll('#at-studies img')];
    stops.forEach((button,j)=>{
      if(studyImages[j])button.prepend(studyImages[j].cloneNode());
    });
    $('tour-progress').replaceChildren(...atlasChapters.map((ch,j)=>{
      const button=atlasElement('button',String(j+1));
      button.type='button';button.setAttribute('aria-label','Chapter '+(j+1)+' · '+ch.question);
      button.onclick=()=>show(j);
      return button;
    }));
    $('tour-start').onclick=()=>{
      returnFocus=$('tour-menu').querySelector('summary');
      show(0);
    };
  }
  function sync(){
    const s=current();
    for(const {button,view} of checkpointButtons){
      const selected=!s.native&&s.case===view.case&&s.profile===view.profile&&s.layer===view.layer&&s.date===view.date;
      button.setAttribute('aria-pressed',String(selected));
    }
  }
  function showCheckpoints(ch){
    $('tour-visits').hidden=!ch.checkpoints.length;
    $('tour-reference').textContent=ch.footprint+' · HH reference '+iso(ch.reference)+' UTC';
    checkpointButtons=ch.checkpoints.map(visit=>{
      const view={...ch.view,date:visit.date},button=atlasElement('button');
      button.type='button';
      button.append(atlasElement('strong',iso(visit.date)),
        atlasElement('small',atlasSignedDb(visit.recent)+' since '+iso(visit.previous)),
        atlasElement('small',atlasSignedDb(visit.reference)+' from reference'));
      button.onclick=()=>apply(view,'Kathmandu checkpoint · '+iso(visit.date)+' UTC');
      return {button,view};
    });
    $('tour-checkpoints').replaceChildren(...checkpointButtons.map(({button})=>button));
  }
  function show(index){
    if(index<0||index>=atlasChapters.length)return;
    const caseId=atlasChapters[index].caseId;
    if(!catalog[caseId]&&prepare){prepare(caseId,()=>show(index));return;}
    let ch;try{ch=atlasChapter(records,catalog,index);}catch(error){$('tour-answer').textContent=error.message;$('tour-panel').hidden=false;return;}
    manual??={...current()};
    chapter=index;
    $('tour-panel').hidden=false;
    if(document.querySelector)document.getElementById('atlas').dataset.tour='true';
    reveal?.();
    $('tour-step').textContent='Chapter '+(index+1)+' of '+atlasChapters.length;
    $('tour-question').textContent=ch.question;
    $('tour-answer').textContent=ch.measured;
    $('tour-next-check').textContent=ch.next;
    showCheckpoints(ch);
    $('tour-back').disabled=index===0;$('tour-next').disabled=index===atlasChapters.length-1;
    stops.forEach((b,j)=>b.setAttribute('aria-pressed',String(j===index)));
    Array.from($('tour-progress').children).forEach((button,j)=>button.setAttribute('aria-current',String(j===index)));
    apply(ch.view,'Guided visit '+(index+1)+' · '+ch.question);
  }
  function clear(){
    chapter=-1;manual=null;observer?.disconnect();observer=null;checkpointButtons=[];
    if(document.querySelector){
      delete document.getElementById('atlas').dataset.tour;
      $('chapters').open=false;
    }
    $('tour-panel').hidden=true;$('tour-scroll').checked=false;$('tour-scroll-stops').hidden=true;
    stops.forEach(b=>b.setAttribute('aria-pressed','false'));
  }
  stops.forEach((b,i)=>b.onclick=()=>{returnFocus=b;show(i);});
  $('tour-next').onclick=()=>show(chapter+1);
  $('tour-back').onclick=()=>show(chapter-1);
  $('tour-exit').onclick=()=>{
    const previous=manual;clear();
    if(previous)apply(previous,'Guided visit ended. Your previous selection is restored.');
    (returnFocus??stops[0])?.focus?.();
  };
  $('tour-scroll').onchange=()=>{
    observer?.disconnect();observer=null;
    const on=$('tour-scroll').checked&&typeof IntersectionObserver!=='undefined';
    $('tour-scroll-stops').hidden=!on;
    if(!on)return;
    observer=new IntersectionObserver(entries=>{
      for(const entry of entries)if(entry.isIntersecting){
        const next=Number(entry.target.dataset.tourChapter);
        if(next!==chapter)show(next);
      }
    },{rootMargin:'-35% 0px -45% 0px'});
    document.querySelectorAll('#atlas [data-tour-chapter]').forEach(n=>observer.observe(n));
  };
  return {clear,sync,show,active:()=>chapter>=0};
}

export function createAtlasSpotlight({tour,simulationView,showTab}){
  if(!document.querySelector)return;
  const $=atlasNode,menu=$('tour-menu');
  menu.hidden=simulationView;
  if(simulationView)return;
  let cutTimer=null;
  const exportButton=$('presenter-export'),exportStatus=$('presenter-status');
  const duration=30;
  const spotlight=[
    [0,1,'context','Find a dated optical check'],
    [7,0,'evidence','Follow the Jamuna'],
    [12,1,'context','Read the Tanguar radar record'],
    [17,2,'evidence','Compare recent change and persistence'],
    [26,2,'evidence','Export and share the evidence']
  ];
  function stopCut(){
    if(cutTimer!==null)clearInterval(cutTimer);
    cutTimer=null;$('cut-stop').hidden=true;
    exportButton.hidden=true;exportStatus.textContent='';
  }
  function activate(index,tab){
    tour.show(index);showTab(tab);
    const stage=$('stage'),box=stage.getBoundingClientRect();
    if(box.top<0||box.top>innerHeight-150){
      stage.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
    }
  }
  function startCut(){
    stopCut();$('presenter').hidden=false;
    let step=-1;
    const start=performance.now();
    const tick=()=>{
      const elapsed=(performance.now()-start)/1000;
      if(elapsed>=duration){
        stopCut();exportButton.hidden=false;
        $('cut-clock').textContent='Tour complete · export the investigation';return;
      }
      const index=spotlight.findLastIndex(([second])=>second<=elapsed);
      const [,chapter,tab,title]=spotlight[index];
      if(index!==step){step=index;activate(chapter,tab);exportButton.hidden=index!==spotlight.length-1;}
      const end=spotlight[index+1]?.[0]??duration;
      $('cut-clock').textContent=title+' · '+Math.max(0,Math.ceil(end-elapsed))+' s';
    };
    $('cut-stop').hidden=false;
    cutTimer=setInterval(tick,200);tick();
  }
  exportButton.onclick=()=>{
    $('export-toast').textContent='';
    $('export').click();
    exportStatus.textContent=$('export-toast').textContent||'See the Evidence panel for the export status.';
  };
  $('spotlight').onclick=startCut;
  $('cut-stop').onclick=()=>{stopCut();$('cut-clock').textContent='Timed tour stopped.';};
  $('tour-exit').addEventListener('click',()=>{stopCut();$('presenter').hidden=true;});
  for(const button of menu.querySelectorAll('button'))button.addEventListener('click',()=>{
    menu.open=false;
    menu.querySelector('summary').focus();
  });
  document.addEventListener('keydown',event=>{
    if(event.defaultPrevented||event.altKey||event.metaKey||event.ctrlKey||
      event.target.matches('input,textarea,select,[contenteditable=true]'))return;
    if(event.key==='Escape'&&tour.active()){$('tour-exit').click();return;}
    if(tour.active()&&/^[1-4]$/.test(event.key)){
      event.preventDefault();stopCut();activate(Number(event.key)-1,'evidence');
    }
  });
}
