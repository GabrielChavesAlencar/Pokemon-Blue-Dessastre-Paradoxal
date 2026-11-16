// CH18: browser-independent query tests plus negative claims about native gameplay.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generateSinnohGuide,sinnohSourcePaths} from '../scripts/sinnoh-guide.mjs';
import {sinnohGuidePage,loadSinnohGuide} from '../src/assets/sinnoh-guide.js';
import {validateSinnohGuide,filterSinnohGuide,sinnohGuideUrl,
        sinnohPendingGroups,normalizeSinnohText} from '../src/assets/sinnoh-search.js';
import {pendingPage} from '../src/assets/pending.js';
import {regionsPage} from '../src/assets/regions.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const load=()=>Object.fromEntries(Object.entries(sinnohSourcePaths)
  .map(([k,p])=>[k,JSON.parse(readFileSync(path.join(root,p),'utf8'))]));
const source=load();
const guide=generateSinnohGuide(source);
const altered=()=>structuredClone(guide);
const failChange=fn=>{
  const bad=altered();fn(bad);
  assert.throws(()=>validateSinnohGuide(bad),/sinnoh-guide-invalid/);
  assert.throws(()=>filterSinnohGuide(bad,'areas',{}),/sinnoh-guide-invalid/);
  assert.throws(()=>sinnohGuidePage(bad,'areas'),/sinnoh-guide-invalid/);
};

