# Runs inside the copied mkxp-z game, after the native compiler.
module KantoNativeCheck
  def self.require!(condition, message)
    raise message unless condition
  end

  # A read-only source sign or a physical CutTree is permitted as an
  # *additional* event on functional maps. Keep all story/event whitelists
  # strict and reject foreign scripts, extra warps, items or trainers.
  def self.passive_field_event?(event)
    return false unless event && event.trigger == 0
    commands = Array(event.list)
    scripts = commands.select { |row| row.code == 355 }.map { |row| row.parameters[0].to_s }
    if event.name.match?(/(?i)(?:cut[ _-]*tree|cuttable[ _-]*tree)/)
      return commands.any? { |row| row.code == 111 && row.parameters[1].to_s == "pbCut" } &&
             scripts == ["pbSmashThisEvent"] &&
             commands.all? { |row| [0, 111, 355, 412].include?(row.code) }
    end
    if event.name.match?(/(?i)(?:sign|notice|placard|plaque|board|poster|billboard|placa)/)
      return !scripts.empty? &&
             scripts.all? { |script| script.start_with?("BlueKantoPilot.npc_dialogue(") } &&
             commands.all? { |row| [0, 355].include?(row.code) }
    end
    false
  end

  def self.whitelisted_core?(events, required, other_allowed = [])
    keys = events.keys
    (required - keys).empty? &&
      (keys - required - other_allowed).all? { |event_id| passive_field_event?(events[event_id]) }
  end

  # K00-C: use the actual loaded RXDATA, native collision and compiled
  # trainers. Battle outcomes and dialogue choices remain controlled in CI.
  # These paths are engine collision witnesses, not manual keyboard play.
  def self.north_component(map_id, point)
    $map_factory.setup(map_id)
    $game_map.events.each_value { |event| event.refresh }
    $game_player.moveto(*point)
    require!(point[0] >= 0 && point[1] >= 0 &&
             point[0] < $game_map.width && point[1] < $game_map.height,
             "K00-C invalid collision anchor #{map_id}:#{point.inspect}")
    directions = {2=>[0,1], 4=>[-1,0], 6=>[1,0], 8=>[0,-1]}
    opposite = {2=>8,4=>6,6=>4,8=>2}
    seen = {point=>0}
    queue = [point]
    cursor = 0
    while cursor < queue.length
      x,y = queue[cursor]
      cursor += 1
      directions.each do |dir,(dx,dy)|
        nx,ny = x+dx,y+dy
        next if nx < 0 || ny < 0 || nx >= $game_map.width || ny >= $game_map.height
        next if seen.key?([nx,ny])
        # Game_Player is a live native object; synchronize its current tile
        # before each directional probe, including the reverse check.
        $game_player.moveto(x,y)
        next unless $game_player.passable?(x,y,dir)
        $game_player.moveto(nx,ny)
        next unless $game_player.passable?(nx,ny,opposite.fetch(dir))
        seen[[nx,ny]] = seen[[x,y]] + 1
        queue << [nx,ny]
      end
    end
    $game_player.moveto(*point)
    probes = directions.map do |dir,(dx,dy)|
      [dir,$game_player.passable?(point[0],point[1],dir)]
    end
    puts "KANTO_K00_COLLISION_COMPONENT:#{[map_id,point,seen.length,probes].inspect}"
    require!(seen.length > 1, "K00-C isolated anchor #{map_id}:#{point.inspect}; forward=#{probes.inspect}")
    seen
  end

  def self.north_edge_cell(map_id, point, dir)
    $map_factory.setup(map_id)
    $game_player.moveto(*point)
    $game_player.passable?(point[0],point[1],dir)
  end

  def self.north_witness(map_a, comp_a, map_b, axis)
    $map_factory.setup(map_a)
    aw,ah = $game_map.width,$game_map.height
    $map_factory.setup(map_b)
    bw,bh = $game_map.width,$game_map.height
    # FRLG source 53,South,0,39,North,0 and 54,West,0,53,East,0.
    # Both have zero offset in the actual installed PBS.
    if axis == :north
      candidates = (0...[aw,bw].min).map { |x| [[x,0],[x,bh-1]] }
      forward,reverse = 8,2
    else
      candidates = (0...[ah,bh].min).map { |y| [[aw-1,y],[0,y]] }
      forward,reverse = 6,4
    end
    candidates.each do |a,b|
      next unless comp_a.key?(a)
      next unless north_edge_cell(map_a,a,forward) && north_edge_cell(map_b,b,reverse)
      # Start the destination component at the actual matched seam cell.
      # Do not substitute another connected area if this cell is isolated.
      return [map_a,a,map_b,b,comp_a[a]]
    end
    raise "K00-C no bidirectional native collision seam #{map_a}/#{map_b}"
  end

  def self.north_event_reachable?(component, event)
    return false unless event
    component.keys.any? { |x,y| (x-event.x).abs + (y-event.y).abs <= 1 }
  end

  def self.north_callback!(event, expected)
    require!(event && Array(event.list).any? { |op| op.code == 355 &&
               op.parameters[0].to_s == expected }, "K00-C missing active callback #{expected}")
  end

  def self.north_transfer!(event, destination)
    op = event && Array(event.list).find { |cmd| cmd.code == 201 && cmd.parameters[0] == 0 &&
                                        cmd.parameters[1] == destination }
    require!(op, "K00-C real transfer to #{destination} absent")
    op.parameters[2,2]
  end

  def self.north_story(battle_calls, losses_remaining)
    city,gym,bridge,route,cottage = [39,42,53,54,55].map { |id| BlueKantoPilot.kanto_map_id(id) }
    require!([city,gym,bridge,route,cottage].all?, "K00-C missing installed source IDs")
    state = BlueKantoPilot.progress
    $map_factory.setup(gym)
    [[11,:BLUE_KANTO_SWIMMER,"Luis"],[16,:BLUE_KANTO_PICNICKER,"Diana"]].each do |id,type,name|
      key = "KANTO_042_%03d" % id
      north_callback!($game_map.events[id],
        "BlueKantoPilot.cerulean_gym_trainer(:#{type}, \"#{name}\", \"#{key}\", #{id})")
      require!(GameData::Trainer.get(type,name,0).pokemon.length > 0, "#{name} compiled team missing")
      losses_remaining[name] = 1
      require!(!BlueKantoPilot.cerulean_gym_trainer(type,name,key,id), "#{name} loss marked as win")
      require!(!$game_self_switches[[gym,id,"A"]], "#{name} loss changed page")
      require!(BlueKantoPilot.cerulean_gym_trainer(type,name,key,id), "#{name} retry failed")
      require!($game_self_switches[[gym,id,"A"]] && state["pilot_wins"].include?(key), "#{name} win not persisted")
      BlueKantoPilot.cerulean_gym_trainer(type,name,key,id)
      require!(battle_calls.count { |row| row[0] == type && row[1] == name } == 2, "#{name} repeated")
    end
    require!($game_self_switches[[gym,1,"A"]], "Misty victory page was not activated")
    $map_factory.setup(city)
    require!(!BlueKantoPilot.cerulean_rival_graphic.to_s.empty?, "Gary graphic missing")
    require!(!$game_map.events[32].character_name.to_s.empty?, "Gary invisible before battle")
    losses_remaining["Blue"] = 1
    require!(!BlueKantoPilot.cerulean_rival && !state["pilot_cerulean_rival"], "Gary false win")
    require!(BlueKantoPilot.cerulean_rival && state["pilot_cerulean_rival"], "Gary retry failed")
    require!($game_map.events[32].character_name.to_s.empty?, "Gary not hidden after win")
    require!(battle_calls.count { |row| row == [:BLUE_KANTO_RIVAL,"Blue",31] } == 2, "Gary team/retry mismatch")
    $map_factory.setup(bridge)
    nugget_before = $bag.quantity(:NUGGET)
    require!(!BlueKantoPilot.nugget_bridge_rocket, "Rocket accepted before five trainers")
    [[1,:BLUE_KANTO_CAMPER,"Ethan"],[2,:BLUE_KANTO_LASS,"Reli"],
     [3,:BLUE_KANTO_YOUNGSTER,"Timmy"],[4,:BLUE_KANTO_LASS,"Ali"],
     [5,:BLUE_KANTO_BUGCATCHER,"Cale"]].each do |id,type,name|
      key = "KANTO_053_%03d" % id
      north_callback!($game_map.events[id], "BlueKantoPilot.battle(:#{type}, \"#{name}\", \"#{key}\")")
      require!(BlueKantoPilot.battle(type,name,key), "Bridge trainer #{name} failed")
      require!(BlueKantoPilot.sync_trainer_event(key,name,id), "Bridge trainer switch #{id} missing")
    end
    north_callback!($game_map.events[6], "BlueKantoPilot.nugget_bridge_rocket")
    losses_remaining["Grunt"] = 1
    require!(!BlueKantoPilot.nugget_bridge_rocket, "Rocket defeat became victory")
    require!($bag.quantity(:NUGGET) == nugget_before+1 && !state["pilot_wins"].include?("KANTO_053_006"),
             "Nugget must be granted once before Rocket victory")
    require!(BlueKantoPilot.nugget_bridge_rocket, "Rocket retry failed")
    require!($bag.quantity(:NUGGET) == nugget_before+1 && $game_self_switches[[bridge,6,"A"]],
             "Rocket prize duplicated or switch missing")
    $map_factory.setup(route)
    [[1,:BLUE_KANTO_HIKER,"Franklin"],[2,:BLUE_KANTO_HIKER,"Wayne"],[3,:BLUE_KANTO_HIKER,"Nob"],
     [6,:BLUE_KANTO_LASS,"Haley"],[7,:BLUE_KANTO_YOUNGSTER,"Chad"],[8,:BLUE_KANTO_CAMPER,"Flint"],
     [9,:BLUE_KANTO_YOUNGSTER,"Joey"],[10,:BLUE_KANTO_YOUNGSTER,"Dan"],[11,:BLUE_KANTO_PICNICKER,"Kelsey"]].each do |id,type,name|
      key = "KANTO_054_%03d" % id
      north_callback!($game_map.events[id], "BlueKantoPilot.battle(:#{type}, \"#{name}\", \"#{key}\")")
      require!(BlueKantoPilot.battle(type,name,key), "Route25 trainer #{name} failed")
      require!(BlueKantoPilot.sync_trainer_event(key,name,id), "Route25 switch #{id} missing")
    end
    # Native collision components and real registered connection rows.
    rows = File.readlines("PBS/map_connections_kanto.txt").map { |line| line.split("#",2)[0].strip }
    require!(rows.include?("#{bridge},South,0,#{city},North,0") &&
             rows.include?("#{route},West,0,#{bridge},East,0"),
             "K00-C source seam registry changed")
    # Use the actual Center exit's authored arrival rather than an
    # experimental teleport coordinate that may land on an obstacle.
    center = BlueKantoPilot.kanto_map_id(40)
    $map_factory.setup(center)
    center_exit = $game_map.events.values.find { |ev| Array(ev.list).any? { |op|
      op.code == 201 && op.parameters[0] == 0 && op.parameters[1] == city } }
    city_landing = north_transfer!(center_exit,city)
    puts "KANTO_K00_CITY_CENTER_EXIT:#{[center,center_exit.id,city,city_landing].inspect}"
    a = north_component(city,city_landing)
    seam1 = north_witness(city,a,bridge,:north)
    puts "KANTO_K00_NATIVE_SEAM:#{seam1.inspect}"
    b = north_component(bridge,seam1[3])
    seam2 = north_witness(bridge,b,route,:east)
    puts "KANTO_K00_NATIVE_SEAM:#{seam2.inspect}"
    c = north_component(route,seam2[3])
    $map_factory.setup(bridge)
    require!(north_event_reachable?(b,$game_map.events[6]), "Rocket unreachable from bridge component")
    $map_factory.setup(route)
    door = $game_map.events[18]
    require!(north_event_reachable?(c,door), "Bill door unreachable from Route25 component")
    landing = north_transfer!(door,cottage)
    d = north_component(cottage,landing)
    north_callback!($game_map.events[3],"BlueKantoPilot.bill_request")
    north_callback!($game_map.events[4],"BlueKantoPilot.bill_computer")
    require!(north_event_reachable?(d,$game_map.events[3]) &&
             north_event_reachable?(d,$game_map.events[4]), "Bill or PC unreachable")
    require!(!BlueKantoPilot.bill_computer && !BlueKantoPilot.bill_reward, "Bill quest bypassed")
    BlueKantoPilot.bill_request
    require!(state["pilot_bill_agreed"], "Bill request not recorded")
    require!(BlueKantoPilot.bill_computer, "Bill restoration failed")
    $game_map.events.each_value { |event| event.refresh }
    north_callback!($game_map.events[8],"BlueKantoPilot.bill_reward")
    d = north_component(cottage,landing)
    require!(north_event_reachable?(d,$game_map.events[8]), "Restored Bill unreachable")
    ticket_item = :BLUE_KANTO_SSTICKET
    ticket_data = GameData::Item.get(ticket_item)
    require!(ticket_data.is_key_item? && ticket_data.pocket == 8 &&
             BlueRegionTravel.regional_item?(ticket_item), "K00-C native regional ticket catalog invalid")
    ticket_before = $bag.quantity(ticket_item)
    require!(BlueKantoPilot.bill_reward && BlueKantoPilot.bill_reward, "Bill reward failed")
    require!(state["pilot_bill_ticket"] && state["pilot_ss_ticket"], "Ticket flag absent")
    require!($bag.quantity(ticket_item) == ticket_before+1 &&
             state["pilot_bill_ticket_item_granted"], "Ticket duplicated or missing")
    # Reconstruct the old digital-permit state in this disposable native
    # game, and prove one-time conversion using the actual Bag.
    require!($bag.remove(ticket_item,1), "K00 legacy ticket fixture removal failed")
    state.delete("pilot_bill_ticket_item_granted")
    require!(state["pilot_bill_ticket"] && state["pilot_ss_ticket"], "Legacy permission lost")
    require!(BlueKantoPilot.bill_reward && BlueKantoPilot.bill_reward &&
             $bag.quantity(ticket_item) == ticket_before+1, "Legacy digital ticket migration failed")
    require!(BlueRegionTravel.local_bag_contents($bag)["items"].include?([ticket_item,1]),
             "Ticket not recognized by regional isolation")
    exit_event = $game_map.events.values.find { |ev| Array(ev.list).any? { |op|
      op.code == 201 && op.parameters[0] == 0 && op.parameters[1] == route } }
    require!(north_event_reachable?(d,exit_event), "Cottage exit unreachable")
    return_landing = north_transfer!(exit_event,route)
    require!(c.key?(return_landing) || c.keys.any? { |x,y|
      (x-return_landing[0]).abs+(y-return_landing[1]).abs <= 1 },
      "Cottage return landing disconnected")
    report = {"mode"=>"native_collision_and_scripted_battle_results",
      "manual_gameplay"=>false,"map_ids"=>[city,gym,bridge,route,cottage],
      "city_center_landing"=>city_landing,"collision_components"=>[a.length,b.length,c.length,d.length],
      "bidirectional_seams"=>[seam1,seam2],"bill_landing"=>landing,
      "bill_return"=>return_landing,"nugget_quantity"=>$bag.quantity(:NUGGET),
      "ticket_mode"=>"native_item","ticket_id"=>ticket_item.to_s,
      "ticket_quantity"=>$bag.quantity(ticket_item),"legacy_permit_upgrade"=>true,
      "regional_key_item"=>true,
      "gary_retry"=>true,"bill_completed"=>true}
    $map_factory.setup(gym)
    report
  end

  # K01-A: real native event pages, save files and bag/party in the disposable
  # pilot. Only the confirmation dialogue is controlled; no user save is read.
  def self.opening_snapshot(label)
    state = BlueKantoPilot.progress
    row = {"label"=>label,"map_id"=>$game_map.map_id,
      "position"=>[$game_player.x,$game_player.y],
      "party"=>$player.party.map { |pkmn| [pkmn.species.to_s,pkmn.level] },
      "starter"=>state["pilot_starter"],"profile_pending"=>state["pilot_profile_pending"],
      "region"=>state["current"],"potions"=>$bag.quantity(:POTION),
      "pokeballs"=>$bag.quantity(:POKEBALL)}
    puts "KANTO_K01A_SAVE_STATE:#{row.inspect}"
    File.open("Data/blue-kanto-k01a-state-trace.txt","a") { |file| file.puts(row.inspect) }
    row
  end

  def self.starter_opening_proof(lab)
    state = BlueKantoPilot.progress
    require!(state["pilot_profile_pending"] && !BlueKantoPilot.starter &&
             $player.party.empty?, "K01-A new-game starter state invalid")
    require!($game_map.map_id == lab, "K01-A not in the laboratory")
    cases = [[18,:BULBASAUR],[19,:SQUIRTLE],[20,:CHARMANDER]]
    cases.each do |id,species|
      event = $game_map.events[id]
      north_callback!(event,"BlueKantoPilot.choose_starter_ball(:#{species})")
      require!(event.trigger == 0 && !event.character_name.to_s.empty? &&
               !$game_self_switches[[lab,id,"A"]], "K01-A missing visible starter #{species}")
    end
    # A separate native baseline lets us test every choice with the actual
    # Pokémon, Bag, self switches and Game.save/Game.load, not a fake party.
    baseline = "K01 A Native Unchosen"
    # The previous proof entered the lab by QA map setup without executing
    # the profile event. Complete its real handler with a controlled choice
    # rather than saving an impossible pre-profile state inside Oak's lab.
    # Only the interactive character selection call is replaced.
    original_profile = Object.instance_method(:pbCharacterSelect)
    begin
      Object.send(:define_method,:pbCharacterSelect) { |*args| nil }
      BlueKantoPilot.choose_profile
    ensure
      Object.send(:define_method,:pbCharacterSelect,original_profile)
    end
    require!(!BlueKantoPilot.progress["pilot_profile_pending"], "K01-A profile handler did not finish")
    $game_player.moveto(6,12)
    before = opening_snapshot("unchosen_before_save")
    require!(Game.save(baseline), "K01-A initial CI save failed")
    baseline_file = SaveData.get_full_path(baseline)
    require!(File.file?(baseline_file), "K01-A baseline save file absent")
    # Preserve the exact file bytes, and reject any unexpected rewrite of
    # the baseline while testing other slots.
    baseline_bytes = File.binread(baseline_file)
    potion_before = $bag.quantity(:POTION)
    ball_before = $bag.quantity(:POKEBALL)
    rows = []
    # Restore Bulbasaur last because the existing full-campaign proof uses it.
    [cases[1],cases[2],cases[0]].each do |id,species|
      require!(File.binread(baseline_file) == baseline_bytes, "K01-A baseline file unexpectedly rewritten")
      saved = SaveData.read_from_file(baseline_file)
      Game.load(saved)
      actual = opening_snapshot("unchosen_reload_#{species}")
      require!(actual["map_id"] == lab, "K01-A baseline map mismatch: expected #{lab}, got #{actual.inspect}")
      require!(actual["party"].empty?, "K01-A baseline party mismatch: #{actual.inspect}")
      require!(!actual["starter"], "K01-A baseline starter flag mismatch: #{actual.inspect}")
      require!(actual["region"] == before["region"] && !actual["profile_pending"],
               "K01-A baseline regional/profile state mismatch: #{actual.inspect}")
      Object.send(:define_method,:pbConfirmMessage) { |*args| false }
      BlueKantoPilot.choose_starter_ball(species)
      require!($player.party.empty? && !BlueKantoPilot.starter &&
               $bag.quantity(:POTION) == potion_before &&
               cases.none? { |eid,_| $game_self_switches[[lab,eid,"A"]] },
               "K01-A cancelled choice changed party, rewards or switches")
      Object.send(:define_method,:pbConfirmMessage) { |*args| true }
      BlueKantoPilot.choose_starter_ball(:PIKACHU)
      require!($player.party.empty? && !BlueKantoPilot.starter,
               "K01-A invalid starter accepted")
      BlueKantoPilot.choose_starter_ball(species)
      require!($player.party.length == 1 && $player.party.first.species == species &&
               $player.party.first.level == 5 && BlueKantoPilot.starter == species,
               "K01-A wrong native starter #{species}")
      cases.each do |eid,other|
        ev = $game_map.events[eid]
        require!($game_self_switches[[lab,eid,"A"]] && ev.character_name.to_s.empty?,
                 "K01-A Poké Ball #{eid} remains visible after selection")
        BlueKantoPilot.choose_starter_ball(other)
      end
      require!($player.party.length == 1 && $player.party.first.species == species &&
               $bag.quantity(:POTION) == potion_before+2 &&
               $bag.quantity(:POKEBALL) == ball_before &&
               !BlueKantoPilot.forest_unlocked?,
               "K01-A repeated starter or early parcel reward")
      slot = "K01 A Native #{species}"
      require!(Game.save(slot), "K01-A selected starter save failed")
      opening_snapshot("selected_before_reload_#{species}")
      Game.load(SaveData.read_from_file(SaveData.get_full_path(slot)))
      opening_snapshot("selected_after_reload_#{species}")
      require!($game_map.map_id == lab && $player.party.length == 1 &&
               $player.party.first.species == species && BlueKantoPilot.starter == species &&
               $bag.quantity(:POTION) == potion_before+2 &&
               $bag.quantity(:POKEBALL) == ball_before &&
               cases.all? { |eid,_| $game_self_switches[[lab,eid,"A"]] },
               "K01-A selected starter/save switches did not survive reload")
      cases.each { |eid,_| $game_map.events[eid].refresh }
      require!(cases.all? { |eid,_| $game_map.events[eid].character_name.to_s.empty? },
               "K01-A Poké Balls reappeared after reload")
      rows << {"species"=>species.to_s,"event_id"=>id,"level"=>5,
               "cancel_no_change"=>true,"invalid_choice_rejected"=>true,
               "party_count"=>1,"potion_delta"=>2,"pokeball_delta"=>0,
               "all_balls_hidden"=>true,"duplicate_rejected"=>true,"save_reload"=>true}
    end
    {"status"=>"PASS","mode"=>"native_party_bag_event_pages_save_reload",
     "manual_gameplay"=>false,"profile_ui_executed"=>false,"profile_handler_executed"=>true,
     "lab_map_id"=>lab,"variants"=>rows}
  ensure
    Object.send(:define_method,:pbConfirmMessage) { |*args| true }
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
    require!(labels.length == 67 && labels.any? { |row| row.include?("Misty") } &&
             labels.any? { |row| row.include?("Nugget Bridge") } &&
             labels.any? { |row| row.include?("Casa do Bill") } &&
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
    opening_report = starter_opening_proof(lab)
    require!($player.party.first&.species == :BULBASAUR, "Starter proof did not leave Bulbasaur for campaign")
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
    require!(mart_visits.empty?,
             "Viridian Mart opened before Oak received the parcel")
    BlueKantoPilot.choose_starter
    require!(BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak did not accept the parcel upon return")
    require!(BlueKantoPilot.forest_unlocked?, "Forest remained blocked after parcel delivery")
    require!($bag.quantity(:POKEBALL) == starting_balls + 5,
             "Oak must award exactly five Poke Balls, not the starter event")
    require!($player.has_pokedex, "Oak parcel delivery did not unlock the Pokedex") if $player.respond_to?(:has_pokedex)
    BlueKantoPilot.choose_starter
    require!($bag.quantity(:POKEBALL) == starting_balls + 5,
             "Returning to Oak duplicated the parcel reward")
    BlueKantoPilot.viridian_mart
    BlueKantoPilot.viridian_mart
    require!(mart_visits.length == 2 &&
             BlueKantoPilot.progress["pilot_oak_parcel_delivered"],
             "Viridian Mart must open only after Oak receives his parcel")
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
    # Native Cerulean quest proof begins after confirming Cascade cannot
    # substitute for Bill; leave the existing badge checks intact below.
    misty_map = BlueKantoPilot.kanto_map_id(42)
    $map_factory.setup(misty_map)
    north_callback!($game_map.events[1],
      'BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001")')
    losses_remaining["Misty"] = 1
    require!(!BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001"),
             "Misty loss marked as win")
    require!(!BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("CASCADE"),
             "Misty defeat granted Cascade")
    require!(!$game_self_switches[[misty_map,1,"A"]], "Misty defeat changed event page")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001")
    require!(BlueKantoPilot.sync_trainer_event("KANTO_042_001","Misty",1),
             "Misty victory switch missing")
    require!(BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO") == ["BOULDER","CASCADE"],
             "Cascade Badge not awarded uniquely")
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER_MISTY, "Misty", "KANTO_042_001")
    require!(battle_calls.count { |row| row[1] == "Misty" } == 2,
             "Misty repeated after victory")
    require!(BlueRegions.crystal_total(BlueKantoPilot.progress, 2) == 4,
             "Two Kanto milestones were double-counted or omitted")
    # Cerulean north: Cascade alone must NOT give an S.S. Ticket.
    # Simulate the player's decision to help Bill after verifying the real
    # cottage events and completing the native PC/reward callbacks. This
    # fixture does not impersonate a manual JoiPlay touchscreen playtest.
    BlueKantoPilot.ticketmaster
    require!(!BlueKantoPilot.progress["pilot_ss_ticket"],
             "Harbor issued a ticket without Bill's Route 25 quest")
    north_report = north_story(battle_calls, losses_remaining)
    BlueKantoPilot.ticketmaster
    require!(BlueKantoPilot.progress["pilot_ss_ticket"] == true,
             "Vermilion ticket missing after Bill's quest")
    # Lt. Surge grants exactly one Thunder Badge after a legitimate victory.
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
    require!(whitelisted_core?($game_map.events, [3, 20]) &&
             $game_map.events[3].trigger == 1 &&
             $game_map.events[20].trigger == 1,
             "Celadon city must retain both walk-through core doors and only audited signs/Cut")
    require!($game_map.events[3].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_gym
    } && $game_map.events[20].list.any? { |row|
      row.code == 201 && row.parameters[1] == celadon_center
    }, "Celadon city doors do not reach the audited destinations")
    $map_factory.setup(celadon_center)
    require!(whitelisted_core?($game_map.events, [1, 2], [3]),
             "Celadon Center wrong active map/events: map=#{$game_map.map_id}, " +
             "target=#{celadon_center}, events=#{$game_map.events.keys.inspect}")
    exit_events = $game_map.events[1].list.map { |row| [row.code, row.parameters] }
    require!(exit_events.any? { |op|
      op[0] == 201 && op[1][1] == celadon_city
    }, "Celadon Center exit target mismatch: current=#{celadon_center} " +
       "city=#{celadon_city} events=#{exit_events.inspect}")
    $map_factory.setup(celadon_gym)
    require!(whitelisted_core?($game_map.events, [1, 5, 7, 42, 43, 44, 45, 46, 47]),
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

    # Phase 10: the Safari sectors and Warden now coexist with protected Fuchsia previews.
    ["Rota 15"].each do |label|
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
    safari_north = map_for.call("Safari Zone Norte")
    safari_west = map_for.call("Safari Zone Oeste")
    warden_house = map_for.call("Casa do Warden")
    $map_factory.setup(fuchsia_city)
    require!(whitelisted_core?($game_map.events, [5, 17, 18, 22, 24]),
             "Unreviewed Fuchsia city events leaked into core")
    [[5, fuchsia_gym], [17, fuchsia_center],
     [18, fuchsia_mart], [22, warden_house], [24, safari_gate]].each do |event_id, target_id|
      ev = $game_map.events[event_id]
      require!(ev.trigger == 1 && ev.list.any? { |op| op.code == 201 && op.parameters[1] == target_id },
               "Fuchsia city has broken entry #{event_id}")
    end
    [[fuchsia_center, [1, 2]], [fuchsia_mart, [1, 2]],
     [fuchsia_gym, [3, 4, 5, 6, 7, 8, 9, 11]],
     [warden_house, [1, 3]], [safari_gate, [1, 2, 3, 5]]].each do |mid, required|
      $map_factory.setup(mid)
      actual = $game_map.events.keys
      optional_center_pc = mid == fuchsia_center ? [3] : []
      require!(whitelisted_core?($game_map.events, required, optional_center_pc),
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
    BlueKantoPilot.safari_guide
    require!($player.money == before_safari_money,
             "Safari informational gate charged money without starting a native session")
    [safari_south, safari_north, safari_west].each do |zone|
      $map_factory.setup(zone)
      require!($game_map.metadata.safari_map && !$game_map.events.empty?,
               "Safari sector lacks native session metadata or map events")
    end
    require!($game_map.events[24].list.any? { |op| op.code == 355 &&
      op.parameters[0] == "BlueKantoPilot.safari_teeth(24)"
    }, "The original West Safari Gold Teeth pickup is missing")
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
    require!(whitelisted_core?($game_map.events, [1,2]) &&
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
    require!(whitelisted_core?($game_map.events, [1,2,3,4,5]),
             "Cinnabar imported unaudited city events")
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
    require!(BlueKantoPilot.viridian_map_id == viridian,
             "Viridian local name points to the wrong mapped Kanto map")
    previous_locale = $PokemonSystem.blue_locale
    $PokemonSystem.blue_locale = "pt-BR"
    require!(GameData::MapMetadata.get(viridian).name == "Cidade de Viridian",
             "Viridian map banner is truncated in Portuguese")
    $PokemonSystem.blue_locale = "en"
    require!(GameData::MapMetadata.get(viridian).name == "Viridian City",
             "Viridian map banner changed in English")
    $PokemonSystem.blue_locale = previous_locale
    $map_factory.setup(viridian)
    northern_house = $game_map.events[2]
    threshold = BlueKantoPilot.viridian_route2_line
    require!(northern_house && threshold &&
             threshold == [viridian, northern_house.y - 1,
                           northern_house.x - 6, northern_house.x - 1] &&
             threshold[1] > 0,
             "Route 2 gate is not on the red-marked line by Viridian north house")
    require!($game_map.events.values.none? { |event|
      event.name == "Kanto Viridian Route 2 Parcel Gate"
    }, "Obsolete north-edge RPG gate survived in Viridian")
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
    arrows = $game_map.events.values.select { |event| event.name == "Kanto Spin Tile" }
    require!(!arrows.empty? && arrows.all? { |event| event.trigger == 1 && event.through },
             "Viridian Gym arrows are not native player-touch floor events")
    require!(whitelisted_core?($game_map.events, [2,3,4,5,6,7,8,9,10,11,16], arrows.map(&:id)),
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
    require!(!BlueKantoPilot.victory_strength([14,15]) &&
             !$game_self_switches[[road1,14,"A"]] &&
             !$game_self_switches[[road1,15,"A"]],
             "Victory Road incorrectly activated Strength without HM04")
    # This is a disposable native CI proof, not a real player save. Give the
    # item and a compatible party member before trying the simplified puzzle.
    require!($bag.add(:HM04), "Native test could not add HM04")
    strength_user = Pokemon.new(:MACHOP, 15)
    require!(strength_user.compatible_with_move?(:STRENGTH),
             "Native Pokémon compatibility rejects the Strength test user")
    $player.party << strength_user
    require!(BlueKantoPilot.victory_strength([14,15]),
             "Victory Road Strength remains blocked after HM + badge + party")
    require!($game_self_switches[[road1,14,"A"]] &&
             $game_self_switches[[road1,15,"A"]],
             "Victory Road adapted Strength barriers did not open")
    $player.party.delete(strength_user)
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
    # Traveling no longer requires League completion. The Hall of Fame must
    # grant only Kanto's completion flag; the independent travel catalogue is
    # already free (physical destinations still require installed maps).
    require!(BlueRegions.unlocked(BlueKantoPilot.progress) == BlueRegions.circuit,
             "League incorrectly restricted the free regional travel catalogue")
    require!(!BlueKantoPilot.league_finalize(pallet),
             "Hall of Fame duplicated completion")

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
    north_state = BlueKantoPilot.progress
    require!(%w[pilot_cerulean_rival pilot_nugget_bridge_awarded pilot_bill_agreed pilot_bill_helped pilot_bill_ticket pilot_ss_ticket].all? { |key| north_state[key] },
             "K00-C quest flags lost after native save/reload")
    north_keys = ["KANTO_CERULEAN_RIVAL","KANTO_042_001","KANTO_042_011","KANTO_042_016"] +
      (1..6).map { |id| "KANTO_053_%03d" % id } +
      [1,2,3,6,7,8,9,10,11].map { |id| "KANTO_054_%03d" % id }
    require!((north_keys - north_state["pilot_wins"]).empty?, "K00-C victory keys lost")
    gym_id,bridge_id,route_id,bill_id = north_report["map_ids"][1,4]
    require!([[gym_id,1],[gym_id,11],[gym_id,16],[bridge_id,6],[bill_id,3],[bill_id,4],[bill_id,8]].all? { |mid,eid| $game_self_switches[[mid,eid,"A"]] },
             "K00-C self switches lost")
    require!($bag.quantity(:NUGGET) == north_report["nugget_quantity"], "Nugget quantity changed after reload")
    if north_report["ticket_mode"] == "native_item"
      require!($bag.quantity(:BLUE_KANTO_SSTICKET) == north_report["ticket_quantity"] &&
               north_state["pilot_bill_ticket_item_granted"], "Ticket quantity or grant flag changed after reload")
    end
    # Engine save/reload and callback state are genuine; battle outcomes are
    # stubbed and collision witnesses are not manual walking/door animation.
    north_report["save_reload"] = true
    north_report["victory_keys"] = north_keys.length
    north_report["native_trainer_encounters"] = north_keys.length
    north_report["misty_loss_retry"] = true
    # The final campaign reload must retain the chosen starter as well.
    require!(BlueKantoPilot.starter == :BULBASAUR &&
             [18,19,20].all? { |eid| $game_self_switches[[lab,eid,"A"]] },
             "K01-A starter flags lost in later campaign")
    opening_report["later_campaign_reload"] = true
    File.write("Data/blue-kanto-k01a-starter-proof.txt", opening_report.inspect)
    puts "KANTO_K01A_NATIVE_STARTER_REPORT:#{opening_report.inspect}"
    puts "KANTO_K01A_THREE_STARTERS_SAVE_RELOAD_OK"
    File.write("Data/blue-kanto-k00-cerulean-proof.txt", north_report.inspect)
    puts "KANTO_K00_CERULEAN_NATIVE_REPORT:#{north_report.inspect}"
    puts "KANTO_K00_CERULEAN_NATIVE_STORY_OK"
    require!(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true &&
             BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
             "Oak parcel quest flags did not persist through save/reload")
    walk_verified = walk_rows.count { |row| row[4] == "native_step_verified" }
    File.write("Data/blue-kanto-proof.txt",
               "Kanto 145 maps: Cerulean north, Nugget Bridge, Bill, Victory Road, eight badge guards, Elite Four/Blue, unique Hall of Fame and Decades/Johto eligibility; save/reload (battles simulated); " +
               "native tile-step probe #{walk_verified}/#{walk_rows.length} destinations (NOT manual keyboard/visual QA)")
  end
end
