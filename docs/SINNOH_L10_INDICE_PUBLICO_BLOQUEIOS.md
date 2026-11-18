# Sinnoh L10 — Índice público de bloqueios e revisão documental

**Issue #194 — somente GitHub, read-only.** O índice organiza a documentação pública dos 44 casos G12/CH20 e 20 critérios L04 herdados do [handoff L09](../data/regions/sinnoh-l09-independent-public-handoff.json). Nenhuma evidência física foi recebida, ninguém atestou proveniência, nenhum teste foi executado e nenhum direito ou MapID foi aprovado.

## Entregas

- [Índice público versionado L10](../data/regions/sinnoh-l10-public-blocker-index.json) e [cópia estática servida pelo portal](../site/public/data/sinnoh-l10-public-blocker-index.json) com igualdade de bytes testada; **44 casos, 20 critérios, 6 tipos de bloqueio**, sendo R09 global.
- [Página navegável L10](../site/public/sinnoh-l10-bloqueios.html), disponível como `/sinnoh-l10-bloqueios.html`, com filtros por ID, plataforma, categoria, critério L04, bloqueio; navegação pelas seis pendências; link no rodapé do portal. Nenhum login, edição, formulário, botão para aprovar ou executar.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l10_public_index.py) recompõe toda a matriz a partir da L09, valida o blob Git público da L09 e executa a cadeia L09/L08/L07/L06/L05/L04/G12; rejeita alterações estruturais ou falsas aprovações na fonte e no espelho.
- [Testes L10](../tests/test_sinnoh_l10_public_index.py): 10 validações positivas e **125 mutações sintéticas negativas**, incluindo adulterações de IDs, permissão, licenças, MapIDs, B11, R09, vínculos, URLs/arquivos privados, ordens, espelho e fontes.
- [Testes Node](../site/tests/sinnoh-l10-blocker-index.test.mjs) cobrem paridade, filtro/UI somente leitura e segregação Windows/Android.
- [CI L10](../.github/workflows/sinnoh-l10-public-index.yml) com suíte L10, regressões L09/L08/L07/L06/L05/L04/L03/L02/L01/L00/G12 e build completo do portal.

## Proveniência pública por commit

| Etapa | Commit Git público |
| --- | --- |
| L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| Fonte pública L09 (blob Git) | `1245ceab070796455da4772ddab0ce974f80605d` |

O Git blob verifica **bytes de documento público**, não identidade física do clone, assinaturas humanas, direitos de propriedade intelectual ou saúde da instalação. O commit de L10 será registrado na issue depois de CI aprovado e merge, evitando autorreferência do arquivo.

## Índice das seis pendências

| Etapa | Escopo | Windows | Android | Estado |
| --- | --- | ---: | ---: | --- |
| `B09` | CROSS_PLATFORM | 43 | 1 | PENDING |
| `B10` | WINDOWS_ONLY | 43 | 0 | PENDING |
| `B11` | WINDOWS_ONLY | 43 | 0 | PENDING |
| `R07` | CROSS_PLATFORM | 43 | 1 | PENDING |
| `R08` | CROSS_PLATFORM | 43 | 1 | PENDING |
| `R09` | GLOBAL_REGION_PENDING_NOT_CASE_GATE | 0 | 0 | PENDING |

**R09 é uma dependência regional global que continua pendente, não é inserida retroativamente como 45º teste, 21º critério ou sexto bloqueio por caso.** A coluna de casos vinculados permanece vazia no JSON de R09. A distinção evita alegar que a G12 originou uma exigência adicional por caso.

### Regras não negociáveis

- **B09:** proveniência de origem e clone não verificada de maneira independente, tanto Windows quanto Android.
- **B10/B11:** exigências exclusivas dos 43 casos Windows. Montagens, isolamento de sessão e escopo real de saves permanecem sem prova física. `watch_unchanged` **não** significa isolamento global.
- **Android/JoiPlay:** um caso próprio e sem B10/B11. O gate local Android L05 da G12 é distinto da documentação L10.
- **R07:** MapIDs candidatos, nove vínculos simbólicos, transferências e reservas não comprovam mapas físicos instalados nem alocação autorizada.
- **R08:** licenças, gráficos, eventos e PBS exigem revisão independente de permissões e materiais físicos antes de qualquer integração.
- **R09:** ainda pendente e global. Nenhuma parte do índice autoriza jogar, executar, instalar, testar ou compartilhar arquivos protegidos.

## Matriz dos 20 critérios humanos L04

