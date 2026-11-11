const labRad=Math.PI/180;
const labClamp=(v,lo=0,hi=1)=>Math.max(lo,Math.min(hi,v));

export function atlasSynthesizeRadar({moisture,water,canopy}){
  const b=labClamp(canopy),wet=labClamp(moisture/100,0,.6),f=1-Math.exp(-Math.max(0,water)/9);
  const angle=38*labRad,cos=Math.cos(angle),sin=Math.sin(angle);
  const fresnel=permittivity=>{
    const r=Math.sqrt(permittivity-sin*sin);
    return ((cos-r)/(cos+r))**2;
  };
  const transmission=Math.exp(-1.5*b/cos);
  const surface=(1-f)*.28*fresnel(3.2+38*wet)+f*.004*fresnel(70);
  const surfaceHH=transmission*surface,volumeHH=.057*b,volumeHV=.033*b;
  const bounceHH=.13*f*(4*b*(1-b))*transmission;
  const hh=.0001+surfaceHH+volumeHH+bounceHH;
  const hv=.00005+.025*surfaceHH+volumeHV+.035*bounceHH;
  return {hhDb:10*Math.log10(hh),hvDb:10*Math.log10(hv),powerShare:hv/(hh+hv),
    components:{surface:surfaceHH,volume:volumeHH,bounce:bounceHH}};
}

export function atlasLabRGB({hhDb,hvDb,powerShare}){
  const scale=(v,lo,hi)=>Math.round(255*labClamp((v-lo)/(hi-lo)));
  return [scale(hhDb,-32,-3),scale(hvDb,-38,-10),scale(powerShare,0,.5)];
}

export function atlasPhaseCoherence(rmsCm,wavelengthCm){
  return Math.exp(-.5*(4*Math.PI*rmsCm/wavelengthCm)**2);
}

export function atlasOrbitScreen(dem,[h,w],buffer,posting,incidence,azimuth){
  const theta=incidence*labRad,angle=azimuth*labRad;
  const east=Math.sin(angle),north=Math.cos(angle);
  if(Math.abs(east)<Math.abs(north))throw Error('Orbit preset requires an east–west range component.');
  const cropW=w-2*buffer,cropH=h-2*buffer,cells=new Uint8Array(cropW*cropH),counts=[0,0,0,0,0];
  const step=east>0?-1:1, x0=east>0?w-1:0;
  const risePerStep=posting/(Math.abs(east)*Math.tan(theta)),layoverLimit=-Math.tan(theta);
  const shifts=Array.from({length:w},(_,k)=>Math.round(k*north/Math.abs(east)));
  const minimum=Math.min(0,shifts.at(-1)),maximum=Math.max(0,shifts.at(-1));
  for(let start=-maximum;start<h-minimum;start++){
    let horizon=-Infinity,seen=false,gap=false;
    for(let k=0;k<w;k++){
      const y=start+shifts[k],x=x0+step*k;
      if(y<0||y>=h)continue;
      const i=y*w+x,z=dem[i];
      if(!Number.isFinite(z)){if(seen)gap=true;continue;}
      seen=true;
      const intercept=z+risePerStep*k, shadow=intercept<horizon-1e-7;
      horizon=Math.max(horizon,intercept);
      if(x<buffer||x>=w-buffer||y<buffer||y>=h-buffer)continue;
      let code=0;
      if(shadow)code=2;
      else if(!gap&&x>0&&x+1<w&&y>0&&y+1<h){
        const toward=((dem[i+1]-dem[i-1])*east+(dem[i-w]-dem[i+w])*north)/(2*posting);
        if(Number.isFinite(toward))code=toward<layoverLimit?3:1;
      }
      cells[(y-buffer)*cropW+x-buffer]=code;
      if(code)counts[code]++;
    }
  }
  counts[0]=cells.length-counts[1]-counts[2]-counts[3];
  return {cells,counts};
}

