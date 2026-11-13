# Sinnoh — plano definitivo passo a passo para criar a região no Blue Dessastre Paradoxal

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data:** 13/11/2026  
**Base de referência:** Pokémon Platinum; Diamond/Pearl para variações que agreguem conteúdo; BDSP como complemento de análise.  
**Fangame a auditar primeiro:** Pokémon Ancient Platinum (Essentials v21.1). **Não** se presume fonte aberta, mapas reutilizáveis ou permissão de redistribuição.  
**Tipo:** roteiro de execução incremental com entregáveis, testes, gates e rollback. **Este MD é planejamento; não representa Sinnoh jogável nem mapas já importados.**

## 0. Fontes obrigatórias e estado verdadeiro

Antes de cada fase, ler:

1. [SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) — ranking, limitações das fontes, trilha, mapeamento de alto nível, regras e as duas barras de Sinnoh.
2. [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md) — circuito regional, badges/esmeraldas, restrição de Pokémon especiais, HMs e pós-jogo global.
3. [ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md) — lista original e ressalvas das fontes.
4. [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) e [HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) — padronização de auditoria, portais, importação em fases, prova nativa e não regressão.
5. [CIRCUITO_REGIONAL.md](CIRCUITO_REGIONAL.md), [EDITOR_MUSICAS.md](EDITOR_MUSICAS.md) e [KANTO_PLANO_APLICAR_MUSICAS.md](KANTO_PLANO_APLICAR_MUSICAS.md) — integrações e fallback musical.
6. [README.md](../README.md) e [AGENTS.md](../AGENTS.md) — estrutura do Blue/Decades e forma segura de publicar.

**Situação verificada na publicação deste plano:**

- O GitHub **não inclui** a instalação-base do Decades em `game/`; é uma cópia local protegida. Nada neste MD comprova que os mapas e áudios de Sinnoh já foram obtidos.
- O menu do jogo principal passa a oferecer **`Testar Sinnoh` na quinta posição lógica**, após `Testar Kanto` e `Testar Johto`, por meio de [`scripts/battle_polish/TitleKanto.rb`](../scripts/battle_polish/TitleKanto.rb).
- A opção **só pode lançar** `SINNOH_JOGAR_EXPERIMENTAL.bat` **E** `scripts/regions/pilot_sinnoh.py` próprios. **Esses dois arquivos ainda não foram criados**. Até sua implementação e instalação no projeto local, a opção informa que Sinnoh está em preparação e volta ao título.
- A existência do botão **não** altera a região inicial da campanha, **não** cria mapas e **não** comprova jogabilidade.
- A pasta `The Pokémon World Project - Sinnoh/Data`, conferida em 13/11/2026, tinha só `Map001.rxdata` e `Map002.rxdata`, sem uma Sinnoh completa. **Não usar Hoenn como fonte substituta**, não inventar mapas nem confundir a existência de um diretório com mapa real.

**Divisão de responsabilidade em vigor:** [SINNOH_CODEX_PENDENCIAS.md](SINNOH_CODEX_PENDENCIAS.md) registra todas as tarefas que dependem da instalação local, dos mapas de origem e de testes gráficos. [SINNOH_FASE_00_AUDITORIA_REPOSITORIO.md](SINNOH_FASE_00_AUDITORIA_REPOSITORIO.md) registra o que já foi conferido pelo GitHub. A ferramenta de preparação apenas de leitura está em [scripts/regions/audit_sinnoh_source.py](../scripts/regions/audit_sinnoh_source.py), com testes em [tests/test_sinnoh_source_preflight.py](../tests/test_sinnoh_source_preflight.py). A CI executa o preflight para detectar regressões de contrato. Nenhum desses artefatos substitui um piloto com mapas reais.

## 1. Regra máxima: implementar SEM quebrar tudo que já existe

**Toda alteração deve ser aditiva, isolada, reversível e testada antes de mudar o jogo principal.** Proteger obrigatoriamente **Decades, Kanto, Johto, Hoenn em preparação, Blue Studio, Pokédex, Habitat Dex, álbum, site, BlueMusic, balanceamento, multiplayer, saves e lançadores Windows/Android**.

### 1.1. Salvaguardas inegociáveis

