# Sinnoh L06 — Roteiro público de revisão humana, 44 casos e bloqueios

**Issue [#182](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/182) — fase documental somente no GitHub.** A L06 NÃO autoriza Windows Sandbox, executável do jogo, Android/JoiPlay, instalação, download ou uso de saves. **L06 documental não é o gate L05 local Android da G12**.

## Entregas
- [Fila JSON versionada de 44 casos](../data/regions/sinnoh-l06-human-evidence-routing.json): IDs e critérios originais de L05/G12, pedidos codificados de revisão, fila Windows versus Android e bloqueio para cada caso.
- [Auditor fail-closed L06](../scripts/regions/audit_sinnoh_l06_human_evidence.py): revalida L05, L04 e G12 e compara integralmente o modelo imutável da L06 com o derivado dessas fontes.
- [Testes L06](../tests/test_sinnoh_l06_human_evidence.py): testes positivos, **65 cenários sintéticos negativos**, incluindo dados adulterados, aprovação fabricada, MapIDs, direitos, B11 e confusão entre plataformas.
- [Workflow do GitHub Actions](../.github/workflows/sinnoh-l06-public-human-review.yml): auditoria, suíte L06 e regressões L05/L04/L03/L02/L01/L00/G12, sem executar ambiente do usuário.

## Como um revisor humano deve tratar cada ficha

Uma ficha pública é um **pedido de revisão**, nunca evidência, certificado, decisão definitiva ou autorização nativa. Todos os 44 itens começam em `NOT_REVIEWED` / `KEEP_PENDING`. As ações **documentais possíveis para processamento em etapa futura** são:

| Ação | Significado e limite |
| --- | --- |
| `REQUEST_SANITIZED_DOCUMENTATION` | Solicitar evidência não sensível mediante autorização explícita fora do repositório |
| `REVIEW_DOCUMENTARY_ONLY` | Examinar a consistência de texto público sem atestar o host ou a origem privada |
| `BLOCK` | Apontar inconsistências ou pré-requisitos ausentes, sem criar permissão |
| `KEEP_PENDING` | Manter todos os bloqueios até ocorrer revisão humana independente (estado vigente) |

**Nenhuma ação altera automaticamente a ficha**, e uma decisão documental tampouco comprova teste do jogo. O auditor rejeita qualquer edição do manifesto L06 que tente promover uma ação para aprovada, forjar assinatura, aceitar evidência, alterar IDs ou acrescentar campos privados. Revisões futuras devem estabelecer um contrato novo e separado, mantendo sua própria trilha de auditoria.

## Critérios físicos exigidos, mas ainda não aprovados

### B09 — CLONE_PROVENANCE
- `B09_ORIGIN`: Check independent, authorized provenance of source game and donor materials. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B09_CLONE`: Compare physically observed clone inventory against the declared B09 count and SHA outside GitHub. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B09_ASSETS`: Review ownership and redistribution restrictions of the individual staged assets. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B09_RECEIPT`: Compare local receipt with dry-run and native clone in a separate human session. **Não revisado**; evidência de host/direitos não disponível no GitHub.

### B10 — WSB_CONFIGURATION
- `B10_LINK`: Independently confirm that the B10 configuration belongs to the reviewed B09 clone. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B10_READONLY`: Inspect WSB mount paths and read-only flags locally without uploading those paths. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B10_OFFLINE`: Inspect disabled network, clipboard, autostart and guest mapping on the actual host. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B10_PLATFORM`: Verify host Windows Sandbox compatibility and isolation separately from a config JSON. **Não revisado**; evidência de host/direitos não disponível no GitHub.

### B11 — LIMITED_SAVE_SCOPE
- `B11_SESSION`: Correlate B11 with its B10 guest session outside the public repository. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B11_SCOPE`: Review actual engine save directories and completeness of the monitored scopes locally. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B11_DIFFERENCE`: Inspect before/after results and any differences without publishing save identifiers. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `B11_LIMIT`: Explicitly reject watch_unchanged as proof of global save isolation. **Não revisado**; evidência de host/direitos não disponível no GitHub.

### R07 — REGIONAL_MAPID_RESERVATIONS
- `R07_NATIVE`: Verify physical MapInfos and ownership of occupied native MapIDs. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R07_REGIONS`: Confirm future regional reservations including Kanto, Johto, Hoenn and planned regions. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R07_CONFLICT`: Independently inspect conflicting and candidate map IDs before approving any allocation. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R07_TOPOLOGY`: Verify nine symbolic Twinleaf bindings and sixteen real transfers in the isolated clone. **Não revisado**; evidência de host/direitos não disponível no GitHub.

### R08 — ASSET_RIGHTS_AND_BINDINGS
- `R08_LICENSE`: Review per-asset source provenance and express permission/redistribution scope. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R08_GRAPHICS`: Inspect fourteen real PNGs and renderer compatibility without uploading copyrighted files. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R08_EVENTS`: Check physical maps, handlers, collision and warp connections after rights approval. **Não revisado**; evidência de host/direitos não disponível no GitHub.
- `R08_PBS`: Verify real authored PBS compilation and Berry/Rowan event contracts in isolated QA. **Não revisado**; evidência de host/direitos não disponível no GitHub.

### Distinção de plataformas
- **43 casos Windows:** precisam examinar B09 (origem/clone), B10 (configuração e isolamento de VM), B11 (escopo e diferença dos diretórios de save), R07 (reservas e topologia) e R08 (direitos e conteúdo), sempre através de revisão externa independente e posterior autorização nativa separada.
- **1 caso Android/JoiPlay:** precisa da origem B09, reservas R07 e direitos R08, além de perfil/QA de dispositivo próprios em um gate futuro. **B10/B11 Windows não são transferíveis para Android**.
- B11 com pasta sem alterações não demonstra isolamento global; uma comparação de recibos não prova autoria de clone; um MapID candidato não é reserva real; ausência de objeção a assets não equivale a licença.

## Fila completa dos 44 casos CH20/G12

A coluna de bloqueios é derivada exatamente da L05. A lista individual de todos os códigos de documentação (`REQUEST_<criterio>` e `REVIEW_<tipo>`) está no JSON, em cada ficha. As verificações por plataforma só descrevem como solicitar análise futura; não devem ser interpretadas como testes já realizados.

| # | ID CH20/G12 | Categoria | Fila | Bloqueios | Situação |
| ---: | --- | --- | --- | --- | --- |
| 1 | `ball-TURTWIG` | starter | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 2 | `barry-TURTWIG-normal-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 3 | `barry-TURTWIG-normal-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 4 | `barry-TURTWIG-master-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 5 | `barry-TURTWIG-master-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 6 | `save-reload-TURTWIG` | save_reload | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 7 | `ball-CHIMCHAR` | starter | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 8 | `barry-CHIMCHAR-normal-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 9 | `barry-CHIMCHAR-normal-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 10 | `barry-CHIMCHAR-master-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 11 | `barry-CHIMCHAR-master-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 12 | `save-reload-CHIMCHAR` | save_reload | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 13 | `ball-PIPLUP` | starter | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 14 | `barry-PIPLUP-normal-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 15 | `barry-PIPLUP-normal-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 16 | `barry-PIPLUP-master-win` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 17 | `barry-PIPLUP-master-loss` | barry | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 18 | `save-reload-PIPLUP` | save_reload | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 19 | `warp-SN_BEDROOM_TO_1F` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 20 | `npc-SN_NPC_MOTHER` | npc | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 21 | `warp-SN_1F_TO_BEDROOM` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 22 | `warp-SN_1F_TO_TWINLEAF` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 23 | `warp-SN_TOWN_TO_HOME` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 24 | `warp-SN_TOWN_TO_BARRY_HOME` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 25 | `warp-SN_TOWN_TO_ROUTE201` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 26 | `npc-SN_NPC_BARRY_INTRO` | npc | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 27 | `warp-SN_BARRY_HOME_TO_TOWN` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 28 | `warp-SN_ROUTE201_TO_TOWN` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 29 | `warp-SN_ROUTE201_TO_LAKE` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 30 | `warp-SN_ROUTE201_TO_SANDGEM` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 31 | `npc-SN_NPC_ROWAN_BRIEFCASE` | npc | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 32 | `npc-SN_NPC_BARRY_BATTLE` | npc | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 33 | `warp-SN_LAKE_TO_ROUTE201` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 34 | `warp-SN_SANDGEM_TO_ROUTE201` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 35 | `warp-SN_SANDGEM_TO_ROWAN_LAB` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 36 | `warp-SN_SANDGEM_TO_ROUTE202` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 37 | `npc-SN_NPC_ROWAN_POKEDEX` | npc | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 38 | `warp-SN_ROWAN_LAB_TO_TOWN` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 39 | `warp-SN_ROUTE202_TO_SANDGEM` | warp | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 40 | `regression-DECADES` | regression | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 41 | `regression-KANTO` | regression | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 42 | `regression-JOHTO` | regression | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 43 | `regression-HOENN` | regression | Windows — revisão do host/VM futura | B09, B10, B11, R07, R08 | `KEEP_PENDING` |
| 44 | `android-joi-play` | android | Android/JoiPlay — revisão independente futura | B09, R07, R08 | `KEEP_PENDING` |

## Protocolo de handoff seguro

1. Conferir as **fontes públicas** L04, L05 e G12 e solicitar primeiro apenas documentos **sanitizados**, sem nomes de usuário, endereços, logs de sessão privados, hashes identificáveis, arquivos de save, PNGs de terceiros, caminhos reais, tokens ou dados de direitos.
2. Um revisor autorizado deve conduzir **separadamente e fora do GitHub** a checagem de origem B09, configuração B10, sessão e abrangência B11, conflitos e reservas R07, licenciamento R08 e pendências R09. Dados autodeclarados não satisfazem revisão independente.
3. A trilha Windows e a Android deverão obter decisões e autorizações de QA nativa por processos próprios, **nunca** por edição da matriz L06. Nenhum comando de execução do jogo é produzido aqui.
4. Qualquer divergência, evidência inconclusiva ou dependência faltante resulta em `BLOCK` ou `KEEP_PENDING` no protocolo documental futuro, **sem promover status atual**.

## Auditoria em máquina CI isolada do repositório

A verificação pública pode ser executada nos jobs do GitHub Actions ou por Python com a cópia **já disponível do código público**:

```sh
python scripts/regions/audit_sinnoh_l06_human_evidence.py
python -m unittest discover -s tests -p 'test_sinnoh_l06_human_evidence.py' -v
```

O auditor não aceita parâmetro de evidência, não procura arquivos locais, não abre VM ou JoiPlay, não faz uploads. Seu resultado exibe **somente IDs públicos, códigos de critérios e flags de bloqueio**. O workflow não armazena arquivos privados e não produz capturas de runtime.

## Indicadores preservados

| Indicador | Estado |
| --- | --- |
| Relatórios locais recebidos | **0/5** |
| Critérios humanos independentes aprovados | **0/20** |
| Testes nativos Windows/Android concluídos | **0/44** |
| Grupos B/C/D | **0/13** |
| R07 / R08 / R09 | **Pendentes** |
| Sinnoh jogável | **Não — planned** |
| Permissões Windows Sandbox / JoiPlay / Game.exe | **Não concedidas** |

**Conclusão L06:** roteiro e bloqueios documentais versionados; **nenhuma** aprovação física ou nativa concedida. **Próxima fase documental segura L07:** propor um painel público de triagem de pendências e integridade de decisões simuladas, sem permitir aprovações humanas ou liberar jogos.
