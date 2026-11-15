import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {presentationPage} from '../src/assets/presentation.js';

const dir=path.dirname(fileURLToPath(import.meta.url));
const readSource=async name=>readFile(path.join(dir,'../src',name),'utf8');

test('Apresentação aparece entre Início e Downloads na navegação principal',async()=>{
  const html=await readSource('index.html');
  const home=html.indexOf('data-nav="home"');
  const about=html.indexOf('data-nav="apresentacao"');
  const downloads=html.indexOf('data-nav="downloads"');
  assert.ok(home>=0&&about>home&&downloads>about);
  assert.match(html,/href="\/assets\/presentation\.css"/);
});

test('SPA carrega a rota de apresentação com título próprio',async()=>{
  const app=await readSource('assets/app.js');
  assert.match(app,/from '\.\/presentation\.js'/);
  assert.match(app,/route==='apresentacao'/);
  assert.match(app,/presentationPage\(model\)/);
  assert.match(app,/setPage\('Apresentação'\)/);
});

test('Apresentação tem hero, conteúdo editorial, galeria e navegação de downloads',()=>{
  const ids=['MIRAIDON','GREATTUSK','SCREAMTAIL','IRONVALIANT','ROARINGMOON'];
  const byId=new Map(ids.map((id,i)=>[id,{
    id,name:id,number:1008+i,sprites:{front:'/assets/test-'+id+'.png'},sprite:'/assets/test-'+id+'.png'
  }]));
  const html=presentationPage({byId});
  assert.match(html,/id="presentation-title"/);
  assert.match(html,/id="conheca-o-blue"/);
  assert.match(html,/class="presentation-gallery"/);
  assert.match(html,/href="\/downloads"/);
  assert.match(html,/href="\/atualizacoes"/);
  assert.match(html,/href="\/pokedex\?grupo=paradox"/);
  assert.match(html,/MIRAIDON|Miraidon/i);
  assert.match(html,/As imagens ilustram espécies da Pokédex/);
  assert.equal((html.match(/class="presentation-gallery-card"/g)||[]).length,4);
});

test('Página possui regras responsivas e movimento reduzido',async()=>{
  const css=await readSource('assets/presentation.css');
  assert.match(css,/@media\(max-width:760px\)/);
  assert.match(css,/@media\(max-width:450px\)/);
  assert.match(css,/prefers-reduced-motion:reduce/);
});
