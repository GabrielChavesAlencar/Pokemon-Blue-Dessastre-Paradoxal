# Sinnoh G07 — Matriz de vínculos físicos pendentes (Twinleaf / Verity / Sandgem)

**17/11/2026 — entrega GitHub-only.** Verifica os contratos versionados sem ler o PC, carregar mapas do doador, abrir `Game.exe` ou compilar eventos. **Nada aqui é um warp instalado.**

## 1. Fontes e alcance real

A G07 cruza [roteiro simbólico CH06](../data/regions/sinnoh-twinleaf-events.json), seu [schema](../data/regions/sinnoh-twinleaf-events.schema.json), [introdução S13](../data/regions/sinnoh-intro-s13.json), [iniciais S14](../data/regions/sinnoh-starters-s14.json) e manifestos públicos [B07](../data/regions/sinnoh-b07-private-stage.json), [B08](../data/regions/sinnoh-b08-private-qa.json) e [B09](../data/regions/sinnoh-b09-native-qa.json).

O auditor [CH06](../scripts/regions/audit_sinnoh_twinleaf_events.py) já validava o grafo de 9 mapas, 24 eventos e 8 pares bidirecionais. A **G07 acrescenta matriz individual de pendências**, reconciliação de história S13 e Poké Bolas S14 com seus locais e ligações, e um portão entre **geometria do stage privado** e **eventos realmente não compilados**.

**Resultado verificável pelo GitHub:** 9 símbolos reconhecidos, 16 warps planejados, 5 handlers narrativos, 3 Poké Bolas físicas e 6 checkpoints narrativos. **Resultado não verificável pelo GitHub:** quais nove dos 54 terrenos de Sinnoh correspondem a esses símbolos; nenhum `map_id`, `map_sha256`, `x`, `y`, `sprite` ou ID de evento nativo foi confirmado.

## 2. Nove mapas de planejamento (todos ainda sem vínculo físico)

| Símbolo de CH06 | Papel | Estado do vínculo |
| --- | --- | --- |
| `SINNOH_PLAYER_BEDROOM` | Quarto inicial do jogador | MapID, posição, passabilidade e spawn não verificados |
| `SINNOH_PLAYER_HOUSE_1F` | Casa, mãe e acesso ao quarto | Interior, sprite da mãe e portais pendentes |
| `SINNOH_TWINLEAF_TOWN` | Exterior de Twinleaf | Entradas de casas e saída para Route 201 pendentes |
| `SINNOH_BARRY_HOUSE` | Casa de Barry | Interior, personagem e saída pendentes |
| `SINNOH_ROUTE_201` | Conexão entre Twinleaf, Lake Verity e Sandgem | Passagem e portais pendentes |
| `SINNOH_LAKE_VERITY` | Maleta de Rowan, 3 Poké Bolas, batalha inicial | Eventos físicos, sprites, permissões e batalha pendentes |
| `SINNOH_SANDGEM_TOWN` | Exterior de Sandgem | Entradas/saídas pendentes |
| `SINNOH_PROFESSOR_ROWAN_LABORATORY` | Laboratório e Pokédex | Interior, evento de Rowan e saída pendentes |
| `SINNOH_ROUTE_202` | Continuação da progressão | Conexão com Sandgem pendente |

**Não atribuir esses símbolos à sequência 442–450 por conveniência.** B07/B09 fornecem 54 terrenos candidatos `442–495`, porém ainda não fornecem o mapeamento auditado símbolo → mapa. Os 22 IDs `496–517` são placeholders excluídos. O total declarado de **702 mapas do clone privado** não prova que qualquer um destes portais está instalado.

## 3. Dezesseis portais simbólicos, organizados em oito pares

| Ida planejada | Volta planejada | Situação |
| --- | --- | --- |
| Quarto → casa 1F | Casa 1F → quarto | Ambas precisam de tile de saída e tile de chegada |
| Casa 1F → Twinleaf | Twinleaf → casa 1F | Entrada/saída do lar não auditadas |
| Twinleaf → casa de Barry | Casa de Barry → Twinleaf | Entrada/saída não auditadas |
| Twinleaf → Route 201 | Route 201 → Twinleaf | Passabilidade não auditada |
| Route 201 → Lake Verity | Lake Verity → Route 201 | Passabilidade não auditada |
| Route 201 → Sandgem | Sandgem → Route 201 | Passabilidade não auditada |
| Sandgem → laboratório de Rowan | Laboratório de Rowan → Sandgem | Portas e chegada não auditadas |
| Sandgem → Route 202 | Route 202 → Sandgem | Passagem não auditada |

