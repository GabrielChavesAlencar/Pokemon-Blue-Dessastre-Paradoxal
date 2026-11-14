import {esc,icon,sprite} from './utils.js';
import {teamPokemon} from './story.js';

let cache;
export async function loadStrongestTeams(fetcher=fetch){
  if(!cache){
    const r=await fetcher('/data/strongest-teams.json');
    if(!r.ok)throw new Error('strongest-teams-unavailable');
    const data=await r.json();
    if(data.schema!==1||!Array.isArray(data.teams))throw new Error('strongest-teams-invalid');
    cache=data;
  }
  return cache;
}
const regions={KANTO:'Kanto',JOHTO:'Johto',HOENN:'Hoenn',SINNOH:'Sinnoh'};
const roles=[['gym','Líderes de ginásio · revanches'],['elite','Elite Four'],['champion','Campeões'],['extra','Desafios extras']];
const sourceLink=db=>'<a class="text-link" href="'+esc(db.source.url)+'" target="_blank" rel="noopener noreferrer">Estudo completo dos times mais fortes '+icon('arrow')+'</a>';
const scaling='<p class="data-note">Níveis dinâmicos: o jogo calcula o nível dos adversários usando o maior nível da equipe do jogador, a dificuldade e as insígnias/esmeraldas conquistadas. Este catálogo apresenta espécies históricas de referência, não revanches já implementadas.</p>';
const sprites=(model,t)=>'<div class="regular-pokemon-strip">'+[...new Set(t.variants.flatMap(v=>v.species))].slice(0,9).map(id=>{const p=model.byId.get(id);return p?'<img src="'+esc(sprite(p))+'" loading="lazy" alt="'+esc(p.name)+'"/>':'<span>'+esc(id)+'</span>';}).join('')+'</div>';
export function leagueIndex(model,db,requested='KANTO'){
  const region=Object.hasOwn(regions,requested)?requested:'KANTO';
  const menu='<nav class="region-picker" aria-label="Liga por região">'+Object.entries(regions).map(([r,name])=>'<a class="filter-chip'+(r===region?' active':'')+'" href="/liga?regiao='+r.toLowerCase()+'"'+(r===region?' aria-current="page"':'')+'>'+name+'</a>').join('')+'</nav>';
  const groups=roles.map(([role,label])=>{
    const matches=db.teams.filter(t=>t.region===region&&t.role===role);
    return matches.length?'<section class="section"><h2>'+esc(label)+'</h2><div class="regular-grid">'+matches.map(t=>'<a class="regular-card" href="/liga/'+encodeURIComponent(t.id)+'"><span class="mini-label">'+esc(t.sourceGame)+'</span><h3>'+esc(t.name)+'</h3>'+sprites(model,t)+'<span class="content-pending-tag">Ainda não adicionado</span><span class="regular-card-action">Ver equipe'+(t.variants.length>1?'s':'')+' '+icon('arrow')+'</span></a>').join('')+'</div></section>':'';
  }).join('');
  return '<div class="container detail-container"><header class="article-heading"><span class="eyebrow">LIGAS · REFERÊNCIA DOCUMENTAL</span><h1>Elite Four, campeões e times mais fortes</h1><p>Times oficiais de referência para futuras revanches, separados por época e função. As equipes de campanha do piloto podem ser diferentes.</p></header>'+menu+scaling+groups+'<p class="data-note">Fonte: '+sourceLink(db)+'</p></div>';
}
export function leagueDetail(model,db,entry,details){
  if(!entry)throw new Error('not-found');
  return '<div class="container detail-container"><a class="back-link" href="/liga?regiao='+entry.region.toLowerCase()+'">← Liga de '+esc(regions[entry.region])+'</a>'+
    '<header class="article-heading"><span class="eyebrow">'+esc(entry.sourceGame)+'</span><h1>'+esc(entry.name)+'</h1><p>Referência histórica mais forte. Não significa que a revanche já foi programada no jogo.</p></header>'+
    '<p><span class="content-pending-tag">Ainda não adicionado</span> · Composição histórica da revanche, não equipe confirmada no jogo.</p>'+
    scaling+entry.variants.map(v=>'<section class="section"><h2>'+esc(v.label)+'</h2><div class="story-pokemon-grid">'+v.species.map(species=>teamPokemon({species,dynamicLevel:true,referenceOnly:true},model,details)).join('')+'</div></section>').join('')+
    '<p class="data-note">Seção '+esc(entry.studySection)+' · '+sourceLink(db)+'</p></div>';
}
