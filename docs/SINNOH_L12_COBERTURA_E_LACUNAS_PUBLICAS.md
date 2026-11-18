# Sinnoh L12 — Cobertura pública completa, evidências reais ausentes

**Issue #199 · PR L12 · exclusivamente documental no GitHub.** Esta entrega separa duas afirmações que não devem ser confundidas: a trilha pública L11 possui os 1.084 vínculos esperados, mas isso **não significa** que um único revisor humano tenha aprovado qualquer fonte física nem que um único teste nativo tenha sido executado.

## Resumo verificável

| Camada | Necessários | Confirmados | Ausentes | Natureza |
| --- | ---: | ---: | ---: | --- |
| `PUBLIC_METADATA_LINKS` | 1084 | 1084 | 0 | DOCUMENTARY_LINKS_PRESENT_NO_PHYSICAL_APPROVAL |
| `INDEPENDENT_HUMAN_REVIEW` | 20 | 0 | 20 | ALL_PENDING |
| `WINDOWS_NATIVE_QA` | 43 | 0 | 43 | NOT_EXECUTED |
| `ANDROID_NATIVE_QA` | 1 | 0 | 1 | NOT_EXECUTED |
| `LOCAL_REPORTS` | 5 | 0 | 5 | NOT_RECEIVED |
| `B_C_D_APPROVALS` | 13 | 0 | 13 | NOT_APPROVED |

A linha `PUBLIC_METADATA_LINKS` verifica **somente links de JSON entre etapas**; todas as outras linhas exigem ações/evidências externas ainda **não recebidas nem aprovadas**. Um relatório de lacunas físicas que marcasse 0 faltantes sem provas independentes é inválido e rejeitado pelo auditor.

## Artefatos de L12

- [Relatório versionado L12](../data/regions/sinnoh-l12-public-coverage-gaps.json) e [espelho público usado no site](../site/public/data/sinnoh-l12-public-coverage-gaps.json) — 44 casos, 20 critérios, seis bloqueios, cobertura documental e contadores explícitos de evidências humanas/nativas ausentes.
- [Handoff público L12](../site/public/sinnoh-l12-lacunas.html) disponível em `/sinnoh-l12-lacunas.html`: filtros por caso, plataforma, grupo, critério, bloqueio e tipo de lacuna, inclusive seleção de **links documentais ausentes** (o filtro deve mostrar zero sem alegar prontidão nativa).
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l12_coverage_gaps.py) — verifica o Git blob do L11 e o espelho, reexecuta auditores L11→L10→L09→L08→L07→L06→L05→L04→G12 e compara o relatório inteiro com uma projeção derivada de fontes públicas aprovadas exclusivamente para metadados.
- [Testes Python L12](../tests/test_sinnoh_l12_coverage_gaps.py) com 11 checagens positivas e **171 mutações sintéticas negativas**: falsas revisões, evidência inventada, mudança de plataforma, direitos R08, MapIDs R07, global B11, relatórios, R09, distorção do espelho e adulteração das versões.
- [Testes Node L12](../site/tests/sinnoh-l12-coverage-gaps.test.mjs), [workflow CI L12](../.github/workflows/sinnoh-l12-public-coverage.yml): três jobs com regressões L11–L00/G12, verificações de UI e build do site.

## Proveniência pública por commit

| Fase | Commit histórico fixo |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| L11 | `9d901a0cf21aa2742f731ee387a51f945bac8a5d` |
| L11 Git blob (arquivo público) | `c39f81867568fb95c65ca8113431e1db05919168` |

O SHA de objeto Git comprova bytes de **um documento público**. Não autentica física ou juridicamente um clone do game, instalação, origem de ativos, licenças, saves, MapIDs ou relatórios locais. O commit resultante da L12 deve ser anotado na issue depois do CI e merge, e não ser colocado dentro do próprio relatório.

## Divisão por plataforma

| Fila | Casos públicos | Testes nativos feitos | Testes faltantes | B10/B11 |
| --- | ---: | ---: | ---: | --- |
| Windows | 43 | **0** | **43** | Requer revisão independente de host e isolamento |
| Android/JoiPlay | 1 | **0** | **1** | Não pode herdar B10/B11 da VM Windows |

A etapa local Android L05 da G12 **não é** concluída por L12. Sem prova física de sessão/isolamento de saves, `watch_unchanged` em escopo limitado não implica isolamento global B11. R07 MapIDs e R08 licenças seguem pendentes. **R09 permanece global, sem criar mais um caso nativo nem critério humano.**

## Handoff dos 20 critérios humanos

