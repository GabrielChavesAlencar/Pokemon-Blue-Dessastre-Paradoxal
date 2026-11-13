# Johto — barra de desenvolvimento offline (sem Game.exe)

**Última atualização:** 13/11/2026. **Objetivo:** permitir avanço verificável de New Bark, Rotas 29–31 e Violet sem obrigar o proprietário a executar o jogo.

## Três barras independentes

| Indicador | Progresso | Interpretação |
|---|---:|---|
| **Desenvolvimento OFFLINE** | **12/12 (100%)** | Passos técnicos fechados com artefatos verificáveis, não jogo pronto |
| **Fases JOGÁVEIS** | **0/13 (0%)** | Depende de jogo real e caminho completo funcional |
| **Fases TESTADAS NO EXE** | **0/13 (0%)** | Depende de QA de gameplay real aprovado |

**Progress bar OFFLINE:** `[############] 12/12 = 100%`

## Checklist das 12 etapas

| ID | Estado | Entrega offline | Critério objetivo |
|---:|---|---|---|
| 01 | **CONCLUÍDO** | Auditoria da base Blue/Decades e da fonte Johto | ZIP privado validado por hash; 207 mapas nativos, 95 PBS e 74 mapas da fonte inventariados; sprites essenciais identificados |
| 02 | **CONCLUÍDO** | Prévia isolada de mapas e tilesets | 74 mapas Johto em IDs 600–673, três interiores geométricos provisórios em 674–676, 42 conexões PBS remapeadas; integridade dos dados originais comparada |
| 03 | **CONCLUÍDO** | Descoberta offline das conexões faltantes | Candidatas Route29 ↔ Cherrygrove e Route31 ↔ Violet derivadas de bordas e passagem estática; sem gravar na campanha; verificadores/testes versionados |
| 04 | **CONCLUÍDO** | Construir quarto definitivo do jogador (New Bark 2F) | RXDATA próprio de quarto 2F em prévia privada, visualização, tileset adequado, cama, escada, piso e proposta de spawn; verificação estática |
| 05 | **CONCLUÍDO** | Construir casa definitiva do jogador (New Bark 1F) | RXDATA próprio de casa 1F, escada 2F, porta exterior, espaço da mãe, propostas de chegada e prévia de passabilidade |
| 06 | **CONCLUÍDO** | Construir laboratório definitivo de Elm | RXDATA de laboratório próprio, mesa com três Poké Bolas físicas, lugar de Elm, porta, caminhos internos e verificação estática |
| 07 | **CONCLUÍDO** | Ligar portas, escadas e spawn entre mapas | 12 pontos/eventos com MapIDs e coordenadas derivados dos layouts, transições reversíveis e checagens de limites/ocupação; aprovação de colisão real permanece separada |
| 08 | **CONCLUÍDO** | Inserir eventos de história de New Bark nos mapas | Eventos próprios para mãe, Elm, três Poké Bolas e rival ligados em RXDATA de cópia isolada; flags únicas, handlers auditados e testes sintéticos sem duplicar iniciais |
| 09 | **CONCLUÍDO** | Preparar PBS do rival e três iniciais | Três equipes rival condicionadas ao inicial escolhido, validação offline de species/trainer types e scripts, sem criar marcador falso de PBS compilado |
| 10 | **CONCLUÍDO** | Preparar encontros e treinadores das Rotas 29–31 | Tabelas de encontros e times na cópia isolada, níveis ajustados às regras Blue, nomes/referências conferidos com PBS, testes de consistência |
| 11 | **CONCLUÍDO** | Preparar Violet City, Sprout Tower e Falkner | Integração offline de mapa/entradas/interiores propostos, eventos de Falkner e Torre Sprout, contratos PBS e insígnia Zephyr sem recompensa duplicada |
| 12 | **CONCLUÍDO** | Auditoria e empacotamento offline da fase inicial | Todas as saídas da prévia verificadas, suíte offline passando, SHA/IDs e proteção de Kanto/Decades/saves confirmados; relatório pronto para futura QA nativa sem alegar jogo funcional |

## Ordem e evidência

