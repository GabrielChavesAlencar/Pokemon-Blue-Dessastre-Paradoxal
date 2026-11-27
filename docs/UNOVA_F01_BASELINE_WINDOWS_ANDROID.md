# Unova F01 — ocupação de MapIDs no Windows e Android

Auditoria de 27/11/2026 sobre a main `1ca1e243d8f27773b2acd93d527aa6dd3e8977a7`.

**Bloqueio confirmado em fontes públicas:** o código declara 452–595 para instalação local de Sinnoh e o manifesto público do Android declara quatro mapas de Kanto em 596–599. O intervalo histórico **518–599** cruza essas duas faixas. O instalador compartilhado de Sinnoh também aceita overlays na faixa 442–599.

| Baseline | Evidência | MapIDs observados no intervalo |
| --- | --- | --- |
| Windows, implementação compartilhada de Sinnoh | `SHARED_IDS` define a faixa padrão local em `scripts/regions/sinnoh_shared.py`. | 518–595 |
| Android, release pública 234 multirregional | 566 MapNNN rastreados no manifesto. MapInfos e recibo Kanto do delta conferem com os hashes publicados. Origem Kanto 68–71 mapeada para 596–599. | 596–599 |

O par público anterior ao lote aponta para `4c21940ae4936adb1919c0052007e3f2812b077d`. Para o Android, conferimos o canal, a revisão, o SHA-256 do manifesto `3b0477bf0d6c37e7b9c79077d37ddda50c87b2f991527631662fb35a82d92170`, o hash do patch `4cf28d3303e3fdb8bef73e98615e9f75ebe214ae90cc7f44c2a06bfdf487f5fc` e o MapInfos SHA-256 `a967108706a79e5810ec8c98ca189905a6ba25d6fe1f74eba1da08d24be0f3c2`. [Release Windows 1628](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/battle-hub-1628-4c21940) · [Release Android 234](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-multiregion-234-4c21940)

## Reproduzir

```powershell
python scripts/regions/audit_unova_a04_mapids.py --base-data "<instalação Windows>" --write
python scripts/regions/audit_unova_a05_candidates.py --a04-report "<relatório A04>" --android-manifest "<release update.json>" --write
```

A08–A12 agora leem `blue-sinnoh-shared.json`. A12 identifica separadamente a faixa local de Sinnoh 452–595 e a faixa de validação de overlays 442–599, inclusive em uma base em que Sinnoh ainda não foi instalado. O BAT portátil contém as versões atualizadas dos auditores. Os 92 IDs alternativos históricos continuam em revisão. O destino efetivo do MapID 3 e a migração de saves exigem validação no motor conforme o roadmap.

## Pendências para o piloto

- **F01, remap:** escolher um conjunto comum aos dois canais após revisar referências dinâmicas, ownership, saves e espaço para os mapas e interiores. Nenhum ID foi atribuído.
- **F01, fonte e direitos:** a decisão deve usar recursos originais do Blue ou comprovadamente autorizados. Não há recibo por asset que aprove o uso do World V18. O [PR A16 #195](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/195) continua aberto e em conflito com a main. O [PR #208](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/208) segue aberto e trata de FRLG.
- **F06/F09/F13/F14:** faltam portas/eventos e saves testados no Game.exe de QA, aparelho com JoiPlay e releases pareadas de Unova. A 0/8 e U 0/32.
