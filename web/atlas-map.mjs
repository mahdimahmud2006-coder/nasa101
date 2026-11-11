import {atlasNode,atlasElement} from './atlas-dom.mjs';
import {labels,iso} from './atlas-state.mjs';
export function createAtlasDrape(set,loadTerrain){
  const $=atlasNode;let drawGeneration=0,key='',sampleCase='',samples=new Map();
  // Display-only terrain: all three axes use metres; no scientific values are
  // sampled from the display pixels. Invalid elevations remain holes.
  return async function drape(c,o,ref,s,scenario){
    const canvas=$('drape'),on=s.terrain==='on';
    canvas.hidden=!on;$('plan').hidden=$('image-stack').hidden=on;$('rotate').hidden=!on;
    if(!on)canvas.dataset.ready='off';
    $('mode').disabled=s.layer==='coherence';$('mode').setAttribute('aria-pressed',String(on));
    $('mode').textContent=on?'Plan view':'Terrain';
    const next=on?[c.case,s.layer,s.date,s.bearing,s.split,scenario?.revision??0].join(':'):'';
    if(next===key)return;
    key=next;
    const token=++drawGeneration;
    if(!on)return;
    canvas.dataset.ready='loading';
    canvas.setAttribute('aria-label','Loading sampled NASADEM relief for '+iso(s.date));
    const ctx=canvas.getContext('2d');
    if(!ctx){set({terrain:'off'},{announce:'Terrain rendering is unavailable. Showing the plan view.'});return;}
    const sample=async src=>{const im=new Image();im.src=src;await im.decode();
      const pan=document.createElement('canvas');pan.width=im.naturalWidth;pan.height=im.naturalHeight;const x=pan.getContext('2d');
      x.imageSmoothingEnabled=false;x.drawImage(im,0,0);return x.getImageData(0,0,pan.width,pan.height);};
    if(sampleCase!==c.case){sampleCase=c.case;samples=new Map();}
    const cached=src=>{
      if(!samples.has(src)){
        if(samples.size>=4)samples.delete(samples.keys().next().value);
        const bank=samples;
        bank.set(src,sample(src).catch(error=>{bank.delete(src);throw error;}));
      }
      return samples.get(src);
    };
    try{
      const [a,b]=await Promise.all([cached(o.images[s.layer]),cached(ref.images[s.layer]),loadTerrain?.(c.case)]);
      if(token!==drawGeneration)return;
      const m=c.terrain,n=m.size,z0=Math.min(...m.elevation_m.filter(Number.isFinite));
      const pts=m.elevation_m.map((z,j)=>Number.isFinite(z)?atlasTerrainPoint(m,Math.floor(j/n),j%n,z,z0,s.bearing):null);
      const faces=[];
      for(let row=0;row<n-1;row++)for(let col=0;col<n-1;col++){
        const j=row*n+col,vertices=[j,j+1,j+n+1,j+n].map(t=>pts[t]);
        if(vertices.some(v=>!v))continue;
        const [u,v]=atlasTerrainUV(n,c.grid.shape,row+.5,col+.5);
        const pix=u<s.split/100?b:a,offset=4*(Math.floor(v*pix.height)*pix.width+Math.floor(u*pix.width));
        const mark=scenario?.sample(u,v),valid=pix.data[offset+3];
        if(!valid&&!scenario)continue;
        let rgb=valid?pix.data.slice(offset,offset+3):[51,67,76];
        if(scenario?.base==='neutral'){
          const light=24+(.213*rgb[0]+.715*rgb[1]+.072*rgb[2])*.66;
          rgb=[Math.round(light*.86),Math.round(light*.97),Math.round(light*1.08)];
        }
        if(mark)for(let k=0;k<3;k++)rgb[k]=Math.round((rgb[k]*(255-mark[3])+mark[k]*mark[3])/255);
        faces.push({vertices,depth:vertices.reduce((sum,v)=>sum+v[2],0),color:'rgb('+rgb.join(',')+')'});
      }
      if(!faces.length)throw Error('Terrain missing');
      // Fit the canvas to the painted relief at this bearing. A fixed canvas
      // aspect ratio leaves side gutters as the projected terrain shape changes.
      const visible=faces.flatMap(face=>face.vertices);
      const xs=visible.map(p=>p[0]),ys=visible.map(p=>p[1]);
      const x0=Math.min(...xs),y0=Math.min(...ys),w=Math.max(...xs)-x0,h=Math.max(...ys)-y0;
      const padding=12,k=(canvas.width-2*padding)/w;
      canvas.height=Math.ceil(h*k+2*padding);
      for(const face of faces.sort((a,b)=>b.depth-a.depth)){
        ctx.beginPath();face.vertices.forEach(([x,y],i)=>ctx[i?'lineTo':'moveTo'](padding+(x-x0)*k,padding+(y-y0)*k));
        ctx.closePath();ctx.fillStyle=ctx.strokeStyle=face.color;ctx.fill();ctx.lineWidth=.6;ctx.stroke();
      }
      canvas.dataset.ready='yes';
      canvas.setAttribute('aria-label',labels[s.layer]+' on '+iso(s.date)+' on sampled NASADEM relief, vertical scale 1×, bearing '+s.bearing+' degrees.'+(scenario?' Includes the active terrain scenario.':''));
    }catch{if(token===drawGeneration)set({terrain:'off'},{announce:'Terrain display unavailable; showing the observed plan view.'});}
  }
}

