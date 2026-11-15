import {esc} from './utils.js';
import {gameDownload} from './downloads.js';
const repo='GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal';
const api=`https://api.github.com/repos/${repo}`;
let cached;
const pilotRegions={kanto:'Kanto',johto:'Johto',hoenn:'Hoenn'};
const sourceKit=`https://github.com/${repo}/archive/refs/heads/main.zip`;
const assetName=(region,platform)=>`Blue-${platform==='android'?'Android':'Windows'}-${pilotRegions[region]}-Piloto.zip`;
const uploaded=(release,name)=>release.assets?.find(a=>a.name===name&&a.state==='uploaded'&&a.size>0);
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
    pilots:Object.fromEntries(Object.keys(pilotRegions).map(key=>[key,!!uploaded(release,assetName(key,'android'))]))};
}

// Publicações independentes já confirmadas. Mantêm Kanto acessível quando a API
// pública falha ou a release sai das páginas de resultados mais recentes.
const verifiedFallback={
  android:{kanto:{tag:'kanto-android-1205-f4b574e',bytes:1292515137,publishedAt:'2026-11-14T18:05:55Z',fallback:true}},
  windows:{kanto:{tag:'kanto-windows-local-ab58da1',bytes:1288615509,publishedAt:'2026-11-14T05:30:07Z',fallback:true}}
};
const emptyPilots=()=>Object.fromEntries(Object.keys(pilotRegions).map(key=>[key,null]));
const publishedTime=release=>Date.parse(release.published_at||release.created_at||'')||0;

async function regionalPilotIndex(fetcher=fetch){
  const releases=[];
  // Builds frequentes da História podem deslocar releases de pilotos para
  // páginas antigas; consultar até três páginas, sem inventar pacotes ausentes.
  for(let page=1;page<=3;page++){
    let batch;
    try{
      const response=await fetcher(api+'/releases?per_page=100'+(page>1?'&page='+page:''));
      if(!response.ok)break;
      batch=await response.json();
    }catch{break;}
    if(!Array.isArray(batch))break;
    releases.push(...batch);
    if(batch.length<100)break;
  }
  const result={android:emptyPilots(),windows:emptyPilots()};
  for(const platform of ['android','windows']){
    for(const key of Object.keys(pilotRegions)){
      const file=assetName(key,platform);
      const candidates=releases.filter(release=>
        typeof release.tag_name==='string'&&release.tag_name.startsWith(key+'-'+platform+'-')&&
        /^[a-f0-9]{40}$/.test(release.target_commitish??'')&&uploaded(release,file));
      candidates.sort((a,b)=>publishedTime(b)-publishedTime(a));
      if(candidates.length){
        const release=candidates[0],asset=uploaded(release,file);
        result[platform][key]={tag:release.tag_name,revision:release.target_commitish,
          bytes:asset.size,publishedAt:release.published_at||release.created_at||''};
      }
    }
  }
  return result;
}

export async function regionalPilotReleases(fetcher=fetch,platform='android'){
  const index=await regionalPilotIndex(fetcher);
  return index[platform]||emptyPilots();
}

const withVerifiedFallback=(found,platform)=>Object.fromEntries(Object.keys(pilotRegions).map(key=>{
  const current=found?.[key]||null,known=verifiedFallback[platform]?.[key]||null;
  if(!known)return [key,current];
  if(!current)return [key,known];
  return Date.parse(current.publishedAt||'')>=Date.parse(known.publishedAt)?[key,current]:[key,known];
}));


const integratedAsset='Blue-Android-Decades-Kanto-Hoenn.zip';
const integratedReleasePrefix='android-multiregion-';