1. **Baseline a cada fase:** registrar SHA da `main`, árvore limpa, lista de MapIDs/tilesets, versões de plugins, snapshots de configurações e hashes antes de trabalhar; executar regressão anterior e guardar logs.
2. **Cópias distintas:** os arquivos da fonte devem ficar, por exemplo, em `.blue-work/sinnoh-source/`; conversão e piloto, em `.blue-work/sinnoh-pilot/`, **fora de `game/` e dos perfis reais de saves**. Caminhos são convenção planejada; criar somente nas fases apropriadas.
3. **Não substituir bancos originais:** é proibido jogar a pasta `Data/` de outro fangame sobre `game/Data/`. Não copiar `Scripts.rxdata`, `PluginScripts.rxdata`, `System.rxdata`, `MapInfos.rxdata` ou `Tilesets.rxdata` em bloco. Ler, identificar dependências e reconstruir/adaptar **somente o necessário**.
4. **IDs congelados:** nunca atribuir a Sinnoh IDs ocupados ou reservados por Decades/Kanto/Johto/Hoenn. Johto já usou/reservou parte da faixa 600–999 em seus estudos; **não presumir que IDs de quatro dígitos funcionam** sem testar RMXP, serializadores, editores, runtime, importadores e saves. Manter `origem -> destino` por recurso, com chaves simbólicas.
5. **Sem reescrever serviços compartilhados:** ampliar os adaptadores existentes (`Regions.rb`, `RegionStart.rb`, `RegionTravel.rb`, `RegionalPolicy.rb`, `RegionalCards.rb` e `BlueMusic.rb`) sem trocar contratos e sem recalcular progressão existente. Alterar apenas quando a API foi auditada na versão local.
6. **Feature flag:** Sinnoh deve permanecer `planned` até haver piloto real e testado; `experimental` somente na cópia isolada; `playable` apenas depois dos gates da fase final. O registro da região não ativa portais para mapas inexistentes.
7. **Instalação transacional:** padrão `--dry-run` (sem alterar arquivos); depois `--apply` somente se permissões, integridade, compatibilidade, backups e plano de rollback estiverem aprovados. Falha parcial restaura tudo, inclusive configurações de áudio e saves se envolvidos.
8. **Nenhum nível fixo novo:** níveis, evoluções, IA, BST/estágio, treinadores e selvagens seguem o **mesmo sistema dinâmico de Decades/Blue**. Os níveis canônicos servem de referência, jamais outro escalonador. No site, mostrar fase/condição do time, não número rígido.
9. **Direitos e proveniência:** download jogável não é fonte editável, e repositório público não equivale a licença. Creditar e obter autorização por mapa, arte, música e scripts conforme uso pretendido; código/arte/áudio sem permissão não devem ir à `main`.
10. **Dois tipos de prova:** CI/headless testa contratos, importação, dados e não regressão; **Game.exe Windows** e **JoiPlay/Android** comprovam caminhada, eventos, encontros, saves, controles, áudio, performance e ausência de softlocks. Nunca marcar aceita uma fase só porque o script Python passou.

### 1.2. Gate antes de qualquer commit de Sinnoh

- [ ] Lista de arquivos alterados inclui somente o escopo desta fase.
- [ ] Nenhum MapID anterior, tileset, evento, switch ou variável foi reutilizado por acidente.
- [ ] Dados da campanha, saves e regiões existentes carregam sem regressão.
- [ ] Instalação/rollback e os testes de menu não falharam.
- [ ] Evidência de licença e auditoria acompanha cada asset importado.
- [ ] Status do piloto e das barras condiz com testes de fato realizados.

## 2. Menu principal: Testar Sinnoh **junto** de Testar Kanto/Johto

### 2.1. Resultado esperado no mesmo Game.exe

A opção deve aparecer no **menu principal da cópia normal do jogo**, sem criar um executável-base diferente nem substituir o controlador original de saves:

```text
Continuar                 (quando existir save)
Novo Jogo
Testar Kanto
Testar Johto
Testar Sinnoh
Mystery Gift / Opções / Sair / demais opções que existirem
```

**Já implementado no código do repositório:** `scripts/battle_polish/TitleKanto.rb` adiciona o comando simbólico `:blue_test_sinnoh` à **quinta posição após Continue** (ou à quarta sem Continue), mantendo índices **originais** retornados para o `PokemonLoad_Scene` do Essentials/Auto Multi Save. A implementação usa `Scene#pbStartScene` e `Scene#pbChoose`, preserva setas negativas dos slots e ignora os comandos de teste dentro dos pilotos.

**O que AINDA falta para `Testar Sinnoh` abrir mapas reais:**

