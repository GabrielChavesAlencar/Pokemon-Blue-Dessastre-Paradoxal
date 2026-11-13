import test from 'node:test';
import assert from 'node:assert/strict';
import {androidReleaseStatus,androidReleaseHtml,androidPilotsHtml} from '../src/assets/android-release.js';
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

test('pilotos só têm link quando os ZIPs regionais existem de verdade',async()=>{
  const status=await androidReleaseStatus(fetcher({path:'.github/workflows/battle-hub-release.yml',head_sha:sha,status:'completed'}));
  assert.match(androidPilotsHtml(status),/Piloto Kanto · indisponível/);
  assert.match(androidPilotsHtml(status),/Piloto Johto · indisponível/);
  assert.doesNotMatch(androidPilotsHtml(status),/href=/);
  const releaseWithPilots={...release,assets:[...release.assets,
    {name:'Blue-Android-Kanto-Piloto.zip',state:'uploaded',size:3000},
    {name:'Blue-Android-Johto-Piloto.zip',state:'uploaded',size:4000}]};
  const api=async url=>({ok:true,json:async()=>url.includes('/releases/')?releaseWithPilots:{workflow_runs:[]}});
  const published=await androidReleaseStatus(api);
  const html=androidPilotsHtml(published);
  assert.match(html,/releases\/download\/build-1\/Blue-Android-Kanto-Piloto\.zip/);
  assert.match(html,/releases\/download\/build-1\/Blue-Android-Johto-Piloto\.zip/);
  assert.doesNotMatch(html,/indisponível/);
  assert.doesNotMatch(androidPilotsHtml({state:'unavailable'}),/href=/);
});
