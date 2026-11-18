# Sinnoh L20 — reconciliação pública de metadados (não jogável)

**Status:** PENDING/BLOCKED. Etapa documental pública, sem aprovação humana, sem QA nativa e sem acesso à instalação do usuário.

## Âncoras e método

- Issue de execução: [#218](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/218).
- Base imutável: [L19, PR #217](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/217) integrado na main no commit `54bbb63a7f2f7a74a26ce8dbc61d52793a27315d`.
- Blob público L19: `ff9f86e14cd28f7960331580d85e2b10d99b8240`. SHA-1 Git do blob é só âncora de *bytes públicos*, jamais prova de direitos, testes nativos, autenticidade de arquivo físico ou isolamento de saves.
- Report: `data/regions/sinnoh-l20-public-reconciliation.json`. Espelho idêntico: `site/public/data/sinnoh-l20-public-reconciliation.json`.
- Painel HTML somente leitura: `/sinnoh-l20-reconciliacao.html`. Filtros por ID, tipo, prioridade P0–P4, plataforma, bloqueio, lacuna e correspondência.
- Auditor Python: `scripts/regions/audit_sinnoh_l20_reconciliation.py`. Testes sintéticos negativos no `tests/test_sinnoh_l20_reconciliation.py`; Node em `site/tests/sinnoh-l20-reconciliation.test.mjs`.

## Invariantes preservadas

| Atributo | Estado L20 |
|---|---|
| Pedidos L19 reconciliados | 88/88 |
| Correspondência das identidades, prioridades, plataforma e status | 88/88, 0 drifts |
| Lacunas | 88 abertas, 0 fechadas |
| Revisões independentes | 0/20 |
| Casos G12 nativos | 0/44 (43 Windows; 1 Android independente) |
| Relatórios locais | 0/5 |
| Slots B/C/D | 0/13 |
| Slots anônimos sem atribuição | 18 (5 relatórios + 13 B/C/D) |
| Ligações caso→critério, caso→bloqueio, critério→bloqueio | 846 + 218 + 20 = 1.084 |
| Portões R07, R08, R09 | PENDING |
| Sinnoh | planned / não jogável |

B09/B10/B11/R07/R08 continuam pendentes por caso quando aplicáveis. R09 permanece global regional, sem arestas por caso. O Android **não** herda B10/B11 nem aprovações de Windows. As prioridades P0–P4 servem somente a ordenação documental; não autorizam execução.

## Restrições e validação

A reconciliação projeta somente campos públicos exatos do L19. O auditor compara relatório e espelho a uma projeção determinística da base L19 protegida por SHA Git, checa estados impeditivos e executa a cadeia L19–L00/G12 anterior. Desvios de identidade, link, cobertura, prioridade, local de execução, aprovação ou atribuição anônima falham fechados.

Não executar Game.exe, Windows Sandbox, JoiPlay, ROM, instaladores, saves; não capturar arquivos privados, nomes de revisores, evidências físicas, direitos ou atestados. Checks documentais verdes não desbloqueiam Sinnoh. Merge na main só após CI relevante efetivamente aprovado; workflows independentes de Kanto e Blue Studio precisam ser acompanhados separadamente e nunca mascarados.
