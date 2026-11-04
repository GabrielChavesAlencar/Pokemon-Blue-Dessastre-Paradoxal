import test from 'node:test';
import assert from 'node:assert/strict';
import {androidReleaseStatus,androidReleaseHtml} from '../src/assets/android-release.js';
const sha='a'.repeat(40),next='b'.repeat(40);
const release={tag_name:'build-1',target_commitish:sha,assets:[{name:'Blue-Android-JoiPlay.zip',state:'uploaded',size:1200000000}]};
const fetcher=(run,ok=true)=>async url=>({ok:url.includes('/releases/')?ok:true,json:async()=>url.includes('/releases/')?release:{workflow_runs:run?[run]:[]}});
test('Android mostra o pacote publicado e separa falha de release de deploy do portal',async()=>{
  const path='.github/workflows/battle-hub-release.yml';
  const current=await androidReleaseStatus(fetcher({path,head_sha:sha,status:'completed',conclusion:'success'}));
  assert.equal(current.state,'published');assert.ok(androidReleaseHtml(current).includes(sha));
  const failed=await androidReleaseStatus(fetcher({path,head_sha:next,status:'completed',conclusion:'failure'}));
  assert.equal(failed.state,'outdated');assert.match(androidReleaseHtml(failed),/Download desatualizado/);
  assert.equal((await androidReleaseStatus(fetcher({path,head_sha:next,status:'in_progress'}))).state,'building');
});
test('falha da API não inventa revisão e dados externos são escapados',async()=>{
  const unknown=await androidReleaseStatus(fetcher(null,false));assert.equal(unknown.state,'unavailable');
  assert.match(androidReleaseHtml(unknown),/Não foi possível/);
  const html=androidReleaseHtml({state:'published',tag:'<script>',revision:sha,bytes:1200000000});
  assert.ok(!html.includes('<script>'));assert.ok(html.includes('&lt;script&gt;'));
});
