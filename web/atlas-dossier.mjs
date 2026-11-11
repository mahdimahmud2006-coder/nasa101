import {atlasMakeState,atlasValidateState} from './atlas-contract.mjs';
import {atlasNode} from './atlas-dom.mjs';
import {observationPacket} from './atlas-evidence.mjs';

export const atlasDossierSchema='terrapulse.atlas-investigation.v2';
export const atlasDossierMaxBytes=8*1024*1024;
export const atlasDossierTolerance=1e-6;
const dossierFields=['hh_reference','hv_reference','hh_successive','hv_successive'];
const dossierText=(value,max=160)=>typeof value==='string'?value.slice(0,max):'';

function dossierComponents(packet){
  const hh=packet.measurementRecords.find(m=>m.quantity==='hh_reference');
  const evidence=packet.coherence_evidence;
  const comparison=evidence?.comparison, summary=evidence?.deltaFootprint;
  const interval=p=>({id:p.id,sourceId:p.sourceId,firstId:p.firstId,lastId:p.secondId,firstUtc:p.startUtc,lastUtc:p.endUtc});
  return {
    hh:{...hh,reference:hh.endpoints.comparison},
    dprvic:{quantity:'ΔDpRVIc',unit:'dimensionless',value:null,status:'unavailable',reference:null,endpoints:null,support:null,
      method:'No accepted transfer of the detected-data method to these NISAR inputs.'},
    coherence:{quantity:'Δcoherence',unit:'dimensionless',value:summary?.median??null,status:summary?.assessed?'measured':'unavailable',
      reference:comparison?interval(evidence.earlier):null,endpoints:comparison?{earlier:interval(evidence.earlier),later:interval(evidence.pair)}:null,
      support:summary?{gridId:comparison.gridId,validPixels:summary.assessed,footprintPixels:summary.footprintPixels,
        policy:comparison.gridPolicy}:null,method:'Median of later-pair minus earlier-pair coherence on joint valid GUNW cells in the footprint.'},
    los:{quantity:'ΔLOS',unit:'m',value:null,status:'unavailable',reference:null,endpoints:null,support:null,
      method:'Release requires corrected and referenced phase, uncertainty and independent LOS validation.'}
  };
}

function dossierMeasuredSignals(packet, components, referenceDualpol){
  const signals=packet.measurementRecords.filter(m=>m.status==='measured');
  const current=packet.dualpol.summary;
  if(Number.isFinite(current?.powerShare)&&Number.isFinite(referenceDualpol?.powerShare)&&
      current.validPixels===packet.common_valid_pixels&&referenceDualpol.validPixels===current.validPixels){
    signals.push({quantity:'change_in_hv_power_share',unit:'percentage points',
      value:100*(current.powerShare-referenceDualpol.powerShare),status:'measured',
      endpoints:components.hh.endpoints,support:components.hh.support,
      method:'Selected minus reference mean of per-cell HV/(HH+HV) in linear power.'});
  }
  if(components.coherence.status==='measured')signals.push(components.coherence);
  return signals;
}

export function atlasCreateDossier(records,state,profile,catalog,threshold,scenario,notes=''){
  if(state.scenarioRun&&!scenario)throw Error('The requested scenario has no completed result to export.');
  const packet=observationPacket(records,state,profile,catalog,threshold,scenario);
  const meta=catalog[state.case],f=state.native?null:meta.footprints[state.profile];
  const components=dossierComponents(packet);
  const referenceDualpol=(state.native?profile.dualpol:f.dualpol)?.[meta.referenceId];
  return {...packet,schema:atlasDossierSchema,
    dossier:{tolerance:{absoluteNumeric:atlasDossierTolerance,identities:'exact',counts:'exact'},
      components,measuredSignals:dossierMeasuredSignals(packet,components,referenceDualpol),
      footprint:{selection:packet.contract.footprint,grid:meta.grid,mask:f?.maskSource??null,
        profileManifestSha256:f?.profileManifestSha256??null,nativeSupport:packet.native_support},
      source:{caseManifestSha256:meta.manifestSha256,recordVersion:meta.recordVersion,evidenceVersion:meta.evidenceVersion},
      review:{notes:dossierText(notes,800),nextAction:packet.field_review?.request??packet.follow_up}}};
}

