import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {loadUnovaGithubProgress,unovaGithubStats,unovaGithubProgressPage} from '../src/assets/unova-progress.js';
import {regionsPage} from '../src/assets/regions.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const readJson=async p=>JSON.parse(await readFile(path.join(root,p),'utf8'));
const board=await readJson('public/data/unova-github-progress.json');
const registry=await readJson('public/data/regions.json');

test('Unova GitHub-only board has exactly 32 tasks in eight complete G01-G08 blocks',()=>{
  const stats=unovaGithubStats(board);
  assert.equal(stats.total,32);
  assert.equal(stats.groups.length,8);
  assert.deepEqual(stats.groups.map(g=>g.id),['G01','G02','G03','G04','G05','G06','G07','G08']);
  assert.equal(stats.groups.every(g=>g.tasks.length===4),true);
  const actualIds=stats.groups.flatMap(g=>g.tasks.map(t=>t.id));
  assert.deepEqual(actualIds,['G01','G02','G03','G04','G05','G06','G07','G08'].flatMap(g=>[1,2,3,4].map(i=>g+'.'+i)));
});
test('documented baseline milestones are nineteen done and 13 pending, never playable',()=>{
  const stats=unovaGithubStats(board);
  assert.equal(stats.completed,19);
  assert.equal(stats.remaining,13);
  assert.equal(stats.percent,59);
  assert.equal(stats.inProgress,0);
  assert.equal(board.status,'PLANNED_NOT_NATIVE_PLAYABLE');
  assert.equal(board.native_technical_bar.completed,0);
  assert.equal(board.native_playable_bar.completed,0);
  assert.equal(registry.regions.UNOVA.status,'planned');
  assert.equal(board.groups.flatMap(x=>x.tasks).filter(x=>x.status==='done').length,19);
});
test('completed milestones have real evidence source files in the repo',async()=>{
  const complete=board.groups.flatMap(x=>x.tasks).filter(x=>x.status==='done');
  for(const task of complete){
    assert.match(task.evidence,/^(?:site\/|data\/|scripts\/|docs\/|tests\/)/);
    const source=path.resolve(root,'..',task.evidence);
    assert.ok(source.startsWith(path.resolve(root,'..')+path.sep),task.id);
    await access(source);
  }
});
test('Unova progress renders meaningful accessible total and group bars',()=>{
  const html=unovaGithubProgressPage(board);
  assert.match(html,/<h1>Progresso das tarefas de Unova<\/h1>/);
  assert.match(html,/19\/32/);
  assert.match(html,/59% concluído/);
  assert.match(html,/13 tarefas restantes/);
  assert.equal((html.match(/<progress\b/g)||[]).length,9);
  assert.match(html,/max="32"/);
  assert.match(html,/value="19"/);
  assert.match(html,/aria-label="Desenvolvimento GitHub:/);
  assert.match(html,/G01/);
  assert.match(html,/G08/);
  assert.match(html,/Barra A técnica: 0\/8/);
  assert.match(html,/Unova jogável: 0\/32/);
  assert.match(html,/não jogável/);
});
test('no completed state can be faked without evidence',()=>{
  const injected=structuredClone(board);
  const target=injected.groups[0].tasks[0];
  target.status='done';
  delete target.evidence;
  assert.throws(()=>unovaGithubStats(injected),/unova-progress-task-invalid/);
});
test('cannot falsely promote Unova native or gameplay technical bars',()=>{
  for(const tamper of [
    b=>{b.native_technical_bar.completed=1;},
    b=>{b.native_playable_bar.completed=1;},
    b=>{b.status='PLAYABLE';},
  ]){
    const changed=structuredClone(board);
    tamper(changed);
    assert.throws(()=>unovaGithubStats(changed),/unova-progress-native-status-false/);
  }
});
test('duplicate task IDs and missing tasks fail closed',()=>{
  const duplicate=structuredClone(board);
  duplicate.groups[1].tasks[1].id='G02.1';
  assert.throws(()=>unovaGithubStats(duplicate),/unova-progress-task-invalid/);
  const truncated=structuredClone(board);
  truncated.groups[4].tasks.pop();
  assert.throws(()=>unovaGithubStats(truncated),/unova-progress-group-invalid/);
});
test('content and acceptance are HTML escaped to protect site from injection',()=>{
  const injected=structuredClone(board);
  injected.groups[0].tasks[0].title='<img src=x onerror=alert(1)>';
  injected.groups[0].tasks[0].acceptance='<script>unsafe</script>';
  const html=unovaGithubProgressPage(injected);
  assert.doesNotMatch(html,/<script>unsafe|<img src=x/);
  assert.match(html,/&lt;script&gt;unsafe/);
  assert.match(html,/&lt;img src=x/);
});
test('Unova appears in the circuit of regions as an informational progress link',()=>{
  const html=regionsPage(registry);
  assert.match(html,/href="\/unova-progresso"/);
  assert.match(html,/Ver progresso GitHub de Unova/);
  assert.match(html,/Planejada<\/span><h2>Unova<\/h2>/);
});
test('loader accepts matching public JSON and rejects unavailable endpoint',async()=>{
  let requests=[];
  const result=await loadUnovaGithubProgress(async url=>{
    requests.push(url);
    return {ok:url==='/data/unova-github-progress.json',json:async()=>board};
  });
  assert.deepEqual(requests,['/data/unova-github-progress.json']);
  assert.equal(unovaGithubStats(result).completed,19);
  await assert.rejects(()=>loadUnovaGithubProgress(async()=>({ok:false})),/unova-progress-unavailable/);
});
