// Conteúdo dinâmico dos guias: a fonte da verdade são os dados exportados do Blue.
const references=[
  {label:'PokéCommunity — Pokémon Decades',url:'https://www.pokecommunity.com/threads/pokemon-decades.540970/'},
  {label:'Eevee Expo — Pokémon Decades',url:'https://eeveeexpo.com/threads/9341/'}
];
const fmt=x=>Number(x??0).toLocaleString('pt-BR');
const section=(title,paragraphs,links=[])=>({title,paragraphs,links});
const link=(label,href)=>({label,href});
const article=(id,title,excerpt,category,icon,sections,options={})=>
  ({id,title,excerpt,category,icon,minutes:Math.max(3,Math.ceil(sections.length*1.4)),sections,...options});
export function generateGuides({catalog,locations,details,editorial}) {
  if(!Array.isArray(catalog?.species)||!Array.isArray(locations?.locations)||!details?.species||!Array.isArray(editorial?.guides))
    throw new Error('Exportação incompleta: não é seguro sincronizar guias.');
  const guides=structuredClone(editorial.guides);
  const species=catalog.species,areas=locations.locations;
  const fan=species.filter(p=>p.generation==='dessastre-paradoxal');
  const megas=catalog.customForms??[];
  const pending=fan.filter(p=>p.pending);
  const paradox=species.filter(p=>(p.flags??[]).includes('Paradox'));
  const methods=new Map(),encountered=new Set();
  let tables=0;
  for(const area of areas)for(const version of area.versions??[])for(const method of version.methods??[]) {
    tables++;
    methods.set(method.id,(methods.get(method.id)??0)+1);
    for(const slot of method.slots??[])encountered.add(slot[0]);
  }
  const methodNames={Land:'grama',LandNight:'grama à noite',LandMorning:'grama de manhã',Water:'surf',OldRod:'vara antiga',GoodRod:'vara boa',SuperRod:'supervara',RockSmash:'quebrar pedras',HeadbuttLow:'árvores comuns',HeadbuttHigh:'árvores raras',Cave:'cavernas',PokeRadar:'Poké Radar'};
  const methodText=[...methods.entries()].sort((a,b)=>b[1]-a[1]).slice(0,8).map(([id,count])=>(methodNames[id]??id)+' ('+fmt(count)+')').join('; ')||'Nenhum método de encontro encontrado.';
  const warning='Este guia lê a última exportação pública do Blue. Mudanças locais no Blue Studio só aparecem após exportar os PBS, enviar os JSON ao GitHub e publicar. Eventos e scripts da história não podem ser deduzidos das tabelas de encontros.';
  const live={synced:true,origin:'Dados atuais do Blue'};
  const legacy={synced:false,origin:'Referência do Pokémon Decades',sources:references};
  const first=guides.find(g=>g.id==='primeiros-passos');
  if(first) {
    first.synced=true;
    first.sections.push(section('O estado atual do arquivo Blue',[
      'Nesta publicação são '+fmt(species.length)+' espécies, '+fmt(areas.length)+' áreas com encontros e '+fmt(paradox.length)+' espécies marcadas como Paradoxo.',
      warning
    ],[link('Pokédex atual','/pokedex'),link('Localizações atuais','/localizacoes')]));
  }
  const encounters=guides.find(g=>g.id==='encontrar-pokemon');
  if(encounters) {
    encounters.synced=true;
    encounters.sections.push(section('Tabelas de encontros atualizadas',[
      'A base publicada contém '+fmt(areas.length)+' áreas, '+fmt(tables)+' tabelas de métodos/variações e '+fmt(encountered.size)+' identificadores de Pokémon em encontros.',
      'Os métodos mais frequentes são: '+methodText+'.',
      warning
    ],[link('Explorar locais','/localizacoes')]));
  }
  const paradoxGuide=guides.find(g=>g.id==='pokemon-paradoxo');
  if(paradoxGuide) {
    paradoxGuide.synced=true;
    paradoxGuide.sections.push(section('Paradoxos cadastrados no Blue',[
      'Atualmente '+fmt(paradox.length)+' espécies da Pokédex estão marcadas como Paradoxo. O total é calculado a partir do catálogo exportado.',
      'A presença na Pokédex não garante encontro selvagem: verifique na ficha e em Localizações.'
    ],[link('Filtrar Paradoxos','/pokedex?grupo=paradox')]));
  }
  const authorGuide=guides.find(g=>g.id==='dessastre-paradoxal');
  if(authorGuide) {
    authorGuide.synced=true;
    authorGuide.sections=[
      section('A geração autoral agora',[
        'No último catálogo, Dessastre Paradoxal tem '+fmt(fan.length)+' espécies e '+fmt(megas.length)+' Mega Evoluções autorais. Os totais mudam automaticamente com a exportação.',
        'Consulte cada ficha para conferir tipos, atributos, habilidades e golpes na versão publicada.'
      ],[link('Geração Dessastre Paradoxal','/pokedex?geracao=dessastre-paradoxal')]),
      section('Registros pendentes',[
        'Há '+fmt(pending.length)+' espécies autorais marcadas como pendentes'+(pending.length?': '+pending.slice(0,12).map(p=>p.name).join(', ')+(pending.length>12?' e outras.':'.'):'.'),
        'Um registro pendente não deve ser tratado como disponível em batalha ou por encontro. A existência de sprites e golpes não comprova uma implementação funcional.'
      ]),
      section('Formas e encontros',[
        'O catálogo contém '+fmt(megas.length)+' formas Mega autorais. Compare as formas pela ficha da espécie base.',
        warning
      ],[link('Localizações','/localizacoes')])
    ];
  }
  const calculated=[
    article('blue-pokedex-atual','Pokédex do Blue atualizada','Quantidades reais de espécies, Paradoxos, Megas e pendências.','Arquivo Blue','grid',[
      section('Pokédex publicada',[
        'O Blue apresenta '+fmt(species.length)+' espécies, '+fmt(catalog.counts?.forms??0)+' formas herdadas e '+fmt(megas.length)+' Mega Evoluções autorais.',
        'A geração autoral conta com '+fmt(fan.length)+' espécies, das quais '+fmt(pending.length)+' seguem pendentes.'
      ],[link('Abrir a Pokédex','/pokedex'),link('Ver geração autoral','/pokedex?geracao=dessastre-paradoxal')]),
      section('Pokémon Paradoxo',[
        'Existem '+fmt(paradox.length)+' espécies marcadas como Paradoxo. É possível filtrar a Pokédex e verificar dados atuais, mas nem todo registro está necessariamente capturável.'
      ],[link('Pokémon Paradoxo','/pokedex?grupo=paradox')]),
      section('Como as fichas mudam',[warning])
    ],live),
    article('blue-mapa-encontros','Mapa de encontros do Blue','Consulte rotas e métodos reconstruídos da versão exportada do jogo.','Arquivo Blue','map',[
      section('Encontros disponíveis na exportação',[
        'As tabelas atuais abrangem '+fmt(areas.length)+' áreas, '+fmt(tables)+' tabelas de métodos/variações e '+fmt(encountered.size)+' identificadores encontrados.',
        'As chances se referem ao peso de cada Pokémon em sua tabela e não à taxa de captura.'
      ],[link('Pesquisar encontros','/localizacoes')]),
      section('Métodos encontrados',['Os métodos mais frequentes são: '+methodText+'.',warning]),
      section('Áreas cadastradas',[
        'Veja exemplos concretos de áreas do arquivo atual. A ordem abaixo não representa a sequência da história.'
      ],areas.slice(0,10).map(a=>link(a.name,'/localizacoes/'+encodeURIComponent(a.id))))
    ],live)
  ];
  const decades=[
    article('decades-beatha','Beatha e as 18 Esmeraldas','Os objetivos centrais da história herdada de Pokémon Decades.','Campanha Decades','compass',[
      section('Região de Beatha',[
        'No Pokémon Decades original, a aventura acontece na região de Beatha. A missão é obter 18 Type Emeralds vencendo os Type Masters e enfrentar a ameaça do Zenith Domain.',
        'O anúncio descreve ainda 51 Mystery Zones, Safari Zone e Battle Paradise. Esses números documentam o jogo-base e não certificam o estado de cada missão no Blue.'
      ]),
      section('Como se orientar no Blue',[
        'Consulte a campanha dentro do jogo para saber a ordem real de objetivos e recompensas. As localizações do site são extraídas dos PBS e não dos eventos de história.',
        'As alterações próprias do Blue podem substituir ou remover partes do percurso original.'
      ],[link('Locais atuais do Blue','/localizacoes'),link('Diário de atualizações','/atualizacoes')])
    ],legacy),
    article('decades-iniciais','Como escolher seu Pokémon inicial','As cinco opções de inicial descritas pelos criadores do Decades.','Campanha Decades','spark',[
      section('As escolhas originais',[
        'Pokémon Decades descreve cinco modalidades: VGC Starters, iniciais tradicionais, escolha dentre primeiros estágios, escolha aleatória e escolha monotype.',
        'A postagem original anuncia mais de 547 opções de primeiros estágios e escolha anterior à chegada ao Aeroporto Internacional. Esse fluxo precisa ser conferido na versão atual do Blue.'
      ]),
      section('Planejamento da equipe',[
        'Depois de escolher, use a Pokédex do Blue para conferir tipos, evoluções e golpes. Consulte os encontros para planejar o restante do time.',
        warning
      ],[link('Pokédex','/pokedex'),link('Encontros','/localizacoes')])
    ],legacy),
    article('decades-batalhas','Battle Paradise e formatos de batalha','As opções de batalhas competitivas anunciadas na base Decades.','Batalhas Decades','shield',[
      section('Battle Paradise',[
        'O criador anuncia um sandbox com mais de 438 treinadores e batalhas individuais, duplas e triplas.',
        'Há formatos como Smogon Cup (nível 100), VGC Cup (nível 50), NFE Cup (nível 30) e Little Cup (nível 5). Esta é uma referência histórica: o funcionamento no Blue depende dos scripts da versão instalada.'
      ]),
      section('Preparação antes de batalhar',[
        'Compare os atributos, habilidades, golpes e tipos no portal antes de montar uma equipe para cada formato.',
        'Se uma regra ou modo não estiver implementado no Blue, o jogo atual prevalece sobre este guia de referência.'
      ],[link('Consultar a Pokédex','/pokedex')])
    ],legacy),
    article('decades-ferramentas','Ferramentas de treinador do Decades','DexNav, Form Trader, PSS, tutores e treinamento facilitado.','Sistemas Decades','layers',[
      section('Treinamento da equipe',[
        'O Decades original anuncia EV/IV Allocator, Ultimate Move Tutor, All Moves Disk, Ability Vial, mints de natureza e opções de experiência.',
        'O criador descreve Pokémon gerados com IVs 31 e personalização de EVs/IVs. Mudanças posteriores do Blue podem ter alterado essas regras.'
      ]),
      section('Explorar com menos tempo perdido',[
        'Entre os recursos anunciados estão DexNav, PSS e Trainer Suites, Form Trader, encontros por pesca/árvores/pedras, viagem rápida pelo telefone, repelente alternável e aceleração de velocidade.',
        'Confirme no jogo os atalhos e requisitos disponíveis; as tabelas PBS não provam o funcionamento desses sistemas.'
      ],[link('Ver métodos de encontro','/localizacoes')])
    ],legacy),
    article('decades-mecanicas','Mecânicas de batalha do Decades','Mega, Z-Power, Dynamax e Terastalização na base do fangame.','Batalhas Decades','book',[
      section('Recursos de batalha anunciados',[
        'Pokémon Decades anuncia Mega Evolução, Z-Power, Dynamax e Terastalização, além de mecânicas das gerações recentes.',
        'O anúncio menciona Adventure Guide, Wiki Dex e a tecla T durante a batalha para consultar combinações de tipos.'
      ]),
      section('Diferenças importantes no Blue',[
        'O Blue pode alterar Pokémon, golpes, habilidades e regras. O portal acompanha os dados exportados, mas não testa automaticamente a lógica dos scripts de batalha.',
        'Consulte os efeitos no jogo e o diário de mudanças antes de considerar um recurso confirmado.'
      ],[link('Guia da base de batalha','/guias/base-geracao-9'),link('Pokédex Blue','/pokedex')])
    ],legacy)
  ];
  const output=[...guides,...calculated,...decades];
  if(new Set(output.map(g=>g.id)).size!==output.length)throw new Error('IDs de guia duplicados.');
  return {guides:output,generatedFrom:catalog.updatedAt??null};
}
