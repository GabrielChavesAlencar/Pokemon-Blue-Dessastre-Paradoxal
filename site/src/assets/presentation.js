import {art,esc,icon,pokemonPath,sprite} from './utils.js';

const highlights=[
  {icon:'map',number:'01',title:'Viaje por várias regiões',description:'Decades é a campanha principal. Kanto e Hoenn avançam em testes de integração, enquanto Johto, Sinnoh e novas regiões ampliam o futuro da aventura.'},
  {icon:'spark',number:'02',title:'Mais de 1.025 Pokémon para descobrir',description:'As 1.025 espécies oficiais dividem espaço no catálogo com Pokémon de fangames, fan forms, Paradoxos e criações originais, sem apagar os clássicos.'},
  {icon:'shield',number:'03',title:'Batalhas com mais estratégia',description:'Mega Evolução, Z-Moves e Terastalização convivem com progressão de dificuldade por insígnias, level cap e equipes de treinadores ajustadas.'}
];
const chapters=[
  {number:'I',label:'A origem',title:'Uma aventura que começa no conhecido.',copy:'O Blue nasce sobre a base de Pokémon Decades. A proposta é expandir a jornada com novas histórias, regiões e surpresas, mantendo a sensação de descobrir o mundo pela primeira vez.'},
  {number:'II',label:'A descoberta',title:'O tempo não segue uma única direção.',copy:'Espécies Paradoxo, formas alternativas e novos encontros colocam passado, presente e futuro lado a lado. O portal reúne o catálogo e deixa claro o que já existe e o que ainda está sendo preparado.'},
  {number:'III',label:'O caminho',title:'A aventura continua crescendo.',copy:'Os pilotos regionais, eventos e melhorias passam por fases de implementação e testes. Veja as atualizações para acompanhar o progresso real de cada parte da campanha.'}
];
const regionStages=[
  {name:'Decades',stage:'Disponível',type:'available',description:'Campanha principal baseada em Pokémon Decades, com progressão e viagem por Agente Regional.'},
  {name:'Kanto',stage:'Disponível para testes',type:'testing',description:'Aventura inspirada em FireRed/LeafGreen, em integração e validação no jogo principal.'},
  {name:'Hoenn',stage:'Disponível para testes',type:'testing',description:'Conteúdo baseado em Emerald com instalador de integração; a jogabilidade completa ainda passa por QA.'},
  {name:'Johto',stage:'Em construção',type:'building',description:'Conteúdo baseado em HeartGold/SoulSilver. A integração ao Decades ainda não está pronta para jogar.'},
  {name:'Sinnoh',stage:'Em construção',type:'building',description:'Expansão inspirada em Platinum, com mapas, eventos e testes ainda em preparação.'}
];
const futureRegions=['Unova','Kalos','Alola','Galar','Paldea','Hisui'];
const battleMechanics=[
  {name:'Mega Evolução',tag:'MEGA',description:'Transformações temporárias em batalha para Pokémon compatíveis com suas Mega Stones e requisitos.'},
  {name:'Z-Moves',tag:'Z',description:'Golpes especiais poderosos que exigem os equipamentos e as condições adequadas.'},
  {name:'Terastalização',tag:'TERA',description:'Mecânica de mudança estratégica de tipo em batalha, quando o recurso está disponível para o Pokémon.'}
];
const galleryIds=['GREATTUSK','SCREAMTAIL','IRONVALIANT','ROARINGMOON'];
const safeArt=p=>art(p);
const safeSprite=p=>sprite(p);
export function presentationPage(model){
  const featured=model.byId.get('MIRAIDON');
  const gallery=galleryIds.map(id=>model.byId.get(id)).filter(Boolean);
  const featureImage=featured?safeArt(featured):art(1008);
  const featureFallback=featured?safeSprite(featured):sprite(1008);
  return `<div class="container presentation-page">
    <div class="presentation-breadcrumb"><a href="/">Início</a><span aria-hidden="true">/</span><span aria-current="page">Apresentação</span></div>
    <article class="presentation-cover" aria-labelledby="presentation-title">
      <div class="presentation-cover-copy">
        <span class="presentation-overline"><span class="presentation-overline-dot"></span> FAN GAME · UMA NOVA JORNADA</span>
        <p class="presentation-edition">O UNIVERSO DE POKÉMON BLUE</p>
        <h1 id="presentation-title">DESSASTRE<br><em>PARADOXAL</em><span class="presentation-title-period">.</span></h1>
        <p class="presentation-lead">As 1.025 espécies oficiais de Pokémon, criaturas de fangames e fan forms em uma aventura multirregional com Mega Evolução, Z-Moves e Terastalização.</p>
        <div class="presentation-tags"><span>RPG Pokémon</span><span>Windows</span><span>Android · JoiPlay</span><span>Em desenvolvimento</span></div>
        <div class="presentation-actions"><a class="button button-primary" href="/downloads">${icon('download')} Baixar o jogo</a><a class="button button-secondary" href="#conheca-o-blue">Conhecer o projeto ${icon('arrow')}</a></div>
      </div>
      <div class="presentation-cover-art">
        <div class="presentation-art-halo"></div><div class="presentation-art-lines" aria-hidden="true"></div>
        <span class="presentation-art-top">PROTOCOLO BLUE / 1008</span>
        <img src="${esc(featureImage)}" data-fallback="${esc(featureFallback)}" alt="Ilustração de Miraidon, Pokémon Paradoxo" width="420" height="420" fetchpriority="high" />
        <span class="presentation-art-bottom">O FUTURO ESTÁ MAIS PERTO DO QUE PARECE</span>
      </div>
      <div class="presentation-cover-index" aria-hidden="true">01 / APRESENTAÇÃO</div>
    </article>
    <div class="presentation-facts" aria-label="Ficha do projeto">
      <div><small>POKÉMON OFICIAIS</small><strong>1.025 espécies + criações de fãs</strong></div>
      <div><small>BASE ORIGINAL</small><strong>Pokémon Decades</strong></div>
      <div><small>PLATAFORMAS</small><strong>PC e Android (JoiPlay)</strong></div>
      <div><small>STATUS</small><strong><i></i> Em desenvolvimento</strong></div>
    </div>
    <section id="conheca-o-blue" class="presentation-intro" aria-labelledby="presentation-intro-title">
      <div><span class="eyebrow">CONHEÇA O JOGO</span><h2 id="presentation-intro-title">O mundo que você conhece.<br><em>Uma história para redescobrir.</em></h2></div>
      <div class="presentation-intro-copy"><p>Pokémon Blue: Dessastre Paradoxal é um projeto de fã que expande a experiência de Pokémon Decades. A ideia é reunir a nostalgia da aventura clássica com novos Pokémon, possibilidades estratégicas e viagens entre regiões.</p><p>Do primeiro parceiro às batalhas decisivas, cada fase acrescenta mais caminhos. O projeto ainda está em desenvolvimento: sistemas e regiões são integrados e testados progressivamente.</p></div>
    </section>
    <section class="presentation-section presentation-dex" aria-labelledby="presentation-dex-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">POKÉDEX EXPANDIDA</span><h2 id="presentation-dex-title">1.025 Pokémon oficiais. <em>E muito mais.</em></h2><p>Um universo que reúne as espécies clássicas e novas possibilidades criadas pela comunidade.</p></div><a class="text-link" href="/pokedex">Explorar a Pokédex ${icon('arrow')}</a></div>
      <div class="presentation-dex-grid">
        <article class="presentation-dex-card"><strong>1.025</strong><h3>Espécies oficiais</h3><p>O catálogo reúne Pokémon das nove gerações oficiais, de Bulbasaur a Pecharunt.</p></article>
        <article class="presentation-dex-card"><span class="presentation-dex-symbol">FAN</span><h3>Pokémon de fangames</h3><p>Espécies e ideias de projetos de fãs ampliam a descoberta além da Pokédex tradicional.</p></article>
        <article class="presentation-dex-card"><span class="presentation-dex-symbol">FORMAS</span><h3>Fan forms e Paradoxos</h3><p>Formas regionais, variantes autorais, evoluções inéditas, Paradoxos e novas Mega Evoluções.</p></article>
      </div>
      <p class="presentation-content-note">O catálogo apresenta o universo do projeto; a presença de cada espécie, forma ou recurso na campanha depende da versão instalada e das etapas já implementadas.</p>
    </section>
    <section class="presentation-section" aria-labelledby="presentation-features-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">POR QUE JOGAR?</span><h2 id="presentation-features-title">Uma aventura. <em>Muitas possibilidades.</em></h2></div><a class="text-link" href="/o-que-mudou">Descubra o que mudou ${icon('arrow')}</a></div>
      <div class="presentation-feature-grid">${highlights.map(item=>`<article class="presentation-feature"><div class="presentation-feature-top"><span class="presentation-feature-icon">${icon(item.icon)}</span><span>${item.number}</span></div><h3>${esc(item.title)}</h3><p>${esc(item.description)}</p></article>`).join('')}</div>
    </section>
    <section class="presentation-section presentation-regions" aria-labelledby="presentation-regions-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">UM MUNDO EM EXPANSÃO</span><h2 id="presentation-regions-title">Regiões disponíveis, <em>em construção e futuras.</em></h2><p>Comece pela campanha principal e acompanhe cada região conforme sua integração avança.</p></div><a class="text-link" href="/regioes">Ver o circuito regional ${icon('arrow')}</a></div>
      <div class="presentation-region-grid">${regionStages.map(region=>`<article class="presentation-region-card"><span class="presentation-region-label presentation-region-label--${region.type}">${esc(region.stage)}</span><h3>${esc(region.name)}</h3><p>${esc(region.description)}</p></article>`).join('')}</div>
      <div class="presentation-future"><div><span class="eyebrow">EXPANSÕES FUTURAS</span><p>Estas regiões estão planejadas, mas ainda não são destinos jogáveis.</p></div><div class="presentation-future-list">${futureRegions.map(region=>`<span>${esc(region)}</span>`).join('')}</div></div>
      <p class="presentation-content-note">“Disponível para testes” não significa campanha concluída: Kanto e Hoenn dependem da integração da versão instalada. Johto ainda não está liberada na campanha principal. Confirme o estado de cada pacote na página de <a href="/downloads">downloads</a>.</p>
    </section>
    <section class="presentation-timeline" aria-labelledby="presentation-timeline-title">
      <div class="presentation-timeline-head"><span class="eyebrow">UMA JORNADA ALÉM DO TEMPO</span><h2 id="presentation-timeline-title">O passado, o presente <em>e o que vem depois.</em></h2><p>O universo de Dessastre Paradoxal é feito de descobertas e de novas possibilidades.</p></div>
      <div class="presentation-chapters">${chapters.map(ch=>`<article class="presentation-chapter"><span class="presentation-chapter-number">${ch.number}</span><div><small>${esc(ch.label)}</small><h3>${esc(ch.title)}</h3><p>${esc(ch.copy)}</p></div></article>`).join('')}</div>
    </section>
    <section class="presentation-section presentation-strategy" aria-labelledby="presentation-strategy-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">SISTEMAS DE BATALHA</span><h2 id="presentation-strategy-title">Mega, Z-Move e <em>Terastal.</em></h2><p>Três mecânicas para mudar o rumo de uma batalha.</p></div></div>
      <div class="presentation-mechanic-grid">${battleMechanics.map(mechanic=>`<article class="presentation-mechanic-card"><span class="presentation-mechanic-mark">${esc(mechanic.tag)}</span><h3>${esc(mechanic.name)}</h3><p>${esc(mechanic.description)}</p></article>`).join('')}</div>
      <p class="presentation-content-note">Na campanha Decades, Mega Evolução, Z-Moves e Terastalização ficam habilitados por padrão; o Dynamax fica desativado. Habilitar a mecânica não concede automaticamente Mega Ring, Z-Ring, Tera Orb ou itens especiais.</p>
      <div class="presentation-section-heading presentation-balance-heading"><div><span class="eyebrow">BALANCEAMENTO INTELIGENTE</span><h2>Uma dificuldade que <em>acompanha sua jornada.</em></h2></div><a class="text-link" href="/balanceamento?regiao=kanto">Ver balanceamento ${icon('arrow')}</a></div>
      <div class="presentation-balance-grid">
        <article><span>01 / PROGRESSÃO</span><h3>Insígnias e esmeraldas</h3><p>Cada insígnia regional inédita conta uma vez para a progressão global. O level cap e as faixas de dificuldade orientam a evolução da aventura.</p></article>
        <article><span>02 / ENCONTROS</span><h3>Selvagens que evoluem</h3><p>Conforme o level cap aumenta, formas evoluídas passam a aparecer ao lado de suas pré-evoluções, respeitando os encontros de cada área.</p></article>
        <article><span>03 / DESAFIOS</span><h3>Treinadores mais preparados</h3><p>Equipes e evoluções dos adversários acompanham a progressão; o modo Master aumenta o nível de desafio, sem depender de níveis fixos nos guias.</p></article>
        <article><span>04 / REGIÕES</span><h3>Itens-chave e HMs locais</h3><p>Insígnias, itens-chave e HMs são independentes por região. Ao viajar, os itens locais são preservados para seu retorno, mas não funcionam automaticamente em outra região.</p></article>
      </div>
      <p class="presentation-content-note">As regras são aplicadas conforme o tipo de encontro e a região. Novos sistemas e ajustes entram nas versões integradas gradualmente.</p>
    </section>
    <section class="presentation-section" aria-labelledby="presentation-gallery-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">GALERIA · ENCONTROS IMPROVÁVEIS</span><h2 id="presentation-gallery-title">Conheça alguns <em>Pokémon Paradoxo.</em></h2><p>Espécies do catálogo do projeto, em destaque na nossa Pokédex.</p></div><a class="text-link" href="/pokedex?grupo=paradox">Ver todos os Paradoxos ${icon('arrow')}</a></div>
      <div class="presentation-gallery">${gallery.map((p,i)=>`<a class="presentation-gallery-card" href="${pokemonPath(p)}" style="--gallery-hue:${[210,345,265,35][i]}"><div class="presentation-gallery-art"><span class="presentation-gallery-number">0${i+1} / PARADOXO</span><img src="${esc(safeArt(p))}" data-fallback="${esc(safeSprite(p))}" alt="${esc(p.name)}" loading="lazy" width="230" height="230"/></div><div class="presentation-gallery-caption"><div><small>ESPÉCIE EM DESTAQUE</small><h3>${esc(p.name)}</h3></div>${icon('arrow')}</div></a>`).join('')}</div>
      <p class="presentation-gallery-note">As imagens ilustram espécies da Pokédex e não representam capturas de tela da jogabilidade. A disponibilidade no jogo pode variar conforme a versão.</p>
    </section>
    <section class="presentation-detail-grid" aria-label="Mais sobre o projeto">
      <article class="presentation-info-panel"><span class="eyebrow">EXPERIÊNCIA</span><h2>O que você vai encontrar.</h2><ul><li>Exploração e progressão inspiradas nos jogos clássicos de Pokémon.</li><li>Novas espécies, formas e encontros ao lado de Pokémon conhecidos.</li><li>Desafios e equipes com balanceamento adaptado à campanha.</li><li>Regiões e eventos adicionais em diferentes estágios de desenvolvimento.</li></ul><a class="text-link" href="/guias">Explorar os guias ${icon('arrow')}</a></article>
      <article class="presentation-info-panel presentation-status"><span class="eyebrow">ACOMPANHE A EVOLUÇÃO</span><h2>Um projeto vivo.</h2><p>Decades é a campanha principal. Kanto e Hoenn têm versões de teste em integração; Johto e Sinnoh seguem em construção. Unova, Kalos, Alola, Galar, Paldea e Hisui fazem parte do planejamento futuro.</p><p>O estágio real de cada versão pode mudar. Consulte sempre a página de downloads e o diário do projeto antes de instalar ou atualizar.</p><a class="text-link" href="/atualizacoes">Últimas atualizações ${icon('arrow')}</a></article>
    </section>
    <section class="presentation-final" aria-labelledby="presentation-final-title"><div><span class="eyebrow">SUA PRÓXIMA JORNADA COMEÇA AQUI</span><h2 id="presentation-final-title">Pronto para entrar <em>nessa história?</em></h2><p>Descubra o jogo, escolha sua versão e acompanhe cada novo capítulo de Dessastre Paradoxal.</p></div><div class="presentation-final-actions"><a class="button button-primary" href="/downloads">${icon('download')} Ir para downloads</a><a class="button button-secondary" href="/pokedex">Explorar a Pokédex ${icon('arrow')}</a></div></section>
    <p class="presentation-disclaimer">Projeto independente feito por fã, sem afiliação com Nintendo, Game Freak ou Creatures. Pokémon e personagens oficiais pertencem aos respectivos titulares.</p>
  </div>`;
}
