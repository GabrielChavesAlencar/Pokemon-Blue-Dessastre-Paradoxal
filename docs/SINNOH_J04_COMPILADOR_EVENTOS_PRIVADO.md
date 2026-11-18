# Sinnoh jogável J04 — compilador privado de eventos originais Blue

Data: 18/11/2026. Base: J03 PR #227 integrado à main depois de 11 checks aprovados.

## Código entregue e situação real

O novo programa scripts/regions/compile_sinnoh_playable_j04.py compila 16 portais, 5 NPCs e 3 Poké Bolas físicas de Turtwig, Chimchar e Piplup **somente** sobre uma cópia isolada que já contenha nove mapas físicos verificados. O código não aceita os cinco mapas ausentes (quarto, casa 1F, casa Barry, Lago Verity, laboratório Rowan) como placeholders.

O registro público CH06 (data/regions/sinnoh-twinleaf-events.json) continua com coordenadas e sprites nulos. Apenas quatro terrenos reais de fonte foram auditados em B00 (Twinleaf, Route 201, Sandgem, Route 202); seus dados e imagens não são publicados neste PR e seus direitos de redistribuição não foram aprovados. **Nenhum evento foi compilado em mapas reais do usuário nesta execução.** As CI usam nove mapas e dois sprites sintéticos criados nos testes, não dados privados.

## Entradas obrigatórias

Todas as entradas abaixo devem existir localmente, depois de revisão de origem e autorização de uso:
- --input-label j04-source --input-sha SHA256: um recibo imutável, produzido por sinnoh_staging_transaction.stage, de um stage privado com nove arquivos Data/MapNNN.rxdata, MapInfos e Tilesets, e os PNGs Graphics/Characters. A J03 disponível atualmente só prepara quatro terrenos; portanto NÃO satisfaz a J04.
- --game-data INSTALACAO/game/Data: baseline real de MapInfos/Tilesets e IDs ocupados, somente leitura.
- --spec .blue-work/sinnoh-jogavel/j04-verified-events.json: uma cópia local COMPLETA do contrato CH06 com nove IDs e SHA-256 reais, posições e chegadas verificadas dos dezesseis warps, coordenadas de NPCs e Poké Bolas, sprites verificados, spawn/passabilidade revisados. Nunca preencher com coordenadas imaginárias.
- --reservations .blue-work/sinnoh-jogavel/j04-reservations.json: contrato J02 LOCAL_RESERVATIONS_CANDIDATE com schema=1, region=SINNOH, baseline_mapinfos_sha256 e protected_ids efetivamente revisados. Essa declaração NÃO prova a reserva global R07.
- --sprite-review .blue-work/sinnoh-jogavel/j04-sprites.json: JSON com schema=1, region=SINNOH, mode=J04_PRIVATE_SPRITE_REVIEW, baseline_mapinfos_sha256, map_stage_plan_sha256, reviewed_locally=true **somente após revisão humana local**, sprite_sha256 contendo SHA exato dos PNGs Characters utilizados. Não autoriza redistribuição, não prova R08.

## Execução segura

Diagnóstico sem argumentos: python scripts/regions/compile_sinnoh_playable_j04.py. Deve encerrar com status de bloqueio e código 2, sem criar stage.

Com todos os insumos físicos e autorizados, executar inicialmente apenas dry-run:

    python scripts/regions/compile_sinnoh_playable_j04.py --input-label j04-source --input-sha SHA_REAL_STAGE --game-data INSTALACAO/game/Data --spec .blue-work/sinnoh-jogavel/j04-verified-events.json --reservations .blue-work/sinnoh-jogavel/j04-reservations.json --sprite-review .blue-work/sinnoh-jogavel/j04-sprites.json --output-label j04-events

Depois de conferir o hash do dry-run, anexar --stage --expected-dry-run SHA_REAL_DRY_RUN. Para verificar o stage produzido:

    python scripts/regions/compile_sinnoh_playable_j04.py --output-label j04-events --verify-stage --expected-dry-run SHA_REAL_DRY_RUN

Para desfazer **apenas o stage íntegro**:

    python scripts/regions/compile_sinnoh_playable_j04.py --output-label j04-events --rollback --expected-dry-run SHA_REAL_DRY_RUN

A ferramenta recusa apagar estágios adulterados, com symlinks ou arquivos extras. Nenhum comando instala no jogo principal ou lê/modifica saves.

## Regras bloqueantes

Valida arquivo, manifesto, SHA, MapIDs na faixa 442–517, reservas e baseline contra jogo real. Preserva todos MapInfos/Tilesets das regiões existentes; exige nove mapas não vazios e sem eventos/músicas do doador. Audita esquema CH06, 24 chaves únicas, oito pares de transferências bidirecionais, sprites com PNG/SHA, coordenadas dentro do mapa e tiles transitáveis para eventos, chegadas e spawn.

Gera RPG::EventCommand de transferência (201), ou chamadas Ruby estáticas permitidas (355): BlueSinnohPilot.mother, barry_intro, rowan_briefcase, barry_rival, rowan_pokedex e choose_starter(TURTWIG/CHIMCHAR/PIPLUP). **A lógica desses handlers ainda não está implementada no motor nativo: J05 fará isso.** Nenhum código Ruby arbitrário do usuário ou do jogo doador é copiado.

## Barra

Código J01–J04 = 4/8 (50%) **somente depois de CI aprovada**. Jogabilidade nativa = 0/8, mapas instalados = 0/9 e 0/44 QA Windows/Android. R07/R08/R09 seguem pendentes. Sinnoh permanece planned/não jogável. A J04 possui suíte sintética com 46 casos, mais regressões J01–J03, CH06 e portal.

Próxima etapa: [J05 — Barry, iniciais, batalhas, save isolado](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/228). O botão permanente de próxima fase no portal aponta à J05.
