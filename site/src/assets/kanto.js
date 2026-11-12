import {esc,icon,sprite} from './utils.js';
import {teamPokemon} from './story.js';
import {regionPicker} from './regions.js';

let catalog;
export async function loadKanto(){
  if(!catalog){
    const response=await fetch('/data/kanto.json');
    if(!response.ok) throw new Error('kanto-unavailable');
    catalog=await response.json();
  }
  return catalog;
}

const pages={
  localizacoes:'Localizações',
  treinadores:'Treinadores',
  chefes:'Líderes de ginásio'
};
const methods={
  Land:'Grama',LandDay:'Grama durante o dia',LandNight:'Grama à noite',LandMorning:'Grama pela manhã',
  Water:'Surf',OldRod:'Old Rod',GoodRod:'Good Rod',SuperRod:'Super Rod',
  Cave:'Caverna',CaveDay:'Caverna durante o dia',CaveNight:'Caverna à noite',RockSmash:'Rock Smash'
};
// The exact eight local Kanto badge rewards are pinned by regions.json.
// Never claim that every gym awards Boulder (the former generic placeholder).
export const KANTO_GYM_REWARDS=Object.freeze({
  Brock:'Boulder',Misty:'Cascade','Lt. Surge':'Thunder',Erika:'Rainbow',
  Koga:'Soul',Sabrina:'Marsh',Blaine:'Volcano',Giovanni:'Earth'
});
const trainerLink=trainer=>'/'+(trainer.leader?'chefes':'treinadores')+'/'+encodeURIComponent(trainer.id);
const locationLink=location=>'/localizacoes/'+encodeURIComponent(location.id);
const link=(href,label)=>'<a class="text-link" href="'+esc(href)+'">'+esc(label)+' '+icon('arrow')+'</a>';

function layout(data,page,title,body,detail=false){
  const header='<header class="article-heading"><span class="eyebrow">KANTO · PILOTO</span><h1>'+esc(title)+'</h1>'+
    '<p>Catálogo experimental de '+data.locations.length+' locais e '+data.trainers.length+
    ' treinadores de Kanto. Mapas, batalhas e encontros vêm da fonte Essentials FRLG; QA manual Windows/JoiPlay e eventos de história ainda estão pendentes.</p></header>';
  const tabs='<nav class="region-picker" aria-label="Catálogo de Kanto">'+Object.entries(pages).map(([key,name])=>
    '<a class="text-link" href="/'+key+'?regiao=kanto"'+(key===page?' aria-current="page"':'')+'>'+name+'</a>').join('')+'</nav>';
  const source='<p class="data-note">Fonte: <a href="'+esc(data.source.url)+'" target="_blank" rel="noopener noreferrer">'+
    esc(data.source.name)+'</a>, de '+esc(data.source.author)+'.</p>';
  return '<div class="container detail-container">'+(detail?'<a class="back-link" href="/'+page+'?regiao=kanto">← '+pages[page]+' de Kanto</a>':'')+
    header+regionPicker(page,'kanto')+tabs+body+source+'</div>';
}

function cards(entries,card){
  return '<div class="regular-grid">'+entries.map(card).join('')+'</div>';
}

function areaCard(area){
  const summary=[];
  if(area.methods.length) summary.push(area.methods.length+' métodos de encontro');
  if(area.trainers.length) summary.push(area.trainers.length+' adversários');
  if(area.status==='preview') summary.push('Somente cenário (sem eventos)');
  if(area.status==='encounter_review') summary.push('Encontros sob revisão');
  return '<a class="regular-card" href="'+locationLink(area)+'"><h3>'+esc(area.name)+'</h3>'+
    (summary.length?'<p>'+esc(summary.join(' · '))+'</p>':'')+
    '<span class="regular-card-action">Ver local '+icon('arrow')+'</span></a>';
}

