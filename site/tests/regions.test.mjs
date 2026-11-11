import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import {regionsPage} from '../src/assets/regions.js';

test('the regional guide separates live areas from the Kanto preview', async () => {
  const registry=JSON.parse(await readFile(new URL('../public/data/regions.json',import.meta.url),'utf8'));
  const page=regionsPage(registry);
  assert.equal((page.match(/class="panel region-entry"/g)??[]).length,11);
  assert.equal((page.match(/>Jogável</g)??[]).length,1);
  assert.match(page,/Piloto em preparação<\/span><h2>Kanto<\/h2>/);
  assert.match(page,/Pallet Town.*Ginásio de Pewter/);
  assert.match(page,/Expedição sem Liga/);
  assert.match(page,/href="\/localizacoes">Ver mapa e encontros/);
});
