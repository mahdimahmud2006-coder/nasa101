import {atlasElement,atlasNode} from './atlas-dom.mjs';
import {fmt} from './atlas-state.mjs';

const atlasGcovRule='Valid GCOV subswaths use codes 1–254. Code 0 marks invalid or partly focused samples and 255 marks fill. Diagonal power and number of looks must be finite and positive.';
const atlasGunwRule='Native GUNW coherence uses valid reference and secondary subswaths, clear anomaly bits and a finite value in [0,1]. The water flag does not exclude a cell.';
const atlasTerrainNames={dem:'Elevation',slope:'Slope',aspect:'Aspect',relative_elevation:'Relative elevation',
  flow_accumulation:'Modeled contributing area',twi:'Topographic wetness index',drainage_distance:'Modeled drainage distance',
  geometry_candidates:'Modeled geometry screening'};
const atlasTerrainUnits={dem:'m',slope:'degrees',aspect:'degrees',relative_elevation:'m',flow_accumulation:'m²',
  twi:'index',drainage_distance:'m',geometry_candidates:'flags'};

export function atlasQualityEvidence(meta,o,s){
  if(!meta?.quality)return null;
  const terrain=meta.quality.terrain;
  const {controls,...terrainEvidence}=terrain;
  const pair=s.layer==='coherence'?meta.pairs.find(p=>p.secondId===o.observation_id):null;
  return {observationId:o.observation_id,gcov:meta.quality.gcov[o.observation_id],gcovPolicy:atlasGcovRule,
    radarPixelAreaKm2:Math.abs(meta.grid.affine[0]*meta.grid.affine[4]-meta.grid.affine[1]*meta.grid.affine[3])/1e6,
    gunw:pair?{id:pair.id,firstUtc:pair.startUtc,lastUtc:pair.endUtc,statistics:meta.quality.gunw[pair.id],policy:atlasGunwRule}:null,
    terrain:terrainEvidence,radiometricControl:controls[o.observation_id]??null};
}

export function atlasDualpolEvidence(c,meta,o,p,s){
  const summary=s.native?p.dualpol?.[o.observation_id]:meta?.footprints[s.profile]?.dualpol?.[o.observation_id];
  return {
    observationId:o.observation_id,sourceId:o.source_granule_id,summary:summary??null,
    scope:'Selected footprint, on the same HH/HV-valid native pixels across recorded visits.',
    hh:{unit:'dB',scale:c.limits.hh},hv:{unit:'dB',scale:c.limits.hv},
    cpr:{unit:'dB',formula:'HV_dB − HH_dB',domain:'Finite paired log-powers. Positive CPR means HV exceeds HH.'},
    powerShare:{unit:'fraction',scale:[0,1],formula:'P_HV / (P_HH + P_HV)',definition:'Mean of pixelwise shares after converting dB to linear power.'},
    unavailable:{
      DpRVI:'Requires an accepted complex HH–HV covariance term.',
      DpRVIc:'Transfer from the published detected GRD method to these filtered NISAR gamma-zero powers has not been verified.',
    },
  };
}