export function atlasTransectSamples(a,b,shape){
  const dx=b[0]-a[0],dy=b[1]-a[1],length=Math.hypot(dx,dy);
  if(length<12||length>260)return null;
  const ux=dx/length,uy=dy/length,[h,w]=shape, samples=[];
  for(let j=0;j<=Math.floor(length);j++){
    const x=a[0]+.5+j*ux,y=a[1]+.5+j*uy;
    const indices=[-1,0,1].map(k=>{
      const cx=Math.floor(x-k*uy),cy=Math.floor(y+k*ux);
      return cx>=0&&cx<w&&cy>=0&&cy<h?cy*w+cx:-1;
    });
    samples.push({indices,x,y});
  }
  return {a,b,ux,uy,length,samples};
}

function atlasTransectEdge(row){
  if(row.slice(0,3).some(x=>x!==1)||row.slice(-3).some(x=>x!==0))return null;
  const first=row.findIndex((v,j)=>j>=3&&v===0&&row[j+1]===0&&row[j+2]===0);
  if(first<0||row.slice(0,first+3).some(v=>v===null))return null;
  if(row.slice(first+3).some((v,j)=>v===1&&row[j+first+4]===1&&row[j+first+5]===1))return null;
  return first-.5;
}

export function atlasBankTrace(transect,valid,dark,visitCount){
  const rows=[],samples=transect.samples,recurrence=Array.from({length:samples.length},()=>[0,0]);
  for(let visit=0;visit<visitCount;visit++){
    const bit=1<<visit;
    const row=samples.map(({indices},j)=>{
      let n=0,m=0;
      for(const i of indices)if(i>=0&&(valid[i]&bit)){n++;if(dark[i]&bit)m++;}
      if(n<2||2*m===n)return null;
      const value=+(2*m>n);
      recurrence[j][0]+=value;recurrence[j][1]++;
      return value;
    });
    rows.push(atlasTransectEdge(row));
  }
  const resolved=rows.filter(Number.isFinite);
  const min=Math.min(...resolved),max=Math.max(...resolved);
  const band=recurrence.filter(([dark,valid],j)=>j>min&&j<=max&&valid);
  const occurrence=band.length?band.reduce((sum,[dark,valid])=>sum+dark/valid,0)/band.length:0;
  return {rows,recurrence,resolved:resolved.length,excursion:resolved.length?max-min:null,occurrence};
}

export function atlasBankProjection(transect,trace,visit,multiplier,cycles,shape,cover,asset){
  const edge=trace.rows[visit];
  if(edge==null||trace.resolved<6)return null;
  const movement=trace.excursion*trace.occurrence*multiplier*cycles;
  const land=Math.min(transect.length,edge+movement),start=[transect.a[0]+.5,transect.a[1]+.5];
  const along=(d,offset=0)=>[start[0]+d*transect.ux-offset*transect.uy,start[1]+d*transect.uy+offset*transect.ux];
  const offset=(x,y)=>{
    const dx=x-start[0],dy=y-start[1];
    return [dx*transect.ux+dy*transect.uy,-dx*transect.uy+dy*transect.ux];
  };
  const hit=(x,y)=>{const [d,k]=offset(x,y);return d>edge&&d<=land&&Math.abs(k)<=1.5;};
  const corners=[along(edge,-1.5),along(land,-1.5),along(land,1.5),along(edge,1.5)];
  let cropland=0,assessed=0,eligible=0;
  if(land>edge){
    const xs=corners.map(v=>v[0]),ys=corners.map(v=>v[1]),[h,w]=shape;
    for(let y=Math.max(0,Math.floor(Math.min(...ys)));y<Math.min(h,Math.ceil(Math.max(...ys)));y++){
      for(let x=Math.max(0,Math.floor(Math.min(...xs)));x<Math.min(w,Math.ceil(Math.max(...xs)));x++){
        if(!hit(x+.5,y+.5))continue;
        eligible++;
        const label=cover?.[y*w+x];
        if(label)assessed++;
        if(label===2)cropland++;
      }
    }
  }
  return {movement:movement*30,displayMovement:(land-edge)*30,edge:along(edge),end:along(land),
    corners,cropland,assessed,eligible,assetHit:asset?hit(asset[0]+.5,asset[1]+.5):null,
    limited:land+1e-8<edge+movement};
}
