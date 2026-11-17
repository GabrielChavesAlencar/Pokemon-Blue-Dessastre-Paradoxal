# Unova E04–E05 — auditoria REAL de Pokémon World V18 (fonte doadora)

> **Data:** 17/11/2026 · **Projeto-alvo:** Pokémon Blue: Dessastre Paradoxal · **Versão da campanha que queremos reconstruir:** Pokémon **White** (Black/White).
>
> **Estado comprovado:** os arquivos originais foram baixados e analisados em execução efêmera de GitHub Actions, diretamente pelos quickkeys MediaFire divulgados na publicação do autor; os arquivos externos **não foram adicionados ao Git, ao Game.exe ou ao instalador**. Nenhum direito de redistribuição foi presumido e nenhum conteúdo foi testado no jogo.

## 1. Resumo decisivo

O pacote é uma fonte **parcial de geometria de Unova**, **não** um jogo pronto de Unova Black/White com NPCs, diálogos, batalhas, ginásios e história configurados.

| Indicador | Resultado verificado |
|---|---:|
| Tamanho do ZIP original | **208.057.674 bytes** |
| Arquivos internos do projeto inteiro | **17.103** |
| Arquivos MapNNN.rxdata (todas as regiões) | **912** |
| Entradas em MapInfos.rxdata | **911** |
| Mapas com arquivo sob a hierarquia Unova Region | **64** |
| Mapas dessa hierarquia cujo RXDATA foi interpretado | **64/64** |
| Mapas Unova de **20×15 tiles** (dimensão padrão; possíveis placeholders) | **56/64** |
| Mapas Unova com dimensões maiores que 20×15 | **8/64** |
| Eventos RMXP (@events) somados nesses 64 mapas | **0** |
| Comandos/diálogos/transferências registrados nesses mapas | **0** |
| Áreas simbólicas com nome correspondente dentro da hierarquia Unova | **20/74** |
| Correspondências apenas em OUTROS ramos (rotas 1–18, Victory Road) | **19/74 — FALSOS POSITIVOS para Unova** |
| Áreas simbólicas sem correspondência exata de nome | **35/74** |
| Recursos classificados para auditoria de direitos (todas as regiões) | **17.076** |
| Créditos do autor | **Credits.txt de 2.425 bytes e 174 linhas** |
| Recursos liberados para redistribuição automaticamente | **0** |

**O que significa o total zero de eventos:** cada uma das 64 estruturas do ramo Unova foi interpretada como objeto RPG::Map e retornou um dicionário de eventos vazio. É uma descoberta de dados real, não uma inferência por falta de arquivo. Portanto não há NPCs ou páginas de evento RMXP **nesses mapas** para importar. Não concluir que não existem dados ou scripts de eventos em qualquer outro local do ZIP: fora desse ramo, um mapa antigo (Map008) teve incompatibilidade com o parser global; outros mecanismos teriam de ser auditados individualmente.

## 2. Origem e hashes

| Recurso | Proveniência | Hash SHA-256 observado |
|---|---|---|
| Pokémon World V18 ZIP | [Publicação do autor](https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/); [MediaFire informado pelo autor](https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file) | ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35 |
| Credits.txt | [MediaFire de créditos](https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file) | 42433e84a3bb8d462ce86d7a7245a23fefe7602ba707f3ea6139aefe4aff5240 |
| MapInfos.rxdata interno | ZIP acima | a5de4d870ae08aa3730942496734c7a0917505a6d435ff178ce5a10f73fc6495 |

O arquivo foi nomeado **Pokemon World V18.zip** no provedor, enquanto sua pasta de projeto interna é **pokemon journeys v18**. A origem foi vinculada ao link publicado pelo autor e à chave do arquivo no provedor; **não foi encontrado um hash independente assinado pelo autor**. O download foi efêmero e descartado após os relatórios.

A execução [Unova E04/E05 — GitHub Actions run 44083797886](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44083797886) produziu um artefato temporário **unova-e04-metadata-only** com os índices completos (MapInfos, eventos, inventário de direitos e hashes). **Não contém sprites, músicas, mapas binários nem o ZIP original.** O artefato da execução tem retenção prevista de sete dias; este documento e o [registro JSON versionado](../data/regions/unova-e04-e05-observed-source.json) são a referência durável.

