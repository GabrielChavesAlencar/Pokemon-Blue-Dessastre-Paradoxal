# Galar — pesquisa e planejamento, sem implementação

Uma campanha **Sword + Shield em 2D** no Blue, com Isle of Armor e
Crown Tundra como capítulos opcionais independentes. Manter as oito
vagas de ginásio; as duplas Bea/Allister e Gordie/Melony representam
variantes da mesma vaga. A [Champion Cup oficial](https://swordshield.pokemon.com/en-gb/people-galar-region/rivals/)
leva ao desafio contra Leon, não a uma Elite Four inventada.
Siga o [plano multirregional do Blue](PLANO_REGIOES_DESSASTRE_V2.md).

**Escopo:** só pesquisa, documentação e planejamento. Sem construir
mapas, alterar código, arte/tiles, MapIDs, saves, catálogo, instalador
ou publicar jogo. O workflow de Galar valida estes documentos, não compila
o jogo. O [roadmap jogável](GALAR_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md)
exige autorização posterior.

## Entregas documentais

| Fase | Saída |
|---|---|
| GD00 | Baseline abaixo: catálogo, limites e contratos reais do Blue. |
| GD01 | [Pesquisa de fontes e direitos](GALAR_GD01_FONTES_E_DIREITOS.md), incluindo quais mapas nativos foram efetivamente identificados. |
| GD02 | [Inventário e progressão](GALAR_GD02_INVENTARIO_E_PROGRESSAO.md): rotas, cidades, Wild Area, campanha, variantes e DLC. |
| GD03 | [Desenho 2D e recorte inicial](GALAR_GD03_DESENHO_E_PRIMEIRO_RECORTE.md): Postwick até a primeira insígnia em Turffield. |
| GD04 | [Validação e entrega futura](GALAR_GD04_VALIDACAO_E_HANDOFF.md): cenários de aceitação, paridade Windows/Android e limites de publicação. |
| GD05 | [Atlas visual](GALAR_GD05_ATLAS_VISUAL_E_TILES_KANTO.md): vistas e localização de rotas, cidades, Wild Area e DLC. |

A regra é por mapa. Procurar versões prontas ou quase prontas em RPG
Maker XP/Essentials. Candidato não basta: verificar formato editável,
traçado fiel, encaixe técnico e permissão por arquivo. Se faltar mapa
aprovado, **refazer em 2D com os tilesets e autotiles de Kanto já usados
no jogo**, preservando o máximo possível de caminhos, silhueta, saídas
e marcos de Galar. Captura, planta e vídeo orientam, não viram assets.

## GD00 — baseline estática

Snapshot `76874bc6494469dfb77827b3707c5cd626a994e2`, árvore
`9e44b821a25d4179eff8c8df919ad9e931dcf603`, 2.299 caminhos
rastreados. A busca por nomes na árvore não encontrou implementação
específica Galar; não equivale a inspecionar instalação, caminhos
genéricos ou saves privados.

| Contrato | Implicação |
|---|---|
| [Registro regional](../site/public/data/regions.json) | `GALAR` permanece `planned`; Sword, Shield e duas DLC, oito chaves e três capacidades de campo. |
| [Seleção inicial](NOVO_JOGO_SELECAO_REGIONAL.md) e [viagem](VIAGEM_REGIONAL_LIVRE_NPC.md) | Um save e um futuro destino em Postwick apenas após qualificação. Táxi, trem e bicicleta não substituem o NPC de viagem entre regiões instaladas. |
| [MapIDs históricos](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) | Nenhum ID reservado ou faixa declarada livre para Galar. Testar capacidade real antes de alocar e preservar IDs existentes. |
| [Balanceamento](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md) | Compartilhar regras do Blue: não reativar Dynamax/Gigantamax porque aparecem nas referências. Estádios e narrativa são separados da política de batalha. |
| [Publicação de Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md) | Lançador Windows e atualização Android pela fonte da mesma revisão; nenhuma distribuição nova nesta entrega. |

Jogabilidade e QA física continuam `NOT_RUN`.
