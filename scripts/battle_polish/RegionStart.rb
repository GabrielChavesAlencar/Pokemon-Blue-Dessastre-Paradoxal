# Regional starting point for NEW GAME only.
# Older saves and the native Decades introduction are never rewritten.
module BlueRegionStart
  MARKER = "Data/blue-kanto-start.txt".freeze
  JOHTO_MARKER = "Data/blue-johto-start.txt".freeze
  JOHTO_INSTALL = "Data/blue-johto-install.json".freeze
  KANTO_INSTALL = "Data/blue-kanto-install.json".freeze
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

  # The installed package is also summarized in a tiny ASCII marker,
  # committed only after all map/PBS hashes pass. Ruby in some embedded mkxp
  # builds omits the JSON gem; this fallback still rejects stray map markers.
  def self.kanto_ready_gate?(spawn)
    path = "Data/blue-kanto-ready.txt"
    return false unless spawn && File.file?(path) && !File.symlink?(path)
    fields = File.read(path, 128).strip.split(",")
    fields == ["BLUE_KANTO_READY_V1", "142", spawn[0].to_s]
  rescue StandardError
    false
  end

  # Kanto must be genuinely merged into the MAIN installation before its
  # New Game option can start within the Decades executable. A standalone
  # "Kanto pilot.json" or a stray start marker is never sufficient.
  def self.kanto_integrated?
    return false if File.file?("Kanto pilot.json") || File.file?("Johto pilot.json") ||
                    File.file?("Hoenn pilot.json") || File.file?("Sinnoh pilot.json")
    spawn = kanto_spawn
    return false unless spawn && File.file?(KANTO_INSTALL) && !File.symlink?(KANTO_INSTALL)
    required = [
      "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
      "PBS/encounters_kanto.txt", "PBS/trainers_kanto.txt",
      "PBS/trainer_types_kanto.txt", "PBS/map_metadata_kanto.txt",
      "PBS/map_connections_kanto.txt",
      "Data/blue-kanto-locale.dat", "Data/blue-kanto-npc-dialogues.dat",
      "Data/blue-kanto-pewter-route3-gate.txt",
      "Data/blue-kanto-pewter-mom-sprite.txt",
      "Data/blue-kanto-viridian-route2-line.txt",
      "Data/blue-kanto-silph-floors.txt",
      "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
    ]
    return false unless required.all? { |name| File.file?(name) }
    begin
      require "json" unless defined?(JSON)
    rescue LoadError
      return kanto_ready_gate?(spawn)
    end
    info = JSON.parse(File.read(KANTO_INSTALL))
    return false unless info.is_a?(Hash) && info["schema"] == 1 &&
                        info["source"] == "Essentials FRLG 21.1" &&
                        info["maps"].is_a?(Hash) && info["maps"].length >= 142
    maps = info["maps"]
    return false unless maps["7"] == spawn[0] && maps["5"].is_a?(Integer) &&
                        maps.values.uniq.length == maps.length &&
                        pbRgssExists?(sprintf("Data/Map%03d.rxdata", maps["5"]))
    true
  rescue StandardError
    false
  end

  # This is an in-memory request, not a save flag: the game only commits the
  # chosen starting region after the native new-game values are initialized.
  def self.request_initial(region)
    return false unless ["DECADES", "KANTO"].include?(region)
    return false if region == "KANTO" && !kanto_integrated?
    @requested_initial = region
    @title_region_chosen = true
    true
  end

  def self.playable?(region)
    region == "DECADES" ||
      (region == "KANTO" && !kanto_spawn.nil?) ||
      (region == "JOHTO" && !johto_spawn.nil?)
  end

  def self.choose_initial
    return "KANTO" if File.file?("Kanto pilot.json") && kanto_spawn
    return "JOHTO" if File.file?("Johto pilot.json") && johto_spawn
    return "KANTO" if @requested_initial == "KANTO" && kanto_integrated?
    "DECADES"
  end

  def self.story_spawn
    # The title screen already asked which region to start in. Never ask
    # again during the Decades Story Mode introduction.
    return nil if @title_region_chosen
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

  # Use the REAL Decades System.rxdata start coordinates, not a guessed
  # town or a copied FRLG location. Store only as a future destination,
  # unlocked by the authentic Kanto League event.
  def self.native_decades_start
    return nil unless $data_system
    point = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]
    return nil unless point.all? { |v| v.is_a?(Integer) } &&
                      point[0] > 0 && point[1] >= 0 && point[2] >= 0
    return nil unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", point[0]))
    point + [2]
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
      # New Game's REGION choice is the only setup menu. Keep Decades' native
      # intro/events and their story flags, but silently take the standard
      # character, Story Mode and traditional starters instead of reopening
      # its legacy character/mode/mechanics configuration screens.
      prepare_regional_story(region)
      $PokemonGlobal.blue_regions["decades_auto_intro"] = true
      $PokemonGlobal.blue_regions["decades_auto_starter_index"] = 0
      if $game_player && defined?(pbChangePlayer)
        pbChangePlayer(0)
        $game_player.transparent = false if $game_player.respond_to?(:transparent=)
        $game_player.refresh_charset if $game_player.respond_to?(:refresh_charset)
      end
      return
    end

    # A campaign started in ANY integrated region must be able to visit
    # Decades without winning a League. Capture its real native start while
    # System.rxdata still contains Decades coordinates. Isolated pilot copies
    # must never forge a shared Decades destination.
    isolated = %w[Kanto Johto Hoenn Sinnoh].any? { |name| File.file?("#{name} pilot.json") }
    decades_start = native_decades_start unless isolated
    prepare_regional_story(region)
    $PokemonGlobal.blue_regions["decades_first_arrival"] = decades_start if decades_start
    if region == "KANTO"
      # Both integrated Kanto and the isolated pilot start walking. Mom gives
      # Running Shoes only after the authored Brock / Route 3 scene.
      # These changes affect only the newly created Kanto save.
      $player.has_running_shoes = false if $player && $player.respond_to?(:has_running_shoes=)
      if $game_player
        pbChangePlayer(1)
        $game_player.refresh_charset
      end
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
    @requested_initial = nil
  end

  # Only the first, genuine Decades New Game introduction is automated.
  # Loaded saves, Kanto/Johto profiles and inter-region arrival NPCs remain
  # untouched. The title screen REGION picker still belongs to the player.
  def self.decades_auto_intro?
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    state.is_a?(Hash) && state["initial"] == "DECADES" &&
      state["current"] == "DECADES" && state["decades_auto_intro"] &&
      $game_map && $data_system && $game_map.map_id == $data_system.start_map_id
  end

  def self.default_decades_intro_choice(labels)
    # Use original event choice indices, not reordered display indices:
    # RPG Maker's command_402 checks these indices to run the correct branch.
    preferred = [
      /\\A(?:Story Mode|Begin Story Mode|Modo Hist[oó]ria|Come[cç]ar Hist[oó]ria)\\z/i,
      /Traditional Starters|Iniciais Tradicionais/i,
      /Intended Soundtrack|Trilha Sonora Original/i,
      /Yes|Sim/i
    ]
    preferred.each do |pattern|
      index = labels.index { |text| text.to_s.match?(pattern) }
      return index if index
    end
    # A new game without manual setup uses its first affirmative option;
    # never choose Cancel/Back/No as an accidental default.
    labels.index { |text| text.to_s !~ /\\A(?:Cancel|Back|No|Voltar|N[aã]o)\\z/i } || 0
  end

  module DecadesAutoChoices
    def command_102
      if BlueRegionStart.decades_auto_intro? && @map_id == $data_system.start_map_id &&
         @parameters && @parameters[0].is_a?(Array) && !@parameters[0].empty?
        options = @parameters[0]
        choice = BlueRegionStart.default_decades_intro_choice(options)
        @branch ||= {}
        @branch[@list[@index].indent] = choice
        return true
      end
      super
    end
  end

  module DecadesAutoProfile
    def pbCharacterSelect(*args)
      return super unless BlueRegionStart.decades_auto_intro?
      pbChangePlayer(0)
      $game_player.transparent = false if $game_player.respond_to?(:transparent=)
      $game_player.refresh_charset if $game_player.respond_to?(:refresh_charset)
      true
    end

    def pbPokemonSelection(list, must_choose=true, settings=nil)
      return super unless BlueRegionStart.decades_auto_intro?
      # Preserve Decades' native event flow: it will add the returned Pokemon
      # normally. Choose conventional starters with no selection UI, once
      # per call, rather than placing fabricated Pokemon directly in storage.
      return super unless list.to_s.match?(/\\A(?:Traditional_Starters|All_Starters)\\z/i)
      state = $PokemonGlobal.blue_regions
      roster = [:BULBASAUR, :CHARMANDER, :SQUIRTLE]
      index = state["decades_auto_starter_index"].to_i
      species = roster[index % roster.length]
      return super unless defined?(GameData::Species) &&
                          GameData::Species.exists?(species) && defined?(Pokemon)
      pokemon = Pokemon.new(species, 5, $player)
      state["decades_auto_starter_index"] = index + 1
      pokemon
    end
  end

  module DecadesIntroExit
    def setup(*args)
      result = super
      state = $PokemonGlobal && $PokemonGlobal.blue_regions
      if state.is_a?(Hash) && state["decades_auto_intro"] && $data_system &&
         map_id != $data_system.start_map_id
        state.delete("decades_auto_intro")
        state.delete("decades_auto_starter_index")
      end
      result
    end
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
    Interpreter.prepend(DecadesAutoChoices) if defined?(Interpreter) &&
      !Interpreter.ancestors.include?(DecadesAutoChoices)
    Object.prepend(DecadesAutoProfile) unless Object.ancestors.include?(DecadesAutoProfile)
    Game_Map.prepend(DecadesIntroExit) if defined?(Game_Map) &&
      !Game_Map.ancestors.include?(DecadesIntroExit)
    @installed = true
  end
end
