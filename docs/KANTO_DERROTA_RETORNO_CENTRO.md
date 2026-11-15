# Kanto — derrota envia ao último Centro Pokémon

## Falha observada
No piloto isolado de Kanto, perder para treinadores, rivais e líderes podia manter o personagem no mapa da derrota e recuperar toda a equipe automaticamente. A causa era `setBattleRule("canLose")` nas rotinas de batalha de `scripts/regions/KantoPilot.rb`, seguido de `$player.heal_party` em caso de derrota. Essa opção instrui o motor Essentials a **não** executar o blackout.

## Comportamento corrigido
Todos os confrontos **da campanha controlados por `BlueKantoPilot`** (rival inicial, treinadores comuns, ginásios, revanches Full Power, casal de Victory Road e Elite Four/Campeão) agora usam `setBattleRule("cannotLose")`. Quando o jogador perde, a rotina **nativa** do Essentials `BattleCreationHelperMethods.after_battle` executa `pbStartOver`, que cura a equipe e transporta ao último checkpoint do Centro Pokémon.

- O último checkpoint é o que o jogo registra ao **curar na enfermeira**: `BlueKantoPilot.heal` chama `$player.heal_party` e `pbSetPokemonCenter`, que atualiza `$PokemonGlobal.pokecenterMapId/X/Y/Direction`. Ao curar em outro Centro, o destino muda para o mais recente.
- Ao selecionar o inicial, o piloto já registra um checkpoint inicial em Pallet/Oak. Isso serve como salvaguarda para o começo da campanha, antes da primeira visita a um Centro.
- Perdas de treinadores comuns e ginásios **não** registram vitória, não concedem insígnia, não colocam o trainer em página vencida e permitem uma nova tentativa.
- Derrota para o rival tutorial não marca `pilot_rival` como concluído: a batalha pode ser refeita. Vitória no tutorial mantém a recuperação planejada após vencer.
- Se perder na Liga, o motor transporta ao último Centro (em vez de teletransportar ao saguão fixo); somente `pilot_league_active`, `pilot_league_full_power` e `pilot_league_wins` são reinicializados. Todas as insígnias e vitórias anteriores permanecem.
- Não alteramos `pbStartOver`, `Game_Event#refresh`, o sistema de saves nem o motor global. Assim Decades, Johto, Hoenn e Sinnoh não mudam. Batalhas selvagens continuam com seu comportamento nativo.
- Revanches opcionais fora da campanha, conduzidas por outros sistemas (`BlueStory.replay`), mantêm suas regras específicas de treino, sem mudança global de `canLose`.

## Validação
`ruby tests/kanto_blackout_runtime.rb scripts/regions/KantoPilot.rb` executa o código real do piloto usando um motor nativo simulado. Confere dois Centros registrados, destino da derrota, recuperação única, líder e treinador derrotável depois, rival, duelo em dupla, Full Power, Liga, persistência de insígnias e vitórias e ausência de teleporte fixo.

## Aceite manual no Windows
1. Atualize a `main` com `RUN.bat`, feche o jogo e reconstrua com `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`.
2. Use a enfermeira de um Centro Pokémon, vá até outro Centro, cure novamente, salve e entre em batalha em uma rota distante.
3. Perca deliberadamente; confirme a animação/mensagem de blackout e o retorno **ao segundo Centro**, com a equipe recuperada.
4. Verifique que o treinador continua disponível, a insígnia não foi concedida e as missões anteriores continuam válidas.
5. Teste derrota na Liga (se tiver acesso): deve sair da tentativa e reaparecer no último Centro, preservando oito insígnias e progresso de outras regiões.
6. Recarregue o save e repita: não pode aparecer na posição da derrota nem em mapa inexistente.

Os testes Ruby verificam contrato e estado simulado, **não substituem** uma partida no `Game.exe`. Só declarar aprovação jogável após teste visual.
