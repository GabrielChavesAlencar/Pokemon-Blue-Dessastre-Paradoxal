# GD01 — fontes, direitos e decisão de desenho para Galar

Pesquisa pública em 28/11/2026. **Há mapas nativos de RPG Maker XP
candidatos, mas nenhum mapa de Galar foi aprovado para importar.** Uma
região jogável em um fangame não comprova fidelidade a Sword/Shield,
compatibilidade com o Blue ou permissão por arquivo. Nenhum jogo, plugin
ou script de terceiros foi executado e nenhum asset foi incorporado.

| ID | Fonte primária | Evidência e limite | Decisão |
|---|---|---|---|
| CANON_SWSH | [Pokémon Sword](https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Pokemon-Sword-1522111.html), [Pokémon Shield](https://www.nintendo.com/en-gb/Games/Nintendo-Switch-games/Pokemon-Shield-1522110.html), [exclusividades](https://swordshield.pokemon.com/en-us/gameplay/version-exclusives/) e [guia visual de Galar](https://assets.pokemon.com/assets/cms2/pdf/video-game/sword-shield/Galar_Tour_Brochure_US.pdf) | Base para a divisão entre rotas construídas, cidades, estádios, Wild Area e variações entre versões. O guia de inspirações visuais não é uma planta de jogo. | `REFERENCIA_APENAS`. Não extrair arquivos da versão de Switch, nem incorporar imagens, malhas, textos ou áudio. |
| CANON_DLC | [Isle of Armor](https://www.nintendo.com/en-gb/DLC/The-Isle-of-Armor-1705980.html), [Crown Tundra](https://www.nintendo.com/en-gb/DLC/The-Crown-Tundra-1705996.html) e [acesso às expansões no original](https://www.nintendo.com/en-gb/Support/Purchases-Subscriptions/Games/Pokemon-Sword-or-Pokemon-Shield-Expansion-Pass-DLC-Is-Not-Appearing-1833572.html) | A ilha do dojo de Mustard tem praia, brejo, mata e cavernas; a tundra inclui expedição, Calyrex e tocas. No original, Wedgehurst Station, Wild Area e o evento do Slowpoke fazem parte do acesso; entrada não equivale a completar a expansão. | `REFERENCIA_APENAS`. Registrar gates do Blue separadamente, sem copiar o sistema de licenças do Switch ou presumir que visitar abre toda a campanha DLC. |
| FIRE_ASH | [Luc-ker: Fire Ash 3.7.1](https://www.eeveeexpo.com/threads/9489/) e [árvore pública em revisão fixa](https://github.com/Luc-ker/fire-ash-public/tree/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4) | RPG Maker XP / Essentials 19.1, reconta a jornada do anime. O índice e quatro arquivos nativos de Galar foram confirmados abaixo. A publicação descreve Masters 8 e inclui menções a Safari Zone Galar: não tratar isso como sequência original do Switch. Não provar a cobertura inteira pelo nome de um mapa. | `BLOQUEADO_IMPORTACAO`. Sem autorização específica demonstrada e sem prova de fidelidade, compatibilidade, tiles, eventos ou colisões no Blue. |
| ROYAL | [Página de Pokémon Royal por Skyflyer](https://skyfangames.blogspot.com/2024/01/pokemon-royal.html), [FAQ do autor](https://skyfangames.blogspot.com/p/faq.html) e [trailer oficial do Demo 2](https://www.youtube.com/watch?v=mZ_QmteVsQQ) | Releitura 2D da campanha com rotas e personagens modificados. A página consultada oferece Demo 1 v0.1.14, cujo FAQ limita a progressão até o terceiro ginásio; o autor publicou trailer separado do Demo 2. Isso não prova conteúdo interno, cobertura do Demo 2 ou formato de seus mapas. | `BLOQUEADO_IMPORTACAO`. Candidato visual, sem inventário técnico. Permissão de gravar conteúdo de canal no FAQ não é licença para reutilizar os mapas ou a arte. |
| UFF | [UFF: anúncio de Pokémon Espada y Escudo Essentials Beta 2.0](https://www.youtube.com/watch?v=F1JBzVCYmb4) e [trailer do autor](https://www.youtube.com/watch?v=PXDWsM-li_A) | Há registros públicos de uma adaptação Essentials com beta rotulada 2.0 em 2022. Não se validaram os binários, a versão do motor, a lista de `.rxdata`, a cobertura das rotas ou os termos. | `BLOQUEADO_IMPORTACAO`. Pista de pesquisa, não doador confirmado. |
| WORLD | [The Pokémon World Project por SocomSeal](https://eeveeexpo.com/resources/1877/) e [repositório](https://github.com/SocomSeal/The-PMon-World-Project) | Na publicação observada, v2.3.0 orientada a Essentials 22, Galar está em 0%. O autor só garante 21.1 para Kanto e Hoenn. | `REFERENCIA_APENAS` para estrutura, não fonte de mapas de Galar. |
| DEMAKES | [Sword and Shield Ultimate Plus GBA, publicação do mantenedor](https://www.pokecommunity.com/threads/sword-and-shield-ultimate-plus-gba-english-version-complete-1-2-1-2.526384/) | Demake em FireRed para GBA. Uma versão visualmente próxima não torna o mapa nativo de RPG Maker XP ou autorizado. | `FORA_DA_BASE_TECNICA`. Não extrair nem importar ROM, patch, tiles ou áudio. |

## Amostra técnica: Fire Ash

Na [revisão pública 078d412…](https://api.github.com/repos/Luc-ker/fire-ash-public/git/trees/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4?recursive=1),
o [MapInfos.rxdata](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/MapInfos.rxdata)
(56.722 bytes, SHA-256
`96d3ad8327fc27f2e0c00ff33ce845404475b921767043d731c05a74aed0bbe9`)
foi lido em memória por parser inerte, sem carregar o jogo. O índice
inclui Hammerlocke, Stow-on-Side, Ballonlea, Wyndon, Slumbering Weald,
Split-Decision Ruins e seis entradas rotuladas Wild Area. Há inclusive
Wyndon e Wyndon Stadium alternativos em uma raiz separada, um motivo
para não adivinhar a cobertura ou equivalência por nome.

Quatro arquivos dessa mesma revisão contêm objetos `RPG::Map` com as
seguintes dimensões, lidas por parser inerte:

| Área no índice | Arquivo nativo da amostra | Dimensões | Bytes | SHA-256 |
|---|---|---|---:|---|
| Spikemuth | [Map977.rxdata](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map977.rxdata) | 90 × 30 tiles | 28.949 | `ed9d4ef2d55543042333a4e4a91619e80e73a538ec21eeec0187113ffa4bd17b` |
| Freezington | [Map981.rxdata](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map981.rxdata) | 50 × 36 tiles | 33.198 | `76668a8ee40f25904e784d4271db309ff140f089cb5848eba7e1ac4383254d0f` |
| Crown Tundra | [Map983.rxdata](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map983.rxdata) | 70 × 50 tiles | 46.570 | `01b479875d6fc871867eecfe16c8f540553692ffa4537a8ca65062f5dc4c12d7` |
| Wedgehurst | [Map985.rxdata](https://github.com/Luc-ker/fire-ash-public/blob/078d41222a30fafeee7cc0a65b7a11bd2f19b2f4/Data/Map985.rxdata) | 50 × 45 tiles | 29.177 | `9a23089c54496a9cdddb44b29253b5bedf742e35b22a4aac17dc9d5a10a152f3` |

Esses números são IDs do doador, não MapIDs do Blue. Os hashes identificam
somente os bytes lidos. A revisão pública não foi equiparada à distribuição
3.7.1 no tópico. A amostra não comprova setores internos, grade de eventos,
entradas e saídas, passabilidade, direitos, equivalência do jogo oficial
ou suporte no runtime. O rótulo Crown Tundra comprova um mapa, **não uma
expansão inteira**; não foi encontrada prova equivalente de cobertura da
Isle of Armor.

## Critério por mapa: importar só com prova; caso contrário, refazer

1. Registrar a revisão, a página original, autor e dependências, o arquivo
   editável, tamanho e SHA-256, as permissões por componente (inspecionar,
   adaptar, distribuir), a atribuição e o responsável pela revisão.
   Página pública e créditos não equivalem a licença. Marcar o que não foi
   confirmado como `NAO_VERIFICADO`.
2. Em futura fase autorizada, confirmar cobertura e fidelidade ao original
   por entrada e saída; verificar camadas, tiles/autotiles, deslocamento,
   escala, colisão, eventos, switches e transições em staging isolado.
   RPG Maker XP em comum não garante funcionamento entre versões. Não
   substituir tilesets, engine, saves, CommonEvents, PBS ou índices
   globais pelo doador. Não executar o projeto de terceiros como atalho.
3. Sem mapa aprovado, **refazer do zero em 2D com os tilesets e autotiles
   de Kanto já usados no Blue**. Cruzar vistas de Sword/Shield, mapa
   regional e gravações de percurso. Preservar o desenho reconhecível:
   bordas, direção de acesso, retornos, marcos, desníveis e conexões entre
   setores. Para Wild Area e expansões, juntar setores 2D legíveis e
   testar as fronteiras em vez de comprimir a área em um mapa genérico.
   Registrar aproximações quando não existir um tile equivalente. Não
   mudar os mapas nem os tilesets globais de Kanto.
4. Manter no projeto uma só Galar de Sword/Shield, com diferenças por
   evento/versão (como Bea/Allister e Gordie/Melony), e expansões como
   capítulos próprios; nenhuma versão ou DLC duplica insígnia. Seguir o
   [contrato multirregional](PLANO_REGIOES_DESSASTRE_V2.md), não sistemas
   de um doador: não inventar Elite Four ou HMs, e separar mobilidade,
   história e conteúdo opcional.
5. A receita futura só poderia obter entrada externa aprovada, fixada e
   permitida diretamente na origem. Não republicar material de terceiros,
   cache, ROM ou ZIP misto. Este documento não autoriza implementação,
   contato externo, publicação ou mudança do estado `planned`.
