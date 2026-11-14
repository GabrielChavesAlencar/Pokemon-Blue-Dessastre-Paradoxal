# Sinnoh — divisão ChatGPT × Codex, execução local e pendências

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Criado:** 13/11/2026  
**Status:** trabalhos de GitHub/infraestrutura preparados; **fonte de mapas, integração real e prova nativa pendentes**.  
**Documentos vinculantes:** [análise das fontes](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md), [13 fases de implementação](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md), [plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md), [procedimento Johto](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) e [procedimento Hoenn](HOENN_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md).

## 1. Como dividir daqui para frente

**Regra automática de trabalho em cada novo pedido:**

1. **ChatGPT faz diretamente na main** tudo que pode ser realizado com repositório disponível: análise de documentos, arquivos de configuração/documentação, scripts próprios, testes estáticos/unitários, adaptação do menu, validações de GitHub Actions e correção de falhas reproduzíveis por código/fixture. Nunca deixar essas atividades como "Codex fará" se for possível publicá-las e verificá-las agora.
2. **Codex recebe neste MD somente a parte realmente dependente do ambiente local**: arquivos externos de Sinnoh, extração local, cópia de `game/` (Decades não está no Git), execução do RPG Maker XP / Game.exe, áudio/graphics reais, verificação dos saves, auditoria de colisões físicas de MapIDs, compilação PBS e teste em Windows/JoiPlay.
3. **Cada item deve passar por sua checagem de entrada:** fontes reais e direitos, CLI executável, hashes, backup, permissões para escrever no destino, baseline sem regressões. Se um bloqueio persistir, registrar evidência e **não falsificar nem "simular sucesso"**.
4. **O Codex não deve duplicar um script já feito no ChatGPT.** Primeiro ler a versão mais recente da main e executar os testes existentes. Se houver regressão introduzida, corrigir a causa preservando as alterações paralelas de Johto/Hoenn.
5. **Somente o trabalho concluído e verificável deve ser publicado na main** (sem force push); guardar mapas, sprites, áudio não autorizados, saves e binários na cópia local em `.blue-work/` e `game/`. Registrar commit, testes e duas barras separadas.

## 2. Trabalhos já executados aqui (não pedir ao Codex para refazer)

| Entregável | Local | O que prova | Limite |
|---|---|---|---|
| Estudo e ranking de fontes | [`SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md`](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) | Referência Platinum/Ancient Platinum, música, escopo e licenças pendentes | Não comprova fonte local/permite copiar material |
| Plano técnico com 13 fases | [`SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md`](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) | Passos, eventos, mapas, testes e prioridades de não regressão | Nenhum mapa Sinnoh importado |
| Botão do menu **Testar Sinnoh** | [`scripts/battle_polish/TitleKanto.rb`](../scripts/battle_polish/TitleKanto.rb) | Comando após Testar Kanto e Johto, preservando índices de Continue/New Game, e aviso seguro sem piloto | Falta instalar plugin na cópia local e validar a janela Game.exe |
| Contrato de menu/testes | [`tests/title_kanto_runtime.rb`](../tests/title_kanto_runtime.rb) e [`tests/test_title_kanto.py`](../tests/test_title_kanto.py) | Ordem, dispatch, comportamento sem launcher, slots, Mystery Gift, isolamento | Testes não provam Windows nativo nem Android |
| Registro regional existente | [`site/public/data/regions.json`](../site/public/data/regions.json) | Sinnoh `planned`, oito insígnias, HMs de Platinum, Liga → Hoenn/Unova | Não há mapas/portais Sinnoh instalados |
| Auditor de fonte **somente leitura** | [`scripts/regions/audit_sinnoh_source.py`](../scripts/regions/audit_sinnoh_source.py) | Verifica ZIP/pasta de fonte, MapInfos/Tilesets, IDs, colisões físicas quando `game/Data` existe, e contrato do registro/menu | Metadados não equivalem a conferir conteúdo de cada `.rxdata` |
| Testes do auditor (fixtures sintéticas) | [`tests/test_sinnoh_source_preflight.py`](../tests/test_sinnoh_source_preflight.py) | Valida isolamento, rejeição de ZIP com traversal/IDs duplicados/múltiplos projetos e falta segura do jogo local | Não é teste com Ancient Platinum real |
| Manifesto conservador | [`data/regions/sinnoh-source.json`](../data/regions/sinnoh-source.json) | Identifica fonte prioritária, bloqueios, entregáveis futuros e fase 00 parcial | Não habilita importação nem direitos de assets |

**Estado atual honesto:** **Barra 1 — 0/13 fases técnicas completamente aprovadas; Barra 2 — 0/13 fases de gameplay integralmente aprovadas.** A etapa 00 ganhou ferramentas, mas depende da fonte e do `game/` locais; a etapa 02 ganhou o botão, mas **não** o piloto com mapas reais.

**Checklist estruturado disponível:** [data/regions/sinnoh-coverage.json](../data/regions/sinnoh-coverage.json) lista **91 áreas simbólicas e 51 marcos de evento**, distribuídos nas fases 03–10, com IDs de origem/destino vazios e todas as verificações em `false`. O Codex deve usar esse inventário como **mínimo de cobertura**, ampliar com interiores, NPCs, itens e passagens reais descobertos na fonte autorizada, e **não preencher MapIDs sem auditoria**. [tests/test_sinnoh_coverage.py](../tests/test_sinnoh_coverage.py) impede marcar a checklist como importada antes das provas.

### Complemento já implementado diretamente no GitHub — não refazer no Codex

