import {esc} from './utils.js';
import {regionPicker} from './regions.js';

const labels={localizacoes:'Localizações',treinadores:'Treinadores',chefes:'Líderes de ginásio'};

export async function loadPilotCatalog(region){
  const response=await fetch('/data/'+region+'-pilot.json');
  if(!response.ok)throw new Error('pilot-catalog-unavailable');
  const data=await response.json();
  if(data.schema!==1||data.region!==region)throw new Error('pilot-catalog-invalid');
  return data;
}

export function pilotIndex(data,route){
  const title=labels[route]+' de '+data.name;
  const rows=route==='localizacoes'?data.locations:data.trainers.filter(row=>row.leader===(route==='chefes'));
  const list=rows.map(row=>{
    const details=row.teams
      ? row.teams.map(team=>'<li>'+esc(team.label)+': '+team.pokemon.map(p=>esc(p[0])).join(', ')+'</li>').join('')
      : Object.entries(row.encounters||{}).map(([method,slots])=>'<li>'+esc(method)+': '+slots.map(p=>esc(p[0])+' (Nv. '+esc(p[1])+'–'+esc(p[2])+', '+esc(p[3])+'%)').join(', ')+'</li>').join('');
    return '<section class="panel region-entry"><h2>'+esc(row.name)+'</h2>'+
      (row.area?'<p>'+esc(row.area)+(row.badge?' · '+esc(row.badge):'')+'</p>':'')+
      (details?'<ul>'+details+'</ul>':'')+
      (row.teams?'<p class="data-note">Níveis dinâmicos no motor Blue.</p>':'')+
      '<span class="content-pending-tag pending-validation">Em validação</span></section>';
  }).join('');
  const empty='<section class="panel"><p>O trecho instalado ainda não inclui um ginásio.</p></section>';
  return '<div class="container detail-container">'+regionPicker(route,data.region)+
    '<header class="article-heading"><h1>'+esc(title)+'</h1><p>'+esc(data.note)+'</p></header>'+
    '<nav class="region-picker" aria-label="Catálogo regional">'+Object.entries(labels).map(([key,label])=>
      '<a class="filter-chip" href="/'+key+'?regiao='+esc(data.region)+'"'+(key===route?' aria-current="page"':'')+'>'+esc(label)+'</a>').join('')+
    '</nav><div class="region-entries">'+(list||empty)+'</div></div>';
}
