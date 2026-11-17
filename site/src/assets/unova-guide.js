// G06.2: navigable, read-only Unova White guide derived from audited sources.
// Never interprets a symbolic reference as native Game.exe content.
import {esc,icon} from './utils.js';

let cache;
const invalid=reason=>{throw new Error('unova-guide-invalid: '+reason);};
export const unovaGuideUrl=(kind,key)=>kind==='home'?'/unova':
 kind==='area'?'/unova/area/'+encodeURIComponent(key):
 kind==='capitulo'?'/unova/capitulo/'+encodeURIComponent(key):
 '/unova/'+encodeURIComponent(kind);
const link=(url,label)=>'<a class="text-link" href="'+esc(url)+'">'+esc(label)+' '+icon('arrow')+'</a>';
const linkArea=(a,label)=>link(unovaGuideUrl('area',a.key),label||a.name);
const linkChapter=(c,label)=>link(unovaGuideUrl('capitulo',c.key),label||('Capítulo '+c.index+' · '+c.title));
const kindLabel={settlement:'Cidade ou vila',route:'Rota',gym:'Ginásio',interior:'Interior',area:'Área',
 cave:'Caverna',forest:'Floresta',bridge:'Ponte',ruin:'Ruína',facility:'Instalação',tower:'Torre',
 mountain:'Montanha',castle:'Castelo',water:'Área aquática'};
const stateLabel={campaign:'Campanha',postgame:'Pós-jogo',optional:'Opcional',event_only:'Evento condicionado'};
const badge='<span class="content-pending-tag">Planejado · Não jogável</span>';
const note=text=>'<p class="data-note">'+esc(text)+'</p>';
const cards=(items,render)=>'<div class="unova-guide-grid">'+items.map(render).join('')+'</div>';
const card=(title,body,kicker='REFERÊNCIA SIMBÓLICA')=>
 '<article class="unova-guide-card"><span class="eyebrow">'+esc(kicker)+'</span>'+
 '<h3>'+esc(title)+'</h3>'+body+badge+'</article>';
const areaBy=(data,key)=>data.areas.find(a=>a.key===key);
const chapterBy=(data,key)=>data.chapters.find(c=>c.key===key);
const listLinks=(list,make)=>list.length?'<div class="unova-guide-related">'+list.map(make).join('')+'</div>':
 note('Nenhuma referência auditada neste catálogo; não significa ausência de conteúdo no jogo original.');
