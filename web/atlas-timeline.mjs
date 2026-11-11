import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {iso,fmt} from './atlas-state.mjs';
import {atlasVisitLabel,atlasSignedDb,atlasComparison,atlasGapBetween} from './atlas-chronology.mjs';

export function atlasVisitText(reference,recent){
  return [atlasSignedDb(reference.values.hh),atlasSignedDb(reference.values.hv),
    recent.target?atlasSignedDb(recent.values.hh):'No preceding visit',
    recent.target?atlasSignedDb(recent.values.hv):'No preceding visit'];
}

function atlasTraceChart(c,traces,kind,i,gaps,limit,choose){
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  const recent=kind==='recent';
  svg.setAttribute('viewBox','0 0 565 153');
  svg.setAttribute('role','img');
  svg.setAttribute('aria-label',(recent?'Recent change from each preceding visit':'Difference from the reference visit')+' in signed dB. HH solid, HV dashed. Dates and values also appear in the measurement table.');
  const dates=c.observations.map(o=>Date.parse(o.timestamp));
  const x=j=>55+(dates[j]-dates[0])/(dates.at(-1)-dates[0]||1)*488;
  const y=v=>17+(limit-v)/(2*limit)*102;
  function shape(tag,attrs,text,parent=svg){
    const node=document.createElementNS('http://www.w3.org/2000/svg',tag);
    for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);
    if(text)node.textContent=text;
    parent.append(node);
    return node;
  }
  for(const v of [-limit,0,limit]){
    shape('line',{x1:55,y1:y(v),x2:543,y2:y(v),stroke:'#3d5662'});
    shape('text',{x:5,y:y(v)+4,fill:'#c4d8dc','font-size':12},fmt(v,1));
  }
  shape('line',{x1:x(i),y1:y(limit),x2:x(i),y2:y(-limit),stroke:'#d8e5e5','stroke-dasharray':'2 3'});
  for(const [channel,color] of [['hh','#78e6ce'],['hv','#ffce85']])traces.forEach((row,j)=>{
    const trace=row[kind],v=trace.values[channel],prev=traces[j-1]?.[kind].values[channel];
    if(!Number.isFinite(v))return;
    if(j&&Number.isFinite(prev)&&dates[j]-dates[j-1]<=13*86400000&&
      !atlasGapBetween(c.observations[j-1].timestamp,c.observations[j].timestamp,gaps)){
      shape('line',{x1:x(j-1),y1:y(prev),x2:x(j),y2:y(v),stroke:color,'stroke-width':2,'stroke-dasharray':channel==='hv'?'4 3':'none'});
    }
    const point=shape('circle',{cx:x(j),cy:y(v),r:j===i?6:4,fill:color,stroke:'transparent','stroke-width':6,'pointer-events':'all'});
    point.addEventListener('click',()=>choose(trace.current.id));
    shape('title',{},channel.toUpperCase()+' '+atlasSignedDb(v)+' · '+trace.current.utc+' minus '+trace.target.utc+' · '+trace.support.footprintLabel+' · '+trace.support.validPixels.toLocaleString()+' common-valid pixels',point);
  });
  shape('text',{x:55,y:140,fill:'#c4d8dc','font-size':13},iso(c.observations[0].timestamp));
  shape('text',{x:543,y:140,fill:'#c4d8dc','font-size':13,'text-anchor':'end'},iso(c.observations.at(-1).timestamp));
  return svg;
}

