# Sinnoh — acompanhamento de progresso

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Última atualização:** 13/11/2026  
**Fonte de verdade:** [data/regions/sinnoh-progress.json](../data/regions/sinnoh-progress.json).  
**Critério:** esta página separa entregáveis de código/documentação de fases que já rodam no jogo. **Barra cheia de preparação NÃO significa Sinnoh jogável.**

## Barra A — desenvolvimento aqui no GitHub

```text
██████░░░░░░░░░░░░░░░░░░  8/32 (25%)
```

- **Concluídas:** 8 entregas de preparação verificáveis no repositório.
- **Parciais:** 7 (não contam como concluídas até atingirem o próprio critério).
- **Pendentes:** 17.
- **Total:** 32 entregas no inventário [JSON](../data/regions/sinnoh-progress.json).
- **Restam 24 para a barra de desenvolvimento** (inclui parciais).

## Subetapas do S07 — remapeamento seguro (parcial)

```text
████████████████░░░░░░░░  6/9 (67% das subetapas de preparação)
```

A ferramenta de remapeamento já verifica IDs reais de origem, símbolos, hashes, colisões, planos anteriores e produz **propostas** de transferência entre os IDs candidatos. Veja [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py), [testes](../tests/test_sinnoh_remap.py) e o [relatório da Fase 01](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md).

As **três subetapas restantes** exigem baseline/reservas de todas as regiões, conversão dos dados reais da fonte autorizada e teste nativo isolado. Por isso **S07 continua parcial**, a Barra A permanece em **8/32** e nenhuma das barras de jogabilidade sobe. Os detalhes R01–R09 estão em [sinnoh-progress.json](../data/regions/sinnoh-progress.json).

### Conversão de geometria — código disponível, mapas reais pendentes

O conversor [convert_sinnoh_geometry.py](../scripts/regions/convert_sinnoh_geometry.py) e seus [6 testes com mapas sintéticos](../tests/test_sinnoh_geometry_converter.py) já produzem prévias de terreno, tilesets e cópias dos índices de mapa **sem eventos/scripts, encontros ou músicas do jogo doador**, com dry-run e stage opcional em `.blue-work`. Consulte [Fase 01 — prévia de geometria](SINNOH_FASE_01_PREVIA_GEOMETRIA.md).

**Limite:** nenhum ZIP real de Sinnoh foi convertido e ainda não existem portais, NPCs, saves ou mapas jogáveis novos. Por isso **R08 segue incompleto**, S07 segue **6/9**, a Barra A permanece **8/32 (25%)** e as barras técnicas/jogáveis continuam **0/13**.

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

**Faltam 2 subetapas:** compilar os PBS e conferir o sprite/batalhas na cópia experimental; testar níveis efetivos, vitória/derrota e saves em Game.exe/JoiPlay. O nível 5 nos PBS é **somente o nível-base técnico**, não o nível fixo exibido ao jogador. Como a integração real não foi verificada, o item **I07 da introdução continua pendente**, a preparação geral permanece **8/32** e nenhuma barra de fases jogáveis sobe.

**CI isolada de Sinnoh:** [execução 43535200301](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43535200301) aprovou **82 testes Python** e o harness Ruby `SINNOH_STORY_RUNTIME_GUARDS_OK`. A suíte geral continua sujeita a uma falha separada de integridade do piloto de Johto (`test_ruby_guard_only_accepts_signed_local_pilot`), que não deve ser confundida com aprovação de gameplay de Sinnoh.

**Atenção:** existe um piloto legado de Sinnoh com MapIDs 800–805, na faixa 600–999 protegida no plano de Johto. Os dois modelos precisam ser conciliados antes de uma integração compartilhada; não mesclar os mapas automaticamente.

## Conciliação do piloto e QA de Barry — nova etapa

```text
████████████░░░░░░░░░░░░  3/6 (50% do subtrabalho de compatibilidade e pré-verificação)
```

A auditoria [audit_sinnoh_pilot_compat.py](../scripts/regions/audit_sinnoh_pilot_compat.py) identifica os MapIDs **800–805** do piloto legado de Sinnoh dentro da faixa **600–999 protegida para Johto**. Ela distingue uma cópia experimental **totalmente independente** de uma instalação **multi-regional**: no segundo cenário, não permite mesclar esses IDs automaticamente. Também registra que [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb) oferece iniciais pelo diálogo, diferentemente das **três Poké Bolas físicas** do [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb).

O [preflight_sinnoh_barry_qa.py](../scripts/regions/preflight_sinnoh_barry_qa.py) confere os dois PBS de Barry **já copiados para uma instalação QA separada**, a partir dos hashes do draft, e registra o sprite candidato, o executável e a ausência de marcador prematuro. **Não compila PBS e não executa a batalha**, logo o trabalho permanece parcial. Veja [guia de reconciliação e QA](SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md).

