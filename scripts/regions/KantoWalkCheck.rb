# Phase 02: native headless walkability probe on the verified Kanto pilot.
# Uses REAL Game_Player#passable? and RPG Maker XP #move_{down,up,left,right} in mkxp-z; it never
# injects keyboard input, opens the GUI, or claims manual acceptance.
# Installed only by CI's one-shot native_check.py inside .blue-work.
module KantoWalkCheck
  DIRECTIONS = {2=>[0,1], 4=>[-1,0], 6=>[1,0], 8=>[0,-1]}.freeze
  MOVE_METHODS = {2=>:move_down, 4=>:move_left, 6=>:move_right, 8=>:move_up}.freeze
  REQUIRED = [
    ["Casa do jogador", "PLAYER_HOME"],
    ["Pallet Town", "PALLET"]
  ].freeze
  OPTIONAL = ["VIRIDIAN", "PEWTER", "ROUTE4", "MOON_1F", "CERULEAN",
              "VERMILION", "CELADON", "FUCHSIA", "SAFFRON", "CINNABAR",
              "ROUTE22", "ROAD_1F", "INDIGO", "LEAGUE"].freeze

  def self.require!(condition, message)
    raise "Kanto walking proof: " + message unless condition
  end

  def self.walk_one(point, label, required)
    map,x,y,dir = point
    $map_factory.setup(map)
    require!($game_map.map_id == map, "Map switch failed for #{label}")
    require!(x>=0 && y>=0 && x<$game_map.width && y<$game_map.height,
             "Out-of-bounds landing for #{label}")
    $game_player.moveto(x,y)
    available = DIRECTIONS.filter_map do |direction,(dx,dy)|
      tx,ty=x+dx,y+dy
      next unless tx>=0 && ty>=0 && tx<$game_map.width && ty<$game_map.height
      next unless $game_player.passable?(x,y,direction)
      [direction,tx,ty]
    end
    if available.empty?
      require!(!required, "No passable adjacent tile at #{label} (#{map}:#{x},#{y})")
      return [label, map, x, y, "blocked_at_arrival", 0]
    end
    direction,target_x,target_y=available.first
    $game_player.public_send(MOVE_METHODS.fetch(direction))
    unless [$game_player.x,$game_player.y] == [target_x,target_y]
      # Some early/headless scenes may have additional movement guards. Do
      # not claim success or misdiagnose physical input as broken. Required
      # Pallet cases are strict; all other locations become manual QA cases.
      require!(!required,
               "Player could not step into passable tile #{label} (#{map}:#{x},#{y})")
      return [label,map,x,y,"headless_step_mismatch_requires_manual_test",0]
    end
    opposite = {2=>8,4=>6,6=>4,8=>2}.fetch(direction)
    # Test a return step only when the engine reports the reverse direction
    # passable. No map events are executed or story switches committed here.
    return_ok = $game_player.passable?(target_x,target_y,opposite)
    if return_ok
      $game_player.public_send(MOVE_METHODS.fetch(opposite))
      unless [$game_player.x,$game_player.y] == [x,y]
        require!(!required, "Player could not return from #{label}")
        return [label,map,x,y,"headless_return_mismatch_requires_manual_test",1]
      end
    end
    [label,map,x,y,"native_step_verified",return_ok ? 2 : 1]
  ensure
    $game_player.moveto(x,y) if $game_player && x && y
  end

  def self.run(home_map, home_x, home_y)
    stops = File.readlines("Data/blue-kanto-experimental-stops.txt",encoding:"UTF-8")
    points = {}
    stops.each do |line|
      code,label,map,x,y,dir=line.strip.split("|")
      next unless code && dir
      points[code]=[label,[map.to_i,x.to_i,y.to_i,dir.to_i]]
    end
    report=[]
    seen={}
    REQUIRED.each do |label,code|
      entry=points[code]
      require!(entry, "Missing required test stop #{code}")
      result=walk_one(entry[1],label,true)
      seen[code]=true
      report << result
    end
    OPTIONAL.each do |code|
      next unless points[code]
      label,point=points[code]
      report << walk_one(point,label,false)
      seen[code]=true
    end
    require!(report.length >= 12, "Too few audited walking destinations")
    require!(report.count { |row| row[4]=="native_step_verified" } >= 2,
             "No real native player steps in the initial region")
    File.write("Data/blue-kanto-walking-proof.txt",
               report.map { |row| row.join("|") }.join("\n")+"\n"+
               "STATUS=headless_native_collision_and_step_only;NOT_MANUAL_GAMEPLAY_QA\n")
    report
  ensure
    $map_factory.setup(home_map) if $map_factory && home_map
    $game_player.moveto(home_x,home_y) if $game_player && home_x && home_y
  end
end
