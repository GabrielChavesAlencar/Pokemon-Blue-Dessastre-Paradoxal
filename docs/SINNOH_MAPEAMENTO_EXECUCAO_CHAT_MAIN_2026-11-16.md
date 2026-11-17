# Sinnoh — mapeamento de entregas diretas ChatGPT → GitHub main

**Criado em:** 16/11/2026  
**Repositório:** `GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal` · branch `main`.  
**Objetivo:** relacionar tudo o que pode ser **escrito, corrigido, testado estaticamente e publicado diretamente pelo chat**, sem depender de Codex para tarefas que cabem no repositório.  
**Fonte de progresso:** [`data/regions/sinnoh-progress.json`](../data/regions/sinnoh-progress.json), objeto `chat_direct_workstream`.  
**Painel:** [`SINNOH_PROGRESSO.md`](SINNOH_PROGRESSO.md), **Barra E**.

> A Barra E mede **novas entregas verificáveis na main**, não porcentagem de Sinnoh jogável. Ferramenta para importar mapas ≠ mapa importado; handler Ruby ≠ evento testado no Game.exe. O desenvolvimento (Barra A) soma 27/32 após as entregas S08, S10, S11, S12, S15, S17, S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29 e a suíte offline S30; a aprovação técnica/jogável/nativa continua 0/13 até provas reais.

## 1. Regra de execução do trabalho pelo chat

1. **Executar diretamente na main:** análises de `docs/`, manifestos e catálogos em `data/` e `site/public/data/`, scripts Python/Ruby autorais, verificadores de compatibilidade, testes em `tests/`, configurações de CI, site e ferramentas que aceitem dados reais **quando fornecidos**.
2. **Não delegar ao Codex o que é possível neste repositório.** Cada próximo pedido deve escolher uma entrega CH, fazer a alteração real, rodar/verificar os testes possíveis e publicar com commit explícito. Se um teste não puder ser executado neste ambiente, declarar "não executado", não "aprovado".
3. **Somente ambiente local quando for indispensável:** obter e inspecionar `game/Data`/PBS reais, arquivos-fonte de Sinnoh e autorização por asset; executar RPG Maker XP/Essentials/Compiler e `Game.exe`; testar áudio, controles, mapas, warps, encontros, vitórias/derrotas, saves e JoiPlay. Um ZIP publicado não é automaticamente fonte editável nem licença de redistribuição.
4. **Modificações aditivas e reversíveis:** não sobrescrever `game/`, saves, `Scripts.rxdata`, `System.rxdata`, `MapInfos.rxdata` ou `Tilesets.rxdata` globais; não atribuir MapIDs sem dados reais. A faixa **600–999 é protegida para Johto**; o piloto legado Sinnoh utiliza **800–805** e **não pode entrar diretamente no jogo multirregional**.
5. **Uma fonte de verdade por status:** atualizar o `chat_direct_workstream` (CH01–CH20) e a Barra E **na mesma entrega**. `done` requer commit e evidência dos critérios de aceite; `partial` não entra no numerador; `pending` permanece 0. Um novo pedido pode decompor entregas complexas, sem inflar tarefas já concluídas.
6. **Não falsear barras:** atualizar a Barra A ou B/C/D **somente** segundo seus próprios critérios independentes. CI headless nunca prova que a região inteira está jogável.

## 2. Nova Barra E — trabalho que pode ser concluído pelo chat

```text
████████████████████  20/20 (100%)
```

**20 concluídas**, **0 parciais**, **0 pendentes** (CH19 e CH20 verificadas em CI **offline**; aceite nativo segue separado). A lista é um **backlog incremental**, não uma recontagem das 32 entregas antigas — há ferramentas existentes que os próximos itens devem **reutilizar, corrigir ou ampliar**, em vez de reimplementar.

| Prioridade | ID | Entrega publicável na `main` | Critério para mover a `done` |
|---|---|---|---|
| P0 | **CH01** ✅ | Mapeamento completo, regras, fila e Barra E | MD, JSON e painel publicados e consistentes; **feito nesta entrega** |
| P0 | **CH02** ✅ | Validador automático do JSON ↔ Barra E ↔ MD | Script + testes asseguram soma, IDs únicos, status e percentual; CI/checagem real |
| P0 | **CH03** ✅ | Proteção estática contra colisão Sinnoh legado 800–805 × Johto 600–999 | Testes negativos impedem que o instalador conjunto injete esses IDs |
| P0 | **CH04** ✅ | Bloqueio explícito do plugin `SinnohPreview.rb` legado na instalação compartilhada | Verificação cobre lançador, cópia QA, marcadores e caminho do instalador principal |
| P0 | **CH05** ✅ | Manifestações das **reservas documentadas**, sem inventar IDs novos | Relatório/fixture diferencia ocupado físico, reserva declarada e desconhecido; nunca libera importação indevidamente |
| P1 | **CH06** ✅ | Schema + auditor das 9 áreas, 24 eventos e 16 warps da introdução | Campos ausentes, coordenadas inválidas, transferência circular/órfã e mapas faltantes reprovam |
| P1 | **CH07** ✅ | Reforçar proteção de flags, três Poké Bolas e save exclusivo de `SinnohPilot.rb` | Ruby/Python com casos duplicados, perda/retorno e fallback sem iniciar outra região |
| P1 | **CH08** ✅ | Aumentar as verificações de Barry, três equipes e escalonamento compartilhado | Fixtures cobrem iniciais, versões, ausência de PBS, 70%/90% e bloqueio seguro |
| P1 | **CH09** ✅ | Teste de integração sintética ponta a ponta de auditor → plano → geometria → overlay → bundle | Cenários de sucesso/falha, rollback e hashes estáveis, **sem** representar Game.exe |
| P1 | **CH10** ✅ | Preparar interface segura do lançador QA do Sinnoh e pré-voo de instalação | Sem fallback para Decades/Johto, saves exclusivos, erro claro sem assets, testes offline |
| P2 | **CH11** ✅ | Contratos regionais de oito insígnias + HMs de Sinnoh | Dados, guardas e testes garantem badge local, sem apropriar HM de outra região |
| P2 | **CH12** ✅ | Modelos de treinadores e evolução com cálculo Blue existente | Regras testadas sem níveis fixos duplicados, preservando Normal/Master e level cap |
| P2 | **CH13** ✅ | Catálogo **simbólico** de encontros por rota/terreno/horário/cap | Registros identificados como `planned`, consistência de espécie e método, sem afirmar encontros instalados |
| P2 | **CH14** ✅ | Estados e contratos para Galactic, Cyrus, Liga e viagem pós-Cynthia | Eventos idempotentes, desbloqueio lógico Hoenn/Unova só quando instalado; testes sintéticos |
| P3 | **CH15** ✅ | Registro de equipes para Roark→Volkner, Elite Four e Cynthia | Esquemas/referências auditáveis, sem espécies ou times inventados nem nível fixo na UI |
| P3 | **CH16** ✅ | Catálogo de chaves musicais Sinnoh e fallbacks BlueMusic | Ordem de prioridade, tema/fade/loop fallback em testes, **sem** publicar áudio sem direitos |
| P3 | **CH17** ✅ | Guias de Sinnoh no site com estado real `planned`/pendente | Áreas, treinadores, liga e itemização visíveis como planejamento, sem map IDs fictícios |
| P3 | **CH18** ✅ | Testes e build do portal para Sinnoh | Pesquisa/filtros/pendências/linkagem sem rótulo `jogável` indevido, suíte do site validada |
| P4 | **CH19** ✅ | Regresso isolado Python/Ruby de Sinnoh no CI | Workflow/testes discriminam Sinnoh de falhas de Johto/Kanto e não declaram QA nativo |
| P4 | **CH20** ✅ | Auditoria estática Android/JoiPlay + checklist de 44 casos nativos | Pré-voo e relatórios reproduzíveis; teste de aparelho e certificação **permanecem locais** |

