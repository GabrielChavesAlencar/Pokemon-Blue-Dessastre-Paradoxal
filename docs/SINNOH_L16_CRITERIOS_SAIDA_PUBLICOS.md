# Sinnoh L16 — Critérios públicos de saída, todos pendentes

**Issue #207 · conteúdo público documental GitHub-only.**

A L16 enumera **o que ainda precisaria de evidência independente para que um gate possa ser considerado**. Não recebe evidências, não confere assinaturas, não testa Game.exe e não aprova a execução nativa. Os códigos de saída são condições futuras não atendidas, derivados das identidades L13/L14/L15 já públicas, sem dar significado físico aos hashes Git.

## Indicadores preservados

| Item | Resultado |
| --- | --- |
| Pedidos inventariados e bloqueados | **88/88 PENDING/BLOCKED** |
| Critérios de saída cumpridos | **0/88** |
| Vínculos documentais | **1.084/1.084**: 846 caso→critério, 218 caso→bloqueio, 20 critério→bloqueio |
| Slots contábeis anônimos | **18**, sem novos vínculos ou identidades |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos L04 aprovados | **0/20** |
| Testes nativos G12 executados | **0/44** (43 Windows, 1 Android) |
| Barras B/C/D | **0/13** |
| R07/R08/R09 | **PENDING** |
| Situação regional | **Sinnoh planned / não jogável** |

## Códigos de saída documentais (não autorizações)

| Tipo | Pedidos | Bloqueados | Critérios atendidos | Vínculos documentais |
| --- | ---: | ---: | ---: | ---: |
| `BLOCKER_DEPENDENCY` | 5 | 5 | 0 | 0 |
| `GLOBAL_REGIONAL_GATE` | 1 | 1 | 0 | 0 |
| `LOCAL_REPORT_SLOT` | 5 | 5 | 0 | 0 |
| `HUMAN_CRITERION` | 20 | 20 | 0 | 20 |
| `BCD_PENDING_SLOT` | 13 | 13 | 0 | 0 |
| `NATIVE_CASE` | 44 | 44 | 0 | 1064 |

**Interpretação por tipo:**

- **B09:** a origem física, clone e cadeia de proveniência ainda exigem validação independente. Documento JSON não prova essa origem.
- **B10:** configuração/escopo do Windows Sandbox ainda sem inspeção independente do host. A L16 não executa Windows Sandbox.
- **B11:** `watch_unchanged` só demonstra invariância do escopo observado, não isolamento global de saves.
- **R07:** MapIDs reais e reservas não validados; vínculos públicos não criam mapas instalados.
- **R08:** direitos sobre assets de terceiros ainda não demonstrados; lista de arquivos não equivale a licença.
- **R09:** aprovação **regional global** ainda ausente, sem aresta por caso e sem criar 45º teste.
- **Cinco relatórios locais:** slots anônimos somente de acompanhamento, sem filename, ID de máquina, caminho real ou evidência recebida.
- **20 critérios L04:** cada um espera revisão humana independente e evidência física de origem autorizada, ainda ausentes.
- **13 slots contábeis B/C/D:** sem identidade específica ou atribuição física inventada; seguem contagem pendente.
- **44 casos G12:** cada caso exige QA nativa independente futura, gate humano adequado e autorização física. **43 Windows com B10/B11**, um Android/JoiPlay sem herança dos requisitos do Windows. Nenhuma execução ocorreu nesta fase.

Prioridades P0–P4 reproduzem somente a ordenação documental da L13 e **não** são a ordem de rodar QA, validar licenças ou executar Game.exe.

## Proveniência Git pública

| Fase | Commit de referência |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| L11 | `9d901a0cf21aa2742f731ee387a51f945bac8a5d` |
| L12 | `58b7f2fec9f66dee06d95676eec66fb2ded6a1de` |
| L13 | `1f12bcc86c10dcc934b024a0562cdadb65d5e2c2` |
| L14 | `11eda18f7225e16b13007c1eb955ccc3d7667b66` |
| L15 | `0192075fb02587c9f3d9db6b170500cba365251c` |

