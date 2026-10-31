import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {mergeHistory,generate,generatedPrefix} from '../scripts/changelog.mjs';
import {esc,normalize,groupSlots,filterSpecies} from '../src/assets/utils.js';
import {effectiveDetail} from '../src/assets/data.js';

const site=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(readFileSync(path.join(site,'public/data',name+'.json'),'utf8'));
const catalog=read('catalog'), details=read('details'), locations=read('locations');
const ids=new Set(catalog.species.map(p=>p.id));
const stamp='2026-10-31T12:00:00Z';
const commit=(n,title,date=stamp)=>({sha:n.repeat(40),title,date});

test('histórico mescla, ordena e deduplica sem publicar commits do robô',()=>{
  const result=mergeHistory([commit('a','docs: guia')],[commit('a','docs: guia'),commit('b','fix: encontro','2026-11-01T12:00:00Z'),commit('c',generatedPrefix),{sha:'bad',title:'inválido',date:stamp}]);
  assert.equal(result.length,2);assert.equal(result[0].sha,'b'.repeat(40));assert.equal(result[0].category,'Correções');assert.equal(result[1].category,'Documentação');
});
test('checkout raso preserva o histórico e adiciona metadados do commit Vercel',()=>{
  const temp=mkdtempSync(path.join(tmpdir(),'blue-history-'));
  try{
    const seed=path.join(temp,'updates.json');writeFileSync(seed,JSON.stringify({commits:[commit('a','feat: primeiro')]}));
    const result=generate({cwd:temp,seedPath:seed,env:{VERCEL_GIT_COMMIT_SHA:'d'.repeat(40),VERCEL_GIT_COMMIT_MESSAGE:'fix: atual\ncorpo'}});
    assert.equal(result.commits.length,2);assert.ok(result.commits.some(x=>x.title==='fix: atual'));
  }finally{rmSync(temp,{recursive:true,force:true});}
});
test('git real acrescenta mudanças fora da pasta do site',()=>{
  const temp=mkdtempSync(path.join(tmpdir(),'blue-git-'));
  const git=args=>execFileSync('git',args,{cwd:temp,stdio:['ignore','pipe','pipe'],env:{...process.env,GIT_AUTHOR_NAME:'Teste',GIT_AUTHOR_EMAIL:'test@example.invalid',GIT_COMMITTER_NAME:'Teste',GIT_COMMITTER_EMAIL:'test@example.invalid'}});
  try{
    git(['init']);writeFileSync(path.join(temp,'README.md'),'Projeto');git(['add','README.md']);git(['commit','-m','feat: campanha']);
    const result=generate({cwd:temp,seedPath:path.join(temp,'missing.json'),env:{}});assert.equal(result.commits.length,1);assert.equal(result.commits[0].title,'feat: campanha');
  }finally{rmSync(temp,{recursive:true,force:true});}
});
test('Pokédex tem espécies únicas, atributos válidos e detalhes para cada ficha',()=>{
  assert.equal(ids.size,catalog.species.length);assert.equal(catalog.species.length,catalog.counts.species);
  for(const p of catalog.species){assert.ok(details.species[p.id],p.id);assert.equal(p.stats.length,6);assert.ok(p.pending?p.stats.every(x=>x===null):p.stats.every(x=>Number.isInteger(x)&&x>0));assert.ok(p.number>0);}
  assert.equal(catalog.species.find(p=>p.id==='MIRAIDON').number,1008);
});
test('golpes, evoluções e formas apontam para registros existentes',()=>{
  for(const [id,p] of Object.entries(details.species)){
    for(const [level,move] of p.moves){assert.ok(level>=-1&&level<=100,id);assert.ok(details.moves[move],`${id}: ${move}`);}
    for(const move of [...p.tutor,...p.egg])assert.ok(details.moves[move],`${id}: ${move}`);
    for(const [target] of p.evolutions)assert.ok(ids.has(target),`${id}: ${target}`);
    if(p.base)assert.ok(ids.has(p.base),p.base);
  }
});
test('locais contêm encontros válidos com pesos e níveis positivos',()=>{
  assert.equal(locations.locations.length,catalog.counts.locations);
  for(const area of locations.locations)for(const version of area.versions)for(const method of version.methods){
    assert.ok(method.slots.length);
    for(const [id,min,max,weight] of method.slots){assert.ok(ids.has(id)||catalog.encounterForms[id],id);assert.ok(min>=1&&max>=min&&weight>0);}
    assert.ok(Math.abs(groupSlots(method).reduce((sum,row)=>sum+row.chance,0)-100)<0.00001);
  }
});
test('formas herdam golpes ausentes e respeitam campos explicitamente vazios',()=>{
  const base={id:'BASE',types:['FIRE'],stats:[1,2,3,4,5,6]};
  const data={species:{BASE:{abilities:['A'],hidden:['B'],moves:[[0,'MOVE']],tutor:['MOVE'],egg:[],evolutions:[]}}};
  const form={own:['HiddenAbilities'],hidden:[],types:[],stats:[]};
  const result=effectiveDetail(base,form,data);assert.deepEqual(result.moves,[[0,'MOVE']]);assert.deepEqual(result.hidden,[]);assert.deepEqual(result.types,['FIRE']);
});
test('filtros combinam busca, tipo, geração e favoritos',()=>{
  const state={q:'Miraidon',type:'DRAGON',generation:'9',group:'favorites'};
  assert.equal(filterSpecies(catalog.species,state,new Set(['MIRAIDON'])).length,1);
  assert.equal(filterSpecies(catalog.species,{...state,type:'FIRE'},new Set(['MIRAIDON'])).length,0);
  assert.equal(normalize('  Elétrico  '),'eletrico');assert.equal(esc('<script>"'), '&lt;script&gt;&quot;');
});
test('guias têm links internos resolvíveis e histórico contém commits reais',()=>{
  const guides=read('guides').guides;assert.ok(guides.length>=5);assert.equal(new Set(guides.map(g=>g.id)).size,guides.length);
  assert.ok(read('updates').commits.every(x=>/^[a-f0-9]{40}$/.test(x.sha)));
});
