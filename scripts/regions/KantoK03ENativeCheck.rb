# Separate disposable 160-map engine test, never injected into a release.
module KantoK03ENativeCheck
  C = KantoNativeCheck
  TRAINERS = {2=>[:YOUNGSTER,"Dave"],5=>[:YOUNGSTER,"Eddie"],7=>[:YOUNGSTER,"Dillon"],
    9=>[:GAMBLER,"Jasper"],10=>[:ENGINEER,"Bernie"],11=>[:ENGINEER,"Braxton"],
    12=>[:GAMBLER,"Hugo"],13=>[:GAMBLER,"Darian"],15=>[:YOUNGSTER,"Yasu"],16=>[:GAMBLER,"Dirk"]}
  def self.require!(value,message)
    raise message unless value
  end

  def self.door!(leg,anchor)
    map, dest, id = leg.values_at("from_map","to_map","event_id")
    component = C.opening_component(map,anchor)
    event = $game_map.events.fetch(id)
    landing = C.north_transfer!(event,dest)
    require!(landing == leg["to_xy"],"K03-E source landing changed")
    old_scene = $scene
    scene = Scene_Map.new
    begin
      $scene = scene
      scene.send(:createSpritesets)
      choices = {2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}.filter_map do |dir,(dx,dy)|
        from = [event.x-dx,event.y-dy]
        next unless component.key?(from)
        $game_player.moveto(*from)
        [from,dir,$game_player.passable?(*from,dir)]
      end.sort_by { |from,_dir,passable| [passable ? 0 : 1,component.fetch(from)] }
      selected = nil
      choices.each do |from,dir,passable|
        $game_player.moveto(*from)
        $game_map.events.each_value { |e| e.clear_starting }
        $game_player.move_generic(dir,true)
        deadline = System.uptime + 3
        until event.starting || System.uptime >= deadline
          break unless $game_player.moving? || $game_player.jumping?
          Graphics.update
          $game_player.update
        end
        if event.starting
          selected = [from,dir,passable]
          break
        end
      end
      require!(selected,"K03-E door failed real Player Touch #{map}/#{id}")
      C.cerulean_native_started_transfer!(event,dest,*selected)
    ensure
      begin
        scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      ensure
        $scene = old_scene
      end
    end
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    Object.send(:define_method,:pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    Object.send(:define_method,:pbConfirmMessage) { |*args| true }
    # Setup of disposable controlled battle fixture, not a claimed campaign playthrough.
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    BlueKantoPilot.progress["pilot_starter"] = "BULBASAUR"
    calls, losses = [], {"Dave"=>1}
    TrainerBattle.define_singleton_method(:start) do |type,name,version=0|
      GameData::Trainer.get(type,name,version)
      calls << [type,name,version]
      if losses.fetch(name,0)>0
        losses[name]-=1
        false
      else
        true
      end
    end
    ids = [18,23,82,81,79,64].map { |sid| BlueKantoPilot.kanto_map_id(sid) }
    require!(ids.all? && ids.uniq.length==6,"K03-E missing installed map IDs")
    forward = C.k03a_chain(ids,[33,12],[19,7])
    reverse = C.k03a_chain(ids.reverse,[19,7],[33,12])
    require!(forward && reverse && forward.length==5 && reverse.length==5,
      "K03-E native collision chain not reciprocal")
    receipts = []
    [[forward,[33,12]],[reverse,[19,7]]].each do |legs,anchor|
      legs.each do |leg|
        if leg["kind"]=="touch_transfer"
          receipts << door!(leg,anchor)
        else
          comp = C.opening_component(leg["from_map"],anchor)
          candidates = C.opening_crossings(leg["from_map"],comp,leg["to_map"])
          require!(candidates.include?([leg["from_xy"],leg["to_xy"]]),"K03-E seam not passable")
          receipts << leg
        end
        anchor = leg["to_xy"]
      end
    end
    route,tunnel = ids[4],ids[2]
    route_comp = C.opening_component(route,[6,18])
    trainers = TRAINERS.map do |eid,(kind,name)|
      ev = $game_map.events.fetch(eid)
      require!(ev.trigger==2 && C.north_event_reachable?(route_comp,ev),"K03-E trainer inaccessible #{eid}")
      type = :"BLUE_KANTO_#{kind}"
      roster = GameData::Trainer.get(type,name,0)
      require!(!roster.pokemon.empty?,"K03-E empty roster #{name}")
      key = "KANTO_079_%03d" % eid
      C.north_callback!(ev,"BlueKantoPilot.battle(:#{type}, \"#{name}\", \"#{key}\")")
      if name=="Dave"
        require!(!BlueKantoPilot.battle(type,name,key) && !BlueKantoPilot.sync_trainer_event(key,name,eid),
          "K03-E loss marked trainer beaten")
      end
      require!(BlueKantoPilot.battle(type,name,key) && BlueKantoPilot.sync_trainer_event(key,name,eid),"K03-E trainer retry/win failed #{name}")
      require!($game_self_switches[[route,eid,"A"]],"K03-E trainer self switch missing")
      BlueKantoPilot.battle(type,name,key)
      require!(calls.count { |row| row[1]==name }==(name=="Dave" ? 2 : 1),"K03-E repeated battle #{name}")
      [eid,name,roster.pokemon.length]
    end
    encounter = GameData::Encounter.get(route)
    cave = GameData::Encounter.get(tunnel)
    require!([:LandDay,:LandNight,:Water,:OldRod,:GoodRod,:SuperRod].all? { |method| encounter.types.key?(method) },
      "K03-E Route 11 encounters missing")
    [:CaveDay,:CaveNight].each do |method|
      slots = cave.types[method]
      require!(slots && slots.map { |slot| slot[1] }.uniq.sort==[:DIGLETT,:DUGTRIO],"K03-E tunnel encounter missing")
      require!(slots.sum { |slot| slot[0] }==100,"K03-E tunnel weights changed")
    end
    $game_player.moveto(6,18)
    slot = "Kanto K03E Native Verification"
    require!(Game.save(slot),"K03-E save failed")
    C.reload_native_slot(SaveData.get_full_path(slot))
    require!($game_map.map_id==route && [$game_player.x,$game_player.y]==[6,18],"K03-E map/position reload failed")
    require!(TRAINERS.keys.all? { |eid| BlueKantoPilot.progress["pilot_wins"].include?("KANTO_079_%03d" % eid) &&
      $game_self_switches[[route,eid,"A"]] },"K03-E trainer flags lost on reload")
    report = {"map_ids"=>ids,"forward"=>forward,"reverse"=>reverse,"transfer_receipts"=>receipts,
      "trainers"=>trainers,"defeat_retry"=>true,"save_reload"=>true,"controlled_battle_results"=>true,
      "manual_gameplay"=>false}
    File.write("Data/blue-kanto-k03e-proof.txt",report.inspect)
    puts "KANTO_K03E_NATIVE_CORRIDOR_REPORT:#{report.inspect}"
    puts "KANTO_K03E_ROUTE11_DIGLETT_TRAINERS_SAVE_RELOAD_OK"
  end
end
