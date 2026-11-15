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


## Atualização 15/11/2026 — derrota após viagem entre regiões

A regra anterior, de retornar ao último Centro registrado, permanece válida **quando esse Centro pertence à região atual**. O problema adicional era o campo nativo `$PokemonGlobal.pokecenterMapId` continuar apontando para outra região depois de uma viagem.

O módulo `scripts/battle_polish/RegionalRespawn.rb`, carregado por `Story.rb`, observa `pbSetPokemonCenter` e prepara o checkpoint **antes** do `pbStartOver` nativo. Ele não recupera HP, executa teleporte extra nem altera a progressão. O mesmo save mantém um registro de Centros visitados **por região**, atualizado pelas enfermeiras reais; Oak em Pallet não é classificado incorretamente como Centro Pokémon.

Na derrota:

1. Um checkpoint nativo já pertencente à região atual continua em uso, inclusive em saves antigos. Um Centro da mesma região visitado mais recentemente prevalece.
2. Se o último checkpoint é de **outra região**, recupera-se o último Centro confirmado da região atual.
3. Se ainda não há Centro regional salvo, utiliza-se um ponto local real: **Viridian** em Kanto (Pallet não possui Centro), o ponto de recuperação de **Cherryhill** em Decades, e o centro indicado por metadados de **Cherrygrove** em Johto (New Bark não possui Centro). Em cópia isolada de Hoenn, a fonte é Oldale. Se a fonte ainda não disponibiliza um Centro verificado, só se usa a chegada segura regional já instalada; não são criados mapas nem interiores fictícios.
4. Se o checkpoint regional não puder ser verificado, o módulo não grava coordenadas inventadas. O motor nativo continua sendo responsável pelo blackout; a ausência da fonte precisa ser investigada no Game.exe.

**Regressão automatizada:** `ruby tests/regional_respawn_runtime.rb scripts/battle_polish/RegionalRespawn.rb`. Simula Kanto → Decades → Kanto, Kanto → Johto e retornos; visita a enfermeiras distintas; revive saves legados sem metadados; rejeita IDs inexistentes; exige uma única cura e uma única chamada ao `pbStartOver`. Continua independente do teste `tests/kanto_blackout_runtime.rb`.

**Teste real pendente (Windows/Android):** visitar Centro de Kanto, trocar para Decades, perder sem curar, confirmar recuperação em Cherryhill; curar em Decades, voltar para Kanto e perder sem curar, confirmar o Centro de Kanto, sem carregar um mapa de Decades. Repetir após salvar/recarregar e, quando o instalador de Johto estiver validado, testar New Bark → Cherrygrove. O Centro inicial deve existir e ter tile de respawn passável no pacote instalado. Essa QA visual não foi afirmada como concluída.
