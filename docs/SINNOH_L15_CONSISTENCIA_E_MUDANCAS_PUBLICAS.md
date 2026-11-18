# Sinnoh L15 — Consistência e mudanças documentais entre L13/L14

**Issue #205 — exclusivamente GitHub público, sem evidência privada.** O relatório L15 compara dois artefatos públicos: a fila L13 e a matriz documental L14. A verificação de consistência de JSON não representa revisão humana independente nem execução de um jogo.

## Resultado: identidades estáveis, projeção pública adicional

| Comparação | Quantidade | Significado |
| --- | ---: | --- |
| Pedidos L13 e L14 com mesmo ID/ordem | **88/88** | Corresponde à mesma fila pública |
| Mudanças em IDs, prioridade P0–P4, plataforma ou `PENDING` | **0** | Não houve avanço de status |
| Novas *relações entre pedidos* representadas na L14 | **1.084** | Projeção de 846 relações caso→critério, 218 caso→bloqueio e 20 critério→bloqueio já existentes como metadados na trilha L11 |
| Provas físicas ou revisões humanas recebidas/aprovadas | **0** | **Não** são mudanças positivas de QA |
| Pedidos L14 `READY` | **0/88** | Todos permanecem `PENDING/BLOCKED` |
| Slots contábeis anônimos sem novas dependências | **18** | Cinco posições de relatórios locais e 13 posições B/C/D não têm arquivos reais associados |

**Importante:** o número de 1.084 não significa que 1.084 evidências externas chegaram. Ele conta a transformação documental em links de IDs públicos feita na L14. A L13 já continha as relações entre casos, critérios e bloqueios, mas não as expunha no mesmo campo de dependências da L14. O campo `l13_direct_dependency_request_links=0` mede a ausência daquele campo específico na L13; não afirma que as relações de metadados eram inexistentes.

## Categorias verificadas

| Categoria | Linha de base | Observado | Adicionado pela projeção | Divergência | Interpretação |
| --- | ---: | ---: | ---: | ---: | --- |
| `REQUEST_IDENTITIES_AND_ORDER` | 88 | 88 | 0 | 0 | UNCHANGED_PUBLIC_METADATA |
| `PRIORITY_PLATFORM_STATUS` | 88 | 88 | 0 | 0 | UNCHANGED_PUBLIC_METADATA |
| `L14_DOCUMENTARY_DEPENDENCY_PROJECTION` | 0 | 1084 | 1084 | 0 | ADDED_DOCUMENTARY_PROJECTION_NOT_NATIVE_EVIDENCE |
| `REAL_HUMAN_AND_NATIVE_APPROVAL` | 0 | 0 | 0 | 0 | NO_REAL_EVIDENCE_RECEIVED |

## Pendências por tipo

| Grupo | Pedidos | Bloqueados | Vínculos L14 | Evidências físicas recebidas |
| --- | ---: | ---: | ---: | ---: |
| `BLOCKER_DEPENDENCY` | 5 | 5 | 0 | 0 |
| `GLOBAL_REGIONAL_GATE` | 1 | 1 | 0 | 0 |
| `LOCAL_REPORT_SLOT` | 5 | 5 | 0 | 0 |
| `HUMAN_CRITERION` | 20 | 20 | 20 | 0 |
| `BCD_PENDING_SLOT` | 13 | 13 | 0 | 0 |
| `NATIVE_CASE` | 44 | 44 | 1064 | 0 |

**Prioridades P0–P4 continuam exclusivamente documentais**, sem execução nativa. Há cinco bloqueios específicos B09, B10, B11, R07 e R08; R09 é global, sem vínculo por caso. As 43 entradas Windows exigem revisão separada de B10/B11, sem transferir aprovação para o único caso Android/JoiPlay.

