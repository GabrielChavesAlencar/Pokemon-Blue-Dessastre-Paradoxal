import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {regionImage,regionCaption,storyIndex,bossesIndex,trainerDetail,allTrainers} from '../src/assets/story.js';
import {activeLocations} from '../src/assets/data.js';
import {createHash} from 'node:crypto';
const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const load=f=>JSON.parse(readFileSync(path.join(site,'public/data',f+'.json'),'utf8'));
const source=load('story-trainers'),region=load('region-points'),catalog=load('catalog'),locations=load('locations'),details=load('details');
const model={story:source,region,catalog,locations:activeLocations(locations.locations,region),byId:new Map(catalog.species.map(x=>[x.id,x]))};
test('importa 18 mestres reais e quatro dificuldades Full Doubles da engine Blue',()=>{
  assert.equal(source.masters.length,18);
  assert.equal(source.masters.filter(t=>t.campaignVariants.length===4).length,18);
  assert.equal(new Set(source.masters.map(t=>t.type)).size,18);
  for(const trainer of source.masters){
    assert.deepEqual(trainer.campaignVariants.map(v=>v.id),['beginner','intermediate','advanced','master']);
    for(const v of trainer.campaignVariants){
      assert.equal(v.team.length,6);assert.equal(v.origin,'blue-engine');assert.equal(v.format,'Full Doubles');
      for(const p of v.team){assert.ok(p.species);assert.ok(p.movesByLevel.length);assert.equal(p.movesByLevel[0].level,1);}
    }
  }
  assert.ok(source.bosses.find(t=>t.id==='zenith'));
});
test('áreas utilizam mapa regional oficial com marcador quando existem coordenadas',()=>{
  const area={name:'Route 1'};
  const html=regionImage(model,area,true);
  assert.match(html,/mapRegion0.png/);
  assert.match(html,/region-marker/);
  assert.match(html,/mapa regional/i);
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
  const t=source.masters[0], v=t.campaignVariants.find(x=>x.id==='master');
  const html=trainerDetail(model,t,v.id,details);
  assert.match(html,/Full Doubles/);
  assert.doesNotMatch(html,/1v1 Full Power|Basic Power|3v3/);
  for(const p of v.team)assert.ok(html.toLowerCase().includes(p.species.toLowerCase().replaceAll('_',' '))||model.byId.has(p.species),p.species);
  assert.match(html,/engine instalada do Blue/);
});

test('nível do jogador recalcula o nível dos líderes e os golpes da engine',()=>{
  const t=source.masters[0];
  for(const v of t.campaignVariants){
    for(const highest of [1,30,50,100]){
      const level=Math.max(1,Math.floor(highest*v.levelPercent/100));
      const html=trainerDetail(model,t,v.id,details,highest);
      assert.match(html,new RegExp('líderes no nível '+level+'\\.'));
      assert.match(html,new RegExp('Nível previsto: '+level));
      for(const p of v.team){
        const moves=p.movesByLevel.filter(row=>row.level<=level).at(-1).moves;
        for(const id of moves)assert.ok(html.includes(details.moves[id]?.name??''),id);
      }
    }
  }
  const fallback=trainerDetail(model,t,'1v1-basic-power',details);
  assert.doesNotMatch(fallback,/Basic Power/);
  assert.match(fallback,/90%/);
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
test('os 137 mapas atuais têm captura nativa própria e os 18 antigos ficam ocultos',()=>{
  assert.equal(model.locations.length,137);
  assert.equal(region.inactiveAreaIds.length,18);
  assert.equal(locations.locations.length,155,'registros brutos antigos permanecem preservados');
  for(const area of model.locations){
    const capture=region.areaImages[String(area.id)];
    assert.equal(capture.kind,'habitat-region-capture');
    assert.equal(capture.src,'/assets/route-maps/route-'+area.id+'.png');
    const raw=readFileSync(path.join(site,'public',capture.src));
    assert.equal(raw.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
    assert.equal(raw.readUInt32BE(16),480);assert.equal(raw.readUInt32BE(20),274);
    assert.equal(createHash('sha256').update(raw).digest('hex'),capture.sha256);
    const html=regionImage(model,area,true);
    assert.match(html,/region-map--capture/);assert.ok(html.includes(capture.src));
    assert.ok(!html.includes('raw.githubusercontent.com'));
    assert.match(regionCaption(model,area),/Captura local.*3×/);
    assert.ok(!region.inactiveAreaIds.includes(area.id));
  }
  assert.ok(model.locations.some(a=>a.id===86&&a.name==='Route 1'));
  assert.ok(!model.locations.some(a=>a.id===5));
});
test('filtro de mapas não modifica a entrada nem depende de IDs presumidos',()=>{
  const areas=[{id:1},{id:2}];
  assert.deepEqual(activeLocations(areas,{inactiveAreaIds:[1]}),[{id:2}]);
  assert.deepEqual(areas,[{id:1},{id:2}]);assert.deepEqual(activeLocations(areas,{}),areas);
});