function trainerCard(model,data,trainer){
  const area=data.locations.find(row=>row.id===trainer.location);
  const species=[...new Set(trainer.variants.flatMap(variant=>variant.team.map(pokemon=>pokemon.species)))];
  const images=species.map(id=>model.byId.get(id)).filter(Boolean).map(pokemon=>
    '<img loading="lazy" src="'+esc(sprite(pokemon))+'" alt="'+esc(pokemon.name)+'"/>').join('');
  return '<a class="regular-card" href="'+trainerLink(trainer)+'">'+
    '<div class="regular-card-meta"><span class="mini-label">'+esc(trainer.role)+'</span><span>'+esc(area.name)+'</span></div>'+
    '<h3>'+esc(trainer.name)+'</h3><div class="regular-pokemon-strip">'+images+'</div>'+
    '<span class="regular-card-action">Ver equipe'+(trainer.variants.length>1?'s':'')+' '+icon('arrow')+'</span></a>';
}

export function kantoIndex(model,data,page){
  if(page==='localizacoes') return layout(data,page,'Localizações de Kanto',cards(data.locations,areaCard));
  const leaders=page==='chefes';
  const trainers=data.trainers.filter(row=>row.leader===leaders);
  return layout(data,page,leaders?'Líderes de Kanto':'Treinadores de Kanto',cards(trainers,row=>trainerCard(model,data,row)));
}

function encounterTable(model,method){
  const slots=method.slots.map(slot=>{
    const pokemon=model.byId.get(slot.species);
    const name=esc(pokemon?.name||slot.species);
    const target='/pokedex/'+encodeURIComponent(slot.species);
    const level=slot.min===slot.max?slot.min:slot.min+'–'+slot.max;
    return '<tr><td>'+(pokemon?'<a href="'+target+'">'+name+'</a>':name)+'</td><td>'+esc(level)+'</td><td>'+esc(slot.chance)+'%</td></tr>';
  }).join('');
  return '<section class="panel kanto-encounters"><h3>'+esc(methods[method.id]||method.id)+'</h3>'+
    '<table><thead><tr><th scope="col">Pokémon</th><th scope="col">Nível</th><th scope="col">Chance</th></tr></thead>'+
    '<tbody>'+slots+'</tbody></table></section>';
}

export function kantoLocation(model,data,area){
  const trainers=area.trainers.map(id=>data.trainers.find(row=>row.id===id));
  const encounters=area.methods.length
    ? '<section class="section"><h2>Encontros</h2><div class="region-entries">'+area.methods.map(method=>encounterTable(model,method)).join('')+'</div></section>'
    : '<p class="data-note">'+(area.status==='preview'
      ? 'Somente cenário: eventos, treinadores e encontros ainda não estão liberados.'
      : area.status==='encounter_review'
        ? 'Encontros temporariamente suspensos: a fonte contém um método duplicado; não foram inventadas probabilidades.'
        : 'A fonte auditada não possui encontros selvagens ativos neste local.')+'</p>';
  const battles=trainers.length
    ? '<section class="section"><h2>Adversários</h2>'+cards(trainers,row=>trainerCard(model,data,row))+'</section>' : '';
  return layout(data,'localizacoes',area.name,encounters+battles,true);
}

export function kantoTrainer(model,data,trainer,details){
  const area=data.locations.find(row=>row.id===trainer.location);
  const variants=trainer.variants.map(variant=>{
    const starter=model.byId.get(variant.starter);
    const title=variant.starter?'Se você escolheu '+(starter?.name||variant.starter):'Equipe';
    return '<section class="section"><h2>'+esc(title)+'</h2><div class="story-team-grid">'+
      variant.team.map(pokemon=>teamPokemon(pokemon,model,details)).join('')+'</div></section>';
  }).join('');
  return layout(data,trainer.leader?'chefes':'treinadores',trainer.name,
    '<p>'+esc(trainer.role)+' · '+link(locationLink(area),area.name)+'</p>'+
    (trainer.leader&&KANTO_GYM_REWARDS[trainer.name]
      ? '<p>Recompensa: '+esc(KANTO_GYM_REWARDS[trainer.name])+' Badge (somente após vitória)</p>'
      : '')+variants,true);
}
