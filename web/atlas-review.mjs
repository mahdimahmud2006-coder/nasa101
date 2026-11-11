import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {fmt,iso} from './atlas-state.mjs';

export function atlasObservedOccupancy(visits){
  const assessed=visits.filter(v=>v.matches===true||v.matches===false);
  const matching=assessed.filter(v=>v.matches).length;
  return {observed:visits.length,valid:assessed.length,unknown:visits.length-assessed.length,
    matching,fraction:assessed.length?matching/assessed.length:null};
}

export function atlasFieldReview(c,meta,p,s){
  if(!meta?.reviewRule||!['river','wetland'].includes(s.lens))return null;
  const footprint=meta.footprints[s.profile];
  const review=s.native?p.review:footprint.review;
  if(!review)return null;
  const opticalId=s.native?null:footprint.opticalFootprintId;
  const visits=c.observations.map(o=>{
    const optical=opticalId?meta.environment.optical[opticalId]?.[o.observation_id]??null:null;
    const overlap=p.reference_matches?.[o.timestamp]?.overlap;
    const match=optical&&optical.clear_assessable_pixels>0?{...optical,overlap,
      offsetHours:(Date.parse(optical.reference_timestamp)-Date.parse(o.timestamp))/3600000}:null;
    return {observationId:o.observation_id,utc:o.timestamp,...review.visits[o.observation_id],
      opticalStatus:optical?.status??'no bound reference',optical:match};
  });
  const selected=visits.find(v=>v.utc===s.date);
  const river=s.lens==='river';
  const request=river?
    'Request co-registered, dated left and right bank outlines and water levels for this reach. Check whether the apparent edge persists at comparable river stage.':
    'Request a water-depth reading, crop growth stage or habitat observation at this footprint on a radar visit. Record the water and vegetation conditions separately.';
  const question=river?'Did the apparent edge move at comparable river stage?':'Does the radar signature coincide with shallow water, vegetation, or both?';
  const status=river?'No validated bank lines for this reach. Movement is unresolved.':
    'Water, flooded vegetation and habitat classes require independent labels. Observations describe the visits shown.';
  const occurrence=atlasObservedOccupancy(visits);
  return {workflow:river?'river_bank_review':'wetland_repeat_visit_review',status,scope:'Exploratory field review',
    footprintId:s.native?null:footprint.id,footprintLabel:p.label,location:review.location,maskSource:s.native?null:footprint.maskSource,
    rule:meta.reviewRule,unit:'One recorded visit with finite HH and HV footprint means on fixed paired-valid pixels.',
    question,request,occurrence,visits,selected,acquisitionGaps:meta.acquisitionGaps,
    alternatives:river?['River stage or seasonal bar exposure','Roughness and observation geometry']:
      ['Wind-roughened water','Vegetation structure','Shadow or viewing geometry'],
    duration:'unavailable',validatedClaims:meta.claimReview.validatedClaims};
}

