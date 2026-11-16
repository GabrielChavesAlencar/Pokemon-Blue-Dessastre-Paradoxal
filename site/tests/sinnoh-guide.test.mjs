// CH17 — source-grounded site guide, negative proof/level/MapID/route tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateSinnohGuide,sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {sinnohGuidePage,loadSinnohGuide} from '../src/assets/sinnoh-guide.js';
import {regionsPage,regionPicker} from '../src/assets/regions.js';
import {guides} from '../src/assets/views.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const sources=()=>Object.fromEntries(Object.entries(sinnohSourcePaths).map(
  ([key,relative])=>[key,JSON.parse(readFileSync(path.join(root,relative),'utf8'))]));
const copy=()=>structuredClone(sources());
const value=generateSinnohGuide(sources());
const reject=(obj,needle=/sinnoh-guide-invalid/)=>assert.throws(()=>generateSinnohGuide(obj),needle);

test('CH17 120 areas: 91 phase-scoped + 29 with unknown phase, never fabricated',()=>{
  assert.equal(value.status,'planned');
  assert.equal(value.canPlay,false);
  assert.equal(value.counts.areas,120);
  assert.equal(value.areas.filter(x=>x.phase!==null).length,91);
  assert.equal(value.areas.filter(x=>x.phase===null).length,29);
  assert.deepEqual(value.phases.map(x=>x.number),[3,4,5,6,7,8,9,10]);
  assert.equal(value.counts.verifiedNativeMaps,0);
  assert.ok(value.areas.every(x=>x.status==='planned'&&x.confirmedWildEncounters===0));
  assert.ok(value.areas.every(x=>!('map_id' in x)&&!('mapId' in x)&&
    !('level' in x)&&!('rate' in x)));
});

test('CH17 40 uninstalled trainer references, eight gyms, Elite and Cynthia',()=>{
  assert.equal(value.counts.trainers,40);
  assert.equal(value.trainers.filter(x=>x.teamInstalled).length,0);
  assert.equal(value.bosses.filter(x=>x.role==='GYM_LEADER').length,8);
  assert.equal(value.bosses.filter(x=>x.role==='ELITE_FOUR').length,4);
  assert.equal(value.bosses.filter(x=>x.role==='CHAMPION').length,1);
  assert.equal(value.bosses.filter(x=>x.rematchSpeciesReference).length,5);
  assert.deepEqual(value.bosses.slice(0,4).map(x=>x.name),
    ['Roark','Gardenia','Fantina','Maylene']);
  assert.deepEqual(value.bosses.slice(0,4).map(x=>x.badge),
    ['COAL','FOREST','RELIC','COBBLE']);
  assert.ok(value.bosses.every(x=>!('level' in x)&&!('historical_levels' in x)&&
    !('trainerVersion' in x)&&x.pbsInstalled===false&&x.fullPowerVerified===false));
});

test('CH17 item badge map preserves regional HM contracts and no grant claims',()=>{
  assert.equal(value.items.length,8);
  assert.deepEqual(value.items.map(x=>x.badge),
    ['COAL','FOREST','COBBLE','RELIC','FEN','MINE','ICICLE','BEACON']);
  assert.equal(value.items.find(x=>x.id==='HM05').badge,'RELIC');
  assert.equal(value.items.find(x=>x.id==='HM03').fieldMove,'SURF');
  assert.ok(value.items.every(x=>x.status==='planned'&&!x.pickupVerified&&x.regionalOnly));
});

test('CH17 story 22 checkpoints, Hall of Fame independent and no unlocked portal',()=>{
  assert.equal(value.steps.length,22);
  assert.equal(value.steps.at(-1).id,'P09_HALL_OF_FAME');
  assert.equal(value.steps.at(-1).engineHallOfFameRequired,true);
  assert.ok(value.steps.every(x=>!x.eventInstalled&&x.status==='planned'));
  assert.ok(value.music.audioInstalled===false&&value.music.cueCount===46);
});

test('CH17 encounter species stay references without rates or levels',()=>{
  assert.equal(value.counts.encounterReferenceAreas,21);
  const route=value.areas.find(x=>x.referenceSymbol==='ROUTE_201');
  assert.deepEqual(route.speciesCandidates,['STARLY','BIDOOF']);
  assert.equal(route.confirmedWildEncounters,0);
  const ambiguous=value.areas.find(x=>x.name==='Route 212');
  assert.equal(ambiguous.phase,null);
  assert.equal(ambiguous.confirmedWildEncounters,0);
  const json=JSON.stringify(value);
  assert.doesNotMatch(json,/"(?:map_id|mapId|physical_map_id|historical_levels|weight_percentages|level_ranges)"\s*:/);
});

