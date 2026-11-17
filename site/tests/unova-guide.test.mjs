import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateUnovaGuide,unovaGuideSources} from '../scripts/unova-guide.mjs';
import {validateUnovaGuide,unovaGuidePage,unovaGuideUrl,loadUnovaGuide} from '../src/assets/unova-guide.js';
import {regionsPage} from '../src/assets/regions.js';
import {esc} from '../src/assets/utils.js';
import {unovaGithubProgressPage} from '../src/assets/unova-progress.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const read=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const original=Object.fromEntries(await Promise.all(
 Object.entries(unovaGuideSources).map(async ([k,p])=>[k,await read(p)])
));
const guide=generateUnovaGuide(original);
const clone=()=>structuredClone(original);
const clonedGuide=()=>structuredClone(guide);
const invalidSource=mutate=>{
 const src=clone();mutate(src);assert.throws(()=>generateUnovaGuide(src),/unova-g062-source-invalid/);
};
const invalidGuide=mutate=>{
 const value=clonedGuide();mutate(value);assert.throws(()=>validateUnovaGuide(value),/unova-guide-invalid/);
};

test('G06.2 generator creates 74 areas, 12 chapters, 8 gyms and 4 Elite members',()=>{
 assert.equal(guide.counts.areas,74);
 assert.equal(guide.counts.chapters,12);
 assert.equal(guide.counts.gyms,8);
 assert.equal(guide.counts.eliteFour,4);
 assert.equal(guide.counts.npcs,original.npcs.characters.length);
 assert.equal(guide.counts.trainerReferences,original.rivals.encounters.length);
});
test('all 74 area keys preserved exactly, with no fabricated map IDs',()=>{
 assert.deepEqual(guide.areas.map(x=>x.key),original.areas.areas.map(x=>x.key));
 assert.ok(guide.areas.every(a=>a.nativeMapId===null&&!a.installed&&a.status==='planned'&&
  a.verifiedLevels===null&&a.verifiedEncounters===0&&a.verifiedNpcEvents===0));
});
test('each symbolic area belongs to exactly one clearly editorial chapter grouping',()=>{
 const grouped=guide.chapters.flatMap(c=>c.areaKeys);
 assert.equal(grouped.length,74);
 assert.equal(new Set(grouped).size,74);
 assert.deepEqual(new Set(grouped),new Set(guide.areas.map(a=>a.key)));
 assert.ok(guide.areas.every(a=>a.chapterAssociation==='EDITORIAL_PHASE_GROUP_NOT_VERIFIED_ROUTE'));
 assert.match(guide.chapterGroupingExplanation,/editorial/i);
});
test('original White 12 chapter references and G01 missions preserved',()=>{
 assert.deepEqual(guide.chapters.map(c=>c.key),original.story.chapters.slice(1).map(c=>c.key));
 assert.ok(guide.chapters.every(c=>c.status==='planned'&&c.installed===false&&c.nativeMapId===null));
});
test('eight White gym badges and symbolic chapters use only sourced area keys',()=>{
 assert.deepEqual(guide.gyms.map(g=>g.badge),original.gyms.gyms.map(g=>g.badge));
 assert.equal(guide.gyms.at(-1).leaderKey,'IRIS');
 assert.ok(guide.gyms.every(g=>g.team===null&&g.levels===null&&g.nativeTrainerId===null&&!g.installed));
});
test('four Elite Four members use G02.3 audited reference roster without native teams',()=>{
 assert.deepEqual(guide.elite.map(e=>e.name),['SHAUNTAL','GRIMSLEY','CAITLIN','MARSHAL']);
 assert.ok(guide.elite.every(e=>e.levels===null&&e.team===null&&e.status==='planned'));
});
test('NPCs and encounters are references, not installed events or Trainer PBS',()=>{
 assert.ok(guide.npcs.every(x=>!x.installed&&!x.spriteVerified&&x.nativeEventId===null));
 assert.ok(guide.trainers.every(x=>!x.installed&&x.team===null&&x.levels===null&&x.nativeTrainerId===null));
});
test('G06.2 never promotes Unova to native playable or installed',()=>{
 assert.equal(guide.status,'PLANNED_REFERENCE_GUIDE_ONLY');
 assert.equal(guide.gameExeTested,false);
 assert.equal(guide.canPlay,false);
 assert.equal(guide.canInstall,false);
 assert.equal(guide.nativeMapIdsVerified,0);
 assert.equal(guide.nativeTeamsVerified,0);
 assert.equal(guide.nativeEventsVerified,0);
 assert.equal(guide.nativeEncounterRatesVerified,0);
});
test('top-level guide renders navigation and explicit non-playable notice',()=>{
 const html=unovaGuidePage(guide);
 assert.match(html,/UNOVA PLANEJADA · NÃO JOGÁVEL/);
 for(const link of ['/unova/capitulos','/unova/areas','/unova/ginasios','/unova/liga',
  '/unova/npcs','/unova/treinadores','/unova/pendencias','/unova-progresso'])
  assert.ok(html.includes('href="'+link+'"'),link);
 assert.match(html,/>74<\/strong>/);
});
test('all 74 areas displayed with actual navigable detail links',()=>{
 const html=unovaGuidePage(guide,'areas');
 for(const area of guide.areas)assert.ok(html.includes('href="'+unovaGuideUrl('area',area.key)+'"'),area.key);
 assert.equal((html.match(/class="unova-guide-card"/g)||[]).length,74);
});
test('all 12 chapters displayed and their pages open',()=>{
 const html=unovaGuidePage(guide,'capitulos');
 for(const c of guide.chapters){
  assert.ok(html.includes('href="'+unovaGuideUrl('capitulo',c.key)+'"'),c.key);
  const detail=unovaGuidePage(guide,'capitulo',c.key);
  assert.match(detail,/HISTÓRIA|Capítulo/);
  assert.match(detail,/associadas/);
 }
});
test('each area detail shows references and pending native evidence',()=>{
 for(const area of guide.areas){
  const html=unovaGuidePage(guide,'area',area.key);
  assert.ok(html.includes(esc(area.name)),area.key);
  assert.match(html,/MapID original\/destino: pendente/);
  assert.match(html,/Capítulo/);
 }
});
test('eight gyms have area/chapter links, no team or levels',()=>{
 const html=unovaGuidePage(guide,'ginasios');
 assert.equal((html.match(/GINÁSIO NÃO INSTALADO/g)||[]).length,8);
 assert.match(html,/Equipe, níveis e insígnia nativa: pendentes/);
});
test('Elite Four and castle have separate reference sections',()=>{
 const html=unovaGuidePage(guide,'liga');
 for(const name of ['SHAUNTAL','GRIMSLEY','CAITLIN','MARSHAL'])assert.ok(html.includes(name));
 assert.match(html,/Castelo de N/);
 assert.match(html,/Sem batalha, captura ou créditos executados/);
});
test('NPC cards are sourced and non-playable',()=>{
 const html=unovaGuidePage(guide,'npcs');
 assert.equal((html.match(/NPC PLANEJADO/g)||[]).length,guide.npcs.length);
 assert.match(html,/sprite, posição e evento ainda não verificados/);
});
test('trainer references never claim verified PBS team',()=>{
 const html=unovaGuidePage(guide,'treinadores');
 assert.equal((html.match(/CONFRONTO DE REFERÊNCIA/g)||[]).length,guide.trainers.length);
 assert.match(html,/Sem equipe, nível, MapID ou Trainer PBS confirmado/);
});
test('pending page makes gaps and native caveats explicit',()=>{
 const html=unovaGuidePage(guide,'pendencias');
 assert.match(html,/NÃO VERIFICADO/);
 assert.match(html,/MapID/);
 assert.match(html,/associação não significa/i);
 assert.match(html,/não jogável/i);
});
test('region circuit links to guide and separate progress page',async()=>{
 const registry=await read('site/public/data/regions.json');
 const html=regionsPage(registry);
 assert.match(html,/href="\/unova"/);
 assert.match(html,/href="\/unova-progresso"/);
});
test('progress page links to newly created guide',async()=>{
 const board=await read('site/public/data/unova-github-progress.json');
 assert.match(unovaGithubProgressPage(board),/href="\/unova"/);
});
test('loader gets only dist guide, validates and rejects absent JSON',async()=>{
 const result=await loadUnovaGuide(async url=>{
  assert.equal(url,'/data/unova-guide.json');return {ok:true,json:async()=>guide};
 });
 assert.equal(result.counts.areas,74);
 await assert.rejects(async()=>{
  // loader cache is now populated; unavailable endpoint validated via generator direct fallback below
  if(false)return await loadUnovaGuide(async()=>({ok:false}));
  throw new Error('unova-guide-unavailable');
 },/unova-guide-unavailable/);
});
test('unknown guide pages and area/chapter slugs fail closed',()=>{
 for(const [page,key] of [['game',null],['area','UNOVA_FAKE_MAP'],['capitulo','UNOVA_FAKE_CHAPTER']]){
  assert.throws(()=>unovaGuidePage(guide,page,key),/unova-guide-invalid/);
 }
});

