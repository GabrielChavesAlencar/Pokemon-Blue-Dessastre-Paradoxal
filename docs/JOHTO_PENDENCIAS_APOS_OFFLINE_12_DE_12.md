# Johto — o que falta após concluir 12/12 de preparação offline

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data de referência:** 13/11/2026  
**Escopo:** checklist operacional da instalação jogável, campanha completa de Johto, testes reais e publicação.  
**Fonte de verdade:** estado da `main` após a [auditoria offline 12/12](JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md), [progresso estruturado](../data/regions/johto-progress.json) e planos de campanha já versionados.

> **Atenção:** o **100% OFFLINE** significa que a preparação do piloto e o pacote de auditoria foram concluídos; **não** significa Johto instalada, totalmente implementada, liberada no `Game.exe` ou testada. **Não** marcar `VERIFIED_PLAYABLE`, criar arquivos de `ready`, ativar `--apply` ou incrementar a barra de jogabilidade por passar testes Python/Ruby.

## 1. Estado verificado e diferença entre as barras

| Indicador | Estado atual | O que mede |
|---|---:|---|
| **Preparação OFFLINE** | **12/12 — 100%** | Scripts, mapas do piloto, PBS propostos e auditoria de arquivos em pasta privada |
| **Fases técnicas integralmente aprovadas** | **0/16** | Critérios técnicos completos, direitos, integração e validação conforme cada fase |
| **Fases JOGÁVEIS** | **0/13** | Conteúdo real que roda no `Game.exe` isolado com fluxo percorrível |
| **Fases TESTADAS no EXE** | **0/13** | QA real aprovado do conteúdo jogável, inclusive saves/regressões |
| **Cobertura de testes de código/contrato** | **16/16** | Existem testes sintéticos para as fases — **não** provas de gameplay |

**Já preparado em arquivos privados (não instalado automaticamente):**

- **74 mapas de terreno** extraídos da fonte Johto, remapeados; mais **8 interiores autorais/provisórios**, totalizando **82 RXDATA `Map600–Map681`** na prévia.
- **32 eventos próprios:** **16 transferências** e **16 ações/NPCs/treinadores**. New Bark, laboratório do Elm, iniciais, Silver, Rotas 29–31, Violet, Falkner e Torre Sprout receberam conteúdo piloto.
- **44 conexões PBS**, sendo **42 da fonte** e **2 inferidas por geometria**, que ainda precisam de prova de travessia no motor.
- **21 versões de equipes PBS** (Silver 3; treinadores das Rotas 29–31: 10; Violet/Sprout: 8) e **6 tabelas selvagens** para três rotas. **Os PBS ainda não foram compilados/testados pelo Essentials**.
- Assets de mapas e sprites de campo reunidos no **ZIP privado de auditoria**; dois nomes de NPC corrigidos em cópias dos mapas 680/681. **Gráficos de batalha de treinador e os direitos de distribuição permanecem pendentes**.
- Os módulos Ruby de várias fases posteriores já estão no GitHub, mas **ter o módulo/contrato não significa que existam os mapas internos, NPCs, itens e batalhas em funcionamento**.

O pacote de auditoria é **`NOT_INSTALLABLE`**: os módulos Ruby estão em `review_only/Ruby/`, não carregados pelo jogo; não há instalador automático validado. **Não copiar o ZIP por cima de `game/`.**

## 2. Ordem de trabalho recomendada — prioridades e critérios de conclusão

### P0 — tornar o começo de Johto instalável em uma cópia de teste, SEM liberar a instalação pública

