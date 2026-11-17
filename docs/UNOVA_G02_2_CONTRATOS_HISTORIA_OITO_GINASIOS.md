# Unova G02.2 — Contratos de história e oito ginásios (campanha White)

**Entrega de código GitHub, NÃO instalação.** Usa as bases G01.1–G01.4 sem tocar em `Game.exe`, saves, scripts Ruby, RXDATA, MapIDs ou mapas. Região continua **planned**.

## Implementação

- [Catálogo de oito ginásios e 40 eventos](../data/regions/unova-g02-gym-story-contracts.json): cinco eventos por ginásio (`ARRIVAL`, `STORY_GATE`, `LEADER_BATTLE`, `BADGE`, `AFTER_STORY`), nomes descritivos originais PT-BR e referências simbólicas U03. Não reproduz diálogos licenciados.
- [Motor de contratos G02.2](../scripts/regions/audit_unova_g02_gym_story.py): entrada `initial`, validação `validate_catalog` / `validate_envelope`, execução **offline** `apply`, demo `--simulate-demo`. Verifica consistência com G01.1 (chapters/missions), G01.2 (pré-requisitos e transições), G01.3 (recibos/reentrada) e round-trip **somente do componente G01** pela G01.4.
- [76 testes negativos/positivos](../tests/test_unova_g02_gym_story.py) no GitHub Actions Linux e Windows.

## Oito ginásios e insígnias

| Nº | Cidade | Líder contratual White | Insígnia | Referência de implementação |
|---|---|---|---|---|
| 1 | Striaton | Chili se Snivy, Cress se Tepig, Cilan se Oshawott | TRIO | U08 |
| 2 | Nacrene | Lenora | BASIC | U10 |
| 3 | Castelia | Burgh | INSECT | U12 |
| 4 | Nimbasa | Elesa | BOLT | U15 |
| 5 | Driftveil | Clay | QUAKE | U16 |
| 6 | Mistralton | Skyla | JET | U19 |
| 7 | Icirrus | Brycen | FREEZE | U22 |
| 8 | Opelucid | Iris (**White**; Drayden é referência Black) | LEGEND | U24 |

Os oito nomes de insígnia correspondem ao `site/public/data/regions.json`. Os capítulos CH02–CH09 e suas missões vêm do contrato G01.1, e suas liberações seguem a máquina G01.2. As referências de mapa são **símbolos** do catálogo U03, não mapas RXDATA com IDs instalados. `trainer_party`, `trainer_levels`, identificadores de NPC, switches e itens das insígnias permanecem **null**.

## Bloqueios de progressão

- O ginásio N só pode ser trabalhado após avançar para o capítulo N+1 correspondente. Capítulos anteriores devem estar concluídos pela G01; o 1º requer todos os 13 eventos U07.
- Dentro de um ginásio, somente o **próximo** evento da sequência de cinco pode ser marcado: chegada, requisito de história, **vitória explícita** contra o líder, claim simbólico da insígnia e capítulo posterior.
- `LEADER_BATTLE` só aceita `outcome=WIN` e o líder correto. `LOSS`, líder errado, Drayden na variante White e batalhas sem resultado são bloqueados.
- A insígnia vem de `BADGE` posterior à vitória. O claim é único; repetir o evento com argumentos idênticos resulta em **no-op**, e qualquer replay conflitante é rejeitado.
- O capítulo não pode ser concluído sem os cinco eventos e a insígnia. `complete` continua exigindo `SIMULATED_ONLY_NO_NATIVE_APPROVAL`; `advance` preserva as travas G01.2.
- Reentrada em capítulos anteriores é apenas leitura, sem reset de missões, checkpoints, itens ou insígnias. Os contratos impedem alcançar a Liga sem **oito claims simbólicos** em ordem.
- O motor não executa os eventos CH10+ (Elite Four, N, Ghetsis, créditos) nem o pós-jogo: **G02.3 e G02.4 permanecem pendentes**.

## Envelope G02.2

A simulação G02.2 mantém, em memória, um envelope separado com `g01_envelope`, `story_receipts` e `badge_claims`. **Não altera a estrutura do schema G01.1 e não adapta saves reais.** O formato serializado G01.4 valida o componente G01; o envelope G02.2 completo ainda não possui codec de persistência, e nenhum estado de insígnia é inserido em saves reais.

Cada resultado explicita `native_badges_granted=false`, `native_events_executed=false`, `native_save_modified=false`, `game_exe_tested=false`, `can_install=false`.

## Verificações sem PC

```bash
python scripts/regions/audit_unova_g02_gym_story.py --check
python scripts/regions/audit_unova_g02_gym_story.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g02_gym_story.py -v
```

O demo pode percorrer CH01 e os oito ginásios simbólicos até a **entrada planejada da Liga (CH10)**, sem simular vitória real ou alterar o jogo. A validação positiva confirma apenas a **coerência estrutural do código**.

**Progresso após CI:** G02 passa para **2/4**, Barra G passa para **13/32 (41%)**; Barra A **0/8**, Unova jogável **0/32** e região **planned** permanecem inalteradas.

**Próxima tarefa:** G02.3 (Elite Four, N, Ghetsis e créditos); a G02.2 não preenche artificialmente esses contratos.
