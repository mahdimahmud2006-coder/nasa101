/** Presentation of saved diagonal-only products; deterministic fixed-footprint CPR arithmetic. */
import {intervalForVisit,canJoinObservations} from './time-axis.mjs';
const escape=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=v=>v===null||v===undefined?'Unavailable':Number(v).toLocaleString('en-US',{maximumFractionDigits:3});
const date=v=>new Date(v).toLocaleDateString('en-GB',{day:'2-digit',month:'short',timeZone:'UTC'});
export const dualpolLayerNames=['hh_fixed','hv_fixed','cpr','composite','hh_baseline','hv_baseline','cpr_baseline','hh_successive','hv_successive','cpr_successive','hint_low','hint_hh','hint_hv'];
export function extensionMatches(extension,data){return !!extension&&extension.case_id===data.case_id&&JSON.stringify(extension.grid)===JSON.stringify(data.grid)&&extension.observations.length===data.observations.length&&extension.observations.every((r,i)=>r.timestamp===data.observations[i].timestamp&&r.source_granule_id===data.observations[i].source_granule_id);}
export function dualpolLayers(extension,index){return extension?dualpolLayerNames.filter(k=>extension.observations[index]?.layers[k]):[];}
export function isDualpolLayer(layer){return dualpolLayerNames.includes(layer);}
export function canCompareDualpol(layer){return ['hh_fixed','hv_fixed','cpr','composite'].includes(layer);}
export function cprProfile(profile){
 if(!profile)return null;
 return {...profile,observations:profile.observations.map(r=>{
  const result={...r};
  for(const suffix of ['mean_db','baseline_delta_db','successive_delta_db']){const h=r['hh_'+suffix],v=r['hv_'+suffix];result['cpr_'+suffix]=h===null||h===undefined||v===null||v===undefined?null:v-h;}
  return result;
 }),cpr_definition:'HV_dB − HH_dB on the same fixed common-valid pixels; mean filtered log-power ratio, not ratio of spatial mean powers.'};
}
export function dualpolLegend(extension,layer){
 const limits=extension.display_limits;
 if(layer==='composite')return {title:'Polarimetric false colour · fixed stretches',low:'R: HH −30…0 · G: HV −40…−5',high:'B: HH−HV 0…20 dB',note:'Linear clipped RGB, identical for every case and visit. Colours describe the three channels; they are not a land-cover class.',ramp:null};
 if(layer.startsWith('hint_'))return {title:'Uncalibrated candidate signature',low:'Dark: other assessable pixels',high:'Light: candidate · transparent: unavailable',note:extension.hint_definitions[layer]+' These signatures do not uniquely identify a cause.',ramp:extension.palette_css.cividis};
 const change=layer.endsWith('_baseline')||layer.endsWith('_successive'),quantity=layer.split('_')[0].toUpperCase(),range=change?limits.change:limits[layer.replace('_fixed','')];
 return {title:quantity+(change?(layer.endsWith('_baseline')?' change from first visit':' change from preceding visit'):quantity==='CPR'?' cross-pol log-power ratio':' filtered log-backscatter')+' · dB',low:number(range[0])+' dB',high:number(range[1])+' dB',note:(quantity==='CPR'?'CPR = HV_dB − HH_dB; sign reversal of the preserved HH−HV ratio. ':'')+(change?'Vik diverging map centered at exactly 0 dB; paired-valid endpoints. ':'Cividis sequential map; fixed scale across cases and dates. ')+'Display can saturate; native COG values are not clipped.',ramp:extension.palette_css[change?'vik':'cividis']};
}
export function cprChart(profile,index,calendar){
 const rows=cprProfile(profile)?.observations||[],finite=rows.filter(r=>Number.isFinite(r.cpr_baseline_delta_db));
 if(!finite.length)return '<p>No CPR trace: insufficient common-valid pixels. Missing measurements remain unavailable.</p>';
 const w=760,h=245,l=65,r=28,t=22,b=52,start=Date.parse(rows[0].timestamp),end=Date.parse(rows.at(-1).timestamp),span=Math.max(1,end-start),lo=Math.min(0,...finite.map(r=>r.cpr_baseline_delta_db))-.5,hi=Math.max(0,...finite.map(r=>r.cpr_baseline_delta_db))+.5;
 const x=row=>l+(Date.parse(row.timestamp)-start)/span*(w-l-r),y=v=>t+(hi-v)/(hi-lo)*(h-t-b);
 let marks=`<line class="chart-zero" x1="${l}" x2="${w-r}" y1="${y(0)}" y2="${y(0)}"/><text x="8" y="18">Δ CPR · dB</text>`;
 for(const value of [lo,0,hi])marks+=`<text x="5" y="${y(value)+5}">${number(value)}</text>`;
 for(let i=1;i<rows.length;i++)if(Number.isFinite(rows[i-1].cpr_baseline_delta_db)&&Number.isFinite(rows[i].cpr_baseline_delta_db)&&canJoinObservations(calendar,rows[i-1].timestamp,rows[i].timestamp))marks+=`<path class="cpr-line" d="M${x(rows[i-1])},${y(rows[i-1].cpr_baseline_delta_db)}L${x(rows[i])},${y(rows[i].cpr_baseline_delta_db)}"/>`;
 for(const row of finite)marks+=`<circle cx="${x(row)}" cy="${y(row.cpr_baseline_delta_db)}" r="${rows.indexOf(row)===index?6:4}" fill="#d7c5ff"><title>${escape(date(row.timestamp))}: ${number(row.cpr_baseline_delta_db)} dB</title></circle>`;
 for(const i of [...new Set([0,Math.floor(rows.length/2),rows.length-1])])marks+=`<text x="${x(rows[i])}" y="${h-15}" text-anchor="middle">${escape(date(rows[i].timestamp))}</text>`;
 return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="CPR signed baseline difference, computed from HV minus HH on the selected fixed footprint; only observed visits">${marks}</svg>`;
}
export function sensitivityRows(sensitivity,index,mode='coupled'){
 const obs=sensitivity?.observations[index];if(!obs?.candidate_area_km2)return [];
 const mid=sensitivity.offsets_db.indexOf(0);
 return sensitivity.offsets_db.map((offset,i)=>{const h=mode==='hv'?mid:i,v=mode==='hh'?mid:i;return {offset_db:offset,hh_cutoff_db:obs.hh_cutoffs_db[h],hv_cutoff_db:obs.hv_cutoffs_db[v],candidate_pixels:obs.candidate_pixels[h][v],area_km2:obs.candidate_area_km2[h][v]};});
}
export function sensitivityHTML(sensitivity,index,mode='coupled'){
 const rows=sensitivityRows(sensitivity,index,mode),obs=sensitivity?.observations[index];
 if(!rows.length)return '<p>Sensitivity unavailable: no common-valid pixels across all loaded visits.</p>';
 const w=760,h=265,l=75,r=25,t=24,b=62,max=Math.max(.0001,...rows.map(d=>d.area_km2))*1.08,minX=rows[0].offset_db,maxX=rows.at(-1).offset_db;
 const x=d=>l+(d.offset_db-minX)/(maxX-minX)*(w-l-r),y=v=>t+(1-v/max)*(h-t-b);
 const path=rows.map((d,i)=>(i?'L':'M')+x(d)+','+y(d.area_km2)).join(' ');
 const marks=`<path class="chart-zero" d="M${l},${t}V${h-b}H${w-r}"/><text x="6" y="18">km²</text><text x="5" y="${t+8}">${number(max)}</text><text x="5" y="${h-b}">0</text><line class="nominal-guide" x1="${x({offset_db:0})}" x2="${x({offset_db:0})}" y1="${t}" y2="${h-b}"/><path class="sensitivity-line" d="${path}"/>`+rows.map(d=>`<circle cx="${x(d)}" cy="${y(d.area_km2)}" r="5"><title>HH ≤ ${d.hh_cutoff_db} dB; HV ≤ ${d.hv_cutoff_db} dB: ${number(d.area_km2)} km² (${d.candidate_pixels} pixels)</title></circle><text x="${x(d)}" y="${h-b+24}" text-anchor="middle">${d.offset_db>0?'+':''}${d.offset_db}</text>`).join('')+`<text x="${w/2}" y="${h-8}" text-anchor="middle">Cutoff offset from illustrative rule · dB</text>`;
 return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Radar-dark candidate area versus cutoff offset, ${mode} sweep, crop-wide fixed common-valid support. Zero offset is the illustrative rule.">${marks}</svg><p class="note">${obs.common_valid_pixels.toLocaleString('en-US')} fixed common pixels · ${number(obs.common_valid_area_km2)} km² assessable across every loaded visit. Zero offset is HH ≤ ${sensitivity.nominal_hh_db}, HV ≤ ${sensitivity.nominal_hv_db} dB. This curve describes sensitivity, not accuracy or uncertainty bounds.</p><details open><summary>Inspect exact cutoffs and pixel counts</summary><div class="dualpol-table-scroll"><table><thead><tr><th>HH cutoff · dB</th><th>HV cutoff · dB</th><th>Pixels</th><th>Area · km²</th></tr></thead><tbody>${rows.map(d=>`<tr><td>${d.hh_cutoff_db}</td><td>${d.hv_cutoff_db}</td><td>${d.candidate_pixels.toLocaleString('en-US')}</td><td>${number(d.area_km2)}</td></tr>`).join('')}</tbody></table></div></details>`;
}
export function dualpolDossier(extension,profile,index,sensitivity){
 if(!extension)return null;
 return {schema_version:1,status:'implemented',formula:extension.formulas,selected_footprint:cprProfile(profile),selected_visit:extension.observations[index],hint_scope:'Hint areas are crop-wide assessable support; they are not selected-footprint diagnoses.',hint_definitions:extension.hint_definitions,sensitivity:sensitivity?{...sensitivity,observations:[sensitivity.observations[index]]}:null,limitations:extension.limits,provenance:extension.provenance};
}