// No static latest/download URL: the combined Android file does not exist
// until a release really uploads a validated, compiled ZIP.
export async function combinedAndroidRelease(fetcher=fetch){
  for(let page=1;page<=3;page++){
    let releases;
    try{
      const url=api+'/releases?per_page=100'+(page>1?'&page='+page:'');
      const response=await fetcher(url);
      if(!response.ok)return {state:'unavailable'};
      releases=await response.json();
    }catch{return {state:'unavailable'};}
    if(!Array.isArray(releases))return {state:'unavailable'};
    for(const release of releases){
      if(!release.tag_name?.startsWith(integratedReleasePrefix) || release.draft ||
         !/^[a-f0-9]{40}$/.test(release.target_commitish??''))continue;
      const asset=uploaded(release,integratedAsset);
      if(!asset || typeof asset.browser_download_url!=='string')continue;
      const prefix='https://github.com/'+repo+'/releases/download/';
      if(!asset.browser_download_url.startsWith(prefix) ||
         !asset.browser_download_url.endsWith('/'+integratedAsset))continue;
      return {state:'published',tag:release.tag_name,revision:release.target_commitish,
        bytes:asset.size,url:asset.browser_download_url};
    }
    if(releases.length<100)break;
  }
  return {state:'pending'};
}

export function combinedAndroidHtml(status){
  if(status.state!=='published'){
    const detail=status.state==='unavailable'
      ?'Não foi possível conferir a publicação no GitHub agora.'
      :'O pacote conjunto ainda não foi publicado com compilação e verificação aprovadas.';
    return '<div class="android-combined-panel"><h3>Decades + Kanto + Hoenn · Android</h3>'+
      '<p>'+esc(detail)+' O ZIP normal do JoiPlay continua sendo a versão Decades, sem garantia de Kanto e Hoenn instalados.</p>'+
      '<span class="button button-secondary android-pilot-disabled" aria-disabled="true">Versão conjunta · aguardando publicação</span></div>';
  }
  return '<div class="android-combined-panel"><h3>Decades + Kanto + Hoenn · Android</h3>'+
    '<p>Jogue na mesma instalação e perfil de saves pelo JoiPlay. '+
    'Pacote experimental compilado, sem garantia de teste em aparelho físico. '+
    'Extraia em uma nova pasta e preserve seus saves antes de migrar.</p>'+
    '<a class="button button-primary" href="'+esc(status.url)+
    '" target="_blank" rel="noopener noreferrer">Baixar Decades + Kanto + Hoenn · ZIP</a>'+
    '<small>Release '+esc(status.tag)+' · '+(status.bytes/1e9).toFixed(2).replace('.',',')+
    ' GB · revisão '+esc(status.revision.slice(0,10))+'</small></div>';
}

export const regionalAndroidReleases=fetcher=>regionalPilotReleases(fetcher);

export function androidReleaseHtml(status){
  if(status.state==='unavailable')return '<p>Não foi possível consultar a revisão agora. Confira a linha <code>Revision:</code> no arquivo <code>LEIA-ME-ANDROID.txt</code> do ZIP.</p>';
  const warning=status.state==='outdated'?'Download desatualizado: a publicação da revisão mais recente não terminou. O botão ainda baixa o pacote abaixo.':status.state==='building'?'Uma nova revisão está sendo preparada. O botão ainda baixa o pacote publicado abaixo.':'';
  const href=`https://github.com/${repo}/releases/tag/${encodeURIComponent(status.tag)}`;
  return `${warning?`<p class="android-release-warning">${esc(warning)}</p>`:''}<p><strong>Pacote publicado:</strong> <a href="${href}" target="_blank" rel="noopener noreferrer">${esc(status.tag)}</a><br>Revisão <code>${esc(status.revision)}</code>${Number.isFinite(status.bytes)?` · ${(status.bytes/1e9).toFixed(2).replace('.',',')} GB`:''}</p><p>Depois de extrair, compare essa revisão com <code>LEIA-ME-ANDROID.txt</code>. Se um evento falhar, o diagnóstico fica em <code>Data/blue-android-event-error.txt</code>.</p>${status.buildKnown?'':'<p>Estado da compilação mais recente indisponível.</p>'}`;
}

