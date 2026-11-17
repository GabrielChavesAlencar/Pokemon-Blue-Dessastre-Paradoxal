# Sinnoh S18 — Encontros selvagens e evolução progressiva por nível

**19ª entrega da Barra A — integração em código e testes offline.** A S18 não instala as tabelas PBS nem cria mapas, Pokémon ou encontros novos em Sinnoh. Os recursos de Sinnoh continuam **planned/pendentes** até haver fonte autorizada e teste real no Game.exe/JoiPlay.

## Implementação efetiva

O jogo já possui a [rotina compartilhada `BlueEvolutionScaling`](../scripts/battle_polish/EvolutionScaling.rb), que utiliza `PokemonEncounters#choose_wild_pokemon` e o catálogo nativo `GameData::Species#get_evolutions(true)` **sem alterar tabelas PBS de probabilidades, mapas, saves ou equipe do jogador**. A S18 introduz uma proteção adicional: um slot cuja base ou referência de progressão não seja um inteiro válido entre 1 e o máximo da engine, ou cujo nível original seja superior à progressão do jogador, **não recebe evolução automática**. Assim o resultado original é preservado em vez de fabricar um Pokémon com nível incorreto. A proteção vale para o pipeline compartilhado, não é uma mudança de encontros apenas de Sinnoh.

O termo *level cap* nesta entrega refere-se **ao maior nível entre os Pokémon não-ovo da equipe do jogador**, limitado a `GameData::GrowthRate.max_level`. Não existe no save um cap numérico regional confirmado por insígnia; a evolução **não usa** o cap BST 350/450/540.

Os níveis de evolução seguem métodos suportados da engine: evolução comum após nível nativo **+5** de graça, pedra a partir de **30**, troca de **40** e felicidade de **45**; evolução ambígua (Eevee), formas especiais e métodos sem condições verificáveis não recebem escolha automática. Para cada nível acima do limiar de evolução, a chance de transformar um *slot já sorteado* é:

| Distância do limiar | Chance de evolução do slot |
|---|---:|
| 0–4 níveis | 15% |
| 5–14 níveis | 30% |
| 15–24 níveis | 45% |
| 25 ou mais | 60% |

Essas porcentagens **não substituem nem alteram a chance original do encontro de uma espécie na área**. O slot original permanece possível; ao evoluir, o nível selecionado nunca ultrapassa a referência do jogador, e o hook preserva metadados extras do resultado nativo. Pokémon em duas ou três fases são avaliados por etapa e rolagem.

## Fontes e testes

- [`sinnoh_s18_wild_runtime.rb`](../tests/sinnoh_s18_wild_runtime.rb) carrega os módulos reais e a fixture CH12, validando método `WildEncounters` via `prepend`, probabilidades e limites 15/30/45/60, níveis antes/depois de cada limiar, evolução em dois estágios, recusa de dados inválidos, evoluções ambíguas/especiais, horários, original do slot e compatibilidade Kanto/Hoenn/Johto/Decades.
- [`data/regions/sinnoh-wild-s18.json`](../data/regions/sinnoh-wild-s18.json) formaliza a política e referencia o [catálogo CH13](../data/regions/sinnoh-symbolic-encounters.json): **21 áreas apenas de referência**, sem MapIDs nem pesos, janelas de horário ou níveis nativos confirmados.
- [`audit_sinnoh_s18_wild.py`](../scripts/regions/audit_sinnoh_s18_wild.py) valida estritamente o contrato S18, o catálogo CH13 e o contrato de progressão CH12 contra o método real. Rejeita MapIDs, slots, probabilidades, horários, dados de nível ou flag `installed` inseridos falsamente nas áreas; separa os eventos estáticos **Drifloon e Rotom** dos encontros aleatórios.
- [12 testes negativos Python](../tests/test_sinnoh_s18_wild.py) verificam as proibições. O [runner CH19](../scripts/regions/sinnoh_ci_ch19.py) roda o Ruby e o auditor; a [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) exige ambos.

## Aceite e limites

Após CI CH19 Python/Ruby, S30, portal, CH20 e merge na `main`, a S18 pode ficar **`done` no escopo de código/testes** e a **Barra A em 19/32 (59%)**, 5 parciais e 8 pendentes. Barra E permanece **20/20 (100%)**, barras B/C/D **0/13**; **44 verificações nativas continuam pendentes**.

**Não demonstrado:** spawn real de Starly, Bidoof, Shinx ou qualquer outra espécie nos mapas de Sinnoh; pesos e níveis de slot PBS; quais espécies aparecem a cada horário; Drifloon/Rotom como eventos funcionais; compilação de PBS; captura, salvamento, gráficos, colisão ou execução em Game.exe/JoiPlay. Nenhum mapa ou save principal foi alterado nesta tarefa.

## Evidências de CI

A inserir após a execução efetiva do GitHub Actions. Os resultados de teste sintético nunca serão promovidos a certificação de jogabilidade.
