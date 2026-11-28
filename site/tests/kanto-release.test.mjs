import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {kantoIndex,kantoLocation,kantoTrainer,KANTO_GYM_REWARDS} from '../src/assets/kanto.js';
import {KANTO_DIFFICULTY,KANTO_EVOLUTION,KANTO_WILD_CHANCE,kantoBalanceNote} from '../src/assets/kanto-balance.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=name=>JSON.parse(readFileSync(path.join(root,'public','data',name+'.json'),'utf8'));
const kanto=data('kanto'),catalog=data('catalog'),details=data('details');
const model={byId:new Map(catalog.species.map(p=>[p.id,p]))};
const loc=id=>kanto.locations.find(v=>v.id===id);

test('Kanto prototype states are explicit and the route 23 exception stays visible',()=>{
  assert.equal(kanto.locations.length,165);
  assert.equal(kanto.trainers.length,202);
  assert.equal(kanto.locations.filter(x=>x.status==='preview').length,35);
  assert.equal(kanto.locations.filter(x=>x.status==='encounter_review').length,1);
  assert.equal(kanto.locations.filter(x=>x.status==='experimental').length,129);
  assert.ok(kanto.locations.filter(x=>x.status==='preview').every(x=>!x.methods.length&&!x.trainers.length));
  const route23=kantoLocation(model,kanto,loc('kanto-route-23'));
  assert.match(route23,/Encontros temporariamente suspensos/);
  assert.match(route23,/método duplicado/);
  const preview=kanto.locations.find(x=>x.status==='preview');
  assert.match(kantoLocation(model,kanto,preview),/Somente cenário/);
  assert.match(kantoIndex(model,kanto,'localizacoes'),/165 locais e 202 treinadores/);
  assert.doesNotMatch(route23,/Trecho de Pallet Town a Pewter City/);
});
test('Rota 11 e a Caverna dos Diglett mantêm os encontros e os treinadores verificados',()=>{
  const route=loc('kanto-route-11'), tunnel=loc('kanto-diglett-tunnel');
  assert.equal(route.status,'experimental');
  assert.equal(route.methods.length,6);
  assert.equal(route.trainers.length,10);
  assert.equal(new Set(route.trainers).size,10);
  assert.ok(route.trainers.every(id=>kanto.trainers.some(t=>t.id===id&&t.location===route.id)));
  assert.equal(tunnel.status,'experimental');
  assert.equal(tunnel.methods.length,2);
  for(const method of tunnel.methods){
    assert.deepEqual(method.slots.map(s=>[s.species,s.chance]),[['DIGLETT',95],['DUGTRIO',5]]);
  }
  for(const id of ['route-2','route-11']){
    const entrance=loc('kanto-diglett-entrance-'+id);
    assert.equal(entrance.status,'experimental');
    assert.deepEqual(entrance.methods,[]);
  }
});
test('seis interiores de Cerulean e Grunt 6 são explícitos sem alterar as prévias',()=>{
  for(const id of ['bike-shop','house-a','house-b','house-c','house-d','ransacked-house']){
    const interior=loc('kanto-cerulean-'+id);
    assert.ok(interior,id);
    assert.equal(interior.status,'experimental');
    assert.deepEqual(interior.methods,[]);
  }
  const grunt=kanto.trainers.find(t=>t.id==='kanto-rocket-cerulean-house');
  assert.ok(grunt);
  assert.equal(grunt.location,'kanto-cerulean-city');
  assert.deepEqual(grunt.variants[0].team.map(p=>[p.species,p.level]),[['MACHOP',17],['DROWZEE',17]]);
  assert.equal(loc('kanto-cerulean-city').trainers.filter(id=>id===grunt.id).length,1);
});
test('rival do navio tem identidade própria e três variantes originais',()=>{
  const rival=kanto.trainers.find(t=>t.id==='kanto-blue-ss-anne');
  assert.ok(rival);
  assert.equal(rival.location,'kanto-ss-anne-2f');
  assert.equal(rival.leader,false);
  assert.equal(loc(rival.location).trainers.filter(id=>id===rival.id).length,1);
  assert.deepEqual(rival.variants.map(v=>[v.starter,v.team.map(p=>[p.species,p.level])]),[
    ['BULBASAUR',[['PIDGEOTTO',19],['RATICATE',16],['KADABRA',18],['CHARMELEON',20]]],
    ['CHARMANDER',[['PIDGEOTTO',19],['RATICATE',16],['KADABRA',18],['WARTORTLE',20]]],
    ['SQUIRTLE',[['PIDGEOTTO',19],['RATICATE',16],['KADABRA',18],['IVYSAUR',20]]]
  ]);
});
test('creche original está catalogada sem declarar aceite físico',()=>{
  const daycare=loc('kanto-day-care');
  assert.ok(daycare);
  assert.equal(daycare.status,'experimental');
  assert.deepEqual(daycare.methods,[]);
  assert.deepEqual(daycare.trainers,[]);
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

test('painel de Kanto documenta todas as faixas e os três métodos selvagens recentes',()=>{
  assert.deepEqual(KANTO_DIFFICULTY.map(x=>x.percent),[70,70,70,90]);
  assert.deepEqual(KANTO_DIFFICULTY.map(x=>x.bst),['350','450','540','Sem teto']);
  assert.deepEqual(KANTO_EVOLUTION.map(x=>x.gate),['Nível natural + 5','Progresso 30','Progresso 40','Progresso 45']);
  assert.deepEqual(KANTO_WILD_CHANCE.map(x=>x.chance),['0%','15%','30%','45%','60%']);
  const html=kantoIndex(model,kanto,'balanceamento');
  for(const sample of ['Rattata','Raticate','Raichu','Alakazam','Crobat','Brock','Misty','Lorelei','Agatha','Lance','Blue','Full Power','45%','90%']){
    assert.match(html,new RegExp(sample),sample);
  }
  assert.match(html,/dez Ligas/);
  assert.match(html,/primeiro confronto/);
  assert.match(html,/regiao=kanto/);
  assert.doesNotMatch(html,/Selecionar região/,'não oferecer região de balanceamento que ainda não existe');
});
test('rotas e fichas distinguem nível do PBS, taxa original do slot e evolução dinâmica',()=>{
  const route=kantoLocation(model,kanto,loc('kanto-route-1'));
  assert.match(route,/Faixa do PBS/);
  assert.match(route,/Chance do slot/);
  assert.match(route,/chance interna começa em 15%/);
  const trainer=kanto.trainers.find(t=>!t.leader&&t.role!=='Rival');
  assert.ok(trainer);
  const normal=kantoTrainer(model,kanto,trainer,details);
  assert.match(normal,/Treinadores comuns/);
  assert.match(normal,/Nível dinâmico/);
  const boss=kantoTrainer(model,kanto,kanto.trainers.find(t=>t.name==='Brock'),details);
  assert.match(boss,/Primeiro desafio de ginásio/);
  assert.match(boss,/sem reduzir BST nem potência/);
  assert.doesNotMatch(boss,/Nível PBS:/);
  const rival=kantoTrainer(model,kanto,kanto.trainers.find(t=>t.role==='Rival'),details);
  assert.match(rival,/Rivais e chefes de história/);
  assert.doesNotMatch(rival,/Primeiro desafio de ginásio/);
  assert.match(kantoBalanceNote('league'),/Elite Four e campeão/);
});

test('Rock Tunnel mantém duas rotas, um Centro e dois andares sem antecipar Lavender',()=>{
  const ids=['route-9','route-10','rock-tunnel-center','rock-tunnel-1f','rock-tunnel-b1f'];
  const locations=ids.map(id=>loc('kanto-'+id));
  for(const row of locations)assert.equal(row.status,'experimental');
  assert.deepEqual(locations.map(row=>row.methods.length),[2,6,0,2,2]);
  assert.deepEqual(locations.map(row=>row.trainers.length),[9,6,0,7,7]);
  const allen=kanto.trainers.filter(t=>t.name==='Allen'&&t.location==='kanto-rock-tunnel-b1f');
  assert.equal(allen.length,1);
  assert.equal(allen[0].variants.length,1);
  assert.equal(loc('kanto-lavender-town'),undefined);
});
