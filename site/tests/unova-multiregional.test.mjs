import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {unovaGithubStats,unovaGithubProgressPage} from '../src/assets/unova-progress.js';
import {regionsPage} from '../src/assets/regions.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const read=async name=>JSON.parse(await readFile(path.join(root,name),'utf8'));
const matrix=await read('data/regions/unova-g08-multiregional-contract.json');
const reg=await read('site/public/data/regions.json');
const travel=await read('data/regions/unova-g05-travel-contract.json');
const blackout=await read('data/regions/unova-g05-blackout-state-contract.json');
const packageContract=await read('data/regions/unova-g07-incremental-contract.json');
const compat=await read('data/regions/unova-g07-platform-compatibility-contract.json');
const progress=await read('site/public/data/unova-github-progress.json');

test('G08.3 matrix has exactly six grounded region identities',()=>{
 assert.deepEqual(matrix.regional_profiles.map(x=>x.id),
  ['DECADES','KANTO','JOHTO','HOENN','SINNOH','UNOVA']);
 assert.deepEqual(matrix.regional_profiles.map(x=>x.registry_status),
  matrix.regional_profiles.map(x=>reg.regions[x.id].status));
});
test('G05.3 native runtime allowlist is not equivalent to publicly installed',()=>{
 assert.deepEqual(travel.routable_runtime_regions,
  ['DECADES','KANTO','JOHTO','HOENN']);
 assert.equal(reg.regions.JOHTO.status,'planned');
 assert.equal(reg.regions.HOENN.status,'planned');
 assert.ok(matrix.regional_profiles.every(x=>x.native_qa_from_this_suite===false));
});
test('Sinnoh and Unova are never promoted by G08.3',()=>{
 assert.deepEqual(matrix.blocked_native_destinations,['SINNOH','UNOVA']);
 assert.equal(reg.regions.SINNOH.status,'planned');
 assert.equal(reg.regions.UNOVA.status,'planned');
 assert.equal(matrix.runtime_evidence.unova_installed,null);
 assert.equal(matrix.runtime_evidence.sinnoh_installed,null);
});
test('travel regression includes a four-hop fixture roundtrip',()=>{
 assert.deepEqual(matrix.allowed_fixture_route,
  ['KANTO','HOENN','JOHTO','DECADES','KANTO']);
 assert.equal(matrix.policy.routable_fixture_never_implies_native_installed,true);
});
test('all five travel, four blackout, seven package failure points retained',()=>{
 assert.equal(matrix.failure_points.travel.length,5);
 assert.equal(matrix.failure_points.blackout.length,4);
 assert.equal(matrix.failure_points.package.length,7);
 assert.equal(new Set(matrix.failure_points.travel).size,5);
 assert.equal(new Set(matrix.failure_points.blackout).size,4);
 assert.equal(new Set(matrix.failure_points.package).size,7);
});
test('state isolation rules include all real-world risks without inventing QA',()=>{
 for(const name of ['regional_HMs','regional_key_items','shared_TMs','badge_achievements',
  'Pokemon_party_and_Boxes','gameplay_progress','center_ownership',
  'money','coins','mechanics','save_snapshot_integrity','CAS_and_rollback']){
  assert.ok(matrix.covered_resources.includes(name),name);
 }
 assert.equal(matrix.can_install,false);
 assert.equal(matrix.can_read_user_saves,false);
 assert.equal(matrix.can_execute_real_travel,false);
 assert.equal(matrix.release_allowed,false);
});
test('Windows/Android continue blocked without verified sources',()=>{
 assert.equal(packageContract.can_install,false);
 assert.equal(compat.can_install,false);
 assert.equal(compat.platforms.windows.native_patch_supported,false);
 assert.equal(compat.platforms.android.native_patch_supported,false);
 assert.equal(blackout.native_center_installed,false);
});
test('G completion never changes technical/playability bars',()=>{
 const stats=unovaGithubStats(progress);
 assert.ok(stats.completed===31||stats.completed===32); // becomes 32 after successful CI
 assert.equal(progress.native_technical_bar.completed,0);
 assert.equal(progress.native_playable_bar.completed,0);
 assert.equal(progress.status,'PLANNED_NOT_NATIVE_PLAYABLE');
 assert.equal(reg.regions.UNOVA.status,'planned');
});
test('final progress remains explicitly non-playable when 100% GitHub',()=>{
 const clone=structuredClone(progress);
 const t=clone.groups.find(g=>g.id==='G08').tasks.find(t=>t.id==='G08.3');
 t.status='done';
 t.evidence='scripts/regions/audit_unova_g08_multiregional.py';
 assert.equal(unovaGithubStats(clone).completed,32);
 const html=unovaGithubProgressPage(clone);
 assert.match(html,/100% concluído/);
 assert.match(html,/0 tarefas restantes/);
 assert.match(html,/Unova continua não jogável/);
 assert.match(html,/Barra A técnica: 0\/8/);
 assert.match(html,/Unova jogável: 0\/32/);
 assert.doesNotMatch(html,/UNOVA INSTALADA|Unova pronta para jogar/i);
});
test('native progress, game claims and incomplete evidence are rejected',()=>{
 for(const mutate of [
  b=>{b.native_playable_bar.completed=1;},
  b=>{b.native_technical_bar.completed=8;},
  b=>{b.status='PLAYABLE';},
  b=>{delete b.groups.find(g=>g.id==='G08').tasks[2].evidence;
       b.groups.find(g=>g.id==='G08').tasks[2].status='done';}
 ]){
  const b=structuredClone(progress);mutate(b);
  assert.throws(()=>unovaGithubStats(b),/unova-progress-(?:native-status-false|task-invalid)/);
 }
});
test('site regional overview maintains planned Unova/Sinnoh and prototype Kanto',()=>{
 const page=regionsPage(reg);
 assert.match(page,/Unova/);
 assert.match(page,/Sinnoh/);
 assert.match(page,/Kanto/);
 assert.match(page,/Ver progresso GitHub de Unova/);
});