- [ ] **P0.1 — Fonte, direitos e baseline:** inventariar autoria, licença/permissão e créditos de mapas, tilesets, sprites, músicas e textos; substituir recursos sem autorização de redistribuição por equivalentes originais/autorizados. Registrar SHA-256 de `game/Data`, `PBS`, `Graphics`, `Plugins`, `Scripts` e saves na instalação de origem, sem publicá-los no GitHub.
- [ ] **P0.2 — Cópia isolada segura:** criar `game-johto-qa/` separada, com backups, diretórios e hashes; nunca sobrescrever Decades/Kanto nem os saves reais. Falhar se algum MapID 600–681, nome de recurso, tipo de treinador ou variável/switch colidir com a instalação existente.
- [ ] **P0.3 — Instalador transacional:** implementar **modo dry-run** e instalação reversível **somente na cópia de teste**: aplicar por arquivo necessário, criar backup, verificar hashes, gravar manifesto e permitir **rollback íntegro** após erro. Prevenir path traversal, links simbólicos e overwrite silencioso. Adaptar `scripts/regions/install_johto.py` **após revisão**; o `--apply` hoje é deliberadamente bloqueado.
- [ ] **P0.4 — Recursos e referências:** conferir todos os 82 MapNNN, 289 entradas de `MapInfos` do staging, `Tilesets`, autotiles, sprites de campo e referências de eventos. Auditar identificadores, passabilidade, portas, escadas, respawns e as duas bordas inferidas. Nenhuma conexão duplicada.
- [ ] **P0.5 — Carregar os handlers no Essentials real:** integrar de forma controlada `JohtoPilot.rb`, `JohtoRouteTrainers.rb`, `JohtoViolet.rb` e as dependências existentes, **sem importar motores de batalha, plugins ou `Scripts.rxdata` de outra base**. Confirmar que `RPG::EventCommand(201/355)` é aceito pela versão nativa.
- [ ] **P0.6 — Compilar e validar PBS:** reconciliar `map_connections`, `trainer_types_johto*`, `trainers_johto*`, `encounters_johto_routes.txt` com os formatos reais do Essentials/Blue. Resolver nomes de tipo de treinador e **gráficos de batalha** (`BLUE_JOHTO_*`), espécies, golpes, níveis, encontros dia/noite e variantes 0/1/2. Detectar duplicações com PBS atuais. **Não criar marcadores de `ready` antes do QA correspondente.**
- [ ] **P0.7 — Completar funcionalidades mínimas do piloto:** executar a abertura em New Bark **dentro do quarto**, com mãe, Elm, três Poké Bolas individuais sem menu nem duplicação, Silver e rotas até Violet; revisar portas/fachadas, sprites e diálogos. Implementar e testar a **cura no Centro Pokémon de Violet**, hoje propositalmente não funcional.
- [ ] **P0.8 — Usar o balanceamento do Blue, não um paralelo:** verificar em batalha real `BlueStory.stage`, `BlueCampaign.common_level/wild_level`, global de insígnias/esmeraldas, **70% normal, 90% Master, 45% selvagem**, equipes de 4 no Master e evoluções condicionadas ao level cap. Os níveis-base do PBS não comprovam o escalonamento dinâmico.
- [ ] **P0.9 — Johto no menu sem afetar outras regiões:** conservar `Continuar`, `Novo Jogo` e `Testar Kanto`; o menu `Testar Johto` somente pode carregar a **cópia de teste realmente montada** com spawn/hashes válidos. O fluxo normal e o seletor de região só devem habilitar Johto após prova de instalação e direitos.
- [ ] **P0.10 — Teste de regressão da instalação:** comparar antes/depois e executar rollback em caso de falha simulada, duas instalações seguidas (idempotência), save antigo, save novo e mudança de região. Não sinalizar que `Blue-Story.exe` instala tudo até essa cadeia estar implementada e aprovada.

**Critério de saída de P0:** a cópia isolada abre New Bark e percorre o corredor até Violet com eventos, batalha e persistência funcionais. Só após isso a **fase de campanha 04/16 poderá ser marcada jogável (1/13)** — não antes; a barra *testada* exige o QA da seção 5.

### P1 — finalizar a campanha principal de Johto usando o motor existente

Os arquivos `docs/JOHTO_FASE_04_*.md` a `docs/JOHTO_FASE_16_*.md` e scripts Ruby de campanha são **pontos de partida**. Cada fase precisa converter planejamento em **mapas reais, interiores, NPCs, itens, batalhas, eventos, PBS, músicas, saves e travessias** sem copiar a engine de outro jogo.