1. Criar `SINNOH_JOGAR_EXPERIMENTAL.bat` e `scripts/regions/pilot_sinnoh.py` próprios **somente quando houver mapas de origem reais auditados e autorizados**.
2. O Python deve preparar uma **instalação isolada**, criar o marcador exato `Sinnoh pilot.json` e configurar **saves exclusivos de piloto**, sem escrever no `game/` principal.
3. Na ausência do BAT **ou** do Python, mostrar **"Sinnoh ainda está em preparação"**, sem usar Kanto/Johto/Hoenn como fallback e **sem fechar o jogo principal**.
4. Se ambos existirem, oferecer confirmação explícita; no Windows, abrir o launcher auditado da raiz do projeto usando `Process.spawn` e permitir que o controlador original feche/limpe o menu. Fora do Windows, mostrar aviso de plataforma.
5. O próprio `Game.exe` do piloto não pode apresentar nenhuma opção de criar outro piloto (evitar recursão). Não trocar `New Game`, `Continue`, `Mystery Gift`, `Quit Game`, perfis ou índices.
6. Manter nomes distintos de arquivos/`run.bat` e da fase de Hoenn, que terá seu próprio plano; Sinnoh jamais se passará por outra região.

**Testes de contrato já ampliados na main:**

```powershell
python -m unittest discover -s tests -p "test_title_kanto.py" -v
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
```

O teste Ruby usa um controlador **simulado**, não executa `Game.exe` nem valida o piloto real. A prova manual é obrigatória na fase do piloto.

### 2.2. Checklist manual do menu quando instalado no Windows

1. Sem saves: verificar ordem `Novo Jogo → Testar Kanto → Testar Johto → Testar Sinnoh` e confirmar que `Novo Jogo` inicia a campanha normal.
2. Com saves/multislots: Continue permanece primeiro; navegação dos slots com setas fica intacta.
3. Selecionar Sinnoh **antes de criar piloto**: aviso de preparação, permanecer no menu, nenhum save/arquivo alterado.
4. Selecionar Kanto e Johto: cada opção abre seu piloto preexistente ou exibe **seu próprio aviso**, nunca a região errada.
5. Com piloto Sinnoh preparado: confirmar, abrir só a cópia isolada, verificar marcador, mapa real de Twinleaf, retorno/fechamento e saves distintos.
6. Rodar `Game.exe` dentro de cada piloto e confirmar que **nenhuma opção Testar ...** aparece, sem recursão.
7. No Android/JoiPlay, o menu não deve depender de `cmd.exe` nem executar BAT, e a campanha principal deve continuar utilizável. Piloto Android é tarefa de pacote separado e só pode ser divulgado como funcional após teste real.

## 3. Arquitetura incremental e organização sugerida

> **Caminhos planejados nesta seção não são afirmação de que os arquivos já existam.** Criar nas fases apropriadas. Nunca colocar dados de terceiros não licenciados no Git.

```text
docs/
  SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md     # análise de fontes
  SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md  # este plano
  SINNOH_FASE_00_AUDITORIA.md                  # futuro
  SINNOH_FASE_XX_<nome>.md                     # futuro, com provas
scripts/regions/
  sinnoh/                                      # módulos incrementais propostos
    audit_source.py
    inventory_maps.py
    plan_import.py
    stage.py
    validate.py
    install.py
  pilot_sinnoh.py                              # futuro: só após mapas reais
data/regions/
  sinnoh-source-manifest.json                  # futuro: somente metadados
  sinnoh-maps.json                             # futuro: mapeamento sem dados fictícios
  sinnoh-events.json                           # futuro
  sinnoh-trainers.json                         # futuro
  sinnoh-music.json                            # futuro
SINNOH_JOGAR_EXPERIMENTAL.bat                  # futuro
tests/
  test_sinnoh_audit.py                         # futuro
  test_sinnoh_import.py                        # futuro
  test_sinnoh_events.py                        # futuro
  test_sinnoh_regions.py                       # futuro
.blue-work/                                    # uso LOCAL, ignorado pelo Git
  sinnoh-source/
  sinnoh-stage/
  sinnoh-pilot/
```

**Manifesto de importação:** registrar ID do arquivo doador, ID lógico, hash original, autor/licença, tileset, autotiles, referências a outros mapas, NPCs, switches, variáveis, música, eventos, mapas de retorno, destino reservado e status de validação. **Não preencher `destination_id` inventado.** Antes de decidir IDs reais, auditar **toda** a instalação atual e a reserva das demais regiões.

**Regra por mapa:** não declarar uma cidade pronta sem todos os **interiores, portões, escadas, telhados acessíveis, NPCs, itens, encontros, movimentos de campo, música, transferências e pontos de cura/respawn** necessários no trecho da campanha.

### 3.1. Evento e diálogos: contrato mínimo

