# Only loaded into the disposable CI Tower fixture.
module KantoK05TowerNativeCheck
  C = KantoNativeCheck
  T = KantoK05CityNativeCheck
  UP = [[609,8,615,[9,18]], [615,7,616,[16,10]], [616,5,617,[2,10]],
        [617,5,618,[16,10]], [618,8,619,[2,10]], [619,10,620,[16,10]]].freeze
  DOWN = [[620,7,619,[16,10]], [619,9,618,[2,10]], [618,7,617,[16,10]],
          [617,6,616,[2,10]], [616,1,615,[16,9]], [615,1,609,[18,7]]].freeze

  def self.want(value, detail)
    raise "K05 Tower: #{detail}" unless value
    value
  end

  def self.trace(key, value)
    File.open("Data/blue-kanto-k05-tower-native-stage.txt", "a"){ |f| f.puts("#{key}:#{value.inspect}") }
  end

  def self.stairs!(chain, start)
    chain.map do |map,event,dest,landing|
      want($game_map.map_id==map, "journey lost previous floor at #{map}")
      trace("TRY_TOUCH",[map,event,start,dest])
      receipt = T.door!(map,dest,event,start,landing)
      start = landing
      receipt
    end
  end

  def self.gate!(seen, has_scope)
    want($bag.has?(:SILPHSCOPE)==has_scope, "incorrect Silph Scope test state")
    comp = C.opening_component(620,[16,10])
    event = want($game_map.events[8], "summit gate absent")
    want([event.x,event.y]==[8,16] && event.list.none? { |op| op.code==201 },
         "summit gate moved or contains a transfer")
    previous = $scene
    scene = Scene_Map.new
    begin
      $scene = scene
      scene.send(:createSpritesets)
      ip = pbMapInterpreter
      dirs = {2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}
      used = dirs.find do |dir,(dx,dy)|
        start = [event.x-dx,event.y-dy]
        next false unless comp.key?(start)
        $game_player.moveto(*start)
        next false unless $game_player.passable?(*start,dir)
        $game_map.events.each_value(&:clear_starting)
        $game_player.move_generic(dir,true)
        deadline = System.uptime + 3
        until event.starting || System.uptime >= deadline
          break unless $game_player.moving? || $game_player.jumping?
          Graphics.update
          $game_player.update
        end
        event.starting
      end
      want(used, "summit gate did not trigger from an accessible tile")
      count = seen.size
      ip.setup_starting_event
      want(ip.running? && ip.instance_variable_get(:@event_id)==8, "wrong interpreter event at summit")
      stop = System.uptime+5
      while ip.running? && System.uptime < stop
        ip.update
        Graphics.update
      end
      want(!ip.running? && $game_map.map_id==620 && !$game_temp.player_transferring &&
           seen.size==count+1 && seen.last.match?(/fantasma/i), "summit failed to announce or block passage")
      {"floor"=>620,"gate"=>[8,16],"silph_scope"=>has_scope,"native_touch"=>true,
       "stayed_on_floor"=>true,"hint"=>seen.last}
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
    end
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    seen = []
    Object.send(:define_method,:pbMessage) { |message,*_args| seen << message; nil }
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    $game_system.encounter_disabled = true
    ids = [93,98,*(100..106)].to_h { |sid| [sid,BlueKantoPilot.kanto_map_id(sid)] }
    want(ids.values==[609,614,*(615..621)], "Tower registry changed")
    # No authored route from an accessible floor may bypass the original gate.
    (609..620).each do |mid|
      $map_factory.setup(mid)
      $game_map.events.each_value do |e|
        want(e.list.nil? || e.list.none? { |op| op.code==201 && op.parameters[1]==621 },
             "premature path into the summit from #{mid}/#{e.id}")
      end
    end
    $map_factory.setup(621)
    want(!$game_map.events[1], "summit Fuji transfer enabled before K07")
    $map_factory.setup(614)
    want(!$game_map.events[3], "Fuji reward enabled before K07")
    $map_factory.setup(609)
    up = stairs!(UP,[8,0])
    want($game_map.map_id==620, "could not climb to the original gate floor")
    blocked = [gate!(seen,false)]
    # K05 must not silently make K07 playable if a disposable migrated
    # test save, debugger or other region already holds the same item ID.
    scope_in_catalog = GameData::Item.exists?(:SILPHSCOPE)
    if scope_in_catalog
      want($bag.add(:SILPHSCOPE), "could not set the synthetic Scope negative control")
      blocked << gate!(seen,true)
      want($bag.remove(:SILPHSCOPE), "could not reset the synthetic Scope negative control")
    end
    down = stairs!(DOWN,[16,10])
    want($game_map.map_id==609 && [$game_player.x,$game_player.y]==[18,7], "native exit did not return to Lavender")
    report = {"native_up"=>up,"native_down"=>down,"summit_gate"=>blocked,
              "native_scope_exists"=>scope_in_catalog,"remained_in_scope"=>true,"actors_tested"=>false,"manual_playthrough"=>false,"published"=>false}
    File.write("Data/blue-kanto-k05-tower-native-proof.txt",report.inspect)
    puts "KANTO_K05_TOWER_NATIVE_STAIRS_OK"
  end
end
