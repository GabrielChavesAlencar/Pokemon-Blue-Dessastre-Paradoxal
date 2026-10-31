import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateGuides} from '../scripts/guides.mjs';
const dir=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(readFileSync(path.join(dir,'public/data',name+'.json'),'utf8'));
const input={catalog:read('catalog'),locations:read('locations'),details:read('details'),editorial:read('guides')};
test('guias herdados do Decades têm fontes e são separados dos dados do Blue',()=>{
  const guides=generateGuides(input).guides;
  assert.equal(new Set(guides.map(g=>g.id)).size,guides.length);
  assert.ok(guides.find(g=>g.id==='decades-beatha').sources.some(s=>s.url.includes('pokecommunity.com')));
  assert.equal(guides.find(g=>g.id==='blue-mapa-encontros').synced,true);
  assert.ok(guides.find(g=>g.id==='dessastre-paradoxal').synced);
});
test('mudanças no catálogo e encontros recalculam guias',()=>{
  const before=generateGuides(input);
  const changed=structuredClone(input);
  changed.catalog.species.push({...changed.catalog.species[0],id:'TEST_GUIDE',generation:'dessastre-paradoxal',pending:true});
  changed.locations.locations.push({...changed.locations.locations[0],id:999999,name:'Área do teste'});
  const after=generateGuides(changed);
  const content=(obj,id)=>obj.guides.find(g=>g.id===id).sections.map(s=>s.paragraphs.join(' ')).join(' ');
  assert.notEqual(content(before,'blue-pokedex-atual'),content(after,'blue-pokedex-atual'));
  assert.notEqual(content(before,'blue-mapa-encontros'),content(after,'blue-mapa-encontros'));
  assert.ok(after.guides.find(g=>g.id==='blue-mapa-encontros').sections.some(s=>s.links?.some(l=>l.href==='/localizacoes/999999')));
});
test('dados incompletos não geram guias potencialmente incorretos',()=>assert.throws(()=>generateGuides({catalog:{},locations:{},details:{},editorial:{}}),/incompleta/));
