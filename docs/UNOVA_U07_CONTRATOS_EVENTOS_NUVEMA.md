# Unova U07 — contratos de eventos do início de Pokémon White

**Projeto:** Pokémon Blue: Dessastre Paradoxal | **Data:** 17/11/2026 | **Estado:** contratos planejados, não jogáveis.

**Nenhum MapID, NPC, sprite, batalha, script ou recompensa real foi inserido no Game.exe.** Unova permanece planned no portal; nenhum save nativo foi aberto.

## Arquivos entregues

- [Catálogo de eventos U07](../data/regions/unova-u07-nuvema-events.json): 13 eventos ordenados em Nuvema, Route 1 e Accumula, com área simbólica U03, NPC SP04, pré-requisitos, diálogo original curto PT-BR, política de batalha, recompensas idempotentes e IDs/posição reais nulos.
- [Validador e simulador U07](../scripts/regions/audit_unova_u07_events.py): confirma 74 áreas, 73 NPCs, estado planned, três iniciais, ordem de flags e recompensas em estado sintético. **Não executa Ruby, scripts Essentials, inventário real ou saves.**
- [Testes U07](../tests/test_unova_u07_events.py): regressões contra reentrada e itens duplicados, perda de batalha, mudanças de inicial, flags externas e MapIDs falsos.
- [UNOVA_VALIDAR_EVENTOS_NUVEMA.bat](../UNOVA_VALIDAR_EVENTOS_NUVEMA.bat): validador por duplo clique sem PowerShell. Relatório privado em .blue-work/unova/audit/u07-events-contract-preview.json.

## Sequência narrativa U07

| Passo | Evento | Local | Comportamento de referência |
|---|---|---|---|
| 1 | STARTER_GIFT | Quarto de Nuvema | Escolha Snivy, Tepig ou Oshawott, só uma vez |
| 2 | BIANCA_FIRST_BATTLE | Quarto | Rival com inicial fraco contra o do jogador; derrota não bloqueia |
| 3 | CHEREN_FIRST_BATTLE | Quarto | Rival com inicial forte contra o jogador; derrota não bloqueia |
| 4 | MOM_XTRANSCEIVER | Casa | Mãe entrega Xtransceiver uma vez |
| 5 | VISIT_BIANCA_HOME | Casa de Bianca | Visita pré-laboratório |
| 6 | JUNIPER_LAB_POKEDEX | Laboratório | Juniper concede Pokédex uma vez |
| 7 | MOM_TOWN_MAP | Saída do laboratório | Mãe entrega Town Map uma vez |
| 8 | ROUTE1_GROUP | Rota 1 | Encontro do grupo |
| 9 | JUNIPER_CAPTURE_TUTORIAL | Rota 1 | Tutorial e 5 Poké Balls, sem duplicação |
| 10 | ACCUMULA_CENTER_INTRO | Accumula | Introdução ao Centro Pokémon |
| 11 | PLASMA_SPEECH | Praça de Accumula | Discurso de Ghetsis |
| 12 | N_FIRST_BATTLE | Praça de Accumula | Batalha de N com vitória exigida na simulação |
| 13 | ROUTE2_PASSAGE | Saída norte de Accumula | Apenas token de história, sem teleporte ou mapa instalado |

Os eventos e recompensas usam prefixos UNOVA_U07 e referência simbólica, nunca IDs numéricos de eventos ou mapas. As falas PT-BR são **originais**, sem copiar os diálogos oficiais, e níveis/times não foram inventados. O agente de viagens fica para evento isolado após Nuvema real. Running Shoes pertencem à Route 2 e ficam fora desse escopo.

## Iniciais e rivais

| Inicial do jogador | Inicial de Cheren (vantagem) | Inicial de Bianca (desvantagem) |
|---|---|---|
| Snivy | Tepig | Oshawott |
| Tepig | Oshawott | Snivy |
| Oshawott | Snivy | Tepig |

O simulador permite avançar após perder as primeiras batalhas com Bianca e Cheren. A derrota para N retorna RETRY_REQUIRED sem desbloquear saída. Batalhas reais, blackout, EXP, cura e persistência na engine ainda precisam de QA separado.

## Recompensas simbólicas, uma única vez

XTRANSCEIVER (1), POKEDEX (1), TOWN_MAP (1), POKE_BALL (5) e ROUTE_2_PASSAGE_READY (1 token de narrativa). **Não são concedidos no Game.exe**: o estado simulado armazena intenções e valida que após salvar/recarregar em JSON sintético não é possível repetir concessões ou trocar o inicial.

## Como validar no Windows

1. Atualize os arquivos do repositório.
2. Dê duplo clique em UNOVA_VALIDAR_EVENTOS_NUVEMA.bat.
3. O BAT valida os contratos e roda a suíte de testes negativa de U07 sem abrir o jogo.
4. Consulte o JSON privado em .blue-work/unova/audit/u07-events-contract-preview.json.

No terminal de desenvolvimento, execute: python scripts/regions/audit_unova_u07_events.py --simulate-demo --starter SNIVY --write. Repita com TEPIG ou OSHAWOTT. Isso não grava nenhum save real.

## Port para Essentials 21.1 — só depois dos insumos reais

1. Obter/produzir Nuvema, seus interiores, Route 1 e Accumula com arte e tiles permitidos.
2. Conferir MapInfos e MapNNN verdadeiros da instalação Decades e remapear sem colisões com as outras regiões.
3. Concluir SP05 Cheren e confirmar sprites/licenças/escala dos demais NPCs.
4. Implementar gatilhos e switches regionais, premiando uma única vez por estado, seguindo API real Essentials 21.1.
5. Testar no Game.exe QA a escolha do inicial, derrotas, revisitas, batalha N, saves, retorno ao Centro Pokémon local e progressão.
6. Validar JoiPlay e regressão multirregional em instalações isoladas; somente então avançar barras jogáveis e integrar no Blue-Story.

**Progresso:** A/B/C/D = 0/8; E = 4/8; Unova jogável = 0/32. O U07 desta entrega é contrato + testes, não evento compilado.

## Referências
- [Detonado Black/White (Bulbapedia)](https://bulbapedia.bulbagarden.net/wiki/Appendix:Black_and_White_walkthrough/Section_1)
- [Nuvema Town (Thonky)](https://www.thonky.com/pokemon-black-white/nuvema-town)
- [Plano Unova U01–U32](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md)
- [Roteiro operacional SP05–U32](UNOVA_ROTEIRO_IMPLEMENTACAO_OPERACIONAL_SP05_U32.md)
