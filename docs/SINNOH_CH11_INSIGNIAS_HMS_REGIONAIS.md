# Sinnoh — CH11: oito insígnias e HMs exclusivamente locais

**Data:** 16/11/2026. **Status:** contrato e runtime publicados, testes Python/Ruby **sem Game.exe**. Sinnoh segue `planned`, sem mapas de ginásio ou eventos de obtenção nativos comprovados.

## Fonte de verdade

O [catálogo público das regiões](../site/public/data/regions.json) já definia os oito badges e movimentos de campo de Sinnoh com base em Platinum. A [versão de contrato auditável](../data/regions/sinnoh-badges-hms-contract.json) preserva esses identificadores (sem IDs de mapa, treinador, NPC ou item criado por suposição):

| Insígnia | Movimento | HM tradicional Platinum |
|---|---|---|
| COAL | ROCK_SMASH | HM06 |
| FOREST | CUT | HM01 |
| COBBLE | FLY | HM02 |
| RELIC | DEFOG | HM05 |
| FEN | SURF | HM03 |
| MINE | STRENGTH | HM04 |
| ICICLE | ROCK_CLIMB | HM08 |
| BEACON | WATERFALL | HM07 |

Esta é a correspondência de **permissões** já mantida no Blue, não a confirmação da sequência jogável de ginásios. Até existirem os eventos nativos auditados, nenhuma conquista ou HM é concedido automaticamente.

## Regras implementadas

1. **Insígnias:** `BlueRegions.award(state, "SINNOH", badge)` continua a fonte de gravação quando um **evento de vitória legítima** chamar a função. Rejeita região ativa diferente, badge inexistente/duplicado e listas de Sinnoh adulteradas. `local_achievements` não lê insígnias de Kanto/Johto/Hoenn ou o array nativo de Decades para formar as oito conquistas de Sinnoh. O desbloqueio de especiais requer oito insígnias **locais**.
2. **HM regional:** `BlueRegions.record_sinnoh_hm(state, action, item, bag, pickup_confirmed)` só registra o HM com `pickup_confirmed == true`, região atual `SINNOH`, item **canônico** na Bolsa e metadados `GameData::Item` confirmando ser o HM do movimento. Consultas/negações não gravam dados. Tentativas de duplicar ou registros malformados falham sem corrigir o save silenciosamente.
3. **Campo:** `BlueRegions.field_access` e `BlueRegionalPolicy.field_result` exigem três condições separadas em Sinnoh: **insígnia da própria região**, **prova registrada da obtenção local** e **HM atualmente na Bolsa**. Um item previamente adquirido em Kanto/Hoenn, sozinho, não autoriza Surf ou outro HM em Sinnoh. Os movimentos das demais regiões e o acesso nativo de Decades continuam com seu comportamento anterior.
4. **Viagem e save:** usa-se o vault já existente `BlueRegionTravel.stage_local_bag` em vez de criar um segundo inventário. Itens-chave, HMs, atalhos e PC de itens são copiados apenas para a região de origem e restaurados por região ao retornar; TMs, consumíveis e itens comuns mantêm o comportamento do Blue. O runtime não modifica saves antigos durante uma consulta.

**Limitação essencial:** um booleano passado por código Ruby não prova que o jogador recolheu um HM físico; o chamador deverá ser um **evento de obtenção de Sinnoh real e validado**. Ainda faltam tais eventos, seus ginásios, mapas, sprites e validação em `Game.exe`. Por isso o contrato permanece não instalável, sem badges ou HMs efetivamente entregues no jogo.

## Auditoria e CI

```bash
python scripts/regions/audit_sinnoh_badges_hms.py
python -m unittest discover -s tests -p 'test_sinnoh_badges_hms_ch11.py' -v
ruby tests/sinnoh_badge_hm_ch11_runtime.rb tests/regions_data_fixture.rb scripts/battle_polish/Regions.rb scripts/battle_polish/RegionTravel.rb scripts/battle_polish/RegionalPolicy.rb data/regions/sinnoh-badges-hms-contract.json
```

O [CI 43958964604](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43958964604) passou: **12 testes Python negativos/positivos CH11**, execução Ruby de todas as oito permissões e trocas sintéticas Kanto → Sinnoh → Hoenn → Kanto → Sinnoh, incluindo Bolsa, PC, atalhos e `Marshal` reload. A suíte de Sinnoh terminou com **251 testes Python aprovados**.

**Barra E:** 11/20 (55%). **Barra A:** 8/32 (25%). **Barras B/C/D:** 0/13. Nenhuma delas indica Sinnoh jogável.
