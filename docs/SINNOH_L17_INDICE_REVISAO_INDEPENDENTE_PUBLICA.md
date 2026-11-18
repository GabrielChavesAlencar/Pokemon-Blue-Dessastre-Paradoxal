# Sinnoh L17 — Índice de orientação para revisão independente futura

**Issue #211 · somente metadados públicos GitHub.** A L17 oferece orientação de leitura para os critérios de saída publicados na L16, sem coletar arquivos privados, nomear revisores, produzir aprovações ou executar jogos.

## Resultado imutável

| Indicador | Estado |
| --- | --- |
| Pedidos públicos | **88/88 PENDING / BLOCKED** |
| Revisões independentes realizadas | **0/88** |
| Critérios de saída L16 atendidos | **0/88** |
| Vínculos exclusivamente documentais | **1.084/1.084** |
| Posições anônimas sem identidade | **18** (5 relatórios, 13 B/C/D) |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos aprovados | **0/20** |
| QA nativa executada | **0/44** (43 Windows, 1 Android) |
| B/C/D aprovados | **0/13** |
| R07/R08/R09 | **PENDING** |
| Sinnoh | **planned / não jogável** |

As prioridades **P0–P4** só ordenam acompanhamento documental: não constituem ordem de QA, direitos, execução, instalação ou autorização.

## Escopos para futura revisão humana independente

| Tipo de pedido | Total | PENDING/BLOCKED | Vínculos públicos | Revisões concluídas |
| --- | ---: | ---: | ---: | ---: |
| `BLOCKER_DEPENDENCY` | 5 | 5 | 0 | 0 |
| `GLOBAL_REGIONAL_GATE` | 1 | 1 | 0 | 0 |
| `LOCAL_REPORT_SLOT` | 5 | 5 | 0 | 0 |
| `HUMAN_CRITERION` | 20 | 20 | 20 | 0 |
| `BCD_PENDING_SLOT` | 13 | 13 | 0 | 0 |
| `NATIVE_CASE` | 44 | 44 | 1064 | 0 |

- **B09:** a proveniência independente da fonte física e clone ainda não foi demonstrada.
- **B10:** não foi revisada independentemente a configuração física do Windows Sandbox.
- **B11:** `watch_unchanged` observa apenas seu próprio escopo; **não prova isolamento global de saves**.
- **R07:** reservas reais e MapIDs regionais ainda não aprovados.
- **R08:** direitos sobre ativos/gráficos/eventos/PBS não demonstrados.
- **R09:** gate **regional global** pendente, sem arestas extras por caso.
- **Relatórios locais (5 slots):** apenas posições contábeis anônimas sem nome, origem, caminho ou recibo recebido.
- **Critérios L04 (20):** falta revisão humana independente real e signoff — nenhum atribuído ou presumido.
- **B/C/D (13 slots):** posições contábeis sem identificação/atribuição física.
- **G12 (44 casos):** nenhum teste nativo executado. A trilha de 43 casos Windows permanece distinta da trilha Android de 1 caso; Android **não herda** B10/B11.

O objetivo da L17 é **consultar o que está faltando**, não solicitar arquivos privados por intermédio deste site.

## Proveniência imutável de metadados públicos

| Etapa | Commit GitHub de referência |
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

| JSON público | Hash de objeto Git |
| --- | --- |
| `data/regions/sinnoh-l13-public-evidence-queue.json` (L13) | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |
| `data/regions/sinnoh-l14-public-readiness-matrix.json` (L14) | `d882d6a20b1c01be33744f14ab7826af2fb6ef41` |
| `data/regions/sinnoh-l15-public-consistency-diff.json` (L15) | `1a19883a3f0523add6aeaa4f78262b922a041e95` |
| `data/regions/sinnoh-l16-public-exit-gates.json` (L16) | `c9e3047106d7860bb966b5927a1fd8304506d395` |

Os hashes de objetos Git provam somente os bytes públicos versionados no repositório. Não comprovam fonte física, ROM, licenças, saves, QA, MapIDs ou signoffs.

## Entregas verificáveis

- [Índice público L17 versionado](../data/regions/sinnoh-l17-public-review-index.json) e [espelho estático do portal](../site/public/data/sinnoh-l17-public-review-index.json).
- [Página L17 somente leitura](../site/public/sinnoh-l17-revisao-independente.html), rota `/sinnoh-l17-revisao-independente.html`; filtros por pedido, prioridade, tipo, plataforma, bloqueio e critério. Exibe grupos, relações públicas e orientação da L16 sem campos de upload, identidade de revisor ou aprovação.
- [Auditor L17 fail-closed](../scripts/regions/audit_sinnoh_l17_public_review.py): reconstitui o índice a partir da L16, verifica os hashes públicos L13–L16, a cadeia documental de auditores anteriores e ambos os espelhos. Qualquer falseamento de signoff, estado ou dependência faz o processo falhar.
- [Testes Python L17](../tests/test_sinnoh_l17_public_review.py) com 127 testes sintéticos negativos e dez testes positivos (sem Game.exe ou save).
- [Testes Node L17](../site/tests/sinnoh-l17-public-review.test.mjs) e [CI L17](../.github/workflows/sinnoh-l17-public-review-index.yml) com regressões L16–L00/G12, os testes do portal e build completo.

## Critérios L04 que permanecem sem revisão

