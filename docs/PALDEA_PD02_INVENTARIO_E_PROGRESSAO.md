# PD02 — inventário e progressão de Paldea

Escopo documental. O [plano multirregional](PLANO_REGIOES_DESSASTRE_V2.md)
prevê uma campanha **Scarlet + Violet**, com The Teal Mask e The Indigo Disk
como capítulos extras. A [publicadora](https://www.pokemon.com/uk/pokemon-video-games/pokemon-scarlet-and-pokemon-violet)
apresenta três histórias que se cruzam em um mundo aberto; não transformar
Paldea numa sequência artificial de rotas. A ordem abaixo é de inventário,
não de desbloqueio. Usar o [catálogo Blue](../site/public/data/regions.json)
e o [atlas visual PD05](PALDEA_PD05_ATLAS_VISUAL_E_TILES_KANTO.md). Chaves C,
P, G, T e B são rótulos de planejamento, não MapIDs nem flags novas.

## Cidades e vilas — 12

| Chave | Local | Âncoras e conexões a preservar |
|---|---|---|
| C01 | Cabo Poco | Casas do jogador e de Nemona, aproximação à praia e Poco Path. Não contar como área de província ou ponto de montaria já adquirido. |
| C02 | Los Platos | Praça e Centro Pokémon; P01 antes de Mesagoza, com retorno ao caminho inicial. |
| C03 | Mesagoza | Portões sul/leste/oeste, praça e escadaria da Naranja Academy (Scarlet) ou Uva Academy (Violet); usar uma academia navegável, sem duplicar história. |
| C04 | Cortondo | P02, olivais e Oliveroll de Katy; manter a quadra da prova e a entrada real do ginásio. |
| C05 | Artazon | Borda P03/P10, moinhos/jardins e prova de Sunflora de Brassius. |
| C06 | Levincia | P11, cidade costeira de três partes, pontes/orla e prova de Iono; farol acessível por caminho. |
| C07 | Cascarrafa | Eixo vertical, elevadores e água, entrada do deserto e ginásio de Kofu; prova remete ao mercado de Porto Marinada. |
| C08 | Porto Marinada | P08, cais, mercado de leilão e conexão à costa ocidental; não é outro ginásio. |
| C09 | Zapapico | P12 e saída para Dalizapa; despachar a variante de armadura de Charcadet como serviço/quest da cidade, não ginásio. |
| C10 | Medali | P09, praças e Treasure Eatery; preservar investigação do prato e combate de Larry; acesso regional a Zero Gate é separado da cidade. |
| C11 | Alfornada | P06, patamar, acesso pela caverna e ginásio de Tulip; não criar subida direta obrigatória. |
| C12 | Montenevera | Glaseado Mountain, palco e ginásio de Ryme; manter separado do ginásio de Grusha. |

Glaseado Gym é um marco da montanha, **não** uma 13ª cidade. A Liga,
estações, Centros isolados, Zero Gate e o marco de Glaseado têm fichas
distintas de cidades. Mossui Town e a Blueberry Academy pertencem aos DLCs,
fora da contagem das 12. Referência: [inventário geográfico](https://bulbapedia.bulbagarden.net/wiki/Paldea).

## Áreas numeradas das províncias — 15, sem rotas fictícias

| Chave | Área original | Âncoras de mapa, não ordem de campanha |
|---|---|---|
| P01 | South Province (Area One) | Campos de Los Platos e portão sul de Mesagoza; início do corredor e Grasswither Shrine como desvio. |
| P02 | South Province (Area Two) | Acesso oeste de Mesagoza, Cortondo, olivais e Grand Olive Orchard; saída para o oeste. |
| P03 | South Province (Area Three) | Acesso leste de Mesagoza, cânions, Klawf e ligação a Artazon; representar a diferença entre desfiladeiro, platô e área de ataque. |
| P04 | South Province (Area Four) | Campo ondulado no sudoeste, rios e encostas; registrar alternativas terrestres e requisitos dos atalhos em separado. |
| P05 | South Province (Area Five) | Campos ao sudeste, rio e zonas úmidas, Secluded Beach; verificar ligações a P03 e Artazon. |
| P06 | South Province (Area Six) | Alfornada Cavern, patamar de Alfornada, catarata e Leaking Tower; não tratar a caverna como mero portal. |
| P07 | West Province (Area One) | Encostas e passagem rumo a Cascarrafa, Bombirdier, Segin Squad e Icerend Shrine; não unificar seus acessos. |
| P08 | West Province (Area Two) | Porto Marinada, costa, Colonnade Hollow e bordas de Asado Desert e Casseroya. |
| P09 | West Province (Area Three) | Medali, caminhos a Casseroya, Glaseado e Dalizapa; acesso a Zero Gate tem condição narrativa própria. |
| P10 | East Province (Area One) | Artazon, vale/rios, base Schedar e ponte rumo a Levincia; não fundir a base e a via pública. |
| P11 | East Province (Area Two) | Entorno de Levincia, farol em falésia, costa, conexão por rio/ponte a P10 e caminho a P12. |
| P12 | East Province (Area Three) | Zona de mineração, Orthworm, Zapapico e ligação a Tagtree/Dalizapa/norte; manter terreno escavado e alturas. |
| P13 | North Province (Area One) | Planalto rugoso e lago das torres; liga Glaseado, Tagtree, P12 e P14, sem inventar saídas sobre falésias. |
| P14 | North Province (Area Two) | Floresta de bambu, Fury Falls, Firescourge Shrine, base Caph e limite P13/P12. |
| P15 | North Province (Area Three) | Faixa costeira entre Glaseado e North Paldean Sea; campo florido e base Ruchbah. |

## Setores nomeados, mares e Área Zero

| Grupo | Setores distintos | Regra de travessia |
|---|---|---|
| Prólogo sul | Poco Path, Inlet Grotto, praia e farol inicial. | Caminho inicial, encontro com montaria, caverna e saída de história não são substituídos por teleporte. |
| Centro-sul e Liga | Academia de Mesagoza, Alfornada Cavern, via da Pokémon League. | A academia é o polo das três histórias; Champion Assessment e ingresso na Liga têm gates próprios, não passe geral para a cratera. |
| Oeste e noroeste | Asado Desert, Colonnade Hollow, Casseroya Lake, Socarrat Trail. | Deserto, lago e ramais preservam o contraste de terreno: Titãs de Asado e Casseroya são objetivos distintos. |
| Leste e norte | Tagtree Thicket, Dalizapa Passage, Glaseado Mountain, Glaseado Gym. | Floresta, túnel/galerias, montanha nevada e ginásio são setores distintos; Dalizapa é passagem, não desbloqueio universal de escalada. |
| Quatro mares | South Paldean Sea, West Paldean Sea, East Paldean Sea, North Paldean Sea. | Separar costa, bancos de areia e ilhas; não criar atalho entre mares e províncias por encostar numa borda de mapa. |
| Santuários e vistas | Grasswither, Icerend, Groundblight (Socarrat), Firescourge; inventariar os Ten Sights como marcos. | Em cada santuário, manter as estacas e o encontro único; não confundir ponto panorâmico nem destino visual com passagem. |
| Great Crater / Area Zero | Zero Gate, descida, estações de pesquisa 1–4, Zero Lab; Area Zero Underdepths é expansão. | Não aceitar salto, planar, escalar, visitar ou viajar como atalho ao gate narrativo. Habilitar painéis de alcance conforme estações visitadas e o estado do capítulo. |

Para transformar o mundo em 2D, desenhar um grafo de setores com
saídas reversíveis onde houver ida e volta, ligações de altura e condições
de passagem. Para cada margem, ponte, queda, encosta e escalada, registrar
a intenção no original e um teste negativo antes de obter a habilidade.
Separar desbloqueio narrativo, característica de colisão e ponto de retorno.
Não introduzir autoescalonamento novo por causa do recorte; confrontar
níveis e encontros originais com o balanceamento existente do Blue sem
inventar uma ordem fixa de ginásios.

## Victory Road — oito chaves locais

| Chave | Local / líder | Chave no Blue | Prova de referência |
|---|---|---|---|
| G01 | Cortondo / Katy, Inseto | CORTONDO | Oliveroll. |
| G02 | Artazon / Brassius, Planta | ARTAZON | Busca de Sunflora. |
| G03 | Levincia / Iono, Elétrico | LEVINCIA | Encontrar Mr. Walksabout e batalhas do evento. |
| G04 | Cascarrafa / Kofu, Água | CASCARRAFA | Devolver a carteira e participar do leilão em Porto Marinada. |
| G05 | Medali / Larry, Normal | MEDALI | Identificar o pedido secreto do restaurante. |
| G06 | Montenevera / Ryme, Fantasma | MONTENEVERA | Abertura de show e batalhas em duplas. |
| G07 | Alfornada / Tulip, Psíquico | ALFORNADA | Exercício de ritmo/emoção e combates da prova. |
| G08 | Glaseado Gym / Grusha, Gelo | GLASEADO | Descida na neve em montaria; local próprio, fora de Montenevera. |

Oito vitórias válidas concedem oito insígnias locais; a primeira de cada
ginásio pode conceder uma esmeralda, conforme a política vigente do Blue.
Revanche, DLC, Titã ou insígnia da Team Star não ocupam esses slots.
Champion Assessment: ingresso/entrevista → **Rika, Poppy, Larry (Voador)
e Hassel** → **Geeta** → encerramento com **Nemona**, se adotado no
contrato de entrega. Larry no ginásio usa Normal; sua luta na Elite
não é outra insígnia. Oito chaves locais liberam uso de especiais na
party de Paldea, não são sinônimo de título, fim da história, ou captura.
Gatilho pós-Liga do Blue precisa da auditoria: o plano multirregional
cita Galar e Decades para conclusão em Paldea, mas há
[contrato de viagem por NPC](VIAGEM_REGIONAL_LIVRE_NPC.md) a reconciliar
com o runtime; não criar uma segunda política de viagem.
[Referência da ordem da campanha](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Scarlet_and_Violet).

## Path of Legends — mobilidade local, não HMs

| Chave | Titã / setor | Evento do catálogo → função |
|---|---|---|
| L01 | Stony Cliff, Klawf, P03 | STONY_CLIFF → DASH (corrida). |
| L02 | Open Sky, Bombirdier, P07 | OPEN_SKY → SURF (nado da montaria, não HM). |
| L03 | Lurking Steel, Orthworm, P12 | LURKING_STEEL → HIGH_JUMP (salto alto). |
| L04 | Quaking Earth, Great Tusk em Scarlet / Iron Treads em Violet, Asado Desert | QUAKING_EARTH → GLIDE (planar, não voo livre). |
| L05 | False Dragon, desfecho Dondozo e Tatsugiri, Casseroya Lake | FALSE_DRAGON → CLIMB (escalada). |

Atribuir poder após a etapa correspondente com Arven/Herba Mystica,
não só ao avistar o Titã. Voltar ao farol de Poco Path para o fechamento
com Arven depois dos cinco. Cenas e uso de **Koraidon/Miraidon como
montaria** não habilitam o uso do Pokémon como combatente em Paldea
antes do gate. A forma de batalha acionada narrativamente no clímax
precisa de teste explícito que não altere a regra da party.
[Mapeamento dos cinco Titãs](https://bulbapedia.bulbagarden.net/wiki/Titan_Pok%C3%A9mon).

## Starfall Street — bases e encerramento próprios

| Chave | Esquadrão / líder | Área |
|---|---|---|
| S01 | Segin / Giacomo, Sombrio | P07, West Province (Area One). |
| S02 | Schedar / Mela, Fogo | P10, East Province (Area One). |
| S03 | Navi / Atticus, Veneno | Tagtree Thicket, setor nomeado separado. |
| S04 | Ruchbah / Ortega, Fada | P15, North Province (Area Three). |
| S05 | Caph / Eri, Lutador | P14, North Province (Area Two). |

Preservar acesso público, portão, Star Barrage, arena do Starmobile e
saída segura como superfícies diferentes. Um equivalente local a Let's Go!
exige decisão e teste no Blue; não falsificar prova dando vitória por
entrada. Após as cinco bases, tratar Clavell e Cassiopeia/Penny na
academia como fim da história, sem novas insígnias de ginásio.
[Referência dos esquadrões](https://bulbapedia.bulbagarden.net/wiki/Team_Star).

## Pontos de convergência e pós-jogo

| Marco | Sequência e limite |
|---|---|
| Prólogo e Treasure Hunt | Cabo Poco → Poco Path e Inlet Grotto → Los Platos → Mesagoza/Academia. Inicial, encontro da montaria e apresentação das três histórias não repetem ao voltar. |
| The Way Home | Após fechar Victory Road, Path of Legends e Starfall Street, reunir Arven, Nemona e Penny em Zero Gate. Descer, visitar quatro estações, abrir Zero Lab, resolver IA Sada (Scarlet) / IA Turo (Violet), máquina do tempo e retorno. Não antecipar a descida por planar/táxi, nem duplicar o clímax por versão. |
| Pós-campanha base | Reinspeção dos oito ginásios, Academy Ace Tournament e recompensas próprias. Tera Raids e encontros especiais têm condições próprias e nunca substituem a Liga. |
| Exclusivos e Paradoxos | Fundir encontros por habitat e método quando plausível; distinguir Paradoxos do passado e futuro, professor/montaria e elementos da edição. Não dar duas recompensas para um objetivo ou misturar encontros narrativos com a tabela de campo. |

[Estações e Zero Lab](https://bulbapedia.bulbagarden.net/wiki/Area_Zero)
e [Academy Ace Tournament](https://bulbapedia.bulbagarden.net/wiki/Academy_Ace_Tournament).
Mundo aberto não significa ausência de gates de história; manter separado
encerramento de uma trilha, acesso à cratera e encerramento da base.

## DLCs — capítulos extracontinentais

A [publicadora](https://press.pokemon.com/en/The-Hidden-Treasure-of-Area-Zero-Announcement)
situa ambas as viagens fora de Paldea; são capítulos do mesmo save Blue,
não regiões iniciáveis extras. The Teal Mask inicia depois da Treasure
Hunt no original; a história principal de The Indigo Disk exige o fim do
jogo-base e a conclusão de The Teal Mask, conforme o
[lançamento oficial](https://press.pokemon.com/en-CA/The-Hidden-Treasure-of-Area-Zero-Part-2-The-Indigo-Disk-DLC-for-Pokemo).
No Blue, definir chegada, volta, gates e instalabilidade sem exigir
compra externa ou conexão ao serviço do Switch.

| Chave | Polo | Áreas, objetivos e limites |
|---|---|---|
| T01 | Mossui Town (Kitakami) | Kitakami Road, centro comunitário e casa/loja; Apple Hills, Wistful Fields, Mossfell Confluence, Fellhorn Gorge, Paradise Barrens, Kitakami Wilds, Timeless Woods e Chilling Waterhead. |
| T02 | Kitakami Hall | Reveler's Road, festa e placas da lenda; Loyalty Plaza, Oni Mountain, Oni's Maw, Dreaded Den, Infernal Pass e Crystal Pool. Preservar arcos de Ogerpon, Loyal Three, Carmine/Kieran e o encontro Bloodmoon de Perrin como missão separada. |
| B01 | Blueberry Academy | Chegada/portaria, dormitório, salas e League Club. Amarys, Crispin, Lacey, Drayton e Kieran formam a BB League, não uma repetição da Elite de Paldea. |
| B02 | Terarium | Savanna, Coastal, Canyon e Polar Biomes, Central Plaza, praças e postos, além de Chargestone Cavern. Cada bioma conserva suas bordas; BBQ/BP, Synchro e cooperação requerem equivalentes testados ou lacuna declarada. |
| Indigo Disk — retorno | Area Zero Underdepths | Acesso pelo Zero Lab em um novo arco; Terapagos e Stellar em estágio próprio. Voo temporário na prova de Amarys e voo permanente só depois do marco pertinente; não substituir GLIDE dos Titãs. |
| Epílogo | Mossui Town / Loyalty Plaza | Mochi Mayhem/Pecharunt, pós-expansão. Original também exige participação no torneio e Mythical Pecha Berry. Definir distribuição local testável e não depender de Mystery Gift do Switch. |

[Geografia de Kitakami](https://bulbapedia.bulbagarden.net/wiki/Kitakami),
[voo e serviços do Indigo Disk](https://press.pokemon.com/en-NZ/NEW-WAYS-TO-PLAY-AND-MORE-EXCITING-DETAILS-ANNOUNCED-FOR-THE-HIDDEN-TR)
e [condições do epílogo](https://bulbapedia.bulbagarden.net/wiki/Mochi_Mayhem).
Nenhum mapa, evento, save ou teste físico foi executado: NOT_RUN.