Os 20 critérios humanos L04 permanecem `NOT_REVIEWED` na fonte; a matriz de comparação os registra como `PENDING/BLOCKED`. Os 44 casos nativos G12 seguem `NOT_EXECUTED` em Windows e Android, 0/44. Nenhum dos cinco relatórios locais foi recebido. As 13 posições B/C/D continuam contábeis, sem origem ou nome físico inventado.

## Proveniência: commits e blobs públicos fixos

| Etapa | Commit Git de referência |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| L11 | `9d901a0cf21aa2742f731ee387a51f945bac8a5d` |
| L12 | `58b7f2fec9f66dee06d95676eec66fb2ded6a1de` |
| L13 | `1f12bcc86c10dcc934b024a0562cdadb65d5e2c2` |
| L14 | `11eda18f7225e16b13007c1eb955ccc3d7667b66` |

| Fonte pública | Blob Git SHA-1 |
| --- | --- |
| L13 — `data/regions/sinnoh-l13-public-evidence-queue.json` | `357215cdfd96b37eaac291e1c0ab3873069a12fe` |
| L14 — `data/regions/sinnoh-l14-public-readiness-matrix.json` | `d882d6a20b1c01be33744f14ab7826af2fb6ef41` |

O auditor verifica também os espelhos públicos correspondentes. Os identificadores de blobs Git servem apenas à integridade dos bytes versionados no repositório; **não** comprovam proveniência física do jogo, licenciamento de assets ou isolamento de saves.

## Arquivos e validações L15

- [Relatório JSON L15](../data/regions/sinnoh-l15-public-consistency-diff.json) e [espelho estático do site](../site/public/data/sinnoh-l15-public-consistency-diff.json).
- [Página navegável L15](../site/public/sinnoh-l15-consistencia.html), em `/sinnoh-l15-consistencia.html`: resumo de alterações, filtros por texto, prioridade, tipo, plataforma, vínculo e divergência, consulta do pedido selecionado, grupos e divisão Windows/Android.
- [Auditor fail-closed L15](../scripts/regions/audit_sinnoh_l15_consistency_diff.py): verifica blobs Git L13/L14, recalcula projeção a partir das duas fontes reais, rejeita fake signoff, diferenças de espelho, alterações de classificação, alteração de direitos, R09 por caso e qualquer avanço nativo fictício; reexecuta auditores de L14 até G12.
- [Testes Python L15](../tests/test_sinnoh_l15_consistency_diff.py), com mais de 25 negativas sintéticas e validações de todos os invariantes.
- [Testes Node L15](../site/tests/sinnoh-l15-public-diff.test.mjs) e [CI L15](../.github/workflows/sinnoh-l15-public-consistency.yml), com regressões L14/L13/L12/L11/L10/L09/L08/L07/L06/L05/L04/L03/L02/L01/L00/G12, testes anteriores do portal e build completo.

### Matriz dos 88 pedidos comparados

