import {atlasNode,atlasOptions} from './atlas-dom.mjs';
import {atlasGridToWorld,atlasWorldToGrid} from './atlas-map.mjs';
import {atlasSlopeTerms,atlasSlopeScreen,atlasStageScreen,atlasBreachScreen,atlasBarrierLine} from './atlas-simulation-model.mjs';

const atlasSimColors={
  1:[50,200,237,165],2:[74,231,238,210],3:[183,141,249,200],4:[255,197,99,215],
  5:[255,118,102,200],6:[249,209,125,235],7:[255,240,181,255],8:[242,246,252,255],9:[147,161,172,190],
};
const atlasSimDefaults={stage:2,m:.3,kh:0,cohesion:5,friction:32,depth:2,weight:18};
const atlasSimArea=(n,cellArea)=>new Intl.NumberFormat('en',{maximumFractionDigits:3}).format(n*cellArea)+' km²';
const atlasSimSlug=/^[a-z_]+$/;
const atlasSimToken=/^[a-z0-9_-]+-[0-9a-f]{16}\.bin$/;

export async function atlasScenarioAsset(meta,url,size){
  if(!meta||!atlasSimToken.test(meta.file)||meta.bytes!==size||!/^[0-9a-f]{64}$/.test(meta.sha256))throw Error();
  const r=await fetch(new URL(meta.file,url),{credentials:'omit'});
  if(!r.ok)throw Error();
  const data=await r.arrayBuffer();
  if(data.byteLength!==size)throw Error();
  if(globalThis.crypto?.subtle){
    const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',data))].map(n=>n.toString(16).padStart(2,'0')).join('');
    if(digest!==meta.sha256)throw Error();
  }
  return data;
}

