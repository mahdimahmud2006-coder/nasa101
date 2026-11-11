import {atlasFitChecks,atlasFitGroups,atlasSignatureLabel} from './atlas-compatibility.mjs';

const escape=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const value=v=>v===null||v===undefined?'Unavailable':Number(v).toLocaleString('en-US',{maximumFractionDigits:3});

function explanationCard({row:rule,result,title}, {optical,pair,openCards}){
 const checks=atlasFitChecks(rule).map(([label,text])=>`<li>${escape(text)}<small>${escape(label)}</small></li>`);
 const missing=[...new Set(rule.missing_inputs)].map(atlasSignatureLabel);
 const waterContext=optical&&['smooth_low_return','flooded_vegetation_like'].includes(rule.id);
 const pairContext=pair&&rule.id==='steep_source_movement';
 const context=waterContext?
  `<p class="note">Matched HLS water-mask context · ${escape(optical.reference_timestamp.slice(0,10))} · ${value(optical.clear_assessable_pixels)} clear cells in this footprint. See Independent optical reference for the overlap and source.</p>`:
  pairContext?
  `<p class="note">GUNW coherence · ${escape(pair.timestamps.map(t=>t.slice(0,10)).join(' → '))} · mean ${value(pair.statistics['20'].mean_coherence)} across the study window. Coherence describes phase consistency.</p>`:'';
 return `<details class="explanation" data-explanation="${escape(rule.id??'')}"${openCards.has(rule.id)?' open':''}>
  <summary>${escape(title)} <span class="explanation-status" data-fit-status="${result.kind}">${result.label}</span></summary>
  ${checks.length?`<ul class="explanation-checks">${checks.join('')}</ul>`:''}
  ${missing.length?`<p class="note">Required context · ${escape(missing.join(', '))}</p>`:''}
  ${context}
  <p class="note">${escape(rule.limitation)}</p>
  ${['match','partial'].includes(result.kind)?`<p class="note"><strong>Evidence to check next</strong></p>
  <ul class="explanation-checks">${rule.evidence_still_required.map(text=>`<li>${escape(text)}</li>`).join('')}</ul>`:''}
 </details>`;
}

export function reasoningHTML(evidence,index,{observation,optical=null,pair=null,openCards=new Set(),otherOpen=false}={}){
 const fit=evidence?.explanations?.[index];
 if(!fit||(observation&&(fit.observation_id!==observation.observation_id||fit.timestamp!==observation.timestamp)))
  return '<p>Select a measured footprint to review the evidence for competing explanations.</p>';
 if(evidence.profile?.status==='INSUFFICIENT_COMMON_VALID_PIXELS')
  return '<p>Choose a footprint with more pixels measured in both radar channels across the visits.</p>';
 const matchedOptical=optical?.radar_timestamp===fit.timestamp&&optical?.observation_id===fit.observation_id&&
   optical?.footprint_id===evidence.reference_footprint_id&&optical?.reference_timestamp&&optical.clear_assessable_pixels>0?optical:null;
 const datedPair=pair?.timestamps?.[1]===fit.timestamp&&Number.isFinite(pair?.statistics?.['20']?.mean_coherence)?pair:null;
 const d=evidence.dna,p=d.persistence,onset=d.onset_interval;
 const {review,additional,summary}=atlasFitGroups(fit.hypotheses);
 const card=item=>explanationCard(item,{optical:matchedOptical,pair:datedPair,openCards});
 const scope=evidence.profile?
  `<p class="note">${escape(evidence.profile.label)} · ${escape(fit.timestamp.slice(0,10))} UTC · ${value(evidence.profile.common_valid_pixels)} paired pixels · Reference ${escape(evidence.profile.observations[0].timestamp.slice(0,10))}</p>`:'';
 return `<p class="state-pill">EXPLORATORY RULES</p>
  ${scope}
  <dl class="response-values"><dt>Persistence, observed visits</dt><dd>${p.k} of ${p.n}</dd><dt>Sampled recovery fraction</dt><dd>${value(d.recovery_fraction)}</dd><dt>Recovery half-crossing</dt><dd>${d.recovery_right_censored?'Right-censored':'Bracketed between visits'}</dd><dt>Onset threshold bracket</dt><dd>${onset?escape((onset.last_observed_below||'Before first eligible visit')+' → '+onset.first_observed_above):'No observed crossing'}</dd><dt>Terrain</dt><dd>${escape(d.terrain.class)}</dd></dl>
  <p class="note">${escape(p.definition)} No continuous persistence, exact onset, historical match or probability is inferred.</p>
  <p class="explanation-summary">${summary}</p>
  <p class="note">Compare measured values with exploratory criteria. A pattern match points to evidence worth checking.</p>
  ${review.map(card).join('')}
  ${additional.length?`<details class="explanation-more"${otherOpen?' open':''}>
  <summary>Other screening results (${additional.length})</summary>
  ${additional.map(card).join('')}</details>`:''}`;
}
export function claimsHTML(bundle){return bundle?bundle.claims.map(c=>`<article class="ledger-claim" data-claim-id="${escape(c.id)}"><strong>${escape(c.id)} · ${escape(c.status)}</strong><p>${escape(c.text)}</p><small>${escape(c.limitation)}</small></article>`).join(''):'Claim ledger unavailable.';}