- [Auditoria profunda de RXDATA](../scripts/regions/audit_sinnoh_rxdata.py): lê a fonte local **ZIP ou pasta RMXP** em modo totalmente inerte, sem extração. Identifica arquivos `Map*.rxdata` reais, `MapInfos`, `Tilesets`, hashes, dimensões, eventos, scripts não executados, transferências estáticas/variáveis, gráficos ausentes, mapas órfãos, referências inválidas e colisões físicas de IDs.
- [Testes da auditoria profunda](../tests/test_sinnoh_rxdata_audit.py): fixtures próprias de Ruby Marshal, ZIP não extraído, grafo de transferências, gráficos, scripts, corrupção e tileset ausente.
- [Estudo conservador de capacidade de MapIDs](../scripts/regions/plan_sinnoh_capacity.py): usa auditoria RXDATA real + instalação local para contar **somente** espaços provisoriamente desocupados. Protege explicitamente **Johto 600–999**, **não presume suporte a IDs ≥1000**, não ocupa espaço que pode estar reservado a Hoenn e **não gera mapping**.
- [Testes do estudo de capacidade](../tests/test_sinnoh_capacity.py): verifica que mapeamento continua vazio, que 600–999 permanecem intocados, que não há reserva de IDs sem `game/Data` e que insuficiência de espaço é reportada, não contornada.
- **Essas ferramentas já estão codificadas. O Codex deve executá-las com a fonte e o `game/` reais; não reimplementá-las.** A aceitação de C00 e C01 exige arquivos locais, proveniência e testes nativos quando aplicável.

**Comandos adicionais para C00/C01, após obter a fonte legítima:**

```powershell
python scripts/regions/audit_sinnoh_rxdata.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/rxdata-report.json
python scripts/regions/plan_sinnoh_capacity.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/capacity.json
python -m unittest discover -s tests -p "test_sinnoh_rxdata_audit.py" -v
python -m unittest discover -s tests -p "test_sinnoh_capacity.py" -v
```

**Leitura obrigatória:** `capacity.json` é uma fotografia de capacidade, não mapa de IDs autorizados. O Codex deverá conferir também reservas de Hoenn e Johto que não estejam fisicamente instaladas e demonstrar compatibilidade de IDs ≥1000 antes de atribuir IDs persistentes. O auditor RXDATA não valida permissões de redistribuição, scripts dinâmicos/conditional calls nem prova caminhabilidade ou gameplay.

### Progresso e ferramentas novas — primeira etapa

- **Painel oficial:** [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md), gerado a partir dos 32 entregáveis enumerados em [data/regions/sinnoh-progress.json](../data/regions/sinnoh-progress.json). **Preparação 8/32 (25%); fase técnica 0/13; jogabilidade 0/13; aceite nativo 0/13.**
- **Grafo de mapas S06 (implementado aqui):** [graph_sinnoh_maps.py](../scripts/regions/graph_sinnoh_maps.py), com [testes](../tests/test_sinnoh_graph.py). Aceita mapas reais já auditados em ZIP/pasta; a opção `--start-map` exige o MapID de Twinleaf (ou outro ponto escolhido) **realmente confirmado**. IDs não encontrados e componentes desconectados são achados de auditoria, não prova de impossibilidade de viagem; eventos comuns/scripts dinâmicos precisam de revisão separada.
- **Staging transacional S07 (parcial):** [sinnoh_staging_transaction.py](../scripts/regions/sinnoh_staging_transaction.py) e [testes](../tests/test_sinnoh_staging_transaction.py). Disponibiliza operações Python `preview(project,label,files)`, `stage(project,label,files,expected_plan_sha256)` e `rollback(project,label,plan_sha256)`. O `stage` é **somente um diretório novo em `.blue-work/sinnoh-stage/`**; verifica SHA-256, não sobrescreve arquivos existentes, rejeita `Scripts.rxdata`/`System.rxdata`/`Plugins` e não grava em `game/`. **Não é importação para uma instalação jogável, nem faz remapeamento de IDs**. O Codex deve aproveitar esse módulo no futuro para artefatos **já convertidos/auditados**, sem tentar usar RXDATA original diretamente.
- **Comando do grafo somente quando a fonte real existir:**

```powershell
python scripts/regions/graph_sinnoh_maps.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/map-graph.json
python -m unittest discover -s tests -p "test_sinnoh_graph.py" -v
python -m unittest discover -s tests -p "test_sinnoh_staging_transaction.py" -v
```

**O que continua exclusivo de Codex/local:** verificar MapInfos/tilesets reais, direitos e uso de assets, MapIDs globais ocupados/reservados, conversão dos mapas e referências de eventos, instalação do piloto em `Game.exe`, áudio, saves e QA Windows/Android. O painel de preparação não autoriza elevar as barras de gameplay.

### Fase 01 — planejamento de remapeamento já concluído por código; integração real pendente

- **Não recriar o planejador:** [scripts/regions/plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py) recebe um relatório RXDATA inerte, `request` com MapIDs reais e hashes, opcionalmente `previous` para congelar os IDs dos saves e `reserved` para registrar IDs reservados de outras regiões. Nunca escolhe IDs sozinho nem autoriza instalar; rejeita destinos ocupados, Johto 600–999 e IDs ≥1000 sem teste.
- **Template de entrada deliberadamente vazio:** [sinnoh-remap-request.template.json](../data/regions/sinnoh-remap-request.template.json). Sem fonte, MapInfos, hashes e IDs reais ela **deve falhar**. Não colocar números falsos, nem mesmo para demonstração na main.
- **Testes unitários:** [tests/test_sinnoh_remap.py](../tests/test_sinnoh_remap.py). Checam colisões, alterações nos hashes, símbolos, transferências, duplicidade e continuidade de save mapping.
- **Procedimento completo da fase e comandos:** [SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md). O Codex deve ler esse MD antes de qualquer conversão.
- **Progresso:** [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md) — S07 **6/9 subetapas de preparação**, mas **parcial** no quadro 32 tarefas; barra A 8/32 (25%); técnicas/jogáveis/QA 0/13.

