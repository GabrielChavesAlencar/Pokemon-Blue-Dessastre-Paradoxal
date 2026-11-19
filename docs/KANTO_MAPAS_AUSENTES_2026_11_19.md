# Kanto: Cerulean, Android e mapas ainda ausentes — 19/11/2026

Auditoria da main `e73356a9`, comparada à fonte Essentials FRLG 1.1 do manifesto.
O arquivo local `Essentials FRLG V1.1.rar` foi conferido por SHA-256 antes da extração:
`48883c8217bcd9e7fa1b9446bddaa9db5f9715a7ba73ac02785b6660769e2683`.
Nenhum mapa do jogo pessoal ou save foi alterado.

## Bugs relatados e entrega Android

- **Norte de Cerulean:** Map053/Rota 24, Map054/Rota 25 e Map055/casa do Bill já foram acrescentados à main, após os 142 IDs antigos. O teste de preservação dos IDs e as três conexões nativas da fonte passaram. A imagem da ponte é consistente com a instalação antiga sem esses mapas; a imagem sozinha não identifica a revisão instalada.
- **Luis no ginásio:** `Journey.rb` reconhecia o nome Luis como um líder de Decades e procurava `Luis (2v2 Full Power)` para `BLUE_KANTO_SWIMMER`. O código atual preserva a identidade dos treinadores `BLUE_KANTO_*`. O log fornecido corresponde exatamente a esse defeito antigo.
- **Entrega comprovada no pacote:** o [workflow integrado 44605300367](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44605300367) terminou com sucesso e verificou o ZIP final: `kanto_maps=145`, `compiled_journey=true`, mapas de Cerulean/rotas/Bill presentes e três conexões remapeadas. É prova de compilação/empacotamento, não de gameplay Android.
- **Edição conjunta:** [android-multiregion-61-efdaec9](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-multiregion-61-efdaec9), com patches para sete revisões anteriores.
- **Piloto isolado:** [kanto-android-2680-b276975](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/kanto-android-2680-b276975), também com as correções. Os canais têm perfis distintos; use o atualizador da instalação existente. Com o JoiPlay fechado: `python ATUALIZAR-ANDROID.py --update`. O atualizador verifica o canal e a revisão; não aplique um patch de outro canal.

## Resultado da cobertura

| Medida | Resultado |
|---|---:|
| Entradas descendentes da pasta Kanto na fonte | 217 |
| Mapas no catálogo integrado | 145 |
| Desses, ainda `preview_only` | 35 |
| Mapas de conteúdo fora do catálogo | 62 |
| Entradas ausentes com aspecto de pasta/cenário vazio | 10 |
| Arquivos de mapas ausentes na fonte para o catálogo atual | 0 |

As dez entradas de hierarquia são candidatos estruturais: possuem filhos, nenhum evento e um terreno 20×15 uniforme. Não são contadas como 10 áreas jogáveis em falta. Intro, Debug, Battle Test e a própria pasta Kanto ficam fora da comparação. Os 35 previews já estão importados, mas não equivalem a áreas com eventos/campanha completos.

**IDs abaixo são da fonte FRLG, não IDs do jogo integrado. Não os use para editar saves ou teletransportar no jogo principal.** Acrescentar os outros mapas exige adaptar eventos, dependências, treinadores, conexões e preservar os IDs já publicados; esta auditoria não instala esses mapas.

## 62 mapas de conteúdo ainda fora da integração

| ID da fonte | Local |
|---|---|
| 023 | Diglett's Cave - Entrance |
| 043 | Bike Shop |
| 044 | Cerulean House |
| 045 | Cerulean House |
| 046 | Cerulean House |
| 047 | Cerulean House |
| 048 | Ransacked House |
| 050 | Cerulean Cave - 1F |
| 051 | Cerulean Cave - 2F |
| 052 | Cerulean Cave - B1F |
| 058 | Pokémon Day Care |
| 068 | Pokémon Fan Club |
| 069 | Vermilion House |
| 070 | Vermilion House |
| 071 | Fisherman's House |
| 079 | Route 11 |
| 080 | Gatehouse |
| 081 | Diglett's Cave - Entrance |
| 082 | Diglett's Cave - Tunnel |
| 083 | Route 12 |
| 084 | Gatehouse |
| 085 | Fishing Guru's House |
| 086 | Route 9 |
| 087 | Route 10 |
| 088 | Rock Tunnel Pokémon Center |
| 090 | Rock Tunnel - 1F |
| 091 | Rock Tunnel - B1F |
| 092 | Power Plant |
| 093 | Lavender Town |
| 094 | Lavender Pokémon Center |
| 095 | Lavender Poké Mart |
| 096 | Lavender House |
| 097 | Name Rater's House |
| 098 | Mr. Fuji's House |
| 100 | Pokémon Tower - 1F |
| 101 | Pokémon Tower - 2F |
| 102 | Pokémon Tower - 3F |
| 103 | Pokémon Tower - 4F |
| 104 | Pokémon Tower - 5F |
| 105 | Pokémon Tower - 6F |
| 106 | Pokémon Tower - 7F |
| 125 | Celadon Diner |
| 126 | Celadon Hotel |
| 127 | Celadon House |
| 128 | Celadon Mansion |
| 129 | Game Corner |
| 131 | Rocket Hideout - B1F |
| 132 | Rocket Hideout - B2F |
| 133 | Rocket Hideout - B3F |
| 134 | Rocket Hideout - B4F |
| 135 | Rocket Hideout - Elevator |
| 136 | Route 16 |
| 137 | Cycling Road Gate |
| 138 | Secret House |
| 139 | Route 16 |
| 140 | Route 17 |
| 148 | Fuchsia House |
| 149 | Fuchsia House |
| 150 | Fuchsia House |
| 151 | Fisherman's House |
| 166 | Route 14 |
| 167 | Route 13 |

