# Unova — Barra G: todas as tarefas possíveis pelo GitHub

**Atualizado:** 2026-11-17 · **Trilha:** desenvolvimento por chat + GitHub, sem depender de arquivos do PC.

> A barra **G** conta entregas de **código, catálogos, documentação, testes e site**, e é independente das fases técnicas A04–A14, da Barra A **0/8** e da campanha Unova **0/32**. Não instala mapas, não confirma saves nem declara Game.exe ou JoiPlay jogável.

## Barra geral

**8/32 entregas concluídas (25%)** · 24 pendentes

`[████████░░░░░░░░░░░░░░░░░░░░░░░░]` **25%**

| Frente | Concluídas | Progresso |
|---|---:|---|
| G01 — Progressão e estado da campanha | **0/4** | `░░░░` |
| G02 — História, ginásios e pós-jogo | **1/4** | `█░░░` |
| G03 — Treinadores e balanceamento | **1/4** | `█░░░` |
| G04 — Áreas, selvagens e temporadas | **1/4** | `█░░░` |
| G05 — Mecânicas e isolamento regional | **0/4** | `░░░░` |
| G06 — Site, guias e acompanhamento | **2/4** | `██░░` |
| G07 — Blue-Story, manifests e instalador | **1/4** | `█░░░` |
| G08 — Auditoria, CI e qualidade | **2/4** | `██░░` |

## Critérios para aumentar a barra

Uma tarefa só passa a `done` após implementação (ou catálogo contratual), testes adequados e evidência de arquivo/commit no GitHub. Planejamento isolado, mapas sem fonte, níveis não verificados, licenças presumidas e testes sintéticos **não** aumentam as barras técnicas ou jogáveis.

A origem de verdade é [site/public/data/unova-github-progress.json](../site/public/data/unova-github-progress.json). O site calcula porcentagens automaticamente e disponibiliza o painel em `/unova-progresso`, acessível pelo Circuito de regiões. **Não atualize manualmente a porcentagem**: altere o status de cada tarefa junto com a evidência, e deixe o teste do site conferir.

## Lista completa por frente

### G01 — Progressão e estado da campanha

Contrato de persistência e desbloqueios de Unova sem ler saves reais.

- [ ] **G01.1 — Criar esquema versionado do estado de Unova.** Flags, capítulos, missões, checkpoints e regras de compatibilidade por versão
- [ ] **G01.2 — Implementar máquina de estados dos capítulos.** Pré-requisitos, desbloqueios e transições testáveis sem engine
- [ ] **G01.3 — Garantir recompensas únicas e reentrada segura.** Simulação de revisitas, perda de batalhas e idempotência
- [ ] **G01.4 — Criar migrador e teste sintético de save regional.** Round-trip e regressões de migração sem tocar em save do jogador

### G02 — História, ginásios e pós-jogo

Contratos narrativos originais e verificáveis sem mapas nativos.

- [x] **G02.1 — Catalogar os 13 eventos iniciais de Nuvema a Accumula.** Contratos simbólicos U07 com testes negativos, sem mapas nem flags instaladas · [Evidência](../data/regions/unova-u07-nuvema-events.json)
- [ ] **G02.2 — Contratar eventos da campanha e dos oito ginásios.** Dependências de história, insígnias e variações de Striaton e Opelucid
- [ ] **G02.3 — Modelar Elite Four, N, Ghetsis e créditos.** Batalhas, derrotas, retornos e clímax White com recompensas únicas
- [ ] **G02.4 — Modelar Looker, sábios, lendários e pós-jogo.** Missões paralelas, fases opcionais e bloqueios de conteúdo especiais

### G03 — Treinadores e balanceamento

Dados e regras de batalha offline, sem presumir equipes ou níveis reais.

- [x] **G03.1 — Catalogar referências simbólicas de treinadores.** Referências-base E07 sem equipes, níveis, PBS ou sprites verificados · [Evidência](../data/regions/unova-e06-e07-preparation.json)
- [ ] **G03.2 — Definir contratos dos líderes e times escalonáveis.** Level cap, evolução dinâmica e variantes de dificuldade
- [ ] **G03.3 — Estruturar rivais, Plasma e chefes por capítulo.** Estado de revanche, eventos e recompensas com identificadores estáveis
- [ ] **G03.4 — Modelar Elite Four, Alder e rematches.** Tabelas e testes para a campanha e o pós-jogo sem fingir PBS compilado

### G04 — Áreas, selvagens e temporadas

Referências e encontros sem MapIDs e probabilidades inventadas.

- [x] **G04.1 — Catalogar 74 áreas simbólicas de Unova.** Catálogo U03 de áreas e estados planned, sem mapas originais ou destino validado · [Evidência](../data/regions/unova-u03-areas.json)
- [ ] **G04.2 — Definir esquema de encontros por área e método.** Grama, água, pesca, cavernas, horário, variante e temporada
- [ ] **G04.3 — Criar regras de evolução e níveis escalonados.** Evoluções, nível mínimo, balanceamento e limites por progressão
- [ ] **G04.4 — Validar encontros, taxas e lacunas de dados.** Soma de probabilidades, duplicações e campos desconhecidos preservados

### G05 — Mecânicas e isolamento regional

Regras compartilhadas com Decades sem editar o jogo principal.

- [ ] **G05.1 — Especificar HMs e itens-chave exclusivos por região.** Inventário, PC de itens e disponibilidade ao viajar
- [ ] **G05.2 — Definir insígnias, esmeraldas e trava de especiais.** Insígnias únicas e restrições regionais de Pokémon especiais
- [ ] **G05.3 — Contratar NPC de viagem e retorno entre regiões.** Viagens por NPC com pré-condições e fallback seguro
- [ ] **G05.4 — Testar blackout, Centro Pokémon e estado compartilhado.** Moedas, boxes, TMs, progresso e fallback de Centro da região atual

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

**Próxima implementação proposta:** G01.1 (esquema versionado do estado regional) seguida de G01.2–G01.4. Cada conclusão futura deve atualizar o JSON, o CI e a barra visual mantendo estas restrições.