test('CH17 builds linkable landing with explicit not-playable warning',()=>{
  const html=sinnohGuidePage(value,'visao');
  assert.match(html,/Guia de Sinnoh/);
  assert.match(html,/NÃO JOGÁVEL/);
  assert.match(html,/Ainda não adicionado/);
  assert.match(html,/href="\/sinnoh\?aba=areas"/);
  assert.match(html,/href="\/sinnoh\?aba=itens"/);
  assert.match(html,/Normal 70% \/ Master 90%/);
  assert.doesNotMatch(html,/href="\/downloads\?regiao=sinnoh"/);
});

test('CH17 areas can be grouped by phase without inventing missing phase',()=>{
  const all=sinnohGuidePage(value,'areas','all');
  const first=sinnohGuidePage(value,'areas','3');
  const unknown=sinnohGuidePage(value,'areas','sem-fase');
  assert.equal((all.match(/class="sinnoh-guide-card"/g)||[]).length,120);
  assert.equal((first.match(/class="sinnoh-guide-card"/g)||[]).length,9);
  assert.equal((unknown.match(/class="sinnoh-guide-card"/g)||[]).length,29);
  assert.match(unknown,/Fase a auditar/);
  assert.match(first,/Route 201/);
  assert.doesNotMatch(first,/Route 225/);
  assert.equal(sinnohGuidePage(value,'areas','999'),all);
});

test('CH17 trainer and gym pages separate references from engine compiled roster',()=>{
  const trainers=sinnohGuidePage(value,'treinadores');
  assert.match(trainers,/Barry/);
  assert.match(trainers,/40/);
  assert.match(trainers,/Nenhuma equipe ou versão/);
  const gyms=sinnohGuidePage(value,'ginasios');
  assert.match(gyms,/Fantina/);
  assert.match(gyms,/Maylene/);
  assert.match(gyms,/Full Power do Blue: não verificado/);
  assert.match(gyms,/GEODUDE/);
  assert.doesNotMatch(gyms,/Nível 14/);
});

test('CH17 Elite Four and Cynthia have no level/tier/PBS false approvals',()=>{
  const league=sinnohGuidePage(value,'liga');
  for(const name of ['Aaron','Bertha','Flint','Lucian','Cynthia'])
    assert.match(league,new RegExp(name));
  assert.match(league,/Revanche histórica/);
  assert.match(league,/Equipe PBS e batalha nativa: pendentes/);
  assert.match(league,/Hall of Fame confirmado/);
  assert.doesNotMatch(league,/N[ií]vel \d+/);
  assert.doesNotMatch(league,/Time instalado/);
});

test('CH17 HM and story pages never display real unlock claims',()=>{
  const items=sinnohGuidePage(value,'itens');
  assert.match(items,/HM06/);
  assert.match(items,/HM05/);
  assert.match(items,/Entrega do HM: não confirmada/);
  const story=sinnohGuidePage(value,'progresso');
  assert.match(story,/22 checkpoints/);
  assert.match(story,/Pós-jogo/);
  assert.match(story,/Sem|Hall of Fame|Cyrus/);
  assert.match(story,/Viagem pós-Liga continua bloqueada/);
  assert.doesNotMatch(story,/Sua partida: concluída/);
});

test('CH17 navigation discoverable from regional map and guide list',()=>{
  const reg=regionsPage(sources().regions);
  assert.match(reg,/href="\/sinnoh">Guia planejado de Sinnoh/);
  assert.match(regionPicker('localizacoes','decades'),/regiao=sinnoh/);
  const landing=guides({guides:[{id:'stub',title:'Teste',excerpt:'Teste',category:'Teste',minutes:1,icon:'book',sections:[]}]});
  assert.match(landing,/href="\/sinnoh"/);
  assert.match(landing,/PLANEJADA/);
});

test('CH17 rendering escapes untrusted names, descriptions, species',()=>{
  const poisoned=structuredClone(value);
  poisoned.areas[0].name='<script>alert("x")</script>';
  poisoned.areas[0].speciesCandidates=['<img src=x>'];
  poisoned.bosses[0].name='<svg onload=x>';
  poisoned.items[0].label='<b>hack</b>';
  for(const [tab,fragment] of [['areas','&lt;script&gt;'],['ginasios','&lt;svg'],['itens','&lt;b&gt;']]){
    const html=sinnohGuidePage(poisoned,tab);
    assert.ok(html.includes(fragment),tab);
    assert.doesNotMatch(html,/<script>|<svg onload|<b>hack/);
  }
});

