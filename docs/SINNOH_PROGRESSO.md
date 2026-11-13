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
- **Parciais:** 5 (não contam como concluídas até atingirem o próprio critério).
- **Pendentes:** 19.
- **Total:** 32 entregas no inventário [JSON](../data/regions/sinnoh-progress.json).
- **Restam 24 para a barra de desenvolvimento** (inclui parciais).

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

## Entregas concretas da Barra A

| Situação | ID | Entregável | Arquivo / evidência |
|---|---|---|---|
| Concluído | S01 | Auditor básico de origem | [auditor](../scripts/regions/audit_sinnoh_source.py) |
| Concluído | S02 | Auditoria interna de RXDATA | [auditor profundo](../scripts/regions/audit_sinnoh_rxdata.py) |
| Concluído | S03 | Estudo de capacidade de MapIDs | [capacidade](../scripts/regions/plan_sinnoh_capacity.py) |
| Concluído | S04 | Proveniência e direitos pendentes | [manifesto](../data/regions/sinnoh-source.json) |
| Concluído | S05 | 91 áreas e 51 eventos simbólicos | [cobertura](../data/regions/sinnoh-coverage.json) |
| Concluído | S06 | Grafo de conexões e referências ausentes | [grafo](../scripts/regions/graph_sinnoh_maps.py), [testes](../tests/test_sinnoh_graph.py) |
| Parcial | S07 | Transação segura: dry-run, staging e rollback só em `.blue-work` | [transação](../scripts/regions/sinnoh_staging_transaction.py), [testes](../tests/test_sinnoh_staging_transaction.py) |
| Parcial | S08 | Integridade de recursos gráficos e mapas | [auditoria RXDATA](../scripts/regions/audit_sinnoh_rxdata.py) |
| Concluído | S09 | Botão Testar Sinnoh sem quebrar saves | [menu](../scripts/battle_polish/TitleKanto.rb) |
| Parcial | S24 | Catálogo musical planejado | [estudo](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) |
| Parcial | S30 | Testes automatizados (escopo parcial) | [testes de grafo](../tests/test_sinnoh_graph.py) |
| Parcial | S31 | Plano de aceitação Windows/JoiPlay | [plano](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) |
| Concluído | S32 | Fila de pendências Codex | [backlog](SINNOH_CODEX_PENDENCIAS.md) |

**As demais entregas de S10–S29 não listadas acima seguem pendentes**; veja a lista completa, com os 32 IDs, no [registro JSON](../data/regions/sinnoh-progress.json). A ordem de implementação é independente das fases integradas: uma API pode estar pronta mas não haver mapa-fonte para aprovar uma fase.

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
