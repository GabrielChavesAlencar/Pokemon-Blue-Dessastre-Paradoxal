# Standalone Sinnoh events, using the Blue engine and save profile.
module BlueSinnohPreview
  STARTERS = [:TURTWIG, :CHIMCHAR, :PIPLUP].freeze
  START = [801, 29, 5].freeze

  def self.state
    region = $PokemonGlobal&.blue_regions
    return unless region && region["current"] == "SINNOH"
    region["sinnoh_pilot"] ||= {}
  end

  def self.profile
    progress = state
    return unless progress && !progress["profile"]
    pbCharacterSelect
    $game_player.refresh_charset
    $game_player.transparent = false
    progress["profile"] = true
  end

  def self.mother
    pbMessage(_INTL("Mãe: Procure o Professor Rowan em Sandgem. Vá pelo caminho da Rota 201.")) if state
  end

  def self.rowan
    progress = state
    return unless progress
    if progress["starter"]
      pbMessage(_INTL("Rowan: O Centro Pokémon fica aqui em Sandgem. Você também pode capturar Pokémon na Rota 201."))
      return
    end
    names = STARTERS.map { |id| GameData::Species.get(id).name }
    choice = pbMessage(_INTL("Rowan: Qual Pokémon vai acompanhar você?"), names + [_INTL("Voltar")], names.length)
    return unless choice && choice.between?(0, STARTERS.length - 1)
    return unless pbAddPokemonSilent(STARTERS[choice], 5)
    progress["starter"] = STARTERS[choice].to_s
    $bag.add(:POKEBALL, 5)
    pbMessage(_INTL("Rowan: Aqui estão cinco Poké Bolas. Explore a rota com seu novo parceiro."))
  end

  def self.heal
    return unless state && !$player.party.empty?
    $player.heal_party
    pbMessage(_INTL("Enfermeira: Seus Pokémon estão recuperados!"))
  end

  def self.verify_compilation
    GameData::Encounter.load
    GameData::MapMetadata.load
    raise "Encontros da Rota 201 ausentes" unless GameData::Encounter.exists?(802, 0)
    raise "Metadados Sinnoh incompletos" unless (800..805).all? { |id| GameData::MapMetadata.exists?(id) }
    connections = load_data("Data/map_connections.dat")
    unless [[800, 802], [802, 803]].all? { |pair| connections.any? { |row| [row[0], row[3]].sort == pair } }
      raise "Conexões de Sinnoh incompletas"
    end
  end

  module Start
    def select_and_prepare
      return super unless @new_game && $PokemonGlobal && File.file?("Sinnoh pilot.json")
      $PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")
      BlueStory.choose_mode(:story)
      BlueCampaign.begin_journey(false)
      $PokemonGlobal.blue_traditional_starters = true
      $PokemonGlobal.blue_campaign_departure = false
      pbChangePlayer(1)
      $game_player.refresh_charset
      $game_player.transparent = false
      $data_system.start_map_id, $data_system.start_x, $data_system.start_y = BlueSinnohPreview::START
    end
  end

  BlueRegionStart.singleton_class.prepend(Start)
end
