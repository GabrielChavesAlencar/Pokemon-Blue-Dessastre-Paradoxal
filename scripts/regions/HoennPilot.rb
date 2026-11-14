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
    stage3 = [7, 8, 11, 12, 13, 14, 16, 17, 18, 19, 20, 101, 102, 103, 104, 105, 106, 156]
    stage4 = (stage3 + [21, 22, 23, 24, 25, 26, 27, 130, 131, 157]).sort
    stage5 = (stage4 + [28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                        38, 39, 40, 108, 111, 112, 159, 160, 161, 162]).sort
    stage2 = [7, 8, 11, 12, 13, 14, 101, 102, 103]
    raise "Mapas do piloto de Hoenn inválidos." unless [stage2, stage3, stage4, stage5].include?(maps.keys.sort) &&
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
    if maps[104] && maps[156]
      {104 => [:POOCHYENA, :MARILL, :WURMPLE, :TAILLOW, :WINGULL],
       156 => [:WURMPLE, :POOCHYENA, :SHROOMISH, :CASCOON, :SILCOON,
               :SLAKOTH, :TAILLOW]}.each do |source_id, species|
        encounter = GameData::Encounter.get(maps.fetch(source_id), 0)
        unless encounter && encounter.types.fetch(:Land, []).map { |slot| slot[1] }.sort == species.sort
          raise "Encontros da etapa 3 ausentes no mapa #{source_id}"
        end
      end
      expected_trainers = [
        [:YOUNGSTER, "Billy", 104], [:FISHERMAN, "Darian", 104],
        [:LADY, "Cindy", 104], [:RICHBOY, "Winston", 104],
        [:LASS, "Haley", 104], [:TWINS, "Gina & Mia", 104],
        [:FISHERMAN, "Ivan", 104], [:BUGCATCHER, "James", 156],
        [:BUGCATCHER, "Lyle", 156], [:BLUE_HOENN_AQUA, "Recruta", 304]
      ]
      unless expected_trainers.all? { |kind, name, ver| GameData::Trainer.exists?(kind, name, ver) }
        raise "Treinadores da Rota 104/Petalburg Woods ou Recruta Aqua incompletos"
      end
    end
    if maps[130] && maps[157] && maps[27]
      route116 = GameData::Encounter.get(maps.fetch(130), 0)
      tunnel = GameData::Encounter.get(maps.fetch(157), 0)
      expected_116 = [:NINCADA, :TAILLOW, :WHISMUR, :POOCHYENA, :ABRA, :SKITTY]
      unless route116 && route116.types.fetch(:Land, []).map { |slot| slot[1] }.sort == expected_116.sort
        raise "Tabela de grama da Rota 116 não compilada"
      end
      unless tunnel && tunnel.types.fetch(:Cave, []).map { |slot| slot[1] } == [:WHISMUR]
        raise "Encontros de Whismur em Rusturf Tunnel não compilados"
      end
      required = [
        [:YOUNGSTER, "Josh", 27], [:YOUNGSTER, "Tommy", 27],
        [:HIKER, "Marc", 27], [:YOUNGSTER, "Joey", 130],
        [:BUGCATCHER, "Jose", 130], [:LASS, "Karen", 130],
        [:LASS, "Janice", 130], [:YOUNGSTER, "Jerry", 130],
        [:RICHBOY, "Dawson", 130], [:LADY, "Sarah", 130],
        [:YOUNGSTER, "Johnson", 130], [:HIKER, "Clark", 130],
        [:HIKER, "Devan", 130], [:HIKER, "Mike", 157],
        [:BLUE_HOENN_ROXANNE, "Roxanne", 427],
        [:BLUE_HOENN_AQUA, "Recruta", 405]
      ]
      unless required.all? { |kind, name, ver| GameData::Trainer.exists?(kind, name, ver) }
        raise "Treinadores da Etapa 4 não compilados: Roxanne/Rusturf/Route116"
      end
    end
    if maps[28] && maps[32] && maps[159]
      expected_caves = {
        159 => [:MAKUHITA, :ZUBAT, :ABRA, :GEODUDE],
        160 => [:ARON, :ZUBAT, :ABRA, :MAKUHITA, :MAWILE, :SABLEYE],
        161 => [:ARON, :ZUBAT, :ABRA, :MAWILE, :SABLEYE],
        162 => [:MAKUHITA, :ZUBAT, :ABRA, :ARON]
      }
      expected_caves.each do |mid, species|
        encounters = GameData::Encounter.get(maps.fetch(mid), 0)
        unless encounters && encounters.types.fetch(:Cave, []).map { |slot| slot[1] }.sort == species.sort
          raise "Encontros de Granite Cave incompletos: #{mid}"
        end
      end
      encounters = [
        [:LASS, "Laura", 31], [:YOUNGSTER, "Takao", 31],
        [:FISHERMAN, "Brenden", 31], [:LASS, "Lilith", 31],
        [:YOUNGSTER, "Cristian", 31], [:LASS, "Jocelyn", 31],
        [:FISHERMAN, "Elliot", 108], [:FISHERMAN, "Ned", 108],
        [:BLUE_HOENN_BRAWLY, "Brawly", 531],
        [:BLUE_HOENN_AQUA, "Recruta", 539],
        [:BLUE_HOENN_AQUA, "Recruta", 540]
      ]
      unless encounters.all? { |kind, name, version| GameData::Trainer.exists?(kind, name, version) }
        raise "Treinadores ou Brawly/Museu de Slateport não compilados"
      end
    end
    names = ["May", "Brendan"]
    unless names.all? { |name| [210, 211, 212].all? { |version|
             GameData::Trainer.exists?(:RIVAL1, name, version) } }
      raise "As seis variantes PBS do rival de Hoenn não foram compiladas"
    end
    connections = load_data("Data/map_connections.dat")
    links = [[maps.fetch(7), route], [maps.fetch(12), route]]
    [102, 103].each do |source_id|
      next unless maps[source_id]
      raise "Encontros ausentes na Rota #{source_id}" unless GameData::Encounter.exists?(maps[source_id], 0)
      links << [maps.fetch(12), maps.fetch(source_id)]
    end
    if maps[104] && maps[16]
      links.concat([[maps.fetch(102), maps.fetch(16)], [maps.fetch(16), maps.fetch(104)]])
    end
    if maps[21] && maps[130]
      links.concat([[maps.fetch(104), maps.fetch(21)], [maps.fetch(21), maps.fetch(130)]])
    end
    if maps[28] && maps[32]
      links.concat([[maps.fetch(28), maps.fetch(108)], [maps.fetch(32), maps.fetch(111)]])
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
      $game_player.moveto($game_player.x, 19) if $game_player && $game_player.y == 18
      return true
    end
    flags["birch_rescue_active"] = true
    pbMessage(_INTL("Birch: Socorro! Um Zigzagoon me persegue! Escolha uma das três Poké Bolas na maleta logo ao norte!"))
    # The player must be able to STEP PAST the entrance trigger to reach
    # the three physical Poké Balls (row 16 in the pinned 20x20 route).
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


  STAGE3_SIGNS = {
    PETALBURG_CITY: "Petalburg: cidade de encontro entre pessoas e natureza.",
    PETALBURG_GYM: "Ginásio de Petalburg. Líder Norman, tipo Normal.",
    WALLY_HOUSE: "Casa de Wally.",
    ROUTE104_SOUTH: "Rota 104: Petalburg fica a leste.",
    ROUTE104_NORTH: "Rota 104: Rustboro fica ao norte, ainda em preparação neste piloto.",
    BRINEY_HOUSE: "Casa do marinheiro Mr. Briney.",
    FLOWER_SHOP: "Floricultura Pretty Petal.",
    WOODS_TIPS_PP: "Os movimentos têm PP. Procure um Centro Pokémon para recuperar sua equipe.",
    WOODS_TIPS_EXP: "Pokémon que participam da batalha recebem experiência."
  }.freeze

  def self.sign(symbol)
    return false unless state
    message = STAGE3_SIGNS[symbol]
    return false unless message
    pbMessage(_INTL(message))
    true
  end

  def self.wally_family
    flags = state
    return false unless flags
    pbMessage(flags["wally_captured"] ?
      _INTL("Família de Wally: Nosso filho está animado por ter capturado seu primeiro Pokémon.") :
      _INTL("Família de Wally: Ele quer conhecer melhor os Pokémon. Visite o ginásio de Norman."))
    true
  end

  def self.norman_intro
    flags = state
    return false unless flags
    unless flags["pokedex_given"]
      pbMessage(_INTL("Norman: Primeiro conclua seu treinamento com o Professor Birch."))
      return false
    end
    unless flags["wally_captured"]
      pbMessage(_INTL("Norman: Wally quer aprender a capturar Pokémon. Vamos ajudá-lo!"))
      pbMessage(_INTL("Wally encontrou um Ralts, lançou uma Poké Bola e conseguiu capturá-lo!"))
      flags["wally_captured"] = true
      pbMessage(_INTL("Norman: Muito bem, Wally! Continue sua jornada até Rustboro."))
      return true
    end
    pbMessage(_INTL("Norman: Volte quando tiver quatro insígnias de Hoenn. Então batalharemos!"))
    true
  end

  def self.flower_shop
    flags = state
    return false unless flags
    if flags["wailmer_pail_received"]
      pbMessage(_INTL("Floricultura: Plante suas Berries e regue com o Wailmer Pail!"))
      return false
    end
    unless $bag && $bag.add(:WAILMERPAIL, 1)
      pbMessage(_INTL("Floricultura: Abra espaço na Bolsa para receber o regador Wailmer Pail."))
      return false
    end
    flags["wailmer_pail_received"] = true
    pbMessage(_INTL("Você recebeu o Wailmer Pail para cuidar das Berries!"))
    true
  end

  def self.briney
    flags = state
    return false unless flags
    unless flags["peecko_rescued"] && flags["stone_letter_received"]
      pbMessage(_INTL("Mr. Briney: primeiro salve Peecko e converse com o presidente Stone em Rustboro."))
      return false
    end
    pbMessage(_INTL("Mr. Briney: obrigado por ajudar Peecko! Posso levá-lo a Dewford."))
    return false unless pbConfirmMessage(_INTL("Viajar para Dewford agora?"))
    boat_to(28)
  end

  def self.pickup(item, key, event_id)
    flags = state
    return false unless flags && item.is_a?(Symbol) && key.is_a?(String)
    storage = "pickup_#{key}"
    return false if flags[storage]
    unless $bag && $bag.add(item, 1)
      pbMessage(_INTL("Sua Bolsa está cheia."))
      return false
    end
    flags[storage] = true
    if $game_map && $game_self_switches && event_id.is_a?(Integer)
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      $game_map.events[event_id]&.refresh
    end
    pbMessage(_INTL("Você encontrou {1}!", item.to_s))
    true
  end

  def self.battle_stage3(kind, name, version, double = false)
    flags = state
    return false unless flags && $player && !$player.party.empty?
    key = "trainer_#{version}_#{kind}_#{name}"
    if flags[key]
      pbMessage(_INTL("{1}: Você está treinando bastante!", name))
      return false
    end
    if double && (defined?(pbCanDoubleBattle?) && !pbCanDoubleBattle?)
      pbMessage(_INTL("As gêmeas só batalham quando você possui dois Pokémon disponíveis."))
      return false
    end
    pbMessage(_INTL("{1}: Vamos batalhar?", name))
    setBattleRule("double") if double
    won = TrainerBattle.start(kind, name, version)
    flags[key] = true if won
    won
  end

  def self.forest_aqua
    flags = state
    return false unless flags
    unless flags["pokedex_given"] && flags["wally_captured"]
      pbMessage(_INTL("Um funcionário da Devon precisa de ajuda na floresta. Primeiro fale com Norman em Petalburg."))
      return false
    end
    unless flags["forest_aqua_defeated"]
      pbMessage(_INTL("Recruta Aqua: Esse documento é da Devon! Não se intrometa!"))
      setBattleRule("canLose")
      won = TrainerBattle.start(:BLUE_HOENN_AQUA, "Recruta", 304)
      unless won
        pbMessage(_INTL("O recruta continua no caminho. Cure sua equipe e volte a enfrentá-lo."))
        return false
      end
      flags["forest_aqua_defeated"] = true
      pbMessage(_INTL("Funcionário Devon: Obrigado! Afugentamos a Equipe Aqua."))
    end
    return false if flags["forest_greatball_received"]
    unless $bag && $bag.add(:GREATBALL, 1)
      pbMessage(_INTL("Funcionário Devon: Guarde espaço na Bolsa para sua Great Ball!"))
      return false
    end
    flags["forest_greatball_received"] = true
    pbMessage(_INTL("Funcionário Devon: Receba esta Great Ball como agradecimento!"))
    true
  end


  # Stage 4 remains completely save-scoped to "HOENN", with one Stone Badge
  # awarded by the existing regional registry. No native badge or global
  # crystal count is overwritten.
  STAGE4_SIGNS = {
    RUSTBORO_CITY: "Rustboro: cidade de ciência, escolas e ginásios.",
    RUSTBORO_GYM: "Ginásio de Rustboro. Líder Roxanne, tipo Pedra.",
    DEVON_CORP: "Devon Corporation: pesquisa e tecnologia.",
    TRAINER_SCHOOL: "Escola de Treinadores: aprenda sobre tipos e condições.",
    CUTTER_HOUSE: "Casa do especialista na técnica Cut.",
    RUSTURF_TUNNEL: "Túnel Rusturf: siga pela Rota 116 ao leste.",
    ROUTE116_TIPS: "Dica: use a Bolsa para organizar os itens.",
    ROUTE116_TRAINERS: "Dica: treine seus Pokémon antes de explorar o túnel.",
    TUNNELERS_HOUSE: "Casa dos Escavadores.",
    RUSTURF_ENTRANCE: "Entrada do Túnel Rusturf."
  }.freeze

  def self.sign_stage4(key)
    return false unless state && STAGE4_SIGNS.key?(key)
    pbMessage(_INTL(STAGE4_SIGNS.fetch(key)))
    true
  end

  def self.stone_badge?
    flags = state
    return false unless flags && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN").include?("STONE")
  end

  def self.roxanne_tm
    flags = state
    return false unless flags && stone_badge?
    if flags["roxanne_tm_given"]
      pbMessage(_INTL("Roxanne: Continue evoluindo suas estratégias de batalha!"))
      return false
    end
    item = [:TM100, :TM39].find do |candidate|
      GameData::Item.exists?(candidate) &&
        GameData::Item.get(candidate).move == :ROCKTOMB
    end
    unless item
      pbMessage(_INTL("Roxanne: A TM Rock Tomb não está registrada neste Blue. Sua recompensa está reservada."))
      return false
    end
    unless $bag && $bag.add(item, 1)
      pbMessage(_INTL("Roxanne: Libere espaço na Bolsa para receber Rock Tomb."))
      return false
    end
    flags["roxanne_tm_given"] = true
    pbMessage(_INTL("Roxanne: Receba Rock Tomb! Use-a com inteligência."))
    true
  end

  def self.roxanne
    flags = state
    return false unless flags && $player && !$player.party.empty?
    if stone_badge?
      flags["roxanne_defeated"] = true
      return roxanne_tm
    end
    unless flags["wally_captured"] && flags["forest_aqua_defeated"]
      pbMessage(_INTL("Roxanne: Explore Petalburg Woods e ajude o funcionário Devon antes do desafio."))
      return false
    end
    pbMessage(_INTL("Roxanne: Sou especialista em Pokémon de Pedra. Aceita meu desafio?"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_ROXANNE, "Roxanne", 427)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions, "HOENN", "STONE")
      pbMessage(_INTL("Roxanne: Erro ao registrar a Stone Badge. Verifique o estado regional."))
      return false
    end
    flags["roxanne_defeated"] = true
    pbMessage(_INTL("Você conquistou a Stone Badge de Hoenn! A técnica Cut está liberada nesta região."))
    roxanne_tm
    true
  end

  def self.cutter
    flags = state
    return false unless flags
    if flags["hm_cut_given"]
      pbMessage(_INTL("Especialista: Ensine Cut a um Pokémon. A Stone Badge libera seu uso em Hoenn."))
      return false
    end
    item = [:HM01, :HMCUT].find { |candidate| GameData::Item.exists?(candidate) }
    unless item
      pbMessage(_INTL("Especialista: O HM Cut ainda não existe nos itens desta instalação."))
      return false
    end
    unless $bag && $bag.add(item, 1)
      pbMessage(_INTL("Especialista: Abra espaço na Bolsa para receber Cut."))
      return false
    end
    flags["hm_cut_given"] = true
    pbMessage(_INTL("Você recebeu HM Cut! Precisa da Stone Badge para usá-lo em Hoenn."))
    true
  end

  def self.cut_tree(event_id)
    flags = state
    return false unless flags && $player && event_id.is_a?(Integer)
    return false unless $game_map && $game_self_switches && $game_map.events[event_id]
    identifier = "cut_tree_#{$game_map.map_id}_#{event_id}"
    if flags[identifier]
      $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
      $game_map.events[event_id].refresh
      return true
    end
    unless stone_badge?
      pbMessage(_INTL("Uma árvore pequena bloqueia a passagem. A Stone Badge de Hoenn é necessária."))
      return false
    end
    unless $bag && [:HM01, :HMCUT].any? { |item|
           GameData::Item.exists?(item) && $bag.has?(item) }
      pbMessage(_INTL("Você precisa obter o HM Cut em Rustboro."))
      return false
    end
    unless $player.party.any? { |pokemon| pokemon.respond_to?(:hasMove?) &&
                                     pokemon.hasMove?(:CUT) }
      pbMessage(_INTL("Nenhum Pokémon da sua equipe conhece Cut."))
      return false
    end
    return false unless pbConfirmMessage(_INTL("Usar Cut para retirar a árvore?"))
    flags[identifier] = true
    $game_self_switches[[$game_map.map_id, event_id, "A"]] = true
    $game_map.events[event_id].refresh
    pbMessage(_INTL("A árvore foi cortada."))
    true
  end

  def self.teacher
    flags = state
    return false unless flags
    if flags["quick_claw_given"]
      pbMessage(_INTL("Professora: Quick Claw pode fazer seu Pokémon agir primeiro!"))
      return false
    end
    unless GameData::Item.exists?(:QUICKCLAW) && $bag && $bag.add(:QUICKCLAW, 1)
      pbMessage(_INTL("Professora: Confira se o item Quick Claw existe e abra espaço na Bolsa."))
      return false
    end
    flags["quick_claw_given"] = true
    pbMessage(_INTL("Você recebeu Quick Claw na Escola de Treinadores!"))
    true
  end

  def self.rustboro_theft
    flags = state
    return false unless flags && stone_badge?
    return false if flags["devon_theft_seen"]
    flags["devon_theft_seen"] = true
    pbMessage(_INTL("Funcionário Devon: Um recruta Aqua roubou nossos produtos! Ele fugiu pela Rota 116!"))
    true
  end

  def self.briney_route116
    flags = state
    return false unless flags
    if flags["peecko_rescued"]
      pbMessage(_INTL("Mr. Briney: Você salvou Peecko! Depois conversaremos sobre viajar pelo mar."))
    elsif flags["devon_theft_seen"]
      pbMessage(_INTL("Mr. Briney: Um recruta levou minha Wingull Peecko para Rusturf Tunnel."))
    else
      pbMessage(_INTL("Mr. Briney: Eu e Peecko gostamos de caminhar pela Rota 116."))
    end
    true
  end

  def self.peeko
    flags = state
    return false unless flags
    pbMessage(flags["peecko_rescued"] ?
      _INTL("Peecko: Pii! Parece muito feliz por estar segura.") :
      _INTL("Peecko: Pii... Está com medo daquele recruta!"))
    true
  end

  def self.rusturf_goods_reward
    flags = state
    return false unless flags && flags["rusturf_aqua_defeated"]
    return true if flags["devon_goods_recovered"]
    if GameData::Item.exists?(:DEVONGOODS)
      unless $bag && $bag.add(:DEVONGOODS, 1)
        pbMessage(_INTL("Os produtos Devon ainda estão aqui. Abra espaço na Bolsa para recuperá-los."))
        return false
      end
      flags["devon_goods_in_bag"] = true
    else
      flags["devon_goods_virtual"] = true
      pbMessage(_INTL("Os produtos Devon foram registrados como missão regional, pois este Blue não possui o item."))
    end
    flags["devon_goods_recovered"] = true
    pbMessage(_INTL("Você recuperou os produtos roubados da Devon. Retorne à corporação."))
    true
  end

  def self.rusturf_aqua
    flags = state
    return false unless flags
    # Recover from a missed city touch trigger instead of trapping a save:
    # the Stone Badge is still mandatory, and the report is unique.
    rustboro_theft if stone_badge? && !flags["devon_theft_seen"]
    unless flags["devon_theft_seen"] && stone_badge?
      pbMessage(_INTL("O túnel está silencioso. Investigue Rustboro após conquistar a Stone Badge."))
      return false
    end
    if flags["rusturf_aqua_defeated"]
      return rusturf_goods_reward
    end
    pbMessage(_INTL("Recruta Aqua: Não vou devolver os produtos da Devon sem uma batalha!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_AQUA, "Recruta", 405)
      $player.heal_party if $player && $player.respond_to?(:heal_party)
      return false
    end
    flags["rusturf_aqua_defeated"] = true
    flags["peecko_rescued"] = true
    pbMessage(_INTL("O recruta fugiu! Peecko está livre e pode voltar com Mr. Briney."))
    rusturf_goods_reward
  end

  def self.devon_route116
    flags = state
    return false unless flags
    rustboro_theft if stone_badge? && !flags["devon_theft_seen"]
    if flags["devon_goods_recovered"]
      pbMessage(_INTL("Funcionário Devon: Leve nossos produtos à corporação de Rustboro. Obrigado!"))
    elsif flags["devon_theft_seen"]
      pbMessage(_INTL("Funcionário Devon: Precisamos recuperar o pacote roubado no túnel."))
    else
      pbMessage(_INTL("Funcionário Devon: Estamos preparando melhorias para os treinadores."))
    end
    true
  end

  def self.devon_employee
    flags = state
    return false unless flags
    if flags["devon_goods_delivered"]
      pbMessage(_INTL("Devon: O presidente Stone deseja conversar com você."))
      return true
    end
    unless flags["devon_goods_recovered"]
      pbMessage(_INTL("Devon: Procure um funcionário na Rota 116 se quiser ajudar nossa pesquisa."))
      return false
    end
    if flags["devon_goods_in_bag"] && GameData::Item.exists?(:DEVONGOODS)
      unless $bag && $bag.has?(:DEVONGOODS) && $bag.remove(:DEVONGOODS, 1)
        pbMessage(_INTL("Devon: Os produtos não foram encontrados na Bolsa."))
        return false
      end
    end
    flags["devon_goods_delivered"] = true
    pbMessage(_INTL("Devon: Obrigado por devolver os produtos! O presidente está no terceiro andar."))
    true
  end

  def self.mr_stone
    flags = state
    return false unless flags
    unless flags["devon_goods_delivered"]
      pbMessage(_INTL("Mr. Stone: Nossa equipe está procurando um pacote que desapareceu."))
      return false
    end
    if flags["stone_letter_received"]
      pbMessage(_INTL("Mr. Stone: Entregue a carta a Steven em Dewford quando a travessia estiver aberta."))
      return true
    end
    if GameData::Item.exists?(:LETTER)
      unless $bag && $bag.add(:LETTER, 1)
        pbMessage(_INTL("Mr. Stone: Libere espaço na Bolsa para receber minha carta."))
        return false
      end
    else
      flags["stone_letter_virtual"] = true
      pbMessage(_INTL("Esta instalação não tem o item Carta; registrei a entrega futura no diário regional."))
    end
    flags["stone_letter_received"] = true
    pbMessage(_INTL("Mr. Stone: Leve esta carta a Steven em Dewford. Briney poderá ajudar na próxima etapa."))
    true
  end

  def self.tunnelers
    return false unless state
    pbMessage(_INTL("Escavador: O túnel para Verdanturf ainda não está concluído."))
    true
  end

  def self.rusturf_east_gate
    return false unless state
    pbMessage(_INTL("A saída leste de Rusturf Tunnel será liberada quando Verdanturf for integrada."))
    false
  end



  # Stage 05: storyline is persisted ONLY in blue_regions["hoenn_pilot"].
  # Brawly awards the existing KNUCKLE milestone; never a native Blue badge.
  STAGE5_SIGNS = {
    DEWFORD_GYM: "Ginásio de Dewford. Brawly utiliza Pokémon Lutadores.",
    DEWFORD_TOWN: "Dewford: uma ilha tranquila ao lado de Granite Cave.",
    BRAWLY_GYM: "Knuckle Badge: permite usar Flash em Hoenn.",
    SLATEPORT_CITY: "Slateport: cidade portuária e centro de pesquisa marinha.",
    SLATEPORT_SHIPYARD: "Estaleiro Stern: converse com a equipe para localizar o capitão.",
    SLATEPORT_HARBOR: "Porto de Slateport. Mais viagens estão em preparação.",
    POKEMON_FAN_CLUB: "Clube dos Fãs: troque histórias com treinadores.",
    SLATEPORT_MART: "Poké Mart de Slateport.",
    OCEANIC_MUSEUM: "Museu Oceânico: pesquisas sobre a vida marinha.",
    GRANITE_CAVE: "Granite Cave: cuidado com os túneis e as escadas.",
    SEASIDE_HOUSE: "Casa da Praia, na Rota 109."
  }.freeze

  def self.sign_stage5(key)
    return false unless state && STAGE5_SIGNS.key?(key)
    pbMessage(_INTL(STAGE5_SIGNS.fetch(key)))
    true
  end

  def self.knuckle_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN").include?("KNUCKLE")
  end

  # A verified item is preferable to guessing a TM index that may be
  # reassigned by Decades. Keep pending rewards until the real move is found.
  def self.give_move_tm(flag, move, candidates, message)
    flags = state
    return false unless flags && !flags[flag]
    item = candidates.find do |candidate|
      GameData::Item.exists?(candidate) &&
        GameData::Item.get(candidate).respond_to?(:move) &&
        GameData::Item.get(candidate).move == move
    end
    unless item
      pbMessage(_INTL("Recompensa pendente: a TM deste movimento ainda não está cadastrada."))
      return false
    end
    unless $bag && $bag.add(item, 1)
      pbMessage(_INTL("Libere espaço na Bolsa para receber a TM."))
      return false
    end
    flags[flag] = true
    pbMessage(_INTL(message))
    true
  end

  def self.brawly
    flags = state
    return false unless flags && $player && !$player.party.empty?
    return give_move_tm("brawly_tm_given", :BULKUP, [:TM08, :TM064, :TM0640],
                        "Brawly: receba Bulk Up!") if knuckle_badge?
    unless stone_badge? && flags["peecko_rescued"]
      pbMessage(_INTL("Brawly: só aceitarei o desafio após sua primeira insígnia e o resgate de Peecko."))
      return false
    end
    pbMessage(_INTL("Brawly: mostrarei a força dos Pokémon Lutadores!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_BRAWLY, "Brawly", 531)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions, "HOENN", "KNUCKLE")
      pbMessage(_INTL("Brawly: erro ao registrar a Knuckle Badge regional."))
      return false
    end
    flags["brawly_defeated"] = true
    pbMessage(_INTL("Você conquistou a Knuckle Badge de Hoenn! Flash está liberado nesta região."))
    give_move_tm("brawly_tm_given", :BULKUP, [:TM08, :TM064, :TM0640],
                 "Brawly: receba Bulk Up!")
    true
  end

  def self.flash_hiker
    flags = state
    return false unless flags
    if flags["hm_flash_received"]
      pbMessage(_INTL("Montanhista: com a Knuckle Badge você pode usar Flash em Hoenn."))
      return false
    end
    hm = [:HM05, :HMFLASH].find { |item| GameData::Item.exists?(item) }
    unless hm
      pbMessage(_INTL("O HM Flash não está cadastrado nesta instalação do Blue."))
      return false
    end
    unless $bag && $bag.add(hm, 1)
      pbMessage(_INTL("Montanhista: deixe espaço na Bolsa para receber HM Flash."))
      return false
    end
    flags["hm_flash_received"] = true
    pbMessage(_INTL("Você recebeu HM Flash! A Knuckle Badge libera seu uso em Hoenn."))
    true
  end

  def self.steven_letter
    flags = state
    return false unless flags
    unless flags["stone_letter_received"]
      pbMessage(_INTL("Steven: Mr. Stone ainda não lhe entregou nenhuma carta."))
      return false
    end
    unless flags["steven_letter_delivered"]
      if GameData::Item.exists?(:LETTER) && !flags["stone_letter_virtual"]
        unless $bag && $bag.has?(:LETTER) && $bag.remove(:LETTER, 1)
          pbMessage(_INTL("Steven: a carta não está na sua Bolsa."))
          return false
        end
      end
      flags["steven_letter_delivered"] = true
      pbMessage(_INTL("Steven: agradeço pela carta de meu pai. Boa sorte em Hoenn!"))
    end
    return false if flags["steven_tm_given"]
    give_move_tm("steven_tm_given", :STEELWING, [:TM47, :TM051],
                 "Steven: aceite a TM Steel Wing como agradecimento!")
  end

  def self.boat_to(source_id)
    flags = state
    return false unless flags
    return false unless [105, 28, 111].include?(source_id)
    unless defined?(BlueRegionTravel) && BlueRegionTravel.respond_to?(:move_to) &&
           defined?($game_temp) && $game_temp && defined?($scene) && $scene &&
           defined?($game_map) && $game_map && !$game_temp.in_battle
      pbMessage(_INTL("O barco ainda não está disponível neste ambiente do jogo."))
      return false
    end
    _, mapped = metadata
    positions = {105 => [11, 6, 2], 28 => [12, 10, 2], 111 => [21, 23, 2]}
    map_id = mapped[source_id]
    return false unless map_id
    to = [map_id, *positions.fetch(source_id)]
    previous = [$game_map.map_id, $game_player.x, $game_player.y, $game_player.direction]
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(to) }
      true
    rescue StandardError => error
      begin
        pbFadeOutIn { BlueRegionTravel.move_to(previous) } if $game_map.map_id != previous[0]
      rescue StandardError
        # Leave the original error visible; NEVER mutate regional flags here.
      end
      pbMessage(_INTL("A travessia não pôde ser concluída: {1}", error.message))
      false
    end
  end

  def self.dewford_boat
    flags = state
    return false unless flags && flags["peecko_rescued"]
    if knuckle_badge? && flags["steven_letter_delivered"] &&
       pbConfirmMessage(_INTL("Mr. Briney: seguir para a praia de Slateport agora?"))
      return boat_to(111)
    end
    return false unless pbConfirmMessage(_INTL("Mr. Briney: voltar à minha casa na Rota 104?"))
    boat_to(105)
  end

  def self.slateport_boat
    return false unless state && $PokemonGlobal.blue_regions["hoenn_pilot"]["steven_letter_delivered"]
    return false unless pbConfirmMessage(_INTL("Mr. Briney: viajar de volta para Dewford?"))
    boat_to(28)
  end

  def self.shipyard
    flags = state
    return false unless flags
    unless flags["devon_goods_delivered"] && flags["stone_letter_received"]
      pbMessage(_INTL("Estaleiro: os pesquisadores aguardam uma entrega da Devon de Rustboro."))
      return false
    end
    if flags["stern_package_delivered"]
      pbMessage(_INTL("Estaleiro: agradecemos por proteger os produtos da Devon!"))
      return true
    end
    flags["stern_delivery_ready"] = true
    pbMessage(_INTL("Estaleiro: o capitão Stern está no Museu Oceânico. O pacote da Devon deve ser entregue a ele."))
    true
  end

  def self.museum_entry
    flags = state
    return false unless flags
    return true if flags["museum_fee_paid"]
    if !$player || !$player.respond_to?(:money) || $player.money < 50
      pbMessage(_INTL("Museu Oceânico: a entrada custa ₽50. Dinheiro insuficiente."))
      $game_player.moveto($game_player.x, 10) if $game_player
      return false
    end
    unless pbConfirmMessage(_INTL("Museu Oceânico: pagar ₽50 pela entrada?"))
      $game_player.moveto($game_player.x, 10) if $game_player
      return false
    end
    $player.money -= 50
    flags["museum_fee_paid"] = true
    pbMessage(_INTL("Bilhete do Museu Oceânico registrado."))
    true
  end

  def self.museum_aqua(index)
    flags = state
    return false unless flags && [1, 2].include?(index)
    key = "museum_aqua_#{index}_defeated"
    return true if flags[key]
    unless flags["stern_delivery_ready"] && flags["museum_fee_paid"]
      pbMessage(_INTL("Recruta Aqua: ainda não é hora de batalhar."))
      return false
    end
    version = index == 1 ? 539 : 540
    pbMessage(_INTL("Recruta Aqua: os produtos da Devon agora pertencem à nossa equipe!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_AQUA, "Recruta", version)
      $player.heal_party if $player && $player.respond_to?(:heal_party)
      return false
    end
    flags[key] = true
    pbMessage(_INTL("O recruta Aqua foi derrotado."))
    true
  end

  def self.stern
    flags = state
    return false unless flags
    unless flags["stern_delivery_ready"] && flags["museum_fee_paid"]
      pbMessage(_INTL("Capitão Stern: você veio do estaleiro com a encomenda da Devon?"))
      return false
    end
    unless flags["museum_aqua_1_defeated"] && flags["museum_aqua_2_defeated"]
      pbMessage(_INTL("Stern: dois membros da Equipe Aqua estão ameaçando minha pesquisa. Enfrente-os!"))
      return false
    end
    if flags["stern_package_delivered"]
      pbMessage(_INTL("Capitão Stern: os produtos da Devon estão seguros. Obrigado!"))
      return true
    end
    flags["stern_package_delivered"] = true
    pbMessage(_INTL("Capitão Stern: obrigado! A encomenda da Devon chegou em segurança."))
    true
  end

  def self.slateport_north_gate
    return false unless state
    pbMessage(_INTL("A Rota 110 será liberada numa fase posterior. Volte para o sul de Slateport."))
    $game_player.moveto($game_player.x, 2) if $game_player && $game_player.y == 1
    false
  end

  def self.soothe_bell
    flags = state
    return false unless flags
    return false if flags["soothe_bell_given"]
    unless GameData::Item.exists?(:SOOTHEBELL) && $bag && $bag.add(:SOOTHEBELL, 1)
      pbMessage(_INTL("Clube Pokémon: abra espaço na Bolsa para receber Soothe Bell."))
      return false
    end
    flags["soothe_bell_given"] = true
    pbMessage(_INTL("Você recebeu Soothe Bell!"))
    true
  end

  def self.soft_sand
    flags = state
    return false unless flags
    return false if flags["soft_sand_given"]
    unless GameData::Item.exists?(:SOFTSAND) && $bag && $bag.add(:SOFTSAND, 1)
      pbMessage(_INTL("Praia: deixe espaço para receber Soft Sand."))
      return false
    end
    flags["soft_sand_given"] = true
    pbMessage(_INTL("Você recebeu Soft Sand!"))
    true
  end


  def self.heal
    return unless state
    if $player.party.empty?
      pbMessage(_INTL("Enfermeira: Traga seus Pokémon quando precisar de atendimento."))
      return
    end
    # Also register Oldale as the respawn Pokémon Center, not only heal HP.
    pbSetPokemonCenter
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
