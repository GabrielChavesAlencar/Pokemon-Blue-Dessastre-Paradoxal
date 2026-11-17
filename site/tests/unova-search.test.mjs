import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateUnovaGuide,unovaGuideSources} from '../scripts/unova-guide.mjs';
import {validateUnovaGuide,unovaGuidePage} from '../src/assets/unova-guide.js';
import {filterUnovaGuide,sanitizeUnovaFilters,unovaGuideOptions,unovaFilterUrl,
 normalizeUnovaText,UNOVA_FILTER_TABS,UNOVA_PENDING_TYPES} from '../src/assets/unova-search.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sources=Object.fromEntries(await Promise.all(Object.entries(unovaGuideSources).map(async ([key,p])=>
 [key,JSON.parse(await readFile(path.join(root,p),'utf8'))])));
const guide=generateUnovaGuide(sources);
const full=(tab)=>filterUnovaGuide(guide,tab);
const listed=(tab,params)=>filterUnovaGuide(guide,tab,params);
const html=(tab,params={})=>unovaGuidePage(guide,tab,null,params);

test('G06.3 sources all 12 real G01 mission references without inventing native events',()=>{
 assert.equal(guide.missions.length,12);
 assert.equal(guide.counts.missions,12);
 assert.deepEqual(guide.missions.map(x=>x.key),sources.story.missions.map(x=>x.key));
 assert.ok(guide.missions.every(x=>x.status==='planned'&&!x.installed&&
  x.nativeEventId===null&&x.nativeMapId===null));
 assert.equal(validateUnovaGuide(guide),guide);
});
test('8 browse categories all accept default query and return planned items',()=>{
 assert.deepEqual([...UNOVA_FILTER_TABS],[
  'areas','capitulos','missoes','npcs','treinadores','ginasios','liga','pendencias'
 ]);
 for(const tab of UNOVA_FILTER_TABS){
  const result=full(tab);
  assert.ok(result.total>0,tab);
  assert.equal(result.count,result.total,tab);
  assert.equal(result.filters.busca,'',tab);
  assert.equal(result.filters.tipo,'todos',tab);
  assert.match(html(tab),/UNOVA PLANEJADA · NÃO JOGÁVEL/);
 }
});
test('74 areas, 12 chapters, 12 missions, 8 gyms remain searchable',()=>{
 assert.equal(full('areas').count,74);
 assert.equal(full('capitulos').count,12);
 assert.equal(full('missoes').count,12);
 assert.equal(full('ginasios').count,8);
});
test('query text is accent and case insensitive',()=>{
 assert.equal(normalizeUnovaText('  POKÉMON  WHITE  '),'pokemon white');
 assert.equal(normalizeUnovaText('CÉLIA'),'celia');
 assert.equal(normalizeUnovaText(' Rota 1 '),'route 1');
});
test('searches area by Nuvema name and exact symbolic key',()=>{
 const name=listed('areas',{busca:'nuvema'});
 const key=listed('areas',{busca:'UNOVA_NUVEMA_TOWN'});
 assert.ok(name.items.some(x=>x.key==='UNOVA_NUVEMA_TOWN'));
 assert.equal(key.count,1);
});
test('searches route with Portuguese and English text',()=>{
 const pt=listed('areas',{busca:'Rota 1'});
 const en=listed('areas',{busca:'Route 1'});
 assert.ok(pt.count>0);
 assert.equal(pt.count,en.count);
 assert.deepEqual(pt.items.map(x=>x.key),en.items.map(x=>x.key));
});
test('searches NPC role, name and referenced area',()=>{
 assert.ok(listed('npcs',{busca:'Bianca'}).count>0);
 assert.ok(listed('npcs',{busca:'RIVAL'}).count>0);
 assert.ok(listed('npcs',{busca:'Nuvema'}).count>0);
});
test('searches trainer actor, reference chapter and area',()=>{
 assert.ok(listed('treinadores',{busca:'CHEREN'}).count>0);
 assert.ok(listed('treinadores',{busca:'Nuvema'}).count>0);
});
test('searches missions by symbolic ID and chapter title',()=>{
 const result=listed('missoes',{busca:'UNOVA_MISSION_CH01_BEGIN_JOURNEY'});
 assert.equal(result.count,1);
 assert.equal(result.items[0].chapterKey,'UNOVA_CH01_NUVEMA');
 assert.ok(listed('missoes',{busca:'Nuvema'}).count>0);
});
test('searches chapters and badges',()=>{
 assert.ok(listed('capitulos',{busca:'Opelucid'}).count>0);
 assert.ok(listed('ginasios',{busca:'TRIO'}).count===1);
 assert.ok(listed('ginasios',{busca:'IRIS'}).count===1);
});
test('searches Elite by member and Castle by story',()=>{
 assert.ok(listed('liga',{busca:'SHAUNTAL'}).items.some(x=>x.entryKind==='elite'));
 assert.ok(listed('liga',{busca:'Castelo'}).count>0);
});
test('area phase selector returns only the selected audited phase',()=>{
 const result=listed('areas',{fase:'U07'});
 assert.ok(result.count>0);
 assert.ok(result.items.every(x=>x.plannedPhase==='U07'));
});
test('trainer chapter filter uses contract chapter key and no native gate',()=>{
 const result=listed('treinadores',{capitulo:'UNOVA_CH01_NUVEMA'});
 assert.ok(result.count>0);
 assert.ok(result.items.every(x=>x.chapterKey==='UNOVA_CH01_NUVEMA'));
 assert.ok(result.items.every(x=>x.status==='planned'&&x.levels===null));
});
test('mission chapter filter returns exactly one canonical mission',()=>{
 const result=listed('missoes',{capitulo:'UNOVA_CH03_NACRENE'});
 assert.equal(result.count,1);
 assert.equal(result.items[0].chapterKey,'UNOVA_CH03_NACRENE');
});
test('NPC chapter filter comes from primary editorial area, not a native map transfer',()=>{
 const result=listed('npcs',{capitulo:'UNOVA_CH01_NUVEMA'});
 assert.ok(result.count>0);
 for(const row of result.items){
  const area=guide.areas.find(x=>x.key===row.areaKey);
  assert.equal(area.chapterKey,'UNOVA_CH01_NUVEMA');
 }
});
test('area type filters only routes and settlement kinds',()=>{
 const routes=listed('areas',{tipo:'route'});
 assert.equal(routes.count,18);
 assert.ok(routes.items.every(x=>x.kind==='route'));
 const town=listed('areas',{tipo:'settlement'});
 assert.equal(town.count,15);
});
test('NPC role filtering returns documented rivals only',()=>{
 const roles=listed('npcs',{tipo:'RIVAL'});
 assert.ok(roles.count>=2);
 assert.ok(roles.items.every(x=>x.role==='RIVAL'));
});
test('trainer actor filter narrows even with shared location',()=>{
 const result=listed('treinadores',{tipo:'CHEREN'});
 assert.ok(result.count>0);
 assert.ok(result.items.every(x=>x.actor==='CHEREN'));
});
test('area context narrows NPCs to their primary/related references',()=>{
 const ref='UNOVA_NUVEMA_TOWN';
 const result=listed('npcs',{area:ref});
 assert.ok(result.count>0);
 assert.ok(result.items.every(n=>n.areaKey===ref||n.relatedAreaKeys.includes(ref)));
});
test('area context narrows trainer encounters to a single area',()=>{
 const ref='UNOVA_NUVEMA_TOWN';
 const result=listed('treinadores',{area:ref});
 assert.ok(result.count>0);
 assert.ok(result.items.every(x=>x.areaKey===ref));
});
test('area context narrows missions to audited referenced location',()=>{
 const result=listed('missoes',{area:'UNOVA_NUVEMA_TOWN'});
 assert.equal(result.count,1);
});
test('pending type filters classify native unresolved categories only',()=>{
 const maps=listed('pendencias',{tipo:'mapas'});
 assert.equal(maps.count,1);
 assert.match(maps.items[0].label,/MapIDs/);
 const qa=listed('pendencias',{pendencia:'qa'});
 assert.equal(qa.count,1);
});
test('NPC pending filter for sprites contains no installed sprite',()=>{
 const result=listed('npcs',{pendencia:'sprites'});
 assert.equal(result.count,guide.npcs.length);
 assert.ok(result.items.every(x=>x.spriteVerified===false));
});
test('trainer pending filter for teams preserves unknown rosters',()=>{
 const result=listed('treinadores',{pendencia:'equipes'});
 assert.equal(result.count,guide.trainers.length);
 assert.ok(result.items.every(x=>x.team===null&&x.levels===null));
});
test('combines phase, area, category and search with logical AND',()=>{
 const result=listed('areas',{fase:'U07',tipo:'settlement',busca:'Nuvema'});
 assert.equal(result.count,1);
 assert.equal(result.items[0].key,'UNOVA_NUVEMA_TOWN');
 const none=listed('areas',{fase:'U07',tipo:'gym',busca:'Nuvema'});
 assert.equal(none.count,0);
});
test('no results render an explicit accessible empty state',()=>{
 const out=html('areas',{busca:'XYXYXY-NOT-AN-AREA'});
 assert.match(out,/Nenhuma referência planejada corresponde aos filtros/);
 assert.match(out,/0 de 74 referências planejadas/);
 assert.match(out,/role="status"/);
});
test('navigation includes a distinct mission view and retains all existing sections',()=>{
 const out=unovaGuidePage(guide);
 for(const dest of ['/unova/missoes','/unova/areas','/unova/capitulos',
  '/unova/npcs','/unova/treinadores','/unova/liga','/unova/ginasios','/unova/pendencias']){
  assert.ok(out.includes('href="'+dest+'"'),dest);
 }
});
test('mission list shows links to area and chapter without native events',()=>{
 const out=html('missoes',{busca:'UNOVA_MISSION_CH01_BEGIN_JOURNEY'});
 assert.match(out,/Evento, flag, recompensa e MapID nativos: pendentes/);
 assert.match(out,/href="\/unova\/capitulo\/UNOVA_CH01_NUVEMA"/);
 assert.match(out,/href="\/unova\/area\/UNOVA_NUVEMA_TOWN"/);
});
test('filtered NPC cards preserve source area links',()=>{
 const out=html('npcs',{busca:'Bianca'});
 assert.match(out,/href="\/unova\/area\/UNOVA_NUVEMA_TOWN"/);
 assert.match(out,/sprite, posição e evento ainda não verificados/);
});
test('filtered trainer cards preserve chapter links',()=>{
 const out=html('treinadores',{busca:'CHEREN'});
 assert.match(out,/href="\/unova\/capitulo\/UNOVA_CH01_NUVEMA"/);
 assert.match(out,/Sem equipe, nível, MapID ou Trainer PBS confirmado/);
});
test('area details expose deep links for NPC and trainer references',()=>{
 const a=guide.areas.find(x=>x.key==='UNOVA_NUVEMA_TOWN');
 const out=unovaGuidePage(guide,'area',a.key);
 assert.match(out,/\/unova\/npcs\?area=UNOVA_NUVEMA_TOWN/);
 assert.match(out,/\/unova\/treinadores\?area=UNOVA_NUVEMA_TOWN/);
});
test('chapter details link to filtered mission list',()=>{
 const out=unovaGuidePage(guide,'capitulo','UNOVA_CH01_NUVEMA');
 assert.match(out,/href="\/unova\/missoes\?capitulo=UNOVA_CH01_NUVEMA"/);
});
test('GET form, accessible labels and aria-live count for keyboard navigation',()=>{
 const out=html('areas');
 assert.match(out,/method="get"/);
 assert.match(out,/role="search"/);
 assert.match(out,/data-unova-filters/);
 assert.match(out,/type="search"/);
 assert.match(out,/maxlength="100"/);
 assert.match(out,/aria-label="Buscar referências de Unova"/);
 assert.match(out,/aria-live="polite"/);
 assert.match(out,/type="submit"/);
 assert.match(out,/href="\/unova\/areas">Limpar filtros/);
});
test('URLSearchParams shareable filters round-trip and preserve text',()=>{
 const target=unovaFilterUrl(guide,'areas',{busca:'Nuvema Town',fase:'U07',tipo:'settlement'});
 assert.match(target,/^\/unova\/areas\?busca=Nuvema\+Town&fase=U07/);
 const q=new URLSearchParams(target.split('?')[1]);
 const result=listed('areas',q);
 assert.equal(result.count,1);
 assert.equal(result.items[0].key,'UNOVA_NUVEMA_TOWN');
});
test('URL-encoded ampersands are safely escaped in rendered input fields',()=>{
 const query='Bianca & Cheren';
 const target=unovaFilterUrl(guide,'npcs',{busca:query});
 assert.ok(target.includes('Bianca+%26+Cheren'));
 const out=html('npcs',new URLSearchParams(target.split('?')[1]));
 assert.ok(out.includes('value="Bianca &amp; Cheren"'));
});
test('unrecognized query parameters cannot influence filters',()=>{
 const url=new URLSearchParams('busca=Nuvema&map_id=518&installed=true&playable=true');
 assert.equal(listed('areas',url).count,listed('areas',{busca:'Nuvema'}).count);
 assert.ok(!('installed' in listed('areas',url).filters));
});
test('unknown filter value falls back to todos and cannot invent content',()=>{
 const all=full('areas');
 for(const field of ['fase','capitulo','tipo','pendencia','area']){
  assert.equal(listed('areas',{[field]:'UNOVA_FAKE_NATIVE'}).count,all.count);
  assert.equal(listed('areas',{[field]:'UNOVA_FAKE_NATIVE'}).filters[field],'todos');
 }
});
test('unexpected query/HTML input is properly escaped',()=>{
 const q='<img src=x onerror=alert(1)>';
 const out=html('areas',{busca:q});
 assert.doesNotMatch(out,/<img src=x onerror=/);
 assert.match(out,/&lt;img src=x onerror=alert\(1\)&gt;/);
});
test('search term capped at 100 code units and dangerous control keys ignored',()=>{
 const term='z'.repeat(10000);
 const f=sanitizeUnovaFilters(guide,'areas',{busca:term});
 assert.equal(f.busca.length,100);
 assert.equal(f.fase,'todos');
 assert.equal(f.area,'todos');
});
test('search does not mutate source catalog or write native state',()=>{
 const initial=structuredClone(guide);
 for(const tab of UNOVA_FILTER_TABS){
  listed(tab,{busca:'Nuvema',pendencia:'mapas',fase:'U07',capitulo:'UNOVA_CH01_NUVEMA'});
  html(tab,{busca:'Nuvema'});
 }
 assert.deepEqual(guide,initial);
 assert.equal(guide.canPlay,false);
 assert.equal(guide.nativeMapIdsVerified,0);
});
test('unknown tab rejected rather than silently treating as real area',()=>{
 assert.throws(()=>listed('jogar',{busca:'Unova'}),/unova-filter-invalid-tab/);
 assert.throws(()=>unovaFilterUrl(guide,'native',{tipo:'area'}),/unova-filter-invalid-tab/);
});
test('filter labels restricted to audited fields and no numeric level/MapID options',()=>{
 const opts=unovaGuideOptions(guide,'treinadores');
 assert.ok(opts.tipos.includes('CHEREN'));
 assert.ok(opts.pendencias.includes('equipes'));
 assert.ok(!opts.pendencias.includes('level_50'));
 assert.ok(!opts.areas.includes('Map518'));
});
test('URL filters only recognized keys and defaults to canonical path',()=>{
 assert.equal(unovaFilterUrl(guide,'areas',{tipo:'FAKE',x:'518'}),'/unova/areas');
 assert.equal(unovaFilterUrl(guide,'missoes',{capitulo:'UNOVA_CH01_NUVEMA'}),
  '/unova/missoes?capitulo=UNOVA_CH01_NUVEMA');
});
test('all browse tab links, filters and result count are consistent with cards',()=>{
 for(const tab of UNOVA_FILTER_TABS){
  const result=full(tab);
  const out=html(tab);
  assert.match(out,new RegExp(result.count+' de '+result.total+' referências planejadas'));
  assert.match(out,/data-unova-filters/);
 }
});
test('code router forwards URLSearchParams, listens for form submit, and preserves SPA navigation',async()=>{
 const app=await readFile(path.join(root,'site/src/assets/app.js'),'utf8');
 assert.match(app,/unovaGuidePage\(guide,guideSection,ref,url.searchParams\)/);
 assert.match(app,/form\[data-unova-filters\]/);
 assert.match(app,/new URLSearchParams\(new FormData\(unovaForm\)\)/);
 assert.match(app,/navigate\(destination\)/);
});
for(const [name,change] of Object.entries({
  missionNativeEvent:d=>d.missions[0].nativeEventId=300,
  missionNativeMap:d=>d.missions[0].nativeMapId=518,
  missionInstalled:d=>d.missions[0].installed=true,
  missionUnknownChapter:d=>d.missions[0].chapterKey='UNOVA_FAKE_CHAPTER',
  missionUnknownArea:d=>d.missions[0].areaKey='UNOVA_MAP_518',
  missionSourceSpoof:d=>d.missions[0].sourcePath='game/Map518.rxdata',
  duplicateMission:d=>d.missions[1].key=d.missions[0].key,
  removeMission:d=>d.missions.pop(),
  fakeAreaMap:d=>d.areas[0].nativeMapId=518,
  fakeTrainerTeam:d=>d.trainers[0].team=['FAKE'],
  fakeGymLevel:d=>d.gyms[0].levels=[25],
  fakeNPCEvent:d=>d.npcs[0].installed=true,
  nativeGameplay:d=>d.canPlay=true,
  nativeQA:d=>d.gameExeTested=true,
  nativeMapCount:d=>d.nativeMapIdsVerified=1,
  nativeEncounterCount:d=>d.nativeEncounterRatesVerified=1
})){
 test('fail-closed tamper '+name,()=>{
  const d=structuredClone(guide);change(d);
  assert.throws(()=>validateUnovaGuide(d),/unova-guide-invalid/);
  assert.throws(()=>unovaGuidePage(d,'areas',null,{busca:'Nuvema'}),/unova-guide-invalid/);
 });
}
test('generated corpus has no novel numeric native level, MapID or team data',()=>{
 assert.ok(guide.areas.every(x=>x.nativeMapId===null&&x.verifiedLevels===null));
 assert.ok(guide.missions.every(x=>x.nativeMapId===null&&x.nativeEventId===null));
 assert.ok(guide.trainers.every(x=>x.levels===null&&x.team===null));
 assert.ok(guide.gyms.every(x=>x.levels===null&&x.team===null));
 assert.equal(guide.canInstall,false);
});