Cada cena deve descrever `event_key`, localização, gatilhos, flag persistente, diálogos (Português, sem alterar scripts doadores), comandos originais/convertidos, condição de cancelamento, batalha Blue correspondente, recompensa, retorno após derrota e teste. Nunca repetir o autorun após salvar/voltar; não usar flag global já ocupada; não confundir scripted battles com equipes PBS nativas.

### 3.2. Treinadores, encontros e dificuldade

- Usar equipes canônicas de Platinum e variantes comprovadas de Diamond/Pearl/BDSP como **dados de origem**, preservando Pokémon, habilidades, itens, golpes e formas válidas para a versão instalada.
- Reutilizar o estágio global por esmeraldas e o escalonamento já existente no Blue no **instante da batalha**; não escrever nível estático em scripts novos nem duplicar o cálculo dentro do piloto.
- A regra Master atual define quatro Pokémon para treinadores conforme o módulo existente, com cobertura de fraquezas e cerca de 90% do nível de referência; outras fases consultam os percentuais reais do código. Não presumir que a documentação substitui a implementação.
- Auditar encontros por mapa, método, horário, clima, tipo de terreno e estágio; permitir evoluções em lugares coerentes quando o level cap subir, sem recriar espécies arbitrariamente.
- Garantir um único cadastro para cada insígnia e não duplicar treinadores/Elite Four ao fundir Diamond/Pearl.

## 4. As DUAS barras oficiais de progresso de Sinnoh

**Barra 1 — fases com implementação técnica verificada: 0/13 (0%).**  
**Barra 2 — fases integralmente aprovadas por jogabilidade real: 0/13 (0%).**

A ordem é **Fase 00 a Fase 12 (13 fases)**, em conformidade com o MD de análise. As opções do título podem estar codificadas sem avançar a Barra 1: a **Fase 02 inclui o piloto com mapas reais**, que ainda não existe. A documentação deste plano não certifica nenhuma fase.

| Fase | Escopo | Técnica | Jogável / aceite integral |
|---|---|---|---|
| 00 | Auditoria de fonte, licença, baseline e dependências | [ ] | [ ] |
| 01 | Importador, manifestos e mapa-fonte autorizado | [ ] | [ ] |
| 02 | Piloto isolado e Testar Sinnoh funcional | [ ] | [ ] |
| 03 | Twinleaf, Route 201, Rowan, Barry, Sandgem | [ ] | [ ] |
| 04 | Jubilife, Oreburgh, Roark | [ ] | [ ] |
| 05 | Floaroma, Eterna, Gardenia e Galactic | [ ] | [ ] |
| 06 | Hearthome, Veilstone, Pastoria e três líderes | [ ] | [ ] |
| 07 | Canalave, Iron Island, Snowpoint e duas insígnias | [ ] | [ ] |
| 08 | Mt. Coronet, Galactic, Spear Pillar, Distortion World | [ ] | [ ] |
| 09 | Sunyshore, Victory Road, Elite Four e Cynthia | [ ] | [ ] |
| 10 | Battle Zone, pós-jogo, opcionais e lendários | [ ] | [ ] |
| 11 | Músicas, encontros, treinadores, site e guias | [ ] | [ ] |
| 12 | Integração final, regressão Windows/Android e publicação | [ ] | [ ] |

**Critério técnico (Barra 1):** artefatos corretos, código/versionamento sem colisões, testes automáticos relevantes e prova de integridade, inclusive dos recursos existentes. Se o escopo exigir mapas reais, código vazio não aprova.

**Critério integral (Barra 2):** caminhar do início ao fim do trecho no `Game.exe` **e** validar a execução alvo no JoiPlay quando essa distribuição for anunciada, batalhas e áudio audíveis, save/load, regressão das regiões antigas, instruções de reprodução e logs. Pode ficar tecnicamente pronto e **não** integralmente aprovado.

## 5. Sequência de execução — uma fase por vez

### FASE 00/12 — Auditar fonte, direitos e estado da instalação

**Ações**
1. Criar baseline do Git, relação de plugins/mapas/saves atuais em cópia local, hashes antes de qualquer alteração. Testar menu principal e casos anteriores.
2. Pedir/obter fonte editável **autorizada** de Sinnoh, priorizando inspeção do Ancient Platinum v1.0.6, mas não supondo que download jogável contenha `Map*.rxdata`.
3. Catalogar arquivos `Data`, `Graphics`, `PBS` e `Audio` da fonte real, autores/licenças, versão, faltas e conflitos, sem execução de scripts de terceiros.
4. Conferir contra Platinum quais mapas/eventos canônicos a fonte realmente cobre. Anotar cada ausência, sem criar dados falsos.
5. Auditar atual uso/reserva de MapIDs, tilesets e saves Kanto/Johto/Hoenn. Testar eventual uso de MapIDs de quatro dígitos em projeto descartável se for necessário.
6. Publicar um MD de auditoria com evidências e **SHA-256 por pacote**.

