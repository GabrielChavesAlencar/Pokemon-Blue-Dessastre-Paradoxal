# Johto — Fase OFFLINE 10/12: encontros e treinadores das Rotas 29–31

**Data:** 13/11/2026. **Não foi aberto Game.exe.** Esta entrega publica apenas código, contratos e testes no GitHub. Os RXDATA, tilesets, gráficos e PBS produzidos a partir da base do proprietário permanecem no **ZIP privado entregue neste chat**, dentro de `.blue-work/`.

## Fonte e limites

O [pacote de mapas de Johto](../data/regions/johto-source.json) contém 74 mapas de terreno, **sem eventos, encontros selvagens ou PBS canônicos de treinadores**. As equipes e probabilidades desta etapa são **propostas de design para o Blue**, não dados oficiais de HeartGold/SoulSilver nem dados supostamente extraídos daquele pacote. **Os IDs de espécies, nomes de golpes e learnsets foram validados no PBS nativo exportado da instalação real do Blue/Decades**. Essas duas origens não devem ser confundidas.

**MapIDs da prévia:** Rota 29 = **625**, Rota 30 = **626**, Rota 31 = **627**. Todos os mapas/IDs foram confirmados no snapshot privado da etapa 08.

## Encontros selvagens propostos

Cada rota tem tabela `Land,21` e `LandNight,21`, e **cada tabela soma 100%**. Os níveis abaixo são bases propostas: o escalonamento global do Blue ainda precisa de QA real.

| Rota | Horário | Slots: chance, espécie, níveis |
|---|---|---|
| 29 | Dia | 50% Pidgey (2–4), 30% Sentret (2–4), 20% Rattata (2–4) |
| 29 | Noite | 50% Hoothoot (2–4), 30% Rattata (2–4), 20% Spinarak (2–3) |
| 30 | Dia | 40% Pidgey (3–5), 30% Caterpie (3–5), 30% Weedle (3–5) |
| 30 | Noite | 40% Hoothoot (3–5), 30% Spinarak (3–5), 30% Rattata (3–5) |
| 31 | Dia | 40% Bellsprout (4–6), 30% Pidgey (4–6), 30% Caterpie (4–5) |
| 31 | Noite | 40% Hoothoot (4–6), 30% Spinarak (4–6), 30% Rattata (4–6) |

## Treinadores propostos

O gerador produz **duas versões por treinador**: versão 0 normal com **dois Pokémon**, versão 1 Master com **quatro Pokémon**. Os golpes vêm dos aprendizados do `pokemon.txt` até o nível de cada Pokémon, com verificação no catálogo `moves.txt` instalado.

| Rota / mapa | NPC e XY do mapa | Tipo | Equipe normal (PBS v0) | Master (PBS v1) |
|---|---|---|---|---|
| 29 / 625 | Johto Mikey (36,10) | Youngster | Rattata, Sentret | Rattata, Sentret, Pidgey, Hoothoot |
| 30 / 626 | Johto Joey (18,20) | Youngster | Rattata, Pidgey | Rattata, Pidgey, Sentret, Hoothoot |
| 30 / 626 | Johto Don (36,35) | Bug Catcher | Caterpie, Weedle | Caterpie, Weedle, Spinarak, Ledyba |
| 31 / 627 | Johto Wade (45,45) | Bug Catcher | Caterpie, Weedle | Caterpie, Weedle, Spinarak, Ledyba |
| 31 / 627 | Johto Ian (54,40) | Youngster | Bellsprout, Pidgey | Bellsprout, Pidgey, Rattata, Sentret |

**Níveis PBS de referência:** Mikey 5, Joey/Don 6, Wade/Ian 7. A **escala global** usa `BlueStory.stage`, `BlueCampaign.common_level/wild_level` e `BlueTrainerMoves`. Os contratos mantêm como expectativas **70% (normal), 90% (Master) e 45% (selvagens)**, além das insígnias/esmeraldas globais. Não foi criada uma regra paralela específica para Johto. **Não afirmar que os níveis dinâmicos já foram provados no Game.exe**; a versão Master e a aplicação dos multiplicadores ainda exigem compilação/QA da engine.

### Auditando coordenadas reais

As posições foram verificadas nas tabelas de tiles reais da prévia de Johto. O primeiro ponto de Wade estava numa componente caminhável separada; foi **corrigido para (45,45)**, na mesma componente que Ian (54,40).

