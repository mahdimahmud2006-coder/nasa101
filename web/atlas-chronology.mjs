import {iso,fmt} from './atlas-state.mjs';

export const atlasDefaultThreshold=3;
const atlasHalfPeak=.5;
const atlasDayMs=86400000;

export function atlasVisitLabel(c,o){
  const day=iso(o.timestamp);
  return c.observations.some(other=>other!==o&&iso(other.timestamp)===day)
    ?o.timestamp.replace('T',' ').replace('Z',' UTC')
    :day;
}

export function atlasSignedDb(value){
  if(!Number.isFinite(value))return 'Unavailable';
  return (value>0?'+':'')+fmt(value)+' dB';
}

export function atlasTraceSupport(p,footprintPixels){
  return {footprintLabel:p.label,validPixels:p.valid_pixels,footprintPixels:footprintPixels??null,
    coverage:footprintPixels?p.valid_pixels/footprintPixels:null,
    policy:'Same native pixels with valid HH and HV in every recorded visit.',
    method:'Difference of arithmetic mean backscatter in dB, or equivalently the mean of pixelwise dB differences on common support.'};
}

export function atlasGapBetween(first,last,gaps){
  const start=Date.parse(first),end=Date.parse(last);
  return gaps.some(g=>start<Date.parse(g.end)&&end>Date.parse(g.start));
}

export function atlasComparison(c,p,i,kind,support,gaps=[]){
  const current=c.observations[i];
  const target=kind==='successive'?c.observations[i-1]:c.observations.find(o=>o.timestamp===c.reference);
  const values=Object.fromEntries(['hh','hv'].map(channel=>{
    const value=p.series[i]?.[channel+'_'+kind];
    return [channel,target&&support.validPixels>0&&Number.isFinite(value)?value:null];
  }));
  const endpoint=o=>o?{id:o.observation_id,utc:o.timestamp,sourceId:o.source_granule_id}:null;
  const elapsedDays=target?(Date.parse(current.timestamp)-Date.parse(target.timestamp))/atlasDayMs:null;
  const chronological=target?[target.timestamp,current.timestamp].sort():[];
  return {current:endpoint(current),target:endpoint(target),unit:'dB',sign:'selected minus comparison visit',values,support,elapsedDays,
    documentedGap:!!target&&elapsedDays!==0&&atlasGapBetween(...chronological,gaps)};
}

export function atlasChronology(c,p,i,threshold=atlasDefaultThreshold){
  const thresholdDb=Number.isFinite(threshold)&&threshold>0?threshold:atlasDefaultThreshold;
  const rule={version:'atlas-hh-departure-v1',thresholdDb,returnFractionOfPeak:atlasHalfPeak,
    metric:'Absolute value of the signed footprint-mean HH difference from the reference, in dB.'};
  const result={rule,onset:null,persistence:null,peak:null,recovery:null,lastComparableUtc:null,status:'insufficient_evidence'};
  const ref=c.observations.findIndex(o=>o.timestamp===c.reference);
  if(i<ref)return {...result,status:'before_reference'};
  const post=c.observations.slice(ref+1,i+1);
  const samples=p.valid_pixels>0?post.flatMap((o,j)=>{
    const value=p.series[ref+1+j]?.hh_reference;
    return Number.isFinite(value)?[{utc:o.timestamp,magnitudeDb:Math.abs(value)}]:[];
  }):[];
  if(!samples.length)return result;
  result.lastComparableUtc=samples.at(-1).utc;
  const first=samples.findIndex(o=>o.magnitudeDb>=thresholdDb);
  if(first===-1)return {...result,status:'no_threshold_crossing',assessedVisits:samples.length,unavailableVisits:post.length-samples.length};
  const before=samples[first-1]?.utc??(Number.isFinite(p.series[ref]?.hh_reference)?c.reference:null);
  const after=samples.slice(first);
  const peak=after.reduce((a,b)=>b.magnitudeDb>a.magnitudeDb?b:a);
  const recoveryTarget=peak.magnitudeDb*atlasHalfPeak;
  const crossing=after.findIndex((o,j)=>j>after.indexOf(peak)&&o.magnitudeDb<=recoveryTarget);
  return {...result,status:'threshold_crossed',onset:{lastBelowUtc:before,firstAtOrAboveUtc:after[0].utc},
    persistence:{visitsAtOrAbove:after.filter(o=>o.magnitudeDb>=thresholdDb).length,assessedVisits:after.length},
    unavailableVisits:post.length-samples.length,peak,
    recovery:{targetDb:recoveryTarget,lastAboveUtc:crossing===-1?null:after[crossing-1].utc,
      firstAtOrBelowUtc:crossing===-1?null:after[crossing].utc,rightCensored:crossing===-1}};
}