**Aceite técnico:** relatório real, mapa de dependências, riscos e permissões claros, sem modificar dados do jogo principal. **Bloqueio:** sem fonte autorizada e editável, não iniciar importação.

### FASE 01/12 — Importação segura e manifesto de mapas

**Ações**
1. Criar leitor passivo de mapas/PBS/tilesets, processando a estrutura real de RMXP/Essentials da fonte aprovada.
2. Montar grafo de referências e colisões para MapID, tileset, autotile, switches, variáveis, eventos comuns e arquivos gráficos.
3. Planejar IDs apenas após auditoria global, salvar mapeamento determinístico e comparar hashes com a fonte.
4. Criar `--dry-run` e relatório legível; implementar `--apply` só com backup/rollback atômico e proteção contra fonte alterada.
5. Gerar a lista de mapas que **podem** ser convertidos; rotular faltantes como **não disponíveis**, sem mapas de placeholder confundidos com mapa jogável.
6. Conferir que um mapa de teste pode ser instalado/retirado em cópia isolada, sem mudar save e mapa do Decades.

**Aceite:** mapas reais planejados, nenhuma substituição de IDs ou engines, simulação reversível e licenças verificadas.

### FASE 02/12 — Piloto real e menu Testar Sinnoh

**Ações**
1. Com os primeiros mapas reais autorizados, construir `scripts/regions/pilot_sinnoh.py` e `SINNOH_JOGAR_EXPERIMENTAL.bat`, sem caminho para modificar `game/` principal.
2. Copiar a base **local** do jogo para pasta descartável de piloto e instalar nela somente patches de Sinnoh; criar marcador **`Sinnoh pilot.json`**.
3. Implementar perfil de save exclusivo de Sinnoh, restaurável; não reutilizar Kanto/Johto ou slots do Decades.
4. Abrir pelo comando `Testar Sinnoh` do menu principal (já acrescentado ao código), com confirmação, verificação de arquivos e retorno seguro se faltar a fonte.
5. Testar todas as opções do título com saves e sem saves, índices do controlador antigo, cancelamento de abrir piloto, falha do BAT e auto-recursão.
6. Reservar ponto de spawn **real da casa do jogador em Twinleaf**: não usar mapa fictício para fingir prova do piloto.

**Aceite:** Game.exe real abre **apenas Sinnoh**, o jogador aparece no mapa-fonte auditado e pode mover/salvar com dados isolados. Mensagem de preparação quando não houver piloto é **aceite do botão**, não de Fase 02.

### FASE 03/12 — Abertura: Twinleaf, Barry, Rowan e Sandgem

**Cobertura:** casa/quarto, térreo, exterior de Twinleaf, Route 201, Lake Verity, Sandgem Town, laboratório do Professor Rowan, Route 202 e acesso seguro a Jubilife.

**Eventos:** cena inicial, diálogo com mãe, Barry, Professor Rowan, obtenção do inicial conforme trama de **Platinum**, escolha única entre **Turtwig, Chimchar e Piplup**, primeira(s) luta(s) previstas, Pokédex, Poké Balls e Tutorial, rival com time coerente. Adaptar diálogos sem misturar o evento de Oak/Kanto.

**Testar:** cada porta/escada, colisor, NPC, inventário, cap, cancelamento de diálogos, salvar no quarto antes/depois de inicial, retorno após derrota, música dia/noite e batalha Blue.

### FASE 04/12 — Jubilife → Oreburgh e Roark

**Cobertura:** Jubilife e interiores, Escola de Treinadores, Pokétch conforme mecânica disponível, Route 203, Oreburgh Gate, Oreburgh, Oreburgh Mine, Centro Pokémon, Poké Mart e primeiro ginásio.

**Eventos:** Barry, treinadores, treinador de ginásio, Roark, insígnia **Coal** única, permissão local Rock Smash e registro de esmeralda global somente uma vez.

**Testar:** entrada e saída de interiores; Roark antes/depois; revanche sem prêmio duplicado; save após obter insígnia; recuperação após blackout; encontros e evolução pelo cap.

### FASE 05/12 — Floaroma, Eterna e Gardenia

