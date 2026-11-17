# Sinnoh — acompanhamento de progresso

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Última atualização:** 17/11/2026  
**Fonte de verdade:** [data/regions/sinnoh-progress.json](../data/regions/sinnoh-progress.json).  
**Critério:** esta página separa entregáveis de código/documentação de fases que já rodam no jogo. **Barra cheia de preparação NÃO significa Sinnoh jogável.**

## Barra E — novas entregas diretas pelo ChatGPT na main

```text
████████████████████  20/20 (100%)
```

- **Concluídas:** 20 (**CH01–CH20**; trabalho direto pelo chat encerrado no escopo estático).
- **Parciais:** 0 (**as 44 observações nativas continuam pendentes em trilha separada**).
- **Pendentes:** 0.
- **Fonte de verdade:** `chat_direct_workstream` em [sinnoh-progress.json](../data/regions/sinnoh-progress.json).
- **Mapeamento:** [SINNOH_MAPEAMENTO_EXECUCAO_CHAT_MAIN_2026-11-16.md](SINNOH_MAPEAMENTO_EXECUCAO_CHAT_MAIN_2026-11-16.md).
- **CH02–CH05:** consistência de progresso e proteções de MapIDs/plugins legados.
- **CH06–CH07:** auditor de Twinleaf, flags, Poké Bolas físicas e save isolado.
- **CH08–CH09:** Barry, 70%/90% e integração E2E sintética até bundle.
- **CH10–CH11:** lançador QA seguro e permissões de oito insígnias/HMs de Sinnoh.
- **CH12–CH13:** modelos de evolução dinâmica e encontros simbólicos sem MapIDs ou taxas inventadas.
- **CH14:** 22 checkpoints Galactic/Cyrus/Liga/Hall of Fame, sem viagem física habilitada automaticamente.
- **CH15:** 13 treinadores de referência Platinum, 5 revanches históricas e PBS/Full Power sinalizados sem comprovação.
- **CH16:** 46 chaves musicais e fallback BlueMusic, sem instalar áudio ou hooks.
- **CH17:** novo guia do portal em **`/sinnoh`**, com abas para **120 áreas** (**91 com fase 3–10 documentada; 29 sem fase, mostradas em filtro “Fase a auditar”**), **40 treinadores de referência**, **8 ginásios, 4 Elite Four e Cynthia**, **8 itens HM e permissões por insígnia regional**, **22 checkpoints Galactic/Cyrus/Liga** e espécies candidatas de **21 áreas**. O [gerador](../site/scripts/sinnoh-guide.mjs) usa os catálogos CH11–CH16, publica somente no `site/dist/data/sinnoh-guide.json` durante o [build](../site/scripts/build.mjs) e rejeita flags falsas de jogabilidade, níveis/MapIDs inventados e vínculos PBS não verificados. A [interface](../site/src/assets/sinnoh-guide.js) está ligada às páginas Guias, Regiões, Localizações, Treinadores, Chefes e Liga, sempre com o aviso **“Planejada / Ainda não adicionado ao Game.exe/JoiPlay”**. **19 testes dedicados**, **108 testes completos do portal** e **347 testes Python isolados de Sinnoh** aprovados; [CI Portal 43979589575](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589575) e [CI Sinnoh 43979589757](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589757). [Documentação CH17](SINNOH_CH17_GUIAS_PORTAL_PLANEJADO.md).
- **CH18:** [mecanismo puro de busca, filtros, URLs e validação da fonte](../site/src/assets/sinnoh-search.js) e [interface aprimorada](../site/src/assets/sinnoh-guide.js) fornecem formulário GET com preservação de filtros, busca sem distinguir acentos, apoio a “Rota/Route”, filtros por fase (incluindo **29 sem fase**), espécies candidatas, referências de área dos treinadores, revanches Platinum e categorias de pendência. A nova aba **Pendências** apresenta sete grupos com contagens documentais (120 áreas, 40 treinadores, 13 equipes históricas, 8 HMs, 22 checkpoints, 21 áreas de encontro e 46 cues), todos **planned/a auditar**. Links contextuais ligam áreas, treinadores, ginásios↔HMs e Liga↔história, sem afirmar que exista NPC/evento físico. [29 novos testes positivos/negativos](../site/tests/sinnoh-search.test.mjs) exigem encoding de URL/HTML, buscas vazias, filtros incorretos com fallback seguro, bloqueio de MapIDs, taxas, níveis, times, badge pickup, músicas e estados jogáveis inventados. [CI Portal 43981753762](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753762): **build e 137/137 testes** aprovados; [CI Sinnoh 43981753812](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753812): **29/29 testes CH18**, **137 testes completos do portal** e **347/347 Python isolados** aprovados. [Documentação CH18](SINNOH_CH18_BUSCA_FILTROS_PENDENCIAS_SITE.md).
- **CH19 (concluída):** [executor de regressão isolada](../scripts/regions/sinnoh_ci_ch19.py), [12 testes negativos](../tests/test_sinnoh_ci_ch19.py) e [workflow Python/Ruby independente](../.github/workflows/sinnoh-ch19.yml) publicados e verificados pela [execução 43985365758](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365758): **374/374 testes Python**, **7/7 verificações Python** e **22/22 verificações Ruby**. Os dois artifacts JSON/MD foram baixados e conferidos (zero falhas; testes apenas offline); [PR #65](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/65) mesclado à `main` em `4bbc767`. O [documento CH19](SINNOH_CH19_CI_PYTHON_RUBY_ISOLADO.md) separa o CI Sinnoh de erros do pipeline geral, sem declarar Game.exe/JoiPlay. **Barra E 20/20 (100%)**.
- **CH20 (concluída em escopo estático):** [pré-voo Android/JoiPlay](../scripts/regions/audit_sinnoh_android_ch20.py), [18 testes CH20](../tests/test_sinnoh_android_ch20.py), [12 testes do auditor de evidências](../tests/test_sinnoh_playtest_audit.py) e [workflow exclusivo CH20](../.github/workflows/sinnoh-ch20.yml) publicados na `main` pelo [PR #66](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/66), merge `c7c8cdd`. [CI 43986405854](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43986405854) **18/18 + 12/12 testes aprovados**, com [relatórios JSON + Markdown e hashes conferidos](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43986405854/artifacts/14284479390). [Relatório CH20](SINNOH_CH20_JOIPLAY_PREFLIGHT.md): **44 IDs de casos completos, 0/44 observados no Game.exe/JoiPlay**, dados do jogo reais não fornecidos. Conclusão da Barra E **20/20 (100%)** não aprova jogo nativo nem altera as barras A/B/C/D.
- **Critério:** tarefas só entram como `done` com arquivos publicados na `main` e validação de CI compatível com seu escopo.

**Limitações:** o build do portal **não comprova publicação externa em Vercel**, nem mapas, batalhas, Pokémon selvagens, itens ou música nativa em Sinnoh. Nenhum Game.exe/JoiPlay foi executado. **Barra A 25/32 (78%)**, **B/C/D 0/13** permanecem intactas.

## Barra A — desenvolvimento aqui no GitHub

```text
████████████████░░░░  25/32 (78%)
```

- **Concluídas:** 25 entregas verificadas no repositório (incluindo S08, S10, S11, S12, S17, S18, S19, S20, S21, S22, S23, S26, S27, S28, S29 e S30).
- **Parciais:** 4 (não contam como concluídas até atingirem o próprio critério).
- **Pendentes:** 3.
- **Total:** 32 entregas no inventário [JSON](../data/regions/sinnoh-progress.json).
- **Restam 7 para a barra de desenvolvimento** (inclui parciais).

## S27 — guias planejados no site (concluída)

A [entrega S27](SINNOH_S27_GUIAS_PORTAL_ACEITE.md) contabiliza o trabalho de **portal web**, não uma região jogável. O guia `/sinnoh` já usa os catálogos CH11–CH16 e a navegação/pesquisa CH17–CH18; agora diferencia explicitamente **guia publicado no portal** de **mapas/eventos ainda não instalados no jogo**. Os [testes de aceite S27](../site/tests/sinnoh-s27-development.test.mjs) validam oito abas, 120 áreas, 40 treinadores, 13 líderes/Liga, 8 HMs, 22 checkpoints e salvaguardas contra anúncios falsos de MapIDs, níveis, PBS, encontros ou jogo funcional. A aprovação da S27 depende do build e da suíte completa do site em CI.

**Situação nativa preservada:** 0 mapas de Sinnoh certificados; Game.exe/JoiPlay não executados nesta entrega. A S27 avançou a Barra A para **9/32 (28%)**, a S29 para **10/32 (31%)**, a S30 para **11/32 (34%)**, a S28 para **12/32 (37%)**, a S10 para **13/32 (40%)**, a S11 para **14/32 (43%)** e a S12 para **15/32 (46%)**; após a S08, o total era **16/32 (50%)**; com a S26, o total era **17/32 (53%)**; após a S17, eram **18/32 (56%)**; com a S18, eram **19/32 (59%)**; após a S19, eram **20/32 (62%)**; com a S20, eram **21/32 (65%)**; com a S21, eram **22/32 (68%)**; com a S22, eram **23/32 (71%)**; com a S23, o total foi **24/32 (75%)**; após a S24, o total é **25/32 (78%)**. Isso não torna as fases S13–S23 jogáveis nem altera B/C/D.

## S24 — música contextual: catálogo S24 concluído em código

A [matriz S24](../data/regions/sinnoh-music-s24.json) descreve 46 chaves musicais por cenário e guarda, com [auditor](../scripts/music/audit_sinnoh_music_s24.py) e [19 testes](../tests/test_sinnoh_s24_music.py) que rejeitam licença, MapID, áudio ou hook inventados. **Nenhuma faixa foi copiada ou instalada**, e BlueMusic não foi modificado. [Aceite S24](SINNOH_S24_CATALOGO_CENARIOS_ACEITE.md).

**Após CI, Barra A 25/32 (78%)**, 4 parciais e 3 pendentes, E 20/20, B/C/D 0/13 e 44 observações nativas pendentes. **S25 (integração efetiva com áudio licenciado) ainda não foi realizada.**

## S29 — níveis dinâmicos sem valores fixos no portal (concluída)

A [S29 — aceite dos níveis dinâmicos](SINNOH_S29_NIVEIS_DINAMICOS_PORTAL_ACEITE.md) conecta os dados de BlueCampaign e BlueEvolutionScaling ao guia de Sinnoh: em todas as oito abas o portal deixa claro que **Normal = 70% e Master = 90% do maior nível da equipe, desconsiderando ovos**, sem presumir um nível exato para líderes, NPCs ou encontros. Insígnias controlam permissões regionais e esmeraldas participam da progressão, mas **não existe um campo numérico de cap regional confirmado** no save auditado. O site não lê o save real.

O [validador web](../site/src/assets/sinnoh-search.js) barra dados falsamente jogáveis e números de nível não auditados; os [8 testes S29](../site/tests/sinnoh-s29-dynamic-levels.test.mjs) cobrem apresentação, contratos e tentativas de falsificação. A S29 teve build e suíte completa do portal aprovados em CI sem certificar gameplay. Na conclusão da S29, **Barra A 10/32 (31%)**; após S30, **11/32 (34%)**; Barra E 20/20, B/C/D 0/13.

## S30 — suíte automatizada offline (concluída após CI)

A [S30](SINNOH_S30_SUITE_AUTOMATIZADA_ACEITE.md) unifica em um [workflow GitHub Actions](../.github/workflows/sinnoh-s30.yml) **cinco jobs independentes**: manifesto auditável, testes Python, regressões Ruby, build/suíte do portal e pré-voo Android estático. O [manifesto de cobertura](../scripts/regions/audit_sinnoh_s30_suite.py) inspeciona presença de testes, arquivos e hashes e rejeita declaração de jogabilidade sem QA S31; [11 novos testes negativos](../tests/test_sinnoh_s30_suite.py) impedem faltas e falsa certificação.

**Critério da S30:** CI com todos os cinco jobs aprovados e documentação versionada. Aprovado apenas o escopo **offline**, sem Game.exe, JoiPlay, MapIDs, saves ou equipamentos reais. **Barra A 11/32 (34%)**, 6 parciais, 15 pendentes. **B/C/D 0/13** e **44 casos de QA nativo** permanecem sem execução.

## S28 — catálogo histórico de times no site (concluído após CI)

A [S28](SINNOH_S28_CATALOGO_TIMES_REFERENCIAS.md) fortalece o guia de Sinnoh com **13 equipes históricas** da fonte CH15: oito líderes, Elite Four e Cynthia, incluindo **cinco revanches documentais** da Liga. O gerador do portal diferencia composição Platinum, revanche histórica, Full Power Blue **não verificado** e PBS nativo **não compilado**. Os **40 treinadores gerais** continuam sem times confirmados e não recebem formações inventadas.

Os [10 testes S28](../site/tests/sinnoh-s28-trainer-teams.test.mjs) conferem composição, origem, ordem, integridade HTML e testes negativos para níveis fixos, times adulterados e aprovação falsa de Full Power/PBS. Após o CI do portal aprovado, a **Barra A 12/32 (37%)**; 6 tarefas parciais e 14 pendentes. Os gates de jogabilidade **B/C/D seguem 0/13**, Barra E 20/20 (100%) e os 44 casos nativos sem execução.

## S10 — lançador Windows experimental isolado (concluído em código após CI)

O [`SINNOH_JOGAR_EXPERIMENTAL.bat`](../SINNOH_JOGAR_EXPERIMENTAL.bat) foi adicionado à raiz do projeto para permitir **duplo clique no Windows** sem PowerShell. Ele chama o [Python de lançamento isolado](../scripts/regions/launch_sinnoh_qa.py) com seleção automática **de uma única** cópia privada `.blue-work/game-sinnoh-qa-<12 hex>`. O fluxo verifica hashes e perfil de save, bloqueia múltiplas cópias ou arquivos alterados, inicia somente a compilação pendente ou uma QA já estruturalmente verificada e **não usa `game/Game.exe` como fallback**. Sem cópia QA instalada, exibe um erro seguro.

A [S10](SINNOH_S10_LANCADOR_EXPERIMENTAL_ACEITE.md) inclui [15 testes negativos e positivos](../tests/test_sinnoh_s10_launcher.py) que **não executam o Game.exe real**, e cobertura na S30. Após os testes de CI aprovados, Barra A **13/32 (40%)**, 6 parciais e 13 pendentes. O lançador **não instala mapas**; S11, S12 e QA Windows/Android permanecem separadas. **B/C/D 0/13**, E 20/20 (100%); 44 observações nativas continuam não executadas.

## S11 — piloto de Sinnoh com saves isolados (concluído em código após CI)

A [S11](SINNOH_S11_PILOTO_SAVES_ISOLADOS_ACEITE.md) torna o isolamento dos saves do piloto **verificável em Python e em Ruby**. O [namespace privado](../scripts/regions/sinnoh_save_isolation.py) liga a pasta QA ao token exclusivo do `mkxp.json`, `Game.ini` e transação do instalador; o [verificador](../scripts/regions/install_sinnoh_qa_copy.py) barra dados adulterados ou caminhos de save customizados. A [inicialização Ruby](../scripts/regions/SinnohQAStart.rb) recusa carregamento de saves sem `blue_regions.initial=SINNOH` e `current=SINNOH`, mesmo quando outro save não tem origem regional. O [lançador S10](../scripts/regions/launch_sinnoh_qa.py) só inicia quando essa auditoria passar.

[13 testes S11](../tests/test_sinnoh_s11_save_isolation.py) e [testes Ruby](../tests/sinnoh_qa_start_runtime.rb) simulam saves estrangeiros, perfis trocados, token e diretório inseguros, sem executar `Game.exe` ou ler/modificar dados reais. **Aceite S11 é de código**: não há evidência de save/reload real ou piloto instalado. Após CI, **Barra A 14/32 (43%)**, 6 parciais e 12 pendentes. **B/C/D 0/13, E 20/20**; 44 casos nativos não executados.

## S12 — instalador isolado do piloto (concluído em código após CI)

A [entrega S12](SINNOH_S12_INSTALADOR_QA_ISOLADO_ACEITE.md) acrescenta o [BAT de instalação](../SINNOH_INSTALAR_EXPERIMENTAL.bat) com duplo clique e [orquestrador seguro](../scripts/regions/sinnoh_s12_installer.py) com simulação por padrão. Ele exige overlay + especificação privada auditados (mapas reais licenciados **não estão no GitHub**), rejeita duplicidade, tokens inconsistentes, arquivos adulterados e symlinks. Quando há fontes válidas, cria apenas uma cópia com nome exclusivo em `.blue-work/` e **sem saves herdados**; nunca substitui `game/`, não executa o `Game.exe` nem certifica jogo funcional. A transação existente realiza cópia temporária com verificação SHA-256 e rollback em falhas antes da publicação.

Os [16 testes S12](../tests/test_sinnoh_s12_installer.py) cobrem simulação sem gravação, criação de cópia sintética, bloqueios e rollback. Após CI de regressão do Sinnoh aprovado, **Barra A 15/32 (46%)**: 15 concluídas, 6 parciais e 11 pendentes. A Barra E permanece 20/20; B/C/D 0/13 e **44 casos nativos pendentes**. A instalação QA real requer mapas autorizados e permanece bloqueada sem esses insumos.

## S08 — integridade de recursos (concluída em código após CI)

O [auditor S08](../scripts/regions/audit_sinnoh_s08_resources.py) reúne a análise inerte de RXDATA, os transfers do grafo, referências de tilesets/autotiles, estrutura mínima de PNGs, consistência dos hashes SHA-256 do overlay e as dependências de scripts Ruby do piloto. Com fonte/overlay ausente, colisões, referências quebradas, gráficos inválidos ou plugins faltantes, **bloqueia sem gravar arquivos nem declarar conteúdo jogável**. O [instalador S12](../scripts/regions/sinnoh_s12_installer.py) agora exige essa auditoria antes de permitir a cópia QA privada.

Os [16 testes S08](../tests/test_sinnoh_s08_integrity.py), incluídos na matriz S30, cobrem análise sem gravação, adulterações, arquivos ausentes, gráficos e plugins, dados de fonte incompletos e proteção da cópia principal. **O aceite é somente de implementação/testes offline**, não substitui os mapas autorizados ou o teste real de renderização, colisão, áudio, save ou JoiPlay. [Documento de aceite](SINNOH_S08_INTEGRIDADE_RECURSOS_ACEITE.md). Após CI, **Barra A 16/32 (50%)**; 5 parciais, 11 pendentes. **B/C/D 0/13**, E 20/20 e 44 testes nativos ainda não executados.

## Entrega S26 e diagnóstico R07 — código e testes (após CI)

A [S26](SINNOH_S26_TESTES_MUSICA_ACEITE.md) consolida a regressão de **fallback musical, precedência de eventos, fade/loop sem ativos não licenciados e restauração**; o [novo teste Ruby](../tests/sinnoh_s26_music_regression.rb) valida os 46 cues e 11 cenários de transição com o BlueMusic existente, sem iniciar áudio. O runner CH19 executa a etapa e a S30 exige o arquivo. **S26 concluída em código; a S25 (integração nativa) e a S24 (licenças) não estão concluídas.**

A [ferramenta R07](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) ganhou um [BAT de duplo clique](../SINNOH_DIAGNOSTICAR_PENDENCIAS.bat) que identifica os **MapIDs instalados** e a **ausência/conflito de reservas futuras** de Kanto, Johto e Hoenn; o relatório vai para `.blue-work/sinnoh-diagnostics/`. São [16 testes Python](../tests/test_sinnoh_r07_reservations.py) sem modificar `game/` ou saves. **R07 ainda não pode ser assinalada como concluída** sem a fonte real, os manifestos verificados e uma aprovação local: S07 permanece `partial` (R01–R06, 6/9).

**Após CI, Barra A 17/32 (53%)**, 5 parciais e 10 pendentes; **B/C/D 0/13, E 20/20**. As 44 verificações nativas continuam pendentes.

## S17 — treinadores com balanceamento dinâmico (concluído em código após CI)

A [S17](SINNOH_S17_TREINADORES_DINAMICOS_ACEITE.md) amplia a prova de funcionamento do **runtime real compartilhado** [Campaign](../scripts/battle_polish/Campaign.rb), [Story](../scripts/battle_polish/Story.rb) e [EvolutionScaling](../scripts/battle_polish/EvolutionScaling.rb) por [testes de Battle em Ruby](../tests/sinnoh_s17_trainer_balance_runtime.rb): nível **70% Normal / 90% Master** arredondado para baixo e relativo ao maior membro **não-ovo**; evoluções regulares **depois** do nível final; elenco de líderes/Elite Four/Cynthia preservado; Master com quatro Pokémon para treinadores pequenos, nunca mais que **seis no lado oposto** em batalha dupla; PBS original, equipe do jogador e saves não alterados.

O [auditor S17](../scripts/regions/audit_sinnoh_s17_balance.py) e [10 testes negativos Python](../tests/test_sinnoh_s17_trainer_balance.py) comparam o [contrato S17](../data/regions/sinnoh-trainer-balance-s17.json) a CH12/CH15 e proíbem aprovação falsa de times históricos, MapIDs e níveis fixos. **A infraestrutura de battle scaling já existia; esta entrega valida sua aplicação a Sinnoh em fixtures e não instala NPCs/mapas.** Após CI, **Barra A 18/32 (56%)**, 5 parciais e 9 pendentes; E 20/20, B/C/D 0/13 e 44 casos nativos ainda não executados.

## S18 — encontros e evoluções selvagens progressivas (concluído em código após CI)

A [S18](SINNOH_S18_ENCONTROS_EVOLUCOES_ACEITE.md) verifica a escolha real de encontros em [EvolutionScaling.rb](../scripts/battle_polish/EvolutionScaling.rb), preservando **os slots e pesos PBS originais**, aplicando evoluções somente quando o maior nível **não-ovo** da equipe chega aos limiares nativos e às faixas de sorteio de **15%, 30%, 45% e 60%**. A regra de evolução de um Pokémon com duas fases exige rolagens separadas. Uma nova proteção não altera slots inválidos, em nível fora do máximo da engine ou já superiores à referência de progressão do jogador. O selector compartilhado continua compatível com Kanto, Johto, Hoenn e Decades.

O [teste Ruby de hook nativo](../tests/sinnoh_s18_wild_runtime.rb) exerce `WildEncounters` e verifica limiares, chance, espécies especiais, metadados originais, horário e recusa de encontros inválidos. O [auditor S18](../scripts/regions/audit_sinnoh_s18_wild.py), o [contrato S18](../data/regions/sinnoh-wild-s18.json) e [12 testes Python negativos](../tests/test_sinnoh_s18_wild.py) confirmam que **as 21 áreas CH13 são referências planejadas**, sem MapIDs, espécies/horários instalados, pesos, níveis nem PBS compilados. Drifloon/Rotom permanecem eventos especiais não instalados.

**Aceite de código após CI: Barra A 19/32 (59%)**, 5 parciais e 8 pendentes; E 20/20, B/C/D 0/13, 44 casos nativos pendentes. Esta entrega não instala mapas, não comprova aparição/captura de Pokémon selvagens nem altera saves ou PBS do jogo principal.

## S19 — Team Galactic, cinco checkpoints seguros (concluído em código após CI)

A [S19](SINNOH_S19_TEAM_GALACTIC_ACEITE.md) adiciona o [adaptador Ruby Galactic](../scripts/regions/SinnohGalacticContracts.rb), ligado ao ledger `sinnoh_ch14` existente. São cinco gates de história das fases 5–7: **Windworks → Mars → Jupiter (Forest) → Pastoria → Lagos**, distinguindo resultado `battle_won` de `scene_completed`. Os eventos seguem o prefixo ordenado CH14, sem duplicar progresso, modificar Kanto/Hoenn/Johto/Decades ou conceder itens, badges, viagens e equipes.

O registro de fontes nativas `VERIFIED_NATIVE_SOURCES` é **vazio e imutável**. Por isso nenhum desses checkpoints pode ser concluído por `record_from_native` antes da prova de MapID/callback compilado. O [runner Ruby](../tests/sinnoh_s19_galactic_runtime.rb) cobre cenários de batalha sintética, Victoria/derrota, pré-requisitos Forest, saves e corrupção; o [auditor S19](../scripts/regions/audit_sinnoh_s19_galactic.py) e [12 testes negativos Python](../tests/test_sinnoh_s19_galactic.py) validam CH14/cobertura e recusam dados nativos inventados. **S20 Cyrus/Giratina está concluída em contratos/testes offline, mas todos os mapas e eventos nativos continuam pendentes**.

Após CI, Barra A **20/32 (62%)** (5 parciais, 7 pendentes); E 20/20; B/C/D 0/13; 44 verificações nativas ainda não executadas. Concluir o código não equivale a instalar cutscenes ou batalhas da Team Galactic em Sinnoh.

## S20 — Cyrus, Spear Pillar, Distortion World e Giratina (concluída em código após CI)

A [S20](SINNOH_S20_CYRUS_DISTORTION_GIRATINA_ACEITE.md) implementa o [adaptador Ruby](../scripts/regions/SinnohDistortionContracts.rb) para **nove checkpoints da fase 8** que seguem a S19: Cyrus → Saturn → Mars → Jupiter → cena de Dialga/Palkia → puzzles do Mundo Distorcido → Cyrus final → encontro resolvido com Giratina → confirmação de retorno seguro. O contrato CH14 existente mantém o prefixo ordenado do save `sinnoh_ch14`; a primeira etapa exige insígnias Mine e Icicle. A distinção entre `battle_won`, `scene_completed`, `puzzles_solved`, `encounter_resolved` e `safe_return_confirmed` impede tratar uma conversa ou chegada ao mapa como vitória.

O registro `VERIFIED_NATIVE_SOURCES` permanece **vazio e congelado**. Assim, a rotina pública não pode aprovar eventos reais sem handlers auditados, e Giratina não vira uma captura obrigatória, premiação ou mudança de party. O [teste Ruby S20](../tests/sinnoh_s20_distortion_runtime.rb) exerce o CH14 e `BlueRegions` reais sobre dados sintéticos, incluindo saves corrompidos e outras regiões; o [auditor Python](../scripts/regions/audit_sinnoh_s20_distortion.py) e [16 testes negativos](../tests/test_sinnoh_s20_distortion.py) bloqueiam MapIDs, PBS, callbacks e retornos falsamente instalados.

**Após CI, Barra A 21/32 (65%)**, 5 tarefas parciais e 6 pendentes. **B/C/D 0/13**, E 20/20 e 44 verificações nativas ainda pendentes. **Nenhum** mapa do Mt. Coronet/Spear Pillar ou Mundo Distorcido, batalha Cyrus ou evento real de Giratina foi adicionado ao Game.exe ou JoiPlay.

## S21 — Elite Four, Cynthia e Hall of Fame (concluída em código após CI)

A [S21](SINNOH_S21_ELITE_CYNTHIA_HALL_OF_FAME_ACEITE.md) implementa um [adaptador Ruby](../scripts/regions/SinnohLeagueContracts.rb) com **oito checkpoints finais do CH14**: Volkner/Beacon, Barry com as oito insígnias, Aaron, Bertha, Flint, Lucian, Cynthia e Hall of Fame. A máquina de estados usa **o ledger `sinnoh_ch14` existente**, não inventa níveis fixos ou equipes PBS, não duplica a Liga e não concede badges/itens/teleportes.

**Cynthia vencida não é Hall of Fame confirmado**: só a etapa separada `engine_hall_of_fame_confirmed` pode registrar a Liga no ledger `leagues`, e a API pública permanece bloqueada com `VERIFIED_NATIVE_SOURCES = {}.freeze`. O [teste Ruby](../tests/sinnoh_s21_league_runtime.rb) valida o runtime BlueRegions/CH14 com fontes sintéticas, saves e oito insignias; o [auditor Python](../scripts/regions/audit_sinnoh_s21_league.py) e [16 testes negativos](../tests/test_sinnoh_s21_league.py) checam CH11/CH14/CH15, detonado S42–S43, bloqueio de fontes, rosters e HoF fictícios.

**Após CI, Barra A 22/32 (68%)**, com 5 parciais e 5 pendentes; E 20/20, B/C/D 0/13 e 44 testes nativos pendentes. Não existem salas/treinadores/MapIDs de Elite Four ou Cynthia instalados; nenhum Game.exe/JoiPlay foi executado nesta tarefa. **S22 tem agora pré-voo e testes offline, mas a viagem física e as chegadas continuam pendentes.**

## S22 — Viagem Sinnoh → Hoenn/Unova e itens regionais (concluída em código após CI)

A [S22](SINNOH_S22_VIAGENS_HOENN_UNOVA_ACEITE.md) introduz [pré-voo somente leitura](../scripts/regions/SinnohTravelContracts.rb) para os dois destinos narrativos pós-Hall **Hoenn/Unova**, usando o CH14 e as verificações existentes do `BlueRegionTravel`. O circuito global de livre viagem de Kanto, Johto, Hoenn e Decades **não muda**. O pré-voo distingue Hall não confirmado, chegada ausente, fonte Sinnoh não instalada e contexto de agente local inexistente. `VERIFIED_NATIVE_DEPARTURES = {}.freeze` impede teleporte por fonte ou NPC inventado.

O [teste Ruby](../tests/sinnoh_s22_travel_runtime.rb) exercita o CH14 e o verdadeiro `RegionTravel.rb` com **Bag, PC e Hoenn sintéticos**: guarda HMs/itens-chave da região de origem, preserva consumíveis comuns, carrega HMs do destino, restaura Sinnoh ao regressar e não modifica o save/objetos originais durante a prévia. O [auditor Python](../scripts/regions/audit_sinnoh_s22_travel.py), [contrato](../data/regions/sinnoh-travel-s22.json) e [16 testes negativos](../tests/test_sinnoh_s22_travel.py) rejeitam destinos MapID, Unova e fontes de partida falsas.

**Após CI, Barra A 23/32 (71%)** com 5 tarefas parciais e 4 pendentes; E 20/20 e B/C/D 0/13, com 44 casos nativos não executados. Não há NPC/MapID de saída de Sinnoh nem ponto de chegada de Unova; Hoenn precisa de instalação válida na build específica. **S23 pós-jogo/revanches está concluída em contratos/testes offline, mas mapas/batalhas reais continuam pendentes**, e a S22 não executou Game.exe, JoiPlay, save ou teleporte real.

## S23 — Pós-jogo, Battle Zone e revanches (concluída em código após CI)

A [S23](SINNOH_S23_POS_JOGO_REVANCHES_ACEITE.md) adiciona o [adaptador Ruby](../scripts/regions/SinnohPostgameContracts.rb) com **seis marcos opcionais e idempotentes** de pós-jogo: Battle Zone, Heatran, Cresselia, Darkrai, Shaymin e marco de revanche Full Power. O acesso lógico é posterior ao Hall of Fame independente de Sinnoh; Heatran requer marco anterior da Battle Zone; Darkrai/Shaymin exigem o requisito de evento confirmado, e todos os callbacks nativos continuam bloqueados via `VERIFIED_NATIVE_SOURCES = {}.freeze`.

O [catálogo S23](../data/regions/sinnoh-postgame-s23.json) conserva **14 áreas planejadas da fase 10**, sem MapIDs ou eventos compilados, e diferencia **5 revanches históricas da Elite/Cynthia** de equipes Blue *Full Power* não verificadas. O *Full Power* global exige **as dez Ligas** mais equipe de revanche verificada; Pokémon especiais na party continuam exigindo **oito insígnias locais**, regra distinta. O [teste Ruby](../tests/sinnoh_s23_postgame_runtime.rb) cobre CH14/BlueRegions, Hall, eventos, idempotência e saves; o [auditor S23](../scripts/regions/audit_sinnoh_s23_postgame.py) e [16 testes negativos](../tests/test_sinnoh_s23_postgame.py) bloqueiam falsas equipes PBS, lendários, portais, mapas e níveis fixos.

**Após CI: Barra A 24/32 (75%)**, 5 parciais e 3 pendentes; E 20/20, B/C/D 0/13, 44 casos nativos não executados. **Não há Battle Zone, Stark Mountain, Battle Frontier, lendários capturáveis ou revanches reais instalados em Game.exe/JoiPlay**.

## Subetapas do S07 — remapeamento seguro (parcial)

```text
████████████████░░░░░░░░  6/9 (67% das subetapas de preparação)
```

A ferramenta de remapeamento já verifica IDs reais de origem, símbolos, hashes, colisões, planos anteriores e produz **propostas** de transferência entre os IDs candidatos. Veja [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py), [testes](../tests/test_sinnoh_remap.py) e o [relatório da Fase 01](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md).

As **três subetapas restantes** exigem baseline/reservas de todas as regiões, conversão dos dados reais da fonte autorizada e teste nativo isolado. Por isso **S07 continua parcial**, a Barra A permanece em **24/32** e nenhuma das barras de jogabilidade sobe. Os detalhes R01–R09 estão em [sinnoh-progress.json](../data/regions/sinnoh-progress.json).

### Conversão de geometria — código disponível, mapas reais pendentes

O conversor [convert_sinnoh_geometry.py](../scripts/regions/convert_sinnoh_geometry.py) e seus [6 testes com mapas sintéticos](../tests/test_sinnoh_geometry_converter.py) já produzem prévias de terreno, tilesets e cópias dos índices de mapa **sem eventos/scripts, encontros ou músicas do jogo doador**, com dry-run e stage opcional em `.blue-work`. Consulte [Fase 01 — prévia de geometria](SINNOH_FASE_01_PREVIA_GEOMETRIA.md).

**Limite:** nenhum ZIP real de Sinnoh foi convertido e ainda não existem portais, NPCs, saves ou mapas jogáveis novos. Por isso **R08 segue incompleto**, S07 segue **6/9**, a Barra A permanece **24/32 (75%)** e as barras técnicas/jogáveis continuam **0/13**.

## Fase 03 — introdução de Twinleaf (preparação parcial)

```text
███████████████░░░░░░░░░  5/8 (63% das subetapas de preparação)
```

Os handlers Ruby [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb), a [template dos eventos](../data/regions/sinnoh-twinleaf-events.json) e o [compilador de overlays autorais](../scripts/regions/build_sinnoh_twinleaf_events.py) foram criados. A história prevista cobre 9 mapas, **5 eventos de história**, **3 Poké Bolas físicas** e **16 warps**, com estado exclusivamente de Sinnoh, seleção sem duplicidade e Barry bloqueado até o PBS isolado estar validado. Testes: [Python](../tests/test_sinnoh_twinleaf_events.py) e [Ruby](../tests/sinnoh_pilot_runtime.rb).

**Faltam 3 subetapas:** auditar os nove mapas e sprites reais com coordenadas e spawn, validar as três equipes PBS de Barry, e integrar/testar o piloto no Game.exe e Android. Todos os mapas e posições da template permanecem `null`/`false`. Portanto **S13 e S14 são parciais**, não entregas jogáveis. Veja o [MD detalhado da Fase 03](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md) e o [inventário de 8 subetapas](../data/regions/sinnoh-progress.json).

**Verificação de código:** [CI de Sinnoh isolada](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43533250672) — **62 testes Python aprovados**, sintaxe Ruby aprovada e execução de `sinnoh_pilot_runtime.rb` com resultado `SINNOH_STORY_RUNTIME_GUARDS_OK`. Esses testes usam fixtures e não certificam gameplay nativo. A suíte geral também inclui testes de Johto; falhas de Johto devem ser investigadas separadamente, sem alterar as barras de Sinnoh.

## Barry — três equipes PBS (código preparado)

```text
████████████████░░░░░░░░  4/6 (67% das subetapas próprias)
```

O [gerador de PBS do Barry](../scripts/regions/build_sinnoh_barry_pbs.py) prepara **três versões com vantagem de tipo** (Turtwig → Chimchar; Chimchar → Piplup; Piplup → Turtwig), sempre usando espécies e golpes existentes na instalação Blue, sem importar equipes do jogo doador. O [verificador](../scripts/regions/verify_sinnoh_barry_pbs.py) compara SHA-256, valida a presença das três equipes, confere o código de balanceamento **70% normal / 90% Master** e recusa o arquivo de liberação no draft. Consulte a [documentação PBS](SINNOH_FASE_03_BARRY_PBS.md).

**Faltam 2 subetapas:** compilar os PBS e conferir o sprite/batalhas na cópia experimental; testar níveis efetivos, vitória/derrota e saves em Game.exe/JoiPlay. O nível 5 nos PBS é **somente o nível-base técnico**, não o nível fixo exibido ao jogador. Como a integração real não foi verificada, o item **I07 da introdução continua pendente**, a preparação geral permanece **24/32** e nenhuma barra de fases jogáveis sobe.

**CI isolada de Sinnoh:** [execução 43535200301](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43535200301) aprovou **82 testes Python** e o harness Ruby `SINNOH_STORY_RUNTIME_GUARDS_OK`. A suíte geral continua sujeita a uma falha separada de integridade do piloto de Johto (`test_ruby_guard_only_accepts_signed_local_pilot`), que não deve ser confundida com aprovação de gameplay de Sinnoh.

**Atenção:** existe um piloto legado de Sinnoh com MapIDs 800–805, na faixa 600–999 protegida no plano de Johto. Os dois modelos precisam ser conciliados antes de uma integração compartilhada; não mesclar os mapas automaticamente.

## Conciliação do piloto e QA de Barry — nova etapa

```text
████████████░░░░░░░░░░░░  3/6 (50% do subtrabalho de compatibilidade e pré-verificação)
```

A auditoria [audit_sinnoh_pilot_compat.py](../scripts/regions/audit_sinnoh_pilot_compat.py) identifica os MapIDs **800–805** do piloto legado de Sinnoh dentro da faixa **600–999 protegida para Johto**. Ela distingue uma cópia experimental **totalmente independente** de uma instalação **multi-regional**: no segundo cenário, não permite mesclar esses IDs automaticamente. Também registra que [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb) oferece iniciais pelo diálogo, diferentemente das **três Poké Bolas físicas** do [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb).

O [preflight_sinnoh_barry_qa.py](../scripts/regions/preflight_sinnoh_barry_qa.py) confere os dois PBS de Barry **já copiados para uma instalação QA separada**, a partir dos hashes do draft, e registra o sprite candidato, o executável e a ausência de marcador prematuro. **Não compila PBS e não executa a batalha**, logo o trabalho permanece parcial. Veja [guia de reconciliação e QA](SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md).

Faltam: auditoria física das reservas, montagem do piloto novo com fonte autorizada e testes reais Windows/Android. O avanço de **3/6** é apenas desta etapa de código; desenvolvimento geral **24/32**, fases técnicas/jogáveis/QA **0/13**.

## Novo piloto — montagem privada do overlay (preparação parcial)

```text
████████████░░░░░░░░░░░░  3/6 (50% das subetapas de integração)
```

O novo montador [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py) reúne em **.blue-work** o stage de geometria, os **24 eventos próprios do Blue em nove mapas** (incluindo **três Poké Bolas físicas** e 16 warps), as **três versões PBS de Barry** e o plugin autoral `SinnohPilot.rb`. Confere transações, hashes, MapInfos/Tilesets e **todos os IDs presentes na geometria**, além de recompilar os eventos e verificar byte a byte a saída. Não copia o piloto legado, `System.rxdata`, `Scripts.rxdata`, `Game.exe` nem saves.

[Documentação e comandos do piloto](SINNOH_FASE_02_PACOTE_INTEGRACAO_QA.md) | [Testes sintéticos de integração](../tests/test_sinnoh_pilot_bundle.py).

**Restam 3 subetapas locais:** auditar a fonte autorizada e os IDs reservados, montar/compilar na cópia real do Game.exe com perfil isolado, testar Windows/Android e a batalha com Barry. O montador fica em **dry-run por padrão**, escreve apenas em pasta nova de `.blue-work` mediante `--publish` e **não cria marcador de batalha**. Portanto a barra geral continua **24/32 (75%)**, as fases técnicas/jogáveis/QA **0/13**, e a compatibilidade do piloto legado permanece **3/6**.

**Validação atualizada de código:** a [CI isolada de Sinnoh, execução 43538522476](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43538522476), aprovou **119 testes Python** e os testes Ruby de introdução e sondagem do Barry em ambiente sintético. A regressão geral permanece com a falha preexistente de Johto `test_ruby_guard_only_accepts_signed_local_pilot` (`[601, 13, 13]` vs `nil`), sem representar falha do montador de Sinnoh. Teste offline não prova Game.exe jogável.

## Instalação experimental com saves separados — preparada em código

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas da instalação QA)
```

O [instalador QA](../scripts/regions/install_sinnoh_qa_copy.py) monta **uma cópia nova em `.blue-work`** a partir de um overlay Sinnoh já auditado. Ele exclui saves da base, atribui identificadores exclusivos em `mkxp.json` e `Game.ini`, prepara o `System.rxdata` para o quarto do jogador e inclui um bootstrap para a compilação das três versões PBS de Barry. Na **primeira execução local do Game.exe QA**, o bootstrap tenta compilar e registra erros ou a prova local da compilação; **não libera o marcador de batalha do Barry**.

O plugin [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) exige a prova de compilação, o perfil Sinnoh e SHA-256 dos arquivos protegidos antes de preparar um novo jogo. A falta de prova bloqueia o início em vez de cair silenciosamente na campanha Decades. Os [testes Python](../tests/test_sinnoh_qa_install.py) e [testes Ruby](../tests/sinnoh_qa_start_runtime.rb) cobrem esse contrato com instalações fictícias. [Guia completo para Codex/Windows](SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md).

**Restam 3 subetapas reais:** auditar e montar a cópia com os mapas autorizados, compilar/verificar o PBS e os caminhos efetivos de saves no Game.exe Windows, e testar Twinleaf/Barry/saves/Android sem regressões. Por isso a instalação QA ainda **não foi executada com assets reais**, o item do piloto continua **parcial**, o desenvolvimento geral permanece **24/32 (75%)** e as barras de aceite **0/13**. Nenhum save principal foi modificado.

**CI isolada:** [execução de Sinnoh](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43539553514) aprovou **134 testes Python**, sintaxe Ruby e os harnesses de abertura/Barry, inclusive `SINNOH_QA_START_SAVE_AND_PBS_GUARDS_OK`. A suíte geral possui uma falha separada anterior do piloto de Johto; isso não equivale a QA Windows/Android para Sinnoh.

## Validação automática pós-compilação do piloto — preparada em código

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas da sondagem nativa)
```

O módulo [SinnohQAProbe.rb](../scripts/regions/SinnohQAProbe.rb), incluído apenas na cópia QA, está pronto para executar **após o `Compiler.main` no Game.exe experimental**. Ele confere `GameData::Trainer` nas três versões de Barry e carrega os nove mapas da introdução para auditar **24 eventos, 16 portais, três Poké Bolas físicas, cinco handlers Blue, nomes, sprites de eventos, gatilhos e coordenadas**. A prova estrutural é registrada em `Data/blue-sinnoh-qa-engine-check.json`, separada do token de compilação. Falhas impedem a liberação de `Novo Jogo` e nenhum script cria `blue-sinnoh-rival-ready.txt`.

O [verificador Python](../scripts/regions/install_sinnoh_qa_copy.py) exige hashes de **todos** os mapas preparados e confere o novo relatório. O [plugin de inicialização QA](../scripts/regions/SinnohQAStart.rb) não autoriza `Novo Jogo` com token sozinho. [Testes Python](../tests/test_sinnoh_qa_install.py), [testes Ruby da sondagem](../tests/sinnoh_qa_engine_probe_runtime.rb) e [início Ruby](../tests/sinnoh_qa_start_runtime.rb) usam só arquivos e equipes **sintéticos**. Detalhes no [guia de validação pós-compilação](SINNOH_FASE_02_VALIDACAO_NATIVA_PBS_EVENTOS.md).

**Restam 3 subetapas reais:** rodar essa sondagem no Game.exe com mapas autorizados, observar batalha/nível efetivo 70%/90% e saves Windows, e validar o Android/JoiPlay com regressões. **Nenhuma dessas três ocorreu nesta conversa.** Portanto o desenvolvimento geral permanece **24/32 (75%)**, as 13 fases técnicas/jogáveis/nativas permanecem **0/13** e a instalação QA continua **4/7**.

**CI isolada comprovada:** [execução 43540748918](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43540748918) — **138 testes Python aprovados** e harnesses Ruby de prova de início, eventos e Barry aprovados. A conclusão **geral** daquela workflow foi falha em testes fora da suíte isolada; não confundir sucesso isolado com pipeline totalmente verde ou gameplay nativo.

## Batalhas e playtest nativo — preparado, execução real pendente

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas de instrumentação e QA)
```

A introdução autoral [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) agora permite **tentar a batalha com Barry só na cópia QA isolada**, após [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) validar provas de compilação, eventos e hashes dos mapas/PBS. Antes disso, Barry permanece bloqueado; o marcador de publicação `blue-sinnoh-rival-ready.txt` **não é criado nem necessário para o teste experimental**. Resultados nulos não avançam o save; as batalhas de teste aceitam vitória ou derrota (`canLose`), preservando Decades/Kanto/Johto/Hoenn.

O [auditor de playtest](../scripts/regions/audit_sinnoh_playtest.py) prepara um roteiro **local de 44 casos**: três Poké Bolas, 12 batalhas (3 iniciais × Normal/Master × vitória/derrota), 16 warps, cinco NPCs, três verificações de save/reload, quatro regressões e Android/JoiPlay. Ele confronta os **níveis observados** com a regra real de código Blue (70%/90%) e exige capturas/logs locais com SHA-256. O resultado **não aprova o jogo automaticamente**, nem prova que uma pessoa executou os testes — as evidências ainda exigem revisão humana. Veja [guia de execução Windows/Android](SINNOH_FASE_02_PLAYTEST_REAL_BARRY_SAVES.md) e [testes do auditor](../tests/test_sinnoh_playtest_audit.py).

**Pendências reais T05–T07:** executar Game.exe QA sobre mapas legítimos e auditar os 12 combates, fazer os testes de portais/saves/regressões e validar Android/JoiPlay. Nenhuma evidência real foi fornecida nesta conversa; o progresso geral permanece **24/32 (75%)** e a aprovação das 13 fases continua **0/13**.

**CI isolada:** a [execução 43541798458](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43541798458) aprovou **151 testes Python** e verificações Ruby da história, início de Sinnoh e estruturas da engine com fixtures. A conclusão da CI geral é acompanhada separadamente.

## Barra B — fases tecnicamente aprovadas

```text
░░░░░░░░░░░░░░░░░░░░░░░░  0/13 (0%)
```

Uma fase só sobe quando seu escopo *inteiro* foi implementado e tecnicamente validado. A Fase 00 depende de auditar uma fonte real e o `game/Data` local; a Fase 02 depende de piloto real. A conclusão de um script de apoio não equivale à aprovação de fase.

## Barra C — fases jogáveis no Game.exe

```text
░░░░░░░░░░░░░░░░░░░░░░░░  0/13 (0%)
```

Contam somente os núcleos que possam ser realmente abertos e percorridos no `Game.exe`, com mapas reais, batalhas/eventos coerentes e saves isolados. Menu `Testar Sinnoh` sem piloto ainda não conta.

## Barra D — aceitação completa Windows / Android

```text
░░░░░░░░░░░░░░░░░░░░░░░░  0/13 (0%)
```

Contam somente fases com QA real comprovado no Windows e, quando distribuída para JoiPlay/Android, no celular. CI Python/Ruby não se confunde com teste manual do jogo.

## Quadro por fase — sequência principal

| Fase | Núcleo | Preparação atual | Implementado e testado no jogo |
|---|---|---|---|
| 00 | Auditoria de fontes, direitos e baseline | Ferramentas criadas; fonte local pendente | Não |
| 01 | Importador e remapeamento de mapas | Prévia segura de geometria codificada; fonte real, eventos e instalação pendentes | Não |
| 02 | Piloto de Sinnoh no menu | Montador e instalador QA com saves distintos feitos; fonte real e testes nativos pendentes | Não |
| 03 | Twinleaf, Rowan, Barry, Sandgem | Handlers próprios + 3 bolas + compilador de eventos prontos; mapas e PBS reais pendentes | Não |
| 04 | Jubilife, Oreburgh e Roark | Inventário simbólico | Não |
| 05 | Floaroma, Eterna e Gardenia | Inventário simbólico | Não |
| 06 | Hearthome, Veilstone e Pastoria | Inventário simbólico | Não |
| 07 | Canalave, Iron Island e Snowpoint | Inventário simbólico | Não |
| 08 | Galactic HQ, Mt. Coronet e Giratina | Inventário simbólico | Não |
| 09 | Sunyshore, Elite Four e Cynthia | Inventário simbólico | Não |
| 10 | Battle Zone e pós-jogo | Inventário simbólico | Não |
| 11 | Músicas, treinadores, encontros e site | Catálogo musical conceitual | Não |
| 12 | Integração final e regressões | Plano de validação existente | Não |

Esta tabela descreve **preparação**, não porcentagens falsas de mapa concluído. As barras B, C e D permanecem em **0/13** até que as fontes, as equipes e os testes necessários estejam realmente disponíveis.

## Entregas concretas da Barra A

| Situação | ID | Entregável | Arquivo / evidência |
|---|---|---|---|
| Concluído | S01 | Auditor básico de origem | [auditor](../scripts/regions/audit_sinnoh_source.py) |
| Concluído | S02 | Auditoria interna de RXDATA | [auditor profundo](../scripts/regions/audit_sinnoh_rxdata.py) |
| Concluído | S03 | Estudo de capacidade de MapIDs | [capacidade](../scripts/regions/plan_sinnoh_capacity.py) |
| Concluído | S04 | Proveniência e direitos pendentes | [manifesto](../data/regions/sinnoh-source.json) |
| Concluído | S05 | 91 áreas e 51 eventos simbólicos | [cobertura](../data/regions/sinnoh-coverage.json) |
| Concluído | S06 | Grafo de conexões e referências ausentes | [grafo](../scripts/regions/graph_sinnoh_maps.py), [testes](../tests/test_sinnoh_graph.py) |
| Parcial | S07 | Dry-run, staging, rollback, planejamento e diagnóstico R07 (6/9 subetapas; fonte real pendente) | [transação](../scripts/regions/sinnoh_staging_transaction.py), [diagnóstico](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) |
| Concluído em código | S08 | Verificação de mapas, PNG, hashes, scripts e dependências antes da instalação QA | [auditor S08](../scripts/regions/audit_sinnoh_s08_resources.py), [aceite](SINNOH_S08_INTEGRIDADE_RECURSOS_ACEITE.md) |
| Concluído | S09 | Botão Testar Sinnoh sem quebrar saves | [menu](../scripts/battle_polish/TitleKanto.rb) |
| Concluído em código | S10 | BAT de duplo clique e seleção segura da cópia QA | [BAT](../SINNOH_JOGAR_EXPERIMENTAL.bat), [relatório S10](SINNOH_S10_LANCADOR_EXPERIMENTAL_ACEITE.md) |
| Concluído em código | S11 | Piloto com namespace exclusivo de saves e carregamento regional protegido | [isolamento](../scripts/regions/sinnoh_save_isolation.py), [aceite S11](SINNOH_S11_PILOTO_SAVES_ISOLADOS_ACEITE.md) |
| Concluído em código | S12 | Instalador QA isolado, dry-run, BAT e rollback | [instalador](../scripts/regions/sinnoh_s12_installer.py), [aceite S12](SINNOH_S12_INSTALADOR_QA_ISOLADO_ACEITE.md) |
| Parcial | S13 | Estrutura autoral de Rowan, Barry e Pokédex | [Ruby](../scripts/regions/SinnohPilot.rb), [MD](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md) |
| Parcial | S14 | Três iniciais em Poké Bolas físicas, com save isolado | [template](../data/regions/sinnoh-twinleaf-events.json), [compilador](../scripts/regions/build_sinnoh_twinleaf_events.py) |
| Concluído em código | S24 | Catálogo simbólico dos 46 cenários musicais | [aceite S24](SINNOH_S24_CATALOGO_CENARIOS_ACEITE.md) |
| Concluída em código | S17 | Balanceamento dinâmico 70/90, Master 4, duplas até 6 e autores preservados | [aceite S17](SINNOH_S17_TREINADORES_DINAMICOS_ACEITE.md) |
| Concluída em código | S18 | Evolução selvagem 15–60%, slots e pesos preservados, 21 áreas apenas planejadas | [aceite S18](SINNOH_S18_ENCONTROS_EVOLUCOES_ACEITE.md) |
| Concluída em código | S19 | Gates Galactic Windworks, Mars, Jupiter, Pastoria e Lagos, sem handlers nativos | [aceite S19](SINNOH_S19_TEAM_GALACTIC_ACEITE.md) |
| Concluída em código | S20 | Nove checkpoints Cyrus, Spear Pillar, Distortion World e Giratina, sem hooks/mapas instalados | [aceite S20](SINNOH_S20_CYRUS_DISTORTION_GIRATINA_ACEITE.md) |
| Concluída em código | S21 | Oito checkpoints Volkner→Barry→Elite→Cynthia→HoF separado, sem PBS nativos | [aceite S21](SINNOH_S21_ELITE_CYNTHIA_HALL_OF_FAME_ACEITE.md) |
| Concluída em código | S22 | Pré-voo de viagem Hoenn/Unova, NPC/origem verificados e isolamento de HMs/Key Items | [aceite S22](SINNOH_S22_VIAGENS_HOENN_UNOVA_ACEITE.md) |
| Concluída em código | S23 | Seis marcos do pós-jogo, 14 áreas planejadas, lendários condicionais e revanches por 10 Ligas | [aceite S23](SINNOH_S23_POS_JOGO_REVANCHES_ACEITE.md) |
| Concluída offline | S26 | Testes de prioridades, fallback, fade e loop com BlueMusic sem reprodução | [S26](SINNOH_S26_TESTES_MUSICA_ACEITE.md) |
| Concluído web | S28 | Catálogo de 13 equipes Platinum, 5 revanches e 40 treinadores pendentes | [relatório S28](SINNOH_S28_CATALOGO_TIMES_REFERENCIAS.md) |
| Concluída offline | S30 | Suíte automatizada Python/Ruby/portal/Android, CI separado | [relatório S30](SINNOH_S30_SUITE_AUTOMATIZADA_ACEITE.md) |
| Parcial | S31 | Plano de aceitação Windows/JoiPlay | [plano](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) |
| Concluído | S32 | Fila de pendências Codex | [backlog](SINNOH_CODEX_PENDENCIAS.md) |

**As demais entregas de S13–S29 não listadas acima seguem pendentes** (exceto S13 e S14, parciais, e S27/S29 já concluídas em código web); veja a lista completa, com os 32 IDs, no [registro JSON](../data/regions/sinnoh-progress.json). A ordem de implementação é independente das fases integradas: uma API pode estar pronta mas não haver mapa-fonte para aprovar uma fase.

## O que foi feito nesta etapa

1. [scripts/regions/graph_sinnoh_maps.py](../scripts/regions/graph_sinnoh_maps.py) lê o relatório RXDATA do jogo doador e identifica ligações por transferência literal, referências ausentes, grupos isolados e áreas não alcançáveis de um mapa inicial **somente quando seu ID real foi informado**.
2. [tests/test_sinnoh_graph.py](../tests/test_sinnoh_graph.py) cobre os casos principais com mapas sintéticos, sem copiar assets de terceiros.
3. Este painel e o [JSON de progresso](../data/regions/sinnoh-progress.json) passam a ser os marcadores para as próximas atualizações.

**Limites:** o grafo **não** executa scripts, não detecta com certeza warps baseados em eventos comuns ou variáveis, nem certifica que um mapa é atravessável. Grupos desconectados não são automaticamente bugs; podem depender de teleporte, navegação ou condição de história.

## Próximo passo

Concluir o **S07**: o dry-run e o estágio atômico com rollback já estão implementados **exclusivamente em `.blue-work`**. Ainda falta integrar um remapeador com os MapIDs reais e verificar os direitos das fontes antes de sequer considerar uma instalação na cópia de teste. Nenhum código atual toca em `game/`. Para testar contra a Sinnoh verdadeira, o Codex precisará de fonte RMXP autorizada, `game/Data` e MapID inicial auditado.

```powershell
python scripts/regions/graph_sinnoh_maps.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/map-graph.json
# Se o MapID inicial estiver confirmado no MapInfos:
python scripts/regions/graph_sinnoh_maps.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data --start-map 123
python -m unittest discover -s tests -p "test_sinnoh_graph.py" -v
```

O `123` é apenas um **exemplo de argumento**: não significa que Twinleaf tenha esse MapID. Sem confirmação do MapInfos, omitir `--start-map`.

**Publicação:** código e documentação sob `main` após testes. O jogo principal, fontes externas, saves, mapas e músicas não autorizados permanecem intactos e fora do Git.
