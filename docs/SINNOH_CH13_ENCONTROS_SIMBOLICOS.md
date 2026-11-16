# Sinnoh — CH13: catálogo simbólico auditável de encontros

**Data:** 16/11/2026 · **Entrega:** CH13 concluída em código e testes, **região não jogável**.  
**Catálogo:** [`data/regions/sinnoh-symbolic-encounters.json`](../data/regions/sinnoh-symbolic-encounters.json)  
**Auditor:** [`audit_sinnoh_symbolic_encounters.py`](../scripts/regions/audit_sinnoh_symbolic_encounters.py)  
**CI:** [Blue Studio regressão 43970908799](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43970908799).

## Interpretação correta

Foram cadastradas **21 áreas**, com **50 menções de espécies** copiadas da **amostra de referência** já revisada em [`detonados-content-review.json`](../data/regions/detonados-content-review.json) para Platinum. A correspondência de símbolos se apoia em [`sinnoh-coverage.json`](../data/regions/sinnoh-coverage.json).

**As espécies são candidatas para conferência, não encontros disponíveis no jogo.** O terreno e os métodos listados abaixo são categorias de trabalho plausíveis a **auditar**, não atribuições da espécie a um método. Nenhum método ou horário está comprovado por PBS nativo. Todos os registros têm `status=planned`, `map_id=null`, `source_map_ids=[]`, `destination_map_ids=[]`, `encounter_slots=[]`, `weight_percentages=null` e `level_ranges=null`. Os flags de instalado, verificado e permissões de escrita são sempre falsos.

## Rota, terreno, métodos e espécies de referência

| Área de referência | Símbolo no inventário | Terreno para auditoria | Métodos PBS candidatos (não ativos) | Espécies de referência (não instaladas) |
|---|---|---|---|---|
| Route 201 | ROUTE_201 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `STARLY`, `BIDOOF` |
| Route 202 | ROUTE_202 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `STARLY`, `BIDOOF`, `SHINX` |
| Route 203 | ROUTE_203 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `STARLY`, `BIDOOF`, `SHINX` |
| Oreburgh Mine | OREBURGH_MINE | CAVE | `Cave`, `CaveMorning`, `CaveDay`, `CaveNight` | `GEODUDE`, `ONIX` |
| Valley Windworks | VALLEY_WINDWORKS | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `SHELLOS`, `BUIZEL`, `PACHIRISU` |
| Eterna Forest | ETERNA_FOREST | FOREST | `Land`, `LandMorning`, `LandDay`, `LandNight` | `BUNEARY`, `GASTLY` |
| Route 206 | ROUTE_206 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `GLIGAR` |
| Wayward Cave | WAYWARD_CAVE | CAVE | `Cave`, `CaveMorning`, `CaveDay`, `CaveNight` | `GIBLE` |
| Mt. Coronet | *Não resolvido* | CAVE | `Cave`, `CaveMorning`, `CaveDay`, `CaveNight` | `CLEFAIRY`, `NOSEPASS` |
| Route 208 | ROUTE_208 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `RALTS`, `BIBAREL` |
| Route 209 | ROUTE_209 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `RALTS`, `BIBAREL` |
| Route 210 | ROUTE_210 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `SCYTHER`, `SWABLU` |
| Route 215 | ROUTE_215 | GRASS | `Land`, `LandMorning`, `LandDay`, `LandNight` | `SCYTHER`, `SWABLU` |
| Route 212 | *Não resolvido* | WETLAND | `Land`, `LandMorning`, `LandDay`, `LandNight` | `QUAGSIRE` |
| Route 213 | ROUTE_213 | COAST | `Land`, `Water`, `OldRod`, `GoodRod`, `SuperRod` | `SHELLOS`, `WINGULL`, `CHATOT` |
| Great Marsh | GREAT_MARSH | WETLAND | `Land`, `LandMorning`, `LandDay`, `LandNight` | `WOOPER`, `YANMA`, `SKORUPI` |
| Route 216 | ROUTE_216 | SNOW | `Land`, `LandMorning`, `LandDay`, `LandNight` | `SNOVER`, `SNORUNT`, `SNEASEL`, `SWINUB` |
| Route 217 | ROUTE_217 | SNOW | `Land`, `LandMorning`, `LandDay`, `LandNight` | `SNOVER`, `SNORUNT`, `SNEASEL`, `SWINUB` |
| Route 222 | ROUTE_222 | COAST | `Land`, `Water`, `OldRod`, `GoodRod`, `SuperRod` | `ELECTABUZZ`, `MAGNEMITE`, `MAGNETON`, `PELIPPER` |
| Victory Road | VICTORY_ROAD | CAVE | `Cave`, `Water`, `OldRod`, `GoodRod`, `SuperRod` | `ONIX`, `STEELIX` |
| Old Chateau | *Não resolvido* | BUILDING | `Cave`, `CaveMorning`, `CaveDay`, `CaveNight` | `GASTLY`, `HAUNTER` |

