import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {changes,changesPage} from '../src/assets/changes.js';

test('comparação prioriza progressão e separa os dois lados em duas colunas',()=>{
  assert.equal(changes[0].id,'progressao');
  assert.equal(new Set(changes.map(x=>x.id)).size,changes.length);
  assert.ok(changes.length>=25);
  changes.forEach((row,i)=>{assert.equal(row.priority,i+1);assert.ok(row.base.length>30);assert.ok(row.blue.length>60);});
  const html=changesPage();
  assert.equal((html.match(/scope="col"/g)||[]).length,2);
  assert.equal((html.match(/scope="row"/g)||[]).length,changes.length);
  for(const row of changes)assert.ok(html.includes(`change-${row.id}`));
  assert.ok(html.includes('Pokémon Decades'));assert.ok(html.includes('Dessastre Paradoxal'));
  assert.ok(html.includes('online permanece experimental'));
});

test('a comparação está na navegação e tem rota própria',()=>{
  const html=readFileSync(new URL('../src/index.html',import.meta.url),'utf8');
  const app=readFileSync(new URL('../src/assets/app.js',import.meta.url),'utf8');
  assert.match(html,/href="\/o-que-mudou" data-nav="o-que-mudou"/);
  assert.match(app,/route==='o-que-mudou'/);assert.match(app,/changesPage\(\)/);
});