| Artefato público | SHA-1 de objeto Git |
| --- | --- |
| L13: `data/regions/sinnoh-l13-public-evidence-queue.json` | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |
| L14: `data/regions/sinnoh-l14-public-readiness-matrix.json` | `d882d6a20b1c01be33744f14ab7826af2fb6ef41` |
| L15: `data/regions/sinnoh-l15-public-consistency-diff.json` | `1a19883a3f0523add6aeaa4f78262b922a041e95` |

Os objetos e espelhos **públicos** L13/L14/L15 são fixados por SHA. A presença de um SHA-1 Git correto não verifica um jogo instalado, a autenticação humana de recibos, licenças, isolamento de saves, MapIDs ou o resultado de testes nativos. A referência do merge L16 é registrada na issue após a publicação, para evitar referência circular no próprio JSON.

## Entregáveis

- [Matriz L16 versionada](../data/regions/sinnoh-l16-public-exit-gates.json) e [espelho público do portal](../site/public/data/sinnoh-l16-public-exit-gates.json) com 88 registros, critérios de saída tipados e todos os indicadores pendentes.
- [Painel L16 somente leitura](../site/public/sinnoh-l16-criterios-saida.html), rota `/sinnoh-l16-criterios-saida.html`, filtros por ID, prioridade, categoria, plataforma, bloqueio e critério, além de consulta a requisitos de cada pedido.
- [Auditor fail-closed L16](../scripts/regions/audit_sinnoh_l16_exit_gates.py) que recalcula a matriz de L13/L14/L15, verifica os três blobs públicos e seus espelhos e reexecuta L15→L14→L13→L12→L11→L10→L09→L08→L07→L06→L05→L04→G12.
- [Testes Python L16](../tests/test_sinnoh_l16_exit_gates.py), incluindo 130 mutações negativas e dez verificações positivas de invariantes.
- [Testes Node do painel](../site/tests/sinnoh-l16-public-exit-gates.test.mjs) e [CI L16](../.github/workflows/sinnoh-l16-public-exit-gates.yml), com regressões L15–L00/G12, todos os testes dos painéis anteriores e build do portal.

## Os 20 critérios humanos L04 — todos sem aprovação

| Critério | Plataforma | Bloqueio | Situação |
| --- | --- | --- | --- |
| `B09_ORIGIN` | cross-platform | B09 | Pendente / sem signoff |
| `B09_CLONE` | cross-platform | B09 | Pendente / sem signoff |
| `B09_ASSETS` | cross-platform | B09 | Pendente / sem signoff |
| `B09_RECEIPT` | cross-platform | B09 | Pendente / sem signoff |
| `B10_LINK` | windows | B10 | Pendente / sem signoff |
| `B10_READONLY` | windows | B10 | Pendente / sem signoff |
| `B10_OFFLINE` | windows | B10 | Pendente / sem signoff |
| `B10_PLATFORM` | windows | B10 | Pendente / sem signoff |
| `B11_SESSION` | windows | B11 | Pendente / sem signoff |
| `B11_SCOPE` | windows | B11 | Pendente / sem signoff |
| `B11_DIFFERENCE` | windows | B11 | Pendente / sem signoff |
| `B11_LIMIT` | windows | B11 | Pendente / sem signoff |
| `R07_NATIVE` | cross-platform | R07 | Pendente / sem signoff |
| `R07_REGIONS` | cross-platform | R07 | Pendente / sem signoff |
| `R07_CONFLICT` | cross-platform | R07 | Pendente / sem signoff |
| `R07_TOPOLOGY` | cross-platform | R07 | Pendente / sem signoff |
| `R08_LICENSE` | cross-platform | R08 | Pendente / sem signoff |
| `R08_GRAPHICS` | cross-platform | R08 | Pendente / sem signoff |
| `R08_EVENTS` | cross-platform | R08 | Pendente / sem signoff |
| `R08_PBS` | cross-platform | R08 | Pendente / sem signoff |