As etapas 04/12 (quarto 2F) e 05/12 (casa 1F) foram concluídas em previews privadas. **06/12 — laboratório de Elm concluído; 07/12 — portas/escadas/spawn concluída; 08/12 — eventos de New Bark concluída; 09/12 — PBS rival/iniciais concluída; 10/12 — encontros e treinadores Rotas 29–31 concluída; 11/12 — Violet, Torre Sprout e Falkner concluída; 12/12 — auditoria e empacotamento concluída; próximo ciclo: compilação/instalação de teste/QA da engine**. Depois portas/spawn (07), eventos (08) e PBS (09). O bloco seguinte prepara Rotas 29–31 (10) e Violet (11). Por último, a auditoria/empacotamento offline fecha o **12/12**.

- 01: `docs/JOHTO_FASE_04_AUDITORIA_BASE_NATIVA_20261113.md`, `docs/JOHTO_FASE_04_ENTRADAS_REAIS_V1.md`
- 02: `docs/JOHTO_FASE_04_STAGE_REAL_PRIVADO_77_MAPAS.md`
- 03: `docs/JOHTO_FASE05_CONEXOES_OFFLINE_ATE_VIOLET.md`, `scripts/regions/johto_route29_cherrygrove.py`, `scripts/regions/johto_route31_violet.py`

## Como uma etapa muda de estado

1. **PENDENTE → EM_ANDAMENTO:** início da implementação real e arquivos localizados, sem aumentar o numerador.
2. **EM_ANDAMENTO → CONCLUÍDO:** arquivo/código/regra gerado, validador de geometria/contratos e testes offline concluídos, evidência registrada na própria etapa. Aumentar em **1** o numerador.
3. **BLOQUEADO:** descrever dependência concreta e não avançar contagem.
4. **CONCLUÍDO** não significa testado em Windows ou integrado ao jogo principal. As barras de jogabilidade **jamais** avançam por passar testes Python/Ruby.

## Condições de segurança e limitações

- **Sem executar Game.exe:** nenhuma das 12 etapas requer janela do jogo, mas os itens que dependem de gameplay devem continuar sinalizados como pendentes na barra de QA.
- Todos os RXDATA/PNG/PBS de terceiros permanecem em arquivo **privado** ou sob `.blue-work/`, não no GitHub público. O repositório recebe somente código próprio, contratos, hashes e documentação. Direitos de redistribuição não foram aprovados pela auditoria.
- `game/` principal, Kanto, Decades, savefiles e scripts que já funcionam não devem ser sobrescritos; a montagem fica em cópia isolada.
- As duas conexões adicionais da etapa 03 são **propostas de passagem estática**, **não** inserções/testes nativos validados. A etapa 07 deve integrá-las somente na prévia isolada de Johto.
- Não marcar posições, colisões ou transições `verified_in_engine=true` antes da execução real. É possível completar os 12 passos offline, mantendo **jogáveis 0/13** e **testados 0/13**.
- O PR #36 ainda não foi integrado à `main`; conferir estado da CI antes do merge. Falha/timeout de Kanto não deve ser contornada para aumentar progresso.

**Atenção ao instalador:** os geradores existem na main, mas o `Blue-Story.exe` ainda não gera/instala os mapas de Johto automaticamente. A integração do instalador é pré-requisito do ciclo antes de habilitar a região. Nenhuma permissão de distribuir RXDATA/PNG de terceiros foi presumida.

**Fonte dos números:** `data/regions/johto-progress.json` → `offline_development` e `progress.offline_development_milestones`. Atualizar sempre o estado das etapas e o contador juntos.

### Etapa 04/12 concluída (13/11/2026)

O script `scripts/regions/build_johto_bedroom_v1.py` constrói quarto próprio de 14×11 tiles em prévia isolada Map674, com cinco peças principais, spawn (6,7) e aproximação da escada (9,8) **apenas propostos**. O RXDATA privado real foi reaberto em Ruby Marshal e não alterou os outros 76 mapas; 5 testes offline passaram. [Detalhes](JOHTO_OFFLINE_FASE_04_QUARTO_2F.md). **Offline 4/12 (33,3%) · Jogáveis 0/13 · Testadas no EXE 0/13.**

### Etapa 05/12 concluída — casa New Bark 1F