| ID real L04 | Etapa | Casos vinculados | Revisão humana | Evidência física |
| --- | --- | ---: | --- | --- |
| `B09_ORIGIN` | B09 | 44 | Não revisado | Evidência ausente |
| `B09_CLONE` | B09 | 44 | Não revisado | Evidência ausente |
| `B09_ASSETS` | B09 | 44 | Não revisado | Evidência ausente |
| `B09_RECEIPT` | B09 | 44 | Não revisado | Evidência ausente |
| `B10_LINK` | B10 | 43 | Não revisado | Evidência ausente |
| `B10_READONLY` | B10 | 43 | Não revisado | Evidência ausente |
| `B10_OFFLINE` | B10 | 43 | Não revisado | Evidência ausente |
| `B10_PLATFORM` | B10 | 43 | Não revisado | Evidência ausente |
| `B11_SESSION` | B11 | 43 | Não revisado | Evidência ausente |
| `B11_SCOPE` | B11 | 43 | Não revisado | Evidência ausente |
| `B11_DIFFERENCE` | B11 | 43 | Não revisado | Evidência ausente |
| `B11_LIMIT` | B11 | 43 | Não revisado | Evidência ausente |
| `R07_NATIVE` | R07 | 44 | Não revisado | Evidência ausente |
| `R07_REGIONS` | R07 | 44 | Não revisado | Evidência ausente |
| `R07_CONFLICT` | R07 | 44 | Não revisado | Evidência ausente |
| `R07_TOPOLOGY` | R07 | 41 | Não revisado | Evidência ausente |
| `R08_LICENSE` | R08 | 44 | Não revisado | Evidência ausente |
| `R08_GRAPHICS` | R08 | 44 | Não revisado | Evidência ausente |
| `R08_EVENTS` | R08 | 44 | Não revisado | Evidência ausente |
| `R08_PBS` | R08 | 21 | Não revisado | Evidência ausente |

## Handoff dos 44 casos G12

| # | Caso real | Categoria | Plataforma | Links para critérios | Bloqueios pendentes | QA nativa |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `ball-TURTWIG` | starter | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 2 | `barry-TURTWIG-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 3 | `barry-TURTWIG-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 4 | `barry-TURTWIG-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 5 | `barry-TURTWIG-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 6 | `save-reload-TURTWIG` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 7 | `ball-CHIMCHAR` | starter | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 8 | `barry-CHIMCHAR-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 9 | `barry-CHIMCHAR-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 10 | `barry-CHIMCHAR-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 11 | `barry-CHIMCHAR-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 12 | `save-reload-CHIMCHAR` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 13 | `ball-PIPLUP` | starter | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 14 | `barry-PIPLUP-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 15 | `barry-PIPLUP-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 16 | `barry-PIPLUP-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 17 | `barry-PIPLUP-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 18 | `save-reload-PIPLUP` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Não executado |
| 19 | `warp-SN_BEDROOM_TO_1F` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 20 | `npc-SN_NPC_MOTHER` | npc | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 21 | `warp-SN_1F_TO_BEDROOM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 22 | `warp-SN_1F_TO_TWINLEAF` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 23 | `warp-SN_TOWN_TO_HOME` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 26 | `npc-SN_NPC_BARRY_INTRO` | npc | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | npc | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | npc | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | npc | windows | 20 | B09, B10, B11, R07, R08 | Não executado |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 40 | `regression-DECADES` | regression | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 41 | `regression-KANTO` | regression | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 42 | `regression-JOHTO` | regression | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 43 | `regression-HOENN` | regression | windows | 19 | B09, B10, B11, R07, R08 | Não executado |
| 44 | `android-joi-play` | android | android | 12 | B09, R07, R08 | Não executado |

## Auditoria somente de documentação pública

```sh
python scripts/regions/audit_sinnoh_l12_coverage_gaps.py
python -m unittest discover -s tests -p 'test_sinnoh_l12_coverage_gaps.py' -v
```

O auditor recebe apenas arquivos JSON públicos em locais fixos. Recusa caminhos arbitrários e alterações de conteúdo; não acessa o PC, Game.exe, Windows Sandbox, JoiPlay, saves, ZIP/PNG/ROM privados, evidências locais ou chaves de acesso. O painel não faz uploads, não modifica o JSON e não concede aprovações.

## Estado técnico preservado

| Indicador | Valor |
| --- | --- |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos aprovados | **0/20** |
| Testes nativos executados | **0/44** |
| Barras B/C/D | **0/13** |
| R07 / R08 / R09 | **PENDENTES** |
| Licenças, MapIDs, isolamento B11 | **Não comprovados** |
| Sinnoh | **planned / não jogável** |

A próxima fase documental L13 deve explorar o pacote de lacunas sem transformar 1.084 vínculos íntegros em autorização para instalar, distribuir ou executar o jogo.
