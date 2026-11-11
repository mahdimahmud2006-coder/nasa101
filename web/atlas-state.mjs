export const labels={hh:'HH backscatter',hv:'HV backscatter',fraction:'Cross-polarized power share',coherence:'HH coherence · 20 m'};
export const lensLabels={river:'River Memory',wetland:'Wetland Pulse',surface:'Surface change'};
export const fmt=(n,digits=2)=>Number.isFinite(n)?n.toFixed(digits):'—';
export const iso=t=>String(t).slice(0,10);
export const db=n=>Number.isFinite(n)?fmt(n)+' dB':'No preceding measurement';
export const pairAt=(c,i)=>c.pairs.find(p=>p.dates[1]===c.observations[i].timestamp);
export const lenses=c=>c.case==='jamuna_river'?['river','surface']:c.case==='tanguar_wetland'?['wetland','surface']:['surface'];
export const indices=(c,k)=>c.observations.map((_,i)=>i).filter(i=>k!=='coherence'||pairAt(c,i));
export function nativeSelection(c,input){
  if(!input)return null;
  const [h,w]=c.grid.shape;
  const val=String(input).trim();if(val.length>6000)return null;
  if(/^\d+\s*,\s*\d+$/.test(val)){
    const [row,col]=val.split(',').map(Number);return row<h&&col<w?row+','+col:null;
  }
  try{
    const pts=JSON.parse(val);
    if(!Array.isArray(pts)||pts.length<3||pts.length>200)return null;
    if(!pts.every(v=>Array.isArray(v)&&v.length===2&&v.every(Number.isFinite)&&v[0]>=0&&v[0]<=w&&v[1]>=0&&v[1]<=h))return null;
    return JSON.stringify(pts);
  }catch{return null;}
}
export function atlasScenarioParameters(value){
  if(!value||!Number.isFinite(value.rainfall_multiplier)||value.rainfall_multiplier<.5||value.rainfall_multiplier>3||
    ![6,12,24,48,72].includes(value.duration_hours)||!['dry','normal','wet','saturated'].includes(value.wetness))return null;
  return {rainfall_multiplier:value.rainfall_multiplier,duration_hours:value.duration_hours,wetness:value.wetness};
}
export function selection(records,input={}){
  const c=records[input.case] && Object.hasOwn(records,input.case)?records[input.case]:(records.jamuna_river??Object.values(records)[0]);
  const layer=Object.hasOwn(labels,input.layer)&&(input.layer!=='coherence'||c.pairs.length)?input.layer:'hh';
  const available=indices(c,layer);
  const requested=c.observations.findIndex(o=>o.timestamp===input.date||iso(o.timestamp)===input.date);
  const index=available.includes(requested)?requested:available.at(-1);
  const n=Number(input.profile),native=nativeSelection(c,input.native);
  const date=c.observations[index].timestamp,ct=c.context;
  const t=ct?.thermal?.find(t=>t.source===input.thermal),scenario=ct?.scenarios?.[date]?.find(x=>x.id===input.scenario);
  const scenarioRun=!scenario&&input.scenarioRun?.anchorUtc===date&&ct?.scenarios?.[date]&&atlasScenarioParameters(input.scenarioRun);
  return {case:c.case,date,layer,...(t?{thermal:t.source}:{}),...(scenario?{scenario:scenario.id}:{}),
    ...(scenarioRun?{scenarioRun:{...scenarioRun,anchorUtc:date}}:{}),
    terrain:input.terrain==='on'&&layer!=='coherence'?'on':'off',bearing:[0,45,90,135,180,225,270,315].includes(Number(input.bearing))?Number(input.bearing):45,
    profile:Number.isInteger(n)&&n>=0&&n<c.profiles.length?n:0,
    ...(native?{native}:{}),
    lens:lenses(c).includes(input.lens)?input.lens:lenses(c)[0],
    split:Math.max(0,Math.min(100,Math.round(Number(input.split)||0)))};
}
export function hashOf(state){return '#'+new URLSearchParams({atlas:'1',...state});}

export function atlasEdition(catalog,caseId,portable){
  const c=catalog[caseId];
  return {footprints:portable?c.capabilities.portableFootprints:c.capabilities.localFootprints,
    layers:c.capabilities.layers,lenses:c.capabilities.lenses,context:c.context,
    label:portable?'Offline edition · saved observations and footprints':'Local edition · saved and native footprints'};
}

export function atlasStore(records,initial){
  let current=selection(records,initial);
  return {get:()=>current,
    update(changes){current=selection(records,{...current,...changes});return current;},
    restore(next){current=selection(records,next);return current;}};
}
