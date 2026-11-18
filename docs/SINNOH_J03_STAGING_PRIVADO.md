# Sinnoh J03 — geometria/tilesets privados em staging isolado

**J03 de engenharia** (não jogo instalado). O PR #225 de J02 foi integrado à main como commit \`479a6eecb1cca46288b0b5e3442151061426d3f0\` após todos os 10 checks aprovados.

## Alcance real

A fonte B00 de Pokémon World/Journeys V18, auditada sem execução, contém terreno não vazio reconhecido para **Twinleaf Town (209), Rota 201 (227), Sandgem (210) e Rota 202 (228)**. Faltam **5 dos 9 mapas essenciais** (quarto, casa 1F, casa Barry, Lago Verity, laboratório Rowan). Esses recursos não estão autorizados nem instalados no GitHub. **Não foi criado um stage com dados de terceiros** nesta fase; CI usa fontes *sintéticas* próprias.

O novo [preparador J03](../scripts/regions/prepare_sinnoh_playable_j03.py) reaproveita o leitor Ruby Marshal sem execução, o [vinculador J02](../scripts/regions/bind_sinnoh_playable_j02.py), o núcleo de filtragem de geometria do [conversor existente](../scripts/regions/convert_sinnoh_geometry.py) e o [staging transacional com rollback](../scripts/regions/sinnoh_staging_transaction.py).

