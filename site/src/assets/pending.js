import {esc} from './utils.js';

let cached;
const titleCase={KANTO:'Kanto',JOHTO:'Johto',HOENN:'Hoenn',SINNOH:'Sinnoh'};
const categories={
  localizacoes:['areas'],
  treinadores:['trainers'],
  chefes:['leaders'],
  liga:['elite_four','champion']
};
const categoryNames={
  areas:'Áreas e interiores',trainers:'Treinadores e grupos a auditar',
  leaders:'Líderes de ginásio',elite_four:'Elite Four',champion:'Campeão'
};

export async function loadPendingRegions(fetcher=fetch){
  if(!cached){
    const response=await fetcher('/data/pending-regions.json');
    if(!response.ok)throw new Error('pending-regions-unavailable');
    const data=await response.json();
    if(data.schema!==1||data.state!=='REFERENCE_NOT_NATIVE_GAMEPLAY'||
      !['KANTO','JOHTO','HOENN','SINNOH'].every(region=>data.regions?.[region]))
      throw new Error('pending-regions-invalid');
    cached=data;
  }
  return cached;
}

export const pendingLabel=()=>'<span class="content-pending-tag">Ainda não adicionado</span>';

// The public catalog is not the native runtime. "Not added" below means
// not yet confirmed as added AND playable. Do not silently auto-publish PBS.
const normalize=name=>String(name||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
  .toLowerCase().replace(/\brotas?\s+/g,'route ')
  .replace(/\s+[—–]\s+.*$/,'').replace(/[^a-z0-9]/g,'');

export function pendingBlocks(db,region,route,{excludeNames=[]}={}){
  const source=db.regions?.[region];
  if(!source)return '';
  const excluded=new Set(excludeNames.map(normalize));
  const names=categories[route]||[];
  const blocks=names.map(category=>{
    const rows=(source[category]||[]).filter(item=>!excluded.has(normalize(item.name)));
    if(!rows.length)return '';
    return '<details class="pending-group" open><summary>'+esc(categoryNames[category])+
      ' · '+rows.length+' pendência'+(rows.length===1?'':'s')+'</summary>'+
      '<div class="pending-grid">'+rows.map(row=>
        '<article class="pending-card"><h3>'+esc(row.name)+'</h3>'+
          (row.city?'<p>'+esc(row.city)+(row.badge?' · Insígnia '+esc(row.badge):'')+'</p>':'')+
          (row.notes?'<p>'+esc(row.notes)+'</p>':'')+pendingLabel()+'</article>'
      ).join('')+'</div></details>';
  }).filter(Boolean);
  if(!blocks.length)return '';
  return '<section class="section pending-content" aria-label="Pendências de '+esc(titleCase[region])+'">'+
    '<div class="section-heading"><div><span class="eyebrow">PRÓXIMAS FASES · '+esc(titleCase[region].toUpperCase())+
    '</span><h2>Conteúdo ainda não adicionado</h2>'+
    '<p>'+esc(db.meaning)+'</p></div></div>'+
    blocks.join('')+
    '<p class="data-note">Lista de referência, não implementação no Game.exe. '+
    'Os nomes dos treinadores agrupados precisam ser extraídos dos PBS/mapas reais. '+
    '<a href="https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/49" '+
    'target="_blank" rel="noopener noreferrer">Acompanhar implantação por etapas</a>.</p></section>';
}

export function pendingPage(db,requested='KANTO'){
  const region=db.regions[requested]?requested:'KANTO';
  const tabs=Object.entries(titleCase).map(([key,name])=>
    '<a class="filter-chip'+(key===region?' active':'')+'" href="/pendencias?regiao='+key.toLowerCase()+
    '"'+(key===region?' aria-current="page"':'')+'>'+name+'</a>').join('');
  const r=db.regions[region], counts=Object.entries({
    'Áreas e interiores':r.areas.length,
    'Treinadores e grupos':r.trainers.length,
    'Líderes':r.leaders.length,
    'Elite Four':r.elite_four.length,
    'Campeão':r.champion.length
  }).map(([label,count])=>'<span class="pending-count">'+esc(label)+' <strong>'+count+'</strong></span>').join('');
  return '<div class="container detail-container"><header class="article-heading">'+
    '<span class="eyebrow">BACKLOG DO JOGO · SEM INSTALAÇÃO AUTOMÁTICA</span>'+
    '<h1>Áreas, treinadores e Liga pendentes</h1>'+
    '<p>'+esc(db.meaning)+'</p></header>'+
    '<nav class="region-picker" aria-label="Região das pendências">'+tabs+'</nav>'+
    '<div class="pending-counters">'+counts+'</div>'+
    pendingBlocks(db,region,'localizacoes')+
    pendingBlocks(db,region,'treinadores')+
    pendingBlocks(db,region,'chefes')+
    pendingBlocks(db,region,'liga')+
    '<p class="data-note">Referência: '+esc(r.doc)+' · '+esc(r.game)+
    '. Sem coordenadas, MapIDs, equipes ou níveis inventados.</p></div>';
}

export function pendingOnlyRegion(db,region,route){
  const title={localizacoes:'Localizações',treinadores:'Treinadores',chefes:'Líderes'}[route]||'Conteúdo';
  const choices=Object.entries({localizacoes:'Localizações',treinadores:'Treinadores',chefes:'Ginásios',liga:'Elite Four'})
    .map(([key,label])=>'<a class="filter-chip'+(key===route?' active':'')+'" href="/'+key+'?regiao='+
      region.toLowerCase()+'">'+label+'</a>').join('');
  return '<div class="container detail-container"><header class="article-heading">'+
    '<span class="eyebrow">'+esc(titleCase[region].toUpperCase())+' · EM PREPARAÇÃO</span>'+
    '<h1>'+title+' de '+esc(titleCase[region])+'</h1>'+
    '<p>Nenhum registro desta página está confirmado como integrado ao jogo. '+
    'Use os cartões abaixo como checklist de implantação, não como localizações jogáveis.</p></header>'+
    '<nav class="region-picker" aria-label="Conteúdo de '+esc(titleCase[region])+'">'+choices+'</nav>'+
    pendingBlocks(db,region,route)+'</div>';
}
