# Alola — pesquisa e planejamento, sem implementação

O plano do Dessastre Paradoxal é **uma jornada em 2D nas quatro ilhas**,
com Ultra Sun + Ultra Moon como espinha dorsal e Sun/Moon como referência
de variantes, não uma segunda campanha. Mantém o
[plano multirregional](PLANO_REGIOES_DESSASTRE_V2.md): oito provas,
quatro grandes provas separadas, Liga e defesa do título. A
[Nintendo](https://www.nintendo.com/en-gb/Misc-/Pokemon-Ultra-Sun-Pokemon-Ultra-Moon-1298959.html)
apresenta USUM como história alternativa no mesmo mundo de SM.

**Escopo desta entrega:** pesquisa e documentação. Não criar mapas,
artes, scripts, reservas de MapIDs, saves, lançadores, instalações, releases
ou um destino clicável. O workflow de Alola valida apenas documentação.
O [roadmap jogável](ALOLA_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md)
exige nova autorização para ser executado.

## Entregas e ordem

| Fase | Saída verificável |
|---|---|
| AD00 | Baseline abaixo: catálogo, escopo e contratos reais do Blue. |
| AD01 | [Matriz de fontes e direitos](ALOLA_AD01_FONTES_E_DIREITOS.md): separar candidatos editáveis, referências e entradas excluídas. |
| AD02 | [Inventário e progressão](ALOLA_AD02_INVENTARIO_E_PROGRESSAO.md): cidades, rotas, ilhas, provas, mobilidade, campanha e pós-jogo. |
| AD03 | [Desenho 2D e primeiro recorte](ALOLA_AD03_DESENHO_E_PRIMEIRO_RECORTE.md): Melemele até Hala, com retorno e requisitos reais. |
| AD04 | [Validação e entrega futura](ALOLA_AD04_VALIDACAO_E_HANDOFF.md): testes, publicação Windows/Android e bloqueios de promoção. |
| AD05 | [Atlas visual](ALOLA_AD05_ATLAS_VISUAL_E_TILES_KANTO.md): referências do traçado original por cidade, rota e área ligada. |

**Regra por mapa:** procurar um mapa RPG Maker XP / Essentials pronto
ou quase pronto e confirmar arquivo editável, cobertura de USUM,
compatibilidade com o Blue e permissão por componente. Se não passar,
refazer do zero com os **tilesets e autotiles de Kanto já usados no jogo**.
A silhueta, os caminhos, as entradas e os marcos são de Alola; a
linguagem visual é de Kanto. Usar imagens e percursos como referência,
não como assets, e anotar o que não pôde ser confirmado.

## AD00 — baseline estática

Revisão inspecionada: `c68d8350262dd1e4c11d61a62120f202523d9095`, árvore
`f7dc77544040b8549bfe9da2c0258aecb6d24319`, 2.291 caminhos rastreados.
A busca por nomes não encontrou mapas/receitas específicos de Alola
nessa árvore; isso não inspeciona dados privados, arquivos instalados
ou arquivos com nomes genéricos.

| Contrato existente | Consequência para o plano |
|---|---|
| [Catálogo regional](../site/public/data/regions.json) | `ALOLA` está `planned`, base USUM, quatro versões registradas, oito chaves de prova e sete Poké Rides narrativos. Não mudar o catálogo nesta entrega. |
| [Novo jogo](NOVO_JOGO_SELECAO_REGIONAL.md) e [viagem regional](VIAGEM_REGIONAL_LIVRE_NPC.md) | Uma instalação e um save. Propor o ponto inicial junto à casa em Hau’oli Outskirts (R01), sujeito à definição no motor e sem criar destino agora. |
| [Inventário histórico de mapas](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) | Não reserva IDs de Alola. Conferir IDs reais, reservados e indiretos e não presumir suporte acima de 999. |
| [Publicação Windows e Android](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md) | Um mesmo produto: lançador Windows e atualização Android pela fonte e pelo fluxo existente; sem novo ZIP geral. |
| [Balanceamento do Blue](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md) | Não criar regras paralelas para Totem, Kahuna ou Liga. Validar comportamento no jogo somente após autorização. |

A validação documental não conta como execução no Game.exe, Android
ou teste físico. Todas as verificações do jogo permanecem `NOT_RUN`.