export function renderAtlasTimeline(c,p,i,support,gaps,choose){
  const $=atlasNode,el=atlasElement;
  const traces=c.observations.map((_,j)=>({reference:atlasComparison(c,p,j,'reference',support,gaps),
    recent:atlasComparison(c,p,j,'successive',support,gaps)}));
  const values=traces.flatMap(t=>[...Object.values(t.recent.values),...Object.values(t.reference.values)]).filter(Number.isFinite);
  const chart=$('chart'),table=$('table');
  chart.replaceChildren();
  if(values.length){
    const limit=Math.ceil(Math.max(1,...values.map(Math.abs)));
    chart.append(el('p','HH solid · HV dashed · same signed dB scale on both plots. Points select recorded visits.'));
    for(const [kind,title] of [['recent','Recent change'],['reference','Difference from reference']]){
      chart.append(el('h3',title),atlasTraceChart(c,traces,kind,i,gaps,limit,choose));
    }
  }else chart.append(el('p','No comparable measurements for this footprint.'));
  const focus=document.activeElement?.dataset?.atlasVisit;
  table.replaceChildren(...traces.map((trace,j)=>{
    const o=c.observations[j],tr=el('tr'),heading=el('th'),button=el('button',atlasVisitLabel(c,o));
    heading.setAttribute('scope','row');
    if(j===i)tr.setAttribute('aria-current','true');
    button.dataset.atlasVisit=o.observation_id;
    button.setAttribute('aria-label','Select visit '+o.timestamp.replace('T',' ').replace('Z',' UTC'));
    button.onclick=()=>choose(o.observation_id);
    heading.append(button);
    tr.append(heading,el('td',trace.recent.target?atlasVisitLabel(c,c.observations[j-1]):'None'),
      ...atlasVisitText(trace.reference,trace.recent).map(v=>el('td',v)));
    return tr;
  }));
  if(focus)for(const row of table.children){
    const button=row.firstElementChild.firstElementChild;
    if(button.dataset.atlasVisit===focus){button.focus();break;}
  }
  $('table-caption').textContent='Signed dB · Reference '+c.reference.replace('T',' ').replace('Z',' UTC')+' · '+p.label+' · '+support.validPixels.toLocaleString()+' common-valid pixels.';
}

export function renderAtlasChronology(summary,gaps){
  const $=atlasNode,el=atlasElement;
  const {rule,onset,persistence,peak,recovery,lastComparableUtc,status,unavailableVisits}=summary;
  const evidence=$('chronology');
  evidence.replaceChildren();
  const day=utc=>utc?utc.replace('T',' ').replace('Z',' UTC'):null;
  if(status==='before_reference')evidence.append(el('p','This visit predates the reference. The threshold summary begins after the reference.'));
  else if(status==='insufficient_evidence')evidence.append(el('p','Insufficient evidence. The rule needs a comparable visit after the reference.'));
  else if(status==='no_threshold_crossing')evidence.append(el('p','No measured visit reached '+rule.thresholdDb+' dB through '+day(lastComparableUtc)+'.'));
  else{
    evidence.append(el('p',onset.lastBelowUtc?'First threshold crossing between '+day(onset.lastBelowUtc)+' and '+day(onset.firstAtOrAboveUtc)+'.':
      'First assessed crossing on '+day(onset.firstAtOrAboveUtc)+'. The earlier bound is unknown.'),
      el('p','Persistence · '+persistence.visitsAtOrAbove+' of '+persistence.assessedVisits+' assessed visits at or above '+rule.thresholdDb+' dB since the crossing.'),
      el('p','Observed peak · '+fmt(peak.magnitudeDb)+' dB on '+day(peak.utc)+'. Half-peak target · '+fmt(recovery.targetDb)+' dB.'),
      el('p',recovery.rightCensored?'Half-peak return not observed through '+day(lastComparableUtc)+' (right-censored).':
        'Half-peak return bracketed by '+day(recovery.lastAboveUtc)+' and '+day(recovery.firstAtOrBelowUtc)+'.'));
  }
  if(unavailableVisits)evidence.append(el('p',unavailableVisits+' recorded visits had no comparable HH measurement.'));
  $('chronology-method').textContent=rule.version+' · '+rule.metric+' The threshold is exploratory. A half-peak return describes the radar signal. Physical recovery requires independent evidence.';
  const coverage=$('trace-gaps');
  coverage.replaceChildren(el('p','Plots use elapsed time and leave breaks across gaps. Playback advances through recorded visits only.'));
  for(const gap of gaps){
    const link=el('a','ASF acquisition notice ↗');link.href=gap.source;link.target='_blank';link.rel='noopener noreferrer';
    coverage.append(el('p','No acquisition on the nominal '+gap.nominalDate+' visit.'),link);
  }
}

const atlasDayLabel=new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
export const atlasShortDate=utc=>atlasDayLabel.format(new Date(utc));

