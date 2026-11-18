import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateUnovaGuide,unovaGuideSources} from '../scripts/unova-guide.mjs';
import {validateUnovaGuide,unovaGuidePage,unovaGuideUrl} from '../src/assets/unova-guide.js';
import {filterUnovaGuide,unovaFilterUrl} from '../src/assets/unova-search.js';
import {unovaGithubStats,unovaGithubProgressPage} from '../src/assets/unova-progress.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const read=async rel=>JSON.parse(await readFile(path.join(root,rel),'utf8'));
const raw=Object.fromEntries(await Promise.all(Object.entries(unovaGuideSources)
 .map(async ([key,filename])=>[key,await read(filename)])));
const guide=generateUnovaGuide(raw);
const board=await read('site/public/data/unova-github-progress.json');
const encounter=await read('data/regions/unova-g04-encounter-validation-contract.json');
const items=await read('data/regions/unova-g05-regional-items-contract.json');
const blackout=await read('data/regions/unova-g05-blackout-state-contract.json');
const platform=await read('data/regions/unova-g07-platform-compatibility-contract.json');
const integration=await read('data/regions/unova-g08-integrated-contract.json');
const reject=update=>{
 const clone=structuredClone(guide);update(clone);
 assert.throws(()=>validateUnovaGuide(clone),/unova-guide-invalid/);
};

