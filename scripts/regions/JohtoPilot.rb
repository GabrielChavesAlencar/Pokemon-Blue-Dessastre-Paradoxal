# First story nucleus of a FUTURE isolated Johto test game.
# This file is deliberately not installed in the main Decades/Kanto runtime.
# Maps and PBS trainer data must be audited and mounted before these handlers
# are bound to any RPG::Event. Do not turn these methods into global hooks.
module BlueJohtoPilot
  STARTERS = [:CHIKORITA, :CYNDAQUIL, :TOTODILE].freeze
  # Pending Johto pilot PBS must define these three rival versions.
  # A version is chosen based on the player's starter.
  RIVAL_CHOICES = {
    :CHIKORITA => [:CYNDAQUIL, 0],
    :CYNDAQUIL => [:TOTODILE, 1],
    :TOTODILE => [:CHIKORITA, 2]
  }.freeze
  RIVAL_READY = "Data/blue-johto-rival-ready.txt".freeze

  def self.regional_state
    return nil unless defined?($PokemonGlobal) && $PokemonGlobal
    record = $PokemonGlobal.blue_regions
    return nil unless record.is_a?(Hash) &&
                      record["version"] == 1 &&
                      record["current"] == "JOHTO"
    record
  end

  def self.progress
    state = regional_state
    return nil unless state
    flags = state["johto_pilot"]
    return nil if flags && !flags.is_a?(Hash)
    state["johto_pilot"] ||= {}
  end

  def self.starter
    flags = progress
    return nil unless flags
    symbol = flags["starter"]
    valid = symbol.is_a?(String) ? symbol.to_sym : nil
    STARTERS.include?(valid) ? valid : nil
  end

  def self.choose_profile
    flags = progress
    return unless flags && flags.delete("profile_pending")
    pbCharacterSelect
    $game_player.refresh_charset
    $game_player.transparent = false
  end

  def self.guard_route
    return unless progress && !starter && $player.party.empty?
    pbMessage(_INTL("Elm: A Rota 29 é perigosa sem um Pokémon. Passe no meu laboratório primeiro."))
    $game_player.moveto(2, $game_player.y)
  end

  def self.mother
    flags = progress
    return false unless flags
    if flags["mother_intro"]
      pbMessage(_INTL("Mãe: Se precisar descansar, sua casa em New Bark estará aqui."))
      return false
    end
    pbMessage(_INTL("Mãe: O Professor Elm quer falar com você no laboratório."))
    flags["mother_intro"] = true
    true
  end

  def self.neighbor
    return unless progress
    pbMessage(_INTL("Vizinha: A entrada da Rota 29 fica a oeste de New Bark. Passe no laboratório antes de sair."))
  end

  def self.silver_window
    return unless progress
    pbMessage(_INTL("Jovem: ... O que você está olhando?"))
  end

  def self.assistant
    flags = progress
    return unless flags && starter && !flags["elm_potions"]
    flags["elm_potions"] = true if pbReceiveItem(:POTION, 5)
  end

  def self.guide
    return unless progress
    pbMessage(_INTL("Cherrygrove dá acesso à Rota 30 pelo norte. O Professor Elm pediu que você procure o Sr. Pokémon por lá."))
  end

  def self.mr_pokemon
    flags = progress
    return unless flags && starter
    if flags["mystery_egg_delivered"]
      pbMessage(_INTL("Sr. Pokémon: Obrigado por levar o Ovo Misterioso ao professor."))
      return
    end
    unless flags["mystery_egg"]
      pbMessage(_INTL("Sr. Pokémon: Encontrei um Ovo Misterioso. Entregue-o ao Professor Elm."))
      flags["mystery_egg"] = true
      $player.has_pokedex = true
      pbMessage(_INTL("Oak registrou sua Pokédex. Elm quer falar com você em New Bark."))
    end
  end

  def self.fisherman
    flags = progress
    return unless flags
    unless flags["old_rod"]
      pbMessage(_INTL("Pescador: Experimente pescar quando encontrar água calma."))
      flags["old_rod"] = true if pbReceiveItem(:OLDROD)
    end
  end

  def self.rock_smash_guide
    flags = progress
    return unless flags && !flags["hm06"]
    flags["hm06"] = true if pbReceiveItem(:HM06)
  end

  def self.field_obstacle(action, event_id)
    state = regional_state
    return unless state
    move = action == "ROCK_SMASH" ? :ROCKSMASH : action.to_sym
    user = $player.get_pokemon_with_move(move)
    if BlueRegions.field_access(state, "JOHTO", action, !!user) != :allowed || !user
      pbMessage(_INTL("Você precisa de um Pokémon com {1} e da insígnia local.", GameData::Move.get(move).name))
      return
    end
    event = $game_map.events[event_id]
    return unless event
    if action == "STRENGTH"
      return unless pbConfirmMessage(_INTL("Empurrar a pedra com Strength?"))
      event.move_straight($game_player.direction)
    elsif pbConfirmMessage(_INTL("Usar {1}?", GameData::Move.get(move).name))
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      event.refresh
      pbRockSmashRandomEncounter if action == "ROCK_SMASH"
    end
  end

  def self.pickup(item, key, event_id)
    flags = progress
    return unless flags && !flags[key]
    return unless pbReceiveItem(item)
    flags[key] = true
    $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    $game_map.events[event_id]&.refresh
  end

  def self.hgss_battle_audio(track, victory: false)
    return unless regional_state && $game_map && (600..681).cover?($game_map.map_id)
    override = victory ? $PokemonGlobal.nextBattleVictoryBGM : $PokemonGlobal.nextBattleBGM
    return if override
    name = "HGSS #{track}"
    return unless File.file?("Audio/BGM/#{name}.ogg")
    victory ? pbResolveAudioFile("../../Audio/BGM/#{name}") : pbResolveAudioFile(name)
  end

  module BattleMusic
    private

    def pbGetWildBattleBGM(*args)
      BlueJohtoPilot.hgss_battle_audio("110 Battle! (Wild Pokemon Johto)") || super
    end

    def pbGetWildVictoryBGM(*args)
      BlueJohtoPilot.hgss_battle_audio("111 Victory! (Wild Pokemon)", victory: true) || super
    end

    def pbGetTrainerBattleBGM(*args)
      category = BlueMusic.trainer_category(args[0])
      track = if Array(args[0]).any? { |t| t.respond_to?(:trainer_type) && t.trainer_type == :BLUE_JOHTO_RIVAL }
                "138 Battle! (Rival)"
              elsif category == "gym"
                "143 Battle! (Gym Leader Johto)"
              else
                "118 Battle! (Trainer Battle Johto)"
              end
      BlueJohtoPilot.hgss_battle_audio(track) || super
    end

    def pbGetTrainerBattleBGMFromType(*args)
      kind = args[0]
      track = if kind == :BLUE_JOHTO_RIVAL
                "138 Battle! (Rival)"
              elsif kind == :BLUE_JOHTO_FALKNER
                "143 Battle! (Gym Leader Johto)"
              else
                "118 Battle! (Trainer Battle Johto)"
              end
      BlueJohtoPilot.hgss_battle_audio(track) || super
    end

    def pbGetTrainerVictoryBGM(*args)
      track = if BlueMusic.trainer_category(args[0]) == "gym"
                "144 Victory! (Gym Leader)"
              else
                "119 Victory! (Trainer Battle)"
              end
      BlueJohtoPilot.hgss_battle_audio(track, victory: true) || super
    end
  end

  if defined?(EventHandlers)
    EventHandlers.add(:on_enter_map, :blue_johto_battle_music, proc do |_old_map|
      Object.prepend(BattleMusic) unless Object.ancestors.include?(BattleMusic)
    end)
  end

  def self.heal
    return unless progress && $player && !$player.party.empty?
    pbSetPokemonCenter
    $player.heal_party
    pbMessage(_INTL("Enfermeira: Seus Pokémon estão recuperados!"))
  end

  def self.elm
    flags = progress
    return false unless flags
    if starter && flags["mystery_egg"] && !flags["mystery_egg_delivered"]
      pbMessage(_INTL("Elm: Você trouxe o Ovo Misterioso! Vou examiná-lo. Agora pode seguir até Violet."))
      flags["mystery_egg_delivered"] = true
      return true
    end
    if starter
      pbMessage(_INTL("Elm: Cuide bem do seu {1}. Sua jornada por Johto está começando.",
                      GameData::Species.get(starter).name))
      return false
    end
    pbMessage(_INTL("Elm: Preciso de ajuda com minhas pesquisas. Escolha um dos três Pokémon."))
    flags["elm_intro"] = true
    true
  end

  # Each Poké Ball event passes a FIXED species. No menu from Elm/dialogue.
  # This lives only in the isolated Johto runtime; no global battle hooks.
  def self.choose_starter_from_ball(species)
    flags = progress
    return false unless flags
    requested = (species.is_a?(String) || species.is_a?(Symbol)) ? species.to_sym : nil
    return false unless STARTERS.include?(requested)
    if flags["starter_received"] || flags.key?("starter")
      pbMessage(_INTL("Elm: Você já escolheu seu Pokémon."))
      return false
    end
    unless flags["elm_intro"]
      pbMessage(_INTL("Elm: Converse comigo antes de escolher uma das Poké Bolas."))
      return false
    end
    name = GameData::Species.get(requested).name
    return false unless pbConfirmMessage(_INTL("Escolher {1} como seu parceiro?", name))
    # Only mark the save after the engine actually succeeds in granting it.
    return false unless pbAddPokemonSilent(requested, 5)
    flags["starter"] = requested.to_s
    flags["starter_received"] = true
    pbMessage(_INTL("Elm: {1} irá com você. Boa jornada por Johto!",
                    GameData::Species.get(requested).name))
    true
  end

  # Kept as a non-granting compatibility entrypoint for older experiment
  # calls; actual selection is exclusively via physical Poké Ball events.
  def self.choose_starter
    flags = progress
    return false unless flags
    pbMessage(_INTL("Elm: Escolha uma das três Poké Bolas sobre as bancadas."))
    false
  end

  def self.rival_species
    chosen = starter
    chosen ? RIVAL_CHOICES.fetch(chosen)[0] : nil
  end

  def self.rival_version
    chosen = starter
    chosen ? RIVAL_CHOICES.fetch(chosen)[1] : nil
  end

  def self.rival_fought?
    flags = progress
    flags && flags["rival_fought"] == true
  end

  def self.rival
    flags = progress
    return false unless flags
    unless starter
      pbMessage(_INTL("Rival: Vá escolher seu Pokémon no laboratório do Elm primeiro."))
      return false
    end
    if rival_fought?
      pbMessage(_INTL("Rival: Na próxima vez estarei mais forte."))
      return false
    end
    # Never invoke a trainer ID until the isolated Johto pilot has compiled
    # and explicitly marked all three custom trainer PBS versions as ready.
    unless File.file?(RIVAL_READY) &&
           File.read(RIVAL_READY).strip == "BLUE_JOHTO_RIVAL_V1_READY" &&
           defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
      pbMessage(_INTL("O encontro com o rival ainda está sendo preparado no piloto de Johto."))
      return false
    end
    pbMessage(_INTL("Rival: Vamos testar esses novos parceiros!"))
    setBattleRule("canLose")
    victory = TrainerBattle.start(:BLUE_JOHTO_RIVAL, "Rival", rival_version)
    $player.heal_party if $player && $player.respond_to?(:heal_party)
    flags["rival_fought"] = true
    pbMessage(victory ?
      _INTL("Rival: Essa vitória foi sua. Vou treinar mais!") :
      _INTL("Rival: Dessa vez eu ganhei. Nos vemos na estrada!"))
    true
  rescue IOError, SystemCallError
    pbMessage(_INTL("Não foi possível validar o treino do rival."))
    false
  end
end