const nav=[
 ['home','Visão geral'],['capitulos','História'],['areas','74 áreas'],
 ['ginasios','8 ginásios'],['liga','Elite Four e Castelo'],
 ['npcs','NPCs'],['treinadores','Treinadores'],['pendencias','Pendências']
];
export function validateUnovaGuide(data){
 if(data?.schema!==1||data.region!=='UNOVA'||data.campaign!=='WHITE_BW'||data.phase!=='G06.2'||
    data.status!=='PLANNED_REFERENCE_GUIDE_ONLY'||data.canPlay!==false||
    data.canInstall!==false||data.gameExeTested!==false||
    !data.sourcePaths||!Array.isArray(data.areas)||data.areas.length!==74||
    !Array.isArray(data.chapters)||data.chapters.length!==12||
    !Array.isArray(data.gyms)||data.gyms.length!==8||
    !Array.isArray(data.elite)||data.elite.length!==4||
    !Array.isArray(data.npcs)||!Array.isArray(data.trainers)||
    !Array.isArray(data.castle)||data.nativeMapIdsVerified!==0||
    data.nativeEventsVerified!==0||data.nativeTeamsVerified!==0||
    data.nativeEncounterRatesVerified!==0||data.counts?.areas!==74||
    data.counts?.chapters!==12||data.counts?.gyms!==8||
    data.counts?.eliteFour!==4||data.counts?.npcs!==data.npcs.length||
    data.counts?.trainerReferences!==data.trainers.length)invalid('summary or native state');
 const ids=new Set(data.areas.map(a=>a.key)),chapterIds=new Set(data.chapters.map(c=>c.key));
 if(ids.size!==74||chapterIds.size!==12||new Set(data.npcs.map(n=>n.key)).size!==data.npcs.length||
   new Set(data.trainers.map(t=>t.key)).size!==data.trainers.length)invalid('duplicate references');
 if(data.areas.some(a=>!/^UNOVA_[A-Z0-9_]+$/.test(a.key)||a.status!=='planned'||a.installed!==false||
   a.nativeMapId!==null||a.verifiedLevels!==null||a.verifiedEncounters!==0||
   a.verifiedNpcEvents!==0||a.verifiedTrainerTeams!==0||
   a.chapterAssociation!=='EDITORIAL_PHASE_GROUP_NOT_VERIFIED_ROUTE'||
   !chapterIds.has(a.chapterKey)||!Array.isArray(a.npcKeys)||
   !Array.isArray(a.trainerEventKeys)))invalid('area invented gameplay or missing links');
 if(data.chapters.some((c,i)=>c.index!==i+1||c.installed!==false||c.nativeMapId!==null||
   c.nativeEventId!==null||c.status!=='planned'||
   c.association!=='EDITORIAL_PLANNING_PHASE_NOT_NATIVE_ROUTE'||
   !c.areaKeys?.every(key=>ids.has(key))||
   (c.referenceAreaKey!==null&&!ids.has(c.referenceAreaKey))))invalid('chapter gameplay or links');
 if(data.chapters.flatMap(c=>c.areaKeys).length!==74||
    new Set(data.chapters.flatMap(c=>c.areaKeys)).size!==74)invalid('incomplete area coverage');
 if(data.gyms.some(g=>g.status!=='planned'||g.installed!==false||
   g.team!==null||g.levels!==null||g.nativeTrainerId!==null||
   !chapterIds.has(g.chapterKey)||!ids.has(g.gymAreaKey)||!ids.has(g.cityAreaKey)))invalid('gym team/MapID falsely installed');
 if(data.elite.some(e=>e.status!=='planned'||e.team!==null||e.levels!==null||
   e.nativeTrainerId!==null||!ids.has(e.areaKey)||!chapterIds.has(e.chapterKey)))invalid('Elite falsely installed');
 if(data.castle.some(e=>e.status!=='planned'||e.nativeEventId!==null||
   e.trainerTeam!==null||e.levels!==null||!ids.has(e.areaKey)))invalid('castle falsely playable');
 if(data.npcs.some(n=>n.status!=='planned'||n.installed!==false||n.spriteVerified!==false||
   n.nativeEventId!==null||!ids.has(n.areaKey)||!n.relatedAreaKeys.every(k=>ids.has(k))))invalid('NPC falsely installed');
 if(data.trainers.some(t=>t.status!=='planned'||t.installed!==false||
   t.team!==null||t.levels!==null||t.nativeTrainerId!==null||
   !ids.has(t.areaKey)||!chapterIds.has(t.chapterKey)))invalid('trainer team/levels falsely verified');
 if(data.areas.some(a=>a.npcKeys.some(k=>!data.npcs.some(n=>n.key===k))||
   a.trainerEventKeys.some(k=>!data.trainers.some(t=>t.key===k))))invalid('broken NPC/trainer area backlinks');
 return data;
}
export async function loadUnovaGuide(fetcher=fetch){
 if(!cache){
  const response=await fetcher('/data/unova-guide.json');
  if(!response.ok)throw new Error('unova-guide-unavailable');
  cache=validateUnovaGuide(await response.json());
 }
 return cache;
}

const section=(title,body)=>'<section class="section"><h2>'+esc(title)+'</h2>'+body+'</section>';
const intro=(title,description)=>'<header class="article-heading"><span class="eyebrow">UNOVA WHITE · GUIA PLANEJADO</span>'+
 '<h1>'+esc(title)+'</h1><p>'+esc(description)+'</p>'+badge+'</header>';
const areaCard=(a,chapter)=>card(a.name,
 '<p>'+esc(kindLabel[a.kind]||a.kind)+' · '+esc(a.plannedPhase)+' · '+esc(stateLabel[a.storyScope]||a.storyScope)+'</p>'+
 note('MapID, eventos, encontros e níveis: pendentes de fonte nativa.')+
 '<div class="unova-guide-context">'+linkArea(a,'Abrir área')+
 (chapter?' '+linkChapter(chapter,'Capítulo relacionado'):'')+'</div>',
 'ÁREA SIMBÓLICA · '+a.plannedPhase);
