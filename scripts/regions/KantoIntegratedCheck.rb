# CI-only native proof. The original Decades intro waits for input and must
# remain a MANUAL check, not a second headless Game.start_new call.
module KantoIntegratedCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  def self.stage(label)
    File.write("Data/blue-kanto-integrated-stage.txt", label)
  end

  # Headless native CI cannot click the screen. Its transport fixture only
  # impersonates the event after finding the actual NPC in a valid origin
  # town; production authorization remains unchanged and is tested below.
  def self.travel_from_verified_agent(target)
    state = BlueRegions.snapshot
    require!(BlueRegionTravel.at_departure_town?(state),
             "Regional test attempted travel outside the departure town")
    name = case state["current"]
           when "KANTO" then BlueRegionTravel::KANTO_AGENT_NAME
           when "DECADES" then BlueRegionTravel::DECADES_AGENT_NAME
           else raise "Unsupported native CI departure region"
           end
    npc = $game_map.events.values.find { |event| event.name == name }
    require!(npc && npc.list.any? { |op|
      op.code == 355 && op.parameters.first.to_s == "BlueRegionTravel.agent(true)"
    }, "Native origin map has no interactable verified regional agent")
    require!(!BlueRegionTravel.travel(target, true),
             "Direct regional travel bypassed the NPC event")
    BlueRegionTravel.instance_variable_set(:@npc_event_context, true)
    begin
      BlueRegionTravel.perform(state, target)
    ensure
      BlueRegionTravel.instance_variable_set(:@npc_event_context, false)
    end
  end

  # Compare the two actual Sprite_Character objects in the integrated game,
  # on the same map and viewport, before and after save/reload. No fake NPC,
  # asset replacement, extra zoom, or mutation of the rival.
  def self.compare_gary_scale(label)
    previous_map = $game_map.map_id
    previous_xy = [$game_player.x,$game_player.y]
    previous_direction = $game_player.direction
    viewport = nil
    sprites = []
    lab = BlueKantoPilot.kanto_map_id(6)
    require!(lab, "Integrated Gary lab ID missing")
    $map_factory.setup(lab)
    gary = $game_map.events[14]
    require!(gary && gary.character_name == BlueKantoPilot.cerulean_rival_graphic,
      "Integrated Gary reference event missing")
    $game_player.moveto(gary.x+1,gary.y)
    $game_player.turn_down
    viewport = Viewport.new(0,0,Graphics.width,Graphics.height)
    [$game_player,gary].each do |actor|
      sprite = Sprite_Character.new(viewport,actor)
      sprites << sprite
      2.times { sprite.update }
    end
    player_sprite,gary_sprite = sprites
    values = sprites.map do |sprite|
      rect = sprite.src_rect
      bounds = BlueKantoPilot.overworld_frame_bounds(sprite.bitmap,rect.x,rect.y,rect.width,rect.height)
      require!(bounds,"Integrated visible frame missing")
      height = bounds[1]-bounds[0]+1
      {"height"=>height,"zoom"=>sprite.zoom_y,"rendered"=>height*sprite.zoom_y,
       "frame_height"=>rect.height,"pivot_y"=>sprite.oy,
       "foot_offset"=>(bounds[1]+1-sprite.oy)*sprite.zoom_y}
    end
    player,reference = values
    # Capture is 2x the native reference (80 vs 40). At that zoom a
    # difference greater than one displayed pixel fails this regression.
    require!(((player["rendered"]-reference["rendered"])*2).abs <= 1.0,
      "Integrated active player frame does not match Gary: #{values.inspect}")
    require!((gary_sprite.zoom_x-1.0).abs < 0.01 &&
      (gary_sprite.zoom_y-1.0).abs < 0.01 &&
      (player_sprite.zoom_x-player_sprite.zoom_y).abs < 0.01,
      "Gary changed or player aspect ratio distorted")
    # Preserve the engine's tile/feet anchor; the sprite's alpha padding
    # may differ by pose. Require the feet to remain within two native pixels.
    require!((player["foot_offset"]-reference["foot_offset"]).abs <= 2.0,
      "Integrated player feet drifted from Gary: #{values.inspect}")
    old_zoom = [1.0,40.0/player["frame_height"]].min
    report = {"label"=>label,"capture_npc_px"=>80,"capture_player_px"=>62,
      "capture_factor"=>80.0/62,"player"=>player,"gary"=>reference,
      "old_rendered_at_2x"=>player["height"]*old_zoom*2,
      "new_rendered_at_2x"=>player["rendered"]*2,
      "reference_rendered_at_2x"=>reference["rendered"]*2,
      "same_map"=>lab,"native_sprites"=>true}
    File.open("Data/blue-kanto-gary-scale-integrated.txt","a") { |file|
      file.puts("KANTO_GARY_VISIBLE_PLAYER_SCALE_INTEGRATED_REPORT:#{report.inspect}")
      file.puts("KANTO_GARY_VISIBLE_PLAYER_SCALE_INTEGRATED_OK:#{label}")
    }
  ensure
    sprites.each { |sprite| sprite.dispose unless sprite.disposed? }
    viewport.dispose if viewport && !viewport.disposed?
    if previous_map
      $map_factory.setup(previous_map)
      $game_player.moveto(*previous_xy)
      case previous_direction
      when 2 then $game_player.turn_down
      when 4 then $game_player.turn_left
      when 6 then $game_player.turn_right
      when 8 then $game_player.turn_up
      end
    end
  end

  def self.run
    stage("bootup")
    SaveData.initialize_bootup_values
    spawn = BlueRegionStart.kanto_spawn
    require!(spawn && spawn.length == 3, "Integrated Kanto marker/map missing")
    require!(BlueRegionStart.kanto_integrated?,
             "Integrated Kanto ready gate rejected installed 156-map registry")
    registry = BlueRegionStart.kanto_compact_maps(spawn)
    require!(registry && registry.size == 156 &&
             (68..71).all? { |source| registry[source.to_s] == BlueKantoPilot.kanto_map_id(source) },
             "Integrated Vermilion registry missing or inconsistent")
    stage("main_title_kanto")
    require!(defined?(BlueKantoTitle), "Testar Kanto title menu plugin not loaded")
    require!(PokemonLoad_Scene.ancestors.include?(BlueKantoTitle::Scene),
             "Native main load scene does not include Kanto and Johto test options")
    commands = [" <- Decades Save -> ", _INTL("New Game"), _INTL("Options"), _INTL("Quit Game")]
    indices = BlueKantoTitle.command_order(commands, true)
    require!(indices == [0, 1, :blue_test_kanto, :blue_test_johto, :blue_test_hoenn, 2, 3],
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
    File.delete("Data/blue-kanto-gary-scale-integrated.txt") if File.file?("Data/blue-kanto-gary-scale-integrated.txt")
    compare_gary_scale("new_game")
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
    require!(BlueRegionTravel.installed? && BlueRegionalPolicy.state &&
             BlueRegionalPolicy.state["current"] == "KANTO",
             "Integrated Kanto regional policy unavailable after native new game")
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

    [41,42,43].zip([:CHARMELEON,:WARTORTLE,:IVYSAUR]).each do |version,evolution|
      data = GameData::Trainer.get(:BLUE_KANTO_RIVAL,"Blue",version)
      require!(data.pokemon.map { |pk| pk[:species] } == [:PIDGEOTTO,:RATICATE,:KADABRA,evolution] &&
        data.to_trainer.party.length == 4, "K03-C integrated rival profile #{version} invalid")
    end
    puts "KANTO_K03C_INTEGRATED_RIVAL_PROFILES_OK"
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
    # The Boulder Badge unlocks only the BADGE gate.  FRLG HM05 must still
    # be obtained and an able, compatible party Pokemon must be present.
    # A fresh Kanto New Game must not be handed Flash by CI or by the badge.
    require!(!BlueRegionalPolicy.hm_owned?(:FLASH),
             "Fresh Kanto unexpectedly owns HM05 before the field pickup")
    require!(BlueRegionalPolicy.field_result(:FLASH) == :hm,
             "Boulder did not advance Flash to its required HM05 gate")
    require!(BlueRegionalPolicy.field_result(:SURF) == :badge, "Surf unlocked without Soul Badge")
    require!(BlueRegionalPolicy.field_result(:CUT) == :badge, "K03-C Cut without Cascade")
    # Isolated temporary state, bag and team; do not change the subsequent
    # integrated travel fixture's badge/crystal counts.
    cut_state = Marshal.load(Marshal.dump(current_state))
    original_party = $player.party.dup
    cut_item = [:HM01,:HMCUT].find { |id| GameData::Item.exists?(id) }
    require!(cut_item && !$bag.has?(cut_item), "K03-C unexpected Cut HM in fresh bag")
    begin
      $PokemonGlobal.blue_regions = cut_state
      BlueRegions.award(cut_state,"KANTO","CASCADE")
      require!(BlueRegionalPolicy.field_result(:CUT) == :hm,"K03-C missing Cut HM accepted")
      require!($bag.add(cut_item,1),"K03-C unable to add temporary HM")
      $player.party.replace([Pokemon.new(:PIDGEY,5)])
      require!(BlueRegionalPolicy.field_result(:CUT) == :pokemon,"K03-C incompatible Pokemon accepted")
      $player.party.replace([Pokemon.new(:BULBASAUR,5)])
      require!(BlueRegionalPolicy.field_result(:CUT) == :allowed,"K03-C eligible Cut blocked")
    ensure
      $bag.remove(cut_item,1) if cut_item && $bag.has?(cut_item)
      $player.party.replace(original_party)
      $PokemonGlobal.blue_regions = current_state
    end
    puts "KANTO_K03C_INTEGRATED_CUT_POLICY_OK"
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
    # The Pallet agent, not the upstairs bedroom, is the entry point.
    # Reject old saves' Decades intro coordinates as a travel destination.
    $map_factory.setup(town_map)
    $game_player.moveto(18, 8)
    decades_destination = BlueRegionTravel.destination(BlueRegions.snapshot, "DECADES")
    require!(decades_destination && decades_destination[0] == BlueRegionTravel.decades_city_map_id &&
             decades_destination[0] != original[0],
             "Kanto travel selected Decades introduction instead of Cherryhill")
    stage("travel_kanto_to_decades")
    require!(travel_from_verified_agent("DECADES"),
             "Kanto->Decades travel did not complete")
    require!($game_map.map_id == decades_destination[0] &&
             [$game_player.x, $game_player.y] == decades_destination[1, 2],
             "Kanto->Decades travel missed the verified Cherryhill arrival")
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
    require!(travel_from_verified_agent("KANTO"),
             "Decades->Kanto travel did not complete")
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
    compare_gary_scale("save_reload")
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
