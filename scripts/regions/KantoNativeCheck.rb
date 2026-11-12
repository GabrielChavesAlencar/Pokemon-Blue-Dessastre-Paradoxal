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
    require!(labels.length == 41 && labels.any? { |row| row.include?("Misty") } &&
             labels.any? { |row| row.include?("Surge") } &&
             labels.any? { |row| row.include?("Captain") } &&
             labels.any? { |row| row.include?("Celadon City") } &&
             labels.any? { |row| row.include?("Erika") } &&
             labels.any? { |row| row.include?("Koga") } &&
             labels.any? { |row| row.include?("Safari Zone") } &&
             labels.any? { |row| row.include?("Sabrina") } &&
             labels.any? { |row| row.include?("Silph Co.") },
             "Experimental Kanto phase 11 Saffron/Silph destinations unavailable")
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
    losses_remaining = { "Doug" => 1, "Erika" => 1 }
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
    # Stage 03: the Pallet -> Viridian -> Pallet Oak parcel loop is local to
    # Kanto, delivered once, and never creates an invalid FRLG item in Decades.
    mart_visits = []
    Object.send(:define_method, :pbPokemonMart) do |stock|
      mart_visits << stock
      true
    end
    BlueKantoPilot.viridian_mart
    require!(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true,
             "Viridian Mart did not register Oak's parcel")
    require!(!BlueKantoPilot.progress["pilot_oak_parcel_delivered"],
             "Oak's parcel delivered without returning to the laboratory")
    BlueKantoPilot.viridian_mart
    require!(mart_visits.length == 2, "Oak parcel interaction disabled Mart shopping")
    BlueKantoPilot.choose_starter
    require!(BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak did not accept the parcel upon return")
    require!($player.has_pokedex, "Oak parcel delivery did not unlock the Pokedex") if $player.respond_to?(:has_pokedex)
    BlueKantoPilot.choose_starter
    BlueKantoPilot.viridian_mart
    require!(mart_visits.length == 3 &&
             BlueKantoPilot.progress["pilot_oak_parcel_delivered"],
             "Returning to Mart after delivery did not keep the shop available")
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

    # MAN-01: the two-way Rival's House doors use REAL map transfers.
    # MAN-02: Rick starts as a Sight(5) Event Touch trainer, and on a
    # recorded victory the same event switches to Action Button via A.
    metadata = File.read("Kanto pilot.json")
    pallet_id = metadata.match(/"5":\s*(\d+)/)[1].to_i
    house_id = metadata.match(/"8":\s*(\d+)/)[1].to_i
    forest_id = metadata.match(/"24":\s*(\d+)/)[1].to_i
    $map_factory.setup(pallet_id)
    require!($game_map.events[2].list.any? { |op|
      op.code == 201 && op.parameters[1] == house_id
    }, "Pallet rival house door was not connected")
    $map_factory.setup(house_id)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == pallet_id
    }, "Rival house return to Pallet was not connected")
    $map_factory.setup(forest_id)
    trainer_event = $game_map.events[16]
    require!(trainer_event.name.include?("Sight(5)") && trainer_event.trigger == 2,
             "Rick must automatically notice the player five tiles away")
    require!(!BlueKantoPilot.sync_trainer_event("KANTO_024_018", "Anthony", 18),
             "An undefeated trainer was incorrectly marked defeated")
    require!(!$game_self_switches[[forest_id, 18, "A"]],
             "A lost or unplayed trainer already has self-switch A")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_024_016", "Rick", 16),
             "Trainer victory was not applied to the source event")
    $game_map.refresh
    require!($game_self_switches[[forest_id, 16, "A"]] &&
             $game_map.events[16].trigger == 0,
             "Trainer must stop auto-challenging after victory")

    # Phase 09 core: City/Center/Gym now have only whitelisted gameplay
    # events. Route 7 and the entire department store remain geometry-only.
    ["Rota 7", "Celadon Loja"].each do |label|
      stop = BlueKantoPilot.experimental_stops.find { |row| row[0].include?(label) }
      require!(stop, "Celadon scenery preview stop missing: #{label}")
      $map_factory.setup(stop[1][0])
      require!($game_map.events.empty?, "Unreviewed preview events in #{label}")
    end
    map_for = proc do |label|
      stop = BlueKantoPilot.experimental_stops.find { |row| row[0].include?(label) }
      require!(stop, "Celadon core stop missing: #{label}")
      stop[1][0]
    end
    celadon_city = map_for.call("Celadon City")
    celadon_center = map_for.call("Celadon Center")
    celadon_gym = map_for.call("Erika")
    $map_factory.setup(celadon_city)
    require!($game_map.events.keys.sort == [3, 20] &&
             $game_map.events[3].trigger == 1 &&
             $game_map.events[20].trigger == 1,
             "Celadon city must contain only two walk-through core doors")
    require!($game_map.events[3].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_gym
    } && $game_map.events[20].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_center
    }, "Celadon city doors do not reach the audited destinations")
    $map_factory.setup(celadon_center)
    require!($game_map.events.keys.sort == [1, 2] &&
             $game_map.events[1].list.any? { |row|
               row.code == 201 && row.parameters[1] == celadon_city
             }, "Celadon Pokemon Center lacks its return exit")
    $map_factory.setup(celadon_gym)
    require!($game_map.events.keys.sort == [1, 5, 7, 42, 43, 44, 45, 46, 47],
             "Celadon Gym imported non-whitelisted events")
    require!($game_map.events[5].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_city
    }, "Celadon gym has no return to the city")
    require!($game_map.events[7].trigger == 2 && $game_map.events[1].trigger == 0,
             "Erika and the trainers have wrong trigger modes")
    erika = GameData::Trainer.get(:BLUE_KANTO_LEADER_ERIKA, "Erika")
    require!(erika.pokemon.map { |pkmn| [pkmn[:species], pkmn[:level]] } ==
             [[:VICTREEBEL,29],[:TANGELA,24],[:VILEPLUME,29]],
             "Erika's pinned FRLG team was not preserved")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("RAINBOW"),
             "Rainbow was awarded without defeating Erika")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_ERIKA, "Erika", "KANTO_124_001")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("RAINBOW"),
             "A loss against Erika incorrectly awarded Rainbow")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_ERIKA, "Erika", "KANTO_124_001")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") ==
             ["BOULDER", "CASCADE", "THUNDER", "RAINBOW"],
             "Erika victory did not award the unique Rainbow Badge")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_124_001", "Erika", 1),
             "Erika did not persist her defeated event state")
    $game_map.refresh
    require!($game_self_switches[[celadon_gym, 1, "A"]] &&
             $game_map.events[1].trigger == 0,
             "Erika remained a battle trigger after a registered victory")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_ERIKA, "Erika", "KANTO_124_001")
    require!(battle_calls.count { |row| row[1] == "Erika" } == 2,
             "Erika was challenged again after winning the Rainbow Badge")

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

    # Phase 11 Saffron: isolated terrain previews, no teleporter scripts,
    # Silph Rocket boss, Sabrina battles or Marsh Badge may be installed.
    stage11 = ["Rota 8", "Portaria Oeste Saffron", "Saffron City",
               "Sabrina", "Fighting Dojo", "Saffron Centro Pokemon",
               "Silph Co. 1F", "Silph Co. 5F", "Silph Co. 11F",
               "Silph Co. Elevador"]
    stage11.each do |label|
      stop = BlueKantoPilot.experimental_stops.find { |entry| entry[0].include?(label) }
      require!(stop, "Phase 11 preview destination missing: #{label}")
      $map_factory.setup(stop[1][0])
      require!($game_map.events.empty?, "Phase 11 unexpectedly imported an event: #{label}")
    end
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("MARSH"),
             "Marsh Badge awarded before Sabrina battle was implemented")

    # Keep the legacy reload-map assertion stable while proving the gym
    # can be loaded and the puzzle flags persist across the same save.
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    slot = "Kanto Native Verification"
    require!(Game.save(slot), "Pilot save failed")
    save_file = SaveData.get_full_path(slot)
    saved = SaveData.read_from_file(save_file)
    Game.load(saved)
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER","CASCADE","THUNDER","RAINBOW"],
             "Pilot badges did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_028_007"),
             "Trainer victory keys did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_124_001"),
             "Erika victory did not persist through save/reload")
    require!($player.party.first&.species == :BULBASAUR, "Pilot team did not survive reload")
    require!($game_map.map_id == lab, "Pilot did not reload its map")
    require!(BlueKantoPilot.progress["pilot_ss_ticket"] == true, "S.S. Ticket permit did not survive reload")
    require!(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true &&
             BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak parcel quest flags did not persist through save/reload")
    File.write("Data/blue-kanto-proof.txt", "Kanto 109 maps: four badges incl Erika, Celadon City/Center/Gym core, 57 trainer sights, save/reload verified (battles simulated)")
  end
end