const chapterCard=c=>card('Capítulo '+c.index+' · '+c.title,
 '<p>'+esc(c.plannedPhase)+' · '+c.areaKeys.length+' áreas agrupadas editorialmente</p>'+
 note('Missão: '+(c.missionKey||'não definida')+' · progresso apenas simbólico')+
 '<div class="unova-guide-context">'+linkChapter(c,'Explorar capítulo')+'</div>',
 'HISTÓRIA · PLANEJADA');
const headerArea=(a,c)=>intro(a.name,(kindLabel[a.kind]||a.kind)+' · '+a.plannedPhase+
 ' · '+(stateLabel[a.storyScope]||a.storyScope)+'. Nenhum mapa ou evento nativo foi validado.');
const breadcrumbs=links=>'<nav class="unova-guide-breadcrumb" aria-label="Você está aqui">'+links.join('<span aria-hidden="true"> / </span>')+'</nav>';
const related=(label,content)=>section(label,content);
const areaDetails=(data,a)=>{
 const chapter=chapterBy(data,a.chapterKey);
 const people=data.npcs.filter(n=>a.npcKeys.includes(n.key));
 const trainer=data.trainers.filter(t=>a.trainerEventKeys.includes(t.key));
 const gyms=data.gyms.filter(g=>g.gymAreaKey===a.key||g.cityAreaKey===a.key);
 const elite=data.elite.filter(e=>e.areaKey===a.key);
 return breadcrumbs([link('/unova','Unova'),link('/unova/areas','74 áreas'),esc(a.name)])+
 headerArea(a,chapter)+
 section('Referência narrativa e pendências',
  note('Vínculo editorial: '+(chapter?'Capítulo '+chapter.index+' · '+chapter.title:'sem capítulo')+
   '. O agrupamento usa fases da documentação; não confirma passagens físicas entre mapas.')+
  note('MapID original/destino: pendente · eventos NPC: pendentes · encontros selvagens e taxas: pendentes · nível de treinadores: pendente · teste Game.exe: não realizado.')+
  (chapter?'<div class="unova-guide-context">'+linkChapter(chapter,'Ver capítulo')+'</div>':''))+
 related('Personagens citados nesta área',
  people.length?cards(people,n=>card(n.name,note('Papel: '+n.role+' · sprite e evento pendentes')+
   '<div class="unova-guide-context">'+link('/unova/npcs','Catálogo de NPCs')+'</div>')):note('Não há associação de NPC auditada para esta área.'))+
 related('Confrontos de referência',
  trainer.length?cards(trainer,t=>card(t.actor,note('Política contratual: '+t.policy+' · nenhum time ou nível PBS confirmado')+
   '<div class="unova-guide-context">'+linkChapter(chapterBy(data,t.chapterKey),'Capítulo do confronto')+'</div>')):note('Não há confronto identificado nesta área no contrato G03.3.'))+
 (gyms.length?related('Ginásio relacionado',listLinks(gyms,()=>link('/unova/ginasios','Ver os oito ginásios'))):'')+
 (elite.length?related('Elite Four',link('/unova/liga','Ver os quatro membros')):'')+
 related('Explorar referências próximas',
  listLinks(data.areas.filter(x=>x.chapterKey===a.chapterKey&&x.key!==a.key).slice(0,10),x=>linkArea(x)));
};
const chapterDetails=(data,c)=>{
 const areas=c.areaKeys.map(k=>areaBy(data,k));
 const gym=data.gyms.filter(g=>g.chapterKey===c.key);
 const trainers=data.trainers.filter(t=>t.chapterKey===c.key);
 const prev=data.chapters[c.index-2],next=data.chapters[c.index];
 return breadcrumbs([link('/unova','Unova'),link('/unova/capitulos','Capítulos'),esc('Capítulo '+c.index)])+
 intro('Capítulo '+c.index+' · '+c.title,c.plannedPhase+' · narrativa planejada, sem eventos jogáveis confirmados.')+
 section('Missão e gates simbólicos',
  note('Missão: '+(c.missionKey||'pendente')+'. Requisito de transição: '+(c.requiredMissionKey||'início da jornada')+
   '. Flags de conclusão são simulações; nenhuma recompensa ou batalha real é ativada.')+
  note('Área de referência: '+(areaBy(data,c.referenceAreaKey)?.name||'pendente')+
   '. Grupo editorial por fase, não roteiro físico entre mapas.'))+
 section('Áreas associadas · '+areas.length,cards(areas,a=>areaCard(a,c)))+
 (gym.length?section('Ginásios deste capítulo',cards(gym,g=>card(g.badge+' · '+g.leaderKey,
  note('Líder e insígnia de referência; equipe, nível e batalha pendentes.')+
  '<div class="unova-guide-context">'+linkArea(areaBy(data,g.gymAreaKey),'Abrir ginásio')+'</div>'))):'')+
 (trainers.length?section('Encontros com rivais e Plasma',cards(trainers,t=>card(t.actor,
   note('Confronto previsto no contrato '+t.key+'. PBS e níveis ainda pendentes.')+
   '<div class="unova-guide-context">'+linkArea(areaBy(data,t.areaKey),'Área relacionada')+'</div>'))):'')+
 section('Navegar na história','<nav class="unova-guide-context" aria-label="Capítulos adjacentes">'+
  (prev?linkChapter(prev,'Anterior'):'')+' '+(next?linkChapter(next,'Próximo'):'')+
  ' '+link('/unova/capitulos','Todos os capítulos')+'</nav>');
};
const gymCard=(data,g)=>card(g.index+'º ginásio · '+g.badge,
 note('Liderança: '+g.leaderKey+' · '+g.sourcePhase+
   '. Equipe, níveis e insígnia nativa: pendentes.')+
 '<div class="unova-guide-context">'+linkArea(areaBy(data,g.gymAreaKey),'Abrir ginásio')+
 ' '+linkChapter(chapterBy(data,g.chapterKey),'Capítulo')+'</div>','GINÁSIO NÃO INSTALADO');
