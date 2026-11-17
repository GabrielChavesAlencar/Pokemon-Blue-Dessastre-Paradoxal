# Sinnoh — CH19: regressões Python/Ruby isoladas e evidências do CI

**Data:** 16/11/2026 · **Situação:** CH19 validada em CI Python e Ruby e publicada na `main` (PR [#65](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/65), merge `4bbc767b22812590ed4a80426092b4dd82b0b97f`). **Sem certificação Game.exe ou JoiPlay.**

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

## Evidência CI de conclusão CH19

- [Workflow CH19 — run 43985365758](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365758): **conclusão `success`**, com dois jobs independentes aprovados.
- [Artefato Python](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365758/artifacts/14284957926): `sinnoh-ch19-python.json` e `sinnoh-ch19-python.md`; **7 verificações aprovadas**, exit code `0` para todas. A descoberta unitária executou **374/374 testes Python** (8,898 segundos), sem falhas.
- [Artefato Ruby](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365758/artifacts/14285755308): `sinnoh-ch19-ruby.json` e `sinnoh-ch19-ruby.md`; **22/22 verificações aprovadas**, todos os retornos `0`. Inclui sintaxe e as sondagens de Twinleaf, Barry, região, evolução, história e BlueMusic.
- Os **dois JSONs foram inspecionados**: `status=passed`, `scope=sinnoh_only`, `native_qa_approved=false`, `game_exe_executed=false`, `joiplay_executed=false`. A referência de execução registrada é o merge temporário do PR `b019f90b784095f6275d8270a7502f0c74e6e6c1`; o código validado foi integrado pela PR [#65](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/65) na `main` no commit `4bbc767b22812590ed4a80426092b4dd82b0b97f`.
- Na primeira execução do PR, **Python falhou em asserções de mensagem do auditor CH20**; foram corrigidas preservando o bloqueio de falsos MapIDs/warps/sprites. O novo CI [CH20 43985365818](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43985365818) também concluiu com sucesso, porém **não foi feita certificação de Android**.
- O job geral Blue Studio é independente: erros de outros módulos (inclusive Kanto) não contam como falhas da matriz isolada. Não declarar o pipeline geral aprovado por causa deste resultado.

**Critério de aceite da CH19 atendido:** Python/Ruby de Sinnoh discriminados em jobs próprios, relatórios auditáveis, falhas negativas preservadas e execução CI real verificada. **A Barra E passa para 19/20 (95%)**, com **CH20 ainda parcial**. **Barras A 8/32 (25%), B/C/D 0/13 permanecem intactas.** Este status representa implementação offline, não Sinnoh jogável em Windows ou Android.
