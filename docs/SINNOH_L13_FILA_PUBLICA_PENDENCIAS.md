# Sinnoh L13 — Fila pública priorizada de pedidos documentais ainda não atendidos

**Issue #201 · exclusivamente GitHub-only · não constitui recepção de evidência física.**

## Síntese: 88 entradas públicas, nenhuma prova recebida

A etapa L13 projeta os metadados da [L12](../data/regions/sinnoh-l12-public-coverage-gaps.json) em **88 entradas estritamente pendentes**, ordenadas por regra determinística. As prioridades são de **acompanhar pendências documentais**, não uma autorização técnica, permissão de executar um emulador, iniciar Windows Sandbox ou solicitar upload de saves e arquivos privados.

| Tipo de item | Total | Identificação |
| --- | ---: | --- |
| Bloqueios B09/B10/B11/R07/R08 | 5 | IDs públicos conhecidos, com critérios e casos vinculados |
| Gate regional R09 | 1 | **Global e sem vínculo adicional por caso** |
| Posições de relatórios locais | 5 | **Anônimas; não são nomes de relatórios reais** |
| Revisões independentes de critérios humanos L04 | 20 | IDs reais, sem assinatura ou evidência aprovada |
| Posições contábeis B/C/D | 13 | **Anônimas; não inferem titularidade ou ordem real** |
| Casos nativos G12 | 44 | **43 Windows e 1 Android**, todos sem autorização e não executados |
| **Total** | **88** | **88 pendentes · 0 aprovados** |

O fato de a matriz L11 conter **1.084 vínculos JSON íntegros** não significa que algum dos 44 testes nativos tenha passado.

## Prioridades reprodutíveis (versão 1)

| Ordem | Código | Grupo | Significado |
| ---: | --- | --- | --- |
| 0 | `P0_DOCUMENTARY_PRECONDITION` | BLOCKER_DEPENDENCY, GLOBAL_REGIONAL_GATE | Documentary prerequisite tracking, not physical approval |
| 1 | `P1_MISSING_REPORT_SLOT` | LOCAL_REPORT_SLOT | Anonymous bookkeeping placeholders only; no private files |
| 2 | `P2_INDEPENDENT_HUMAN_REVIEW` | HUMAN_CRITERION | Human signoff still missing |
| 3 | `P3_BCD_PENDING_BOOKKEEPING` | BCD_PENDING_SLOT | Anonymous counters; no invented specific BCD steps |
| 4 | `P4_NATIVE_QA_UNAUTHORIZED` | NATIVE_CASE | Not executed, not authorized; inventory only |

A ordem é estável: primeiro B09/B10/B11/R07/R08 e R09 global, em seguida cinco posições contábeis de relatórios, os 20 critérios humanos, 13 posições B/C/D e, por último, os 44 casos nativos. Esse sequenciamento foi escolhido apenas para organizar a **fila de acompanhamento**, não para criar dependências físicas novas ou assumir que as fases devam ser executadas nessa ordem. A L13 **não cria links automáticos** de posições anônimas para casos ou critérios porque suas identidades reais são desconhecidas.

## Entregas e fontes fixas

- [Fila L13 em JSON](../data/regions/sinnoh-l13-public-evidence-queue.json) e [espelho usado no portal](../site/public/data/sinnoh-l13-public-evidence-queue.json).
- [Painel público somente leitura](../site/public/sinnoh-l13-pendencias.html) na rota `/sinnoh-l13-pendencias.html`, com filtros por texto, prioridade, tipo, plataforma, bloqueio e critério. Os únicos controles disponíveis são os filtros e a limpeza dos filtros — **nenhum upload, aprovação ou ação sobre o jogo**.
- [Auditor fail-closed L13](../scripts/regions/audit_sinnoh_l13_public_queue.py): recompõe os 88 itens da L12, verifica o hash de objeto Git público das duas cópias L12 e revalida a cadeia de auditorias **L12/L11/L10/L09/L08/L07/L06/L05/L04/G12**.
- [Testes sintéticos L13](../tests/test_sinnoh_l13_public_queue.py) com mais de 25 mutações negativas (IDs, prioridade, autorização indevida, locais privados, isolamento, licenças, MapIDs, contador, R09, troca de plataformas e falsos signoffs).
- [Testes do portal](../site/tests/sinnoh-l13-public-queue.test.mjs) e [workflow CI](../.github/workflows/sinnoh-l13-public-request-queue.yml) com regressões L12 até L00/G12 e build completo do site.

## Ancoragem exclusivamente pública

| Etapa | Commit Git público |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| L11 | `9d901a0cf21aa2742f731ee387a51f945bac8a5d` |
| L12 | `58b7f2fec9f66dee06d95676eec66fb2ded6a1de` |
| Arquivo público L12 (Git blob SHA-1) | `dbd9181a5910c7fc711eaaa20d0e3b24a9d1710e` |

Essa ancoragem verifica somente o conteúdo de documentos **públicos GitHub**, não a proveniência física da instalação, o licenciamento de terceiros ou um save local. O commit da L13 será incluído na issue após CI e merge, para não criar referência circular dentro do arquivo.

## Separação rigorosa de Windows, Android e R09