## 3. Geometria candidata: nomes exatos encontrados dentro de Unova Region

Os números abaixo são **MapIDs SOMENTE DO FANGAME DOADOR**, não MapIDs disponíveis nem instalados no Decades.

| Área com nome reconhecível | MapID original |
|---|---:|
| Nuvema Town | 463 |
| Accumula Town | 464 |
| Striaton City | 465 |
| Nacrene City | 466 |
| Castelia City | 468 |
| Nimbasa City | 469 |
| Driftveil City | 471 |
| Mistralton City | 472 |
| Icirrus City | 473 |
| Opelucid City | 474 |
| Anville Town | 470 |
| Undella Town | 477 |
| Wellspring Cave | 522 |
| Pinwheel Forest | 908 |
| Desert Resort | 907 |
| Relic Castle | 527 |
| Chargestone Cave | 523 |
| Dragonspiral Tower | 529 |
| Giant Chasm | 531 |
| Challenger's Cave | 530 |

**20/74 são apenas nomes correspondentes dentro do ramo Unova.** A geometria visual, colisão, ligações e direitos ainda exigem revisão individual. Sem essa verificação, nem mesmo um mapa com o mesmo nome é considerado apto para instalação.

### 3.1 Outros grupos do ramo Unova

A árvore contém IDs de origem para grupos como **Unova Region (32)**, **Unova Interiors (461)**, **Unova Route Connections (462)**, **UNOVA Gyms (486)**, Poké Centers, Pokémarts e Labs. Esses grupos são MapInfos, não prova de oito ginásios funcionais ou interiores com NPCs.

O projeto utiliza **Route 301–323** dentro da árvore Unova, não Route 1–18 da campanha oficial Black/White. Esses números não podem ser convertidos automaticamente 301→1 etc. sem estudar geometria, sequência, portas e o detonado.

### 3.2 Auditoria de dimensões: a maior parte pode ser placeholder

A leitura real da geometria estrutural revelou **56 dos 64 mapas com 20×15 tiles**. Esse é um tamanho padrão que pode corresponder a um mapa inicial/vazio ou a um interior pequeno — **não é evidência suficiente para afirmar que estão vazios**. Todos esses 56 também têm zero eventos RMXP.

Somente **8 mapas** possuem dimensões maiores que 20×15:

| MapID original | Mapa na fonte | Dimensões em tiles |
|---:|---|---:|
| 463 | Nuvema Town | 67×44 |
| 464 | Accumula Town | 77×41 |
| 465 | Striaton City | 109×64 |
| 466 | Nacrene City | 100×82 |
| 468 | Castelia City | 150×200 |
| 490 | Route 301 | 67×60 |
| 494 | Route 302 | 73×28 |
| 495 | Route 303 | 64×72 |

O [atlas completo versionado](../data/regions/unova-e05-source-map-atlas.json) contém os 64 IDs de origem, nomes, relação com o pai, dimensões, ausência de eventos e flags impedindo importação. Esse atlas não transporta arquivos de terceiros.

**Consequência prática:** o Pokémon World V18 parece aproveitável sobretudo como referência geográfica das **primeiras cinco cidades e três rotas**, ainda sujeitas a inspecionar os dados de tiles, prioridades, colisões, sprites e licenças. Para Nimbasa em diante, os mapas de 20×15 e nomes vazios de eventos indicam alto esforço de reconstrução. Não devemos anunciar “64 mapas completos” nem escolher um MapID de destino antecipadamente.

### 3.3 Armadilhas de interpretação

A busca global por nome encontrou **Route 1–18** com IDs originais **34–51** e três mapas chamados **Victory Road** nos IDs **335, 383 e 626**; nenhum desses 19 conjuntos pertence à hierarquia Unova identificada no arquivo. Portanto são correspondências perigosas e **não devem ser importadas** como Unova.

Além disso, não surgiram correspondências exatas para áreas importantes como **White Forest, N's Castle, a Elite Four individual, diversos ginásios, Dreamyard, Celestial Tower e Tubeline Bridge**. Ausência de nome exato não prova ausência de algum cenário reaproveitável, mas proíbe afirmar que a área está presente/funcional.

