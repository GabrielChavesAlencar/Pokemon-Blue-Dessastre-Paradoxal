# Sinnoh L01 — Exportador local opcional de relatórios sanitizados

**17/11/2026 · Continuação da issue #168.** A L01 é **somente código versionado no GitHub**. Não foi executada no computador do usuário, não abre `Game.exe`, não inicia Windows Sandbox/JoiPlay, não lê saves, PNGs, mapas, ZIPs ou `private-baseline.json`, não transmite arquivos e não muda R07/R08/R09, **B/C/D 0/13** nem os **44 casos nativos pendentes**.

## O que foi construído

- [Exportador local, opcional e sem rede](../scripts/regions/export_sinnoh_l01_reports.py): cinco projetores de B09/B10/B11/R07/R08 com **campos de entrada estritamente controlados**. A única entrada possível são **sete relatórios JSON explicitamente preparados** em uma pasta local fixa; não há busca recursiva no computador.
- Reutiliza a validação [G01](../scripts/regions/audit_sinnoh_g01_b09_receipt.py) do par recibo/dry-run B09, com hash de plano associado ao recibo; B10 precisa ter o mesmo `source_clone_sha256`.
- Antes de mostrar qualquer saída, submete a projeção ao auditor [L00](../scripts/regions/audit_sinnoh_l00_readiness.py), que impede declarações falsas de aprovação ou jogabilidade.
- [30 testes L01](../tests/test_sinnoh_l01_exporter.py): casos positivos sintéticos, falsificações de SHA, inconsistência de contagens, rede/clipboard, falso `watch_unchanged`, vazamento de identificadores de sessão B11, symlinks e nenhuma leitura de saves.
- [Workflow CI L01](../.github/workflows/sinnoh-l01-sanitized-export.yml): dois jobs, regressões L00/G01/G12/B11 e **sem upload de artifacts**.

## Entradas (somente relatórios existentes, nunca arquivos do jogo)

**A ferramenta só lê nomes fixos** dentro da pasta privada do checkout local `.blue-work/sinnoh-l01-source/`. O operador poderá preparar esses arquivos **voluntariamente em outro momento**:

| Arquivo local de entrada | Origem esperada | Projeção |
| --- | --- | --- |
| `b09-receipt.json` | Recibo público da operação B09 | B09, acompanhado obrigatoriamente de dry-run |
| `b09-dry-run.json` | Dry-run B09 do **mesmo** plano/clone, validado por G01 | SHA do plano; sem `relative_path`, nomes de arquivos ou bytes do jogo |
| `b10-session.json` | Resumo B10 `WSB_CONFIG_PREPARED_NOT_LAUNCHED` | Política de mapeamento somente leitura, rede/clipboard desligados, VM não iniciada |
| `b11-before.json` | Resumo público B11 anterior ao teste | Contagens/escopo, **não exporta** `watch_id`, `clone_sha256`, `config_relative_path` |
| `b11-after.json` | Resumo público B11 posterior **do mesmo watch_id** | Contagens/alterações; nunca inclui HMAC, baseline, arquivos de save ou nomes |
| `r07-diagnostic.json` | Relatório de diagnóstico R07 do script oficial | Contagem agregada de regiões e colisões, sem IDs de reserva ou observações humanas |
| `r08-review-count.json` | Pequeno agregado preenchido manualmente, **sem inventário de ativos** | Contagem de revisões de permissões (0–14), **não** direitos aprovados |

O exportador aceita arquivos de entrada contendo apenas os campos das versões oficiais dos scripts. **Campos extras, mesmo aparentemente inofensivos, fazem a exportação falhar**, inclusive `private-baseline.json`, `hmac_key`, nomes, caminhos particulares, dados de imagem e listas de saves. Informações como `relative_path` ou `watch_id`, presentes nos resumos originais oficiais, são verificadas quando necessário, mas **nunca copiadas ao resultado**.

Para R08 — que ainda não possui recibo automático aprovado — o único formato de entrada aceito é:

```json
{
  "schema": 1,
  "region": "SINNOH",
  "stage": "R08",
  "kind": "MANUAL_AGGREGATE_REVIEW_COUNT_ONLY",
  "status": "RIGHTS_REVIEW_PENDING",
  "source_expected_png_count": 14,
  "per_asset_licenses_reviewed_count": 0,
  "source_asset_rights_verified": false,
  "r08_complete": false
}
```

A contagem é uma **declaração documental manual**. Mesmo 14/14 não prova licença, direito de redistribuição, existência/instalação dos arquivos ou aprovação de R08.

## Operação local voluntária no futuro

**Esta L01 só publica o código; os comandos abaixo não foram executados no PC do usuário.** Quando os relatórios já existirem e o operador decidir prepará-los:

1. Colocar os resumos JSON escolhidos na pasta fixa `.blue-work/sinnoh-l01-source/`. B09 precisa de seus dois arquivos; B10 depende desse par; B11 precisa de ambos os relatórios de um mesmo acompanhamento. R07 e R08 podem ser usados separadamente. A ferramenta não executa nenhum desses estágios.
2. **Pré-visualizar, sem escrever arquivos:**

   ```bat
   python scripts\regions\export_sinnoh_l01_reports.py --preview
   ```

3. Somente após verificar o conteúdo, **gravar voluntariamente um único arquivo sanitizado local:**

   ```bat
   python scripts\regions\export_sinnoh_l01_reports.py --write
   ```

A gravação é atômica em **`.blue-work/sinnoh-l00-input/public-reports.json`**, com recusa de symlinks e validação L00 prévia. É o caminho fixo já aceito por `audit_sinnoh_l00_readiness.py --workspace-reports`.

**Não existe upload automático, envio para GitHub, publicação em artifacts, cópia para clipboard, telemetria ou conexão com seu computador.** O proprietário deve **revisar todo o JSON** antes de decidir se deseja ou não compartilhá-lo. Não enviar o diretório `.blue-work` completo, recibos B11 originais, ZIPs, `Game.exe`, `private-baseline.json`, imagens nem saves.

## Segurança e limites

- B09/ B10: comparações de plano/recibo e contagens não constituem auditoria física independente nem verificam que um jogo abre.
- B10: o status de WSB preparada **não confirma que a VM foi iniciada**. O exportador não abre a Sandbox, nem instala a região.
- B11: `watch_unchanged` só cobre os diretórios explicitamente monitorados; o exportador impõe `coverage_is_partial=true`, nunca isolamento global.
- R07: mesmo com zero colisões documentadas, o mapa não está automaticamente reservado/aprovado.
- R08: revisão manual não equivale a permissões legais aprovadas.
- A L01 não altera o portal: Sinnoh continua `planned`, **0/44 casos nativos verificados**, **B/C/D 0/13**.

## Próxima fase segura sugerida

**L02 — revisão de consistência dos relatórios L00/L01 e pacote de handoff documental**, com bloqueios de origem/recibo falsificado e um checklist privado para escolha de QA futura em VM. Continua GitHub-only: não lê o PC, não executa Game.exe/Windows Sandbox/JoiPlay, não muda saves nem declara Sinnoh jogável.