**Três entregas locais efetivas restantes no S07:**
1. **R07:** auditar a pasta `game/Data` e todas as reservas Kanto/Johto/Hoenn, inclusive mapas ainda não instalados, garantindo que a proposta não sobrescreva IDs de outras regiões.
2. **R08:** converter a fonte real e permitida em geometria, recursos e referências de mapa em staging isolado, adaptando eventos sem copiar scripts/RMXP de outra engine. Não copiar `MapInfos` global, `Scripts.rxdata`, `System.rxdata` nem arquivos de saves.
3. **R09:** montar o piloto com o primeiro mapa real de Twinleaf e validar `Game.exe` e JoiPlay, entrada/saída e save/load. **Não usar a aprovação dos testes Python como substituto dessa prova.**

**Linha de comando para a proposta somente leitura**, depois de executar `audit_sinnoh_rxdata.py` com o ZIP verdadeiro:

```powershell
python scripts/regions/plan_sinnoh_remap.py --audit .blue-work/sinnoh/rxdata-report.json --request .blue-work/sinnoh/remap-request.json --output .blue-work/sinnoh/remap-plan.json
python -m unittest discover -s tests -p "test_sinnoh_remap.py" -v
```

### Implementação de conversão de terreno (R08 — código de prévia preparado)

- **Já implementado aqui:** [scripts/regions/convert_sinnoh_geometry.py](../scripts/regions/convert_sinnoh_geometry.py), com [tests/test_sinnoh_geometry_converter.py](../tests/test_sinnoh_geometry_converter.py). O módulo audita fonte ZIP/pasta real e cópia `game/Data`; revalida o `plan_sha256` do remapeamento, confere hashes e gera em memória `MapNNN.rxdata` de **geometria somente**, índices MapInfos/Tilesets da **cópia**, tileset PNGs prefixados e relatório de hashes dos arquivos nativos.
- **Segurança garantida pelo código:** `@events={}`, `@encounter_list=[]`, BGM/BGS vazios, nenhum script doador executado, sem NPCs, batalhas ou portais copiados. A saída `--stage` requer SHA-256 de dry-run e grava **somente** na pasta ignorada `.blue-work/sinnoh-stage/`. Não instalar o stage no `game/`: ele não é jogável nem inclui os eventos necessários.
- **Guia operacional obrigatório:** [SINNOH_FASE_01_PREVIA_GEOMETRIA.md](SINNOH_FASE_01_PREVIA_GEOMETRIA.md), com exemplos Windows, limites de licença e provas de teste.
- **R08 permanece parcial** porque a fonte Sinnoh verdadeira, permissões, coordenadas de eventos, scripts autorais e QA de mapa não foram auditados. **Não refazer o conversor; use-o somente quando os assets locais reais estiverem disponíveis.**
- **Barras:** desenvolvimento 8/32 (25%); remapeamento S07 6/9 (67%); técnica, jogável e QA nativa continuam 0/13. Arquivo mestre: [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md).

### Fase 03 — Twinleaf, Rowan, Barry e iniciais: código feito, integrações locais restantes

**Já publicado no GitHub (NÃO reimplementar):**

- [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb): módulo `BlueSinnohPilot` com estado `blue_regions["sinnoh_pilot"]` que opera **somente** com `current == "SINNOH"`, mãe, Barry, Rowan/maleta, três Poké Bolas de Turtwig/Chimchar/Piplup, primeira batalha e concessão de Pokédex. A batalha exige três versões PBS já compiladas e marcador seguro exclusivo da cópia.
- [sinnoh-twinleaf-events.json](../data/regions/sinnoh-twinleaf-events.json): 9 mapas simbólicos, 5 handlers, 3 Poké Bolas físicas e 16 warps; sem IDs, sprites ou posições inventadas.
- [build_sinnoh_twinleaf_events.py](../scripts/regions/build_sinnoh_twinleaf_events.py): recompila eventos **do Blue**, exclusivamente sobre stage de geometria anteriormente auditado, hashes de mapa e coordenadas verificadas, gerando apenas overlay local; sem instalar `game/`.
- [tests/test_sinnoh_twinleaf_events.py](../tests/test_sinnoh_twinleaf_events.py) e [tests/sinnoh_pilot_runtime.rb](../tests/sinnoh_pilot_runtime.rb): segurança de eventos, save isolado, bloqueio de segundo inicial, gating de Barry e Pokédex. A workflow `regression.yml` executa o teste Ruby.
- [SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md): sequência original de Blue, ferramentas, comandos e critérios obrigatórios de QA.