| Critério | Bloco | Vínculos G12 | Windows/Android | Estado |
| --- | --- | ---: | --- | --- |
| `B09_ORIGIN` | B09 | 44 | 43/1 | Não revisado |
| `B09_CLONE` | B09 | 44 | 43/1 | Não revisado |
| `B09_ASSETS` | B09 | 44 | 43/1 | Não revisado |
| `B09_RECEIPT` | B09 | 44 | 43/1 | Não revisado |
| `B10_LINK` | B10 | 43 | 43/0 | Não revisado |
| `B10_READONLY` | B10 | 43 | 43/0 | Não revisado |
| `B10_OFFLINE` | B10 | 43 | 43/0 | Não revisado |
| `B10_PLATFORM` | B10 | 43 | 43/0 | Não revisado |
| `B11_SESSION` | B11 | 43 | 43/0 | Não revisado |
| `B11_SCOPE` | B11 | 43 | 43/0 | Não revisado |
| `B11_DIFFERENCE` | B11 | 43 | 43/0 | Não revisado |
| `B11_LIMIT` | B11 | 43 | 43/0 | Não revisado |
| `R07_NATIVE` | R07 | 44 | 43/1 | Não revisado |
| `R07_REGIONS` | R07 | 44 | 43/1 | Não revisado |
| `R07_CONFLICT` | R07 | 44 | 43/1 | Não revisado |
| `R07_TOPOLOGY` | R07 | 41 | 40/1 | Não revisado |
| `R08_LICENSE` | R08 | 44 | 43/1 | Não revisado |
| `R08_GRAPHICS` | R08 | 44 | 43/1 | Não revisado |
| `R08_EVENTS` | R08 | 44 | 43/1 | Não revisado |
| `R08_PBS` | R08 | 21 | 20/1 | Não revisado |

## Casos nativos G12/CH20 representados no índice

| # | ID real | Plataforma | Grupo | Bloqueios por caso | Critérios | Estado |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | `ball-TURTWIG` | windows | starter | B09, B10, B11, R07, R08 | 20 | Pendente |
| 2 | `barry-TURTWIG-normal-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 3 | `barry-TURTWIG-normal-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 4 | `barry-TURTWIG-master-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 5 | `barry-TURTWIG-master-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 6 | `save-reload-TURTWIG` | windows | save_reload | B09, B10, B11, R07, R08 | 18 | Pendente |
| 7 | `ball-CHIMCHAR` | windows | starter | B09, B10, B11, R07, R08 | 20 | Pendente |
| 8 | `barry-CHIMCHAR-normal-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 9 | `barry-CHIMCHAR-normal-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 10 | `barry-CHIMCHAR-master-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 11 | `barry-CHIMCHAR-master-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 12 | `save-reload-CHIMCHAR` | windows | save_reload | B09, B10, B11, R07, R08 | 18 | Pendente |
| 13 | `ball-PIPLUP` | windows | starter | B09, B10, B11, R07, R08 | 20 | Pendente |
| 14 | `barry-PIPLUP-normal-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 15 | `barry-PIPLUP-normal-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 16 | `barry-PIPLUP-master-win` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 17 | `barry-PIPLUP-master-loss` | windows | barry | B09, B10, B11, R07, R08 | 20 | Pendente |
| 18 | `save-reload-PIPLUP` | windows | save_reload | B09, B10, B11, R07, R08 | 18 | Pendente |
| 19 | `warp-SN_BEDROOM_TO_1F` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 20 | `npc-SN_NPC_MOTHER` | windows | npc | B09, B10, B11, R07, R08 | 20 | Pendente |
| 21 | `warp-SN_1F_TO_BEDROOM` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 22 | `warp-SN_1F_TO_TWINLEAF` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 23 | `warp-SN_TOWN_TO_HOME` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 26 | `npc-SN_NPC_BARRY_INTRO` | windows | npc | B09, B10, B11, R07, R08 | 20 | Pendente |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | windows | npc | B09, B10, B11, R07, R08 | 20 | Pendente |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | windows | npc | B09, B10, B11, R07, R08 | 20 | Pendente |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | windows | npc | B09, B10, B11, R07, R08 | 20 | Pendente |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | windows | warp | B09, B10, B11, R07, R08 | 19 | Pendente |
| 40 | `regression-DECADES` | windows | regression | B09, B10, B11, R07, R08 | 19 | Pendente |
| 41 | `regression-KANTO` | windows | regression | B09, B10, B11, R07, R08 | 19 | Pendente |
| 42 | `regression-JOHTO` | windows | regression | B09, B10, B11, R07, R08 | 19 | Pendente |
| 43 | `regression-HOENN` | windows | regression | B09, B10, B11, R07, R08 | 19 | Pendente |
| 44 | `android-joi-play` | android | android | B09, R07, R08 | 12 | Pendente |

## Instruções de auditoria documental (sem QA nativa)

```sh
python scripts/regions/audit_sinnoh_l10_public_index.py
python -m unittest discover -s tests -p 'test_sinnoh_l10_public_index.py' -v
```

Esses comandos usam somente caminhos fixos de JSON públicos. O auditor recusa parâmetros, symlinks, arquivos adulterados e novas permissões, sem acessar a instalação do usuário, caches pessoais, saves, ROM, ZIP, PNG privados, Sandbox, JoiPlay ou serviços externos.

### Indicadores preservados

| Indicador | Estado |
| --- | --- |
| Relatórios locais | **0/5** |
| Critérios humanos aprovados | **0/20** |
| Testes nativos Windows/Android | **0/44** |
| B/C/D | **0/13** |
| R07, R08, R09 | **Pendentes** |
| Isolamento global de saves B11 | **Não comprovado** |
| MapIDs e direitos de assets | **Não aprovados** |
| Sinnoh | **planned / não jogável** |

A conclusão da L10 se limita a navegação pública e conformidade documental, não equivale a homologação, revisão física ou aptidão nativa. Próxima fase L11 deve manter os bloqueios e vincular-se à próxima issue após CI e merge.
