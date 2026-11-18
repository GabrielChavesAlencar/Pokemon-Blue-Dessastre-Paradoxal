# Sinnoh L19 — Consolidação pública das 88 lacunas pendentes

**Issue #216 · somente GitHub público.** Base imutável: L18, PR #215, merge `38ff6e635287f84464e1371160f3a06ae8dba953`.

A L19 consolida cobertura, referências e bloqueios existentes **sem alterar o jogo, recolher evidências físicas ou aprovar qualquer requisito**. Git SHA-1, documentos e testes automatizados do próprio portal comprovam apenas integridade documental pública.

## Indicadores imutáveis

| Item | Estado documental |
| --- | --- |
| Pedidos consolidados | **88/88 PENDING/BLOCKED** |
| Lacunas abertas / fechadas | **88 / 0** |
| Critérios de saída cumpridos | **0/88** |
| Revisões independentes aprovadas | **0/88** |
| Vínculos entre IDs públicos | **1.084** = 846 caso→critério + 218 caso→bloqueio + 20 critério→bloqueio |
| Slots anônimos sem atribuição física | **18** (5 relatórios locais + 13 B/C/D) |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos aprovados L04 | **0/20** |
| QA nativa G12 executada | **0/44** (43 Windows, 1 Android) |
| B/C/D | **0/13** |
| R07/R08/R09 | **PENDING** |
| Região Sinnoh | **planned / não jogável** |

## Grupos e cobertura

| Grupo público | Pedidos | Bloqueados | Vínculos documentais | Signoffs independentes |
| --- | ---: | ---: | ---: | ---: |
| `BLOCKER_DEPENDENCY` | 5 | 5 | 0 | 0 |
| `GLOBAL_REGIONAL_GATE` | 1 | 1 | 0 | 0 |
| `LOCAL_REPORT_SLOT` | 5 | 5 | 0 | 0 |
| `HUMAN_CRITERION` | 20 | 20 | 20 | 0 |
| `BCD_PENDING_SLOT` | 13 | 13 | 0 | 0 |
| `NATIVE_CASE` | 44 | 44 | 1064 | 0 |

**Bloqueios específicos:** B09 (proveniência física), B10 (Windows Sandbox), B11 (isolamento global de saves), R07 (MapIDs reais) e R08 (direitos sobre assets) permanecem pendentes. **R09** é gate regional **global**, não um sexto bloqueio por caso, sem novas arestas a G12.

O indicador `watch_unchanged` limita-se ao seu escopo observado e não prova isolamento global B11. As 43 verificações Windows dependem de B10/B11, mas o único caso Android não herda esses gates. Metadados de prioridades **P0–P4** são apenas ordenação documental, não instruções para QA.

## Proveniência: commits públicos L07–L18

| Etapa | Commit fixado |
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
| L18 | `38ff6e635287f84464e1371160f3a06ae8dba953` |

## Blobs Git públicos ancorados

| Documento | SHA-1 do objeto Git |
| --- | --- |
| L13 `data/regions/sinnoh-l13-public-evidence-queue.json` | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |
| L14 `data/regions/sinnoh-l14-public-readiness-matrix.json` | `d882d6a20b1c01be33744f14ab7826af2fb6ef41` |
| L15 `data/regions/sinnoh-l15-public-consistency-diff.json` | `1a19883a3f0523add6aeaa4f78262b922a041e95` |
| L16 `data/regions/sinnoh-l16-public-exit-gates.json` | `c9e3047106d7860bb966b5927a1fd8304506d395` |
| L17 `data/regions/sinnoh-l17-public-review-index.json` | `273feb1460b9200cd3c0af63cf4ebb092b8691df` |
| L18 `data/regions/sinnoh-l18-public-review-gaps.json` | `649e85b2daef7635d00e19201ad5f39cc43c5c90` |

O SHA-1 de objeto Git só valida os bytes públicos comparados pelo auditor. **Não confere direitos R08, MapIDs R07, proveniência física B09, isolamento B11, autoria independente ou aprovação de QA**. Nenhum arquivo ZIP/ROM/PNG, save, licença privada ou anexo foi solicitado ou aberto.

## Entregáveis L19

