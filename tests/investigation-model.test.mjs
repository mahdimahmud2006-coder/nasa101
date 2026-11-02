import test from 'node:test';
import assert from 'node:assert/strict';
import {availableLayers,safeLayer,canCompare,pixelFromPointer,finding,dossier} from '../web/investigation-model.mjs';
import fs from 'node:fs/promises';
const manifest=JSON.parse(await fs.readFile(new URL('../web/public/cases/nepal_surface/investigation/manifest.json',import.meta.url),'utf8'));
test('the first observed visit never offers an invented successive difference',()=>{
 assert.equal(availableLayers('surface',0).includes('successive'),false);
 assert.equal(safeLayer('successive','surface',0),'hh');
 assert.equal(availableLayers('surface',1).includes('successive'),true);
 assert.equal(canCompare('baseline'),false);assert.equal(canCompare('hv'),true);
});
test('river and wetland signature controls are scoped to their actual case type',()=>{
 assert.ok(availableLayers('river',1).includes('river'));assert.ok(!availableLayers('surface',1).includes('water'));
 assert.ok(availableLayers('wetland',1).includes('wetland'));assert.equal(safeLayer('river','wetland',1),'hh');
});
test('map picking respects letterboxing and rejects clicks outside the actual raster',()=>{
 const rect={left:100,top:100,width:800,height:400};
 assert.equal(pixelFromPointer(rect,150,300,[1000,1000]),null);
 assert.deepEqual(pixelFromPointer(rect,500,300,[1000,1000]),{row:500,col:500});
 assert.equal(pixelFromPointer(rect,700,300,[1000,1000]),null);
});
test('real measured profile supports persistence wording without inventing recovery or cause',()=>{
 const p=manifest.profiles[0];assert.ok(finding(p,2).includes('baseline HH difference persists'));
 assert.ok(finding(p,0).includes('no preceding-visit difference'));
 assert.ok(finding(null,2).includes('No missing measurement is replaced with zero'));
});
test('export carries exact selected visit, sources, footprint and scientific limits',()=>{
 const profile=manifest.profiles[0],result=dossier(manifest,profile,1,'hv');
 assert.equal(result.selected_observation_id,manifest.observations[1].observation_id);
 assert.equal(result.selected_layer,'hv');assert.equal(result.selected_footprint,profile);
 assert.equal(result.cause_status,'UNRESOLVED');assert.equal(result.prediction_status,'NOT_A_FORECAST');
 assert.equal(result.observations[1].source_granule_id,manifest.observations[1].source_granule_id);
 assert.deepEqual(result.provenance,manifest.provenance);assert.ok(result.limitations.length);
});
