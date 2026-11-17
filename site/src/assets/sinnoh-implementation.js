// G10: evidence panel for the planned Sinnoh portal. Never a game-state UI.
import {esc} from './utils.js';
let cached;
const bad=reason=>{throw new Error('sinnoh-g10-unsafe: '+reason);};
export function validateSinnohImplementation(d){
  if(!d||d.schema!==1||d.region!=='SINNOH'||d.stage!=='G10'||
     d.status!=='PUBLIC_CONTRACT_EVIDENCE_ONLY_NO_NATIVE_APPROVAL'||
     !Array.isArray(d.states)||d.states.length!==4||
     !Array.isArray(d.categories)||d.categories.length!==6||
     !Array.isArray(d.gyms)||d.gyms.length!==8||
     !Array.isArray(d.league)||d.league.length!==8||
     !Array.isArray(d.postgame)||d.postgame.length!==6||
     !Array.isArray(d.blockers)||d.blockers.length!==4)
    bad('shape');
  const expectedKeys=['planned','private_preparation','installed','playable'];
  const expectedCounts=[120,54,0,0];
  if(d.states.some((x,i)=>x.key!==expectedKeys[i]||
      x.count!==expectedCounts[i]||typeof x.label!=='string'||
      typeof x.meaning!=='string'))bad('implementation stages');
  const cats=['areas','trainers','gyms','hms','league','postgame'];
  const counts=[120,40,8,8,8,6];
  if(d.categories.some((x,i)=>x.key!==cats[i]||x.count!==counts[i]||
      !['areas','treinadores','ginasios','itens','liga','progresso'].includes(x.tab)||
      typeof x.pending!=='string'))bad('category evidence');
  if(d.gyms.some(g=>g.state!=='pending'||g.mapVerified!==false||
      g.pbsVerified!==false||g.hmPickupVerified!==false||
      !g.id||!g.label||!g.badge||!g.hm||!g.move)||
     d.league.some(x=>x.state!=='pending'||x.nativeVerified!==false)||
     d.postgame.some(x=>x.state!=='pending'||x.nativeVerified!==false))
    bad('native binding claimed');
  const v=d.verification;
  if(!v||v.nativeAssetBytesInspected!==false||
     v.privateStageExecutionVerified!==false||
     v.nativeMapBindingsVerified!==false||v.gameExeTested!==false||
     v.joiplayTested!==false||v.installedVerified!==false||
     v.playableVerified!==false||v.phaseBApproved!==0||
     v.phaseCApproved!==0||v.phaseDApproved!==0)
    bad('fake native approval');
  if(d.blockers.some(x=>typeof x!=='string'||!x.trim()))bad('blocker missing');
  // Unknown key injection must not be able to add fake gameplay claims.
  const prohibited=new Set(['map_id','mapId','physical_map_id','x','y',
    'playable','installed','level','levels','nativeSource','verifiedNative',
    'gameplayApproved','gameplayVerified','savePath','assetPath']);
  for(const group of [d.states,d.categories,d.gyms,d.league,d.postgame]){
    if(group.some(row=>Object.keys(row).some(k=>prohibited.has(k))))
      bad('unverified property injected');
  }
  return d;
}
export async function loadSinnohImplementation(fetcher=fetch){
  if(!cached){
    const response=await fetcher('/data/sinnoh-implementation.json');
    if(!response.ok)throw new Error('sinnoh-g10-metadata-unavailable');
    const data=await response.json();
    cached=validateSinnohImplementation(data);
  }
  return cached;
}
const link=(tab,label)=>'<a class="text-link" href="/sinnoh?aba='+esc(tab)+'">'+esc(label)+'</a>';
const status=(state)=>'<span class="sinnoh-evidence-status">'+esc(state)+'</span>';
export function sinnohImplementationPanel(info,section='visao'){
  validateSinnohImplementation(info);
  const stages='<div class="sinnoh-implementation-stages">'+info.states.map(s=>
    '<div class="sinnoh-implementation-stage" data-sinnoh-state="'+esc(s.key)+'">'+
    '<strong>'+s.count+'</strong><span>'+esc(s.label)+'</span>'+
    '<p>'+esc(s.meaning)+'</p></div>').join('')+'</div>';
  const categories='<div class="sinnoh-implementation-categories">'+
    info.categories.map(c=>'<article class="sinnoh-implementation-category"><h3>'+
      esc(c.label)+' '+status('Pendente')+'</h3><p>'+esc(c.count)+
      ' referências · '+esc(c.pending)+'</p>'+link(c.tab,'Abrir seção')+'</article>').join('')+
    '</div>';
  const gymRows=info.gyms.map(g=>'<li><strong>'+esc(g.label)+'</strong>'+
    ' · '+esc(g.badge)+' · '+esc(g.hm)+' / '+esc(g.move)+' '+status('Evento pendente')+
    '</li>').join('');
  const special='<section class="sinnoh-implementation-details"><h3>Ginásios e HMs — por insígnia</h3>'+
    '<p>Fantina / RELIC / DEFOG é o terceiro ginásio; Maylene / COBBLE / FLY é o quarto. Nenhum HM foi coletado ou liberado na engine.</p>'+
    '<ol>'+gymRows+'</ol>'+
    '<h3>Liga, Cynthia e pós-jogo</h3>'+
    '<p>Oito checkpoints de Liga, incluindo confirmação independente de Hall of Fame após Cynthia; seis gates de pós-jogo ainda sem eventos nativos.</p>'+
    '<p>Heatran exige entrada na Battle Zone; Darkrai/Shaymin exigem itens de evento verificados; Full Power exige dez Ligas e equipe nativa comprovada.</p>'+
    '</section>';
  const blockers='<div class="sinnoh-implementation-blockers"><h3>Provas ainda necessárias</h3><ul>'+
    info.blockers.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div>';
  return '<section class="section sinnoh-implementation" aria-label="Evidências de implementação de Sinnoh">'+
    '<div class="section-heading"><div><span class="eyebrow">G10 · ESTADO COM EVIDÊNCIAS</span>'+
    '<h2>Planejamento não é jogo instalado<span>.</span></h2></div></div>'+
    '<p class="data-note">Os números da cópia privada são <strong>candidatos dos contratos B07–B09</strong>, não prova de arquivos efetivamente preparados ou executados neste computador. As barras B/C/D continuam em 0/13.</p>'+
    stages+
    (section==='implantacao'?categories+special+blockers:
      '<p class="sinnoh-implementation-more">'+link('implantacao','Ver matriz completa, ginásios, HMs e bloqueios')+'</p>')+
    '<p class="data-note">Nenhum save real foi consultado. O portal não certifica instalação, executável ou JoiPlay.</p>'+
    '</section>';
}