**Ordem recomendada:** CH19–CH20. Priorizar segurança de IDs, saves e linha de instalação antes de nova campanha ou site. Cada CH concluída deve ter evidência de arquivo, teste e SHA de commit; CH sem teste possível deve registrar explicitamente o bloqueio e continuar `partial`.

**CH20 concluída no escopo estático:** [auditor de pacote ZIP JoiPlay e checklist de 44 casos](../scripts/regions/audit_sinnoh_android_ch20.py), [18 testes CH20](../tests/test_sinnoh_android_ch20.py), [12 testes do auditor nativo de evidências](../tests/test_sinnoh_playtest_audit.py) e [CI CH20](../.github/workflows/sinnoh-ch20.yml) aprovados em [run 43986405854](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43986405854), com [artefato JSON+MD e hashes inspecionados](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43986405854/artifacts/14284479390). [PR #66](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/66) integrado à `main` como `c7c8cdd`; [documentação final CH20](SINNOH_CH20_JOIPLAY_PREFLIGHT.md). **44 casos planejados, 0 executados nativamente**; pacote Android real não foi fornecido, Game.exe/JoiPlay não executados. Barra E 20/20 (100%) significa **código/documentação auditáveis**, não Sinnoh jogável.

**CH19 concluída:** o [executor de regressões Python/Ruby isoladas](../scripts/regions/sinnoh_ci_ch19.py), o [workflow de matriz Python/Ruby](../.github/workflows/sinnoh-ch19.yml) e os [12 testes negativos](../tests/test_sinnoh_ci_ch19.py) foram validados em execução real de CI ([run 43985365758](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365758)): **374 testes Python**, **7 verificações Python** e **22 verificações Ruby**, todos aprovados. Ambos os artifacts JSON/MD foram conferidos; toda evidência foi marcada `offline_synthetic`, sem Game.exe/JoiPlay. [PR #65](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/65) integrado à `main` em `4bbc767`. [Relatório CH19](SINNOH_CH19_CI_PYTHON_RUBY_ISOLADO.md). Barra E alcançou 20/20 (100%) após a CH20; A/B/C/D preservadas.

**CH18 concluída:** [motor puro de pesquisa/validação](../site/src/assets/sinnoh-search.js), [interface com filtros responsivos](../site/src/assets/sinnoh-guide.js), [navegação GET/SPA](../site/src/assets/app.js) e [29 testes negativos e positivos](../site/tests/sinnoh-search.test.mjs). A página `/sinnoh` permite buscar nomes, rotas, espécies candidatas, treinadores, insígnias, HMs, Galactic/Cyrus/Cynthia e classes de pendência; filtra fase documentada ou “sem fase”, com/sem espécies de referência, área citada e revanches Platinum. URLs preservam parâmetros, filtros inválidos voltam ao escopo seguro, resultados vazios não geram provas fictícias, e links bidirecionais levam da área ao catálogo de treinadores, de ginásios às permissões HM e da Liga aos checkpoints; a [página de backlog](../site/src/assets/pending.js) também aponta para o guia. Sete categorias de pendência mostram apenas quantidades documentadas. O validador rejeita falsos MapIDs, níveis, taxas, PBS compilado, pickups, eventos, música instalada, regiões jogáveis e payloads corrompidos. [CI Portal 43981753762](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753762): **build/137 testes**; [CI Sinnoh 43981753812](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753812): **29 testes CH18**, **137 do portal** e **347 Python de Sinnoh**, todos aprovados. [Documentação CH18](SINNOH_CH18_BUSCA_FILTROS_PENDENCIAS_SITE.md). Sem certificação Game.exe ou JoiPlay.

**CH17 concluída:** [gerador do portal](../site/scripts/sinnoh-guide.mjs) consumindo **CH11–CH16**, [UI dedicada](../site/src/assets/sinnoh-guide.js) em `/sinnoh` e compatibilidade de `/localizacoes`, `/treinadores`, `/chefes` e `/liga` para Sinnoh. Há 120 áreas de referência, **91 atribuídas a fases reais do checklist** e **29 sem fase**, separadas em “Fase a auditar”; 40 treinadores ainda não instalados, oito líderes, quatro Elite, Cynthia, oito HMs e 22 checkpoints de história. O [build](../site/scripts/build.mjs) deriva um `dist/data/sinnoh-guide.json` e não escreve MapIDs, níveis fixos, taxas, itens concedidos nem equipes PBS instaladas. [19 testes negativos/positivos](../site/tests/sinnoh-guide.test.mjs), [build + 108 testes do portal aprovados](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589575), [CI isolado CH17 + 347 Sinnoh aprovados](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43979589757). [Documentação CH17](SINNOH_CH17_GUIAS_PORTAL_PLANEJADO.md). Nenhum dado foi afirmado jogável, e este trabalho não inclui certificação de deploy externo.

**CH16 concluída:** [46 chaves musicais simbólicas](../data/regions/sinnoh-music-ch16.json), organizadas a partir de 45 nomes já documentados (Hall of Fame dividido em BGM e ME), [auditor Python](../scripts/music/audit_sinnoh_music_ch16.py) e [resolvedor Ruby inerte](../scripts/music/SinnohMusicContracts.rb). Prioridades protegem áudio explícito da engine, cenas confirmadas, escolhas BlueMusic, batalhas, transportes e mapas; fallback de faixa ausente, licença/hash não verificados, mudança de região, vitória, reload e ME mantêm áudio existente. Fade e loop seguem defaults do motor até arquivos autorizados serem auditados; nenhum MP3/OGG/MIDI, MapID, evento ou hook foi criado. [23 testes Python](../tests/test_sinnoh_music_ch16.py), [Ruby com BlueMusic real](../tests/sinnoh_music_ch16_runtime.rb) e **347 testes Python de Sinnoh** aprovados no [CI 43977207679](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43977207679). [Documentação CH16](SINNOH_CH16_CATALOGO_MUSICAL_FALLBACK.md).

**CH15 concluída:** [catálogo de 13 treinadores](../data/regions/sinnoh-trainer-teams-ch15.json), [auditor e sondagem PBS somente leitura](../scripts/regions/audit_sinnoh_teams_ch15.py) e [23 testes negativos/positivos](../tests/test_sinnoh_teams_ch15.py) separaram as equipes de primeiro confronto dos 8 ginásios, Elite Four e Cynthia (13), as revanches Platinum documentadas apenas para Elite Four/Cynthia (5), as variantes **Full Power do Blue não verificadas** e as equipes **nativas PBS sem comprovação**. O registro respeita as espécies e níveis históricos de [Platinum](SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md), mas bloqueia exibir níveis fixos como reais, reclassificar fontes Kanto/Johto/Decades ou publicar compilações/versões de treinador inventadas. Guardas de `Campaign.rb` e `Story.rb` mantêm escala 70%/90% e espécies autorais de líderes/chefes. [CI 43974961958](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43974961958): CH15 **23/23** e suite Sinnoh **324/324**. [Documentação](SINNOH_CH15_TIMES_LIDERES_ELITE_CYNTHIA.md). Sem mapas, binds NPC ou Game.exe real.

**CH14 concluída:** [contrato de 22 passos Galactic/Cyrus/Liga](../data/regions/sinnoh-story-ch14-contract.json) e [runtime Ruby](../scripts/regions/SinnohStoryContracts.rb) isolam flags numa única chave regional `sinnoh_ch14`; só aceitam a próxima etapa confirmada, nunca duplicam eventos e exigem oito insígnias Sinnoh no portão da Liga. Cynthia não marca `leagues`: apenas a confirmação separada do Hall of Fame chama `BlueRegions.complete_league`. [Auditor Python](../scripts/regions/audit_sinnoh_story_ch14.py), [15 testes Python](../tests/test_sinnoh_story_ch14.py) e [teste Ruby com `RegionTravel` real](../tests/sinnoh_story_ch14_runtime.rb) bloqueiam saves falsos, regressos/atalhos, premiação fictícia e viagem para Hoenn/Unova sem fonte/destino/NPC instalados, mesmo após Hall of Fame sintético. O [CI 43973023734](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43973023734) aprovou CH14 e **301 testes Python isolados de Sinnoh**. [Documentação](SINNOH_CH14_GALACTIC_CYRUS_LIGA.md). Não foram adicionados eventos físicos, MapIDs, NPCs, equipes, recompensas ou prova jogável.

**CH13 concluída:** [catálogo simbólico de 21 áreas](../data/regions/sinnoh-symbolic-encounters.json), [auditor read-only](../scripts/regions/audit_sinnoh_symbolic_encounters.py) e [20 testes Python](../tests/test_sinnoh_symbolic_encounters_ch13.py) verificam 50 referências de espécies ancoradas no inventário existente de Platinum, terrenos e métodos candidatos do Blue, horários a conferir, cap de evolução compartilhado, símbolos ausentes/ambíguos, exclusão de eventos especiais e ausência total de MapIDs/percentuais/slots fictícios. Drifloon e Rotom permanecem eventos estáticos; Mt. Coronet, Route 212 e Old Chateau aguardam mapeamento inequívoco. [CI 43970908799](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43970908799): CH13 **20/20** e Sinnoh **286/286**. [Descrição CH13](SINNOH_CH13_ENCONTROS_SIMBOLICOS.md). Nenhum encounter nativo ou taxa por horário foi instalado.

**CH12 concluída:** [manifesto de regras de Sinnoh](../data/regions/sinnoh-trainer-evolution-contract.json) e [auditor](../scripts/regions/audit_sinnoh_trainer_evolution.py) evitam recriar níveis fixos, inventar um cap regional e atribuir jogabilidade. O balanceamento real de `Campaign.rb` usa 70% Normal / 90% Master, base no maior nível não-ovo do jogador limitada por `GrowthRate.max_level`; o BST 350/450/540 de `Story.rb` é outro teto. [15 casos Python CH12](../tests/test_sinnoh_trainer_evolution_ch12.py) e [runtime Ruby com código Blue real](../tests/sinnoh_evolution_ch12_runtime.rb) confirmam evoluções pós-escala de iniciais Turtwig/Chimchar/Piplup, pedra 30, troca 40, felicidade 45, nível+5, condicionais, PBS/bosses intactos e expansão Master com fixtures. [CI 43968704804](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43968704804) aprovou CH12. [Documentação CH12](SINNOH_CH12_BALANCEAMENTO_EVOLUCAO.md). Sem afirmar qualquer batalha nativa ou cap regional por insígnias.

**CH11 concluída:** [contrato declarativo das 8 insígnias/HMs](../data/regions/sinnoh-badges-hms-contract.json) conferido com o catálogo público pelo [auditor](../scripts/regions/audit_sinnoh_badges_hms.py). [Regions.rb](../scripts/battle_polish/Regions.rb) impede que conquistas inválidas, insígnias de outra região ou HM apenas presente na Bolsa liberem campo de Sinnoh; somente eventos futuros de obtenção local confirmada podem registrar cada HM, sem gerar o item. [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb) exige essa prova antes de aceitar o HM físico. [12 testes Python](../tests/test_sinnoh_badges_hms_ch11.py) e [Ruby com vault de Bolsa/PC/atalhos](../tests/sinnoh_badge_hm_ch11_runtime.rb) passaram no [CI 43958964604](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43958964604); **251 testes Sinnoh** também passaram. Nenhuma prova de ginásio/HM nativo ou aprovação jogável foi criada. [Descrição CH11](SINNOH_CH11_INSIGNIAS_HMS_REGIONAIS.md).

**CH10 concluída:** o [lançador QA](../scripts/regions/launch_sinnoh_qa.py) não executa `Game.exe` por padrão; `--compile` exige um pedido de compilação íntegro e `--launch` exige provas estruturais nativas. O [instalador da cópia](../scripts/regions/install_sinnoh_qa_copy.py) fixa SHA-256 de arquivos executáveis/críticos, confirma assets e perfil de saves e rejeita saves de outras regiões/copias adulteradas; a atualização Ruby [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) recusa saves Kanto/Johto/Hoenn/Decades e novos jogos com estado estrangeiro, sem fallback para o selector principal. [14 testes CH10](../tests/test_sinnoh_ch10_qa_launcher.py) + [Ruby QA](../tests/sinnoh_qa_start_runtime.rb) passaram no [CI 43925173071](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43925173071); **239 testes Python isolados** passaram. É uma barreira sintética, não prova de Game.exe/JoiPlay.

**CH09 concluída:** [8 testes de integração ponta a ponta](../tests/test_sinnoh_ch09_integration.py) montam uma fonte RMXP **100% sintética e temporária**, passam pelo auditor, plano explícito de IDs, conversor que remove eventos/áudio doador, stage atômico, compilador de eventos autorais, draft PBS de Barry, validação e publicação de bundle *privado*. Exercitam SHA-256 determinístico, arquivo fonte adulterado, ID protegido/ocupado, PBS inválido, corrupção de stage, falhas simuladas de fsync e rollback que não apaga arquivos contaminados. [CI 43923392072](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43923392072): CH09 **8/8** e suíte isolada de Sinnoh **225/225**. **Não** implica instalação, Game.exe, autorização para redistribuir fonte, nem MapIDs 500–508 reais. [Documentação da CH09](SINNOH_CH09_E2E_SINTETICO.md).

**CH08 concluída:** [validador PBS](../scripts/regions/verify_sinnoh_barry_pbs.py) reforçado contra times, seed e versões incorretos, `effective_level` fixo ou falsas aprovações. [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) não chama `TrainerBattle` sem um único contra-inicial compilado válido da versão selecionada. [Testes CH08 em Python](../tests/test_sinnoh_barry_ch08.py) cobrem PBS ausente, adulterações e bloqueio; [Ruby](../tests/sinnoh_barry_ch08_runtime.rb) executa a escala compartilhada real de `Campaign.rb` Normal 70% / Master 90% (incluindo limite e ovo) com fixtures, sem dizer que ela foi testada dentro do Game.exe. [CI isolado 43921882696](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43921882696) aprovado; as barras jogáveis permanecem 0/13.

**CH07 concluída:** o [runtime Sinnoh](../scripts/regions/SinnohPilot.rb) verifica flags, grava só ações confirmadas, recusa dois iniciais físicos e chamadas reentrantes, preserva o progresso após derrota válida de Barry, reload de save e viagens entre regiões e rejeita estados forjados. [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) bloqueia Novo Jogo QA com global ausente, sem cair em Decades. Novos [testes Ruby CH07](../tests/sinnoh_pilot_ch07_runtime.rb) e testes do [início QA](../tests/sinnoh_qa_start_runtime.rb) rodam no CI isolado: [execução 43920105394](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43920105394). Não comprova execução no Game.exe nem aprovação de Sinnoh jogável.

**CH06 concluída:** [schema JSON 2020-12](../data/regions/sinnoh-twinleaf-events.schema.json), [auditor estático](../scripts/regions/audit_sinnoh_twinleaf_events.py) e [15 testes negativos/positivos](../tests/test_sinnoh_twinleaf_schema.py) verificam os 9 mapas, 24 eventos, 16 warps, oito pares bidirecionais, alcance, IDs, campos e limites com dimensões locais. O template continua com `null/false`; somente a nota desatualizada de 15 portais foi corrigida para 16. Nem um mapa real, nem Game.exe/JoiPlay, nem qualquer save foi modificado. A auditoria **não libera instalação**.

**CH05 concluída:** o [manifesto auditável](../data/regions/sinnoh-map-id-reservations.json) e o [validador](../scripts/regions/audit_region_map_id_reservations.py) distinguem ocupação física **não fornecida**, reservas de código Johto 600–699 / Hoenn 700–999, IDs variáveis de Kanto e Decades desconhecidos e o piloto isolado Sinnoh 800–805. Relatório local RXDATA opcional permite observar ocupação sem atribuir dono nem declarar ID livre. Testes de adulteração/falsas aprovações estão em [test_sinnoh_map_id_reservations.py](../tests/test_sinnoh_map_id_reservations.py). Nenhum mapa, save ou Game.exe foi alterado.

**CH04 concluída:** o [guard de plugin legado](../scripts/regions/sinnoh_legacy_plugin_guard.py) impede `SinnohPreview.rb`, `BlueSinnohPreview`, metadados/flags de piloto e perfil de save isolado no jogo principal, lançador, instalador Johto e origem da cópia QA Sinnoh. O overlay compartilhado é auditado antes de gravação. [Testes negativos](../tests/test_sinnoh_legacy_plugin_guard.py) e regressões foram incluídos no CI. Piloto standalone não foi modificado. Isso não prova gameplay.

**CH03 concluída:** `scripts/regions/sinnoh_map_id_guard.py` recusa IDs 600–999 para Sinnoh integrada, inclusive os seis legados 800–805, e protege a fronteira de escrita do preview compartilhado de Johto contra a inclusão de mapas externos; arquivos já existentes de Hoenn não são removidos. Testes de guarda e regressão estão no CI. Isso não cria mapas reais nem libera Sinnoh.

**CH02 concluída:** `scripts/regions/validate_sinnoh_chat_progress.py` é uma verificação **somente leitura** de IDs, prioridades, estado, contagens, evidências e consistência entre JSON, tabela e Barra E. Testes negativos estão em `tests/test_sinnoh_chat_progress.py`; a workflow de regressão inclui um passo explícito.

## 3. Mapeamento exaustivo das 32 entregas oficiais (S01–S32)

Legenda: **GitHub** = pode publicar código/dados/docs completos aqui; **Misto** = publicar preparação aqui, só concluir com dados/testes reais locais; **Local** = depende de execução nativa, embora o chat possa criar auditoria/roteiro.

| ID | Pode ser realizado diretamente neste chat / main | Fronteira que NÃO se resolve apenas com GitHub | Tipo |
|---|---|---|---|
| S01 | Auditor de origem ZIP/pasta, segurança e testes | Fonte efetiva e direitos | GitHub (código já existe) |
| S02 | Auditor RXDATA de mapas, tilesets, eventos, transferências e testes | Rodar em arquivos fonte reais | GitHub (código já existe) |
| S03 | Análise e testes de capacidade de MapIDs | MapInfos/Data e reservas locais reais | GitHub (código já existe) |
| S04 | Manifesto da fonte, pendências e licença | Confirmação legal de reutilização de cada asset | GitHub (código já existe) |
| S05 | Inventário simbólico de áreas/eventos | MapIDs, interiores e NPCs de fonte real | GitHub (código já existe) |
| S06 | Grafo, relatório de transferências e testes | Caminhabilidade/dinâmica na engine | GitHub (código já existe) |
| S07 | Planejador, staging, SHA, rollback e segurança dos IDs | Remapeamento real e implantação em Game.exe | Misto |
| S08 | Validar hashes, recursos ausentes, referências e relatórios | Conferir gráficos/collisions nativos reais | Misto |
| S09 | Menu, botão Testar Sinnoh e testes sem motor | UI operando no executável real | GitHub (código já existe) |
| S10 | Arquivo/launcher seguro, validação e erro controlado | Executar BAT/EXE Windows com instalação real | Misto |
| S11 | Preparador de piloto/save isolado, contratos e testes | Mapas, sprites, PBS compilados e save/load real | Misto |
| S12 | Instalador privado, dry-run, manifests e rollback | Instalar/compilar na máquina com dados autorizados | Misto |
| S13 | Ruby autoral Rowan/Barry/mãe, eventos/flags, testes | Spawns, colisões, batalhas e cenas jogadas | Misto |
| S14 | Três Poké Bolas, prevenção de duplicidade e testes | Eventos posicionados e sprites reais no mapa | Misto |
| S15 | PBS/registradores dos oito ginásios e contratos de badge | NPC, puzzle, vitória real, item e insígnia | Misto |
| S16 | Política de HMs e testes de permissão local | Uso de HM em obstáculos reais | Misto |
| S17 | Modelos e adaptadores de treinador/IA e level scaling | Equipes reais em cada NPC e batalha | Misto |
| S18 | Tabelas propostas de encontro/horário/cap e validação | Slots, mapa real, captura e animações de campo | Misto |
| S19 | Lógica de flags Galactic, scripts autorais e testes | Cutscenes, NPCs, edifícios e evento nativo | Misto |
| S20 | Contrato de Cyrus, Spear Pillar e Giratina | Mundo Distorcido, mapas/puzzles e execução | Misto |
| S21 | Cadastro de Elite/Cynthia, condições e Hall of Fame | Batalhas reais, salas, vitória/derrota | Misto |
| S22 | Gate de viagem e desbloqueio Hoenn/Unova e regressões | Portais, MapIDs e save compartilhado comprovados | Misto |
| S23 | Catálogos pós-jogo/revanche e idempotência de eventos | Battle Zone, lendários e rematches jogados | Misto |
| S24 | Plano/catalogação musical, regras e créditos | Música utilizável/legalmente distribuível | Misto |
| S25 | Integração de chaves BlueMusic e fallback | Reprodução/loop/fade real de faixas | Misto |
| S26 | Testes de prioridade/fallback/fade sem motor | Testes auditivos no Windows/JoiPlay | Misto |
| S27 | Página e guias Sinnoh com estado honesto e mapas simbólicos | Publicar como guia de áreas já acessíveis só com prova real | GitHub (site planejado) |
| S28 | Catálogo de equipes de líderes e Liga no site | Conferência com PBS final e time no jogo | Misto |
| S29 | Ocultar níveis fixos; indicar badge/esmeraldas/cap no site | Nível real só comprovável em batalha | GitHub (site/código) |
| S30 | Unitários, fixtures, regressões, CI e verificações de esquema | End-to-end gráfico do game | GitHub (suite de código) |
| S31 | Criar protocolo/validador de logs, imagens e 44 testes | **Aceite Windows + JoiPlay é local** | Local |
| S32 | Atualizar planos, docs de integração, backlog e barras verificáveis | Evidências locais não podem ser fabricadas | GitHub (documentação) |

**Conclusão:** dá para publicar diretamente na `main` a **camada de engenharia** de praticamente todas as 32 linhas; isso **não** significa que os requisitos finais de jogabilidade de S07–S31 possam ser aprovados sem a instalação local e os assets autorizados. O único aceite essencialmente local é S31, e todas as outras tarefas "mistas" terminam em prova nativa.

## 4. Reutilizar antes de escrever código novo

- **Infraestrutura:** [`audit_sinnoh_rxdata.py`](../scripts/regions/audit_sinnoh_rxdata.py), [`plan_sinnoh_remap.py`](../scripts/regions/plan_sinnoh_remap.py), [`convert_sinnoh_geometry.py`](../scripts/regions/convert_sinnoh_geometry.py), [`sinnoh_staging_transaction.py`](../scripts/regions/sinnoh_staging_transaction.py).
- **Introdução:** [`SinnohPilot.rb`](../scripts/regions/SinnohPilot.rb), [`build_sinnoh_twinleaf_events.py`](../scripts/regions/build_sinnoh_twinleaf_events.py), [`build_sinnoh_barry_pbs.py`](../scripts/regions/build_sinnoh_barry_pbs.py).
- **QA:** [`prepare_sinnoh_pilot_bundle.py`](../scripts/regions/prepare_sinnoh_pilot_bundle.py), [`install_sinnoh_qa_copy.py`](../scripts/regions/install_sinnoh_qa_copy.py), [`audit_sinnoh_playtest.py`](../scripts/regions/audit_sinnoh_playtest.py).
- **Proteções:** [`SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md`](SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md) e [`SINNOH_CODEX_PENDENCIAS.md`](SINNOH_CODEX_PENDENCIAS.md).
- **Portal:** [`site/public/data/regions.json`](../site/public/data/regions.json), [`site/public/data/pending-regions.json`](../site/public/data/pending-regions.json).
- **Testes:** `tests/test_sinnoh_*.py`, `tests/sinnoh_*.rb` e `tests/title_kanto_runtime.rb` (testes de execução fictícia não equivalem a validação em Game.exe).

### S27 — Guias Sinnoh no site (Barra A concluída)

A [S27](SINNOH_S27_GUIAS_PORTAL_ACEITE.md) foi concluída no escopo do portal web: as páginas e referências de Sinnoh já estão disponíveis nos módulos CH17–CH18, com navegação, pesquisas e rótulos honestos de `planned`; o [teste adicional de aceite](../site/tests/sinnoh-s27-development.test.mjs) confirma que 8 abas, áreas, treinadores, ginásios, Liga e HMs são dados de referência e não eventos instalados. **Barra A: 9/32 (28%)** após CI e merge; os 44 testes nativos continuam pendentes, B/C/D permanecem 0/13 e Barra E 20/20 (100%).

### S29 — nível dinâmico no guia (Barra A concluída)

A [S29](SINNOH_S29_NIVEIS_DINAMICOS_PORTAL_ACEITE.md) explica a fonte real do cálculo `70% Normal / 90% Master` sobre o maior Pokémon não-ovo da party. Em todas as oito abas, o guia diferencia regra de balanceamento, insígnias regionais/esmeraldas e número efetivo só calculável numa batalha real; **não inventa cap numérico regional**, nível fixo de treinadores ou níveis de encontros. [Testes S29](../site/tests/sinnoh-s29-dynamic-levels.test.mjs) e filtros negam falso `levelCap`, `effectiveLevel`, equipe instalada ou leitura de save. **A Barra A atinge 10/32 (31%)**, com B/C/D 0/13 e Barra E 20/20.

### S30 — matriz de testes automatizados offline (Barra A concluída)

A [S30](SINNOH_S30_SUITE_AUTOMATIZADA_ACEITE.md) consolida os testes Python/Ruby de Sinnoh, o portal e os testes estáticos Android em [workflow S30](../.github/workflows/sinnoh-s30.yml), cinco jobs independentes. O [auditor de cobertura com hashes](../scripts/regions/audit_sinnoh_s30_suite.py) exige fontes e testes e recusa falso sucesso sem aprovações do workflow; [11 testes S30](../tests/test_sinnoh_s30_suite.py) incluem manipulações de QA, componentes faltantes e sobrescrita de relatórios. **Barra A 11/32 (34%)**, 6 parciais, 15 pendentes; B/C/D 0/13, E 20/20. Sem Game.exe/JoiPlay reais nem liberação de mapas/Sinnoh jogável.

### S28 — catálogo de times de líderes e Liga (Barra A concluída no portal)

A [S28](SINNOH_S28_CATALOGO_TIMES_REFERENCIAS.md) gera uma apresentação auditável de **13 equipes históricas Platinum** (8 ginásios, 4 Elite e Cynthia), 5 revanches de referência e a pendência de times nativos dos 40 treinadores gerais. O [gerador CH17/S28](../site/scripts/sinnoh-guide.mjs), [schema](../site/src/assets/sinnoh-search.js) e [10 testes S28](../site/tests/sinnoh-s28-trainer-teams.test.mjs) recusam PBS compilado inventado, Full Power falseado, níveis fixos, mudança de origem e campos extras. **Barra A 12/32 (37%)** (6 parciais, 14 pendentes), E 20/20; B/C/D 0/13 e 44 casos nativos ainda pendentes. Esta entrega documenta times planejados, **não aprova batalhas Game.exe**.

### S10 — duplo clique experimental Windows (Barra A concluída em código)

O [BAT S10](../SINNOH_JOGAR_EXPERIMENTAL.bat) invoca o [launcher Python](../scripts/regions/launch_sinnoh_qa.py) para localizar **exatamente uma** pasta privada `.blue-work/game-sinnoh-qa-<token>`. A seleção exige nome auditável, recusa symlink/ambiguidade e usa verificações de transação, SHA-256 e save segregado antes de compilar ou lançar o `Game.exe` **privado**. Nunca busca `game/Game.exe` principal nem inicia Johto/Hoenn/Decades como fallback. `--check` apenas lê, e o BAT informa erros quando não há cópia QA instalada.

[15 testes S10](../tests/test_sinnoh_s10_launcher.py) validam o fluxo sem executar `Game.exe` real e a [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige os arquivos do lançador. Documentação e critérios: [aceite S10](SINNOH_S10_LANCADOR_EXPERIMENTAL_ACEITE.md). **Barra A 13/32 (40%)**, 6 parciais, 13 pendentes; E 20/20 e **B/C/D 0/13**. S11/S12 e os 44 testes Windows/JoiPlay continuam bloqueados por instalação/QA reais.

### S11 — saves privados de Sinnoh (Barra A concluída em código)

A [S11](SINNOH_S11_PILOTO_SAVES_ISOLADOS_ACEITE.md) introduz verificação cruzada do token privado nas configurações `mkxp.json`, `Game.ini` e no manifesto QA. O [instalador privado](../scripts/regions/install_sinnoh_qa_copy.py) e o [launcher](../scripts/regions/launch_sinnoh_qa.py) bloqueiam inicialização em pasta ou namespace divergente; o [Ruby QA](../scripts/regions/SinnohQAStart.rb) rejeita saves antigos sem `blue_regions.initial=current=SINNOH` **antes do fluxo original poder carregá-los**. [13 testes Python](../tests/test_sinnoh_s11_save_isolation.py) e [fixture Ruby](../tests/sinnoh_qa_start_runtime.rb) garantem, com dados sintéticos, que a cópia privada não usa nem remove saves das outras regiões.

**Barra A 14/32 (43%)** (6 parciais, 12 pendentes), Barra E 20/20; B/C/D 0/13. Nem a S11 nem o CI afirmam compilação ou abertura real de mapas, save/reload no Windows ou QA JoiPlay: isso continua no piloto S12 e na S31.

### S12 — instalação transacional privada de Sinnoh (Barra A concluída em código)

O [BAT S12](../SINNOH_INSTALAR_EXPERIMENTAL.bat) usa o [orquestrador Python](../scripts/regions/sinnoh_s12_installer.py) para selecionar **um único overlay autorizado** e a especificação local `.blue-work/sinnoh-qa-spec.json`. O script inicia em `dry-run` e só cria arquivos com `--install`; o BAT, ao ser aberto por duplo clique, tenta essa instalação **somente após a auditoria integral dos insumos**. Rejeita fontes inexistentes, symlinks, MapIDs colidentes, manifestos adulterados, saves e instalações QA preexistentes. Copia a base para pasta temporária privada, verifica SHA-256, publica por rename atômico e faz rollback da transação antes da publicação em caso de falha. **Não copia saves, não toca em game/, não baixa assets, não executa Game.exe.**

A [S12](SINNOH_S12_INSTALADOR_QA_ISOLADO_ACEITE.md) inclui [16 testes sintéticos de instalação e rollback](../tests/test_sinnoh_s12_installer.py) na regressão CH19/S30. **Barra A 15/32 (46%)**, 6 parciais e 11 pendentes; E 20/20 e B/C/D 0/13. O piloto em dados reais continua bloqueado pela ausência de fontes autorizadas e de QA Windows/JoiPlay.

### S08 — validador de integridade de recursos (Barra A concluída em código)

O [validador S08](../scripts/regions/audit_sinnoh_s08_resources.py) consolida auditoria RXDATA, ligações/MapIDs, referências de tilesets/autotiles, assinatura PNG, dependências Ruby e hashes SHA-256 dos mapas/scripts/PBS gerados. O [instalador S12](../scripts/regions/sinnoh_s12_installer.py) agora **bloqueia a criação de QA privada se a S08 não aprovar os recursos**. A [cobertura com 16 testes](../tests/test_sinnoh_s08_integrity.py) usa apenas arquivos sintéticos, não altera o Decades ou saves, não executa Game.exe e rejeita report falso, gráficos corrompidos e links inseguros.

O [aceite S08](SINNOH_S08_INTEGRIDADE_RECURSOS_ACEITE.md) só conclui a infraestrutura de auditoria em código: **Barra A 16/32 (50%)**, 5 parciais, 11 pendentes; E 20/20, B/C/D 0/13; 44 casos nativos seguem não observados. Direitos dos assets, renderização, colisões e QA real continuam bloqueados sem fonte legítima.

### R07 — diagnóstico de reservas futuras sem conclusão falsa da S07

O [diagnóstico R07](SINNOH_R07_DIAGNOSTICO_RESERVAS.md) e o [BAT de duplo clique](../SINNOH_DIAGNOSTICAR_PENDENCIAS.bat) leem o MapInfos local e manifestos futuros de Kanto, Johto e Hoenn sem tocar `game/` ou saves, e geram `.blue-work/sinnoh-diagnostics/r07-reservations.json`. A [suite de 16 testes negativos](../tests/test_sinnoh_r07_reservations.py) detecta IDs ocupados, reservas futuras conflitantes, baseline divergente, symlink e falso aceite nativo. A presença de código **não prova** que todas as reservas foram fornecidas: **S07 continua parcial (6/9, R07–R09 pendentes)**.

### S26 — regressões da política musical, offline

O [teste Ruby S26](../tests/sinnoh_s26_music_regression.rb), executado via [CH19](../scripts/regions/sinnoh_ci_ch19.py), confere todos os **46 cues CH16**, prioridades do BlueMusic, fallback sem faixa licenciada, ausência de loops/fades inventados, 11 transições e ausência de alteração em outra região. [Aceite e bloqueios](SINNOH_S26_TESTES_MUSICA_ACEITE.md). A **Barra A 17/32 (53%)** (5 parciais, 10 pendentes); B/C/D 0/13 e E 20/20. As tarefas S24/S25 exigem fonte/licenças e instalação real de áudio; o código de testes não desbloqueia músicas.

### S17 — regressões de battle scaling, sem NPCs instalados

O [contrato S17](../data/regions/sinnoh-trainer-balance-s17.json) e o [auditor estático](../scripts/regions/audit_sinnoh_s17_balance.py) validam as regras já existentes em [Campaign.rb](../scripts/battle_polish/Campaign.rb), [Story.rb](../scripts/battle_polish/Story.rb) e [EvolutionScaling.rb](../scripts/battle_polish/EvolutionScaling.rb). O novo [runner Ruby S17](../tests/sinnoh_s17_trainer_balance_runtime.rb) carrega os módulos reais por `Battle.prepend` com treinadores sintéticos e testa **70%/90%, ovos excluídos, evolução regular, chefes preservados, 4 integrantes no Master, até 6 adversários em duplas e zero alteração do PBS/party**. [10 testes Python](../tests/test_sinnoh_s17_trainer_balance.py) rejeitam alegações de `Game.exe`, rosters Platinum nativos e níveis fixos não comprovados.

A [S17](SINNOH_S17_TREINADORES_DINAMICOS_ACEITE.md) só conclui o escopo do runtime compartilhado e testes offline: **Barra A 18/32 (56%)**, 5 parciais, 9 pendentes, E 20/20, B/C/D 0/13. **Não há treinadores Sinnoh novos instalados nos mapas, nem batalhas Windows/Android certificadas**; S15/S16/S18–S23 e S31 continuam exigindo mapas/eventos reais.

### S18 — progressão selvagem por nível e teste do hook sem PBS nativo

A [S18](SINNOH_S18_ENCONTROS_EVOLUCOES_ACEITE.md) acrescenta uma proteção no [EvolutionScaling.rb](../scripts/battle_polish/EvolutionScaling.rb): não evoluir encontros com `base_level`/`cap` inválidos ou acima da referência de progressão, preservando o slot original. O [runner Ruby](../tests/sinnoh_s18_wild_runtime.rb) exerce o verdadeiro `WildEncounters` com dados sintéticos e valida chances **15%, 30%, 45%, 60%**, espécies originais, evolução em várias fases, limiares de pedra/troca/felicidade, horário, casos especiais e ausência de alteração nas tabelas de spawn de Kanto/Johto/Hoenn/Decades.

O [auditor S18](../scripts/regions/audit_sinnoh_s18_wild.py) e [12 testes negativos](../tests/test_sinnoh_s18_wild.py) vinculam a política ao catálogo CH13: **21 áreas de referência não são áreas jogáveis**, sem MapIDs, pesos, métodos/horários confirmados ou PBS compilados; Drifloon e Rotom ainda são eventos estáticos. **Barra A 19/32 (59%)**, 5 parciais, 8 pendentes, E 20/20, B/C/D 0/13 e 44 casos nativos aguardando dados reais. A regra compartilhada é exercida offline, não um encontro testado no Game.exe.

### S19 — Team Galactic, sequência CH14 por resultados confirmados (offline)

O [adaptador Ruby](../scripts/regions/SinnohGalacticContracts.rb) usa a única chave de save `sinnoh_ch14` para as cinco etapas **Windworks, Mars, Jupiter (Forest), Pastoria e Lagos**, respeitando batalhas confirmadas, ordem e bloqueio regional. Como não existem MapIDs/callbacks verificados, `VERIFIED_NATIVE_SOURCES` permanece vazio; **não registra eventos reais, não altera equipes, sprites, itens, NPCs ou mapas**. O [contrato S19](../data/regions/sinnoh-galactic-s19.json), [auditor Python](../scripts/regions/audit_sinnoh_s19_galactic.py), [12 testes negativos](../tests/test_sinnoh_s19_galactic.py) e [runner Ruby](../tests/sinnoh_s19_galactic_runtime.rb) cobrem resultados inválidos, repetição, sequência, saves e regressões cross-region. [Aceite/limitações](SINNOH_S19_TEAM_GALACTIC_ACEITE.md).

**Barra A 20/32 (62%)**, 5 parciais, 7 pendentes; E 20/20, B/C/D 0/13, 44 testes nativos aguardam fontes reais. S20 já dispõe de contratos/testes offline, mas S19 e S20 ainda requerem mapas/callbacks físicos para aprovação jogável.

### S20 — Cyrus, Spear Pillar, Mundo Distorcido e Giratina

O [adaptador Ruby S20](../scripts/regions/SinnohDistortionContracts.rb) expõe gates por resultado tipado e a única sequência `sinnoh_ch14` para as nove etapas da fase 8: Cyrus, Saturn, Mars, Jupiter, Dialga/Palkia, puzzles, Cyrus final, Giratina e retorno seguro. Só inicia após as cinco etapas S19, exige Mine+Icicle e **não modifica mapas, salva flags paralelas, força captura de Giratina ou gera teleportes**. O registro `VERIFIED_NATIVE_SOURCES` é vazio e o método público rejeita confirmações sem callback instalado. O [contrato S20](../data/regions/sinnoh-distortion-s20.json) segue a referência S39 e o inventário CH14; [auditoria](../scripts/regions/audit_sinnoh_s20_distortion.py), [16 testes negativos](../tests/test_sinnoh_s20_distortion.py) e [teste Ruby de salvamento/resultado](../tests/sinnoh_s20_distortion_runtime.rb) usam fixtures, nunca jogo nativo.

[Critérios de aceite S20](SINNOH_S20_CYRUS_DISTORTION_GIRATINA_ACEITE.md): **Barra A 21/32 (65%)**, 5 parciais, 6 pendentes; E 20/20, B/C/D 0/13, 44 casos nativos pendentes. Ainda requer mapas autorizados de Mt. Coronet/Distortion, encontros/puzzles reais, battle results e Game.exe/JoiPlay. **S21 possui contratos e testes offline, mas nenhuma batalha física de Elite/Cynthia/Hall foi instalada.**

### S21 — Liga de Sinnoh, Elite Four, Cynthia e Hall of Fame (offline)

O [adaptador Ruby S21](../scripts/regions/SinnohLeagueContracts.rb) preserva as oito etapas CH14 após o retorno seguro da S20: Volkner/Beacon, Barry após oito insígnias **locais** de Sinnoh, Aaron, Bertha, Flint, Lucian, Cynthia e o Hall of Fame. O resultado `battle_won` de Cynthia **não basta** para a conclusão da Liga: o Hall exige `engine_hall_of_fame_confirmed` independente, com atualização pelo CH14 da única lista regional `leagues`. Não cria flags de liberação de Hoenn/Unova, badges, recompensas ou portais.

O [contrato S21](../data/regions/sinnoh-league-s21.json) continua *reference_only*, com `VERIFIED_NATIVE_SOURCES` vazio, nenhum MapID ou PBS compilado, e oito checkpoints sem evento instalado. O [auditor](../scripts/regions/audit_sinnoh_s21_league.py) compara CH11, CH14, CH15, cobertura da fase 9 e o detonado S42/S43; [16 testes negativos](../tests/test_sinnoh_s21_league.py) e [testes Ruby de progresso/save](../tests/sinnoh_s21_league_runtime.rb) só usam fixtures sintéticas.

[Critérios de aceite e limitações](SINNOH_S21_ELITE_CYNTHIA_HALL_OF_FAME_ACEITE.md): **Barra A 22/32 (68%)**, 5 parciais e 5 pendentes, E 20/20, B/C/D 0/13. Os 44 casos nativos, salas, combates, Hall e save real no Game.exe/JoiPlay seguem **não realizados**. A S22 possui o pré-voo e testes offline, porém não instala a viagem física para Hoenn/Unova.

### S22 — Pré-verificação de viagens Sinnoh → Hoenn/Unova, sem mapas novos

O [contrato S22](../data/regions/sinnoh-travel-s22.json) é implementado em [`SinnohTravelContracts.rb`](../scripts/regions/SinnohTravelContracts.rb) e usa o CH14 (Hall confirmado) e as verificações reais de `BlueRegionTravel` sem autorizar viagem: o registro nativo de partida é **vazio**. Hoenn pode ter chegada auditada por instalação independente, mas **Sinnoh não possui mapa/NPC de saída**; Unova não tem ponto de chegada real. O circuito global de viagens livres existente **não depende de Hall** e não foi alterado.

O [runner Ruby S22](../tests/sinnoh_s22_travel_runtime.rb) testa `RegionTravel.stage_local_bag` com bolsa/PC falsos: separa HMs e itens-chave de origem/destino, preserva itens comuns, reverte corretamente ao regressar a Sinnoh e rejeita dados de inventário inválidos sem tocar no objeto real da prévia. O [auditor Python](../scripts/regions/audit_sinnoh_s22_travel.py) e [16 testes negativos](../tests/test_sinnoh_s22_travel.py) bloqueiam chegada fictícia de Unova, MapIDs de Sinnoh não instalados, Hall falso e permissões de NPC fabricadas. [Aceite S22](SINNOH_S22_VIAGENS_HOENN_UNOVA_ACEITE.md).

**Barra A 23/32 (71%)**, 5 parciais, 4 pendentes, E 20/20, B/C/D 0/13. Faltam instalação física, save/teleporte nativo e 44 verificações reais; **S23 possui contratos e testes offline, mas nenhuma área, missão ou revanche física foi instalada.**

### S23 — Battle Zone, missões opcionais e revanches sem NPC/PBS físico

A [S23](SINNOH_S23_POS_JOGO_REVANCHES_ACEITE.md) implementa apenas o [adaptador Ruby de pós-jogo](../scripts/regions/SinnohPostgameContracts.rb) e o [catálogo de 14 áreas/6 eventos](../data/regions/sinnoh-postgame-s23.json). Ele exige Hall CH14, bloqueia Heatran antes da Battle Zone e Darkrai/Shaymin sem confirmação nativa de evento; não fornece lendários, teleporte, item de evento nem flags de missão paralelas exceto o ledger opcional sintético de marcos `sinnoh_s23`. Nenhum handler `record_from_native` funciona enquanto `VERIFIED_NATIVE_SOURCES` permanecer vazio.

As **cinco revanches históricas Platinum** de Aaron, Bertha, Flint, Lucian e Cynthia são referências CH15, não times jogáveis. A revanche **Blue Full Power global** só pode ser preparada após **dez Ligas concluídas** e elenco nativo de revanche auditado; para lendários/míticos/UB/paradoxos na party valem as **oito insígnias locais** já existentes, não dez Ligas. O [auditor S23](../scripts/regions/audit_sinnoh_s23_postgame.py), [16 testes negativos](../tests/test_sinnoh_s23_postgame.py) e [runtime Ruby com saves sintéticos](../tests/sinnoh_s23_postgame_runtime.rb) verificam essas invariantes sem executar batalhas.

**Barra A 24/32 (75%)**, 5 parciais, 3 pendentes, E 20/20, B/C/D 0/13, 44 casos nativos ainda pendentes. Battle Zone, Stark Mountain, Battle Frontier e eventos lendários continuam **não instalados** no Game.exe/JoiPlay.

### S24 — catálogo dos 46 cenários musicais (sem gravações)

A [entrega S24](SINNOH_S24_CATALOGO_CENARIOS_ACEITE.md) acrescenta a [matriz](../data/regions/sinnoh-music-s24.json), o [auditor estático](../scripts/music/audit_sinnoh_music_s24.py) e [19 testes](../tests/test_sinnoh_s24_music.py). As 46 chaves CH16 foram associadas a contexto, guarda e fallback sem inventar licença, MapID, arquivo, evento ou binding. **S24 conclui catálogo, não música distribuível**: S25 e o teste nativo continuam bloqueados.

**Após CI e merge: Barra A 25/32 (78%)**, 4 parciais e 3 pendentes; E 20/20, B/C/D 0/13, 44 verificações nativas não realizadas.

### S25 — Ponte BlueMusic read-only, sem faixas instaladas

A [entrega S25](SINNOH_S25_BLUEMUSIC_INTEGRACAO_OFFLINE_ACEITE.md) adiciona [bridge Ruby](../scripts/music/SinnohBlueMusicBridge.rb), manifesto, [auditor](../scripts/music/audit_sinnoh_music_s25.py), 21 testes negativos e testes Ruby contra BlueMusic real, com preferências manuais e outras regiões preservadas. O registro de faixas nativas continua vazio.

**Após CI e merge: Barra A 26/32 (81%)**, 4 parciais, 2 pendentes; E 20/20, B/C/D 0/13. Sem licenças/áudio instalado e 44 testes nativos ainda necessários.

### S15 — oito ginásios em contrato, sem badges nativas instaladas

A [S15](SINNOH_S15_OITO_GINASIOS_INSIGNIAS_ACEITE.md) associa os [oito líderes Platinum](../data/regions/sinnoh-gyms-s15.json) a eventos e insígnias planejados, verificando CH15 (equipes), CH11 (HM/badges) e BlueRegions/BlueCampaign. A [ponte Ruby](../scripts/regions/SinnohGymContracts.rb) mantém `VERIFIED_NATIVE_SOURCES` vazio e impede concessão de insígnias por eventos falsos. O [auditor](../scripts/regions/audit_sinnoh_s15_gyms.py), [22 testes Python](../tests/test_sinnoh_s15_gyms.py) e [fixture Ruby](../tests/sinnoh_s15_gyms_runtime.rb) só exercitam contratos offline. Nenhum Ginásio real foi importado.

**Após CI e merge: Barra A 27/32 (84%)**, quatro parciais, um pendente; E 20/20 e B/C/D 0/13. 44 verificações nativas ainda necessárias.

## 5. Bloqueios que exigem Windows/Android, Codex local ou fonte fornecida

| Entrega exclusivamente local ou dependente de arquivos ausentes | Prova a exigir |
|---|---|
| Permissão e integridade de fonte editável de Sinnoh | Arquivo fonte/hashes/licença por recurso; não publicar asset não autorizado |
| Auscultar `game/Data` e reservas existentes | Inventário de MapIDs/tilesets efetivamente instalados e ocupações futuras |
| Escolher/remapear MapIDs definitivos | Manifesto de origem→destino e 100% das transferências resolvidas |
| Compilar scripts, eventos, PBS e Game.exe de QA | Resultado do compilador, relatório estrutural e lançamento real |
| Caminhar em Twinleaf/Sandgem e depois em todos os segmentos | Evidência visual de passabilidade, NPCs, interiores, portais e eventos |
| Barry, ginásios, Liga, XP e escalonamento | Resultado de batalhas reais, níveis, vitória/derrota, save/load |
| Música e recursos externos | Arquivos autorizados; escuta e fallback em Windows e Android |
| Viagem multirregional e save antigo | Mesma instalação/saves reais sem regressão e rollback testado |
| JoiPlay e atualização Android | Teste em aparelho, menus, encontros, performance, saves e relatório de execução |

## 6. Protocolo de cada próxima entrega CH

1. Ler `AGENTS.md`, este mapeamento, `SINNOH_PROGRESSO.md`, JSON de progresso e scripts atuais da função afetada.
2. Identificar **arquivos novos/alterados** e casos negativos, assegurar que o escopo de Sinnoh não sobrescreve Kanto/Johto/Hoenn/Decades.
3. Fazer a implementação com estado `planned`/QA e testes reais do que pode ser executado sem a base do jogo. Não ligar conteúdo experimental ao principal.
4. Publicar diretamente na `main` sem force push e atualizar **somente** a(s) entrada(s) CH realmente concluída(s).
5. Informar SHA/links, verificações PASS/FAIL/não executadas e bloqueios; preservar barras oficiais de 13 fases até aceitação.

**Próxima ação sugerida após CH01–CH20:** obter e auditar fonte real autorizada, reconciliar MapIDs, instalar em cópia QA separada e executar os 44 testes nativos Windows/JoiPlay previstos em S13/S14/S31; **não** ativar Sinnoh no Game.exe sem essas evidências. CH01–CH20 estão concluídas apenas em código/testes/documentação.
