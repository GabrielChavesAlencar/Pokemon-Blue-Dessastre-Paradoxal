export const types={NORMAL:'Normal',FIRE:'Fogo',WATER:'Água',ELECTRIC:'Elétrico',GRASS:'Planta',ICE:'Gelo',FIGHTING:'Lutador',POISON:'Veneno',GROUND:'Terra',FLYING:'Voador',PSYCHIC:'Psíquico',BUG:'Inseto',ROCK:'Pedra',GHOST:'Fantasma',DRAGON:'Dragão',DARK:'Sombrio',STEEL:'Aço',FAIRY:'Fada',STELLAR:'Stellar',SHADOW:'Shadow'};
export const colors={NORMAL:'#aaa9a1',FIRE:'#ff9c60',WATER:'#6ab5ff',ELECTRIC:'#f1ce65',GRASS:'#80cf9c',ICE:'#8bd8df',FIGHTING:'#e99182',POISON:'#c28cdc',GROUND:'#c5a477',FLYING:'#a6baf2',PSYCHIC:'#ee90b5',BUG:'#b5c96e',ROCK:'#c4b98b',GHOST:'#a997d2',DRAGON:'#918feb',DARK:'#b4a9a7',STEEL:'#a8c6d5',FAIRY:'#e9a9d6',STELLAR:'#8de0df'};
export const methods={Land:'Grama',LandNight:'Grama · noite',LandMorning:'Grama · manhã',Water:'Surf',OldRod:'Vara antiga',GoodRod:'Vara boa',SuperRod:'Supervara',RockSmash:'Quebra de pedras',HeadbuttLow:'Árvores · comum',HeadbuttHigh:'Árvores · raro',Cave:'Caverna',PokeRadar:'Poké Radar',TrashCan:'Lixeiras',BugContest:'Concurso de insetos'};
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const normalize=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
export const number=value=>String(value).padStart(3,'0');
export const generationName=p=>p.generationLabel??`Geração ${p.generation}`;
export const pokemonPath=p=>`/pokedex/${encodeURIComponent(p.base??p.id)}${p.base?`?forma=${p.form}`:''}`;
export const art=(n,shiny=false)=>typeof n==='object'?(n.sprites?.[shiny?'front-shiny':'front']??n.art??(n.generation==='dessastre-paradoxal'?'/assets/fan-placeholder.svg':art(n.number,shiny))):`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${shiny?'shiny/':''}${n}.png`;
export const sprite=n=>typeof n==='object'?(n.sprite??n.art??(n.generation==='dessastre-paradoxal'?'/assets/fan-placeholder.svg':sprite(n.number))):`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${n}.png`;
export const date=value=>new Intl.DateTimeFormat('pt-BR',{day:'2-digit',month:'short',year:'numeric',timeZone:'America/Sao_Paulo'}).format(new Date(value));
// Sempre usa o instante real do commit e o fuso de Brasília; nunca o fuso do navegador.
export const time=value=>new Intl.DateTimeFormat('pt-BR',{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:'America/Sao_Paulo'}).format(new Date(value));
export function typePills(list){return list.map(type=>`<span class="type-pill" style="--type:${colors[type]??'#aaa'}"><i></i>${esc(types[type]??type)}</span>`).join('');}
const paths={arrow:'M5 12h14m-6-6 6 6-6 6',search:'m21 21-5.5-5.5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z',compass:'m16.5 7.5-3 6-6 3 3-6 6-3ZM22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',map:'m9 3-6 3v15l6-3 6 3 6-3V3l-6 3-6-3Zm0 0v15m6-12v15',spark:'m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z',shield:'m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Zm-4 9 3 3 5-6',layers:'m12 3 10 6-10 6L2 9l10-6Zm-9 11 9 5 9-5M3 18l9 5 9-5',heart:'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z',book:'M12 6C9 3 4 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-2-1-7-1-10 2Zm0 0v15',clock:'M12 8v5l3 2M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',code:'m8 7-5 5 5 5m8-10 5 5-5 5m-3-14-2 18',pin:'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Zm-5 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',grid:'M3 3h7v7H3V3Zm11 0h7v7h-7V3ZM3 14h7v7H3v-7Zm11 0h7v7h-7v-7Z',chevron:'m9 5 7 7-7 7',download:'M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4',check:'m5 12 4 4L19 6',close:'m6 6 12 12M6 18 18 6'};
export const icon=(name,cls='')=>`<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name]??paths.spark}"/></svg>`;
export function groupSlots(method){
  const result=new Map();let total=0;
  for(const [id,min,max,weight] of method.slots){total+=weight;const row=result.get(id)??{id,min,max,weight:0};row.min=Math.min(row.min,min);row.max=Math.max(row.max,max);row.weight+=weight;result.set(id,row);}
  return [...result.values()].map(row=>({...row,chance:total?row.weight/total*100:0})).sort((a,b)=>b.chance-a.chance);
}
export function filterSpecies(list,state,favorites=new Set()){
  const q=normalize(state.q);
  return list.filter(p=>(!q||normalize(`${p.name} ${p.id} ${number(p.number)}`).includes(q))&&(!state.type||p.types.includes(state.type))&&(!state.generation||String(p.generation)===String(state.generation))&&(state.group!=='future'||p.future===true)&&(state.group!=='paradox'||p.flags.includes('Paradox'))&&(state.group!=='legendary'||p.flags.some(x=>['Legendary','Mythical'].includes(x)))&&(state.group!=='favorites'||favorites.has(p.id))).sort((a,b)=>state.sort==='name'?a.name.localeCompare(b.name):state.sort==='bst'?b.stats.reduce((x,y)=>x+y,0)-a.stats.reduce((x,y)=>x+y,0):a.number-b.number);
}