- Requer a instalação real \`game/Data\` **somente para leitura**, fonte local original e MapInfos com SHA congelado.
- Requer **quatro** MapIDs de destino \`442–495\` distintos e vazios no baseline; recusa IDs ocupados, intervalos legados 800–805 e candidatos em reservas locais.
- Verifica o hash de cada mapa B00, dimensões, tabela de terreno realmente não vazia, gráfico PNG e hash por asset, além de uma declaração **local** de revisão para uso **privado e não redistribuível**.
- Reconstrói quatro \`Data/MapNNN.rxdata\` **sem eventos, scripts, encontros, músicas ou NPCs do doador**; junta cópias locais de MapInfos/Tilesets e rebatiza imagens por hash. O mapa original não é alterado.
- Faz **dry-run padrão sem escrever nada**. Staging real exige uma segunda invocação com SHA-256 exato do dry-run e cria pasta inédita somente em \`.blue-work/sinnoh-stage\`. Verificação posterior é read-only; rollback só apaga estágio intacto com assinatura/hash exatos.
- Não lê/modifica saves, não toca \`game/\`, não copia Game.exe/JoiPlay, não publica ZIP/PNG/Map*.rxdata. A declaração local não constitui licença validada: R07/R08/R09 permanecem pendentes e \`can_install=false\`.

## Entradas exigidas (arquivos locais dentro de .blue-work)

Crie \`.blue-work/sinnoh-jogavel/j03-bindings.json\` com campos exatos:

\`\`\`json
{
  "schema": 1,
  "region": "SINNOH",
  "mode": "J03_FOUR_TERRAIN_DRY_RUN",
  "baseline_mapinfos_sha256": "HASH_REAL_DO_MAPINFOS_INSTALADO",
  "source_mapinfos_sha256": "HASH_REAL_DO_MAPINFOS_DA_FONTE",
  "source_archive_sha256": null,
  "bindings": [
    {
      "symbol": "SINNOH_TWINLEAF_TOWN",
      "source_id": 209,
      "destination_id": 0,
      "source_sha256": "SHA_REAL_DO_MAPA_209",
      "width": 86,
      "height": 36
    }
  ]
}
\`\`\`

**É um esquema parcial ilustrativo, sempre inválido até preencher os quatro registros** e os SHAs reais. O destino \`0\` é *deliberadamente inválido* para evitar copiar um ID não comprovado. Para ZIP, \`source_archive_sha256\` é o SHA do ZIP atual; para pasta, \`null\` e o conteúdo dos arquivos MapInfos e MapNNN continua obrigatoriamente pinado. A ordem exigida é Twinleaf 209, Route 201 227, Sandgem 210, Route 202 228; cada destino deve ser escolhido após verificar os mapas ocupados/reservados.

\`.blue-work/sinnoh-jogavel/j03-reservations.json\`:

\`\`\`json
{"schema":1,"region":"SINNOH","mode":"LOCAL_RESERVATIONS_CANDIDATE",
 "baseline_mapinfos_sha256":"HASH_REAL_DO_MAPINFOS_INSTALADO",
 "protected_ids":[1,600,700]}
\`\`\`

Os IDs acima são **exemplo de formato, não um inventário completo**, não provam R07 e jamais autorizam instalar. Não declare lista vazia sem revisar reservas reais.

\`.blue-work/sinnoh-jogavel/j03-asset-review.json\`:

\`\`\`json
{"schema":1,"region":"SINNOH","mode":"J03_LOCAL_ASSET_REVIEW",
 "allowed_use":"LOCAL_PRIVATE_QA_ONLY_NO_REDISTRIBUTION",
 "source_mapinfos_sha256":"HASH_REAL_DO_MAPINFOS_DA_FONTE",
 "source_archive_sha256":null,
 "reviewed_locally":false,
 "asset_sha256":{"Graphics/Tilesets/TILESET.png":"SHA_REAL_DO_PNG"}}
\`\`\`

Preencher *todos os gráficos efetivamente usados*, com hashes reais e direito/autorização para cópia privada; \`reviewed_locally=true\` só quando houve revisão humana local. Mesmo com isso, **R08 não é aprovada automaticamente** e não é permitido redistribuir. Nenhum documento do GitHub ou teste sintético comprova direito de uso.

## Comandos

**Diagnóstico público sem fonte** (falha de forma segura, código 2):

\`\`\`sh
python scripts/regions/prepare_sinnoh_playable_j03.py
\`\`\`

**Dry-run privado**:

\`\`\`sh
python scripts/regions/prepare_sinnoh_playable_j03.py --source "CAMINHO_DA_FONTE_LOCAL.zip" --game-data "CAMINHO_DO_GAME/Data" --bindings ".blue-work/sinnoh-jogavel/j03-bindings.json" --reservations ".blue-work/sinnoh-jogavel/j03-reservations.json" --asset-review ".blue-work/sinnoh-jogavel/j03-asset-review.json" --label j03-twinleaf
\`\`\`

**Staging após revisar hash e conteúdos do dry-run** (não instala no jogo):

\`\`\`sh
python scripts/regions/prepare_sinnoh_playable_j03.py --source "CAMINHO_DA_FONTE_LOCAL.zip" --game-data "CAMINHO_DO_GAME/Data" --bindings ".blue-work/sinnoh-jogavel/j03-bindings.json" --reservations ".blue-work/sinnoh-jogavel/j03-reservations.json" --asset-review ".blue-work/sinnoh-jogavel/j03-asset-review.json" --label j03-twinleaf --stage --expected-dry-run "SHA256_DO_DRY_RUN"
\`\`\`

**Verificar e reverter (somente stage J03 imutável)**:

\`\`\`sh
python scripts/regions/prepare_sinnoh_playable_j03.py --label j03-twinleaf --verify-stage --expected-dry-run "SHA256_DO_DRY_RUN"
python scripts/regions/prepare_sinnoh_playable_j03.py --label j03-twinleaf --rollback --expected-dry-run "SHA256_DO_DRY_RUN"
\`\`\`

**Não execute esses comandos com saves pessoais ou uma fonte para a qual não tenha autorização.** O stage é exclusivamente local e não deve ser compartilhado; o instalador do jogo principal nunca é alterado.

## Critérios, testes e progresso

A nova suíte \`tests/test_sinnoh_j03_private_staging.py\` testa 41 cenários sintéticos, incluindo hashes, colisões, fonte alterada, mapa vazio, PNG ausente, revisão local ausente, symlink, entrada maliciosa, stage alterado, rollback e preservação do save. A CI reexecuta J02, o conversor existente, transações e o build do portal.

- Código **J01+J02+J03 = 3/8 (37,5%)**, se checks aprovados;
- Mapas nativos instalados **0/9** e 5 mapas essenciais ausentes;
- Execuções nativas **0/44**; Game.exe/JoiPlay não executados; Sinnoh continua \`planned\`.

**Próxima:** [J04 — portais, NPCs e Poké Bolas físicas](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/226). O botão persistente do portal é alimentado pelo JSON da barra e recebe prompt J04. Avançar para compilação **exige mapas físicos e coordenadas/sprites reais**, não apenas os códigos.
