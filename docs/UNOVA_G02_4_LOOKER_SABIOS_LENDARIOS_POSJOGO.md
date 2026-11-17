# Unova G02.4 — Looker, sábios, lendários e pós-jogo White (somente GitHub)

**Entrega planejada e testável sem PC**, baseada nas fases [G01.1–G01.4](UNOVA_G01_4_SERIALIZACAO_MIGRACAO_SINTETICA.md), [G02.2](UNOVA_G02_2_CONTRATOS_HISTORIA_OITO_GINASIOS.md) e [G02.3](UNOVA_G02_3_ELITE_FOUR_N_GHETSIS_CREDITOS.md).

**Não instala conteúdos no Game.exe**, não manipula `.rxdata`, scripts Ruby, backups, saves ou itens reais. Insígnias, HMs, Pokémon capturados, party, níveis e créditos **não são verificados nem concedidos** por esta ferramenta.

## Entregas

- [Catálogo versionado de pós-jogo](../data/regions/unova-g02-postgame-contracts.json): seis sábios restantes, Looker, seis encontros lendários opcionais, sete atividades opcionais, as exceções de eventos e revanche da Liga.
- [Motor G02.4 offline](../scripts/regions/audit_unova_g02_postgame.py): valida o catálogo com fontes G01–G02 e U03; opera sobre cópia profunda de envelope pré-aprovado *somente na simulação*.
- [128 testes positivos e negativos](../tests/test_unova_g02_postgame.py): acesso, flags, seis sábios em qualquer ordem, recompensas sem duplicar, lendários e rematches de vários ciclos.
- CI Linux/Windows `--check`, `--simulate-demo` e suíte Python, mais portal.

## Pré-requisitos e fronteira G02.3 → G02.4

O motor reconstrói por G01/G02.2/G02.3 a jornada sintética completa: **oito insígnias**, quatro vitórias na Elite, cinco eventos do Castelo, vitória de N/Ghetsis, créditos e entrada **CH12_POSTGAME**. Só nesse estado os eventos G02.4 podem começar. O acesso é **mais restritivo do que certas opções do Pokémon White original**, pois esta trilha G02.4 concentra as atividades no pós-jogo para teste; não afirma que todos esses lendários só existem após os créditos no jogo oficial.

O catálogo exige os tokens anteriores `UNOVA_G023_CREDITS_SIMULATED` e `UNOVA_G023_POSTGAME_ACCESS_SIMULATED`. Tentativas em capítulos anteriores, tokens falsificados ou dados de outra região falham fechadas. O CH12 permanece com sua missão **active**: as atividades opcionais não a completam automaticamente.

## Looker e seis sábios

Após créditos, Looker é registrado uma única vez em referência a Nuvema, com intenção **SUPER_ROD_NOT_GRANTED** (nada é entregue no inventário). Somente após esse encontro são aceitos os seis sábios restantes em **qualquer ordem**, sem incluir Ghetsis — já derrotado na G02.3.

| Sábio | Localização simbólica U03 | Intenção de recompensa |
|---|---|---|
| Gorm | Dreamyard | TM75 Swords Dance |
| Ryoku | Relic Castle | TM04 Calm Mind |
| Zinzolin | Cold Storage | TM01 Hone Claws |
| Bronius | Chargestone Cave | TM69 Rock Polish |
| Rood | Route 18 | TM32 Double Team |
| Giallo | Route 14 | TM08 Bulk Up |

Cada sábio tem **um recibo único e uma intenção de TM**, mas nenhuma TM é realmente entregue. Repetir um encontro dá no-op. O contrato requer sinalização **sintética** de Surf para Route 18 e Surf + Waterfall para Route 14, sem criar ou verificar HM no jogo. A conclusão de Looker só é registrada após **seis recibos distintos**.

