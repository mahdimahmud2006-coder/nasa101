/** Versioned state and measurement boundary for the saved and local atlas. */
import {atlasScenarioParameters} from './atlas-state.mjs';

const atlasAssert=(condition,message)=>{if(!condition)throw new Error(message);};
const atlasHas=(object,key)=>object!=null&&Object.hasOwn(object,key);
const atlasStates=['measured','missing','out_of_scope','invalid'];

function atlasCase(catalog,id){
  atlasAssert(atlasHas(catalog,id),'Unknown study window.');
  return catalog[id];
}

function atlasFootprint(c,input){
  atlasAssert(input?.gridId===c.gridId,'Footprint belongs to another or outdated grid.');
  const [h,w]=c.grid.shape;
  if(input.kind==='saved'){
    const f=c.footprints.find(x=>x.id===input.id);
    atlasAssert(f,'Saved footprint is stale or belongs to another study window.');
    return {profile:f.ordinal};
  }
  atlasAssert(c.capabilities.localFootprints.includes(input.kind),'Footprint type is outside this case’s supported scope.');
  if(input.kind==='point'){
    atlasAssert(Number.isInteger(input.row)&&Number.isInteger(input.col)&&input.row>=0&&input.row<h&&input.col>=0&&input.col<w,'Point is outside the native grid.');
    return {profile:0,native:input.row+','+input.col};
  }
  const points=input.vertices;
  atlasAssert(Array.isArray(points)&&points.length>=3&&points.length<=200&&points.every(v=>Array.isArray(v)&&v.length===2&&v.every(Number.isFinite)&&v[0]>=0&&v[0]<=w&&v[1]>=0&&v[1]<=h),'Polygon has invalid or out-of-grid coordinates.');
  const native=JSON.stringify(points);
  atlasAssert(native.length<=6000,'Polygon exceeds the native selection size limit.');
  return {profile:0,native};
}

export function atlasValidateState(catalog,state){
  atlasAssert(state?.schemaVersion===1,'Unsupported investigation schema version.');
  const c=atlasCase(catalog,state.caseId);
  const originalIntensity=state.layerId!=='coherence'&&typeof c.previousIntensityEvidenceVersion==='string'&&
    state.evidenceVersion===c.previousIntensityEvidenceVersion;
  atlasAssert(state.recordVersion===c.recordVersion&&state.manifestSha256===c.manifestSha256&&
    (state.evidenceVersion===c.evidenceVersion||originalIntensity),'Investigation record is outdated; open the matching edition.');
  atlasAssert(state.gridId===c.gridId,'Investigation grid does not match this study window.');
  const o=c.observations.find(o=>o.id===state.currentId);
  atlasAssert(o,'Observation is not available for this study window.');
  atlasAssert(state.referenceId===c.referenceId,'Reference observation does not match this saved record.');
  atlasAssert(c.capabilities.layers.includes(state.layerId),'Layer is outside this case’s supported scope.');
  if(state.layerId==='coherence'){
    const p=c.pairs.find(p=>p.id===state.pair?.id);
    atlasAssert(p&&p.firstId===state.pair.firstId&&p.secondId===state.pair.secondId&&p.secondId===o.id&&state.pair.gridId===p.grid.id,'Coherence pair, endpoints or grid do not match this observation.');
  }else atlasAssert(state.pair===null,'Pair metadata is only valid for a coherence layer.');
  const {thermalId,scenarioId,scenarioRun}=state.contextSelections||{};
  atlasAssert(thermalId===null||c.context.thermal.some(x=>x.id===thermalId),'Thermal observation is unavailable for this study window.');
  atlasAssert(scenarioId===null||c.context.scenarios.some(x=>x.id===scenarioId&&x.observationId===o.id),'Scenario is unavailable for this observation.');
  const model=c.environment?.scenario;
  if(scenarioRun)atlasAssert(!scenarioId&&model?.anchors[o.id]&&scenarioRun.observationId===o.id&&
    scenarioRun.modelVersion===model.modelVersion&&scenarioRun.inputsSha256===model.inputsSha256&&
    atlasScenarioParameters(scenarioRun),'Scenario request does not match the accepted observation and model inputs.');
  const d=state.display||{};
  atlasAssert(c.capabilities.lenses.includes(d.lens)&&Number.isInteger(d.split)&&d.split>=0&&d.split<=100&&
    ['on','off'].includes(d.terrain)&&!(d.terrain==='on'&&state.layerId==='coherence')&&
    [0,45,90,135,180,225,270,315].includes(d.bearing),'Invalid display selection.');
  return {case:c.caseId,date:o.utc,layer:state.layerId,...atlasFootprint(c,state.footprint),lens:d.lens,split:d.split,terrain:d.terrain,bearing:d.bearing,
    ...(thermalId?{thermal:thermalId}:{}),...(scenarioId?{scenario:scenarioId}:{}),
    ...(scenarioRun?{scenarioRun:{...atlasScenarioParameters(scenarioRun),anchorUtc:o.utc}}:{})};
}