Faltam: auditoria física das reservas, montagem do piloto novo com fonte autorizada e testes reais Windows/Android. O avanço de **3/6** é apenas desta etapa de código; desenvolvimento geral **8/32**, fases técnicas/jogáveis/QA **0/13**.

## Novo piloto — montagem privada do overlay (preparação parcial)

```text
████████████░░░░░░░░░░░░  3/6 (50% das subetapas de integração)
```

O novo montador [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py) reúne em **.blue-work** o stage de geometria, os **24 eventos próprios do Blue em nove mapas** (incluindo **três Poké Bolas físicas** e 16 warps), as **três versões PBS de Barry** e o plugin autoral `SinnohPilot.rb`. Confere transações, hashes, MapInfos/Tilesets e **todos os IDs presentes na geometria**, além de recompilar os eventos e verificar byte a byte a saída. Não copia o piloto legado, `System.rxdata`, `Scripts.rxdata`, `Game.exe` nem saves.

[Documentação e comandos do piloto](SINNOH_FASE_02_PACOTE_INTEGRACAO_QA.md) | [Testes sintéticos de integração](../tests/test_sinnoh_pilot_bundle.py).

**Restam 3 subetapas locais:** auditar a fonte autorizada e os IDs reservados, montar/compilar na cópia real do Game.exe com perfil isolado, testar Windows/Android e a batalha com Barry. O montador fica em **dry-run por padrão**, escreve apenas em pasta nova de `.blue-work` mediante `--publish` e **não cria marcador de batalha**. Portanto a barra geral continua **8/32 (25%)**, as fases técnicas/jogáveis/QA **0/13**, e a compatibilidade do piloto legado permanece **3/6**.

**Validação atualizada de código:** a [CI isolada de Sinnoh, execução 43538522476](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43538522476), aprovou **119 testes Python** e os testes Ruby de introdução e sondagem do Barry em ambiente sintético. A regressão geral permanece com a falha preexistente de Johto `test_ruby_guard_only_accepts_signed_local_pilot` (`[601, 13, 13]` vs `nil`), sem representar falha do montador de Sinnoh. Teste offline não prova Game.exe jogável.

## Instalação experimental com saves separados — preparada em código

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas da instalação QA)
```

O [instalador QA](../scripts/regions/install_sinnoh_qa_copy.py) monta **uma cópia nova em `.blue-work`** a partir de um overlay Sinnoh já auditado. Ele exclui saves da base, atribui identificadores exclusivos em `mkxp.json` e `Game.ini`, prepara o `System.rxdata` para o quarto do jogador e inclui um bootstrap para a compilação das três versões PBS de Barry. Na **primeira execução local do Game.exe QA**, o bootstrap tenta compilar e registra erros ou a prova local da compilação; **não libera o marcador de batalha do Barry**.

O plugin [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) exige a prova de compilação, o perfil Sinnoh e SHA-256 dos arquivos protegidos antes de preparar um novo jogo. A falta de prova bloqueia o início em vez de cair silenciosamente na campanha Decades. Os [testes Python](../tests/test_sinnoh_qa_install.py) e [testes Ruby](../tests/sinnoh_qa_start_runtime.rb) cobrem esse contrato com instalações fictícias. [Guia completo para Codex/Windows](SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md).

**Restam 3 subetapas reais:** auditar e montar a cópia com os mapas autorizados, compilar/verificar o PBS e os caminhos efetivos de saves no Game.exe Windows, e testar Twinleaf/Barry/saves/Android sem regressões. Por isso a instalação QA ainda **não foi executada com assets reais**, o item do piloto continua **parcial**, o desenvolvimento geral permanece **8/32 (25%)** e as barras de aceite **0/13**. Nenhum save principal foi modificado.

**CI isolada:** [execução de Sinnoh](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43539553514) aprovou **134 testes Python**, sintaxe Ruby e os harnesses de abertura/Barry, inclusive `SINNOH_QA_START_SAVE_AND_PBS_GUARDS_OK`. A suíte geral possui uma falha separada anterior do piloto de Johto; isso não equivale a QA Windows/Android para Sinnoh.

## Validação automática pós-compilação do piloto — preparada em código

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas da sondagem nativa)
```

O módulo [SinnohQAProbe.rb](../scripts/regions/SinnohQAProbe.rb), incluído apenas na cópia QA, está pronto para executar **após o `Compiler.main` no Game.exe experimental**. Ele confere `GameData::Trainer` nas três versões de Barry e carrega os nove mapas da introdução para auditar **24 eventos, 16 portais, três Poké Bolas físicas, cinco handlers Blue, nomes, sprites de eventos, gatilhos e coordenadas**. A prova estrutural é registrada em `Data/blue-sinnoh-qa-engine-check.json`, separada do token de compilação. Falhas impedem a liberação de `Novo Jogo` e nenhum script cria `blue-sinnoh-rival-ready.txt`.