export function referenceForSelection(bundle,evidence,observationId){
 const id=evidence?.reference_footprint_id;
 const row=id?bundle?.results.find(r=>r.footprint_id===id&&r.observation_id===observationId):null;
 if(row)return {status:row.reference_status,result:row,design_sha256:bundle.design_sha256,freeze_commit:bundle.freeze_commit,scope:row.scope};
 return {status:evidence?.reference_status==='context overlap'?'context overlap':'none',result:null,scope:'No date-matched reference evaluated for this selected footprint. Any older impact-map overlap is case-wide context.'};
}
export function referenceHTML(bundle,evidence,observationId){
 const selected=referenceForSelection(bundle,evidence,observationId),r=selected.result;
 if(!r)return `<p class="state-pill">${escape(selected.status)}</p><p>${escape(selected.scope)}</p><p>Choose a “Frozen reference” footprint to inspect the preselected optical comparison areas.</p>`;
 const overlap=r.overlap;
 return `<p class="state-pill">${escape(selected.status)}</p><p>${escape(r.footprint_role.replaceAll('_',' '))} · ${escape(r.reference_timestamp||'No eligible reference')}</p><p>${escape(r.reason||r.reference_definition||'Reference unavailable')}</p>${overlap?`<dl class="response-values"><dt>Assessable optical area</dt><dd>${value(overlap.assessable_area_km2)} km²</dd><dt>Reference water area</dt><dd>${value(overlap.reference_water_area_km2)} km²</dd><dt>Radar-dark / water intersection</dt><dd>${value(overlap.intersection_area_km2)} km²</dd><dt>Absolute time difference</dt><dd>${value(r.delta_seconds/3600)} hours</dd></dl>`:''}${r.clear_assessable_pixels>0?`<img src="${escape(r.thumbnail)}" alt="Cloud-masked optical context inside the selected frozen footprint; transparent pixels are unavailable" style="width:100%;max-width:320px;image-rendering:pixelated">`:''}<p class="note">${escape(selected.scope)} Optical and L-band radar differ. Overlap is descriptive, not accuracy or a confirmed cause. Areas use reference-grid pixel centers; native radar means use a different sampling grid.</p><details><summary>Reference provenance</summary><p>${escape(r.reference_id||'None')}</p><p>Design ${escape(bundle.design_sha256)} · freeze ${escape(bundle.freeze_commit)}</p><ul>${Object.entries(r.sources||{}).map(([band,url])=>`<li><a href="${escape(url)}" target="_blank" rel="noreferrer">${escape(band)} source</a></li>`).join('')}</ul></details>`;
}

export function interferometryHTML(pairs, expanded, caseId, mode, footprint) {
  if (!pairs.length) {
    if (!expanded?.coherence_pairs) return '';
    return `<p class="state-pill">MEASURED COHERENCE</p>
      <p>${escape(expanded.coherence_pairs)} recorded HH pairs on native 20 m and 80 m grids.</p>
      <p><a href="/expanded.html#case=${escape(caseId)}&amp;layer=coherence20">Open the coherence map →</a></p>`;
  }
  const links = pairs.map(pair => {
    const [start, end] = pair.timestamps;
    const profile = /^saved:\d+$/.test(footprint) ? footprint.slice(6) : '0';
    const view = new URLSearchParams({atlas:'1',case:caseId,date:end,layer:'coherence',profile,lens:mode});
    if (footprint.startsWith('point:')) view.set('native', footprint.slice(6));
    if (footprint.startsWith('polygon:')) view.set('native', footprint.slice(8));
    return `<li><a href="/#${escape(view.toString())}">${escape(start.slice(0,10))} → ${escape(end.slice(0,10))} · Open map</a>
      <br><small>Mean coherence across the study window: ${value(pair.statistics['20'].mean_coherence)}</small></li>`;
  });
  return `<p class="state-pill">MEASURED COHERENCE</p>
    <p>Follow phase consistency between two radar visits. Compare both pairs in the Atlas on the native 20 m grid.</p>
    <ul>${links.join('')}</ul>`;
}
