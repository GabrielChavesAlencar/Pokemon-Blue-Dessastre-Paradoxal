# Paldea — pesquisa e planejamento, sem implementação

Uma campanha **Scarlet + Violet em 2D**, mantendo os três caminhos de
Paldea e seu encontro na Area Zero. Kitakami (The Teal Mask) e Blueberry
Academy (The Indigo Disk) são capítulos extras, com retorno e regras
próprias. A [descrição oficial de Scarlet/Violet](https://www.pokemon.com/uk/pokemon-video-games/pokemon-scarlet-and-pokemon-violet)
confirma as três histórias em mundo aberto e as duas viagens das
expansões. O [plano multirregional do Blue](PLANO_REGIOES_DESSASTRE_V2.md)
define quais conquistas contam e como o mesmo save atravessa regiões.

**Escopo desta entrega:** pesquisar, documentar e planejar. Não criar
mapas, scripts, assets, MapIDs, saves, instaladores, releases nem ativar
destino. O workflow de Paldea valida só a documentação.
O [roadmap jogável](PALDEA_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md)
depende de autorização posterior.

## Entregas documentais

| Fase | Saída |
|---|---|
| PD00 | Baseline abaixo: catálogo, limites e contratos reais do Blue. |
| PD01 | [Pesquisa de fontes e direitos](PALDEA_PD01_FONTES_E_DIREITOS.md), separando mapa editável, recurso visual e referência. |
| PD02 | [Inventário e progressão](PALDEA_PD02_INVENTARIO_E_PROGRESSAO.md): mundo aberto, províncias, três caminhos, Area Zero e DLC. |
| PD03 | [Desenho 2D e recorte inicial](PALDEA_PD03_DESENHO_E_PRIMEIRO_RECORTE.md): Cabo Poco, Mesagoza e primeira insígnia possível, sem tornar a jornada linear. |
| PD04 | [Validação e entrega futura](PALDEA_PD04_VALIDACAO_E_HANDOFF.md): testes de navegação, progresso, paridade Windows/Android e publicação. |
| PD05 | [Atlas visual](PALDEA_PD05_ATLAS_VISUAL_E_TILES_KANTO.md): cidades, áreas das províncias, marcos e expansões. Não há rotas numeradas clássicas. |

A regra vale por área e mapa. Um mapa pronto ou quase pronto em RPG
Maker XP / Essentials só entra se arquivo editável, traçado, encaixe
técnico e permissão por componente forem verificados. Onde faltar mapa
aprovado, **reconstruir do zero em 2D com os tilesets e autotiles de
Kanto já usados no jogo**. Usar o maior número de vistas complementares
úteis para se aproximar de Scarlet/Violet: manter silhueta, conexões,
desníveis e marcos, sem copiar capturas ou modelos. Registrar o que
não puder ser conferido e cada adaptação do terreno.

## PD00 — baseline estática

Revisão `59afa3a7c73f9aea53b8eb592ebea3315965d92e`, árvore
`d24dbc9b4909b46e8dab28bf548b3fff304ee27a`, 2.307 caminhos
rastreáveis. A busca por nomes não encontrou implementação específica
de Paldea. Esta leitura não inspeciona instalações, dados privados
ou arquivos genéricos.

| Contrato | Implicação |
|---|---|
| [Catálogo regional](../site/public/data/regions.json) | `PALDEA` está `planned`; Scarlet/Violet e duas expansões, oito conquistas de ginásio e cinco capacidades de montaria. Não alterar o catálogo. |
| [Novo jogo](NOVO_JOGO_SELECAO_REGIONAL.md) e [viagem](VIAGEM_REGIONAL_LIVRE_NPC.md) | Um save; propor o agente regional no ponto inicial em Cabo Poco, só após Paldea instalada. Não confundir com táxi ou travessia da montaria. |
| [MapIDs históricos](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) | Não reservar nem declarar IDs livres. Verificar a capacidade real de todos os alvos e preservar mapas publicados. |
| [Balanceamento](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md) | Oito ginásios liberam especiais em batalha; Titãs e Equipe Star não geram esmeraldas de ginásio. Mestres, Terastalização e atividades de rede não se presumem implementados. |
| [Publicação de Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md) | Windows e Android pela fonte na mesma revisão funcional; não redistribuir jogo/arquivos de doador. |

Não há validação de gameplay, aparelho, importação ou publicação.
Todos esses cenários permanecem `NOT_RUN`.
