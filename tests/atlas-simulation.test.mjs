import assert from 'node:assert/strict';
import {test} from 'node:test';
import {atlasStageScreen,atlasBreachScreen,atlasSlopeTerms,atlasSlopeScreen} from '../web/atlas-simulation-model.mjs';

test('HAND stage uses inclusive thresholds and preserves unavailable terrain',()=>{
  const stage=Uint8Array.of(0,10,11,100,101,254,255);
  assert.deepEqual([...atlasStageScreen(stage,10).cells],[2,2,1,1,1,1,0]);
  const result=atlasStageScreen(stage,100);
  assert.deepEqual([...result.cells],[2,2,2,2,1,1,0]);
  assert.equal(result.assessed,6);
  assert.equal(result.below,4);
});

test('A breach opens only an eligible cell; closed and open reachability are counted separately',()=>{
  const size=[5,5],cells=Uint8Array.from({length:25},()=>2);
  const result=atlasBreachScreen(cells,size,[2,0],[2,4],[0,2]);
  assert.equal(result.gap,12);
  assert.equal(result.closed,10);
  assert.equal(result.open,21);
  assert.equal(result.reach[24],2);
  assert.equal(result.reach[0],3);
  cells[12]=1;
  assert.equal(atlasBreachScreen(cells,size,[2,0],[2,4],[0,2]).open,10);
  assert.equal(atlasBreachScreen(cells,size,[2,0],[2,4],[2,1]),null);
});

test('Infinite-slope thresholds separate assumed water and shaking from terrain support',()=>{
  const terms=atlasSlopeTerms(Float32Array.of(0,30,45,NaN));
  const assumptions={m:0,kh:0,cohesion:5,friction:32,depth:2,weight:18};
  const dry=atlasSlopeScreen(terms,assumptions);
  assert.deepEqual([...dry.cells],[1,1,2,0]);
  const saturated=atlasSlopeScreen(terms,{...assumptions,m:1});
  assert.deepEqual([...saturated.cells],[1,2,2,0]);
  const shaken=atlasSlopeScreen(terms,{...assumptions,m:1,kh:.4,cohesion:0});
  assert.deepEqual([...shaken.cells],[2,2,2,0]);
  assert.equal(shaken.assessed,3);
});
