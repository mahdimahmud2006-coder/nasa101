import {atlasMakeState,atlasVersionedHash,atlasReadHash} from './atlas-contract.mjs';
import {labels,lensLabels,iso,pairAt,indices,nativeSelection,selection,atlasEdition,atlasStore} from './atlas-state.mjs';
import {observationPacket,guidance} from './atlas-evidence.mjs';
import {atlasNode,atlasElement,atlasOptions} from './atlas-dom.mjs';
import {renderAtlasTimeline,renderAtlasChronology,createAtlasDateDock} from './atlas-timeline.mjs';
import {atlasVisitLabel,atlasDefaultThreshold,atlasTraceSupport,atlasComparison,atlasChronology} from './atlas-chronology.mjs';
import {atlasCompatibility,renderAtlasCompatibility} from './atlas-compatibility.mjs';
import {renderAtlasContext} from './atlas-context.mjs';
import {renderAtlasDiscovery} from './atlas-discovery.mjs';
import {renderAtlasQuality} from './atlas-quality.mjs';
import {createAtlasScenarios} from './atlas-scenarios.mjs';
import {createAtlasSimulations} from './atlas-simulations.mjs';
import {createAtlasLabs} from './atlas-labs.mjs';
import {renderAtlasInspector,renderAtlasAnswer} from './atlas-inspector.mjs';
import {renderAtlasPairs} from './atlas-pairs.mjs';
import {renderAtlasFieldReview} from './atlas-review.mjs';
import {createAtlasDrape,createAtlasMap,createAtlasFrames,renderAtlasLegend} from './atlas-map.mjs';
import {createAtlasProbe} from './atlas-data.mjs';
import {createAtlasTour,createAtlasSpotlight} from './atlas-tour.mjs';
import {atlasHostedCase,atlasHostedLoader} from './atlas-hosted.mjs';
import {atlasCreateDossier,atlasDossierSelection,atlasVerifyDossier,atlasFieldSurvey,createAtlasDossierControls,atlasDossierMaxBytes,atlasDossierSchema} from './atlas-dossier.mjs';
import {createAtlasPresentation} from './atlas-ui.mjs';
export {selection,nativeSelection,hashOf} from './atlas-state.mjs';
export {observationPacket} from './atlas-evidence.mjs';
const atlasLabKinds=['surge','bank','slope','orbit','radar'];
function atlasCountryCase(search){
  const country=new URLSearchParams(search).get('country');
  return country==='nepal'?'nepal_surface':country==='bangladesh'?'jamuna_river':null;
}
function mount(records,catalog,hosted=null){
  const $=atlasNode,el=atlasElement,options=atlasOptions;
  const standalone=document.body.dataset.portable==='yes',portable=standalone||!!hosted,disclosure={thermal:false};
  const params=new URLSearchParams(location.search),linkedLab=params.get('lab');
  const simulationView=!standalone&&(params.get('view')==='simulations'||atlasLabKinds.includes(linkedLab));
  let simulationKind='';
  const dateSpeech=new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'long',year:'numeric',timeZone:'UTC'});
  for(const c of Object.values(records))if(c.manifest_sha256!==catalog[c.case]?.manifestSha256)throw Error('The atlas identity catalog does not match the saved record.');
  const countryCase=atlasCountryCase(location.search);
  const store=atlasStore(records,{case:countryCase??(hosted?Object.keys(records)[0]:undefined),split:simulationView?0:50});
  let timer=null,s=store.get(),initialNote='',initialNative='',liveProfile=null,probeStatus='',threshold=atlasDefaultThreshold,stateRevision=0;
  try{
    const restored=atlasReadHash(catalog,location.hash);
    if(restored){initialNative=restored.native;s=store.restore({...restored,native:''});}
  }
  catch(error){initialNote='Link not opened: '+error.message+' Showing the default view.';}
  const probe=createAtlasProbe({catalog});
  const scenarios=createAtlasScenarios({portable,changed:()=>render()});
  const drape=createAtlasDrape(set,hosted?.terrain);
  const active=()=>records[s.case];
  const drawTerrain=()=>{
    const c=active(),o=c.observations[idx()],r=c.observations.find(v=>v.timestamp===c.reference);
    drape(c,o,r,s,labs.overlay()??simulations.overlay());
  };
  const simulations=createAtlasSimulations({standalone,
    manifestFor:id=>hosted?hosted.entries[id]?.simulation:'/atlas-simulations/'+id+'.json',
    redraw:()=>{if(s.terrain==='on')drawTerrain();},
    showMap:plan=>{
      if(s.layer==='coherence'||plan&&s.terrain==='on')set({layer:'hh',...(plan?{terrain:'off'}:{})});
      const map=$('map');map.focus({preventScroll:true});map.scrollIntoView({block:'start'});
    }});
  const labs=createAtlasLabs({
    manifestFor:id=>hosted?hosted.entries[id]?.simulation:'/atlas-simulations/'+id+'.json',
    redraw:()=>{if(s.terrain==='on')drawTerrain();},
    chooseVisit,
    focusMap:(mode,focus)=>{
      const terrain=mode==='terrain'?'on':'off';
      if(s.layer==='coherence'||s.terrain!==terrain)set({layer:s.layer==='coherence'?'hh':s.layer,terrain});
      if(focus){const map=$('map');map.focus({preventScroll:true});map.scrollIntoView({block:'start'});}
    }
  });
  const fieldLocation=()=>s.native?liveProfile?.field_location:catalog[s.case].footprints[s.profile].fieldLocation;
  const idx=()=>active().observations.findIndex(o=>o.timestamp===s.date);
  const playLabel=()=>simulationView?'Play dates':s.layer==='coherence'?'Play pairs':'Play visits';
  const stop=()=>{if(timer!==null)clearInterval(timer);timer=null;$('play').textContent=playLabel();$('play').setAttribute('aria-pressed','false');};
  function set(changes,{keepPlaying=false,announce='',replace=false,measured=null}={}){
    stateRevision++;
    if(!keepPlaying)stop();
    const requested={...s,...changes};
    if(simulationView&&requested.layer==='coherence')requested.layer='hh';
    if(Object.hasOwn(changes,'native')||Object.hasOwn(changes,'profile')||Object.hasOwn(changes,'case')){
      resetProbe();
      liveProfile=measured;
    }
    s=store.update(requested);
    if(requested.date && iso(requested.date)!==iso(s.date))announce='No '+labels[s.layer]+' frame for '+iso(requested.date)+'; showing the recorded '+iso(s.date)+' frame.';
    // replaceState is restricted by some file: URL implementations. Hash-only
    // navigation still restores the exact recorded selection on those hosts.
    writeHash(replace||keepPlaying);
    render(announce);
  }
  function writeHash(replace=true){
    const hash=atlasVersionedHash(atlasMakeState(catalog,s));
    handledHash=hash;
    if(location.hash!==hash){try{const method=!replace&&history.pushState?'pushState':'replaceState';history[method](null,'',hash);}catch{location.hash=hash;}}
  }
  function resetProbe(){
    probe.cancel();
    probeStatus='';
  }
  function showProbeStatus(message){
    probeStatus=message;
    $('probe-help').textContent=message;
  }
  async function measure(native,{replace=false,onAccept}={}){
    stop();
    $('probe-panel').open=true;
    if(portable){
      render('This link opens a native footprint. Showing a saved footprint in the offline edition.');
      return;
    }
    showProbeStatus('Checking the footprint. The inspector still shows the selected measurements.');
    let profile;
    try{
      profile=await probe.measure(active(),native);
    }catch(error){
      showProbeStatus(error.message+' The previous footprint is still selected.');
      if(replace)writeHash();
      return;
    }
    if(!profile)return;
    onAccept?.();
    set({native},{replace,measured:profile});
  }
  const map=createAtlasMap({active,current:()=>s,set,portable,compareVisits:!simulationView,normalize:nativeSelection,measure,resetProbe,showProbeStatus,
    canMeasure:()=>!simulationView||simulationKind==='radar',
    pickSimulation:point=>labs.pick(point)||simulations.pick(point)});
  const frames=createAtlasFrames({local:!portable,entryPreview:hosted?.entryPreview,onGeometry:map.updateGeometry});
  const drawDateDock=createAtlasDateDock(chooseVisit);
  const ui=createAtlasPresentation({portable,standalone,hosted,simulationView,wipe:updateWipe,shortcuts:timelineKey});
  function paintWipe(split){
    const c=active(),o=c.observations[idx()],r=c.observations.find(v=>v.timestamp===c.reference);
    frames(c,o,r,{...s,split},pairAt(c,idx()));
    $('divider').hidden=s.layer==='coherence'||split===0||split===100;
    $('split').value=split;$('split').setAttribute('aria-valuetext',split+' percent reference');
    $('share').textContent=split+'%';$('image-stack').style.setProperty('--split',split+'%');
    $('wipe-handle').setAttribute('aria-valuenow',String(split));
    $('wipe-handle').setAttribute('aria-valuetext',split+' percent reference');
  }
  function updateWipe(value,commit){
    if(s.layer==='coherence')return;
    const split=Math.max(0,Math.min(100,Math.round(Number(value)||0)));
    paintWipe(split);
    if(commit&&s.split!==split){
      stateRevision++;stop();s=store.update({...s,split});writeHash(true);
      map.updateGeometry();
      if(s.terrain==='on')drawTerrain();
    }
  }
  function syncWorkspaceLinks(c){
    if(standalone)return;
    const hash=atlasVersionedHash(atlasMakeState(catalog,s));
    $('simulations-tab').href='?view=simulations'+hash;
    $('observations-tab').href=simulationView?'?country='+c.country.toLowerCase()+hash:'./';
    if(!simulationView||!simulationKind)return;
    const address=new URL(location.href);
    if(address.searchParams.get('lab')!==simulationKind){
      address.searchParams.set('lab',simulationKind);
      history.replaceState(null,'',address.href);
    }
  }
  function render(note=''){
    const c=active(),i=idx(),o=c.observations[i],r=c.observations.find(v=>v.timestamp===c.reference),p=liveProfile??c.profiles[s.profile],pair=pairAt(c,i),co=s.layer==='coherence',g=guidance(c,s);
    const meta=catalog[c.case],gaps=meta.acquisitionGaps??[];
    $('field-export').disabled=!fieldLocation();
    const support=atlasTraceSupport(p,s.native?p.footprint_pixels:meta.footprints[s.profile].footprintPixels);
    const recent=atlasComparison(c,p,i,'successive',support,gaps);
    const reference=atlasComparison(c,p,i,'reference',support,gaps);
    const cases=hosted?Object.entries(hosted.entries).map(([id,c])=>[id,c.label]):
      Object.values(records).map(c=>[c.case,c.country+' · '+c.title.split(' · ')[0]]);
    options($('case'),cases,s.case);
    const edition=atlasEdition(catalog,c.case,portable);
    syncWorkspaceLinks(c);
    $('edition').textContent=hosted?'Saved observations and footprints · static edition':edition.label;
    options($('lens'),edition.lenses.map(k=>[k,lensLabels[k]]),s.lens);
    options($('profile'),[...c.profiles.map((p,j)=>[j,p.label]),...(s.native?[['native','Selected native footprint']]:[])],s.native?'native':s.profile);
    $('probe-panel').hidden=portable;
    $('probe-help').textContent=probeStatus||(liveProfile?(p.valid_pixels?'Native footprint measured.':'No pixels are valid across all recorded visits.'):'Grid: '+c.grid.shape.join(' × ')+'. Draw a polygon or enter a row and column for a fixed neighborhood.');
    const allowedLayers=edition.layers.filter(k=>!simulationView||k!=='coherence');
    options($('layer'),allowedLayers.map(k=>[k,labels[k]]),s.layer);
    options($('date'),indices(c,s.layer).map(j=>[c.observations[j].timestamp,
      co?pairAt(c,j).dates.map(iso).join(' → '):atlasVisitLabel(c,c.observations[j])]),s.date);
    $('date-label').textContent=co?'Coherence pair (UTC)':'Recorded visit';
    $('date').setAttribute('aria-label',co?'Coherence pair (UTC)':'Recorded visit');
    $('prev').setAttribute('aria-label',co?'Previous coherence pair':'Previous observed visit');
    $('next').setAttribute('aria-label',co?'Next coherence pair':'Next observed visit');
    $('prev').title=co?'Previous coherence pair':'Previous recorded visit';
    $('next').title=co?'Next coherence pair':'Next recorded visit';
    if(timer===null)$('play').textContent=playLabel();
    $('place').textContent=c.country+' / '+c.title;$('scene').textContent=labels[s.layer];$('question').textContent=g.question;
    paintWipe(s.split);
    for(const k of ['less','more','split'])$(k).disabled=co;
    $('caption').textContent=co?'Pair similarity · GUNW · 20 m grid.':
      simulationView?'Observed '+labels[s.layer]+' · '+iso(s.date)+' UTC.':
      s.layer==='fraction'?'HV divided by total HH and HV power.':'Drag the divider to compare visits at the same location.';
    $('status').textContent=note||(co?c.pairs.length+' measured pairs. '+pair.dates.map(date=>dateSpeech.format(new Date(date))).join(' to ')+' UTC.':
      'Visit '+(i+1)+' of '+c.observations.length+', '+dateSpeech.format(new Date(s.date))+' UTC. '+labels[s.layer]+'.');
    $('notice').hidden=!note||!/unavailable|could not|not opened|no .* frame|offline edition/i.test(note);
    $('notice').textContent=$('notice').hidden?'':note;
    tour.sync();
    renderAtlasInspector({c,i,o,p,reference,recent,pair,co,g,s,portable,set});
    renderAtlasAnswer(p,meta,s,o,recent,reference);
    drawDateDock(c,p,meta,s,gaps,i);
    renderAtlasCompatibility(atlasCompatibility(meta,p,s.native?null:s.profile,o.observation_id));
    $('guide-current').textContent=labels[s.layer]+' · '+(co?'Pair '+pair.dates.map(iso).join(' to ')+'. Use recorded pair endpoints.':'Selected '+iso(s.date)+'; reference '+iso(c.reference)+'. Use the same footprint to compare visits.');
    if(s.terrain==='on')$('caption').textContent+=' Terrain overview · NASADEM at 1× vertical scale · '+s.bearing+'° bearing. Display colours sampled on a coarse mesh; inspect native measurements for analysis.';
    renderAtlasLegend(c,s.layer);
    const reviewLocation=s.lens==='surface'?null:meta.footprints[s.profile].review?.location;
    const pairGrid=co?meta.pairs.find(v=>v.secondId===o.observation_id)?.grid:null;
    map.render(c,s,p.native_support,reviewLocation,pairGrid);
    ui.render(c,o,s,pair,pairGrid,simulationKind,allowedLayers,edition);
    simulations.update(c,o,s,simulationView&&(simulationKind==='surge'||simulationKind==='slope'));labs.update(c,o,s,p,meta);
    if(simulationView){
      $('layout').dataset.simulationTool=simulationKind;
      labs.open(simulationKind);
      for(const kind of atlasLabKinds)$('launch-'+kind).setAttribute('aria-pressed',String(kind===simulationKind));

    }
    drawTerrain();renderAtlasTimeline(c,p,i,support,gaps,chooseVisit);
    renderAtlasChronology(atlasChronology(c,p,i,threshold),gaps);
    renderAtlasQuality(c,meta,o,p,s,portable);
    renderAtlasPairs(meta,o,s,p);
    renderAtlasFieldReview(c,meta,p,s,set,()=>$('export').click());
    const scenario=scenarios.select(s,o,meta.environment?.scenario);
    renderAtlasContext(c,o,p,s,set,disclosure,meta,portable,scenario,scenarios.retry);
    if(!simulationView)renderAtlasDiscovery(c,o.timestamp,co?pair:null);
    document.getElementById('atlas').dataset.ready='yes';
  }
  function chooseVisit(id){
    const c=active(),i=c.observations.findIndex(o=>o.observation_id===id);
    if(i<0)return;
    const useIntensity=s.layer==='coherence'&&!pairAt(c,i);
    set({date:c.observations[i].timestamp,...(useIntensity?{layer:'hh'}:{})},
      {announce:useIntensity?'Showing HH intensity. No coherence pair ends on this visit.':''});
  }
  function move(delta,loop=false){
    const c=active(),available=indices(c,s.layer),j=available.indexOf(idx())+delta;
    if(!loop&&(j<0||j>=available.length)){stop();return;}
    set({date:c.observations[available[(j+available.length)%available.length]].timestamp},{keepPlaying:timer!==null});
  }
  function prepareCase(id,apply){
    if(!hosted||Object.hasOwn(records,id)){apply();return;}
    stop();
    const revision=++stateRevision;
    $('status').textContent='Loading '+hosted.entries[id].label+'…';
    $('notice').hidden=false;$('notice').textContent=$('status').textContent;
    hosted.ensure(id).then(()=>{
      if(revision===stateRevision)apply();
    }).catch(error=>{if(revision===stateRevision)render(error.message+' The current view is still open.');});
  }
  function launchLab(kind){
    ui.exitBaseline?.();
    const nepal=active().country==='Nepal';
    const target=kind==='bank'||kind==='surge'&&nepal?'jamuna_river':
      kind==='orbit'&&!nepal?'nepal_impact_corridor':kind==='slope'&&!nepal?'nepal_surface':s.case;
    prepareCase(target,()=>{
      const changedCase=s.case!==target;
      simulationKind=kind;
      set({...(changedCase?{case:target,native:'',date:'',lens:'',profile:0}:{}),
        layer:s.layer==='coherence'?'hh':s.layer,split:0,terrain:kind==='orbit'||kind==='slope'?'on':'off'},{replace:true});
    });
  }
  $('case').onchange=()=>{
    ui.exitBaseline?.();
    const id=$('case').value;
    prepareCase(id,()=>{
      if(simulationView&&simulationKind!=='radar'){
        if(id.startsWith('nepal_')&&['bank','surge'].includes(simulationKind))simulationKind='slope';
        if(!id.startsWith('nepal_')&&(['orbit','slope'].includes(simulationKind)||id!=='jamuna_river'&&simulationKind==='bank'))simulationKind='surge';
      }
      set({case:id,native:'',date:'',lens:'',layer:'hh',profile:0,split:simulationView?0:50,
        ...(simulationView?{terrain:['slope','orbit'].includes(simulationKind)?'on':'off'}:{})});
    });
  };
  $('sort').onchange=()=>render();
  $('fit-jump').onclick=()=>{
    ui.showTab('evidence');
    const heading=$('fit-title');
    heading.focus({preventScroll:true});
    heading.scrollIntoView({block:'start'});
  };
  $('threshold').value=String(threshold);
  $('threshold').onchange=()=>{stateRevision++;threshold=Number($('threshold').value);render();};
  $('profile').onchange=()=>set({profile:$('profile').value,native:''});
  for(const k of ['date','lens','layer'])$(k).onchange=()=>set({[k]:$(k).value});
  $('split').oninput=()=>updateWipe($('split').value,true);
  $('mode').onclick=()=>set({terrain:s.terrain==='on'?'off':'on'});
  $('rotate').onclick=()=>set({bearing:(s.bearing+45)%360});
  $('less').onclick=()=>updateWipe(s.split-10,true);$('more').onclick=()=>updateWipe(s.split+10,true);
  $('prev').onclick=()=>{stop();move(-1,true);};$('next').onclick=()=>{stop();move(1,true);};
  function jumpFrame(edge){
    const c=active(),frames=indices(c,s.layer),index=edge==='first'?frames[0]:frames.at(-1);
    set({date:c.observations[index].timestamp});
  }
  $('first').onclick=()=>jumpFrame('first');$('last').onclick=()=>jumpFrame('last');
  function startPlayback(restart=true){
    const c=active(),a=indices(c,s.layer);
    if(restart&&idx()===a.at(-1))set({date:c.observations[a[0]].timestamp});
    const speed=Number($('speed').value)||1;
    timer=setInterval(()=>{
      if(simulationView&&($('current').dataset.ready==='loading'||$('drape').dataset.ready==='loading'||!simulations.ready()||!labs.ready()))return;
      move(1,$('loop').checked===true);
    },1200/speed);
    $('play').textContent='Pause';$('play').setAttribute('aria-pressed','true');
  }
  $('play').onclick=()=>{if(timer!==null)stop();else startPlayback();};
  $('speed').onchange=()=>{if(timer!==null){stop();startPlayback(false);}};
  function timelineKey(event){
    const c=active(),key=event.key;
    if(key===' '){event.preventDefault();$('play').click();}
    else if(['ArrowLeft','ArrowRight','Home','End','r','R','[',']'].includes(key)){
      event.preventDefault();
      if(key==='ArrowLeft'||key==='ArrowRight'){stop();move(key==='ArrowLeft'?-1:1,true);}
      else if(key==='Home'||key==='End')jumpFrame(key==='Home'?'first':'last');
      else if(key==='r'||key==='R'){
        set({date:c.reference,...(s.layer==='coherence'&&!c.pairs.some(p=>p.dates[1]===c.reference)?{layer:'hh'}:{})});
      }else if(!simulationView&&c.pairs.length){
        const j=c.pairs.findIndex(pair=>pair.dates[1]===s.date);
        const next=j<0?(key==='['?c.pairs.length-1:0):(j+(key==='['?-1:1)+c.pairs.length)%c.pairs.length;
        set({layer:'coherence',date:c.pairs[next].dates[1]});
      }
    }
  }
  $('date-dock').tabIndex=0;
  const tour=createAtlasTour({records,catalog,current:()=>s,prepare:prepareCase,reveal:()=>ui.revealTour?.(),apply:(next,note)=>{
    // The tour state is complete. Clear prior context/native fields before applying it.
    const {native,...view}=next;
    set({scenario:'',scenarioRun:null,thermal:'',...view,native:''},{announce:note});
    if(native)reopenNative(native);
  }});
  createAtlasSpotlight({tour,simulationView,showTab:ui.showTab});
  const makeDossier=createAtlasDossierControls({
    makePacket:notes=>atlasCreateDossier(records,s,liveProfile,catalog,threshold,scenarios.get(),notes),
    async reopen(saved,currentFile){
      const revision=stateRevision;
      if(hosted&&saved.schema===atlasDossierSchema)await hosted.ensure(saved.contract?.caseId);
      if(!currentFile()||revision!==stateRevision)throw Error('The selection changed while verifying. Reopen the dossier again.');
      const next=atlasDossierSelection(saved,catalog,portable);
      const c=records[next.case],o=c.observations.find(row=>row.timestamp===next.date);
      const model=catalog[next.case].environment?.scenario;
      const measured=next.native?await probe.measure(c,next.native):null;
      const modelResult=next.scenarioRun?await scenarios.replay(next,o,model):null;
      if(!currentFile()||revision!==stateRevision||next.native&&!measured)throw Error('The selection changed while verifying. Reopen the dossier again.');
      const savedThreshold=saved.chronology.rule.thresholdDb;
      const replay=atlasCreateDossier(records,next,measured,catalog,savedThreshold,modelResult);
      atlasVerifyDossier(saved,replay,catalog,next);
      stop();tour.clear();threshold=savedThreshold;
      $('threshold').value=String(threshold);
      $('dossier-notes').value=typeof saved.dossier?.review?.notes==='string'?saved.dossier.review.notes.slice(0,800):'';
      if(modelResult)scenarios.restore(next,o,model,modelResult);
      set({scenario:'',scenarioRun:null,thermal:'',native:'',...next},{measured,announce:'Reopened the verified dossier.'});
    }
  });
  function download(file,extension){
    if(file.size>atlasDossierMaxBytes){
      $('dossier-tools').open=true;$('dossier-status').textContent='This dossier exceeds 8 MiB. Try a smaller footprint.';return;
    }
    const url=URL.createObjectURL(file),a=el('a','');
    a.href=url;a.download='TerraPulse-'+s.case+'-'+iso(s.date)+extension;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),2000);return true;
  }
  $('export').onclick=()=>{
    const packet=makeDossier();
    if(packet&&download(new Blob([JSON.stringify(packet,null,2)],{type:'application/json'}),'.json'))showDossierCard(packet);
  };
  function showDossierCard(packet){
    if(!document.querySelector)return;
    const contract=packet.contract;
    const card=$('export-card'),description=$('export-description'),copy=$('copy-id'),toast=$('export-toast');
    const summary=active().title+' · '+iso(packet.selected_utc)+' · '+packet.footprint+' · '+packet.schema;
    description.textContent=summary;card.hidden=false;copy.hidden=true;
    toast.textContent='✓ Investigation dossier prepared for download.';
    if(!globalThis.crypto?.subtle)return;
    crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(contract))).then(buffer=>{
      if(description.textContent!==summary)return;
      const id=Array.from(new Uint8Array(buffer),byte=>byte.toString(16).padStart(2,'0')).join('').slice(0,12);
      description.textContent=summary+' · Evidence ID '+id;copy.hidden=!navigator.clipboard;
      copy.onclick=async()=>{
        try{await navigator.clipboard.writeText(id);toast.textContent='✓ Evidence ID copied.';}
        catch{toast.textContent='Copy the visible evidence ID manually.';}
      };
    }).catch(()=>{});
  }
  $('field-export').onclick=()=>{
    const packet=makeDossier();
    const feature=packet&&atlasFieldSurvey(packet,fieldLocation());
    if(feature)download(new Blob([JSON.stringify(feature,null,2)],{type:'application/geo+json'}),'-field-check.geojson');
  };
  function reopenNative(native){
    if(!portable)$('coords').value=native;
    measure(native,{replace:true});
  }
  let handledHash=location.hash;
  function readLocation(){
    const requestedHash=location.hash;
    if(requestedHash===handledHash)return;
    const caseId=hosted&&atlasHostedCase(requestedHash,hosted.entries);
    if(caseId&&!Object.hasOwn(records,caseId)){
      prepareCase(caseId,()=>{if(location.hash===requestedHash)readLocation();});return;
    }
    handledHash=requestedHash;
    try{
      const restored=atlasReadHash(catalog,location.hash);
      if(restored){
        stateRevision++;stop();tour.clear();resetProbe();liveProfile=null;
        s=store.restore({...restored,native:'',...(simulationView&&restored.layer==='coherence'?{layer:'hh'}:{})});
        render();
        if(restored.native)reopenNative(restored.native);
        else writeHash();
      }
    }catch(error){stop();render('Link not opened: '+error.message+' The current selection is unchanged.');}
  }
  window.addEventListener('hashchange',readLocation);
  window.addEventListener('popstate',readLocation);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  if(!standalone){
    document.getElementById('atlas').dataset.view=simulationView?'simulations':'observations';
    $(simulationView?'simulations-tab':'observations-tab').setAttribute('aria-current','page');
  }
  if(simulationView){
    document.getElementById('atlas-title').textContent='Simulations';
    $('intro').textContent='Choose a model, adjust its inputs and play the recorded dates on the map.';
    $('simulation-tools').hidden=false;$('tool-gallery').hidden=false;$('tool-gallery').open=!linkedLab;
    $('evidence-inspector').hidden=true;$('sim-inspector').hidden=false;
    $('radar-selection').append($('profile').parentElement,$('probe-panel'));
    for(const kind of atlasLabKinds)$('launch-'+kind).onclick=()=>{
      const button=$('launch-'+kind);
      if(button.getAttribute('aria-disabled')==='true'){$('sim-input-note').textContent=button.title+'.';return;}
      $('tool-gallery').open=false;launchLab(kind);
    };
    launchLab(atlasLabKinds.includes(linkedLab)?linkedLab:active().country==='Nepal'?'slope':'surge');
  }else render(initialNote);
  if(initialNative)reopenNative(initialNative);
  else if(!initialNote&&location.hash.startsWith('#atlas='))writeHash();
}
if(typeof document!=='undefined' && document.getElementById('atlas')){
  const bundle=document.getElementById('atlas-data'),identity=document.getElementById('atlas-identity');
  const configuration=document.getElementById('atlas-hosted-config');
  const fail=()=>{
    const message='Recorded visits could not be opened. Reload the Atlas or open the generated offline file.';
    atlasNode('status').textContent=message;
    atlasNode('notice').textContent=message;atlasNode('notice').hidden=false;
  };
  if(configuration){
    const hosted=atlasHostedLoader(JSON.parse(configuration.textContent));
    const requested=atlasHostedCase(location.hash,hosted.entries)??atlasCountryCase(location.search);
    hosted.ensure(requested??hosted.defaultCase).then(()=>mount(hosted.records,hosted.catalog,hosted)).catch(fail);
  }else if(bundle){try{mount(JSON.parse(bundle.textContent),JSON.parse(identity.textContent));}catch{fail();}}
  else Promise.all(['/atlas-record.json','/atlas-contract-records.json'].map(path=>fetch(path).then(res=>{
    if(!res.ok)throw Error('Atlas unavailable');
    return res.json();
  }))).then(([records,catalog])=>mount(records,catalog)).catch(fail);
}