export function createAtlasDateDock(choose){
  const dock=atlasNode('time-axis'),scrub=atlasNode('scrub');
  let lastCase,lastProfile,lastNative,lastLayer,available=[],rows=[];
  const svgNode=(name,attrs={})=>{
    const node=document.createElementNS('http://www.w3.org/2000/svg',name);
    for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);
    return node;
  };
  scrub.oninput=()=>choose(available[Number(scrub.value)]?.observation_id);
  return (c,p,meta,s,gaps,i)=>{
    const coherence=s.layer==='coherence';
    if(lastCase!==c||lastProfile!==p||lastNative!==s.native||lastLayer!==coherence){
      lastCase=c;lastProfile=p;lastNative=s.native;lastLayer=coherence;
      available=c.observations.filter(o=>!coherence||c.pairs.some(pair=>pair.dates[1]===o.timestamp));
      const times=c.observations.map(o=>Date.parse(o.timestamp)),start=times[0],duration=times.at(-1)-start||1;
      const position=utc=>100*(Date.parse(utc)-start)/duration;
      const graphic=svgNode('svg',{class:'atlas-axis-graphic',viewBox:'0 0 1000 66',preserveAspectRatio:'none','aria-hidden':'true'});
      const nodes=gaps.map(gap=>{
        const left=Math.max(0,position(gap.start)),right=Math.min(100,position(gap.end));
        const band=atlasElement('div');
        band.className='atlas-gap';
        band.style.setProperty('--at-x',left+'%');band.style.setProperty('--at-length',Math.max(0,right-left)+'%');
        band.title='No usable visit during the recorded gap. The nominal '+gap.nominalDate+' visit was never acquired.';
        band.setAttribute('aria-label',band.title);
        return band;
      });
      atlasNode('gap-key').hidden=!nodes.length;
      if(coherence){
        for(const pair of c.pairs){
          const [from,to]=pair.dates,x=position(from)*10,y=position(to)*10;
          graphic.append(svgNode('path',{class:'atlas-pair-arc',d:'M'+x+' 23 Q'+(x+y)/2+' -2 '+y+' 23'}));
        }
      }
      const dualpol=s.native?p.dualpol:meta.footprints[s.profile]?.dualpol;
      const means=c.observations.map((o,j)=>{
        const observed=dualpol?.[o.observation_id];
        return observed?.validPixels>0&&Number.isFinite(observed.hhDb)?observed.hhDb:
          p.valid_pixels>0&&Number.isFinite(p.native_means?.[j]?.hh)?p.native_means[j].hh:null;
      });
      rows=c.observations.map((o,j)=>{
        const pair=coherence?c.pairs.find(v=>v.dates[1]===o.timestamp):null;
        const button=atlasElement('button');
        button.type='button';button.dataset.frame=o.observation_id;button.dataset.ref=String(o.timestamp===c.reference);
        button.dataset.pair=String(Boolean(pair));button.style.setProperty('--at-x',position(o.timestamp)+'%');
        const label=atlasElement('span',atlasShortDate(o.timestamp));
        const dot=atlasElement('span');dot.className='atlas-tick-dot';dot.setAttribute('aria-hidden','true');
        label.className='atlas-tick-label';
        button.append(dot,label);
        const baseline=pair?Math.round((Date.parse(pair.dates[1])-Date.parse(pair.dates[0]))/86400000):0;
        button.title=(pair?pair.dates.map(atlasShortDate).join(' ↔ ')+' · '+baseline+' d baseline':iso(o.timestamp))+
          (o.timestamp===c.reference?' · fixed reference':'')+
          (coherence&&!pair?' · no coherence pair ends here':'')+
          (Number.isFinite(means[j])?' · HH mean '+fmt(means[j])+' dB':'');
        button.setAttribute('aria-label',button.title);
        button.setAttribute('aria-disabled',String(coherence&&!pair));
        button.onclick=()=>{if(!coherence||pair)choose(o.observation_id);};
        button.onkeydown=event=>{
          if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
          event.preventDefault();
          const index=available.indexOf(o),next=event.key==='Home'?0:event.key==='End'?available.length-1:
            Math.min(available.length-1,Math.max(0,index+(event.key==='ArrowLeft'?-1:1)));
          const id=available[next]?.observation_id;
          if(id){choose(id);rows.find(row=>row.dataset.frame===id)?.focus();}
        };
        return button;
      });
      dock.replaceChildren(...nodes,graphic,...rows);
    }
    for(const [j,button] of rows.entries()){
      button.setAttribute('aria-current',String(j===i));button.tabIndex=j===i?0:-1;
    }
    const index=available.indexOf(c.observations[i]);
    scrub.max=String(Math.max(0,available.length-1));scrub.value=String(Math.max(0,index));
    scrub.setAttribute('aria-valuetext',rows[i]?.title??'');
  };
}
