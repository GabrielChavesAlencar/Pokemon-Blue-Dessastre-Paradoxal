import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {extractSprites} from '../scripts/extract-sprites.mjs';
import {extractExtras} from '../scripts/extract-extras.mjs';
import {filterSpecies,generationName,art,pokemonPath} from '../src/assets/utils.js';
import {pokemonDetail} from '../src/assets/detail.js';
const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const catalog=JSON.parse(await readFile(path.join(site,'public/data/catalog.json'),'utf8'));
const details=JSON.parse(await readFile(path.join(site,'public/data/details.json'),'utf8'));
const all=[...catalog.species,...catalog.customForms];
const model={catalog,locations:[],byId:new Map(all.map(p=>[p.id,p]))};
const state={generation:'dessastre-paradoxal',group:'all',q:'',sort:'number',moveKind:'level',moveQ:'',moveLimit:40,form:''};
test('descrições e medidas aprovadas, renomes e cries são publicados sem inventar dados pendentes',async()=>{
  const approved=JSON.parse(await readFile(path.join(site,'public/data/pokedex-approved.json'),'utf8')).species;
  for(const [id,value] of Object.entries(approved)){
    const entry=model.byId.get(id);assert.equal(entry.description,value.description);assert.equal(entry.height,value.height);assert.equal(entry.weight,value.weight);
  }
  assert.equal(model.byId.get('PRIMALNOTIC').name,'Witchcap Haze');
  assert.equal(model.byId.get('PRIMALMUK').name,'Tar Chasm');
  assert.equal(model.byId.get('PRIMALNOTIC').pending,true);
  const cave=model.byId.get('CAVEFANG');assert.ok(pokemonDetail(model,cave,details,state,new Set()).includes('<audio controls'));
  const form=catalog.customForms.find(p=>p.base==='ARBOK');
  assert.ok(pokemonDetail(model,model.byId.get('ARBOK'),details,{...state,form:String(form.form)},new Set()).includes('mega-stone-art'));
});
test('pacote de cries e pedras extrai 60 arquivos autorais verificados',async()=>{
  const temp=await mkdtemp(path.join(tmpdir(),'blue-fan-extras-'));
  try{assert.equal(await extractExtras(site,temp),60);const wav=await readFile(path.join(temp,'assets/fan-extras/cries/CAVEFANG.wav'));assert.equal(wav.toString('ascii',0,4),'RIFF');}finally{await rm(temp,{recursive:true,force:true});}
});
test('geração com nome contém 59 espécies e 12 formas mega, sem alterar as oficiais',()=>{
  const result=filterSpecies(all,state);assert.equal(result.length,71);assert.equal(result.filter(p=>p.base).length,12);
  assert.equal(catalog.species.find(p=>p.id==='MIRAIDON').number,1008);assert.ok(result.every(p=>generationName(p)==='Dessastre Paradoxal'));
  const form=result.find(p=>p.base==='ARBOK');assert.equal(pokemonPath(form),'/pokedex/ARBOK?forma='+form.form);assert.ok(art(form).startsWith('/assets/fan-pokemon/'));
});
test('cadastros pendentes mostram ???? e suas fichas não inventam atributos',()=>{
  const pending=catalog.species.filter(p=>p.pending);assert.equal(pending.length,7);
  for(const p of pending){assert.deepEqual(p.stats,[null,null,null,null,null,null]);const html=pokemonDetail(model,p,details,state,new Set());assert.ok(html.includes('indisponível em batalhas'));assert.ok(html.includes('????'));assert.ok(!html.includes('null no total'));}
});
test('Megas usam sprites, tipos, habilidade e geração da forma selecionada',()=>{
  const form=catalog.customForms.find(p=>p.base==='ARBOK');const base=model.byId.get('ARBOK');
  const html=pokemonDetail(model,base,details,{...state,form:String(form.form)},new Set());
  assert.ok(html.includes(form.art));assert.ok(html.includes('Dessastre Paradoxal'));assert.ok(html.includes('Multiscale'));assert.ok(html.includes('Dragão'));assert.ok(html.includes('Arbokita DP'));
});
test('pacote de sprites é extraído com checksum e nomes controlados',async()=>{
  const temp=await mkdtemp(path.join(tmpdir(),'blue-fan-assets-'));
  try{assert.equal(await extractSprites(site,temp),491);const data=await readFile(path.join(temp,'assets/fan-pokemon/CAVEFANG/front.png'));assert.equal(data.toString('hex',0,8),'89504e470d0a1a0a');assert.equal(data.readUInt32BE(16),128);}finally{await rm(temp,{recursive:true,force:true});}
});
