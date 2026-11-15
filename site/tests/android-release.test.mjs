import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {androidReleaseStatus,androidReleaseHtml,androidPilotsHtml,regionalAndroidReleases} from '../src/assets/android-release.js';
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
  assert.match(androidPilotsHtml(status),/href="\/data\/pilotos\/johto-android\.txt" download/);
  assert.doesNotMatch(androidPilotsHtml(status),/\/releases\/download\//);
  const releaseWithPilots={...release,assets:[...release.assets,
    {name:'Blue-Android-Kanto-Piloto.zip',state:'uploaded',size:3000},
    {name:'Blue-Android-Johto-Piloto.zip',state:'uploaded',size:4000}]};
  const api=async url=>({ok:true,json:async()=>url.includes('/releases/')?releaseWithPilots:{workflow_runs:[]}});
  const published=await androidReleaseStatus(api);
  const html=androidPilotsHtml(published);
  assert.match(html,/releases\/download\/build-1\/Blue-Android-Kanto-Piloto\.zip/);
  assert.match(html,/releases\/download\/build-1\/Blue-Android-Johto-Piloto\.zip/);
  assert.match(html,/href="\/data\/pilotos\/hoenn-android\.txt" download/);
  assert.doesNotMatch(androidPilotsHtml({state:'unavailable'}),/\/releases\/download\//);
});

test('Kanto tem release experimental própria; download não depende do ZIP geral',async()=>{
  const release={tag_name:'kanto-android-512-abc1234',target_commitish:sha,prerelease:true,assets:[
    {name:'Blue-Android-Kanto-Piloto.zip',state:'uploaded',size:1500000000}
  ]};
  const api=async()=>({ok:true,json:async()=>[release]});
  const regional=await regionalAndroidReleases(api);
  assert.equal(regional.kanto.tag,release.tag_name);
  assert.equal(regional.johto,null);
  const html=androidPilotsHtml({state:'unavailable',regional});
  assert.match(html,/releases\/download\/kanto-android-512-abc1234\/Blue-Android-Kanto-Piloto\.zip/);
  assert.match(html,/\/data\/pilotos\/johto-android\.txt/);
  assert.doesNotMatch(html,/href="[^"]*Blue-Android-Johto-Piloto\.zip"/);
  const malformed=await regionalAndroidReleases(async()=>({ok:true,json:async()=>[
    {...release,target_commitish:'not-sha'},
    {...release,assets:[{name:'Blue-Android-Kanto-Piloto.zip',state:'starter',size:200}]}
  ]}));
  assert.equal(malformed.kanto,null);
});


test('pilotos escolhem a publicação mais recente pela data, não pela ordem da API',async()=>{
  const older={tag_name:'kanto-android-local-old',target_commitish:sha,published_at:'2026-11-14T05:27:26Z',
    assets:[{name:'Blue-Android-Kanto-Piloto.zip',state:'uploaded',size:1200}]};
  const newer={tag_name:'kanto-android-1205-new',target_commitish:next,published_at:'2026-11-14T18:05:55Z',
    assets:[{name:'Blue-Android-Kanto-Piloto.zip',state:'uploaded',size:1300}]};
  const fetcher=async()=>({ok:true,json:async()=>[older,newer]});
  const regional=await regionalAndroidReleases(fetcher);
  assert.equal(regional.kanto.tag,newer.tag_name);
  assert.equal(regional.kanto.bytes,1300);
});

test('pilotos publicados na página 2 ainda são descobertos e Johto não usa o ZIP geral',async()=>{
  const firstPage=Array.from({length:100},(_,i)=>({
    tag_name:'battle-hub-'+i,target_commitish:sha,assets:[]
  }));
  const johto={tag_name:'johto-android-1-sample',target_commitish:next,published_at:'2026-11-14T21:00:00Z',
    assets:[{name:'Blue-Android-Johto-Piloto.zip',state:'uploaded',size:9000}]};
  const fetcher=async url=>({ok:true,json:async()=>url.includes('page=2')?[johto]:firstPage});
  const regional=await regionalAndroidReleases(fetcher);
  assert.equal(regional.johto.tag,johto.tag_name);
  const html=androidPilotsHtml({regional});
  assert.match(html,/Blue-Android-Johto-Piloto[.]zip/);
  assert.match(html,/\/data\/pilotos\/hoenn-android\.txt/);
});

test('guias regionais existem para Windows e Android enquanto não há ZIP completo',()=>{
  for(const platform of ['windows','android']){
    const html=androidPilotsHtml({state:'unavailable',regional:{}},platform);
    for(const region of ['johto','hoenn']){
      const guide=`/data/pilotos/${region}-${platform}.txt`;
      assert.ok(existsSync(new URL('../public'+guide,import.meta.url)));
      assert.ok(html.includes(`href="${guide}" download`));
    }
    assert.ok(html.includes('/archive/refs/heads/main.zip'));
    assert.match(html,/O ZIP do jogo ainda não foi publicado/);
    assert.doesNotMatch(html,/testar (Johto|Hoenn)|Blue-(Windows|Android)-(Johto|Hoenn)-Piloto\.zip/);
  }
});
