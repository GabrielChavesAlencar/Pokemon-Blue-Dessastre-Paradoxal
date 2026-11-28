# Runs only in disposable K04 CI. No save, proof code, or archive is shipped.
module KantoK04NativeCheck
  C = KantoNativeCheck
  D = KantoK03ENativeCheck
  ENCOUNTERS = {86=>[:LandDay,:LandNight], 87=>[:LandDay,:LandNight,:Water,:OldRod,:GoodRod,:SuperRod],
    90=>[:CaveDay,:CaveNight], 91=>[:CaveDay,:CaveNight]}.freeze
  DIRECTIONS = {2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}.freeze

  def self.require!(value, reason)
    raise "K04 #{reason}" unless value
    value
  end

  def self.trace(label, value)
    File.open("Data/blue-kanto-k04-stage.txt","a") { |f| f.puts("#{label}:#{value.inspect}") }
  end

  def self.door(ids, source, eid, dest, anchor, native_ledges: false)
    from,to = ids.values_at(source,dest)
    component = C.opening_component(from,anchor,[],false,native_ledges)
    event = require!($game_map.events[eid], "missing warp #{source}/#{eid}")
    return nil unless event.trigger == 1 && C.north_event_reachable?(component,event)
    {"kind"=>"touch_transfer","event_id"=>eid,"from_map"=>from,"to_map"=>to,
      "from_xy"=>[event.x,event.y],"to_xy"=>C.north_transfer!(event,to)}
  end

  def self.passage(ids, first, last, anchor)
    # Keep the separate north and south exterior sections explicit. A test
    # that happens to leave through the same mouth it entered is not a pass.
    north = first == 12
    entry = require!(door(ids,87,first,90,anchor), "tunnel entrance unreachable #{first}")
    # There can be up to four staircase traversals, not just one down
    # and one up. Search actual native collision components until the other
    # mouth is reachable; do not treat a same-mouth loop as success.
    queue = [[90,entry.fetch("to_xy"),[entry]]]
    visited = {}
    until queue.empty?
      area,at,legs = queue.shift
      key = [area,at]
      next if visited[key]
      visited[key] = true
      component = C.opening_component(ids.fetch(area),at)
      trace("FLOOR_COMPONENT",[area,at,component.length,legs.map { |leg| leg["event_id"] }])
      if area == 90 && legs.length >= 3 && (exit_leg = door(ids,90,last,87,at))
        require!(exit_leg["to_xy"] == (north ? [8,68] : [8,30]), "wrong tunnel mouth return")
        current = anchor
        return [*legs,exit_leg].map do |leg|
          trace("TOUCH", [leg,current])
          receipt = D.door!(leg,current,settle_motion: true)
          current = leg.fetch("to_xy")
          receipt
        end
      end
      dest,eids = area == 90 ? [91,13..16] : [90,27..30]
      eids.each do |eid|
        if (ladder = door(ids,area,eid,dest,at))
          queue << [dest,ladder.fetch("to_xy"),[*legs,ladder]]
        end
      end
    end
    raise "K04 no collision-verified path through B1F from exterior mouth #{first} to #{last}"
  end

  def self.route_component(map,anchor)
    comp = C.opening_component(map,anchor,[],false,true)
    return comp unless [39,86,87].map { |sid| BlueKantoPilot.kanto_map_id(sid) }.include?(map)
    previous = $scene
    scene = nil
    begin
      loop do
        tree = $game_map.events.values.find { |ev|
          BlueKantoPilot.cut_tree_obstacle?(ev) && !ev.instance_variable_get(:@erased) &&
            C.opening_action_witness(comp,ev)
        }
        break unless tree
        require!(BlueRegionalPolicy.field_result(:CUT) == :allowed, "Cut did not pass local requirements")
        unless scene
          scene = Scene_Map.new
          $scene = scene
          scene.send(:createSpritesets)
        end
        witness = C.opening_action_witness(comp,tree)
        $game_player.moveto(*witness.fetch("standing"))
        $game_player.direction = witness.fetch("direction")
        $game_map.events.each_value { |ev| ev.clear_starting }
        $game_player.check_event_trigger_there([0])
        require!(tree.starting, "native action button did not select Cut tree #{map}/#{tree.id}")
        interpreter = pbMapInterpreter
        interpreter.setup_starting_event
        require!(interpreter.running? && interpreter.instance_variable_get(:@event_id) == tree.id,
          "native interpreter did not select Cut tree #{map}/#{tree.id}")
        deadline = System.uptime + 8
        while interpreter.running? && System.uptime < deadline
          interpreter.update
          Graphics.update
          $game_player.update
          $game_map.update
        end
        require!(!interpreter.running? && tree.instance_variable_get(:@erased),
          "Cut did not clear original tree #{map}/#{tree.id}")
        trace("NATIVE_CUT",[map,tree.id,witness])
        comp = C.opening_component(map,anchor,[],false,true,reuse_loaded: true)
      end
    ensure
      scene.send(:disposeSpritesets) if scene && scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
    end
    comp
  end

  def self.route_chain(sequence, anchor, goal, tried = {})
    map = sequence.first
    return nil if tried[[sequence,anchor]]
    tried[[sequence,anchor]] = true
    comp = route_component(map,anchor)
    return comp.key?(goal) ? [] : nil if sequence.length == 1
    target = sequence[1]
    doors = $game_map.events.values.filter_map do |ev|
      next unless ev.trigger == 1 && C.north_event_reachable?(comp,ev)
      op = ev.list.find { |cmd| cmd.code == 201 && cmd.parameters[0] == 0 && cmd.parameters[1] == target }
      next unless op
      {"kind"=>"touch_transfer","event_id"=>ev.id,"from_map"=>map,"to_map"=>target,
        "from_xy"=>[ev.x,ev.y],"to_xy"=>op.parameters[2,2]}
    end
    seams = doors.empty? ? C.opening_crossings(map,comp,target).map { |from,to|
      {"kind"=>"native_seam","from_map"=>map,"to_map"=>target,"from_xy"=>from,"to_xy"=>to}
    } : []
    trace("ROUTE_COMPONENT",[map,anchor,comp.length,target,doors+seams])
    (doors+seams).each do |leg|
      suffix = route_chain(sequence.drop(1),leg.fetch("to_xy"),goal,tried)
      return [leg,*suffix] if suffix
    end
    nil
  end

  def self.cut_inventory(ids)
    [39,86,87].to_h do |sid|
      $map_factory.setup(ids.fetch(sid))
      cut = $game_map.events.values.select { |ev| BlueKantoPilot.cut_tree_obstacle?(ev) }
      [sid,cut.map { |ev| [ev.id,ev.x,ev.y] }]
    end
  end

  def self.center!(ids)
    id = ids.fetch(88)
    component = C.opening_component(id,[7,8])
    nurse = require!($game_map.events.values.find { |event|
      Array(event.list).any? { |op| op.code == 355 && op.parameters[0].to_s == "BlueKantoPilot.heal" }
    }, "healing service missing")
    witness = require!(C.opening_action_witness(component,nurse), "healing service is not reachable")
    $game_player.moveto(*witness.fetch("standing"))
    $game_player.direction = witness.fetch("direction")
    $player.party.first.hp = 1
    $game_map.events.each_value { |ev| ev.clear_starting }
    $game_player.check_event_trigger_there([0])
    require!(nurse.starting, "native action button did not select nurse")
    interpreter = pbMapInterpreter
    interpreter.setup_starting_event
    require!(interpreter.running? && interpreter.instance_variable_get(:@event_id) == nurse.id,
      "native interpreter did not select nurse")
    deadline = System.uptime + 5
    while interpreter.running? && System.uptime < deadline
      interpreter.update
      Graphics.update
    end
    require!(!interpreter.running? && $player.party.first.hp == $player.party.first.totalhp,
      "native nurse did not heal damaged party")
    require!($PokemonGlobal.pokecenterMapId == id, "healing did not register Rock Tunnel respawn")
    witness
  end

  def self.check_area(errors, label)
    output = yield
    trace(label, output)
    output
  rescue StandardError => error
    errors[label] = error.message
    trace(label + "_ERROR", error.full_message)
    nil
  end

  def self.aide_action(witness,eid)
    $game_player.moveto(*witness.fetch("standing"))
    $game_player.direction = witness.fetch("direction")
    $game_map.events.each_value { |ev| ev.clear_starting }
    $game_player.check_event_trigger_there([0])
    interpreter = pbMapInterpreter
    interpreter.setup_starting_event
    require!(interpreter.running? && interpreter.instance_variable_get(:@event_id) == eid,
      "native Action did not select Route 2 aide")
    deadline = System.uptime + 5
    while interpreter.running? && System.uptime < deadline
      interpreter.update
      Graphics.update
    end
    require!(!interpreter.running?, "Route 2 aide interpreter did not complete")
  end

  def self.acquire_flash!(hm)
    gate = require!(BlueKantoPilot.kanto_map_id(21), "Route 2 aide gatehouse absent")
    route = require!(BlueKantoPilot.kanto_map_id(18), "Route 2 absent")
    $map_factory.setup(route)
    incoming = $game_map.events.values.filter_map do |ev|
      op = ev.list.find { |cmd| cmd.code == 201 && cmd.parameters[0] == 0 && cmd.parameters[1] == gate }
      [ev.id,op.parameters[2,2]] if op && ev.trigger == 1
    end
    require!(!incoming.empty?, "no original Route 2 door into Flash gatehouse")
    witness = nil
    incoming.each do |eid, landing|
      comp = C.opening_component(gate,landing)
      aide = $game_map.events[2]
      C.north_callback!(aide,"BlueKantoPilot.route2_flash")
      if (candidate = C.opening_action_witness(comp,aide))
        witness = candidate.merge("from_route_door"=>eid,"gatehouse_landing"=>landing)
        break
      end
    end
    require!(witness,"Flash aide is not reachable from a Route 2 door")
    dex = $player.pokedex
    seed = [:BULBASAUR,:IVYSAUR,:VENUSAUR,:CHARMANDER,:CHARMELEON,:CHARIZARD,
            :SQUIRTLE,:WARTORTLE,:BLASTOISE,:CATERPIE,:METAPOD]
    seed.each do |species|
      break if dex.owned_count(0) >= 9
      dex.set_owned(species)
    end
    require!(dex.owned_count(0)==9, "could not establish threshold-minus-one on native Kanto Pokédex")
    aide_action(witness,2)
    require!($bag.quantity(hm)==0, "aide granted Flash with fewer than 10 species")
    seed.each do |species|
      break if dex.owned_count(0)>=10
      dex.set_owned(species)
    end
    require!(dex.owned_count(0)==10, "could not establish threshold on native Kanto Pokédex")
    2.times do
      aide_action(witness,2)
      require!($bag.quantity(hm)==1, "aide did not award exactly one real Flash HM")
    end
    trace("FLASH_AIDE_NATIVE",witness.merge("threshold"=>10,"quantity"=>$bag.quantity(hm)))
    witness
  end

  def self.flash!(ids)
    $map_factory.setup(ids[90])
    $game_player.moveto(24,7)
    compatible = [:PIKACHU,:BULBASAUR,:ABRA].map { |species| Pokemon.new(species,15) }
                    .find { |pkmn| pkmn.compatible_with_move?(:FLASH) }
    require!(compatible, "no compatible native Flash fixture species")
    incompatible = Pokemon.new(:MAGIKARP,10)
    require!(!incompatible.compatible_with_move?(:FLASH), "incompatible fixture changed")
    $player.party.replace([compatible])
    hm = BlueRegionalPolicy::KANTO_HM_ITEMS[:FLASH].find { |item| GameData::Item.exists?(item) }
    unless hm
      GameData::Item.each { |item| hm ||= item.id if item.is_HM? && item.move == :FLASH }
    end
    require!(hm, "no genuine Flash HM in compiled PBS")
    require!(BlueRegionalPolicy.field_result(:FLASH) == :badge, "Flash allowed without regional Boulder")
    require!(BlueRegions.award(BlueKantoPilot.progress,"KANTO","BOULDER"), "could not award fixture Boulder")
    require!(BlueRegionalPolicy.field_result(:FLASH) == :hm, "Flash allowed without owned HM")
    acquired = acquire_flash!(hm)
    $map_factory.setup(ids[90])
    $game_player.moveto(24,7)
    $player.party.replace([incompatible])
    require!(BlueRegionalPolicy.field_result(:FLASH) == :pokemon, "incompatible Pokémon accepted")
    $player.party.replace([compatible])
    compatible.hp = 0
    require!(BlueRegionalPolicy.field_result(:FLASH) == :pokemon, "fainted Pokémon accepted")
    compatible.heal
    require!(BlueRegionalPolicy.field_result(:FLASH,compatible) == :allowed, "valid combination rejected")
    previous = $scene
    scene = Scene_Map.new
    begin
      $scene = scene
      scene.send(:createSpritesets)
      EventHandlers.trigger(:on_map_or_spriteset_change,scene,false) if !$game_temp.darkness_sprite || $game_temp.darkness_sprite.disposed?
      dark = require!($game_temp.darkness_sprite, "native darkness sprite missing")
      radius = dark.radius
      require!(!dark.disposed? && radius < dark.radiusMax && !$PokemonGlobal.flashUsed, "initial tunnel not dark")
      require!(HiddenMoveHandlers.triggerCanUseMove(:FLASH,compatible,false), "native Flash CanUseMove rejected")
      require!(HiddenMoveHandlers.triggerUseMove(:FLASH,compatible), "native Flash use failed")
      require!($PokemonGlobal.flashUsed && dark.radius > radius && dark.radius == dark.radiusMax,
        "Flash failed to illuminate native darkness")
      require!(!HiddenMoveHandlers.triggerCanUseMove(:FLASH,compatible,false), "repeat Flash wasn't rejected")
      {"hm"=>hm.to_s,"initial_radius"=>radius,"illuminated_radius"=>dark.radius,"native_effect"=>true,"aide"=>acquired}
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
    end
  end

  def self.trainer_witness(ids,sid,anchor)
    comp = C.opening_component(ids.fetch(sid),anchor)
    $game_map.events.each_value do |ev|
      next unless C.north_event_reachable?(comp,ev)
      script = ev.list.find { |op| op.code == 355 && op.parameters[0].to_s.start_with?("BlueKantoPilot.battle(") }
      next unless script
      m = script.parameters[0].match(/\ABlueKantoPilot\.battle\(:(BLUE_KANTO_\w+), "([A-Za-z]+)", "(KANTO_\d{3}_\d{3})"\)\z/)
      next unless m
      require!(m[3] == ("KANTO_%03d_%03d" % [sid,ev.id]), "trainer battle key not native to this event")
      require!(ev.trigger == 2, "original tunnel trainer lost event-touch trigger")
      type = m[1].to_sym
      roster = GameData::Trainer.get(type,m[2],0)
      require!(roster && !roster.pokemon.empty?, "missing compiled trainer roster")
      return [ev.id,type,m[2],m[3],roster.pokemon.size]
    end
    raise "K04 no reachable trainer from tunnel floor #{sid} at #{anchor.inspect}"
  end

  def self.trainer_blackout!(ids,lower_landing)
    require!($PokemonGlobal.pokecenterMapId == ids.fetch(88), "no real Center checkpoint before blackout")
    first = trainer_witness(ids,90,[24,7])
    lower = trainer_witness(ids,91,lower_landing)
    warn_flag = BlueKantoPilot.progress.fetch("regional_pokecenters",{})["KANTO"]
    require!(warn_flag && warn_flag[0] == ids.fetch(88), "native Center checkpoint wasn't saved for Kanto")
    checkpoint = BlueRegionalRespawn.checkpoint
    scene = Scene_Map.new
    previous = $scene
    old = TrainerBattle.method(:start)
    calls = []
    should_lose = true
    # Only battle outcome is controlled. Blackout uses the engine, including
    # the current checkpoint, Scene_Map transfer, stats and the real party.
    TrainerBattle.define_singleton_method(:start) do |type,name,version=0|
      GameData::Trainer.get(type,name,version)
      calls << [type,name,version]
      if should_lose
        should_lose = false
        $player.party.each { |pkmn| pkmn.hp = 0 }
        pbStartOver(true)
        false
      else
        true
      end
    end
    begin
      $map_factory.setup(ids.fetch(90))
      $game_player.moveto(24,7)
      $scene = scene
      scene.send(:createSpritesets)
      eid,type,name,key,_team = first
      old_blackouts = $stats.blacked_out_count
      require!(!BlueKantoPilot.battle(type,name,key), "loss recorded as win")
      require!($stats.blacked_out_count == old_blackouts + 1 &&
        $game_map.map_id == checkpoint[0] && [$game_player.x,$game_player.y] == checkpoint[1,2],
        "native blackout did not return to saved Rock Tunnel Center tile")
      require!($player.party.all? { |pkmn| pkmn.hp == pkmn.totalhp },
        "native blackout did not heal after defeat")
      require!(!BlueKantoPilot.progress.fetch("pilot_wins",[]).include?(key) &&
        !$game_self_switches[[ids.fetch(90),eid,"A"]], "defeat changed trainer completion")
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
    end
    [[90,[24,7],first],[91,lower_landing,lower]].each do |sid,anchor,(eid,type,name,key,_)|
      $map_factory.setup(ids.fetch(sid))
      $game_player.moveto(*anchor)
      require!(BlueKantoPilot.battle(type,name,key) && BlueKantoPilot.sync_trainer_event(key,name,eid),
        "native trainer retry did not record victory")
      require!($game_self_switches[[ids.fetch(sid),eid,"A"]], "native trainer victory switch missing")
      BlueKantoPilot.battle(type,name,key)
    end
    require!(calls.size == 3, "completed trainer fought twice")
    {"native_blackout"=>true,"checkpoint"=>checkpoint,"rosters"=>[first,lower],"controlled_outcomes"=>true}
  ensure
    TrainerBattle.define_singleton_method(:start,old) if old
  end

  def self.south_boundary!(ids,arrival)
    comp = C.opening_component(ids.fetch(87),arrival)
    last_row = $game_map.height - 1
    approach = comp.keys.select { |_x,y| y == last_row }.sort
    require!(!approach.empty?, "south Rock Tunnel mouth cannot reach the original Lavender boundary")
    {"route10"=>ids.fetch(87),"mouth_landing"=>arrival,"south_edge_tiles"=>approach,
     "lavender_city_installed"=>false,"crossing_deferred_to_k05"=>true}
  end

  def self.save_reload!(ids,flash)
    floor = ids.fetch(90)
    require!($game_map.map_id == floor && [$game_player.x,$game_player.y] == [24,7],
      "Flash test did not finish in the north entrance")
    slot = "Kanto K04 Native CI"
    require!(Game.save(slot), "native synthetic save failed")
    path = SaveData.get_full_path(slot)
    require!(File.file?(path), "native save file is missing")
    begin
      $map_factory.setup(ids.fetch(88))
      $game_player.moveto(7,8)
      facts = C.reload_native_slot(path)
      hm = flash.fetch("hm").to_sym
      require!($game_map.map_id == floor && [$game_player.x,$game_player.y] == [24,7],
        "save reopened on wrong Rock Tunnel map or position")
      require!(facts.fetch("region") == "KANTO" && $bag.quantity(hm) == 1 &&
        BlueKantoPilot.progress.fetch("pilot_items").include?("KANTO_021_FLASH_AIDE"),
        "native save lost Kanto identity, HM or one-time quest flag")
      require!($PokemonGlobal.pokecenterMapId == ids.fetch(88),
        "save lost Rock Tunnel Center respawn")
      {"map"=>floor,"xy"=>[24,7],"hm"=>hm,"center"=>ids.fetch(88)}
    ensure
      File.delete(path) if File.file?(path)
    end
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    Object.send(:define_method,:pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    Object.send(:define_method,:pbConfirmMessage) { |*args| true }
    ids = [39,86,87,88,90,91].to_h { |sid| [sid,BlueKantoPilot.kanto_map_id(sid)] }
    require!(ids.values_at(86,87,88,90,91)==[604,605,606,607,608], "published candidate ID mismatch")
    trace("MAPS",ids)
    encounters = ENCOUNTERS.to_h do |sid,methods|
      table = GameData::Encounter.get(ids[sid])
      require!(table && table.types.keys.sort == methods.sort, "native encounters changed on source #{sid}")
      [sid,methods.to_h { |method|
        rows = table.types[method]
        require!(!rows.empty? && rows.all? { |w,s,lo,hi| w > 0 && GameData::Species.exists?(s) && lo <= hi },
          "invalid native encounters on source #{sid}/#{method}")
        [method,rows.length]
      }]
    end
    [86,87,88,90,91].each do |sid|
      require!(!!GameData::MapMetadata.get(ids[sid]).dark_map == [90,91].include?(sid), "DarkMap metadata changed #{sid}")
    end
    require!(BlueKantoPilot.kanto_map_id(92).nil? && BlueKantoPilot.kanto_map_id(93).nil?,
      "Power Plant or Lavender installed before its own phase")
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    BlueKantoPilot.progress["pilot_starter"] = "BULBASAUR"
    # Preserve real walking, collision and event interpreters; prevent the
    # RNG from starting unrelated combat while enumerating ledge witnesses.
    # Native encounter tables are checked above. This save is disposable.
    previous_encounters = $game_system.encounter_disabled
    $game_system.encounter_disabled = true
    errors = {}
    trace("ACTIVE_CUT_OBSTACLES",cut_inventory(ids))
    center = check_area(errors,"NATIVE_NURSE") { center!(ids) }
    entrances = check_area(errors,"CENTER_NATIVE_DOORS") do
      into = require!(door(ids,87,22,88,[13,31],native_ledges: false), "Center entrance unreachable from its reciprocal landing")
      out = require!(door(ids,88,1,87,[7,8],native_ledges: false), "Center exit unreachable")
      [D.door!(into,[13,31]),D.door!(out,[7,8])]
    end
    # The corridor probe models many native ledge jumps while planning
    # candidate positions; run the ordinary cave contacts and Action probes
    # first, so they can never inherit the route scan's movement timers.
    north = check_area(errors,"TUNNEL_NORTH_TO_SOUTH") { passage(ids,12,17,[13,31]) }
    south = check_area(errors,"TUNNEL_SOUTH_TO_NORTH") { passage(ids,13,1,[8,68]) }
    boundary = check_area(errors,"LAVENDER_SOUTH_BOUNDARY") { south_boundary!(ids,north.last.fetch("landing")) } if north
    battles = check_area(errors,"TRAINER_BLACKOUT_RETRY") do
      lower = north.find { |receipt| receipt.fetch("destination") == ids.fetch(91) }
      trainer_blackout!(ids,lower.fetch("landing"))
    end if north
    flash = check_area(errors,"NATIVE_FLASH") { flash!(ids) }
    saved = check_area(errors,"NATIVE_SAVE_RELOAD") { save_reload!(ids,flash) } if flash
    center_path = [39,86,87,88].map { |sid| ids[sid] }
    roads = check_area(errors,"CERULEAN_ROUTE9_ROUTE10") do
      # Test fixture represents a player who finished S.S. Anne. Same native
      # Cut item and field gates as the ordinary player, no through toggles.
      require!(BlueRegions.award(BlueKantoPilot.progress,"KANTO","CASCADE"), "could not seed fixture Cascade")
      BlueKantoPilot.progress.fetch("field_events")["KANTO"] ||= []
      BlueKantoPilot.progress.fetch("field_events")["KANTO"] << "SS_ANNE_CAPTAIN"
      cut = BlueRegionalPolicy::KANTO_HM_ITEMS[:CUT].find { |item| GameData::Item.exists?(item) }
      require!(cut && $bag.add(cut), "could not register native Cut HM in fixture")
      $player.party.replace([Pokemon.new(:RATTATA,20)])
      from_city = route_chain(center_path,[22,20],[7,8])
      to_city = route_chain(center_path.reverse,[7,8],[22,20])
      require!(from_city && to_city && [from_city,to_city].all? { |legs| legs.length == 3 },
        "Cerulean / routes / medical center corridor is not reciprocal")
      [from_city,to_city]
    end
    require!(errors.empty?, "native gate failures: #{errors.inspect}")
    report = {"map_ids"=>ids,"encounters"=>encounters,"center_service"=>center,
      "center_doors"=>entrances,"north_to_south"=>north,"south_to_north"=>south,
      "seams"=>[roads[0].take(2),roads[1].drop(1)],"flash"=>flash,"native_save"=>saved,
      "south_boundary"=>boundary,"battles"=>battles,
      "manual_playthrough"=>false,"not_a_release"=>true}
    File.write("Data/blue-kanto-k04-proof.txt",report.inspect)
    puts "KANTO_K04_NATIVE_CORRIDOR_FLASH_OK"
  ensure
    $game_system.encounter_disabled = previous_encounters if defined?(previous_encounters) && !previous_encounters.nil?
  end
end
