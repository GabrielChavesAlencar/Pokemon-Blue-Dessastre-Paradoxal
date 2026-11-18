# Sinnoh L18 — Lacunas públicas de revisão e próximos passos documentais

**Issue #214 · fase exclusivamente documental baseada no PR #212/L17.** Este relatório organiza metadados Git públicos em 88 orientações de leitura; não recebe ou verifica arquivos privados, não atribui revisores humanos e não executa QA nativa.

## Resumo sem aprovações artificiais

| Indicador | Resultado |
| --- | --- |
| Pedidos e lacunas registradas | **88/88 PENDING/BLOCKED** |
| Lacunas abertas | **88** |
| Lacunas encerradas | **0** |
| Revisões independentes concluídas | **0/88** |
| Critérios de saída L16 cumpridos | **0/88** |
| Relações públicas preservadas | **1.084** = 846 caso→critério + 218 caso→bloqueio + 20 critério→bloqueio |
| Posições contábeis anônimas | **18** (5 relatórios, 13 B/C/D), todas sem identidade/atribuição |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos aprovados | **0/20** |
| Casos G12 executados | **0/44** (Windows 0/43, Android/JoiPlay 0/1) |
| B/C/D aprovados | **0/13** |
| R07 / R08 / R09 | **PENDING** |
| Sinnoh | **planned / não jogável** |

## Pendências por grupo

| Grupo | Pedidos | Bloqueados | Relações documentais | Revisões concluídas |
| --- | ---: | ---: | ---: | ---: |
| `BLOCKER_DEPENDENCY` | 5 | 5 | 0 | 0 |
| `GLOBAL_REGIONAL_GATE` | 1 | 1 | 0 | 0 |
| `LOCAL_REPORT_SLOT` | 5 | 5 | 0 | 0 |
| `HUMAN_CRITERION` | 20 | 20 | 20 | 0 |
| `BCD_PENDING_SLOT` | 13 | 13 | 0 | 0 |
| `NATIVE_CASE` | 44 | 44 | 1064 | 0 |

## Tipos de lacuna e próximo passo permitido — organização pública, não QA

| Grupo | Tipos de lacuna registrados | Próximo passo documental |
| --- | --- | --- |
| `BLOCKER_DEPENDENCY` | `UNVERIFIED_PUBLIC_DEPENDENCY`, `INDEPENDENT_HUMAN_GATE_PENDING` | Conferir e organizar somente as referências públicas do bloqueio; manter a validação independente física fora desta fase. |
| `GLOBAL_REGIONAL_GATE` | `GLOBAL_REGIONAL_SIGNOFF_NOT_REVIEWED` | Documentar R09 como decisão regional futura isolada, sem relacionar o gate a novos casos G12. |
| `LOCAL_REPORT_SLOT` | `ANONYMOUS_LOCAL_REPORT_MISSING`, `SLOT_IDENTITY_UNASSIGNED` | Manter cinco posições contábeis sem inventar relatórios, origens, nomes ou anexos. |
| `HUMAN_CRITERION` | `INDEPENDENT_HUMAN_REVIEW_MISSING`, `NO_PHYSICAL_EVIDENCE_ACCEPTED` | Conferir a relação pública entre critério L04 e seus bloqueios; não preencher revisão ou signoff. |
| `BCD_PENDING_SLOT` | `ANONYMOUS_BCD_POSITION_UNASSIGNED`, `BCD_SIGNOFF_PENDING` | Preservar 13 posições B/C/D como pendências anônimas sem mapear para conteúdo físico. |
| `NATIVE_CASE` | `NATIVE_QA_NOT_EXECUTED`, `HUMAN_GATES_PENDING`, `NO_NATIVE_EXECUTION_AUTHORIZATION` | Conferir a cobertura pública G12 de casos, plataforma e critérios L04; não executar QA nativa. |

**Interpretação de gates não atendidos:** B09 permanece dependente de proveniência física independente, B10 de configuração física isolada do Windows Sandbox e B11 de comprovação de isolamento global real de saves. O indicador público `watch_unchanged` não prova esse isolamento. R07 não assegura MapIDs reais, R08 não assegura direitos sobre ativos, e **R09 é um único gate regional global sem novas arestas por caso**.