export function createAtlasSimulations({standalone,manifestFor,redraw,showMap}){
  const $=atlasNode,panel=$('simulation'),canvas=$('sim-map'),cache=new Map(),preferences=new Map();
  if(standalone)return {update:()=>null,pick:()=>false,overlay:()=>null};
  let current=null,frame=0,revision=0,overlay=null,picking=false;
  const inputKeys=Object.keys(atlasSimDefaults);
  const input=k=>$(k==='stage'?'sim-stage-level':'sim-'+k);
  const state=()=>{
    const id=current.c.case;
    if(!preferences.has(id))preferences.set(id,{...atlasSimDefaults,view:current.c.country==='Bangladesh'?'hh':'terrain',points:[]});
    return preferences.get(id);
  };
  const entry=()=>current&&cache.get(current.c.case);
  function describe(){
    const stage=current.c.country==='Bangladesh';
    $('sim-title').textContent=stage?'River surge & embankment':'Slope stability & shaking';
    $('sim-stage').hidden=!stage;$('sim-slope').hidden=stage;$('sim-breach').hidden=!stage;
    $('sim-scope').textContent=stage
      ?'Explore which low, gently sloping terrain would meet an assumed rise above mapped drainage.'
      :'Explore how a shallow slope responds to assumed saturation and horizontal shaking.';
  }
  async function load(c){
    const path=manifestFor(c.case);
    if(!path||!atlasSimSlug.test(c.case))throw Error();
    const url=new URL(path,location.href),r=await fetch(url,{credentials:'omit'});
    if(!r.ok)throw Error();
    const m=await r.json(),g=m.grid,n=g?.shape?.[0]*g?.shape?.[1],stage=c.country==='Bangladesh';
    if(m.schema!==1||m.case!==c.case||m.caseSha256!==c.manifest_sha256||
       m.terrainSha256!==c.terrain.source_manifest_sha256||m.kind!==(stage?'stage':'slope')||!Number.isInteger(n)||n<=0||n>1e6||
       !g.shape.every(x=>Number.isInteger(x)&&x>0)||g.crs!==c.grid.crs||
       g.affine.length!==6||!g.affine.every(Number.isFinite)||g.affine[0]!==30||g.affine[4]!==-30||g.affine[1]||g.affine[3])throw Error();
    const raw=await atlasScenarioAsset(m.terrain,url,n*(stage?1:4));
    const result={m,url,n,terrain:stage?new Uint8Array(raw):atlasSlopeTerms(new Float32Array(raw)),layers:new Map()};
    if(stage)result.drainage=new Uint8Array(await atlasScenarioAsset(m.drainage,url,n));
    return result;
  }
  function request(data,meta){
    if(!data.layers.has(meta.file)){
      const layer={pending:true};
      data.layers.set(meta.file,layer);
      atlasScenarioAsset(meta,data.url,data.n).then(raw=>{layer.values=new Uint8Array(raw);},()=>{layer.error=true;})
        .finally(()=>{layer.pending=false;if(panel.open&&entry()?.data===data)schedule();});
    }
    return data.layers.get(meta.file);
  }
  function clear(){
    if(overlay){overlay=null;canvas.hidden=true;redraw();}
    canvas.hidden=true;
    $('sim-map-caption').hidden=true;
  }
  function sync(){
    if(!current)return;
    if(panel.hidden||!panel.open){picking=false;$('sim-pick').setAttribute('aria-pressed','false');clear();return;}
    const {c}=current;
    describe();
    if(!cache.has(c.case)){
      const item={pending:true};cache.set(c.case,item);
      load(c).then(data=>{item.data=data;},()=>{item.error=true;})
        .finally(()=>{item.pending=false;if(current?.c.case===c.case&&panel.open)schedule();});
    }
    schedule();
  }
  function schedule(){
    if(frame)return;
    frame=requestAnimationFrame(()=>{frame=0;paint();});
  }
  function paint(){
    if(panel.hidden||!panel.open||!current)return;
    const item=entry();
    $('sim-controls').hidden=!item?.data;
    $('sim-retry').hidden=!item?.error;
    if(!item?.data){
      $('sim-status').textContent=item?.error?'Scenario layers could not be opened.':'Loading scenario layers…';
      clear();return;
    }
    $('sim-status').textContent='';
    const {data}=item,{m,terrain}=data,{c,o,s}=current,p=state(),stage=m.kind==='stage';
    const modes=stage?[['terrain','Terrain screen'],['hh','Observed HH within screen']]:
      [['terrain','Factor of safety'],...(m.comparisons.length?[['coherence','Compare with GUNW coherence']]:[]),
        ...(m.localImpact?[['impact','Compare with UNOSAT impact map']]:[])];
    if(!modes.some(([id])=>id===p.view))p.view='terrain';
    atlasOptions($('sim-view'),modes,p.view);
    for(const k of inputKeys)if(document.activeElement!==input(k))input(k).value=p[k];
    $('sim-stage-value').textContent='+'+p.stage.toFixed(1)+' m';
    $('sim-m-value').textContent=p.m.toFixed(2);
    $('sim-kh-value').textContent=p.kh.toFixed(2)+' g';
    const result=stage?atlasStageScreen(terrain,Math.round(p.stage*10)):atlasSlopeScreen(terrain,p);
    const scale=30**2/1e6,area=n=>atlasSimArea(n,scale),{assessed,below,cells}=result;
    $('sim-result').textContent=area(below)+(stage?' meets the stage screen':' has FoS below 1.0')+' · '+area(assessed)+' assessed.';
    const meta=stage?m.observations[o.observation_id]:p.view==='impact'?m.localImpact:m.comparisons[0];
    const layer=p.view!=='terrain'&&meta?request(data,meta):null;
    const values=layer?.values;
    const marks=new Uint8Array(cells.length);
    const counts=[0,0,0,0];let joint=0,inside=0,overlap=0;
    for(let i=0;i<cells.length;i++){
      const selected=cells[i]===2, value=values?.[i]??0;
      if(selected){
        marks[i]=stage?1:5;
        if(stage&&values){counts[value]++;marks[i]=value===1?2:value===3?4:value===2?3:9;}
      }
      if(!stage&&values&&cells[i]){
        if(value)joint++;
        if(value===1){inside++;if(selected)overlap++;}
        if(value===1&&!selected)marks[i]=3;
        if(value===1&&selected)marks[i]=4;
      }
    }
    let extra='',keys=stage?[[1,'Meets stage screen']]:[[5,'FoS below 1.0']];
    if(stage&&p.view==='hh'&&values){
      keys=[[2,'Low HH'],[3,'Middle HH'],[4,'High HH'],[9,'HH not assessed']];
      extra=o.timestamp.slice(0,10)+' · Observed HH within the stage screen: '+area(counts[1])+' below −19.5 dB, '+area(counts[3])+' above −11.5 dB, '+area(counts[2])+' between (inclusive), '+area(counts[0])+' without valid HH.';
    }
    if(!stage&&values){
      const isImpact=p.view==='impact',label=isImpact?'Mapped impact':'Lower coherence';
      keys=[[5,'FoS below 1.0'],[3,label],[4,'Overlap']];
      extra=area(overlap)+' overlaps '+(isImpact?'the mapped impact':'lower coherence')+'; '+area(inside)+' has '+(isImpact?'mapped impact in assessed terrain. The outline is preliminary.':'lower coherence within '+area(joint)+' with valid paired measurements. '
        +meta.pairs.map(pair=>pair.startUtc.slice(0,10)+' → '+pair.endUtc.slice(0,10)).join(' vs ')+' (later minus earlier).');
    }
    if(layer?.pending)extra='Loading the comparison layer. The terrain result is ready.';
    else if(layer?.error)extra='The comparison layer could not be opened. The terrain result is still visible.';
    else if(p.view!=='terrain'&&!meta)extra='No comparison for this visit. The terrain result is still visible.';
    $('sim-compare').textContent=extra;
    const link=$('sim-source');link.hidden=!(p.view==='impact'&&values);
    if(!link.hidden)link.href=meta.sourceUrl;
    $('sim-method').textContent=stage
      ?'30 m NASADEM · HAND ≤ stage and slope ≤ 8°. Drainage starts at 1 km² of contributing area within a '+(m.bufferM/1000).toFixed(1)+' km buffered grid. Unresolved cells are excluded; open DEM edges and the drainage choice affect coverage. Stage is relative to local drainage. HH is from the selected NISAR visit; it cannot identify Boro rice or predict the next pass.'
      :'30 m NASADEM · FoS compares resisting and driving stresses. Water unit weight is 9.81 kN/m³; uniform soil assumptions are editable. The 3D view samples a coarser display mesh. Coherence and mapped impacts are separate observations; this model does not estimate runout or identify actual failures.';
    if(stage){
      const points=p.points,[h,w]=m.grid.shape;
      $('sim-example').hidden=!m.example;
      let note=points.length===1?'Set the other end of the barrier.':points.length===2?'Choose the drainage source.':points.length===3?'Barrier and source set.':'Set two barrier ends and a drainage source, by map or grid coordinates.';
      if(points.length>=2){
        const line=atlasBarrierLine(points[0],points[1],w);
        for(const i of line)marks[i]=6;
        if(points.length===3){
          const breach=atlasBreachScreen(cells,[h,w],...points);
          if(breach){
            for(let i=0;i<marks.length;i++)if(breach.reach[i]===2)marks[i]=7;
            marks[breach.gap]=8;marks[breach.seed]=8;
            note=area(breach.open-breach.closed)+' newly connected · '+area(breach.closed)+' closed vs '+area(breach.open)+' open.';
            keys.push([7,'Newly connected'],[8,'Opening / source']);
          }else note='The source must meet the stage screen and sit outside the assumed barrier.';
        }
        keys.push([6,'Assumed barrier']);
      }
      for(const [x,y] of points)marks[y*w+x]=8;
      $('sim-breach-result').textContent=p.pointError||note;
      if(picking&&s.layer!=='coherence'&&s.terrain!=='on')$('sim-breach-result').textContent+=' Click the plan map.';
    }
    $('sim-map-note').textContent=s.layer==='coherence'?'Switch to an intensity layer to see the scenario on the map.':'';
    $('sim-legend').replaceChildren(...keys.map(([id,label])=>{
      const tag=document.createElement('span'),swatch=document.createElement('i');
      swatch.style.background='rgb('+atlasSimColors[id].slice(0,3).join(',')+')';
      tag.append(swatch,label);return tag;
    }));
    const caption=$('sim-map-caption');
    caption.hidden=s.layer==='coherence';
    caption.textContent='WHAT IF?  '+(stage?'River surge +'+p.stage.toFixed(1)+' m':'Slope stability · m '+p.m.toFixed(2)+' · '+p.kh.toFixed(2)+' g')+' · '+keys.map(([,label])=>label).join(' / ');
    const [h,w]=m.grid.shape;
    canvas.width=w;canvas.height=h;
    const ctx=canvas.getContext('2d'),image=ctx?.createImageData(w,h);
    if(image){
      for(let i=0;i<marks.length;i++)if(marks[i])image.data.set(atlasSimColors[marks[i]],4*i);
      ctx.putImageData(image,0,0);
    }
    const toRadar=pos=>atlasWorldToGrid(c.grid.affine,atlasGridToWorld(m.grid.affine,pos));
    const [left,top]=toRadar([0,0]),[right,bottom]=toRadar([w,h]),[rh,rw]=c.grid.shape;
    Object.assign(canvas.style,{left:left/rw*100+'%',top:top/rh*100+'%',width:(right-left)/rw*100+'%',height:(bottom-top)/rh*100+'%'});
    canvas.hidden=s.layer==='coherence'||s.terrain==='on';
    overlay={revision:++revision,sample:(u,v)=>{
      const x=Math.floor((u*rw-left)*w/(right-left)),y=Math.floor((v*rh-top)*h/(bottom-top));
      return x>=0&&x<w&&y>=0&&y<h?atlasSimColors[marks[y*w+x]]:null;
    }};
    redraw();
  }
  function put(points){
    const data=entry()?.data,p=state();
    const [h,w]=data.m.grid.shape;
    if(!points.every(([x,y])=>Number.isInteger(x)&&Number.isInteger(y)&&x>=0&&x<w&&y>=0&&y<h))
      p.pointError='Enter whole column and row numbers inside this terrain grid.';
    else if(points.length>=2&&atlasBarrierLine(points[0],points[1],w).length<3)
      p.pointError='Set the barrier ends at least two grid cells apart.';
    else if(points.length===3&&!data.drainage[points[2][1]*w+points[2][0]])
      p.pointError='Choose a mapped drainage cell as the source. Use the terrain screen to find the channel.';
    else{
      p.pointError='';p.points=points;
      $('sim-coords').value=points.map(pt=>pt.join(',')).join(' / ');
      if(points.length===3){picking=false;$('sim-pick').setAttribute('aria-pressed','false');}
    }
    schedule();
  }
  panel.ontoggle=sync;
  for(const k of inputKeys){
    input(k).oninput=e=>{
      const value=e.target.valueAsNumber;
      if(Number.isFinite(value)&&value>=Number(e.target.min)&&value<=Number(e.target.max))state()[k]=value;
      schedule();
    };
    input(k).onchange=()=>{input(k).value=state()[k];};
  }
  $('sim-view').onchange=e=>{state().view=e.target.value;schedule();};
  $('sim-retry').onclick=()=>{cache.delete(current.c.case);sync();};
  $('sim-show').onclick=()=>showMap(false);
  $('sim-pick').onclick=()=>{
    picking=!picking;
    $('sim-pick').setAttribute('aria-pressed',String(picking));
    if(picking){put([]);showMap(true);}else schedule();
  };
  $('sim-clear').onclick=()=>{picking=false;$('sim-pick').setAttribute('aria-pressed','false');put([]);};
  $('sim-example').onclick=()=>{
    state().stage=2;input('stage').value=2;put(entry().data.m.example);
  };
  $('sim-apply').onclick=()=>{
    const input=$('sim-coords').value.trim(),points=input.split('/').map(pair=>pair.split(',').map(v=>v.trim()));
    if(points.length!==3||!points.every(pair=>pair.length===2&&pair.every(v=>/^\d+$/.test(v)))){
      state().pointError='Enter three column,row pairs separated by slashes.';schedule();return;
    }
    put(points.map(pair=>pair.map(Number)));
  };
  return {
    update(c,o,s,show){
      const switched=current?.c.case!==c.case;
      if(current?.o.observation_id!==o.observation_id)canvas.hidden=true;
      current={c,o,s};
      panel.hidden=!show||!manifestFor(c.case);
      panel.open=!panel.hidden;
      if(switched){
        $('sim-controls').hidden=true;
        $('sim-result').textContent='';
        $('sim-compare').textContent='';
        for(const k of inputKeys)input(k).value=state()[k];
        picking=false;$('sim-pick').setAttribute('aria-pressed','false');
        $('sim-coords').value=state().points.map(pt=>pt.join(',')).join(' / ');
        clear();
      }
      describe();sync();
    },
    ready(){
      if(panel.hidden||!panel.open)return true;
      const item=entry();
      if(!item||item.pending)return false;
      if(!item.data||state().view!=='hh')return true;
      const {data}=item,meta=data.m.observations?.[current.o.observation_id];
      return !meta||data.layers.get(meta.file)?.pending===false;
    },
    pick(pt){
      const data=entry()?.data;
      if(!picking||!panel.open||data?.m.kind!=='stage')return false;
      const xy=atlasWorldToGrid(data.m.grid.affine,atlasGridToWorld(current.c.grid.affine,pt)).map(Math.floor);
      put([...state().points,xy]);return true;
    },
    overlay:()=>overlay,
  };
}
