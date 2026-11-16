# Sinnoh — CH19: regressões Python/Ruby isoladas e evidências do CI

**Data:** 16/11/2026 · **Situação:** código e workflow publicados na `main`; aguardando comprovação dos dois jobs CH19 na execução do GitHub Actions. **Sem certificação Game.exe ou JoiPlay.**

## Implementação

- [Executor fail-closed](../scripts/regions/sinnoh_ci_ch19.py): executa explicitamente os testes Python de Sinnoh e os testes Ruby de sintaxe/fixtures CH07–CH16, sem executar Kanto/Johto/Hoenn como parte do resultado regional. Também verifica auditorias offline e consistência da Barra E.
- [Workflow dedicado](../.github/workflows/sinnoh-ch19.yml): jobs independentes na matriz `python` e `ruby`, com `fail-fast: false`. O resultado de um job não cancela nem substitui o outro. O pipeline geral [`regression.yml`](../.github/workflows/regression.yml) continua existindo, sem alteração de seus testes.
- [Testes negativos](../tests/test_sinnoh_ci_ch19.py): conferem escopo, runners inexistentes, retorno não zero, conjunto vazio, status desconhecido, falhas parciais, relatórios e o bloqueio permanente de alegações nativas.
- Cada job gera `sinnoh-ch19-python.json` ou `sinnoh-ch19-ruby.json`, mais uma síntese Markdown, publicados como artifacts **mesmo se o job falhar**. Os relatórios contêm o comando, status, exit code, cauda do log, commit e distinção explícita entre teste offline e QA nativo.

### Comandos reproduzíveis (somente testes/arquivos do repositório)

```bash
python scripts/regions/sinnoh_ci_ch19.py --suite python --output .blue-work/sinnoh-ch19
python scripts/regions/sinnoh_ci_ch19.py --suite ruby --output .blue-work/sinnoh-ch19
python -m unittest discover -s tests -p 'test_sinnoh_ci_ch19.py' -v
```

**Critérios de falha:** runner ausente = `blocked`; teste com código diferente de zero ou timeout = `failed`; somente todos os comandos com exit 0 = `passed`. A CLI termina com código 1 para `failed/blocked`. Nenhuma dessas categorias modifica MapIDs, PBS, saves, `game/` ou a aprovação nativa. Os comandos não incluem `Game.exe` ou JoiPlay.

**Separação de subsistemas:** o campo `external_subsystems` informa `not_run` para Kanto/Johto/Hoenn (não `passed`). Uma falha de Kanto em um workflow geral não apaga um sucesso de Sinnoh, e um sucesso de Sinnoh não corrige nem reclassifica a falha geral.

## Evidências anteriores à CH19

- [Execução geral 43981753812](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753812): o job **Sinnoh — contratos isolados** terminou `success`, inclusive **347/347 testes Python Sinnoh** e demais checks anteriores. O job **PBS + contratos UI + syntax JS** terminou `failure` na etapa **Validar escopo regional de Kanto na engine Ruby**.
- O log desse job geral identifica `tests/kanto_cut_tree_runtime.rb:79` e `CutTree regression: previous protagonist scale fix was lost`; falha de **Kanto**, não da suíte isolada de Sinnoh.
- [Portal 43981753762](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43981753762): build e **137 testes do site** concluídos na CH18. Este resultado **não** é resultado da nova matriz CH19.

## Portão para concluir CH19

Para passar de `partial` a `done`, consultar uma execução do workflow `Sinnoh CH19 - regressao Python Ruby isolada` sobre o commit final, confirmar **ambos os jobs** `python` e `ruby` aprovados, ler os dois artifacts e registrar os links/contagens efetivos na documentação. Erros de Kanto/Johto ficam num bloco separado, sem falsa aprovação ou penalização de Sinnoh.

**Barras preservadas:** A **8/32 (25%)**, B/C/D **0/13**. A Barra E conta CH19 **parcial enquanto não há CI confirmado**; CH20 permanece pendente. Não se inferiu uma compilação nativa nem se abriu uma região jogável por estes testes.
