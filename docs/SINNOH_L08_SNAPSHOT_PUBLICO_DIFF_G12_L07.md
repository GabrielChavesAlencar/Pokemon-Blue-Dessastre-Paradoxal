# Sinnoh L08 — Snapshot de proveniência pública por commit e diferenças semânticas

**Issue [#189](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/189).** Fase GitHub-only. O resultado é uma comprovação de **integridade de metadados públicos**, **não** da autenticidade de uma instalação, direitos de redistribuição, execução de QA, isolamento de saves ou aprovação de Sinnoh como jogável.

## Entregas

- [Snapshot imutável L08](../data/regions/sinnoh-l08-pinned-snapshot.json): 44 casos CH20/G12, 20 critérios L04, 43 Windows e 1 Android, dependências e bloqueios.
- [Relatório de diferenças semânticas](../data/regions/sinnoh-l08-semantic-diff.json): compara **G12→L05**, **L04→L05**, **L05→L06**, **L06→L07**, **L07→L08**. As cinco comparações são reconstituídas pelo auditor a partir de arquivos públicos, não presumidas com base no JSON.
- [Auditor fail-closed](../scripts/regions/audit_sinnoh_l08_pinned_snapshot.py): verifica o conteúdo binário de seis arquivos Git públicos pelo identificador de blob, revalida a cadeia L07→L06→L05→L04→G12, recalcula os diffs e rejeita fontes adulteradas.
- [Testes sintéticos](../tests/test_sinnoh_l08_pinned_snapshot.py): testes positivos, **102 testes negativos**, adulteração de IDs, ordem, plataformas, revisão, direitos, mapas, flags, blob pinning e regressões.
- [Workflow CI L08](../.github/workflows/sinnoh-l08-pinned-diff.yml): suíte L08, regressões L07/L06/L05/L04/L03/L02/L01/L00/G12 e testes Node de integridade do painel L07.

## O que é ancorado no commit

O snapshot usa como **commit público de referência** o squash merge da L07:

`d98033b362dac82347e0d97cb5606870eaa70b22`

Abaixo estão os IDs de objeto **Git blob SHA-1**, confirmados tanto nesse commit como na `main` antes da L08. São identificadores **públicos de arquivos do repositório**; não são hashes de saves privados, de imagens ou de clones locais.

| Contrato | Git blob SHA-1 público |
| --- | --- |
| G12 — handoff nativo pendente | `e0fb08348fe5211f62acd057200d9c4a926351ab` |
| L04 — critérios humanos | `cffdaac87c0dc542b99dd9bdebe54d49038d940d` |
| L05 — 44 casos × 20 critérios | `4c8d35e510dd863568e34fd3cc7d2e4ba908bcde` |
| L06 — roteiros humanos | `9ec4170d9c60e4d53028234e447a0a38346ddace` |
| L07 — matriz de triagem | `ec42d1010293d352fba8ad96cc40793e2acc190f` |
| L07 — cópia pública para o portal | `ec42d1010293d352fba8ad96cc40793e2acc190f` |

O commit da **L08 em si** será registrado na issue após aprovação de CI e merge; não é embutido na própria matriz para evitar uma autorreferência impossível (um arquivo não pode conter o hash final de um commit que depende dos bytes do próprio arquivo).

### Escopo de cada comparação

| Comparação | Elementos verificados | Resultado documental esperado |
| --- | --- | --- |
| G12 → L05 | 44 IDs, ordem, categoria, plataforma e status nativo | Zero divergências |
| L04 → L05 | 20 IDs de critérios, ordem, cobertura | Zero divergências |
| L05 → L06 | 44 IDs, critérios exigidos, bloqueios e plataformas | Zero divergências |
| L06 → L07 | 44 IDs, vínculos, fila Windows/Android, gates e status | Zero divergências |
| L07 → L08 | 44 IDs, vínculos, status e permissões sempre falsas | Zero divergências |

O diff registra quatro classes de alterações: **IDs adicionais, IDs ausentes, IDs reordenados e linhas modificadas**. Se qualquer comparação divergir, a L08 **bloqueia** a validação. A ausência de diferenças entre documentos públicos não certifica que os mapas, assets, direitos, saves ou testes existam fisicamente.

### Separação obrigatória Windows/Android

- **43 casos Windows:** mantêm origem B09, revisão de isolamento B10/B11 e bloqueios regionais/direitos R07/R08. `watch_unchanged` **não** implica isolamento global de saves nem autentica vínculo B10/B11.
- **1 caso Android/JoiPlay:** depende da própria futura revisão Android, B09/R07/R08; **não herda** B10/B11 da Windows Sandbox.
- **R07:** reservas/MapIDs candidatos não equivalem a IDs nativos reservados.
- **R08:** ativos e licenças sem revisão independente não equivalem a direitos aprovados.
- **R09:** continua pendente; a L08 não altera nenhuma função jogável do game.

## Como executar a auditoria documental em CI

```sh
python scripts/regions/audit_sinnoh_l08_pinned_snapshot.py
python -m unittest discover -s tests -p 'test_sinnoh_l08_pinned_snapshot.py' -v
```

O comando **não recebe caminhos arbitrários**, somente arquivos JSON públicos em locais fixos do repositório. Verifica Git blobs usando SHA-1 de formato `blob <tamanho>\\0<bytes>`, método de identidade do Git, sem invocar Git, acessar rede, varrer diretórios ou fazer upload. O verificador rejeita symlinks e arquivos acima do limite seguro de leitura.

## Indicadores preservados

| Indicador | Status |
| --- | --- |
| Contratos públicos de casos | 44 IDs, 43 Windows + 1 Android |
| Revisão humana independente | **0/20** aprovações |
| Relatórios locais recebidos | **0/5** |
| Testes nativos Windows/Android | **0/44** |
| Barras B/C/D | **0/13** |
| R07, R08 e R09 | **Pendentes** |
| Sinnoh no Game.exe e JoiPlay | **planned — não jogável** |
| Aprovação de direitos, isolamento global B11, instalação | **Não comprovados / não autorizados** |

**Próxima etapa segura L09:** criar uma revisão independente da consistência do snapshot fixo e um pacote de handoff público para revisor, sem tokens de execução, aprovação de direitos nem mudanças na jogabilidade.