**Apenas o que depende do Codex / dados locais:**
1. Conferir fonte real autorizada e identificar os **nove** mapas/interiores/rotas e todos os MapIDs, paredes, colisões, sprites, portais, posicionamentos e início verificável **no quarto** do jogador. Não colocar números hipotéticos na template publicada; trabalhar em cópia dentro de `.blue-work/sinnoh/`.
2. Reusar `convert_sinnoh_geometry.py` para gerar stage somente da geometria. Conferir o stage e completar a cópia local da template com os dados efetivos. Não copiar eventos originais nem sobrescrever staging existente.
3. Executar `build_sinnoh_twinleaf_events.py` primeiro sem `--stage` para dry-run e depois `--stage --expected-dry-run SHA_REAL` para uma **nova** sobreposição em `.blue-work/sinnoh-stage/`. O compilador deve rejeitar source MapIDs sem hash, coordenadas não verificadas ou outro tipo de script.
4. Criar e testar três versões **próprias do Blue** do treinador `BLUE_SINNOH_RIVAL` com inicial de vantagem e level cap/insígnias do Blue; habilitar `Data/blue-sinnoh-rival-ready.txt` **apenas** na cópia isolada depois de todas as equipes PBS terem sido validadas. Nunca conceder um segundo starter nem usar o PBS do doador.
5. Validar no Windows e JoiPlay: mãe → Barry → Rowan/maleta → clique nas três bolas (uma só é recebida) → Barry (ganhando/perdendo) → Pokédex → rotas/portas e save/reload, além de regressão Decades/Kanto/Johto/Hoenn. Publicar relatório com hashes e evidências sem enviar assets privados.

**Progresso real:** S13 e S14 **parciais**; preparação da introdução **5/8 subetapas**; desenvolvimento geral **8/32 (25%)**; fases técnicas, jogáveis e QA continuam **0/13** até os mapas reais e testes nativos. Relatório central: [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md).

### Barry — I07: gerar times reais PBS sem criar marcador de batalha antecipado

**Já está feito no GitHub; Codex NÃO deve reimplementar:**

- [build_sinnoh_barry_pbs.py](../scripts/regions/build_sinnoh_barry_pbs.py): gera os dois fragmentos `trainer_types_sinnoh_barry.txt` / `trainers_sinnoh_barry.txt` com as três versões exatas de `BLUE_SINNOH_RIVAL,Barry,0/1/2`, a partir dos `trainer_types.txt`, `pokemon.txt` e `moves.txt` nativos. As espécies seguem Turtwig → Chimchar, Chimchar → Piplup, Piplup → Turtwig, e os golpes são aprendidos pelo Pokémon do Blue até nível 5.
- [verify_sinnoh_barry_pbs.py](../scripts/regions/verify_sinnoh_barry_pbs.py): confirma a integridade do draft, SHA-256 dos PBS de origem, hashes dos dois PBS novos, três versões e contrato **70% normal / 90% Master**. Não cria `Data/blue-sinnoh-rival-ready.txt` em nenhuma circunstância.
- [Testes do gerador](../tests/test_sinnoh_barry_pbs.py) e [testes do verificador](../tests/test_sinnoh_barry_verify.py) usam apenas PBS sintéticos. No relatório `PBS draft` as flags de instalação, batalha real, compilação, sprite, save e liberação são todas **false**.
- [SINNOH_FASE_03_BARRY_PBS.md](SINNOH_FASE_03_BARRY_PBS.md): instruções locais completas, integração segura, bloqueios e divergência do piloto antigo.

**Codex: executar apenas após acesso ao `game/PBS` real, sem alterar os arquivos principais:**

```powershell
python scripts/regions/build_sinnoh_barry_pbs.py --game game --output .blue-work/sinnoh-barry-pbs-v1
python scripts/regions/verify_sinnoh_barry_pbs.py --game game --draft .blue-work/sinnoh-barry-pbs-v1
python -m unittest discover -s tests -p "test_sinnoh_barry*.py" -v
```

**Pontos obrigatórios que permanecem locais:**
1. Integrar os dois PBS **somente à cópia isolada**, compilar os dados Essentials, conferir sprite e todas as três versões do `GameData::Trainer`.
2. Conferir no motor que `BlueCampaign.trainer_level` realmente dimensiona ao jogador (70%/90%) conforme estágio, insígnias e nível real, e que a batalha de Barry pode ser perdida, sem importar scripts de origem.
3. Testar três starters, level cap, save/load e evitar repetição. **Apenas depois** criar o marcador `blue-sinnoh-rival-ready.txt` dentro da instalação de QA, jamais no Blue principal.
4. Investigar antes de combinar os pilotos: [pilot_sinnoh.py](../scripts/regions/pilot_sinnoh.py) usa IDs **800–805**, sobrepostos a Johto **600–999** no plano compartilhado, enquanto [SinnohPreview.rb](../scripts/regions/SinnohPreview.rb) seleciona starter via diálogo, diferente das três Poké Bolas físicas de [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb). Essas implementações não devem ser mescladas cegamente.

**Progresso sem inflar gameplay:** barra interna Barry **4/6**, introdução **5/8**, geral **8/32**, técnica/jogável/QA **0/13**. I07 ainda **não** aprovada.

### Novo: reconciliação do piloto Sinnoh e pré-verificação PBS de Barry

**Já implementado diretamente na main; não duplicar:**

- [audit_sinnoh_pilot_compat.py](../scripts/regions/audit_sinnoh_pilot_compat.py) e [testes](../tests/test_sinnoh_pilot_compat.py): detectam que o piloto antigo de Sinnoh associa seis mapas aos IDs **800–805**, dentro de **600–999** de Johto. Ele pode ser mantido numa cópia legada totalmente isolada; não mesclar os IDs nem reutilizar saves automaticamente. Também comparam o `SinnohPreview.rb` antigo (iniciais por diálogo) com `SinnohPilot.rb` novo (três Poké Bolas).
- [preflight_sinnoh_barry_qa.py](../scripts/regions/preflight_sinnoh_barry_qa.py) e [testes](../tests/test_sinnoh_barry_qa.py): conferem **somente leitura** o executável, hashes dos dois fragmentos PBS na pasta QA privada, candidato a sprite, possível conflito físico de MapIDs 800–805 e ausência de marcador prematuro. Não compilam PBS, não liberam Barry nem alteram o game.
- [SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md](SINNOH_FASE_03_CONCILIAR_PILOTO_E_QA_BARRY.md) contém o roteiro e os comandos completos.

