# Sinnoh S07/R07 — diagnóstico de reservas de MapIDs (continua pendente)

**Objetivo:** identificar conflitos entre mapas reais já instalados e reservas futuras de Kanto, Johto e Hoenn **antes** de aceitar qualquer remapeamento de Sinnoh. Este diagnóstico **não** implanta mapas, não confere direitos e **não conclui R07**.

## Ferramentas

O arquivo [`SINNOH_DIAGNOSTICAR_PENDENCIAS.bat`](../SINNOH_DIAGNOSTICAR_PENDENCIAS.bat) executa, por duplo clique no Windows, o [auditor de reservas](../scripts/regions/audit_sinnoh_r07_reservations.py). Nenhum PowerShell é necessário. O script apenas lê o baseline `game/Data/MapInfos.rxdata` e nomes de `MapNNN.rxdata` e grava um resumo em:

`.blue-work/sinnoh-diagnostics/r07-reservations.json`

**Não acessa, migra ou apaga saves.** O código de saída é 2 quando faltam insumos; isso é um bloqueio esperado, não um erro de instalação.

## Atualização B02 — inventário e códigos já confrontados (17/11/2026)

A [auditoria B02](SINNOH_B02_RESERVAS_REGIONAIS_2026-11-17.md) cruzou o ZIP real do Decades (**648 MapIDs ocupados**) com as restrições documentadas: Johto 600–699 e Hoenn 700–999. A região de Kanto possui instalação com destinos dinâmicos; **suas reservas futuras ainda não foram apresentadas**. O intervalo 442–599 é fisicamente vazio, mas não está reservado a Sinnoh. **R07 segue parcial** e o auditor R07 exige manifestos privados vinculados ao baseline, sem prova artificial.

## Atualização B03 — modelos de reserva futura, ainda não validados

A [B03](SINNOH_B03_RESERVAS_E_TILESETS_2026-11-17.md) confirmou em código a origem de cada faixa protegida e criou [três modelos privados a preencher](../data/regions/sinnoh-b03-reservation-review-templates.json), vinculados ao SHA do `MapInfos` recebido em B01. Os modelos têm listas vazias e `reviewed_locally=false` de propósito; **não constituem evidência R07**. O inventário real não incluiu `blue-kanto-install.json`, `blue-johto-main-preview.json` nem `blue-hoenn-install.json`, e não permite inventar reservas futuras. Os 250 IDs fisicamente vazios, inclusive 442–599, não foram alocados; R07 continua parcial.

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

**Estado do subfluxo nativo mantido: R01–R06 completos, R07/R08/R09 pendentes (6/9), sem aceite nativo.** A entrega S07 de engenharia foi finalizada em código (Barra A **29/32** somente após CI/merge) pelo [reconciliador](../scripts/regions/sinnoh_s07_reconcile.py), mas **R07 não ganhou ponto nem passou a completo**. A aprovação do código não concede instalação, MapIDs, direitos ou jogabilidade. R08 requer converter os mapas reais autorizados, e R09 exige compilar e testar a cópia QA no Game.exe e JoiPlay com saves isolados. B/C/D continuam 0/13; 44 casos nativos não executados.
