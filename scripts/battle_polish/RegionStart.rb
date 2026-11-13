# Regional starting point for NEW GAME only.
# Older saves and the native Decades introduction are never rewritten.
module BlueRegionStart
  MARKER = "Data/blue-kanto-start.txt".freeze
  JOHTO_MARKER = "Data/blue-johto-start.txt".freeze
  JOHTO_INSTALL = "Data/blue-johto-install.json".freeze
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

  # Read-only guard for a future audited Johto installation. Neither file
  # exists in the current game, so Decades/Kanto behavior stays unchanged.
  # An isolated Johto pilot must provide the same two markers inside its COPY.
  def self.johto_spawn
    return nil unless File.file?(JOHTO_MARKER) && File.file?(JOHTO_INSTALL)
    fields = File.read(JOHTO_MARKER).strip.split(",")
    return nil unless fields.length == 5 && fields[0] == "BLUE_JOHTO_START_V1" &&
                      fields[1] == "JOHTO"
    values = fields[2, 3].map { |part| Integer(part, 10) rescue nil }
    return nil unless values.all? { |part| part.is_a?(Integer) }
    map_id, x, y = values
    return nil unless map_id >= 600 && map_id <= 999 && x >= 0 && y >= 0
    return nil unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map_id))
    [map_id, x, y]
  rescue IOError, SystemCallError, ArgumentError
    nil
  end

  def self.playable?(region)
    region == "DECADES" ||
      (region == "KANTO" && !kanto_spawn.nil?) ||
      (region == "JOHTO" && !johto_spawn.nil?)
  end

  def self.choose_initial
    return "KANTO" if File.file?("Kanto pilot.json") && kanto_spawn
    return "JOHTO" if File.file?("Johto pilot.json") && johto_spawn
    "DECADES"
  end

  def self.story_spawn
    return nil unless $game_temp&.begun_new_game && $game_map.map_id == $data_system.start_map_id
    return nil unless BlueRegions.snapshot&.fetch("initial", nil) == "DECADES"

    destinations = {"Decades" => nil}
    kanto = kanto_spawn
    johto = johto_spawn
    destinations["Kanto"] = ["KANTO", kanto] if kanto
    destinations["Johto"] = ["JOHTO", johto] if johto
    return nil if destinations.length == 1

    choice = pbMessage(_INTL("Em qual região você quer começar o Modo História?"),
                       destinations.keys, 1)
    return nil unless choice && choice >= 0
    destinations.values[choice]
  end

  def self.prepare_regional_story(region)
    $PokemonGlobal.blue_regions = BlueRegions.new_state(region)
    BlueStory.choose_mode(:story)
    BlueCampaign.begin_journey(false)
    $PokemonGlobal.blue_traditional_starters = true
    $PokemonGlobal.blue_campaign_departure = false
  end

  def self.enter_story_region(region, spawn)
    prepare_regional_story(region)
    pbFadeOutIn do
      $game_screen.pictures[1].erase
      pbToneChangeAll(Tone.new(0, 0, 0, 0), 0)
      $game_player.transparent = false
      $game_player.refresh_charset
      BlueRegionTravel.move_to([*spawn, 2])
    end
  end

  def self.select_and_prepare
    return unless @new_game && $PokemonGlobal
    # Called only AFTER the native SaveData new-game initialization, and BEFORE
    # the native map factory chooses the starting map.
    region = choose_initial
    spawn = case region
            when "KANTO" then kanto_spawn
            when "JOHTO" then johto_spawn
            end
    region = "DECADES" unless region == "DECADES" || spawn
    if region == "DECADES"
      $PokemonGlobal.blue_regions = BlueRegions.new_state(region)
      return
    end

    prepare_regional_story(region)
    if region == "KANTO" && File.file?("Kanto pilot.json")
      pbChangePlayer(1)
      $game_player.refresh_charset
      $PokemonGlobal.blue_regions["pilot_profile_pending"] = true
    end
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
