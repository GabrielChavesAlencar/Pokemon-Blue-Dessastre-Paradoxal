import {art,esc,icon,pokemonPath,sprite} from './utils.js';

const highlights=[
  {icon:'map',number:'01',title:'Explore diferentes regiões',description:'Comece por Decades, descubra a experiência de Kanto e acompanhe os pilotos de Johto, Hoenn e as próximas expansões. Cada região tem seus próprios desafios e uma jornada em construção.'},
  {icon:'spark',number:'02',title:'Encontre o inesperado',description:'Pokémon Paradoxo, novas formas, evoluções e uma geração autoral ampliam as possibilidades de montar sua equipe sem substituir as espécies clássicas.'},
  {icon:'shield',number:'03',title:'Crie sua estratégia',description:'Batalhas, líderes, campeões e progressão por insígnias fazem parte de uma aventura que evolui a cada atualização do projeto.'}
];
const chapters=[
  {number:'I',label:'A origem',title:'Uma aventura que começa no conhecido.',copy:'O Blue nasce sobre a base de Pokémon Decades. A proposta é expandir a jornada com novas histórias, regiões e surpresas, mantendo a sensação de descobrir o mundo pela primeira vez.'},
  {number:'II',label:'A descoberta',title:'O tempo não segue uma única direção.',copy:'Espécies Paradoxo, formas alternativas e novos encontros colocam passado, presente e futuro lado a lado. O portal reúne o catálogo e deixa claro o que já existe e o que ainda está sendo preparado.'},
  {number:'III',label:'O caminho',title:'A aventura continua crescendo.',copy:'Os pilotos regionais, eventos e melhorias passam por fases de implementação e testes. Veja as atualizações para acompanhar o progresso real de cada parte da campanha.'}
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
        <p class="presentation-lead">Uma jornada fora do tempo. Regiões para explorar, espécies para descobrir e um mundo Pokémon que não para de evoluir.</p>
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
      <div><small>PROJETO</small><strong>Pokémon Blue</strong></div>
      <div><small>BASE ORIGINAL</small><strong>Pokémon Decades</strong></div>
      <div><small>PLATAFORMAS</small><strong>PC e Android (JoiPlay)</strong></div>
      <div><small>STATUS</small><strong><i></i> Em desenvolvimento</strong></div>
    </div>
    <section id="conheca-o-blue" class="presentation-intro" aria-labelledby="presentation-intro-title">
      <div><span class="eyebrow">CONHEÇA O JOGO</span><h2 id="presentation-intro-title">O mundo que você conhece.<br><em>Uma história para redescobrir.</em></h2></div>
      <div class="presentation-intro-copy"><p>Pokémon Blue: Dessastre Paradoxal é um projeto de fã que expande a experiência de Pokémon Decades. A ideia é reunir a nostalgia da aventura clássica com novos Pokémon, possibilidades estratégicas e viagens entre regiões.</p><p>Do primeiro parceiro às batalhas decisivas, cada fase acrescenta mais caminhos. O projeto ainda está em desenvolvimento: sistemas e regiões são integrados e testados progressivamente.</p></div>
    </section>
    <section class="presentation-section" aria-labelledby="presentation-features-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">POR QUE JOGAR?</span><h2 id="presentation-features-title">Uma aventura. <em>Muitas possibilidades.</em></h2></div><a class="text-link" href="/o-que-mudou">Descubra o que mudou ${icon('arrow')}</a></div>
      <div class="presentation-feature-grid">${highlights.map(item=>`<article class="presentation-feature"><div class="presentation-feature-top"><span class="presentation-feature-icon">${icon(item.icon)}</span><span>${item.number}</span></div><h3>${esc(item.title)}</h3><p>${esc(item.description)}</p></article>`).join('')}</div>
    </section>
    <section class="presentation-timeline" aria-labelledby="presentation-timeline-title">
      <div class="presentation-timeline-head"><span class="eyebrow">UMA JORNADA ALÉM DO TEMPO</span><h2 id="presentation-timeline-title">O passado, o presente <em>e o que vem depois.</em></h2><p>O universo de Dessastre Paradoxal é feito de descobertas e de novas possibilidades.</p></div>
      <div class="presentation-chapters">${chapters.map(ch=>`<article class="presentation-chapter"><span class="presentation-chapter-number">${ch.number}</span><div><small>${esc(ch.label)}</small><h3>${esc(ch.title)}</h3><p>${esc(ch.copy)}</p></div></article>`).join('')}</div>
    </section>
    <section class="presentation-section" aria-labelledby="presentation-gallery-title">
      <div class="presentation-section-heading"><div><span class="eyebrow">GALERIA · ENCONTROS IMPROVÁVEIS</span><h2 id="presentation-gallery-title">Conheça alguns <em>Pokémon Paradoxo.</em></h2><p>Espécies do catálogo do projeto, em destaque na nossa Pokédex.</p></div><a class="text-link" href="/pokedex?grupo=paradox">Ver todos os Paradoxos ${icon('arrow')}</a></div>
      <div class="presentation-gallery">${gallery.map((p,i)=>`<a class="presentation-gallery-card" href="${pokemonPath(p)}" style="--gallery-hue:${[210,345,265,35][i]}"><div class="presentation-gallery-art"><span class="presentation-gallery-number">0${i+1} / PARADOXO</span><img src="${esc(safeArt(p))}" data-fallback="${esc(safeSprite(p))}" alt="${esc(p.name)}" loading="lazy" width="230" height="230"/></div><div class="presentation-gallery-caption"><div><small>ESPÉCIE EM DESTAQUE</small><h3>${esc(p.name)}</h3></div>${icon('arrow')}</div></a>`).join('')}</div>
      <p class="presentation-gallery-note">As imagens ilustram espécies da Pokédex e não representam capturas de tela da jogabilidade. A disponibilidade no jogo pode variar conforme a versão.</p>
    </section>
    <section class="presentation-detail-grid" aria-label="Mais sobre o projeto">
      <article class="presentation-info-panel"><span class="eyebrow">EXPERIÊNCIA</span><h2>O que você vai encontrar.</h2><ul><li>Exploração e progressão inspiradas nos jogos clássicos de Pokémon.</li><li>Novas espécies, formas e encontros ao lado de Pokémon conhecidos.</li><li>Desafios e equipes com balanceamento adaptado à campanha.</li><li>Regiões e eventos adicionais em diferentes estágios de desenvolvimento.</li></ul><a class="text-link" href="/guias">Explorar os guias ${icon('arrow')}</a></article>
      <article class="presentation-info-panel presentation-status"><span class="eyebrow">ACOMPANHE A EVOLUÇÃO</span><h2>Um projeto vivo.</h2><p>Decades é a base da experiência principal. Kanto, Johto e Hoenn possuem iniciativas e pilotos regionais, com integrações e validações em andamento. Sinnoh e outras expansões continuam em preparação.</p><p>O estágio real de cada versão pode mudar. Consulte sempre a página de downloads e o diário do projeto antes de instalar ou atualizar.</p><a class="text-link" href="/atualizacoes">Últimas atualizações ${icon('arrow')}</a></article>
    </section>
    <section class="presentation-final" aria-labelledby="presentation-final-title"><div><span class="eyebrow">SUA PRÓXIMA JORNADA COMEÇA AQUI</span><h2 id="presentation-final-title">Pronto para entrar <em>nessa história?</em></h2><p>Descubra o jogo, escolha sua versão e acompanhe cada novo capítulo de Dessastre Paradoxal.</p></div><div class="presentation-final-actions"><a class="button button-primary" href="/downloads">${icon('download')} Ir para downloads</a><a class="button button-secondary" href="/pokedex">Explorar a Pokédex ${icon('arrow')}</a></div></section>
    <p class="presentation-disclaimer">Projeto independente feito por fã, sem afiliação com Nintendo, Game Freak ou Creatures. Pokémon e personagens oficiais pertencem aos respectivos titulares.</p>
  </div>`;
}