test('CH18 validates baseline planned, 120 areas and 40 trainers without playable claims',()=>{
  assert.equal(validateSinnohGuide(guide),guide);
  assert.equal(guide.counts.areas,120);
  assert.equal(guide.counts.trainers,40);
  assert.equal(guide.counts.verifiedNativeMaps,0);
  assert.equal(guide.counts.verifiedNativeItems,0);
});
test('CH18 accent and Portuguese route aliases search consistently',()=>{
  assert.equal(normalizeSinnohText('  RoTa  201 '),'route 201');
  assert.equal(normalizeSinnohText('  Insígnia  RELIC  '),'insignia relic');
  const a=filterSinnohGuide(guide,'areas',{busca:'rota 201'});
  const b=filterSinnohGuide(guide,'areas',{busca:'Route 201'});
  assert.deepEqual(a.items.map(x=>x.id),b.items.map(x=>x.id));
  assert.ok(a.items.some(x=>x.name==='Route 201'));
});
test('CH18 combines area search with a real documented phase',()=>{
  const a=filterSinnohGuide(guide,'areas',{busca:'Route 201',fase:'3'});
  assert.equal(a.count,1);
  assert.equal(a.items[0].name,'Route 201');
  const b=filterSinnohGuide(guide,'areas',{busca:'Route 201',fase:'9'});
  assert.equal(b.count,0);
  assert.equal(b.noResults,true);
  const c=filterSinnohGuide(guide,'areas',{fase:'999'});
  assert.equal(c.count,120);
  assert.equal(c.fase,'all');
});
test('CH18 preserves 91 documented phases and 29 unresolved phases',()=>{
  assert.equal(filterSinnohGuide(guide,'areas',{fase:'sem-fase'}).count,29);
  assert.equal(filterSinnohGuide(guide,'areas',{pendencia:'sem-fase'}).count,29);
  const known=guide.phases.reduce((n,p)=>
    n+filterSinnohGuide(guide,'areas',{fase:String(p.number)}).count,0);
  assert.equal(known,91);
  assert.equal(guide.areas.length,known+29);
});
test('CH18 filters areas by source-only species candidates, not playable encounters',()=>{
  const withReferences=filterSinnohGuide(guide,'areas',{pendencia:'com-especies'});
  const without=filterSinnohGuide(guide,'areas',{pendencia:'sem-especies'});
  assert.ok(withReferences.count>0);
  assert.ok(without.count>0);
  assert.equal(withReferences.count+without.count,120);
  assert.ok(withReferences.items.every(x=>x.speciesCandidates.length>0&&x.confirmedWildEncounters===0));
  assert.equal(filterSinnohGuide(guide,'areas',{busca:'STARLY'}).items
    .some(x=>x.name==='Route 201'),true);
});
test('CH18 searches trainer names and areas with no fake teams or PBS',()=>{
  const r=filterSinnohGuide(guide,'treinadores',{busca:'Barry'});
  assert.ok(r.count>0);
  assert.ok(r.items.some(x=>x.name.includes('Barry')));
  assert.ok(r.items.every(x=>x.status==='planned'&&x.teamInstalled===false));
  const c=filterSinnohGuide(guide,'treinadores',{busca:'Galactic'});
  assert.ok(c.count>0);
  assert.ok(c.items.every(x=>x.teamInstalled===false));
});
test('CH18 trainers area-reference filters partition all 40 entries',()=>{
  const a=filterSinnohGuide(guide,'treinadores',{pendencia:'com-area'});
  const b=filterSinnohGuide(guide,'treinadores',{pendencia:'sem-area'});
  assert.equal(a.count+b.count,40);
  assert.ok(a.items.every(x=>!!x.area));
  assert.ok(b.items.every(x=>!x.area));
});
test('CH18 filter gym by historical badge, species and trainer name',()=>{
  for(const word of ['RELIC','Fantina','MISMAGIUS']){
    const result=filterSinnohGuide(guide,'ginasios',{busca:word});
    assert.equal(result.count,1,word);
    assert.equal(result.items[0].name,'Fantina');
    assert.equal(result.items[0].pbsInstalled,false);
  }
  assert.equal(filterSinnohGuide(guide,'ginasios',{busca:'NONEXISTENT'}).count,0);
});
test('CH18 Elite and Cynthia historical rematches are not Blue Full Power',()=>{
  const all=filterSinnohGuide(guide,'liga');
  const withRematch=filterSinnohGuide(guide,'liga',{pendencia:'com-revanche'});
  const without=filterSinnohGuide(guide,'liga',{pendencia:'sem-revanche'});
  assert.equal(all.count,5);
  assert.equal(withRematch.count+without.count,all.count);
  assert.ok(withRematch.items.every(x=>!x.fullPowerVerified&&!x.pbsInstalled));
  assert.equal(filterSinnohGuide(guide,'liga',{busca:'Cynthia'}).count,1);
});
test('CH18 HM lookup uses original badge associations',()=>{
  const byBadge=filterSinnohGuide(guide,'itens',{busca:'RELIC'});
  assert.equal(byBadge.count,1);
  assert.equal(byBadge.items[0].id,'HM05');
  const byMove=filterSinnohGuide(guide,'itens',{busca:'ROCK SMASH'});
  assert.equal(byMove.count,1);
  assert.equal(byMove.items[0].badge,'COAL');
  assert.ok(filterSinnohGuide(guide,'itens',{pendencia:'sem-coleta'}).items
    .every(x=>!x.pickupVerified&&x.regionalOnly));
});
test('CH18 story search respects 22 uninstalled checkpoints',()=>{
  const galactic=filterSinnohGuide(guide,'progresso',{busca:'GALACTIC'});
  assert.ok(galactic.count>0);
  assert.ok(galactic.items.every(x=>x.status==='planned'&&!x.eventInstalled));
  const hof=filterSinnohGuide(guide,'progresso',{busca:'HALL OF FAME'});
  assert.equal(hof.count,1);
  assert.equal(hof.items[0].engineHallOfFameRequired,true);
});
test('CH18 pending categories are grounded in source counts',()=>{
  const rows=sinnohPendingGroups(guide);
  assert.deepEqual(rows.map(x=>x.key),['areas','treinadores','equipes','itens','historia','encontros','musica']);
  assert.deepEqual(rows.map(x=>x.count),[120,40,13,8,22,21,46]);
  assert.ok(rows.every(x=>x.description&&!x.description.includes('jogável')));
  assert.equal(filterSinnohGuide(guide,'pendencias',{tipo:'musica'}).count,1);
  assert.equal(filterSinnohGuide(guide,'pendencias',{tipo:'areas'}).items[0].count,120);
});
test('CH18 pending search and type filters can combine without inventing statuses',()=>{
  const result=filterSinnohGuide(guide,'pendencias',{busca:'PBS'});
  assert.ok(result.count>0);
  assert.equal(filterSinnohGuide(guide,'pendencias',{busca:'musicais',tipo:'musica'}).count,1);
  assert.equal(filterSinnohGuide(guide,'pendencias',{busca:'PBS',tipo:'musica'}).count,0);
});
test('CH18 bad tab, phase, pending type and category fail to safe defaults',()=>{
  const r=filterSinnohGuide(guide,'javascript:alert(1)',{pendencia:'playable',tipo:'fake',fase:'999'});
  assert.equal(r.tab,'visao');
  assert.equal(r.count,0);
  const a=filterSinnohGuide(guide,'areas',{pendencia:'native_approved',fase:'800'});
  assert.equal(a.count,120);
  assert.equal(a.pendencia,'todas');
  assert.equal(a.fase,'all');
  assert.equal(filterSinnohGuide(guide,'pendencias',{tipo:'installed'}).count,7);
});
test('CH18 only documented route and query keys are encoded into contextual links',()=>{
  const href=sinnohGuideUrl('areas',{busca:'Rota 201 & <svg>',fase:'3',mystery:'javascript:alert(1)'});
  const url=new URL(href,'https://portal.invalid');
  assert.equal(url.pathname,'/sinnoh');
  assert.equal(url.searchParams.get('aba'),'areas');
  assert.equal(url.searchParams.get('fase'),'3');
  assert.equal(url.searchParams.get('busca'),'Rota 201 & <svg>');
  assert.equal(url.searchParams.has('mystery'),false);
  assert.equal(sinnohGuideUrl('javascript:alert(1)'),'/sinnoh?aba=visao');
});
test('CH18 input and URLs cap search length and preserve encoded markup',()=>{
  const long='<script>alert(1)</script>'.repeat(30);
  const a=filterSinnohGuide(guide,'areas',{busca:long});
  assert.ok(a.busca.length<=100);
  const rendered=sinnohGuidePage(guide,'areas','all',{busca:long});
  assert.doesNotMatch(rendered,/<script>/);
  assert.match(rendered,/&lt;script&gt;/);
  assert.ok(new URL(sinnohGuideUrl('areas',{busca:long}),'https://portal.invalid')
    .searchParams.get('busca').length<=100);
});
test('CH18 forms include actual GET submit, searchable input and scope',()=>{
  const html=sinnohGuidePage(guide,'areas','3',{busca:'Starly',pendencia:'com-especies'});
  assert.match(html,/data-sinnoh-filters/);
  assert.match(html,/method="get" action="\/sinnoh"/);
  assert.match(html,/type="search" name="busca"/);
  assert.match(html,/name="fase" value="3"/);
  assert.match(html,/name="pendencia"/);
  assert.match(html,/type="submit"/);
  assert.match(html,/value="Starly"/);
});
test('CH18 visible pending badges survive all filtered areas and trainers',()=>{
  const html=sinnohGuidePage(guide,'areas','3',{busca:'Route 201'});
  assert.equal((html.match(/class="sinnoh-guide-card"/g)||[]).length,1);
  assert.match(html,/Ainda não adicionado/);
  assert.match(html,/1 referência exibida/);
  const t=sinnohGuidePage(guide,'treinadores','all',{busca:'Barry'});
  assert.match(t,/Ainda não adicionado/);
  assert.match(t,/Team|Treinadores a localizar/);
});
test('CH18 no-results state is explanatory, never fabricated',()=>{
  for(const tab of ['areas','treinadores','ginasios','liga','itens','progresso','pendencias']){
    const html=sinnohGuidePage(guide,tab,'all',{busca:'zxzxzx_NONE'});
    assert.match(html,/Nenhuma referência encontrada/,tab);
    assert.match(html,/não jogáveis/,tab);
    assert.match(html,/PLANEJADA · NÃO JOGÁVEL/,tab);
    assert.doesNotMatch(html,/Pokémon encontrado em 100%/);
  }
});
test('CH18 phase links retain search/filter values without authorizing playback',()=>{
  const html=sinnohGuidePage(guide,'areas','3',{busca:'rota 201',pendencia:'com-especies'});
  assert.match(html,/href="\/sinnoh\?aba=areas&amp;fase=4&amp;busca=rota\+201&amp;pendencia=com-especies"/);
  assert.match(html,/Nenhuma faixa|Ainda não adicionado/);
});
test('CH18 contextual links connect areas, trainers, gym/HM, Elite and story',()=>{
  const area=sinnohGuidePage(guide,'areas','3',{busca:'Route 201'});
  assert.match(area,/href="\/sinnoh\?aba=treinadores"/);
  assert.match(area,/tipo=areas/);
  const trainer=sinnohGuidePage(guide,'treinadores','all',{busca:'Barry'});
  assert.match(trainer,/href="\/sinnoh\?aba=areas"/);
  const gym=sinnohGuidePage(guide,'ginasios','all',{busca:'Fantina'});
  assert.match(gym,/aba=itens&amp;busca=RELIC/);
  const item=sinnohGuidePage(guide,'itens','all',{busca:'HM05'});
  assert.match(item,/aba=ginasios&amp;busca=RELIC/);
  const league=sinnohGuidePage(guide,'liga','all',{busca:'Cynthia'});
  assert.match(league,/aba=progresso/);
  const story=sinnohGuidePage(guide,'progresso');
  assert.match(story,/aba=areas&amp;fase=9/);
});
test('CH18 backlog has guide link and regions remain planned',()=>{
  const html=pendingPage(source.pending,'SINNOH');
  assert.match(html,/href="\/sinnoh\?aba=pendencias"/);
  const page=regionsPage(source.regions);
  assert.match(page,/href="\/sinnoh">Guia planejado de Sinnoh/);
  assert.match(page,/Planejada<\/span><h2>Sinnoh/);
});
test('CH18 categories render only documentary counts with pending status',()=>{
  const html=sinnohGuidePage(guide,'pendencias','all',{tipo:'encontros'});
  assert.match(html,/21 registros de referência em auditoria/);
  assert.match(html,/taxas, níveis ou slots/);
  assert.match(html,/Ainda não adicionado/);
  assert.doesNotMatch(html,/Instalado e jogável/);
});
test('CH18 nested false claims: areas/teams/items/story cannot become playable',()=>{
  for(const mutate of [
    x=>{x.status='playable';},x=>{x.canPlay=true;},
    x=>{x.gameplayVerified=true;},x=>{x.counts.verifiedNativeMaps=1;},
    x=>{x.areas[0].status='playable';},
    x=>{x.areas[0].installed=true;},
    x=>{x.areas[0].confirmedWildEncounters=2;},
    x=>{x.trainers[0].teamInstalled=true;},
    x=>{x.bosses[0].pbsInstalled=true;},
    x=>{x.bosses[0].fullPowerVerified=true;},
    x=>{x.items[0].pickupVerified=true;},
    x=>{x.items[0].regionalOnly=false;},
    x=>{x.steps[0].eventInstalled=true;},
    x=>{x.music.audioInstalled=true;}
  ])failChange(mutate);
});
test('CH18 fake MapIDs, levels and encounter rates are refused at UI boundary',()=>{
  for(const mutate of [
    x=>{x.areas[0].map_id=800;},
    x=>{x.areas[0].level=20;},
    x=>{x.areas[0].rate=50;},
    x=>{x.areas[0].weight_percentages=[100];},
    x=>{x.trainers[0].trainerVersion=1;},
    x=>{x.bosses[0].historical_levels=[10,12];},
    x=>{x.bosses[0].level=40;},
    x=>{x.steps[0].mapId=800;},
    x=>{x.items[0].physical_map_id=300;}
  ])failChange(mutate);
});
test('CH18 catalog corruption, missing records and wrong scaling do not render',()=>{
  for(const mutate of [
    x=>{x.schema=2;},x=>{x.region='KANTO';},
    x=>{x.areas=[];},x=>{x.bosses.pop();},
    x=>{x.trainers.pop();},x=>{x.phases.pop();},
    x=>{x.steps.pop();},x=>{x.items.pop();},
    x=>{x.balance.normalPercent=100;},
    x=>{x.balance.masterPercent=100;},
    x=>{x.counts.trainers=999;},
    x=>{x.music.cueCount=48;},
    x=>{x.phases[0].status='playable';}
  ])failChange(mutate);
});
test('CH18 duplicate public IDs or bad status are blocked',()=>{
  for(const mutate of [
    x=>{x.areas[1].id=x.areas[0].id;},
    x=>{x.bosses[1].id=x.bosses[0].id;},
    x=>{x.items[1].id=x.items[0].id;},
    x=>{x.steps[1].id=x.steps[0].id;},
    x=>{x.trainers[1].id=x.trainers[0].id;},
    x=>{x.trainers[0].status='native_qa_pending';},
    x=>{x.areas[0].phase=800;}
  ])failChange(mutate);
});
test('CH18 generated portal artifact equals audited source when build is run',()=>{
  const file=path.join(root,'site/dist/data/sinnoh-guide.json');
  assert.ok(existsSync(file),'site build must run before tests');
  const built=JSON.parse(readFileSync(file,'utf8'));
  assert.deepEqual(built,guide);
  assert.equal(filterSinnohGuide(built,'pendencias').count,7);
});
test('CH18 app owns GET SPA navigation and does not claim Sinnoh download',()=>{
  const app=readFileSync(path.join(root,'site/src/assets/app.js'),'utf8');
  assert.match(app,/data-sinnoh-filters/);
  assert.match(app,/new FormData\(form\)/);
  assert.match(app,/navigate\('\/sinnoh\?'/);
  assert.match(app,/sinnohSearchOptions\(url\)/);
  assert.doesNotMatch(app,/sinnohGuide.*Game.exe.*instalado/);
});