test('CH17 rejected source region statuses and fabricated installation',()=>{
  for(const edit of [
    s=>{s.regions.regions.SINNOH.status='playable';},
    s=>{s.coverage.status='READY';},
    s=>{s.coverage.integrity.verified_runtime_entries=1;},
    s=>{s.badges.approved_for_install=true;},
    s=>{s.badges.native_map_ids_assigned=true;},
    s=>{s.teams.gameplay_verified=true;},
    s=>{s.story.native_events_installed=true;},
    s=>{s.music.gameplay_verified=true;},
    s=>{s.music.recordings=['copyright.mp3'];},
    s=>{s.encounters.may_install=true;}
  ]){const d=copy();edit(d);reject(d);}
});

test('CH17 rejects invented MapIDs, levels, wild rates and award proofs',()=>{
  for(const edit of [
    s=>{s.coverage.phases[0].areas[0].source_map_ids=[800];},
    s=>{s.coverage.phases[0].events[0].verified=true;},
    s=>{s.pending.regions.SINNOH.areas[0].map_id=800;},
    s=>{s.pending.regions.SINNOH.areas[0].level=5;},
    s=>{s.pending.regions.SINNOH.trainers[0].level=20;},
    s=>{s.badges.rules[0].verified_hm_pickup_event=true;},
    s=>{s.badges.rules[0].verified_gym_event=true;},
    s=>{s.teams.trainers[0].native_pbs.compiled=true;},
    s=>{s.encounters.areas[0].map_id=800;},
    s=>{s.encounters.areas[0].encounter_slots=[{weight:100}];},
    s=>{s.encounters.areas[0].weight_percentages=[100];},
    s=>{s.story.steps[0].grants_item=true;},
    s=>{s.story.steps[0].native_event_installed=true;},
    s=>{s.music.cues[0].enabled=true;},
    s=>{s.music.cues[0].track_path='Sinnoh/Cynthia.mp3';}
  ]){const d=copy();edit(d);reject(d);}
});

test('CH17 rejects missing catalog or incomplete roster without guessing',()=>{
  for(const edit of [
    s=>{delete s.teams;},
    s=>{s.pending.regions.SINNOH.areas=[];},
    s=>{s.teams.trainers.pop();},
    s=>{s.story.steps.pop();},
    s=>{s.badges.rules.pop();},
    s=>{s.music.cues.pop();},
    s=>{s.encounters.areas.pop();},
    s=>{s.coverage.phases.pop();}
  ]){const d=copy();edit(d);reject(d);}
});

test('CH17 rejects duplicated source IDs, foreign badge or unsupported phase',()=>{
  const a=copy();a.pending.regions.SINNOH.areas[1].id=a.pending.regions.SINNOH.areas[0].id;reject(a,/duplicated/);
  const b=copy();b.pending.regions.SINNOH.trainers[1].id=b.pending.regions.SINNOH.trainers[0].id;reject(b,/duplicated/);
  const c=copy();c.badges.rules[0].badge='BOULDER';reject(c,/badge association/);
  const d=copy();d.pending.regions.SINNOH.areas[0].phase=999;reject(d,/unverified area/);
});

test('CH17 rendered data cannot be relabeled as gameplay',()=>{
  for(const edit of [
    x=>{x.status='playable';},
    x=>{x.canPlay=true;},
    x=>{x.gameplayVerified=true;}
  ]){const bad=structuredClone(value);edit(bad);
    assert.throws(()=>sinnohGuidePage(bad),/sinnoh-guide-invalid/);}
});

test('CH17 loader exposes generated build data only after schema validation',async()=>{
  const loaded=await loadSinnohGuide(async url=>({
    ok:url==='/data/sinnoh-guide.json',json:async()=>value
  }));
  assert.equal(loaded.counts.areas,120);
  assert.equal(loaded.gameplayVerified,false);
});

test('CH17 site build publishes valid generated JSON without static game files',()=>{
  const file=path.join(root,'site/dist/data/sinnoh-guide.json');
  assert.ok(existsSync(file),'run npm run build before node --test');
  const built=JSON.parse(readFileSync(file,'utf8'));
  assert.deepEqual(built,value);
  assert.equal(built.counts.verifiedNativeMaps,0);
});
