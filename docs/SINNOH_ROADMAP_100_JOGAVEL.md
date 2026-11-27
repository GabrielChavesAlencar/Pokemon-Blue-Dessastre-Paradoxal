# Sinnoh — Roadmap executável para 100% jogável (Codex)

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Baseline da análise:** 27/11/2026 | **Destino:** Blue-Story principal (Windows) e canal Android multiregion (JoiPlay)  
**Status:** plano de implementação; NÃO representa certificação de gameplay.  
**Issue de história:** [#318](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/318) | **Integrações:** [#338](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/338), [#339](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/339).

## 1. Instrução principal ao Codex

Execute este documento em ordem de dependências, na revisão atual de main, aproveitando o código já existente. O objetivo é entregar Sinnoh como região do mesmo mundo compartilhado, do quarto inicial ao Hall of Fame e ao pós-game, não como piloto separado. Priorize alterações funcionais verificáveis em vez de criar novos relatórios sem mudanças de gameplay. Cada etapa SN01–SN25 é um checkpoint de trabalho, distinto das antigas fases S, J, CH e F; não renomeie nem apague seus históricos.

Comece por SN01 e identifique o primeiro bloqueio real. Trabalhe em PRs pequenos e coerentes (uma etapa ou corredor jogável por PR), reutilize testes e scripts; não reimporte mapas já corretos. Execute localmente testes rápidos de cada alteração, depois CI de integração e, quando possível, runner Windows descartável. Se uma falha exigir fonte privada ou dispositivo indisponível, marque BLOCKED_ENV com ação concreta para desbloqueio. Não simule recibos, não declare sucesso e não publique conteúdo não aprovado. Continue somente as tarefas independentes que não prejudiquem o gate bloqueado.

### Definição de 100%

- **Campanha completa:** Novo Jogo → Sinnoh, Lucas/Dawn e nome, três escolhas de inicial, história contínua de Platinum adaptada ao Dessastre Paradoxal, oito ginásios e esmeraldas, Galáctica, lagos, Giratina, Victory Road, Elite Four, Cynthia e Hall of Fame.
- **Região completa:** todas as áreas, rotas, interiores relevantes, encontros, treinadores, serviços, HMs, missões secundárias, lendários previstos, Battle Frontier e pós-game dentro do escopo registrado. Mecânicas não suportadas devem receber implementação autoral equivalente aprovada, ou permanecer explicitamente pendentes; não retirar requisitos para chegar a 100%.
- **Distribuição completa:** mesmo Game.exe, mesmo perfil de save e agente de Twinleaf; Windows e Android publicados na mesma revisão funcional com instalação limpa, atualização, migração e regressão multirregional verificadas. JoiPlay precisa de execução real independente.

## 2. Baseline verificada e pendências

Fonte de verdade: [manifesto de expansão](../data/regions/sinnoh-expansion-progress.json), [progresso](SINNOH_PROGRESSO.md), [integração compartilhada](SINNOH_BLUE_STORY_COMPARTILHADO.md), [F12D](SINNOH_F12D_INTEGRATED_GAMEPLAY.md), [reserva compartilhada](../data/regions/sinnoh-shared-mapids.json). Atualize a leitura antes de agir; alguns campos históricos contradizem documentos recentes.

| Área | Evidência existente | Próximo gate |
|---|---|---|
| F01–F07 | Ferramentas QA, 14 cidades, 30 rotas, 127 mapas na antiga fixture | Revalidar no mundo compartilhado; cobertura total de interiores e destinos |
| F08 | 145 conexões direcionais candidatas; 83 pendentes na fotografia histórica; 131 mapas ao fim da fase | Recalcular grafo atual, resolver Cycling Road, Resort Area, conexões e dependências |
| F09 | 120 métodos de encontro recuperados; pesos e métodos auditados | Conferir catálogo real compilado, todos os terrenos e métodos nativos |
| F10 | 2.124 eventos auditados em 127 mapas-fonte; seis treinadores recuperados em fixture, seis candidatos específicos pendentes | Instalar e testar eventos efetivos, inventário total por área |
| F11 | Oito salas e líderes, 89 portais na fixture de 139 mapas | Batalhas, recompensas, permissões e persistência no jogo principal |
| F12B | Windworks preparado, acesso QA-only registrado | Rota 205/Floaroma, chave, Mars e retorno físico |
| F12C | Quatro andares de Eterna preparados, base QA 144 | Cut, Jupiter, resgate, bicicleta e Cycling Road |
| F12D | Pastoria F12D2, SecretPotion, provas nativas de Surf | Continuidade dos três lagos, Celestic, comandante e história |
| F13 | Pendente no manifesto | Victory Road, Liga, Cynthia e Hall of Fame |
| F14 | Pendente | Pós-game, lendários e instalações de batalha |
| F15 | Pendente | Aceite nativo, publicação e regressões |
| Compartilhado | 144 mapas; Windows compilado e oito viagens registradas; ZIP QA Android verificado | Aceite campanha, dispositivo JoiPlay, direitos e distribuição estável |

**MapIDs:** a reserva atual lida em main tem 144 chaves, valores únicos esperados de 452 a 595. O manifesto histórico usa 451–594 e os relatórios F12D antigos usam IDs da fixture. Nunca aplicar offsets cegamente. Resolver cada referência pelo identificador simbólico e MapInfos real da instalação; migrar saves somente com prova de mapeamento individual e rollback. Não supor que 596 em diante esteja livre, especialmente após mudanças de Kanto/Johto/Hoenn/Unova.

**CI observada:** PR #338, HEAD a2ac85fe4a27bf8d273c3d770e9b55dcf461e60d, 11/11 workflows retornados com sucesso. PR #339, HEAD 3fbc798fed47b3f62df6f765737c4c8cecefbbbd, 29/31 execuções retornadas com sucesso; falhas históricas em [Blue Studio 45932731933](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/45932731933) e [Piloto Kanto 45932731866](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/45932731866). Ambos PRs estão merged. Reconfirmar na main atual, sem revertê-los automaticamente ou assumir falha ainda aberta.

**Lagos:** último registro F12D/issue #318 indica F12D 3/8, Valor condicional 1/3, trajetos integrais 0/3 e comandantes da sequência 0/3. Provas de Surf nos IDs antigos 511 e 529: 154 e 78 passos respectivamente (46/48 secos, 108/30 aquáticos/transição; 2 embarques e 2 desembarques cada); quatro transferências Verity preservadas; 19 intervalos vazios verificados, zero offsets aceitos. Não confundir prova de movimento local com jornada inteira. Eventos fonte 82/82 e 156/1 são candidatos norte e precisam de componentes de chegada/saída reais, remapeados na base atual.

## 3. Fontes, downloads e ambiente

| Recurso | Local/URL | Uso |
|---|---|---|
| Repositório | https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal | Código, documentação, issues |
| Clone | https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git | Checkout imutável por SHA |
| Releases | https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases | Escolher par funcional existente, manifestos e assets |
| Blue-Story.exe geral | https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/blue-story-windows/Blue-Story.exe | Link estável definido pelo workflow; verificar disponibilidade, revisão e hash antes do uso |
| CI | https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions | Runs, jobs e recibos |
| Base original Decades | https://github.com/HazyCrazy/Pokemon-Decades | Base autorizada conforme instalador e créditos |
| Fórum do criador Decades | https://eeveeexpo.com/threads/9341/ | Proveniência |
| Sinnoh Maps.zip (fonte primária) | https://eeveeexpo.com/resources/generation-3-styled-sinnoh-exterior-and-cave-maps.1661/download | Download do autor; redirect MEGA ID PMZxiYhI |
| Sinnoh Maps.zip (rota alternativa do mesmo autor) | https://eeveeexpo.com/resources/1661/download | Mesmo recurso, mesmo hash |
| Ultimate Gen 4 Overworlds Pack.zip | https://eeveeexpo.com/resources/609/download | Download do autor; MediaFire ID vmrjeckhz5dclzr |
| JoiPlay e plugin RPG Maker | https://www.joiplay.net/ | Teste em Android autorizado |
| Termux | https://github.com/termux/termux-app | Opcional, atualização incremental |
| GitHub CLI | https://cli.github.com/ | CI e releases |
| Python | https://www.python.org/downloads/ | Usar versão do workflow |
| Pokémon Essentials | https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki | Referência de API; validar contra engine real |
| RPG Maker XP | https://store.rpgmakerofficial.com/products/rpg-maker-xp | Edição legal de recursos próprios |
| Platinum — walkthrough | https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pokémon_Platinum | Referência de progressão, não pacote de assets |
| Pokéarth Sinnoh | https://www.serebii.net/pokearth/sinnoh/ | Referência de áreas, encontros e conexões |

Links dos dois ZIPs vêm diretamente de [sinnoh_source_download.py](../scripts/regions/sinnoh_source_download.py); hashes de [sinnoh_private_visual.py](../scripts/regions/sinnoh_private_visual.py). Não foi realizado novo download dos arquivos nesta análise.

| Arquivo | Bytes esperados | SHA-256 |
|---|---:|---|
| Sinnoh Maps.zip | 89235961 | `79a7a4e4d176039daa9d3a2866540ced4daad4c9043a9a82378dae45a60e9e26` |
| Ultimate Gen 4 Overworlds Pack.zip | 2158072 | `e9d240918b62460c76d56ec9e5d4067a4ee853979d16a6657c05917d9bfd2b99` |

Use primeiro o cache privado já validado. O downloader existente usa Windows CNG para MEGA, permite apenas provedores/IDs esperados, tamanho/hash exatos e retries limitados. Não use mirrors, ROMs não autorizadas, scripts de donor executados diretamente, chaves privadas ou download sem verificação. A disponibilidade pública não implica autorização de redistribuição. Se fonte faltar, pedir arquivo local legítimo ou criar mapa/sprite autoral, documentando licença, identidade e equivalência. Guardar material privado em .blue-work, fora de Git e artifacts públicos. Registrar créditos e direitos de cada pacote, música e sprite; se distribuição não autorizada, manter instalação local privada com recursos fornecidos pelo usuário e NÃO promover Android.

## 4. Bootstrap e rotina de execução

Comandos de terminal (adaptar PowerShell/bash e caminhos; não executar no save principal do usuário):

```bash
git clone https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git
cd Pokemon-Blue-Dessastre-Paradoxal
git fetch origin
git switch main
git pull --ff-only origin main
git rev-parse HEAD
git status --short
git switch -c sinnoh/sn01-baseline
gh auth status
gh pr list --state open --search Sinnoh
gh issue view 318
gh run list --limit 50
gh release list --limit 30
```

Em checkout Windows descartável, com engine e recursos de uso autorizado, siga o fluxo do workflow existente:

```powershell
python scripts/install_game.py --help
python scripts/install_game.py --apply
Get-FileHash 'Sinnoh Maps.zip' -Algorithm SHA256
Get-FileHash 'Ultimate Gen 4 Overworlds Pack.zip' -Algorithm SHA256
python scripts/regions/prepare_sinnoh_shared.py --help
python scripts/regions/stage_sinnoh_shared_qa.py --help
python scripts/regions/prepare_sinnoh_shared.py
python scripts/regions/stage_sinnoh_shared_qa.py --compile
```

Fornecer os ZIPs autorizados na raiz da instalação (ou cache privado reconhecido pelo downloader). Usar o mesmo --base-game nas duas etapas quando a base for externa. A preparação grava .blue-work/sinnoh-shared-candidate/world/ e candidate.json; stage grava .blue-work/sinnoh-shared-qa/game/ e stage.json. O perfil QA nunca deve ativar a instalação de uso real. Não rodar Game.exe fora de runner descartável/cópia QA autorizada; não acessar saves pessoais. A própria base pode ter mudado: primeiro confirmar pré-condições e reusar os argumentos atuais de --help, sem presumir que hashes históricos sejam hashes dos builds atuais.

### Arquivos centrais para editar/reutilizar

- [Preparação compartilhada](../scripts/regions/prepare_sinnoh_shared.py), [instalação transacional](../scripts/regions/sinnoh_shared.py), [stage QA](../scripts/regions/stage_sinnoh_shared_qa.py).
- [Instalador geral](../scripts/install_game.py), [launcher](../scripts/launch_game.py), [Bootstrap Windows](../scripts/windows/Bootstrap.cs), [build Windows](../scripts/windows/build.py).
- [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb), [SinnohSharedEvents.rb](../scripts/regions/SinnohSharedEvents.rb), [SinnohF12DIntegrated.rb](../scripts/regions/SinnohF12DIntegrated.rb), [PBS](../scripts/regions/pbs.py).
- [RegionStart](../scripts/battle_polish/RegionStart.rb), [RegionTravel](../scripts/battle_polish/RegionTravel.rb), [RegionalRespawn](../scripts/battle_polish/RegionalRespawn.rb), [TitleKanto](../scripts/battle_polish/TitleKanto.rb).
- [Compilador F12D](../scripts/regions/sinnoh_f12d_integrated.py), [runtime F12D](../scripts/regions/sinnoh_f12d_runtime.py), [geometria](../scripts/regions/sinnoh_f12d3_canonical_network.py), [Cut Psyduck](../scripts/regions/sinnoh_f12d3_celestic_cut.py), [SecretPotion](../scripts/regions/sinnoh_f12d3_secretpotion_catalogue.py).
- [Package Android](../scripts/android/package.py), [publicador de deltas](../scripts/android/publish_updates.py), [atualizador](../scripts/android/update_client.py).
- [Workflow Windows](../.github/workflows/blue-story-windows.yml), [Android](../.github/workflows/android-multiregion-tests.yml), [verificação integrada Kanto](../.github/workflows/kanto-pilot-check.yml), [tests](../tests/).

Pesquisar outros arquivos por rg -i sinnoh scripts data tests .github/workflows e localizar implementações existentes antes de criar novas.

## 5. Invariantes obrigatórias

1. Preservar saves, MapIDs existentes, flags e progresso de Decades, Kanto, Johto, Hoenn e Unova; nunca sobrescrever dados de outra região. Reservar novos IDs depois de checar ocupação real, mapa simbólico, reservas, connections e migração.
2. Uma insígnia regional gera uma esmeralda exatamente uma vez. Level cap regional; Normal 70% e Master 90% do maior Pokémon do jogador conforme implementação global existente, sem alterar chefes autorais/líderes/Elite/Campeões protegidos. Evolução dinâmica conforme política global (nível +5, pedra a partir de 30, troca a partir de 40, felicidade a partir de 45), preservar exceções. XP de equipe ligado; Dynamax desativado.
3. HMs exigem HM adquirido na região, insígnia correta e Pokémon compatível. Referência Platinum: Cut/Forest, Fly/Cobble, Surf/Fen, Strength/Mine, Defog/Relic, Rock Smash/Coal, Waterfall/Beacon, Rock Climb/Icicle. Confirmar catálogo oficial do projeto antes de aplicar; não emprestar flags/itens de outra região.
4. Viagens pelo agente inicial, equipe enviada ao Box pela política de viagem vigente, sem perda ou duplicação; PC e save compartilhados, separar itens-chave/HMs/progresso regional. Região inicial não deve ser substituída pela região atual. Blackout retorna ao último Centro da região, fallback à cidade inicial. Sem menus indevidos ao chegar em Decades.
5. Recompensas/itens/lendários/puzzles com transações idempotentes: vitória real antes de flag, falha não concede, cancelamento e bolsa/PC cheios tratados, persistência após reload.
6. Não desbloquear conteúdo via flag artificial, teleporte de QA, botão que entrega itens ou alteração de teste. Teleporte de desenvolvedor permanece isolado e não conta como percurso válido.
7. PT-BR, sprites e música adequados, sem tiles pretos ou colisões inconsistentes. Não substituir mapas por placeholders, não importar executáveis/scripts externos sem revisão.
8. Cada mudança deve preservar a baseline funcional de Kanto (incluindo Gary e escala do player), Johto, Hoenn, Decades e demais catálogos. Nenhum teste obrigatório pode ser desativado, afrouxado ou marcado sucesso sem execução.

## 6. Etapas executáveis (25)

**P0:** bloqueia campanha/distribuição; **P1:** necessário para escopo completo. Toda etapa inclui diff funcional quando houver lacuna, testes negativos/positivos, recibo e atualização de manifesto. Se já comprovada na revisão atual, reutilize evidência verificável, não reimplemente.

### SN01 — Reconciliar baseline e CI (P0; sem dependência)

- [ ] Registrar SHA atual, HEADs/merges de #338/#339, issue #318, PRs de Kanto ativos e distribuição funcional mais recente.
- [ ] Recalcular mapa simbólico → MapID → nome real, hashes de MapInfos, tilesets, connections, metadados, PBS e plugins; detectar duplicidade e ocupação.
- [ ] Investigar jobs das duas falhas históricas #339 e regressões atuais; separar falha de fonte indisponível de falha de código.
- [ ] Reconciliar estados F12 e intervalo de IDs com fatos atuais; identificar o primeiro corredor bloqueado; criar matriz de tarefas e testes existentes.
- Aceite: inventário sem colisão ou bloqueio claramente identificado; nenhuma aprovação antiga transferida para SHA novo sem evidência; CI atual registrada. Não mudar IDs para ajustar documento.

### SN02 — Consolidar instalação compartilhada dos mapas (P0; SN01)

- [ ] Reusar prepare/stage/shared; verificar fontes e gerar candidato dos 144 mapas contra base atual.
- [ ] Garantir arquivos RXDATA não vazios, tilesets, sprites, encontros, MapInfos e connections coerentes; preservar os mapas de outras regiões. Verificar mapeamentos históricos de fixture.
- [ ] Compilar no Game.exe da cópia QA; confirmar quarto inicial, agente único em Twinleaf e retorno dos quatro destinos Decades/Kanto/Johto/Hoenn. Testar origem Kanto → Sinnoh mantendo região inicial.
- [ ] Comparar instalação limpa e upgrade de cada baseline suportada. Testar hash incorreto, arquivo faltante, ID ocupado, interrupção e rollback.
- Aceite: pacote QA reproduzível, oito viagens efetivas registradas, save/reload e hashes; nada promovido prematuramente.

### SN03 — Grafo físico e recuperação de conexões (P0; SN02)

- [ ] Inventariar cada destino do catálogo e interiores reais; classificar entradas, saídas, portas, escadas, mapas compostos e conexões de borda.
- [ ] Construir grafo direcionado de componentes passáveis usando terreno, camadas, máscaras, prioridades, eventos, origem/destino e condições de história/HM. Provar percurso e retorno, não só presença de MapID.
- [ ] Recalcular F08: resolver Cycling Road, Resort Area, cavernas, rotas divididas, corredores e estabelecimentos. Priorizar conexões necessárias para SN04–SN19; repetir grafo a cada etapa.
- [ ] Preservar entradas existentes, evitar transferências artificiais; se geometria do donor inviável, criar adaptação autoral aprovada com passabilidade e isolamento. Verificar barreiras e trechos inacessíveis intencionais.
- Aceite: cobertura por fase de progressão, testes de caminho proibido antes do gate e permitido depois; cada componente pendente tem motivo e responsável. Nenhuma viagem válida depende de QA.

### SN04 — Twinleaf, Verity inicial, Rowan (P0; SN02–03)

- [ ] Confirmar escolha de Lucas/Dawn e nome, escala/sprites, música, quarto/térreo, mãe, Barry, chegada ao local inicial de história.
- [ ] Reusar SinnohPilot e SharedEvents para seleção real das três Poké Bolas; cada escolha cria somente um Pokémon; restantes somem e flags persistem.
- [ ] Validar introdução de Barry, batalha conforme contrato existente, catálogo compilado, Pokédex e cinco Poké Bolas de Rowan.
- [ ] Bloquear grama sem Pokémon e Rota 202 antes da entrega; liberar depois; encontros R201, Centro, Poké Mart e save inicial.
- Aceite: seis variantes personagem × inicial em fixtures, pelo menos caminhos representativos em engine real; cancelar escolha, derrota e reload sem duplicação ou softlock.

### SN05 — Jubilife, Oreburgh e Roark (P0; SN04)

- [ ] Reconectar R202–Jubilife–R203–Oreburgh Gate–Oreburgh/Mina, incluindo retorno.
- [ ] Revisar escola de treinadores, Pokétch (UI adaptada se necessário), eventos, rival e encontro com Galáctica conforme ordem de Platinum/projeto.
- [ ] Instalar/validar treinador de ginásio, quebra-cabeça, Roark, Coal Badge, esmeralda e HM Rock Smash regional; bloqueios para próximo trecho.
- Aceite: jornada sem QA até primeira insígnia e retorno; falha sem prêmio, vitória única, uso negativo/positivo Rock Smash, save/reload.

### SN06 — Floaroma, Valley Windworks e Mars (P0; SN05)

- [ ] Resolver acesso real pela Rota 205 e Floaroma, incluindo saída e retorno; investigar seams fonte 111↔94/199 e ambiguidade de lado registrada, sem inventar offsets.
- [ ] Reusar F12B4/B5; preparar layout comprovado (ou adaptação autoral explícita), recrutas, batalha pela Works Key, porta trancada, Mars, resgate e liberação posterior.
- [ ] Auditar catálogo POTION, TM24, ELECTIRIZER, MAXELIXER; cada pickup único, acessível, sem concessão antecipada; Works Key independente.
- Aceite: entrada normal, bloqueio antes da chave, vitória real e saída; derrota/retry, bolsa, save/reload e acesso Eterna após resolução. Eliminar dependência de teleporte QA.

### SN07 — Eterna, Jupiter, bicicleta e Cycling Road (P0; SN06)

- [ ] Eterna Forest e acompanhante Cheryl, passagem a Eterna; Gardenia e Forest Badge.
- [ ] Conectar quatro andares Galactic Eterna Building, escadas e saída; exigir Cut legal, recrutas, Jupiter e resgate do dono da loja.
- [ ] Validar bicicleta como recompensa única e deslocamento em Cycling Road, gates de entrada, comportamento ao desmontar; resolver R206.
- Aceite: trilha completa após Windworks, antes/depois da insígnia/Cut, batalha e resgate, bicicleta persistente; sem salto via QA.

### SN08 — Hearthome, Solaceon, Veilstone (P0; SN07)

- [ ] Corredor R206/207/Mt. Coronet/R208/Hearthome; Fantina e Relic Badge; Barry conforme roteiro.
- [ ] Solaceon R209/210/215, Day Care (depósito, retirada, ovo e persistência se previsto), Solaceon Ruins, NPCs e treinador.
- [ ] Veilstone, Maylene e Cobble Badge; recuperação da Pokédex e confronto galáctico; Fly adquirido no evento correto, deslocamento legal.
- Aceite: terceira e quarta insígnias, progressão e retorno; Fly não permite saltar gates, serviço Day Care sem perda de equipe, derrota/reload.

### SN09 — Pastoria e SecretPotion (P0; SN08)

- [ ] Validar corredor R214/213/Pastoria e Valor Lakefront, Crasher Wake/Fen Badge, NPCs Great Marsh e perseguição do recruta.
- [ ] Reusar compilador F12D; encontro com Cynthia, entrega regional única da SecretPotion, consumo uma vez e desbloqueio persistente.
- [ ] Provar corte real dos quatro Psyduck no grafo e em runtime: sem contorno prematuro, caminho após a cura e retorno seguro; testar save antes e depois.
- Aceite: nenhum desvio proibido por portais, Fly ou Surf, nenhum item duplicado, continuidade até Celestic.

### SN10 — Celestic, ruínas e Surf (P0; SN09)

- [ ] Reauditar cinco eixos e conexão de saída de R210 para Celestic, história das ruínas e eventos com Cynthia/Cyrus conforme escopo aprovado.
- [ ] Validar HM03 adquirido legalmente e recibo regional, Fen Badge e espécie compatível; reutilizar probes de Surf já aprovados mapeados para IDs compartilhados atuais.
- [ ] Provar embarque, movimento, encontros e desembarque com Game_Player real; testes negativos sem HM, badge, recibo ou Pokémon.
- Aceite: jogador chega e retorna fisicamente, Surf funcional na campanha (não apenas compile-only) e persistência do desbloqueio.

### SN11 — Canalave, Iron Island e Byron (P0; SN10)

- [ ] Conectar Jubilife/R218 por Surf e Canalave; rival, biblioteca e gatilho de história no momento apropriado.
- [ ] Ferry/viagem a Iron Island, Riley, cavernas e ovo Riolu se previsto; retorno sem softlock, tratamento de equipe/PC cheios.
- [ ] Byron/Mine Badge e Strength conforme contrato, autorização para corredor norte.
- Aceite: sexta insígnia, retorno à região central e barco seguro; pré-requisitos negativos, save/reload.

### SN12 — Três lagos e comandantes (P0; SN10–11; depende do acesso norte SN13)

- [ ] Reusar sinnoh_f12d_integrated.py, runtime, assets e graph receipts. Ler últimas evidências #318/#338 e gerar relatório de componentes atual, não repetir cegamente busca já negativa.
- [ ] Valor: provar ida/volta ao interior, evento Saturn e missão; condição Surf só quando permitido.
- [ ] Verity: preservar quatro transferências reais e suas direções; resolver componentes externos/internos sem sobrescrever eventos; revalidar dependências e paths antes de ativar Mars.
- [ ] Acuity: usar o corredor norte desbloqueado em SN13; tratar eventos fonte 82/82 e 156/1 com geometria real, não inferir coordenadas nem converter Rock sem prova; acesso a Acuity exige Icicle no ponto de história previsto.
- [ ] Aplicar sequência ordenada e gate all-or-nothing existente: nenhum comandante marcado concluído só por fixture, vitória efetiva e retorno nos três lagos; conferir flags, recompensas e desbloqueio HQ.
- Aceite: 3/3 trajetos integrais ida/volta, 3/3 comandantes/eventos da sequência, gates e save/reload; F12D.4–8 encerradas apenas quando seus contratos forem satisfeitos. Se norte bloquear, executar SN13 antes de finalizar SN12.

### SN13 — Mt. Coronet norte, R216/217, Snowpoint (P0; SN11; executar em paralelo lógico com SN12)

- [ ] Provar corredor Mine Badge → Strength → Mt. Coronet → Route216/217 → Snowpoint usando mapas reais, eventos recíprocos e componentes de chegada; respeitar Rock Smash e limites de campo.
- [ ] Candice e Icicle Badge; Rock Climb no catálogo correto; desbloquear Acuity na fase prevista, não antecipar Lake Acuity.
- [ ] Validar neve, colisões, encontros, treinadores, retorno e blackout regional.
- Aceite: caminho e retorno sem teleporte QA, sétima insígnia, gates negativos e caminho até Acuity, entregar dependência SN12.

### SN14 — Veilstone Galactic HQ, Cyrus e trio dos lagos (P0; SN12–13)

- [ ] Verificar Warehouse, HQ, interiores e conexões; recuperar fontes autorizadas ou construir equivalentes originais, identificados no inventário.
- [ ] Storage Key/Galactic Key conforme roteiro, recrutas, teletransportadores internos legítimos de puzzle, batalha Cyrus e resgate Uxie/Mesprit/Azelf; bloquear acesso precoce.
- [ ] Recompensa Master Ball se prevista, flags de trio livre e desbloqueio de Mt. Coronet/Spear Pillar; sem duplicação ou inventário indevido.
- Aceite: caminho completo, retorno, derrota/retry, itens e flags persistidos; nenhuma progressão artificial.

### SN15 — Mt. Coronet sul/topo, Spear Pillar e Distortion World (P0; SN14)

- [ ] Inventário de andares, cavernas, terreno, conexões e HM Rock Climb; construir percurso fisicamente válido até Spear Pillar e retorno.
- [ ] Recrutas, batalha dupla Mars/Jupiter com Barry se definida, Cyrus e abertura do Distortion World na ordem correta.
- [ ] Auditar suporte do motor a plataforma, inversão/perspectiva e puzzle; implementar equivalente autoral jogável se engine não suportar original, mantendo progressão, obstáculos, retorno e checkpoints.
- Aceite: caminho reproduzível, puzzles não bloqueiam save, batalha real, nenhuma possibilidade de ir ao final sem história.

### SN16 — Giratina, retorno e Sunyshore (P0; SN15)

- [ ] Cyrus final, Cynthia, Giratina (captura/derrota/fuga conforme regra do projeto), saída e retorno seguro.
- [ ] Fechar flags da Galáctica, liberar R222/Sunyshore, evento Flint/Volkner; validar oitavo ginásio, Beacon Badge e Waterfall conforme contrato.
- Aceite: final da história registrado, oito badges/esmeraldas, nenhuma duplicação, acesso liga desbloqueado só com requisitos; persistência e blackout.

### SN17 — Matriz final dos oito ginásios, HMs e balanceamento (P0; SN05–16)

- [ ] Revalidar Roark/Coal, Gardenia/Forest, Fantina/Relic, Maylene/Cobble, Wake/Fen, Byron/Mine, Candice/Icicle, Volkner/Beacon.
- [ ] Para cada um: acesso, puzzles e treinadores, líder, time compilado, derrota/retry, vitória, insígnia, uma esmeralda, HM/permissão, level cap e Trainer Card.
- [ ] Testar cada HM com combinações faltando cada requisito e todas presentes, inclusive badges de outra região, Pokémon incompatível e tentativa antes da história.
- [ ] Normal/Master, evolução dinâmica, XP, chefes protegidos e persistência. Não inventar equipe/nivel original sem fonte e contrato.
- Aceite: 8/8 ginásios e 8/8 HMs em matriz com recibos reais; nenhuma regressão em outra região.

### SN18 — Victory Road e portão da Liga (P0; SN16–17)

- [ ] Verificar Route223, Waterfall, Centro antes da Liga e todos os mapas/andares da Victory Road; reservar novos IDs apenas com inventário.
- [ ] Importar/criar mapas legais e tilesets; instalar puzzles, treinadores, itens e encontros. Resolver entrada/saída, HM gates e bloqueio de insígnias.
- Aceite: jornada e retorno até Liga por gameplay, negativo com badge/HM ausente, save em cada andar e blackout seguro.

### SN19 — Elite Four, Cynthia, Hall of Fame (P0; SN18)

- [ ] Implementar salas e ligações para Aaron, Bertha, Flint, Lucian e Cynthia; times homologados e protegidos pelo balanceamento autoral.
- [ ] Fluxo contínuo com derrota, tentativa, cura conforme regras e avanço somente por vitória real; sem teleporte entre salas para burlar sequência.
- [ ] Hall of Fame, registro de campeão, créditos/retorno e abertura do pós-game; múltiplas vitórias e revanches sem prêmio duplicado.
- Aceite: do Novo Jogo à vitória de Cynthia em uma partida sem QA, save/reload e pós-game acessível. Campanha 100% ainda não equivale a região 100%.

### SN20 — Completar treinadores, encontros e NPCs (P1; incremental desde SN03, fechar após SN19)

- [ ] Atualizar inventário por mapa dos 2.124 eventos históricos; identificar classe/nome/equipe, páginas, condição, sprite e geometria. Priorizar Austin, Kevin, Helen, Louis, Alexander e Wyatt; reauditar restantes sem confundir candidatos com total de treinadores.
- [ ] Compilar PBS local; batalha por visão e interação, duplas, times escalonáveis, rematches/VS Seeker; diálogos PT-BR, serviços, PC/Mart, objetos, NPCs e acompanhantes Cheryl/Mira/Riley/Marley/Buck.
- [ ] Validar grama, cavernas, água, Old/Good/Super Rod, horários, Poké Radar, Honey Trees, swarms e Great Marsh; reconciliar pesos reais, espécies, níveis e condições. Não introduzir tabela genérica em área sem fonte.
- Aceite: cada área tem inventário esperado versus instalado, teste representativo de cada método, encontros proibidos e válidos, ausência de NPC/treinador inacessível ou erro de catálogo.

### SN21 — Pós-game, áreas e lendários (P1; SN19)

- [ ] Fight/Survival/Resort Area, R225–230, transporte, National Dex, Stark Mountain/Buck/Heatran, Snowpoint Temple/Regigigas, Turnback Cave, Fullmoon Island/Cresselia.
- [ ] Uxie/Mesprit/Azelf, Dialga/Palkia e Giratina conforme estado da história; roaming persistente quando previsto, encontros estáticos únicos, captura, derrota, fuga e nova tentativa conforme política.
- [ ] Darkrai/Newmoon, Shaymin/Flower Paradise, Arceus e demais eventos especiais: registrar método de desbloqueio autoral aprovado e fonte legal; não copiar distribuição de eventos proprietários. Se fora do escopo, decisão explícita do proprietário, não marcar automaticamente completo.
- Aceite: todos os destinos pós-game acessíveis após gate, sem acesso prematuro, ledger de lendários/recompensas e saves válidos.

### SN22 — Battle Frontier e atividades secundárias (P1; SN19–21)

- [ ] Battle Tower, Factory, Castle, Arcade e Hall: mapas, regras, times, UI, progressão de sequência, pontos e recompensas; adaptar motor com testes e aprovação de escopo.
- [ ] Underground, Super Contests, Pokétch, Day Care, Great Marsh, Game Corner/atividades compatíveis, lojas especiais, revanches, missões e colecionáveis; respeitar limitações reais do motor.
- [ ] Separar atividade opcional de história; tratar desistência, perda, retorno ao save normal e recuperação após falha.
- Aceite: cada atividade prevista tem entrada, ciclo jogável, saída e persistência; nenhuma lista meramente documental conta como concluída.

### SN23 — Polimento, tradução e recursos (P1; transversal)

- [ ] Revisar nomes, placas, diálogos e menus PT-BR, fonte/acentuação, sprites Lucas/Dawn/Barry/Rowan/líderes, alinhamento e escala regional.
- [ ] Revisar tiles pretos, árvores, layers, colisões, transições, câmeras, performance em mapas grandes e dispositivos Android.
- [ ] Auditar 46 chaves musicais históricas, nomes e arquivos reais, fallback, BGM cidades/rotas/batalhas; testar transição, retorno e ouvir reprodução em QA, não alegar áudio por mera chamada.
- [ ] Town Map, Pokédex, Trainer Card, HUD, indicador de versão com SHA/data/hora, lista QA separada.
- Aceite: screenshots/recibos das áreas, ausência de crashes e erros de arquivo, licença/crédito de cada recurso distribuível.

### SN24 — QA integral Windows e Android (P0; SN01–23)

- [ ] Reusar auditor de aceite S31/CH20 e ampliar os 44 casos históricos para a região inteira; reconciliar antigos casos, não apagá-los. Separar teste offline, compile-only, runtime automatizado, sessão real de gameplay e QA humana.
- [ ] Windows: instalação limpa e upgrade, Novo Jogo, três iniciais, campanha completa, oito HMs, liga, pós-game, quatro pares de viagem, blackout, save/reload.
- [ ] Android: JoiPlay e plugin RPG Maker reais em dispositivo/emulador compatível; repetir jornada, testar toque, controles, desempenho, áudio, resume, crash/retomada e updater incremental.
- [ ] Migrações de saves reais de teste: antes/depois de cada gate, em mapas de Sinnoh e outras regiões, times/PC/bolsa/dex/badges/esmeraldas/flags; verificação de idempotência.
- [ ] Testes de regressão das outras regiões e integridade de Game.exe, Data, Plugins e PBS; verificação do ZIP, CRC, SHA, inventário, patch aplicado e estado final byte a byte.
- Aceite: recibos independentes por plataforma e SHA, falhas zero, direitos aprovados. Se não existir dispositivo/runner, BLOCKED_ENV; não substituir por mock ou marcar 100%.

### SN25 — Publicação estável, portal e documentação (P0; SN24)

- [ ] Gerar manifesto aprovado BLUE_SINNOH_SHARED_V1, pacote revisado, mapa simbólico, pontos de início/chegada/agente, hashes de base e overlay. Promover somente usando fluxo aprovado existente; nunca copiar candidate.json e forçar flags.
- [ ] Publicar Windows e Android multiregion a partir da mesma revisão funcional de main; não usar o piloto separado. Checar releases, hashes, manifestos, updater e link Blue-Story.exe; oferecer versão pinada e link geral.
- [ ] Atualizar README, docs/SINNOH_PROGRESSO.md, manifestos de expansão/progresso, portal Sinnoh e issue #318 com estados comprovados. Registrar notas de versão, mapa de migração, direitos, limites e links de download.
- [ ] Revalidar pós-merge e pós-publicação; se falha, retirar/invalidar release insegura conforme política, corrigir e gerar novo par. Não anunciar 100% antes de todos os gates.
- Aceite: pacote estável instalado, testado e baixável, revisão comum, saves protegidos, nenhum blocker P0/P1 sem decisão formal do proprietário.

## 7. Testes e evidências (rotina por PR)

Execute primeiro os testes tocados; depois as suítes compartilhadas. Exemplos reais de testes encontrados nos workflows/repositório:

```bash
python -m unittest discover -s tests -p 'test_sinnoh_shared_install.py' -v
python -m unittest discover -s tests -p 'test_blue_story_sinnoh_menu.py' -v
python -m unittest discover -s tests -p 'test_sinnoh_j12e_experimental_installer.py' -v
python -m unittest discover -s tests -p 'test_sinnoh_expansion_f03.py' -v
python -m unittest discover -s tests -p 'test_android_multiregion.py' -v
python -m py_compile scripts/android/package.py scripts/android/update_client.py scripts/android/publish_updates.py
ruby tests/region_travel_runtime.rb
ruby tests/sinnoh_shared_events_runtime.rb
ruby tests/region_start_android_no_json_runtime.rb
git diff --check
```

Verifique se os testes permanecem presentes/compatíveis com a main atual. Reutilize a versão Ruby/Python e dependências dos workflows, e execute as suites completas exigidas. Adicione testes de regressão para a causa, não apenas para a mensagem do erro. CI verde é necessária mas não suficiente. O job sinnoh-shared-world-candidate do workflow Windows encontrado tem condição específica de branch sinnoh-shared-blue-story e PR interno; para novas branches, ajustar gatilho de modo explícito e seguro ou executar equivalente em runner privado autorizado. Não interpretar job ignorado como aprovação, nem expor segredos em PR externo.

```bash
gh pr checks NUMERO_DO_PR --watch
gh run list --commit SHA_DA_HEAD
gh run view ID_DA_EXECUCAO
gh run view ID_DA_EXECUCAO --job ID_DO_JOB --log-failed
gh run view ID_DA_EXECUCAO --job ID_DO_JOB --log
```

Os tokens NUMERO_DO_PR, SHA_DA_HEAD, ID_DA_EXECUCAO e ID_DO_JOB são placeholders. Conferir HEAD/base/merge e runs associados. Exigir todos os checks obrigatórios da revisão atual, não um número fixo de workflows históricos. Reexecutar somente erros transitórios após investigação; corrigir causa de falha funcional. Não fazer merge com testes quebrados ou em execução.

### Recibo mínimo por gate

Gravar JSON/MD pequeno e sanitizado (sem dados privados), usando manifestos existentes quando possível:

```json
{
  "stage": "SNxx",
  "head_sha": "sha-real",
  "base_sha": "sha-real",
  "platform": "windows|android|offline",
  "evidence_type": "static|fixture|compile_only|native_runtime|real_playthrough",
  "status": "PENDING|BLOCKED_ENV|FAILED|PASSED",
  "test_cases": [],
  "source_hashes": {},
  "mapids_before_after": {},
  "paths_forward_reverse": [],
  "negative_cases": [],
  "save_reload": null,
  "workflow_run_ids": [],
  "artifact_sha256": null,
  "remaining_blockers": []
}
```

Nunca preencher PASSED por inferência. Para eventos: MapID simbólico e real, posição, estado antes/depois, resultado da batalha e quantidade de item, retorno e reload. Para movimento: caminho cardinal/transferências, componente e gates de HM, não screenshot isolado. Para CI: link de run/job, SHA, marcadores verificados e exit code. Não publicar saves nem arquivos privados de engine/recursos. Se necessário, usar recibo local com hashes e logs sanitizados.

## 8. Integração e release Windows

1. Em runner autorizado e base limpa/atualizada, executar fluxo de instalação e preparação da seção 4; conferir baseline compartilhada e direitos.
2. Conferir contrato [sinnoh_shared.py](../scripts/regions/sinnoh_shared.py): aprovações map_ids, asset_rights, connected_world, windows_travel; Android acrescenta joiplay_travel e android_distribution. Aprovação deve refletir prova real. O perfil local/QA é distinto do manifesto estável.
3. O instalador busca .blue-work/sinnoh-shared/manifest.json e o overlay autorizado após integrar outras regiões. Reusar scripts/install_game.py, scripts/launch_game.py, Bootstrap.cs e RegionStart/Travel, sem substituir Game.ini, mkxp.json, Scripts.rxdata do jogo principal por dados de piloto. Validar overlay merge e rollback.
4. Construir Blue-Story.exe no Windows com o processo existente, após testes:

```powershell
python scripts/windows/build.py
Get-FileHash dist/Blue-Story.exe -Algorithm SHA256
```

5. Reusar [workflow Blue-Story Windows](../.github/workflows/blue-story-windows.yml) e seu workflow_dispatch quando aplicável. Descobrir workflow de release funcional principal e entradas em main, sem presumir que build de launcher sozinho publique o jogo. Conferir tag geral blue-story-windows e release pinada; não clobber manual de asset estável antes do aceite.
6. Verificar download efetivo de Blue-Story.exe da release aprovada, SHA256, execução, identidade de versão no menu, instalação limpa e atualização. Link geral: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/blue-story-windows/Blue-Story.exe (não implica que a versão atual já inclua Sinnoh completa).
7. Não publicar ZIP do donor ou saves em Git; se licença exige recurso fornecido pelo usuário, manter fluxo local, registrar limitação e não alegar distribuição integral.

## 9. Integração e release Android / JoiPlay

### Candidato QA (comandos existentes)

```bash
python scripts/android/package.py --channel multiregion --sinnoh-qa --game-dir .blue-work/sinnoh-shared-qa/game --request-compile
# Executar Game.exe da cópia descartável para compilar; conferir recibo.
python scripts/android/package.py --channel multiregion --sinnoh-qa --game-dir .blue-work/sinnoh-shared-qa/game
```

Instalar JoiPlay e plugin RPG Maker do site oficial; extrair ZIP completo em pasta privada de QA, adicionar Game.exe no JoiPlay e testar. Usar perfil de saves separado. ZIP QA não pode passar pelo publicador estável; não remover --sinnoh-qa de uma cópia ainda não aprovada para burlar o gate.

### Distribuição estável

Somente depois de map_ids, asset_rights, connected_world, windows_travel, joiplay_travel e android_distribution verdadeiros com evidência, preparar instalação compartilhada estável e compilada em game/ (não piloto). Comandos de referência, preencher SHA, ZIP e manifestos reais e confirmar --help/CI da revisão:

```bash
python scripts/android/package.py --help
python scripts/android/publish_updates.py --help
python scripts/android/package.py --channel multiregion --game-dir game --revision SHA_FUNCIONAL --output CAMINHO_ZIP_ESTAVEL
python scripts/android/publish_updates.py --channel multiregion --full-zip CAMINHO_ZIP_ESTAVEL --previous-manifest MANIFESTO_ANTERIOR
```

O publicador aceita --previous-manifest repetido; obter os manifestos publicados reais dos builds suportados. Usar workflow oficial que publica releases android-multiregion-* e verificar pelo inventário/tag, não inventar versão numérica nem nome de asset. Testar hash SHA-256/CRC e patch do build anterior (e baselines suportadas) até a revisão comum, comparar instalação final com ZIP integral, impedir perda de Sinnoh após upgrade.

No Termux (se usuário optar por esse método), instalar Python pelo repositório oficial, conceder acesso à pasta escolhida e usar o update_client.py/atualizador oficial da distribuição com --help. Exemplo para versão atual do CLI: `python update_client.py --game-dir "/caminho/real/do/jogo" --update`. Confirmar canal pelo manifesto instalado; não usar --full por padrão, não criar backup integral do jogo, apenas transação/rollback dos arquivos alterados e proteção de saves. Atualizar a partir de pelo menos duas baselines quando possível, inclusive jogo já integrado com Sinnoh; simular interrupção, hash inválido, espaço insuficiente e rede indisponível. Não exigir reinstalação manual completa salvo recuperação explicitamente necessária.

## 10. Matriz final de aceite

| Gate | Evidência obrigatória |
|---|---|
| Mapa | 100% dos destinos do catálogo de escopo acessíveis no estágio correto e retorno válido |
| História | Todos os checkpoints aprovados; nenhum teleporte QA para completar |
| Iniciais e rival | 3 iniciais, ambos protagonistas, Barry e derrota/retry |
| Badges/HMs | 8/8 badges + esmeraldas únicas; 8/8 movimentos e negativos regionais |
| Galáctica | Windworks, Eterna, Psyduck, três lagos, HQ, Cyrus, Spear Pillar, Distortion e Giratina |
| Liga | Victory Road, 4 Elite Four, Cynthia, Hall of Fame e pós-game |
| Conteúdo opcional | Inventário com encontros, treinadores, serviços, lendários, Frontier e atividades |
| Save | Reload e migração, antes/depois de gates, sem perda de outros progressos |
| Viagem | Agente Twinleaf, 4 pares de ida e volta; origem inicial preservada, time/PC/bolsa corretos |
| Windows | Sessão real Game.exe, instalação limpa e atualização |
| Android | Sessão real JoiPlay, instalação limpa e atualização incremental |
| CI | Todos checks obrigatórios aprovados contra main atual e após merge |
| Release | Mesmo SHA funcional em ambas, assets, hashes, manifestos e patches conferidos |
| Direitos | Fontes e permissões de distribuição revisadas; créditos atualizados |

## 11. Estratégia de commits e economia de contexto do Codex

- Use a matriz como fila de execução: PENDING → IN_PROGRESS → IMPLEMENTED → VERIFIED_OFFLINE → VERIFIED_NATIVE_WINDOWS → VERIFIED_NATIVE_ANDROID → PUBLISHED. BLOCKED_ENV e FAILED não contam como concluído; registro por escopo, não por volume de código.
- Leia apenas arquivos relevantes ao gate atual, use rg e git diff, reaproveite fixtures; não ler toda árvore a cada rodada. Agrupe consultas de runs/jobs e evitar polling infinito. Para problemas geométricos, compute componentes uma vez por mapa/hash e reexecute somente os afetados, com teste global final.
- Cada PR: título SNxx, SHA base, mudança funcional, testes positivos/negativos, evidências, riscos, estado de QA, arquivos alterados, próximo gate. Não misturar refactor geral com correção de mapa. Não anexar dados privados.
- Atualize [issue #318](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/318) e manifesto a cada gate de história; no restante, criar/usar issue de execução apropriada e relacionar a #318. Não fechar issue antiga por mera implementação do compilador.
- Merge só após testes obrigatórios aprovados, sincronização com main e autorização de direitos. Publicar revisão intermediária somente se for candidata estável dentro do escopo explícito e não remover/ativar indevidamente conteúdo; não promover QA ao canal público. Ao finalizar SN25, publicar ambos os instaladores.
- Relatório de retomada curto: etapa, HEAD, base, checks, recibos, blocker e próximo comando. Não reiniciar fases já comprovadas.

### Prompt inicial para Codex (copiar)

> Leia docs/SINNOH_ROADMAP_100_JOGAVEL.md na main e execute a primeira etapa sem prova atual, começando pela reconciliação SN01. Consulte a issue #318, PRs #338/#339 e os manifestos existentes. Priorize alterações de gameplay no GitHub e o primeiro corredor físico bloqueado. Reutilize as fontes autorizadas e hashes fixados no roadmap; não copie recursos privados nem execute donor. Preserve saves, MapIDs, outras regiões, Gary e balanceamento. Valide positivos/negativos, CI contra a main e recibos reais; não confunda fixture ou compilação com gameplay. Use o Blue-Story compartilhado, não piloto. Avance em PRs pequenos até campanha, Liga e pós-game; execute QA Windows e JoiPlay real, publique ambos na mesma revisão funcional somente após gates e direitos, valide assets/hashes/patches e atualize issue e documentação. Se depender de dispositivo/fonte indisponível, marque BLOCKED_ENV e entregue a ação exata necessária. Não invente aprovação, não desative testes e não prometa execução em segundo plano.

## 12. Limites deste documento

Esta análise foi feita com metadados, conteúdo do GitHub e registros existentes, sem baixar os ZIPs, executar Game.exe/JoiPlay ou testar pessoalmente o jogo. Não implementa as 25 etapas nem publica binários. Os links de fonte foram confirmados no código; sua disponibilidade e direitos precisam ser revalidados durante a execução. A sequência e o escopo do pós-game são proposta de implementação; adaptações autorais relevantes exigem aceite explícito do proprietário. Em caso de divergência com a main futura, prevalece a evidência real da revisão e este roadmap deve ser atualizado sem enfraquecer os gates.
