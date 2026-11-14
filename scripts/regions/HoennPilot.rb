# Loaded by the standalone Hoenn copy.

module BlueHoennPilot
  STARTERS = [:TREECKO, :TORCHIC, :MUDKIP].freeze
  WILD_THEME = "BLUE_HOENN_Wild".freeze
  VICTORY_THEME = "BLUE_HOENN_WildVictory".freeze
  MARKER = "Data/blue-hoenn-pilot.txt".freeze

  def self.metadata
    return @metadata if @metadata
    lines = File.readlines(MARKER, chomp: true)
    raise "Marcador do piloto de Hoenn inválido." unless lines.shift == "BLUE_HOENN_PILOT_V1"
    values = lines.flat_map { |line| line.split(",") }.map { |part| Integer(part, 10) }
    start = values.shift(3)
    maps = values.each_slice(2).to_h
    expected = [7, 8, 11, 12, 13, 101]
    raise "Mapas do piloto de Hoenn inválidos." unless [expected, [7, 8, 11, 12, 13, 14, 101, 102, 103]].include?(maps.keys.sort) &&
                                                         maps.values.uniq.length == maps.length &&
                                                         maps.values.all? { |id| (700..999).cover?(id) } &&
                                                         start == [maps.fetch(8), 25, 6]
    @metadata = [start, maps]
  end

  def self.verify_compilation
    GameData::Encounter.load
    GameData::MapMetadata.load
    GameData::Trainer.load
    _, maps = metadata
    route = maps.fetch(101)
    table = GameData::Encounter.get(route, 0)
    expected = [:ZIGZAGOON, :POOCHYENA, :WURMPLE]
    unless table && table.types.fetch(:Land, []).map { |slot| slot[1] }.sort == expected.sort
      raise "Tabela de encontros da Rota 101 não foi compilada."
    end
    maps.each_value do |id|
      unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", id)) && GameData::MapMetadata.exists?(id)
        raise "Mapa ou metadados de Hoenn ausentes: #{id}"
      end
    end
    if maps[102] && ![[:YOUNGSTER, "Calvin"], [:BUGCATCHER, "Rick"],
                      [:YOUNGSTER, "Allen"], [:LASS, "Tiana"]].all? { |kind, name| GameData::Trainer.exists?(kind, name, 102) }
      raise "Treinadores da Rota 102 incompletos"
    end
    connections = load_data("Data/map_connections.dat")
    links = [[maps.fetch(7), route], [maps.fetch(12), route]]
    [102, 103].each do |source_id|
      next unless maps[source_id]
      raise "Encontros ausentes na Rota #{source_id}" unless GameData::Encounter.exists?(maps[source_id], 0)
      links << [maps.fetch(12), maps.fetch(source_id)]
    end
    links.each do |first, second|
      unless connections.any? { |row| [row[0], row[3]].sort == [first, second].sort }
        raise "Conexão de Hoenn não compilada: #{first}/#{second}"
      end
    end
    true
  end

  def self.state
    region = $PokemonGlobal&.blue_regions
    return unless region && region["current"] == "HOENN"
    region["hoenn_pilot"] ||= {}
  end

  def self.choose_profile
    progress = state
    return unless progress && progress["profile_pending"]
    pbCharacterSelect
    $game_player.refresh_charset
    $game_player.transparent = false
    progress.delete("profile_pending")
  end

  def self.battle(trainer_type, name)
    progress = state
    return unless progress && !$player.party.empty?
    key = "route102_#{name}"
    if progress[key]
      pbMessage(_INTL("{1}: Boa sorte na jornada!", name))
      return
    end
    pbMessage(_INTL("{1}: Vamos batalhar?", name))
    progress[key] = true if TrainerBattle.start(trainer_type, name, 102)
  end

  def self.mart
    return unless state
    pbPokemonMart([:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL])
  end

  def self.clock
    progress = state
    return unless progress && !progress["clock_set"]
    now = pbGetTimeNow
    pbMessage(_INTL("Você ajustou o relógio para {1}.", now.strftime("%H:%M")))
    progress["clock_set"] = true
  end

  # Only active inside the separate Hoenn pilot. These flags are kept in the
  # regional save, never in a global switch shared by Kanto/Johto/Decades.
  RIVAL_VERSIONS = { TREECKO: 210, TORCHIC: 211, MUDKIP: 212 }.freeze
  RIVAL_COUNTER = { TREECKO: :TORCHIC, TORCHIC: :MUDKIP,
                    MUDKIP: :TREECKO }.freeze

  def self.starter
    flags = state
    return nil unless flags
    chosen = flags["starter"]
    symbol = chosen.to_sym if chosen.is_a?(String) || chosen.is_a?(Symbol)
    STARTERS.include?(symbol) ? symbol : nil
  end

  def self.mother
    flags = state
    return false unless flags
    if flags["pokedex_given"] && !flags["running_shoes_given"]
      unless $player && $player.respond_to?(:has_running_shoes=)
        pbMessage(_INTL("Mãe: Ainda não consigo entregar seus Tênis de Corrida."))
        return false
      end
      $player.has_running_shoes = true
      flags["running_shoes_given"] = true
      pbMessage(_INTL("Mãe: Você recebeu os Tênis de Corrida! Boa viagem por Hoenn!"))
      return true
    end
    if !flags["clock_set"]
      pbMessage(_INTL("Mãe: Chegamos a Littleroot! Ajuste o relógio do quarto."))
    elsif flags["pokedex_given"]
      pbMessage(_INTL("Mãe: Cuide bem dos seus Pokémon e volte quando quiser!"))
    else
      pbMessage(_INTL("Mãe: O Professor Birch está perto da Rota 101."))
    end
    flags["met_mother"] = true
    true
  end

  def self.route_birch
    flags = state
    return false unless flags
    return false if flags["birch_rescued"] || flags["met_birch"]
    if !flags["met_mother"] || !flags["clock_set"]
      pbMessage(_INTL("Converse com sua mãe e ajuste o relógio antes de partir."))
    else
      flags["birch_rescue_active"] = true
      pbMessage(_INTL("Birch: Socorro! Um Zigzagoon está me perseguindo! Escolha uma das três Poké Bolas na maleta perto daqui!"))
    end
    # The player-touch event guards the northbound passage. Don't allow
    # walking into the rest of Route 101 without resolving Birch's rescue.
    $game_player.moveto($game_player.x, 19) if $game_player && $game_player.y == 18
    true
  end

  # Kept for the three decorative lab balls in older copies of the pilot.
  # Only the three real ball EVENTS near Birch may award a starter.
  def self.choose_starter(species, rescue_birch: false)
    return false unless state && STARTERS.include?(species)
    if starter
      pbMessage(_INTL("Você já tem um Pokémon inicial."))
    else
      pbMessage(_INTL("Birch: A maleta está na Rota 101. Primeiro preciso de ajuda!"))
    end
    false
  end

  def self.choose_birch_ball(species)
    flags = state
    return false unless flags && STARTERS.include?(species)
    return rescue_birch_battle if starter && !flags["birch_rescued"] &&
                                  !flags["met_birch"] && flags["birch_rescue_active"]
    if starter
      pbMessage(_INTL("Você já escolheu seu Pokémon inicial."))
      return false
    end
    unless flags["birch_rescue_active"]
      pbMessage(_INTL("Há três Poké Bolas na maleta do Professor Birch."))
      return false
    end
    name = GameData::Species.get(species).name
    return false unless pbConfirmMessage(_INTL("Escolher {1} para ajudar Birch?", name))
    return false unless pbAddPokemonSilent(species, 5)
    flags["starter"] = species.to_s
    # Older saves from the first Hoenn pilot already received five balls with
    # the starter. This explicit new flag avoids re-awarding them on migration.
    flags["balls_at_lab_pending"] = true
    rescue_birch_battle
  end

  def self.rescue_birch_battle
    flags = state
    return false unless flags && starter && flags["birch_rescue_active"]
    return false if flags["birch_rescued"] || flags["met_birch"]
    setBattleRule("canLose")
    WildBattle.start(:ZIGZAGOON, 2)
    flags["birch_rescued"] = true
    flags["met_birch"] = true
    flags.delete("birch_rescue_active")
    $player.heal_party if $player && $player.respond_to?(:heal_party)
    pbMessage(_INTL("Birch: Obrigado! Visite meu laboratório quando puder."))
    true
  end

  def self.rival_name
    return "May" if $player && $player.respond_to?(:gender) && $player.gender == 0
    "Brendan"
  end

  def self.rival_103
    flags = state
    return false unless flags && starter
    return false unless flags["birch_rescued"] || flags["met_birch"]
    return false if flags["rival_103_done"]
    name = rival_name
    pbMessage(_INTL("{1}: Vamos testar nossos Pokémon antes de voltar a Littleroot!", name))
    setBattleRule("canLose")
    victory = TrainerBattle.start(:RIVAL1, name, RIVAL_VERSIONS.fetch(starter))
    $player.heal_party if $player && $player.respond_to?(:heal_party)
    # A canLose result is a completed story battle whether victory or loss.
    flags["rival_103_done"] = true
    pbMessage(victory ?
      _INTL("{1}: Você batalhou muito bem! Volte ao laboratório de Birch.", name) :
      _INTL("{1}: Foi uma boa batalha! Volte ao laboratório de Birch.", name))
    true
  end

  def self.birch
    flags = state
    return false unless flags
    unless starter && (flags["birch_rescued"] || flags["met_birch"])
      pbMessage(_INTL("Birch: Estou pesquisando os Pokémon da Rota 101."))
      return false
    end
    unless flags["rival_103_done"]
      pbMessage(_INTL("Birch: Encontre Brendan ou May na Rota 103 e depois volte aqui."))
      return false
    end
    if flags["pokedex_given"]
      pbMessage(_INTL("Birch: Continue registrando os Pokémon de Hoenn!"))
      return false
    end
    unless $player && $player.respond_to?(:has_pokedex=)
      pbMessage(_INTL("Birch: Não foi possível ativar sua Pokédex."))
      return false
    end
    if flags["balls_at_lab_pending"]
      unless $bag && $bag.add(:POKEBALL, 5)
        pbMessage(_INTL("Birch: Abra espaço na Bolsa para receber cinco Poké Bolas."))
        return false
      end
      flags.delete("balls_at_lab_pending")
    end
    $player.has_pokedex = true
    flags["pokedex_given"] = true
    pbMessage(_INTL("Birch: Aqui está sua Pokédex! Volte para falar com sua mãe antes de partir."))
    true
  end

  def self.heal
    return unless state
    if $player.party.empty?
      pbMessage(_INTL("Enfermeira: Traga seus Pokémon quando precisar de atendimento."))
      return
    end
    $player.heal_party
    pbMessage(_INTL("Enfermeira: Seus Pokémon estão recuperados. Boa viagem!"))
  end

  module Music
    private

    def pbGetWildBattleBGM(*args)
      if BlueHoennPilot.state && !$PokemonGlobal.nextBattleBGM &&
         File.file?("Audio/BGM/#{BlueHoennPilot::WILD_THEME}.ogg")
        return pbResolveAudioFile(BlueHoennPilot::WILD_THEME)
      end
      super
    end

    def pbGetWildVictoryBGM(*args)
      if BlueHoennPilot.state && !$PokemonGlobal.nextBattleVictoryBGM &&
         File.file?("Audio/BGM/#{BlueHoennPilot::VICTORY_THEME}.ogg")
        return pbResolveAudioFile("../../Audio/BGM/" + BlueHoennPilot::VICTORY_THEME)
      end
      super
    end
  end

  module Start
    def select_and_prepare
      return super unless @new_game && $PokemonGlobal && File.file?(BlueHoennPilot::MARKER)
      start, = BlueHoennPilot.metadata
      $PokemonGlobal.blue_regions = BlueRegions.new_state("HOENN")
      $PokemonGlobal.blue_regions["hoenn_pilot"] = { "profile_pending" => true }
      BlueStory.choose_mode(:story)
      BlueCampaign.begin_journey(false)
      $PokemonGlobal.blue_traditional_starters = true
      $PokemonGlobal.blue_campaign_departure = false
      pbChangePlayer(1)
      $game_player.refresh_charset if $game_player.respond_to?(:refresh_charset)
      $game_player.transparent = false
      $data_system.start_map_id, $data_system.start_x, $data_system.start_y = start
    end
  end

  BlueRegionStart.singleton_class.prepend(Start)
  EventHandlers.add(:on_enter_map, :blue_hoenn_music, proc do |_old_map|
    Object.prepend(Music) unless Object.ancestors.include?(Music)
  end)
end
