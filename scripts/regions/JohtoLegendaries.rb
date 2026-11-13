# Johto phase 14/16: legendary story and optional postgame (future isolated pilot).
# Does NOT install maps, roamers, wild battles, items, travel or native switches.
module BlueJohtoLegendaries
  REGION = "JOHTO".freeze
  VERSIONS = %w[HEARTGOLD SOULSILVER CRYSTAL].freeze
  BEASTS = [:RAIKOU, :ENTEI].freeze
  ISLAND_ENTRANCES = %w[NW NE SW SE].freeze
  RUINS_PUZZLES = [0, 1, 2, 3].freeze
  KIMONO_TRAINER = :BLUE_JOHTO_KIMONO_GIRL
  ROAMER_READY = "Data/blue-johto-roaming-ready.txt".freeze
  ROAMER_TOKEN = "BLUE_JOHTO_ROAMING_V1_READY".freeze
  VERSION_READY = "Data/blue-johto-version-ready.txt".freeze
  VERSION_TOKEN = "BLUE_JOHTO_VERSION_V1_READY".freeze
  BELL_READY = "Data/blue-johto-bell-tower-ready.txt".freeze
  BELL_TOKEN = "BLUE_JOHTO_BELL_TOWER_V1_READY".freeze
  WHIRL_READY = "Data/blue-johto-whirl-islands-ready.txt".freeze
  WHIRL_TOKEN = "BLUE_JOHTO_WHIRL_ISLANDS_V1_READY".freeze
  SAFE_EXIT_READY = "Data/blue-johto-legendary-exits-ready.txt".freeze
  SAFE_EXIT_TOKEN = "BLUE_JOHTO_LEGENDARY_EXITS_V1_READY".freeze
  KIMONO_READY = "Data/blue-johto-kimono-ready.txt".freeze
  KIMONO_TOKEN = "BLUE_JOHTO_KIMONO_V1_READY".freeze
  ITEM_READY = "Data/blue-johto-legendary-items-ready.txt".freeze
  ITEM_TOKEN = "BLUE_JOHTO_LEGENDARY_ITEMS_V1_READY".freeze
  ENCOUNTER_READY = "Data/blue-johto-legendary-battles-ready.txt".freeze
  ENCOUNTER_TOKEN = "BLUE_JOHTO_LEGENDARY_BATTLES_V1_READY".freeze
  RUINS_READY = "Data/blue-johto-ruins-ready.txt".freeze
  RUINS_TOKEN = "BLUE_JOHTO_RUINS_V1_READY".freeze
  EUSINE_READY = "Data/blue-johto-eusine-ready.txt".freeze
  EUSINE_TOKEN = "BLUE_JOHTO_EUSINE_V1_READY".freeze

  # Provisional Essentials item IDs; these are NOT proof of item availability.
  WINGS = {"HEARTGOLD"=>:RAINBOWWING, "SOULSILVER"=>:SILVERWING}.freeze
  BELLS = {"HEARTGOLD"=>:CLEARBELL, "SOULSILVER"=>:TIDALBELL}.freeze
  PRIMARY = {"HEARTGOLD"=>:HOOH, "SOULSILVER"=>:LUGIA}.freeze
  SECONDARY_WINGS = {:HOOH=>:RAINBOWWING, :LUGIA=>:SILVERWING}.freeze

  def self.record
    return nil unless defined?(BlueJohtoPilot)
    BlueJohtoPilot.regional_state
  end

  def self.progress
    return nil unless record
    BlueJohtoPilot.progress
  end

  def self.marker?(path, token)
    File.file?(path) && File.read(path).strip == token
  rescue IOError, SystemCallError
    false
  end

  def self.version
    flags = progress
    return nil unless flags
    value = flags["johto_campaign_version"]
    VERSIONS.include?(value) ? value : nil
  end

  # Can only be called once by a verified NEW GAME configuration event.
  # Do not silently default to HGSS or switch an existing save to Crystal.
  def self.choose_version(value)
    flags = progress
    return false unless flags && VERSIONS.include?(value)
    return false if flags.key?("johto_campaign_version")
    return false unless marker?(VERSION_READY, VERSION_TOKEN)
    flags["johto_campaign_version"] = value
    true
  end

  def self.league_cleared?
    state = record
    state && state["leagues"].is_a?(Array) && state["leagues"].include?(REGION)
  end

  def self.eight_badges?
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.allow_specials?(state, REGION) == true
  end

  def self.field_allowed?(action, tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, action, tool_ready) == :allowed
  end

  def self.species_ready?(species)
    defined?(GameData::Species) && GameData::Species.respond_to?(:exists?) &&
      GameData::Species.exists?(species)
  end

  def self.item_in_bag?(item)
    return false unless item && defined?(GameData::Item) &&
                        GameData::Item.respond_to?(:exists?) &&
                        GameData::Item.exists?(item) && defined?($bag) && $bag &&
                        $bag.respond_to?(:quantity)
    quantity = $bag.quantity(item)
    quantity.is_a?(Numeric) && quantity > 0
  end

  def self.give_item_once(item, flag)
    flags = progress
    return false unless flags && item && !flags[flag]
    return false unless marker?(ITEM_READY, ITEM_TOKEN) &&
                        defined?(GameData::Item) &&
                        GameData::Item.respond_to?(:exists?) &&
                        GameData::Item.exists?(item) && defined?(pbReceiveItem)
    return false unless pbReceiveItem(item) == true
    flags[flag] = true
    true
  end

  # The Burned Tower release already exists as a PHASE 08 story flag.
  # The actual roaming engine must register each species before passing
  # :registered, including route routing and encounter persistence.
  def self.register_roamer(species, result)
    flags = progress
    return false unless flags && version && BEASTS.include?(species) &&
                        flags["burned_tower_beasts_awakened"] == true &&
                        marker?(ROAMER_READY, ROAMER_TOKEN) &&
                        species_ready?(species) && result == :registered
    roamers = flags["johto_roamers"] ||= {}
    return false unless roamers.is_a?(Hash)
    return false if roamers.key?(species.to_s)
    roamers[species.to_s] = "roaming"
    true
  end

  def self.roamer_result(species, result)
    flags = progress
    return false unless flags && version && BEASTS.include?(species) &&
                        marker?(ROAMER_READY, ROAMER_TOKEN)
    roamers = flags["johto_roamers"]
    return false unless roamers.is_a?(Hash) &&
                        roamers[species.to_s] == "roaming"
    return false if result == :fled || result == :lost
    next_state = {:caught=>"caught", :defeated=>"awaiting_verified_rematch"}[result]
    return false unless next_state
    roamers[species.to_s] = next_state
    true
  end

  # The genuine next-Hall-of-Fame event must be audited before resetting
  # defeated roaming beasts; this never revives one already captured.
  def self.reactivate_roamer(species, outcome)
    flags = progress
    return false unless flags && BEASTS.include?(species) && league_cleared? &&
                        marker?(ROAMER_READY, ROAMER_TOKEN)
    roamers = flags["johto_roamers"]
    return false unless roamers.is_a?(Hash) &&
                        roamers[species.to_s] == "awaiting_verified_rematch" &&
                        outcome == :rematch_recorded
    roamers[species.to_s] = "roaming"
    true
  end

  # Radio Tower wing reward. In Crystal no wing/event is inferred.
  def self.radio_wing_reward
    flags = progress
    v = version
    return false unless flags && WINGS.key?(v) &&
                        flags["goldenrod_radio_tower_cleared"] == true
    give_item_once(WINGS[v], "johto_radio_wing_received")
  end

  # Five sequential scripted Kimono Girl fights. They must be compiled in PBS.
  def self.kimono_girl(index)
    flags = progress
    return false unless flags && WINGS.key?(version) && eight_badges? &&
                        flags["goldenrod_radio_tower_cleared"] == true &&
                        flags["johto_radio_wing_received"] == true &&
                        index.is_a?(Integer) && (0..4).include?(index)
    return false unless marker?(KIMONO_READY, KIMONO_TOKEN) &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    return false unless (flags["johto_kimono_step"] || 0) == index
    return false unless TrainerBattle.start(KIMONO_TRAINER, "Kimono Girl", index) == true
    flags["johto_kimono_step"] = index + 1
    true
  end

  def self.kimono_bell_reward
    flags = progress
    v = version
    return false unless flags && BELLS.key?(v) &&
                        flags["johto_kimono_step"] == 5
    give_item_once(BELLS[v], "johto_kimono_bell_received")
  end

  def self.kimono_ritual
    flags = progress
    return false unless flags && WINGS.key?(version) &&
                        flags["johto_kimono_bell_received"] == true &&
                        flags["johto_kimono_step"] == 5 &&
                        item_in_bag?(WINGS[version]) && item_in_bag?(BELLS[version]) &&
                        marker?(KIMONO_READY, KIMONO_TOKEN)
    return false if flags["johto_kimono_ritual_done"]
    flags["johto_kimono_ritual_done"] = true
    true
  end

  # A chosen real cave entrance must have complete, verified return warps.
  # The Phase 10 Whirl Islands gate is deliberately disabled until a future
  # physical installer binds these audited Phase 14 handlers.
  def self.whirl_entrance(entrance, surf_tool = false, whirl_tool = false)
    flags = progress
    return false unless flags && version && ISLAND_ENTRANCES.include?(entrance) &&
                        flags["route41_visited"] == true &&
                        flags["rocket_hq_whirlpool_received"] == true &&
                        field_allowed?("SURF", surf_tool) &&
                        field_allowed?("WHIRLPOOL", whirl_tool) &&
                        marker?(WHIRL_READY, WHIRL_TOKEN) &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    return false if flags["johto_whirl_entrance"]
    flags["johto_whirl_entrance"] = entrance
    true
  end

  def self.whirl_chamber
    flags = progress
    return false unless flags && flags["johto_whirl_entrance"] &&
                        marker?(WHIRL_READY, WHIRL_TOKEN) &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    return false if flags["johto_whirl_chamber"]
    flags["johto_whirl_chamber"] = true
    true
  end

  # The future map exit event must confirm a genuine, safe return before
  # allowing another island entrance. This clears travel checkpoints only,
  # never the Lugia outcome or any captured Pokemon.
  def self.whirl_exit
    flags = progress
    return false unless flags && flags["johto_whirl_entrance"] &&
                        marker?(WHIRL_READY, WHIRL_TOKEN) &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    flags.delete("johto_whirl_entrance")
    flags.delete("johto_whirl_chamber")
    true
  end

  def self.bell_tower_enter
    flags = progress
    return false unless flags && version &&
                        flags["ecruteak_visited"] == true &&
                        flags["burned_tower_beasts_awakened"] == true &&
                        marker?(BELL_READY, BELL_TOKEN) &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    return false if flags["johto_bell_tower_entered"]
    flags["johto_bell_tower_entered"] = true
    true
  end

  def self.bell_tower_roof
    flags = progress
    return false unless flags && flags["johto_bell_tower_entered"] &&
                        marker?(BELL_READY, BELL_TOKEN) &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    return false if flags["johto_bell_roof_reached"]
    flags["johto_bell_roof_reached"] = true
    true
  end

  # Version-specific main mascot; secondary mascot is post-Hall-of-Fame.
  # Crystal's divergent legendary flow is intentionally NOT mapped here.
  def self.legendary_begin(species)
    flags = progress
    v = version
    return false unless flags && PRIMARY.key?(v) &&
                        [:HOOH, :LUGIA].include?(species) &&
                        species_ready?(species) &&
                        marker?(ENCOUNTER_READY, ENCOUNTER_TOKEN)
    results = flags["johto_legendary_results"] || {}
    return false unless results.is_a?(Hash)
    return false if results.key?(species.to_s) || flags["johto_legendary_pending"]
    main = PRIMARY[v] == species
    return false unless eight_badges?
    if main
      return false unless flags["johto_kimono_ritual_done"] &&
                          item_in_bag?(WINGS[v]) && item_in_bag?(BELLS[v])
    else
      return false unless league_cleared? &&
                          item_in_bag?(SECONDARY_WINGS[species])
    end
    room_ok = species == :HOOH ? flags["johto_bell_roof_reached"] :
                                 flags["johto_whirl_chamber"]
    return false unless room_ok == true &&
                        marker?(SAFE_EXIT_READY, SAFE_EXIT_TOKEN)
    flags["johto_legendary_pending"] = species.to_s
    true
  end

  # Only the verified battle callback may pass :caught/:defeated. Flee or
  # blackout leaves the legendary retryable; the script never adds a Pokemon.
  def self.legendary_result(species, outcome)
    flags = progress
    return false unless flags && version &&
                        flags["johto_legendary_pending"] == species.to_s &&
                        marker?(ENCOUNTER_READY, ENCOUNTER_TOKEN)
    flags.delete("johto_legendary_pending")
    return false unless [:caught, :defeated].include?(outcome)
    existing = flags["johto_legendary_results"]
    return false if existing && !existing.is_a?(Hash)
    (flags["johto_legendary_results"] ||= {})[species.to_s] =
      outcome == :caught ? "caught" : "awaiting_verified_rematch"
    true
  end

  # An actual subsequent Hall of Fame must confirm this event; no repeated
  # catch of an already captured species.
  def self.legendary_rematch_reset(species, outcome)
    flags = progress
    results = flags && flags["johto_legendary_results"]
    return false unless [:HOOH, :LUGIA].include?(species) &&
                        PRIMARY.key?(version) &&
                        results.is_a?(Hash) && league_cleared? &&
                        outcome == :rematch_recorded &&
                        results[species.to_s] == "awaiting_verified_rematch" &&
                        marker?(ENCOUNTER_READY, ENCOUNTER_TOKEN)
    results.delete(species.to_s)
    true
  end

  # HGSS Suicune continues into Kanto Route 25; travelling there from
  # Johto is not supported by the native adapter yet. Do not invent an event.
  def self.hgss_suicune_route25
    return false unless record
    false
  end

  # Crystal uses a different Suicune/Eusine/Tin Tower story. A future
  # independent implementation needs actual flags, Clear Bell and map data.
  def self.crystal_suicune
    return false unless record && version == "CRYSTAL"
    false
  end

  # Ruins of Alph logical puzzle ledger; does not install tile arrangements,
  # Chambers, Unown forms/encounter slots, radio channels or puzzle prizes.
  def self.ruins_enter
    flags = progress
    return false unless flags && version &&
                        marker?(RUINS_READY, RUINS_TOKEN)
    return false if flags["johto_ruins_entered"]
    flags["johto_ruins_entered"] = true
    true
  end

  def self.ruins_puzzle(index)
    flags = progress
    return false unless flags && flags["johto_ruins_entered"] &&
                        index.is_a?(Integer) && RUINS_PUZZLES.include?(index) &&
                        marker?(RUINS_READY, RUINS_TOKEN)
    solved = flags["johto_ruins_puzzles"] || []
    return false unless solved.is_a?(Array) && !solved.include?(index)
    (flags["johto_ruins_puzzles"] ||= []) << index
    true
  end

  def self.unown_research_ready?
    flags = progress
    solved = flags && flags["johto_ruins_puzzles"]
    solved.is_a?(Array) && !solved.empty?
  end

  # Optional minigames, Kanto Route 25, Mt. Silver and Red require real maps,
  # trainers, assets and policy checks; no fake completion/unlock possible.
  def self.bug_contest
    false
  end
  def self.pokeathlon
    false
  end
  def self.mt_silver
    false
  end
  def self.red_battle
    false
  end
end
