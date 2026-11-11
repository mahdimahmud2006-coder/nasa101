import assert from 'node:assert/strict';
import {test} from 'node:test';
import {atlasSynthesizeRadar,atlasLabRGB,atlasPhaseCoherence,atlasOrbitScreen,atlasTransectSamples,atlasBankTrace,atlasBankProjection} from '../web/atlas-lab-model.mjs';

test('Forward model distinguishes soil, smooth water, canopy and flooded stems in fixed channels',()=>{
  const inputs={moisture:15,water:0,canopy:0};
  const dry=atlasSynthesizeRadar(inputs),wet=atlasSynthesizeRadar({...inputs,moisture:40});
  const water=atlasSynthesizeRadar({...inputs,water:70});
  const stems=atlasSynthesizeRadar({...inputs,water:70,canopy:.4});
  const canopy=atlasSynthesizeRadar({...inputs,canopy:.4});
  assert.ok(wet.hhDb>dry.hhDb);
  assert.ok(water.hhDb<dry.hhDb&&stems.hhDb>water.hhDb);
  assert.ok(stems.components.bounce>0&&canopy.components.bounce===0);
  assert.ok(canopy.hvDb>dry.hvDb);
  assert.ok(atlasLabRGB(water).every(x=>Number.isInteger(x)&&x>=0&&x<=255));
});
test('Shorter wavelengths respond more to the same assumed phase-center motion',()=>{
  assert.equal(atlasPhaseCoherence(0,5.6),1);
  assert.ok(atlasPhaseCoherence(1,5.6)<atlasPhaseCoherence(1,24));
  assert.ok(atlasPhaseCoherence(3,24)<atlasPhaseCoherence(1,24));
});
test('Terrain ray sweep casts shadow behind a ridge and reverses with the look direction',()=>{
  const grid=Float32Array.from({length:7*11},(_,i)=>i%11===5?120:0);
  const west=atlasOrbitScreen(grid,[7,11],1,30,45,270),east=atlasOrbitScreen(grid,[7,11],1,30,45,90);
  const flat=atlasOrbitScreen(new Float32Array(7*11),[7,11],1,30,45,90);
  assert.deepEqual(flat.counts,[0,45,0,0,0]);
  assert.equal(west.cells[2*9+5],2);
  assert.equal(east.cells[2*9+3],2);
  assert.equal(west.cells[2*9+3],3);
  assert.equal(east.cells[2*9+5],3);
  assert.ok(atlasOrbitScreen(grid,[7,11],1,30,50,270).counts[2]>=west.counts[2]);
});
test('Bank scenario uses visit recurrence, preserves missing edges and checks only the inland corridor',()=>{
  const shape=[9,34],valid=new Uint16Array(9*34).fill(1023),dark=new Uint16Array(valid.length);
  const t=atlasTransectSamples([2,4],[31,4],shape);
  for(let j=0;j<10;j++)for(let y=0;y<9;y++)for(let x=0;x<34;x++){
    const cutoff=j===9?34:j<5?11:15;
    if(x<cutoff)dark[y*34+x]|=1<<j;
  }
  const trace=atlasBankTrace(t,valid,dark,10),cover=new Uint8Array(valid.length).fill(2);
  assert.equal(trace.resolved,9);
  assert.equal(trace.excursion,4);
  assert.equal(trace.occurrence,.5);
  assert.equal(trace.rows.at(-1),null);
  assert.equal(atlasBankProjection(t,trace,9,2,2,shape,cover,null),null);
  const result=atlasBankProjection(t,trace,0,2,2,shape,cover,[16,4]);
  assert.equal(result.movement,240);
  assert.equal(result.cropland,result.eligible);
  assert.equal(result.assetHit,true);
  assert.equal(atlasBankProjection(t,trace,0,1,1,shape,cover,[16,4]).assetHit,false);
});