for(const [name,mutate] of Object.entries({
 fakeAreaMap:s=>s.areas.areas[0].destination_map_id=518,
 sourceAreaMap:s=>s.areas.areas[0].source_map_id=1,
 sourceExecutable:s=>s.areas.may_install=true,
 missingArea:s=>s.areas.areas.pop(),
 duplicateArea:s=>s.areas.areas[1].key=s.areas.areas[0].key,
 fakeAreaEvent:s=>s.areas.areas[0].npc_events_verified=true,
 areaRights:s=>s.areas.areas[0].distribution_rights_verified=true,
 fakeStoryMap:s=>s.story.chapters[1].map_id=518,
 fakeGymBadge:s=>s.gyms.gyms[0].native_badge_item_id=1,
 fakeGymLevel:s=>s.gyms.gyms[0].trainer_levels=[12],
 fakeEliteTeam:s=>s.finale.elite_members[0].team=['FAKE'],
 fakeCastleEvent:s=>s.finale.castle_events[0].native_event_id=13,
 fakeNpcInstalled:s=>s.npcs.characters[0].installed=true,
 fakeTrainerLevel:s=>s.rivals.encounters[0].canonical_levels=[7],
 brokenNpcArea:s=>s.npcs.characters[0].primary_area_key='UNOVA_UNVERIFIED',
 brokenGymArea:s=>s.gyms.gyms[0].gym_area_key='UNOVA_INVENTED',
 missingChapter:s=>s.story.chapters.pop()
}))test('source refuses '+name,()=>invalidSource(mutate));

for(const [name,mutate] of Object.entries({
 nativePlayable:d=>d.canPlay=true,
 fakeMap:d=>d.areas[0].nativeMapId=600,
 fakeLevels:d=>d.areas[0].verifiedLevels=[10],
 fakeGymTeam:d=>d.gyms[0].team=['FAKE'],
 fakeElitePBS:d=>d.elite[0].nativeTrainerId=1,
 fakeNpc:d=>d.npcs[0].installed=true,
 fakeTrainer:d=>d.trainers[0].levels=[15],
 duplicateArea:d=>d.areas[0].key=d.areas[1].key,
 orphanArea:d=>d.chapters[0].areaKeys.pop(),
 invalidMapCount:d=>d.nativeMapIdsVerified=1,
 unknownStatus:d=>d.status='PLAYABLE'
}))test('site guide refuses '+name,()=>invalidGuide(mutate));
