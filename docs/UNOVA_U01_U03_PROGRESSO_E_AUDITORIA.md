# Unova — U01–U03: implementação inicial, auditoria e barras de progresso

> Data: 17/11/2026. Referência: Pokémon White / Black & White.
>
> **ESTADO REAL:** pesquisa publicada, auditor de ZIP e catálogo simbólico implementados. **Unova ainda não está instalada ou jogável.** Não foi possível inspecionar o ZIP real de Pokémon World V18 neste ambiente e não há autorização geral para redistribuir seus assets.

## Entregas publicadas

| Entrega | Arquivo | Evidência / limite |
|---|---|---|
| Pesquisa de fontes RMXP | [Pesquisa](UNOVA_PESQUISA_FONTES_RMXP.md) | Candidatos e limites de licenciamento documentados |
| Plano U01–U32 | [Plano](UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md) | Estratégia sem modificar jogo |
| Auditor U02 | [audit_unova_u02.py](../scripts/regions/audit_unova_u02.py) | Lê apenas metadados ZIP, sem extração, execução ou instalação |
| Catálogo U03 | [unova-u03-areas.json](../data/regions/unova-u03-areas.json) | 74 áreas de referência, 18 rotas e 8 ginásios |
| Validador U03 | [audit_unova_u03_catalog.py](../scripts/regions/audit_unova_u03_catalog.py) | Valida exclusão de MapIDs falsos e status planned |
| Testes negativos | [U02](../tests/test_unova_u02_source.py) e [U03](../tests/test_unova_u03_catalog.py) | 12 + 14 testes sintéticos passaram localmente |
| Diagnóstico por duplo clique | [UNOVA_AUDITAR_FONTE.bat](../UNOVA_AUDITAR_FONTE.bat) | BAT publicado; ainda não testado num Windows real |

O auditor rejeita ZIP com path traversal, links simbólicos, duplicatas, membros criptografados, tamanho descompactado excessivo e estruturas sem MapInfos/Tilesets. Ele devolve total de mapas do projeto inteiro, **NÃO** a contagem de Unova, que continua null até ser investigada em RXDATA real.

## As cinco barras de progresso

São **trilhas auxiliares independentes de oito marcos cada**. Não confundir seu total com as 32 fases U01–U32 e não somar trabalho documental à jogabilidade.

| Barra | Resultado real | Justificativa |
|---|---:|---|
| **A — Fontes, mapas, MapIDs** | **0/8 (0%)** | ZIP real e MapInfos local não auditados |
| **B — História, NPCs, ginásios** | **0/8 (0%)** | Nenhum evento Unova instalado |
| **C — Selvagens, treinadores, música, pós-jogo** | **0/8 (0%)** | Nenhum recurso de origem integrado |
| **D — Game.exe, Blue-Story, JoiPlay** | **0/8 (0%)** | Nenhum teste real ou pacote instalado |
| **E — Documentação, ferramentas, catálogos** | **4/8 (50%)** | E01 fontes, E02 plano, E03 áreas/testes e E07 cues/treinadores/fallbacks simbólicos |

Pendências E04, E05, E06 e E08: ZIP real, nomes/eventos, direitos por arquivo e QA real. E07 documenta apenas chaves musicais, treinadores e fallbacks simbólicos, sem áudio ou equipes instalados.

**Fases U01–U32 aprovadas como jogáveis: 0/32.** U01 pesquisa inicial documentada (direitos ainda pendentes); U02 ferramentas criadas mas auditoria da fonte bloqueada; U03 catálogo de referências criado mas sem confrontar MapInfos real; U04–U32 não executadas.

## Proteções para não quebrar regiões anteriores