**Pendências exclusivamente locais/realmente nativas:**

1. Apresentar auditoria dos MapIDs reais e reservas de mapas ainda não instalados (Kanto/Johto/Hoenn). Nunca inserir 800–805 no multi-regiões só por estarem livres na cópia do piloto antigo.
2. Montar uma **cópia QA separada** com fonte autorizada. O PBS de Barry deve ser gerado, copiado somente para essa cópia e conferido com `preflight_sinnoh_barry_qa.py --game game --draft .blue-work/sinnoh-barry-pbs-v1 --qa .blue-work/sinnoh-qa`.
3. No Game.exe da cópia, compilar PBS em três versões, conferir sprite e battle engine, testemunhar escala real normal 70%/Master 90%, salvar/carregar e comprovar não regressão.
4. Substituir no **piloto novo** o fluxo Rowan por diálogo por três Poké Bolas físicas e eventos autorais, somente depois de posições e gráficos realmente auditados; não misturar plugins `BlueSinnohPreview` e `BlueSinnohPilot` sem migração explicitamente testada.
5. Só depois de testes nativos completos, habilitar o marcador de Barry **exclusivamente no QA**. Não modificar saves nem a instalação principal.

**Barra específica:** reconciliação/QA **3/6**, Barry **4/6**, introdução **5/8**, geral **8/32**, fases de aprovação **0/13**.

### Nova Fase 02 — montador do piloto com eventos autorais e PBS de Barry

**Já foi implementado no GitHub:** [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py) e [testes sintéticos](../tests/test_sinnoh_pilot_bundle.py) combinam o stage auditado de geometria, o stage de eventos autorais dos nove mapas de Twinleaf/Sandgem e os dois PBS de Barry, além do próprio `SinnohPilot.rb`. Revalidam todos os SHA-256 de stage, os índices nativos MapInfos/Tilesets, MapIDs também das outras áreas presentes no stage, os 24 eventos gerados, os 16 warps e as três Poké Bolas físicas. O pacote permanece **privado, não jogável e sem marcador Barry**, e não contém Game.exe, System, Scripts ou saves.

**Leia o roteiro completo:** [SINNOH_FASE_02_PACOTE_INTEGRACAO_QA.md](SINNOH_FASE_02_PACOTE_INTEGRACAO_QA.md) antes de utilizar a ferramenta.

**Use somente com fonte Sinnoh autorizada e coordinates/MapIDs reais validados.** O modo sem `--publish` é dry-run e não escreve. Quando a auditoria passar, `--publish` permite apenas **novo diretório em `.blue-work`**, nunca `game/`. A template pública de Twinleaf está bloqueada por campos `null` intencionalmente.

**Não refazer o montador. Pendências Codex/local restantes:**
1. Auditar todos os MapIDs/reservas (incluindo futuros de Hoenn/Johto), direitos/licenças de cada asset, coords/sprites dos 9 mapas e garantir spawn no quarto.
2. Executar a integração com os dados verdadeiros e conferir os arquivos gerados apenas em `.blue-work`. Não usar os IDs 800–805 do piloto legado no multi-regional.
3. Montar **instalação QA completa separada**, com Game.exe e saves próprios, integrar o plugin BlueSinnohPilot e os dois PBS e compilar no Essentials real.
4. Testar os 3 iniciais em Poké Bolas, Barry versões 0/1/2, 16 warps, níveis 70%/90%, save/load e JoiPlay; só então conferir gates e eventual marcador no QA.
5. **Não publicar fontes não autorizadas, maps/tilesets privados ou o pacote QA no repositório.**

**Progresso honesto:** pacote de integração **3/6 subetapas de preparação**, geral **8/32**, fase técnica/jogável/QA **0/13**. Os scripts isolados, por si sós, não certificam gameplay.

### Instalador QA isolado e primeiro bootstrap PBS — código publicado

**Implementado aqui:**
- [install_sinnoh_qa_copy.py](../scripts/regions/install_sinnoh_qa_copy.py) — usa como entrada `game/` original e overlay Sinnoh privado com hashes; copia base **sem saves** para novo diretório `.blue-work`, cria identidade exclusiva `mkxp.json`/`Game.ini`, posiciona `System.rxdata` no quarto real, injeta na **cópia** o bootstrap de compilação das três versões Barry e fornece opção `--verify`. Não toca no jogo principal.
- [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) — no piloto isolado, impede `Novo Jogo` sem prova da compilação e hashes de MapInfos, System, mapa inicial e dois PBS. Inicializa `BlueRegions.new_state("SINNOH")` apenas após verificação; não reinicia saves carregados.
- [test_sinnoh_qa_install.py](../tests/test_sinnoh_qa_install.py) + [sinnoh_qa_start_runtime.rb](../tests/sinnoh_qa_start_runtime.rb) — testes com Game.exe **fictício**, sem ROM, cobrindo perfis novos, preservação de arquivos, compilação pendente, start gate, hashes e save state. Executados na CI isolada.
- [SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md](SINNOH_FASE_02_INSTALACAO_QA_SAVES_E_PBS.md) — comandos exatos e critérios nativos.