O [verificador Python](../scripts/regions/install_sinnoh_qa_copy.py) exige hashes de **todos** os mapas preparados e confere o novo relatório. O [plugin de inicialização QA](../scripts/regions/SinnohQAStart.rb) não autoriza `Novo Jogo` com token sozinho. [Testes Python](../tests/test_sinnoh_qa_install.py), [testes Ruby da sondagem](../tests/sinnoh_qa_engine_probe_runtime.rb) e [início Ruby](../tests/sinnoh_qa_start_runtime.rb) usam só arquivos e equipes **sintéticos**. Detalhes no [guia de validação pós-compilação](SINNOH_FASE_02_VALIDACAO_NATIVA_PBS_EVENTOS.md).

**Restam 3 subetapas reais:** rodar essa sondagem no Game.exe com mapas autorizados, observar batalha/nível efetivo 70%/90% e saves Windows, e validar o Android/JoiPlay com regressões. **Nenhuma dessas três ocorreu nesta conversa.** Portanto o desenvolvimento geral permanece **8/32 (25%)**, as 13 fases técnicas/jogáveis/nativas permanecem **0/13** e a instalação QA continua **4/7**.

**CI isolada comprovada:** [execução 43540748918](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43540748918) — **138 testes Python aprovados** e harnesses Ruby de prova de início, eventos e Barry aprovados. A conclusão **geral** daquela workflow foi falha em testes fora da suíte isolada; não confundir sucesso isolado com pipeline totalmente verde ou gameplay nativo.

## Batalhas e playtest nativo — preparado, execução real pendente

```text
██████████████░░░░░░░░░░  4/7 (57% das subetapas de instrumentação e QA)
```

A introdução autoral [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) agora permite **tentar a batalha com Barry só na cópia QA isolada**, após [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) validar provas de compilação, eventos e hashes dos mapas/PBS. Antes disso, Barry permanece bloqueado; o marcador de publicação `blue-sinnoh-rival-ready.txt` **não é criado nem necessário para o teste experimental**. Resultados nulos não avançam o save; as batalhas de teste aceitam vitória ou derrota (`canLose`), preservando Decades/Kanto/Johto/Hoenn.

O [auditor de playtest](../scripts/regions/audit_sinnoh_playtest.py) prepara um roteiro **local de 44 casos**: três Poké Bolas, 12 batalhas (3 iniciais × Normal/Master × vitória/derrota), 16 warps, cinco NPCs, três verificações de save/reload, quatro regressões e Android/JoiPlay. Ele confronta os **níveis observados** com a regra real de código Blue (70%/90%) e exige capturas/logs locais com SHA-256. O resultado **não aprova o jogo automaticamente**, nem prova que uma pessoa executou os testes — as evidências ainda exigem revisão humana. Veja [guia de execução Windows/Android](SINNOH_FASE_02_PLAYTEST_REAL_BARRY_SAVES.md) e [testes do auditor](../tests/test_sinnoh_playtest_audit.py).

**Pendências reais T05–T07:** executar Game.exe QA sobre mapas legítimos e auditar os 12 combates, fazer os testes de portais/saves/regressões e validar Android/JoiPlay. Nenhuma evidência real foi fornecida nesta conversa; o progresso geral permanece **8/32 (25%)** e a aprovação das 13 fases continua **0/13**.

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
| Parcial | S07 | Dry-run, staging, rollback e proposta segura de remapeamento (6/9 subetapas) | [transação](../scripts/regions/sinnoh_staging_transaction.py), [remapeamento](../scripts/regions/plan_sinnoh_remap.py), [testes](../tests/test_sinnoh_remap.py) |
| Parcial | S08 | Integridade de recursos gráficos e mapas | [auditoria RXDATA](../scripts/regions/audit_sinnoh_rxdata.py) |
| Concluído | S09 | Botão Testar Sinnoh sem quebrar saves | [menu](../scripts/battle_polish/TitleKanto.rb) |
| Parcial | S13 | Estrutura autoral de Rowan, Barry e Pokédex | [Ruby](../scripts/regions/SinnohPilot.rb), [MD](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md) |
| Parcial | S14 | Três iniciais em Poké Bolas físicas, com save isolado | [template](../data/regions/sinnoh-twinleaf-events.json), [compilador](../scripts/regions/build_sinnoh_twinleaf_events.py) |
| Parcial | S24 | Catálogo musical planejado | [estudo](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) |
| Parcial | S30 | Testes automatizados (escopo parcial) | [testes de grafo](../tests/test_sinnoh_graph.py) |
| Parcial | S31 | Plano de aceitação Windows/JoiPlay | [plano](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) |
| Concluído | S32 | Fila de pendências Codex | [backlog](SINNOH_CODEX_PENDENCIAS.md) |

**As demais entregas de S10–S29 não listadas acima seguem pendentes** (exceto S13 e S14, agora parciais); veja a lista completa, com os 32 IDs, no [registro JSON](../data/regions/sinnoh-progress.json). A ordem de implementação é independente das fases integradas: uma API pode estar pronta mas não haver mapa-fonte para aprovar uma fase.

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
