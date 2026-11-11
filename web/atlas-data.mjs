import {atlasNativeProfile} from './atlas-contract.mjs';

/** Measure a candidate footprint without changing the displayed selection. */
export function createAtlasProbe({catalog,fetcher=(...args)=>fetch(...args)}){
  let pending=null;
  function cancel(){
    pending?.abort();
    pending=null;
  }
  async function measure(c,native){
    cancel();
    const request=new AbortController();
    pending=request;
    const polygon=native.startsWith('['),[row,col]=polygon?[]:native.split(',').map(Number);
    const expected=polygon?{kind:'polygon',vertices:JSON.parse(native)}:{kind:'point',row,col};
    try{
      const res=await fetcher('/api/cases/'+c.case+'/atlas-native',{
        method:'POST',headers:{'Content-Type':'application/json'},signal:request.signal,
        body:JSON.stringify({selection:expected})
      });
      const data=await res.json().catch(()=>null);
      if(request.signal.aborted)return null;
      if(!res.ok)throw Error(data?.error||'The native footprint could not be measured.');
      const meta=catalog[c.case];
      const p=atlasNativeProfile(meta,expected,data);
      const reference=meta.observations.find(o=>o.id===meta.referenceId);
      const nativeExplanations=Object.fromEntries((data.explanations??[])
        .filter(v=>v.model_version===meta.hypotheses?.version&&v.reference_timestamp===reference?.utc&&
          v.common_valid_pixels===p.common_valid_pixels&&meta.observations.some(o=>o.id===v.observation_id&&o.utc===v.timestamp))
        .map(v=>[v.observation_id,v.hypotheses]));
      return {label:p.label,valid_pixels:p.common_valid_pixels,area_km2:p.common_valid_area_km2,footprint_pixels:p.footprint_pixels,dualpol:p.dualpol,review:p.review,coherence:p.coherence,boundary_area:p.boundary_area,
        native_support:data.support,field_location:p.field_location,historical_land_cover:p.historical_land_cover,
        native_means:p.observations.map(r=>({hh:r.hh_mean_db,hv:r.hv_mean_db})),
        series:p.observations.map(r=>Object.fromEntries(['hh','hv'].flatMap(k=>[[k+'_reference',r[k+'_reference_delta_db']??null],[k+'_successive',r[k+'_successive_delta_db']??null]]))),
        fits:data.explanations?.map(v=>v.hypotheses),
        nativeExplanations};
    }catch(error){
      if(request.signal.aborted)return null;
      throw error;
    }finally{
      if(pending===request)pending=null;
    }
  }
  return {measure,cancel};
}