Referências externas consultadas para relações históricas e localizações:
- [Serebii — Team Plasma, seis sábios](https://www.serebii.net/blackwhite/plasma.shtml)
- [GamesRadar — six sages e Super Rod pós-jogo](https://www.gamesradar.com/pokemon-black-and-white-post-game-walkthrough-and-supplemental-guide/2/)
- [SuperCheats — seis sábios/TMs e locais](https://www.supercheats.com/guides/pokemon-white/new-game-things-to-do)

## Lendários e encontros opcionais

| Encontro | Local simbólico | Condições do simulador |
|---|---|---|
| Cobalion | Mistralton Cave | Plano de Surf |
| Terrakion | Victory Road | Recibo prévio de encontro de Cobalion |
| Virizion | Pinwheel Forest | Recibo prévio de encontro de Cobalion |
| Kyurem | Giant Chasm | CH12 |
| Thundurus | Route 7 | CH12; variante White, não Tornadus natural |
| Landorus | Abundant Shrine | Plano Surf, encontro de Thundurus e declaração **sintética** da dupla Tornadus/Thundurus |

A operação `legendary_encounter` admite apenas `outcome="ENCOUNTERED"`. **Não captura, não vence batalha nem altera party**; os recibos representam apenas planejamento de encontro único. O requisito do Landorus envolve `plan_genie_pair` com marcador `SIMULATED_ONLY_NO_NATIVE_APPROVAL`; esse marcador **não comprova** posse dos dois Pokémon.

**Victini, Keldeo, Meloetta e Genesect** ficam explicitamente bloqueados por dependerem de condições externas/eventos de distribuição. A G02.4 não inventa Liberty Pass, presente misterioso, ROM, código ou direitos.

Volcarona em Relic Castle é classificado corretamente como **encontro especial opcional**, e não como espécie lendária.

Fontes complementares para as relações: [Bulbapedia — Pokémon de eventos de B/W](https://bulbapedia.bulbagarden.net/wiki/List_of_in-game_event_Pok%C3%A9mon_in_Pok%C3%A9mon_Black_and_White); [Gamer Guides — lendários B/W](https://www.gamerguides.com/pokemon-black-white/guide/postgame-walkthrough/checklists/rare-pokemon).

## Outras atividades opcionais

Os contratos incluem rotas orientais (Route 11), **White Forest** (não Black City), Undella, Abyssal Ruins em Undella Bay, Battle Subway, Royal Unova e Volcarona em Relic Castle. O contrato da Abyssal Ruins exige plano de Dive. Cada atividade é registrada uma única vez por chave, sem prêmio real, colisão, NPC ou teleporte.

Os registros de navegação `DIVE`, `SURF` e `WATERFALL` são **sinalizadores sintéticos** de pré-requisitos. Nenhum sistema regional HM, status do jogador ou save é lido.

## Revanche da Elite Four e Alder

Uma `start_rematch(session_id)` inicia sessão sequencial: id 1, depois 2 e assim por diante. Em cada sessão, os quatro membros originais da Elite Four podem vencer em qualquer ordem, sem contagem duplicada. Só depois dessas quatro vitórias a batalha com **Alder** pode ser marcada `WIN`. `LOSS` deixa o envelope intacto e aponta apenas `UNOVA_POKEMON_LEAGUE` como sugestão simbólica de retorno — **nenhum teleporte**.

Após Alder, `finish_rematch` arquiva uma sessão única. São permitidas novas sessões independentes, com limite defensivo de 25 registros (não representa limite do jogo oficial); o histórico não guarda equipes, níveis ou itens. Replays com a mesma sessão são idempotentes e não concedem recompensas. A volta a outras áreas/capítulos é somente leitura, preservando as insígnias e as provas G02.3.

## Modelo e limites de persistência

Envelope G02.4: `g023_envelope`, `navigation_planned`, `looker_briefed`, `sages_found`, `looker_completed`, `legendary_encounters`, `party_pair_planned`, `optional_activities`, `rematches_completed`, `active_rematch`, além de versão, região, campanha e escopo.

Validações recusam recibos duplicados, TM alterada, captura falsa, lendários sem pré-requisitos, Ghetsis como sétimo sábio, completude prematura, sessões de rematch ilegais, Alder antes da Elite e campos que declarem aprovação nativa. Todas as operações devolvem cópias e nunca escrevem arquivos.

O codec [G01.4](../scripts/regions/audit_unova_g01_serialization.py) ainda executa round-trip apenas da **projeção G01**, e **não** armazena os novos campos G02.2–G02.4 ou saves reais. Mesmo com G02 completo, a integração jogável exige mapas, conteúdo licenciado, persistência nativa e testes separados.

## Comandos verificados pelo CI

```bash
python scripts/regions/audit_unova_g02_postgame.py --check
python scripts/regions/audit_unova_g02_postgame.py --simulate-demo
python -m unittest discover -s tests -p test_unova_g02_postgame.py -v
```

**Ao passar CI e integrar na main:** Barra G **15/32 (47%)**, G02 **4/4 (100%)**. Barra A permanece **0/8**, campanha Unova jogável **0/32** e status regional **planned**. Próxima frente GitHub: G03 — treinador e balanceamento auditável.
