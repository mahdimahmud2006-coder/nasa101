import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {atlasShortDate,atlasVisitText} from './atlas-timeline.mjs';
import {atlasVisitLabel} from './atlas-chronology.mjs';
import {iso,fmt} from './atlas-state.mjs';
export function renderAtlasInspector({c,i,o,p,reference,recent,pair,co,g,s,portable,set}){
  const $=atlasNode,el=atlasElement;
    const supportText=reference.support;
    $('support').textContent=p.label+' · '+p.valid_pixels.toLocaleString()+
      (supportText.footprintPixels?' of '+supportText.footprintPixels.toLocaleString()+' native pixels ('+fmt(supportText.coverage*100,1)+'%)':' native pixels')+
      ' · '+fmt(p.area_km2,4)+' km².'+(p.boundary_area?' Drawn boundary: '+fmt(100*p.boundary_area.ellipsoidal_km2,3)+' ha on WGS84.':'');
    const [hh,hv,recentHH,recentHV]=atlasVisitText(reference,recent);
    $('base').textContent=hh;$('recent').textContent=recentHH;
    $('base-hv').textContent='HV '+hv;$('recent-hv').textContent='HV '+recentHV;
    const label=utc=>atlasVisitLabel(c,c.observations.find(o=>o.timestamp===utc));
    const format=utc=>label(utc)===iso(utc)?atlasShortDate(utc):label(utc);
    for(const [key,trace] of [['base',reference],['recent',recent]]){
      const node=$(key+'-endpoints'),gap=key==='recent'&&trace.documentedGap;
      node.textContent=(trace.target?format(trace.target.utc)+' → '+format(trace.current.utc):'First recorded visit')+
        (gap?' · gap':'');
      node.title=trace.target?label(trace.target.utc)+' to '+label(trace.current.utc)+
        (gap?' · recorded gap between visits':''):'First recorded visit';
    }
    $('trace-support').textContent=supportText.policy+' Signed dB: selected visit minus comparison visit.';
    $('mirror').textContent=o.timestamp.replace('T',' ').replace('Z',' UTC')+' · '+(co?'Coherence map; footprint values describe intensity. ':'')
      +'HH '+hh+' and HV '+hv+' from reference. HH '+recentHH+' and HV '+recentHV+' from previous visit.'
      +' Common-valid support: '+p.valid_pixels.toLocaleString()+' pixels.';
    const nativeBox=$('native-support'),support=p.native_support;
    nativeBox.replaceChildren();
    if(support){
      const w=support.window,mean=p.native_means[i];
      nativeBox.append(el('p',support.rule),el('p',
        'Native bounds start at row '+w.row+', column '+w.col+' · '+w.height+' rows × '+w.width+' columns · '+support.crs+'.'),
        el('p',support.pairedValidCounts[i].toLocaleString()+' paired-valid pixels on this visit. Common-valid HH '+(Number.isFinite(mean.hh)?fmt(mean.hh)+' dB':'unavailable')+' · HV '+(Number.isFinite(mean.hv)?fmt(mean.hv)+' dB':'unavailable')+'. Footprint and common-valid masks are included in the export.'));
    }
    const resp=o.response||{};
    const area=s.lens==='river'&&Number.isFinite(resp.radar_dark_candidate_area_km2)?'This visit: '+fmt(resp.radar_dark_candidate_area_km2)+' km² of radar-dark candidates across the crop. ':'';
    $('next-check').textContent=area+g.next;
    $('provenance').textContent='NASA–ISRO NISAR · ASF DAAC · Track '+o.track+' / frame '+o.frame+' · '+o.processing_release+' · '+c.grid.crs+' · HH/HV.';
    $('source').textContent=(co?pair.source+' · GUNW coherence':o.source_granule_id+' · GCOV version '+o.product_version)+' · source manifest SHA-256 '+c.manifest_sha256;
    $('area').textContent='Whole study boundary: '+fmt(c.scope_area.projected_km2,3)+' km² on projected grid; '+fmt(c.scope_area.ellipsoidal_km2,3)+' km² on WGS84. Neither is a mapped damage area.';
    const native=$('native');native.hidden=portable||Boolean(s.native)||(co&&c.country==='Bangladesh');
    native.href=c.country==='Nepal'?'/expanded.html#'+new URLSearchParams({case:c.case,date:s.date,layer:co?'coherence20':s.layer==='fraction'?'cpr':s.layer,footprint:s.profile}):'/investigations.html#'+new URLSearchParams({case:c.case,date:s.date,mode:s.lens,overlay:s.layer==='fraction'?'cpr':s.layer,footprint:'saved:'+s.profile});
    const queue=$('queue'),focus=document.activeElement?.dataset?.atlasProfile;
    const order=$('sort').value==='successive'?'successive':'reference';
    const score=v=>Number.isFinite(v)?Math.abs(v):-1;
    queue.replaceChildren(...c.profiles.map((p,j)=>({p,j,v:p.series[i]['hh_'+order]})).sort((a,b)=>score(b.v)-score(a.v)).map(({p,j,v})=>{
      const item=el('li',''),button=el('button',p.label+' · '+fmt(v)+' dB');button.setAttribute('aria-pressed',String(!s.native&&j===s.profile));
      button.dataset.atlasProfile=String(j);
      button.onclick=()=>set({profile:j,native:''});item.append(button);return item;
    }));
    if(focus!=null)queue.querySelector('[data-atlas-profile="'+focus+'"]')?.focus();
}

