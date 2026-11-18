# Sinnoh L07 — Triagem pública estática dos 44 casos × 20 critérios

**Issue [#186](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/186).** Entrega **exclusivamente documental**, com metadados públicos versionados e dashboard estático com filtros. Não é homologação, não comprova proveniência física ou direitos, não reserva MapIDs e não autoriza executar Game.exe, Windows Sandbox, JoiPlay nem atualizar/instalar o jogo.

## Entregas e proveniência

- [Fonte pública L07](../data/regions/sinnoh-l07-public-triage.json) e [espelho público no site](../site/public/data/sinnoh-l07-public-triage.json): representação **imutável**, equivalência byte a byte comprovada pelo teste Node; filas de 43 casos Windows e 1 Android, 20 critérios e status de bloqueio.
- [Painel filtrável de Sinnoh](../site/public/sinnoh-l07-triagem.html): publicação como página `/sinnoh-l07-triagem.html`, com pesquisa por ID, plataforma, categoria, critério L04 e bloqueio B09/B10/B11/R07/R08. Os filtros apenas escondem/exibem linhas; não gravam escolhas nem habilitam execução.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l07_public_triage.py): revalida a cadeia L06 → L05 → L04 → G12, valida os estados e todas as permissões, recompõe o contrato L07 com base nas fontes verdadeiras e exige igualdade estrutural/tipada tanto da fonte como do espelho usado pelo site.
- [Testes Python](../tests/test_sinnoh_l07_public_triage.py): **98 testes**, incluindo **88 cenários negativos sintéticos**, detectando aprovações inventadas, modificações de critérios, ID duplicado, reordenação, direitos R08 fictícios, MapIDs R07 declarados, B11 indevidamente universal, troca de plataforma, relatórios forjados, arquivos privados e tentativa de autorizar runtime.
- [Testes Node do portal](../site/tests/sinnoh-l07-triage.test.mjs): verificações adicionais de paridade do espelho, separação Windows/Android, filtros e presença da página pública sem execução/alteração de jogos.
- [Workflow dedicado](../.github/workflows/sinnoh-l07-public-triage.yml): 3 jobs (auditoria L07, regressões L06/L05/L04/L03/L02/L01/L00/G12 e compilação do portal).

## Quatro estados de triagem permitidos, nenhum de aprovação

A fonte L06 prevê somente `REQUEST_SANITIZED_DOCUMENTATION`, `REVIEW_DOCUMENTARY_ONLY`, `BLOCK` e `KEEP_PENDING` como **categorias de ação documental**. A L07 as exibe como vocabulário, não como ações executadas. **Todos os 44 casos continuam em `KEEP_PENDING`**, `NOT_REVIEWED` e `pending`; nenhuma revisão humana ou evidência foi recebida, alterada ou fabricada. A interface não envia formulários, não publica em GitHub e não altera a matriz.

### Segurança e limites

1. **Windows (43):** origem B09, configuração e vínculo de Sandbox B10, provas de escopo limitado B11 e revisões independentes R07/R08. `watch_unchanged` não comprova isolamento global de saves; a sessão B11 não está comprovadamente correlacionada à B10.
2. **Android/JoiPlay (1):** fila própria B09/R07/R08. A ausência de B10/B11 neste caso é intencional: a evidência de VM Windows nunca autoriza Android; o gate de QA Android futuro deverá ser independente. **L07 documental não é o gate local L05 da G12.**
3. **R07:** IDs candidatos sem confirmação física e reservas regionais verificadas continuam pendentes, assim como topologia e ligações nativas.
4. **R08:** fonte/licença de assets, gráficos PNG, eventos e PBS não estão independentemente aprovados. Nenhum asset privado foi acessado ou copiado.
5. **R09:** pendente, assim como validação nativa, oito ginásios, Elite/Cynthia e desbloqueio do jogo. A documentação não avança a jogabilidade.

### Indicadores imutáveis

| Indicador | Estado |
| --- | --- |
| Casos oficiais CH20/G12 | 44/44 listados, **0/44 executados** |
| Plataformas | **43 Windows + 1 Android**, trilhas isoladas |
| Critérios L04 | 20/20 listados, **0/20 aprovados** |
| Relatórios locais | **0/5 recebidos** |
| Barras B/C/D | **0/13** |
| R07/R08/R09 | **Pendentes** |
| Sinnoh | **planned — não jogável** |
| Autorização Game.exe, Sandbox, JoiPlay, instalação e uploads | **Negada/não concedida** |

## Casos G12 — fila pública completa