export function atlasParseDossier(text,size){
  if(size>atlasDossierMaxBytes||text.length>atlasDossierMaxBytes)throw Error('Choose a dossier of 8 MiB or smaller.');
  let packet;
  try{packet=JSON.parse(text);}catch{throw Error('This file is not valid JSON.');}
  if(!packet||typeof packet!=='object'||Array.isArray(packet))throw Error('This file is not an investigation dossier.');
  return packet;
}

export function atlasDossierSummary(packet){
  const fields=dossierFields.flatMap(key=>{
    const value=packet.measurements?.[key];
    return Number.isFinite(value)?[key.replace('_',' ').toUpperCase()+' '+value.toFixed(3)+' dB']:[];
  });
  return [dossierText(packet.study),dossierText(packet.selected_utc,45),dossierText(packet.footprint),
    fields.join(' · '),dossierText(packet.dossier?.review?.nextAction??packet.follow_up,440),
    dossierText(packet.dossier?.review?.notes,800)].filter(Boolean);
}

export function atlasDossierSelection(packet,catalog,limited){
  if(packet.schema!==atlasDossierSchema)throw Error('This dossier version cannot be reopened in this edition.');
  if(![1,3,5].includes(packet.chronology?.rule?.thresholdDb))throw Error('The dossier does not specify an accepted chronology threshold.');
  const state=atlasValidateState(catalog,packet.contract);
  if(limited&&state.native)throw Error('This footprint needs the full local runtime and its matching native rasters.');
  if(limited&&state.scenarioRun)throw Error('This custom scenario needs the full local runtime and its matching model inputs.');
  return state;
}

function dossierCompare(saved,current,path,tolerance){
  if(saved===current)return;
  if(typeof current==='number'&&typeof saved==='number'&&Number.isFinite(saved)&&Math.abs(current-saved)<=tolerance)return;
  if(current&&typeof current==='object'&&saved&&typeof saved==='object'&&Array.isArray(current)===Array.isArray(saved)){
    const keys=Object.keys(current);
    if(keys.length===Object.keys(saved).length&&keys.every(k=>Object.hasOwn(saved,k))){
      for(const key of keys)dossierCompare(saved[key],current[key],path+'.'+key,
        /(?:pixels|count|areaCells|matched|observed|unknown|visits|assessed|total)$/i.test(key)?0:tolerance);
      return;
    }
  }
  throw Error('Saved evidence differs at '+path+'. The current selection is unchanged.');
}

export function atlasVerifyDossier(saved,current,catalog,state){
  const expected=atlasMakeState(catalog,state),prior=catalog[state.case].previousIntensityEvidenceVersion;
  const oldIntensity=typeof prior==='string'&&expected.layerId!=='coherence'&&saved.contract?.evidenceVersion===prior;
  dossierCompare(saved.contract,oldIntensity?{...expected,evidenceVersion:prior}:expected,'investigation identity',0);
  const source=current.dossier.source;
  dossierCompare(saved.dossier?.source,oldIntensity?{...source,evidenceVersion:prior}:source,'source identity',0);
  dossierCompare(saved.dossier?.footprint,current.dossier.footprint,'footprint and mask',0);
  for(const field of ['measurements','measurementRecords','history','chronology','dualpol','optical_reference','environmental_context','context']){
    const contents=field==='context'&&current.context?.counterfactual?
      [{...saved.context,counterfactual:saved.context?.counterfactual&&{...saved.context.counterfactual,edition:current.context.counterfactual.edition}},current.context]:
      [saved[field],current[field]];
    dossierCompare(...contents,field,atlasDossierTolerance);
  }
  const field=packet=>{
    if(!packet.field_review)return null;
    const {map,...evidence}=packet.field_review;
    return evidence;
  };
  dossierCompare(field(saved),field(current),'field review evidence',atlasDossierTolerance);
  dossierCompare(saved.coherence_evidence?.footprint??null,current.coherence_evidence?.footprint??null,'pair footprint',atlasDossierTolerance);
  dossierCompare(saved.dossier?.components,current.dossier.components,'component evidence',atlasDossierTolerance);
  if(Object.hasOwn(saved.dossier??{},'measuredSignals'))
    dossierCompare(saved.dossier.measuredSignals,current.dossier.measuredSignals,'measured signals',atlasDossierTolerance);
  if(Object.hasOwn(saved,'historical_land_cover'))
    dossierCompare(saved.historical_land_cover,current.historical_land_cover,'historical land cover',atlasDossierTolerance);
}

