import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {fmt,iso} from './atlas-state.mjs';

export function atlasPairEvidence(meta,o,s,p){
  if(s.layer!=='coherence'||!meta)return null;
  const pair=meta.pairs.find(v=>v.secondId===o.observation_id);
  if(!pair)return null;
  const comparison=meta.coherenceComparisons?.find(v=>v.laterId===pair.id);
  const earlier=comparison?meta.pairs.find(v=>v.id===comparison.earlierId):null;
  return {pair,earlier,comparison,footprint:(s.native?p?.coherence?.pairs[pair.id]:pair.footprints?.[s.profile])??null,
    deltaFootprint:(s.native?p?.coherence?.deltas[pair.id]:comparison?.footprints[s.profile])??null,
    gates:meta.claimReview};
}

export function renderAtlasPairs(meta,o,s,p){
  const box=atlasNode('pairs'),el=atlasElement;
  const evidence=atlasPairEvidence(meta,o,s,p);
  box.hidden=!evidence;
  box.replaceChildren();
  if(!evidence)return;
  const {pair,earlier,comparison,footprint,deltaFootprint}=evidence;
  const interval=v=>iso(v.startUtc)+' → '+iso(v.endUtc);
  const support=v=>v.assessed.toLocaleString()+' of '+v.footprintPixels.toLocaleString()+' cells';
  const baseline=v=>v.baselineRangeM?v.baselineRangeM.map(n=>fmt(n,1)).join(' to ')+' m':'unavailable';
  box.append(el('h3','Coherence between two acquisitions'),
    el('p',interval(pair)+' · '+(pair.intervalSeconds/86400)+' days · '+pair.channel+' · '+pair.postingM+' m · '+pair.passDirection+', '+pair.lookDirection.toLowerCase()+' look.'),
    el('p','Track '+pair.track+' / frame '+pair.frame+' · '+pair.coverage.valid_pixels.toLocaleString()+' of '+pair.coverage.total_pixels.toLocaleString()+' valid crop cells.'),
    el('p',footprint?p.label+' · '+support(footprint)+' · mean coherence '+fmt(footprint.mean,3)+'.':'Coherence statistics are unavailable for this footprint.'));
  const sources=el('details');
  sources.append(el('summary','Pair identities and geometry'),el('p',pair.startUtc+' · '+pair.firstId+' → '+pair.endUtc+' · '+pair.secondId),
    el('p',pair.sourceId+' · GUNW '+pair.productVersion+' · '+pair.release),el('p',pair.sourceSlc.join(' → ')),
    el('p','Perpendicular baseline samples: '+baseline(pair)+' across '+pair.baselineSampleCount+' finite metadata grid cells at '+pair.baselineSample[2]+' m ellipsoidal height. '+pair.grid.crs+'.'));
  box.append(sources);
  if(comparison){
    const preview=el('img');preview.src=comparison.image;preview.alt='Later minus earlier coherence, negative and positive coherence changes';
    const key=el('div');key.className='atlas-legend';
    const swatch=el('span');swatch.className='atlas-swatch';swatch.style.background=comparison.paletteCss;swatch.setAttribute('aria-hidden','true');
    key.append(swatch,el('span','−0.5 decrease · 0 · +0.5 increase. Colors clip at these limits.'));
    box.append(el('h3','Compare two pairs'),el('p',interval(pair)+' minus '+interval(earlier)+'. Sampled baselines: '+baseline(pair)+' and '+baseline(earlier)+', respectively.'),
      preview,key,el('p','Whole crop · '+support(comparison.crop)+' · median change '+fmt(comparison.crop.median,3)+'.'),
      el('p',deltaFootprint?p.label+' · '+support(deltaFootprint)+' · median change '+fmt(deltaFootprint.median,3)+'.':'Coherence change is unavailable for this footprint.'),
      el('p','The pairs share an acquisition. The comparison describes coherence change on jointly valid cells. Geometry and temporal decorrelation can affect the result.'));
  }else if(meta.coherenceComparisons.some(v=>v.earlierId===pair.id)){
    box.append(el('p','Select the next pair to compare coherence across the two intervals.'));
  }
}