test('G08.2 links 22 source phases without native promotion',()=>{
 assert.equal(integration.coverage.length,22);
 assert.equal(integration.status,'PLANNED_CROSS_CONTRACT_REGRESSION_ONLY');
 assert.equal(integration.can_install,false);
 assert.equal(integration.native_technical_completed,0);
 assert.equal(integration.native_playable_completed,0);
});
test('G01 story has 12 missions and 12 linked chapters in portal',()=>{
 assert.equal(guide.chapters.length,12);
 assert.equal(guide.missions.length,12);
 assert.deepEqual(guide.missions.map(m=>m.key),raw.story.missions.map(m=>m.key));
 for(const mission of guide.missions){
  assert.ok(guide.chapters.some(c=>c.key===mission.chapterKey));
  assert.ok(guide.areas.some(a=>a.key===mission.areaKey));
  assert.equal(mission.nativeMapId,null);
  assert.equal(mission.nativeEventId,null);
 }
});
test('74 U03 areas are the same G04 encounter symbolic areas',()=>{
 assert.equal(guide.areas.length,74);
 assert.deepEqual(new Set(guide.areas.map(a=>a.key)),
                  new Set(encounter.areas.map(a=>a.area_key)));
});
test('no native encounter table falsely inferred from guides or season filters',()=>{
 assert.equal(encounter.native_encounters_verified,false);
 assert.ok(encounter.areas.every(e=>e.native_map_id===null&&
  e.native_encounter_rate===null&&e.native_pbs_verified===false));
 assert.ok(guide.areas.every(a=>a.verifiedEncounters===0&&a.nativeMapId===null));
});
test('all eight G02 White gyms are linked to chapter and area',()=>{
 assert.equal(guide.gyms.length,8);
 for(const g of guide.gyms){
  assert.ok(guide.chapters.some(c=>c.key===g.chapterKey));
  assert.ok(guide.areas.some(a=>a.key===g.cityAreaKey));
  assert.ok(guide.areas.some(a=>a.key===g.gymAreaKey));
  assert.equal(g.team,null);assert.equal(g.levels,null);
 }
});
test('G02 finale four trainers have only symbolic teams',()=>{
 assert.equal(guide.elite.length,4);
 for(const row of guide.elite){
  assert.equal(row.team,null);assert.equal(row.levels,null);
  assert.equal(row.nativeTrainerId,null);
 }
});
test('G03 rivals/Plasma link contract IDs, never native trainer teams',()=>{
 assert.deepEqual(guide.trainers.map(t=>t.key),raw.rivals.encounters.map(t=>t.id));
 assert.ok(guide.trainers.every(t=>t.team===null&&t.levels===null&&t.nativeTrainerId===null));
});
test('G05 regional item rules never install local HM from guide reference',()=>{
 assert.equal(items.can_install,false);
 assert.ok(guide.areas.every(a=>a.installed===false));
});
test('G05 blackout does not claim Unova healing center installed',()=>{
 assert.equal(blackout.native_center_installed,false);
 assert.equal(blackout.can_install,false);
 assert.ok(guide.areas.every(a=>a.nativeMapId===null));
});
test('G07 windows and android cannot claim native package install',()=>{
 assert.equal(platform.can_install,false);
 assert.equal(platform.platforms.windows.native_patch_supported,false);
 assert.equal(platform.platforms.android.native_patch_supported,false);
 assert.equal(platform.platforms.android.existing_update_channels.includes('unova'),false);
});
test('cross source guide validation is fail-closed',()=>{
 assert.equal(validateUnovaGuide(guide),guide);
 assert.equal(guide.canPlay,false);assert.equal(guide.canInstall,false);
});
test('all G08.2 source paths are repo-local and exact',async()=>{
 for(const [key,rel] of Object.entries(integration.source_contracts)){
  assert.ok(!rel.startsWith('/')&&!rel.includes('..'),key);
  assert.ok(rel.endsWith('.json'),key);
  assert.ok((await read(rel)).region==='UNOVA'||['board','registry'].includes(key),key);
 }
});
test('tracker cannot confuse G-completion and playable game',()=>{
 assert.equal(board.status,'PLANNED_NOT_NATIVE_PLAYABLE');
 assert.equal(board.native_technical_bar.completed,0);
 assert.equal(board.native_playable_bar.completed,0);
 assert.equal(board.groups.find(g=>g.id==='G08').tasks.length,4);
});
test('portal shows explicit planned/unplayable warning',()=>{
 const html=unovaGuidePage(guide);
 assert.match(html,/UNOVA PLANEJADA · NÃO JOGÁVEL/);
 assert.match(html,/nenhum.*Game.exe/i);
});
test('source mission records open a chapter page with no native rewards',()=>{
 for(const m of guide.missions){
  const url=unovaGuideUrl('capitulo',m.chapterKey);
  const page=unovaGuidePage(guide,'capitulo',m.chapterKey);
  assert.match(page,/missão|Missões/i);
  assert.ok(page.includes('href="/unova/missoes?capitulo='));
  assert.ok(url.startsWith('/unova/capitulo/'));
 }
});
test('all 74 area page URLs remain shareable',()=>{
 for(const a of guide.areas){
  const html=unovaGuidePage(guide,'area',a.key);
  assert.match(html,/MapID original\/destino: pendente/);
  assert.ok(unovaGuideUrl('area',a.key).startsWith('/unova/area/'));
 }
});
test('mission chapter filters do not create Game.exe events',()=>{
 const chapter=guide.chapters[0].key;
 const result=filterUnovaGuide(guide,'missoes',{capitulo:chapter});
 assert.ok(result.items.length>0);
 assert.ok(result.items.every(e=>e.nativeEventId===null&&e.installed===false));
});
test('G03 trainer area filter only returns references',()=>{
 const first=guide.trainers[0];
 const result=filterUnovaGuide(guide,'treinadores',{area:first.areaKey});
 assert.ok(result.items.length>0);
 assert.ok(result.items.every(e=>e.team===null&&e.nativeTrainerId===null));
});
test('filter query URL can round-trip the symbolic area without MapID',()=>{
 const key=guide.areas[0].key;
 const u=unovaFilterUrl(guide,'areas',{area:key});
 const result=filterUnovaGuide(guide,'areas',u.split('?')[1]);
 assert.ok(result.items.some(x=>x.key===key));
});
test('pending status filter never unlocks a native gameplay button',()=>{
 const u=unovaFilterUrl(guide,'pendencias',{tipo:'mapas'});
 const html=unovaGuidePage(guide,'pendencias',null,new URLSearchParams(u.split('?')[1]));
 assert.match(html,/não jogável|NÃO JOGÁVEL/i);
 assert.doesNotMatch(html,/native install approved/i);
});
test('Barra G tracker correctly corresponds to G08.2 source evidence only',()=>{
 const stats=unovaGithubStats(board);
 assert.equal(stats.total,32);
 assert.ok([30,31].includes(stats.completed)); // branch tracker advances only after first CI
 assert.equal(board.native_playable_bar.completed,0);
 assert.match(unovaGithubProgressPage(board),/Barra G|Progresso/);
});
for(const [key,mutation] of Object.entries({
  nativeArea:d=>d.areas[0].nativeMapId=518,
  fakeAreaInstalled:d=>d.areas[0].installed=true,
  duplicateArea:d=>d.areas[0].key=d.areas[1].key,
  fakeLevels:d=>d.areas[0].verifiedLevels=[80],
  fakeEncounters:d=>d.areas[0].verifiedEncounters=3,
  forgedMissionMap:d=>d.missions[0].nativeMapId=518,
  forgedMissionEvent:d=>d.missions[0].nativeEventId=2,
  missionInstalled:d=>d.missions[0].installed=true,
  missingMission:d=>d.missions.pop(),
  badMissionChapter:d=>d.missions[0].chapterKey='UNOVA_UNKNOWN_CH',
  badMissionArea:d=>d.missions[0].areaKey='UNOVA_UNKNOWN_AREA',
  gymTeam:d=>d.gyms[0].team=['FAKE_MON'],
  gymLevel:d=>d.gyms[0].levels=[100],
  gymInstalled:d=>d.gyms[0].installed=true,
  eliteTeam:d=>d.elite[0].team=['FAKE_MON'],
  trainerLevels:d=>d.trainers[0].levels=[50],
  trainerInstalled:d=>d.trainers[0].installed=true,
  castleEvent:d=>d.castle[0].nativeEventId=2,
  statusPromoted:d=>d.status='NATIVE_READY',
  canPlay:d=>d.canPlay=true,
  mapVerified:d=>d.nativeMapIdsVerified=74,
  encounterVerified:d=>d.nativeEncounterRatesVerified=74
})){
 test('fail-closed G08.2 portal forged '+key,()=>reject(mutation));
}
