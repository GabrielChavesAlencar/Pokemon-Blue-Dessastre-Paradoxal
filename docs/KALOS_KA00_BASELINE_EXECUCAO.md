# Kalos KA00 — baseline antes de reservar MapIDs

Início da execução de [KA00–KA31](KALOS_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md), autorizado para Kalos. Esta fase é somente leitura e evidência; não instala Kalos, não reserva IDs, não altera a seleção regional nem publica uma versão do jogo.

## Corte exato de partida

- Main lida: `665f0b828ddf5f22bbca6a238a8bfb2cd82d33b9` (árvore `195158174ed58251ff484151cea011931c697e25`). Hoenn H03 [#403](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/403) e H04 [#386](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/386) já preservados.
- Kanto Celadon [#395](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/pull/395) observado em `ae96941364f285099e1e8da82c9dc81fe1309cf0`. IDs 276–279 tratados como **bloqueados preventivamente** para Kalos. Não reservar nem editar o branch de Kanto.
- Prova de base limpa: clone descartável do Decades na revisão fixada pelo instalador. Prova com regiões: inventário do ZIP **histórico** [Android 247](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/android-multiregion-247-02732ea), verificado em tamanho e SHA-256, sem extração e sem republicar dados. Não representa instalação atual ou aparelho.
- KA00 reutiliza o coletor inerte de MapInfos/arquivos do [auditor A04](UNOVA_A04_MAPIDS_MULTIRREGIONAIS.md) e o critério de propriedade do [auditor H00](../scripts/regions/audit_hoenn_h00.py): ocupação física, índice, manifesto, ausências e vínculos conflitantes são coisas diferentes. O CI publica somente JSON de evidência sem nomes de jogadores, saves, assets, binários ou RAR.

| Proteção | Tratamento |
|---|---|
| Kanto lançado | O contrato K05 usa 609–621, dentro da antiga janela atribuída a Johto. O histórico sozinho não prova propriedade ou vaga; preservar os 13 IDs, sem acusar colisão física a partir de faixas. |
| Johto e Hoenn | Preservar limites conservadores 600–699 e 700–999 e validar marcadores reais. A ausência de um marcador não libera a faixa. |
| Sinnoh e Unova | Não tocar o hold 442–517, MapIDs já mapeados de Sinnoh, ou a janela candidata 518–599. Proposta antiga de Unova não é autorização de alocação. |
| Arquivos compartilhados | A via de integração inclui RegionStart, RegionTravel, respawn, instalador e atualizador. A prova registra hashes; só alterar depois de qualificação incremental e checagem do resultado da fusão com main atual. |
| Quatro dígitos | Nenhum suporte assumido. Reservas, limites do editor/Windows/JoiPlay, referências indiretas e divergências de dados serão confrontados em KA02 antes de instalar mapas. |

## Saída desta fase

O workflow testa regras negativas e compara uma base limpa com uma instalação histórica específica. Uma prova verde permite concluir **KA00** como baseline, não libera KA02, jogabilidade ou publicação Windows/Android. Em KA01, usar o [atlas](KALOS_KD05_ATLAS_VISUAL_E_TILES_KANTO.md) e preparar trabalho autoral só com procedência validada. Antes da alocação de qualquer ID em KA02, exigir inventário físico atual com a base de release relevante, revisão dos manifestos e reservas ativas, e prova nativa suficiente. Manter o catálogo de Kalos `planned` até existir um lote aceito.