const peopleCard=(data,n)=>card(n.name,note(n.role+' · sprite, posição e evento ainda não verificados')+
 '<div class="unova-guide-context">'+linkArea(areaBy(data,n.areaKey),'Área de referência')+'</div>','NPC PLANEJADO');
const trainerCard=(data,t)=>card(t.actor,note('Contrato: '+t.key+' · '+t.policy+
  '. Sem equipe, nível, MapID ou Trainer PBS confirmado.')+
 '<div class="unova-guide-context">'+linkArea(areaBy(data,t.areaKey),'Local citado')+
 ' '+linkChapter(chapterBy(data,t.chapterKey),'Capítulo')+'</div>','CONFRONTO DE REFERÊNCIA');
const noGame=()=>note('Estas fichas organizam os contratos existentes, mas nenhum MapID, taxa, Pokémon selvagem, nível fixo, equipe, evento, NPC instalado ou SaveData real de Unova foi confirmado.');
export function unovaGuidePage(data,sectionKey='home',id=null){
 validateUnovaGuide(data);
 const known=new Set(nav.map(([key])=>key));
 if(!known.has(sectionKey)&&!['area','capitulo'].includes(sectionKey))invalid('unknown guide page');
 let content;
 if(sectionKey==='area'){
  const a=areaBy(data,id);if(!a)invalid('unknown area');
  content=areaDetails(data,a);
 }else if(sectionKey==='capitulo'){
  const c=chapterBy(data,id);if(!c)invalid('unknown chapter');
  content=chapterDetails(data,c);
 }else if(sectionKey==='capitulos'){
  content=intro('História e progressão de Unova','12 capítulos de campanha e pós-jogo, com ligações narrativas auditadas.')+
   section('Capítulos contratados',cards(data.chapters,chapterCard));
 }else if(sectionKey==='areas'){
  content=intro('74 áreas de Unova','Cidades, rotas, cavernas, ginásios e locais opcionais: todos ainda planejados.')+
   section('Todas as 74 referências',cards(data.areas,a=>areaCard(a,chapterBy(data,a.chapterKey))));
 }else if(sectionKey==='ginasios'){
  content=intro('Oito ginásios de Unova White','Contratos da campanha White por capítulo e insígnia; nenhum combate nativo disponível.')+
   section('Insígnias e líderes de referência',cards(data.gyms,g=>gymCard(data,g)));
 }else if(sectionKey==='liga'){
  content=intro('Elite Four, N e Ghetsis','Elite Four e Castelo de N documentados como eventos simbólicos.')+
   section('Quatro membros da Elite Four',cards(data.elite,e=>card(e.name,
    note('Especialidade: '+e.specialty+' · equipe, níveis e Trainer PBS pendentes')+
    '<div class="unova-guide-context">'+linkArea(areaBy(data,e.areaKey),'Área da Liga')+
    ' '+linkChapter(chapterBy(data,e.chapterKey),'Capítulo')+'</div>','ELITE FOUR PLANEJADA')))+
   section('Castelo de N e desfecho (apenas contratos)',cards(data.castle,e=>card(e.description,
    note('Evento simbólico '+e.key+'. Sem batalha, captura ou créditos executados.')+
    '<div class="unova-guide-context">'+linkArea(areaBy(data,e.areaKey),'Castelo')+'</div>')));
 }else if(sectionKey==='npcs'){
  content=intro('NPCs de referência','Catálogo SP04 de personagens; nenhum sprite ou evento aprovado para o Game.exe.')+
   section(data.npcs.length+' personagens documentados',cards(data.npcs,n=>peopleCard(data,n)));
 }else if(sectionKey==='treinadores'){
  content=intro('Rivais, Plasma e treinadores','Referências G03.3 de encontros planejados; nenhuma equipe PBS compilada.')+
   section(data.trainers.length+' confrontos auditados',cards(data.trainers,t=>trainerCard(data,t)));
 }else if(sectionKey==='pendencias'){
  content=intro('Pendências de Unova','O catálogo não autoriza instalar mapas ou usar dados de combate no jogo.')+
   section('O que falta comprovar',cards(Object.entries(data.pending).map(([k,v])=>({key:k,val:v})),
    p=>card(p.key.replaceAll(/([A-Z])/g,' $1').trim(),note(String(p.val)),'NÃO VERIFICADO')))+
   section('Proveniência',note(data.chapterGroupingExplanation)+noGame()+
    link('/unova-progresso','Acompanhar Barra G no GitHub'));
 }else{
  content=intro('Guia de Unova White','Explore as 74 áreas e a campanha auditadas apenas como planejamento, sem acesso jogável ao Game.exe.')+
   '<div class="unova-guide-stats">'+[
    [data.counts.areas,'Áreas planejadas'],[data.counts.chapters,'Capítulos'],
    [data.counts.gyms,'Ginásios'],[data.counts.eliteFour,'Elite Four'],
    [data.counts.npcs,'NPCs de referência'],[data.counts.trainerReferences,'Confrontos referenciados']
   ].map(([n,label])=>'<div class="unova-guide-stat"><strong>'+n+'</strong><span>'+esc(label)+'</span></div>').join('')+'</div>'+
   section('Seguir a história',cards(data.chapters,chapterCard))+
   section('Áreas de referência',cards(data.areas.slice(0,8),a=>areaCard(a,chapterBy(data,a.chapterKey))))+
   '<div class="unova-guide-actions">'+link('/unova/areas','Consultar todas as 74 áreas')+
   link('/unova/ginasios','Líderes e insígnias')+
   link('/unova/liga','Elite Four e desfecho')+'</div>'+
   section('Estado da implementação',noGame()+note(data.chapterGroupingExplanation)+
    link('/unova-progresso','Barra G: trabalho no GitHub'));
 }
 const navHtml='<nav class="unova-guide-nav" aria-label="Seções do guia de Unova">'+
  nav.map(([key,label])=>'<a class="filter-chip'+(sectionKey===key?' active':'')+
   '" href="'+esc(unovaGuideUrl(key))+'"'+(sectionKey===key?' aria-current="page"':'')+
   '>'+esc(label)+'</a>').join('')+'</nav>';
 return '<div class="container detail-container unova-guide-page">'+
 '<a class="back-link" href="/regioes">← Circuito de regiões</a>'+
 '<div class="unova-guide-alert" role="note"><strong>UNOVA PLANEJADA · NÃO JOGÁVEL</strong>'+
 '<p>'+esc(data.warning)+'</p></div>'+navHtml+content+
 '<footer class="unova-guide-footer">'+noGame()+
 '<div class="unova-guide-context">'+link('/unova-progresso','Ver progresso GitHub')+
 ' '+link('/regioes','Voltar às regiões')+'</div></footer></div>';
}
