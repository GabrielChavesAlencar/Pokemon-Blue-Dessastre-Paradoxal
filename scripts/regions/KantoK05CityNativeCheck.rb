# Only loaded into the CI Lavender city fixture, never into a release.
module KantoK05CityNativeCheck
  C = KantoNativeCheck
  D = KantoK03ENativeCheck
  DOORS = {
    94=>[6,[7,8],1,[6,6]], 95=>[7,[4,7],1,[20,16]],
    96=>[15,[4,7],5,[5,17]], 97=>[16,[4,7],5,[10,17]],
    98=>[14,[4,7],1,[10,12]]
  }.freeze
  STOCK = [:GREATBALL,:SUPERPOTION,:REVIVE,:ANTIDOTE,:PARALYZEHEAL,
           :BURNHEAL,:ICEHEAL,:ESCAPEROPE,:SUPERREPEL].freeze

  def self.require!(value, why)
    raise "K05 city: #{why}" unless value
    value
  end

  def self.trace(phase, value)
    File.open("Data/blue-kanto-k05-city-stage.txt", "a") { |f| f.puts("#{phase}:#{value.inspect}") }
  end

  def self.move_over_seam!(from, start, dir, to, landing)
    $map_factory.setup(from)
    $game_player.moveto(*start)
    require!($game_player.passable?(*start,dir), "native seam is blocked #{from}/#{start.inspect}")
    previous = $scene
    scene = Scene_Map.new
    begin
      $scene = scene
      scene.send(:createSpritesets)
      $game_temp.encounter_triggered = false
      $game_player.move_generic(dir,true)
      deadline = System.uptime + 5
      while System.uptime < deadline
        Graphics.update
        $game_player.update
        $game_map.update
        break if $game_map.map_id == to && !$game_player.moving? && !$game_player.jumping?
      end
      seen = [$game_player.x,$game_player.y]
      trace("NATIVE_SEAM_MOVE", [from,start,dir,to,landing,$game_map.map_id,seen])
      require!($game_map.map_id == to && seen == landing, "natural crossing did not enter expected map")
      {"from"=>[from,*start],"to"=>[to,*seen],"direction"=>dir,"native_move"=>true}
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
    end
  end

  def self.cross!(route, town)
    comp = C.opening_component(route,[8,68])
    options = C.opening_crossings(route,comp,town)
    pair = options.find { |left,right| left[1] == 89 && right[1] == 0 && C.north_edge_cell(town,right,8) }
    a,b = require!(pair, "Rock Tunnel southern mouth cannot reach a reciprocal Lavender tile")
    [move_over_seam!(route,a,2,town,b),move_over_seam!(town,b,8,route,a)]
  end

  def self.door!(from, dest, eid, anchor, landing)
    D.door!({"from_map"=>from,"to_map"=>dest,"event_id"=>eid,"to_xy"=>landing},
            anchor,settle_motion:true)
  end

  def self.service!(map, anchor, event_id)
    comp = C.opening_component(map,anchor)
    event = require!($game_map.events[event_id], "service event missing #{map}/#{event_id}")
    sample = require!(C.opening_action_witness(comp,event), "service counter inaccessible #{map}/#{event_id}")
    $game_player.moveto(*sample.fetch("standing"))
    $game_player.direction = sample.fetch("direction")
    $game_map.events.each_value { |e| e.clear_starting }
    $game_player.check_event_trigger_there([0])
    require!(event.starting, "action did not start service #{map}/#{event_id}")
    ip = pbMapInterpreter
    ip.setup_starting_event
    require!(ip.running? && ip.instance_variable_get(:@event_id)==event_id,
             "interpreter selected wrong event at #{map}")
    stop = System.uptime + 5
    while ip.running? && System.uptime < stop
      ip.update
      Graphics.update
    end
    require!(!ip.running?, "interpreter did not finish service at #{map}")
    sample
  end

  def self.name_rater!(map)
    mon = Pokemon.new(:BULBASAUR,20)
    stranger = Pokemon.new(:RATTATA,20)
    stranger.owner = Pokemon::Owner.new(($player.id ^ 1), "Visitor", 0, 0)
    $player.party.replace([mon,stranger])
    picked, text = -1,""
    prompts = []
    BlueKantoLavender.define_singleton_method(:select_for_nickname) { picked }
    BlueKantoLavender.define_singleton_method(:pick_nickname) { |pkmn| prompts << pkmn; text }
    before = [mon.name,stranger.name]
    service!(map,[4,7],1)
    require!([mon.name,stranger.name]==before && prompts.empty?, "party cancellation changed a nickname")
    picked = 1
    service!(map,[4,7],1)
    require!(stranger.name==before.last && prompts.empty?, "foreign Pokémon reached text entry")
    picked = 0
    service!(map,[4,7],1)
    require!(mon.name==before.first && prompts==[mon], "empty text entry changed a nickname")
    text = "Folha"
    service!(map,[4,7],1)
    require!(mon.name=="Folha" && stranger.name==before.last, "approved original owner nickname was not applied")
    {"native_action"=>true,"party_cancelled"=>true,"text_cancelled"=>true,"foreign_refused"=>true,
      "renamed"=>mon.name,"input_screens_scripted"=>true}
  end

  def self.no_shortcuts!(ids)
    known = ids.fetch(93)
    rows = File.readlines("PBS/map_connections_kanto.txt").filter_map do |line|
      columns = line.split("#",2).first.to_s.strip.split(",").map(&:strip)
      next unless columns.length == 6 && [columns[0].to_i,columns[3].to_i].include?(known)
      columns
    end
    require!(rows == [[known.to_s,"North","0",ids.fetch(87).to_s,"South","0"]],
             "unapproved Lavender route connection #{rows.inspect}")
    [83,92,99,*(100..106),129,131].each { |sid|
      require!(BlueKantoPilot.kanto_map_id(sid).nil?, "later source Map#{sid} was activated")
    }
    $map_factory.setup(ids.fetch(98))
    require!(!$game_map.events[3], "Fuji reward event present in the first visit")
  end

  def self.save_reopen!(ids)
    map = ids.fetch(93)
    $map_factory.setup(map)
    $game_player.moveto(6,6)
    slot = "Kanto K05 Native City CI"
    path = SaveData.get_full_path(slot)
    require!(!File.exist?(path), "native synthetic slot already exists")
    begin
      require!(Game.save(slot) && File.file?(path), "save failed")
      $map_factory.setup(ids.fetch(87))
      $game_player.moveto(8,68)
      facts = C.reload_native_slot(path)
      require!(facts.fetch("region")=="KANTO" && $game_map.map_id==map &&
               [$game_player.x,$game_player.y]==[6,6], "save lost Lavender location")
      require!($PokemonGlobal.pokecenterMapId==ids.fetch(94), "save lost Lavender Center checkpoint")
      {"map"=>map,"xy"=>[6,6],"center"=>ids.fetch(94)}
    ensure
      File.delete(path) if File.file?(path)
    end
  end

  def self.run
    SaveData.initialize_bootup_values
    Game.start_new
    Object.send(:define_method,:pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
    Object.send(:define_method,:pbConfirmMessage) { |*args| true }
    calls = []
    # Witness the actual stock delivered by the native event interpreter;
    # menus and transactions are not claimed by this automated smoke test.
    Object.send(:define_method,:pbPokemonMart) { |stock,*_args| calls << stock.dup }
    ids = [87,*(93..98)].to_h { |sid| [sid,BlueKantoPilot.kanto_map_id(sid)] }
    require!(ids.values==[605,609,610,611,612,613,614], "wrong map registry")
    previous = $game_system.encounter_disabled
    $game_system.encounter_disabled = true
    $player.party.replace([Pokemon.new(:BULBASAUR,20)])
    no_shortcuts!(ids)
    seams = cross!(ids.fetch(87),ids.fetch(93))
    landing = seams.first.fetch("to")[1,2]
    doors = {}
    DOORS.each do |sid,(enter,inside,leave,outside)|
      area,town = ids.values_at(sid,93)
      doors[sid] = [door!(town,area,enter,landing,inside),door!(area,town,leave,inside,outside)]
      trace("NATIVE_DOOR_PAIR",[sid,doors[sid]])
    end
    $player.party.first.hp = 1
    center = service!(ids.fetch(94),[7,8],2)
    require!($player.party.first.hp==$player.party.first.totalhp &&
             $PokemonGlobal.pokecenterMapId==ids.fetch(94) &&
             BlueKantoPilot.progress.fetch("regional_pokecenters",{}).fetch("KANTO",[]).first==ids.fetch(94),"Lavender nurse did not heal/save regional checkpoint")
    mart = service!(ids.fetch(95),[4,7],2)
    require!(calls==[STOCK] && STOCK.all? { |item| GameData::Item.exists?(item) }, "shop stock differs from original")
    rater = name_rater!(ids.fetch(97))
    saved = save_reopen!(ids)
    report = {"maps"=>ids,"seams"=>seams,"native_door_pairs"=>doors,"center"=>center,
              "mart"=>mart,"stock"=>calls.first,"name_rater"=>rater,"native_save"=>saved,
              "tower_or_fuji_reward"=>false,"manual_playthrough"=>false,"published"=>false}
    File.write("Data/blue-kanto-k05-city-proof.txt",report.inspect)
    puts "KANTO_K05_CITY_NATIVE_OK"
  ensure
    $game_system.encounter_disabled = previous if defined?(previous) && !previous.nil?
  end
end