export function renderAtlasFieldReview(c,meta,p,s,set,exportReview){
  const $=atlasNode,el=atlasElement,box=$('field-review');
  const review=atlasFieldReview(c,meta,p,s);
  const open=box.querySelector?.('details')?.open??false;
  const focused=document.activeElement?.dataset?.atlasReviewVisit;
  box.hidden=!review;box.replaceChildren();
  if(!review)return;
  const river=s.lens==='river';
  box.append(el('h3',river?'River Memory · Bank review':'Wetland Pulse · Repeat-visit review'),
    el('p',review.question),el('p',review.status));
  const guides=el('div');guides.className='atlas-actions';
  const target=meta.footprints.find(v=>v.opticalFootprintId?.endsWith('_target_geographic'));
  if(target&&(target.ordinal!==s.profile||s.native)){
    const guided=el('button',river?'Open guided Jamuna reach':'Open guided Tanguar footprint');
    const date=Object.entries(c.profiles[target.ordinal].reference_matches??{})
      .filter(([,match])=>match.clear_assessable_pixels>0).map(([date])=>date).sort()[0];
    guided.onclick=()=>set({profile:target.ordinal,native:'',...(date?{date}:{}),split:50});
    guides.append(guided);
  }
  const compare=el('button','Compare reference and selected visit');
  compare.onclick=()=>set({split:50});
  guides.append(compare);box.append(guides);
  if(review.location){
    const {latitude,longitude}=review.location;
    box.append(el('p',p.label+' · review point '+fmt(latitude,5)+'° N, '+fmt(longitude,5)+'° E.'));
  }
  const a=review.occurrence,r=review.rule;
  box.append(el('p',a.valid?a.matching+' of '+a.valid+' valid visits matched ('+fmt(100*a.fraction,0)+'%). '+a.unknown+' unknown of '+a.observed+' recorded visits.':
    'Occurrence unavailable · '+a.unknown+' of '+a.observed+' recorded visits lack paired footprint support.'),
    el('p','A visit matches when its footprint means are HH ≤ '+r.hhMaxDb+' dB and HV ≤ '+r.hvMaxDb+' dB. The fraction describes observed visits only.'));
  const v=review.selected;
  if(v.optical){
    box.append(el('p','Selected optical comparison · '+v.optical.reference_timestamp.replace('T',' ').replace('Z',' UTC')+
      ' · '+fmt(Math.abs(v.optical.offsetHours),1)+' hours '+(v.optical.offsetHours<0?'before':'after')+
      ' radar · '+v.optical.clear_assessable_pixels.toLocaleString()+' eligible cells. '+v.optical.reference_id+'.'));
    const overlap=v.optical.overlap;
    if(overlap?.assessable_area_km2>0){
      const opticalOnly=overlap.reference_water_area_km2-overlap.intersection_area_km2;
      const darkOnly=overlap.radar_dark_area_km2-overlap.intersection_area_km2;
      box.append(el('p','On clear, shared support, '+fmt(opticalOnly,3)+' km² matched only the optical water rule and '+
        fmt(darkOnly,3)+' km² matched only the radar-dark rule. Check this disagreement in the field.'));
    }
    const match=p.reference_matches?.[v.utc];
    if(match?.image){
      const image=el('img');image.src=match.image;image.alt='Dated optical comparison on the selected footprint';box.append(image);
    }
  }else box.append(el('p','No eligible optical match for this footprint and visit.'));
  box.append(el('p','Other explanations to check: '+review.alternatives.join(' · ')+'.'));
  const chronology=el('details'),scroll=el('div'),table=el('table'),head=el('thead'),body=el('tbody'),heading=el('tr');
  chronology.open=open;
  scroll.className='atlas-scroll';scroll.tabIndex=0;scroll.setAttribute('aria-label','Review visits, scroll horizontally if needed');
  for(const title of ['Visit UTC','HH dB','HV dB','Dark cells','Match','Optical']){
    const th=el('th',title);th.setAttribute('scope','col');heading.append(th);
  }
  head.append(heading);
  for(const visit of review.visits){
    const row=el('tr'),day=el('button',iso(visit.utc)),cell=el('th');
    day.dataset.atlasReviewVisit=visit.observationId;
    cell.setAttribute('scope','row');day.onclick=()=>set({date:visit.utc});cell.append(day);
    if(visit.utc===s.date)row.setAttribute('aria-current','true');
    row.append(cell, ...[fmt(visit.hhDb),fmt(visit.hvDb),
      visit.pairedPixels?visit.darkPixels.toLocaleString()+' / '+visit.pairedPixels.toLocaleString():'—',
      visit.matches==null?'Unknown':visit.matches?'Yes':'No',visit.optical?'Dated match':'Unavailable'].map(text=>el('td',text)));
    body.append(row);
  }
  table.append(head,body);scroll.append(table);
  chronology.append(el('summary','HH, HV and optical evidence by visit'),scroll);
  for(const gap of review.acquisitionGaps)chronology.append(el('p','No acquisition on '+gap.nominalDate+'. The denominator uses recorded visits.'));
  box.append(chronology,el('h4','Field check'),el('p',review.request));
  const exportButton=el('button','Export field check ↓');exportButton.onclick=exportReview;box.append(exportButton);
  if(focused)box.querySelector?.('[data-atlas-review-visit="'+focused+'"]')?.focus();
}