**Cobertura:** Route 204, Ravaged Path, Floaroma, Route 205, Valley Windworks, Eterna Forest, Eterna City, Galactic Eterna Building, Route 211; Fuego Ironworks e locais opcionais quando autorizados.

**Eventos:** Team Galactic, Mars/Jupiter, Drifloon condicionado ao estado/horário, Cheryl na floresta, bicicleta e Gardenia (**Forest Badge**). Incluir interiores e rotas opcionais relevantes sem bloquear progresso.

**Testar:** parceiro NPC sem duplicar party, batalha dupla suportada, capturas e encontros sob clima/horário, recompensas únicas, Cut condicionado à Forest e não à insígnia de outra região.

### FASE 06/12 — Hearthome, Solaceon, Veilstone e Pastoria

**Cobertura:** Cycling Road/Route 206, Wayward Cave, Mt. Coronet inicial, Route 208, Hearthome, Route 209/Lost Tower, Solaceon e ruínas, Route 210/215, Veilstone e prédios Galactic, Routes 214/213, Valor Lakefront, Pastoria, Great Marsh.

**Eventos:** Barry em encontros canônicos, Fantina (**Relic**), Maylene (**Cobble**), Crasher Wake (**Fen**); Contest Hall, Amity Square, Safari/Great Marsh e seus NPCs quando suportados, perseguição Galactic, rotas conectadas.

**Testar:** não embaralhar a ordem de Platinum; **Defog requer Relic e Surf requer Fen**; cobrir três insígnias sem duplicata; colisão em pontes e lama, Fly nas condições locais.

### FASE 07/12 — Canalave, Iron Island, lagos e Snowpoint

**Cobertura:** Route 218, Canalave com interiores e biblioteca, Iron Island e Riley, Route 211 e Mt. Coronet intermediário, Routes 216/217, Acuity Lakefront, Snowpoint, cavernas e passagens entre andares.

**Eventos:** Byron (**Mine**), Candice (**Icicle**), equipe Galactic nos lagos Verity/Valor/Acuity, quests principais; neve e Rock Climb com o requisito local. Cuidar da ordenação de eventos por Platinum.

**Testar:** múltiplos andares, gelo/neve, parceiros NPC, força/rock climb, portas e retorno de Fly, salvamento em exterior/baixo da nevasca e no meio da missão.

### FASE 08/12 — Galactic HQ, Mt. Coronet, Spear Pillar e Distortion World

**Cobertura:** esconderijos Galactic, elevadores, andares reais do Mt. Coronet, cume Spear Pillar, área/cenas do Distortion World; não supor mapas completos caso só exista visual parcial.

**Eventos:** Saturn, Jupiter, Mars, Cyrus, Dialga/Palkia dentro da trama Platinum, Giratina e sequência do mundo distorcido, perseguição e retorno. Gravar flags de cutscene idempotentes antes de transferências críticas.

**Testar:** puzzles, transições 2D para gravidade/orientação do Distortion World, queda/respawn seguro, salvar antes/depois, música de cena com prioridade correta, sem autorun infinito, sem substituir motor de batalha.

### FASE 09/12 — Sunyshore, Victory Road e Liga de Cynthia

**Cobertura:** Route 222, Sunyshore City e todos os interiores necessários, Route 223, Victory Road, Pokémon League, salas de cada Elite Four, Hall of Fame e retorno a Twinleaf.

**Eventos:** Volkner (**Beacon**), Waterfall só com insígnia local, Aaron, Bertha, Flint, Lucian e campeã **Cynthia**; cura, derrotas, badges, créditos, Hall of Fame. Encontros, treinadores e música regional auditados.

**Desbloqueio:** na **primeira** Liga de Sinnoh vencida, gravar um único marco e liberar logicamente **Hoenn e Unova** no circuito, sem permitir teleporte para mapas dessas regiões que não estejam instalados. NPC de viagem na **cidade inicial Twinleaf** e atalho pós-Liga usando serviço comum, respeitando outras regiões desbloqueadas.

**Testar:** quatro batalhas consecutivas, Cynthia, derrota/retry, save/load, esmeraldas sem duplicata, mesmas espécies na Box e no PC; viagem/reentrada no mesmo save, inclusive ao retornar de outra região.

### FASE 10/12 — Pós-jogo, Battle Zone, lendários e variações

**Cobertura:** Fight Area, Survival Area, Resort Area, Routes 225–230, Stark Mountain, Turnback Cave, Battle Frontier (somente se sistema real for implementado), casas/rotas/locais opcionais e missões adicionais de Platinum.

