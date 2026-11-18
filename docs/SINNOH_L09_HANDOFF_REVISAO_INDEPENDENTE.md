# Sinnoh L09 — Handoff público para revisão humana independente

**Issue #192, PR L09.** Esta fase organiza a solicitação e revisão **documental futura**. Nenhum ser humano revisou ou aprovou aqui a origem física do jogo, arquivos privados, licença de assets, isolamento da VM ou execução nativa. Todo resultado é um inventário de metadados públicos e permanece bloqueado.

## Entregas e fontes de origem verificáveis

- [Pacote JSON de revisão L09](../data/regions/sinnoh-l09-independent-public-handoff.json): 44 fichas oficiais com checklist de IDs e 20 tarefas por critério L04, todos `NOT_REVIEWED`, `KEEP_PENDING` e `pending`; nenhuma permissão.
- [Auditor L09 fail-closed](../scripts/regions/audit_sinnoh_l09_public_handoff.py): executa a auditoria L08 de novo (que audita L07/L06/L05/L04/G12), fixa 3 Git blobs públicos, compara integralmente o pacote com a versão calculada a partir do snapshot e do checklist e rejeita estados/evidências falsos.
- [Testes L09](../tests/test_sinnoh_l09_public_handoff.py): **107 casos sintéticos negativos** e 10 verificações positivas, inclusive mudanças de IDs, critérios, plataforma, assinaturas, mapas, licenças, fontes e direitos.
- [Workflow CI L09](../.github/workflows/sinnoh-l09-public-independent-handoff.yml): três jobs — integridade L09, regressões L08/L07/L06/L05/L04/L03/L02/L01/L00/G12 e testes de leitura do painel L07.

As identidades dos arquivos públicos são **SHA-1 de objeto Git**, não hashes de saves ou de clones privados:

| Referência | Commit / Git blob público |
| --- | --- |
| Baseline L07 | `d98033b362dac82347e0d97cb5606870eaa70b22` |
| Merge L08 | `8617ef47ea6745920cb6fe4be251982380d7628d` |
| L08 (`data/regions/sinnoh-l08-pinned-snapshot.json`) | `63f520c26cdb13d88c6e027ec371e2a2de7d0b30` |
| L08_DIFF (`data/regions/sinnoh-l08-semantic-diff.json`) | `e8198e0b94d45c187d295d416aaec63241793a7b` |
| L04 (`data/regions/sinnoh-l04-independent-review-checklist.json`) | `cffdaac87c0dc542b99dd9bdebe54d49038d940d` |

Os bytes fixos do L08 não comprovam que a instalação de Windows ou Android exista, que a VM tenha sido iniciada ou que itens tenham licenciamento válido. Esse pacote não inclui tokens de execução, comandos para ativação da Sandbox ou caminhos privados.

## Protocolo de revisão independente: o que falta verificar

1. **B09 — origem e clone:** exigir revisão por pessoa autorizada em ambiente privado apropriado; recibos de origem autodeclarados não bastam. Não transferir paths/identificadores de clone ao repositório.
2. **B10 — Windows Sandbox:** revisão independente de configuração de montagem em modo somente leitura, rede e recursos, compatibilidade host/guest e vínculo com o material B09. Esta é uma exigência da fila Windows, não do Android.
3. **B11 — isolamento limitado:** conferir escopo real das pastas de save em inspeção autorizada, correlação da sessão B10/B11 e diferenças antes/depois. O fato de um diretório monitorado não mudar **não** prova isolamento global dos saves nem que todos os possíveis diretórios tenham sido monitorados.
4. **R07 — reservas e mapas:** confirmar a ocupação dos MapIDs reais e reservas de todas as regiões, conflitos e topologia somente em processo futuro autorizado. IDs candidatos e nomes simbólicos não são reservas físicas.
5. **R08 — direitos e bindings:** revisão humana independente da licença/escopo de cada asset, gráficos PNG de terceiros, mapa, eventos e PBS. Quantidade de arquivos não certifica direito de distribuição ou funcionamento.
6. **R09 e QA real:** continuam pendentes, com gate próprio para Windows e Android, revisão/autorização separada e 44 testes executados por processo apropriado. A L09 não faz nenhuma dessas atividades.

