# Lavender's Name Rater uses Essentials' party and text-entry screens without
# borrowing a donor project's global switch or variable IDs.
module BlueKantoLavender
  def self.select_for_nickname
    selected = -1
    pbFadeOutIn do
      screen = PokemonPartyScreen.new(PokemonParty_Scene.new,$player.party)
      screen.pbStartScene(BlueKantoPilot.t("Choose a Pokémon.","Escolha um Pokémon."),false)
      begin
        selected = screen.pbChoosePokemon
      ensure
        screen.pbEndScene
      end
    end
    selected
  end

  def self.pick_nickname(pokemon)
    pbEnterPokemonName(BlueKantoPilot.t("What should its new nickname be?","Qual será o novo apelido?"),
      0,Pokemon::MAX_NAME_SIZE,pokemon.name,pokemon)
  end

  def self.name_rater
    return false unless $player && $game_map && BlueKantoPilot.kanto_current? &&
      $game_map.map_id == BlueKantoPilot.kanto_map_id(97)
    return false if $player.party.empty?
    return false unless pbConfirmMessage(BlueKantoPilot.t("Would you like to change a Pokémon's nickname?",
      "Quer mudar o apelido de um Pokémon?"))
    index = select_for_nickname
    return false unless index.is_a?(Integer) && index >= 0 && index < $player.party.length
    pokemon = $player.party[index]
    if pokemon.egg? || pokemon.foreign?($player)
      pbMessage(BlueKantoPilot.t("I can only rename a Pokémon you raised yourself.",
                                "Só posso mudar o apelido de um Pokémon de sua autoria."))
      return false
    end
    nickname = pick_nickname(pokemon)
    return false if !nickname.is_a?(String) || nickname.strip.empty? || nickname == pokemon.name
    pokemon.name = nickname
    pbMessage(BlueKantoPilot.t("Its new nickname is {1}.","O novo apelido é {1}.",pokemon.name))
    true
  end
end