| Fase da campanha | O que ainda precisa ficar funcional | Aceite jogável |
|---|---|---|
| **04/16 — New Bark** | Casa/quarto, Elm, três iniciais físicos, Silver, saída e save | Escolher um único inicial, sair/voltar e salvar/recarregar |
| **05/16 — Cherrygrove e Violet** | Rotas 29–31, encontros, visitas a interiores, Torre Sprout, Falkner, Zephyr e Centro com cura | Chegar a Violet, vencer Falkner e obter **uma** Zephyr |
| **06/16 — Azalea/Bugsy** | Rota 32, Union Cave, Slowpoke Well, Rocket, Kurt, ginásio Bugsy e Hive Badge | Percurso e missão Rocket completos; insígnia gravada |
| **07/16 — Ilex/Goldenrod** | Farfetch'd/Cut, Rota 34, Day Care, Goldenrod, Whitney, Plain Badge, Sudowoodo e itens | Eventos encadeados e acesso à próxima rota |
| **08/16 — Ecruteak/Morty** | Rotas 35–37, National Park, Burned Tower, Morty, Fog Badge, encontros e cenas | Ginásio e progressão concluídos sem loops |
| **09/16 — Olivine/Cianwood/Chuck** | Lighthouse, travessia Surf das Rotas 40–41, farmácia/SecretPotion e Chuck | SecretPotion única, Chuck e Storm Badge |
| **10/16 — Jasmine/Ampharos** | Retorno à Lighthouse, cura de Amphy, Jasmine, Mineral Badge e acessos a Whirl Islands | Amphy recuperado e Jasmine derrotada uma vez |
| **11/16 — Mahogany/Pryce/Rocket** | Lake of Rage, Rocket HQ, Pryce, Glacier Badge, invasão da Radio Tower | Condições Rocket, gelo e história persistentes |
| **12/16 — Blackthorn/Clair** | Route 44, Ice Path, Blackthorn, Clair, Dragon's Den, Rising Badge | 8 insígnias **locais**, desbloqueios e flags corretos |
| **13/16 — Liga de Johto** | Tohjo Falls, Victory Road, Will/Koga/Bruno/Karen, Lance, Hall of Fame | Liga concluída, recompensas idempotentes, desbloquear **Kanto + Hoenn** |
| **14/16 — Lendários/pós-jogo** | Raikou/Entei/Suicune, Bell Tower, Whirl Islands, Ruins of Alph, encontros condicionais, rematches | Eventos únicos e pós-jogo jogáveis sem quebrar o save |
| **15/16 — Música/treinadores/portal** | BGMs/MEs autorizados, loops, fades, mapas no site, Dex “onde capturar”, times normal/Master | Catálogos correspondem aos dados **instalados e testados** |
| **16/16 — Integração e aceite** | Viagem entre regiões, Box, HMs locais, bloqueios especiais, instalador final, CI, Windows/JoiPlay | Provas de release concluídas; rollback e saves aprovados |

**Por fase, executar sempre nesta ordem:**

1. Identificar mapas já disponíveis na fonte de terreno e **todos os interiores/andares ainda ausentes**; construir ou obter recursos com direitos válidos.
2. Posicionar portas, conexões, escadas e NPCs; conferir origem e destino reversíveis, colisões e eventos de cenário com coordenadas reais.
3. Implementar diálogos autorais/adaptados, switches de história, itens visíveis/ocultos, presentes únicos, lojas, TMs/HMs, puzzles, cenas e condições de chegada/saída.
4. Montar PBS de treinadores/rival/líder/Rocket e de encontros por bioma, horário, tipo de terreno, Surf/pesca e condições, usando os Pokémon/golpes/habilidades do **Blue**, com versões normal/Master.
5. Integrar música e efeitos permitidos, fallback quando ausente, fades/loops e ajustes de prioridade por eventos.
6. Testar a fase **em cópia isolada** e comparar com Kanto/Decades; registrar evidências por rota, evento, batalha, insígnia, save/reload, captura e volta.
7. Só então atualizar `johto-progress.json`: o contador **jogável** pode avançar após completar o fluxo real; **testado** exige todos os critérios de QA do cenário.