## Os 44 casos nativos G12 — nenhuma execução

| # | Caso | Plataforma | Bloqueios | Critérios L04 vinculados | QA nativa |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `ball-TURTWIG` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 2 | `barry-TURTWIG-normal-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 3 | `barry-TURTWIG-normal-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 4 | `barry-TURTWIG-master-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 5 | `barry-TURTWIG-master-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 6 | `save-reload-TURTWIG` | windows | B09, B10, B11, R07, R08 | 18 | 0 / BLOQUEADO |
| 7 | `ball-CHIMCHAR` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 8 | `barry-CHIMCHAR-normal-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 9 | `barry-CHIMCHAR-normal-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 10 | `barry-CHIMCHAR-master-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 11 | `barry-CHIMCHAR-master-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 12 | `save-reload-CHIMCHAR` | windows | B09, B10, B11, R07, R08 | 18 | 0 / BLOQUEADO |
| 13 | `ball-PIPLUP` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 14 | `barry-PIPLUP-normal-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 15 | `barry-PIPLUP-normal-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 16 | `barry-PIPLUP-master-win` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 17 | `barry-PIPLUP-master-loss` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 18 | `save-reload-PIPLUP` | windows | B09, B10, B11, R07, R08 | 18 | 0 / BLOQUEADO |
| 19 | `warp-SN_BEDROOM_TO_1F` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 20 | `npc-SN_NPC_MOTHER` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 21 | `warp-SN_1F_TO_BEDROOM` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 22 | `warp-SN_1F_TO_TWINLEAF` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 23 | `warp-SN_TOWN_TO_HOME` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 26 | `npc-SN_NPC_BARRY_INTRO` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | windows | B09, B10, B11, R07, R08 | 20 | 0 / BLOQUEADO |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 40 | `regression-DECADES` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 41 | `regression-KANTO` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 42 | `regression-JOHTO` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 43 | `regression-HOENN` | windows | B09, B10, B11, R07, R08 | 19 | 0 / BLOQUEADO |
| 44 | `android-joi-play` | android | B09, R07, R08 | 12 | 0 / BLOQUEADO |

## Registro completo dos 88 pedidos L16

