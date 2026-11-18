# Sinnoh L11 — Trilha pública de rastreabilidade dos casos, critérios e bloqueios

**Issue #197 — somente GitHub, dados públicos e página read-only.** Esta fase **não** executa o game nem a QA Windows/Android, não revê arquivos físicos, não adquire licenças, não reserva MapIDs e não aceita provas nativas. Os vínculos são metadados derivados do índice L10, não evidência de aprovação humana.

## Entregas L11

- [Matriz pública versionada L11](../data/regions/sinnoh-l11-public-traceability.json) e [espelho usado no portal](../site/public/data/sinnoh-l11-public-traceability.json). Ambos precisam ser idênticos de forma estrutural e em bytes: 44 nós de casos, 20 critérios e seis nós de bloqueio, incluindo R09 global.
- [Página navegável L11](../site/public/sinnoh-l11-rastreabilidade.html), na rota `/sinnoh-l11-rastreabilidade.html`. A navegação permite selecionar um caso, consultar critérios e bloqueios e filtrar por ID, plataforma, critério e bloqueio. Ações são apenas locais de visualização.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l11_traceability.py): valida os identificadores públicos de blob Git das duas cópias L10, reexecuta auditores L10→L09→L08→L07→L06→L05→L04→G12, recalcula os 1.084 vínculos e detecta divergências de IDs/ordem/plataforma/escopos.
- [Testes de integridade L11](../tests/test_sinnoh_l11_traceability.py): **152 cenários negativos sintéticos** e 11 testes positivos, incluindo adulteração de fontes, links, revisões, direitos, MapIDs, saves, permissões, gate R09 e diferenças de espelho.
- [Testes Node](../site/tests/sinnoh-l11-traceability.test.mjs): invariantes dos links em ambos os sentidos, fila Windows/Android e segurança estática da interface.
- [Workflow L11](../.github/workflows/sinnoh-l11-public-traceability.yml): três jobs de auditoria e regressões L10/L09/L08/L07/L06/L05/L04/L03/L02/L01/L00/G12, testes Node e build completo do portal.

## Proveniência pública versionada

| Etapa | Commit de referência |
| --- | --- |
| L07 — triagem | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| L08 — snapshot | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L09 — pacote humano | `39e51de92aafdab3f5aea3f929f57f5c0bb72b2d` |
| L10 — índice de bloqueios | `7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a` |
| Git blob público do JSON L10 | `ebb2559d59fcb9a2318173da4bf649e3d3af7567` |

O Git blob confirma bytes públicos de um arquivo do repositório. **Não** comprova a integridade de cópias privadas, direitos de redistribuição, isolamento de saves, origem física de instalação ou inspeção humana real. O commit final L11 será informado após CI e merge, para evitar autorreferência.

## Grafo de rastreabilidade documental

| Relação | Vínculos reais |
| --- | ---: |
| Caso G12 → critério L04 | 846 |
| Caso G12 → bloqueio específico B09/B10/B11/R07/R08 | 218 |
| Critério L04 → etapa de bloqueio B09/B10/B11/R07/R08 | 20 |
| **Total de vínculos auditados** | **1084** |

Cada ligação da matriz é recalculada a partir dos vetores originais do índice L10. Uma alteração de ID, tipo, plataforma, vínculo, sequência ou gate provoca falha do auditor e impede que o relatório declare conformidade.

### Bloqueios e escopos

| Código | Escopo | Casos conectados | Estado |
| --- | --- | ---: | --- |
| `B09` | CROSS_PLATFORM | 44 | PENDING |
| `B10` | WINDOWS_ONLY | 43 | PENDING |
| `B11` | WINDOWS_ONLY | 43 | PENDING |
| `R07` | CROSS_PLATFORM | 44 | PENDING |
| `R08` | CROSS_PLATFORM | 44 | PENDING |
| `R09` | GLOBAL_REGION_PENDING_NOT_CASE_GATE | 0 | PENDING |

- **B09:** origens e clones reais não auditados por revisor independente.
- **B10:** configuração de Windows Sandbox ainda não verificada (43 casos Windows, nenhum Android).
- **B11:** `watch_unchanged` é apenas observação de escopo limitado; não demonstra isolamento global nem autentica a correlação B10/B11.
- **R07:** MapIDs físicos, conflitos regionais e reservas ainda não comprovados.
- **R08:** direitos individuais sobre assets, PNGs, eventos e PBS ainda não avaliados.
- **R09:** é gate regional global `PENDING`, **sem links diretos a qualquer caso**. Não aumenta o total G12, não cria um 21º critério nem autoriza QA por plataforma.

### Invariantes regionais obrigatórios

