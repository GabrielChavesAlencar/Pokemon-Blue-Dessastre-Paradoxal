# Runs inside the copied mkxp-z game, after the native compiler.
module KantoNativeCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    require!($data_system.start_map_id == $game_map.map_id, "Player Home did not load")
    require!($game_map.events.size >= 4, "Player Home events missing")
    require!([$game_player.x, $game_player.y] == [25, 7], "Kanto did not start upstairs")
    require!($player.character_ID == 1 && !$game_player.character_name.empty? &&
             !$game_player.transparent, "Kanto sprite is not visible before the first step")
    require!(BlueKantoPilot.progress["pilot_profile_pending"], "Pilot missed character and name selection")
    home = $game_map.map_id
    # Phase 02: actual mkxp-z Game_Player passable? and directional move_ methods
    # in a throwaway CI run, not simulated keyboard/graphical acceptance.
    load "Data/blue-kanto-walk-check.rb"
    walk_rows = KantoWalkCheck.run(home,25,7)
    require!(walk_rows.count { |row| row[4] == "native_step_verified" } >= 2,
             "Stage 02 native step probe recorded no actual movement")
    require!($game_map.map_id == home && [$game_player.x,$game_player.y] == [25,7],
             "Walking probe did not restore the original upstairs Pallet spawn")
    home_exit = $game_map.events[1]
    home_return = home_exit.list.find { |row| row.code == 201 }
    require!(home_return, "Player Home has no return door")
    pallet = home_return.parameters[1]
    require!($game_map.events[3].list.any? { |row|
      row.code == 201 && row.parameters[1] == home
    }, "Home stairs do not connect both floors")
    $map_factory.setup(pallet)
    load "Data/blue-kanto-music-native-probe.rb"
    KantoMusicNativeProbe.run("pilot")
    require!($game_map.events.size >= 5, "Pallet Town events missing")
    require!([1, 2, 3].all? { |eid| $game_map.events[eid].trigger == 1 },
      "Pallet house and laboratory doors are not Player Touch")
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == home
    }, "Player Home door cannot be entered from Pallet")
    require!(BlueKantoPilot.experimental?, "Test-only menu marker was not loaded in the isolated pilot")
    labels = BlueKantoPilot.experimental_stops.map(&:first)
    puts "KANTO_NATIVE_STOPS:#{labels.length}|#{labels.grep(/Route|Elite|Hall|Lance|Champ|Kanto|Indigo/).join(";")}"
    require!(labels.length == 64 && labels.any? { |row| row.include?("Misty") } &&
             labels.any? { |row| row.include?("Surge") } &&
             labels.any? { |row| row.include?("Captain") } &&
             labels.any? { |row| row.include?("Celadon City") } &&
             labels.any? { |row| row.include?("Erika") } &&
             labels.any? { |row| row.include?("Koga") } &&
             labels.any? { |row| row.include?("Safari Zone") } &&
             labels.any? { |row| row.include?("Sabrina") } &&
             labels.any? { |row| row.include?("Silph Co.") } &&
             labels.any? { |row| row.include?("Cinnabar") } &&
             labels.any? { |row| row.include?("Blaine") } &&
             labels.any? { |row| row.include?("Ginasio Viridian Giovanni") } &&
             labels.any? { |row| row.include?("Hall of Fame") } &&
             labels.any? { |row| row.include?("Elite Four") } &&
             labels.any? { |row| row.include?("Mansion") },
             "Experimental Kanto phase 11 Saffron/Silph destinations unavailable")
    require!(!File.expand_path(SaveData::SAVE_DIR).include?("Pokemon Blue Dessastre Paradoxal"),
             "Pilot pointed at Decades save directory")

    current = $game_map.map_id
    destinations = $game_map.events.values.flat_map do |event|
      Array(event.list).filter_map { |command| command.parameters[1] if command.code == 201 }
    end
    lab = destinations.find { |id| GameData::MapMetadata.get(id).real_name.include?("Oak") }
    require!(lab, "Oak's Lab transfer missing")
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    require!($game_map.events.size >= 3, "Lab events missing")

    # Supply the choice and battle results so the compiler can run without a user.
    Object.send(:define_method, :pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    Object.send(:define_method, :pbConfirmMessage) { |*args| true }
    battle_calls = []
    losses_remaining = { "Doug" => 1, "Erika" => 1, "Koga" => 1, "Giovanni" => 1, "Sabrina" => 1, "Blaine" => 1 }
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
    BlueKantoPilot.choose_starter_ball(:BULBASAUR)
    require!($player.party.first&.species == :BULBASAUR, "Starter was not given")
    require!(!BlueKantoPilot.forest_unlocked?, "Forest opened before Oak's parcel")
    require!(Game_Player.ancestors.include?(BlueKantoPilot::Route2ExitGuard),
             "Viridian Route 2 outdoor boundary hook was not installed")
    starting_balls = $bag.quantity(:POKEBALL)
    # Stage 03: the Pallet -> Viridian -> Pallet Oak parcel loop is local to
    # Kanto, delivered once, and never creates an invalid FRLG item in Decades.
    mart_visits = []
    # A stale intro self-switch in older Kanto saves must be reset by
    # walking into the Mart, before the parcel has been collected.
    mart_id = File.read("Kanto pilot.json").match(/"12":\s*(\d+)/)[1].to_i
    $map_factory.setup(mart_id)
    intro_id = $game_map.events.values.find { |ev| ev.name == "Kanto Oak Parcel Intro" }&.id
    require!(intro_id, "Viridian Mart automatic parcel scene is missing")
    $game_self_switches[[mart_id, intro_id, "A"]] = true
    BlueKantoPilot.prepare_viridian_mart_visit(mart_id, intro_id)
    require!(!$game_self_switches[[mart_id, intro_id, "A"]],
             "Mart entrance did not re-arm the automatic parcel event")
    Object.send(:define_method, :pbPokemonMart) do |stock|
      stock.delete_if { false }
      mart_visits << stock
      true
    end
    BlueKantoPilot.viridian_mart
    require!(mart_visits.empty?, "First parcel encounter unexpectedly opened the Mart")
    require!(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true,
             "Viridian Mart did not register Oak's parcel")
    require!(!BlueKantoPilot.progress["pilot_oak_parcel_delivered"],
             "Oak's parcel delivered without returning to the laboratory")
    require!(!BlueKantoPilot.forest_unlocked?, "Forest opened before parcel delivery")
    BlueKantoPilot.viridian_mart
    require!(mart_visits.length == 1, "Returning to the Mart should allow shopping")
    BlueKantoPilot.choose_starter
    require!(BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak did not accept the parcel upon return")
    require!(BlueKantoPilot.forest_unlocked?, "Forest remained blocked after parcel delivery")
    require!($bag.quantity(:POKEBALL) == starting_balls + 5,
             "Oak must award exactly five Poke Balls, not the starter event")
    require!($player.has_pokedex, "Oak parcel delivery did not unlock the Pokedex") if $player.respond_to?(:has_pokedex)
    # Real Essentials 21.1 regional PBS + menu hook, not a mock UI. The
    # original seen/owned flags are shared between KantoDex and National.
    dexid = BlueKantoDex.index
    require!(dexid.is_a?(Integer), "KantoDex native manifest was not loaded")
    entries = pbAllRegionalSpecies(dexid)
    require!(entries.length == 151 && entries.first == :BULBASAUR && entries.last == :MEW,
             "Native KantoDex is not Bulbasaur #001 through Mew #151")
    require!(Settings.pokedex_names[dexid] == "KantoDex" &&
             Settings.pokedex_names.last == "Pokédex Nacional",
             "Native Pokédex selector does not name KantoDex and National correctly")
    $player.pokedex.refresh_accessible_dexes
    require!($player.pokedex.accessible_dexes.include?(dexid) &&
             $player.pokedex.accessible_dexes.include?(-1),
             "Native KantoDex and National missing after Oak: " +
             "index=#{dexid} available=#{$player.pokedex.accessible_dexes.inspect} " +
             "seen_bulbasaur=#{$player.pokedex.seen?(:BULBASAUR)} " +
             "seen_regional=#{$player.pokedex.seen_count(dexid)}")
    BlueKantoPilot.choose_starter
    require!($bag.quantity(:POKEBALL) == starting_balls + 5,
             "Returning to Oak duplicated the parcel reward")
    BlueKantoPilot.viridian_mart
    require!(mart_visits.length == 2 &&
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
    require!($game_map.events.keys.sort == [1, 2, 3, 20] &&
             $game_map.events[3].trigger == 1 &&
             $game_map.events[20].trigger == 1 &&
             [1, 2].all? { |id| $game_map.events[id].name == "CutTree" },
             "Celadon city must keep both doors and two source Cut trees")
    require!($game_map.events[3].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_gym
    } && $game_map.events[20].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_center
    }, "Celadon city doors do not reach the audited destinations")
    $map_factory.setup(celadon_center)
    require!($game_map.events.keys.include?(1) && $game_map.events.keys.include?(2) &&
             ($game_map.events.keys - [1, 2, 3]).empty?,
             "Celadon Center wrong active map/events: map=#{$game_map.map_id}, " +
             "target=#{celadon_center}, events=#{$game_map.events.keys.inspect}")
    exit_events = $game_map.events[1].list.map { |row| [row.code, row.parameters] }
    require!(exit_events.any? { |op|
      op[0] == 201 && op[1][1] == celadon_city
    }, "Celadon Center exit target mismatch: current=#{celadon_center} " +
       "city=#{celadon_city} events=#{exit_events.inspect}")
    $map_factory.setup(celadon_gym)
    require!($game_map.events.keys.sort == [1, 4, 5, 6, 7, 8, 42, 43, 44, 45, 46, 47] &&
             [4, 6, 8].all? { |id| $game_map.events[id].name == "CutTree" },
             "Celadon Gym must keep trainers, exit and three source Cut trees")
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

    # Phase 10 Fuchsia/Koga: limited City/Center/Mart/Gym/Safari-Gate
    # core while all Safari capture sectors and Warden remain preview-only.
    ["Casa Warden", "Safari Zone Sul", "Safari Zone Norte",
     "Safari Zone Oeste", "Rota 15"].each do |label|
      location = map_for.call(label)
      $map_factory.setup(location)
      require!($game_map.events.empty?, "Protected Fuchsia preview imported foreign events: #{label}")
    end
    fuchsia_city = map_for.call("Fuchsia City")
    fuchsia_center = map_for.call("Fuchsia Centro")
    fuchsia_mart = map_for.call("Fuchsia Mart")
    fuchsia_gym = map_for.call("Ginasio Fuchsia Koga")
    safari_gate = map_for.call("Safari Zone Portao")
    safari_south = map_for.call("Safari Zone Sul")
    $map_factory.setup(fuchsia_city)
    require!($game_map.events.keys.sort == [1, 2, 3, 4, 5, 17, 18, 24] &&
             [1, 2, 3, 4].all? { |id| $game_map.events[id].name == "CutTree" },
             "Fuchsia city must keep core doors and four original Cut trees")
    [[5, fuchsia_gym], [17, fuchsia_center],
     [18, fuchsia_mart], [24, safari_gate]].each do |event_id, target_id|
      ev = $game_map.events[event_id]
      require!(ev.trigger == 1 && ev.list.any? { |op| op.code == 201 && op.parameters[1] == target_id },
               "Fuchsia city has broken entry #{event_id}")
    end
    [[fuchsia_center, [1, 2]], [fuchsia_mart, [1, 2]],
     [fuchsia_gym, [3, 4, 5, 6, 7, 8, 9, 11]],
     [safari_gate, [1, 2, 5]]].each do |mid, required|
      $map_factory.setup(mid)
      actual = $game_map.events.keys
      optional_center_pc = mid == fuchsia_center ? [3] : []
      require!((required - actual).empty? &&
               (actual - required - optional_center_pc).empty?,
               "Fuchsia interior #{mid} contains unexpected/missing events #{actual.inspect}")
      exit_id = mid == fuchsia_gym ? 9 : (mid == safari_gate ? 2 : 1)
      require!($game_map.events[exit_id].list.any? { |op|
        op.code == 201 && op.parameters[1] == fuchsia_city
      }, "Fuchsia interior #{mid} has no exit to the city")
    end
    $map_factory.setup(safari_gate)
    require!($game_map.events[1].trigger == 0 &&
             !$game_map.events[1].list.any? { |row| row.code == 201 &&
               row.parameters[1] == safari_south },
             "Safari access started without tickets/balls/steps implementation")
    before_safari_money = $player.money
    BlueKantoPilot.safari_preview
    require!($player.money == before_safari_money,
             "Safari informational gate charged money without starting a native session")
    $map_factory.setup(fuchsia_gym)
    require!($game_map.events[3].trigger == 2 && $game_map.events[11].trigger == 0,
             "Koga/Tamers have incorrect trigger modes")
    koga = GameData::Trainer.get(:BLUE_KANTO_LEADER_KOGA, "Koga")
    require!(koga.pokemon.map { |pkmn| [pkmn[:species], pkmn[:level]] } ==
             [[:KOFFING,37],[:MUK,39],[:KOFFING,37],[:WEEZING,43]],
             "Koga's four pinned FRLG Pokemon/levels changed")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("SOUL"),
             "Soul Badge granted before Koga")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_KOGA, "Koga", "KANTO_147_011")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("SOUL") &&
             !BlueKantoPilot.progress["pilot_wins"].include?("KANTO_147_011"),
             "Koga loss granted a badge or victory flag")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_KOGA, "Koga", "KANTO_147_011")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") ==
             ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL"],
             "Koga victory did not grant one Soul Badge")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_147_011", "Koga", 11),
             "Koga victory flag not linked to his source event")
    $game_map.refresh
    require!($game_self_switches[[fuchsia_gym, 11, "A"]] &&
             $game_map.events[11].trigger == 0,
             "Koga kept his encounter active after winning")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_KOGA, "Koga", "KANTO_147_011")
    require!(battle_calls.count { |row| row[1] == "Koga" } == 2,
             "Koga battle repeated or grant awarded twice")

    # Stage 11: sourced Saffron city -> interiors; Silph card-key, rival,
    # Giovanni and Sabrina awards use region-only state, not the Decades save.
    ["Rota 8", "Portaria Oeste Saffron"].each do |label|
      id = map_for.call(label)
      $map_factory.setup(id)
      require!($game_map.events.empty?, "Saffron gate/Route 8 must remain a preview")
    end
    saffron = map_for.call("Saffron City")
    sabrina_gym = map_for.call("Ginasio Sabrina")
    saffron_center = map_for.call("Saffron Centro")
    silph_1f = map_for.call("Silph Co. 1F")
    silph_5f = map_for.call("Silph Co. 5F")
    silph_11f = map_for.call("Silph Co. 11F")
    silph_elevator = map_for.call("Silph Co. Elevador")
    $map_factory.setup(saffron)
    [[6,sabrina_gym],[10,silph_1f],[13,saffron_center]].each do |eid,dest|
      ev = $game_map.events[eid]
      require!(ev && ev.trigger == 1 && ev.list.any? { |op|
        op.code == 201 && op.parameters[1] == dest
      }, "Broken Saffron City entrance #{eid}")
    end
    $map_factory.setup(saffron_center)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == saffron
    }, "Saffron Center exit does not return to city")
    $map_factory.setup(silph_1f)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == saffron
    }, "Silph 1F is a one-way trap")
    $map_factory.setup(silph_elevator)
    require!($game_map.events.keys.sort == [1,2] &&
      $game_map.events[1].list.none? { |op| op.code == 201 },
      "Silph elevator imported unmapped FRLG targets")
    require!(File.readlines("Data/blue-kanto-silph-floors.txt").length == 11,
      "Silph elevator must offer 11 real floors")

    $map_factory.setup(sabrina_gym)
    require!($game_map.events.values.count { |ev|
      ev.name.start_with?("Warp Tile ")
    } == 30, "Sabrina gym should have 30 source teleporter events")
    require!($game_map.events[3].trigger == 2 &&
      $game_map.events[2].trigger == 0, "Sabrina/trainer trigger mismatch")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("MARSH"),
      "Marsh Badge granted before defeating Sabrina")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SABRINA,"Sabrina","KANTO_171_002")
    require!(battle_calls.none? { |row| row[1]=="Sabrina" },
      "Sabrina challenged before the Silph rescue")
    $map_factory.setup(silph_5f)
    BlueKantoPilot.silph_card_key
    require!(BlueKantoPilot.progress["pilot_silph_card_key"],
      "Silph Card Key was not stored locally")
    require!($game_self_switches[[silph_5f, 9, "A"]],
      "Silph Card Key pickup should not respawn")
    $map_factory.setup(silph_11f)
    locked = $game_map.events.values.find { |ev| ev.name=="Locked Door" }
    if locked
      # Representative Card Key door tile: not open before using the key.
      require!(!$game_self_switches[[silph_11f,locked.id,"A"]],
        "Silph door opened without the Card Key")
    end
    boss = GameData::Trainer.get(:BLUE_KANTO_ROCKETBOSS,"Giovanni",2)
    require!(boss.pokemon.length >= 2, "Silph Giovanni PBS team is missing")
    BlueKantoPilot.battle(:BLUE_KANTO_ROCKETBOSS,"Giovanni","KANTO_188_010",2)
    require!(!BlueKantoPilot.progress["pilot_silph_rescued"],
      "Giovanni defeat incorrectly marked Silph rescue")
    BlueKantoPilot.battle(:BLUE_KANTO_ROCKETBOSS,"Giovanni","KANTO_188_010",2)
    require!(BlueKantoPilot.progress["pilot_silph_rescued"],
      "Giovanni victory did not liberate Silph")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_188_010","Giovanni",10),
      "Giovanni event did not persist")
    BlueKantoPilot.battle(:BLUE_KANTO_ROCKETBOSS,"Giovanni","KANTO_188_010",2)
    require!(battle_calls.count { |row| row[1]=="Giovanni" }==2,
      "Giovanni boss battle repeated")
    $map_factory.setup(sabrina_gym)
    sabrina = GameData::Trainer.get(:BLUE_KANTO_LEADER_SABRINA,"Sabrina")
    require!(sabrina.pokemon.length == 4, "Sabrina source roster missing")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SABRINA,"Sabrina","KANTO_171_002")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("MARSH"),
      "Sabrina defeat awarded Marsh Badge")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SABRINA,"Sabrina","KANTO_171_002")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("MARSH"),
      "Sabrina victory did not grant Marsh Badge")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_171_002","Sabrina",2),
      "Sabrina event not linked to Marsh reward")
    $game_map.refresh
    require!($game_self_switches[[sabrina_gym,2,"A"]],
      "Sabrina victory self-switch did not persist")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_SABRINA,"Sabrina","KANTO_171_002")
    require!(battle_calls.count { |row| row[1]=="Sabrina" }==2,
      "Sabrina battle repeated after Marsh")
    
    # Phase 12: Cinnabar Island/Center/Mart/Gym/Mansion in the isolated game.
    # The battle runner simulates victory and defeat; it does not assert visual QA.
    ["Rota 19", "Rota 20", "Seafoam 1F"].each do |label|
      id = map_for.call(label)
      $map_factory.setup(id)
      require!($game_map.events.empty?, "Phase 12 ocean/Seafoam preview imported foreign events")
    end
    cinnabar = map_for.call("Cinnabar Island")
    cinnabar_gym = map_for.call("Ginasio Cinnabar Blaine")
    cinnabar_center = map_for.call("Cinnabar Centro")
    mansion = map_for.call("Pokémon Mansion 1F")
    mansion_b1f = map_for.call("Pokémon Mansion B1F")
    $map_factory.setup(cinnabar)
    require!($game_map.events.keys.sort == [1,2,3,4,5], "Cinnabar imported unaudited city events")
    mart_entry = $game_map.events[1]
    mart_transfer = mart_entry.list.find { |op| op.code == 201 } if mart_entry
    require!(mart_entry && mart_entry.trigger == 1 && mart_transfer,
      "Cinnabar Mart does not have a real Player Touch entrance")
    cinnabar_mart = mart_transfer.parameters[1]
    require!(cinnabar_mart != cinnabar_center && cinnabar_mart != mansion,
      "Cinnabar Mart entrance points at the wrong interior")
    [[2,cinnabar_center], [3,mansion]].each do |eid, target|
      ev = $game_map.events[eid]
      require!(ev && ev.trigger == 1 && ev.list.any? { |op|
        op.code == 201 && op.parameters[1] == target
      }, "Cinnabar city entrance #{eid} is invalid")
    end
    $map_factory.setup(cinnabar_mart)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == cinnabar
    }, "Cinnabar Mart does not return to the city")
    $map_factory.setup(cinnabar_center)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == cinnabar
    }, "Cinnabar Center cannot return to the city")
    $map_factory.setup(mansion)
    require!($game_map.events[1].list.any? { |op|
      op.code == 201 && op.parameters[1] == cinnabar
    }, "Cinnabar Mansion has no exit")
    require!($game_map.events[4].list.any? { |op|
      op.code == 355 && op.parameters[0].include?("mansion_switch")
    }, "Cinnabar Mansion statue still uses original switches")
    $map_factory.setup(cinnabar_gym)
    require!(!$game_self_switches[[cinnabar_gym, 20, "A"]],
      "Blaine quiz door was unlocked before any action")
    require!(!BlueKantoPilot.progress["pilot_cinnabar_secret_key"],
      "Secret Key was granted before reaching the Mansion")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_BLAINE, "Blaine", "KANTO_202_016")
    require!(battle_calls.none? { |row| row[1] == "Blaine" },
      "Blaine could be fought without the Secret Key")
    $map_factory.setup(mansion_b1f)
    BlueKantoPilot.mansion_secret_key
    require!(BlueKantoPilot.progress["pilot_cinnabar_secret_key"] &&
             $game_self_switches[[mansion_b1f, 8, "A"]],
      "Secret Key was not recorded as a unique local event")
    BlueKantoPilot.mansion_secret_key
    require!(BlueKantoPilot.progress["pilot_cinnabar_secret_key"],
      "Secret Key disappeared after revisiting the pickup")
    $map_factory.setup(cinnabar_gym)
    BlueKantoPilot.cinnabar_quiz(1)
    require!(BlueKantoPilot.progress.fetch("pilot_cinnabar_doors", []).include?(1) &&
             $game_self_switches[[cinnabar_gym, 20, "A"]],
      "The first Blaine quiz failed to open its linked door group")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("VOLCANO"),
      "Volcano Badge was granted before Blaine's battle")
    blaine = GameData::Trainer.get(:BLUE_KANTO_LEADER_BLAINE, "Blaine")
    require!(blaine.pokemon.length >= 2, "Blaine's original PBS team is missing")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_BLAINE, "Blaine", "KANTO_202_016")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("VOLCANO"),
      "Blaine defeat granted Volcano Badge")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_BLAINE, "Blaine", "KANTO_202_016")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO").include?("VOLCANO"),
      "Blaine victory did not grant Volcano Badge")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_202_016", "Blaine", 16),
      "Blaine victory was not attached to his map/event key")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_BLAINE, "Blaine", "KANTO_202_016")
    require!(battle_calls.count { |row| row[1] == "Blaine" } == 2,
      "Blaine battle could be repeated after earning Volcano Badge")

    # Phase 13 — independent Viridian Giovanni gym: seven LOCAL Kanto badges
    # and rescued Silph required. All fights here are simulated by this CI test.
    viridian_gym = map_for.call("Ginasio Viridian Giovanni")
    viridian = map_for.call("Viridian City")
    $map_factory.setup(viridian)
    gate = $game_map.events[1]
    require!(gate && gate.trigger == 1 &&
             gate.list.none? { |row| row.code == 201 } &&
             gate.list.any? { |row| row.code == 355 &&
               row.parameters[0].include?("BlueKantoPilot.viridian_gym_gate") },
             "Viridian Gym entrance bypasses the local badge gate")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("EARTH"),
             "Earth Badge awarded before the gym")
    earned = BlueKantoPilot.progress["achievements"]["KANTO"]
    require!(earned.include?("VOLCANO"), "Blaine's Volcano Badge is missing before Giovanni")
    earned.delete("VOLCANO")
    require!(!BlueKantoPilot.viridian_access? &&
             BlueKantoPilot.viridian_gym_gate(viridian_gym,17,22)==false,
             "Viridian Gym opened without seven local badges")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_GIOVANNI,"Giovanni","KANTO_013_004")
    require!(battle_calls.none? { |row| row[0]==:BLUE_KANTO_LEADER_GIOVANNI },
             "Giovanni accepted a battle before all seven local badges")
    earned << "VOLCANO"
    BlueKantoPilot.progress["pilot_silph_rescued"] = false
    require!(!BlueKantoPilot.viridian_access?,
             "Viridian Gym opened before saving Silph Co.")
    BlueKantoPilot.progress["pilot_silph_rescued"] = true
    require!(BlueKantoPilot.viridian_access?, "Viridian Gym stayed locked after requirements")
    $map_factory.setup(viridian_gym)
    require!($game_map.events.keys.sort == [2,3,4,5,6,7,8,9,10,11,16],
             "Viridian gym imported unsanctioned source events")
    require!([2,3,5,6,7,8,9,10].all? { |eid| $game_map.events[eid].trigger==2 } &&
             $game_map.events[4].trigger==0,
             "Viridian eight Sight trainers/leader triggers are incorrect")
    require!($game_map.events[11].list.any? { |row|
      row.code == 201 && row.parameters[1]==viridian
    }, "Giovanni Gym has no exit to Viridian City")
    jason = GameData::Trainer.get(:BLUE_KANTO_TAMER,"Jason")
    cole  = GameData::Trainer.get(:BLUE_KANTO_TAMER,"Cole")
    require!(jason.pokemon.any? && cole.pokemon.any? &&
             $game_map.events[8].list.any? { |row|
               row.code == 355 && row.parameters[0].include?('"Jason"')
             }, "FRLG source Jason/Cole battle typo not repaired")
    leader = GameData::Trainer.get(:BLUE_KANTO_LEADER_GIOVANNI,"Giovanni")
    require!(leader.pokemon.length >= 4, "Giovanni Gym original FRLG roster unavailable")
    wins = (BlueKantoPilot.progress["pilot_wins"] ||= [])
    require!(wins.include?("KANTO_188_010"), "Silph Giovanni's separate victory was lost")
    wins << "Giovanni"  # Simulate an older Silph save with name-only victory.
    losses_remaining["Giovanni"] = 1
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_GIOVANNI,"Giovanni","KANTO_013_004")
    require!(battle_calls.count { |row| row[0]==:BLUE_KANTO_LEADER_GIOVANNI }==1 &&
             !wins.include?("KANTO_013_004") &&
             !BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("EARTH"),
             "Giovanni loss or legacy Silph flag incorrectly granted Earth")
    wins.delete("Giovanni")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_GIOVANNI,"Giovanni","KANTO_013_004")
    require!(wins.include?("KANTO_013_004") &&
             BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").last=="EARTH",
             "Giovanni victory did not grant Earth Badge")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_013_004","Giovanni",4),
             "Giovanni Gym event win flag was not saved")
    $game_map.refresh
    require!($game_self_switches[[viridian_gym,4,"A"]],
             "Giovanni did not move to his defeated event page")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_GIOVANNI,"Giovanni","KANTO_013_004")
    require!(battle_calls.count { |row| row[0]==:BLUE_KANTO_LEADER_GIOVANNI }==2,
             "Giovanni Gym repeated a defeated battle")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").length==8 &&
             !BlueKantoPilot.progress["leagues"].include?("KANTO"),
             "Eight badges completed League prematurely or duplicated progress")

    # The CI runs inside mkxp before Scene_Map has created its spriteset.
    # Tamas's DexNav invokes playersprite during transfer_player and would
    # crash in this headless proof despite compiling and running normally.
    # Only this disposable test replaces the transfer with native map setup;
    # production BlueRegionTravel.move_to remains unmodified.
    league_ci_transfers = []
    BlueRegionTravel.define_singleton_method(:move_to) do |point|
      raise "Invalid proof map point" unless point.is_a?(Array) && point.length == 4 &&
        pbRgssExists?(sprintf("Data/Map%03d.rxdata", point[0]))
      $map_factory.setup(point[0])
      $game_player.moveto(point[1], point[2])
      league_ci_transfers << point
      true
    end

    # Phase 14 native proof. Battle outcomes are simulated, but the
    # source maps, PBS identities, event triggers and regional state are real.
    route22 = map_for.call("Route 22 (Plateau Gate)")
    route23 = map_for.call("Route 23 (oito guardas)")
    road1 = map_for.call("Victory Road 1F")
    road2 = map_for.call("Victory Road 2F")
    lobby = map_for.call("Indigo Lobby")
    lorelei_room = map_for.call("Elite Four Lorelei")
    lance_room = map_for.call("Elite Four Lance")
    champion_room = map_for.call("Campeao Blue")
    hall = map_for.call("Hall of Fame Kanto")
    require!(!BlueKantoPilot.progress["leagues"].include?("KANTO"), "Kanto League prematurely completed")
    earned = BlueKantoPilot.progress["achievements"]["KANTO"]
    require!(earned.length == 8 && BlueKantoPilot.league_badges?, "Need exactly eight local Kanto badges")
    earned.delete("EARTH")
    require!(!BlueKantoPilot.league_badges? &&
             BlueKantoPilot.league_begin(lorelei_room,6,12) == false,
             "The League accepted seven local badges or global Decades crystals")
    $map_factory.setup(route23)
    require!(!BlueKantoPilot.league_badge_check(8,19,18) &&
             !$game_self_switches[[route23,18,"A"]],
             "The eighth Route 23 checkpoint was opened without Earth")
    earned << "EARTH"
    $map_factory.setup(route23)
    BlueKantoPilot.league_badge_check(8,19,18)
    require!($game_self_switches[[route23,18,"A"]] &&
             $game_self_switches[[route23,19,"A"]],
             "Route 23 eighth badge barrier/guard did not open")
    $map_factory.setup(road1)
    BlueKantoPilot.victory_strength([14,15])
    require!($game_self_switches[[road1,14,"A"]] &&
             $game_self_switches[[road1,15,"A"]],
             "Victory Road adapted Strength barriers did not open")
    $map_factory.setup(road2)
    require!([9,11,13,14,16].all? { |event_id| $game_map.events[event_id].trigger == 2 },
             "Victory Road has missing source sight trainers")
    coolcouple = GameData::Trainer.get(:BLUE_KANTO_COOLCOUPLE, "Ray & Tyra")
    require!(coolcouple.pokemon.length >= 2, "Victory Road double-battle roster unavailable")
    $map_factory.setup(map_for.call("Victory Road 2F"))
    $map_factory.setup(map_for.call("Elite Four Lorelei"))
    require!($game_map.events[3].trigger == 0, "Lorelei is not an interactive boss")
    require!(!BlueKantoPilot.league_active?, "League run activated without entering Lobby")
    BlueKantoPilot.league_battle("LORELEI",:BLUE_KANTO_ELITE_LORELEI,"Lorelei",lobby)
    require!(battle_calls.none? { |r| r[0] == :BLUE_KANTO_ELITE_LORELEI },
             "Teleport to Lorelei bypassed the Lobby gate")
    $map_factory.setup(lobby)
    BlueKantoPilot.league_begin(lorelei_room,6,12)
    require!(BlueKantoPilot.league_active?, "League did not start after badge check")
    require!(BlueKantoPilot.league_battle("BRUNO",:BLUE_KANTO_ELITE_BRUNO,"Bruno",lobby) == false,
             "Bruno accepted out-of-order battle before Lorelei")
    losses_remaining["Lorelei"] = 1
    BlueKantoPilot.league_battle("LORELEI",:BLUE_KANTO_ELITE_LORELEI,"Lorelei",lobby)
    require!(!BlueKantoPilot.league_active? && BlueKantoPilot.progress["pilot_league_wins"].empty? &&
             !BlueKantoPilot.progress["leagues"].include?("KANTO"),
             "Lorelei loss did not reset local league attempt")
    BlueKantoPilot.league_begin(lorelei_room,6,12)
    [
      ["LORELEI",:BLUE_KANTO_ELITE_LORELEI,"Lorelei"],
      ["BRUNO",:BLUE_KANTO_ELITE_BRUNO,"Bruno"],
      ["AGATHA",:BLUE_KANTO_ELITE_AGATHA,"Agatha"],
      ["LANCE",:BLUE_KANTO_ELITE_LANCE,"Lance"],
    ].each_with_index do |row, i|
      require!(GameData::Trainer.get(row[1],row[2]).pokemon.length >= 4,
               "Original PBS team missing for #{row[2]}")
      require!(BlueKantoPilot.league_battle(*row,lobby),
               "Elite Four battle did not record victory for #{row[2]}")
      require!(BlueKantoPilot.progress["pilot_league_wins"].length == i+1,
               "Elite Four win order was not preserved")
    end
    require!(BlueKantoPilot.league_advance("CHAMPION",hall,5,12) == false,
             "Champion door bypassed Blue's battle")
    champion = GameData::Trainer.get(:BLUE_KANTO_CHAMPION_BLUE,"Blue",1)
    require!(champion.pokemon.length == 6,
             "Champion Blue original team is missing or incomplete")
    BlueKantoPilot.league_battle("CHAMPION",:BLUE_KANTO_CHAMPION_BLUE,"Blue",lobby)
    require!(BlueKantoPilot.progress["pilot_league_wins"] == %w[LORELEI BRUNO AGATHA LANCE CHAMPION] &&
             !BlueKantoPilot.progress["leagues"].include?("KANTO"),
             "Champion win skipped Hall of Fame ceremony or sequence")
    require!(BlueKantoPilot.league_finalize(pallet),
             "Hall of Fame refused a valid run")
    require!(BlueKantoPilot.progress["pilot_hall_of_fame"] &&
             BlueKantoPilot.progress["leagues"] == ["KANTO"] &&
             BlueRegions.unlocked(BlueKantoPilot.progress).include?("DECADES") &&
             BlueRegions.unlocked(BlueKantoPilot.progress).include?("JOHTO"),
             "Kanto clear did not unlock exactly the eligible adjacent regions")
    require!(league_ci_transfers.last == [pallet,18,8,2],
             "Hall of Fame did not return to Pallet Town")
    require!(!BlueRegions.unlocked(BlueKantoPilot.progress).include?("HOENN") &&
             !BlueKantoPilot.league_finalize(pallet),
             "Hall of Fame duplicated completion or unlocked extra regions")

    # Keep the legacy reload-map assertion stable while proving the gym
    # can be loaded and the puzzle flags persist across the same save.
    $map_factory.setup(lab)
    $game_player.moveto(6, 12)
    slot = "Kanto Native Verification"
    require!(Game.save(slot), "Pilot save failed")
    save_file = SaveData.get_full_path(slot)
    saved = SaveData.read_from_file(save_file)
    Game.load(saved)
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress, "KANTO") == ["BOULDER","CASCADE","THUNDER","RAINBOW","SOUL","MARSH","VOLCANO","EARTH"],
             "Pilot badges did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_028_007"),
             "Trainer victory keys did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_124_001"),
             "Erika victory did not persist through save/reload")
    require!(BlueKantoPilot.progress["pilot_silph_card_key"] && BlueKantoPilot.progress["pilot_silph_rescued"],
              "Silph Card Key/boss progress lost after reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_171_002"),
              "Sabrina victory did not persist")
    require!(BlueKantoPilot.progress["pilot_cinnabar_secret_key"] &&
             BlueKantoPilot.progress.fetch("pilot_cinnabar_doors", []).include?(1) &&
             BlueKantoPilot.progress["pilot_wins"].include?("KANTO_202_016"),
             "Cinnabar Secret Key, gym door and Blaine did not survive reload")
    require!(BlueKantoPilot.progress["pilot_hall_of_fame"] &&
             BlueKantoPilot.progress["leagues"] == ["KANTO"] &&
             BlueKantoPilot.progress["pilot_league_wins"] == %w[LORELEI BRUNO AGATHA LANCE CHAMPION],
             "Hall of Fame / Kanto League result did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_013_004") &&
             $game_self_switches[[viridian_gym,4,"A"]],
             "Giovanni Gym Earth Badge/self-switch did not survive reload")
    require!(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_147_011"),
             "Koga victory did not persist through save/reload")
    require!($player.party.first&.species == :BULBASAUR, "Pilot team did not survive reload")
    require!($game_map.map_id == lab, "Pilot did not reload its map")
    require!(BlueKantoPilot.progress["pilot_ss_ticket"] == true, "S.S. Ticket permit did not survive reload")
    require!(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true &&
             BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak parcel quest flags did not persist through save/reload")
    walk_verified = walk_rows.count { |row| row[4] == "native_step_verified" }
    File.write("Data/blue-kanto-proof.txt",
               "Kanto 142 maps: Victory Road, eight badge guards, Elite Four/Blue, unique Hall of Fame and Decades/Johto eligibility; save/reload (battles simulated); " +
               "native tile-step probe #{walk_verified}/#{walk_rows.length} destinations (NOT manual keyboard/visual QA)")
  end
end
