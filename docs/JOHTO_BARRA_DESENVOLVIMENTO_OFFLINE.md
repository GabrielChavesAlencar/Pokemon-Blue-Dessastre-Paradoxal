# Johto — barra de desenvolvimento offline (sem Game.exe)

**Última atualização:** 13/11/2026. **Objetivo:** permitir avanço verificável de New Bark, Rotas 29–31 e Violet sem obrigar o proprietário a executar o jogo.

## Três barras independentes

| Indicador | Progresso | Interpretação |
|---|---:|---|
| **Desenvolvimento OFFLINE** | **5/12 (41,7%)** | Passos técnicos fechados com artefatos verificáveis, não jogo pronto |
| **Fases JOGÁVEIS** | **0/13 (0%)** | Depende de jogo real e caminho completo funcional |
| **Fases TESTADAS NO EXE** | **0/13 (0%)** | Depende de QA de gameplay real aprovado |

**Progress bar OFFLINE:** `[#####-------] 5/12 = 41,7%`

## Checklist das 12 etapas

| ID | Estado | Entrega offline | Critério objetivo |
|---:|---|---|---|
| 01 | **CONCLUÍDO** | Auditoria da base Blue/Decades e da fonte Johto | ZIP privado validado por hash; 207 mapas nativos, 95 PBS e 74 mapas da fonte inventariados; sprites essenciais identificados |
| 02 | **CONCLUÍDO** | Prévia isolada de mapas e tilesets | 74 mapas Johto em IDs 600–673, três interiores geométricos provisórios em 674–676, 42 conexões PBS remapeadas; integridade dos dados originais comparada |
| 03 | **CONCLUÍDO** | Descoberta offline das conexões faltantes | Candidatas Route29 ↔ Cherrygrove e Route31 ↔ Violet derivadas de bordas e passagem estática; sem gravar na campanha; verificadores/testes versionados |
| 04 | **CONCLUÍDO** | Construir quarto definitivo do jogador (New Bark 2F) | RXDATA próprio de quarto 2F em prévia privada, visualização, tileset adequado, cama, escada, piso e proposta de spawn; verificação estática |
| 05 | **CONCLUÍDO** | Construir casa definitiva do jogador (New Bark 1F) | RXDATA próprio de casa 1F, escada 2F, porta exterior, espaço da mãe, propostas de chegada e prévia de passabilidade |
| 06 | PENDENTE | Construir laboratório definitivo de Elm | RXDATA de laboratório próprio, mesa com três Poké Bolas físicas, lugar de Elm, porta, caminhos internos e verificação estática |
| 07 | PENDENTE | Ligar portas, escadas e spawn entre mapas | 12 pontos/eventos com MapIDs e coordenadas derivados dos layouts, transições reversíveis e checagens de limites/ocupação; aprovação de colisão real permanece separada |
| 08 | PENDENTE | Inserir eventos de história de New Bark nos mapas | Eventos próprios para mãe, Elm, três Poké Bolas e rival ligados em RXDATA de cópia isolada; flags únicas, handlers auditados e testes sintéticos sem duplicar iniciais |
| 09 | PENDENTE | Preparar PBS do rival e três iniciais | Três equipes rival condicionadas ao inicial escolhido, validação offline de species/trainer types e scripts, sem criar marcador falso de PBS compilado |
| 10 | PENDENTE | Preparar encontros e treinadores das Rotas 29–31 | Tabelas de encontros e times na cópia isolada, níveis ajustados às regras Blue, nomes/referências conferidos com PBS, testes de consistência |
| 11 | PENDENTE | Preparar Violet City, Sprout Tower e Falkner | Integração offline de mapa/entradas/interiores propostos, eventos de Falkner e Torre Sprout, contratos PBS e insígnia Zephyr sem recompensa duplicada |
| 12 | PENDENTE | Auditoria e empacotamento offline da fase inicial | Todas as saídas da prévia verificadas, suíte offline passando, SHA/IDs e proteção de Kanto/Decades/saves confirmados; relatório pronto para futura QA nativa sem alegar jogo funcional |

## Ordem e evidência

As etapas 04/12 (quarto 2F) e 05/12 (casa 1F) foram concluídas em previews privadas. **Próxima: 06/12 — laboratório de Elm**. Depois portas/spawn (07), eventos (08) e PBS (09). O bloco seguinte prepara Rotas 29–31 (10) e Violet (11). Por último, a auditoria/empacotamento offline fecha o **12/12**.

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
