import {esc,icon,sprite,types,normalize,pokemonPath} from './utils.js';
import {futureSprite} from './future-eevee.js';

const baseImage='https://raw.githubusercontent.com/HazyCrazy/Pokemon-Decades/main/Graphics/Pictures/';
const emerald=type=>baseImage+String(type||'normal').toLowerCase()+'Emerald.png';
const storyRef='https://www.pokecommunity.com/threads/pokemon-decades.540970/';
const srcRef='https://github.com/HazyCrazy/Pokemon-Decades/blob/main/PBS/trainers_story_mode.txt';
const simple=(s)=>esc(String(s||'').replace(/_/g,' ').toLowerCase().replace(/\b\w/g,c=>c.toUpperCase()));
const iconLink=(url,label)=>'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' '+icon('arrow')+'</a>';
export const allTrainers=story=>[...(story?.masters||[]),...(story?.bosses||[])];
const locationFor=(model,name)=>model.locations.find(a=>normalize(a.name)===normalize(name));

const pointFor=(map,area)=>map.points?.[area.name]??map.points?.[Object.keys(map.points??{}).find(name=>normalize(name)===normalize(area.name))];
const imageFor=(map,area)=>map.areaImages?.[String(area.id)]??null;
const regionSource='https://github.com/HazyCrazy/Pokemon-Decades/blob/main/Graphics/UI/Town%20Map/Regions/mapRegion0.png';
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const round=value=>Number(value.toFixed(3));
export function regionCaption(model,area){
  const map=model.region??{},image=imageFor(map,area);
  if(image?.kind==='habitat-region-capture')return 'Captura local do mapa regional em zoom de 3×, como Ver no mapa na Habitat Dex. A área selecionada está destacada em rosa.';
  if(image?.src)return 'Miniatura específica encontrada nos arquivos públicos de Pokémon Decades. Não é uma captura completa do cenário jogável.';
  if(pointFor(map,area))return 'Recorte ampliado do mapa regional oficial de Beatha, centrado nesta localização. Não é a imagem do mapa interno de jogo.';
  return 'Não foi encontrada uma imagem pública confiável desta área. Nenhuma imagem de outro mapa foi usada como substituta.';
}
export function regionImage(model,area,compact=false){
  const map=model.region??{},local=imageFor(map,area),className='region-map '+(compact?'mini ':'');
  if(local?.src){
    if(local.kind==='habitat-region-capture')return '<div class="'+className+'region-map--local region-map--capture"><img class="region-map-individual" src="'+esc(local.src)+'" alt="Captura da Habitat Dex: '+esc(area.name)+', mapa regional em zoom de 3 vezes" loading="lazy"/><span class="region-map-caption">Habitat Dex · mapa regional · 3×</span></div>';
    return '<div class="'+className+'region-map--local"><img class="region-map-individual" src="'+esc(local.src)+'" alt="Miniatura específica de '+esc(area.name)+' no material de Pokémon Decades" loading="lazy"/><span class="region-map-caption">Miniatura da área · fonte Decades</span></div>';
  }
  const point=pointFor(map,area);
  if(point&&map.regionImage){
    // Aproximar o ponto correspondente mantendo sempre o quadro ocupado pelo mapa.
    // O zoom é sobre a imagem REGIONAL: jamais é rotulado como mapa interno.
    const x=clamp(Number(point.x)/Number(map.regionMaxX||63),0,1);
    const y=clamp(Number(point.y)/Number(map.regionMaxY||47),0,1);
    const zoom=compact?3.4:2.15;
    const left=clamp(.5-x*zoom,1-zoom,0),top=clamp(.5-y*zoom,1-zoom,0);
    const translateX=left+(zoom-1)*x,translateY=top+(zoom-1)*y;
    const pinX=(left+zoom*x)*100,pinY=(top+zoom*y)*100;
    const style='transform-origin:'+round(x*100)+'% '+round(y*100)+'%;transform:translate('+round(translateX*100)+'%,'+round(translateY*100)+'%) scale('+zoom+');';
    return '<div class="'+className+'region-map--focused">'+
      '<div class="region-map-crop" style="'+style+'"><img src="'+esc(map.regionImage)+'" alt="Recorte do mapa regional de Beatha perto de '+esc(area.name)+'" loading="lazy"/></div>'+
      '<span class="region-marker" style="left:'+round(pinX)+'%;top:'+round(pinY)+'%" aria-hidden="true"></span>'+
      '<span class="region-map-caption">Recorte regional · '+esc(area.name)+'</span></div>';
  }
  // Para áreas sem coordenadas (ex.: Rock Cave 1F), não mostrar a imagem genérica
  // de toda Beatha: é enganoso e repete a mesma imagem em todas as fichas.
  return '<div class="'+className+'region-map--missing">'+
    '<div class="region-map-missing-art"><span class="region-map-missing-glyph">◇</span><span class="region-map-missing-name">'+esc(area.name)+'</span>'+
    '<span class="region-map-missing-description">Mapa individual não encontrado</span></div>'+
    '<span class="region-map-caption">Imagem específica indisponível</span></div>';
}
function label(origin){return '<p class="story-source-note">'+esc(origin||'Equipes da versão original de Pokémon Decades, não verificadas nos arquivos locais do Blue.')+'</p>';}
const stage=(n,title,desc,url)=>'<a class="story-step" href="'+esc(url)+'"><span class="story-step-number">'+esc(n)+'</span><div><strong>'+esc(title)+'</strong><p>'+esc(desc)+'</p></div>'+icon('arrow')+'</a>';
export function difficultyGuide(){return '<section class="story-honesty difficulty-guide"><strong>Como a dificuldade progride</strong><p>Na História com iniciais tradicionais, a dificuldade avança pelas esmeraldas totais: cristais do Decades mais uma esmeralda por insígnia única conquistada em cada região, incluindo Kanto. Os 18 líderes do Decades usam Full Doubles: seis Pokémon em batalhas em dupla.</p><div class="difficulty-grid">'+[
 ['Iniciante','0–1 esmeraldas','Até 350 BST · golpes de até 60 de poder'],['Intermediário','2–4 esmeraldas','Até 450 BST · golpes de até 90 de poder'],
 ['Avançado','5–10 esmeraldas','Até 540 BST · sem teto de poder dos golpes'],['Master','11+ esmeraldas','Sem teto de BST ou poder dos golpes']
 ].map(([name,crystals,rule])=>'<div><b>'+name+'</b><span>'+crystals+'</span><small>'+rule+'</small></div>').join('')+'</div><p>Espécies acima do limite são adaptadas pela engine; os golpes também passam pelos filtros de efeitos da fase inicial. Megas acima do teto de BST ficam bloqueadas. O nível depende do Pokémon de maior nível da sua equipe, ignorando ovos: 70% nas três primeiras dificuldades e 90% para todos os treinadores no Master, arredondado para baixo, com mínimo 1 e máximo 100. Exemplo: jogador no nível 50 enfrenta treinadores e líderes no nível 35 ou, no Master, 45. Em Kanto o mesmo balanceamento de níveis, BST e golpes se aplica; Pokémon selvagens são ajustados a 45% do maior nível sem ovos.</p></section>';}
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
    '<section class="story-hero"><div><span class="eyebrow">AJUDA DA CAMPANHA · BLUE / DECADES</span><h1>Guia da<br><em>História.</em></h1><p>Objetivos da jornada, mapa de Beatha, Mestres de Tipo e equipes Full Doubles dos Mestres verificadas na engine do Blue.</p><div class="story-actions"><a class="button button-primary" href="/chefes">Ver os 18 Mestres '+icon('arrow')+'</a><a class="button button-secondary" href="/localizacoes">Pesquisar áreas '+icon('map')+'</a><a class="button button-secondary" href="/treinadores">Treinadores '+icon('arrow')+'</a></div></div><img class="story-hero-map" src="'+esc(world)+'" loading="lazy" alt="Mapa de Beatha do Pokémon Decades"/></section>'+
    '<div class="story-honesty"><strong>Referência da história original</strong><p>Os objetivos gerais estão documentados pelo criador. As etapas exatas, condições de desbloqueio e eventuais mudanças de roteiro do Blue não foram inferidas de arquivos de encontros. Os Mestres exibem perfis Full Doubles exportados da engine do Blue; outros chefes mantêm a referência do PBS.</p></div>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">O CAMINHO ATÉ O ZENITH DOMAIN</span><h2>Missões principais<span>.</span></h2></div></div><div class="story-steps">'+journey.join('')+'</div></section>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">DESAFIOS PRINCIPAIS</span><h2>18 Mestres de Tipo<span>.</span></h2></div><a class="text-link" href="/chefes">Ver todos os times '+icon('arrow')+'</a></div><div class="story-master-grid">'+(trainers.masters||[]).map((t,i)=>masterCard(t,i,model)).join('')+'</div></section>'+
    '<section class="section"><div class="section-heading"><div><span class="eyebrow">CONFRONTOS PELO MAPA</span><h2>Treinadores comuns<span>.</span></h2></div><a class="text-link" href="/treinadores">Consultar todas as equipes '+icon('arrow')+'</a></div><p class="data-note">Busque treinadores por nome, classe, área ou Pokémon e confira as quatro dificuldades da campanha.</p></section>'+
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
   '<span class="eyebrow">FULL DOUBLES · CAMPANHA BLUE</span><h1>Chefes e <em>Mestres.</em></h1><p>Os líderes mostram somente suas equipes Full Doubles, nas dificuldades Iniciante, Intermediário, Avançado e Master. Selecione um líder para consultar Pokémon, habilidades, itens e golpes.</p></section>'+difficultyGuide()+
   '<section class="section"><div class="section-heading"><div><span class="eyebrow">BEATHA</span><h2>Todos os Mestres<span>.</span></h2></div></div><div class="story-master-grid">'+(story.masters||[]).map((t,i)=>masterCard(t,i,model)).join('')+'</div></section>'+
   '<section class="section"><div class="section-heading"><div><span class="eyebrow">ZENITH DOMAIN</span><h2>Chefe final<span>.</span></h2></div></div><div class="story-master-grid">'+(story.bosses||[]).map((t,i)=>masterCard({...t,type:'STELLAR'},i,model)).join('')+'</div></section>'+
   '<p class="data-note">A Elite Four clássica e os times do Super Boss não são confirmados por esta extração. '+iconLink(srcRef,'Consultar fonte')+'</p><p class="data-note"><a href="/liga?regiao=kanto">Times fortes de Elite Four e campeões '+icon('arrow')+'</a></p></div>';
}
const moveName=(id,details)=>esc(details?.moves?.[id]?.name??simple(id));
export function teamPokemon(p,model,details){
  const baseId=p.species;
  const entity=(Number(p.form)===50?model.byId.get(baseId+',50'):null)||model.byId.get(baseId);
  const image=entity?sprite(entity):'/assets/fan-placeholder.svg';
  const artwork=entity?.future?futureSprite(entity,'front','future-team-sprite'):'<img src="'+esc(image)+'" alt="'+esc(entity?.name||baseId)+'" loading="lazy"/>';
  const subtitle=[p.form?('Forma '+p.form):null,p.item?('Item: '+(details?.items?.[p.item]??simple(p.item))):null,p.teraType?('Tera: '+(types[p.teraType]||simple(p.teraType))):null,p.nature?('Nature: '+simple(p.nature)):null].filter(Boolean);
  const name=entity?.name||simple(baseId);
  const url=entity?pokemonPath(entity):null;
  return '<article class="story-pokemon"><div class="story-poke-header">'+artwork+'<div><h3>'+(url?'<a href="'+esc(url)+'">'+esc(name)+'</a>':esc(name))+'</h3><span>'+ ((p.dynamicLevel?'Nível dinâmico · ajustado pela campanha':(p.movesByLevel||p.calculatedLevel)?'Nível previsto: '+esc(p.level):p.level===1?'Nível base 1 · escalonável':'Nível PBS: '+esc(p.level)) +'</span></div></div>'+
    '<p class="story-poke-extras">'+subtitle.map(esc).join(' · ')+(p.ability?' · Ability: '+esc(p.ability):'')+(p.abilityIndex!=null?' · Índice da habilidade: '+esc(p.abilityIndex):'')+(p.preview?' · Reforço Master estimado':'')+(p.planned?' · PARADOXO FUTURO PLANEJADO (só no site)':'')+'</p>'+
    (p.evs?'<p class="story-poke-extras">EVs: '+Object.entries(p.evs).filter(([,n])=>n>0).map(([s,n])=>esc(({HP:'HP',ATTACK:'Atk',DEFENSE:'Def',SPECIAL_ATTACK:'SpA',SPECIAL_DEFENSE:'SpD',SPEED:'Spe'}[s]??s)+' '+n)).join(' / ')+'</p>':'')+
    (Array.isArray(p.moves)&&p.moves.length?'<div class="story-poke-moves">'+p.moves.map(m=>'<span>'+moveName(m,details)+'</span>').join('')+'</div>':'<p class="data-note">'+(p.referenceOnly?'Golpes variam conforme a implementação e fase da campanha.':p.movesByLevel?'Sem golpe legal disponível neste nível; a engine usa Struggle.':'Golpes não informados no PBS')+'</p>')+
    '</article>';
}

const weaknesses={
  NORMAL:['Lutador'],FIRE:['Água','Terra','Pedra'],WATER:['Elétrico','Planta'],
  ELECTRIC:['Terra'],GRASS:['Fogo','Gelo','Voador','Venenoso','Inseto'],
  ICE:['Fogo','Lutador','Pedra','Aço'],FIGHTING:['Voador','Psíquico','Fada'],
  POISON:['Terra','Psíquico'],GROUND:['Água','Planta','Gelo'],
  FLYING:['Elétrico','Gelo','Pedra'],PSYCHIC:['Inseto','Fantasma','Sombrio'],
  BUG:['Fogo','Voador','Pedra'],ROCK:['Água','Planta','Lutador','Terra','Aço'],
  GHOST:['Fantasma','Sombrio'],DRAGON:['Gelo','Dragão','Fada'],
  DARK:['Lutador','Inseto','Fada'],STEEL:['Fogo','Lutador','Terra'],
  FAIRY:['Venenoso','Aço']
};
export function trainerDetail(model,trainer,variantId,details,playerLevel=50){
 const master=trainer.role==='type-master';
 const all=master?(trainer.campaignVariants||[]):(trainer.variants||[]);
 const chosen=all.find(x=>x.id===variantId)||all.find(x=>x.id===(master?'master':'1v1-full-power'))||all[0];
 const highest=Math.min(100,Math.max(1,Math.trunc(Number(playerLevel))||50));
 const level=chosen?.levelPercent?Math.max(1,Math.floor(highest*chosen.levelPercent/100)):null;
 const team=chosen?.team.map(p=>({...p,level:level??p.level,moves:p.movesByLevel?.filter(row=>row.level<=level).at(-1)?.moves??p.moves}));
 const area=locationFor(model,trainer.location);
 return '<div class="container story-container"><a class="back-link" href="/chefes">← Todos os chefes</a>'+
   '<div class="trainer-banner"><img src="'+emerald(trainer.type||'normal')+'" alt="" loading="lazy"/><div><span class="eyebrow">'+esc(trainer.role==='type-master'?'MESTRE DE TIPO':'CHEFE FINAL · ZENITH DOMAIN')+'</span><h1>'+esc(trainer.name)+'</h1><p>'+esc(trainer.location)+' · '+esc(types[trainer.type]||'Desafio final')+'</p>'+(area?'<a href="/localizacoes/'+area.id+'">Ver área cadastrada '+icon('arrow')+'</a>':'')+'</div></div>'+
   '<section class="story-objective"><span class="eyebrow">COMO AVANÇAR NA HISTÓRIA</span><h2>'+(trainer.role==='type-master'?'Conquistar a Esmeralda de '+esc(types[trainer.type]||trainer.type):'Enfrentar a ameaça do Zenith Domain')+'</h2><p>'+(trainer.role==='type-master'?'Na campanha original, procure '+esc(trainer.name)+' em '+esc(trainer.location)+', prepare seu time para o tipo '+esc(types[trainer.type]||trainer.type)+' e vença o Mestre para avançar na coleta das 18 Type Emeralds. A disponibilidade do confronto pode variar conforme os eventos do Blue.':'O objetivo anunciado pelo criador é reunir os 18 Type Emeralds e enfrentar o poder selado no Zenith Domain. Confira no jogo os eventos necessários para desbloquear a luta.')+'</p>'+(trainer.role==='type-master'?'<p><strong>Fraquezas tradicionais do tipo:</strong> '+(weaknesses[trainer.type]||[]).map(esc).join(' · ')+'. Pokémon de dupla tipagem ou habilidades podem alterar essas vantagens.</p>':'')+'</section>'+ 
   (master?difficultyGuide():'')+
   '<div class="trainer-choice"><div><h2>Equipe do treinador</h2><p>'+(master?'Full Doubles · 6 Pokémon · dupla':'Referência do Pokémon Decades original')+'</p></div><label class="select-field"><span>'+(master?'Dificuldade':'Versão')+'</span><select data-select="trainerVariant" aria-label="Escolher variante da equipe">'+all.map(v=>'<option value="'+esc(v.id)+'" '+(v.id===chosen?.id?'selected':'')+'>'+esc(v.label)+' · '+v.team.length+' Pokémon</option>').join('')+'</select></label>'+(master?'<label class="select-field trainer-level"><span>Maior nível da sua equipe</span><input type="number" data-select="trainerLevel" aria-label="Maior nível da sua equipe" min="1" max="100" step="1" value="'+highest+'"/><small>Enter ou clique fora para calcular</small></label>':'')+'</div>'+
   (master&&level?'<p class="data-note">Prévia: maior nível do jogador '+highest+' → líderes no nível '+level+'. Os golpes abaixo são recalculados para esse nível; o nível do arquivo PBS não é fixo.</p>':'')+
   (chosen?'<div class="story-pokemon-grid">'+team.map(p=>teamPokemon(p,model,details)).join('')+'</div>':'<p class="data-note">Esta equipe ainda não possui dados exportados.</p>')+
   '<div class="story-honesty"><strong>Origem e atualização</strong><p>'+(master?'Quatro equipes exportadas da engine instalada do Blue, usando os mesmos adaptadores de espécies e golpes da campanha. A simulação de nível segue a regra do jogo.':chosen?.origin==='blue-pbs'?'Equipe sincronizada a partir do PBS local do Blue Studio. Publique uma nova exportação quando a configuração mudar.':'Equipe extraída do PBS original do Decades. Itens, Pokémon, golpes e níveis podem ter sido modificados no Blue; exporte os dados locais para substituir esta referência.')+'</p>'+iconLink(srcRef,'Conferir arquivo original')+'</div></div>';
}
