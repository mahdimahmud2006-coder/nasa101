import {atlasNode,atlasElement,atlasOptions} from './atlas-dom.mjs';
import {iso,fmt,atlasScenarioParameters} from './atlas-state.mjs';

const atlasUtc=t=>t?t.replace('T',' ').replace('Z',' UTC'):'Unavailable';
const atlasOffset=(timestamp,anchor)=>fmt((Date.parse(timestamp)-Date.parse(anchor))/3600000,2)+' h from radar';
const atlasPercent=f=>Number.isFinite(f)?fmt(100*f,1)+'%':'Unavailable';
const atlasImage=(src,alt)=>{const img=atlasElement('img');img.src=src;img.alt=alt;return img;};

export function atlasContextDetails(meta,o,s){
  const env=meta?.environment;
  if(!env)return null;
  const saved=s.native?null:meta.footprints[s.profile];
  const optical=env.optical[saved?.opticalFootprintId]?.[o.observation_id]??null;
  const thermal=s.thermal?env.thermal[s.thermal]:null;
  return {
    imerg:env.imerg[o.observation_id]??null,rain:env.rain[o.observation_id]??null,
    rainSource:env.rainSource??null,optical,opticalPolicy:env.opticalPolicy??null,
    thermal:thermal?{...thermal,sourceId:s.thermal,offsetSeconds:(Date.parse(thermal.utc)-Date.parse(o.timestamp))/1000}:null,
    thermalPolicy:env.thermalPolicy??null,
  };
}

function atlasScenarioText(v){
  return 'High-index area '+fmt(v.summary.high_susceptibility_area_km2)+' km² versus '+
    fmt(v.summary.baseline_high_area_km2)+' km² in the model baseline. Valid model coverage '+atlasPercent(v.summary.coverage_fraction)+'.';
}

function renderAtlasScenario({c,o,s,meta,set,portable,live,retry}){
  const $=atlasNode,el=atlasElement;
  const section=$('scenario-section'),status=$('scenario-status'),output=$('scenario-output'),form=$('scenario-form');
  const anchor=meta?.environment?.scenario?.anchors[o.observation_id];
  const presets=c.context?.scenarios?.[o.timestamp]??[];
  const select=$('scenario-select');
  $('scenario-presets').hidden=!presets.length;
  atlasOptions(select,[['','Choose a saved scenario'],...presets.map(v=>[v.id,v.parameters.rainfall_multiplier+'× rain · '+v.parameters.duration_hours+' h · '+v.parameters.wetness])],s.scenario??'');
  select.onchange=()=>set({scenario:select.value,scenarioRun:null});
  form.hidden=portable||!anchor;
  status.textContent=live.status||(!anchor?'Scenario inputs are unavailable for this case and visit.':portable?'This edition includes saved scenario results.':'');
  output.replaceChildren();
  const binding=[c.case,o.observation_id].join(':');
  if(section.dataset.anchor!==binding){
    section.dataset.anchor=binding;
    $('scenario-multiplier').value='1.5';
    $('scenario-duration').value='48';
    $('scenario-wetness').value='wet';
  }
  if(s.scenarioRun&&section.dataset.request!==JSON.stringify(s.scenarioRun)){
    $('scenario-multiplier').value=s.scenarioRun.rainfall_multiplier;
    $('scenario-duration').value=s.scenarioRun.duration_hours;
    $('scenario-wetness').value=s.scenarioRun.wetness;
  }
  section.dataset.request=JSON.stringify(s.scenarioRun??null);
  form.onsubmit=event=>{
    event.preventDefault();
    const parameters=atlasScenarioParameters({rainfall_multiplier:Number($('scenario-multiplier').value),
      duration_hours:Number($('scenario-duration').value),wetness:$('scenario-wetness').value});
    if(!parameters){status.textContent='Choose a multiplier from 0.5 to 3, a duration, and a wetness assumption.';return;}
    retry();set({scenario:'',scenarioRun:{...parameters,anchorUtc:o.timestamp}});
  };
  const saved=presets.find(v=>v.id===s.scenario),v=live.result??saved;
  if(!v)return;
  const params=v.parameters;
  const inputWindow=v.rainfall_window??meta.environment.rain[o.observation_id]?.rain_168h?.window;
  const end=inputWindow?.end_utc??inputWindow?.end_exclusive_utc;
  output.append(el('strong',saved?'Saved model scenario':'Local model scenario'),
    el('p',atlasScenarioText(v)),el('p',params.rainfall_multiplier+'× the last '+params.duration_hours+
      ' complete hours · '+params.wetness+' wetness assumption · cutoff '+atlasUtc(end)+'.'),
    atlasImage(v.preview_url??v.image,'Uncalibrated flood attention model preview for '+iso(o.timestamp)));
  const method=el('details'),summary=el('summary','Scenario provenance');
  method.append(summary,el('p','Radar anchor '+atlasUtc(o.timestamp)+' · '+params.observation_id+' · model '+v.model_version+'.'),
    el('p','Input SHA-256 '+v.inputs_sha256+'.'));
  output.append(method);
}

