# Loaded by the standalone Hoenn copy.

module BlueHoennPilot
  STARTERS = [:TREECKO, :TORCHIC, :MUDKIP].freeze
  MARKER = "Data/blue-hoenn-pilot.txt".freeze

  def self.metadata
    return @metadata if @metadata
    lines = File.readlines(MARKER, chomp: true)
    raise "Marcador do piloto de Hoenn inválido." unless lines.shift == "BLUE_HOENN_PILOT_V1"
    values = lines.flat_map { |line| line.split(",") }.map { |part| Integer(part, 10) }
    start = values.shift(3)
    maps = values.each_slice(2).to_h
    raise "Mapas do piloto de Hoenn inválidos." unless maps.keys.sort == [7, 8, 11, 12, 13, 101] &&
                                                         maps.values.uniq.length == 6 &&
                                                         maps.values.all? { |id| (700..999).cover?(id) } &&
                                                         start == [maps.fetch(8), 25, 6]
    @metadata = [start, maps]
  end

  def self.verify_compilation
    GameData::Encounter.load
    GameData::MapMetadata.load
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
    connections = load_data("Data/map_connections.dat")
    [[maps.fetch(7), route], [maps.fetch(12), route]].each do |first, second|
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

  def self.mother
    return unless state
    pbMessage(_INTL("Mãe: Bem-vindo a Littleroot! O Professor Birch espera por você no laboratório, ao sul da cidade."))
  end

  def self.birch
    progress = state
    return unless progress
    progress["met_birch"] = true
    if progress["starter"]
      pbMessage(_INTL("Birch: Siga ao norte pela Rota 101 para chegar a Oldale. Você pode treinar na grama pelo caminho."))
    else
      pbMessage(_INTL("Birch: Escolha um parceiro na bancada. Da esquerda para a direita: Treecko, Torchic e Mudkip."))
    end
  end

  def self.choose_starter(species)
    progress = state
    return unless progress && STARTERS.include?(species)
    if progress["starter"]
      pbMessage(_INTL("Birch: Você já escolheu seu parceiro."))
      return
    end
    unless progress["met_birch"]
      pbMessage(_INTL("Fale com o Professor Birch antes de escolher."))
      return
    end
    name = GameData::Species.get(species).name
    return unless pbConfirmMessage(_INTL("Escolher {1} como seu parceiro?", name))
    return unless pbAddPokemonSilent(species, 5)
    progress["starter"] = species.to_s
    $bag.add(:POKEBALL, 5)
    pbMessage(_INTL("Birch: {1} vai com você. Leve também cinco Poké Bolas para suas primeiras capturas.", name))
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

  module Start
    def select_and_prepare
      return super unless @new_game && $PokemonGlobal && File.file?(BlueHoennPilot::MARKER)
      start, = BlueHoennPilot.metadata
      $PokemonGlobal.blue_regions = BlueRegions.new_state("HOENN")
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
end