| Ordem | Pedido | Prioridade | Tipo | Códigos de critério de saída ainda não cumpridos | Estado |
| ---: | --- | --- | --- | --- | --- |
| 1 | `L13-BLOCKER-B09` | P0 | BLOCKER_DEPENDENCY | INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED · APPLICABLE_HUMAN_REVIEW_PENDING | `PENDING/BLOCKED` |
| 2 | `L13-BLOCKER-B10` | P0 | BLOCKER_DEPENDENCY | INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED · APPLICABLE_HUMAN_REVIEW_PENDING | `PENDING/BLOCKED` |
| 3 | `L13-BLOCKER-B11` | P0 | BLOCKER_DEPENDENCY | INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED · APPLICABLE_HUMAN_REVIEW_PENDING | `PENDING/BLOCKED` |
| 4 | `L13-BLOCKER-R07` | P0 | BLOCKER_DEPENDENCY | INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED · APPLICABLE_HUMAN_REVIEW_PENDING | `PENDING/BLOCKED` |
| 5 | `L13-BLOCKER-R08` | P0 | BLOCKER_DEPENDENCY | INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED · APPLICABLE_HUMAN_REVIEW_PENDING | `PENDING/BLOCKED` |
| 6 | `L13-GLOBAL-R09` | P0 | GLOBAL_REGIONAL_GATE | REGIONAL_R09_SIGNOFF_PENDING | `PENDING/BLOCKED` |
| 7 | `L13-REPORT-01` | P1 | LOCAL_REPORT_SLOT | ANONYMOUS_REPORT_SLOT_UNASSIGNED · LOCAL_REPORT_NOT_RECEIVED | `PENDING/BLOCKED` |
| 8 | `L13-REPORT-02` | P1 | LOCAL_REPORT_SLOT | ANONYMOUS_REPORT_SLOT_UNASSIGNED · LOCAL_REPORT_NOT_RECEIVED | `PENDING/BLOCKED` |
| 9 | `L13-REPORT-03` | P1 | LOCAL_REPORT_SLOT | ANONYMOUS_REPORT_SLOT_UNASSIGNED · LOCAL_REPORT_NOT_RECEIVED | `PENDING/BLOCKED` |
| 10 | `L13-REPORT-04` | P1 | LOCAL_REPORT_SLOT | ANONYMOUS_REPORT_SLOT_UNASSIGNED · LOCAL_REPORT_NOT_RECEIVED | `PENDING/BLOCKED` |
| 11 | `L13-REPORT-05` | P1 | LOCAL_REPORT_SLOT | ANONYMOUS_REPORT_SLOT_UNASSIGNED · LOCAL_REPORT_NOT_RECEIVED | `PENDING/BLOCKED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 13 | `L13-HUMAN-B09_CLONE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 14 | `L13-HUMAN-B09_ASSETS` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 16 | `L13-HUMAN-B10_LINK` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 17 | `L13-HUMAN-B10_READONLY` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 20 | `L13-HUMAN-B11_SESSION` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 21 | `L13-HUMAN-B11_SCOPE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 23 | `L13-HUMAN-B11_LIMIT` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 24 | `L13-HUMAN-R07_NATIVE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 25 | `L13-HUMAN-R07_REGIONS` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 28 | `L13-HUMAN-R08_LICENSE` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 30 | `L13-HUMAN-R08_EVENTS` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 31 | `L13-HUMAN-R08_PBS` | P2 | HUMAN_CRITERION | INDEPENDENT_L04_SIGNOFF_PENDING · PHYSICAL_EVIDENCE_NOT_ACCEPTED | `PENDING/BLOCKED` |
| 32 | `L13-BCD-01` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 33 | `L13-BCD-02` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 34 | `L13-BCD-03` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 35 | `L13-BCD-04` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 36 | `L13-BCD-05` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 37 | `L13-BCD-06` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 38 | `L13-BCD-07` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 39 | `L13-BCD-08` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 40 | `L13-BCD-09` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 41 | `L13-BCD-10` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 42 | `L13-BCD-11` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 43 | `L13-BCD-12` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 44 | `L13-BCD-13` | P3 | BCD_PENDING_SLOT | ANONYMOUS_BCD_SLOT_UNASSIGNED · BCD_APPROVAL_PENDING | `PENDING/BLOCKED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 84 | `L13-NATIVE-regression-DECADES` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 85 | `L13-NATIVE-regression-KANTO` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 86 | `L13-NATIVE-regression-JOHTO` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 87 | `L13-NATIVE-regression-HOENN` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |
| 88 | `L13-NATIVE-android-joi-play` | P4 | NATIVE_CASE | NATIVE_G12_QA_NOT_EXECUTED · APPLICABLE_HUMAN_GATES_PENDING · PHYSICAL_AUTHORIZATION_ABSENT | `PENDING/BLOCKED` |

## Auditoria pública permitida

```sh
python scripts/regions/audit_sinnoh_l16_exit_gates.py
python -m unittest discover -s tests -p 'test_sinnoh_l16_exit_gates.py' -v
```

O auditor aceita apenas caminhos pré-definidos dentro dos metadados públicos do GitHub. Ele rejeita argumentos de host, arquivos externos, aprovações forjadas, alterações nos espelhos ou nas referências de commits. Não acessa PC, Game.exe, Windows Sandbox, JoiPlay, saves, ROM, ZIP/PNG privados ou licenças pessoais. O painel não oferece upload, mudança de estado, aceitação de evidência nem acionamento de QA.
