# Executes only in the disposable 178-map K06 approach (not the released game).
module KantoK06ApproachNativeCheck
  C = KantoNativeCheck
  N = KantoK05CityNativeCheck
  def self.truth(value,label)
    raise "K06 route: #{label}" unless value
    value
  end

  def self.trace(key,value)
    File.open("Data/blue-kanto-k06-native-stages.txt","a"){ |f| f.puts("#{key}:#{value.inspect}") }
  end

  def self.seam(from,anchor,to,receiver=nil)
    row,dir,_ = C.opening_seams(from,to)
    into = receiver ? C.opening_component(to,receiver) : nil
    component=C.opening_component(from,anchor)
    selected=C.opening_crossings(from,component,to).find do |_a,b|
      (!into || into.key?(b)) && C.north_edge_cell(to,b,10-dir)
    end
    trace("SEAM_TRY",[row,anchor,receiver,selected])
    a,b=truth(selected,"no reachable reciprocal boundary #{from} / #{to}")
    result=N.move_over_seam!(from,a,dir,to,b)
    [result,b]
  end

  def self.doors(ids,legs,anchor)
    legs.map do |src,eid,dest,landing|
      trace("DOOR_TRY",[src,eid,dest,anchor])
      result=N.door!(ids.fetch(src),ids.fetch(dest),eid,anchor,landing)
      anchor=landing
      result
    end
  end

  def self.closed_gate(ids,src,inside,messages)
    mid=ids.fetch(src)
    cells=C.opening_component(mid,inside)
    gate=$game_map.events.fetch(2)
    truth(gate.trigger==1 && gate.list.none? { |op| op.code==201 },
          "Saffron gate acquired a native transfer before approval")
    original=$scene
    scene=Scene_Map.new
    begin
      $scene=scene
      scene.send(:createSpritesets)
      tried=[]
      selected={2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}.find do |dir,(x,y)|
        spot=[gate.x-x,gate.y-y]
        next false unless cells.key?(spot)
        $game_player.moveto(*spot)
        $game_map.events.each_value(&:clear_starting)
        $game_temp.encounter_triggered=false
        $game_player.move_generic(dir,true)
        deadline=System.uptime+3
        until gate.starting || !($game_player.moving? || $game_player.jumping?) || System.uptime>=deadline
          Graphics.update
          $game_player.update
        end
        tried << [spot,dir,gate.starting]
        gate.starting
      end
      trace("SAFFRON_GATE",[src,inside,tried])
      truth(selected,"guard event not reached by native contact")
      n=messages.length
      ip=pbMapInterpreter
      ip.setup_starting_event
      truth(ip.running? && ip.instance_variable_get(:@event_id)==2,"native gate did not own interpreter")
      stop=System.uptime+5
      while ip.running? && System.uptime<stop
        ip.update
        Graphics.update
      end
      truth(!ip.running? && !$game_temp.player_transferring && $game_map.map_id==mid &&
        messages.length==n+1 && messages.last.match?(/Saffron/i),"closed gate messaging/transfer changed")
      {"map"=>mid,"source"=>src,"blocked"=>true,"native_touch"=>true}
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene=original
    end
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    $game_system.encounter_disabled=true
    messages=[]
    Object.send(:define_method,:pbMessage){ |text,*_args| messages << text; nil }
    ids=[93,87,*(107..114),168].to_h { |sid| [sid,BlueKantoPilot.kanto_map_id(sid)] }
    truth(ids.values.all? && ids.fetch(93)==609,"published registry drift")
    [83,125,129,130,131,132,133,134,135].each do |sid|
      truth(!BlueKantoPilot.kanto_map_id(sid),"unpublished area available: #{sid}")
    end
    forward,route8=seam(ids.fetch(93),[8,0],ids.fetch(107),[9,20])
    out=doors(ids,[[107,13,109,[6,8]],[109,1,110,[76,3]],[110,1,113,[7,4]],[113,3,111,[7,30]]],route8)
    into_city,town=seam(ids.fetch(111),[7,30],ids.fetch(114))
    back_from_city,route7=seam(ids.fetch(114),town,ids.fetch(111),[7,30])
    back=doors(ids,[[111,2,113,[6,8]],[113,1,110,[3,4]],[110,2,109,[7,4]],[109,3,107,[9,20]]],route7)
    returned,_=seam(ids.fetch(107),[9,20],ids.fetch(93),[8,0])
    gates=[[107,5,108,[11,5],1,[3,25],[9,20]],
           [111,1,112,[1,5],1,[15,25],[7,30]]].map do |road,enter,guard,inside,leave,exit,anchor|
      walk=N.door!(ids.fetch(road),ids.fetch(guard),enter,anchor,inside)
      block=closed_gate(ids,guard,inside,messages)
      retreat=N.door!(ids.fetch(guard),ids.fetch(road),leave,inside,exit)
      {"enter"=>walk,"blocked"=>block,"retreat"=>retreat}
    end
    result={"native_seams"=>[forward,into_city,back_from_city,returned],
            "native_underground"=>out+back,"saffron_guards"=>gates,
            "rocket_available"=>false,"manual_playthrough"=>false,"published"=>false}
    File.write("Data/blue-kanto-k06-approach-proof.txt",result.inspect)
    puts "KANTO_K06_NATIVE_APPROACH_OK"
  end
end