## Mapas importados somente como prévia

- 057: `SAFFRON_GATE_NORTH`
- 062: `SAFFRON_GATE_SOUTH`
- 107: `ROUTE_8`
- 108: `SAFFRON_GATE_EAST`
- 109: `UNDERGROUND_ROUTE8_EAST`
- 110: `UNDERGROUND_ROUTE8_TUNNEL`
- 111: `ROUTE_7`
- 112: `SAFFRON_GATE_WEST`
- 113: `UNDERGROUND_ROUTE7_WEST`
- 117: `CELADON_DEPT_1F`
- 118: `CELADON_DEPT_2F`
- 119: `CELADON_DEPT_3F`
- 120: `CELADON_DEPT_4F`
- 121: `CELADON_DEPT_5F`
- 122: `CELADON_DEPT_ROOF`
- 123: `CELADON_DEPT_ELEVATOR`
- 141: `ROUTE_18_FUCHSIA`
- 142: `ROUTE_18_GATE`
- 143: `ROUTE_18_CYCLING`
- 164: `ROUTE_15`
- 165: `ROUTE_15_GATE`
- 173: `SAFFRON_TRAINER_FAN_CLUB`
- 174: `SAFFRON_HOUSE_A`
- 175: `SAFFRON_HOUSE_B`
- 176: `SAFFRON_HOUSE_C`
- 177: `SILPH_LOBBY`
- 190: `ROUTE_19`
- 191: `ROUTE_20`
- 193: `SEAFOAM_1F`
- 194: `SEAFOAM_B1F`
- 195: `SEAFOAM_B2F`
- 196: `SEAFOAM_B3F`
- 197: `SEAFOAM_B4F`
- 198: `ROUTE_21`
- 210: `VICTORY_ROAD_HUB`

## Entradas vazias de organização, separadas do conteúdo

- 035: Mt. Moon
- 049: Cerulean Cave
- 073: S.S. Anne
- 089: Rock Tunnel
- 099: Pokémon Tower
- 116: Celadon Dept. Store
- 130: Rocket Hideout
- 154: Safari Zone
- 192: Seafoam Island Cave
- 204: Pokémon Mansion

## Verificação reproduzível e limites

Execute `python scripts/regions/audit_kanto_coverage.py` depois de preparar a fonte pelo procedimento de SHA-256 do projeto. O JSON também lista saídas diretas dos mapas catalogados para destinos ausentes, tanto por conexões como por transferências dos eventos da fonte. Essas referências não provam que os eventos importados deixam o jogador atravessar: portas podem estar intencionalmente bloqueadas. Scripts arbitrários e transferências calculadas não são executados por esta auditoria.

A verificação do ZIP Android passou a conferir **todos os 145 arquivos de mapa**, em vez de apenas os cinco mapas críticos de Cerulean. Testes rejeitam um ZIP sem Pallet ou com Floresta de Viridian truncada, mesmo quando Cerulean está completa, nos canais integrado e piloto.

Validações locais: 255 testes Kanto preexistentes passaram (um ignorado); cinco testes novos da auditoria passaram; 46 testes Android passaram (três ignorados), incluindo os três testes novos de entrega. A fonte real passou nos testes de coordenadas/conexões de Cerulean. O teste Ruby da identidade Luis foi executado com sucesso pela CI nativa existente; Ruby não está disponível no PATH desta sessão local.

**T3/T4: não executados nesta sessão (BLOCKED_ENV).** Esta cópia de trabalho contém código e a fonte FRLG, sem um Game.exe isolado preparado para QA; não há sessão Android conectada. Não houve playthrough visual, batalha no aparelho Android nem save/reload real. Compilação Windows e testes estruturais não substituem esses testes. Não foram alterados `accepted_integrally`, `playable` ou as barras de aceite.

