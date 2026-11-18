# Sinnoh L03 — Matriz documental de reconciliação e protocolo de revisão humana

**17/11/2026 · issue #174 · somente engenharia no GitHub.** A L03 amplia o [revisor L02](SINNOH_L02_REVISAO_DOCUMENTAL_EVIDENCIAS.md), que utiliza as garantias de [L00](SINNOH_L00_PRONTIDAO_RELATORIOS_SANITIZADOS.md), [L01](SINNOH_L01_EXPORTADOR_SANITIZADO_OPCIONAL.md) e [G12](SINNOH_G12_HANDOFF_FINAL_B10_B11_44_CASOS.md). **Nenhuma execução no PC, nenhum Game.exe/Windows Sandbox/JoiPlay, nenhuma leitura/alteração de saves, sprites ou arquivos nativos.**

## Entregas versionadas

- [Matriz L03](../data/regions/sinnoh-l03-documentary-review.json): cinco etapas B09, B10, B11, R07, R08, com dependências, critérios de revisão humana separada e estados documentais. Todos iniciam `MISSING_REPORT`, `physical_ready=false` e `independent_evidence_accepted=false`.
- [Auditor/handoff L03](../scripts/regions/audit_sinnoh_l03_matrix.py): valida **exatamente** o esquema L03, cruza os estados calculados pela L02 e produz um pacote JSON de pendências e próximos atos documentais. Não copia valores de entrada, paths, hashes, observações livres ou identificadores privados.
- [40 testes negativos/positivos](../tests/test_sinnoh_l03_matrix.py): verificação dos cinco estados, fraude de SHA, adulteração de critérios de revisão, autorização prematura, mudanças em barras B/C/D, injeção de caminhos e revisão humana falsamente concluída.
- [Workflow CI L03](../.github/workflows/sinnoh-l03-documentary-handoff.yml): dois jobs, 40 testes L03 e regressões L02 (40), L01 (30), L00 (24), G12 (20). **Não publica artifacts** de relatório, não transmite dados do computador e não executa jogo/VM.

## Matriz de reconciliação

| Origem | Depende de | Verificação documental automática | Prova física para futuro avaliador |
| --- | --- | --- | --- |
| **B09** | — | Existência, hashes e contagens da cópia QA apenas declarados e coerentes | Origem e autorização dos assets, identidade e integridade reais do clone |
| **B10** | B09 | SHA B09→B10 e flags WSB somente leitura, sem rede, clipboard ou execução | Conferência independente de política da Sandbox e do ambiente host |
| **B11** | B09 + B10 | Contagem de arquivos monitorados, comparação antes/depois, sinal de cobertura parcial | Correlação de sessão **fora do GitHub**, caminhos reais usados pela engine e ausência de alteração em saves dentro dos escopos acordados |
| **R07** | — | Contagem de ocupação/colisões e status `reviewable` (não reserva) | Disponibilidade e pertencimento de MapIDs em todas as regiões planejadas |
| **R08** | — | Número de análises documentais das 14 imagens (não licença) | Autorizações legais por ativo, mapa/warp, permissões de uso e compilação real do PBS |

Os quatro estados preservados diretamente da L02 são:

| Estado L02 | Decisão automática L03 — exclusivamente documental |
| --- | --- |
| `MISSING_REPORT` | `REQUEST_NEW_SANITIZED_REPORT` |
| `SELF_REPORTED_AWAITING_HUMAN_REVIEW` | `SCHEDULE_DOCUMENTARY_ANALYSIS` |
| `PREREQUISITE_MISSING_BLOCKED` | `RECONCILE_PREREQUISITES` |
| `CONFLICTING_EVIDENCE_BLOCKED` | `BLOCK_AND_REVIEW` |

**Essas decisões não autorizam teste nativo.** A L03 permite que uma pessoa, em etapa futura separada, registre apenas uma destas disposições documentais: `REVIEW`, `REQUEST_NEW_SANITIZED_REPORT`, `BLOCK` ou `SCHEDULE_DOCUMENTARY_ANALYSIS`. Nenhuma delas significa `APPROVED`, `READY_TO_LAUNCH`, permissão para executar `Game.exe` ou certificação de direitos R08.

### O que o esquema não consegue verificar

A L00/L01 não conserva datas/horas de execução e retira identificadores privados de sessão B11. **Mesmo com cinco resumos sintaticamente válidos**, não é possível atestar:

1. A cronologia real B09→B10→B11.
2. Que o B11 veio efetivamente da mesma execução B10, sem verificar provas privadas fora do repositório.
3. Que o `watch_unchanged` cobre todos os locais onde a engine pode gravar saves.
4. Que os 54 MapIDs de terreno candidatos não conflitam com ocupações/reservas futuras.
5. Que as 14 imagens e demais assets possuem direitos autorizados.
6. Que os eventos, PBS, mapas, `Game.exe`, JoiPlay ou o jogo principal foram testados.

O protocolo exige que provas físicas sejam examinadas **em ambiente aprovado, por revisão humana independente e por autorização separada**. A L03 não cria um mecanismo de aprovação da QA: o campo `physical_qa_preapproved` permanece `false`, e o resultado só permite **planejamento documental**.

## Como consultar o protocolo (quando desejar, em outro momento)

Por padrão, consulta apenas os manifests públicos, que continuam sem os cinco relatórios locais:

```sh
python scripts/regions/audit_sinnoh_l03_matrix.py
```

Opcionalmente, após preparar e revisar manualmente o arquivo sanitizado da L01, o operador poderá escolher:

```sh
python scripts/regions/audit_sinnoh_l03_matrix.py --workspace-reports
```

Nesse modo, o programa lê **somente o caminho fixo** `.blue-work/sinnoh-l00-input/public-reports.json`. Não varre arquivos, não acessa jogos nem saves, não copia relatórios e **não executa nada na máquina do usuário nesta entrega GitHub**.

## Handoff para uma futura decisão humana

Uma revisão de evidências físicas exigirá documento externo específico com: proveniência do clone/ativos B09, prova independente dos parâmetros B10, confirmação privada da sessão B11, análise da cobertura completa de saves, reservas R07 de todas as regiões relevantes, permissões R08 por ativo, PBS/eventos reais e prova de ambiente isolado. **Esses dados não devem ser enviados como imagens, caminhos, snapshots privados ou saves ao repositório**. A pessoa responsável poderá solicitar novos resumos sanitizados e avaliar a próxima etapa — sem a L03 autorizar a execução.

**Situação preservada:** G01–G12 terminadas como engenharia GitHub; L00–L03 são auditorias documentais. R07/R08/R09 **pendentes**, Sinnoh `planned`, **B/C/D 0/13**, **0/44 testes nativos** (43 Windows e 1 Android), `Game.exe`/JoiPlay **não testados**.

**Próxima etapa segura sugerida:** **L04 — checklist de revisão manual de proveniência e critérios de autorização futura**, ainda sem PC, save, Sandbox ou jogo. A L04 não deverá transformar a qualidade dos JSONs em permissão para executar o jogo.
