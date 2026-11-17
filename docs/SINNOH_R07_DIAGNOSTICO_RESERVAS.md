# Sinnoh S07/R07 — diagnóstico de reservas de MapIDs (continua pendente)

**Objetivo:** identificar conflitos entre mapas reais já instalados e reservas futuras de Kanto, Johto e Hoenn **antes** de aceitar qualquer remapeamento de Sinnoh. Este diagnóstico **não** implanta mapas, não confere direitos e **não conclui R07**.

## Ferramentas

O arquivo [`SINNOH_DIAGNOSTICAR_PENDENCIAS.bat`](../SINNOH_DIAGNOSTICAR_PENDENCIAS.bat) executa, por duplo clique no Windows, o [auditor de reservas](../scripts/regions/audit_sinnoh_r07_reservations.py). Nenhum PowerShell é necessário. O script apenas lê o baseline `game/Data/MapInfos.rxdata` e nomes de `MapNNN.rxdata` e grava um resumo em:

`.blue-work/sinnoh-diagnostics/r07-reservations.json`

**Não acessa, migra ou apaga saves.** O código de saída é 2 quando faltam insumos; isso é um bloqueio esperado, não um erro de instalação.

## Evidências ainda necessárias

1. **Baseline local real:** `game/Data/MapInfos.rxdata` e mapas de Decades/Kanto/Johto/Hoenn atualmente instalados; é proibido substituir por arquivos sintéticos em produção.
2. **Reservas ainda não instaladas:** um manifesto privado para cada região, em `.blue-work/sinnoh-reservations/kanto.json`, `johto.json`, `hoenn.json`. Cada arquivo exige `schema=1`, `region` correto, `kind=LOCAL_FUTURE_MAP_ID_RESERVATIONS`, `baseline_mapinfos_sha256` do mesmo baseline, `future_reserved_map_ids` reais auditados, `ownership_evidence` textual identificando a origem, `reviewed_locally=true` após revisão humana e `read_only=true`. **Não crie IDs hipotéticos só para preencher os campos.**
3. **Plano candidato de Sinnoh:** um arquivo de `plan_sinnoh_remap.py` com `mode=REMAP_CANDIDATE_ONLY`, fonte RXDATA autorizada e SHA-256 de cada mapa, salvo dentro de `.blue-work`; use o parâmetro `--plan` somente depois de construir esse arquivo.

O auditor informa IDs ocupados, reservas conflitantes e MapIDs futuros faltantes. Mesmo que nenhuma colisão seja identificada, o estado máximo é `CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED` com `r07_complete=false`. **Uma declaração local de revisão não equivale a comprovação de reserva exaustiva ou licença.** O intervalo 600–999 continua indisponível para o remapeamento compartilhado; IDs de quatro dígitos continuam bloqueados.

## Evidência de CI

- [Matriz S30 — run 43998666938](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43998666938): job Python e manifesto `success`, exigindo o script, BAT e os **16 testes R07**; não precisa de arquivos do usuário para os fixtures.
- [CH19 — run 43998666939](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43998666939): regressões Python e Ruby aprovadas. **Nenhum** MapInfos do usuário, mapa autorizado ou save real foi inspecionado por esses testes.
- No repositório os MapIDs futuros **não** estão provados; o relatório R07 de uma máquina real segue bloqueado até os insumos locais existirem.

## Testes e pendências

[16 testes R07](../tests/test_sinnoh_r07_reservations.py) validam ausência de baseline, referências de região, SHA do MapInfos, manifests ausentes/adulterados, conflito com Decades e outras reservas, symlinks, input fora de `.blue-work` e relatório sem modificação dos arquivos originais. Testes usam RXDATA sintético; não há cópia local real no GitHub.

**Estado mantido: S07 `partial`, R01–R06 completos, R07/R08/R09 pendentes (6/9); Barra A não ganha ponto pela R07.** R08 requer converter os mapas reais autorizados, e R09 exige compilar e testar a cópia QA no Game.exe e JoiPlay com saves isolados. B/C/D continuam 0/13; 44 casos nativos não executados.
