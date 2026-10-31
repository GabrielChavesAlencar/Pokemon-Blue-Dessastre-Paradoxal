import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {regionImage,storyIndex,bossesIndex,trainerDetail,allTrainers} from '../src/assets/story.js';
const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const load=f=>JSON.parse(readFileSync(path.join(site,'public/data',f+'.json'),'utf8'));
const source=load('story-trainers'),region=load('region-points'),catalog=load('catalog'),locations=load('locations'),details=load('details');
const model={story:source,region,catalog,locations:locations.locations,byId:new Map(catalog.species.map(x=>[x.id,x]))};
test('importa 18 mestres de tipo reais e as seis variações do PBS do Decades',()=>{
  assert.equal(source.masters.length,18);
  assert.equal(source.masters.filter(t=>t.variants.length===6).length,18);
  assert.equal(new Set(source.masters.map(t=>t.type)).size,18);
  for(const trainer of source.masters){
    assert.ok(trainer.variants.some(v=>v.id==='1v1-basic-power'&&v.team.length===4),trainer.name);
    assert.ok(trainer.variants.some(v=>v.id==='1v1-full-power'&&v.team.length===6),trainer.name);
    for(const v of trainer.variants)for(const p of v.team){assert.ok(p.species);assert.ok(p.level>0);}
  }
  assert.ok(source.bosses.find(t=>t.id==='zenith'));
});
test('áreas utilizam mapa regional oficial com marcador quando existem coordenadas',()=>{
  const area={name:'Route 1'};
  const html=regionImage(model,area,true);
  assert.match(html,/mapRegion0.png/);
  assert.match(html,/region-marker/);
  assert.match(html,/Mapa regional/);
  assert.ok(!regionImage(model,{name:'Nome completamente novo'},false).includes('region-marker'));
});
test('guia e chefes usam as mesmas equipes do arquivo extraído',()=>{
  const guide=storyIndex(model),index=bossesIndex(model);
  assert.match(guide,/18 Mestres de Tipo/);
  assert.match(guide,/Zenith Domain/);
  assert.match(index,/Marigold/);
  assert.match(index,/Azure/);
  assert.equal(allTrainers(source).length,19);
});
test('ficha do mestre apresenta Pokémon e golpes da variante selecionada',()=>{
  const t=source.masters[0], v=t.variants.find(x=>x.id==='1v1-full-power');
  const html=trainerDetail(model,t,v.id,details);
  assert.match(html,/1v1 Full Power/);
  for(const p of v.team)assert.ok(html.toLowerCase().includes(p.species.toLowerCase().replaceAll('_',' '))||model.byId.has(p.species),p.species);
  assert.match(html,/Pokémon Decades/);
});