| # | Case ID oficial | Categoria | Plataforma | Critérios vinculados | Bloqueios | Estado |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `ball-TURTWIG` | starter | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 2 | `barry-TURTWIG-normal-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 3 | `barry-TURTWIG-normal-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 4 | `barry-TURTWIG-master-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 5 | `barry-TURTWIG-master-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 6 | `save-reload-TURTWIG` | save_reload | Windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 7 | `ball-CHIMCHAR` | starter | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 8 | `barry-CHIMCHAR-normal-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 9 | `barry-CHIMCHAR-normal-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 10 | `barry-CHIMCHAR-master-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 11 | `barry-CHIMCHAR-master-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 12 | `save-reload-CHIMCHAR` | save_reload | Windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 13 | `ball-PIPLUP` | starter | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 14 | `barry-PIPLUP-normal-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 15 | `barry-PIPLUP-normal-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 16 | `barry-PIPLUP-master-win` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 17 | `barry-PIPLUP-master-loss` | barry | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 18 | `save-reload-PIPLUP` | save_reload | Windows | 18 | B09, B10, B11, R07, R08 | Pendente |
| 19 | `warp-SN_BEDROOM_TO_1F` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 20 | `npc-SN_NPC_MOTHER` | npc | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 21 | `warp-SN_1F_TO_BEDROOM` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 22 | `warp-SN_1F_TO_TWINLEAF` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 23 | `warp-SN_TOWN_TO_HOME` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 26 | `npc-SN_NPC_BARRY_INTRO` | npc | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | npc | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | npc | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | npc | Windows | 20 | B09, B10, B11, R07, R08 | Pendente |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | warp | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 40 | `regression-DECADES` | regression | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 41 | `regression-KANTO` | regression | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 42 | `regression-JOHTO` | regression | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 43 | `regression-HOENN` | regression | Windows | 19 | B09, B10, B11, R07, R08 | Pendente |
| 44 | `android-joi-play` | android | Android | 12 | B09, R07, R08 | Pendente |

## Critérios de proveniência — dependências públicas

Contagens abaixo são **vínculos de documentação**, não provas de aprovação.

| Critério L04 | Bloco | Casos vinculados | Windows | Android | Revisão |
| --- | --- | ---: | ---: | ---: | --- |
| `B09_ORIGIN` | B09 | 44 | 43 | 1 | Não revisado |
| `B09_CLONE` | B09 | 44 | 43 | 1 | Não revisado |
| `B09_ASSETS` | B09 | 44 | 43 | 1 | Não revisado |
| `B09_RECEIPT` | B09 | 44 | 43 | 1 | Não revisado |
| `B10_LINK` | B10 | 43 | 43 | 0 | Não revisado |
| `B10_READONLY` | B10 | 43 | 43 | 0 | Não revisado |
| `B10_OFFLINE` | B10 | 43 | 43 | 0 | Não revisado |
| `B10_PLATFORM` | B10 | 43 | 43 | 0 | Não revisado |
| `B11_SESSION` | B11 | 43 | 43 | 0 | Não revisado |
| `B11_SCOPE` | B11 | 43 | 43 | 0 | Não revisado |
| `B11_DIFFERENCE` | B11 | 43 | 43 | 0 | Não revisado |
| `B11_LIMIT` | B11 | 43 | 43 | 0 | Não revisado |
| `R07_NATIVE` | R07 | 44 | 43 | 1 | Não revisado |
| `R07_REGIONS` | R07 | 44 | 43 | 1 | Não revisado |
| `R07_CONFLICT` | R07 | 44 | 43 | 1 | Não revisado |
| `R07_TOPOLOGY` | R07 | 41 | 40 | 1 | Não revisado |
| `R08_LICENSE` | R08 | 44 | 43 | 1 | Não revisado |
| `R08_GRAPHICS` | R08 | 44 | 43 | 1 | Não revisado |
| `R08_EVENTS` | R08 | 44 | 43 | 1 | Não revisado |
| `R08_PBS` | R08 | 21 | 20 | 1 | Não revisado |

## Execução permitida de auditoria documental

No repositório clonado em máquina apropriada de desenvolvimento/CI, **sem acessar arquivos privados**, é possível validar a coerência dos metadados:

```sh
python scripts/regions/audit_sinnoh_l07_public_triage.py
python -m unittest discover -s tests -p 'test_sinnoh_l07_public_triage.py' -v
```

O script aceita apenas fontes **públicas e caminhos fixos**. Rejeita parâmetros de caminho ou arquivo fornecidos por usuários, não busca evidência local e não transmite dados. O CI é a validação de integridade documental, não a execução dos 44 casos.

**Handoff L08 recomendado:** congelamento de snapshot público referenciado por commit e relatório de diferenças de critérios/triagem sem promover gates humanos ou jogo. Criar uma issue separada após aprovação do CI/merge, mantendo explícita a etapa nativa pendente.
