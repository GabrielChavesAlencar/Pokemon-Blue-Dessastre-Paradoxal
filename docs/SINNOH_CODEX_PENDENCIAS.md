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