export function atlasMakeState(catalog,s){
  const c=atlasCase(catalog,s.case);
  const o=c.observations.find(o=>o.utc===s.date);
  atlasAssert(o,'Observation is not available for this study window.');
  let footprint={kind:'saved',gridId:c.gridId,id:c.footprints[s.profile]?.id};
  if(s.native?.startsWith('['))footprint={kind:'polygon',gridId:c.gridId,vertices:JSON.parse(s.native)};
  else if(s.native){
    const [row,col]=s.native.split(',').map(Number);
    footprint={kind:'point',gridId:c.gridId,row,col};
  }
  const p=s.layer==='coherence'?c.pairs.find(p=>p.secondId===o.id):null;
  const model=c.environment?.scenario;
  const run=s.scenarioRun?{...atlasScenarioParameters(s.scenarioRun),observationId:o.id,
    modelVersion:model?.modelVersion,inputsSha256:model?.inputsSha256}:null;
  const state={schemaVersion:1,caseId:c.caseId,recordVersion:c.recordVersion,manifestSha256:c.manifestSha256,evidenceVersion:c.evidenceVersion,
    gridId:c.gridId,currentId:o.id,referenceId:c.referenceId,layerId:s.layer,footprint,
    pair:p?{id:p.id,firstId:p.firstId,secondId:p.secondId,gridId:p.grid.id}:null,
    contextSelections:{thermalId:s.thermal??null,scenarioId:s.scenario??null,...(run?{scenarioRun:run}:{})},
    display:{lens:s.lens,split:s.split,terrain:s.terrain,bearing:s.bearing}};
  atlasValidateState(catalog,state);
  return state;
}

export function atlasVersionedHash(state){
  return '#'+new URLSearchParams({atlas:'2',view:JSON.stringify(state)});
}

export function atlasReadHash(catalog,hash){
  atlasAssert(hash.length<=24000,'Investigation link exceeds the size limit.');
  const p=new URLSearchParams(hash.replace(/^#/,''));
  if(!p.has('atlas'))return null; // Older specialist routes retain their own state.
  if(p.get('atlas')==='2'){
    let state;
    try{state=JSON.parse(p.get('view'));}catch{throw new Error('Malformed investigation link.');}
    return atlasValidateState(catalog,state);
  }
  atlasAssert(p.get('atlas')==='1','Unsupported investigation link version.');
  const c=atlasCase(catalog,p.get('case'));
  const layer=p.get('layer')||'hh';
  const time=p.get('date')||'';
  const dates=c.observations.filter(o=>o.utc===time||o.utc.slice(0,10)===time);
  atlasAssert(dates.length===1,'Old link does not name an unambiguous recorded date in this case.');
  atlasAssert(c.capabilities.layers.includes(layer),'Old link requests an unavailable layer.');
  if(layer==='coherence')atlasAssert(c.pairs.some(pair=>pair.secondId===dates[0].id),'Old link does not name an available coherence pair.');
  const profile=p.get('profile')??'0';
  atlasAssert(/^\d+$/.test(profile)&&c.footprints[Number(profile)],'Old link names an unknown saved footprint.');
  const raw=Object.fromEntries(p);
  if(raw.thermal)atlasAssert(c.context.thermal.some(x=>x.id===raw.thermal),'Old link requests an unavailable thermal record.');
  if(raw.scenario)atlasAssert(c.context.scenarios.some(x=>x.id===raw.scenario&&x.observationId===dates[0].id),'Old link requests an unavailable scenario.');
  if(raw.native){
    let input;
    if(/^\d+\s*,\s*\d+$/.test(raw.native)){const [row,col]=raw.native.split(',').map(Number);input={kind:'point',row,col};}
    else{let vertices;try{vertices=JSON.parse(raw.native);}catch{throw new Error('Old link contains malformed geometry.');}input={kind:'polygon',vertices};}
    const normalized=atlasFootprint(c,{...input,gridId:c.gridId});
    raw.native=normalized.native;
  }
  return {...raw,case:c.caseId,date:dates[0].utc,layer,profile:Number(profile)};
}

export function atlasMeasurement({quantity,unit,value,status,sourceIds,support,method,interpretation}){
  atlasAssert(atlasStates.includes(status),'Unsupported measurement status.');
  atlasAssert(status==='measured'?Number.isFinite(value):value===null,'Measured values must be finite; unavailable values must be null.');
  atlasAssert([quantity,unit,method,interpretation].every(x=>typeof x==='string'&&x.length>0)&&
    Array.isArray(sourceIds)&&sourceIds.every(x=>typeof x==='string')&&
    (support===null||Number.isInteger(support.validPixels)&&support.validPixels>=0&&typeof support.gridId==='string'),
    'Invalid measurement metadata.');
  atlasAssert(status!=='measured'||(sourceIds.length>0&&support?.validPixels>0),'Measured value has no valid support or source.');
  return {quantity,unit,value,status,sourceIds,support,method,interpretation};
}

export function atlasNativeProfile(c,expected,data){
  const b=data?.atlasBinding;
  atlasAssert(b&&['caseId','recordVersion','manifestSha256','gridId'].every(k=>b[k]===c[k]),'Native result is bound to a different record or grid.');
  atlasAssert(b.selection?.kind===expected.kind&&(expected.kind==='point'?
    b.selection.row===expected.row&&b.selection.col===expected.col:
    JSON.stringify(b.selection.vertices)===JSON.stringify(expected.vertices)),'Native result is bound to a different footprint.');
  const p=data.profile;
  atlasAssert(Array.isArray(p?.observations)&&p.observations.length===c.observations.length&&
    p.observations.every((x,i)=>x.timestamp===c.observations[i].utc&&x.observation_id===c.observations[i].id),
    'Native result does not match this observation series.');
  return p;
}