Cada um dos 16 eventos tem chave própria `SN_*` conferida no arquivo CH06. O relatório G07 fornece **as duas chaves de cada par**, ambos os símbolos, e deixa o `native_event_id` e a posição de chegada como `null`. O validador recusa topologia modificada, retorno órfão, destino inexistente, portais adicionais inventados ou `verified_arrival=true` sem prova.

## 4. História e eventos físicos: cruzamento S13/S14

Sequência narrativa **autoral Blue**, sem reproduzir scripts do doador:

1. Mãe `mother_intro` na casa 1F, `SN_NPC_MOTHER`.
2. Barry `barry_intro` na casa de Barry, `SN_NPC_BARRY_INTRO`, após mãe.
3. Rowan `rowan_briefcase_seen` em Lake Verity, `SN_NPC_ROWAN_BRIEFCASE`, após Barry.
4. `starter_received` por **três eventos físicos** `SN_BALL_TURTWIG`, `SN_BALL_CHIMCHAR`, `SN_BALL_PIPLUP`, após Rowan.
5. `rival_fought` em Lake Verity, `SN_NPC_BARRY_BATTLE`, depois de receber inicial.
6. `pokedex_received` no laboratório, `SN_NPC_ROWAN_POKEDEX`, depois da batalha.

**S14** associa Turtwig → rival Chimchar (PBS 0), Chimchar → rival Piplup (PBS 1), Piplup → rival Turtwig (PBS 2). O código exige evento físico com trigger `action`, sem escolha no diálogo de Rowan, e recusa qualquer `event_compiled`, `grant_tested_in_game`, `native_event_id`, sprite ou callback marcado como comprovado sem evidência. **As versões PBS de Barry continuam sem compilação nativa comprovada.**

## 5. Proteções e entregáveis

- [Auditor G07](../scripts/regions/audit_sinnoh_g07_twinleaf_bindings.py): valida contratos CH06, S13, S14, B07–B09 e gera matriz detalhada de mapas, eventos, portais, história e pendências.
- [20 testes negativos e positivos G07](../tests/test_sinnoh_g07_twinleaf_bindings.py): mutações de MapID, SHA, coordenada, sprite, retorno, handlers, cadeia S13, escolha S14, geometrias B07, inventário B09 e gates falseados.
- [Workflow GitHub Actions G07](../.github/workflows/sinnoh-g07-twinleaf-bindings.yml): executa testes e arquiva **somente um JSON de metadados simbólicos**. Não baixa PNG, RXDATA, PBS, Game.exe nem saves privados.

Comando de relatório offline no repositório, somente leitura:

~~~bash
python scripts/regions/audit_sinnoh_g07_twinleaf_bindings.py
python -m unittest discover -s tests -p 'test_sinnoh_g07_twinleaf_bindings.py' -v
~~~

**Status esperado:** `TWINLEAF_SYMBOLIC_BINDING_MATRIX_ONLY_NATIVE_EVIDENCE_PENDING`.

## 6. O que falta para converter o roteiro em eventos jogáveis

É obrigatório obter autorização e comprovação física para cada mapa: associar 9 símbolos a 9 MapIDs reais sem colisão, confrontar SHA e dimensões, validar spawn e passabilidade, conferir 16 saídas/chegadas reais e 5 NPCs com sprites e callbacks, posicionar as 3 Poké Bolas físicas, compilar PBS/handlers em cópia isolada e testar dentro da VM B10 com auditoria B11 e no JoiPlay.

Apenas após essas evidências pode ser discutida a passagem para eventos efetivos; **G07 não instala nem habilita Sinnoh na instalação principal**. As reservas R07, direitos R08 e aprovação R09 seguem pendentes. **Barras de jogabilidade B/C/D: 0/13.**

**Próxima entrega G08:** testes mais profundos dos contratos de Rowan, Barry, iniciais e balanceamento dinâmico, sempre com fixtures offline.
