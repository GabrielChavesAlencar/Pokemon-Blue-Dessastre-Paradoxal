# CI-only native proof. The original Decades intro waits for input and must
# remain a MANUAL check, not a second headless Game.start_new call.
module KantoIntegratedCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.stage(label)
    File.write("Data/blue-kanto-integrated-stage.txt", label)
  end


  # Exercise the production NPC travel entry point with only its menus replaced
  # by deterministic responses in the disposable headless Windows CI copy.
  # The real map, agent event, permissions, and perform() checks stay active.
  def self.travel_from_real_agent!(destination)
    state = BlueRegions.snapshot
    require!(state && state["current"] != destination, "Invalid regional agent destination")
    point = case state["current"]
            when "KANTO" then BlueRegionTravel.kanto_town_point
            when "DECADES" then BlueRegionTravel.decades_town_point
            end
    require!(point && point[0].is_a?(Integer), "No verified initial-town departure map")
    $map_factory.setup(point[0])
    $game_player.moveto(point[1], point[2])
    require!(BlueRegionTravel.at_departure_town?(state), "Regional departure town not verified")
    agents = $game_map.events.values.select do |event|
      event.list && event.list.any? { |op|
        op.code == 355 && op.parameters.first.to_s.include?("BlueRegionTravel.agent(true)")
      }
    end
    require!(agents.length == 1, "Exactly one real regional travel NPC is required")
    require!(!BlueRegionTravel.travel(destination, true),
             "Travel bypassed the physical NPC interaction gate")

    keys = BlueRegions.circuit + ["HISUI"]
    choice = keys.index(destination)
    require!(!choice.nil?, "Destination is absent from regional NPC menu")
    singleton = BlueRegionTravel.singleton_class
    require!(!singleton.instance_methods(false).include?(:pbMessage) &&
             !singleton.instance_methods(false).include?(:pbConfirmMessage),
             "CI would overwrite an existing NPC method")
    menu_calls = 0
    confirmations = 0
    singleton.send(:define_method, :pbMessage) do |_text, *args|
      if args.length == 2 && args[0].is_a?(Array) && args[1] == -1
        menu_calls += 1
        raise "Regional NPC menu repeated after failed travel" unless menu_calls == 1
        choice
      else
        nil # arrival notice only; no actual UI in headless CI
      end
    end
    singleton.send(:define_method, :pbConfirmMessage) do |*_args|
      confirmations += 1
      true
    end
    begin
      BlueRegionTravel.agent(true)
    ensure
      singleton.send(:remove_method, :pbMessage)
      singleton.send(:remove_method, :pbConfirmMessage)
    end
    require!(menu_calls == 1 && confirmations == 1,
             "Regional NPC dialog/confirmation was not exercised")
    require!($PokemonGlobal.blue_regions["current"] == destination,
             "Regional NPC did not complete the real transfer")
    require!(!BlueRegionTravel.instance_variable_get(:@npc_event_context),
             "NPC authorization leaked beyond the event")
  end

  def self.run
    stage("bootup")
    SaveData.initialize_bootup_values
    spawn = BlueRegionStart.kanto_spawn
    require!(spawn && spawn.length == 3, "Integrated Kanto marker/map missing")
    stage("main_title_kanto")
    require!(defined?(BlueKantoTitle), "Testar Kanto title menu plugin not loaded")
    require!(PokemonLoad_Scene.ancestors.include?(BlueKantoTitle::Scene),
             "Native main load scene does not include Kanto and Johto test options")
    commands = [" <- Decades Save -> ", _INTL("New Game"), _INTL("Options"), _INTL("Quit Game")]
    indices = BlueKantoTitle.command_order(commands, true)
    require!(indices == [0, 1, :blue_test_kanto, :blue_test_johto, :blue_test_hoenn, :blue_test_sinnoh, 2, 3],
             "Regional test options changed Continue/New Game or Auto Multi Save indexes")
    require!(BlueKantoTitle::LABEL == "Testar Kanto" &&
             BlueKantoTitle::JOHTO_LABEL == "Testar Johto",
             "Both regional labels must be available on the native title")
    require!(BlueKantoTitle.windows?, "Windows-native executable did not detect Windows")
    require!(Process.respond_to?(:spawn), "Native Ruby runtime cannot spawn Kanto launcher")
    launcher = BlueKantoTitle.launcher
    require!(launcher && launcher[0].end_with?("KANTO_JOGAR_EXPERIMENTAL.bat"),
             "Main Game.exe cannot locate the project-owned Kanto launcher")
    # Check actual Windows process creation, including BAT names with spaces.
    # This disposable CI-only BAT writes one marker and NEVER opens the pilot.
    probe_dir = File.join(launcher[1], ".blue-work", "kanto title spawn proof")
    Dir.mkdir(probe_dir) unless Dir.exist?(probe_dir)
    probe_bat = File.join(probe_dir, "test launch.cmd")
    probe_marker = File.join(probe_dir, "child-ok.txt")
    begin
      File.write(probe_bat, "@echo off\r\n>\"#{probe_marker}\" echo ok\r\n")
      child = Process.spawn("cmd.exe", "/d", "/c", probe_bat, :chdir => launcher[1])
      Process.wait(child)
      require!(File.file?(probe_marker) && File.read(probe_marker).strip == "ok",
               "Native Game.exe could not launch a Windows BAT through cmd.exe")
    ensure
      File.delete(probe_bat) if File.file?(probe_bat)
      File.delete(probe_marker) if File.file?(probe_marker)
      Dir.rmdir(probe_dir) if Dir.exist?(probe_dir)
    end
    original = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]

    # Select Kanto without opening a graphical choice menu in headless CI.
    # Real visual choice and Decades introduction remain manual acceptance tests.
    BlueRegionStart.define_singleton_method(:choose_initial) { "KANTO" }
    stage("before_kanto_new_game")
    Game.start_new
    stage("after_kanto_new_game")
    require!($game_map.map_id == spawn[0], "Kanto initial map did not load")
    require!([$game_player.x, $game_player.y] == spawn[1,2], "Kanto spawn is wrong")
    # The canonical Kanto start is now the player's upstairs bedroom.
    require!($game_map.events[1]&.list&.any? { |op| op.code == 201 },
             "Kanto home has no Pallet exit")
    require!($game_map.events[3]&.list&.any? { |op|
      op.code == 201 && op.parameters[1] == spawn[0]
    }, "Kanto home upstairs stairs have no return path")
    house_map = $game_map.map_id
    town_map = $game_map.events[1].list.find { |op| op.code == 201 }.parameters[1]
    $map_factory.setup(town_map)
    load "Data/blue-kanto-music-native-probe.rb"
    KantoMusicNativeProbe.run("integrated")
    require!($game_map.events[1]&.trigger == 1 &&
             $game_map.events[1].list.any? { |op|
               op.code == 201 && op.parameters[1] == house_map
             }, "Pallet player home cannot be entered by walking")
    require!($game_map.events[9]&.list&.any? { |op|
      op.code == 355 && op.parameters.first.to_s.include?("BlueRegionTravel.agent")
    }, "Pallet starter town has no NPC for region travel")
    $map_factory.setup(house_map)
    $game_player.moveto(spawn[1],spawn[2])
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto initial region not saved")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region not saved")
    require!($PokemonGlobal.blue_story_mode == :story, "Story mode was not selected")
    require!($PokemonGlobal.blue_traditional_starters == true, "Regional starter mode not enabled")
    require!($PokemonGlobal.blue_campaign_departure == false, "Kanto would lose Oak's items on departure")
    require!([$data_system.start_map_id, $data_system.start_x, $data_system.start_y] == original,
             "Native Decades System.rxdata start coordinates were changed")

    # These are the three Oak Lab versions used by BlueKantoPilot.rival.
    # Tests must instantiate the *real compiled Essentials NPCTrainer*, not
    # only assert that a row exists. This exercises type, species, level,
    # move/ability fields, trainer construction and trainer Pokémon data.
    stage("gary_native_trainer_preflight")
    [:BULBASAUR, :CHARMANDER, :SQUIRTLE].zip([11,12,13]).each do |starter,version|
      require!(GameData::TrainerType.exists?(:BLUE_KANTO_RIVAL),
               "Gary type missing from compiled trainer_types_kanto")
      require!(GameData::Trainer.exists?(:BLUE_KANTO_RIVAL,"Blue",version),
               "Gary version #{version} missing from compiled trainers_kanto")
      pokemon_data=GameData::Trainer.get(:BLUE_KANTO_RIVAL,"Blue",version)
      require!(pokemon_data.pokemon.is_a?(Array) && !pokemon_data.pokemon.empty?,
               "Gary version #{version} has empty roster")
      begin
        trainer=pokemon_data.to_trainer
      rescue StandardError => error
        raise "Gary #{starter}/#{version} cannot build native NPCTrainer: #{error.class}: #{error.message}"
      end
      require!(trainer.is_a?(NPCTrainer) && trainer.party.length==pokemon_data.pokemon.length,
               "Gary #{version} native team is not battle-ready")
    end

    stage("regional_policy_start")
    require!(defined?(BlueRegionalPolicy), "Regional policy plugin was not loaded")
    current_state = $PokemonGlobal.blue_regions
    mewtwo = Pokemon.new(:MEWTWO, 30)
    require!(BlueRegionalPolicy.restricted?(mewtwo), "Kanto allowed Legendary before 8 badges")
    require!(BlueRegionalPolicy.field_result(:FLASH) == :badge, "Flash allowed without Boulder")
    # The retrofit must not retroactively lock old Decades saves.
    $PokemonGlobal.blue_regions = BlueRegions.new_state("DECADES")
    require!(!BlueRegionalPolicy.restricted?(mewtwo), "Native Decades PC was locked")
    $PokemonGlobal.blue_regions = current_state
    require!(BlueRegions.award(current_state, "KANTO", "BOULDER"), "Boulder badge not awarded")
    require!(!BlueRegions.award(current_state, "KANTO", "BOULDER"), "Boulder was counted twice")
    # Boulder removes only the local badge restriction. Flash still requires
    # HM05/HMFLASH in the Bag and an eligible party Pokemon (tested end-to-end
    # by tests/kanto_hm_gate_runtime.rb). Do not bypass either requirement.
    require!(BlueRegions.field_access(current_state, "KANTO", "FLASH", false) == :tool,
             "Boulder did not clear the Flash badge gate")
    require!(BlueRegionalPolicy.field_result(:FLASH) == :hm,
             "Flash was allowed without the HM after Boulder")
    require!(BlueRegionalPolicy.field_result(:SURF) == :badge, "Surf unlocked without Soul Badge")
    base_total = $player.badge_count
    require!(BlueRegions.crystal_total(current_state, base_total) == base_total + 1,
             "Local Kanto badge was not added to Blue global stage once")

    # A restricted gift is caught before entering the party; it is deposited
    # in the real native PC while keeping ownership/Pokédex.
    stage("regional_policy_gift")
    gift = Pokemon.new(:MEWTWO, 20)
    require!(pbAddPokemonSilent(gift), "Restricted gift could not be stored")
    require!(!$player.party.any? { |p| p.equal?(gift) }, "Restricted gift entered party")
    boxed_gift = BlueRegionTravel.free_storage_slots(2)
    require!($PokemonStorage[0,0]&.species == :MEWTWO, "Restricted gift missing from PC")

    stage("before_travel_validation")
    # Game.start_new does not run Scene_Map.main or initialize graphics
    # spritesets in this headless proof. The installed DexNav overwrites
    # transfer_player and needs those sprites. Only in this CI proof, replace
    # that renderer-dependent method with the real PokemonMapFactory setup and
    # real player movement. Production gameplay keeps the original method.
    $scene.define_singleton_method(:transfer_player) do
      target = $game_temp.player_new_map_id
      $map_factory.setup(target) if $game_map.map_id != target
      $game_player.moveto($game_temp.player_new_x, $game_temp.player_new_y)
      case $game_temp.player_new_direction
      when 2 then $game_player.turn_down
      when 4 then $game_player.turn_left
      when 6 then $game_player.turn_right
      when 8 then $game_player.turn_up
      end
      $game_temp.player_transferring = false
      $game_map.update
    end
    # This is a discardable CI session. Simulate Kanto's future League here,
    # because only Pallet-Pewter exists today; real gameplay NEVER grants it.
    state = $PokemonGlobal.blue_regions
    state["leagues"] << "KANTO"
    state["decades_return"] = [original[0], original[1], original[2], 2]
    pokemon = Pokemon.new(:BULBASAUR, 5)
    $player.party << pokemon
    original_money = $player.money
    original_bag = Marshal.dump($bag)
    original_pc = Marshal.dump($PokemonStorage)
    original_dex = Marshal.dump($player.pokedex)
    stage("travel_kanto_to_decades")
    travel_from_real_agent!("DECADES")
    require!($game_map.map_id == original[0], "Decades return map differs from original")
    require!($PokemonGlobal.blue_regions["current"] == "DECADES", "Travel state was not committed")
    # Town NPC belongs in the first Decades city (Cherryhill Map077).
    # Dynamic on-map insertion does not mutate native Map077.rxdata.
    require!(BlueRegionTravel::DECADES_AGENT_MAP == 77,
             "Decades starting city NPC moved to a non-audited map")
    $map_factory.setup(BlueRegionTravel::DECADES_AGENT_MAP)
    agents = $game_map.events.values.select { |event|
      event.name == BlueRegionTravel::DECADES_AGENT_NAME
    }
    require!(agents.length == 1,
             "Cherryhill City regional NPC missing or duplicated")
    require!(agents[0].list.any? { |op|
      op.code == 355 && op.parameters[0] == "BlueRegionTravel.agent(true)"
    }, "Decades city NPC cannot open regional travel")
    $map_factory.setup(original[0])
    $game_player.moveto(original[1], original[2])

    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Travel changed the initial region")
    require!($player.party.first.equal?(pokemon), "Travel replaced the party Pokémon")

    # Emulate the already-audited Decades ending only in the throwaway CI
    # session so we can verify a two-way route without playing the full story.
    league = BlueRegionData::REGISTRY["decades"]["league"]
    $player.badges[league["badge"]] = true
    $game_switches[league["switch"]] = true
    # An actual Legendary in the native storage implementation must be
    # deposited before arriving in Kanto without eight local badges.
    special = Pokemon.new(:MEWTWO, 50)
    $player.party << special
    status, reservations = BlueRegionTravel.preview(BlueRegions.snapshot, "KANTO")
    require!(status == :ok && reservations.length == 1, "Special travel reservation missing")
    reserved = reservations.first.last
    require!(BlueRegionTravel.special?(special), "Mewtwo not classified as Legendary")
    stage("travel_decades_to_kanto")
    travel_from_real_agent!("KANTO")
    # Returning visitors arrive outdoors in Pallet beside the regional NPC;
    # only a NEW GAME spawns in the player's upstairs bedroom.
    pallet_point = BlueRegionTravel.kanto_town_point
    require!(pallet_point && $game_map.map_id == pallet_point[0] &&
             [$game_player.x, $game_player.y] == pallet_point[1, 2],
             "Kanto return must arrive in Pallet Town, not inside the bedroom")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Return state was not committed")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Return changed the starting region")
    require!($PokemonGlobal.blue_regions["travel_history"].length == 2, "Two-way history missing")
    require!($player.party == [pokemon], "Special was not removed from active party")
    boxed = $PokemonStorage[reserved[0], reserved[1]]
    require!(boxed.equal?(special), "Legendary was not deposited in the reserved PC slot")
    require!(BlueRegionTravel.restricted?(boxed), "Kanto did not lock Mewtwo before eight badges")
    restored_pc = Marshal.load(Marshal.dump($PokemonStorage))
    restored_pc[reserved[0], reserved[1]] = nil
    require!(Marshal.dump(restored_pc) == original_pc, "Other PC data changed during travel")
    require!($player.money == original_money, "Travel altered player money")
    require!(Marshal.dump($bag) == original_bag, "Travel altered the bag")
    require!(Marshal.dump($player.pokedex) == original_dex, "Travel altered Pokédex")

    stage("before_kanto_save")
    slot = "Kanto Integration CI"
    require!(Game.save(slot), "Kanto integrated save failed")
    saved = SaveData.read_from_file(SaveData.get_full_path(slot))
    stage("before_kanto_reload")
    SaveData.mark_values_as_unloaded
    Game.load(saved)
    stage("after_kanto_reload")
    require!($game_map.map_id == BlueRegionTravel.kanto_town_point[0],
             "Kanto save did not restore the Pallet arrival map")
    require!($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto save lost its origin")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region did not survive save")
    require!($PokemonGlobal.blue_regions["travel_history"].length == 2, "Travel history lost on save/reload")
    require!($player.party.first.species == :BULBASAUR, "Team changed after save/reload")
    require!($PokemonStorage[reserved[0], reserved[1]]&.species == :MEWTWO,
             "Boxed Legendary did not survive reload")
    require!($PokemonStorage[0,0]&.species == :MEWTWO, "Gift was lost after travel/save")
    require!(BlueRegions.local_achievements($PokemonGlobal.blue_regions,"KANTO").include?("BOULDER"),
             "Local Kanto badge did not survive reload")
    File.write("Data/blue-kanto-integrated-proof.txt",
               "Two-way transfer, native PC gift and Legendary deposit, Boulder HM and unique badge, same-save reload OK; League simulated only in CI")
    stage("completed")
  end
end