export function renderAtlasAnswer(p,meta,s,o,recent,reference){
  const $=atlasNode,el=atlasElement;
  const r=recent.values.hh,b=reference.values.hh;
  $('verdict').textContent=s.layer==='coherence'
    ?'The map shows pair similarity. The readings below compare radar power.'
    :!recent.target?'The first recorded visit has no earlier visit to compare.'
    :'Radar power changes on the same footprint. The cause needs independent evidence.';
  for(const [key,value] of [['recent',r],['base',b]]){
    const node=$(key);
    node.dataset.sign=value>0?'pos':value<0?'neg':value===0?'measured-zero':'missing';
    if(!Number.isFinite(value))node.textContent=key==='recent'&&!recent.target?'No prior visit':'No data';
    const hv=(key==='recent'?recent:reference).values.hv;
    $(key+'-hv').dataset.sign=hv>0?'pos':hv<0?'neg':hv===0?'measured-zero':'missing';
    $(key).title=Number.isFinite(value)?(value===0?'Measured zero. ':'')+'Selected visit minus comparison visit, same valid pixels.':'No comparable measurement.';
  }
  const support=reference.support;
  $('support-chips').replaceChildren(el('span',support.validPixels.toLocaleString()+' px'),
    el('span',p.area_km2<1?fmt(p.area_km2*100)+' ha':fmt(p.area_km2)+' km²'),
    ...(!Number.isFinite(support.coverage)?[]:[el('span',Number((support.coverage*100).toFixed(1))+'% valid')]),
    el('span',p.label.replace(/^Frozen reference: /,'').replace(/ · common-valid mean$/,'')));
  const footprint=s.native?null:meta.footprints[s.profile];
  const optical=footprint?.opticalFootprintId?meta.environment?.optical?.[footprint.opticalFootprintId]?.[o.observation_id]:null;
  const opticalCells=optical?.clear_assessable_pixels??0,labels=meta.claimReview?.heldOutLabels;
  const stages=[
    ['Radar measurement',support.validPixels>0?'Recorded':'No overlap',
      support.validPixels>0?'Same footprint across visits.':'Choose a footprint with pixels valid in both channels.',support.validPixels>0?'observed':'missing'],
    ['Optical context',opticalCells>0?'Available':'Pending',
      opticalCells>0?'Clear pixels overlap the footprint.':'Look for a clear image covering the same area near this visit.',opticalCells>0?'context':'missing'],
    ['Independent validation',labels>0?'Labels available':'Pending',
      labels>0?labels+' held-out labels available.':'A separate set of reference labels is needed to test accuracy.','missing'],
    ['Physical cause','Unresolved','Check independent observations at the same place and time.','missing']
  ];
  $('evidence-ladder').replaceChildren(...stages.map(([title,status,note,state])=>{
    const step=el('li'),badge=el('span',status);
    badge.className='atlas-evidence-status';step.dataset.state=state;
    step.append(el('strong',title),badge,el('small',note));return step;
  }));
}