export function renderAtlasContext(c,o,p,s,set,disclosure,meta,portable,live,retry){
  const $=atlasNode,el=atlasElement;
  const box=$('ancillary'),focus=document.activeElement?.id;
  box.replaceChildren();
  const details=atlasContextDetails(meta,o,s);
  if(!details)return;
  const cover=s.native?p.historical_land_cover:meta.footprints[s.profile]?.historicalLandCover;
  if(cover?.validCells>0){
    const ha=n=>fmt(n*cover.radarCellAreaM2/10000)+' ha';
    box.append(el('h3','Historical land cover · ESA WorldCover 2021'),
      el('p',ha(cover.croplandCells)+' mapped cropland · '+ha(cover.builtUpCells)+' mapped built-up land on this footprint.'),
      el('p',cover.validCells.toLocaleString()+' of '+cover.pairedCells.toLocaleString()+
        ' paired-valid radar cells overlap the historical map. A current site check can establish today’s land use.'));
  }
  const opticalPreview=p.reference_matches?.[o.timestamp];
  const optical=details.optical;
  const opticalSection=el('section');
  opticalSection.append(el('h3','Optical reference'));
  if(optical?.reference_timestamp){
    const clear=optical.clear_assessable_pixels,policy=details.opticalPolicy;
    opticalSection.append(el('p',(clear?'Date-matched HLS context':'HLS scene has no assessable pixels')+' · '+
      atlasUtc(optical.reference_timestamp)+' · '+atlasOffset(optical.reference_timestamp,o.timestamp)+
      ' · '+policy.resolutionM+' m · '+clear.toLocaleString()+' of '+optical.reference_pixels.toLocaleString()+' eligible reference pixels.'),
      el('p',optical.reference_id+' · Frozen match window ±'+(policy.timeToleranceSeconds/86400)+' days. '+policy.qa));
    if(clear&&opticalPreview?.image)opticalSection.append(atlasImage(opticalPreview.image,'HLS reference for this footprint on '+iso(optical.reference_timestamp)));
  }else opticalSection.append(el('p','No accepted optical match for this footprint and visit.'));
  box.append(opticalSection);
  box.append(el('h3','Antecedent precipitation'));
  if(details.rain){
    const grid=details.rainSource.native_resolution_degrees;
    box.append(el('p','NASA POWER hourly model and reanalysis context · '+grid.latitude+'° latitude × '+grid.longitude+
      '° longitude. Values summarize the Kathmandu study crop.'));
    for(const [key,r] of Object.entries(details.rain)){
      const w=r.window;
      box.append(el('p',key.slice(5)+' · '+(Number.isFinite(r.meanMm)?fmt(r.meanMm)+' mm':'Unavailable')+' · '+
        atlasUtc(w.start_inclusive_utc)+' → '+atlasUtc(w.end_exclusive_utc)+' · cutoff '+fmt(w.end_lag_seconds/60,1)+
        ' min before radar · '+w.bin_count+' expected hourly bins · '+atlasPercent(r.validCropFraction)+' crop coverage.'));
    }
  }else box.append(el('p','No matched POWER precipitation window for this case and visit.'));
  const imerg=details.imerg;
  if(imerg)box.append(el('p','IMERG Final V07 · unavailable · '+imerg.acceptedBins+' of '+imerg.expectedBins+
    ' overlapping half-hour bins admitted at 0.1° for the '+atlasUtc(imerg.startUtc)+' → '+atlasUtc(imerg.endUtc)+' window.'));

  if(c.context){
    const ct=c.context;
    for(const [key,name] of [['flood','Flood attention'],['landslide','Hillside susceptibility']]){
      const m=ct.models[key][o.timestamp];
      if(m)box.append(el('p',name+' · exploratory crop mean index '+fmt(m.mean_score)+' / 100 on '+atlasUtc(o.timestamp)),
        atlasImage(m.image,name+' model preview for '+iso(o.timestamp)));
    }
    const detail=el('details');detail.open=disclosure.thermal;
    detail.ontoggle=()=>{disclosure.thermal=detail.open;};
    detail.append(el('summary','Independently dated Landsat temperature'));
    const label=el('label','Thermal acquisition'),select=el('select');
    select.id='at-thermal-select';label.append(select);detail.append(label);box.append(detail);
    atlasOptions(select,[['','Choose a Landsat scene'],...ct.thermal.map(t=>[t.source,atlasUtc(t.timestamp)])],s.thermal??'');
    select.onchange=()=>{disclosure.thermal=true;set({thermal:select.value});};
    const t=details.thermal,policy=details.thermalPolicy;
    if(t){
      detail.append(el('p',atlasUtc(t.utc)+' · '+atlasOffset(t.utc,o.timestamp)+' · '+s.thermal+
        ' · '+(Number.isFinite(t.meanC)&&t.validFraction>0?fmt(t.meanC)+' °C crop mean':'Unavailable')+
        ' · '+atlasPercent(t.validFraction)+' QA-valid coverage. Native '+policy.native_thermal_resolution_m+
        ' m thermal samples on a '+policy.analysis_grid_m+' m grid.'),
      el('p',policy.qa_rule));
      if(t.validFraction>0)detail.append(atlasImage(ct.thermal.find(scene=>scene.source===s.thermal).image,'QA-screened land surface temperature'));
    }else detail.append(el('p','Select a scene to view its actual date and offset from the radar visit.'));
    if(focus===select.id)document.getElementById(focus)?.focus();
  }else box.append(el('p','No accepted thermal scenes in this study window.'));
  renderAtlasScenario({c,o,s,meta,set,portable,live,retry});
}
