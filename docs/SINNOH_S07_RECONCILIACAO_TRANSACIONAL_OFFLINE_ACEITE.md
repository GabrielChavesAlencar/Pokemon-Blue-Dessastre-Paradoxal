# S07 — Entrega de código 29/32: reconciliação de remapeamento, staging e rollback

**Escopo desta entrega:** concluir somente a **camada de código** do importador transacional, com auditoria estática e testes sintéticos. O subfluxo de **aceite nativo R07–R09 continua 6/9 e parcial**, pois faltam fontes autorizadas, MapInfos/MapIDs reais e Game.exe/JoiPlay.

## Implementação

- [Novo reconciliador](../scripts/regions/sinnoh_s07_reconcile.py) reconstrói o plano de remapeamento com o código original `make_plan`, compara todos os campos (MapIDs, símbolos, SHA-256, vínculos estáticos, listas protegidas e flags) e recusa plano manipulado, mesmo que alguém recalcule seu hash. Reconfere ocupação real de `game/Data` e cruza o candidato com as **três** reservas futuras R07 (Kanto, Johto, Hoenn).
- Sem reservas locais, o reconciliador responde **`BLOCKED_NATIVE_OR_FUTURE_RESERVATIONS`**, não sucesso. Com reservas coerentes, o estado máximo é **`RECONCILED_FOR_MANUAL_REVIEW_NOT_APPROVED`**. Em ambos os casos `r07_complete=false`, `r08_real_maps_imported=false`, `r09_game_exe_joiplay_tested=false`, `can_install=false`.
- [Rollback reforçado](../scripts/regions/sinnoh_staging_transaction.py): confere formato e campos completos do manifesto, assinatura original do dry-run, destino canônico, hashes e tamanhos, diretórios adicionais inesperados, identidade do stage e ausência de symlinks antes de apagar somente a pasta correspondente em `.blue-work/sinnoh-stage`.
- [19 testes S07](../tests/test_sinnoh_s07_reconcile.py) verificam bloqueio por fonte/reserva ausentes, conflito com Hoenn, alteração do baseline ou dos MapIDs, referência de warp adulterada, plano com `can_install` falso, compatibilidade de plano anterior, ausência de writes e rollback de stage alterado. Runner CH19, S30 e documentação foram atualizados.

## Como usar com dados locais autorizados

Os documentos `source-audit.json` (auditoria RXDATA real) e `candidate.json` (plano criado por `plan_sinnoh_remap.py`) devem existir dentro de `.blue-work`; não são gerados pelo chat.

```bash
python scripts/regions/sinnoh_s07_reconcile.py --project . --source-audit .blue-work/source-audit.json --candidate .blue-work/candidate.json
```

O comando é **read-only** e devolve código 2 se faltar reserva/MapInfos ou houver fraude/conflito. O resultado máximo é revisão manual, **nunca** alteração do jogo.

## Progresso e bloqueios

**Barra A 29/32 (90%) apenas para entregáveis de engenharia**, 3 parciais (S13, S14, S31), 0 pendentes; **Barra E 20/20**, B/C/D 0/13. O subfluxo nativo R07–R09 **não avançou de 6/9**: falta auditar reservas reais de Kanto/Johto/Hoenn, converter os mapas com fonte licenciada e validar os 44 casos nativos Windows/Android. Estes limites não podem ser supridos por testes sintéticos e não serão considerados jogáveis.
