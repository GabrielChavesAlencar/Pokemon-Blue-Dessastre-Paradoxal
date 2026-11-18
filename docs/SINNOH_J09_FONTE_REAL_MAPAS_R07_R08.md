# J09 — Sinnoh fontes reais, cinco mapas ausentes e gates R07/R08/R09

Base: PR #237 J08 integrada, issue #236. Próxima retomada: issue #238 (J09-R1).

## Evidência recuperada da Biblioteca, somente metadados

Em 18/11/2026 a cópia privada do Pokemon World V18.zip foi lida inerte, sem extrair arquivos nem executar código. A integridade SHA-256 é:

- ZIP original de 208.057.674 bytes: ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35
- Data/MapInfos.rxdata: a5de4d870ae08aa3730942496734c7a0917505a6d435ff178ce5a10f73fc6495
- Data/Tilesets.rxdata: ddd1e57f033e9ad061870d2cb72288e17ab4f28bb2ace7cea69336a95f8cd1f1
- Data/Map209.rxdata, Twinleaf Town: 51835569951ca9cdb7832973946781b8258096e1118e6addea26a66a63d80e42
- Data/Map227.rxdata, Route 201: 6652a810c5d25f32d610021f88b2e949e55305fdd30bc684fa583d301976ba34
- Data/Map210.rxdata, Sandgem Town: f03bb0cfb97f7e807e950c26c9123e05aa49888f3b180323efd116e51c7ac34f
- Data/Map228.rxdata, Route 202: 3aa9c9e26c2121495e79fef489f23262876447222ed5e3ec563133225f925f35

São QUATRO arquivos de terreno encontrados, não quatro mapas instalados ou licenciados. Nenhum material binário ou doador foi redistribuído ao GitHub. Relatório público sanitizado: data/regions/sinnoh-j09-private-source-recheck.json.

**Ainda faltam 5 mapas físicos originais**, sem usar placeholders vazios: SINNOH_PLAYER_BEDROOM (quarto), SINNOH_PLAYER_HOUSE_1F (térreo), SINNOH_BARRY_HOUSE (casa Barry), SINNOH_LAKE_VERITY (lago), SINNOH_PROFESSOR_ROWAN_LABORATORY (laboratório). No doador, Map005 Sinnoh Interiors, Map263 4 Lakes NC e Map272 Sinnoh Labs têm 0 tiles e são INUTILIZÁVEIS.

## Ferramenta executável J09

Arquivo: scripts/regions/audit_sinnoh_playable_j09.py, somente leitura e sem executar scripts Ruby de terceiros.

Inspecionar original quando o arquivo estiver disponível de modo privado:

    python scripts/regions/audit_sinnoh_playable_j09.py --source-zip "CAMINHO_PRIVADO/Pokemon World V18.zip"

Esperado hoje: historical_exteriors_verified_this_run=4, authored_missing_maps_verified_this_run=0, missing_source_symbols com cinco mapas e can_install=false.

O operador que tiver CRIADO ou ADQUIRIDO LEGALMENTE os cinco mapas genuínos deve colocá-los, após revisão de direitos, apenas em diretório privado ignorado pelo Git:

    .blue-work/sinnoh-j09-authored/SINNOH_PLAYER_BEDROOM.rxdata
    .blue-work/sinnoh-j09-authored/SINNOH_PLAYER_HOUSE_1F.rxdata
    .blue-work/sinnoh-j09-authored/SINNOH_BARRY_HOUSE.rxdata
    .blue-work/sinnoh-j09-authored/SINNOH_LAKE_VERITY.rxdata
    .blue-work/sinnoh-j09-authored/SINNOH_PROFESSOR_ROWAN_LABORATORY.rxdata

O auditor exige cinco arquivos RXDATA distintos com objetos RPG::Map, tabela de terreno coerente, tiles desenhados e sem eventos de terceiros. Não inventa fontes, MapIDs, coordenadas, sprites ou autorização. Rejeita mapas vazios, eventos extras, cópias idênticas, arquivos fora da pasta privada e symlinks. Teste:

    python scripts/regions/audit_sinnoh_playable_j09.py --source-zip "CAMINHO_PRIVADO/Pokemon World V18.zip" --authored-dir ".blue-work/sinnoh-j09-authored"

## R07 — reservas globais de MapID

As opções --game-data e --r07-review só funcionam juntas. O diretório game/Data é inspecionado em modo read-only via auditor J02, sem ler saves. O arquivo privado .blue-work/j09-r07-review.json deve conter EXATAMENTE:

- schema: 1; region: SINNOH; stage: J09; mode: LOCAL_R07_RESERVATIONS_NOT_NATIVE_APPROVAL
- baseline_mapinfos_sha256, occupied_ids (todos ocupados reais), candidate_sinnoh_ids (nove IDs distintos de 442 a 517)
- reserved_by_region contendo DECADES, KANTO, JOHTO, HOENN e UNOVA, sem sobreposições com as nove candidatas ou IDs ocupados
- locally_reviewed: true APENAS depois de revisão humana, review_reference verificável

Passar nessa estrutura NÃO homologa reservas de jogo: é uma declaração local, sem aprovação independente. Qualquer colisão ou baseline desatualizado bloqueia.

## R08 — direito por arquivo de mapa

A opção --r08-review requer os cinco mapas originais, além do ZIP B00. O arquivo privado .blue-work/j09-r08-review.json contém EXATAMENTE:

- schema: 1; region: SINNOH; stage: J09; mode: LOCAL_R08_MAP_RIGHTS_NOT_REDISTRIBUTABLE
- locally_reviewed: true somente com revisão real; redistribution_authorized: false; review_reference e maps
- maps: os nove símbolos, cada um com sha256, basis (ORIGINAL_USER_AUTHORED, EXPLICIT_PRIVATE_USE_PERMISSION ou LICENSED_FOR_PRIVATE_QA), permission_evidence individual e private_qa_permitted true somente quando aplicável

O auditor compara cada SHA, mas NÃO confere independentemente direitos legais. Tilesets, sprites, áudio e autorização final continuam dependentes dos gates J03/J06 e revisão humana. Direitos não são criados por escrever um JSON.

--require-complete falha se faltar qualquer um dos nove mapas, R07 ou R08. Mesmo se os nove arquivos e recibos forem apresentados, a saída mantém native_playable=false, can_install=false, can_publish=false. Para salvar somente os metadados em pasta privada, use --report .blue-work/sinnoh-j09-source-intake.json; nunca sobrescreve.

## R09 — QA real, não fixtures

Após fonte de nove mapas e direitos, usar somente cópia QA isolada J06, compilar 24 eventos Blue, executar J07 43 casos Windows e J08 1 caso Android/JoiPlay REAL, observar Blackout, save/reload e proteção Kanto/Johto/Hoenn/Decades. Sem evidência física revisada, o CI não altera a barra nativa. No GitHub as fixtures são sintéticas, não incluem Game.exe, ROM, saves ou assets de terceiro.

Situação atual: engenharia 8/8 (código), nativa 0/8, mapas instalados 0/9 e casos G12 0/44; R07/R08/R09 pendentes; Sinnoh planned/não jogável.

Próximo botão: https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/238
