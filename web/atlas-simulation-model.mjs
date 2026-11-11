export function atlasSlopeTerms(slopes){
  const driving=new Float32Array(slopes.length), normal=new Float32Array(slopes.length);
  for(let i=0;i<slopes.length;i++){
    const angle=slopes[i]*Math.PI/180;
    if(!(angle>=0&&angle<Math.PI/2)){driving[i]=NaN;continue;}
    const cos=Math.cos(angle);normal[i]=cos*cos;driving[i]=Math.sin(angle)*cos;
  }
  return {driving,normal};
}
export function atlasSlopeScreen({driving,normal},{m,kh,cohesion,friction,depth,weight}){
  const dry=weight*depth, shaking=kh*dry, strength=(weight-m*9.81)*depth*Math.tan(friction*Math.PI/180);
  const cells=new Uint8Array(driving.length);let assessed=0,below=0;
  for(let i=0;i<driving.length;i++){
    if(!Number.isFinite(driving[i]))continue;
    const load=dry*driving[i]+shaking;
    // No driving stress on level terrain with shaking off.
    const fos=load>0?(cohesion+strength*normal[i])/load:Infinity;
    const failing=fos<1;
    cells[i]=failing?2:1;assessed++;below+=failing;
  }
  return {cells,assessed,below};
}
export function atlasStageScreen(stages,tenths){
  const cells=new Uint8Array(stages.length);let assessed=0,below=0;
  for(let i=0;i<stages.length;i++){
    if(stages[i]===255)continue;
    const eligible=stages[i]<=tenths;
    cells[i]=eligible?2:1;assessed++;below+=eligible;
  }
  return {cells,assessed,below};
}
export function atlasBarrierLine([x,y],[endX,endY],width){
  const dx=Math.abs(endX-x),dy=-Math.abs(endY-y),sx=x<endX?1:-1,sy=y<endY?1:-1;
  let error=dx+dy;
  const cells=[];
  while(true){
    cells.push(y*width+x);
    if(x===endX&&y===endY)return cells;
    const twice=2*error;
    if(twice>=dy){error+=dy;x+=sx;}
    if(twice<=dx){error+=dx;y+=sy;}
  }
}
export function atlasBreachScreen(cells,[height,width],a,b,source){
  const line=atlasBarrierLine(a,b,width), gap=line[Math.floor(line.length/2)], seed=source[1]*width+source[0];
  if(line.length<3||cells[seed]!==2||line.includes(seed))return null;
  const barriers=new Uint8Array(cells.length),reach=new Uint8Array(cells.length);
  const queue=new Int32Array(cells.length);
  for(const i of line)barriers[i]=1;
  function fill(mark){
    queue[0]=seed;reach[seed]|=mark;
    let head=0,tail=1;
    function enqueue(i){
      if(cells[i]===2&&!barriers[i]&&!(reach[i]&mark)){reach[i]|=mark;queue[tail++]=i;}
    }
    while(head<tail){
      const i=queue[head++],x=i%width;
      if(x>0)enqueue(i-1);if(x<width-1)enqueue(i+1);
      if(i>=width)enqueue(i-width);if(i<width*(height-1))enqueue(i+width);
    }
    return tail;
  }
  const closed=fill(1);barriers[gap]=0;const open=fill(2);
  return {reach,line,gap,seed,closed,open};
}
