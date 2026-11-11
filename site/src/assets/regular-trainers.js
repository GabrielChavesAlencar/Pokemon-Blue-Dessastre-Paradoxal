import {esc,icon,sprite,normalize} from './utils.js';
import {teamPokemon} from './story.js';
import {futureSprite} from './future-eevee.js';

export const DIFFICULTIES=[
  {id:'beginner',label:'Inicial',crystals:'0–1 cristais',percent:70,bst:350},
  {id:'intermediate',label:'Intermediário',crystals:'2–4 cristais',percent:70,bst:450},
  {id:'advanced',label:'Avançado',crystals:'5–10 cristais',percent:70,bst:540},
  {id:'master',label:'Master',crystals:'11+ cristais',percent:90,bst:null}
];
export const regularTrainerById=(data,id)=>data?.trainers?.find(trainer=>trainer.id===id);
const clampLevel=value=>Math.min(100,Math.max(1,Math.trunc(Number(value))||50));
const bytes=value=>[...new TextEncoder().encode(String(value))];

function multiplier(attack,defending,chart){
  if(!defending?.length)return 1;
  return defending.reduce((acc,type)=>{
    const rules=chart[type];
    return acc*(rules?.immunities.includes(attack)?0:rules?.weaknesses.includes(attack)?2:rules?.resistances.includes(attack)?0.5:1);
  },1);
}
function lastMoves(species,level,details){
  const rows=details?.species?.[species]?.moves||[];
  const learned=rows.filter(([at])=>at<=level).map(([,id])=>id).reverse();
  return [...new Set(learned)].slice(0,4).reverse();
}
function threatWeights(team,model,chart){
  const attacks=Object.keys(chart),threats={};
  for(const type of attacks){
    const mult=team.map(p=>multiplier(type,model.byId.get(p.species)?.types,chart));
    const weak=mult.reduce((sum,n)=>sum+(n>=4?4:n>1?2:0),0);
    const resisted=mult.filter(n=>n<1).length;
    if(weak>resisted)threats[type]=weak-resisted;
  }
  return threats;
}
function eligiblePartners(model,details){
  return model.catalog.species.filter(p=>{
    if(p.pending||!p.types?.length||!Array.isArray(p.stats)||p.stats.some(n=>!Number.isInteger(n)||n<=0))return false;
    const bst=p.stats.reduce((sum,n)=>sum+n,0);
    if(bst<440||bst>570)return false;
    if(p.flags?.some(flag=>['Legendary','Mythical','UltraBeast','Paradox','Pending'].includes(flag)))return false;
    return (details?.species?.[p.id]?.moves||[]).length>0;
  });
}
function nextPartner(team,trainer,level,model,details,chart){
  const existing=new Set(team.map(p=>p.species));
  const usedTypes=new Set(team.flatMap(p=>model.byId.get(p.species)?.types||[]));
  const threats=threatWeights(team,model,chart);
  const salt=bytes(trainer.name).reduce((sum,byte,i)=>sum+byte*(i+1),0);
  let selected=null,best=null;
  for(const pokemon of eligiblePartners(model,details)){
    if(existing.has(pokemon.id))continue;
    const coverage=Object.entries(threats).reduce((sum,[attack,risk])=>{
      const effectiveness=multiplier(attack,pokemon.types,chart);
      return sum+risk*(effectiveness===0?6:effectiveness<1?4:effectiveness>1?-4:0);
    },0);
    const bst=pokemon.stats.reduce((sum,n)=>sum+n,0);
    const variety=(bytes(pokemon.id).reduce((sum,n)=>sum+n,0)+salt)%7;
    const score=coverage*3+pokemon.types.filter(type=>!usedTypes.has(type)).length*9+
      Math.floor((bst-440)/12)+variety;
    const tuple=[score,bst,pokemon.id];
    if(!best||tuple[0]>best[0]||(tuple[0]===best[0]&&
      (tuple[1]>best[1]||(tuple[1]===best[1]&&tuple[2]>best[2])))){
      selected=pokemon;best=tuple;
    }
  }
  if(!selected)return null;
  const offense=selected.stats[1]>=selected.stats[4]?'ATTACK':'SPECIAL_ATTACK';
  return {species:selected.id,level,moves:lastMoves(selected.id,level,details),
    evs:{HP:4,[offense]:252,SPEED:252},preview:true};
}
export function regularTeam(model,data,trainer,mode,details,highest=50){
  const difficulty=DIFFICULTIES.find(x=>x.id===mode)||DIFFICULTIES[0];
  const level=Math.max(1,Math.floor(clampLevel(highest)*difficulty.percent/100));
  const team=(trainer.team||[]).map(p=>({...p,level,calculatedLevel:true,
    moves:p.moves?.length?p.moves:p.form===50?lastMoves(p.species+',50',level,details):p.moves}));
  if(difficulty.id==='master' && !trainer.name.includes('(Auto Grind)')){
    while(team.length>0&&team.length<4){
      const newMember=nextPartner(team,trainer,level,model,details,data.typeChart||{});
      if(!newMember)break;
      team.push({...newMember,calculatedLevel:true});
    }
  }
  return {team,level,difficulty};
}
const sourceNote='Times-base extraídos do Pokémon Decades; nove treinadores recebem formas regionais de Eevee na instalação do Blue. O reforço Master automático continua sendo uma prévia calculada.';

