import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {kantoIndex,kantoLocation,kantoTrainer,KANTO_GYM_REWARDS} from '../src/assets/kanto.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=name=>JSON.parse(readFileSync(path.join(root,'public','data',name+'.json'),'utf8'));
const kanto=data('kanto'),catalog=data('catalog'),details=data('details');
const model={byId:new Map(catalog.species.map(p=>[p.id,p]))};
const loc=id=>kanto.locations.find(v=>v.id===id);

test('Kanto prototype states are explicit and Route 23 shows the five audited methods',()=>{
  assert.equal(kanto.locations.length,142);
  assert.equal(kanto.trainers.length,144);
  assert.equal(kanto.locations.filter(x=>x.status==='preview').length,45);
  assert.equal(kanto.locations.filter(x=>x.status==='experimental').length,97);
  assert.ok(kanto.locations.filter(x=>x.status==='preview').every(x=>!x.methods.length&&!x.trainers.length));
  const route23=kantoLocation(model,kanto,loc('kanto-route-23'));
  assert.deepEqual(loc('kanto-route-23').methods.map(x=>x.id),['LandDay','Water','OldRod','GoodRod','SuperRod']);
  assert.match(route23,/<h2>Encontros<\/h2>/);
  const preview=kanto.locations.find(x=>x.status==='preview');
  assert.match(kantoLocation(model,kanto,preview),/Somente cenário/);
  assert.match(kantoIndex(model,kanto,'localizacoes'),/142 locais e 144 treinadores/);
  assert.doesNotMatch(route23,/Trecho de Pallet Town a Pewter City/);
});
test('cada líder exibe sua INSÍGNIA própria e nenhum treinador comum recebe Boulder',()=>{
  const leaders=kanto.trainers.filter(t=>t.leader);
  assert.equal(leaders.length,8);
  assert.deepEqual(new Set(leaders.map(t=>t.name)),new Set(Object.keys(KANTO_GYM_REWARDS)));
  for(const boss of leaders){
    const view=kantoTrainer(model,kanto,boss,details);
    assert.match(view,new RegExp('Recompensa: '+KANTO_GYM_REWARDS[boss.name]+' Badge'));
  }
  const normal=kanto.trainers.find(t=>!t.leader);
  assert.doesNotMatch(kantoTrainer(model,kanto,normal,details),/Recompensa: .* Badge/);
});
test('cavernas distinguem encontros diurnos e noturnos, nunca marcam Kanto como finalizada',()=>{
  const mansion=kantoLocation(model,kanto,loc('kanto-mansion-1f'));
  assert.match(mansion,/Caverna durante o dia/);
  assert.match(mansion,/Caverna à noite/);
  assert.match(mansion,/QA manual Windows\/JoiPlay/);
  assert.doesNotMatch(mansion,/100% jogável/);
});
