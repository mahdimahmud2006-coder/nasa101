import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {atlasGridToWorld,atlasWorldToGrid} from './atlas-map.mjs';
import {atlasScenarioAsset} from './atlas-simulations.mjs';
import {atlasSynthesizeRadar,atlasLabRGB,atlasPhaseCoherence,atlasOrbitScreen,atlasTransectSamples,atlasBankTrace,atlasBankProjection} from './atlas-lab-model.mjs';

const orbitColors=[null,null,[119,146,255,235],[255,171,79,227]];
const labDate=utc=>utc.slice(0,10);
const labDistance=value=>Math.round(value).toLocaleString()+' m';
const labCoords=text=>/^\d+\s*,\s*\d+$/.test(text.trim())?text.trim().split(',').map(Number):null;

export function createAtlasLabs({manifestFor,focusMap,redraw,chooseVisit}){
  const $=atlasNode,el=atlasElement,radar=$('radar-lab'),bank=$('bank-lab'),orbit=$('orbit-lab');
  const bankMap=$('bank-map'),orbitMap=$('orbit-map'),caption=$('lab-map-caption');
  const radarMap=$('radar-map'),radarKey=$('radar-map-key');
  const cache=new Map(),orbits=new Map();
  let state,frame=0,pickMode='',revision=0,overlay=null,orbitScreen=null,bankTrace=null;
  const hand=$('simulation'),line={points:[],asset:null,multiplier:1.5,cycles:2},sensor={moisture:25,water:0,canopy:.35};
  const panels={radar,bank,orbit};
  const geometry=()=>orbits.get(state.c.case);
  const data=()=>cache.get(state.c.case)?.value;
  const active=panel=>panel.open&&!panel.hidden;
  const input=(key,value)=>{$(key).value=value;};
  const text=(key,value)=>{$(key).textContent=value;};
  const setSwatch=(key,values)=>{
    const rgb=values?atlasLabRGB(values):null;
    $(key).style.background=rgb?'rgb('+rgb.join(',')+')':'repeating-linear-gradient(135deg,#2c444f 0 4px,#1b2f38 4px 8px)';
  };
  const radarText=({hhDb,hvDb,powerShare})=>'HH '+hhDb.toFixed(1)+' dB · HV '+hvDb.toFixed(1)+' dB'+
    (Number.isFinite(powerShare)?' · HV share '+(100*powerShare).toFixed(1)+'%':'');
  const signed=n=>(n>0?'+':'')+n.toFixed(1);
  function renderRadar(){
    const {o,p,meta,s}=state;
    const observed=(s.native?p.dualpol:meta.footprints[s.profile]?.dualpol)?.[o.observation_id];
    for(const [key,value] of Object.entries(sensor)){
      input('radar-'+key,value);
      text('radar-'+key+'-value',value+(key==='moisture'?'%':key==='water'?' cm':''));
    }
    const synthetic=atlasSynthesizeRadar(sensor);
    const terms=Object.entries(synthetic.components),total=terms.reduce((sum,[,v])=>sum+v,0);
    const names={surface:'Surface',volume:'Canopy volume',bounce:'Stem–water bounce'};
    text('radar-footprint',p.label+' · '+labDate(o.timestamp)+' UTC');
    setSwatch('radar-sim-swatch',synthetic);
    text('radar-sim-values',radarText(synthetic));
    if(observed?.validPixels&&Number.isFinite(observed.hhDb)&&Number.isFinite(observed.hvDb)){
      setSwatch('radar-obs-swatch',observed);
      text('radar-obs-values',radarText(observed)+' · '+observed.validPixels.toLocaleString()+' paired-valid samples');
      text('radar-difference','Model − observed · HH '+signed(synthetic.hhDb-observed.hhDb)+' dB · HV '+signed(synthetic.hvDb-observed.hvDb)+' dB');
      $('radar-difference').style.setProperty('--fit-share',Math.max(0,1-Math.abs(synthetic.hhDb-observed.hhDb)/20)*100+'%');
    }else{
      setSwatch('radar-obs-swatch',null);
      text('radar-obs-values','No paired HH/HV samples for this footprint.');text('radar-difference','');
    }
    text('radar-mechanisms','Simulated HH terms · '+terms.map(([k,v])=>names[k]+' '+Math.round(100*v/total)+'%').join(' / '));
    drawRadar(synthetic,observed?.validPixels?observed:null);
  }
  function drawRadar(synthetic,observed){
    const {c,s,meta,o}=state;
    if(s.terrain==='on')return;
    const [h,w]=c.grid.shape;
    const rgb=atlasLabRGB(synthetic).join(',');
    const stroke={'vector-effect':'non-scaling-stroke',stroke:'#ffffff','stroke-width':2,fill:'rgba('+rgb+',.65)'};
    radarMap.setAttribute('viewBox','0 0 '+w+' '+h);
    radarMap.setAttribute('preserveAspectRatio','none');
    radarMap.replaceChildren();
    if(s.native?.startsWith('[')){
      const vertices=JSON.parse(s.native);
      radarMap.append(node('polygon',{...stroke,points:vertices.map(pair=>pair.join(',')).join(' ')}));
    }else if(s.native){
      const [row,col]=s.native.split(',').map(Number);
      radarMap.append(node('circle',{...stroke,cx:col+.5,cy:row+.5,r:Math.max(w,h)/110}));
    }else{
      const footprint=meta.footprints[s.profile]?.review?.location;
      if(footprint)radarMap.append(node('circle',{...stroke,cx:footprint.col+.5,cy:footprint.row+.5,r:Math.max(w,h)/65}));
    }
    radarMap.removeAttribute('hidden');
    setSwatch('radar-map-model',synthetic);
    setSwatch('radar-map-observed',observed);
    radarKey.hidden=false;
    mapNote('RADAR MODEL · Simulated color compared with '+labDate(o.timestamp)+' UTC.');
  }
  async function load(c){
    const path=manifestFor(c.case);
    if(!path)throw Error();
    const url=new URL(path,location.href),res=await fetch(url,{credentials:'omit'});
    if(!res.ok)throw Error();
    const m=await res.json(),g=m.grid,[h,w]=g.shape,n=h*w;
    if(m.schema!==1||m.case!==c.case||m.caseSha256!==c.manifest_sha256||m.terrainSha256!==c.terrain.source_manifest_sha256||
       g.crs!==c.grid.crs||g.affine[0]!==30||g.affine[4]!==-30||g.affine[1]||g.affine[3]||
       g.affine[2]!==c.grid.affine[2]||g.affine[5]!==c.grid.affine[5]||
       ![h,w].every(v=>Number.isInteger(v)&&v>0&&v<=1000))throw Error();
    if(c.case==='jamuna_river'){
      const b=m.bank, ids=c.observations.map(v=>v.observation_id);
      if(!b||b.hhCutoffDb!==-17||ids.length>16||JSON.stringify(ids)!==JSON.stringify(b.ids))throw Error();
      const [raw,cover]=await Promise.all([atlasScenarioAsset(b.series,url,n*4),
        b.cover?atlasScenarioAsset(b.cover,url,n):null]);
      const series=new Uint16Array(raw);
      return {g,b,valid:series.subarray(0,n),dark:series.subarray(n),cover:cover?new Uint8Array(cover):null};
    }
    const a=m.orbit,k=a?.bufferCells;
    if(!Number.isInteger(k)||k<1||k>100||!Number.isFinite(a.ascAzimuth)||!Number.isFinite(a.ascIncidence)||
       !c.observations.some(v=>v.source_granule_id===a.sourceId&&v.track===a.track))throw Error();
    const shape=[h+2*k,w+2*k],raw=await atlasScenarioAsset(a.dem,url,4*shape[0]*shape[1]);
    return {g,a,shape,dem:new Float32Array(raw)};
  }
  function getData(kind){
    const id=state.c.case;
    if(!cache.has(id)){
      const item={};cache.set(id,item);
      load(state.c).then(value=>{item.value=value;},()=>{item.failed=true;})
        .finally(()=>{if(state.c.case===id)schedule();});
    }
    const item=cache.get(id);
    $(kind+'-controls').hidden=!item.value;
    text(kind+'-status',item.failed?'Could not load this lab’s inputs. Close and reopen the lab to retry.':item.value?'':'Loading analysis inputs…');
    return item.value;
  }
  function schedule(){
    if(frame)return;
    frame=requestAnimationFrame(()=>{frame=0;paint();});
  }
  function resetPicks(){
    pickMode='';$('bank-pick').setAttribute('aria-pressed','false');$('bank-pick-asset').setAttribute('aria-pressed','false');
  }
  function clearOrbit(){
    if(overlay){overlay=null;redraw();}
    orbitMap.hidden=true;orbitScreen=null;
  }
  function paint(){
    if(!state)return;
    $('layout').dataset.labMap=String(active(radar)||active(bank)||active(orbit));
    radarMap.setAttribute('hidden','');radarKey.hidden=true;
    bankMap.setAttribute('hidden','');caption.hidden=true;
    if(active(radar))renderRadar();
    if(active(orbit)){
      const value=getData('orbit');
      if(value)renderOrbit(value);
    }else clearOrbit();
    if(active(bank)){
      const value=getData('bank');
      if(value)renderBank(value);
    }
  }
  function place(target,g){
    const {c}=state,[h,w]=g.shape,[rh,rw]=c.grid.shape;
    const toRadar=pos=>atlasWorldToGrid(c.grid.affine,atlasGridToWorld(g.affine,pos));
    const [x0,y0]=toRadar([0,0]),[x1,y1]=toRadar([w,h]);
    Object.assign(target.style,{left:x0/rw*100+'%',top:y0/rh*100+'%',width:(x1-x0)/rw*100+'%',height:(y1-y0)/rh*100+'%'});
    return (u,v)=>[Math.floor((u*rw-x0)*w/(x1-x0)),Math.floor((v*rh-y0)*h/(y1-y0))];
  }
  function mapNote(message){
    caption.hidden=false;caption.textContent=message;
  }
  const orbitMasks=new Set([2,3]);
  for(const [key,code] of [['orbit-shadow',2],['orbit-layover',3]])$(key).onclick=()=>{
    if(orbitMasks.has(code))orbitMasks.delete(code);else orbitMasks.add(code);
    $(key).setAttribute('aria-pressed',String(orbitMasks.has(code)));
    schedule();
  };
  function renderOrbit(value){
    const {g,a,dem,shape}=value,[h,w]=g.shape,{c,s,o,p,meta}=state;
    if(!geometry())orbits.set(c.case,{angle:a.ascIncidence,look:'asc',band:'L',motion:1});
    const q=geometry(),az=(a.ascAzimuth+(q.look==='asc'?0:180))%360;
    for(const k of ['angle','look','band','motion'])if(document.activeElement!==$('orbit-'+k))input('orbit-'+k,q[k]);
    $('orbit-angle').dataset.baseline=a.ascIncidence;
    $('orbit-direction').style.setProperty('--look-azimuth',az+'deg');
    text('orbit-angle-value',q.angle.toFixed(1)+'°');text('orbit-motion-value',q.motion.toFixed(1)+' cm');
    text('orbit-azimuth','Toward-sensor azimuth '+az.toFixed(1)+'° clockwise from grid north. '+(q.look==='asc'?'Based on the recorded ascending look.':'Hypothetical opposite look.'));
    const key=c.case+':'+q.angle+':'+az;
    let changed=false;
    if(orbitScreen?.key!==key)orbitScreen={key,...atlasOrbitScreen(dem,shape,a.bufferCells,30,q.angle,az)};
    const maskKey=[...orbitMasks].sort().join(',');
    if(orbitScreen.maskKey!==maskKey){
      const {cells}=orbitScreen;
      orbitScreen.maskKey=maskKey;
      orbitMap.width=w;orbitMap.height=h;
      const ctx=orbitMap.getContext('2d'),img=ctx.createImageData(w,h);
      for(let i=0;i<cells.length;i++)if(orbitMasks.has(cells[i]))img.data.set(orbitColors[cells[i]],i*4);
      ctx.putImageData(img,0,0);
      const convert=place(orbitMap,g);
      overlay={revision:'orbit-'+(++revision),sample(u,v){
        const [x,y]=convert(u,v);
        return x>=0&&x<w&&y>=0&&y<h&&orbitMasks.has(cells[y*w+x])?orbitColors[cells[y*w+x]]:null;
      }};
      changed=true;
    }
    const count=orbitScreen.counts,valid=h*w-count[0],fraction=n=>valid?(100*n/valid).toFixed(1)+'%':'—';
    text('orbit-result',fraction(count[2])+' shadow · '+fraction(count[3])+' layover candidate');
    const l=atlasPhaseCoherence(q.motion,24),short=atlasPhaseCoherence(q.motion,5.6);
    text('orbit-model','Phase-only coherence example · '+(q.band==='L'?'L '+l.toFixed(2)+' selected · C '+short.toFixed(2):'C '+short.toFixed(2)+' selected · L '+l.toFixed(2))+'. This illustrates sensitivity to assumed canopy motion.');
    const pair=meta.pairs.find(v=>v.secondId===o.observation_id);
    const obs=pair?(s.native?p.coherence?.pairs?.[pair.id]:pair.footprints?.[s.profile]):null;
    text('orbit-observed',Number.isFinite(obs?.mean)
      ?'Observed L-band GUNW on this footprint: '+obs.mean.toFixed(3)+' · '+labDate(pair.startUtc)+' → '+labDate(pair.endUtc)+'.'
      :'Observed L-band GUNW: choose a visit ending a measured pair to compare.');
    orbitMap.hidden=s.terrain==='on'||s.layer==='coherence'||!orbitMasks.size;
    if(s.layer!=='coherence')mapNote('SENSOR GEOMETRY · '+q.angle.toFixed(1)+'° · '+(q.look==='asc'?'Ascending 098':'Opposite look')+' · violet shadow / amber layover');
    if(changed)redraw();
  }
  function node(tag,props={}){
    const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
    for(const [key,value] of Object.entries(props))n.setAttribute(key,value);
    return n;
  }
  function drawBank(g,result){
    const [h,w]=g.shape;
    if(!line.points.length||state.s.layer==='coherence'||state.s.terrain==='on')return;
    place(bankMap,g);bankMap.setAttribute('viewBox','0 0 '+w+' '+h);bankMap.setAttribute('preserveAspectRatio','none');
    bankMap.removeAttribute('hidden');
    if(result&&result.displayMovement>0)bankMap.append(node('polygon',{points:result.corners.map(p=>p.join(',')).join(' '),
      fill:'#ffb65d88',stroke:'#ffbc68','vector-effect':'non-scaling-stroke','stroke-width':1.5}));
    const points=line.points.map(pt=>pt.map(n=>n+.5).join(','));
    if(points.length===2)bankMap.append(node('polyline',{points:points.join(' '),fill:'none',stroke:'#d6fcff','stroke-width':2,
      'vector-effect':'non-scaling-stroke','stroke-dasharray':'5 3'}));
    const dot=(x,y,fill,r=3)=>node('circle',{cx:x,cy:y,r,fill,stroke:'#10232a','stroke-width':1,'vector-effect':'non-scaling-stroke'});
    for(const [x,y] of line.points)bankMap.append(dot(x+.5,y+.5,'#d6fcff'));
    if(result){
      const [x1,y1]=result.edge,[x2,y2]=result.end;
      bankMap.append(node('line',{x1,y1,x2,y2,stroke:'#ffbc68','stroke-width':3,'vector-effect':'non-scaling-stroke'}),
        dot(x1,y1,'#68e5fa'),dot(x2,y2,'#ffbd66'));
    }
    if(line.asset)bankMap.append(dot(line.asset[0]+.5,line.asset[1]+.5,result?.assetHit?'#ff8070':'#e5f8e8',4));
    mapNote('BANK SCENARIO · cyan observed threshold edge / amber assumed retreat / white transect');
  }
  function renderBank(value){
    const {g,b,dark,valid,cover}=value,{c,o}=state;
    $('bank-map').replaceChildren();
    $('bank-example').hidden=!b.example;
    if(!line.edited&&!line.points.length&&b.example){
      line.points=b.example;
      input('bank-coords',line.points.map(point=>point.join(',')).join(' / '));
    }
    for(const k of ['multiplier','cycles']){
      input('bank-'+k,line[k]);
      text('bank-'+k+'-value',k==='cycles'?line[k]:line[k].toFixed(1)+'×');
    }
    const strip=$('bank-recurrence'),visits=$('bank-visits');
    strip.replaceChildren();visits.replaceChildren();
    let result=null,support='',exposure='',outcome='',assetNote='';
    if(line.points.length===2){
      const key=JSON.stringify(line.points);
      if(bankTrace?.key!==key){
        const transect=atlasTransectSamples(...line.points,g.shape);
        bankTrace={key,transect,trace:atlasBankTrace(transect,valid,dark,b.ids.length)};
      }
      const {transect,trace}=bankTrace,visit=b.ids.indexOf(o.observation_id);
      result=atlasBankProjection(transect,trace,visit,line.multiplier,line.cycles,g.shape,cover,line.asset);
      const edge=trace.rows[visit];
      outcome=result?labDistance(result.movement)+' assumed retreat'+(result.limited?' · clipped at transect end':'')
        :edge===null?'No single radar-dark edge on '+labDate(o.timestamp)+'. Select another visit or move the transect.':'Too few comparable visits for a retreat scenario.';
      support=trace.resolved+' of '+b.ids.length+' visits with one edge'
        +(trace.excursion===null?'':' · '+labDistance(trace.excursion*30)+' observed edge spread · '+Math.round(trace.occurrence*100)+'% mean dark recurrence across that spread');
      for(const [dark,n] of trace.recurrence){
        const bin=el('i');bin.style.background=n?'rgba(91,222,243,'+(.12+.88*dark/n)+')':'#283b44';strip.append(bin);
      }
      for(const [j,v] of c.observations.entries()){
        const button=el('button',labDate(v.timestamp).slice(5)+' · '+(trace.rows[j]===null?'—':labDistance(trace.rows[j]*30)));
        button.setAttribute('aria-pressed',String(j===visit));
        button.onclick=()=>chooseVisit(v.observation_id);visits.append(button);
      }
      if(result){
        exposure=cover?result.cropland.toLocaleString()+' historical cropland cells in the corridor (ESA WorldCover 2021; '+result.assessed+' of '+result.eligible+' cells labeled).':'No historical land-cover grid for this case.';
        if(line.asset)assetNote=result.assetHit?'Marked point intersects the scenario corridor.':'Marked point lies outside the scenario corridor.';
      }else if(line.asset)assetNote='Asset check requires a resolved scenario corridor.';
    }else outcome='Try the sample transect or draw from channel to land.';
    text('bank-result',outcome);
    text('bank-support',support);text('bank-exposure',exposure);text('bank-asset-result',assetNote);
    if(line.error)text('bank-status',line.error);
    else if(pickMode)text('bank-status',pickMode==='asset'?'Click the assumed asset point.':line.points.length?'Now click the inland end.':'Click in the main channel.');
    drawBank(g,result);
  }
  function setLine(points){
    const g=data()?.g;
    if(!g)return;
    if(!points.every(p=>inside(p,g)))line.error='Use valid column,row coordinates inside the study grid.';
    else if(points.length===2&&!atlasTransectSamples(...points,g.shape))line.error='Place the ends 360–7,800 m apart.';
    else{
      line.edited=true;line.points=points;line.error='';
      input('bank-coords',points.map(p=>p.join(',')).join(' / '));
      if(points.length===2)resetPicks();
    }
    schedule();
  }
  function inside(point,g){
    return !!point&&point[0]>=0&&point[0]<g.shape[1]&&point[1]>=0&&point[1]<g.shape[0];
  }
  function setAsset(point){
    const g=data()?.g;
    if(!g)return;
    line.error=inside(point,g)?'':'Use a valid asset column,row inside the study grid.';
    if(!line.error){line.asset=point;input('bank-asset',point.join(','));resetPicks();}
    schedule();
  }
  function openMapPanel(panel,other,kind){
    if(!panel.open||panel.hidden){
      resetPicks();
      if(cache.get(state?.c.case)?.failed)cache.delete(state.c.case);
    }else{
      other.open=false;hand.open=false;
      if(kind==='orbit')focusMap('terrain',false);
      else if(state.s.terrain==='on'||state.s.layer==='coherence')focusMap('plan',false);
    }
    schedule();
  }
  radar.ontoggle=schedule;
  bank.ontoggle=()=>openMapPanel(bank,orbit,'bank');
  orbit.ontoggle=()=>openMapPanel(orbit,bank,'orbit');
  hand.addEventListener('toggle',()=>{if(hand.open){bank.open=false;orbit.open=false;schedule();}});
  for(const k of Object.keys(sensor))$('radar-'+k).oninput=e=>{sensor[k]=e.target.valueAsNumber;schedule();};
  for(const [k,params] of Object.entries({water:[10,60,0],stems:[35,40,.42],dry:[10,0,.75]}))$('radar-'+k+'-preset').onclick=()=>{
    [sensor.moisture,sensor.water,sensor.canopy]=params;schedule();
  };
  for(const k of ['multiplier','cycles'])$('bank-'+k).oninput=e=>{line[k]=e.target.valueAsNumber;schedule();};
  $('bank-example').onclick=()=>{setLine(data().b.example);focusMap('plan',true);};
  $('bank-apply').onclick=()=>{
    const parts=$('bank-coords').value.split('/').map(labCoords);
    if(parts.length===2)setLine(parts);else{line.error='Enter both column,row endpoints separated by a slash.';schedule();}
  };
  $('bank-pick').onclick=()=>{
    if(pickMode==='line'){resetPicks();schedule();return;}
    resetPicks();line.error='';pickMode='line';$('bank-pick').setAttribute('aria-pressed','true');setLine([]);focusMap('plan',true);
  };
  $('bank-pick-asset').onclick=()=>{
    if(pickMode==='asset'){resetPicks();schedule();return;}
    resetPicks();line.error='';pickMode='asset';$('bank-pick-asset').setAttribute('aria-pressed','true');focusMap('plan',true);schedule();
  };
  $('bank-apply-asset').onclick=()=>setAsset(labCoords($('bank-asset').value));
  $('bank-clear-asset').onclick=()=>{line.asset=null;line.error='';input('bank-asset','');resetPicks();schedule();};
  $('orbit-show').onclick=()=>focusMap('terrain',true);
  $('orbit-pair').onclick=()=>{const pair=state.meta.pairs.at(-1);if(pair)chooseVisit(pair.secondId);};
  for(const k of ['angle','motion','look','band'])$('orbit-'+k).oninput=e=>{
    const q=geometry();if(!q)return;q[k]=['angle','motion'].includes(k)?e.target.valueAsNumber:e.target.value;schedule();
  };
  return {
    open(kind){
      for(const [name,panel] of Object.entries(panels)){
        if(name!==kind)panel.hidden=true;
        panel.open=!panel.hidden;
      }
      schedule();
    },
    update(c,o,s,p,meta){
      const switched=state?.c.case!==c.case;
      if(state?.o.observation_id!==o.observation_id){
        radarMap.setAttribute('hidden','');radarKey.hidden=true;bankMap.setAttribute('hidden','');
      }
      state={c,o,s,p,meta};
      radar.hidden=false;
      bank.hidden=c.case!=='jamuna_river'||!manifestFor(c.case);
      orbit.hidden=c.country!=='Nepal'||!manifestFor(c.case);
      if(switched){
        bank.open=false;orbit.open=false;bankMap.setAttribute('hidden','');caption.hidden=true;resetPicks();
        clearOrbit();
      }
      if(active(radar)||active(bank)||active(orbit))schedule();
    },
    pick(pt){
      const g=data()?.g;
      if(!g||!active(bank)||!pickMode)return false;
      const cell=atlasWorldToGrid(g.affine,atlasGridToWorld(state.c.grid.affine,pt)).map(Math.floor);
      if(pickMode==='asset')setAsset(cell);else setLine([...line.points,cell]);
      return true;
    },
    ready(){
      if(!active(bank)&&!active(orbit))return true;
      const item=cache.get(state.c.case);
      return !!(item?.value||item?.failed);
    },
    overlay:()=>active(orbit)?overlay:null,
  };
}
