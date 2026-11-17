// S28: times historicos de Platinum != PBS/Full Power instalados no Blue.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateSinnohGuide,sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {validateSinnohGuide} from '../src/assets/sinnoh-search.js';
import {sinnohGuidePage} from '../src/assets/sinnoh-guide.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sources=()=>Object.fromEntries(Object.entries(sinnohSourcePaths)
  .map(([key,relative])=>[key,JSON.parse(readFileSync(path.join(root,relative),'utf8'))]));
const guide=generateSinnohGuide(sources());
const corrupt=(change)=>{
  const altered=structuredClone(guide);
  change(altered);
  assert.throws(()=>validateSinnohGuide(altered),/sinnoh-guide-invalid/);
  assert.throws(()=>sinnohGuidePage(altered,'liga'),/sinnoh-guide-invalid/);
};

test('S28 catalogo completo: 8 ginasios, 4 Elite, Cynthia e 5 revanches documentais',()=>{
  assert.equal(validateSinnohGuide(guide),guide);
  assert.equal(guide.bosses.length,13);
  assert.equal(guide.bosses.filter(x=>x.role==='GYM_LEADER').length,8);
  assert.equal(guide.bosses.filter(x=>x.role==='ELITE_FOUR').length,4);
  assert.equal(guide.bosses.filter(x=>x.role==='CHAMPION').length,1);
  assert.equal(guide.teamCatalog.historicalTrainerCount,13);
  assert.equal(guide.teamCatalog.regularTrainersWithoutVerifiedTeams,40);
  assert.equal(guide.teamCatalog.officialPlatinumRematchReferences,5);
  assert.equal(guide.teamCatalog.verifiedBlueTrainerTeams,0);
  assert.equal(guide.teamCatalog.blueFullPowerVerifiedTeams,0);
  assert.equal(guide.teamCatalog.compiledNativePBSTeams,0);
  assert.equal(guide.teamCatalog.gameExeVerifiedTeams,0);
  assert.equal(guide.teamCatalog.fixedRuntimeLevelsPublished,false);
  assert.equal(guide.canPlay,false);
});

test('S28 prova integridade de cada composicao com o contrato CH15',()=>{
  const src=sources().teams;
  assert.equal(src.trainers.length,13);
  for(const t of src.trainers){
    const b=guide.bosses.find(x=>x.id===t.id);
    assert.ok(b,t.id);
    assert.deepEqual(b.speciesReference,t.first_battle.species);
    assert.equal(b.teamAudit.firstBattle.memberCount,t.first_battle.species.length);
    assert.equal(b.teamAudit.firstBattle.origin,'PLATINUM_FIRST_BATTLE');
    assert.equal(b.teamAudit.firstBattle.verifiedInBlue,false);
    assert.deepEqual(b.rematchSpeciesReference,
      t.historical_rematch?.species??null);
    assert.equal(b.teamAudit.historicalRematch?.memberCount??null,
      t.historical_rematch?.species.length??null);
    assert.equal(b.teamAudit.blueFullPower.species,null);
    assert.equal(b.teamAudit.nativePBS.team,null);
    assert.equal(b.teamAudit.nativePBS.compiled,false);
    assert.equal(b.teamAudit.nativePBS.eventBound,false);
    assert.equal(b.teamAudit.nativePBS.gameExeVerified,false);
    assert.ok(!Object.hasOwn(b,'level')&&!Object.hasOwn(b,'historical_levels'));
  }
});

test('S28 Roark, Candice, Aaron e Cynthia preservam equipe e ordem historica',()=>{
  const byName=Object.fromEntries(guide.bosses.map(b=>[b.name,b]));
  assert.deepEqual(byName.Roark.speciesReference,['GEODUDE','ONIX','CRANIDOS']);
  assert.equal(byName.Candice.speciesReference.length,4);
  assert.deepEqual(byName.Aaron.speciesReference,
    ['YANMEGA','SCIZOR','VESPIQUEN','HERACROSS','DRAPION']);
  assert.deepEqual(byName.Cynthia.speciesReference,
    ['SPIRITOMB','ROSERADE','MILOTIC','TOGEKISS','LUCARIO','GARCHOMP']);
  assert.equal(byName.Cynthia.teamAudit.historicalRematch.memberCount,6);
  assert.equal(byName.Fantina.order,3);
  assert.equal(byName.Maylene.order,4);
  assert.ok(guide.bosses.filter(b=>b.role==='GYM_LEADER')
    .every(b=>b.teamAudit.historicalRematch===null));
});

test('S28 UI exibe 13 equipes historicas e deixa 40 treinadores comuns pendentes',()=>{
  const gym=sinnohGuidePage(guide,'ginasios');
  const league=sinnohGuidePage(guide,'liga');
  const trainer=sinnohGuidePage(guide,'treinadores');
  const overview=sinnohGuidePage(guide,'visao');
  assert.equal((gym.match(/Catálogo histórico:/g)||[]).length,8);
  assert.equal((league.match(/Catálogo histórico:/g)||[]).length,5);
  assert.equal((league.match(/Revanche Platinum:/g)||[]).length,5);
  assert.match(gym,/Full Power Blue: pendente/);
  assert.match(gym,/Equipe PBS: não compilada/);
  assert.match(league,/Não representa variante Full Power do Blue/);
  assert.match(trainer,/40 treinadores gerais não têm times Blue verificados/);
  assert.match(trainer,/Equipe nativa Blue: a auditar/);
  assert.match(overview,/13<\/strong><span>Equipes históricas auditadas/);
  for(const html of [gym,league,trainer]){
    assert.match(html,/NÃO JOGÁVEL/);
    assert.doesNotMatch(html,/\b(?:Lv\.?|Nível)\s*\d+\b/i);
  }
});