### P2 — requisitos regionais que não podem ser esquecidos

- [ ] **Uma campanha/um save:** manter Pokémon, PC, Dex, dinheiro, itens, opções, histórico, missões e estados de cada região ao viajar; tratar migração de saves antigos e autosaves.
- [ ] **Insígnia local × esmeraldas globais:** cada insígnia de Johto soma **uma vez** ao contador global de esmeraldas/cristais do Blue; HMs/field moves dependem das **insígnias locais** pertinentes, não apenas do total global.
- [ ] **Pokémon especiais:** lendários, míticos, Ultra Beasts e Paradoxos ficam **fora da party** ao entrar numa região com menos de oito insígnias locais e ficam bloqueados na Box até a liberação; não perder itens ou Pokémon na viagem.
- [ ] **Viagens:** após Liga Johto, NPC de New Bark libera somente destinos desbloqueados **Kanto + Hoenn**, se as regiões de destino já possuírem mapas/instalação válidos; não teleportar para mapa inexistente.
- [ ] **Pós-jogo forte:** após completar todas as campanhas principais previstas, usar os times mais fortes oficiais/documentados de líderes, Elite e campeões, aplicando **o balanceamento original** sem inventar um segundo escalonador.
- [ ] **Cartão de treinador e portal:** página regional com oito insígnias de Johto e página global com todas; lista de treinadores, equipes/versões, mapa, músicas, Pokédex, onde capturar, missões e histórico refletindo o jogo real.
- [ ] **Atividades HGSS:** Pokégear/telefone/rematches, Headbutt, Apricorns/Kurt, Day Care, rádio, Bug-Catching Contest, Pokéathlon, Safari Zone, S.S. Aqua, Battle Frontier e demais atrações aplicáveis. Para cada uma, implementar equivalência validada ou registrar claramente como **não implementada**; não dizer “HGSS completo” sem cobertura.

## 3. Bloqueios de entrega atuais

| Bloqueio | Evidência no projeto | Como resolver |
|---|---|---|
| **O pacote é uma prévia offline** | `data/regions/johto-stage12-package-contract.json`: `can_install=false` | Construir pipeline instalável **somente em cópia de teste** e depois liberar sob QA |
| **`install_johto.py --apply` bloqueado** | `scripts/regions/install_johto.py` deliberadamente read-only | Implementar backups + rollback e provas antes de permitir aplicação |
| **PBS não compilados** | Relatório 12/12 indica `pbs_compiled=false` | Compilar no Essentials real, validar conflitos, sprites e batalha |
| **Centros/interiores provisórios** | `docs/JOHTO_OFFLINE_FASE_11_VIOLET_SPROUT_FALKNER.md` | Completar interiores, sprites e cura, testar portas |
| **Conteúdo após Violet não montado em gameplay** | Fases 06–16 são contratos/scripts e planejamento, não aceite real | Construir mapas interiores, NPCs, itens e eventos por fase |
| **Músicas/redistribuição pendentes** | `data/johto-music.json` e documentação de fonte | Verificar licença, obter áudios permitidos ou criar substituições |
| **Sem QA de `Game.exe`** | `johto-progress.json`: jogáveis/testadas 0/13 | Executar testes reais e salvar registros/hashes, sem confundir CI com gameplay |
| **Instalação/site não sincronizados** | Pacote privado não alimenta automaticamente `game/` nem portal | Gerar dados do portal **após** a compilação e aprovação dos mapas/treinadores |

**A ausência de autorização para redistribuição não impede a documentação e a auditoria privada, mas impede tratar recursos não licenciados como pacote público distribuível.** Não publicar ZIPs privados, ROMs ou binários de origem no GitHub por conveniência.

## 4. Estratégia de testes — antes e depois do `Game.exe`

### 4.1. Automatizados offline: podem rodar agora