export function atlasGridToWorld([a,b,c,d,e,f],[col,row]){
  return [a*col+b*row+c,d*col+e*row+f];
}

export function atlasWorldToGrid([a,b,c,d,e,f],[x,y]){
  const det=a*e-b*d;
  if(!Number.isFinite(det)||!det)throw Error('Native grid is singular.');
  return [(e*(x-c)-b*(y-f))/det,(a*(y-f)-d*(x-c))/det];
}

export function atlasDisplayToGrid(rect,[height,width],x,y){
  if(!rect.width||!rect.height)return null;
  const u=(x-rect.left)/rect.width,v=(y-rect.top)/rect.height;
  return u>=0&&u<1&&v>=0&&v<1?[u*width,v*height]:null;
}

export function atlasTerrainPoint(mesh,row,col,z,minimum,bearing){
  const theta=bearing*Math.PI/180;
  const x=(col/(mesh.size-1)-.5)*mesh.width_m;
  const y=(.5-row/(mesh.size-1))*mesh.height_m;
  const depth=x*Math.sin(theta)+y*Math.cos(theta);
  return [x*Math.cos(theta)-y*Math.sin(theta),-(depth*.5+(z-minimum)*Math.sqrt(.75)),depth];
}

export function atlasTerrainUV(size,[height,width],row,col){
  return [(.5+col*(width-1)/(size-1))/width,(.5+row*(height-1)/(size-1))/height];
}

const atlasPreviewScaleCap=8,atlasSmallWindow=250,atlasPaneGap=8;

export function atlasMapZoomLimit(fitWidth,sourceLimit){
  return fitWidth>0?Math.max(1,Math.min(4,sourceLimit/fitWidth)):4;
}

