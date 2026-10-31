import {esc,icon,sprite,types,normalize,pokemonPath} from './utils.js';

const baseImage='https://raw.githubusercontent.com/HazyCrazy/Pokemon-Decades/main/Graphics/Pictures/';
const emerald=type=>baseImage+String(type||'normal').toLowerCase()+'Emerald.png';
const storyRef='https://www.pokecommunity.com/threads/pokemon-decades.540970/';
const srcRef='https://github.com/HazyCrazy/Pokemon-Decades/blob/main/PBS/trainers_story_mode.txt';
const simple=(s)=>esc(String(s||'').replace(/_/g,' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase()));
const iconLink=(url,label)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' '+icon('arrow')+'</a>';
export const allTrainers=story=>[...(story?.masters||[]),...(story?.bosses||[])];
const locationFor=(model,name)=>model.locations.find(a=>normalize(a.name)===normalize(name));

export function regionImage(model,area,compact=false){
  const map=model.region??{};
  const point=map.points?.[area.name]||map.points?.[Object.keys(map.points||{}).find(key=>normalize(key)===normalize(area.name))];
  const marker=point?'<span class="region-marker" style="left:'+Math.max(0,Math.min(100,point.x/(map.regionMaxX||63)*100))+'%;top:'+Math.max(0,Math.min(100,point.y/(map.regionMaxY||47)*100))+'%" aria-hidden="true"></span>':'';
  return '<div class="region-map '+(compact?'mini':'')+'"><img src="'+esc(map.regionImage||'')+'" alt="Mapa regional oficial de Beatha, da base Pokémon Decades" loading="lazy"/>'+marker+'<span class="region-map-caption">'+(point?'Localização no mapa regional':'Mapa regional de Beatha · referência Decades')+'</span></div>';
}
function label(origin){return '<p class="story-source-note">'+esc(origin||'Equipes da versão original de Pokémon Decades, não verificadas nos arquivos locais do Blue.')+'</p>';}
const stage=(n,title,desc,url)=>'<a class="story-step" href="'+esc(url)+'"><span class="story-step-number">'+esc(n)+'</span><div><strong>'+esc(title)+'</strong><p>'+esc(desc)+'</p></div>'+icon('arrow')+'</a>';
export function storyIndex(model){
  const trainers=model.story||{};
  const featured=allTrainers(trainers);
  const world=model.region?.regionImage||'';
  const journey=[
    stage('01','Escolha um Pokémon inicial','Na base Decades, escolha entre as cinco modalidades de parceiro inicial. Confira a versão ativa no Blue.','/guias/decades-iniciais'),
    stage('02','Explore Beatha e procure os Mestres','A campanha original gira em torno de 18 Type Masters e seus Type Emeralds. A ordem não está comprovada por eventos publicados.','/chefes'),
    stage('03','Reúna os 18 Type Emeralds','Procure os Mestres nas cidades correspondentes e prepare estratégias para seus tipos.','/chefes'),
    stage('04','Avance para o Zenith Domain','O objetivo final publicado pelo autor é impedir a ameaça do Zenith Domain.','/chefes/zenith')
  ];
  return '<div class="container story-container">'+
    '<section class="story-hero"><div><span class="eyebrow">AJUDA DA CAMPANHA · BLUE / DECADES</span><h1>Guia da<br><em>História.</em></h1><p>Objetivos da jornada, mapa de Beatha, Mestres de Tipo e equipes verificadas nos arquivos originais do Decades.</p><div class="story-actions"><a class="button button-primary" href="/chefes">Ver os 18 Mestres '+icon('arrow')+'</a><a class="button button-secondary" href="/localizacoes">Pesquisar áreas '+icon('map')+'</a></div></div><img class="story-hero-map" src="'+esc(world)+'" loading="lazy" alt="Mapa de Beatha do Pokémon Decades"/></section>'+
    '<div class="story-honesty"><strong>Referência da história original</strong><p>Os objetivos gerais estão documentados pelo criador. As etapas exatas, condições de desbloqueio e eventuais mudanças de roteiro do Blue não foram inferidas de arquivos de encontros. As equipes exibidas foram extraídas dos arquivos PBS do Decades.</p></div>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">O CAMINHO ATÉ O ZENITH DOMAIN</span><h2>Missões principais<span>.</span></h2></div></div><div class="story-steps">'+journey.join('')+'</div></section>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">DESAFIOS PRINCIPAIS</span><h2>18 Mestres de Tipo<span>.</span></h2></div><a class="text-link" href="/chefes">Ver todos os times '+icon('arrow')+'</a></div><div class="story-master-grid">'+(trainers.masters||[]).map((t,i)=>masterCard(t,i,model)).join('')+'</div></section>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">CHEFES E PÓS-JOGO</span><h2>Desafios finais<span>.</span></h2></div></div><div class="story-note-cards"><a href="/chefes/zenith" class="story-note"><h3>Zenith Domain · Danny</h3><p>Consulte as equipes do chefe final registradas na base Decades e compare as variantes disponíveis.</p>'+icon('arrow')+'</a><a href="/chefes" class="story-note"><h3>Super Boss e outros desafios</h3><p>O Decades menciona um Super Boss, mas seus times precisam de extração adicional. Não serão inventados.</p>'+icon('arrow')+'</a><div class="story-note"><h3>Elite Four</h3><p>Não foi confirmada uma Elite Four tradicional como objetivo principal do Decades. A campanha original destaca os 18 Mestres de Tipo.</p></div></div></section>'+
    '<p class="data-note">Fontes: '+iconLink(storyRef,'Anúncio oficial de Pokémon Decades')+' · '+iconLink(srcRef,'Arquivo público dos treinadores')+'</p>'+
    '</div>';
}
function masterCard(trainer,index,model){
  const area=locationFor(model,trainer.location);
  return '<a class="master-card" href="/chefes/'+encodeURIComponent(trainer.id)+'"><span class="master-number">'+String(index+1).padStart(2,'0')+'</span><img src="'+emerald(trainer.type)+'" loading="lazy" alt="Esmeralda '+esc(types[trainer.type]||trainer.type)+'"/><div><span class="mini-label">'+esc(types[trainer.type]||trainer.type)+'</span><h3>'+esc(trainer.name)+'</h3><p>'+esc(trainer.location)+(area?' · área cadastrada':'')+'</p></div>'+icon('arrow')+'</a>';
}
export function bossesIndex(model){
 const story=model.story||{};
 return '<div class="container story-container">'+
   '<section class="story-page-heading">'+
   '<span class="eyebrow">EQUIPES EXTRAÍDAS DO PBS ORIGINAL</span><h1>Chefes e <em>Mestres.</em></h1><p>Selecione um líder para ver os Pokémon, golpes, itens e versões Basic / Full Power. Os times desta página são referências do Decades, até serem reexportados do Blue.</p></section>'+
   '<div class="story-honesty"><strong>18 Type Masters · várias formações</strong><p>As equipes do PBS original incluem 1v1, 2v2, 3v3, Basic Power (4 Pokémon) e Full Power (6 Pokémon). O nível 1 do arquivo pode ser substituído por escalonamento no jogo. Não apresentamos níveis finais como confirmados.</p></div>'+
   '<section class="section"><div class="section-heading"><div><span class="eyebrow">BEATHA</span><h2>Todos os Mestres<span>.</span></h2></div></div><div class="story-master-grid">'+(story.masters||[]).map((t,i)=>masterCard(t,i,model)).join('')+'</div></section>'+
   '<section class="section"><div class="section-heading"><div><span class="eyebrow">ZENITH DOMAIN</span><h2>Chefe final<span>.</span></h2></div></div><div class="story-master-grid">'+(story.bosses||[]).map((t,i)=>masterCard({...t,type:'STELLAR'},i,model)).join('')+'</div></section>'+
   '<p class="data-note">A Elite Four clássica e os times do Super Boss não são confirmados por esta extração. '+iconLink(srcRef,'Consultar fonte')+'</p></div>';
}
const moveName=(id,details)=>esc(details?.moves?.[id]?.name??simple(id));
function teamPokemon(p,model,details){
  const baseId=p.species;
  const entity=model.byId.get(baseId);
  const image=entity?sprite(entity):'/assets/fan-placeholder.svg';
  const subtitle=[p.form?('Forma '+p.form):null,p.item?('Item: '+simple(p.item)):null,p.teraType?('Tera: '+(types[p.teraType]||simple(p.teraType))):null,p.nature?('Nature: '+simple(p.nature)):null].filter(Boolean);
  const name=entity?.name||simple(baseId);
  const url=entity?pokemonPath(entity):null;
  return '<article class="story-pokemon"><div class="story-poke-header"><img src="'+esc(image)+'" alt="'+esc(name)+'" loading="lazy"/><div><h3>'+(url?'<a href="'+esc(url)+'">'+esc(name)+'</a>':esc(name))+'</h3><span>'+ (p.level===1?'Nível base 1 · escalonável':'Nível PBS: '+esc(p.level)) +'</span></div></div>'+
    '<p class="story-poke-extras">'+subtitle.map(esc).join(' · ')+'</p>'+
    (Array.isArray(p.moves)&&p.moves.length?'<div class="story-poke-moves">'+p.moves.map(m=>'<span>'+moveName(m,details)+'</span>').join('')+'</div>':'<p class="data-note">Golpes não informados no PBS</p>')+
    '</article>';
}
export function trainerDetail(model,trainer,variantId,details){
 const all=trainer.variants||[];
 const chosen=all.find(x=>x.id===variantId)||all.find(x=>x.id==='1v1-full-power')||all[0];
 const area=locationFor(model,trainer.location);
 return '<div class="container story-container"><a class="back-link" href="/chefes">← Todos os chefes</a>'+
   '<div class="trainer-banner"><img src="'+emerald(trainer.type||'normal')+'" alt="" loading="lazy"/><div><span class="eyebrow">'+esc(trainer.role==='type-master'?'MESTRE DE TIPO':'CHEFE FINAL · ZENITH DOMAIN')+'</span><h1>'+esc(trainer.name)+'</h1><p>'+esc(trainer.location)+' · '+esc(types[trainer.type]||'Desafio final')+'</p>'+(area?'<a href="/localizacoes/'+area.id+'">Ver área cadastrada '+icon('arrow')+'</a>':'')+'</div></div>'+
   '<div class="trainer-choice"><div><h2>Equipe do treinador</h2><p>Escolha o formato registrado no Pokémon Decades original.</p></div><label class="select-field"><span>Versão</span><select data-select="trainerVariant" aria-label="Escolher variante da equipe">'+all.map(v=>'<option value="'+esc(v.id)+'" '+(v.id===chosen?.id?'selected':'')+'>'+esc(v.label)+' · '+v.team.length+' Pokémon</option>').join('')+'</select></label></div>'+
   (chosen?'<div class="story-pokemon-grid">'+chosen.team.map(p=>teamPokemon(p,model,details)).join('')+'</div>':'<p class="data-note">Esta equipe ainda não possui dados exportados.</p>')+
   '<div class="story-honesty"><strong>Origem e atualização</strong><p>Equipe extraída de PBS/trainers_story_mode.txt da versão original do Decades. Itens, Pokémon, golpes e níveis podem ter sido modificados no Blue. Para atualizar, execute a exportação dos treinadores locais; não interpretamos a formação original como garantida no hack atual.</p>'+iconLink(srcRef,'Conferir arquivo oficial')+'</div></div>';
}
