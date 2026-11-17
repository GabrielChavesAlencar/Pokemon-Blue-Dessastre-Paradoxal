# Sinnoh S30 — suíte automatizada de regressões offline

**Escopo:** desenvolver e verificar uma suíte automatizada auditável para a região de Sinnoh. Esta entrega da Barra A é **exclusivamente de engenharia de testes**: não afirma que Sinnoh foi instalado no Game.exe, nem que os 44 casos nativos foram observados no Windows/JoiPlay.

## Implementação da S30

- [Auditor S30](../scripts/regions/audit_sinnoh_s30_suite.py) gera um manifesto somente de leitura com SHA-256 dos arquivos essenciais. Bloqueia testes ausentes, workflows incompletos, contadores incompatíveis, região falsamente jogável, importação ativada indevidamente e aprovação nativa sem etapa S31.
- [11 testes negativos/positivos](../tests/test_sinnoh_s30_suite.py) verificam quatro grupos de arquivos, recusa de arquivo/tarefa ausente, gates incompletos, saída fora de `.blue-work`, sobrescrita de relatórios e falsas declarações de CI/Windows/Android.
- [Workflow S30](../.github/workflows/sinnoh-s30.yml) tem cinco jobs independentes: **Manifesto**, **Python**, **Ruby**, **Portal**, **Android estático**. Falha em qualquer job impede aprovação do workflow; uma execução offline jamais cria um selo de jogabilidade.
- Python e Ruby usam a [regressão isolada CH19](../scripts/regions/sinnoh_ci_ch19.py), sem executar Kanto, Johto ou Hoenn nesses jobs. O portal realiza **build** e **suíte Node completa**. Android combina os testes de integridade CH20 e os 44 casos `pending`, sem executar JoiPlay.
- O estado da região e o progresso continuam derivados do [ledger](../data/regions/sinnoh-progress.json); o relatório tem `native_game_exe_tested=false`, `joiplay_tested=false`, `native_qa_approved=false` e `ci_jobs_verified_by_manifest=false`.

## Comandos reproduzíveis

```bash
python -m unittest discover -s tests -p 'test_sinnoh_s30_suite.py' -v
python scripts/regions/audit_sinnoh_s30_suite.py --output .blue-work/sinnoh-s30/manifest.json
python scripts/regions/sinnoh_ci_ch19.py --suite python --output .blue-work/sinnoh-s30
python scripts/regions/sinnoh_ci_ch19.py --suite ruby --output .blue-work/sinnoh-s30
cd site && npm run build && npm test
```

O manifesto é propositalmente `ready_for_ci_not_native_verified`. **Só os resultados reais dos cinco jobs no GitHub Actions** permitem registrar S30 como `done`; o manifesto sozinho não é um certificado de testes executados.

## Aceite e barras

Após os cinco jobs serem verificados em uma execução real de CI e o PR integrado à `main`, a **S30** fica concluída em seu escopo offline: **Barra A 11/32 (34%)**, 6 etapas parciais, 15 pendentes. A Barra E permanece **20/20 (100%)** e B/C/D **0/13**.

**Fora do escopo desta S30:** mapa real, Game.exe, JoiPlay, compilar PBS nativo, saves, áudio, colisões, batalhas e observações dos 44 testes nativos. A aceitação Windows/Android continua na **S31**, com bloqueios de fonte autorizada, IDs e QA real.
