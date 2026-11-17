# Unova — Barra G: todas as tarefas possíveis pelo GitHub

**Atualizado:** 2026-11-17 · **Trilha:** desenvolvimento por chat + GitHub, sem depender de arquivos do PC.

> A barra **G** conta entregas de **código, catálogos, documentação, testes e site**, e é independente das fases técnicas A04–A14, da Barra A **0/8** e da campanha Unova **0/32**. Não instala mapas, não confirma saves nem declara Game.exe ou JoiPlay jogável.

## Barra geral

**25/32 entregas concluídas (78%)** · 7 pendentes

`[█████████████████████████░░░░░░░]` **78%**

| Frente | Concluídas | Progresso |
|---|---:|---|
| G01 — Progressão e estado da campanha | **4/4** | `████` |
| G02 — História, ginásios e pós-jogo | **4/4** | `████` |
| G03 — Treinadores e balanceamento | **4/4** | `████` |
| G04 — Áreas, selvagens e temporadas | **4/4** | `████` |
| G05 — Mecânicas e isolamento regional | **4/4** | `████` |
| G06 — Site, guias e acompanhamento | **2/4** | `██░░` |
| G07 — Blue-Story, manifests e instalador | **1/4** | `█░░░` |
| G08 — Auditoria, CI e qualidade | **2/4** | `██░░` |

## Critérios para aumentar a barra

Uma tarefa só passa a `done` após implementação (ou catálogo contratual), testes adequados e evidência de arquivo/commit no GitHub. Planejamento isolado, mapas sem fonte, níveis não verificados, licenças presumidas e testes sintéticos **não** aumentam as barras técnicas ou jogáveis.

A origem de verdade é [site/public/data/unova-github-progress.json](../site/public/data/unova-github-progress.json). O site calcula porcentagens automaticamente e disponibiliza o painel em `/unova-progresso`, acessível pelo Circuito de regiões. **Não atualize manualmente a porcentagem**: altere o status de cada tarefa junto com a evidência, e deixe o teste do site conferir.

## Lista completa por frente

### G01 — Progressão e estado da campanha

Contrato de persistência e desbloqueios de Unova sem ler saves reais.

- [x] **G01.1 — Criar esquema versionado do estado de Unova.** Flags, capítulos, missões, checkpoints e regras de compatibilidade por versão · [Evidência](../data/regions/unova-g01-state-contract.json)
- [x] **G01.2 — Implementar máquina de estados dos capítulos.** Pré-requisitos, desbloqueios e transições testáveis sem engine · [Evidência](../scripts/regions/audit_unova_g01_chapter_machine.py)
- [x] **G01.3 — Garantir recompensas únicas e reentrada segura.** Simulação de revisitas, perda de batalhas e idempotência · [Evidência](../scripts/regions/audit_unova_g01_reentry_ledger.py)
- [x] **G01.4 — Criar migrador e teste sintético de save regional.** Round-trip e regressões de migração sem tocar em save do jogador · [Evidência](../scripts/regions/audit_unova_g01_serialization.py)

### G02 — História, ginásios e pós-jogo

Contratos narrativos originais e verificáveis sem mapas nativos.

- [x] **G02.1 — Catalogar os 13 eventos iniciais de Nuvema a Accumula.** Contratos simbólicos U07 com testes negativos, sem mapas nem flags instaladas · [Evidência](../data/regions/unova-u07-nuvema-events.json)
- [x] **G02.2 — Contratar eventos da campanha e dos oito ginásios.** Dependências de história, insígnias e variações de Striaton e Opelucid · [Evidência](../scripts/regions/audit_unova_g02_gym_story.py)
- [x] **G02.3 — Modelar Elite Four, N, Ghetsis e créditos.** Batalhas em qualquer ordem na Elite, derrotas e retornos seguros, créditos únicos e desbloqueio simbólico do pós-jogo · [Evidência](../scripts/regions/audit_unova_g02_elite_finale.py)
- [x] **G02.4 — Modelar Looker, sábios, lendários e pós-jogo.** Seis sábios, quatro restrições de evento externo, encontros opcionais e sessões de revanche com Alder, todos apenas em simulação · [Evidência](../scripts/regions/audit_unova_g02_postgame.py)

