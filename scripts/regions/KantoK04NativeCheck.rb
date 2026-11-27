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

  def self.door(ids, source, eid, dest, anchor)
    from,to = ids.values_at(source,dest)
    component = C.opening_component(from,anchor)
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
    first_anchor = entry.fetch("to_xy")
    first_ladders = (13..16).filter_map { |id| door(ids,90,id,91,first_anchor) }
    first_ladders.each do |down|
      lower_anchor = down.fetch("to_xy")
      (27..30).each do |id|
        up = door(ids,91,id,90,lower_anchor)
        next unless up
        exit_leg = door(ids,90,last,87,up.fetch("to_xy"))
        next unless exit_leg
        require!(exit_leg["to_xy"] == (north ? [8,68] : [8,30]), "wrong tunnel mouth return")
        at = anchor
        results = [entry,down,up,exit_leg].map do |leg|
          trace("TOUCH", [leg,at])
          receipt = D.door!(leg,at)
          at = leg.fetch("to_xy")
          receipt
        end
        return results
      end
    end
    raise "K04 no collision-verified path through B1F from exterior mouth #{first} to #{last}"
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
    require!($bag.add(hm), "could not add Flash HM to synthetic bag")
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
      {"hm"=>hm.to_s,"initial_radius"=>radius,"illuminated_radius"=>dark.radius,"native_effect"=>true}
    ensure
      scene.send(:disposeSpritesets) if scene.respond_to?(:disposeSpritesets,true)
      $scene = previous
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
    center_path = [39,86,87,88].map { |sid| ids[sid] }
    from_city = C.k03a_chain(center_path,[22,20],[7,8])
    to_city = C.k03a_chain(center_path.reverse,[7,8],[22,20])
    require!(from_city && to_city && [from_city,to_city].all? { |legs| legs.length == 3 },
      "Cerulean / routes / medical center corridor is not reciprocal")
    into_center = D.door!(from_city.last,from_city[-2].fetch("to_xy"))
    from_center = D.door!(to_city.first,[7,8])
    trace("CENTER_RETURN",from_center)
    north = passage(ids,12,17,from_center.fetch("landing"))
    south = passage(ids,13,1,north.last.fetch("landing"))
    trace("PASSAGES", {"north_to_south"=>north.length,"south_to_north"=>south.length})
    flash = flash!(ids)
    report = {"map_ids"=>ids,"encounters"=>encounters,"center_door"=>into_center,
      "center_return"=>from_center,"north_to_south"=>north,"south_to_north"=>south,
      "seams"=>[from_city.take(2),to_city.drop(1)],"flash"=>flash,
      "manual_playthrough"=>false,"not_a_release"=>true}
    File.write("Data/blue-kanto-k04-proof.txt",report.inspect)
    puts "KANTO_K04_NATIVE_CORRIDOR_FLASH_OK"
  end
end