- Rota 29: Mikey na componente de **812 tiles estaticamente conectados**, longe de Silver (71,17).
- Rota 30: Joey e Don na mesma componente de **799 tiles estaticamente conectados**.
- Rota 31: Wade e Ian na mesma componente de **370 tiles estaticamente conectados**.
- Todos os cinco pontos têm passagem estática livre e pelo menos dois vizinhos acessíveis, mas **isso não confirma visão, colisão, caminhada automática ou comportamento em Game.exe**. Os eventos são de interação, não de avistamento automático.

## Entrega técnica na main

- `data/regions/johto-stage10-routes.json`: 3 rotas, 6 tabelas de encontros e 5 NPCs com equipes normal/Master, `gameplay_ready=false`.
- `scripts/regions/build_johto_routes_stage10.py`: lê PBS nativo, valida espécies/golpes/tipos e colisões; compõe PBS de encontros e treinadores; escreve **só em pasta nova** `.blue-work/johto-staging-routes-v1`; acrescenta 5 `RPG::Event` próprios usando `BlueJohtoRouteTrainers.battle(:KEY)`; exige etapa 08 e preserva Silver.
- `scripts/regions/JohtoRouteTrainers.rb`: handler opcional isolado de batalha, guarda a vitória por save e escolhe PBS v1 somente em `BlueStory.stage == 3`. **Bloqueia as batalhas na ausência do marcador `Data/blue-johto-routes-ready.txt` e do sistema compartilhado do Blue.** Esta etapa **não gera esse marcador**.
- `tests/test_johto_routes_stage10.py`: 10 testes de probabilidades, versões PBS, learnsets, colisões e preservação de mapas em stage sintético.
- `tests/johto_routes10_runtime.rb` + `tests/test_johto_routes10_runtime.py`: 1 harness sintético Ruby (5 normal/Master, vitória/derrota, save/reload, ausência de ready marker, isolamento Kanto/Decades). Não substitui batalhas reais.

Arquivos gerados apenas no ZIP privado:

```text
.blue-work/johto-staging-routes-v1/
  Data/Map600.rxdata ... Map676.rxdata    # 77 mapas (3 alterados)
  PBS/encounters_johto_routes.txt         # 3 rotas × 2 períodos
  PBS/trainers_johto_routes.txt           # 5 treinadores × 2 versões
  johto-routes10-report.json
  johto-stage.json
  ...
```

### Auditoria do pacote privado com dados reais

Os cinco NPCs foram adicionados e o **Ruby Marshal reabriu corretamente** os RXDATA resultantes. Os três únicos mapas diferentes da etapa 08 são:

| Arquivo | SHA-256 novo |
|---|---|
| `Map625.rxdata` | `b2ac23a1a2ef63808a41a8409ecac8b2c541fb421b8f8c53451948ca7890cbd1` |
| `Map626.rxdata` | `d8852c473f1d3cb4397ade27e39b620072c0e16ee3918c3cf60e2767057abf15` |
| `Map627.rxdata` | `77a62865a8a717a67bf356b90ba231899e7950a34adac73532e3bac76fb9ad48` |

**Outros 74 MapNNN inalterados byte a byte**, e `MapInfos.rxdata`/`Tilesets.rxdata` idênticos ao estágio da etapa 08. PBS gerados:

- `PBS/encounters_johto_routes.txt` SHA-256: `63c520ee529526a17e797d775ff5dc4fb9c9cda1c2748132d6bad7f787aaaa1b`.
- `PBS/trainers_johto_routes.txt` SHA-256: `0af84144a84d2fe01dabff2278fcf2fb0c3ced41fccedb4743e622fe44a97508`.

O ZIP privado foi testado contra CRC de todas as entradas, sem erros. A serialização feita diretamente por Ruby pode gerar hashes distintos da serialização de Python (por exemplo, referências de strings), devendo ser auditada semanticamente e com o manifesto **de cada build**.

### Comandos offline após obter a prévia 08

```powershell
python scripts/regions/build_johto_routes_stage10.py
python -m unittest discover -s tests -p "test_johto_routes_stage10.py" -v
python -m unittest discover -s tests -p "test_johto_routes10_runtime.py" -v
```

Estes comandos não iniciam `Game.exe`. É **proibido** copiar o ZIP sobre `game/` original: atualização do `Blue-Story.exe`, compilação real dos PBS, configuração de encontro, marcadores pós-QA e verificação dos sprites de treinador permanecem pendentes.

**Barra OFFLINE: 10/12 (83,3%). JOGÁVEIS: 0/13. TESTADAS NO EXE: 0/13.**

**Próxima OFFLINE 11/12:** Violet City, Sprout Tower, Falkner, preparação da insígnia Zephyr e ligações de mapas mantendo proteção por região.
