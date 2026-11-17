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
| **E — Documentação, ferramentas, catálogos** | **3/8 (37,5%)** | E01 fontes, E02 plano 32 fases, E03 catálogo/validador/testes publicados |

Pendências E04–E08: auditoria real do ZIP; nomes/eventos RXDATA; direitos de recursos; dados musicais/treinadores; evidências integradas de QA.

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
