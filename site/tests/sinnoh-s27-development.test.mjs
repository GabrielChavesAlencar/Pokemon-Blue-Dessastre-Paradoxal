// S27 — aceite da entrega de guias WEB (nao certifica mapas nativos).
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateSinnohGuide, sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {sinnohGuidePage} from '../src/assets/sinnoh-guide.js';
import {filterSinnohGuide, validateSinnohGuide} from '../src/assets/sinnoh-search.js';
import {regionsPage} from '../src/assets/regions.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sources=Object.fromEntries(Object.entries(sinnohSourcePaths)
  .map(([key,relative])=>[key,JSON.parse(readFileSync(path.join(root,relative),'utf8'))]));
const guide=generateSinnohGuide(sources);
const tabs=['visao','areas','treinadores','ginasios','liga','itens','progresso','pendencias'];

test('S27 usa apenas as fontes CH11–CH16 e mantem status nao jogavel',()=>{
  assert.equal(validateSinnohGuide(guide),guide);
  assert.equal(guide.region,'SINNOH');
  assert.equal(guide.status,'planned');
  assert.equal(guide.canPlay,false);
  assert.equal(guide.gameplayVerified,false);
  assert.equal(guide.counts.verifiedNativeMaps,0);
  assert.equal(guide.counts.verifiedNativeTrainers,0);
  assert.equal(guide.counts.verifiedNativeItems,0);
  assert.equal(guide.music.audioInstalled,false);
  assert.equal(guide.counts.areas,120);
  assert.equal(guide.counts.trainers,40);
  assert.equal(guide.counts.gyms,8);
  assert.equal(guide.counts.eliteFour,4);
  assert.equal(guide.counts.champions,1);
  assert.equal(guide.counts.hmItems,8);
  assert.equal(guide.counts.storySteps,22);
});

test('S27 as oito abas deixam clara a diferenca guia no portal e jogo instalado',()=>{
  for(const tab of tabs){
    const html=sinnohGuidePage(guide,tab);
    assert.match(html,/Guia disponível no portal/,tab);
    assert.match(html,/não está instalado como região jogável/,tab);
    assert.match(html,/Ainda não adicionado ao Game.exe\/JoiPlay/,tab);
    assert.match(html,/href="\/sinnoh\?aba=pendencias"/,tab);
    assert.match(html,/SINNOH · PLANEJADA · NÃO JOGÁVEL/,tab);
    assert.doesNotMatch(html,/Sinnoh instalado e jogável/,tab);
  }
});

test('S27 mapeia referencias documentais sem expor nivel, MapID ou encontro como jogavel',()=>{
  assert.equal(guide.areas.length,120);
  assert.equal(guide.trainers.length,40);
  assert.equal(guide.bosses.length,13);
  assert.equal(guide.items.length,8);
  assert.ok(guide.areas.every(a=>a.status==='planned'&&a.confirmedWildEncounters===0
    &&!('map_id' in a)&&!('level' in a)&&!('rate' in a)));
  assert.ok(guide.trainers.every(t=>t.status==='planned'&&!t.teamInstalled
    &&!('map_id' in t)&&!('level' in t)));
  assert.ok(guide.bosses.every(b=>b.status==='planned'&&!b.pbsInstalled
    &&!b.fullPowerVerified&&!('level' in b)));
  assert.ok(guide.items.every(i=>i.status==='planned'&&!i.pickupVerified&&i.regionalOnly));
  assert.ok(guide.steps.every(s=>s.status==='planned'&&!s.eventInstalled));
});

test('S27 preserva 29 areas sem fase e os links navegaveis de pendencias',()=>{
  assert.equal(filterSinnohGuide(guide,'areas',{fase:'sem-fase'}).count,29);
  assert.equal(filterSinnohGuide(guide,'areas',{busca:'Route 201'}).count>=1,true);
  const areas=sinnohGuidePage(guide,'areas','sem-fase');
  assert.match(areas,/Fase a auditar/);
  assert.match(areas,/Auditar mapas/);
  const league=sinnohGuidePage(guide,'liga');
  assert.match(league,/Cynthia/);
  assert.match(league,/Equipe PBS e batalha nativa: pendentes/);
  const reg=regionsPage(sources.regions);
  assert.match(reg,/href="\/sinnoh">Guia planejado de Sinnoh/);
});

test('S27 recusa promocao artificial de guia para jogo ou provas nativas',()=>{
  for(const modify of [
    x=>{x.canPlay=true;},
    x=>{x.status='playable';},
    x=>{x.gameplayVerified=true;},
    x=>{x.counts.verifiedNativeMaps=1;},
    x=>{x.areas[0].map_id=801;},
    x=>{x.bosses[0].pbsInstalled=true;},
    x=>{x.items[0].pickupVerified=true;}
  ]){
    const bad=structuredClone(guide);
    modify(bad);
    assert.throws(()=>validateSinnohGuide(bad),/sinnoh-guide-invalid/);
  }
});

test('S27 build publica exatamente o guia auditado, nao um mapa jogavel',()=>{
  const target=path.join(root,'site/dist/data/sinnoh-guide.json');
  assert.ok(existsSync(target),'execute npm run build antes dos testes');
  const published=JSON.parse(readFileSync(target,'utf8'));
  assert.deepEqual(published,guide);
  assert.equal(published.canPlay,false);
  assert.equal(published.counts.verifiedNativeMaps,0);
});