function card(model,trainer){
  const images=trainer.team.slice(-3).map(p=>{
    const found=(p.form===50?model.byId.get(p.species+',50'):null)||model.byId.get(p.species);
    return found?.future?futureSprite(found,'icon','future-trainer-icon'):
      '<img loading="lazy" src="'+esc(found?sprite(found):'/assets/fan-placeholder.svg')+'" alt="'+esc(found?.name||p.species)+'"/>';
  }).join('');
  return '<a class="regular-card" href="/treinadores/'+encodeURIComponent(trainer.id)+'">'+
    '<div class="regular-card-meta"><span class="mini-label">'+esc(trainer.trainerClass)+'</span><span>'+esc(trainer.location)+'</span></div>'+
    '<h3>'+esc(trainer.name)+'</h3><div class="regular-pokemon-strip">'+images+'</div>'+
    '<p>'+trainer.team.length+' Pokémon no PBS · '+(trainer.name.includes('(Auto Grind)')?'Batalha automática':'4 fases de dificuldade')+'</p>'+
    '<span class="regular-card-action">Ver equipes '+icon('arrow')+'</span></a>';
}
export function regularResults(model,data,state){
  const search=normalize(state.trainerQ||''),area=state.trainerArea||'all';
  const filtered=data.trainers.filter(trainer=>
    (area==='all'||trainer.location===area) &&
    (!search||normalize([
      trainer.name,trainer.trainerClass,trainer.trainerType,trainer.location,
      ...trainer.team.map(p=>model.byId.get(p.species)?.name||p.species)
    ].join(' ')).includes(search))
  );
  const visible=filtered.slice(0,state.trainerLimit||24);
  const html=visible.length?'<div class="regular-grid">'+visible.map(t=>card(model,t)).join('')+'</div>'+
    (visible.length<filtered.length?'<div class="load-more"><button class="button button-secondary" data-more="trainers">Carregar mais '+icon('arrow')+'</button></div>':''):
    '<div class="story-honesty"><strong>Nenhum treinador encontrado.</strong><p>Experimente outro nome, classe, localização ou Pokémon.</p></div>';
  return {html,count:filtered.length};
}
export function regularIndex(model,data,state){
  const areas=[...new Set(data.trainers.map(x=>x.location))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  const found=regularResults(model,data,state);
  return '<div class="container story-container">'+
    '<section class="story-page-heading"><span class="eyebrow">CAMPANHA BLUE · REGISTROS DO PBS</span>'+
    '<h1>Treinadores da <em>jornada.</em></h1><p>Consulte equipes, golpes, itens e variações por dificuldade dos treinadores comuns de Beatha. Mesma apresentação das fichas dos Mestres.</p></section>'+
    '<section class="regular-toolbar" aria-label="Filtros dos treinadores">'+
    '<label class="search-field">'+icon('search')+'<input data-search="trainers" type="search" aria-label="Pesquisar treinadores" placeholder="Pesquisar nome, classe, Pokémon ou rota…" value="'+esc(state.trainerQ||'')+'"/></label>'+
    '<label class="select-field"><span>Localização</span><select data-select="trainerArea" aria-label="Filtrar por localização"><option value="all">Todas as áreas</option>'+
    areas.map(a=>'<option value="'+esc(a)+'" '+(a===state.trainerArea?'selected':'')+'>'+esc(a)+'</option>').join('')+'</select></label></section>'+
    '<p class="regular-results-caption"><strong id="regular-count">'+found.count+'</strong> treinadores encontrados · '+data.trainers.length+' registros no total</p>'+
    '<div id="regular-results">'+found.html+'</div>'+
    '<p class="story-source-note">'+esc(sourceNote)+' <a href="'+esc(data.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Consultar arquivo de origem '+icon('arrow')+'</a></p></div>';
}
export function regularDetail(model,data,trainer,variant,details,highest=50){
  const mode=DIFFICULTIES.find(x=>x.id===variant)||DIFFICULTIES[0];
  const outcome=regularTeam(model,data,trainer,mode.id,details,highest);
  const area=model.locations.find(x=>normalize(x.name)===normalize(trainer.location));
  const support=outcome.team.filter(p=>p.preview).length;
  return '<div class="container story-container"><a class="back-link" href="/treinadores">← Todos os treinadores</a>'+
    '<section class="trainer-banner regular-banner"><div class="regular-avatar" aria-hidden="true">'+esc(trainer.name.slice(0,1))+'</div><div>'+
    '<span class="eyebrow">'+esc(trainer.trainerClass)+' · '+esc(trainer.trainerType)+'</span><h1>'+esc(trainer.name)+'</h1>'+
    '<p>'+esc(trainer.location)+'</p>'+(area?'<a href="/localizacoes/'+area.id+'">Ver localização '+icon('arrow')+'</a>':'')+'</div></section>'+
    '<div class="trainer-choice"><div><h2>Equipe do treinador</h2><p>'+esc(outcome.difficulty.label)+' · '+outcome.team.length+' Pokémon previstos</p></div>'+
    '<label class="select-field"><span>Dificuldade</span><select data-select="trainerVariant" aria-label="Escolher variante da equipe">'+
    DIFFICULTIES.map(m=>'<option value="'+m.id+'" '+(m.id===mode.id?'selected':'')+'>'+m.label+' · '+m.crystals+'</option>').join('')+'</select></label>'+
    '<label class="select-field trainer-level"><span>Maior nível da sua equipe</span><input type="number" data-select="trainerLevel" aria-label="Maior nível da sua equipe" min="1" max="100" value="'+clampLevel(highest)+'"/><small>Enter ou sair do campo para calcular</small></label></div>'+
    '<p class="data-note">Prévia: maior nível do jogador '+clampLevel(highest)+' → equipe no nível '+outcome.level+' ('+outcome.difficulty.percent+'%). '+
    (mode.id==='master'?'Master pode completar times menores até 4 Pokémon com cobertura de tipos.':'Os limites de BST e golpes são aplicados pela engine durante a batalha.')+'</p>'+
    '<div class="story-pokemon-grid">'+outcome.team.map(p=>teamPokemon(p,model,details)).join('')+'</div>'+
    (support?'<p class="data-note"><strong>Reforço Master estimado:</strong> '+support+' Pokémon calculado(s) pela regra de cobertura a partir da Pokédex; confira a composição final no jogo.</p>':'')+
    '<div class="story-honesty"><strong>Dados de origem e limitações</strong><p>'+esc(sourceNote)+'</p><p>O PBS original registra '+trainer.team.length+' Pokémon para este treinador; não há quatro arquivos de equipes separados por dificuldade. As versões acima são prévias das regras da campanha, não times independentes confirmados.</p><a href="'+esc(data.sourceUrl)+'" target="_blank" rel="noopener noreferrer">Abrir PBS original '+icon('arrow')+'</a></div></div>';
}
