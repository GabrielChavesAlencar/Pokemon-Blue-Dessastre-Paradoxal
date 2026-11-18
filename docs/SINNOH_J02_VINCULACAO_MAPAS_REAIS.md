# Sinnoh J02 — vínculos reais de mapas para primeiro piloto jogável

**18/11/2026.** J01 foi integrada na `main` pelo PR #222 (merge `066aa6a0614342a14262b80c1eefcd80ca126047`). A J02 adiciona código de vinculação de mapas RXDATA reais, **sem** afirmar instalação.

## Fonte já auditada

Auditoria B00 da fonte fornecida pelo usuário (`Pokemon World V18.zip`, árvore `Pokemon Journeys V18`; SHA-256 `ca6226a...`) identificou **quatro mapas com terreno** relevantes ao piloto:

| Símbolo do piloto | ID na fonte original | Dimensão | Conteúdo de terreno |
|---|---:|---:|---|
| `SINNOH_TWINLEAF_TOWN` | 209 | 86×36 | Presente, 0 eventos |
| `SINNOH_ROUTE_201` | 227 | 90×29 | Presente, 0 eventos |
| `SINNOH_SANDGEM_TOWN` | 210 | 38×33 | Presente, 0 eventos |
| `SINNOH_ROUTE_202` | 228 | 68×35 | Presente, 0 eventos |

Arquivo com hashes reais desses quatro mapas: [`sinnoh-j02-map-source-catalog.json`](../data/regions/sinnoh-j02-map-source-catalog.json), ancorado no [B00](../data/regions/sinnoh-b00-actual-source.json).

**Cinco mapas reais não estão disponíveis nesse material:** quarto do jogador, 1º andar da casa, casa do Barry, Lago Verity e laboratório do Rowan. Os mapas de referência `4 Lakes NC` (263), `Sinnoh Labs` (272) e `Sinnoh Interiors` (5) são **placeholders vazios de 20×15**; reutilizá-los como mapas jogáveis seria falso.

## Código executável J02

[`bind_sinnoh_playable_j02.py`](../scripts/regions/bind_sinnoh_playable_j02.py) faz:
1. Conferência de SHA do catálogo contra fonte B00 e contrato dos 9 mapas/16 portais.
2. Leitura **inerte**, sem executar scripts/eventos, dos nove arquivos `MapNNN.rxdata` reais; SHA-256, dimensões, tabela de tiles não vazia.
3. Auditoria da instalação `game/Data/MapInfos.rxdata`; rejeição de MapIDs de destino repetidos, já ocupados ou listados como reservados no arquivo local informado.
4. Geração opcional de relatório apenas em `.blue-work/sinnoh-jogavel`, sem sobrescrita ou alterações em `game/`/saves.

Execução em modo diagnóstico (não instala nada):
```sh
python scripts/regions/bind_sinnoh_playable_j02.py
```

Quando todos os 9 mapas **reais e autorizados** existirem, a integração receberá, em `.blue-work`, dois arquivos JSON locais com o seguinte contrato:

```json
{
  "schema": 1,
  "region": "SINNOH",
  "mode": "J02_LOCAL_BINDING_CANDIDATE",
  "baseline_mapinfos_sha256": "HASH_SHA256_DO_MAPINFOS_DA_INSTALACAO",
  "source_mapinfos_sha256": "HASH_SHA256_DO_MAPINFOS_DA_FONTE",
  "source_archive_sha256": "HASH_SHA256_DO_ZIP_OU_NULL_PARA_PASTA",
  "bindings": [
    {
      "symbol": "SINNOH_TWINLEAF_TOWN",
      "source_id": 209,
      "destination_id": 442,
      "source_sha256": "HASH_SHA256_REAL_DO_MAPA",
      "width": 86,
      "height": 36
    }
  ]
}
```

O trecho contém **apenas uma linha ilustrativa**, não um plano utilizável; os nove registros têm de estar em ordem exata do contrato e IDs de destino devem ser escolhidos após a auditoria real de ocupação. O valor 442 é um exemplo, **não uma reserva confirmada**. Não completar o JSON com IDs imaginados.

O JSON opcional de reservas locais usa `schema=1`, `region="SINNOH"`, `mode="LOCAL_RESERVATIONS_CANDIDATE"`, `baseline_mapinfos_sha256` real e `protected_ids` (lista de IDs protegidos) e **não certifica R07**.

```sh
python scripts/regions/bind_sinnoh_playable_j02.py --source "FONTE_AUTORIZADA.zip" --game-data "PASTA/game/Data" --bindings ".blue-work/sinnoh-jogavel/bindings.json" --reservations ".blue-work/sinnoh-jogavel/reservations.json"
```

O JSON de saída do melhor caso só afirma `NINE_LOCAL_CANDIDATES_VERIFIED_NOT_INSTALLABLE`. Direitos individuais R08, reservas futuras R07 e validação nativa R09 **continuam reprovados/pendentes**, mesmo com todos os nove mapas. **Nenhum arquivo do ZIP nem sprites é publicado por este PR**.

## Barra J, sem falsa conclusão

- Engenharia executável: J01 + J02 = **2/8 (25%)**, condicionada a CI passar.
- Mapas físicos instalados: **0/9**.
- Referências históricas com terreno: **4/9**, não instalações.
- Mapas reais ausentes no arquivo auditado: **5/9**.
- QA nativa: **0/8 fases comprovadas** e **0/44 casos G12**.

Próxima etapa [J03 — staging isolado de terrenos e tilesets](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/224), somente com recursos permitidos. O portal terá botão permanente: abre uma mensagem pronta para o ChatGPT executar a fase seguinte **após o usuário enviá-la**. Não inicia código em segundo plano.