### G03 — Treinadores e balanceamento

Dados e regras de batalha offline, sem presumir equipes ou níveis reais.

- [x] **G03.1 — Catalogar referências simbólicas de treinadores.** Referências-base E07 sem equipes, níveis, PBS ou sprites verificados · [Evidência](../data/regions/unova-e06-e07-preparation.json)
- [x] **G03.2 — Definir contratos dos líderes e times escalonáveis.** Level cap sem número regional fictício, evolução dinâmica com fixtures, dificuldades 70/90 e cobertura defensiva sintética · [Evidência](../scripts/regions/audit_unova_g03_leader_scaling.py)
- [x] **G03.3 — Estruturar rivais, Plasma e chefes por capítulo.** Vínculos read-only G01/G02, nove vitórias simbólicas, variantes estáveis, intenções únicas e revenches planejadas · [Evidência](../scripts/regions/audit_unova_g03_rivals_plasma.py)
- [x] **G03.4 — Modelar Elite Four, Alder e rematches.** Cinco atores, 19 variantes de dificuldade, cobertura sintética, integração com sessões G02.4 e bloqueio Full Power sem PBS verificado · [Evidência](../scripts/regions/audit_unova_g03_elite_alder.py)

### G04 — Áreas, selvagens e temporadas

Referências e encontros sem MapIDs e probabilidades inventadas.

- [x] **G04.1 — Catalogar 74 áreas simbólicas de Unova.** Catálogo U03 de áreas e estados planned, sem mapas originais ou destino validado · [Evidência](../data/regions/unova-u03-areas.json)
- [x] **G04.2 — Definir esquema de encontros por área e método.** 74 áreas U03, 20 métodos PBS, janelas do dia/estações como perguntas de auditoria; slots/pesos/níveis permanecem desconhecidos · [Evidência](../scripts/regions/audit_unova_g04_encounter_methods.py)
- [x] **G04.3 — Criar regras de evolução e níveis escalonados.** Contrato G04.2/G03.2, simulação somente com fixtures de evolução condicional e nível mínimo, 82 testes e sem PBS/MapIDs nativos · [Evidência](../scripts/regions/audit_unova_g04_wild_scaling.py)
- [x] **G04.4 — Validar encontros, taxas e lacunas de dados.** Auditoria por método/horário/estação/campanha, 88 testes sintéticos de soma, duplicações e campos desconhecidos, sem encontros reais supostos · [Evidência](../scripts/regions/audit_unova_g04_encounter_validation.py)

### G05 — Mecânicas e isolamento regional

Regras compartilhadas com Decades sem editar o jogo principal.

- [x] **G05.1 — Especificar HMs e itens-chave exclusivos por região.** Contrato auditável de Bolsa, PC de itens, atalhos e seis ações simbólicas de Unova, simulação ida/retorno e 98 testes, sem modificar Ruby/saves · [Evidência](../scripts/regions/audit_unova_g05_regional_items.py)
- [x] **G05.2 — Definir insígnias, esmeraldas e trava de especiais.** Oito insígnias locais de Unova, soma de conquistas globais, quatro categorias especiais, prévia segura de Box/party, 120 testes offline e nenhuma alteração de saves · [Evidência](../scripts/regions/audit_unova_g05_badges_specials.py)
- [x] **G05.3 — Contratar NPC de viagem e retorno entre regiões.** Contrato de NPC da cidade inicial, origem/destino instalados, retorno seguro, prévia G05.1/G05.2 e rollback sintético em cinco pontos, 127 testes offline · [Evidência](../scripts/regions/audit_unova_g05_travel.py)
- [x] **G05.4 — Testar blackout, Centro Pokémon e estado compartilhado.** Auditoria do hook Ruby, Centro local e fallback por região, 122 testes offline de persistência/rollback e dois riscos nativos registrados sem modificar o jogo · [Evidência](../scripts/regions/audit_unova_g05_blackout_state.py)