export function createAtlasMap({active,current,set,portable,compareVisits,normalize,measure,resetProbe,showProbeStatus,pickSimulation,canMeasure=()=>true}){
  const $=atlasNode,viewport=$('map'),stack=$('image-stack'),overlay=$('overlay');
  const reference=$('reference'),referencePane=$('reference-stack'),referenceOutline=$('reference-outline');
  const selected=$('current'),plan=$('plan');
  let zoom=1,maxZoom=4,draft=null,previousCase='',previousNative=null,reviewLocation=null,pairShape=null,cursor=null,pinch=null,lastFootprint='',footprintSupport;
  function updateGeometry(){
    const c=active(),s=current(),[h,w]=pairShape??c.grid.shape,aspect=w/h;
    const bounds=s.native?null:reviewLocation?.boundsPixel;
    const compactFootprint=bounds&&Math.max(bounds[2]-bounds[0],bounds[3]-bounds[1])<atlasSmallWindow;
    const usable=image=>image.dataset.ready==='yes'&&image.naturalWidth>0&&image.naturalHeight>0;
    const compactImage=usable(selected)&&Math.max(selected.naturalWidth,selected.naturalHeight)<atlasSmallWindow;
    const sideBySide=Boolean(compareVisits&&s.split>0&&s.layer!=='coherence'&&s.terrain!=='on'&&(compactFootprint||compactImage));
    if(viewport.dataset.sideBySide!==String(sideBySide))zoom=1;
    viewport.dataset.sideBySide=String(sideBySide);
    referencePane.hidden=$('selected-pane-label').hidden=!sideBySide;
    $('compare-caption').hidden=!sideBySide;
    const parent=sideBySide?referencePane:stack;
    if(reference.parentElement&&reference.parentElement!==parent){
      if(sideBySide)referencePane.prepend(reference);
      else selected.after(reference);
    }
    const sources=[selected,...(!reference.hidden?[reference]:[])].filter(usable);
    const sourceLimit=atlasPreviewScaleCap*Math.min(...sources.map(image=>Math.min(image.naturalWidth,image.naturalHeight*aspect)));
    const width=viewport.offsetWidth,height=viewport.offsetHeight,panes=sideBySide?2:1;
    const fitWidth=Math.min((width-(sideBySide?atlasPaneGap:0))/panes,height*aspect,sourceLimit);
    maxZoom=atlasMapZoomLimit(fitWidth,sourceLimit);
    zoom=Math.min(zoom,maxZoom);
    viewport.style.setProperty('--map-aspect',aspect);
    viewport.style.setProperty('--preview-limit',Number.isFinite(sourceLimit)?sourceLimit+'px':'100vmax');
    viewport.style.setProperty('--pane-gap',atlasPaneGap+'px');
    viewport.dataset.zoomed=String(zoom>1&&s.terrain!=='on');
    plan.style.setProperty('--map-zoom',zoom);
    $('zoom-out').disabled=zoom===1||s.terrain==='on';
    $('zoom-in').disabled=zoom>=maxZoom||s.terrain==='on';
    $('zoom-in').title=zoom>=maxZoom&&maxZoom<4?'Preview pixel limit reached':'Zoom in';
    $('zoom-reset').disabled=zoom===1||s.terrain==='on';
  }
  function draw(c,s){
    const [h,w]=pairShape??c.grid.shape;
    updateGeometry();
    const canInspect=!portable&&canMeasure()&&s.layer!=='coherence'&&s.terrain!=='on';
    stack.dataset.inspect=referencePane.dataset.inspect=String(canInspect);
    $('draw').setAttribute('aria-pressed',String(Boolean(draft)));
    $('draw').disabled=!canInspect;
    $('undo').disabled=!draft?.length;
    $('cancel').disabled=!draft;
    overlay.replaceChildren();
    referenceOutline.replaceChildren();
    if(!canInspect&&(!reviewLocation||s.layer==='coherence'||s.terrain==='on'))return;
    overlay.setAttribute('viewBox','0 0 '+w+' '+h);
    overlay.setAttribute('preserveAspectRatio','none');
    referenceOutline.setAttribute('viewBox','0 0 '+w+' '+h);
    referenceOutline.setAttribute('preserveAspectRatio','none');
    const node=(tag,attrs)=>{
      const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
      for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));
      overlay.append(n);
      if(compareVisits&&typeof n.cloneNode==='function')referenceOutline.append(n.cloneNode());
    };
    const stroke={'vector-effect':'non-scaling-stroke',stroke:'#fff2a8','stroke-width':2,fill:'#fff2a84d'};
    if(draft||s.native?.startsWith('[')){
      const pts=draft??JSON.parse(s.native);
      node(draft?'polyline':'polygon',{...stroke,fill:draft?'none':stroke.fill,points:pts.map(p=>p.join(',')).join(' ')});
      if(draft)for(const [x,y] of pts)node('circle',{cx:x,cy:y,r:Math.max(w,h)/200,...stroke});
    }else if(s.native){
      const [row,col]=s.native.split(',').map(Number);
      const x=Math.max(0,col-5),y=Math.max(0,row-5);
      const center=footprintSupport?.centerProjected??atlasGridToWorld(c.grid.affine,[col+.5,row+.5]);
      const [cx,cy]=atlasWorldToGrid(c.grid.affine,center);
      node('rect',{x,y,width:Math.min(w,col+6)-x,height:Math.min(h,row+6)-y,...stroke});
      node('circle',{cx,cy,r:1.6,...stroke});
    }else if(reviewLocation){
      const [x,y,right,bottom]=reviewLocation.boundsPixel;
      node('rect',{x,y,width:right-x,height:bottom-y,...stroke,fill:'none','stroke-dasharray':'5 3'});
      node('circle',{cx:reviewLocation.col+.5,cy:reviewLocation.row+.5,r:Math.max(w,h)/110,...stroke});
    }
    if(cursor&&document.activeElement===viewport&&!pairShape){
      const [x,y]=cursor,d=Math.max(w,h)/65;
      node('path',{d:'M'+(x-d)+' '+y+'h'+2*d+' M'+x+' '+(y-d)+'v'+2*d,
        'vector-effect':'non-scaling-stroke',stroke:'#ffffff','stroke-width':2});
    }
  }
  function setZoom(value){
    const map=viewport.getBoundingClientRect(),before=plan.getBoundingClientRect();
    const center=[(map.left+map.width/2-before.left)/before.width,(map.top+map.height/2-before.top)/before.height];
    zoom=Math.min(maxZoom,Math.max(1,value));updateGeometry();
    if(zoom===1){viewport.scrollLeft=viewport.scrollTop=0;return;}
    const after=plan.getBoundingClientRect();
    viewport.scrollLeft+=after.left+after.width*center[0]-map.left-map.width/2;
    viewport.scrollTop+=after.top+after.height*center[1]-map.top-map.height/2;
  }
  $('zoom-in').onclick=()=>setZoom(zoom*2);
  $('zoom-out').onclick=()=>setZoom(zoom/2);
  $('zoom-reset').onclick=()=>setZoom(1);
  if(typeof ResizeObserver==='function')new ResizeObserver(updateGeometry).observe(viewport);
  function edit(vertices){
    draft=vertices;
    $('coords').value=draft?JSON.stringify(draft):current().native||'';
    draw(active(),current());
  }
  $('draw').onclick=()=>{
    const {native}=current();
    edit(native?.startsWith('[')?JSON.parse(native):[]);
    resetProbe();
    showProbeStatus('Click around the boundary in order, then choose Measure footprint. The polygon closes automatically.');
  };
  function revise(){
    resetProbe();
    showProbeStatus('Edit the coordinates or choose Measure footprint to check them.');
  }
  $('coords').oninput=revise;
  $('undo').onclick=()=>{edit(draft.slice(0,-1));revise();};
  $('cancel').onclick=()=>{edit(null);resetProbe();showProbeStatus('Draft discarded.');$('draw').focus?.();};
  $('probe').onclick=()=>{
    const val=normalize(active(),$('coords').value);
    if(!val){
      resetProbe();
      showProbeStatus('Enter a valid in-grid row and column or 3–200 [column,row] polygon vertices.');
      return;
    }
    measure(val,{onAccept:()=>{draft=null;}});
  };
  $('clear').onclick=()=>{edit(null);set({native:''});};
  function pick(pt){
    const s=current();
    if(s.layer==='coherence'||$('current').dataset.ready!=='yes'||!pt)return;
    if(pickSimulation?.(pt)||portable||!canMeasure())return;
    const [col,row]=pt;
    $('probe-panel').open=true;
    if(draft){
      if(draft.length===200){$('probe-help').textContent='Polygon limit reached. Undo a vertex or measure the draft.';return;}
      edit([...draft,pt.map(n=>Math.round(n*100)/100)]);
      revise();
      return;
    }
    measure(Math.floor(row)+','+Math.floor(col));
  }
  for(const pane of [stack,referencePane])pane.onclick=e=>{
    pick(atlasDisplayToGrid(pane.getBoundingClientRect(),active().grid.shape,e.clientX,e.clientY));
  };
  viewport.onkeydown=event=>{
    if(event.target!==viewport)return;
    const s=current(),[h,w]=active().grid.shape;
    if(s.layer==='coherence'||s.terrain==='on'||portable)return;
    const directions={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
    if(!directions[event.key]&&event.key!=='Enter')return;
    event.preventDefault();
    cursor??=[Math.floor(w/2)+.5,Math.floor(h/2)+.5];
    if(event.key==='Enter'){pick(cursor);return;}
    const [dx,dy]=directions[event.key],step=event.shiftKey?100:10;
    cursor=[Math.max(.5,Math.min(w-.5,cursor[0]+dx*step)),Math.max(.5,Math.min(h-.5,cursor[1]+dy*step))];
    $('map-position').textContent='Row '+Math.floor(cursor[1])+', column '+Math.floor(cursor[0])+'. Press Enter to select.';
    draw(active(),s);
  };
  viewport.onblur=()=>{if(cursor)draw(active(),current());};
  const touchAngle=touches=>Math.atan2(touches[1].clientY-touches[0].clientY,touches[1].clientX-touches[0].clientX)*180/Math.PI;
  const touchDistance=touches=>Math.hypot(touches[1].clientX-touches[0].clientX,touches[1].clientY-touches[0].clientY);
  viewport.addEventListener('touchstart',event=>{
    if(event.touches.length!==2)return;
    pinch={distance:touchDistance(event.touches),angle:touchAngle(event.touches),zoom,bearing:current().bearing};
  },{passive:true});
  viewport.addEventListener('touchmove',event=>{
    if(!pinch||event.touches.length!==2)return;
    event.preventDefault();
    if(current().terrain==='on'){
      const bearing=(pinch.bearing+Math.round((touchAngle(event.touches)-pinch.angle)/45)*45+360)%360;
      if(current().bearing!==bearing)set({bearing},{replace:true});
    }else if(pinch.distance>0){
      const value=Math.min(maxZoom,Math.max(1,pinch.zoom*touchDistance(event.touches)/pinch.distance));
      if(Math.abs(value-zoom)>.04)setZoom(value);
    }
  },{passive:false});
  for(const event of ['touchend','touchcancel'])viewport.addEventListener(event,()=>{pinch=null;},{passive:true});
  function render(c,s,support,review,pairGrid){
    reviewLocation=review;pairShape=pairGrid?.shape;footprintSupport=support;
    if(previousCase!==c.case){
      zoom=1;draft=null;cursor=null;previousCase=c.case;previousNative=null;
    }
    if(previousNative!==s.native){
      previousNative=s.native;draft=null;$('coords').value=s.native||'';
    }
    if(draft&&(s.layer==='coherence'||s.terrain==='on'))edit(null);
    draw(c,s);
    const selected=[c.case,s.native??s.profile].join('/');
    if(lastFootprint&&lastFootprint!==selected&&overlay.childNodes?.length&&typeof overlay.animate==='function'&&
       !matchMedia('(prefers-reduced-motion: reduce)').matches&&!document.getElementById('atlas').dataset.tour){
      overlay.animate([{opacity:.45},{opacity:1}],{duration:180});
    }
    lastFootprint=selected;
  }
  return {render,updateGeometry};
}