O painel público não aceita upload e a auditoria não lê saves, PNGs, ROM, ZIP de jogo, licenças privadas ou evidência local.

### Ações de triagem possíveis em etapas futuras

| Código de decisão documental | Significado |
| --- | --- |
| `REQUEST_SANITIZED_DOCUMENTATION` | Solicitar apenas documentação pública sanitizada, sem arquivos privados |
| `REVIEW_DOCUMENTARY_ONLY` | Analisar a coerência dos dados públicos, sem atestar prova física |
| `BLOCK` | Assinalar uma inconsistência documental |
| `KEEP_PENDING` | Manter dependências pendentes, única decisão vigente em L09 |

O catálogo de ações **não é um formulário de autorização**. Revisões humanas, se forem futuramente necessárias, ocorrerão fora deste repositório, com autorização e escopos próprios. Nenhuma edição unilateral do JSON L09 pode registrar `APPROVED`, `passed`, `reviewed` nem aceitar evidências reais.

## Checklist dos 20 critérios L04

A contagem de casos representa apenas vínculos técnicos, não comprovação.

| Critério | Bloco | Exigência pública | Casos ligados | Windows / Android | Estado |
| --- | --- | --- | ---: | --- | --- |
| `B09_ORIGIN` | B09 | Check independent, authorized provenance of source game and donor materials | 44 | 43 / 1 | Não revisado |
| `B09_CLONE` | B09 | Compare physically observed clone inventory against the declared B09 count and SHA outside GitHub | 44 | 43 / 1 | Não revisado |
| `B09_ASSETS` | B09 | Review ownership and redistribution restrictions of the individual staged assets | 44 | 43 / 1 | Não revisado |
| `B09_RECEIPT` | B09 | Compare local receipt with dry-run and native clone in a separate human session | 44 | 43 / 1 | Não revisado |
| `B10_LINK` | B10 | Independently confirm that the B10 configuration belongs to the reviewed B09 clone | 43 | 43 / 0 | Não revisado |
| `B10_READONLY` | B10 | Inspect WSB mount paths and read-only flags locally without uploading those paths | 43 | 43 / 0 | Não revisado |
| `B10_OFFLINE` | B10 | Inspect disabled network, clipboard, autostart and guest mapping on the actual host | 43 | 43 / 0 | Não revisado |
| `B10_PLATFORM` | B10 | Verify host Windows Sandbox compatibility and isolation separately from a config JSON | 43 | 43 / 0 | Não revisado |
| `B11_SESSION` | B11 | Correlate B11 with its B10 guest session outside the public repository | 43 | 43 / 0 | Não revisado |
| `B11_SCOPE` | B11 | Review actual engine save directories and completeness of the monitored scopes locally | 43 | 43 / 0 | Não revisado |
| `B11_DIFFERENCE` | B11 | Inspect before/after results and any differences without publishing save identifiers | 43 | 43 / 0 | Não revisado |
| `B11_LIMIT` | B11 | Explicitly reject watch_unchanged as proof of global save isolation | 43 | 43 / 0 | Não revisado |
| `R07_NATIVE` | R07 | Verify physical MapInfos and ownership of occupied native MapIDs | 44 | 43 / 1 | Não revisado |
| `R07_REGIONS` | R07 | Confirm future regional reservations including Kanto, Johto, Hoenn and planned regions | 44 | 43 / 1 | Não revisado |
| `R07_CONFLICT` | R07 | Independently inspect conflicting and candidate map IDs before approving any allocation | 44 | 43 / 1 | Não revisado |
| `R07_TOPOLOGY` | R07 | Verify nine symbolic Twinleaf bindings and sixteen real transfers in the isolated clone | 41 | 40 / 1 | Não revisado |
| `R08_LICENSE` | R08 | Review per-asset source provenance and express permission/redistribution scope | 44 | 43 / 1 | Não revisado |
| `R08_GRAPHICS` | R08 | Inspect fourteen real PNGs and renderer compatibility without uploading copyrighted files | 44 | 43 / 1 | Não revisado |
| `R08_EVENTS` | R08 | Check physical maps, handlers, collision and warp connections after rights approval | 44 | 43 / 1 | Não revisado |
| `R08_PBS` | R08 | Verify real authored PBS compilation and Berry/Rowan event contracts in isolated QA | 21 | 20 / 1 | Não revisado |

