import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {mergeIronCatalog,mergeIronDetails} from '../src/assets/future-iron.js';
import {futureSprite} from '../src/assets/future-eevee.js';
import {pokemonCard} from '../src/assets/views.js';
import {pokemonDetail} from '../src/assets/detail.js';
import {filterSpecies} from '../src/assets/utils.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(readFileSync(path.join(root,'public/data',name+'.json'),'utf8'));
const manifest=read('future-iron');
const catalog=read('catalog');
const originalSpecies=catalog.species.length;
mergeIronCatalog(catalog,manifest);
mergeIronCatalog(catalog,manifest);
const details=read('details');
mergeIronDetails(details,manifest);
const model={catalog,locations:[],futureEevee:{forms:[]},byId:new Map(catalog.species.map(p=>[p.id,p]))};
const state={q:'',type:'',generation:'dessastre-paradoxal',group:'future',sort:'number',limit:40,moveKind:'level',moveQ:'',moveLimit:40,form:''};
test('sete novos Paradoxos ficam na Dex sem alterar as espécies base ou o jogo',()=>{
 assert.equal(manifest.forms.length,7);
 assert.equal(catalog.species.length,originalSpecies+7);
 assert.equal(catalog.counts.plannedFutureParadoxes,7);
 assert.ok(manifest.forms.every(f=>f.card.future&&f.card.inGame===false&&f.card.flags.includes('Paradox')));
 for(const {card,details:profile} of manifest.forms){
  assert.notEqual(card.id,card.baseSpecies);
  assert.equal(card.stats.reduce((a,b)=>a+b,0),570);
  assert.deepEqual(card.stats,profile.stats);
  assert.deepEqual(profile.abilities,['QUARKDRIVE']);
  assert.equal(profile.moves.length,17);
  assert.equal(profile.tm.length,15);
  assert.equal(profile.egg.length,0);
  assert.equal(profile.evolutions.length,0);
  assert.equal(profile.learnsetStatus,'design-proposal-only');
  assert.ok(card.description&&card.height>0&&card.weight>0);
  assert.ok(model.byId.has(card.baseSpecies));
 }
 assert.equal(filterSpecies(catalog.species,state).length,7);
});
test('sprite atlas real e todas as sete perspectivas são renderizados',()=>{
 const png=readFileSync(path.join(root,'public/assets/future-iron/sprites-atlas.png'));
 assert.equal(png.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
 assert.equal(png.readUInt32BE(16),896);
 assert.equal(png.readUInt32BE(20),896);
 assert.deepEqual(manifest.atlas.roleOrder,['front','front-shiny','back','back-shiny','icon','icon-shiny','footprint']);
 for(const {card} of manifest.forms){
  for(const role of manifest.atlas.roleOrder){
   const sprite=futureSprite(card,role);
   assert.match(sprite,/sprites-atlas.png/);
   assert.match(sprite,/background-size:700% 700%/);
  }
  assert.match(pokemonCard(card),/FUTURO NO JOGO/);
  const html=pokemonDetail(model,card,details,state,new Set());
  assert.match(html,/apenas na Pokédex do site/);
  assert.match(html,/570/);
  assert.match(html,/Conceito do Paradoxo futuro/);
  assert.match(html,/Sprites de/);
  assert.match(html,/Quark Drive|QUARKDRIVE/);
  assert.match(html,/sem alteração no instalador, PBS/);
 }
});
test('tipagens dos quatro Paradoxos revisados pelo autor e compatibilidade dos golpes',()=>{
 const accepted={
  IRONORACLE:{types:['PSYCHIC','ELECTRIC'],level:['THUNDERSHOCK','DISCHARGE','THUNDERBOLT'],tm:['ELECTRICTERRAIN']},
  IRONRAPTOR:{types:['ELECTRIC','FLYING'],level:['WILDCHARGE','BRAVEBIRD','SUPERCELLSLAM'],tm:['THUNDERPUNCH']},
  IRONSTINGER:{types:['BUG','ELECTRIC'],level:['BUGBUZZ','DISCHARGE','THUNDERBOLT'],tm:['VOLTSWITCH']},
  IRONGLIMMER:{types:['WATER','STEEL'],level:['SURF','FLASHCANNON','STEELBEAM'],tm:['IRONDEFENSE']},
 };
 for(const entry of manifest.forms){
  if(!accepted[entry.card.id]){
   assert.equal(entry.card.typeStatus,'proposed-in-study');
   continue;
  }
  const config=accepted[entry.card.id];
  assert.equal(entry.card.typeStatus,'approved-by-author');
  assert.equal(entry.details.typeStatus,'approved-by-author');
  assert.deepEqual(entry.card.types,config.types);
  assert.deepEqual(entry.details.types,config.types);
  assert.equal(entry.details.moves.length,17);
  assert.equal(entry.details.tm.length,15);
  assert.equal(new Set(entry.details.tm).size,15);
  assert.ok(entry.details.moves.every(([level],index,rows)=>index===0||level>=rows[index-1][0]));
  for(const move of config.level)assert.ok(entry.details.moves.some(row=>row[1]===move),entry.card.id+': '+move);
  for(const move of config.tm)assert.ok(entry.details.tm.includes(move),entry.card.id+': '+move);
  assert.deepEqual(entry.details.abilities,['QUARKDRIVE']);
  assert.equal(entry.card.stats.reduce((sum,value)=>sum+value,0),570);
  assert.equal(entry.card.inGame,false);
 }
 assert.ok(!manifest.forms.find(x=>x.card.id==='IRONGLIMMER').details.tm.includes('VOLTSWITCH'));
});
