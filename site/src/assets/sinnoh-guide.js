// CH17 — navigable Sinnoh planning guide. All data is generated from CH11–CH16.
import {esc,icon} from './utils.js';
import {validateSinnohGuide,filterSinnohGuide,sinnohGuideUrl,sinnohPendingGroups} from './sinnoh-search.js';

let cache;
export async function loadSinnohGuide(fetcher=fetch){
  if(!cache){
    const response=await fetcher('/data/sinnoh-guide.json');
    if(!response.ok)throw new Error('sinnoh-guide-unavailable');
    const value=await response.json();
    validateSinnohGuide(value);
    cache=value;
  }
  return cache;
}

const tabs=[
 ['visao','Visão geral'],['areas','Áreas'],['treinadores','Treinadores'],
 ['ginasios','8 ginásios'],['liga','Elite Four e Cynthia'],
 ['itens','Itens e HMs'],['progresso','História e progresso'],
 ['pendencias','Pendências']
];
const tabHref=key=>'/sinnoh?aba='+key;
const pending='<span class="content-pending-tag">Ainda não adicionado</span>';
const note=(text)=>'<p class="data-note">'+esc(text)+'</p>';
const species=items=>'<span class="sinnoh-species">'+items.map(esc).join(' · ')+'</span>';
const cards=(items,render)=>'<div class="sinnoh-guide-grid">'+items.map(render).join('')+'</div>';
const summary=(num,label)=>'<div class="sinnoh-guide-stat"><strong>'+num+'</strong><span>'+esc(label)+'</span></div>';
const article=(title,body,kicker='REFERÊNCIA PLANEJADA')=>
  '<article class="sinnoh-guide-card"><span class="eyebrow">'+esc(kicker)+'</span><h3>'+esc(title)+'</h3>'+body+pending+'</article>';

const contextLink=(tab,params,label)=>
  '<a class="text-link" href="'+esc(sinnohGuideUrl(tab,params))+'">'+esc(label)+' '+icon('arrow')+'</a>';
const context=(...links)=>'<nav class="sinnoh-guide-context" aria-label="Relações com outros guias">'+links.join('')+'</nav>';
const emptyResult='<p class="sinnoh-guide-empty" role="status">Nenhuma referência encontrada. Tente outra busca ou remova os filtros. Os dados continuam planejados e não jogáveis.</p>';
const cardResults=(items,render)=>items.length?cards(items,render):emptyResult;
const searchFilters={
  areas:[['todas','Todas as referências'],['sem-fase','Fase a auditar'],['com-especies','Com espécies candidatas'],['sem-especies','Sem espécies candidatas']],
  treinadores:[['todas','Todos os treinadores'],['com-area','Área citada na fonte'],['sem-area','Sem área citada']],
  liga:[['todas','Toda a Liga'],['com-revanche','Com revanche Platinum'],['sem-revanche','Sem revanche documentada']],
  itens:[['todas','Todos os HMs'],['sem-coleta','Coleta não confirmada']]
};
function filterForm(tab,phase,filtered){
  if(!['areas','treinadores','ginasios','liga','itens','progresso','pendencias'].includes(tab))return '';
  const choices=searchFilters[tab]||[];
  const typeChoices=[['todos','Todos os tipos'],...sinnohPendingGroupsSafe(tab)];
  const selection=choices.length?'<label>Tipo de pendência<select name="pendencia">'+
    choices.map(([key,label])=>'<option value="'+esc(key)+'"'+(filtered.pendencia===key?' selected':'')+'>'+esc(label)+'</option>').join('')+
    '</select></label>':'';
  const kind=tab==='pendencias'?'<label>Categoria<select name="tipo">'+
    typeChoices.map(([key,label])=>'<option value="'+esc(key)+'"'+(filtered.tipo===key?' selected':'')+'>'+esc(label)+'</option>').join('')+'</select></label>':'';
  return '<form class="sinnoh-guide-filters" data-sinnoh-filters method="get" action="/sinnoh" role="search" aria-label="Pesquisar referências planejadas">'+
    '<input type="hidden" name="aba" value="'+esc(tab)+'">'+
    (tab==='areas'&&phase!=='all'?'<input type="hidden" name="fase" value="'+esc(phase)+'">':'')+
    '<label>Buscar no guia<input type="search" name="busca" maxlength="100" autocomplete="off" value="'+esc(filtered.busca)+'" placeholder="Nome, local, espécie, insígnia…" aria-label="Buscar referências de Sinnoh"></label>'+
    selection+kind+
    '<button type="submit" class="button button-primary">Pesquisar</button>'+
    '<a class="button button-secondary" href="'+esc(sinnohGuideUrl(tab,tab==='areas'?{fase:phase}:{}))+'">Limpar filtros</a>'+
    '</form>';
}
const pendingFilterLabels={
  areas:'Mapas e áreas',treinadores:'Treinadores e NPCs',
  equipes:'Ginásios, Elite Four e Cynthia',itens:'HMs e permissões',
  historia:'Galactic, Cyrus e Liga',encontros:'Encontros selvagens',
  musica:'Chaves musicais'
};
const sinnohPendingGroupsSafe=tab=>tab==='pendencias'?
  Object.entries(pendingFilterLabels):[];