Os **43 casos Windows** são relacionados aos gates B10 e B11. O único caso **Android** permanece separado e não recebe B10/B11 Windows por inferência. Nenhum teste nativo ou instalação foi executado nesta entrega.

**P0–P4** são prioridades exclusivamente documentais, não instruções para rodar testes. Os 5 relatórios locais e 13 slots B/C/D são 18 posições anônimas sem nomes, caminhos físicos, recibos ou associação presumida.

## Referências públicas imutáveis

| Etapa | Commit Git |
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
| L16 | `709776022679dc5831748ea4ed2254c6ced1da84` |
| L17 | `eb1333953d02d319e9b44a96c23fe2e071bd2a2e` |

| Fonte pública | SHA-1 do objeto Git |
| --- | --- |
| L13 · `data/regions/sinnoh-l13-public-evidence-queue.json` | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |
| L14 · `data/regions/sinnoh-l14-public-readiness-matrix.json` | `d882d6a20b1c01be33744f14ab7826af2fb6ef41` |
| L15 · `data/regions/sinnoh-l15-public-consistency-diff.json` | `1a19883a3f0523add6aeaa4f78262b922a041e95` |
| L16 · `data/regions/sinnoh-l16-public-exit-gates.json` | `c9e3047106d7860bb966b5927a1fd8304506d395` |
| L17 · `data/regions/sinnoh-l17-public-review-index.json` | `273feb1460b9200cd3c0af63cf4ebb092b8691df` |

O SHA Git verifica somente a integridade do objeto público. Não valida a fonte física, licença, save, execução do jogo ou julgamento humano. O hash do merge L18 será registrado na issue após a integração, evitando referência circular no próprio arquivo.

## Artefatos de entrega

- [Relatório L18 versionado](../data/regions/sinnoh-l18-public-review-gaps.json), espelho [JSON estático do portal](../site/public/data/sinnoh-l18-public-review-gaps.json).
- [Painel L18 navegável e read-only](../site/public/sinnoh-l18-lacunas-revisao.html), na rota `/sinnoh-l18-lacunas-revisao.html`, com filtros por ID, prioridade, categoria, plataforma, bloqueio e tipo de lacuna. Só consulta documentos públicos; não há upload, signoff ou ação de execução.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l18_review_gaps.py), que reconstrói o relatório exato a partir da L17, verifica blob Git L17 e espelho e reexecuta a cadeia L16→L00/G12.
- [Testes Python L18](../tests/test_sinnoh_l18_review_gaps.py), incluindo 133 mutações negativas sintéticas e dez verificações de referência, identidade, gates e isolamento.
- [Testes Node L18](../site/tests/sinnoh-l18-review-gaps.test.mjs) e [workflow CI L18](../.github/workflows/sinnoh-l18-public-review-gaps.yml) com regressões L17–L00/G12, testes Node anteriores e build completo do portal.

## Todos os 88 pedidos — lacunas abertas