1. Nenhum arquivo existente de Decades, Kanto, Johto, Hoenn ou Sinnoh foi editado nesta entrega.
2. A nova ferramenta U02 não abre game/Data, nem reserva IDs, nem executa código Ruby do fangame doador, nem extrai ZIP.
3. Entrada de fonte autorizada só em **.blue-work/unova/sources/**, relatório só em **.blue-work/unova/audit/**; .blue-work já é ignorada pelo Git.
4. O catálogo não possui MapIDs originais ou de destino; todos são null, e o status do site de Unova permanece planned.
5. Os testes U02 recusam arquivos suspeitos e U03 falha quando qualquer área ou o registro é falsamente marcado jogável, autorizado ou instalado.
6. Antes de mapas reais, será obrigatório conferir MapInfos da instalação com reservas de Kanto, Johto, Hoenn e Sinnoh; nenhuma numeração de destino foi atribuída agora.

## Como rodar o auditor sem PowerShell

1. Obter, para análise privada e com os cuidados de autorização, o ZIP do autor na [publicação de Pokémon World V18](https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/).
2. Não extrair. Copiar como **Pokemon_World_V18.zip** para a pasta **.blue-work/unova/sources/** dentro do projeto local, ou arrastar o ZIP para cima do arquivo **UNOVA_AUDITAR_FONTE.bat**; o BAT só copia para a pasta isolada quando não há ZIP anterior.
3. Dar dois cliques no BAT; ele usa Python instalado e gera o relatório **.blue-work/unova/audit/u02-source.json** quando possível.
4. Conferir os bloqueios e os totais de arquivos. Total de mapas é **do projeto inteiro**, nunca declarar que todos pertencem a Unova.
5. A auditoria nunca habilita o seletor Unova nem instala mapas.

O BAT não foi executado em Windows/JoiPlay nesta entrega. Na ausência do ZIP o auditor retorna código 2 e informa bloqueio, o que é esperado.

**Teste local executado:** python -m unittest discover -s tests -p "test_unova_*.py" -v → 26 casos aprovados com dados sintéticos. Este teste não valida um ZIP real, os MapIDs do seu computador ou o jogo nativo. A suíte geral de CI do repositório já usa unittest discover; verificar o status da execução GitHub após os commits.

## Próximo passo U02 final / U03 real

Obter ZIP e créditos do autor, validar hashes/direitos, fazer o parse **inerte** de MapInfos/MapNNN para descobrir quais áreas Unova realmente existem, preencher matriz PRESENT/PARTIAL/MISSING e cruzar os 74 registros simbólicos com os mapas. Depois, U04 deve auditar MapInfos real e as reservas de todas as regiões antes de qualquer mapa piloto U05.

**Não marcar como concluída uma fase de importação sem a fonte, compilação e QA real.**


## Atualização da Barra E — 17/11/2026

Foram publicados instrumentos adicionais de trabalho, sem substituir arquivos jogáveis:

| Componente | Arquivo | Estado comprovado |
|---|---|---|
| Parser RXDATA inerte E05 | [audit_unova_source_detail.py](../scripts/regions/audit_unova_source_detail.py) | Implementado, mas ainda não aplicado ao ZIP real. Conta eventos, scripts não executados e transferências de MapNNN |
| Direitos e cues E06/E07 | [unova-e06-e07-preparation.json](../data/regions/unova-e06-e07-preparation.json) | 14 grupos de direitos UNVERIFIED, 69 chaves musicais e 19 referências de treinadores sem níveis/times inventados |
| Validador de direitos e música | [audit_unova_e06_e07.py](../scripts/regions/audit_unova_e06_e07.py) | Falha se houver licença, MapID, música ou time falsamente aprovado |
| Relatório E08 | [audit_unova_e08_readiness.py](../scripts/regions/audit_unova_e08_readiness.py) | Mostra 4/8 (50%), bloqueios e nenhuma aprovação Windows/JoiPlay |
| Validação com duplo clique | [UNOVA_VALIDAR_DOCUMENTACAO.bat](../UNOVA_VALIDAR_DOCUMENTACAO.bat) | Executa auditorias documentais sem iniciar Game.exe |
| Testes complementares | [RXDATA](../tests/test_unova_e05_rxdata.py), [direitos/music](../tests/test_unova_e06_e07.py), [relatório](../tests/test_unova_e08_readiness.py) | 33 cenários adicionais de proteção sintética |

### Critérios exatos, sem trocar documentação por conteúdo jogável

- [x] E01 — pesquisa e comparação de fontes reais
- [x] E02 — plano de integração U01–U32
- [x] E03 — 74 áreas de referência, validador e testes
- [ ] E04 — ZIP real do autor inspecionado, SHA-256, proveniência e créditos auditados; ferramenta preparada
- [ ] E05 — MapInfos/MapNNN reais confrontados com Unova; parser inerte preparado, nomes ainda não conferidos
- [ ] E06 — licenças e autorizações de cada asset verificadas; matriz preparatória não é autorização
- [x] E07 — 69 chaves musicais, fallbacks simbólicos e 19 referências de treinadores; nenhum áudio/time instalado
- [ ] E08 — evidências reais de QA Windows/Game.exe e Android/JoiPlay; gerador de checklist não substitui testes

**Barra E = 4/8 (50%).** A/B/C/D = 0/8; campanha jogável = 0/32. O status regional de Unova continua PLANNED.

### Execução sem PowerShell

Dê duplo clique em [UNOVA_VALIDAR_DOCUMENTACAO.bat](../UNOVA_VALIDAR_DOCUMENTACAO.bat). Este verifica as 74 áreas, 69 cues, 19 treinadores e o relatório E08, sem mexer no jogo. Para auditar a fonte, mantenha o ZIP original em .blue-work/unova/sources/Pokemon_World_V18.zip, obtido do autor, e rode novamente o BAT. O parser grava um relatório somente em .blue-work/unova/audit/u02-rxdata-detail.json. Fontes desconhecidas, direitos incompletos e dados não comprovados continuam bloqueados.

**Observação sobre CI:** em uma execução anterior da suíte geral, a etapa Ruby de Kanto falhou no teste de escala do protagonista kanto_cut_tree_runtime.rb; ela não é uma prova de falha da auditoria Unova. Não declarar toda a regressão global verde antes de verificar o run final da main.


### Evidência CI independente de Unova

- [Workflow Unova E — run 44076192454](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44076192454) concluiu com **success**: 59 testes Python específicos de Unova aprovados, validação das 74 áreas, auditoria de 14 categorias de direitos (todas pendentes), 69 chaves musicais, 19 referências de treinadores e verificação de sintaxe dos scripts.
- Esse CI só usa fixtures sintéticas e contratos de dados. Não baixou ZIP do autor, não inspecionou RXDATA real do usuário e não executou Game.exe, Blue-Story ou JoiPlay.
- O workflow independente não substitui a suíte completa. Houve anteriormente uma falha Ruby em Kanto/CutTree (escala do protagonista) na regressão geral; ela requer acompanhamento separado e não autoriza afirmar que a suite total está verde.

**Critério de encerramento:** preencher E04/E05/E06 com fonte real e direitos por arquivo, e E08 com QA Windows/Android registrado. Os 59 testes servem para proteger o trabalho preparatório, não para declarar Unova jogável.


## Continuação da Barra E — pipeline de fontes E04–E06

Novos scripts e testes foram desenvolvidos em branch de integração protegida, **sem editar o Decades, o Blue-Story, mapas ou saves**. O objetivo é diminuir o trabalho manual que faltará quando o ZIP do autor estiver disponível:

- [Auditor de correspondências E05](../scripts/regions/audit_unova_e05_crosswalk.py): cruza a leitura RXDATA com as 74 áreas e separa nome único, nome repetido, nome genérico e ausência de nome. Não confirma identidade regional nem aloca MapIDs de destino.
- [Inventário de direitos por asset E06](../scripts/regions/audit_unova_e06_rights_inventory.py): enumera arquivos do ZIP, categorias, CRC de referência, hash do arquivo de créditos quando presente e bloqueia redistribuição presumida.
- [Manual de execução E04–E06](UNOVA_E04_E06_AUDITORIA_FONTE_DIREITOS.md): explica o fluxo por duplo clique, relatórios locais e a revisão de direitos.
- [UNOVA_VALIDAR_DOCUMENTACAO.bat](../UNOVA_VALIDAR_DOCUMENTACAO.bat): agora tenta os relatórios E05/E06 depois da inspeção U02 se o ZIP existir; sem ZIP, exibe pendência e mantém Unova bloqueada.
- [Testes E05](../tests/test_unova_e05_crosswalk.py) e [E06](../tests/test_unova_e06_rights_inventory.py): 24 casos novos de segurança, correspondência ambígua e licenças não comprovadas.

A suíte independente de Unova passou **83 testes sintéticos (59 anteriores + 24 novos)** na [execução 44077820904](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44077820904). CI de preparação não prova mapa jogável, fonte real aprovada ou direitos para redistribuição.

**Estado mantido: E 4/8 (50%), U01–U32 jogáveis 0/32.** E04 requer ZIP e proveniência, E05 requer conferir os mapas/eventos reais, E06 requer licenças por recurso, E08 requer testes Windows/JoiPlay. Os novos auditores apenas preparam e protegem esse trabalho.


## Etapa seguinte — assistente E04 (sem aprovação de fonte)

Criado o [UNOVA_E04_ESCOLHER_FONTE.bat](../UNOVA_E04_ESCOLHER_FONTE.bat) e o [script de aquisição isolada](../scripts/regions/unova_e04_intake.py), com [instruções completas](UNOVA_E04_ASSISTENTE_FONTE.md).

O BAT permite escolher o ZIP pela janela do Windows ou arrastar o arquivo. Copia exclusivamente para a área privada .blue-work/unova/sources, calcula SHA-256, impede sobrescrever uma fonte diferente e encaminha para os auditores já existentes. Credits.txt é opcional para o transporte, mas obrigatório como evidência a verificar antes do fechamento de direitos.

**Não** houve download do ZIP original do Pokémon World V18 neste ambiente. Os hashes são do arquivo selecionado pelo usuário e não comprovam sua origem. Créditos **não** equivalem a licença. A nova entrega acrescenta testes negativos sintéticos; ela não instala nenhuma região.

**Barra E permanece 4/8 (50%)**, E04 ainda pendente da auditoria de fonte/proveniência. **Barra jogável continua 0/32.**


## SP03 — Auditor de sprites Gen 5 (documentação/ferramentas)

Foi implementada a ferramenta [audit_unova_sprite_pack.py](../scripts/regions/audit_unova_sprite_pack.py), independente do auditor RXDATA: lê ZIPs com PNG, GIF ou APNG; registra dimensões, quadros declarados, possíveis grades 4×4/3×4, nomes candidatos de NPCs, conteúdos duplicados SHA-256, colisões de basenames e possíveis diferenças de tamanho frente a Graphics/Characters do Decades, quando disponível. Nunca extrai ou instala arquivos do pack.

O [UNOVA_AUDITAR_SPRITES.bat](../UNOVA_AUDITAR_SPRITES.bat) permite escolher ZIP pela janela do Windows ou arrastar e soltar, e comparar opcionalmente a pasta local de sprites do Decades. O relatório é salvo apenas em .blue-work/unova/audit/sprite-packs/ e os créditos continuam não verificados. [Manual SP03](UNOVA_AUDITOR_SPRITES_SP03.md).

**Situação de progresso:** construção do auditor e execução de testes sintéticos não equivalem a auditar os packs originais nem a comprovar direitos e funcionamento nativo. **Barra E permanece 4/8; Unova jogável permanece 0/32.** Nenhuma alteração em Game.exe, saves, MapInfos, PBS, instalador ou outras regiões.


## SP04 — Catálogo de NPCs de Unova (elenco planejado)

Criado [catálogo SP04 de 73 personagens/arquétipos](../data/regions/unova-sp04-npcs.json), incluindo elenco inicial, N, Ghetsis, Team Plasma, líderes Black/White, Elite Four, Alder, classes de treinadores e agente regional próprio. Também inclui as **19 referências de treinador anteriores**, sem inventar níveis, times, MapIDs ou eventos.

O novo [auditor SP04](../scripts/regions/audit_unova_sp04_npcs.py) cruza esse catálogo com os relatórios privados do SP03: candidatos por nome, dimensões, frames, grade e alertas de escala; nenhum sprite é selecionado ou aprovado automaticamente. Use [UNOVA_CATALOGAR_NPCS.bat](../UNOVA_CATALOGAR_NPCS.bat) para gerar o relatório; o [UNOVA_AUDITAR_SPRITES.bat](../UNOVA_AUDITAR_SPRITES.bat) passa a chamar SP04 após a inspeção SP03. Manual: [UNOVA_SP04_CATALOGO_NPCS.md](UNOVA_SP04_CATALOGO_NPCS.md).

A campanha White mantém **Iris como líder do oitavo ginásio**, com Drayden identificado como referência de Black. A lista é de elenco/arquétipos, não de todas as instâncias anônimas nos mapas.

**E = 4/8 (50%)**, pois pack real, direitos e QA ainda estão pendentes; fases Unova realmente jogáveis **0/32**. Nenhuma alteração no jogo, saves, Blue-Story ou sprites instalados.