## Pacote individual dos 44 casos nativos

| # | ID verdadeiro G12/CH20 | Categoria | Fila | Bloqueios | Critérios | Estado |
| ---: | --- | --- | --- | --- | ---: | --- |
| 1 | `ball-TURTWIG` | starter | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 2 | `barry-TURTWIG-normal-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 3 | `barry-TURTWIG-normal-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 4 | `barry-TURTWIG-master-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 5 | `barry-TURTWIG-master-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 6 | `save-reload-TURTWIG` | save_reload | Windows | B09, B10, B11, R07, R08 | 18 | Pendente |
| 7 | `ball-CHIMCHAR` | starter | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 8 | `barry-CHIMCHAR-normal-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 9 | `barry-CHIMCHAR-normal-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 10 | `barry-CHIMCHAR-master-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 11 | `barry-CHIMCHAR-master-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 12 | `save-reload-CHIMCHAR` | save_reload | Windows | B09, B10, B11, R07, R08 | 18 | Pendente |
| 13 | `ball-PIPLUP` | starter | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 14 | `barry-PIPLUP-normal-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 15 | `barry-PIPLUP-normal-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 16 | `barry-PIPLUP-master-win` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 17 | `barry-PIPLUP-master-loss` | barry | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 18 | `save-reload-PIPLUP` | save_reload | Windows | B09, B10, B11, R07, R08 | 18 | Pendente |
| 19 | `warp-SN_BEDROOM_TO_1F` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 20 | `npc-SN_NPC_MOTHER` | npc | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 21 | `warp-SN_1F_TO_BEDROOM` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 22 | `warp-SN_1F_TO_TWINLEAF` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 23 | `warp-SN_TOWN_TO_HOME` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 26 | `npc-SN_NPC_BARRY_INTRO` | npc | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | npc | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | npc | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | npc | Windows | B09, B10, B11, R07, R08 | 20 | Pendente |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | warp | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 40 | `regression-DECADES` | regression | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 41 | `regression-KANTO` | regression | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 42 | `regression-JOHTO` | regression | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 43 | `regression-HOENN` | regression | Windows | B09, B10, B11, R07, R08 | 19 | Pendente |
| 44 | `android-joi-play` | android | Android/JoiPlay | B09, R07, R08 | 12 | Pendente |

### Separação de plataformas

A fila Windows possui 43 casos e requer pré-condições B09/B10/B11/R07/R08. O caso Android/JoiPlay possui **1** ficha, com revisão de dispositivo independente B09/R07/R08 e sem transferência indevida das provas de Sandbox B10/B11. Este L09 documental **não** é a etapa local Android L05 da G12.

## Comando seguro para auditar somente contratos públicos

```sh
python scripts/regions/audit_sinnoh_l09_public_handoff.py
python -m unittest discover -s tests -p 'test_sinnoh_l09_public_handoff.py' -v
```

O script aceita somente entradas **fixas do repositório**, rejeita qualquer argumento de caminho, confere identidades de objetos Git com os bytes públicos e não efetua conexões de rede, leitura dos diretórios de usuário, execução de jogo, instalação nem uploads. Um resultado de sucesso prova **apenas consistência de documentação**.

## Indicadores que não podem avançar pela L09

| Indicador | Valor |
| --- | --- |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos fisicamente aprovados | **0/20** |
| Testes nativos executados Windows/Android | **0/44** |
| Barras B/C/D | **0/13** |
| R07, R08, R09 | **Pendentes** |
| Isolamento global de save B11 | **Não comprovado** |
| Direitos/MapIDs | **Não aprovados / não reservados** |
| Game.exe / Windows Sandbox / JoiPlay | **Não executados / não autorizados** |
| Sinnoh no jogo | **planned — não jogável** |

A conclusão documental de L09 deve criar a issue L10 somente após validação CI e merge, mantendo separadas a consistência dos artefatos GitHub e a futura revisão física independente.
