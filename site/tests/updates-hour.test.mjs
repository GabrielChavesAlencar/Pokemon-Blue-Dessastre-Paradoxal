import test from 'node:test';
import assert from 'node:assert/strict';
import {date,time} from '../src/assets/utils.js';
import {updateRow,updates} from '../src/assets/views.js';

const entry={date:'2026-10-31T20:25:00Z',sha:'a'.repeat(40),title:'feat: guias do Blue',category:'Novidades'};
test('horário de Brasília utiliza instante do commit, não o fuso do navegador',()=>{
  assert.equal(time(entry.date),'17:25');
  assert.ok(date(entry.date).includes('2026'));
  assert.equal(time('2026-10-31T17:25:00-03:00'),'17:25');
});
test('cada atualização mostra data, hora, fuso e mantém link do commit',()=>{
  const html=updateRow(entry);
  assert.match(html,/17:25 · Brasília/);
  assert.match(html,/datetime="2026-10-31T20:25:00Z"/);
  assert.match(html,/commit\/aaaaaaaa/);
});
test('resumo de atualizações mostra hora e possui atalho dos guias',()=>{
  const html=updates({updates:[entry]},{category:'all',updateQ:'',updateLimit:24});
  assert.match(html,/às 17:25 · Brasília/);
  assert.match(html,/href="\/guias"/);
  assert.match(html,/Explorar os guias/);
});