```powershell
python -m unittest discover -s tests -p "test_johto*.py" -v
python scripts/regions/install_johto.py
```

O segundo comando executa somente o **preflight read-only**; não instalar. Manter cobertura de regressão das novas montagens, validação de SHA, IDs, switches, eventos, PBS, permissões, arquivos ausentes, sequências especiais, recuperação e integridade Kanto/Decades. Produzir relatório por commit. **A CI aprovada não autoriza marcar uma fase jogável ou testada.**

### 4.2. QA nativo, somente quando existir cópia testável

- [ ] **Windows:** menu `Testar Johto`, spawn do quarto, mãe, Elm, cada uma das três Poké Bolas, Silver, caminhos e entradas/saídas (inclusive ida/volta), Pokémon selvagens dia/noite, batalha líder, item/insígnia e morte/derrota.
- [ ] **Normal/Master:** número de Pokémon, quatro no Master, level cap por esmeraldas totais, evoluções coerentes com nível, golpes/habilidades e sem prêmios duplicados.
- [ ] **Save/reload:** salvar antes/depois de cada evento importante, carregar e verificar party/PC/itens/conquistas, sem reproduzir luta/insígnia ou resetar flags.
- [ ] **Regiões:** sair e voltar a Johto, preservar Kanto/Decades/Hoenn, HMs locais, especiais na Box e desbloqueio de destinos de Liga.
- [ ] **JoiPlay/Android:** testar input, portas, eventos, transições, tilemaps, áudio, battles e saves sem assumir que sucesso no Windows prova Android.
- [ ] **Falhas/rollback:** interromper instalação, restaurar arquivos e saves a partir de cópias, comparar hashes e abrir Kanto/Decades sem corrupção.
- [ ] **Áudio/portal:** trilhas autorizadas, fades/loops, cenas prioritárias, listagem de treinadores/encontros/insígnias sincronizadas.

**Evidência requerida para marcar cada fase:** commit, versão/arquivo de build, SHA dos RXDATA/PBS, log/relatório de QA com ações realizadas e resultado, screenshots/gravação quando aplicável, lista de bugs conhecidos e regressão de saves. Apenas após isso mudar `gameplay_playable=true` e/ou `gameplay_tested=true`.

## 5. Condição de release final de Johto

O arquivo [`johto-release-proof.schema.json`](../data/regions/johto-release-proof.schema.json) exige os **13 checks reais**:

1. `source_rights`
2. `maps_and_warps`
3. `sprites_and_tilesets`
4. `story_events`
5. `trainers_pbs`
6. `battles_and_encounters`
7. `native_save_reload`
8. `hms_and_badges`
9. `region_travel_and_box`
10. `audio_rights_and_playback`
11. `kanto_decades_regression`
12. `windows_gameplay`
13. `joiplay_gameplay`

Eles **não devem** ser preenchidos como `true` por planejamento, testes simulados ou mera existência de arquivos. A barreira de release só passa após instalação funcional, testes realmente executados, direitos aprovados, hashes e revisão.

### Definição objetiva de “Johto concluída”

- As fases **04–16** realmente percorríveis: **13/13 jogáveis**;
- Todas com QA exigido: **13/13 testadas**;
- Núcleos técnicos com evidências: **16/16 integralmente aprovados**;
- Campanha completa (8 insígnias, Elite Four/Lance, Hall of Fame), sidequests e atividades declaradas como feitas ou explicitamente pendentes;
- Installer/atualizador com aplicação idempotente, backup, rollback e suporte aos saves;
- Nenhuma regressão Kanto/Decades, batalha original, portal, dados especiais ou circuitos regionais;
- 13 checks do esquema de release demonstrados, **não presumidos**.

## 6. Próxima tarefa recomendada (primeiro commit de execução após este MD)

**“Criar um instalador de teste isolado para o conteúdo offline 12/12, com um dry-run de hashes/colisões, backups e rollback, compilar PBS de New Bark–Violet sem tocar no jogo principal e registrar blockers. Não habilitar `Testar Johto` ou `--apply` na instalação principal antes de QA.”**