| Ordem | Pedido | Prioridade | Plataforma | Lacunas públicas | Links | Status |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | `L13-BLOCKER-B09` | P0 | cross-platform | UNVERIFIED_PUBLIC_DEPENDENCY · INDEPENDENT_HUMAN_GATE_PENDING | 0 | `PENDING/BLOCKED` |
| 2 | `L13-BLOCKER-B10` | P0 | windows | UNVERIFIED_PUBLIC_DEPENDENCY · INDEPENDENT_HUMAN_GATE_PENDING | 0 | `PENDING/BLOCKED` |
| 3 | `L13-BLOCKER-B11` | P0 | windows | UNVERIFIED_PUBLIC_DEPENDENCY · INDEPENDENT_HUMAN_GATE_PENDING | 0 | `PENDING/BLOCKED` |
| 4 | `L13-BLOCKER-R07` | P0 | cross-platform | UNVERIFIED_PUBLIC_DEPENDENCY · INDEPENDENT_HUMAN_GATE_PENDING | 0 | `PENDING/BLOCKED` |
| 5 | `L13-BLOCKER-R08` | P0 | cross-platform | UNVERIFIED_PUBLIC_DEPENDENCY · INDEPENDENT_HUMAN_GATE_PENDING | 0 | `PENDING/BLOCKED` |
| 6 | `L13-GLOBAL-R09` | P0 | global | GLOBAL_REGIONAL_SIGNOFF_NOT_REVIEWED | 0 | `PENDING/BLOCKED` |
| 7 | `L13-REPORT-01` | P1 | unassigned | ANONYMOUS_LOCAL_REPORT_MISSING · SLOT_IDENTITY_UNASSIGNED | 0 | `PENDING/BLOCKED` |
| 8 | `L13-REPORT-02` | P1 | unassigned | ANONYMOUS_LOCAL_REPORT_MISSING · SLOT_IDENTITY_UNASSIGNED | 0 | `PENDING/BLOCKED` |
| 9 | `L13-REPORT-03` | P1 | unassigned | ANONYMOUS_LOCAL_REPORT_MISSING · SLOT_IDENTITY_UNASSIGNED | 0 | `PENDING/BLOCKED` |
| 10 | `L13-REPORT-04` | P1 | unassigned | ANONYMOUS_LOCAL_REPORT_MISSING · SLOT_IDENTITY_UNASSIGNED | 0 | `PENDING/BLOCKED` |
| 11 | `L13-REPORT-05` | P1 | unassigned | ANONYMOUS_LOCAL_REPORT_MISSING · SLOT_IDENTITY_UNASSIGNED | 0 | `PENDING/BLOCKED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 13 | `L13-HUMAN-B09_CLONE` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 14 | `L13-HUMAN-B09_ASSETS` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 16 | `L13-HUMAN-B10_LINK` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 17 | `L13-HUMAN-B10_READONLY` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 20 | `L13-HUMAN-B11_SESSION` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 21 | `L13-HUMAN-B11_SCOPE` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 23 | `L13-HUMAN-B11_LIMIT` | P2 | windows | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 24 | `L13-HUMAN-R07_NATIVE` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 25 | `L13-HUMAN-R07_REGIONS` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 28 | `L13-HUMAN-R08_LICENSE` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 30 | `L13-HUMAN-R08_EVENTS` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 31 | `L13-HUMAN-R08_PBS` | P2 | cross-platform | INDEPENDENT_HUMAN_REVIEW_MISSING · NO_PHYSICAL_EVIDENCE_ACCEPTED | 1 | `PENDING/BLOCKED` |
| 32 | `L13-BCD-01` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 33 | `L13-BCD-02` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 34 | `L13-BCD-03` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 35 | `L13-BCD-04` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 36 | `L13-BCD-05` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 37 | `L13-BCD-06` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 38 | `L13-BCD-07` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 39 | `L13-BCD-08` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 40 | `L13-BCD-09` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 41 | `L13-BCD-10` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 42 | `L13-BCD-11` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 43 | `L13-BCD-12` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 44 | `L13-BCD-13` | P3 | global | ANONYMOUS_BCD_POSITION_UNASSIGNED · BCD_SIGNOFF_PENDING | 0 | `PENDING/BLOCKED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 23 | `PENDING/BLOCKED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 23 | `PENDING/BLOCKED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 23 | `PENDING/BLOCKED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 25 | `PENDING/BLOCKED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 84 | `L13-NATIVE-regression-DECADES` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 85 | `L13-NATIVE-regression-KANTO` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 86 | `L13-NATIVE-regression-JOHTO` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 87 | `L13-NATIVE-regression-HOENN` | P4 | windows | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 24 | `PENDING/BLOCKED` |
| 88 | `L13-NATIVE-android-joi-play` | P4 | android | NATIVE_QA_NOT_EXECUTED · HUMAN_GATES_PENDING · NO_NATIVE_EXECUTION_AUTHORIZATION | 15 | `PENDING/BLOCKED` |

## Auditoria documental segura

```sh
python scripts/regions/audit_sinnoh_l18_review_gaps.py
python -m unittest discover -s tests -p 'test_sinnoh_l18_review_gaps.py' -v
```

Os comandos só leem metadados do repositório e recusam argumentos de caminhos externos. Não acessam PC, Game.exe, Windows Sandbox, JoiPlay, saves, ROM, ZIPs, imagens ou licenças privadas. **O fechamento da fase L18, se os checks passarem, registra apenas validação documental pública.**
