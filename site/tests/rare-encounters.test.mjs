import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {rareEncounterNote} from '../src/assets/encounters.js';

test('public rare locations match all 44 manifest species at exactly five percent',async()=>{
  const policy=JSON.parse(await readFile(new URL('../../data/fan-encounters.json',import.meta.url)));
  const locations=JSON.parse(await readFile(new URL('../public/data/locations.json',import.meta.url)));
  assert.deepEqual(locations.authorEncounters,policy);
  const ids=new Set();
  for(const row of policy.areas){
    const area=locations.locations.find(a=>a.id===row.mapId);assert.ok(area);
    for(const version of area.versions){
      const method=version.methods.find(m=>m.id===row.method);assert.ok(method);
      for(const id of row.species){
        ids.add(id);assert.equal(method.slots.filter(s=>s[0]===id).reduce((sum,s)=>sum+s[3],0),5);
      }
      assert.equal(method.slots.reduce((sum,s)=>sum+s[3],0),100);
    }
  }
  assert.equal(ids.size,44);
  for(const area of locations.locations.filter(a=>[156,157].includes(a.id)))assert.ok(!area.species.some(id=>ids.has(id)));
});

test('route and Dex notes explain the crystal gate and escape habitat text',()=>{
  const model={encounterPolicy:{version:2,chancePerSpecies:5,unlocks:{crystals:11},areas:[{mapId:88,species:['CAVEFANG'],reason:'Caverna <script>'}]}};
  assert.match(rareEncounterNote(model,{id:88}),/11 cristais/);
  assert.match(rareEncounterNote(model,{id:88}),/350, 450 e 540 BST/);
  assert.match(rareEncounterNote(model,{id:88}),/&lt;script&gt;/);
  assert.match(rareEncounterNote(model,null,{id:'CAVEFANG',name:'Cave Fang'}),/Cave Fang · encontro raro de 5%/);
  assert.equal(rareEncounterNote(model,{id:87}),'');
});
