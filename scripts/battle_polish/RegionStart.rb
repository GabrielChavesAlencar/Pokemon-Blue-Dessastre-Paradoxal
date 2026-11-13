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

  # Shared read-only release proof for the future ISOLATED Johto pilot.
  # Arbitrary "{}" or a lone start marker is NOT a valid install. The hashes
  # bind the proof to real deployed map metadata and two audited map files.
  # Neither this method nor phase 16 produces a release proof automatically.
  JOHTO_PROOFS = %w[
    source_rights maps_and_warps sprites_and_tilesets story_events
    trainers_pbs battles_and_encounters native_save_reload hms_and_badges
    region_travel_and_box audio_rights_and_playback kanto_decades_regression
    windows_gameplay joiplay_gameplay
  ].freeze
  def self.johto_install_proof
    return nil unless File.file?(JOHTO_INSTALL) && !File.symlink?(JOHTO_INSTALL)
    # A ausência das bibliotecas JSON/Digest no runtime minimalista não pode
    # impedir o menu e os mapas de Kanto/Decades de abrir. O gate de Johto
    # permanece fechado quando não puder validar a prova completa.
    begin
      require "json" unless defined?(JSON)
      require "digest" unless defined?(Digest::SHA256)
    rescue LoadError
      return nil
    end
    data = JSON.parse(File.read(JOHTO_INSTALL))
    return nil unless data.is_a?(Hash) && data["schema"] == 1 &&
                      data["region"] == "JOHTO" &&
                      data["status"] == "VERIFIED_PLAYABLE" &&
                      data["source_archive_sha256"].is_a?(String) &&
                      data["source_archive_sha256"].match?(/\A[a-f0-9]{64}\z/)
    checks = data["checks"]
    return nil unless checks.is_a?(Hash) &&
                      JOHTO_PROOFS.all? { |key| checks[key] == true }
    points = [data["start"], data["travel_point"], data["npc_point"]]
    return nil unless points.all? do |point|
      point.is_a?(Array) && point.length == 4 &&
        point.all? { |v| v.is_a?(Integer) } &&
        (600..999).include?(point[0]) &&
        point[1] >= 0 && point[2] >= 0 &&
        [2,4,6,8].include?(point[3]) &&
        pbRgssExists?(sprintf("Data/Map%03d.rxdata", point[0]))
    end
    return nil unless data["travel_point"][0] == data["npc_point"][0] &&
                      data["travel_point"][1, 2] != data["npc_point"][1, 2] &&
                      (data["travel_point"][1] - data["npc_point"][1]).abs +
                      (data["travel_point"][2] - data["npc_point"][2]).abs <= 3
    files = data["file_hashes"]
    required = ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata"] +
               points.map { |point| sprintf("Data/Map%03d.rxdata", point[0]) }
    return nil unless files.is_a?(Hash) &&
                      required.all? { |name|
                        hash = files[name]
                        hash.is_a?(String) && hash.match?(/\A[a-f0-9]{64}\z/) &&
                          File.file?(name) && !File.symlink?(name) &&
                          Digest::SHA256.file(name).hexdigest == hash
                      }
    data
  rescue JSON::ParserError, IOError, SystemCallError, ArgumentError
    nil
  end

  def self.johto_spawn
    proof = johto_install_proof
    return nil unless proof && File.file?(JOHTO_MARKER) &&
                      !File.symlink?(JOHTO_MARKER)
    fields = File.read(JOHTO_MARKER).strip.split(",")
    return nil unless fields.length == 5 && fields[0] == "BLUE_JOHTO_START_V1" &&
                      fields[1] == "JOHTO"
    values = fields[2, 3].map { |part| Integer(part, 10) rescue nil }
    return nil unless values.all? { |part| part.is_a?(Integer) }
    map_id, x, y = values
    return nil unless [map_id, x, y, 2] == proof["start"]
    [map_id, x, y]
  rescue IOError, SystemCallError, ArgumentError
    nil
  end

  def self.johto_town_point
    proof = johto_install_proof
    return nil unless proof && johto_spawn
    proof["travel_point"]
  end

  def self.johto_agent_point
    proof = johto_install_proof
    return nil unless proof && johto_spawn
    proof["npc_point"]
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
