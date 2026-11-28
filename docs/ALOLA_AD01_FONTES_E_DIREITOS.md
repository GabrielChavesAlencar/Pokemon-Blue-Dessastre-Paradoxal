# AD01 — fontes, direitos e escolha de versão para Alola

Pesquisa pública de 28/11/2026. **Há mapas nativos candidatos**, mas nenhum
mapa ou pacote de Alola foi homologado para o Blue. Ler o índice de um
doador não prova que o cenário de USUM está pronto para importar. Não foram
executados o jogo, plugins ou scripts de terceiros. Nenhum arquivo de
doador, ROM, ZIP, tile ou imagem foi incorporado à documentação ou ao jogo.

## Referências e candidatos

| ID | Fonte primária | O que a evidência permite afirmar | Decisão |
|---|---|---|---|
| CANON_SM | [Nintendo: Sun](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-Sun-1092368.html), [Moon](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-Moon-1092369.html), [provas e Z-Moves](https://www.nintendo.com/en-gb/News/2016/August/Z-Moves-and-undiscovered-Pokemon-announced-for-Pokemon-Sun-and-Pokemon-Moon-1128345.html) | Quatro ilhas naturais e Aether Paradise, provas, Totens, grandes provas dos kahunas, Poké Ride e diferenças de versão. | REFERENCIA_APENAS; variante de história e geografia, não fonte de arquivos RPG Maker. |
| CANON_USUM | [Nintendo: Ultra Sun](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-Ultra-Sun-1231949.html), [Ultra Moon](https://www.nintendo.com/en-gb/Games/Nintendo-3DS-games/Pokemon-Ultra-Moon-1231705.html), [The Pokémon Company: diferenças das provas e transporte](https://press.pokemon.com/en/NEW-DETAILS-REVEALED-FOR-POKEMON-ULTRA-SUN-AND-POKEMON-ULTRA-MOO-30650), [Nintendo: Ultra Megalopolis](https://www.nintendo.com/au/games/nintendo-3ds/pokemon-ultra-sun/) | Trama alternativa com Necrozma, provas alteradas (incluindo a nova prova de Mina), Mantine Surf, Ultra Wormholes e Ultra Megalopolis. | Base narrativa do planejamento atual, REFERENCIA_APENAS para construção. |
| FIRE_ASH | [Publicação do mantenedor](https://www.eeveeexpo.com/threads/9489/), [arquivos públicos de Luc-ker](https://github.com/Luc-ker/fire-ash-public/tree/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4) | RPG Maker XP / Essentials 19.1, releitura do anime no visual de FireRed/LeafGreen. A revisão pública contém mapas nativos com locais reconhecíveis de Alola, conforme amostra abaixo. | BLOQUEADO_IMPORTACAO. O acesso público é para RPGPlayer; o README trata de contribuição ao próprio Fire Ash. Não localizei licença de reutilização por componente e não comparei a cobertura integral de SM/USUM. |
| GOLDEN_CROWN | [Pokémon Golden Crown, publicação de NicolayBlack](https://www.eeveeexpo.com/threads/4419/) | Descreve a sua Alola jogável em Essentials 19.1, mas como região reconstruída numa campanha própria, com a Liga em Hakka Island. O tópico mostra a versão do projeto como 1.0.9 e lista download v1.0.10; nenhum arquivo dessas versões foi inspecionado. | BLOQUEADO_IMPORTACAO; não é evidência de planta fiel ao USUM nem de arquivos editáveis com licença. |
| WORLD | [The Pokémon World Project 2.0.0, SocomSeal](https://www.eeveeexpo.com/resources/1877/), [repositório](https://github.com/SocomSeal/The-PMon-World-Project) | O quadro público do autor declara Essentials 21.1 e Alola em 0% nessa versão; sem cobertura documentada para usar. | REFERENCIA_APENAS de estrutura, não fornecedor de mapas de Alola. |
| KINGTAPIR | [KingTapir Tilesets v1.0, compilação de NocTurn](https://eeveeexpo.com/resources/636/) | O compilador indica permissão de KingTapir para a compilação e oferece conjuntos de tiles, incluindo Aether Paradise e peças avulsas de Alola. A publicação identifica peças de outra autoria, incluindo a mansão atualizada de Lusamine. | Tiles avulsos, não mapas. REFERENCIA_APENAS neste escopo; confirmar autoria, versão e termos por peça antes de qualquer exceção ao acervo de Kanto. |
| DEMAKES | [Ultra Eclipse por Phaneropterinae](https://www.reddit.com/r/PokemonROMhacks/comments/1qsx596/ultra_eclipse_demake_of_the_pokeride_system/), [Alolan Seaglass por Nemo](https://www.reddit.com/r/PokemonROMhacks/comments/1tn9tgb/pok%C3%A9mon_alolan_seaglass_dev_01_it_exists/) | Anúncios dos próprios autores: Ultra Eclipse usa pokeemerald-expansion; Alolan Seaglass é apresentado como ROM hack. | FORA_DA_BASE_TECNICA. Demonstração 2D não equivale a mapa RPG Maker XP. Não extrair ROM, patch, tiles ou script. |
| HOMONIMOS | [Pokémon External Demo](https://mail.eeveeexpo.com/threads/8273/), [Pokémon Ultra Alchemy](https://www.eeveeexpo.com/threads/9865/) | External usa uma história própria após USUM; Ultra Alchemy usa Essentials v21.1 mas situa-se em Pelli, região original. | Não são fornecedores confirmados do mapa de Alola. |

### Amostra nativa: Fire Ash

A [árvore Git pública](https://api.github.com/repos/Luc-ker/fire-ash-public/git/trees/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4?recursive=1)
tinha 996 arquivos `Data/Map*.rxdata` numerados no projeto inteiro, **não**
996 mapas de Alola. O [MapInfos.rxdata dessa revisão](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/MapInfos.rxdata)
(56.722 bytes, blob Git `1622efe230a813229eb89b9d53b4bf463161b587`,
SHA-256 `96d3ad8327fc27f2e0c00ff33ce845404475b921767043d731c05a74aed0bbe9`)
foi lido em memória com leitor inerte, sem executar código do doador.
Exemplos indexados: Hau'oli City (894), Iki Town (902), Verdant Cavern
(905), Paniola Town (906), Vast Poni Canyon (921), Malie City (953) e
Alola Pokemon League (958). Os números são do doador, **não são MapIDs
alocados para o Blue**. A leitura inerte confirmou também a classe
`RPG::Map` e as dimensões de três arquivos físicos na mesma revisão:
[Route 1](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map889.rxdata)
(80 × 80 tiles), [Hau'oli](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map894.rxdata)
(69 × 64) e [Iki](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map902.rxdata)
(44 × 50). O índice põe a Liga sob Manalo Stadium, um sinal claro para
não usar a progressão, conexões ou Liga desse projeto como o padrão de
USUM. O SHA comprova somente o índice observado, não uma licença nem
que essa revisão pública corresponda ao lançamento 3.7.1. A amostra não
valida a topologia, eventos, tiles, edições no motor do Blue ou execução.

## Qual versão orienta o desenho e a história?

- **Espinha dorsal:** uma Alola de Ultra Sun + Ultra Moon, conforme
  [o plano multirregional](PLANO_REGIOES_DESSASTRE_V2.md) e
  [o catálogo do Blue](../site/public/data/regions.json). Uma só campanha
  com as quatro ilhas naturais e a ilha artificial; não duplicar mapas
  para uma diferença de elenco, encontro, horário ou diálogo.
- **Sun/Moon como referência identificada:** conservar alternativas
  em fichas, separadas da rota obrigatória. Se uma captura de tela divergir
  da planta de USUM, etiquetar a edição, horário e estado da campanha.
  Não importar a sequência de SM, o capítulo de outro fangame ou a história
  do anime como se fosse a progressão principal.
- **Diferenças que afetam o mapa e os testes:** Mina, pontos de Mantine Surf,
  Ultra Megalopolis, novos setores e estados de Necrozma são entradas
  distintas a conferir. O modo de transporte entre ilhas, o Poké Ride
  de obstáculos e a viagem entre regiões do Blue são regras diferentes.
  Quatro grandes provas dos kahunas não duplicam as oito conquistas
  oficiais da campanha USUM. Conteúdo de versão e pós-jogo só entra na
  rota principal se o plano do Blue o determinar expressamente.

## Decisão por mapa

1. Se aparecer um mapa RPG Maker XP pronto ou quase pronto, registrar
   autor/titular, página original, a revisão, cada arquivo e seu tamanho
   e SHA-256, permissões de inspecionar, adaptar e distribuir separadas,
   atribuição e dependências com seus próprios termos. Download
   público, créditos ou acesso ao GitHub não substituem autorização.
   Nada de reutilização enquanto a situação for `NAO_VERIFICADO`.
2. Em futura fase autorizada, comparar o mapa às vistas de USUM: desenho
   geral, marcos, ordem, chegadas e saídas, desníveis, portas e andares.
   Auditar `RPG::Map`, três camadas, tiles/autotiles e passabilidade,
   eventos, scripts, transfers, IDs, switches, objetos e colisões em
   staging isolado. Mesmo formato RPG Maker XP ou nome igual não basta; não
   substituir índices, tilesets, PBS, engine, saves ou eventos globais
   pelo conjunto de outro projeto.
3. Se não for aprovado ou faltar, **refazer do zero em 2D com os tiles e
   autotiles de Kanto já usados no Blue**, sem esperar pacote regional.
   Cruza-se mapa regional, captura local e gravação de percurso dos dois
   sentidos, não a estética do doador. Preservar forma reconhecível,
   conexões e pontos de referência com o acervo atual, sem copiar pixels,
   modelos, textos ou áudio de referência. Registrar a diferença se não
   houver equivalente direto no acervo. O mapa de Kanto e seus tilesets
   globais não são alterados.
4. A atualização futura pode baixar na origem somente uma entrada
   aprovada e fixada, se os termos permitirem essa forma de obtenção.
   Não republicar ROM, arquivo original de terceiros, dados extraídos
   ou ZIP misto. Este estudo não executa ou induz contato externo, não
   dá licença e não muda o estado `planned`.
