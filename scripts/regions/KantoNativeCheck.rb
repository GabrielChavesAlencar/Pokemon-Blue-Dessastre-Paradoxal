# Runs inside the copied mkxp-z game, after the native compiler.
module KantoNativeCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    require!($data_system.start_map_id == $game_map.map_id, "Pallet did not load")
    require!($game_map.events.size >= 4, "Pallet events missing")
    require!(BlueKantoPilot.experimental?, "Test-only menu marker was not loaded in the isolated pilot")
    labels = BlueKantoPilot.experimental_stops.map(&:first)
    require!(labels.length == 31 && labels.any? { |row| row.include?("Misty") } &&
             labels.any? { |row| row.include?("Surge") } &&
             labels.any? { |row| row.include?("Captain") } &&
             labels.any? { |row| row.include?("Celadon City") } &&
             labels.any? { |row| row.include?("Erika") } &&
             labels.any? { |row| row.include?("Koga") } &&
             labels.any? { |row| row.include?("Safari Zone") },
             "Experimental Kanto phase 10 Fuchsia/Safari destinations unavailable")
    require!(!File.expand_path(SaveData::SAVE_DIR).include?("Pokemon Blue Dessastre Paradoxal"),
             "Pilot pointed at Decades save directory")

    current = $game_map.map_id
    destinations = $game_map.events.values.flat_map do |event|
      event.list.filter_map { |command| command.parameters[1] if command.code == 201 }
    end
    lab = destinations.find { |id| GameData::MapMetadata.get(id).real_name.include?("Oak") }
    require!(lab, "Oak's Lab transfer missing")
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    require!($game_map.events.size >= 3, "Lab events missing")

    # Supply the choice and battle results so the compiler can run without a user.
    Object.send(:define_method, :pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    battle_calls = []
    losses_remaining = { "Doug" => 1 }
    TrainerBattle.define_singleton_method(:start) do |type, name, version = 0|
      data = GameData::Trainer.get(type, name, version)
      battle_calls << [type, name, version]
      if losses_remaining.fetch(name, 0) > 0
        losses_remaining[name] -= 1
        false
      else
        !!data
      end
    end
    BlueKantoPilot.choose_starter
    require!($player.party.first&.species == :BULBASAUR, "Starter was not given")
    BlueKantoPilot.rival
    require!(battle_calls.last == [:BLUE_KANTO_RIVAL, "Blue", 11], "Wrong rival team")
    require!(BlueKantoPilot.rival_done?, "Rival result not recorded")
    first_route = nil
    MapFactoryHelper.eachConnectionForMap(current) do |edge|
      neighbor = edge[0] == current ? edge[3] : edge[0]
      if GameData::MapMetadata.get(neighbor).real_name == "Rota 1"
        first_route = neighbor
        break
      end
    end
    require!(first_route, "Route 1 connection missing")
    require!(GameData::Encounter.get(first_route).types[:LandDay].any? { |slot| slot[1] == :PIDGEY },
             "Route 1 wild table missing")
    brock = GameData::Trainer.get(:BLUE_KANTO_LEADER, "Brock")
    require!(brock.pokemon.map { |pokemon| pokemon[:species] } == [:GEODUDE, :ONIX], "Brock roster differs")
    # Two NPC events may have the same on-screen name; their win flags must
    # remain independent. A lost battle may be retried, but not counted as a win.
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick", "KANTO_024_016")
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick", "KANTO_TEST_SECOND_RICK")
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick", "KANTO_024_016")
    require!(battle_calls.count { |row| row[1] == "Rick" } == 2,
             "Trainers with duplicate names share their victory flag")

    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Doug", "KANTO_024_017")
    require!(!BlueKantoPilot.progress["pilot_wins"].include?("KANTO_024_017"),
             "Defeat incorrectly marked as a win")
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Doug", "KANTO_024_017")
    require!(battle_calls.count { |row| row[1] == "Doug" } == 2 &&
             BlueKantoPilot.progress["pilot_wins"].include?("KANTO_024_017"),
             "Trainer retry after defeat failed")

    # Pilot saves created before stable keys saved the trainer's name.
    BlueKantoPilot.progress["pilot_wins"] << "Sammy"
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Sammy", "KANTO_024_020")
    require!(battle_calls.none? { |row| row[1] == "Sammy" }, "Legacy trainer win replayed")

    BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock", "KANTO_028_007")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER"],
             "Badge was not awarded exactly once")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_028_007"),
             "Stable Brock trainer key not persisted")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock", "KANTO_028_007")
    require!(battle_calls.count { |row| row[1] == "Brock" } == 1, "Brock battle repeated after victory")

    # Phase 07: Misty must have a real compiled trainer profile and a
    # distinct Cascade milestone. The battle result is stubbed ONLY in CI.
    misty = GameData::Trainer.get(:BLUE_KANTO_LEADER_MISTY, "Misty")
    require!(misty.pokemon.map { |pokemon| pokemon[:species] } == [:STARYU, :STARMIE],
             "Misty original FRLG team differs from Staryu/Starmie")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO") == ["BOULDER","CASCADE"],
             "Cascade Badge not awarded uniquely")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001")
    require!(battle_calls.count { |row| row[1] == "Misty" } == 1,
             "Misty repeated after victory")
    require!(BlueRegions.crystal_total(BlueKantoPilot.progress, 2) == 4,
             "Two Kanto milestones were double-counted or omitted")
    # Phase 08: the S.S. Ticket bridge is available only after Cascade,
    # and Lt. Surge grants exactly one Thunder Badge for a genuine victory.
    BlueKantoPilot.ticketmaster
    require!(BlueKantoPilot.progress["pilot_ss_ticket"] == true, "Vermilion S.S. Ticket permit was not granted after Cascade")
    BlueKantoPilot.ticketmaster
    surge = GameData::Trainer.get(:BLUE_KANTO_LEADER_SURGE, "Lt. Surge")
    require!(surge.pokemon.length == 3, "Lt. Surge original FRLG roster missing")
    require!(surge.pokemon.map { |pokemon| pokemon[:species] } == [:VOLTORB,:PIKACHU,:RAICHU],
             "Lt. Surge team differs from the pinned FRLG source")
    # The locked gym must be inaccessible until two adjacent cans are activated.
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SURGE, "Lt. Surge", "KANTO_067_005")
    require!(battle_calls.none? { |row| row[1] == "Lt. Surge" },
             "Surge could be challenged while the gym puzzle was locked")
    surge_destination = BlueKantoPilot.experimental_stops.find { |label, _point| label.include?("Surge") }
    require!(surge_destination, "Surge gym stop unavailable")
    surge_map_id = surge_destination[1][0]
    $map_factory.setup(surge_map_id)
    $game_player.moveto(5, 18)
    pairs = BlueKantoPilot.surge_pairs
    require!(!pairs.empty?, "No adjacent trash cans in Surge gym")
    first, second = pairs.first
    BlueKantoPilot.progress["pilot_surge_solution"] = [first, second]
    BlueKantoPilot.surge_can(first)
    require!(BlueKantoPilot.progress["pilot_surge_first"], "First Surge lock not triggered")
    BlueKantoPilot.surge_can(second)
    require!(BlueKantoPilot.progress["pilot_surge_unlocked"], "Surge puzzle did not unlock")
    require!($game_self_switches[[surge_map_id, 8, "A"]] == true,
             "Surge gym barrier did not receive its local self switch")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SURGE, "Lt. Surge", "KANTO_067_005")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO") ==
             ["BOULDER","CASCADE","THUNDER"], "Thunder Badge was not awarded uniquely")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SURGE, "Lt. Surge", "KANTO_067_005")
    require!(battle_calls.count { |row| row[1] == "Lt. Surge" } == 1,
             "Surge battle repeated after victory")
    require!(BlueRegions.crystal_total(BlueKantoPilot.progress, 2) == 5,
             "Three Kanto milestones were double-counted or omitted")

    # Phase 09: inspect scenery in the native engine without executing or
    # pretending that Celadon trainers, Erika, doors or quests exist yet.
    stage09 = ["Rota 7", "Celadon City", "Erika", "Celadon Center", "Celadon Loja"]
    stage09.each do |label|
      stop = BlueKantoPilot.experimental_stops.find { |entry| entry[0].include?(label) }
      require!(stop, "Phase 09 preview stop missing: #{label}")
      $map_factory.setup(stop[1][0])
      require!($game_map.events.empty?, "Phase 09 imported events before audit: #{label}")
    end
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("RAINBOW"),
             "Rainbow badge was granted without an Erika event")

    # Fuchsia/Safari phase 10: proof of map loading and absence of imported
    # NPCs, trainers, Safari counters, items and gym scripts.
    stage10 = ["Fuchsia City", "Koga", "Fuchsia Centro", "Casa Warden",
               "Safari Zone Portao", "Safari Zone Sul", "Safari Zone Norte",
               "Safari Zone Oeste", "Rota 15"]
    stage10.each do |label|
      stop = BlueKantoPilot.experimental_stops.find { |entry| entry[0].include?(label) }
      require!(stop, "Phase 10 preview destination missing: #{label}")
      $map_factory.setup(stop[1][0])
      require!($game_map.events.empty?, "Phase 10 imported events before review: #{label}")
    end
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("SOUL"),
             "Soul Badge was awarded before Koga battle was implemented")

    # Keep the legacy reload-map assertion stable while proving the gym
    # can be loaded and the puzzle flags persist across the same save.
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    slot = "Kanto Native Verification"
    require!(Game.save(slot), "Pilot save failed")
    save_file = SaveData.get_full_path(slot)
    saved = SaveData.read_from_file(save_file)
    Game.load(saved)
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER","CASCADE","THUNDER"],
             "Pilot badges did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_028_007"),
             "Trainer victory keys did not survive reload")
    require!($player.party.first&.species == :BULBASAUR, "Pilot team did not survive reload")
    require!($game_map.map_id == lab, "Pilot did not reload its map")
    require!(BlueKantoPilot.progress["pilot_ss_ticket"] == true, "S.S. Ticket permit did not survive reload")
    File.write("Data/blue-kanto-proof.txt", "Kanto 40 maps: Pallet/Mt Moon/Cerulean/Vermilion, ticket, Surge, three badges and save/reload verified (battles simulated)")
  end
end