`build_johto_home1f_v1.py`: gerou Map675 privado original 16×13 via tileset Inside, com cozinha, mesa, sofá, escada visual e porta; cinco pontos de entrada/saída/mãe propostos e conectados por 106 tiles estáticos. Ruby Marshal reabriu o RXDATA, outros 76 MapNNN + MapInfos/Tilesets intactos, 6 testes offline passaram. [Relatório técnico](JOHTO_OFFLINE_FASE_05_CASA_1F.md). **Barra offline 5/12 (41,7%) · Jogáveis 0/13 · EXE testados 0/13.**

### Etapa 06/12 concluída — Laboratório de Elm

Gerado **Map676 (20×16)** em prévia isolada com três Poké Bolas físicas em tiles individuais 5328/5329/5330, cada uma de Chikorita, Cyndaquil e Totodile. Computador, estante e equipamento de laboratório; Elm e porta possuem posições propostas. Um novo tileset privado (ID 32) adiciona os gráficos das bolas extraídos do sprite nativo `Object_Ball.png`. O mapa foi reaberto com Ruby Marshal; **76 mapas restantes, 207 MapInfos e as 32 definições de tileset anteriores preservados**. Caminho estático com **198 tiles**, **7 testes Python aprovados**. As Poké Bolas **ainda não possuem evento de interação**; substituir os tiles por eventos individuais na etapa 08. A instalação automática no `Blue-Story.exe` segue pendente. [Relatório detalhado](JOHTO_OFFLINE_FASE_06_LABORATORIO_ELM.md). **Offline 6/12 (50%) · Jogáveis 0/13 · Testadas no EXE 0/13.**

### Etapa 07/12 concluída — seis warps em quatro mapas de New Bark

A rotina `scripts/regions/build_johto_warps_v1.py` compila eventos **RMXP código 201** em cópia **nova** da prévia privada de 77 mapas. Ida/volta: quarto↔casa, casa↔cidade, cidade↔laboratório. Destinos não coincidem com gatilhos de retorno; spawn proposto no quarto (6,7). A rota New Bark↔Route29 continua no PBS de conexão, sem teleport duplicado. Todos os 13 pontos de origem/chegada/spawn têm passabilidade de flags estáticas e são alcançáveis por caminho local. Prova privada Ruby Marshal: 6 eventos, **somente Map600, Map674, Map675, Map676 alterados; 73 mapas, MapInfos e Tilesets inalterados**. [Relatório](JOHTO_OFFLINE_FASE_07_PORTAS_ESCADAS_SPAWN.md) e **12 testes sintéticos**. A próxima fase 08 deverá anexar os NPCs/3 Poké Bolas interativas sem apagar os warps. **Offline 7/12 (58,3%); Jogáveis 0/13; Testados no EXE 0/13.**

### Etapa 08/12 concluída — mãe, Elm, três Poké Bolas e Silver