Ordem: **P0.1/P0.2 → P0.3 → P0.4/P0.5/P0.6 → P0.7/P0.8 → QA real → fase 04/16 jogável → fase 05/16 jogável → demais fases**.

## Execução do Codex — instalador isolado de QA (13/11/2026)

Implementado [johto_qa.py](../scripts/regions/johto_qa.py) para receber o ZIP do empacotador OFFLINE 12 e preparar uma cópia privada. A ferramenta confere os hashes da prévia, a compatibilidade com a base, MapIDs, eventos, referências de gráficos, duplicações PBS e conexões. Ela escreve exclusivamente em `.blue-work/game-johto-qa/` e preserva os originais substituídos no subdiretório `_johto_backup`. A instalação de produção continua bloqueada.

~~~powershell
python scripts/regions/johto_qa.py --dry-run --report .blue-work/johto-qa-preflight.json
python scripts/regions/johto_qa.py --stage-qa
python scripts/regions/johto_qa.py --rollback
~~~

Use `--game` para indicar outra base Decades em modo de leitura e `--bundle` para indicar o ZIP privado compatível. O rollback arquiva a cópia de QA inteira em `.blue-work`; uma execução nova recebe seu próprio perfil de save. Se o ZIP foi gerado sobre outra base, regenere a prévia com os MapInfos/Tilesets da base escolhida em vez de forçar a cópia. Nenhum desses comandos abre a engine.

Na primeira abertura, a cópia isolada solicita compilação nativa e registra o SHA-256 do pacote em `Data/blue-johto-qa-compiled.txt`. Se houver erro, escreve `Data/blue-johto-qa-compile-error.txt` e retém a solicitação. O menu **Testar Johto** pode abrir essa cópia compilada. A entrada na campanha normal continua condicionada ao aceite regional.

**Evidência:** o ZIP privado da etapa 12 passou na conferência de 82 mapas, 32 eventos, 44 conexões e 21 equipes. A compilação nativa passou no Windows. Uma verificação no Game.exe iniciou uma nova partida no mapa 674, coordenadas (6, 7), identificou a região como Johto e carregou os dados de Silver. Portas, batalhas completas e saves ainda aguardam o percurso de QA. Nenhuma fase completa foi aprovada.


### Documentos que devem continuar sendo a referência

- [Barra offline 12/12](JOHTO_BARRA_DESENVOLVIMENTO_OFFLINE.md)
- [Auditoria integrada 12/12](JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md)
- [Plano integral de mapas, eventos, NPCs, itens e músicas](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md)
- [Fases técnicas 01–16 e barras de gameplay](JOHTO_ETAPAS.md)
- [Teste E2E](JOHTO_TESTES_E2E.md)
- [Fase 16 — integração e aceite](JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md)
- [Plano de circuitos regionais](PLANO_REGIOES_DESSASTRE_V2.md)
- [Prova de release](../data/regions/johto-release-proof.schema.json)

**Este documento é planejamento operacional. A criação do MD não altera os 12/12, 0/16, 0/13 e 0/13 registrados e não autoriza instalação ou liberação de Johto.**


## Correções no piloto local após o teste de 14/11

A revisão do piloto usa os portões existentes do Route 29, Cherrygrove, Route 31 e Violet. As passagens entre os lados do mesmo portão mantêm a fachada e permitem o retorno. A abertura ganhou a entrega do Ovo Misterioso, o assistente de Elm, o guia de Cherrygrove, itens de campo e atendimento do Centro de Violet. Cut, Strength e Rock Smash usam a insígnia local e um Pokémon com o golpe.

Para montar com as músicas locais, informe `--audio PASTA_HGSS` ao [instalador de QA](../scripts/regions/johto_qa.py). O piloto reconhece as faixas loopadas pelo nome original da [biblioteca ENLS](https://www.enls.eu/prelooped/album/?game=HGSS). Os arquivos de áudio ficam na instalação local. As outras etapas da campanha seguem o [detonado](JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md).