### G06 — Site, guias e acompanhamento

Conteúdo de referência exibido como planejado, nunca como jogável.

- [x] **G06.1 — Registrar Unova no circuito de regiões como planned.** Registro público da região com status planned e oito insígnias · [Evidência](../site/public/data/regions.json)
- [ ] **G06.2 — Criar guias das 74 áreas e progressão da história.** Páginas por capítulo, ginásios, áreas e pendências explícitas
- [ ] **G06.3 — Adicionar busca e filtros de NPCs, trainers e missões.** Links contextuais, pesquisa por fase e acessibilidade
- [x] **G06.4 — Publicar barra de progresso GitHub com 32 tarefas.** Página /unova-progresso alimentada por JSON e testada no CI · [Evidência](../site/public/data/unova-github-progress.json)

### G07 — Blue-Story, manifests e instalador

Preparação, dry-run e rollback, sem instalação de Unova.

- [x] **G07.1 — Auditar estaticamente alocações dos instaladores regionais.** Auditor A12 com análise AST das fontes e política fail-closed · [Evidência](../scripts/regions/audit_unova_a12_ownership.py)
- [ ] **G07.2 — Criar schema de pacote incremental de Unova.** Versão, hashes, direitos, caminhos e manifestos de origem requeridos
- [ ] **G07.3 — Simular transação de instalação e reversão.** Conflitos, backups, rollback e compare-and-swap com fixtures sintéticas
- [ ] **G07.4 — Preparar contratos Windows e Android/JoiPlay.** Atualizações incrementais compatíveis, sem alegar aprovação nativa

### G08 — Auditoria, CI e qualidade

Proteções automatizadas para código e documentação no GitHub.

- [x] **G08.1 — Disponibilizar ferramentas de proveniência e direitos.** Auditores E04–E06; nenhum asset é considerado licenciado sem prova · [Evidência](../scripts/regions/audit_unova_e06_rights_inventory.py)
- [ ] **G08.2 — Expandir suíte de testes integrados dos sistemas G01–G07.** Testes negativos, fixtures e simulações de progressão e conteúdo
- [ ] **G08.3 — Criar matriz de regressão multirregional offline.** Invariantes de Kanto, Johto, Hoenn, Sinnoh e Decades
- [x] **G08.4 — Validar o próprio tracker e barras no CI/site.** Testes de consistência de 32 tarefas e bloqueio de promoção jogável · [Evidência](../site/tests/unova-progress.test.mjs)

## Base já existente que não equivale a uma fase jogável

O repositório já registra **74 áreas simbólicas**, **73 NPCs/arquétipos**, os **13 contratos de eventos iniciais** e referências simbólicas para treinadores/música. Esses artefatos são entregas documentais auditáveis, **não** mapas instalados nem um jogo jogável. A ferramenta A12 também existe como revisão estática de instaladores; sua existência não valida futuras reservas regionais.

## Trabalhos fora desta barra — exigem insumos ou testes locais

- Obter a fonte real de mapas e sprites com permissão de uso/redistribuição e inventário de arquivos RXDATA; revisar direitos por recurso.
- Auditar alocações reais e futuras de MapIDs e referências dinâmicas em toda a instalação, não apenas snapshot.
- Rodar o `Game.exe` numa cópia QA isolada; verificar inicialização, save/reload, blackout, viagens e compatibilidade com Decades/Kanto/Johto/Hoenn/Sinnoh.
- Portar mapas/tilesets e executar QA real de NPCs, eventos, colisões, áudio e PBS.
- Validar atualizador e jogabilidade Android/JoiPlay no dispositivo real.
- Promover Unova do status `planned` **somente após evidências nativas suficientes**.

**Próxima implementação proposta:** G06.2 (guias das 74 áreas, progressão de capítulos e ginásios, status de pendências verificáveis e links de navegação, sem simular jogabilidade). Mesmo com a frente G04 concluída, slots, espécies, taxas e níveis reais de Unova continuam pendentes por falta de fontes nativas verificadas. Cada conclusão futura deve atualizar o JSON, o CI e a barra visual mantendo estas restrições.