const resultCount=filtered=>'<p class="sinnoh-guide-result-count" role="status" aria-live="polite">'+
  filtered.count+' referência'+(filtered.count===1?'':'s')+' exibida'+(filtered.count===1?'':'s')+
  (filtered.busca?' para “'+esc(filtered.busca)+'”':'')+'. Todas permanecem pendentes de prova nativa.</p>';


export function sinnohGuidePage(data,requested='visao',phase='all',options={}){
  validateSinnohGuide(data);
  const tab=tabs.some(([key])=>key===requested)?requested:'visao';
  const filtered=filterSinnohGuide(data,tab,{...options,fase:phase});
  const selected=filtered.fase;
  const navigation='<nav class="sinnoh-guide-tabs" aria-label="Seções do guia de Sinnoh">'+
    tabs.map(([key,label])=>'<a class="filter-chip'+(key===tab?' active':'')+'" href="'+
      tabHref(key)+'"'+(key===tab?' aria-current="page"':'')+'>'+esc(label)+'</a>').join('')+'</nav>';
  let section='';
  if(tab==='visao'){
    section='<section class="section"><div class="section-heading"><div><span class="eyebrow">CATÁLOGOS CH11–CH16</span>'+
      '<h2>Uma região em planejamento<span>.</span></h2></div></div>'+
      '<div class="sinnoh-guide-stats">'+summary(data.counts.areas,'Áreas de referência')+
      summary(data.counts.trainers,'Treinadores a auditar')+
      summary(data.counts.gyms,'Ginásios')+summary(data.counts.eliteFour,'Elite Four')+
      summary(data.counts.hmItems,'HMs regionais')+summary(data.counts.storySteps,'Etapas de história')+'</div>'+
      '<div class="sinnoh-guide-grid">'+tabs.filter(([key])=>key!=='visao').map(([key,label])=>
      '<a class="sinnoh-guide-card sinnoh-guide-link" href="'+tabHref(key)+'">'+
      '<span class="eyebrow">GUIA DE REFERÊNCIA</span><h3>'+esc(label)+'</h3>'+
      '<p>Consultar planejamento, restrições e pendências verificadas.</p>'+
      '<span class="text-link">Explorar '+icon('arrow')+'</span></a>').join('')+'</div></section>'+
      '<section class="section"><h2>O que não foi instalado</h2>'+
      note('Os registros de encontros, versões de treinadores, insígnias, itens, músicas e viagens dependem de eventos e PBS verificados no Game.exe. As equipes de Platinum não equivalem às equipes do Blue.')+
      note('Normal '+data.balance.normalPercent+'% / Master '+data.balance.masterPercent+
       '%: '+data.balance.note)+
      note('Músicas simbólicas: '+data.music.cueCount+
       '. Nenhuma faixa licenciada, MapID ou hook musical Sinnoh foi instalada.')+'</section>';
  }else if(tab==='areas'){
    const byPhase=filtered.items;
    const filters='<nav class="sinnoh-guide-phase" aria-label="Filtrar áreas por fase">'+
      '<a href="'+esc(sinnohGuideUrl('areas',{busca:filtered.busca,pendencia:filtered.pendencia}))+
       '" class="filter-chip'+(selected==='all'?' active':'')+'">Todas</a>'+
      data.phases.map(p=>'<a href="'+esc(sinnohGuideUrl('areas',{
        fase:String(p.number),busca:filtered.busca,pendencia:filtered.pendencia}))+
        '" class="filter-chip'+(selected===String(p.number)?' active':'')+'">Fase '+p.number+'</a>').join('')+
      '<a href="'+esc(sinnohGuideUrl('areas',{fase:'sem-fase',busca:filtered.busca,
        pendencia:filtered.pendencia}))+'" class="filter-chip'+
      (selected==='sem-fase'?' active':'')+'">Fase a auditar</a></nav>';
    section='<section class="section"><h2>Áreas previstas · '+byPhase.length+'</h2>'+
      note('MapIDs, posições, acesso e encontros permanecem não verificados. Espécies abaixo são candidatas da auditoria de habitats, sem taxas ou níveis publicados.')+
      filterForm(tab,selected,filtered)+filters+resultCount(filtered)+
      cardResults(byPhase,a=>article(a.name,
        '<p>'+esc(a.phase===null?'Fase a auditar':'Fase '+a.phase)+' · '+esc(a.notes)+'</p>'+
        (a.speciesCandidates.length?'<p>Referências de espécies: '+species(a.speciesCandidates)+
         '</p><small>Espécies a auditar · nenhuma taxa/slot confirmado.</small>':'<p>Encontros nativos: pendentes de conferência.</p>')+
        context(
          contextLink('treinadores',{},'Treinadores de referência (vínculo não confirmado)'),
          contextLink('pendencias',{tipo:'areas'},'Auditar mapas')),
        'ÁREA · '+(a.phase===null?'SEM FASE':String(a.phase).padStart(2,'0'))))+'</section>';
  }else if(tab==='treinadores'){
    section='<section class="section"><h2>Treinadores a localizar · '+filtered.count+'</h2>'+
      note('Grupos e personagens da campanha de Platinum para auditoria futura de mapas, NPCs e PBS. Nenhuma equipe ou versão de treinador foi considerada compilada.')+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      cardResults(filtered.items,t=>article(t.name,
        '<p>'+esc(t.area||'Local de encontro a auditar')+'</p>'+
        (t.notes?'<p>'+esc(t.notes)+'</p>':'')+
        context(contextLink('areas',{},'Conferir áreas'),
          contextLink('pendencias',{tipo:'treinadores'},'Vínculos PBS pendentes')),
        'TREINADOR · REFERÊNCIA'))+'</section>';
  }else if(tab==='ginasios'){
    section='<section class="section"><h2>Oito ginásios de Sinnoh</h2>'+
      note('Ordem histórica de Platinum. Fantina é a terceira (Relic) e Maylene a quarta (Cobble). Espécies históricas não são times PBS instalados nem recebem níveis fixos no site.')+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      cardResults(filtered.items,t=>article(t.name,
        '<p>'+esc(t.city||'Cidade a conferir')+' · Insígnia '+esc(t.badge)+'</p>'+
        '<p>Equipe de referência: '+species(t.speciesReference)+'</p>'+
        '<p>Full Power do Blue: não verificado · PBS: não instalado.</p>'+
        context(contextLink('itens',{busca:t.badge},'HM vinculado à insígnia'),
          contextLink('areas',{busca:t.city||''},'Buscar cidade de referência')),
        'GINÁSIO '+String(t.order).padStart(2,'0')))+'</section>';
  }else if(tab==='liga'){
    section='<section class="section"><h2>Elite Four e Cynthia</h2>'+
      note('Composição histórica Platinum; revanches históricas não são variantes Full Power do Blue. A Liga só termina após evento independente do Hall of Fame confirmado.')+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      cardResults(filtered.items,t=>article(t.name,
        '<p>Primeira equipe de referência: '+species(t.speciesReference)+'</p>'+
        (t.rematchSpeciesReference?'<p>Revanche histórica: '+species(t.rematchSpeciesReference)+'</p>':'')+
        '<p>Equipe PBS e batalha nativa: pendentes.</p>'+
        context(contextLink('progresso',{},'Progressão da Liga'),
          contextLink('pendencias',{tipo:'equipes'},'Conferir pendências PBS')),
        t.role==='CHAMPION'?'CAMPEÃ':'ELITE FOUR '+t.order))+'</section>';
  }else if(tab==='itens'){
    section='<section class="section"><h2>Itens e permissões regionais</h2>'+
      note('O item HM precisa ser obtido dentro de Sinnoh, e a insígnia local precisa ter sido conquistada. Ter o mesmo item ou uma insígnia em outra região não libera o golpe de campo aqui.')+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      cardResults(filtered.items,r=>article(r.label,
        '<p>Exige Insígnia '+esc(r.badge)+' de Sinnoh.</p>'+
        '<p>Entrega do HM: não confirmada; permissão: não ativada.</p>'+
        context(contextLink('ginasios',{busca:r.badge},'Líder da insígnia'),
          contextLink('pendencias',{tipo:'itens'},'Checar coleta nativa')),
        'ITEM-CHAVE · HM'))+'</section>';
  }else if(tab==='progresso'){
    section='<section class="section"><h2>História e progressão planejadas</h2>'+
      note('Estes checkpoints não representam o save de quem está jogando. São contratos para futuras implementações; não há vitórias, mapas ou desbloqueios certificados.')+
      cards(data.phases,p=>article('Fase '+p.number+' · '+p.title,
        '<p>'+p.areaCount+' áreas de referência · '+p.eventCount+' eventos previstos.</p>'+
        context(contextLink('areas',{fase:String(p.number)},'Áreas desta fase')),
        'ROTEIRO PLATINUM'))+
      '<h2 class="sinnoh-guide-steps-title">Galactic, Cyrus e Liga: '+data.steps.length+' checkpoints</h2>'+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      (filtered.items.length?'<ol class="sinnoh-guide-steps">'+filtered.items.map(st=>
        '<li><strong>'+esc(st.title)+'</strong><span>Fase '+esc(st.phase)+
        ' · Evento não instalado'+(st.requiresBadges.length?' · Exige '+esc(st.requiresBadges.join(', ')):'')+
        (st.engineHallOfFameRequired?' · Confirmação independente do Hall of Fame obrigatória':'')+
        '</span>'+context(
          contextLink('areas',{fase:String(st.phase)},'Consultar áreas da fase'),
          contextLink('liga',{},'Referências da Liga'))+'</li>').join('')+'</ol>':emptyResult)+
      note('Viagem pós-Liga continua bloqueada sem origem de Sinnoh e destino físico verificados. Não criar teleporte automático para Hoenn ou Unova.')+
      '</section>';
  }else if(tab==='pendencias'){
    section='<section class="section"><h2>Pendências documentadas</h2>'+
      note('Todas as categorias abaixo representam trabalhos ainda sem comprovação em dados nativos. O catálogo do portal não instala mapas, versões de treinadores, encontros ou itens.')+
      filterForm(tab,selected,filtered)+resultCount(filtered)+
      cardResults(filtered.items,r=>article(r.label,
        '<p>'+esc(r.count)+' registros de referência em auditoria.</p>'+
        '<p>'+esc(r.description)+'</p>'+
        context(contextLink(r.tab,{},'Abrir guia correspondente'),
          contextLink('progresso',{},'Ver etapas planejadas')),
        'PENDÊNCIA · CH11–CH16'))+'</section>';
  }
  return '<div class="container detail-container sinnoh-guide-page">'+
    '<a class="back-link" href="/guias">← Todos os guias</a>'+
    '<header class="article-heading"><span class="eyebrow">SINNOH · PLANEJADA · NÃO JOGÁVEL</span>'+
    '<h1>Guia de Sinnoh</h1>'+
    '<p>'+esc(data.meaning)+'</p>'+
    '<p><span class="content-pending-tag">Ainda não adicionado ao Game.exe/JoiPlay</span></p>'+
    '</header>'+navigation+section+
    '<section class="sinnoh-guide-footer"><h2>Estado da implementação</h2>'+
      note('Dados organizados a partir das auditorias CH11–CH16. Isso não comprova instalação de mapas, NPCs, treinadores, encontros, itens ou músicas.')+
      contextLink('pendencias',{},'Ver pendências no guia')+
      '<p><a class="text-link" href="/pendencias?regiao=sinnoh">Abrir backlog regional completo '+icon('arrow')+'</a></p>'+
      '</section></div>';
}