**Não reimplementar ferramentas. Necessário somente no ambiente Codex/Windows local:**
1. Auditar mapas/sprites originais e autorização de Sinnoh, resolver reservas de Johto/Hoenn/Kanto e preencher o JSON **local** de Twinleaf com hashes/MapIDs/coordenadas reais.
2. Produzir o overlay com `prepare_sinnoh_pilot_bundle.py`, executar `install_sinnoh_qa_copy.py` primeiro sem `--install` (dry-run) e depois com `--install`. Não incluir saves reais no GitHub; a nova pasta terá perfil próprio.
3. Abrir o `Game.exe` **da cópia**, aguardar a compilação PBS nativa de `BLUE_SINNOH_RIVAL,Barry,0/1/2`, conferir `--verify` e eventuais erros dentro da cópia. A primeira execução deve **encerrar depois da compilação**, não começar um jogo.
4. Na segunda abertura, verificar start no quarto, três Poké Bolas físicas, Rowan, Barry, 16 warps, save/load e diferença efetiva dos diretórios de save em `AppData`/mkxp. Testar Normal 70% e Master 90% sem criar o marcador de rival prematuramente.
5. Validar Android/JoiPlay, regressão Decades/Kanto/Johto/Hoenn e documentação de direitos; **só depois** considerar aprovação de fases jogáveis. Não ativar Barry na main.

**Progresso:** QA installation **4/7** em código; bundle **3/6**, introdução **5/8**, desenvolvimento total **8/32**, aprovações técnicas/jogáveis/Android **0/13**.

### Pós-compilação de Sinnoh — nova auditoria dentro da engine (código pronto)

**Não reimplementar:** [SinnohQAProbe.rb](../scripts/regions/SinnohQAProbe.rb) é a nova sondagem autoral somente para o `Game.exe` **da cópia QA**. [install_sinnoh_qa_copy.py](../scripts/regions/install_sinnoh_qa_copy.py) já a inclui na cópia; depois do `Compiler.main`, exige exatamente os **9 mapas, 24 eventos, 16 portais, 3 Poké Bolas e 3 GameData::Trainer de Barry** com contra-iniciais e nível-base PBS 5. Os destinos, coordenadas, sprites e scripts são comparados com os dados da auditoria local; o relatório é `Data/blue-sinnoh-qa-engine-check.json`. O instalador só escreve o token de compilação se essa sondagem passar.

O `--verify` do instalador valida esse relatório e os hashes dos mapas da cópia. [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) bloqueia `Novo Jogo` sem relatório nativo, mesmo que o token anterior já exista. Nenhuma ferramenta cria o arquivo `blue-sinnoh-rival-ready.txt` nem aprova gameplay. O [teste Ruby simulado](../tests/sinnoh_qa_engine_probe_runtime.rb) e os [testes Python](../tests/test_sinnoh_qa_install.py) estão na workflow. Procedimento completo: [SINNOH_FASE_02_VALIDACAO_NATIVA_PBS_EVENTOS.md](SINNOH_FASE_02_VALIDACAO_NATIVA_PBS_EVENTOS.md).

**Somente o que depende do Codex/local agora:**
1. Confirmar direito de uso, origem e hashes dos mapas reais de Twinleaf/Sandgem, além dos MapIDs de todas as regiões para evitar colisão.
2. Gerar o overlay e instalar uma cópia QA **nova** via ferramenta já publicada, sem importar saves e sem tocar no jogo principal.
3. Rodar o `Game.exe` QA apenas para compilar e executar a sondagem de eventos. Verificar o resultado de `--verify`: `compiled_marker_present:true`, `engine_structural_report_consistent:true` e `playable_approved:false`. Se houver erro, examinar `blue-sinnoh-qa-compile-error.txt`; não criar o marcador de Barry para contornar a falha.
4. Testar em jogo os três iniciais, batalha de Barry, níveis efetivos 70%/90%, sprites, navegação real, save/load e caminhos de saves Windows. Testar Android/JoiPlay separadamente. Somente então discutir liberação e atualização das barras de aceite.

**Barra de código da sondagem:** `4/7`. **Desenvolvimento geral** `8/32`. **Fases aprovadas** `0/13`; os mapas e a engine reais ainda não foram executados aqui.

### Playtest completo de Sinnoh — acesso de QA ao Barry + roteiro de 44 casos

**Já implementei no GitHub:**

- [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) agora permite **tentar** a batalha de Barry sem marcador de publicação, mas **exclusivamente** quando [SinnohQAStart.rb](../scripts/regions/SinnohQAStart.rb) autoriza a cópia QA com compilação/eventos/hashes válidos e a região atual é Sinnoh. No jogo principal Barry mantém o bloqueio. Batalha com resultado `nil` nunca altera o save; teste de vitória/derrota respeita `canLose`.
- [audit_sinnoh_playtest.py](../scripts/regions/audit_sinnoh_playtest.py) cria/verifica roteiro local de **44 cenários**: três iniciais e bloqueio de segunda Poké Bola; 12 batalhas de Barry em Normal 70% e Master 90% com vitória/derrota; 16 transições; cinco NPCs; save/load para cada inicial; regressões Decades/Kanto/Johto/Hoenn; JoiPlay. Exige captura/log com SHA256 por caso e confere nível observado, tipo rival, versão PBS, destino do warp e saves declarados. **Não cria marcador nem aprova a região automaticamente.**
- Testes: [test_sinnoh_playtest_audit.py](../tests/test_sinnoh_playtest_audit.py), [sinnoh_pilot_runtime.rb](../tests/sinnoh_pilot_runtime.rb) e [sinnoh_qa_start_runtime.rb](../tests/sinnoh_qa_start_runtime.rb).
- Passo a passo: [SINNOH_FASE_02_PLAYTEST_REAL_BARRY_SAVES.md](SINNOH_FASE_02_PLAYTEST_REAL_BARRY_SAVES.md).