A amostra contém **18 símbolos encontrados de forma inequívoca** na lista do projeto. **Mt. Coronet** reúne vários setores e pisos, enquanto **Route 212** e **Old Chateau** ainda não possuem uma referência simbólica própria na cobertura; portanto ficaram sem símbolo até reconciliação. Nenhuma delas recebeu MapID por aproximação.

## Horário, progresso e evolução

- Todos os locais contêm `time_windows_to_audit = ["morning", "day", "night"]`: são **perguntas de auditoria**, não prova de presença das espécies nesses horários. `time_assignment_verified=false` e `species_method_assignments=[]`.
- Os tipos `Land`, `Cave`, `Water`, `OldRod`, `GoodRod` e `SuperRod` e suas variantes realmente são nomes reconhecidos pelo PBS do Blue e, quando listados como candidatos, aparecem no Habitat Dex. Isso não significa que cada local disponha do método ou de todos seus Pokémon nesses métodos.
- A referência de progresso é `BlueEvolutionScaling.progress_level`: maior nível **não-ovo** da equipe, limitado ao nível máximo em `GameData::GrowthRate`. Não existe cap numérico de Sinnoh por insígnias confirmado no save.
- O seletor existente usa `GameData::Species#get_evolutions(true)`, nível de evolução **+5**, pedra **30**, troca **40** e felicidade **45**. Cada tentativa de evolução selvagem mantém o slot original e usa chances **15%, 30%, 45% e 60%** conforme o progresso acima do limiar. **Esses percentuais são chances condicionais de evolução do slot já sorteado; nunca são taxas de spawn PBS das áreas.**
- **Drifloon** de Valley Windworks é evento semanal estático; **Rotom** de Old Chateau é evento roteirizado. Ambos ficam exclusivamente em `special_events`, com `event_installed=false`. Não são injetados como slots regulares.

## Guardas automatizadas

O [auditor](../scripts/regions/audit_sinnoh_symbolic_encounters.py) compara as 21 áreas com a revisão Platinum, valida as referências de espécies e os símbolos contra o inventário de cobertura, confere os métodos candidatos nos arquivos **reais** `pbs.py` e `Habitat.rb`, e verifica os limiares compartilhados de `EvolutionScaling.rb`. Rejeita: campos incompletos, áreas duplicadas/fora de ordem, espécies alteradas, métodos inválidos para o terreno, horário ou espécie alocados sem prova, MapID ou percentuais inventados, eventos estáticos convertidos em wild encounters, runtime divergente e aprovações falsas.

```bash
python scripts/regions/audit_sinnoh_symbolic_encounters.py
python -m unittest discover -s tests -p 'test_sinnoh_symbolic_encounters_ch13.py' -v
python -m unittest discover -s tests -p 'test_sinnoh_*.py' -v
```

**Resultado do CI:** **20/20 testes CH13** e **286/286 testes Python de Sinnoh** passaram na [execução 43970908799](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43970908799).

**Pendências reais:** carregar e comparar `game/Data` e `PBS/encounters.txt` autorizados, confirmar coordenadas, ocupação dos mapas, método, distribuição por hora, taxas que somem 100% por método, nível de selvagens e eventos estáticos no Game.exe/JoiPlay. Nenhum desses passos foi concluído nesta entrega. Decades, Kanto, Johto, Hoenn e saves permanecem sem alterações.

**Barras após CH13:** E **13/20 (65%)**; A **8/32 (25%)**, B/C/D **0/13**.