test('S28 recusa registro adulterado de time compilado ou Full Power',()=>{
  for(const mutation of [
    x=>{x.bosses[0].teamAudit.nativePBS.compiled=true;},
    x=>{x.bosses[0].teamAudit.nativePBS.eventBound=true;},
    x=>{x.bosses[0].teamAudit.nativePBS.gameExeVerified=true;},
    x=>{x.bosses[0].teamAudit.nativePBS.team=['GEODUDE'];},
    x=>{x.bosses[0].teamAudit.blueFullPower.verified=true;},
    x=>{x.bosses[0].teamAudit.blueFullPower.species=['ARCEUS'];},
    x=>{x.teamCatalog.compiledNativePBSTeams=13;},
    x=>{x.teamCatalog.gameExeVerifiedTeams=13;},
    x=>{x.teamCatalog.blueFullPowerVerifiedTeams=13;},
    x=>{x.teamCatalog.verifiedBlueTrainerTeams=40;}
  ])corrupt(mutation);
});

test('S28 recusa corrupcao dos 13 registros, revanches e numero de slots',()=>{
  for(const mutation of [
    x=>{x.bosses.pop();},
    x=>{x.bosses[0].teamAudit.firstBattle.memberCount=6;},
    x=>{x.bosses[0].teamAudit.historicalRematch={origin:'PLATINUM_LEAGUE_REMATCH',
      memberCount:3,verifiedInBlue:false};},
    x=>{x.bosses[8].teamAudit.historicalRematch=null;},
    x=>{x.bosses[8].rematchSpeciesReference=[];},
    x=>{x.bosses[12].teamAudit.firstBattle.verifiedInBlue=true;},
    x=>{x.bosses[12].teamAudit.historicalRematch.verifiedInBlue=true;},
    x=>{x.teamCatalog.officialPlatinumRematchReferences=0;},
    x=>{x.teamCatalog.regularTrainersWithoutVerifiedTeams=0;}
  ])corrupt(mutation);
});

test('S28 recusa niveis historicos embutidos no payload e role falsamente jogavel',()=>{
  for(const mutation of [
    x=>{x.bosses[0].teamAudit.firstBattle.historical_levels=[12,12,14];},
    x=>{x.bosses[12].teamAudit.historicalRematch.level=78;},
    x=>{x.bosses[12].teamAudit.nativePBS.level=78;},
    x=>{x.bosses[12].level=62;},
    x=>{x.teamCatalog.fixedRuntimeLevelsPublished=true;},
    x=>{x.bosses[0].pbsInstalled=true;},
    x=>{x.bosses[0].fullPowerVerified=true;}
  ])corrupt(mutation);
});

test('S28 gerador rejeita origens alteradas, falsos PBS e rematch como Full Power',()=>{
  const original=sources();
  for(const mutation of [
    x=>{x.teams.trainers[0].first_battle.verified_in_blue_pbs=true;},
    x=>{x.teams.trainers[0].first_battle.source='BLUE_NATIVE';},
    x=>{x.teams.trainers[0].first_battle.levels_are_not_runtime_levels=false;},
    x=>{x.teams.trainers[0].first_battle.species.pop();},
    x=>{x.teams.trainers[8].historical_rematch.verified_in_blue_pbs=true;},
    x=>{x.teams.trainers[8].historical_rematch.source='BLUE_FULL_POWER';},
    x=>{x.teams.trainers[0].native_pbs.team=['GEODUDE'];},
    x=>{x.teams.trainers[0].native_pbs.source_file='PBS/trainers.txt';},
    x=>{x.teams.trainers[0].blue_strongest.species=['ARCEUS'];},
    x=>{x.teams.ui_policy.publish_rematch_as_blue_strongest=true;},
    x=>{x.teams.ui_policy.publish_unverified_blue_native_as_installed=true;},
    x=>{x.teams.native_event_battle_bindings_verified=true;},
    x=>{x.teams.may_write_pbs=true;}
  ]){
    const copy=structuredClone(original);
    mutation(copy);
    assert.throws(()=>generateSinnohGuide(copy),/sinnoh-guide-invalid/);
  }
});

test('S28 protege HTML de nomes de especies fornecidos por dados de referencia',()=>{
  const copy=sources();
  copy.teams.trainers[0].first_battle.species[0]='<svg onload=alert(1)>';
  const html=sinnohGuidePage(generateSinnohGuide(copy),'ginasios');
  assert.match(html,/&lt;svg onload=alert\(1\)&gt;/);
  assert.doesNotMatch(html,/<svg onload=/);
});

test('S28 build do portal reproduz exatamente o catalogo auditado',()=>{
  const out=path.join(root,'site/dist/data/sinnoh-guide.json');
  assert.ok(existsSync(out),'execute npm run build antes de npm test');
  const built=JSON.parse(readFileSync(out,'utf8'));
  assert.deepEqual(built,guide);
  assert.equal(built.teamCatalog.compiledNativePBSTeams,0);
  assert.equal(built.teamCatalog.historicalTrainerCount,13);
  assert.ok(built.bosses.every(b=>b.teamAudit.nativePBS.gameExeVerified===false));
});
