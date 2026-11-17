// G10: safe public evidence must not imply Game.exe, ROM or regional save access.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {sinnohG10Sources,generateSinnohG10Status} from '../scripts/sinnoh-g10-status.mjs';
import {generateSinnohGuide,sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {validateSinnohImplementation,sinnohImplementationPanel} from '../src/assets/sinnoh-implementation.js';
import {sinnohGuidePage} from '../src/assets/sinnoh-guide.js';
import {SINNOH_TABS,filterSinnohGuide} from '../src/assets/sinnoh-search.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const load=paths=>Object.fromEntries(Object.entries(paths).map(([key,relative])=>
  [key,JSON.parse(readFileSync(path.join(root,relative),'utf-8'))]));
const source=load(sinnohG10Sources);
const guide=generateSinnohGuide(load(sinnohSourcePaths));
const make=()=>generateSinnohG10Status(structuredClone(source),guide);
const data=make();
const unsafe=mutate=>{
  const changed=structuredClone(source);
  mutate(changed);
  assert.throws(()=>generateSinnohG10Status(changed,guide),/sinnoh-g10-invalid/);
};

test('G10 stage counts distinguish planned areas, private candidate terrains and zero installed/playable',()=>{
  assert.deepEqual(data.states.map(x=>[x.key,x.count]),[
    ['planned',120],['private_preparation',54],['installed',0],['playable',0]
  ]);
  assert.match(data.states[1].meaning,/não verificados neste portal/);
  assert.equal(data.status,'PUBLIC_CONTRACT_EVIDENCE_ONLY_NO_NATIVE_APPROVAL');
});
test('G10 six evidence categories reconcile guide and G09',()=>{
  assert.deepEqual(data.categories.map(x=>x.count),[120,40,8,8,8,6]);
  assert.deepEqual(data.categories.map(x=>x.tab),
    ['areas','treinadores','ginasios','itens','liga','progresso']);
});
test('G10 Fantina and Maylene remain badge-scoped not CH11 array position',()=>{
  assert.deepEqual(data.gyms.slice(2,4).map(x=>[x.label,x.badge,x.hm,x.move]),[
    ['Fantina','RELIC','HM05','DEFOG'],
    ['Maylene','COBBLE','HM02','FLY']
  ]);
  assert.ok(data.gyms.every(x=>x.state==='pending'&&!x.hmPickupVerified));
});
test('G10 two separate League final checkpoints and six inactive postgame gates',()=>{
  assert.deepEqual(data.league.slice(-2).map(x=>x.id),
    ['P09_CYNTHIA_BATTLE','P09_HALL_OF_FAME']);
  assert.equal(data.postgame.length,6);
  assert.ok(data.postgame.every(x=>x.nativeVerified===false));
});
test('G10 integration output is uniformly no native QA',()=>{
  assert.deepEqual(data.verification,{
    nativeAssetBytesInspected:false,privateStageExecutionVerified:false,
    nativeMapBindingsVerified:false,gameExeTested:false,joiplayTested:false,
    installedVerified:false,playableVerified:false,
    phaseBApproved:0,phaseCApproved:0,phaseDApproved:0
  });
  assert.ok(validateSinnohImplementation(data));
});
test('G10 planned region cannot be forced playable',()=>{
  unsafe(x=>{x.registry.regions.SINNOH.status='playable';});
});
test('G10 private B07 installed or R07 fake claims blocked',()=>{
  for(const change of [
    x=>{x.b07.can_install_into_game=true;},
    x=>{x.b07.r07_complete=true;},
    x=>{x.b07.rights_per_asset_verified=true;},
    x=>{x.b07.candidate_terrain_destinations.pop();},
    x=>{x.b07.phase_b_approved=1;},
    x=>{x.b07.imports_donor_events=true;}
  ])unsafe(change);
});
test('G10 B08 cannot claim local stage was received',()=>{
  for(const change of [
    x=>{x.b08.has_live_stage_evidence=true;},
    x=>{x.b08.can_mark_gameplay=true;},
    x=>{x.b08.expected_pngs=13;},
    x=>{x.b08.b07_source_sha256='a'.repeat(64);}
  ])unsafe(change);
});
test('G10 B09 clone without Game.exe evidence remains unapproved',()=>{
  for(const change of [
    x=>{x.b09.game_exe_tested=true;},
    x=>{x.b09.can_mark_native_playable=true;},
    x=>{x.b09.runtime_save_isolation_verified=true;},
    x=>{x.b09.native_b08_user_report_received=true;},
    x=>{x.b09.expected_qa_clone_map_count=703;},
    x=>{x.b09.phase_c_approved=13;}
  ])unsafe(change);
});
test('G10 S15 refuses fake installed gyms, PBS, physical MapIDs',()=>{
  for(const change of [
    x=>{x.gyms.gyms[0].physical_map_id=442;},
    x=>{x.gyms.gyms[2].badge='COBBLE';},
    x=>{x.gyms.gyms[3].trainer_pbs_compiled=true;},
    x=>{x.gyms.gyms[4].physical_event_installed=true;},
    x=>{x.gyms.battles_playable=true;}
  ])unsafe(change);
});
test('G10 S16 requires local HM pickup and no item auto grant',()=>{
  for(const change of [
    x=>{x.hms.can_grant_hm=true;},
    x=>{x.hms.native_receipts_verified=1;},
    x=>{x.hms.hms[0].enabled=true;},
    x=>{x.hms.hms[1].pickup_event_verified=true;},
    x=>{x.hms.hms[2].badge='RELIC';}
  ])unsafe(change);
});
test('G10 S21 never claims Cynthia automatically causes Hall of Fame',()=>{
  for(const change of [
    x=>{x.league.native_hall_of_fame_verified=true;},
    x=>{x.league.steps[7].outcome='battle_won';},
    x=>{x.league.steps[6].id='P09_HALL_OF_FAME';},
    x=>{x.league.steps[6].native_battle_result_verified=true;},
    x=>{x.league.compiled_native_pbs.push('fake');}
  ])unsafe(change);
});
test('G10 postgame not available until HoF, event items, and 10 Leagues',()=>{
  for(const change of [
    x=>{x.postgame.requires_separate_hall_of_fame=false;},
    x=>{x.postgame.events[1].requires_previous_event=null;},
    x=>{x.postgame.events[3].requires_event_item_verification=false;},
    x=>{x.postgame.events[5].requires_all_ten_leagues=false;},
    x=>{x.postgame.installed_postgame_map_ids.push(600);},
    x=>{x.postgame.verification.gameplay_certified=true;}
  ])unsafe(change);
});
test('G10 fails closed on invented status or runtime proof at UI boundary',()=>{
  for(const change of [
    x=>{x.states[2].count=1;},
    x=>{x.states[1].key='installed';},
    x=>{x.verification.gameExeTested=true;},
    x=>{x.verification.phaseBApproved=1;},
    x=>{x.gyms[0].hmPickupVerified=true;},
    x=>{x.league[7].nativeVerified=true;},
    x=>{x.postgame[0].nativeVerified=true;},
    x=>{x.categories[0].playable=true;},
    x=>{x.gyms[0].map_id=442;}
  ]){
    const modified=structuredClone(data);change(modified);
    assert.throws(()=>validateSinnohImplementation(modified),/sinnoh-g10-unsafe/);
  }
});
test('G10 guide navigation exposes implementation tab with proper no-play labels',()=>{
  assert.ok(SINNOH_TABS.includes('implantacao'));
  const html=sinnohGuidePage(guide,'visao','all',{},data);
  assert.match(html,/aba=implantacao/);
  assert.match(html,/Cópia privada prevista/);
  assert.match(html,/54 terrenos candidatos/);
  assert.match(html,/Instalado no jogo/);
  assert.match(html,/Jogável e testado/);
  assert.match(html,/B\/C\/D continuam em 0\/13/);
  assert.doesNotMatch(html,/Instalado e jogável/);
});
test('G10 implementation detail includes gym local HMs, HoF and blocked postgame',()=>{
  const html=sinnohGuidePage(guide,'implantacao','all',{},data);
  assert.match(html,/Fantina/);
  assert.match(html,/RELIC/);
  assert.match(html,/DEFOG/);
  assert.match(html,/Maylene/);
  assert.match(html,/Cynthia/);
  assert.match(html,/Hall of Fame/);
  assert.match(html,/Darkrai\/Shaymin/);
  assert.match(html,/dez Ligas/);
  assert.match(html,/R07:/);
  assert.match(html,/R09:/);
});
test('G10 source-generated cards display safe pending but never fabricate runtime results',()=>{
  const html=sinnohImplementationPanel(data,'implantacao');
  assert.match(html,/Pendente/);
  assert.doesNotMatch(html,/Game.exe testado com sucesso/);
  assert.doesNotMatch(html,/C:\\Users\\/);
  assert.doesNotMatch(html,/\/downloads\?regiao=sinnoh/);
});
test('G10 HTML escapes poisoned display metadata',()=>{
  const modified=structuredClone(data);
  modified.categories[0].label='<svg onload=alert(1)>';
  modified.blockers[0]='<script>danger</script>';
  const html=sinnohImplementationPanel(modified,'implantacao');
  assert.match(html,/&lt;svg/);
  assert.match(html,/&lt;script&gt;/);
  assert.doesNotMatch(html,/<script>|<svg onload/);
});
test('G10 existing guide filters still return unchanged planned records',()=>{
  assert.equal(filterSinnohGuide(guide,'areas',{fase:'3'}).count,9);
  assert.equal(filterSinnohGuide(guide,'ginasios').count,8);
  assert.equal(filterSinnohGuide(guide,'itens').count,8);
  assert.equal(filterSinnohGuide(guide,'pendencias').count,7);
});
test('G10 build artifact exactly matches audited sources, no fake install',()=>{
  const file=path.join(root,'site/dist/data/sinnoh-implementation.json');
  assert.ok(existsSync(file),'run site build first');
  const generated=JSON.parse(readFileSync(file,'utf-8'));
  assert.deepEqual(generated,data);
  assert.equal(generated.verification.gameExeTested,false);
  assert.equal(generated.states[3].count,0);
});