**Eventos:** Heatran, Giratina conforme estado narrativo, Cresselia, Darkrai/Shaymin somente com eventos/métodos coerentes e autorização dos assets, Giratina/Regigigas e outros lendários/mitos conforme documentação oficial. Não inventar missões inexistentes.

**Revanche/pós-jogo global:** após todas as Ligas do circuito terem sido vencidas uma vez, liberar versões **documentadas** de equipes fortes dos oito líderes, Elite Four e Cynthia, sem substituir o sistema de níveis dinâmicos nem duplicar insígnias. BDSP pode servir de catálogo de equipes mais fortes, mediante conferência.

**Testar:** evento uma vez, reentrada, lendário especial bloqueado na party de regiões com menos de oito insígnias e preservado na Box, sem perda por Box cheia; Battle Frontier só é declarada jogável quando comprovada.

### FASE 11/12 — Música, sons, treinadores, encontros e site completos

**Música:** mapear chaves em [SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) aos **MapIDs/cenas efetivos**; distinção BGM/ME, dia/noite, trainer/wild/rival/gym/Galactic/Giratina/Cynthia, clima, Surf, Hall of Fame, prioridade de cenas, fade/loop/fallback. Arquivos ausentes não geram silêncio em Decades. Publicar áudio somente com direitos verificados.

**Dados:** conferir os oito líderes, quatro Elite e Cynthia, equipes e variantes reais, PBS por ID único, encontros de todas as rotas por método e horário, estágios de evolução coerentes, Pokémon regionais/novos do Dessastre onde previstos, Drop/itens apenas se já suportado.

**Site:** adicionar Sinnoh com mapas reais por rota, pontos de captura, treinadores, líderes, Elite e campeão, equipes por estágio e formas de revanche. **Não exibir níveis fixos** onde a engine calcula por esmeraldas, nível do jogador e insígnias. Não publicar spoilers como se todas as quests fossem jogáveis antes de estarem disponíveis.

**Testar:** navegação por região, guias corretos, hashes de faixa, reprodução com loop, retorno à música original após batalha, consistência site↔PBS/mapa e build do site; escopo Android/JoiPlay validado separadamente.

### FASE 12/12 — Integração controlada e aceite final no jogo principal

1. Congelar a fonte/commit e baseline de todas as regiões e salvar backup recuperável da instalação local.
2. Gerar `dry-run` da instalação completa de Sinnoh; revisar cada dif de dados e scripts; validar que mapas e recursos da origem têm autorização.
3. Aplicar à cópia de integração e somente depois considerar instalação na cópia do usuário com backups e migração segura; nunca fazer `git add game/`.
4. Rodar bateria de regressão Decades/Kanto/Johto/Hoenn, save antigo/novo, menu, Blue Studio, Pokédex, Habitat, BlueMusic, box e balanceamento.
5. Executar **Game.exe Windows**: campanha de Twinleaf à Cynthia, encontros, insígnias, oito HMs, audiovisual, post-game e retorno.
6. Executar **JoiPlay/Android** em aparelho: controles, abertura de mapa, encontros selvagens, batalha, save/load, música, consumo de memória e interação; não declarar aceitação Android sem esse teste.
7. Confirmar portais seguros Hoenn↔Sinnoh↔Unova conforme permissões, seleção inicial só quando disponível, Box cheia/cancelamento na transferência e rollback se um arquivo necessário sumir.
8. Atualizar duas barras com evidência e relatórios; publicar scripts próprios, JSONs/manifestos sem assets protegidos, MD e site aprovado na `main` após CI; se faltarem provas, manter Sinnoh experimental.

**Aceite:** nenhuma regressão conhecida, arquivos originais preservados, campanha completa comprovada, lista exata de testes/ambientes registrada, rollback testado e status correto de distribuição.

## 6. Matriz de testes imprescindíveis

| Área | Prova automática | Prova real necessária |
|---|---|---|
| Menu | [`tests/title_kanto_runtime.rb`](../tests/title_kanto_runtime.rb), [`tests/test_title_kanto.py`](../tests/test_title_kanto.py) | Game.exe com/sem save, todos os comandos |
| Arquivos de mapa | Graph traversal, referências/IDs e hashes | Entrar e sair de todo interior, borda, caverna, ponte |
| NPCs/eventos | Flags, diálogos, ausência de autorun eterno | Jogar cenas, perder, salvar/recarregar |
| Batalhas | Times PBS válidos, integração com sistema Blue | Selvagem, rival, líder, Elite, Cynthia, Master |
| Música | BGM/ME, prioridade, faixas/fallback, hashes | Audição, loop, fade, troca de mapa, Android |
| Esmeraldas | Novo badge soma **uma vez** e progressão idempotente | Revanche, restauração de save, 8/8 e pós-Liga |
| HMs | Permissão por badge **de Sinnoh** | Testar Cut, Fly, Surf, Strength, Defog, Rock Smash, Rock Climb, Waterfall |
| Viagem/Box | 8 insígnias locais, bloqueio de especiais, rollback | Viajar com PC/party cheios, cancelar e voltar |
| Site | Build e integridade dos guias/MapIDs | Navegar no navegador e conferir equipes reais |
| Distribuição | Artefato sem arquivos não autorizados | Windows e Android em dispositivo, sem crash |

