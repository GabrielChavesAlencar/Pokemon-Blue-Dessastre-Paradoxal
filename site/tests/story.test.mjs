import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {regionImage,regionCaption,storyIndex,bossesIndex,trainerDetail,allTrainers} from '../src/assets/story.js';
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

test('as localizações com coordenadas mostram recortes DIFERENTES em vez do mapa inteiro repetido',()=>{
  const a=regionImage(model,{id:5,name:'Route 1'},false);
  const b=regionImage(model,{id:21,name:'Route 2'},false);
  assert.match(a,/region-map--focused/);
  assert.match(a,/region-map-crop/);
  assert.ok(a.includes('scale(2.15)'));
  assert.notEqual(a,b);
  assert.ok(regionCaption(model,{id:5,name:'Route 1'}).includes('Recorte ampliado'));
});
test('miniatura específica de Lappet Town tem prioridade sobre qualquer fallback',()=>{
  const html=regionImage(model,{id:2,name:'Lappet Town'},false);
  assert.match(html,/mapLappetTown.png/);
  assert.match(html,/region-map--local/);
  assert.ok(!html.includes('mapRegion0.png'));
  assert.ok(regionCaption(model,{id:2,name:'Lappet Town'}).includes('Miniatura específica'));
});
test('Rock Cave 1F sem imagem comprovada não exibe a mesma Beatha inteira',()=>{
  const html=regionImage(model,{id:49,name:'Rock Cave 1F'},false);
  assert.match(html,/Mapa individual não encontrado/);
  assert.match(html,/region-map--missing/);
  assert.ok(!html.includes('mapRegion0.png'));
  assert.ok(!html.includes('region-marker'));
  assert.ok(regionCaption(model,{id:49,name:'Rock Cave 1F'}).includes('Nenhuma imagem'));
});
test('a maioria dos locais com dados na base pode ser focada e os sem coordenadas são explícitos',()=>{
  const rendered=locations.locations.map(area=>regionImage(model,area,true));
  const focused=rendered.filter(html=>html.includes('region-map--focused')).length;
  assert.ok(focused>=130,'esperava dezenas de recortes regionais distintos, obteve '+focused);
  assert.equal(rendered.length,locations.locations.length);
  assert.ok(rendered.every(html=>html.includes('region-map--')));
});
