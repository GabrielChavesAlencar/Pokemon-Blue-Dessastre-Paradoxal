# Sinnoh L02 — revisão offline e fail-closed de relatórios sanitizados

**17/11/2026 — issue #171.** A L02 consolida a cadeia documental já implementada em [L00](SINNOH_L00_PRONTIDAO_RELATORIOS_SANITIZADOS.md), [L01](SINNOH_L01_EXPORTADOR_SANITIZADO_OPCIONAL.md) e [G12](SINNOH_G12_HANDOFF_FINAL_B10_B11_44_CASOS.md). **É exclusivamente uma entrega de código e testes GitHub-only.** Não foi acessado o computador do usuário; o programa não abre nem inicia Game.exe, Windows Sandbox, JoiPlay, arquivos de saves ou assets privados.

## Componentes versionados

- [Revisor L02](../scripts/regions/review_sinnoh_l02_evidence.py): recebe somente um **documento L00/L01 já sanitizado** e cruza com os contratos públicos existentes via o validador oficial `audit_sinnoh_l00_readiness.py` e o handoff G12.
- [40 testes sintéticos e negativos](../tests/test_sinnoh_l02_evidence.py): cobrem recibos ausentes, formato, dependências B09–B11, erros de SHA/MapID, contradições de contagens, Sandbox insegura, monitoramento B11, direitos e aprovação prematura.
- [Workflow CI L02](../.github/workflows/sinnoh-l02-review.yml): 2 jobs. Valida os 40 testes e reexecuta **L01 (30), L00 (24), G12 (20), G11 (18)**; não faz upload de relatórios, capturas ou saves.
- O modelo base [`sinnoh-l00-public-reports.json`](../data/regions/sinnoh-l00-public-reports.json) permanece com **cinco valores `null`**, pois **nenhum relatório real da máquina do usuário foi compartilhado**.

## Classificação dos cinco relatórios

| Código L02 | Significado, sem extrapolar provas físicas |
| --- | --- |
| `MISSING_REPORT` | Relatório sanitizado não foi fornecido; nenhuma conclusão sobre a existência do respectivo stage no PC |
| `SELF_REPORTED_AWAITING_HUMAN_REVIEW` | Campos e invariantes documentais passam pela L00, mas o arquivo é **auto-declarado, sem autenticação independente** |
| `PREREQUISITE_MISSING_BLOCKED` | B10 não está vinculado a B09 válido, ou B11 não tem simultaneamente recibos B09/B10 validados; bloqueia avanço |
| `CONFLICTING_EVIDENCE_BLOCKED` | Campos extras ou ausentes, hash/contagem inválida, aprovação falsa, WSB insegura, alteração B11 escondida ou outro contrato incompatível |

O relatório global será `INCOMPLETE_DOCUMENTARY_HANDOFF`, `BLOCKED_MISSING_CHAIN_PREREQUISITES`, `BLOCKED_CONFLICTING_OR_UNSAFE_REPORTS` ou `DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING`. Mesmo cinco registros bem-formados **não** tornam Sinnoh instalável/jogável e **não** liberam a QA nativa. A CLI retorna erro quando há contradições ou dependências quebradas; ausência de relatórios é uma revisão segura e incompleta, não erro de sistema.

A saída imprime apenas **nomes de etapas fixos, códigos, contagens por classe e ações genéricas para revisão humana**. Ela não copia SHA de plano, inventário, nome ou caminho de save, `watch_id`, HMAC, baseline, dados de PNG, timestamps ou valores dos recibos. Essas limitações também se aplicam aos testes sintéticos.

### Vínculos e lacunas intencionais

- **B09 → B10:** confere que o SHA declarado no B10 corresponde ao SHA sanitizado do plano B09. Não comprova que o clone existe fisicamente, nem a autenticidade desse SHA. B10 sem B09 é bloqueado.
- **B11:** confere estado `before/after`, contagens, `coverage_is_partial=true`, alterações e permissões pelas mesmas regras da L00. A L01 remove `watch_id` e `clone_sha256` por privacidade; **L02 não pode provar que B11 pertence à mesma sessão B10**. Mesmo quando a cadeia contém três recibos bem-formados, permanece `b11_session_link_in_sanitized_sources_available=false`.
- **Datas e cronologia:** o esquema público L00/L01 **não contém timestamps de execução**. A L02 exige revisão privada posterior para provar a ordem real dos acontecimentos, e registra `chronology_dates_in_sanitized_sources_available=false`. Nenhuma data ou horário é inventado.
- **R07:** reservas de MapID e ausência de colisões declaradas não garantem propriedade de IDs ou ausência de conflito em regiões futuras.
- **R08:** até 14/14 análises documentais de licença não significam aprovação de direitos ou assets físicos prontos.
- **B11 `watch_unchanged`:** prova apenas o resultado dos escopos monitorados pelo relatório — **não** cobertura de todas as pastas de save da engine nem isolamento global.

## Execução documental opcional, nunca automática

O comando padrão lê **somente o modelo público do repositório**:

```bash
python scripts/regions/review_sinnoh_l02_evidence.py
```

Para o operador que já tenha escolhido gerar e revisar localmente o único JSON sanitizado pela L01, há uma opção específica:

```bash
python scripts/regions/review_sinnoh_l02_evidence.py --workspace-reports
```

A segunda forma **só lê** `.blue-work/sinnoh-l00-input/public-reports.json`. É opcional e não foi executada no computador do usuário nesta conversa. Ela não aceita `--file`, `--project`, `--game-dir`, parâmetros com caminhos ou diretórios arbitrários. Erros não ecoam argumentos privados. Não há instrução para executar o jogo, coletar saves ou transmitir relatórios. Qualquer decisão de compartilhar resultado depende de revisão e ação explícitas do operador.

## Checklist de revisão humana que continua aberto

1. Comprovar origem real de B09, material de entrada autorizado e integridade da cópia QA independentemente dos JSONs.
2. Validar em ambiente controlado e com aprovação separada política B10, leitura somente do clone, ausência de rede/clipboard e isolamento físico dos arquivos.
3. Correlacionar localmente a sessão B11 a B10 sem publicar o identificador/segredos; verificar a cobertura real de diretórios de saves e comparação antes/depois.
4. Verificar reservas futuras R07 e direitos reais por ativo R08, inclusive mapas/warps, sprites e PBS.
5. **Somente depois** planejar 43 casos Windows e 1 Android/JoiPlay com evidências nativas, sem executar nada por meio da L02.

**Estado preservado:** G01–G12 concluídas como engenharia GitHub; L00/L01/L02 são ferramentas documentais; Sinnoh continua `planned`, **R07/R08/R09 pendentes, 0/44 testes nativos e B/C/D 0/13**.

**Próxima fase segura sugerida — L03:** preparar uma matriz de reconciliação manual de evidências **sem dados privados** e um protocolo de aceite separado para autorizar *somente o planejamento* de QA futura. Isso não executa Game.exe, Windows Sandbox ou JoiPlay nem libera instalação.