### 6.1. Regressões obrigatórias por fase

- Decades abre em `Novo Jogo` e `Continuar`, preserva esmeraldas, saves e batalhas originais.
- Kanto permanece disponível, sem mudança nos mapas, Oak/Gary, música, encontro, insígnias e escalonamento.
- Johto continua com o seu piloto, mapas, histórico de auditoria e times, sem troca inadvertida de IDs.
- Hoenn mantém a origem e o status reais, sem alterações em fontes ou reservas.
- A diferença entre estágio **global** de esmeraldas e insígnias **locais** continua visível nos cartões do jogador.
- Pokémon especiais da party são enviados à Box **antes** de viajar a Sinnoh quando ainda não tem 8/8 badges locais; não perder itens/equipe se caixa estiver cheia ou transação falhar.
- A regra global de pós-jogo só modifica o conjunto de oponentes permitido, sem nível fixo hardcoded.
- Todas as decisões de viagem e HM consideram **região atual, desbloqueio e disponibilidade do mapa**.

### 6.2. Evidências por fase

O relatório `docs/SINNOH_FASE_XX_*.md` precisa registrar: commit base e commit final, fonte/versão/licença/hashes, MapIDs importados ou justificativa de ausência, NPCs/itens/eventos/testes cobertos, comandos executados, saída PASS/FAIL, imagens ou logs de `Game.exe`/JoiPlay **quando disponíveis**, lista de regressões, plano de rollback e resultado das **duas barras**. **Não alterar status por testes simulados de código que não existe.**

## 7. Prompts de execução reproduzíveis via Codex/ChatGPT

### Primeira ação (somente após este MD)

> Aplique a **FASE 00** de `docs/SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md` ao projeto Blue Dessastre Paradoxal. Audite a `main`, as fontes reais de Sinnoh, direitos, arquivos RXDATA, gráficos, PBS e áudio, IDs ocupados por Decades/Kanto/Johto/Hoenn, e produza relatório com evidências. Não invente mapas nem sobrescreva `game/`. Rode testes de menu/regressão, publique o MD e o relatório na main e informe **Barra 1/Barra 2** sem marcar fases que não foram de fato aprovadas.

### Próximo núcleo (troque XX pela fase pedida)

> Continue a **FASE XX** de `docs/SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md`, seguindo o inventário e os mapas reais autorizados. Faça apenas alterações aditivas, valide ids e ligações, preserve Decades/Kanto/Johto/Hoenn e saves, execute os testes automáticos cabíveis e não afirme aceite do jogo sem Game.exe e JoiPlay. Publique na main o código/documentação aprovados e informe as duas barras e bloqueios.

### Testar Sinnoh quando houver piloto real

> Valide o `Testar Sinnoh` do mesmo menu inicial do `Game.exe`. Teste os três botões regionais e o comportamento com/sem saves, `Mystery Gift`, falha de launcher, flag de piloto, caminho de spawn em Twinleaf, batalha selvagem, save/load, retorno, BlueMusic e Android/JoiPlay. Não misture saves nem substitua mapas dos outros pilotos. Entregue relatório de aceite com evidências; se faltar prova, mantenha a Barra 2 pendente.

## 8. Primeiro objetivo concreto

**Primeira entrega a executar:** Fase 00/12 — obter **fonte de Sinnoh em formato editável e uso autorizado**, conferir contra Platinum, registrar mapas/interiores/eventos/áudio realmente presentes, IDs seguros e baseline; emitir o relatório. **O botão Testar Sinnoh já consta do código**, mas seu piloto com mapas reais precisa ser criado na fase 02. **Não enviar um ZIP com mapas inventados, nem adaptar Hoenn ou Johto para fingir Sinnoh.**

**Conclusão do plano:** Sinnoh cresce como módulo isolado, com todos os locais e eventos de Platinum, combate/balanceamento nativos do Blue, música própria auditada, menu experimental seguro e **zero regressão aceita** em Decades/Kanto/Johto/Hoenn.