**Falta executar somente onde existem dados/jogo reais:**
1. Gerar mapa/fonte de Sinnoh autorizada e instalação QA isolada; verificar `engine_structural_report_consistent:true` no Game.exe compilado e nunca instalar o QA em `game/`.
2. Rodar `python scripts/regions/audit_sinnoh_playtest.py --qa .blue-work/game-sinnoh-qa-PERFIL_REAL --create`, que gera o roteiro **não preenchido**. Não marcar casos que não foram executados.
3. No Game.exe QA real, fazer os três iniciais, tentar segundo starter, executar 12 variações de Barry (Normal/Master × vitória/derrota), registrar nível mais alto do jogador, nível da equipe rival observado, espécie/versão e quantidade de membros (a equipe Master pode ser expandida conforme a regra Blue).
4. Percorrer e validar **os 16 portais**, cinco NPCs, save/load dos três iniciais com **perfis de save de QA realmente distintos**, e executar regressões Decades/Kanto/Johto/Hoenn na própria instalação não modificada.
5. Registrar screenshot ou log real por caso em `qa-evidence/` dentro do QA privado, preencher o SHA-256 na checklist, realizar teste Android/JoiPlay separadamente e executar o auditor em modo `--audit`. Examinar capturas/manualmente; não publicar arquivos privados no GitHub.
6. Somente após análise integral das evidências humanas e verificação de direitos de material externo, discutir a aprovação de fases nativas; o script jamais cria `blue-sinnoh-rival-ready.txt`.

**Barras:** playtest/QA `4/7` em código; geral `8/32`; fases técnicas/jogáveis/Android `0/13`.

## 3. Pendências organizadas para o Codex

| ID | Dono | Fase | Situação inicial | Condição objetiva de aceite |
|---|---|---|---|---|
| **C00** | Codex/local | 00 | **BLOQUEADO:** fonte real e `game/Data` fora do Git | SHA-256 do ZIP/projeto, permissões por asset, MapInfos/tilesets/mapas, IDs nativos e relatório da fonte |
| **C01** | Codex/local | 01 | Depende de C00 | Inventário RXDATA completo, eventos/portas/warps/NPCs/itens/gráficos, grafo de conexões e ID mapping sem colisões |
| **C02** | Codex/local | 02 | Depende de mapas reais e C01 | Piloto Sinnoh isolado executa em Game.exe com saves próprios, sem mapas falsos, e Testar Sinnoh abre só ele |
| **C03** | Codex/local | 03 | Depende de C02 | Twinleaf casa→Route 201→Rowan→Sandgem e inicial de Platinum testados |
| **C04** | Codex/local | 04 | Depende de C03 | Jubilife/Oreburgh/Roark, primeira insígnia, Rock Smash e save/load |
| **C05** | Codex/local | 05 | Depende de C04 | Floaroma/Eterna/Gardenia, Galactic, Cheryl, Cut e retorno |
| **C06** | Codex/local | 06 | Depende de C05 | Hearthome/Veilstone/Pastoria; Fantina/Maylene/Wake, Surf/Defog corretos |
| **C07** | Codex/local | 07 | Depende de C06 | Canalave/Iron Island/Snowpoint, Byron/Candice, neve/Rock Climb |
| **C08** | Codex/local | 08 | Depende de C07 | Galactic HQ/Mt. Coronet/Spear Pillar/Distortion World com Cyrus/Giratina sem travar |
| **C09** | Codex/local | 09 | Depende de C08 | Volkner/Liga (Aaron, Bertha, Flint, Lucian, Cynthia), Hall of Fame e Sinnoh → Hoenn/Unova |
| **C10** | Codex/local | 10 | Depende de C09 | Battle Zone, missões de pós-jogo e lendários/revanches auditados |
| **C11** | Compartilhado | 11 | Depende de mapas/cenas reais e áudios autorizados | Música por cena correta, site sem níveis fixos, treinadores e encontros completos |
| **C12** | Codex/local | 12 | Depende de todos os anteriores | Integração reversível, Game.exe e JoiPlay testados, regressão Decades/Kanto/Johto/Hoenn, saves antigos válidos |

**ChatGPT continua responsável** pelos patches de documentação, dados públicos permitidos, ferramentas de análise, testes automatizados e melhorias do site que não dependam da engine local. O Codex **não** deve esperar que essas frentes deixem de avançar; deve sempre sincronizar o último commit antes de seu próprio trabalho.

## 4. Ordem de execução do Codex AGORA (C00)

### 4.1. Sincronizar e validar baseline

Na pasta do projeto em Windows, atualizar a **branch main** preservando qualquer alteração não commitada. Seguir `AGENTS.md`, e **não** usar `git clean -fdx`, `reset --hard` nem copiar `game/` inteiro para o Git.

```powershell
git status --short
git branch --show-current
git pull --ff-only origin main
python -m unittest discover -s tests -p "test_sinnoh_source_preflight.py" -v
python -m unittest discover -s tests -p "test_title_kanto.py" -v
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
```

Se houver conflitos ou alterações locais, **não descartá-las**: registrar e resolver com segurança. Se não houver `ruby` no PATH, registrar a dependência, mas prosseguir apenas nos testes Python válidos; não declarar teste Ruby aprovado sem o executar.

### 4.2. Inventariar fonte de Sinnoh legitimamente obtida