export function renderAtlasLegend(c,layer){
  const box=atlasNode('legend'),co=layer==='coherence',fraction=layer==='fraction';
  const palette=c.country==='Bangladesh'&&!fraction?'radar-blue':'cividis';
  const swatch=atlasElement('span',''),missing=atlasElement('span','');
  swatch.className='atlas-swatch '+palette;missing.className='atlas-missing';
  swatch.setAttribute('aria-hidden','true');missing.setAttribute('aria-hidden','true');
  const range=co?'0 to 1 coherence':fraction?'0% to 100% HV power share':
    c.limits[layer].map(x=>x.toFixed(2)).join(' to ')+' dB';
  box.replaceChildren(swatch,atlasElement('span','Low to high · '+range+(co?'':fraction?'':' · darker = weaker return')),missing,atlasElement('span','No data · transparent'));
}

async function atlasLocalIntensityFrames(c){
  const manifestUrl=new URL('/'+c.manifest_path,location.href);
  const caseRoot='/cases/'+c.case+'/';
  if(manifestUrl.origin!==location.origin||!manifestUrl.pathname.startsWith(caseRoot))return null;
  const response=await fetch(manifestUrl);
  if(!response.ok)return null;
  const bytes=await response.arrayBuffer();
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  const checksum=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
  if(checksum!==c.manifest_sha256)return null;
  const manifest=JSON.parse(new TextDecoder().decode(bytes));
  const frames=new Map();
  for(const visit of manifest.observations){
    const sources={};
    for(const layer of ['hh','hv']){
      const asset=visit.layers[layer];
      if(!asset)continue;
      const url=new URL(asset,manifestUrl);
      if(url.origin===manifestUrl.origin&&url.pathname.startsWith(caseRoot)&&/\.(png|webp)$/.test(url.pathname))
        sources[layer]=url.pathname;
    }
    frames.set(visit.observation_id,{utc:visit.timestamp,sources});
  }
  return frames;
}