| Plataforma | Casos nativos | Executados | Pré-condição B10/B11 Windows |
| --- | ---: | ---: | --- |
| Windows | **43** | **0** | Pendente; requer inspeção independente e prova de isolamento apropriada |
| Android/JoiPlay | **1** | **0** | **Não se aplica**; o gate de Android é independente |

R09 permanece **regional global** com zero `case_ids` associados. Não cria um 45º teste, um 21º critério ou novo bloqueio por caso.

- B09: proveniência física de origem e clone não confirmada independentemente.
- B10: configuração e restrições de Windows Sandbox não verificadas em host real.
- B11: `watch_unchanged` **não** comprova isolamento global de saves, apenas escopo monitorado.
- R07: MapIDs reais e reservas regionais não validados; IDs candidatos não são MapIDs instalados.
- R08: direitos sobre assets, gráficos, eventos e PBS não comprovados; listagem de arquivos não certifica licença.
- R09: aprovação regional futura **pendente**, sem execução nativa.

## Os 20 critérios L04 continuam pendentes

| Critério humano | Bloqueio | Casos relacionados | Revisão |
| --- | --- | ---: | --- |
| `B09_ORIGIN` | B09 | 44 | Pendente |
| `B09_CLONE` | B09 | 44 | Pendente |
| `B09_ASSETS` | B09 | 44 | Pendente |
| `B09_RECEIPT` | B09 | 44 | Pendente |
| `B10_LINK` | B10 | 43 | Pendente |
| `B10_READONLY` | B10 | 43 | Pendente |
| `B10_OFFLINE` | B10 | 43 | Pendente |
| `B10_PLATFORM` | B10 | 43 | Pendente |
| `B11_SESSION` | B11 | 43 | Pendente |
| `B11_SCOPE` | B11 | 43 | Pendente |
| `B11_DIFFERENCE` | B11 | 43 | Pendente |
| `B11_LIMIT` | B11 | 43 | Pendente |
| `R07_NATIVE` | R07 | 44 | Pendente |
| `R07_REGIONS` | R07 | 44 | Pendente |
| `R07_CONFLICT` | R07 | 44 | Pendente |
| `R07_TOPOLOGY` | R07 | 41 | Pendente |
| `R08_LICENSE` | R08 | 44 | Pendente |
| `R08_GRAPHICS` | R08 | 44 | Pendente |
| `R08_EVENTS` | R08 | 44 | Pendente |
| `R08_PBS` | R08 | 21 | Pendente |

## Os 44 casos G12 continuam pendentes

| # | Caso | Plataforma | Critérios | Bloqueios | QA nativa |
| ---: | --- | --- | ---: | --- | --- |
| 1 | `ball-TURTWIG` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 2 | `barry-TURTWIG-normal-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 3 | `barry-TURTWIG-normal-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 4 | `barry-TURTWIG-master-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 5 | `barry-TURTWIG-master-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 6 | `save-reload-TURTWIG` | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 7 | `ball-CHIMCHAR` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 8 | `barry-CHIMCHAR-normal-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 9 | `barry-CHIMCHAR-normal-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 10 | `barry-CHIMCHAR-master-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 11 | `barry-CHIMCHAR-master-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 12 | `save-reload-CHIMCHAR` | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 13 | `ball-PIPLUP` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 14 | `barry-PIPLUP-normal-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 15 | `barry-PIPLUP-normal-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 16 | `barry-PIPLUP-master-win` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 17 | `barry-PIPLUP-master-loss` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 18 | `save-reload-PIPLUP` | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 19 | `warp-SN_BEDROOM_TO_1F` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 20 | `npc-SN_NPC_MOTHER` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 21 | `warp-SN_1F_TO_BEDROOM` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 22 | `warp-SN_1F_TO_TWINLEAF` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 23 | `warp-SN_TOWN_TO_HOME` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 26 | `npc-SN_NPC_BARRY_INTRO` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 40 | `regression-DECADES` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 41 | `regression-KANTO` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 42 | `regression-JOHTO` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 43 | `regression-HOENN` | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 44 | `android-joi-play` | android | 12 | B09, R07, R08 | Não executado |

## Verificação da fila pública (sem operar o jogo)

```sh
python scripts/regions/audit_sinnoh_l13_public_queue.py
python -m unittest discover -s tests -p 'test_sinnoh_l13_public_queue.py' -v
```

Não se aceita parâmetro de caminho externo, arquivo de host, recibo, token, ZIP/PNG privado, save, upload ou autorização de execução. O script é somente um verificador de JSON público com caminhos fixos e falha caso qualquer dado contradiga as fontes de L12.

## Invariantes sem mudança

| Indicador | Resultado |
| --- | --- |
| Vínculos documentais públicos L11 | **1.084/1.084** (não são evidências nativas) |
| Relatórios locais recebidos | **0/5** |
| Revisões humanas aprovadas | **0/20** |
| Testes nativos executados | **0/44** |
| B/C/D aprovados | **0/13** |
| R07/R08/R09 | **Pendentes** |
| Isolamento global B11, direitos R08 e MapIDs R07 | **Não demonstrados** |
| Sinnoh | **planned / não jogável** |

Próxima fase L14 pode continuar refinando a auditoria documental, nunca transformando posições anônimas da L13 em provas físicas sem uma revisão independente e autorizada.
