import {atlasElement,atlasNode} from './atlas-dom.mjs';
import {fmt} from './atlas-state.mjs';

const atlasFitTitles={
  smooth_low_return:'Low returns in both channels',
  flooded_vegetation_like:'Brightening in both channels',
  moisture_roughness:'Rainfall and radar change',
  vegetation_structure:'Cross-polarized response change',
  steep_source_movement:'Steep-slope disturbance screen',
  radiometric_processing:'Change in comparison areas'
};
const atlasSignatureLabels={
  hh_last_db:'Mean HH',hv_last_db:'Mean HV',hh_delta_db:'HH change from reference',hv_delta_db:'HV change from reference',
  hh_change_abs_db:'Absolute HH mean difference',hv_change_abs_db:'Absolute HV mean difference',
  cpr_change_abs_db:'Absolute CPR difference',mean_abs_hh_change_db:'Mean absolute pixelwise HH change',
  median_slope_degrees:'Median slope',rain_72h_mm:'Scientific IMERG rainfall in the prior 72 h',paired_darkening:'Paired darkening',
  control_offset_abs_db:'Largest case-wide control shift'
};
const atlasRuleSigns={le:'≤',lt:'<',ge:'≥',gt:'>',eq:'='};
function atlasFitResult(row){
  if(row.status==='contradicted')return {kind:'excluded',label:'Excluded by this screen'};
  if(row.missing_inputs?.length||row.status==='unknown'||row.status==='insufficient evidence')
    return {kind:'incomplete',label:'Evidence incomplete'};
  if(row.status==='consistent')return {kind:'match',label:'Full pattern match'};
  if(row.supporting_signatures?.length)return {kind:'partial',label:'Partial pattern match'};
  return {kind:'outside',label:'Outside screening criteria'};
}

export const atlasSignatureLabel=field=>atlasSignatureLabels[field]??field;

export function atlasFitGroups(rows){
  const items=rows.map(row=>({row,result:atlasFitResult(row),title:atlasFitTitles[row.id]??row.title}));
  const matches=items.filter(item=>item.result.kind==='match');
  const partial=items.filter(item=>item.result.kind==='partial');
  const additional=items.filter(item=>!['match','partial'].includes(item.result.kind));
  const summary=matches.length+' full '+(matches.length===1?'match':'matches')+' · '+partial.length+
    ' partial '+(partial.length===1?'match':'matches')+' · '+items.length+' exploratory screens';
  return {review:[...matches,...partial],additional,summary};
}

export function atlasCompatibility(meta,p,profileOrdinal,observationId){
  if(!meta?.hypotheses)return null;
  const fits=profileOrdinal==null?p.nativeExplanations?.[observationId]:
    meta.footprints[profileOrdinal]?.explanationEvidence?.[observationId];
  const rows=meta.hypotheses.templates.map(template=>{
    const row=p.valid_pixels>0?fits?.find(h=>h.id===template.id):null;
    return {id:template.id,title:template.title,status:row?.status==='unknown'||!row?'insufficient evidence':row.status,
      supporting_signatures:row?.supporting_signatures??[],contradicting_signatures:row?.contradicting_signatures??[],
      unmet_signatures:row?.unmet_signatures??[],missing_inputs:[...new Set(row?.missing_inputs??[])],
      evaluated:Boolean(row),evidence_still_required:template.required,limitation:template.limitation};
  });
  const visit=meta.observations.find(o=>o.id===observationId);
  const reference=meta.observations.find(o=>o.id===meta.referenceId);
  const min=meta.hypotheses.nativeMinPairedFraction;
  const lowSupport=profileOrdinal==null&&Number.isFinite(min)&&p.valid_pixels<p.footprint_pixels*min;
  return {ruleVersion:meta.hypotheses.version,observationId,rows,footprint:p.label,
    selectedUtc:visit?.utc,referenceUtc:reference?.utc,commonValidPixels:p.valid_pixels,
    unavailableReason:!p.valid_pixels?'Choose a footprint with pixels valid in both channels across all recorded visits.':
      lowSupport?'Choose a smaller or nearby footprint. Rules require at least '+Math.round(min*100)+'% paired coverage across recorded visits.':
      rows.some(r=>r.evaluated)?null:'Rule inputs are unavailable for this selection.'};
}

export function atlasSignatureText(rule){
  const name=atlasSignatureLabel(rule.field);
  if(rule.field==='paired_darkening'&&rule.observed_value===true)
    return 'Both HH and HV decreased by at least 3 dB from the reference';
  const unit=rule.field.endsWith('_db')?' dB':rule.field.endsWith('_mm')?' mm':rule.field.endsWith('_degrees')?'°':'';
  const observed=typeof rule.observed_value==='number'?fmt(rule.observed_value):String(rule.observed_value);
  return name+' '+observed+unit+' · criterion '+atlasRuleSigns[rule.op]+' '+rule.value+unit;
}

export function atlasFitChecks(row){
  return [['Criterion met',row.supporting_signatures],['Exclusion triggered',row.contradicting_signatures],
    ['Outside criterion',row.unmet_signatures]].flatMap(([label,conditions])=>
    (conditions??[]).map(condition=>[label,atlasSignatureText(condition)]));
}

export function renderAtlasCompatibility(compatibility){
  const $=atlasNode,el=atlasElement;
  const list=$('fit'),other=$('fit-other'),disclosure=$('fit-disclosure');
  const open=new Set([...list.children,...other.children].filter(row=>row.open).map(row=>row.dataset.hypothesis));
  const groups=atlasFitGroups(compatibility?.unavailableReason?[]:compatibility?.rows??[]);
  $('fit-scope').textContent=compatibility?
    [compatibility.footprint,compatibility.selectedUtc?.replace('T',' ').replace('Z',' UTC'),
      'Reference '+compatibility.referenceUtc?.slice(0,10),compatibility.commonValidPixels.toLocaleString()+' paired pixels'].join(' · '):'';
  $('fit-coverage').textContent=compatibility?.unavailableReason??(compatibility?groups.summary:'Choose a measured footprint to review radar patterns.');
  function card({row,result,title}){
    const details=el('details'),summary=el('summary');
    details.className='atlas-fit-card';
    details.dataset.fitStatus=result.kind;
    details.dataset.hypothesis=row.id;details.open=open.has(row.id);
    const status=el('span',result.label);
    status.className='atlas-fit-status';
    summary.append(el('strong',title),status);
    details.append(summary);
    const body=el('div');
    body.className='atlas-fit-detail';
    const checks=atlasFitChecks(row);
    if(checks.length){
      const items=el('ul');
      for(const [label,text] of checks){
        const item=el('li',text);
        item.append(el('small',label));
        items.append(item);
      }
      body.append(items);
    }
    if(row.missing_inputs.length)body.append(el('p','Required context · '+row.missing_inputs.map(atlasSignatureLabel).join(', ')));
    body.append(el('small',row.limitation));
    if(['match','partial'].includes(result.kind)){
      body.append(el('h3','Evidence to check next'));
      const needed=el('ul');
      needed.append(...row.evidence_still_required.map(text=>el('li',text)));
      body.append(needed);
    }
    details.append(body);
    return details;
  }
  list.replaceChildren(...groups.review.map(card));
  other.replaceChildren(...groups.additional.map(card));
  disclosure.hidden=!groups.additional.length;
  $('fit-other-label').textContent='Other screening results ('+groups.additional.length+')';
}
