# Regional starting point for NEW GAME only.
# Older saves and the native Decades introduction are never rewritten.
module BlueRegionStart
  MARKER = "Data/blue-kanto-start.txt".freeze
  def self.kanto_spawn
    return nil unless File.file?(MARKER)
    # Created only by install_kanto.py after committing an integrated map set.
    fields = File.read(MARKER).strip.split(",")
    return nil unless fields.length == 5 && fields[0] == "BLUE_KANTO_START_V1" && fields[1] == "KANTO"
    values = fields[2, 3].map { |part| Integer(part, 10) rescue nil }
    return nil unless values.all? { |part| part.is_a?(Integer) }
    map_id, x, y = values
    return nil if map_id <= 0 || x < 0 || y < 0
    return nil unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map_id))
    [map_id, x, y]
  rescue IOError, SystemCallError, ArgumentError
    nil
  end

  def self.playable?(region)
    region == "DECADES" || (region == "KANTO" && !kanto_spawn.nil?)
  end

  def self.choose_initial
    return "DECADES" unless $PokemonGlobal
    keys = BlueRegions.circuit + ["HISUI"]
    labels = keys.map do |key|
      label = BlueRegions.info(key)["name"]
      playable?(key) ? _INTL("{1} - pronta para começar", label) : _INTL("{1} - em preparação", label)
    end
    loop do
      selection = pbMessage(
        _INTL("Escolha a região inicial. Esta decisão será salva na nova partida."),
        labels + [_INTL("Iniciar em Decades")], -1
      )
      return "DECADES" if selection.nil? || selection < 0 || selection >= keys.length
      region = keys[selection]
      unless playable?(region)
        pbMessage(_INTL("Ainda não existem mapas instalados e validados para começar em {1}.", BlueRegions.info(region)["name"]))
        next
      end
      next unless pbConfirmMessage(_INTL("Começar sua jornada em {1}?", BlueRegions.info(region)["name"]))
      return region
    end
  end

  def self.select_and_prepare
    return unless @new_game && $PokemonGlobal
    # Called only AFTER the native SaveData new-game initialization, and BEFORE
    # the native map factory chooses the starting map.
    region = choose_initial
    spawn = region == "KANTO" ? kanto_spawn : nil
    region = "DECADES" unless region == "DECADES" || spawn
    $PokemonGlobal.blue_regions = BlueRegions.new_state(region)
    return if region == "DECADES"

    # Preserve the Blue battle rules for Kanto; Decades' original Story/Battle
    # choices and their event flags must not be executed on a Kanto start.
    BlueStory.choose_mode(:story)
    BlueCampaign.begin_journey(false)
    $PokemonGlobal.blue_traditional_starters = true
    # The Decades departure handler clears the bag on the first non-map-1
    # transition; on Kanto, Oak awards the starter and items in the lab.
    $PokemonGlobal.blue_campaign_departure = false
    $data_system.start_map_id, $data_system.start_x, $data_system.start_y = spawn
  end

  def self.with_new_game
    # A loaded save calls Game.load, not Game.start_new. This scope prevents any
    # new region prompts during startup, save migration or load.
    original = nil
    if $data_system
      original = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]
    end
    @new_game = true
    yield
  ensure
    if original && $data_system
      $data_system.start_map_id, $data_system.start_x, $data_system.start_y = original
    end
    @new_game = false
  end

  module NewGame
    def start_new(*args)
      BlueRegionStart.with_new_game { super }
    end
  end

  module SaveValues
    def load_new_game_values(*args)
      result = super
      BlueRegionStart.select_and_prepare
      result
    end
  end

  def self.install
    return if @installed
    Game.singleton_class.prepend(NewGame)
    SaveData.singleton_class.prepend(SaveValues)
    @installed = true
  end
end
