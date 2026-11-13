import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {leagueIndex,leagueDetail} from '../src/assets/league.js';
const read=p=>readFileSync(new URL(p,import.meta.url),'utf8');
const db=JSON.parse(read('../public/data/strongest-teams.json'));
const catalog=JSON.parse(read('../public/data/catalog.json'));
const model={byId:new Map(catalog.species.map(p=>[p.id,p]))};
test('listas documentais corretas sem níveis fixos',()=>{
  assert.equal(db.schema,1);
  assert.equal(db.teams.filter(t=>t.region==='KANTO'&&t.role==='gym').length,10);
  assert.equal(db.teams.filter(t=>t.region==='KANTO'&&t.role==='elite').length,4);
  assert.equal(db.teams.filter(t=>t.region==='JOHTO'&&t.role==='elite').length,4);
  assert.equal(db.teams.find(t=>t.id==='kanto-blue-champion').variants.length,3);
  assert.equal(db.teams.find(t=>t.id==='kanto-trace-champion').variants.length,2);
  const md=read('../../docs/ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md');
  for(const t of db.teams){
    assert.ok(md.includes('### '+t.studySection+' '),t.id);
    for(const v of t.variants){assert.ok(v.species.length>=5&&v.species.length<=6,t.id);assert.ok(!('level' in v),t.id);}
  }
});
test('fichas de Liga mostram espécies e regra de nível sem valor fixo',()=>{
  assert.match(leagueIndex(model,db,'KANTO'),/Elite Four/);
  assert.match(leagueIndex(model,db,'JOHTO'),/Will/);
  const blue=db.teams.find(t=>t.id==='kanto-blue-champion');
  const html=leagueDetail(model,db,blue,{});
  assert.match(html,/Jogador escolheu Bulbasaur/);
  assert.match(html,/Nível dinâmico/);
  assert.doesNotMatch(html,/Nível PBS:|Nível previsto:/);
});