O doador mistura cenários **Black/White**, **Black 2/White 2** e referências ao **anime**, incluindo Aspertia City, Floccesy Town, Virbank City, Reversal Mountain, Black City e Vertress Conference. A campanha alvo do Dessastre continua sendo Pokémon **White B/W**, com N, Ghetsis e Iris no oitavo ginásio; não aproveitar uma rota de anime/BW2 como história Black/White.

## 4. Eventos, NPCs, treinadores e áudio

- **Mapas Unova:** 64/64 mapas inspecionados e **0 eventos RMXP**. Isso não fornece NPCs, placas, objetos do chão, treinadores, warps por evento, cutscenes, ginásios com ações nem flags de história.
- **Treinadores da campanha:** não foi demonstrada existência de equipes, páginas de combate ou configurações de trainers aplicáveis à White; reconstruir contra detonado e fontes de dados verificáveis.
- **Pokémon selvagens:** qualquer arquivo PBS doador depende de análise de variante, método e localização; não inventar slots, porcentagens ou MapIDs.
- **Música:** o ZIP possui **85 arquivos Audio/BGM/BGS** e outros **903 Audio/ME/SE** somando todas as regiões. É necessário verificar autoria e permissão por faixa; não empacotar OST oficial apenas porque consta de um fangame.
- **Créditos:** o inventário identificou **17.076 recursos classificáveis**; o Credits.txt contém 174 linhas, mas essa contagem não autoriza o uso de nenhum item. E06 permanece bloqueada até revisão dos direitos por arquivo.

## 5. Conclusão de engenharia

1. **Fonte de geometria candidata:** podemos estudar desenhos das cidades, cavernas e áreas existentes, somente depois de verificar direitos e compatibilidade do tileset.
2. **Fonte de NPCs/eventos:** **não serve como doador pronto de Unova**; os 64 mapas do ramo não têm eventos RMXP.
3. **Fonte de música:** **não aprovada para redistribuição**. Usar catálogo BlueMusic e fontes autorizadas/fallbacks.
4. **Versão de Essentials:** o doador é um projeto antigo v18. No Dessastre (Essentials v21.1), reconstruir lógica diretamente no motor existente e nunca sobrescrever scripts, MapInfos, save flags ou PBS globais.
5. **ID original não é ID novo:** a próxima etapa antes de qualquer importação é auditar a instalação real e as reservas Kanto/Johto/Hoenn/Sinnoh, depois gerar overlay em QA privado.
6. **A história de Black/White deve ser construída:** Nuvema → oito ginásios → Elite Four → castelo de N → Ghetsis → pós-jogo, com flags regionais, HM/itens exclusivos, save/blackout, viagens por NPC e balanceamento do Blue.

## 6. Barra E — resultado da etapa

| Marco | Status |
|---|---|
| E01 — pesquisa das fontes | **Concluído** |
| E02 — plano de 32 fases | **Concluído** |
| E03 — catálogo simbólico e testes | **Concluído** |
| E04 — ZIP/credits reais, hashes e inventário | **Concluído como pesquisa de fonte** |
| E05 — estrutura, nomes e eventos reais do ramo Unova cruzados | **Concluído como auditoria de fonte** |
| E06 — direitos por recurso | **Pendente** |
| E07 — catálogo musical/treinadores simbólico | **Concluído como documentação** |
| E08 — testes reais Windows Game.exe e Android JoiPlay | **Pendente** |

**Barra E: 6/8 (75%).** Barras A/B/C/D jogáveis: **0/8**. Fases U01–U32 jogáveis: **0/32**.

Esses 75% significam avanço documental, **não** 75% de Unova instalada. A fonte e os eventos foram inventariados; nenhum mapa da região passou por conversão, autorização de distribuição ou teste nativo.

## 7. Testes e próximos gates

**Concluído:** 17 testes do cliente remoto, 12 de MapInfos, 10 de eventos com tolerância isolada, além das suites pré-existentes. As leituras remotas ocorreram apenas em runner descartável; nenhum script do doador foi executado.

**Próxima implementação útil:** E06 — revisar direitos/licenças por item e produzir uma lista explícita de assets permitidos/substituíveis. Para a Barra A, iniciar U04 em instalação real e U05 com **um mapa-piloto** em QA isolado após direitos. E08 só será aprovado quando a campanha e o fluxo de viagem funcionarem em Game.exe/JoiPlay de verdade.
