# KD05 — atlas visual de Kalos X/Y e reconstrução com tiles de Kanto

A regra vale por mapa, não por região inteira. Procurar primeiro um mapa
pronto ou quase pronto em **RPG Maker XP / Pokémon Essentials**. Só planejar
reaproveitamento após validar o arquivo editável, a fidelidade ao local de
X/Y, o encaixe com os tiles e o motor do Blue e a permissão por componente
([KD01](KALOS_KD01_FONTES_E_DIREITOS.md)). Até esta revisão, nenhum mapa de
Kalos passou nesses critérios. Se não passar, **refazer do zero em 2D com os
tilesets e autotiles de Kanto já usados pelo Blue**. O formato do mapa é de
Kalos; a linguagem visual é de Kanto. É também o padrão para mapas faltantes
de Galar, Alola e Paldea, sem ampliar o escopo desta entrega.

## Como usar as referências

- **Imagem local**: vista ou composição do cenário em X/Y, para ler o traçado,
  as bordas e os marcos. **Mapa regional**: local destacado no mapa de X/Y;
  ajuda a localizar vizinhos, mas não mostra por onde se anda. Ambos apontam
  para páginas do [Bulbagarden Archives](https://archives.bulbagarden.net/wiki/Category:Kalos_maps).
- **Percurso**: cruzar as vistas com [gameplay de Pokémon Y](https://www.youtube.com/watch?v=QQedARjQKlM),
  [capturas em sequência do guia francês](https://www.pokemon-france.com/en/guides/pokemon-x-and-y/),
  [mapa interativo do Pokékalos](https://www.pokekalos.fr/jeux/3ds/xy/map/) e
  [índice fotográfico do Pokéarth](https://www.serebii.net/pokearth/kalos/).
  A [brochura oficial](https://www.nintendo.com/eu/media/downloads/games_8/3ds_pokemonxandy_1/PokemonXandY_Brochure_ptPT.pdf)
  é referência regional e de ambientação, não uma planta. A gravação serve
  para confirmar percurso; a listagem não afirma que todos os trechos foram
  assistidos nem que todos os interiores têm vistas completas.
- Antes de desenhar, procurar o maior número de **vistas complementares**
  úteis, não duplicatas: panorama, chegada e saída nos dois sentidos,
  bifurcações, desníveis, acessos e interiores relevantes, e versões
  antes/depois de eventos que mudam o acesso. Anotar URL, minuto ou
  imagem/andar, o que ela prova e o que falta conferir; uma foto isolada
  não comprova colisão nem passagem.
- Estes links servem para observação. Não baixar pacotes, copiar pixels,
  malhas, áudio ou scripts, nem incorporar capturas no repositório.
  Não usar anime, Legends: Z-A ou outro fangame para completar uma lacuna
  de X/Y como se fosse evidência canônica. Registrar a lacuna antes de
  tomar uma decisão autoral.

## Cidades e vilas — 16

As opções de tiles abaixo são funções visuais a buscar no acervo já usado
por Kanto, não nomes de arquivos ou garantia de que existe uma peça idêntica.

| Chave | Cidade/vila | Referências visuais | Preservar em 2D | Buscar nos tiles de Kanto |
|---|---|---|---|---|
| C01 | Vaniville Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Vaniville_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Vaniville_Town_Map.png) | Vizinhança, casa/quarto, curva de saída para R01. | casa, cercas, flores e caminho de terra |
| C02 | Aquacorde Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Aquacorde_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Aquacorde_Town_Map.png) | Praça, fonte, edifícios nas bordas e acessos R01/R02. | piso de praça, fonte, fachadas e degraus |
| C03 | Santalune City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Santalune_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Santalune_City_Map.png) | Centro, praça, ginásio e saídas R03/R04/R22. | fachada de ginásio, jardim, portas e rua |
| C04 | Lumiose City | [sul](https://archives.bulbagarden.net/wiki/File:Lumiose_City_South_Boulevard_XY.png), [norte](https://archives.bulbagarden.net/wiki/File:Lumiose_City_North_Boulevard_XY.png), [centro](https://archives.bulbagarden.net/wiki/File:Lumiose_City_middle_XY.png), [praça central](https://archives.bulbagarden.net/wiki/File:Lumiose_City_Centrico_Plaza_XY.png), [distritos e setores](https://archives.bulbagarden.net/wiki/Category:Lumiose_City_maps), [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Lumiose_City_Map.png) | Traçado radial, avenidas norte/sul, praças, Prism Tower e estação. | pavimento urbano, fachadas, praças e marco central |
| C05 | Camphrier Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Camphrier_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Camphrier_Town_Map.png) | Castelo, praça, acessos R05/R07. | alvenaria, muro, pátio e trilha |
| C06 | Ambrette Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Ambrette_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Ambrette_Town_Map.png) | Falésia, Fossil Lab, aquário e caminhos R08/R09. | desnível costeiro, escada e edifícios de serviço |
| C07 | Cyllage City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Cyllage_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Cyllage_City_Map.png) | Costa, pista de bicicleta, entrada do ginásio e acessos. | piso costeiro, rampa, praia e rocha |
| C08 | Geosenge Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Geosenge_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Geosenge_Town_Map.png) | Praça e monumentos de pedra, saídas R10/R11 e setor Flare. | rochas verticais, caminho e bordas rochosas |
| C09 | Shalour City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Shalour_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Shalour_City_Map.png) | Praia, ginásio, Tower of Mastery e saída R12. | água, areia, acesso à torre e portões |
| C10 | Coumarine City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Coumarine_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Coumarine_City_Map.png) | Marina e parte alta conectadas por monotrilho, ginásio. | cais, água, desnível e duas estações |
| C11 | Laverre City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Laverre_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Laverre_City_Map.png) | Árvore do ginásio, caminhos entre casas e ramal da Factory. | árvore destacada, trilhas e fachadas |
| C12 | Dendemille Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Dendemille_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Dendemille_Town_Map.png) | Moinho, acessos R15/R17 e Frost Cavern. | caminho, fachada de moinho e transição de terreno |
| C13 | Anistar City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Anistar_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Anistar_City_Map.png) | Sundial à beira da água, ginásio e acesso R18. | piso de praça, água e marco do relógio solar |
| C14 | Couriway Town | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Couriway_Town_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Couriway_Town_Map.png) | Cachoeira, estação e sequência de acessos R18/R19. | queda d’água, plataforma e escadas |
| C15 | Snowbelle City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Snowbelle_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Snowbelle_City_Map.png) | Neve, ginásio, R19/R20/R21 e retorno da floresta. | piso claro, rochas, árvores e fachadas |
| C16 | Kiloude City | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kiloude_City_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Kiloude_City_Map.png) | Chegada de trem, Battle Maison e Friend Safari. | estação, praça e portas dos dois serviços |

