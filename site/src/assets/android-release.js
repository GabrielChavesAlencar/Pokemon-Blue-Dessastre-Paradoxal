import {esc} from './utils.js';
const repo='GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal';
const api=`https://api.github.com/repos/${repo}`;
let cached;
export async function androidReleaseStatus(fetcher=fetch){
  const [releaseResult,runsResult]=await Promise.allSettled([
    fetcher(`${api}/releases/latest`).then(r=>{if(!r.ok)throw Error('release');return r.json();}),
    fetcher(`${api}/actions/runs?branch=main&per_page=30`).then(r=>{if(!r.ok)throw Error('build');return r.json();})
  ]);
  if(releaseResult.status!=='fulfilled')return {state:'unavailable'};
  const release=releaseResult.value;
  const asset=release.assets?.find(a=>a.name==='Blue-Android-JoiPlay.zip'&&a.state==='uploaded');
  if(!asset||!/^[a-f0-9]{40}$/.test(release.target_commitish??''))return {state:'unavailable'};
  const run=runsResult.status==='fulfilled'?runsResult.value.workflow_runs?.find(x=>x.path==='.github/workflows/battle-hub-release.yml'):null;
  const pending=run&&run.head_sha!==release.target_commitish;
  return {state:pending?(run.status==='completed'?'outdated':'building'):'published',buildKnown:!!run,
    tag:release.tag_name,revision:release.target_commitish,date:release.published_at,
    bytes:asset.size,digest:asset.digest??'',runId:run?.id,
    pilots:{
      kanto:!!release.assets?.some(x=>x.name==='Blue-Android-Kanto-Piloto.zip'&&x.state==='uploaded'&&x.size>0),
      johto:!!release.assets?.some(x=>x.name==='Blue-Android-Johto-Piloto.zip'&&x.state==='uploaded'&&x.size>0)
    }};
}

export async function regionalAndroidReleases(fetcher=fetch){
  let releases;
  try{
    const response=await fetcher(api+'/releases?per_page=30');
    if(!response.ok)throw new Error('releases');
    releases=await response.json();
  }catch{return {kanto:null,johto:null};}
  if(!Array.isArray(releases))return {kanto:null,johto:null};
  const find=(kind,file)=>{
    for(const release of releases){
      if(typeof release.tag_name!=='string'||!release.tag_name.startsWith(kind+'-android-')
          ||!/^[a-f0-9]{40}$/.test(release.target_commitish??''))continue;
      const asset=release.assets?.find(a=>a.name===file&&a.state==='uploaded'&&a.size>0);
      if(asset)return {tag:release.tag_name,revision:release.target_commitish,bytes:asset.size};
    }
    return null;
  };
  return {kanto:find('kanto','Blue-Android-Kanto-Piloto.zip'),
          johto:find('johto','Blue-Android-Johto-Piloto.zip')};
}

export function androidReleaseHtml(status){
  if(status.state==='unavailable')return '<p>Não foi possível consultar a revisão agora. Confira a linha <code>Revision:</code> no arquivo <code>LEIA-ME-ANDROID.txt</code> do ZIP.</p>';
  const warning=status.state==='outdated'?'Download desatualizado: a publicação da revisão mais recente não terminou. O botão ainda baixa o pacote abaixo.':status.state==='building'?'Uma nova revisão está sendo preparada. O botão ainda baixa o pacote publicado abaixo.':'';
  const href=`https://github.com/${repo}/releases/tag/${encodeURIComponent(status.tag)}`;
  return `${warning?`<p class="android-release-warning">${esc(warning)}</p>`:''}<p><strong>Pacote publicado:</strong> <a href="${href}" target="_blank" rel="noopener noreferrer">${esc(status.tag)}</a><br>Revisão <code>${esc(status.revision)}</code>${Number.isFinite(status.bytes)?` · ${(status.bytes/1e9).toFixed(2).replace('.',',')} GB`:''}</p><p>Depois de extrair, compare essa revisão com <code>LEIA-ME-ANDROID.txt</code>. Se um evento falhar, o diagnóstico fica em <code>Data/blue-android-event-error.txt</code>.</p>${status.buildKnown?'':'<p>Estado da compilação mais recente indisponível.</p>'}`;
}

const androidPilots=[
  {id:'kanto',region:'Kanto',asset:'Blue-Android-Kanto-Piloto.zip',note:'Experimento isolado a partir de Pallet Town; saves separados do jogo principal.'},
  {id:'johto',region:'Johto',asset:'Blue-Android-Johto-Piloto.zip',note:'Experimento isolado a partir de New Bark; mapas, eventos e QA próprios.'}
];
export function androidPilotsHtml(status){
  return androidPilots.map(p=>{
    const regional=status.regional?.[p.id];
    const regular=status.state!=='unavailable'&&status.pilots?.[p.id]===true&&typeof status.tag==='string'&&status.tag.length>0;
    const enabled=!!regional||regular;
    const tag=regional?.tag||status.tag;
    const href=enabled?'https://github.com/'+repo+'/releases/download/'+encodeURIComponent(tag)+'/'+p.asset:'';
    return '<article class="android-pilot-card"><span class="eyebrow">PILOTO '+esc(p.region.toUpperCase())+'</span>'+
      '<h4>'+esc(p.region)+'</h4><p>'+esc(p.note)+'</p>'+
      (enabled?'<a class="button button-secondary" href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">Baixar piloto '+esc(p.region)+' · .zip</a>':
      '<span class="button button-secondary android-pilot-disabled" aria-disabled="true">Piloto '+esc(p.region)+' · indisponível</span>')+
      '<small>'+(enabled?'Arquivo independente publicado na release '+esc(tag)+'. Adicione Game.exe desta pasta ao JoiPlay.':
        'Ainda não existe ZIP regional publicado e verificado. O ZIP geral não substitui este piloto.')+'</small></article>';
  }).join('');
}

export async function bindAndroidRelease(container){
  const target=container.querySelector('[data-android-release]');
  const pilots=container.querySelector('[data-android-pilots]');
  if(!target&&!pilots)return;
  if(!cached||Date.now()-cached.time>60000)cached={time:Date.now(),promise:Promise.all([androidReleaseStatus(),regionalAndroidReleases()])};
  const [status,regional]=await cached.promise;
  status.regional=regional;
  if(target?.isConnected)target.innerHTML=androidReleaseHtml(status);
  if(pilots?.isConnected)pilots.innerHTML=androidPilotsHtml(status);
}