export function renderAtlasQuality(c,meta,o,p,s,portable){
  const $=atlasNode,el=atlasElement;
  const dualpol=atlasDualpolEvidence(c,meta,o,p,s),dp=$('dualpol'),q=$('quality');
  dp.replaceChildren();q.replaceChildren();
  const addRaster=(parent,text,href)=>{
    if(portable||!href)return;
    const link=el('a',text);link.href=href;link.download='';parent.append(link);
  };
  const summary=dualpol.summary;
  dp.append(el('p',dualpol.scope));
  if(summary?.validPixels){
    dp.append(el('p','Mean HH '+fmt(summary.hhDb)+' dB · Mean HV '+fmt(summary.hvDb)+' dB · Mean CPR '+fmt(summary.cprDb)+
      ' dB · Mean cross-polarized power share '+fmt(100*summary.powerShare,2)+'%.'),
      el('p',summary.validPixels.toLocaleString()+' paired-valid pixels · '+summary.crossDominantPixels.toLocaleString()+' with HV greater than HH.'));
  }else dp.append(el('p','No supported dual-pol summary for this footprint.'));
  dp.append(el('p','HH/HV means use filtered gamma-zero in dB. CPR is HV − HH in dB. The 0–100% power share averages per-pixel fractions in linear power.'),
    el('p','Fixed map scales · HH '+c.limits.hh.join(' to ')+' dB · HV '+c.limits.hv.join(' to ')+' dB · power share 0–100%.'));
  const quality=atlasQualityEvidence(meta,o,s);
  if(!quality)return;
  const gcov=quality.gcov,terrain=quality.terrain;
  const counts=(row,area)=>['assessed','masked','excluded'].map(k=>k+' '+row[k].toLocaleString()+
    ' ('+fmt(row[k]*area,3)+' km²)').join(' · ');
  q.append(el('h3','Radar input quality'),el('p',quality.gcovPolicy),
    el('p','Saturation or visibility flags are not carried in this GCOV validity mask. Geometry screening is shown separately.'),
    el('p','Whole radar crop · '+o.processing_release+' · '+o.source_granule_id));
  if(gcov)for(const channel of ['hh','hv']){
    const row=gcov[channel];
    q.append(el('p',channel.toUpperCase()+' · '+counts(row,quality.radarPixelAreaKm2)+
      '. Raw source codes '+row.sourceMaskCodes.join(', ')+' · '+row.sourceMasked.toLocaleString()+' source samples masked. '+row.alignment+'.'));
    addRaster(q,'Download '+channel.toUpperCase()+' raster with nodata mask',row.raster);
  }
  if(quality.gunw){
    const stats=quality.gunw.statistics;
    q.append(el('p','Coherence · 20 m pair '+quality.gunw.firstUtc+' → '+quality.gunw.lastUtc+' · '+
      counts({assessed:stats.valid_pixels,masked:stats.total_pixels-stats.valid_pixels,excluded:0},.0004)+'.'),
      el('p',quality.gunw.policy));
    addRaster(q,'Download native coherence QA mask',stats.sourceMask);
    addRaster(q,'Download decoded coherence validity mask',stats.validMask);
    addRaster(q,'Download HH coherence GeoTIFF · 20 m',stats.coherenceRaster);
    addRaster(q,'Download HH coherence GeoTIFF · 80 m',stats.coherenceRaster80);
  }
  q.append(el('h3','Terrain context'),el('p',terrain.source+' · '+terrain.verticalDatum+' · '+terrain.nativeResolution+
    ' source samples on a '+terrain.grid.resolution_m+' m '+terrain.grid.crs+' grid. Static context for this study window.'),
    el('p',terrain.demVoidCells.toLocaleString()+' DEM void cells · '+terrain.nearFlatCells.toLocaleString()+' slope cells below 0.01°.'));
  const layers=el('details');layers.append(el('summary','Assessable area by terrain layer'));
  for(const [name,row] of Object.entries(terrain.layers)){
    const area=terrain.grid.resolution_m**2/1e6;
    layers.append(el('p',atlasTerrainNames[name]+' · '+counts(row,area)+'. Display '+row.scale.join(' to ')+' '+atlasTerrainUnits[name]+'.'));
    addRaster(layers,'Download '+atlasTerrainNames[name].toLowerCase()+' raster',row.raster);
  }
  q.append(layers,el('p','Geometry flags use the '+terrain.geometrySpacingM+' m look metadata from '+terrain.geometrySource+
    ' at '+terrain.geometryHeightEllipsoidM+' m above the ellipsoid. Flagged cells are excluded from that screening tally only.'),
    el('p','Modeled D8 routing ends at open DEM boundaries and void edges. Routing used a '+terrain.routingBufferM.toLocaleString()+' m buffer with '+terrain.hydrology.outlet_count.toLocaleString()+
    ' open outlet cells. Contributing area beyond that domain is unresolved.'));
  const sensitivity=terrain.hand.cropOnlySensitivity;
  if(sensitivity){
    const audit=el('details');audit.append(el('summary','Crop-only HAND sensitivity'));
    for(const [threshold,row] of Object.entries(sensitivity)){
      audit.append(el('p',fmt(Number(threshold)/1e6,1)+' km² drainage threshold · '+row.assessed.toLocaleString()+
        ' assessed · '+row.boundaryAffected.toLocaleString()+' open-outlet paths · '+row.masked.toLocaleString()+
        ' DEM-masked · '+(row.negativeHeight+row.unresolved).toLocaleString()+' other unresolved cells.'));
    }
    q.append(audit);
  }
  const control=quality.radiometricControl;
  if(control)q.append(el('p','Putative stable controls · '+control.common_control_pixels.toLocaleString()+' pixels · HH shift '+fmt(control.hh_baseline_shift_db)+
    ' dB · HV shift '+fmt(control.hv_baseline_shift_db)+' dB · control reference '+terrain.controlReferenceUtc+'.'));
}