| Plataforma | Casos | Bloqueios por caso | Resultado |
| --- | ---: | --- | --- |
| Windows | 43 | B09, B10, B11, R07, R08 | Pendente, sem autorização |
| Android/JoiPlay | 1 | B09, R07, R08 | Pendente, sem autorização |

O gate de QA Android é próprio; evidência de Windows Sandbox nunca serve para autorizá-lo. L11 documental também **não é** o gate local Android L05 da G12.

## Os 20 critérios L04 vinculados

| Critério | Origem | Casos relacionados | Estado |
| --- | --- | ---: | --- |
| `B09_ORIGIN` | B09 | 44 | Não revisado |
| `B09_CLONE` | B09 | 44 | Não revisado |
| `B09_ASSETS` | B09 | 44 | Não revisado |
| `B09_RECEIPT` | B09 | 44 | Não revisado |
| `B10_LINK` | B10 | 43 | Não revisado |
| `B10_READONLY` | B10 | 43 | Não revisado |
| `B10_OFFLINE` | B10 | 43 | Não revisado |
| `B10_PLATFORM` | B10 | 43 | Não revisado |
| `B11_SESSION` | B11 | 43 | Não revisado |
| `B11_SCOPE` | B11 | 43 | Não revisado |
| `B11_DIFFERENCE` | B11 | 43 | Não revisado |
| `B11_LIMIT` | B11 | 43 | Não revisado |
| `R07_NATIVE` | R07 | 44 | Não revisado |
| `R07_REGIONS` | R07 | 44 | Não revisado |
| `R07_CONFLICT` | R07 | 44 | Não revisado |
| `R07_TOPOLOGY` | R07 | 41 | Não revisado |
| `R08_LICENSE` | R08 | 44 | Não revisado |
| `R08_GRAPHICS` | R08 | 44 | Não revisado |
| `R08_EVENTS` | R08 | 44 | Não revisado |
| `R08_PBS` | R08 | 21 | Não revisado |

## Os 44 casos oficiais G12/CH20

| # | Identificador | Categoria | Plataforma | Critérios | Bloqueios | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `ball-TURTWIG` | starter | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 2 | `barry-TURTWIG-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 3 | `barry-TURTWIG-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 4 | `barry-TURTWIG-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 5 | `barry-TURTWIG-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 6 | `save-reload-TURTWIG` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 7 | `ball-CHIMCHAR` | starter | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 8 | `barry-CHIMCHAR-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 9 | `barry-CHIMCHAR-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 10 | `barry-CHIMCHAR-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 11 | `barry-CHIMCHAR-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 12 | `save-reload-CHIMCHAR` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 13 | `ball-PIPLUP` | starter | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 14 | `barry-PIPLUP-normal-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 15 | `barry-PIPLUP-normal-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 16 | `barry-PIPLUP-master-win` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 17 | `barry-PIPLUP-master-loss` | barry | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 18 | `save-reload-PIPLUP` | save_reload | windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 19 | `warp-SN_BEDROOM_TO_1F` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 20 | `npc-SN_NPC_MOTHER` | npc | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 21 | `warp-SN_1F_TO_BEDROOM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 22 | `warp-SN_1F_TO_TWINLEAF` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 23 | `warp-SN_TOWN_TO_HOME` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 26 | `npc-SN_NPC_BARRY_INTRO` | npc | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | npc | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | npc | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | npc | windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | warp | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 40 | `regression-DECADES` | regression | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 41 | `regression-KANTO` | regression | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 42 | `regression-JOHTO` | regression | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 43 | `regression-HOENN` | regression | windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 44 | `android-joi-play` | android | android | 12 | B09, R07, R08 | Pendente |

## Executar somente auditoria de documentação pública no CI

```sh
python scripts/regions/audit_sinnoh_l11_traceability.py
python -m unittest discover -s tests -p 'test_sinnoh_l11_traceability.py' -v
```

O auditor usa exclusivamente arquivos **JSON públicos fixos** e rejeita argumentos de caminho, mudanças dos Git blobs, symlinks, submissão de saves e novas permissões. Nenhum Game.exe, Windows Sandbox, JoiPlay ou instalador é aberto; arquivos do PC do usuário permanecem fora do escopo.

## Barra técnica e pendências inalteradas

| Indicador | Situação |
| --- | --- |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos fisicamente aprovados | **0/20** |
| Testes nativos executados | **0/44** |
| Barras B/C/D | **0/13** |
| R07, R08, R09 | **Pendentes** |
| Isolamento global de saves B11 | **Não demonstrado** |
| MapIDs e licenças de assets | **Não aprovados** |
| Sinnoh | **planned — não jogável** |

A conclusão técnica de L11 significa apenas que os vínculos entre documentos públicos são coerentes. Próxima fase L12 deve continuar no modo documental, sem converter checks estáticos em aprovações nativas.