O primeiro candidato é [Ancient Platinum — publicação do autor](https://eeveeexpo.com/threads/9085/). **Não** pressupor que possua arquivos editáveis ou licença de redistribuição. A fonte deve ter sido disponibilizada e autorizada pelo responsável para o uso proposto; **se não estiver acessível, parar em C00 com relatório de bloqueio e não substituir por outro jogo**. O World Project Sinnoh foi visto com apenas dois Map*.rxdata na data do estudo; não é uma substituição válida para o mundo completo.

**Exemplo quando existir ZIP local:**

```powershell
New-Item -ItemType Directory -Force .blue-work/sinnoh | Out-Null
python scripts/regions/audit_sinnoh_source.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/preflight.json
```

Ou, quando o projeto doador já tiver sido extraído de maneira segura em local autorizado:

```powershell
python scripts/regions/audit_sinnoh_source.py --source ".blue-work/sinnoh-source/Projeto" --game-data game/Data > .blue-work/sinnoh/preflight.json
```

**Interpretar saída corretamente:**
- Código de saída 0 significa que o relatório **foi gerado sem erro estrutural**; **não** significa que a região, fonte ou licença está pronta.
- `source.map_count` representa arquivos `Map*.rxdata` presentes, **não a quantidade de cidades jogáveis**; nomes, eventos, tilesets e caminhos exigem inspeção posterior.
- `unmapped_id_collisions` é só a interseção **do ID bruto da fonte com IDs nativos do jogo**; todos os IDs precisam de remapeamento mesmo quando a interseção é vazia.
- `source.empty_or_template_source == true` é um bloqueio explícito de piloto jogável.
- `rights_verified`, `map_installation_verified`, `native_gameplay_verified` seguem `false` por construção; **somente provas posteriores** podem alterar estados externos, nunca esse auditor de pré-instalação.

**Codex deve entregar o relatório `docs/SINNOH_FASE_00_AUDITORIA_LOCAL.md`**, contendo: nome e versão da fonte, link/autoria, SHA-256 do arquivo, declaração de permissão por asset, tabela com todos os MapIDs e nomes (não IDs inventados), MapInfos/Tilesets/CommonEvents, NPCs, eventos, músicas, PBS, checagem de interações bloqueadas, lista de áreas faltantes, ID nativo atual e requisitos para criar o piloto. Não incluir binários ou mapas protegidos no commit.

### 4.3. Confirmar o sistema de IDs ANTES de C01

Pesquisar em `scripts/regions` pelos alocadores Johto/Kanto/Hoenn, conferir as reservas existentes, carregar `game/Data/MapInfos.rxdata` e listar todos os `MapXXX.rxdata`. **A faixa 600–999 já aparece em trabalho Johto**; números ≥1000 **só** podem ser usados após demonstrar suporte no RMXP, plugins, runtime, formatação de filenames, save loader, site e conversores. Nenhum MapID pode ser reservado empiricamente sem este teste.

### 4.4. Gates obrigatórios do Codex

- `game/`, `.blue-work/`, saves, MP3/OGG de terceiros e binários continuam ignorados pelo Git.
- Nunca substituir globalmente `System.rxdata`/`Scripts.rxdata`/`MapInfos.rxdata` do Blue pelo de Ancient Platinum.
- Treinadores, IA, evolução, níveis e esmeraldas usam os adaptadores de batalha do Blue; HMs exigem **insígnias locais de Sinnoh**, inclusive **Relic→Defog** e **Fen→Surf**.
- O piloto terá nome e perfil únicos: `SINNOH_JOGAR_EXPERIMENTAL.bat`, `scripts/regions/pilot_sinnoh.py`, `Sinnoh pilot.json`. **Só criar ao haver um spawn em mapa real de Twinleaf, com saída e retorno válidos**.
- Nunca alterar os save slots originais de `Continue`. Cuidado com Box cheia, especiais e troca regional; se a transferência falhar, restaurar o estado.
- Rodar `python -m unittest discover -s tests -v`, testes do site, validação Ruby e regressão das áreas anteriores **antes e depois**. Relatar resultados, inclusive falhas antigas separadas das introduzidas.
- Testes GUI no Windows e Android são necessários para aceite integral. **Não apresentar fixtures/unit tests como evidência de gameplay.**

## 5. Padrão de atualização deste MD (ao finalizar cada execução)

Atualizar a linha da tabela C00–C12 correspondente, sem reescrever histórico e sem marcar como concluída uma fase maior. Cada registro traz: data, commit base e final, fonte/hash, arquivos exatos alterados, novos testes, entradas/saídas e logs, pendências, se houve prova em `Game.exe`/JoiPlay, e alterações em **Barra 1 técnica** versus **Barra 2 integral**. Quando houver falta de arquivo real ou direito de uso, registrar como **BLOQUEADO** em vez de gerar placeholder.

**Andamento:** C00 = **parcial (infraestrutura e análise GitHub prontas; fonte/local pendentes)**; C01–C12 = **pendentes**. Etapas de mapa, trainer, NPC e música não foram importadas por este documento.

## 6. Prompt pronto para iniciar o Codex

> Continue a implementação de **Sinnoh** no projeto `GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal`. Primeiro leia `docs/SINNOH_CODEX_PENDENCIAS.md`, `docs/SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md`, `docs/SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md` e `AGENTS.md`, e sincronize a main sem descartar mudanças. **Execute agora C00/Fase 00**: teste o auditor `scripts/regions/audit_sinnoh_source.py`, faça inventário dos RXDATA/MapIDs da instalação local e fonte editável/autorizada de Sinnoh, confira SHA-256 e licenças, compare com Platinum e produza `docs/SINNOH_FASE_00_AUDITORIA_LOCAL.md` com evidências, lacunas e próximos passos. Não sobrescreva Decades/Kanto/Johto/Hoenn, não publique assets terceiros, não gere mapas ou logs fictícios, não crie piloto sem mapas reais. Se a fonte estiver indisponível, documente precisamente o bloqueio, publique apenas o relatório e mantenha 0/13 nas duas barras. Execute testes e publique código/MD verificáveis na main, informando commit, PASS/FAIL e próximos itens C01/C02.