export function atlasFieldSurvey(packet,coordinates){
  if(!Array.isArray(coordinates)||coordinates.length!==2||
      !coordinates.every((x,i)=>Number.isFinite(x)&&Math.abs(x)<=(i?90:180)))return null;
  return {type:'FeatureCollection',features:[{
    type:'Feature',geometry:{type:'Point',coordinates},properties:{
      caseId:packet.case_id,study:packet.study,footprint:packet.footprint,
      locationRole:'Representative radar footprint point for navigation',
      radarUtc:packet.selected_utc,referenceUtc:packet.reference_utc,sourceGranule:packet.source_granule,
      pairedValidPixels:packet.common_valid_pixels,historicalLandCover:packet.historical_land_cover,nextCheck:packet.dossier.review.nextAction,
      observationUtc:null,observationNotes:''
    }
  }]};
}

export function createAtlasDossierControls({reopen,makePacket}){
  const $=atlasNode;
  let staged=null,revision=0;
  $('dossier-open').disabled=true;
  async function stageFile(selected){
    const request=++revision;
    $('dossier-status').dataset.result='';
    staged=null;$('dossier-open').disabled=true;$('dossier-summary').textContent='';
    if(!selected){$('dossier-status').textContent='';return;}
    try{
      if(selected.size>atlasDossierMaxBytes)throw Error('Choose a dossier of 8 MiB or smaller.');
      const packet=atlasParseDossier(await selected.text(),selected.size);
      if(revision!==request)return;
      staged=packet;
      $('dossier-summary').textContent=atlasDossierSummary(packet).join('\n');
      $('dossier-status').textContent=packet.schema===atlasDossierSchema?
        'File read. This summary is unverified until you reopen it.':'Unsupported dossier version. The summary below is unverified.';
      $('dossier-open').disabled=packet.schema!==atlasDossierSchema;
    }catch(error){if(revision===request)$('dossier-status').textContent=error.message;}
  }
  $('dossier-file').onchange=()=>stageFile($('dossier-file').files?.[0]);
  const drop=$('dossier-drop');
  drop.addEventListener('dragover',event=>{event.preventDefault();drop.dataset.drag='true';});
  drop.addEventListener('dragleave',()=>{delete drop.dataset.drag;});
  drop.addEventListener('drop',event=>{
    event.preventDefault();delete drop.dataset.drag;
    $('dossier-file').value='';
    stageFile(event.dataTransfer?.files?.[0]);
  });
  $('dossier-open').onclick=async()=>{
    if(!staged)return;
    const request=++revision;
    $('dossier-open').disabled=true;
    $('dossier-status').textContent='Checking the saved selection and evidence…';
    try{
      await reopen(staged,()=>request===revision);
      if(request===revision){
        $('dossier-status').dataset.result='verified';
        $('dossier-status').textContent='✓ Verified and reopened. The matching edition reproduced the saved measurements.';
      }
    }catch(error){if(request===revision){
      $('dossier-status').dataset.result='mismatch';
      $('dossier-status').textContent='⚠ '+error.message;
    }}
    finally{if(request===revision)$('dossier-open').disabled=false;}
  };
  return ()=>{
    try{return makePacket(dossierText($('dossier-notes').value,800));}
    catch(error){$('dossier-tools').open=true;$('dossier-status').textContent=error.message;return null;}
  };
}