Gerador `scripts/regions/build_johto_story_v1.py` acrescenta **6 eventos** no estágio privado de 77 mapas, mantendo os **6 warps** anteriores. A escolha do inicial passou a ocorrer **diretamente em cada bola** (handler `BlueJohtoPilot.choose_starter_from_ball(:SPECIES)`), sem menu do Elm, idempotente por estado de save; as três bolas originais da camada de tiles foram removidas para não duplicar gráficos. Silver ocupa posição candidata na Route29 e sua batalha depende dos PBS da etapa 09. Os RXDATA reais foram serializados/reabertos com Ruby Marshal: alterados somente Map625/675/676, 74 restantes e MapInfos/Tilesets intactos. [Relatório 08/12](JOHTO_OFFLINE_FASE_08_EVENTOS_NEW_BARK.md); dez testes Python novos e harness Ruby adaptado. **OFFLINE 8/12 (66,7%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa 09/12 — PBS nativo e 3 versões de Silver

`build_johto_rival_pbs_v2.py` gerou em pasta privada dois PBS de Johto: tipo `BLUE_JOHTO_RIVAL` baseado no RIVAL1 instalado, e três equipes nível 5 com golpes conferidos no `pokemon.txt` e `moves*.txt` nativos. Versões 0/1/2: Chikorita jogador→Cyndaquil Leer/Tackle, Cyndaquil→Totodile Leer/Scratch, Totodile→Chikorita Growl/Tackle. Hashes vinculados aos três mapas de eventos da etapa 08. São **dados PBS preparados, não compilados no Essentials**; o marcador `blue-johto-rival-ready.txt` permanece ausente, o level cap dinâmico ainda não foi testado e o instalador Blue-Story.exe não monta Johto automaticamente. 10 testes sintéticos Python + 1 teste Ruby das três variantes passaram localmente. [Relatório](JOHTO_OFFLINE_FASE_09_PBS_RIVAL_SILVER.md). **OFFLINE 9/12 (75%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa 10/12 — Rotas 29–31: encontros e treinadores preparados

Contrato `data/regions/johto-stage10-routes.json`, gerador `build_johto_routes_stage10.py` e módulo `JohtoRouteTrainers.rb` preparam **6 tabelas Land/LandNight** (100% por horário), **5 treinadores** e **10 times PBS** (2 Pokémon no normal, 4 no Master). O pacote de mapas **não tem PBS canônicos**, portanto tabelas e times são propostas do Blue (espécies e golpes verificados na base real). Os eventos estão em cópia privada: Map625/626/627 alterados com Ruby Marshal, os outros **74** e os metadados nativos inalterados. Os pontos de 5 NPCs estão na mesma componente caminhável por rota, e Silver foi preservado. A lógica não cria níveis paralelos: remete ao balanceamento Blue global 70/90, selvagens 45; comportamento da engine ainda pendente. **Nenhuma batalha é habilitada sem marcador pós-QA**, e o Blue-Story.exe ainda não monta Johto. [Relatório](JOHTO_OFFLINE_FASE_10_ROTAS_29_31.md). **OFFLINE 10/12 (83,3%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa 11/12 — Violet City, Torre Sprout e Falkner

Em `.blue-work`, acrescentados **cinco interiores provisórios**: ginásio Map677, Torre Sprout andares 1F/2F/3F Maps678-680 e Centro Map681; a cidade original Map602 recebe **três entradas**, ligadas por **10 eventos de transferência reversíveis**. Cinco NPCs de história, incluindo Falkner e Ancião Li; **8 equipes PBS** (normal2/Master4) de Falkner/Li/Sages Nico e Troy. Zephyr é concedida **uma única vez por BlueRegions.award após batalha vencida**, e Li nunca concede a insígnia. RXDATA privado real: **76 mapas anteriores preservados**, cinco novos MapInfos, tilesets existentes intocados, 82 mapas no total. **Limites:** sprites específicos de Falkner, Li, Sages e atendente não encontrados na fonte; interiores não são oficiais HGSS; Centro não cura; PBS ainda não compilados na engine e Blue-Story.exe não instala Johto automaticamente. [Relatório detalhado](JOHTO_OFFLINE_FASE_11_VIOLET_SPROUT_FALKNER.md). **OFFLINE 11/12 (91,7%) · JOGÁVEIS 0/13 · TESTADAS 0/13.**

### Etapa 12/12 — Auditoria de integração privada completa (não é gameplay)

O auditor e empacotador `scripts/regions/package_johto_offline12.py` valida **82 RXDATA** com **16 warps e 16 eventos autorais**, **21 equipes PBS** (Silver3+Rotas10+Violet8), **6 tabelas dia/noite**, **44 conexões** (42 originais + duas inferidas), **5 tilesets e 14 autotiles realmente usados** e sprites dos NPCs. A exportação nativa completa mostrou que Falkner/Sage já existiam e permitiu corrigir as referências Li→`NPC_HGSS_Elder` e enfermeira→`NPC_DPP_PokeCenter_Nurse` em uma cópia dos mapas 680/681; **80/82 mapas permaneceram idênticos**, MapInfos/Tilesets preservados. ZIP privado auditado por CRC, SHA256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49`; **nenhuma alteração do game/ original**. [Relatório](JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md). 

**Importante:** 12/12 é **somente preparação offline**; a opção de instalar Johto via `Blue-Story.exe` **não foi habilitada**, porque ainda faltam montagem transacional, PBS compilados, direitos de distribuição, gráficos de batalha, cura no Centro e QA Windows/JoiPlay. **JOGÁVEIS 0/13; TESTADAS NO EXE 0/13.**