| # | ID do pedido | Prioridade | Plataforma | Relações na projeção L14 | Estado |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `L13-BLOCKER-B09` | P0 | cross-platform | 0 | `PENDING/BLOCKED` |
| 2 | `L13-BLOCKER-B10` | P0 | windows | 0 | `PENDING/BLOCKED` |
| 3 | `L13-BLOCKER-B11` | P0 | windows | 0 | `PENDING/BLOCKED` |
| 4 | `L13-BLOCKER-R07` | P0 | cross-platform | 0 | `PENDING/BLOCKED` |
| 5 | `L13-BLOCKER-R08` | P0 | cross-platform | 0 | `PENDING/BLOCKED` |
| 6 | `L13-GLOBAL-R09` | P0 | global | 0 | `PENDING/BLOCKED` |
| 7 | `L13-REPORT-01` | P1 | unassigned | 0 | `PENDING/BLOCKED` |
| 8 | `L13-REPORT-02` | P1 | unassigned | 0 | `PENDING/BLOCKED` |
| 9 | `L13-REPORT-03` | P1 | unassigned | 0 | `PENDING/BLOCKED` |
| 10 | `L13-REPORT-04` | P1 | unassigned | 0 | `PENDING/BLOCKED` |
| 11 | `L13-REPORT-05` | P1 | unassigned | 0 | `PENDING/BLOCKED` |
| 12 | `L13-HUMAN-B09_ORIGIN` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 13 | `L13-HUMAN-B09_CLONE` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 14 | `L13-HUMAN-B09_ASSETS` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 15 | `L13-HUMAN-B09_RECEIPT` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 16 | `L13-HUMAN-B10_LINK` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 17 | `L13-HUMAN-B10_READONLY` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 18 | `L13-HUMAN-B10_OFFLINE` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 19 | `L13-HUMAN-B10_PLATFORM` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 20 | `L13-HUMAN-B11_SESSION` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 21 | `L13-HUMAN-B11_SCOPE` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 22 | `L13-HUMAN-B11_DIFFERENCE` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 23 | `L13-HUMAN-B11_LIMIT` | P2 | windows | 1 | `PENDING/BLOCKED` |
| 24 | `L13-HUMAN-R07_NATIVE` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 25 | `L13-HUMAN-R07_REGIONS` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 26 | `L13-HUMAN-R07_CONFLICT` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 27 | `L13-HUMAN-R07_TOPOLOGY` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 28 | `L13-HUMAN-R08_LICENSE` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 29 | `L13-HUMAN-R08_GRAPHICS` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 30 | `L13-HUMAN-R08_EVENTS` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 31 | `L13-HUMAN-R08_PBS` | P2 | cross-platform | 1 | `PENDING/BLOCKED` |
| 32 | `L13-BCD-01` | P3 | global | 0 | `PENDING/BLOCKED` |
| 33 | `L13-BCD-02` | P3 | global | 0 | `PENDING/BLOCKED` |
| 34 | `L13-BCD-03` | P3 | global | 0 | `PENDING/BLOCKED` |
| 35 | `L13-BCD-04` | P3 | global | 0 | `PENDING/BLOCKED` |
| 36 | `L13-BCD-05` | P3 | global | 0 | `PENDING/BLOCKED` |
| 37 | `L13-BCD-06` | P3 | global | 0 | `PENDING/BLOCKED` |
| 38 | `L13-BCD-07` | P3 | global | 0 | `PENDING/BLOCKED` |
| 39 | `L13-BCD-08` | P3 | global | 0 | `PENDING/BLOCKED` |
| 40 | `L13-BCD-09` | P3 | global | 0 | `PENDING/BLOCKED` |
| 41 | `L13-BCD-10` | P3 | global | 0 | `PENDING/BLOCKED` |
| 42 | `L13-BCD-11` | P3 | global | 0 | `PENDING/BLOCKED` |
| 43 | `L13-BCD-12` | P3 | global | 0 | `PENDING/BLOCKED` |
| 44 | `L13-BCD-13` | P3 | global | 0 | `PENDING/BLOCKED` |
| 45 | `L13-NATIVE-ball-TURTWIG` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 46 | `L13-NATIVE-barry-TURTWIG-normal-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 47 | `L13-NATIVE-barry-TURTWIG-normal-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 48 | `L13-NATIVE-barry-TURTWIG-master-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 49 | `L13-NATIVE-barry-TURTWIG-master-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 50 | `L13-NATIVE-save-reload-TURTWIG` | P4 | windows | 23 | `PENDING/BLOCKED` |
| 51 | `L13-NATIVE-ball-CHIMCHAR` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 52 | `L13-NATIVE-barry-CHIMCHAR-normal-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 53 | `L13-NATIVE-barry-CHIMCHAR-normal-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 54 | `L13-NATIVE-barry-CHIMCHAR-master-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 55 | `L13-NATIVE-barry-CHIMCHAR-master-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 56 | `L13-NATIVE-save-reload-CHIMCHAR` | P4 | windows | 23 | `PENDING/BLOCKED` |
| 57 | `L13-NATIVE-ball-PIPLUP` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 58 | `L13-NATIVE-barry-PIPLUP-normal-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 59 | `L13-NATIVE-barry-PIPLUP-normal-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 60 | `L13-NATIVE-barry-PIPLUP-master-win` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 61 | `L13-NATIVE-barry-PIPLUP-master-loss` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 62 | `L13-NATIVE-save-reload-PIPLUP` | P4 | windows | 23 | `PENDING/BLOCKED` |
| 63 | `L13-NATIVE-warp-SN_BEDROOM_TO_1F` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 64 | `L13-NATIVE-npc-SN_NPC_MOTHER` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 65 | `L13-NATIVE-warp-SN_1F_TO_BEDROOM` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 66 | `L13-NATIVE-warp-SN_1F_TO_TWINLEAF` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 67 | `L13-NATIVE-warp-SN_TOWN_TO_HOME` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 68 | `L13-NATIVE-warp-SN_TOWN_TO_BARRY_HOME` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 69 | `L13-NATIVE-warp-SN_TOWN_TO_ROUTE201` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 70 | `L13-NATIVE-npc-SN_NPC_BARRY_INTRO` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 71 | `L13-NATIVE-warp-SN_BARRY_HOME_TO_TOWN` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 72 | `L13-NATIVE-warp-SN_ROUTE201_TO_TOWN` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 73 | `L13-NATIVE-warp-SN_ROUTE201_TO_LAKE` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 74 | `L13-NATIVE-warp-SN_ROUTE201_TO_SANDGEM` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 75 | `L13-NATIVE-npc-SN_NPC_ROWAN_BRIEFCASE` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 76 | `L13-NATIVE-npc-SN_NPC_BARRY_BATTLE` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 77 | `L13-NATIVE-warp-SN_LAKE_TO_ROUTE201` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 78 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE201` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 79 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROWAN_LAB` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 80 | `L13-NATIVE-warp-SN_SANDGEM_TO_ROUTE202` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 81 | `L13-NATIVE-npc-SN_NPC_ROWAN_POKEDEX` | P4 | windows | 25 | `PENDING/BLOCKED` |
| 82 | `L13-NATIVE-warp-SN_ROWAN_LAB_TO_TOWN` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 83 | `L13-NATIVE-warp-SN_ROUTE202_TO_SANDGEM` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 84 | `L13-NATIVE-regression-DECADES` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 85 | `L13-NATIVE-regression-KANTO` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 86 | `L13-NATIVE-regression-JOHTO` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 87 | `L13-NATIVE-regression-HOENN` | P4 | windows | 24 | `PENDING/BLOCKED` |
| 88 | `L13-NATIVE-android-joi-play` | P4 | android | 15 | `PENDING/BLOCKED` |

## Verificar apenas metadados públicos, sem executar o jogo

```sh
python scripts/regions/audit_sinnoh_l15_consistency_diff.py
python -m unittest discover -s tests -p 'test_sinnoh_l15_consistency_diff.py' -v
```

O auditor aceita apenas caminhos fixos de documentos públicos do repositório. Não acessa o computador do usuário, Game.exe, Windows Sandbox, JoiPlay, ROMs, saves, ZIP/PNG privados ou fontes de licença restrita. O painel não oferece mecanismo de upload.

## Bloqueios e barras imutáveis

| Indicador | Estado |
| --- | --- |
| Relatórios locais aceitos | **0/5** |
| Critérios humanos aprovados | **0/20** |
| Casos nativos executados | **0/44** |
| Barras B/C/D | **0/13** |
| R07 / R08 / R09 | **Pendentes** |
| Isolamento global B11 | **Não demonstrado** |
| Direitos R08 e MapIDs R07 | **Não aprovados** |
| Sinnoh | **planned / não jogável** |

L15 conclui somente a comparação e integridade **documental pública**, não promove indicadores de jogabilidade.
