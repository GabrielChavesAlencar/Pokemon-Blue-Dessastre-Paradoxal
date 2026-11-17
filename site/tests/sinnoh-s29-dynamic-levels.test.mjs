// S29 — nivel dinamico documentado sem dados de save, MapIDs ou QA nativa.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateSinnohGuide,sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {sinnohGuidePage} from '../src/assets/sinnoh-guide.js';
import {validateSinnohGuide} from '../src/assets/sinnoh-search.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sources=()=>Object.fromEntries(Object.entries(sinnohSourcePaths)
  .map(([key,relative])=>[key,JSON.parse(readFileSync(path.join(root,relative),'utf8'))]));
const guide=generateSinnohGuide(sources());
const tabs=['visao','areas','treinadores','ginasios','liga','itens','progresso','pendencias'];
const rejects=change=>{
  const forged=structuredClone(guide);
  change(forged);
  assert.throws(()=>validateSinnohGuide(forged),/sinnoh-guide-invalid/);
  assert.throws(()=>sinnohGuidePage(forged,'liga'),/sinnoh-guide-invalid/);
};

test('S29 contratos reais: maior nivel nao-ovo da party, sem cap regional numerico',()=>{
  assert.equal(validateSinnohGuide(guide),guide);
  assert.equal(guide.balance.normalPercent,70);
  assert.equal(guide.balance.masterPercent,90);
  assert.equal(guide.levelPolicy.reference,'highest_non_egg_party_level');
  assert.equal(guide.levelPolicy.regionalNumericCap,null);
  assert.equal(guide.levelPolicy.badgesDoNotRevealExactLevel,true);
  assert.equal(guide.levelPolicy.verifiedRuntimeLevels,false);
  assert.equal(guide.levelPolicy.source,'scripts/battle_polish/Campaign.rb');
  assert.equal(guide.levelPolicy.fieldEvolutionSource,
    'scripts/battle_polish/EvolutionScaling.rb');
  assert.equal(guide.gameplayVerified,false);
  assert.equal(guide.canPlay,false);
});

test('S29 as oito abas apresentam regra 70/90 e ausencia de nivel exato',()=>{
  for(const tab of tabs){
    const html=sinnohGuidePage(guide,tab);
    assert.match(html,/Balanceamento e progressão de níveis/,tab);
    assert.match(html,/maior nível entre os Pokémon da equipe, desconsiderando ovos/,tab);
    assert.match(html,/Normal 70% · Master 90%/,tab);
    assert.match(html,/não consulta/,tab);
    assert.match(html,/nenhuma delas fornece aqui um level cap regional numérico confirmado/,tab);
    assert.match(html,/sem PBS nativo/i,tab);
    assert.match(html,/Ainda não adicionado ao Game.exe\/JoiPlay/,tab);
  }
});

test('S29 líderes e Cynthia mantêm apenas especies historicas, sem level fixo',()=>{
  for(const tab of ['ginasios','liga']){
    const html=sinnohGuidePage(guide,tab);
    assert.doesNotMatch(html,/\b(?:Lv\.?|Nível)\s*\d+\b/i);
    assert.match(html,/PBS: não instalado|Equipe PBS|PBS e batalha nativa/);
  }
  assert.equal(guide.bosses.length,13);
  assert.ok(guide.bosses.every(b=>!Object.hasOwn(b,'level') &&
    !Object.hasOwn(b,'historical_levels')&&!Object.hasOwn(b,'effective_level')&&
    b.pbsInstalled===false&&b.fullPowerVerified===false));
});

test('S29 badges regionais e esmeraldas nunca certificam cap nem recompensa',()=>{
  const html=sinnohGuidePage(guide,'itens');
  assert.match(html,/Insígnias locais controlam permissões regionais e esmeraldas/);
  assert.match(html,/Entrega do HM: não confirmada; permissão: não ativada/);
  assert.equal(guide.levelPolicy.regionalNumericCap,null);
  assert.ok(guide.items.every(x=>x.regionalOnly&&!x.pickupVerified));
});

test('S29 rejeita percentuais, caps, fontes e autenticacao de nivel adulterados',()=>{
  for(const mutation of [
    x=>{x.balance.normalPercent=100;},
    x=>{x.balance.masterPercent=100;},
    x=>{x.levelPolicy.reference='BADGE_COUNT';},
    x=>{x.levelPolicy.regionalNumericCap=50;},
    x=>{x.levelPolicy.regionalNumericCap=0;},
    x=>{x.levelPolicy.badgesDoNotRevealExactLevel=false;},
    x=>{x.levelPolicy.verifiedRuntimeLevels=true;},
    x=>{x.levelPolicy.source='fake.rb';},
    x=>{x.levelPolicy.fieldEvolutionSource='fake.rb';},
    x=>{x.balance.fixedLevel=42;},
    x=>{x.levelPolicy.effectiveLevel=70;}
  ])rejects(mutation);
});

test('S29 rejeita niveis inventados em area, treinador, chefe e etapas',()=>{
  for(const mutation of [
    x=>{x.areas[0].level_cap=40;},
    x=>{x.areas[0].levelRange=[10,20];},
    x=>{x.trainers[0].effective_level=22;},
    x=>{x.bosses[0].effectiveLevel=50;},
    x=>{x.bosses[0].levelCap=60;},
    x=>{x.steps[0].fixedLevel=30;},
    x=>{x.items[0].exact_level=25;}
  ])rejects(mutation);
});

test('S29 falha fechada quando fonte altera regras ou presume cap por badge',()=>{
  for(const mutation of [
    x=>{x.teams.dynamic_balance.normal_percent=100;},
    x=>{x.teams.dynamic_balance.master_percent=100;},
    x=>{x.teams.dynamic_balance.reference_level='highest_badge';},
    x=>{x.teams.ui_policy.publish_historical_fixed_levels=true;},
    x=>{x.teams.ui_policy.render_actual_levels_from='STATIC_PLATINUM';},
    x=>{x.encounters.global_progress.reference_party='badge';},
    x=>{x.encounters.global_progress.regional_numeric_level_cap=45;},
    x=>{x.badges.no_cross_region_key_item_or_hm_transfer=false;}
  ]){
    const inputs=sources();
    mutation(inputs);
    assert.throws(()=>generateSinnohGuide(inputs),/sinnoh-guide-invalid/);
  }
});

test('S29 JSON gerado via build nao publica niveis fixos nem provas de runtime',()=>{
  const file=path.join(root,'site/dist/data/sinnoh-guide.json');
  assert.ok(existsSync(file),'execute npm run build antes dos testes');
  const built=JSON.parse(readFileSync(file,'utf8'));
  assert.deepEqual(built,guide);
  assert.equal(built.levelPolicy.regionalNumericCap,null);
  assert.equal(built.levelPolicy.verifiedRuntimeLevels,false);
  assert.ok(built.areas.every(a=>!('level' in a)));
  assert.ok(built.bosses.every(b=>!('historical_levels' in b)));
});
