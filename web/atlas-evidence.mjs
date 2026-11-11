import {atlasMakeState,atlasVersionedHash,atlasMeasurement} from './atlas-contract.mjs';
import {labels,pairAt,hashOf} from './atlas-state.mjs';
import {atlasComparison,atlasTraceSupport,atlasChronology,atlasDefaultThreshold} from './atlas-chronology.mjs';
import {atlasCompatibility} from './atlas-compatibility.mjs';
import {atlasContextDetails} from './atlas-context.mjs';
import {atlasQualityEvidence,atlasDualpolEvidence} from './atlas-quality.mjs';
import {atlasPairEvidence} from './atlas-pairs.mjs';
import {atlasFieldReview} from './atlas-review.mjs';
export function observationPacket(records,s,liveProfile=null,catalog=null,threshold=atlasDefaultThreshold,liveScenario=null){
  const c=records[s.case],i=c.observations.findIndex(o=>o.timestamp===s.date),o=c.observations[i],p=s.native?liveProfile:c.profiles[s.profile];
  if(!p)throw Error('The requested footprint has no measured profile.');
  const pair=s.layer==='coherence'?pairAt(c,i):null;
  const state=catalog?atlasMakeState(catalog,s):null;
  const meta=catalog?.[c.case],gaps=meta?.acquisitionGaps??[];
  const support=atlasTraceSupport(p,s.native?p.footprint_pixels:meta?.footprints[s.profile]?.footprintPixels);
  const comparisonsAt=j=>({
    recent:atlasComparison(c,p,j,'successive',support,gaps),reference:atlasComparison(c,p,j,'reference',support,gaps)
  });
  const comparisons=comparisonsAt(i);
  const pairs=atlasPairEvidence(meta,o,s,p);
  const field=atlasFieldReview(c,meta,p,s);
  const fieldReview=field?{...field,area:{studyBoundary:c.scope_area,drawnBoundary:p.boundary_area??null,
      pairedSupportKm2:p.area_km2,mappedClassKm2:null,areaAdjustedKm2:null,exposureEstimate:null},
    map:{layer:s.layer,scope:'Study window previews with fixed display limits; the footprint location is separate.',
      reference:c.observations.find(r=>r.timestamp===c.reference).images[s.layer],selected:o.images[s.layer]}}:null;
  const typed=state?Object.entries(p.series[i]).map(([quantity,v])=>{
    const trace=quantity.endsWith('_successive')?comparisons.recent:comparisons.reference;
    const value=trace.values[quantity.slice(0,2)];
    return {...atlasMeasurement({quantity,unit:trace.unit,value,
      status:value!==null?'measured':!trace.target?'out_of_scope':Number.isFinite(v)||v==null?'missing':'invalid',
      sourceIds:[trace.current.sourceId,...(trace.target?[trace.target.sourceId]:[])],
      support:{...support,gridId:state.gridId},
      method:support.method,
      interpretation:'Signed difference between radar observations. Physical interpretation needs independent evidence.'}),
      endpoints:{selected:trace.current,comparison:trace.target}};
  }):null;
  return {schema:'terrapulse.atlas-investigation.v1',view:state?atlasVersionedHash(state):hashOf(s),...(state?{contract:state,measurementRecords:typed}:{}),study:c.title,case_id:c.case,manifest_sha256:c.manifest_sha256,
    display_quantity:labels[s.layer],display_definition:s.layer==='fraction'?'HV / (HH + HV), in linear power from paired filtered native dB samples.':labels[s.layer],selected_utc:o.timestamp,reference_utc:c.reference,preceding_utc:i?c.observations[i-1].timestamp:null,
    context:contextEvidence(c,s,liveScenario),environmental_context:atlasContextDetails(meta,o,s),
    quality:atlasQualityEvidence(meta,o,s),dualpol:atlasDualpolEvidence(c,meta,o,p,s),source_granule:o.source_granule_id,reference_granule:c.observations.find(r=>r.timestamp===c.reference).source_granule_id,
    historical_land_cover:s.native?p.historical_land_cover??null:meta?.footprints[s.profile]?.historicalLandCover??null,
    doi:o.doi,track:o.track,frame:o.frame,release:o.processing_release,grid:c.grid,study_window_boundary:c.scope_area,
    terrain_source_manifest_sha256:c.terrain.source_manifest_sha256,measurement:'Fixed footprint; differences in decibels on common-valid native pixels.',
    footprint:p.label,drawn_boundary:p.boundary_area??null,native_selection:s.native??null,native_support:p.native_support??null,native_means:p.native_means?.[i]??null,common_valid_pixels:p.valid_pixels,common_valid_area_km2:p.area_km2,
    measurements:p.series[i],comparisons,chronology:atlasChronology(c,p,i,threshold),acquisition_gaps:gaps,
    compatibility:atlasCompatibility(meta,p,s.native?null:s.profile,o.observation_id),
    history:p.series.map((r,j)=>({timestamp:c.observations[j].timestamp,observation_id:c.observations[j].observation_id,...r,
      comparison_endpoints:{recent:c.observations[j-1]?.observation_id??null,reference:comparisons.reference.target?.id??null},
      ...(p.native_means?{native_mean_db:p.native_means[j]}:{})})),
    pair:pair?{source:pair.source,timestamps:pair.dates,quantity:'Measured coherence; 0–1, not displacement.'}:null,
    pair_comparison:pair?c.pair_comparison:null,coherence_evidence:pairs,field_review:fieldReview,
    independent_validation:meta?.claimReview??null,explanations:p.fits?.[i]??null,optical_reference:referenceInfo(p,o.timestamp),extent_response:o.response,follow_up:guidance(c,s).next,limits:'Candidate interpretations require independent, dated corroboration. Study boundary is separate from assessed footprint.'};
}
function contextEvidence(c,s,liveScenario){
  if(!c.context)return null;
  const ct=c.context,t=ct.thermal.find(t=>t.source===s.thermal);
  const saved=ct.scenarios[s.date]?.find(x=>x.id===s.scenario),scenario=liveScenario??saved;
  return {thermal:t?{source:t.source,timestamp:t.timestamp,mean_c:t.mean_c,valid_fraction:t.valid_fraction,scope:'Kathmandu crop; independently dated.'}:null,
    rain:ct.rain[s.date]??null,rain_source:'NASA POWER, available matched crop summaries only',
    counterfactual:scenario?{id:scenario.id??scenario.scenario_id,edition:saved?'saved':'local',radar_anchor_utc:s.date,rainfall_window:scenario.rainfall_window??null,parameters:scenario.parameters,model_version:scenario.model_version,inputs_sha256:scenario.inputs_sha256,summary:scenario.summary,scope:'Uncalibrated historical scenario; not observed flood extent.'}:null};
}
function referenceInfo(profile,date){
  const m=profile.reference_matches?.[date];
  if(!m)return null;
  const {image,...evidence}=m;return evidence;
}
export function guidance(c,s){
  if(s.lens==='river')return {question:'Which river signals recur?',next:'Check a recurring radar-dark patch against a dated bank outline or gauge record before attributing it to channel migration.'};
  if(s.lens==='wetland')return {question:'How does the wetland response vary?',next:'Compare both polarizations and request a dated water-depth or habitat observation. A dark visit alone cannot establish inundation duration.'};
  if(c.country==='Nepal')return {question:'Did the change persist?',next:'Check independently dated imagery or an event inventory against the footprint. If the radar difference remains unexplained, request a field review.'};
  return {question:'What still differs from the reference?',next:'Compare the same footprint across both channels. Check a dated optical view or site observation before assigning a cause.'};
}