export function createAtlasFrames({local=false,entryPreview,onGeometry}={}){
  const $=atlasNode,current=$('current'),reference=$('reference'),plan=$('plan');
  const requests=new WeakMap(),details=new Map();
  let comparing=false,viewKey='',generation=0,lastLayer='';
  const decoded=new Map();
  function predecode(source){
    if(decoded.has(source))return decoded.get(source);
    if(decoded.size>=12)decoded.delete(decoded.keys().next().value);
    const image=new Image(),entry={ready:false};
    image.src=source;
    entry.promise=image.decode().then(()=>{entry.ready=true;},error=>{
      if(decoded.get(source)===entry)decoded.delete(source);
      throw error;
    });
    decoded.set(source,entry);
    return entry;
  }
  const ready=(image)=>image.dataset.ready==='yes';
  function sync(){
    const aligned=comparing&&ready(current)&&ready(reference)&&
      current.naturalWidth===reference.naturalWidth&&current.naturalHeight===reference.naturalHeight;
    plan.dataset.compare=String(aligned);
    onGeometry?.();
    $('frame-status').textContent=current.dataset.ready==='error'?'The selected radar preview is unavailable. Measurements are shown below.':
      comparing&&(reference.dataset.ready==='error'||ready(current)&&ready(reference)&&!aligned)?
        'Reference preview is unavailable or has a different grid. Showing the selected visit.':'';
  }
  function show(image,source,description,fallback){
    image.alt=description;
    const existing=requests.get(image);
    if(existing?.source===source){
      existing.fallback=fallback;
      if(image.dataset.ready==='error'&&fallback)Promise.resolve().then(fallback);
      return;
    }
    const request={source,fallback};requests.set(image,request);
    image.dataset.ready='loading';
    image.src=source;
    if(typeof image.decode!=='function')return;
    image.decode().then(()=>{
      if(requests.get(image)===request){
        image.dataset.ready='yes';sync();
        if(image===current&&typeof image.animate==='function'&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
          const layer=description.split(' on ')[0];
          image.animate([{opacity:.25},{opacity:1}],{duration:lastLayer===layer?220:160});
          lastLayer=layer;
        }
        if(ready(current)&&(!comparing||ready(reference))&&document.body.dataset.atlasHosted==='yes'&&!performance.getEntriesByName('atlas-first-usable').length){
          const mark=performance.mark('atlas-first-usable');
          if(new URLSearchParams(location.search).has('benchmark')){
            const entries=[...performance.getEntriesByType('navigation'),...performance.getEntriesByType('resource')];
            document.body.dataset.atlasBenchmark=JSON.stringify({readyMs:mark.startTime,userAgent:navigator.userAgent,
              resources:entries.map(e=>({path:new URL(e.name).pathname,bodyBytes:e.encodedBodySize,transferBytes:e.transferSize}))});
          }
        }
      }
    },()=>{
      if(requests.get(image)===request){
        image.dataset.ready='error';
        request.fallback?.();
        sync();
      }
    });
  }
  return (c,o,r,s,pair)=>{
    const co=s.layer==='coherence';
    comparing=!co&&s.split>0;reference.hidden=!comparing;reference.setAttribute('aria-hidden',String(!comparing));
    const key=[c.case,s.date,s.layer,comparing].join('/');
    if(key===viewKey)return;
    viewKey=key;
    const token=++generation;
    const selectedLabel=co?'Pairwise coherence for '+pair.dates.map(iso).join(' to '):labels[s.layer]+' on '+iso(s.date);
    const referenceLabel='Reference '+iso(c.reference)+' '+labels[s.layer];
    function present(selected,baseline,fallback){
      show(current,selected,selectedLabel,fallback);
      if(comparing)show(reference,baseline,referenceLabel,fallback);
      sync();
    }
    const compact=()=>{
      if(token===generation)present(co?pair.image:o.images[s.layer],r.images[s.layer]);
    };
    if(entryPreview&&c.case===entryPreview.case&&s.date===entryPreview.date&&s.layer==='hh'){
      present(entryPreview.selected,entryPreview.reference,compact);return;
    }
    function upgrade(frames){
      if(token!==generation||!frames)return false;
      const source=visit=>{
        const frame=frames.get(visit.observation_id);
        return frame?.utc===visit.timestamp?frame.sources[s.layer]:null;
      };
      const selected=source(o),baseline=comparing?source(r):null;
      if(!selected||comparing&&!baseline)return false;
      const needed=[predecode(selected),...(baseline?[predecode(baseline)]:[])];
      const apply=()=>{
        if(token!==generation)return;
        present(selected,baseline,compact);
        if(typeof requestIdleCallback==='function'&&!navigator.connection?.saveData){
          const i=c.observations.indexOf(o);
          requestIdleCallback(()=>{
            if(token!==generation)return;
            for(const adjacent of [c.observations[i+1],c.observations[i-1]]){
              const url=adjacent&&source(adjacent);
              if(url)predecode(url).promise.catch(()=>{});
            }
          });
        }
      };
      if(needed.every(entry=>entry.ready)){apply();return true;}
      Promise.all(needed.map(entry=>entry.promise)).then(apply).catch(()=>{});
      return false;
    }
    if(!local||!globalThis.crypto?.subtle||typeof Image!=='function'||typeof Image.prototype.decode!=='function'||!['hh','hv'].includes(s.layer)){compact();return;}
    if(!details.has(c.case)){
      const entry={};
      entry.pending=atlasLocalIntensityFrames(c).catch(()=>null).then(frames=>entry.frames=frames);
      details.set(c.case,entry);
    }
    const entry=details.get(c.case);
    if(upgrade(entry.frames))return;
    compact();
    if(entry.frames===undefined)entry.pending.then(upgrade);
  };
}
