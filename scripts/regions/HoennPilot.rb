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
    stage6 = (stage5 + [41, 42, 43, 44, 45, 46, 47, 113, 114, 115]).sort
    stage7 = (stage6 + [53,54,55,56,57,58,59,60,61,62,63,117,118,120,121,122,123,
                        124,125,126,128,177,178,179,180,191,192]).sort
    stage8 = (stage7 + [48,49,50,51,52,64,65,66,67,68,69,70,71,72,73,74,75,
                        132,133,134,135,136,137,138,139]).sort
    stage9 = (stage8 + [76,77,78,79,80,81,82,141,144,
                        182,183,184,185,186,187,188,189,
                        206,207,208,209,210,211,212,213,215,216,217]).sort
    stage10 = (stage9 + (83..100).to_a + (146..155).to_a +
               (227..236).to_a + (238..248).to_a + (250..252).to_a +
               [255,258,259,260,261,262,263,266,322]).sort
    stage2 = [7, 8, 11, 12, 13, 14, 101, 102, 103]
    raise "Mapas do piloto de Hoenn inválidos." unless [stage2, stage3, stage4, stage5, stage6, stage7, stage8, stage9, stage10].include?(maps.keys.sort) &&
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
    if maps[113] && maps[41] && maps[47]
      route110 = GameData::Encounter.get(maps.fetch(113), 0)
      species = [:ELECTRIKE, :POOCHYENA, :GULPIN, :ODDISH, :WINGULL,
                 :PLUSLE, :MINUN]
      unless route110 && route110.types.fetch(:Land, []).map { |slot| slot[1] }.sort == species.sort
        raise "Tabela de encontros da Rota 110 não compilada"
      end
      expected = [
        [:BLUE_HOENN_WATTSON, "Wattson", 647],
        [:BLUE_HOENN_WALLY, "Wally", 641],
        [:YOUNGSTER, "Edward", 113], [:RICHBOY, "Edwin", 113],
        [:YOUNGSTER, "Joseph", 113], [:YOUNGSTER, "Timmy", 113],
        [:LASS, "Jaclyn", 113], [:FISHERMAN, "Dale", 113],
        [:YOUNGSTER, "Kaleb", 113], [:LASS, "Isabel", 113],
        [:YOUNGSTER, "Anthony", 114], [:LASS, "Abigail", 114],
        [:YOUNGSTER, "Benjamin", 114], [:LASS, "Jasmine", 114],
        [:YOUNGSTER, "Jacob", 114], [:LASS, "Alyssa", 114],
        [:LASS, "Vivian", 47], [:YOUNGSTER, "Kirk", 47],
        [:YOUNGSTER, "Ben", 47], [:BUGCATCHER, "Angelo", 47],
        [:YOUNGSTER, "Shawn", 47]
      ]
      unless expected.all? { |kind, name, ver| GameData::Trainer.exists?(kind, name, ver) }
        raise "Treinadores/Wattson/Wally da Etapa 6 não compilados"
      end
      ["May", "Brendan"].each do |name|
        [610, 611, 612].each do |ver|
          raise "Rival da Rota 110 não compilado: #{name}/#{ver}" unless GameData::Trainer.exists?(:RIVAL1, name, ver)
        end
      end
    end
    if maps[53] && maps[58] && maps[178]
      {
        117 => [:SANDSHREW,:TRAPINCH,:BALTOY,:CACNEA],
        121 => [:NUMEL,:MARILL],
        123 => [:SPINDA,:SLUGMA,:SKARMORY],
        125 => [:SWABLU,:LOTAD,:SEEDOT,:LOMBRE,:NUZLEAF,
                :SEVIPER,:ZANGOOSE,:SURSKIT],
        180 => [:NUMEL,:MACHOP,:SPOINK,:COMBUSKEN]
      }.each do |source_id, species|
        table = GameData::Encounter.get(maps.fetch(source_id),0)
        unless table && table.types.fetch(:Land,[]).map{|row|row[1]}.sort == species.sort
          raise "Encontros da Etapa 7 não compilados: #{source_id}"
        end
      end
      {
        177 => [:NUMEL,:GRIMER,:KOFFING,:MACHOP,:SLUGMA,:TORKOAL],
        191 => [:ZUBAT,:LUNATONE,:SOLROCK],
        192 => [:GOLBAT,:LUNATONE,:SOLROCK]
      }.each do |source_id,species|
        table=GameData::Encounter.get(maps.fetch(source_id),0)
        unless table && table.types.fetch(:Cave,[]).map{|row|row[1]}.sort == species.sort
          raise "Encontros Cave da Etapa 7 não compilados: #{source_id}"
        end
      end
      bosses=[
        [:BLUE_HOENN_FLANNERY,"Flannery",763],
        [:BLUE_HOENN_TABITHA,"Tabitha",778],
        [:BLUE_HOENN_MAXIE,"Maxie",779],
        [:BLUE_HOENN_MAGMA,"Recruta",780],
        [:BLUE_HOENN_MAGMA,"Recruta",781]
      ]
      unless bosses.all?{|kind,name,version|GameData::Trainer.exists?(kind,name,version)}
        raise "Chefe/treinadores Magma da Etapa 7 não compilados"
      end
    end
    if maps[64] && maps[69] && maps[137]
      {
        132=>[:ODDISH,:POOCHYENA,:MARILL,:ROSELIA,:ILLUMISE,:VOLBEAT,:SEEDOT,:SURSKIT],
        134=>[:ELECTRIKE,:ZIGZAGOON,:WINGULL,:LINOONE,:MANECTRIC,:KECLEON],
        135=>[:LINOONE,:ODDISH,:ZIGZAGOON,:TROPIUS,:KECLEON,:GROVYLE],
        138=>[:ODDISH,:MARILL,:MIGHTYENA,:POOCHYENA,:ABSOL,:KECLEON,:SEEDOT,:SURSKIT],
        139=>[:SHUPPET,:DUSKULL,:MIGHTYENA,:POOCHYENA,:ODDISH,:GLOOM,:WINGULL,:KECLEON]
      }.each do |source_id,species|
        table=GameData::Encounter.get(maps.fetch(source_id),0)
        unless table && table.types.fetch(:Land,[]).map{|row|row[1]}.sort==species.sort
          raise "Encontros Stage8 não compilados: #{source_id}"
        end
      end
      bosses=[
        [:BLUE_HOENN_NORMAN,"Norman",820],
        [:BLUE_HOENN_WINONA,"Winona",868],
        [:BLUE_HOENN_SHELLY,"Shelly",837]
      ]
      grunts=[851,852,853,854].map{|ver|[:BLUE_HOENN_AQUA,"Recruta",ver]}
      unless (bosses+grunts).all?{|kind,name,ver| GameData::Trainer.exists?(kind,name,ver)}
        raise "Norman/Winona/Shelly/Aqua do Weather Institute não compilados"
      end
      ["May","Brendan"].each do |name|
        [819,820,821,822,823,824].each do |ver|
          raise "Rival de Route119/Lilycove não compilado: #{name}/#{ver}" unless GameData::Trainer.exists?(:RIVAL1,name,ver)
        end
      end
    end
    if maps[76] && maps[82] && maps[215]
      boss_rows=[
        [:BLUE_HOENN_TATE_LIZA,"Tate & Liza",982],
        [:BLUE_HOENN_MATT,"Matt",917],
        [:BLUE_HOENN_TABITHA,"Tabitha",988],
        [:BLUE_HOENN_MAXIE,"Maxie",989],
        [:BLUE_HOENN_MAXIE,"Maxie",992],
        [:BLUE_HOENN_TABITHA,"Tabitha",993]
      ]
      grunts=([920,921,922,923,950,951,952,953,954].map{|ver|[:BLUE_HOENN_AQUA,"Recruta",ver]}+
              [940,941,942,943,944,945,946,991,994].map{|ver|[:BLUE_HOENN_MAGMA,"Recruta",ver]})
      raise "Chefe ou recruta Stage9 não compilado" unless (boss_rows+grunts).all? do |kind,name,version|
        GameData::Trainer.exists?(kind,name,version)
      end
      %w[Maura Nate Preston Hannah Virgil Macey Blake Samantha Mark Leah
         Zander William Gabrielle Kayla Tasha Atsushi Cedric Valerie].each do |name|
        source_map=%w[Maura Nate Preston Hannah Virgil Macey Blake Samantha].include?(name) ? 82 :
                   %w[Mark Leah Zander].include?(name) ? 207 :
                   %w[William Gabrielle Kayla].include?(name) ? 208 :
                   name=="Tasha" ? 209 : name=="Atsushi" ? 210 : 211
        # The Python stage9 audit is authoritative for actual Blue type aliases.
        unless [:YOUNGSTER,:LASS].any?{|kind|GameData::Trainer.exists?(kind,name,source_map)}
          raise "Trainer Stage9 não compilado: #{name}/#{source_map}"
        end
      end
    end
    if maps[83] && maps[87] && maps[93]
      rows = [
        [:BLUE_HOENN_JUAN,"Juan",1087],
        [:BLUE_HOENN_ARCHIE,"Archie",1026],
        [:BLUE_HOENN_WALLY,"Wally",1025],
        [:BLUE_HOENN_ELITE,"Sidney",1094],
        [:BLUE_HOENN_ELITE,"Phoebe",1095],
        [:BLUE_HOENN_ELITE,"Glacia",1096],
        [:BLUE_HOENN_ELITE,"Drake",1097],
        [:BLUE_HOENN_CHAMPION,"Wallace",1098]
      ]
      raise "Chefes ou campeao Stage10 nao compilados" unless rows.all? do |kind,name,version|
        GameData::Trainer.exists?(kind,name,version)
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
    if maps[41] && maps[113]
      links.concat([[maps.fetch(32), maps.fetch(113)], [maps.fetch(113), maps.fetch(41)]])
    end
    if maps[53] && maps[58] && maps[178]
      links.concat([[maps.fetch(41),maps.fetch(117)],
                    [maps.fetch(117),maps.fetch(121)],
                    [maps.fetch(123),maps.fetch(117)],
                    [maps.fetch(123),maps.fetch(53)],
                    [maps.fetch(125),maps.fetch(53)],
                    [maps.fetch(121),maps.fetch(58)],
                    [maps.fetch(123),maps.fetch(121)]])
    end
    if maps[64] && maps[69] && maps[137]
      links.concat([[maps.fetch(41),maps.fetch(132)],
                    [maps.fetch(132),maps.fetch(48)],
                    [maps.fetch(41),maps.fetch(134)],
                    [maps.fetch(134),maps.fetch(135)],
                    [maps.fetch(135),maps.fetch(64)],
                    [maps.fetch(64),maps.fetch(138)],
                    [maps.fetch(138),maps.fetch(139)],
                    [maps.fetch(139),maps.fetch(69)]])
    end
    if maps[76] && maps[141] && maps[144]
      links.concat([[maps.fetch(139),maps.fetch(141)],
                    [maps.fetch(69),maps.fetch(144)],
                    [maps.fetch(144),maps.fetch(76)]])
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
    if balance_badge?
      return surf_from_wally_family unless flags["hm_surf_received"]
      pbMessage(_INTL("Família de Wally: Surf já foi entregue. Boa sorte em Hoenn!"))
      return true
    end
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
    pbMessage(heat_badge? ? _INTL("Norman: você está pronto para o desafio da Balance Badge. Venha ao fundo do ginásio!") :
      _INTL("Norman: Volte quando tiver quatro insígnias de Hoenn. Então batalharemos!"))
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

  # QA07: the standalone Hoenn gym events call this map-scoped dispatcher.
  # TrainerBattle.start remains inside the original leader methods; the
  # existing Blue/Decades scaling, local badges and deferred rewards are kept.
  # Other scripts cannot invoke an arbitrary method via the event parameter.
  HOENN_QA7_GYMS = {
    STONE:   [27, :roxanne],
    KNUCKLE: [31, :brawly],
    DYNAMO:  [47, :wattson],
    HEAT:    [63, :flannery],
    BALANCE: [20, :norman],
    FEATHER: [68, :winona],
    MIND:    [82, :tate_liza],
    RAIN:    [87, :juan]
  }.freeze

  def self.qa7_gym_battle(badge)
    flags = state
    config = HOENN_QA7_GYMS[badge]
    return false unless flags && config && $game_map
    _, maps = metadata
    return false unless maps[config[0]] && $game_map.map_id == maps[config[0]]
    send(config[1])
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
    flags = state
    return false unless flags
    unless flags["rusturf_aqua_defeated"] && dynamo_badge?
      pbMessage(_INTL("Escavador: primeiro ajude em Rusturf Tunnel e conquiste a Dynamo Badge."))
      return false
    end
    return field_hm_reward(:STRENGTH, [:HM04, :HMSTRENGTH],
                           "hm_strength_received",
                           "Escavador: receba Strength! A Heat Badge permite mover pedras em Hoenn.")
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
    if flags[key]
      pbMessage(_INTL("Recruta Aqua: você já me venceu. Estou recuando!"))
      return false
    end
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
      if flags["groudon_awakened"] && !flags["slateport_submarine_stolen"]
        return slateport_submarine_news
      end
      pbMessage(_INTL("Capitão Stern: os produtos da Devon estão seguros. Obrigado!"))
      return true
    end
    flags["stern_package_delivered"] = true
    pbMessage(_INTL("Capitão Stern: obrigado! A encomenda da Devon chegou em segurança."))
    true
  end

  def self.slateport_north_gate
    flags = state
    return false unless flags
    return true if flags["stern_package_delivered"]
    pbMessage(_INTL("Antes de ir à Rota 110, conclua a entrega ao Capitão Stern."))
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



  # Hoenn Stage 06 — events are guarded by BlueHoennPilot.state; no Decades,
  # Kanto, Johto or Sinnoh save data or native badge fields are mutated.
  STAGE6_SIGNS = {
    MAUVILLE: "Mauville: cidade dos encontros e da eletricidade.",
    MAUVILLE_GYM: "Ginásio de Mauville. Líder Wattson, tipo Elétrico.",
    RYDEL: "Rydel's Cycles: Mach Bike e Acro Bike disponíveis.",
    CYCLING_SIGN: "Cycling Road: é obrigatório ter uma bicicleta.",
    CYCLING_NORTH_SIGN: "Cycling Road. Portaria norte.",
    TRICK_HOUSE: "Trick House: conteúdo em preparação.",
    SLATEPORT_DIRECTION: "Slateport fica ao sul.",
    MAUVILLE_DIRECTION: "Mauville fica ao norte."
  }.freeze

  def self.sign_stage6(key)
    return false unless state && STAGE6_SIGNS.key?(key)
    pbMessage(_INTL(STAGE6_SIGNS.fetch(key)))
    true
  end

  def self.dynamo_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN").include?("DYNAMO")
  end

  def self.rival_110_itemfinder
    flags = state
    return false unless flags && flags["rival_110_done"] && !flags["rival_110_itemfinder"]
    unless GameData::Item.exists?(:ITEMFINDER) && $bag && $bag.add(:ITEMFINDER, 1)
      pbMessage(_INTL("O Itemfinder está reservado. Abra espaço na Bolsa e converse novamente com o rival."))
      return false
    end
    flags["rival_110_itemfinder"] = true
    pbMessage(_INTL("Você recebeu o Itemfinder do rival!"))
    true
  end

  RIVAL_110_VERSIONS = { TREECKO: 610, TORCHIC: 611, MUDKIP: 612 }.freeze

  def self.rival_110
    flags = state
    return false unless flags && starter && $player && !$player.party.empty?
    unless flags["stern_package_delivered"]
      pbMessage(_INTL("Seu rival está mais ao norte. Primeiro conclua a entrega a Stern."))
      return false
    end
    return rival_110_itemfinder if flags["rival_110_done"]
    name = rival_name
    version = RIVAL_110_VERSIONS.fetch(starter)
    pbMessage(_INTL("{1}: vamos testar o quanto sua equipe cresceu!", name))
    setBattleRule("canLose")
    unless TrainerBattle.start(:RIVAL1, name, version)
      $player.heal_party if $player.respond_to?(:heal_party)
      pbMessage(_INTL("{1}: treine mais e depois me desafie!", name))
      return false
    end
    flags["rival_110_done"] = true
    pbMessage(_INTL("{1}: você está cada vez mais forte. Siga até Mauville!", name))
    rival_110_itemfinder
    true
  end

  def self.wally_mauville
    flags = state
    return false unless flags && $player && !$player.party.empty?
    unless flags["rival_110_done"] && flags["wally_captured"]
      pbMessage(_INTL("Wally: vou praticar minhas batalhas e esperar você se preparar."))
      return false
    end
    if flags["wally_mauville_done"]
      pbMessage(_INTL("Wally: vou continuar treinando para ficar mais forte!"))
      return false
    end
    pbMessage(_INTL("Wally: Ralts e eu queremos desafiá-lo antes de você entrar no ginásio!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_WALLY, "Wally", 641)
      $player.heal_party if $player.respond_to?(:heal_party)
      pbMessage(_INTL("Wally: está bem, podemos tentar de novo depois!"))
      return false
    end
    flags["wally_mauville_done"] = true
    pbMessage(_INTL("Wally: você venceu! Vou continuar meu treinamento com meu tio."))
    true
  end

  def self.wally_uncle_mauville
    flags = state
    return false unless flags
    pbMessage(flags["wally_mauville_done"] ?
      _INTL("Tio de Wally: obrigado por estimular o treinamento dele!") :
      _INTL("Tio de Wally: Wally quer testar a própria força. Converse com ele!"))
    true
  end

  def self.wattson_tm
    flags = state
    return false unless flags && dynamo_badge?
    return false if flags["wattson_tm_given"]
    give_move_tm("wattson_tm_given", :SHOCKWAVE, [:TM34, :TM039],
                 "Wattson: receba a TM Shock Wave!")
  end

  def self.wattson
    flags = state
    return false unless flags && $player && !$player.party.empty?
    return wattson_tm if dynamo_badge?
    unless knuckle_badge? && flags["stern_package_delivered"] &&
           flags["rival_110_done"] && flags["wally_mauville_done"]
      pbMessage(_INTL("Wattson: conclua Slateport, a Rota 110 e a batalha de Wally antes do desafio."))
      return false
    end
    pbMessage(_INTL("Wattson: hahaha! Mostre a energia dos seus Pokémon!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_WATTSON, "Wattson", 647)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions, "HOENN", "DYNAMO")
      pbMessage(_INTL("Wattson: não foi possível registrar a Dynamo Badge."))
      return false
    end
    flags["wattson_defeated"] = true
    pbMessage(_INTL("Você conquistou a Dynamo Badge de Hoenn! Rock Smash fica autorizado nesta região."))
    wattson_tm
    true
  end

  def self.rock_smash_teacher
    flags = state
    return false unless flags
    return false if flags["rock_smash_given"]
    item = [:HM06, :TM94].find do |candidate|
      GameData::Item.exists?(candidate) &&
        GameData::Item.get(candidate).respond_to?(:move) &&
        GameData::Item.get(candidate).move == :ROCKSMASH
    end
    unless item && $bag && $bag.add(item, 1)
      pbMessage(_INTL("Morador: a técnica Rock Smash precisa estar disponível e caber na Bolsa."))
      return false
    end
    flags["rock_smash_given"] = true
    pbMessage(_INTL("Você recebeu Rock Smash! A Dynamo Badge autoriza seu uso em Hoenn."))
    true
  end

  def self.rydel_bikes
    flags = state
    return false unless flags && $bag
    candidates = [:MACHBIKE, :ACROBIKE]
    unless candidates.all? { |item| GameData::Item.exists?(item) }
      pbMessage(_INTL("Rydel: faltam os itens Mach Bike ou Acro Bike nesta instalação."))
      return false
    end
    choice = pbMessage(_INTL("Rydel: qual bicicleta deseja usar?"),
                       [_INTL("Mach Bike"), _INTL("Acro Bike"), _INTL("Cancelar")], -1)
    return false unless [0, 1].include?(choice)
    wanted = candidates[choice]
    if $bag.has?(wanted)
      pbMessage(_INTL("Rydel: você já possui essa bicicleta."))
      return false
    end
    old = candidates.find { |item| item != wanted && $bag.has?(item) }
    unless $bag.add(wanted, 1)
      pbMessage(_INTL("Rydel: abra espaço na Bolsa antes de receber a bicicleta."))
      return false
    end
    if old && !$bag.remove(old, 1)
      $bag.remove(wanted, 1)
      pbMessage(_INTL("Rydel: não foi possível trocar. Sua bicicleta anterior foi mantida."))
      return false
    end
    flags["bike_chosen"] = wanted.to_s
    pbMessage(_INTL("Rydel: você recebeu a {1}! Pode trocar comigo sempre que quiser.",
                     wanted == :MACHBIKE ? "Mach Bike" : "Acro Bike"))
    true
  end

  def self.has_hoenn_bike?
    flags = state
    flags && $bag && ([:MACHBIKE, :ACROBIKE].any? { |item|
      GameData::Item.exists?(item) && $bag.has?(item) })
  end

  def self.cycling_gate(dest_source, x, y)
    flags = state
    return false unless flags
    allowed = [[114, 18, 16], [114, 19, 88], [115, 14, 7], [115, 14, 21]]
    return false unless allowed.include?([dest_source, x, y])
    # Players may ALWAYS leave the cycling route, even if they discarded
    # their bicycle during a legacy save migration.
    unless dest_source == 115 || has_hoenn_bike?
      pbMessage(_INTL("Portaria: você precisa da Mach Bike ou da Acro Bike para entrar."))
      return false
    end
    unless defined?(BlueRegionTravel) && BlueRegionTravel.respond_to?(:move_to) &&
           defined?($game_temp) && $game_temp && defined?($scene) && $scene &&
           defined?($game_player) && $game_player && defined?($game_map) && $game_map
      pbMessage(_INTL("A Cycling Road exige uma transferência segura do jogo."))
      return false
    end
    _, maps = metadata
    dest_id = maps[dest_source]
    return false unless dest_id && !$game_temp.in_battle
    before = [$game_map.map_id, $game_player.x, $game_player.y, $game_player.direction]
    begin
      pbFadeOutIn { BlueRegionTravel.move_to([dest_id, x, y, 2]) }
      flags["cycling_road_visited"] = true if dest_source == 114
      true
    rescue StandardError => error
      begin
        pbFadeOutIn { BlueRegionTravel.move_to(before) } if $game_map.map_id != before[0]
      rescue StandardError
        # Fail safely; do not mark any travel/badge flags on a failed move.
      end
      pbMessage(_INTL("Portaria: viagem cancelada ({1}).", error.message))
      false
    end
  end

  def self.wattson_gate
    return false unless state
    pbMessage(_INTL("Uma barreira elétrica bloqueia o caminho. Procure os interruptores."))
    false
  end

  def self.wattson_switch(blue_ids, pink_ids)
    flags = state
    return false unless flags && $game_map && $game_self_switches &&
                        blue_ids.is_a?(Array) && pink_ids.is_a?(Array)
    _, maps = metadata
    return false unless $game_map.map_id == maps[47]
    flags["wattson_switch_blue_open"] = !flags["wattson_switch_blue_open"]
    blue_open = flags["wattson_switch_blue_open"]
    {blue_ids => blue_open, pink_ids => !blue_open}.each do |ids, open|
      ids.each do |id|
        next unless id.is_a?(Integer) && $game_map.events[id]
        $game_self_switches[[$game_map.map_id, id, "A"]] = open
        $game_map.events[id].refresh
      end
    end
    pbMessage(blue_open ?
      _INTL("O circuito azul foi desativado e o rosa ficou energizado!") :
      _INTL("O circuito rosa foi desativado e o azul ficou energizado!"))
    true
  end

  def self.mauville_future_gate
    return false unless state
    pbMessage(_INTL("Essa saída de Mauville será liberada ao adicionar as próximas rotas de Hoenn."))
    if $game_player
      $game_player.moveto(38, $game_player.y) if $game_player.x == 39
      $game_player.moveto($game_player.x, 1) if $game_player.y == 0
    end
    false
  end



  # Stage 07 — all story flags remain local to the Hoenn pilot, never to
  # $player.badges or an existing Decades/Kanto/Johto/other region save.
  STAGE7_SIGNS = {
    FALLARBOR: "Fallarbor: cidade tranquila entre cinzas vulcânicas.",
    LAVARIDGE: "Lavaridge: fontes termais aquecidas pelo vulcão.",
    LAVARIDGE_GYM: "Ginásio de Flannery: Pokémon do tipo Fogo.",
    ROUTE111: "Rota 111: cuidado com as pedras e a passagem do deserto.",
    MT_CHIMNEY: "Mt. Chimney: o teleférico leva ao topo do vulcão.",
    FALLARBOR_SIGN: "Rota 113: cinzas vulcânicas e a cidade de Fallarbor.",
    METEOR_FALLS: "Meteor Falls: a Equipe Magma foi avistada na região.",
    JAGGED_PASS: "Jagged Pass: trilha íngreme que leva a Lavaridge."
  }.freeze

  GYM_STEAM_COORDINATES = [
    [12,24],[37,24],[10,15],[35,15],[7,20],[32,20],
    [2,23],[27,23],[3,20],[28,20],[2,16],[27,16],
    [2,12],[27,12],[4,9],[29,9],[9,8],[34,8],
    [14,9],[39,9],[14,18],[39,18]
  ].freeze

  def self.sign_stage7(key)
    return false unless state && STAGE7_SIGNS.key?(key)
    pbMessage(_INTL(STAGE7_SIGNS.fetch(key)))
    true
  end

  def self.heat_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN").include?("HEAT")
  end

  def self.meteor_falls_ambush
    flags=state
    return false unless flags
    unless flags["stern_package_delivered"] && dynamo_badge?
      pbMessage(_INTL("Um pesquisador estuda meteoritos. Continue sua jornada por Mauville."))
      return false
    end
    if flags["meteorite_stolen"]
      pbMessage(_INTL("Professor Cozmo: a Equipe Magma levou o meteorito para Mt. Chimney!"))
      return false
    end
    flags["meteorite_stolen"]=true
    pbMessage(_INTL("Professor Cozmo: os membros da Equipe Magma roubaram um meteorito!"))
    pbMessage(_INTL("Eles seguiram para Mt. Chimney. Volte à estação do teleférico na Rota 112!"))
    true
  end

  def self.magma_blocker(event_id)
    flags=state
    return false unless flags && event_id.is_a?(Integer)
    _, maps=metadata
    return false unless $game_map && $game_map.map_id==maps[121] &&
                        $game_self_switches && $game_map.events[event_id]
    unless flags["meteorite_stolen"]
      pbMessage(_INTL("Recruta Magma: o teleférico está interditado. Não entre!"))
      return false
    end
    flags["magma_blockers_cleared"] ||= []
    unless flags["magma_blockers_cleared"].include?(event_id)
      flags["magma_blockers_cleared"] << event_id
    end
    $game_self_switches[[$game_map.map_id,event_id,"A"]]=true
    $game_map.events[event_id].refresh
    flags["cable_car_unlocked"]=true if flags["magma_blockers_cleared"].size>=2
    pbMessage(flags["cable_car_unlocked"] ?
      _INTL("Os dois recrutas Magma recuaram. O teleférico foi liberado!") :
      _INTL("Um recruta recuou, mas o outro ainda bloqueia o teleférico."))
    true
  end

  def self.cable_car
    flags=state
    return false unless flags && defined?(BlueRegionTravel) &&
                        BlueRegionTravel.respond_to?(:move_to)
    unless defined?($game_map) && $game_map &&
           defined?($game_player) && $game_player &&
           defined?($game_temp) && $game_temp && !$game_temp.in_battle &&
           defined?($scene) && $scene
      pbMessage(_INTL("A viagem de teleférico não está disponível neste ambiente."))
      return false
    end
    _, map_ids=metadata
    from=$game_map.map_id
    lower,upper=map_ids[122],map_ids[179]
    unless [lower,upper].include?(from)
      pbMessage(_INTL("A estação do teleférico não pertence a este mapa."))
      return false
    end
    if from==lower && (!flags["meteorite_stolen"] || !flags["cable_car_unlocked"])
      pbMessage(_INTL("O teleférico está bloqueado. Investigue Meteor Falls e afaste os dois recrutas Magma."))
      return false
    end
    target=from==lower ? [upper,8,9,2] : [lower,8,9,2]
    return false unless target[0]
    return false unless pbConfirmMessage(_INTL("Viajar de teleférico para a outra estação?"))
    prev=[from,$game_player.x,$game_player.y,$game_player.direction]
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(target) }
      flags["mt_chimney_visited"]=true if from==lower
      true
    rescue StandardError => error
      begin
        pbFadeOutIn { BlueRegionTravel.move_to(prev) } if $game_map.map_id!=prev[0]
      rescue StandardError
        # Preserve initial error and never mark the journey complete.
      end
      pbMessage(_INTL("O teleférico não conseguiu concluir a travessia: {1}",error.message))
      false
    end
  end

  def self.magma_grunt(index)
    flags=state
    return false unless flags && [1,2].include?(index) &&
                        $player && !$player.party.empty?
    unless flags["meteorite_stolen"]
      pbMessage(_INTL("O cume de Mt. Chimney está tranquilo por enquanto."))
      return false
    end
    key="magma_grunt_#{index}_defeated"
    if flags[key]
      pbMessage(_INTL("Recruta Magma: não vou enfrentá-lo de novo!"))
      return false
    end
    version=index==1 ? 780 : 781
    pbMessage(_INTL("Recruta Magma: não se meta em nossos planos!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_MAGMA,"Recruta",version)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags[key]=true
    pbMessage(_INTL("O recruta Magma foi derrotado."))
    true
  end

  def self.tabitha
    flags=state
    return false unless flags && $player && !$player.party.empty?
    if flags["tabitha_defeated"]
      pbMessage(_INTL("Tabitha: vou me retirar por enquanto..."))
      return false
    end
    unless flags["meteorite_stolen"] &&
           flags["magma_grunt_1_defeated"] &&
           flags["magma_grunt_2_defeated"]
      pbMessage(_INTL("Tabitha: enfrente nossos recrutas antes de se aproximar de Maxie!"))
      return false
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_TABITHA,"Tabitha",778)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["tabitha_defeated"]=true
    pbMessage(_INTL("Tabitha: você venceu... Mas Maxie não desistirá!"))
    true
  end

  def self.maxie
    flags=state
    return false unless flags && $player && !$player.party.empty?
    if flags["maxie_defeated"]
      pbMessage(_INTL("Maxie: precisamos rever nossos planos."))
      return false
    end
    unless flags["tabitha_defeated"]
      pbMessage(_INTL("Maxie: primeiro enfrente Tabitha."))
      return false
    end
    pbMessage(_INTL("Maxie: a Equipe Magma pretende transformar a terra com este meteorito!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_MAXIE,"Maxie",779)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["maxie_defeated"]=true
    pbMessage(_INTL("Maxie: você foi forte. Recuaremos de Mt. Chimney!"))
    true
  end

  def self.meteorite_machine
    flags=state
    return false unless flags
    unless flags["maxie_defeated"]
      pbMessage(_INTL("A máquina está ligada à Equipe Magma. Afaste Maxie antes de mexer nela."))
      return false
    end
    if flags["meteorite_recovered"]
      pbMessage(_INTL("O meteorito já foi recuperado."))
      return false
    end
    item=:METEORITE_RSE
    if GameData::Item.exists?(item)
      unless $bag && $bag.add(item,1)
        pbMessage(_INTL("Deixe espaço na Bolsa para retirar o meteorito."))
        return false
      end
    else
      flags["meteorite_virtual"]=true
    end
    flags["meteorite_recovered"]=true
    pbMessage(_INTL("Você recuperou o meteorito roubado do Professor Cozmo!"))
    true
  end

  def self.flannery_tm
    flags=state
    return false unless flags && heat_badge?
    return false if flags["flannery_tm_given"]
    give_move_tm("flannery_tm_given",:OVERHEAT,[:TM50,:TM050,:TM107],
                 "Flannery: receba a TM Overheat!")
  end

  def self.flannery
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return flannery_tm if heat_badge?
    unless dynamo_badge? && flags["maxie_defeated"] &&
           flags["meteorite_recovered"]
      pbMessage(_INTL("Flannery: enfrente a Equipe Magma em Mt. Chimney e recupere o meteorito antes de me desafiar."))
      return false
    end
    pbMessage(_INTL("Flannery: sou a líder de Lavaridge! Mostrarei a força do meu time de Fogo!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_FLANNERY,"Flannery",763)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions,"HOENN","HEAT")
      pbMessage(_INTL("Flannery: erro ao registrar a Heat Badge de Hoenn."))
      return false
    end
    flags["flannery_defeated"]=true
    pbMessage(_INTL("Você conquistou a Heat Badge de Hoenn! Strength está autorizado nesta região."))
    flannery_tm
    true
  end

  def self.gym_steam_vent(x,y)
    flags=state
    return false unless flags && defined?($game_map) && $game_map &&
                        defined?($game_player) && $game_player
    _, maps=metadata
    return false unless $game_map.map_id==maps[63] &&
                        GYM_STEAM_COORDINATES.include?([x,y])
    $game_player.moveto(x,y)
    pbMessage(_INTL("Uma corrente de vapor mudou sua posição no ginásio!"))
    true
  end

  def self.glass_workshop
    return false unless state
    pbMessage(_INTL("Artesão: consigo fabricar objetos com cinzas vulcânicas. A coleta de cinzas será integrada em outra etapa."))
    true
  end

  def self.fossil_house
    return false unless state
    pbMessage(_INTL("Fossil Maniac: estudo fósseis. O túnel profundo ainda está bloqueado neste piloto."))
    true
  end

  def self.stage7_future_gate(reason)
    return false unless state
    messages={
      MIRAGE_TOWER:"Mirage Tower será adicionada em uma fase futura.",
      MAGMA_HIDEOUT:"O esconderijo Magma ainda não está disponível.",
      METEOR_DEEP:"Os andares profundos de Meteor Falls ainda não estão preparados.",
      METEOR_ROUTE115:"A saída para Rota 115 ainda está bloqueada neste piloto.",
      FOSSIL_TUNNEL:"O Fossil Maniac ainda está escavando esse túnel."
    }
    return false unless messages.key?(reason)
    pbMessage(_INTL(messages.fetch(reason)))
    false
  end



  # Stage 08 — Norman / HM Surf / Weather Institute / Winona / Lilycove.
  # No event touches the native Blue badges or switches in other regions.
  STAGE8_SIGNS = {
    VERDANTURF: "Verdanturf: uma cidade tranquila próxima a Mauville.",
    FORTREE_GYM: "Ginásio de Fortree: Winona, especialista no tipo Voador.",
    FORTREE: "Fortree: casas construídas nas árvores.",
    LILYCOVE: "Lilycove: uma cidade costeira com lojas e museu.",
    LILYCOVE_STORE: "Department Store de Lilycove: várias seções.",
    WEATHER_INSTITUTE: "Instituto Meteorológico: a Equipe Aqua tomou conta da pesquisa!",
    SAFARI: "Safari Zone: a entrada será liberada em outra etapa."
  }.freeze

  NORMAN_GYM_TARGETS = [
    [9,8],[54,24],[46,8],[46,36],[52,8],[9,20],[43,20],
    [35,40],[29,36],[35,4],[26,24],[52,36],[46,40],[26,20],
    [54,20],[37,24],[29,8],[35,36],[46,4],[3,8],[43,24],
    [35,8],[3,20],[37,20]
  ].freeze

  def self.sign_stage8(key)
    return false unless state && STAGE8_SIGNS.key?(key)
    pbMessage(_INTL(STAGE8_SIGNS.fetch(key)))
    true
  end

  def self.balance_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN").include?("BALANCE")
  end

  def self.feather_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN").include?("FEATHER")
  end

  def self.norman_gym_warp(x,y)
    flags=state
    return false unless flags && NORMAN_GYM_TARGETS.include?([x,y])
    _,map_ids=metadata
    return false unless defined?($game_map) && $game_map &&
                        $game_map.map_id==map_ids[20] &&
                        defined?($game_player) && $game_player
    $game_player.moveto(x,y)
    true
  end

  def self.norman_tm
    flags=state
    return false unless flags && balance_badge?
    return false if flags["norman_tm_given"]
    give_move_tm("norman_tm_given",:FACADE,[:TM42,:TM103],
                 "Norman: receba a TM Facade!")
  end

  def self.norman
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return norman_tm if balance_badge?
    needed=["STONE","KNUCKLE","DYNAMO","HEAT"]
    badges=BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")
    unless needed.all?{|badge|badges.include?(badge)}
      pbMessage(_INTL("Norman: enfrente-me depois das quatro primeiras insígnias de Hoenn!"))
      return false
    end
    pbMessage(_INTL("Norman: mostre a força que desenvolveu durante sua jornada!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_NORMAN,"Norman",820)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions,"HOENN","BALANCE")
      pbMessage(_INTL("Norman: não foi possível registrar a Balance Badge."))
      return false
    end
    flags["norman_defeated"]=true
    pbMessage(_INTL("Você recebeu a Balance Badge de Hoenn! Surf foi liberado nesta região."))
    norman_tm
    true
  end

  def self.surf_from_wally_family
    flags=state
    return false unless flags && balance_badge? && !flags["hm_surf_received"]
    item=[:HM03,:HMSURF].find{|id|
      GameData::Item.exists?(id) &&
      GameData::Item.get(id).respond_to?(:move) &&
      GameData::Item.get(id).move==:SURF
    }
    unless item
      pbMessage(_INTL("Família de Wally: o HM Surf não está cadastrado com o movimento correto neste Blue."))
      return false
    end
    unless $bag && $bag.add(item,1)
      pbMessage(_INTL("Família de Wally: libere espaço na Bolsa para receber Surf."))
      return false
    end
    flags["hm_surf_received"]=true
    pbMessage(_INTL("Você recebeu HM Surf! A Balance Badge permite usá-lo em Hoenn."))
    true
  end

  def self.good_rod_fisherman
    flags=state
    return false unless flags
    if flags["good_rod_received"]
      pbMessage(_INTL("Pescador: continue praticando com sua Good Rod!"))
      return false
    end
    unless GameData::Item.exists?(:GOODROD) && $bag && $bag.add(:GOODROD,1)
      pbMessage(_INTL("Pescador: a Good Rod precisa estar registrada e caber na Bolsa."))
      return false
    end
    flags["good_rod_received"]=true
    pbMessage(_INTL("Você recebeu a Good Rod!"))
    true
  end

  def self.daycare_info
    return false unless state
    pbMessage(_INTL("Day Care de Hoenn: o serviço de criação e ovos ainda está em integração neste piloto."))
    true
  end

  def self.weather_aqua(version)
    flags=state
    return false unless flags && [851,852,853,854].include?(version) &&
                        $player && !$player.party.empty?
    unless balance_badge? && flags["hm_surf_received"]
      pbMessage(_INTL("Recruta Aqua: primeiro vença Norman e obtenha Surf para alcançar a Rota 119."))
      return false
    end
    key="weather_aqua_#{version}_defeated"
    if flags[key]
      pbMessage(_INTL("Recruta Aqua: já fui derrotado, vou recuar!"))
      return false
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_AQUA,"Recruta",version)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags[key]=true
    pbMessage(_INTL("O recruta Aqua foi derrotado."))
    true
  end

  def self.weather_shelly
    flags=state
    return false unless flags && $player && !$player.party.empty?
    if flags["weather_shelly_defeated"]
      pbMessage(_INTL("Shelly: vamos retirar a Equipe Aqua do instituto!"))
      return false
    end
    unless [851,852,853,854].all?{|version|flags["weather_aqua_#{version}_defeated"]}
      pbMessage(_INTL("Shelly: antes de me enfrentar, passe pelos recrutas da Equipe Aqua."))
      return false
    end
    pbMessage(_INTL("Shelly: os dados deste instituto pertencem à Equipe Aqua!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_SHELLY,"Shelly",837)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["weather_shelly_defeated"]=true
    pbMessage(_INTL("Shelly: a Equipe Aqua vai recuar do Instituto Meteorológico!"))
    true
  end

  def self.weather_castform
    flags=state
    return false unless flags
    unless flags["weather_shelly_defeated"]
      pbMessage(_INTL("Pesquisador: a Equipe Aqua ainda está ocupando o instituto!"))
      return false
    end
    if flags["weather_castform_received"]
      pbMessage(_INTL("Pesquisador: cuide bem de Castform!"))
      return false
    end
    unless GameData::Species.exists?(:CASTFORM) && defined?(pbAddPokemon)
      pbMessage(_INTL("Pesquisador: Castform não pode ser entregue nesta instalação."))
      return false
    end
    unless pbAddPokemon(:CASTFORM,25)
      pbMessage(_INTL("Pesquisador: libere espaço para receber Castform."))
      return false
    end
    flags["weather_castform_received"]=true
    pbMessage(_INTL("Você recebeu Castform como agradecimento!"))
    true
  end

  RIVAL_STAGE8_119_VERSIONS={TREECKO:819,TORCHIC:820,MUDKIP:821}.freeze
  RIVAL_STAGE8_LILYCOVE_VERSIONS={TREECKO:822,TORCHIC:823,MUDKIP:824}.freeze

  def self.rival_119_fly
    flags=state
    return false unless flags && flags["rival_119_done"] && !flags["hm_fly_received"]
    item=[:HM02,:HMFLY].find{|id|
      GameData::Item.exists?(id) &&
      GameData::Item.get(id).respond_to?(:move) &&
      GameData::Item.get(id).move==:FLY
    }
    unless item && $bag && $bag.add(item,1)
      pbMessage(_INTL("Rival: o HM Fly precisa estar cadastrado e caber na Bolsa."))
      return false
    end
    flags["hm_fly_received"]=true
    pbMessage(_INTL("Você recebeu HM Fly! A Feather Badge permitirá usá-lo."))
    true
  end

  def self.rival_119
    flags=state
    return false unless flags && starter && $player && !$player.party.empty?
    unless flags["weather_shelly_defeated"]
      pbMessage(_INTL("Seu rival está treinando ao norte. Antes liberte o Weather Institute."))
      return false
    end
    return rival_119_fly if flags["rival_119_done"]
    name=rival_name
    pbMessage(_INTL("{1}: quero testar o quanto seus Pokémon melhoraram!",name))
    setBattleRule("canLose")
    unless TrainerBattle.start(:RIVAL1,name,RIVAL_STAGE8_119_VERSIONS.fetch(starter))
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["rival_119_done"]=true
    pbMessage(_INTL("{1}: foi uma batalha incrível! Você está chegando a Fortree!",name))
    rival_119_fly
    true
  end

  def self.steven_scope
    flags=state
    return false unless flags
    unless flags["rival_119_done"]
      pbMessage(_INTL("Steven: ainda não chegou o momento da pesquisa com Kecleon. Explore a Rota 119!"))
      return false
    end
    if flags["devon_scope_received"]
      pbMessage(_INTL("Steven: use o Devon Scope para revelar os Kecleon invisíveis."))
      return true
    end
    unless GameData::Item.exists?(:DEVONSCOPE) && $bag && $bag.add(:DEVONSCOPE,1)
      pbMessage(_INTL("Steven: o Devon Scope ainda não está disponível ou sua Bolsa está cheia."))
      return false
    end
    flags["devon_scope_received"]=true
    pbMessage(_INTL("Steven: receba o Devon Scope! Ele revela Pokémon Kecleon escondidos."))
    true
  end

  def self.kecleon_scope(event_id,location)
    flags=state
    return false unless flags && [:FORTREE,:ROUTE120].include?(location) &&
                        event_id.is_a?(Integer) && $game_map &&
                        $game_self_switches && $game_map.events[event_id]
    _,map_ids=metadata
    expected=location==:FORTREE ? map_ids[64] : map_ids[138]
    return false unless expected && $game_map.map_id==expected
    unless flags["devon_scope_received"]
      pbMessage(_INTL("Uma presença invisível bloqueia sua passagem! Procure Steven e o Devon Scope."))
      return false
    end
    key="kecleon_#{location}_cleared"
    unless flags[key]
      pbMessage(_INTL("O Devon Scope revelou Kecleon! Ele fugiu e liberou a passagem."))
      flags[key]=true
    end
    $game_self_switches[[$game_map.map_id,event_id,"A"]]=true
    $game_map.events[event_id].refresh
    true
  end

  def self.winona_tm
    flags=state
    return false unless flags && feather_badge?
    return false if flags["winona_tm_given"]
    give_move_tm("winona_tm_given",:AERIALACE,[:TM40,:TM099,:TM101],
                 "Winona: receba a TM Aerial Ace!")
  end

  def self.winona
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return winona_tm if feather_badge?
    unless balance_badge? && flags["rival_119_done"] &&
           flags["devon_scope_received"] && flags["kecleon_FORTREE_cleared"]
      pbMessage(_INTL("Winona: conclua a missão do Weather Institute e use o Devon Scope antes do desafio."))
      return false
    end
    pbMessage(_INTL("Winona: vamos descobrir até onde seus Pokémon conseguem voar!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_WINONA,"Winona",868)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions,"HOENN","FEATHER")
      pbMessage(_INTL("Winona: não foi possível registrar a Feather Badge."))
      return false
    end
    flags["winona_defeated"]=true
    pbMessage(_INTL("Você conquistou a Feather Badge de Hoenn! Fly está liberado nesta região."))
    winona_tm
    true
  end

  def self.rival_lilycove
    flags=state
    return false unless flags && starter && $player && !$player.party.empty?
    unless feather_badge?
      pbMessage(_INTL("Seu rival: enfrente Winona em Fortree antes de continuar por Lilycove."))
      return false
    end
    if flags["rival_lilycove_done"]
      pbMessage(_INTL("Seu rival: nos encontraremos novamente mais adiante!"))
      return false
    end
    name=rival_name
    pbMessage(_INTL("{1}: uma última batalha antes de explorar Lilycove!",name))
    setBattleRule("canLose")
    unless TrainerBattle.start(:RIVAL1,name,RIVAL_STAGE8_LILYCOVE_VERSIONS.fetch(starter))
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["rival_lilycove_done"]=true
    pbMessage(_INTL("{1}: você venceu de novo! Vamos continuar nossa jornada!",name))
    true
  end

  def self.harbor_stage8
    return false unless state
    pbMessage(_INTL("Porto de Lilycove: as viagens marítimas e a Equipe Aqua serão integradas na próxima fase."))
    true
  end

  def self.contest_stage8
    return false unless state
    pbMessage(_INTL("Contest Hall de Lilycove: o concurso completo será integrado depois."))
    true
  end

  def self.stage8_future_gate(key)
    return false unless state
    messages={
      AQUA_HIDEOUT:"O esconderijo Aqua será aberto na próxima etapa.",
      SAFARI_ZONE:"A Safari Zone ainda não foi integrada neste piloto.",
      SCORCHED_SLAB:"Scorched Slab ainda não possui eventos validados.",
      MT_PYRE_PIER:"A travessia para Mt. Pyre pertence à próxima etapa."
    }
    return false unless messages.key?(key)
    pbMessage(_INTL(messages.fetch(key)))
    false
  end



  # Stage 09: isolated, regional-only event progression. This does NOT
  # register a playable certificate for Game.exe or Android.
  STAGE9_SIGNS = {
    MOSSDEEP_GYM:"Ginásio de Mossdeep: Tate e Liza desafiam você em dupla!",
    SPACE_CENTER:"Centro Espacial de Mossdeep: pesquisas e lançamento de foguetes.",
    MOSSDEEP:"Mossdeep: uma cidade de aventuras marinhas e espaciais."
  }.freeze
  STAGE9_GRUNT_PYRE=[920,921,922,923].freeze
  STAGE9_GRUNT_MAGMA=[940,941,942,943,944,945,946].freeze
  STAGE9_GRUNT_AQUA=[950,951,952,953,954].freeze
  STAGE9_GRUNT_SPACE=[991,994].freeze

  def self.sign_stage9(key)
    return false unless state && STAGE9_SIGNS.key?(key)
    pbMessage(_INTL(STAGE9_SIGNS.fetch(key)))
    true
  end

  def self.mind_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN").include?("MIND")
  end

  def self.stage9_transfer(source_id,dest_id,x,y)
    flags=state
    return false unless flags && [source_id,dest_id,x,y].all?{|v|v.is_a?(Integer)}
    return false unless defined?(BlueRegionTravel) && BlueRegionTravel.respond_to?(:move_to)
    _,map_ids=metadata
    return false unless map_ids[source_id] && map_ids[dest_id]
    return false unless $game_map && $game_player && $game_map.map_id==map_ids[source_id]
    # Only the producer of the event may authorize these source routes.
    if (182..189).cover?(dest_id) && !flags["magma_emblem_received"]
      pbMessage(_INTL("A entrada para o esconderijo Magma exige o Magma Emblem!"))
      return false
    end
    if (215..217).cover?(dest_id) && !flags["slateport_submarine_stolen"]
      pbMessage(_INTL("O esconderijo Aqua ainda está bloqueado. Investigue Slateport!"))
      return false
    end
    if (206..213).cover?(dest_id) && !feather_badge?
      pbMessage(_INTL("Você deve vencer Winona antes de explorar Mt. Pyre."))
      return false
    end
    if dest_id==82 && !flags["submarine_escaped"]
      pbMessage(_INTL("O ginásio de Mossdeep reabre depois que a Equipe Aqua partir."))
      return false
    end
    destination=[map_ids[dest_id],x,y,2]
    original=[$game_map.map_id,$game_player.x,$game_player.y,$game_player.direction]
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(destination) }
      true
    rescue StandardError => err
      begin
        pbFadeOutIn { BlueRegionTravel.move_to(original) } if $game_map.map_id!=original[0]
      rescue StandardError
      end
      pbMessage(_INTL("A passagem ainda não pôde ser realizada: {1}",err.message))
      false
    end
  end

  def self.stage9_grunt(kind,version,versions,key_prefix,requirement)
    flags=state
    return false unless flags && versions.include?(version) &&
                        $player && !$player.party.empty?
    unless requirement
      pbMessage(_INTL("Você ainda não concluiu a etapa anterior da missão de Hoenn."))
      return false
    end
    key="#{key_prefix}_#{version}_defeated"
    return false if flags[key]
    setBattleRule("canLose")
    unless TrainerBattle.start(kind,"Recruta",version)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags[key]=true
    pbMessage(_INTL("O recruta foi derrotado!"))
    true
  end

  def self.pyre_aqua_grunt(version)
    stage9_grunt(:BLUE_HOENN_AQUA,version,STAGE9_GRUNT_PYRE,
                 "pyre_aqua",feather_badge?)
  end

  def self.pyre_archie
    flags=state
    return false unless flags && feather_badge?
    pbMessage(flags["pyre_orb_stolen"] ?
      _INTL("Archie: o Red Orb já está com a Equipe Aqua!") :
      _INTL("Archie, líder Aqua, planeja roubar o Red Orb no cume."))
    true
  end

  def self.pyre_orb_scene
    flags=state
    return false unless flags && feather_badge?
    return false if flags["pyre_orb_stolen"]
    unless STAGE9_GRUNT_PYRE.all?{|v|flags["pyre_aqua_#{v}_defeated"]}
      pbMessage(_INTL("Quatro recrutas Aqua ainda vigiam o altar de Mt. Pyre."))
      return false
    end
    flags["pyre_orb_stolen"]=true
    pbMessage(_INTL("Archie roubou o Red Orb! A Equipe Aqua está fugindo para o mar."))
    pbMessage(_INTL("A senhora de Mt. Pyre precisa conversar com você antes que saia."))
    true
  end

  def self.pyre_elder
    flags=state
    return false unless flags
    unless flags["pyre_orb_stolen"]
      pbMessage(_INTL("Anciã: proteja os orbes de Mt. Pyre."))
      return false
    end
    if flags["magma_emblem_received"]
      pbMessage(_INTL("Anciã: o Magma Emblem abre a passagem secreta em Jagged Pass."))
      return true
    end
    item=:MAGMAEMBLEM
    if GameData::Item.exists?(item)
      unless $bag && $bag.add(item,1)
        pbMessage(_INTL("Anciã: sua Bolsa precisa de espaço para o Magma Emblem."))
        return false
      end
    else
      flags["magma_emblem_virtual"]=true
    end
    flags["magma_emblem_received"]=true
    pbMessage(_INTL("Você recebeu o Magma Emblem para investigar o esconderijo Magma!"))
    true
  end

  def self.enter_magma_hideout
    flags=state
    return false unless flags
    unless flags["magma_emblem_received"] && heat_badge?
      pbMessage(_INTL("Uma entrada secreta está selada. Investigue Mt. Pyre primeiro."))
      return false
    end
    stage9_transfer(180,182,15,38)
  end

  def self.magma_hideout_grunt(version)
    flags=state
    stage9_grunt(:BLUE_HOENN_MAGMA,version,STAGE9_GRUNT_MAGMA,
                 "magma_hideout",flags && flags["magma_emblem_received"])
  end

  def self.magma_hideout_tabitha
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return false if flags["hideout_tabitha_defeated"]
    unless [940,941].all?{|v|flags["magma_hideout_#{v}_defeated"]}
      pbMessage(_INTL("Tabitha: enfrente os primeiros recrutas do esconderijo!"))
      return false
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_TABITHA,"Tabitha",988)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["hideout_tabitha_defeated"]=true
    pbMessage(_INTL("Tabitha: Maxie não vai recuar!"))
    true
  end

  def self.magma_hideout_maxie
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return false if flags["hideout_maxie_defeated"]
    unless flags["hideout_tabitha_defeated"]
      pbMessage(_INTL("Maxie: Tabitha ainda está protegendo o acesso."))
      return false
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_MAXIE,"Maxie",989)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["hideout_maxie_defeated"]=true
    pbMessage(_INTL("Maxie: tentaremos despertar Groudon, mesmo após esta derrota!"))
    true
  end

  def self.groudon_hideout
    flags=state
    return false unless flags
    return false if flags["groudon_awakened"]
    unless flags["hideout_maxie_defeated"]
      pbMessage(_INTL("Groudon ainda dorme. Primeiro enfrente o líder Magma."))
      return false
    end
    flags["groudon_awakened"]=true
    pbMessage(_INTL("Groudon despertou e deixou o esconderijo Magma!"))
    pbMessage(_INTL("Volte a Slateport e procure o Capitão Stern: a Equipe Aqua está atrás de um submarino."))
    true
  end

  def self.slateport_submarine_news
    flags=state
    return false unless flags
    unless flags["groudon_awakened"]
      pbMessage(_INTL("Stern: o submarino ainda está em segurança."))
      return false
    end
    return false if flags["slateport_submarine_stolen"]
    flags["slateport_submarine_stolen"]=true
    pbMessage(_INTL("Stern: a Equipe Aqua roubou o submarino em Slateport!"))
    pbMessage(_INTL("Investigue o esconderijo Aqua, a leste de Lilycove."))
    true
  end

  def self.enter_aqua_hideout
    flags=state
    return false unless flags
    unless flags["slateport_submarine_stolen"]
      pbMessage(_INTL("O esconderijo Aqua ainda está trancado. Investigue o porto de Slateport."))
      return false
    end
    stage9_transfer(69,215,14,29)
  end

  def self.aqua_hideout_grunt(version)
    flags=state
    stage9_grunt(:BLUE_HOENN_AQUA,version,STAGE9_GRUNT_AQUA,
                 "aqua_hideout",flags && flags["slateport_submarine_stolen"])
  end

  def self.aqua_hideout_matt
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return false if flags["aqua_matt_defeated"]
    unless [950,953].all?{|v|flags["aqua_hideout_#{v}_defeated"]}
      pbMessage(_INTL("Matt: vença os recrutas nos corredores do esconderijo Aqua!"))
      return false
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_MATT,"Matt",917)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["aqua_matt_defeated"]=true
    pbMessage(_INTL("Matt: Archie já está saindo com o submarino!"))
    true
  end

  def self.submarine_escape
    flags=state
    return false unless flags
    return false if flags["submarine_escaped"]
    unless flags["slateport_submarine_stolen"] && flags["aqua_matt_defeated"]
      pbMessage(_INTL("O submarino Aqua ainda não pode partir. Investigue Slateport e enfrente Matt."))
      return false
    end
    flags["submarine_escaped"]=true
    pbMessage(_INTL("O submarino da Equipe Aqua escapou! Siga a leste rumo a Mossdeep."))
    true
  end

  def self.tate_liza_tm
    flags=state
    return false unless flags && mind_badge?
    return false if flags["tate_liza_tm_given"]
    give_move_tm("tate_liza_tm_given",:CALMMIND,[:TM04,:TM129,:TM130],
                 "Tate e Liza: receba a TM Calm Mind!")
  end

  def self.tate_liza
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return tate_liza_tm if mind_badge?
    unless feather_badge? && flags["submarine_escaped"]
      pbMessage(_INTL("Tate e Liza: detenha a Equipe Aqua antes de nosso desafio em dupla."))
      return false
    end
    if defined?(pbCanDoubleBattle?) && !pbCanDoubleBattle?
      pbMessage(_INTL("Tate e Liza: você precisa de dois Pokémon disponíveis para a batalha dupla."))
      return false
    end
    pbMessage(_INTL("Tate e Liza: una suas estratégias e enfrente nosso time Psíquico!"))
    setBattleRule("double")
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_TATE_LIZA,"Tate & Liza",982)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions,"HOENN","MIND")
      pbMessage(_INTL("O registro da Mind Badge regional falhou."))
      return false
    end
    flags["tate_liza_defeated"]=true
    pbMessage(_INTL("Você conquistou a Mind Badge de Hoenn! Dive está autorizado nesta região."))
    tate_liza_tm
    true
  end

  def self.space_magma_grunt(version)
    flags=state
    stage9_grunt(:BLUE_HOENN_MAGMA,version,STAGE9_GRUNT_SPACE,
                 "space_magma",flags && mind_badge?)
  end

  def self.space_center_maxie
    flags=state
    return false unless flags
    pbMessage(flags["space_center_saved"] ?
      _INTL("Maxie: a Equipe Magma desistiu da invasão do Centro Espacial.") :
      _INTL("Maxie: queremos o combustível do foguete! Steven está nos enfrentando."))
    true
  end

  def self.space_center_steven
    flags=state
    return false unless flags && $player && !$player.party.empty?
    if flags["space_center_saved"]
      pbMessage(_INTL("Steven: obrigado por defender o Centro Espacial! Procure minha casa para obter Dive."))
      return true
    end
    unless mind_badge? && STAGE9_GRUNT_SPACE.all?{|v|flags["space_magma_#{v}_defeated"]}
      pbMessage(_INTL("Steven: vença Tate e Liza e afaste os recrutas Magma primeiro."))
      return false
    end
    pbMessage(_INTL("Steven: vamos enfrentar Maxie e Tabitha!"))
    # This is a provisional guarded SEQUENCE, NOT proof of the Emerald
    # native Steven+player multi-trainer double battle.
    unless flags["space_tabitha_defeated"]
      setBattleRule("canLose")
      unless TrainerBattle.start(:BLUE_HOENN_TABITHA,"Tabitha",993)
        $player.heal_party if $player.respond_to?(:heal_party)
        return false
      end
      flags["space_tabitha_defeated"]=true
    end
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_MAXIE,"Maxie",992)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["space_center_saved"]=true
    pbMessage(_INTL("Steven: a Equipe Magma recuou! O Centro Espacial está seguro."))
    true
  end

  def self.steven_house_stage9
    flags=state
    return false unless flags
    unless mind_badge? && flags["space_center_saved"]
      pbMessage(_INTL("Steven: volte à minha casa após defender o Centro Espacial."))
      return false
    end
    return false if flags["hm_dive_received"]
    item=[:HM08,:HMDIVE].find{|id|
      GameData::Item.exists?(id) && GameData::Item.get(id).respond_to?(:move) &&
      GameData::Item.get(id).move==:DIVE
    }
    unless item && $bag && $bag.add(item,1)
      pbMessage(_INTL("Steven: HM Dive precisa estar registrado e sua Bolsa deve ter espaço."))
      return false
    end
    flags["hm_dive_received"]=true
    pbMessage(_INTL("Steven: receba HM Dive! A Mind Badge permite usar o movimento em Hoenn."))
    true
  end

  def self.super_rod_stage9
    flags=state
    return false unless flags
    return false if flags["super_rod_received"]
    unless GameData::Item.exists?(:SUPERROD) && $bag && $bag.add(:SUPERROD,1)
      pbMessage(_INTL("Pescador: a Super Rod deve estar cadastrada e caber na Bolsa."))
      return false
    end
    flags["super_rod_received"]=true
    pbMessage(_INTL("Você recebeu a Super Rod!"))
    true
  end

  def self.mossdeep_space_scientist
    return false unless state
    pbMessage(_INTL("Pesquisador: nosso Centro Espacial estuda foguetes, meteoritos e viagens pelo espaço."))
    true
  end


  # Stage 10 — Emerald ending in an isolated Hoenn save namespace.
  # These scripts do NOT reproduce native Dive, Waterfall, ice floors,
  # Strength puzzles, Legendary weather, Hall of Fame or League UI.
  STAGE10_ELITE = [
    [:BLUE_HOENN_ELITE,"Sidney",1094,"sidney"],
    [:BLUE_HOENN_ELITE,"Phoebe",1095,"phoebe"],
    [:BLUE_HOENN_ELITE,"Glacia",1096,"glacia"],
    [:BLUE_HOENN_ELITE,"Drake",1097,"drake"]
  ].freeze

  def self.rain_badge?
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN").include?("RAIN")
  end

  # QA08: count actual local badges, never the global badge counter.
  # Reusing Wally's story flag from an older save cannot replace the eight
  # Hoenn gym victories. The gym events themselves still use Decades scaling.
  QA8_LEAGUE_BADGES = %w[STONE KNUCKLE DYNAMO HEAT BALANCE FEATHER MIND RAIN].freeze
  QA8_VICTORY_ROAD = (250..252).freeze

  def self.qa8_league_badges?
    return false unless state && defined?(BlueRegions)
    badges = BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")
    QA8_LEAGUE_BADGES.all?{|badge| badges.include?(badge)}
  end

  # QA09: story flags must form a complete prefix of four League wins.
  # A prior save with a later flag but missing an earlier win cannot skip a room.
  # The remapped map guard protects direct event calls, not only entrances.
  def self.qa9_at_league_map?(source_id)
    return false unless state && $game_map
    _, maps = metadata
    maps[source_id] && $game_map.map_id == maps[source_id]
  end

  def self.qa9_elite_unlocked?(index)
    flags = state
    return false unless flags && index.is_a?(Integer) && (0..3).cover?(index)
    return false unless qa8_league_badges? && flags["wally_road_defeated"]
    (0...index).all? { |previous|
      flags["elite_#{STAGE10_ELITE[previous][3]}_defeated"]
    }
  end

  def self.qa9_champion_unlocked?
    return false unless state && qa9_elite_unlocked?(3)
    flags = state
    flags["elite_drake_defeated"] &&
      STAGE10_ELITE.all? { |_,_,_,key| flags["elite_#{key}_defeated"] }
  end

  def self.sign_stage10(key)
    return false unless state
    signs = {
      SOOTOPOLIS_GYM: "Ginásio de Sootopolis: Juan. A crise do clima deve acabar antes do desafio.",
      LEAGUE_GATE: "Liga Pokémon de Hoenn: são exigidas oito insígnias desta região."
    }
    return false unless signs.key?(key)
    pbMessage(_INTL(signs.fetch(key)))
    true
  end

  # QA04: these guards apply exclusively to the isolated HOENN regional save.
  # No prepend of Essentials native field-move handlers and no global badge
  # mutation: native field movement still needs real Game.exe certification.
  HOENN_FIELD_BADGES = {
    CUT:"STONE", FLASH:"KNUCKLE", ROCKSMASH:"DYNAMO",
    STRENGTH:"HEAT", SURF:"BALANCE", DIVE:"MIND",
    WATERFALL:"RAIN"
  }.freeze
  HOENN_FIELD_ITEMS = {
    CUT:[:HM01,:HMCUT], FLASH:[:HM05,:HMFLASH],
    ROCKSMASH:[:HM06,:TM94], STRENGTH:[:HM04,:HMSTRENGTH],
    SURF:[:HM03,:HMSURF], DIVE:[:HM08,:HMDIVE],
    WATERFALL:[:HM07,:HMWATERFALL]
  }.freeze

  def self.field_move_ready?(move, show_message=false)
    flags=state
    badge=HOENN_FIELD_BADGES[move]
    return false unless flags && badge && defined?(BlueRegions)
    badges=BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")
    unless badges.include?(badge)
      pbMessage(_INTL("Este movimento exige a insígnia {1} de Hoenn.", badge)) if show_message
      return false
    end
    return false unless $bag && defined?(GameData::Item)
    item=HOENN_FIELD_ITEMS.fetch(move).find{|id|
      GameData::Item.exists?(id) &&
      GameData::Item.get(id).respond_to?(:move) &&
      GameData::Item.get(id).move==move &&
      $bag.has?(id)
    }
    unless item
      pbMessage(_INTL("Obtenha o HM do movimento {1} antes de usá-lo em Hoenn.",move)) if show_message
      return false
    end
    party=$player && $player.respond_to?(:party) ? $player.party : nil
    unless party && party.any?{|pkmn|
      pkmn.respond_to?(:hasMove?) && pkmn.hasMove?(move)
    }
      pbMessage(_INTL("Um Pokémon da sua equipe precisa conhecer {1}.",move)) if show_message
      return false
    end
    true
  end

  def self.field_hm_reward(move, candidates, key, message)
    flags=state
    return false unless flags && HOENN_FIELD_BADGES.key?(move) &&
                        key.is_a?(String) && candidates.is_a?(Array)
    return false if flags[key]
    return false unless defined?(GameData::Item)
    hm=candidates.find{|id|
      GameData::Item.exists?(id) && GameData::Item.get(id).move==move
    }
    unless hm
      pbMessage(_INTL("O HM {1} ainda não está registrado nesta instalação do Blue.",move))
      return false
    end
    unless $bag && $bag.add(hm,1)
      pbMessage(_INTL("Abra espaço na Bolsa para receber o HM {1}.",move))
      return false
    end
    flags[key]=true
    pbMessage(_INTL(message))
    true
  end

  def self.waterfall_from_juan
    flags=state
    return false unless flags && rain_badge?
    field_hm_reward(:WATERFALL,[:HM07,:HMWATERFALL],"hm_waterfall_received",
                    "Juan: receba HM Waterfall! A Rain Badge libera seu uso em Hoenn.")
  end

  def self.rock_smash_obstacle(event_id)
    flags=state
    return false unless flags && event_id.is_a?(Integer) &&
                        $game_map && $game_self_switches
    _,map_ids=metadata
    return false unless map_ids.value?($game_map.map_id)
    event=$game_map.events[event_id]
    return false unless event
    key="rock_smash_#{$game_map.map_id}_#{event_id}"
    if flags[key]
      $game_self_switches[[$game_map.map_id,event_id,"A"]]=true
      event.refresh
      return true
    end
    return false unless field_move_ready?(:ROCKSMASH,true)
    return false unless pbConfirmMessage(_INTL("Usar Rock Smash para quebrar a pedra?"))
    flags[key]=true
    $game_self_switches[[$game_map.map_id,event_id,"A"]]=true
    event.refresh
    pbMessage(_INTL("A pedra foi quebrada."))
    true
  end

  def self.strength_boulder(event_id)
    return false unless state && event_id.is_a?(Integer) &&
                        $game_map && $game_player
    _,map_ids=metadata
    return false unless map_ids.value?($game_map.map_id)
    event=$game_map.events[event_id]
    return false unless event && event.respond_to?(:move_straight)
    return false unless field_move_ready?(:STRENGTH,true)
    old=[event.x,event.y]
    event.move_straight($game_player.direction)
    moved=[event.x,event.y]!=old
    pbMessage(_INTL("A pedra não pode ser empurrada nessa direção.")) unless moved
    moved
  end

  SEAFLOOR_INTERIORS = (227..236).freeze
  QA5_SEAFLOOR_STORY_KEYS = %w[
    groudon_awakened slateport_submarine_stolen submarine_escaped
    space_center_saved hm_dive_received
  ].freeze

  def self.seafloor_story_ready?
    flags=state
    return false unless flags && mind_badge?
    QA5_SEAFLOOR_STORY_KEYS.all?{|key| flags[key]}
  end

  def self.stage10_transfer(source_id,dest_id,x,y)
    flags=state
    return false unless flags && [source_id,dest_id,x,y].all?{|n|n.is_a?(Integer)}
    _,maps=metadata
    return false unless maps[source_id] && maps[dest_id] && $game_map &&
                        $game_map.map_id==maps[source_id]
    if [255,258,259,260,261,262,263,266,227,228,229,230,231,232,233,234,235,236].include?(dest_id) &&
       !([255,258,259,260,261,262,263,266,227,228,229,230,231,232,233,234,235,236].include?(source_id))
      return false unless field_move_ready?(:DIVE,true)
    end
    # Upper Ever Grande: real Waterfall competency is required; the Rain Badge
    # alone is NOT enough. Other coastal crossings still rely on native Surf.
    if source_id==91 && [250,322].include?(dest_id)
      # All southern entrances must respect the waterfall field technique.
      # Exiting Victory Road is not subject to this rule.
      return false unless field_move_ready?(:WATERFALL,true)
    end
    if QA8_VICTORY_ROAD.cover?(dest_id) &&
       !QA8_VICTORY_ROAD.cover?(source_id) && !qa8_league_badges?
      pbMessage(_INTL("Victory Road exige as oito insígnias de Hoenn."))
      return false
    end
    if source_id==250 && dest_id==322 && !flags["wally_road_defeated"]
      pbMessage(_INTL("Wally espera você antes da saída de Victory Road."))
      return false
    end
    # Lock the cave only when ENTERING from another area. Never lock stairs
    # inside the cave or block a retreat from a partially migrated save.
    if SEAFLOOR_INTERIORS.cover?(dest_id) && !SEAFLOOR_INTERIORS.cover?(source_id)
      unless seafloor_story_ready?
        pbMessage(_INTL("A Seafloor Cavern exige a fuga do submarino, a defesa do Centro Espacial e Dive com a Mind Badge."))
        return false
      end
    end
    if dest_id==238 && !flags["sootopolis_crisis_started"]
      pbMessage(_INTL("Fale com Steven sobre a crise do clima em Sootopolis."))
      return false
    end
    if (239..240).cover?(dest_id) && !flags["sootopolis_crisis_started"]
      return false
    end
    if (241..248).cover?(dest_id) && !flags["sky_pillar_task"]
      pbMessage(_INTL("Wallace ainda precisa abrir o caminho para Sky Pillar."))
      return false
    end
    # QA06: upper Sky Pillar floors require Wallace's permission.
    # Preserve escape paths for saves already inside the tower.
    if (243..248).cover?(dest_id) && !(243..248).cover?(source_id) &&
       !flags["sky_pillar_open"]
      pbMessage(_INTL("Wallace precisa liberar a entrada de Sky Pillar."))
      return false
    end
    if dest_id==87 && !flags["crisis_resolved"]
      pbMessage(_INTL("O ginásio de Juan está fechado durante a crise do clima."))
      return false
    end
    if [250,251,252,322,93,100,94,95,96,97,98,99].include?(dest_id) && !rain_badge?
      pbMessage(_INTL("O caminho para a Liga exige a Rain Badge de Hoenn."))
      return false
    end
    if [93,100,94,95,96,97,98,99].include?(dest_id) &&
       (!flags["wally_road_defeated"] || !qa8_league_badges?)
      pbMessage(_INTL("A Liga exige as oito insígnias de Hoenn e a vitória sobre Wally em Victory Road."))
      return false
    end
    if (94..97).cover?(dest_id) && !qa9_elite_unlocked?(dest_id-94)
      pbMessage(_INTL("A Elite Four deve ser vencida na ordem: Sidney, Phoebe, Glacia e Drake."))
      return false
    end
    if dest_id==98 && !qa9_champion_unlocked?
      pbMessage(_INTL("Vença Sidney, Phoebe, Glacia e Drake antes do Campeão Wallace."))
      return false
    end
    if dest_id==99 && !flags["champion_wallace_defeated"]
      pbMessage(_INTL("Derrote Wallace para entrar no Hall of Fame."))
      return false
    end
    stage9_transfer(source_id,dest_id,x,y)
  end

  def self.seafloor_archie
    flags=state
    return false unless flags && seafloor_story_ready? &&
                        $player && !$player.party.empty?
    _,map_ids=metadata
    return false unless $game_map && $game_map.map_id==map_ids[236]
    return true if flags["seafloor_archie_defeated"]
    pbMessage(_INTL("Archie: o poder de Kyogre será da Equipe Aqua!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_ARCHIE,"Archie",1026)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["seafloor_archie_defeated"]=true
    pbMessage(_INTL("Archie recuou. O despertar de Kyogre está próximo."))
    true
  end

  def self.seafloor_awakening
    flags=state
    return false unless flags && seafloor_story_ready? &&
                        flags["seafloor_archie_defeated"]
    _,map_ids=metadata
    return false unless $game_map && $game_map.map_id==map_ids[236]
    return false if flags["kyogre_awakened"]
    flags["kyogre_awakened"]=true
    pbMessage(_INTL("Kyogre despertou! Uma crise climática se espalha por Hoenn."))
    true
  end

  # QA06: all climate-story events are bound to their original Hoenn maps.
  def self.qa6_at_map?(source_id)
    _,map_ids=metadata
    $game_map && $game_map.map_id==map_ids[source_id]
  end

  def self.sootopolis_crisis
    flags=state
    return false unless flags && qa6_at_map?(83) &&
                         flags["groudon_awakened"] &&
                         flags["kyogre_awakened"] &&
                         flags["seafloor_archie_defeated"]
    return false if flags["sootopolis_crisis_started"]
    flags["sootopolis_crisis_started"]=true
    pbMessage(_INTL("Steven: Groudon e Kyogre desequilibraram o clima! Procure Wallace na Cave of Origin."))
    true
  end

  def self.origin_wallace_stage10
    flags=state
    return false unless flags && qa6_at_map?(240) && flags["sootopolis_crisis_started"]
    return true if flags["sky_pillar_task"]
    flags["sky_pillar_task"]=true
    pbMessage(_INTL("Wallace: Rayquaza pode deter a crise. Encontre-me em Sky Pillar!"))
    true
  end

  def self.sky_pillar_wallace
    flags=state
    return false unless flags && qa6_at_map?(241) && flags["sky_pillar_task"]
    return true if flags["sky_pillar_open"]
    flags["sky_pillar_open"]=true
    pbMessage(_INTL("Wallace: siga até o topo de Sky Pillar para alcançar Rayquaza."))
    true
  end

  def self.rayquaza_stage10
    flags=state
    return false unless flags && qa6_at_map?(248) &&
                         flags["sootopolis_crisis_started"] &&
                         flags["groudon_awakened"] &&
                         flags["kyogre_awakened"] &&
                         flags["sky_pillar_task"] &&
                         flags["sky_pillar_open"]
    return false if flags["crisis_resolved"]
    flags["rayquaza_summoned"]=true
    flags["crisis_resolved"]=true
    pbMessage(_INTL("Rayquaza atendeu ao chamado! A crise climática terminou. Volte ao ginásio de Juan."))
    true
  end

  def self.juan_tm
    flags=state
    return false unless flags && rain_badge?
    return false if flags["juan_tm_given"]
    give_move_tm("juan_tm_given",:WATERPULSE,[:TM03],
                 "Juan: receba a TM Water Pulse!")
  end

  def self.juan
    flags=state
    return false unless flags && $player && !$player.party.empty?
    if rain_badge?
      waterfall_from_juan unless flags["hm_waterfall_received"]
      return juan_tm
    end
    unless flags["crisis_resolved"] && mind_badge?
      pbMessage(_INTL("Juan: a paz deve voltar a Sootopolis antes da nossa batalha."))
      return false
    end
    pbMessage(_INTL("Juan: uma batalha de Água definirá o destino da Rain Badge!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_JUAN,"Juan",1087)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    unless BlueRegions.award($PokemonGlobal.blue_regions,"HOENN","RAIN")
      pbMessage(_INTL("Não foi possível registrar a Rain Badge regional."))
      return false
    end
    flags["juan_defeated"]=true
    pbMessage(_INTL("Rain Badge de Hoenn conquistada! Waterfall está autorizado na região."))
    waterfall_from_juan
    juan_tm
    true
  end

  def self.wally_victory_road
    flags=state
    return false unless flags && $player && !$player.party.empty?
    _, maps = metadata
    return false unless $game_map && $game_map.map_id == maps[250]
    return true if flags["wally_road_defeated"]
    unless qa8_league_badges?
      pbMessage(_INTL("Wally: conquiste as oito insígnias de Hoenn antes do desafio final!"))
      return false
    end
    pbMessage(_INTL("Wally: desta vez vou mostrar tudo que aprendi!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_WALLY,"Wally",1025)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["wally_road_defeated"]=true
    pbMessage(_INTL("Wally: boa sorte na Liga Pokémon!"))
    true
  end

  def self.elite_four(index)
    flags=state
    return false unless flags && index.is_a?(Integer) && (0..3).cover?(index) &&
                        $player && !$player.party.empty?
    return false unless qa9_at_league_map?(94 + index)
    kind,name,version,key=STAGE10_ELITE[index]
    completed="elite_#{key}_defeated"
    return false unless qa9_elite_unlocked?(index)
    return true if flags[completed]
    pbMessage(_INTL("{1}: mostre a força de seu time!",name))
    setBattleRule("canLose")
    unless TrainerBattle.start(kind,name,version)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags[completed]=true
    pbMessage(_INTL("{1}: você venceu! Siga para a próxima sala.",name))
    true
  end

  def self.champion_wallace
    flags=state
    return false unless flags && $player && !$player.party.empty?
    return false unless qa9_at_league_map?(98) && qa9_champion_unlocked?
    return true if flags["champion_wallace_defeated"]
    pbMessage(_INTL("Wallace: você conquistou o direito de me desafiar!"))
    setBattleRule("canLose")
    unless TrainerBattle.start(:BLUE_HOENN_CHAMPION,"Wallace",1098)
      $player.heal_party if $player.respond_to?(:heal_party)
      return false
    end
    flags["champion_wallace_defeated"]=true
    pbMessage(_INTL("Wallace: parabéns! Entre no Hall of Fame e registre sua vitória."))
    true
  end

  # QA10: only the authored Hall event on source Map99 may commit Hoenn's
  # League victory. Never award on Wallace battle, on a source warp or in a
  # different region; never write native Decades badges/switches.
  def self.qa10_hall_ready?
    flags=state
    return false unless flags && qa9_at_league_map?(99) &&
                        qa9_champion_unlocked? && flags["champion_wallace_defeated"]
    return false unless defined?(BlueRegions) &&
                        BlueRegions.respond_to?(:complete_league) &&
                        BlueRegions.respond_to?(:unlocked)
    region=$PokemonGlobal.blue_regions
    region.is_a?(Hash) && region["leagues"].is_a?(Array)
  end

  def self.qa10_postgame_status
    flags=state
    return false unless flags && flags["hoenn_hall_of_fame"] &&
                        qa9_champion_unlocked?
    region=$PokemonGlobal.blue_regions
    return false unless region.is_a?(Hash) && region["leagues"].is_a?(Array) &&
                        region["leagues"].include?("HOENN") &&
                        defined?(BlueRegions) &&
                        BlueRegions.respond_to?(:neighbors) &&
                        BlueRegions.respond_to?(:unlocked)
    _,maps=metadata
    return false unless $game_map &&
                        [maps[99],maps[322]].include?($game_map.map_id)
    neighbors=BlueRegions.neighbors("HOENN")
    unlocked=BlueRegions.unlocked(region)
    return false unless neighbors.is_a?(Array) && neighbors.length==2 &&
                        neighbors.all?{|key| unlocked.include?(key)}
    pbMessage(_INTL("Circuito regional: Hoenn concluída. Johto e Sinnoh foram liberadas; a viagem só ficará disponível após a instalação e validação dos respectivos mapas."))
    true
  end

  def self.hall_of_fame_stage10
    return false unless qa10_hall_ready?
    flags=state
    region=$PokemonGlobal.blue_regions
    # Old QA saves may have a local flag only. Reconcile it only after
    # validating every win, badges and the physical Hall map.
    unless region["leagues"].include?("HOENN")
      return false unless BlueRegions.complete_league(region,"HOENN")
    end
    if flags["hoenn_hall_of_fame"]
      return qa10_postgame_status
    end
    flags["hoenn_hall_of_fame"]=true
    pbMessage(_INTL("Hall of Fame de Hoenn: sua vitória foi registrada neste save regional!"))
    qa10_postgame_status
    # Native Hall of Fame animation, credits and end-screen remain unverified.
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