| Critério | Plataforma | Bloqueios | Resultado |
| --- | --- | --- | --- |
| `B09_ORIGIN` | cross-platform | B09 | Não revisado |
| `B09_CLONE` | cross-platform | B09 | Não revisado |
| `B09_ASSETS` | cross-platform | B09 | Não revisado |
| `B09_RECEIPT` | cross-platform | B09 | Não revisado |
| `B10_LINK` | windows | B10 | Não revisado |
| `B10_READONLY` | windows | B10 | Não revisado |
| `B10_OFFLINE` | windows | B10 | Não revisado |
| `B10_PLATFORM` | windows | B10 | Não revisado |
| `B11_SESSION` | windows | B11 | Não revisado |
| `B11_SCOPE` | windows | B11 | Não revisado |
| `B11_DIFFERENCE` | windows | B11 | Não revisado |
| `B11_LIMIT` | windows | B11 | Não revisado |
| `R07_NATIVE` | cross-platform | R07 | Não revisado |
| `R07_REGIONS` | cross-platform | R07 | Não revisado |
| `R07_CONFLICT` | cross-platform | R07 | Não revisado |
| `R07_TOPOLOGY` | cross-platform | R07 | Não revisado |
| `R08_LICENSE` | cross-platform | R08 | Não revisado |
| `R08_GRAPHICS` | cross-platform | R08 | Não revisado |
| `R08_EVENTS` | cross-platform | R08 | Não revisado |
| `R08_PBS` | cross-platform | R08 | Não revisado |

## Os 88 pedidos L17 — todos sem signoff

| Ordem | Pedido | Prioridade | Plataforma | Códigos de saída | Vínculos públicos | Revisão |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | `L13-BLOCKER-B09` | P0 | cross-platform | 2 | 0 | `NOT_REVIEWED` |
| 2 | `L13-BLOCKER-B10` | P0 | windows | 2 | 0 | `NOT_REVIEWED` |
| 3 | `L13-BLOCKER-B11` | P0 | windows | 2 | 0 | `NOT_REVIEWED` |
| 4 | `L13-BLOCKER-R07` | P0 | cross-platform | 2 | 0 | `NOT_REVIEWED` |
| 5 | `L13-BLOCKER-R08` | P0 | cross-platform | 2 | 0 | `NOT_REVIEWED` |
| 6 | `L13-GLOBAL-R09` | P0 | global | 1 | 0 | `NOT_REVIEWED` |
| 7 | `L13-REPORT-01` | P1 | unassigned | 2 | 0 | `NOT_REVIEWED` |
| 8 | `L13-REPORT-02` | P1 | unassigned | 2 | 0 | `NOT_REVIEWED` |
| 9 | `L13-REPORT-03` | P1 | unassigned | 2 | 0 | `NOT_REVIEWED` |
| 10 | `L13-REPORT-04` | P1 | unassigned | 2 | 0 | `NOT_REVIEWED` |
| 11 | `L13-REPORT-05` | P1 | unassigned | 2 | 0 | `NOT_REVIEWED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 13 | `L13-HUMAN-B09_CLONE` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 14 | `L13-HUMAN-B09_ASSETS` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 16 | `L13-HUMAN-B10_LINK` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 17 | `L13-HUMAN-B10_READONLY` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 20 | `L13-HUMAN-B11_SESSION` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 21 | `L13-HUMAN-B11_SCOPE` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 23 | `L13-HUMAN-B11_LIMIT` | P2 | windows | 2 | 1 | `NOT_REVIEWED` |
| 24 | `L13-HUMAN-R07_NATIVE` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 25 | `L13-HUMAN-R07_REGIONS` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 28 | `L13-HUMAN-R08_LICENSE` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 30 | `L13-HUMAN-R08_EVENTS` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 31 | `L13-HUMAN-R08_PBS` | P2 | cross-platform | 2 | 1 | `NOT_REVIEWED` |
| 32 | `L13-BCD-01` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 33 | `L13-BCD-02` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 34 | `L13-BCD-03` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 35 | `L13-BCD-04` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 36 | `L13-BCD-05` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 37 | `L13-BCD-06` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 38 | `L13-BCD-07` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 39 | `L13-BCD-08` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 40 | `L13-BCD-09` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 41 | `L13-BCD-10` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 42 | `L13-BCD-11` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 43 | `L13-BCD-12` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 44 | `L13-BCD-13` | P3 | global | 2 | 0 | `NOT_REVIEWED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | P4 | windows | 3 | 23 | `NOT_REVIEWED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | P4 | windows | 3 | 23 | `NOT_REVIEWED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | P4 | windows | 3 | 23 | `NOT_REVIEWED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | P4 | windows | 3 | 25 | `NOT_REVIEWED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 84 | `L13-NATIVE-regression-DECADES` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 85 | `L13-NATIVE-regression-KANTO` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 86 | `L13-NATIVE-regression-JOHTO` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 87 | `L13-NATIVE-regression-HOENN` | P4 | windows | 3 | 24 | `NOT_REVIEWED` |
| 88 | `L13-NATIVE-android-joi-play` | P4 | android | 3 | 15 | `NOT_REVIEWED` |

## Comandos de auditoria pública opcional

```sh
python scripts/regions/audit_sinnoh_l17_public_review.py
python -m unittest discover -s tests -p 'test_sinnoh_l17_public_review.py' -v
```

Esses comandos só verificam os arquivos públicos do repositório; não leem nem editam arquivos de host, ROM, Game.exe, Windows Sandbox, JoiPlay, saves ou licenças privadas. Não há endpoint de submissão de provas ou atribuição humana no painel.
