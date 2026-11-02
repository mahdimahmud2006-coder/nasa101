/** Pure presentation policies; measurements and classifications stay in saved scientific outputs. */
export const basicLayers=['hh','hv','ratio','baseline','successive'];
export function availableLayers(module,index){return [...basicLayers.filter(v=>v!=='successive'||index>0),...(module==='river'?['river','water','occupancy']:module==='wetland'?['wetland','water','occupancy']:[])];}
export function safeLayer(layer,module,index){const options=availableLayers(module,index);return options.includes(layer)?layer:'hh';}
export function canCompare(layer){return layer==='hh'||layer==='hv';}
export function pixelFromPointer(rect,x,y,shape){
 const [height,width]=shape,scale=Math.min(rect.width/width,rect.height/height),left=rect.left+(rect.width-width*scale)/2,top=rect.top+(rect.height-height*scale)/2;
 const col=Math.floor((x-left)/scale),row=Math.floor((y-top)/scale);
 return row>=0&&row<height&&col>=0&&col<width?{row,col}:null;
}
export function finding(profile,index,threshold=3){
 const row=profile?.observations[index];
 if(!row||row.hh_baseline_delta_db===null)return 'This footprint lacks enough common-valid pixels across the channels and visits. No missing measurement is replaced with zero.';
 if(index===0)return 'This is the first observed baseline. There is no preceding-visit difference, and the baseline is not independently established as an undisturbed state.';
 if(Math.abs(row.hh_baseline_delta_db)>=threshold&&Math.abs(row.hh_successive_delta_db)<threshold)return 'A baseline HH difference persists while the latest HH change is smaller. Reduced new change does not establish a return to baseline or physical recovery.';
 return 'These are measured backscatter differences on the same pixels. Moisture, roughness, vegetation and measurement effects remain competing explanations.';
}
export function dossier(manifest,profile,index,layer){return {schema_version:1,project:'TerraPulse',case_id:manifest.case_id,module:manifest.module,selected_observation_id:manifest.observations[index].observation_id,selected_layer:layer,baseline_observation_id:manifest.baseline_observation_id,collection:manifest.collection,grid:manifest.grid,selected_footprint:profile,observations:manifest.observations.map(({observation_id,timestamp,source_granule_id,product_version,processing_release,quality,doi,response})=>({observation_id,timestamp,source_granule_id,product_version,processing_release,quality,doi,response})),reference:manifest.reference,thresholds:manifest.thresholds,formulas:manifest.formulas,provenance:manifest.provenance,limitations:manifest.limitations,cause_status:'UNRESOLVED',prediction_status:'NOT_A_FORECAST'};}