- [Relatório público L19 JSON](../data/regions/sinnoh-l19-public-gap-consolidation.json) e [espelho do portal](../site/public/data/sinnoh-l19-public-gap-consolidation.json).
- [Página L19 somente leitura](../site/public/sinnoh-l19-consolidacao.html), caminho `/sinnoh-l19-consolidacao.html`: pesquisa, filtros por prioridade P0–P4, grupo, plataforma, bloqueio, tipo de lacuna e detalhe por ID. Nenhum campo de upload nem gravação.
- [Auditor fail-closed L19](../scripts/regions/audit_sinnoh_l19_consolidation.py): deriva relatório de L18, verifica os dois objetos Git L18 e espelhos, reexecuta auditores da cadeia pública, rejeita mudanças de estados, nomes, vínculos e signoffs fictícios.
- [Testes negativos e de contrato L19](../tests/test_sinnoh_l19_consolidation.py) e [testes Node do portal](../site/tests/sinnoh-l19-consolidation.test.mjs).
- [Workflow CI L19](../.github/workflows/sinnoh-l19-public-gap-consolidation.yml): auditoria L19, regressões L18–L00/G12 e testes do portal mais build completo.

## Lista consolidada — 88 pedidos sem avanço humano ou nativo

| Ordem | Pedido | Prioridade documental | Plataforma | Tipos de lacuna | Vínculos | Status |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | `L13-BLOCKER-B09` | P0 | cross-platform | 2 | 0 | `PENDING/BLOCKED` |
| 2 | `L13-BLOCKER-B10` | P0 | windows | 2 | 0 | `PENDING/BLOCKED` |
| 3 | `L13-BLOCKER-B11` | P0 | windows | 2 | 0 | `PENDING/BLOCKED` |
| 4 | `L13-BLOCKER-R07` | P0 | cross-platform | 2 | 0 | `PENDING/BLOCKED` |
| 5 | `L13-BLOCKER-R08` | P0 | cross-platform | 2 | 0 | `PENDING/BLOCKED` |
| 6 | `L13-GLOBAL-R09` | P0 | global | 1 | 0 | `PENDING/BLOCKED` |
| 7 | `L13-REPORT-01` | P1 | unassigned | 2 | 0 | `PENDING/BLOCKED` |
| 8 | `L13-REPORT-02` | P1 | unassigned | 2 | 0 | `PENDING/BLOCKED` |
| 9 | `L13-REPORT-03` | P1 | unassigned | 2 | 0 | `PENDING/BLOCKED` |
| 10 | `L13-REPORT-04` | P1 | unassigned | 2 | 0 | `PENDING/BLOCKED` |
| 11 | `L13-REPORT-05` | P1 | unassigned | 2 | 0 | `PENDING/BLOCKED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 13 | `L13-HUMAN-B09_CLONE` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 14 | `L13-HUMAN-B09_ASSETS` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 16 | `L13-HUMAN-B10_LINK` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 17 | `L13-HUMAN-B10_READONLY` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 20 | `L13-HUMAN-B11_SESSION` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 21 | `L13-HUMAN-B11_SCOPE` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 23 | `L13-HUMAN-B11_LIMIT` | P2 | windows | 2 | 1 | `PENDING/BLOCKED` |
| 24 | `L13-HUMAN-R07_NATIVE` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 25 | `L13-HUMAN-R07_REGIONS` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 28 | `L13-HUMAN-R08_LICENSE` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 30 | `L13-HUMAN-R08_EVENTS` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 31 | `L13-HUMAN-R08_PBS` | P2 | cross-platform | 2 | 1 | `PENDING/BLOCKED` |
| 32 | `L13-BCD-01` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 33 | `L13-BCD-02` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 34 | `L13-BCD-03` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 35 | `L13-BCD-04` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 36 | `L13-BCD-05` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 37 | `L13-BCD-06` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 38 | `L13-BCD-07` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 39 | `L13-BCD-08` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 40 | `L13-BCD-09` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 41 | `L13-BCD-10` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 42 | `L13-BCD-11` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 43 | `L13-BCD-12` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 44 | `L13-BCD-13` | P3 | global | 2 | 0 | `PENDING/BLOCKED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | P4 | windows | 3 | 23 | `PENDING/BLOCKED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | P4 | windows | 3 | 23 | `PENDING/BLOCKED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | P4 | windows | 3 | 23 | `PENDING/BLOCKED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | P4 | windows | 3 | 25 | `PENDING/BLOCKED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 84 | `L13-NATIVE-regression-DECADES` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 85 | `L13-NATIVE-regression-KANTO` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 86 | `L13-NATIVE-regression-JOHTO` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 87 | `L13-NATIVE-regression-HOENN` | P4 | windows | 3 | 24 | `PENDING/BLOCKED` |
| 88 | `L13-NATIVE-android-joi-play` | P4 | android | 3 | 15 | `PENDING/BLOCKED` |

## Auditoria pública permitida

```sh
python scripts/regions/audit_sinnoh_l19_consolidation.py
python -m unittest discover -s tests -p 'test_sinnoh_l19_consolidation.py' -v
```

Não são executados Game.exe, Windows Sandbox, JoiPlay ou saves. A conclusão da L19 só certifica os documentos públicos, não altera B/C/D, R07/R08/R09, aceitação humana, direitos ou jogabilidade.
