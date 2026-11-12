# Local Kanto pilot events. Loaded only by the separately prepared test game.
module BlueKantoPilot
  STARTERS = [:BULBASAUR, :CHARMANDER, :SQUIRTLE].freeze
  RIVAL_VERSIONS = {BULBASAUR: 11, CHARMANDER: 12, SQUIRTLE: 13}.freeze

  def self.progress
    $PokemonGlobal.blue_regions ||= BlueRegions.new_state("KANTO")
  end

  def self.starter
    progress["pilot_starter"]&.to_sym
  end

  def self.choose_starter
    if starter
      pbMessage(_INTL("Oak: Cuide bem do seu {1}.", GameData::Species.get(starter).name))
      return
    end
    names = STARTERS.map { |id| GameData::Species.get(id).name }
    choice = pbMessage(_INTL("Oak: Qual Pokémon vai viajar com você?"), names + [_INTL("Voltar")], 4)
    return unless choice && choice.between?(0, STARTERS.length - 1)
    species = STARTERS[choice]
    return unless pbAddPokemonSilent(species, 5)
    progress["pilot_starter"] = species.to_s
    $bag.add(:POKEBALL, 5)
    $bag.add(:POTION, 2)
    pbSetPokemonCenter
    pbMessage(_INTL("Oak: {1} escolheu você! Pegue estas Poké Bolas e fale com Blue.", names[choice]))
  end

  def self.rival_done?
    progress["pilot_rival"] == true
  end

  def self.rival
    if !starter
      pbMessage(_INTL("Blue: Escolha o seu Pokémon primeiro."))
      return
    end
    if rival_done?
      pbMessage(_INTL("Blue: A próxima batalha é em Pewter. Nos vemos na Rota 1!"))
      return
    end
    setBattleRule("canLose")
    result = TrainerBattle.start(:BLUE_KANTO_RIVAL, "Blue", RIVAL_VERSIONS.fetch(starter))
    $player.heal_party
    progress["pilot_rival"] = true
    if result
      pbMessage(_INTL("Blue: Você venceu. Vou treinar para a revanche!"))
    else
      pbMessage(_INTL("Blue: Essa foi minha. Vá treinar na Rota 1."))
    end
  end

  def self.battle(type, name, event_key = nil)
    return unless starter
    wins = (progress["pilot_wins"] ||= [])
    # New events persist stable region/map/event keys. Accept old name-only
    # entries from pilot saves built before this fix without replaying battles.
    key = event_key || "#{type}:#{name}"
    if wins.include?(key) || wins.include?(name)
      pbMessage(_INTL("{1}: Boa sorte na sua jornada!", name))
      return
    end
    setBattleRule("canLose")
    won = TrainerBattle.start(type, name)
    unless won
      $player.heal_party
      return
    end
    wins << key
    return unless type == :BLUE_KANTO_LEADER
    if BlueRegions.award(progress, "KANTO", "BOULDER")
      pbMessage(_INTL("Brock: A Boulder Badge é sua. Você concluiu o piloto de Kanto!"))
    end
  end

  def self.heal
    $player.heal_party
    pbSetPokemonCenter
    pbMessage(_INTL("Sua equipe está descansada."))
  end
end