export function androidPilotsHtml(status,platform='android'){
  return Object.entries(pilotRegions).map(([id,region])=>{
    const asset=assetName(id,platform);
    const regional=status.regional?.[id];
    const regular=platform==='android'&&status.state!=='unavailable'&&status.pilots?.[id]===true&&typeof status.tag==='string'&&status.tag.length>0;
    const enabled=!!regional||regular;
    const tag=regional?.tag||status.tag;
    const href=enabled?'https://github.com/'+repo+'/releases/download/'+encodeURIComponent(tag)+'/'+asset:'';
    const hasSetup=!enabled&&(id==='johto'||id==='hoenn');
    const windowsAlternative=!enabled&&!hasSetup&&platform==='windows';
    const setupHref=hasSetup?`/data/pilotos/${id}-${platform==='android'?'android':'windows'}.txt`:'';
    const label=enabled?'Baixar piloto '+region+' · .zip':windowsAlternative?'Baixar História · testar '+region:'Piloto '+region+' · indisponível';
    const action=hasSetup?
      `<a class="button button-secondary" href="${setupHref}" download>Baixar guia de montagem · .txt</a>`+
      `<a class="text-link" href="${sourceKit}" target="_blank" rel="noopener noreferrer">Baixar ferramentas do projeto · .zip</a>`:
      enabled||windowsAlternative?
      '<a class="button button-secondary" href="'+esc(enabled?href:gameDownload)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+'</a>':
      '<span class="button button-secondary android-pilot-disabled" aria-disabled="true">'+esc(label)+'</span>';
    const detail=enabled?'ZIP regional independente na release '+tag+(regional?.fallback?' (última publicação confirmada)':'')+
      (platform==='android'?'. Extraia em uma pasta própria e adicione o Game.exe ao JoiPlay.':'. Extraia o ZIP e abra Game.exe.'):
      hasSetup?'O ZIP do jogo ainda não foi publicado. O guia e as ferramentas não contêm o jogo e exigem a instalação e os arquivos de origem locais.':
      windowsAlternative?'Ainda não há ZIP próprio de '+region+'. O instalador abre o modo História com a opção Testar '+region+'; a montagem regional pode exigir arquivos locais e ainda não equivale a um piloto aprovado.':
      'Ainda não existe ZIP Android independente e verificado para '+region+'. O pacote geral do JoiPlay não substitui o piloto.';
    return '<article class="android-pilot-card"><span class="eyebrow">PILOTO '+esc(region.toUpperCase())+'</span>'+
      '<h4>'+esc(region)+'</h4><p>'+esc(platform==='android'?'JoiPlay · instalação e saves separados':'Windows · teste com saves separados')+'</p>'+
      action+'<small>'+esc(detail)+'</small></article>';
  }).join('');
}

export async function bindAndroidRelease(container){
  const target=container.querySelector('[data-android-release]');
  const pilots=container.querySelector('[data-android-pilots]');
  const windows=container.querySelector('[data-windows-pilots]');
  const integrated=container.querySelector('[data-android-multiregion]');
  if(!target&&!pilots&&!windows&&!integrated)return;
  if(integrated?.isConnected)integrated.innerHTML=combinedAndroidHtml({state:'pending'});
  // Local guides remain usable while GitHub is still answering.
  if(pilots?.isConnected)pilots.innerHTML=androidPilotsHtml({
    state:'unavailable',regional:withVerifiedFallback(null,'android')});
  if(windows?.isConnected)windows.innerHTML=androidPilotsHtml({
    regional:withVerifiedFallback(null,'windows')},'windows');
  if(!cached||Date.now()-cached.time>60000)cached={time:Date.now(),promise:Promise.all([androidReleaseStatus(),regionalPilotIndex(),combinedAndroidRelease()])};
  const [status,index,combined]=await cached.promise;
  status.regional=withVerifiedFallback(index.android,'android');
  const windowsRegional=withVerifiedFallback(index.windows,'windows');
  if(target?.isConnected)target.innerHTML=androidReleaseHtml(status);
  if(integrated?.isConnected)integrated.innerHTML=combinedAndroidHtml(combined);
  if(pilots?.isConnected)pilots.innerHTML=androidPilotsHtml(status);
  if(windows?.isConnected)windows.innerHTML=androidPilotsHtml({regional:windowsRegional},'windows');
}
