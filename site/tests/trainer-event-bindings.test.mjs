import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {loadTrainerBindings,trainerBindingsPanel,pendingPage} from '../src/assets/pending.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../');
const registry=JSON.parse(await readFile(path.join(root,'data/regions/trainer-event-bindings-phase1.json'),'utf8'));
const backlog=JSON.parse(await readFile(path.join(root,'site/public/data/pending-regions.json'),'utf8'));

test('pilot source bindings have 13 distinct namespaced NPCs and no claimed runtime proof',()=>{
  assert.equal(registry.schema,1);
  assert.equal(registry.records.length,13);
  assert.equal(new Set(registry.records.map(x=>x.id)).size,13);
  assert.equal(registry.records.filter(x=>x.region==='HOENN').length,4);
  assert.equal(registry.records.filter(x=>x.region==='JOHTO').length,9);
  assert.ok(registry.records.every(x=>x.gameplay_verified===false));
  assert.ok(registry.records.every(x=>Number.isInteger(x.x)&&Number.isInteger(x.y)));
  assert.equal(registry.records.find(x=>x.id==='HOENN_ROUTE102_CALVIN').map_stage_id,null);
  assert.ok(registry.records.some(x=>x.id==='JH_VIOLET_FALKNER'&&x.map_stage_id===677));
});
test('early bindings render below trainer names with offline map distinction',()=>{
  const h=trainerBindingsPanel(registry,'HOENN');
  assert.match(h,/Calvin/);
  assert.match(h,/ID 102 da fonte/);
  assert.match(h,/Em validação/);
  assert.doesNotMatch(h,/Map102 · etapa offline/);
  const j=trainerBindingsPanel(registry,'JOHTO');
  assert.match(j,/Johto Joey/);
  assert.match(j,/Map625 · etapa offline/);
  assert.match(j,/Falkner/);
  assert.equal((j.match(/class="pending-card"/g)||[]).length,9);
  assert.equal(trainerBindingsPanel(registry,'SINNOH'),'');
});
test('candidate rival Route 103 remains not added and cannot be mistaken for a battle',()=>{
  const target=backlog.regions.HOENN.trainers.find(t=>t.id==='hoenn-route103-rival');
  assert.ok(target);
  assert.equal(target.status,'not_added');
  assert.equal(target.native_absence_confirmed,false);
  assert.match(target.notes,/não existe evento de batalha/);
  assert.match(pendingPage(backlog,'HOENN',registry),/Brendan\/May — primeira batalha/);
});
test('binding loader rejects unsupported schema and can load a private fixture',async()=>{
  const first=await loadTrainerBindings(async uri=>({
    ok:uri==='/data/trainer-event-bindings-phase1.json',
    json:async()=>registry
  }));
  assert.equal(first.records.length,13);
});