## Rotas de Kalos — 1 a 22

| Chave | Referências visuais | O que conferir no traçado |
|---|---|---|
| R01 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_1_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_1_Map.png) | Corredor curto de terra entre as duas vilas; cercas, vegetação e as duas bocas. |
| R02 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_2_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_2_Map.png) | Trilha de aproximação da floresta, água/desnível e primeiros trechos de grama. |
| R03 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_3_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_3_Map.png) | Abra a floresta para o caminho da cidade, preservando curvas, grama e retornos. |
| R04 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_4_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_4_Map.png) | Jardins geométricos, fonte, corredores laterais e portões de Santalune/Lumiose. |
| R05 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_5_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_5_Map.png) | Declives, acessos e desvios do percurso entre Lumiose e Camphrier. |
| R06 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_6_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_6_Map.png) | Alameda para Parfum Palace e caminhos laterais de grama; preservar retorno à R07. |
| R07 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_7_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_7_Map.png) | Eixo comprido com água, ponte, Snorlax e acessos laterais aos serviços e à R06. |
| R08 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_8_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_8_Map.png) | Separar trilha alta na falésia e caminho baixo da praia; confirmar entradas, rampas e retornos de cada nível. |
| R09 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_9_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_9_Map.png) | Terreno rochoso e percurso de Rhyhorn rumo à Glittering Cave; manter o retorno. |
| R10 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_10_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_10_Map.png) | Alinhamento dos menires, gramado e conexões entre Cyllage e Geosenge. |
| R11 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_11_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_11_Map.png) | Caminho curto entre Geosenge e Reflection Cave, sem ligação direta a Shalour. |
| R12 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_12_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_12_Map.png) | Fazenda Skiddo, praia e bifurcação de água para Azure Bay. |
| R13 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_13_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_13_Map.png) | Área árida, desníveis e desvio para a Central; saída norte para Lumiose. |
| R14 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_14_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_14_Map.png) | Pântano, passagens secas, água e desvio da casa, entre Lumiose e Laverre. |
| R15 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_15_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_15_Map.png) | Trilha, vegetação de outono, ruínas e ramificações para R16 e Lost Hotel. |
| R16 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_16_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_16_Map.png) | Ramificações para R15, acesso próprio do Lost Hotel e Jaune Street; não criar saída para Dendemille. |
| R17 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_17_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_17_Map.png) | Campos nevados, traçado do Mamoswine, obstáculos e rampas. |
| R18 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_18_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_18_Map.png) | Trilhos, desníveis e porta da Terminus Cave no caminho até Couriway. |
| R19 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_19_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_19_Map.png) · [vista complementar](https://www.wikidex.net/wiki/Archivo:Ruta_19_full.jpg) | Pântano sob a ponte, travessia superior e as duas entradas. |
| R20 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_20_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_20_Map.png) | Mata de baixa visibilidade, bifurcações, Moss Rock e saída para Pokémon Village. |
| R21 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_21_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_21_Map.png) | Percurso de Snowbelle à portaria, áreas opcionais de água e passagens sem atalho. |
| R22 | [vista do jogo](https://archives.bulbagarden.net/wiki/File:Kalos_Route_22_XY.png) · [mapa regional](https://archives.bulbagarden.net/wiki/File:Kalos_Route_22_Map.png) | Saída de Santalune, ramificações e água até Chamber of Emptiness; portaria comum com R21. |

## Áreas conectadas, interiores e pontos de referência

Para setores sem vista aqui, abrir o local no índice visual e procurar
o trecho da chegada e o caminho de volta no vídeo, antes de fixar portas
ou andares. Em Lumiose, separar avenidas, praças, andares da torre,
serviços e variações de acesso; na R08, conferir independentemente o
trecho alto e o baixo. Outros recortes de interiores ainda podem estar
incompletos. A Liga é uma área separada das 16 cidades/vilas.
- **Começo:** [Exterior da casa](https://archives.bulbagarden.net/wiki/File:Player_House_XY.png), [térreo](https://archives.bulbagarden.net/wiki/File:Player_House_1F_XY.png), [quarto](https://archives.bulbagarden.net/wiki/File:Player_Bedroom_f_XY.png), [floresta](https://archives.bulbagarden.net/wiki/File:Santalune_Forest_XY.png), [Centro](https://archives.bulbagarden.net/wiki/File:Pok%C3%A9mon_Center_inside_XY.png), [ginásio: entrada](https://archives.bulbagarden.net/wiki/File:Santalune_Gym_Exterior_XY.png), [ginásio: piso inferior](https://archives.bulbagarden.net/wiki/File:Santalune_Gym_B1F_XY.png).
- **Palácios e costa:** [Shabboneau](https://archives.bulbagarden.net/wiki/File:Shabboneau_Castle_XY.png), [Parfum Palace](https://archives.bulbagarden.net/wiki/File:Parfum_Palace_XY.png), [jardins](https://archives.bulbagarden.net/wiki/File:Parfum_Palace_Courtyard_XY.png), [Connecting Cave](https://archives.bulbagarden.net/wiki/File:Connecting_Cave_XY.png), [Glittering Cave](https://archives.bulbagarden.net/wiki/File:Glittering_Cave_main_cave_XY.png), [Reflection Cave](https://archives.bulbagarden.net/wiki/File:Reflection_Cave_1F_XY.png), [Tower of Mastery](https://archives.bulbagarden.net/wiki/File:Tower_of_Mastery_XY.png), [Azure Bay](https://archives.bulbagarden.net/wiki/File:Azure_Bay_XY.png), [Sea Spirit’s Den](https://archives.bulbagarden.net/wiki/File:Sea_Spirit%27s_Den_interior_XY.png).
- **Interior e montanha:** [Central](https://archives.bulbagarden.net/wiki/File:Kalos_Power_Plant_XY.png), [Poké Ball Factory](https://archives.bulbagarden.net/wiki/File:Pok%C3%A9_Ball_Factory_interior_XY.png), [Lost Hotel](https://archives.bulbagarden.net/wiki/File:Lost_Hotel_XY.png), [Frost Cavern: exterior](https://archives.bulbagarden.net/wiki/File:Frost_Cavern_Outside_XY.png), [Frost Cavern: 3F](https://archives.bulbagarden.net/wiki/File:Frost_Cavern_3F_XY.png), [QG Flare](https://archives.bulbagarden.net/wiki/File:Team_Flare_Secret_HQ_XY.png), [Terminus Cave](https://archives.bulbagarden.net/wiki/File:Terminus_Cave_1F_Entrance_XY.png), [Pokémon Village](https://archives.bulbagarden.net/wiki/File:Pok%C3%A9mon_Village_XY.png), [Unknown Dungeon](https://archives.bulbagarden.net/wiki/File:Unknown_Dungeon_XY.png), [Chamber of Emptiness](https://archives.bulbagarden.net/wiki/File:Chamber_of_Emptiness_XY.png).
- **Liga e pós-jogo:** [Portaria](https://archives.bulbagarden.net/wiki/File:Kalos_Victory_Road_Gate_XY.png), [primeira caverna](https://archives.bulbagarden.net/wiki/File:Kalos_Victory_Road_First_cave_XY.png), [primeira clareira](https://archives.bulbagarden.net/wiki/File:Kalos_Victory_Road_First_grove_XY.png), [Liga](https://archives.bulbagarden.net/wiki/File:Pok%C3%A9mon_League_Kalos.png), [Battle Maison](https://archives.bulbagarden.net/wiki/File:Battle_Maison_outside_XY.png), [Friend Safari](https://archives.bulbagarden.net/wiki/File:Friend_Safari_inside_XY.png).
## Da referência ao mapa 2D

1. Fazer um croqui por local e alinhar suas bordas com os vizinhos. Fixar
   primeiro o percurso principal, ordem e direção das saídas, portas,
   atalhos com requisito e retornos; depois, curvas, silhuetas e distâncias
   relativas. Traduzir desnível com borda, escada, rampa ou transição entre
   mapas; não copiar a câmera 3D, nem transformar caminho jogável em cenário.
2. No catálogo de tiles de Kanto **já usados pelo Blue**, escolher os
   equivalentes para chão, paredes, água, vegetação e marcos. Compor peças
   existentes para lembrar o local de X/Y o máximo possível: manter posição
   relativa, proporção e função dos marcos. Se faltar um equivalente, usar
   a composição mais próxima com o acervo existente e anotar a diferença;
   outras peças ou assets exigem revisão separada. Não repintar os
   tilesets globais nem alterar mapas de Kanto para adaptar Kalos.
3. Registrar por mapa o croqui, as fontes consultadas, conexões e portas,
   equivalências de tiles, diferenças intencionais e lacunas. Começar pelo
   [corredor Vaniville → Aquacorde → Santalune](KALOS_KD03_DESENHO_E_PRIMEIRO_RECORTE.md).
4. Quando houver autorização para implementar, comparar lado a lado a
   vista 2D e as referências: o local tem de ser reconhecível pelo traçado
   e pelos marcos, não só pelo nome. Validar no motor passabilidade,
   entradas e retornos nos dois sentidos, transições de nível e gates.
   Se o estilo e a fidelidade competirem, preservar o percurso e os marcos
   com os tiles do Blue em vez de copiar textura, modelo ou câmera.
   Revisão visual não substitui teste de jogabilidade.

Esta fase documenta as referências e a regra de construção. Não cria
MapIDs, mapas, tiles, scripts ou build. Kalos permanece `planned`.
