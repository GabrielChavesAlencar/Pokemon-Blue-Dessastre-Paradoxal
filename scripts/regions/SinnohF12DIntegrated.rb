# Private project-authored gameplay candidate.
module BlueSinnohF12DIntegrated
  LOCATIONS=__LOCATIONS__.freeze
  SPECS=__SPECS__.freeze
  EDIT_CELLS=__EDIT_CELLS__.freeze
  CHASE_LANES=__CHASE_LANES__.freeze
  CELESTIC_LANES=__CELESTIC_LANES__.freeze
  SURF_ROUTES=__SURF_ROUTES__.freeze
  SURF_DRY_PORTALS=__SURF_DRY_PORTALS__.freeze
  NORTH_ROCK_EDGES=__NORTH_ROCK_EDGES__.freeze
  LAKE_ORDER=%w[VALOR VERITY ACUITY].freeze
  LAKE_LEDGER="sinnoh_f12d_lakes".freeze
  T=BlueSinnohF12D3Transaction
  def self.lake_history(s)
    h=s.fetch(LAKE_LEDGER,[])
    return nil unless h.is_a?(Array) && h.length<=LAKE_ORDER.length && h==LAKE_ORDER.first(h.length)
    h.dup
  end
  def self.lake_allowed?(s,key,badges)
    h=lake_history(s)
    T.cleared?(s) && h && LAKE_ORDER[h.length]==key && badges.include?("MINE") &&
      (key!="ACUITY" || badges.include?("ICICLE"))
  end
  def self.state
    return nil unless defined?(BlueSinnohF12C3)
    s=BlueSinnohF12C3.state
    return nil unless s && BlueSinnohF12D.ready?(s) && T.history(s)
    s
  end
  def self.original_lake_entry_allowed?(a,b)
    s=state
    return false unless s && T.cleared?(s) && defined?(BlueRegions)
    badges=BlueRegions.local_achievements(s,"SINNOH")
    return false unless badges.include?("MINE")
    return badges.include?("ICICLE") if [[159,161],[161,159],[161,162],[162,161]].include?([a,b])
    # Route 216 is needed before earning ICICLE. The lake entry itself
    # still requires ICICLE; this original cave pair only requires MINE.
    [[82,156],[156,82],[195,196],[196,195],[214,215],[215,214],[215,217],[217,215]].include?([a,b])
  end
  def self.rock_reference_valid?
    return false unless defined?(GameData::TerrainTag)
    tag=GameData::TerrainTag.try_get(4)
    tag && tag.id==:Rock && tag.id_number==4 && !tag.can_surf && !tag.ice && !tag.ledge &&
      !tag.bridge && !tag.ignore_passability && !tag.must_walk && !tag.must_walk_or_run &&
      !tag.waterfall && !tag.waterfall_crest && !tag.can_dive && !tag.deep_bush
  end
  # Native method behavior on controlled map doubles. This is a compiler
  # acceptance gate, not gameplay QA. It exercises the loaded engine and
  # rejects unknown overrides or unexpected collision outcomes.
  class CompileProbeMap
    attr_accessor :allow_exit, :allow_entry, :events
    attr_reader :calls
    def initialize
      @allow_exit=true; @allow_entry=true; @events={}; @calls=[]
    end
    def map_id; 473; end
    def valid?(x,y); x>=0 && x<3 && y>=0 && y<3; end
    def validLax?(x,y); x>=-1 && x<=3 && y>=-1 && y<=3; end
    def passage(x,y,d,strict)
      @calls << [x,y,d,strict]
      (x==1 && y==1) ? @allow_exit : @allow_entry
    end
    def passable?(x,y,d,entity); passage(x,y,d,false); end
    def passableStrict?(x,y,d,entity); passage(x,y,d,true); end
  end
  class CompileProbeFactory
    attr_accessor :allow
    attr_reader :calls
    def initialize(allow); @allow=allow; @calls=[]; end
    def isPassableFromEdge?(x,y,*args)
      @calls << [x,y]; @allow
    end
  end
  class CompileProbeEvent
    attr_accessor :through, :character_name
    def initialize(x,y,through=false,character_name="Probe")
      @x=x; @y=y; @through=through; @character_name=character_name
    end
    def at_coordinate?(x,y); @x==x && @y==y; end
  end
  def self.verify_native_movement!
    raise "Sinnoh F12D: passable? owner inesperado" unless Game_Player.instance_method(:passable?).owner==Game_Player
    raise "Sinnoh F12D: super de passable? inesperado" unless Game_Player.instance_method(:passable?).super_method &&
      Game_Player.instance_method(:passable?).super_method.owner==Game_Character
    previous=[$game_map,$map_factory,$game_player,$DEBUG,$game_switches,$game_variables,$game_self_switches,$game_temp]
    begin
      $DEBUG=false
      # Decades has an additional passable? branch before the ordinary
      # superclass checks. At compile time there is no New Game state.
      # Exercise it with actual native default containers, not permissive
      # mocks, and restore every global even if the collision probe fails.
      $game_switches=Game_Switches.new
      $game_variables=Game_Variables.new
      $game_self_switches=Game_SelfSwitches.new
      $game_temp=Game_Temp.new
      $game_map=CompileProbeMap.new
      $map_factory=nil
      $game_player=Game_Player.new
      puts "SINNOH_F12D_NATIVE_STAGE FRESH_MOVEMENT_CONTEXT"
      p=$game_player
      p.instance_variable_set(:@x,1); p.instance_variable_set(:@y,1)
      p.instance_variable_set(:@width,1); p.instance_variable_set(:@height,1)
      p.instance_variable_set(:@through,false); p.instance_variable_set(:@character_name,"Probe")
      check=lambda do |label,expected,x,y,d,strict|
        actual=p.passable?(x,y,d,strict)
        raise "Sinnoh F12D: prova passable? #{label} x=#{x} y=#{y} dir=#{d} strict=#{strict} expected=#{expected.inspect} actual=#{actual.inspect}" unless actual==expected
      end
      [2,4,6,8].each do |dir|
        dx=(dir==6 ? 1 : dir==4 ? -1 : 0)
        dy=(dir==2 ? 1 : dir==8 ? -1 : 0)
        [false,true].each do |strict|
          $game_map.allow_exit=true; $game_map.allow_entry=true
          $game_map.calls.clear
          check.call("dry",true,1,1,dir,strict)
          raise "Sinnoh F12D: duas direcoes de passagem" unless $game_map.calls==[[1,1,dir,strict],[1+dx,1+dy,10-dir,strict]]
          $game_map.allow_exit=false
          check.call("blocked_origin",false,1,1,dir,strict)
          $game_map.allow_exit=true; $game_map.allow_entry=false
          check.call("blocked_destination",false,1,1,dir,strict)
          $game_map.allow_entry=true
          $game_map.events={1=>CompileProbeEvent.new(1+dx,1+dy)}
          check.call("solid_event",false,1,1,dir,strict)
          $game_map.events[1].through=true
          check.call("through_event",true,1,1,dir,strict)
          $game_map.events[1].through=false; $game_map.events[1].character_name=""
          check.call("invisible_event",true,1,1,dir,strict)
          $game_map.events={}
        end
      end
      check.call("outside_lax",false,3,1,6,false)
      check.call("no_factory",false,2,1,6,false)
      $map_factory=CompileProbeFactory.new(false)
      check.call("closed_edge",false,2,1,6,false)
      $map_factory.allow=true
      check.call("open_edge",true,2,1,6,false)
      raise "Sinnoh F12D: coordenada de borda" unless $map_factory.calls==[[3,1],[3,1]]
      true
    ensure
      $game_map,$map_factory,$game_player,$DEBUG,$game_switches,$game_variables,$game_self_switches,$game_temp=*previous
    end
  end
  def self.verify_native_transaction!
    raise "Sinnoh F12D: bolsa nativa ausente" unless defined?(PokemonBag)
    initial={"current"=>"SINNOH","sinnoh_f12d_quest"=>T::CHASE.dup}
    bag=PokemonBag.new
    first=T.stage(initial,bag,T::ORDER[0],catalogue_verified:true,geometry_verified:true)
    raise "Sinnoh F12D: entrega nativa falhou" unless first && bag.quantity(T::ITEM)==0 && first[:bag].quantity(T::ITEM)==1
    s,b=Marshal.load(Marshal.dump([first[:state],first[:bag]]))
    raise "Sinnoh F12D: entrega repetida" if T.stage(s,b,T::ORDER[0],catalogue_verified:true,geometry_verified:true)
    last=T.stage(s,b,T::ORDER[1],catalogue_verified:true,geometry_verified:true)
    raise "Sinnoh F12D: consumo nativo falhou" unless last && b.quantity(T::ITEM)==1 && last[:bag].quantity(T::ITEM)==0
    final_s,final_b=Marshal.load(Marshal.dump([last[:state],last[:bag]]))
    raise "Sinnoh F12D: persistencia nativa falhou" unless T.cleared?(final_s) && final_b.quantity(T::ITEM)==0
    raise "Sinnoh F12D: consumo repetido" if T.stage(final_s,final_b,T::ORDER[1],catalogue_verified:true,geometry_verified:true)
    true
  end
  # Verify only terrain catalogue semantics here. Real Surf movement and
  # regional HM acquisition still require their own actual runtime evidence.
  def self.lake_surf_terrain_reference?
    return false unless defined?(GameData::TerrainTag)
    [5,6].all? do |n|
      tag=GameData::TerrainTag.try_get(n)
      tag && tag.id_number==n && tag.can_surf && !tag.waterfall && !tag.waterfall_crest && !tag.ledge && !tag.bridge
    end
  end
  # Regional pickup is transactional: stage on deep copies, then atomically
  # replace the local receipt and bag. Never adopt an item already in a bag.
  def self.surf_hm_valid?
    item=GameData::Item.try_get(:HM03)
    !!(item && item.is_HM? && item.move==:SURF && BlueRegionTravel.regional_item?(:HM03))
  end
  def self.surf_pickup_story_ready?(s)
    h=T.history(s)
    return false unless h && h.include?(T::ORDER[0])
    T.cleared?(s) || (LOCATIONS.key?("SURF_HM03") && LOCATIONS["SURF_HM03"]==LOCATIONS["CYNTHIA"])
  end
  def self.stage_surf_pickup(s,bag)
    return nil unless s && surf_pickup_story_ready?(s) && BlueRegions.valid_sinnoh_badges?(s) &&
      s["current"]=="SINNOH" && BlueRegions.local_achievements(s,"SINNOH").include?("FEN") && surf_hm_valid?
    claims=BlueRegions.sinnoh_local_hms(s)
    return nil unless claims && !claims.include?("SURF") && bag && bag.quantity(:HM03)==0
    next_s=Marshal.load(Marshal.dump(s))
    next_bag=Marshal.load(Marshal.dump(bag))
    return nil unless next_bag.add(:HM03,1) && next_bag.quantity(:HM03)==1
    return nil unless BlueRegions.record_sinnoh_hm(next_s,"SURF",:HM03,next_bag,true)
    return nil unless BlueRegions.field_access(next_s,"SINNOH","SURF",true)==:allowed &&
      bag.quantity(:HM03)==0 && BlueRegions.sinnoh_local_hms(s)==claims
    {state:next_s,bag:next_bag}
  rescue StandardError
    nil
  end
  def self.surf_permission(s,bag,party,selected=nil)
    return :unavailable unless s && s["current"]=="SINNOH" && T.cleared?(s)
    outcome=BlueRegions.field_access(s,"SINNOH","SURF",true)
    return outcome unless outcome==:allowed
    return :hm unless surf_hm_valid? && bag && bag.has?(:HM03)
    eligible=Array(party).any? do |p|
      p && (!selected || p.equal?(selected)) && !p.egg? && !p.fainted? &&
        p.respond_to?(:compatible_with_move?) && p.compatible_with_move?(:SURF)
    end
    eligible ? :allowed : :pokemon
  rescue StandardError
    :unavailable
  end
  def self.surf_route_mode(cell)
    return nil unless cell.is_a?(Array) && cell.length==3
    route=SURF_ROUTES[cell[0]]
    row=route && route.find { |q| q[0]==cell[1] && q[1]==cell[2] }
    row && row[2]
  end
  def self.surf_route_edge?(a,b)
    return false unless a.is_a?(Array) && b.is_a?(Array) && a.length==3 && b.length==3 && a[0]==b[0]
    return false unless (a[1]-b[1]).abs+(a[2]-b[2]).abs==1
    route=SURF_ROUTES[a[0]]
    return false unless route
    route.each_cons(2).any? { |x,y| [x[0,2],y[0,2]]==[a[1,2],b[1,2]] || [y[0,2],x[0,2]]==[a[1,2],b[1,2]] }
  end
  def self.surf_step_allowed?(s,bag,party,surfing,a,b,boarding=false)
    return false unless surf_route_edge?(a,b) && surf_permission(s,bag,party)==:allowed
    origin=surf_route_mode(a);target=surf_route_mode(b)
    return origin=="walk" && target=="surf" && !surfing if boarding
    surfing && origin=="surf" && ["walk","surf"].include?(target)
  end
  def self.runtime_surf_step_allowed?(a,b,boarding=false)
    return false unless LOCATIONS.key?("SURF_HM03") && $PokemonGlobal && $game_map && $game_player
    return false unless surf_step_allowed?(state,$bag,$player && $player.party,$PokemonGlobal.surfing,a,b,boarding)
    return false unless a[0]==$game_map.map_id && a[1]==$game_player.x && a[2]==$game_player.y
    # Both endpoints must still match the certified terrain. A stale
    # shoreline or changed origin must not authorize the aquatic exception.
    [a,b].each do |cell|
      tag=$game_map.terrain_tag(cell[1],cell[2])
      water=surf_route_mode(cell)=="surf"
      return false unless tag && (water ? tag.can_surf_freely : !tag.can_surf)
    end
    # Reject all occupied targets, including invisible scripted events,
    # in the aquatic exception. Native collision checks still apply.
    return false if $game_map.events.values.any? { |event| event.at_coordinate?(b[1],b[2]) }
    true
  rescue StandardError
    false
  end
  module NativeSurfEntry
    def pbStartSurfing(*args,&block)
      return super unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
      return false unless $game_player && $game_map && $map_factory && $PokemonGlobal
      a=[$game_map.map_id,$game_player.x,$game_player.y]
      b=$map_factory.getFacingTile($game_player.direction,$game_player)
      return false unless BlueSinnohF12DIntegrated.runtime_surf_step_allowed?(a,b,true)
      # Native pbStartSurfing sets surfing and calls jumpForward. Do not
      # manufacture movement with moveto, through or altered passages.
      result=super
      unless $game_player.x==b[1] && $game_player.y==b[2] && $PokemonGlobal.surfing
        pbCancelVehicles
        return false
      end
      result
    end
    private :pbStartSurfing
  end
  def self.offer_surf(s)
    return false unless near?("SURF_HM03") && s && !s.frozen? && state.equal?(s) &&
      defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return !!($bag && $bag.has?(:HM03)) if BlueRegions.sinnoh_local_hms(s)&.include?("SURF")
    return false unless pbConfirmMessage(_INTL("Cynthia: deseja receber a HM Surf de Sinnoh?"))
    bag=$bag;staged=stage_surf_pickup(s,bag)
    return false unless staged && state.equal?(s) && $bag.equal?(bag)
    old=s["region_local_hms"];existed=s.key?("region_local_hms")
    begin
      s["region_local_hms"]=staged[:state]["region_local_hms"]
      $bag=staged[:bag]
      raise "Sinnoh HM03 commit" unless BlueRegions.sinnoh_local_hms(s).include?("SURF") && $bag.quantity(:HM03)==1
    rescue StandardError
      $bag=bag
      existed ? s["region_local_hms"]=old : s.delete("region_local_hms")
      return false
    end
    pbMessage(_INTL("Voce recebeu a HM03 Surf de Sinnoh!"))
    true
  end
  # Actual compiled catalogue, PokemonBag and regional state receipt. No
  # synthetic map traversal or claim that the player has used Surf.
  # Compile-only execution precedes New Game. DBK's real Pokemon constructor
  # reads native indexed globals (Terastallization#getTeraType). Never
  # replace Pokemon.new or disable a mechanic to make this probe pass.
  def self.with_native_surf_pokemon_context
    previous=[$game_variables,$game_switches,$game_self_switches,$game_temp,$PokemonGlobal,$stats]
    begin
      $game_variables=Game_Variables.new
      $game_switches=Game_Switches.new
      $game_self_switches=Game_SelfSwitches.new
      $game_temp=Game_Temp.new
      $PokemonGlobal=PokemonGlobalMetadata.new
      $stats=GameStats.new
      yield
    ensure
      $game_variables,$game_switches,$game_self_switches,$game_temp,$PokemonGlobal,$stats=*previous
    end
  end
  def self.verify_native_surf_pickup!
    with_native_surf_pokemon_context { verify_native_surf_pickup_in_context! }
  end
  def self.verify_native_surf_pickup_in_context!
    raise "Sinnoh HM03 catalogue" unless surf_hm_valid?
    s=BlueRegions.new_state("SINNOH")
    s["sinnoh_f12d_quest"]=T::CHASE.dup;s[T::LEDGER]=T::ORDER.dup
    b=PokemonBag.new
    raise "Sinnoh HM03 before badge" if stage_surf_pickup(s,b)
    s["achievements"]["SINNOH"]=["FEN"]
    early=Marshal.load(Marshal.dump(s));early[T::LEDGER]=[]
    raise "Sinnoh HM03 before potion" if stage_surf_pickup(early,b)
    preclear=Marshal.load(Marshal.dump(s));preclear[T::LEDGER]=[T::ORDER[0]]
    if LOCATIONS["SURF_HM03"]==LOCATIONS["CYNTHIA"]
      early_pair=stage_surf_pickup(preclear,b)
      raise "Sinnoh HM03 existing Cynthia receipt" unless early_pair
      raise "Sinnoh HM03 early Surf" unless surf_permission(early_pair[:state],early_pair[:bag],[])==:unavailable
    else
      raise "Sinnoh HM03 early Celestic pickup" if stage_surf_pickup(preclear,b)
    end
    raise "Sinnoh HM03 missing receipt gate" unless surf_permission(s,b,[])==:hm
    foreign=Marshal.load(Marshal.dump(s));foreign["current"]="KANTO"
    raise "Sinnoh HM03 foreign pickup" if stage_surf_pickup(foreign,b)
    borrowed=PokemonBag.new
    raise "Sinnoh HM03 test bag" unless borrowed.add(:HM03,1)
    raise "Sinnoh HM03 borrowed item" if stage_surf_pickup(s,borrowed)
    next_pair=stage_surf_pickup(s,b)
    raise "Sinnoh HM03 staged receipt" unless next_pair && b.quantity(:HM03)==0 && BlueRegions.sinnoh_local_hms(s).empty?
    saved,bag=Marshal.load(Marshal.dump([next_pair[:state],next_pair[:bag]]))
    raise "Sinnoh HM03 persistent receipt" unless BlueRegions.sinnoh_local_hms(saved).include?("SURF") && bag.quantity(:HM03)==1
    raise "Sinnoh HM03 duplicate" if stage_surf_pickup(saved,bag)
    raise "Sinnoh HM03 incompatible party" unless surf_permission(saved,bag,[])==:pokemon
    no_badge=Marshal.load(Marshal.dump(saved));no_badge["achievements"]["SINNOH"]=[]
    raise "Sinnoh HM03 missing badge" unless surf_permission(no_badge,bag,[])==:badge
    raise "Sinnoh HM03 missing item" unless surf_permission(saved,PokemonBag.new,[])==:hm
    # Exercise real compiled species compatibility rather than a permissive
    # party double. The Pokemon is temporary and never written to a save.
    candidate=[:PIPLUP,:PSYDUCK,:GOLBAT].lazy.filter_map do |id|
      next unless GameData::Species.exists?(id)
      Pokemon.new(id,20)
    end.find { |pkmn| !pkmn.egg? && !pkmn.fainted? && pkmn.compatible_with_move?(:SURF) }
    raise "Sinnoh HM03 compatible native species missing" unless candidate
    raise "Sinnoh HM03 compatible party" unless surf_permission(saved,bag,[candidate],candidate)==:allowed
    raise "Sinnoh HM03 selected not in party" unless surf_permission(saved,bag,[],candidate)==:pokemon
    # An actual compatible Pokemon must not mask a missing regional receipt,
    # badge or item. An empty party alone cannot establish those gates.
    raise "Sinnoh HM03 borrowed receipt gate" unless surf_permission(s,borrowed,[candidate],candidate)==:hm
    raise "Sinnoh HM03 badge with compatible party" unless surf_permission(no_badge,bag,[candidate],candidate)==:badge
    raise "Sinnoh HM03 item with compatible party" unless surf_permission(saved,PokemonBag.new,[candidate],candidate)==:hm
    incompatible=[:STARLY,:SHINX,:BIDOOF,:WURMPLE].lazy.filter_map do |id|
      next unless GameData::Species.exists?(id)
      Pokemon.new(id,20)
    end.find { |pkmn| !pkmn.egg? && !pkmn.fainted? && !pkmn.compatible_with_move?(:SURF) }
    raise "Sinnoh HM03 incompatible native species missing" unless incompatible
    raise "Sinnoh HM03 incompatible native party" unless surf_permission(saved,bag,[incompatible],incompatible)==:pokemon
    SURF_ROUTES.each do |mid,route|
      shore=route.each_cons(2).find { |a,b| a[2]=="walk" && b[2]=="surf" }
      raise "Sinnoh HM03 route lacks boarding #{mid}" unless shore
      a,b=shore.map { |x,y,_| [mid,x,y] }
      raise "Sinnoh HM03 permitted boarding #{mid}" unless surf_step_allowed?(saved,bag,[candidate],false,a,b,true)
      raise "Sinnoh HM03 borrowed boarding #{mid}" if surf_step_allowed?(s,borrowed,[candidate],false,a,b,true)
      raise "Sinnoh HM03 badge boarding #{mid}" if surf_step_allowed?(no_badge,bag,[candidate],false,a,b,true)
      raise "Sinnoh HM03 item boarding #{mid}" if surf_step_allowed?(saved,PokemonBag.new,[candidate],false,a,b,true)
      raise "Sinnoh HM03 incompatible boarding #{mid}" if surf_step_allowed?(saved,bag,[incompatible],false,a,b,true)
      raise "Sinnoh HM03 dry movement #{mid}" if surf_step_allowed?(saved,bag,[candidate],false,a,b)
    end
    true
  end
  # Read the actual private RXDATA and use Game_Map/Game_Player native
  # collision methods. This verifies the complete path in both directions,
  # including boarding and landing collision, not scene animation or QA.
  def self.verify_native_surf_map_collision!
    raise "Sinnoh Surf terrain" unless lake_surf_terrain_reference?
    raise "Sinnoh Surf hooks" unless Object.ancestors.include?(NativeSurfEntry)
    prev=[$game_map,$map_factory,$game_player,$DEBUG,$game_switches,$game_variables,$game_self_switches,$game_temp,$PokemonGlobal,$stats]
    begin
      $DEBUG=false;$map_factory=nil
      $game_switches=Game_Switches.new;$game_variables=Game_Variables.new
      $game_self_switches=Game_SelfSwitches.new;$game_temp=Game_Temp.new
      $PokemonGlobal=PokemonGlobalMetadata.new
      $stats=GameStats.new
      $game_player=Game_Player.new
      p=$game_player
      # Suppress only scene/event notifications in this compile-only
      # probe. Native jumpForward, jump and passable? remain untouched.
      def p.triggerLeaveTile; end
      p.instance_variable_set(:@width,1);p.instance_variable_set(:@height,1)
      p.instance_variable_set(:@through,false);p.instance_variable_set(:@character_name,"Probe")
      tiles=load_data("Data/Tilesets.rxdata")
      SURF_ROUTES.each do |mid,route|
        raw=load_data(sprintf("Data/Map%03d.rxdata",mid))
        ts=tiles[raw.tileset_id]
        $game_map=Game_Map.new
        {map_id:mid,map:raw,passages:ts.passages,priorities:ts.priorities,terrain_tags:ts.terrain_tags,events:{}}.each do |k,v|
          $game_map.instance_variable_set(:"@#{k}",v)
        end
        # Recheck route occupancy on the actual compiled private map. A
        # certified transfer may stand at a dry endpoint beyond the shore.
        route_cells=route.map { |x,y,_| [x,y] }
        occupied=raw.events.values.filter_map do |event|
          [event.x,event.y,event.id,event.name] if route_cells.include?([event.x,event.y])
        end
        unless occupied.sort==SURF_DRY_PORTALS.fetch(mid,[]).sort
          raise "Sinnoh Surf occupied path #{mid}"
        end
        route.each do |x,y,mode|
          tag=$game_map.terrain_tag(x,y)
          raise "Sinnoh Surf changed terrain #{mid}" unless tag && (mode=="surf" ? tag.can_surf_freely : !tag.can_surf)
        end
        count=0;dry_count=0;boardings=0;landings=0
        [route,route.reverse].each do |path|
          path.each_cons(2) do |a,b|
            ax,ay,am=a;bx,by,bm=b
            raise "Sinnoh Surf noncardinal witness #{mid}" unless (ax-bx).abs+(ay-by).abs==1
            dir=bx>ax ? 6 : bx<ax ? 4 : by>ay ? 2 : 8
            p.instance_variable_set(:@x,ax);p.instance_variable_set(:@y,ay)
            $PokemonGlobal.surfing=false
            if am=="walk" && bm=="walk"
              raise "Sinnoh Surf native dry approach #{mid} #{ax},#{ay}" unless p.passable?(ax,ay,dir)
              dry_count+=1
              next
            end
            raise "Sinnoh Surf water walk leak #{mid}" if bm=="surf" && p.passable?(ax,ay,dir)
            $PokemonGlobal.surfing=true
            raise "Sinnoh Surf native collision #{mid} #{ax},#{ay}" unless p.passable?(ax,ay,dir)
            if am!=bm
              p.instance_variable_set(:@direction,dir)
              # Test native one-tile boarding/landing displacement against
              # original masks. The scene vehicle animation and on_step
              # completion are deliberately not part of this compile probe.
              raise "Sinnoh Surf native jump #{mid} #{ax},#{ay}" unless p.jumpForward && p.x==bx && p.y==by
              if bm=="surf";boardings+=1;else;landings+=1;end
            end
            count+=1
          end
        end
        raise "Sinnoh Surf missing aquatic edges" if count==0
        puts "SINNOH_F12D_NATIVE_SURF_MAP_COLLISION_MAP #{mid} #{count}"
        raise "Sinnoh Surf missing shoreline jump" unless boardings>0 && landings>0
        puts "SINNOH_F12D_NATIVE_SURF_SHORE_JUMP_MAP #{mid} #{boardings} #{landings}"
        raise "Sinnoh Surf incomplete route #{mid}" unless count+dry_count==2*(route.length-1)
        puts "SINNOH_F12D_NATIVE_SURF_FULL_ROUTE_MAP #{mid} #{count+dry_count} #{dry_count}"
      end
      unless NORTH_ROCK_EDGES.empty?
        raise "Sinnoh North terrain" unless rock_reference_valid?
        raw=load_data("Data/Map500.rxdata")
        ts=tiles[raw.tileset_id]
        $game_map=Game_Map.new
        {map_id:500,map:raw,passages:ts.passages,priorities:ts.priorities,terrain_tags:ts.terrain_tags,events:{}}.each do |k,v|
          $game_map.instance_variable_set(:"@#{k}",v)
        end
        occupied=raw.events.values.map { |event| [event.x,event.y] }
        $PokemonGlobal.surfing=false
        NORTH_ROCK_EDGES.each do |mid,ax,ay,bx,by|
          raise "Sinnoh North scope" unless mid==500 && [ax,ay]==[61,73] && (ax-bx).abs+(ay-by).abs==1
          raise "Sinnoh North occupied" if occupied.include?([ax,ay]) || occupied.include?([bx,by])
          raise "Sinnoh North Rock" unless [[ax,ay],[bx,by]].any? { |x,y| $game_map.terrain_tag(x,y).id==:Rock }
          [[ax,ay,bx,by],[bx,by,ax,ay]].each do |x,y,nx,ny|
            dir=nx>x ? 6 : nx<x ? 4 : ny>y ? 2 : 8
            p.instance_variable_set(:@x,x);p.instance_variable_set(:@y,y)
            raise "Sinnoh North native collision #{x},#{y}" unless p.passable?(x,y,dir)
          end
        end
        puts "SINNOH_F12D_NATIVE_NORTH_ROCK_APPROACH_STEPS #{2*NORTH_ROCK_EDGES.length}"
      end
      true
    ensure
      $game_map,$map_factory,$game_player,$DEBUG,$game_switches,$game_variables,$game_self_switches,$game_temp,$PokemonGlobal,$stats=*prev
    end
  end
  def self.verify_compile_inputs!(token,map_files,plugin)
    manifest=BlueSinnohQA.parse_json(File.binread("sinnoh-experimental-qa.json"))
    hashes=manifest.fetch("file_sha256")
    raise "Sinnoh F12D: compile manifest token mismatch" unless manifest.fetch("compile_token")==token
    pbs=hashes.keys.grep(%r{\APBS/[a-zA-Z0-9_]+\.txt\z})
    (map_files + pbs + [plugin]).uniq.each do |path|
      unless File.file?(path) && !File.symlink?(path) && BlueSinnohQA.sha256_file(path)==hashes.fetch(path)
        raise "Sinnoh F12D: changed compile input #{path}"
      end
    end
  end
  def self.verify_compiled!
    raise "Sinnoh F12D: regional Surf pickup missing" unless LOCATIONS.key?("SURF_HM03")
    raise "Sinnoh F12D: original Surf routes missing" unless SURF_ROUTES.length==2
    verify_native_surf_pickup!
    puts "SINNOH_F12D_NATIVE_SURF_PICKUP_TRANSACTION_OK"
    verify_native_surf_map_collision!
    puts "SINNOH_F12D_NATIVE_SURF_MAP_COLLISION_OK"
    raise "Sinnoh F12D: native Surf terrain missing" unless lake_surf_terrain_reference?
    puts "SINNOH_F12D_NATIVE_LAKE_SURF_TERRAIN_REFERENCE_OK"
    raise "Sinnoh F12D3: terreno Rock incompatível" unless rock_reference_valid?
    raise "Sinnoh F12D3: item regional invalido" unless T.compiled_item_valid?
    raise "Sinnoh F12D lagos: equipes invalidas" unless SPECS.values.all? { |spec| BlueSinnohF10B.valid_team?(spec) }
    raise "Sinnoh F12D: hooks ausentes" unless Game_Event.ancestors.include?(BarrierPages) && Game_Player.ancestors.include?(ProgressionMovement)
    raise "Sinnoh F12D: hooks sobrescritos" unless Game_Player.instance_method(:move_generic).owner==ProgressionMovement &&
      Game_Event.instance_method(:refresh).owner==BarrierPages
    # Both native probes have already run at the beginning of the private
    # compile verification. Repeat them here for the complete proof.
    verify_native_movement!
    verify_native_transaction!
    true
  end
  def self.near?(key)
    loc=LOCATIONS[key]
    loc && $game_map && $game_player && $game_map.map_id==loc[0] &&
      ($game_player.x-loc[1]).abs+($game_player.y-loc[2]).abs==1
  end
  def self.commit_item(s,action)
    h=T.history(s)
    return false unless h && !s.frozen? && $bag && state.equal?(s)
    bag=$bag;staged=T.stage(s,bag,action,catalogue_verified:true,geometry_verified:true)
    return false unless staged && state.equal?(s) && $bag.equal?(bag) && T.history(s)==h
    existed=s.key?(T::LEDGER);old=s[T::LEDGER]
    begin
      s[T::LEDGER]=staged[:history]
      $bag=staged[:bag]
      raise "Sinnoh F12D3 commit failed" unless T.history(s)==staged[:history] &&
        $bag.quantity(T::ITEM)==(action==T::ORDER[0] ? 1 : 0)
    rescue StandardError
      $bag=bag
      existed ? s[T::LEDGER]=old : s.delete(T::LEDGER)
      return false
    end
    $game_map.need_refresh=true if $game_map && $game_map.respond_to?(:need_refresh=)
    true
  end
  def self.interact(key)
    s=state
    return false unless s && !@busy && near?(key) && rock_reference_valid?
    @busy=true
    begin
      if key=="CYNTHIA"
        if T.history(s).include?(T::ORDER[0])
          return offer_surf(s) if LOCATIONS["SURF_HM03"]==LOCATIONS["CYNTHIA"]
          return true
        end
        return false unless commit_item(s,T::ORDER[0])
        pbMessage(_INTL("Cynthia: Use esta SecretPotion para ajudar os Psyduck da Rota 210."))
        return true
      elsif key=="SURF_HM03"
        return offer_surf(s)
      elsif key.start_with?("PSYDUCK_")
        return true if T.cleared?(s)
        return false unless T.history(s)==[T::ORDER[0]]
        return false unless pbConfirmMessage(_INTL("Usar a SecretPotion nos Psyduck?"))
        return false unless commit_item(s,T::ORDER[1])
        pbMessage(_INTL("Os quatro Psyduck se afastaram. A passagem para Celestic está livre!"))
        return true
      end
      badges=BlueRegions.local_achievements(s,"SINNOH")
      return false unless lake_allowed?(s,key,badges)
      h=lake_history(s)
      if key=="ACUITY"
        pbMessage(_INTL("Jupiter: A Galactic já terminou aqui. Vamos para a nossa sede!"))
      else
        spec=SPECS[key]
        return false unless spec && $player && $player.party.any? { |p| !p.egg? && p.hp>0 }
        return false unless defined?(BlueCampaign) && BlueCampaign.active? && defined?(BlueCampaign::Teams) &&
          defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
        return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && BlueSinnohF10B.valid_team?(spec)
        return false unless $game_temp && $game_temp.respond_to?(:waiting_trainer) && !$game_temp.waiting_trainer &&
          $game_temp.respond_to?(:battle_rules) && $game_temp.battle_rules.is_a?(Hash) && $game_temp.battle_rules.empty?
        return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
        return false unless TrainerBattle.start_core([spec[0].to_sym,spec[1],spec[2]])==1
      end
      return false unless state.equal?(s) && lake_history(s)==h && lake_allowed?(s,key,BlueRegions.local_achievements(s,"SINNOH"))
      s[LAKE_LEDGER]=h+[key]
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f12d_integrated",error)
    false
  end
  module BarrierPages
    def refresh(*args)
      if defined?($game_self_switches) && $game_self_switches &&
        BlueSinnohF12DIntegrated::LOCATIONS.any? { |key,loc| key.start_with?("PSYDUCK_") && loc[0]==@map_id && loc[3]==@id }
        s=BlueSinnohF12DIntegrated.state
        key=[@map_id,@id,"A"];value=!!(s && BlueSinnohF12DIntegrated::T.cleared?(s))
        $game_self_switches[key]=value if $game_self_switches[key]!=value
      end
      super(*args)
    end
  end
  def self.movement_allowed?(s,current,facing)
    return false unless current.is_a?(Array) && facing.is_a?(Array)
    lane=current+facing
    return !!(s && T.cleared?(s)) if CELESTIC_LANES.include?(lane)
    return !!(s && T.history(s)) if EDIT_CELLS.include?(facing) || CHASE_LANES.include?(lane)
    true
  end
  module ProgressionMovement
    def move_generic(dir,*args,&block)
      if defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy? &&
         $game_map && [2,4,6,8].include?(dir)
        facing=$map_factory && $map_factory.getFacingTile(dir,self)
        return unless facing && BlueSinnohF12DIntegrated.movement_allowed?(
          BlueSinnohF12DIntegrated.state,[$game_map.map_id,x,y],facing)
      end
      super(dir,*args,&block)
    end
  end
  module PrivateSurfPolicy
    def field_result(move,selected=nil)
      if move.to_s.upcase=="SURF" && defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
        return BlueSinnohF12DIntegrated.surf_permission(BlueSinnohF12DIntegrated.state,$bag,$player && $player.party,selected)
      end
      super
    end
    def field_allowed?(move,showmsg=true,selected=nil)
      if move.to_s.upcase=="SURF" && defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
        outcome=field_result(move,selected)
        return true if outcome==:allowed
        if showmsg
          message=case outcome
          when :badge then "Obtenha a Insignia FEN em Sinnoh."
          when :hm then "Obtenha a HM03 e o comprovante local de Surf em Sinnoh."
          when :pokemon then "Voce precisa de um Pokemon compativel com Surf na equipe."
          else "Surf regional indisponivel neste momento."
          end
          pbMessage(_INTL(message))
        end
        return false
      end
      super
    end
    def kanto_field_context?(move)
      if move.to_s.upcase=="SURF" && defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
        return @field_move==:SURF && field_result(:SURF)==:allowed
      end
      super
    end
  end
  def self.bind_pages!
    return false unless defined?(Game_Event) && defined?(Game_Player)
    Game_Event.prepend(BarrierPages) unless Game_Event.ancestors.include?(BarrierPages)
    Game_Player.prepend(ProgressionMovement) unless Game_Player.ancestors.include?(ProgressionMovement)
    if LOCATIONS.key?("SURF_HM03")
      return false unless defined?(BlueRegionalPolicy)
      klass=BlueRegionalPolicy.singleton_class
      klass.prepend(PrivateSurfPolicy) unless klass.ancestors.include?(PrivateSurfPolicy)
      Object.prepend(NativeSurfEntry) unless Object.ancestors.include?(NativeSurfEntry)
    end
    true
  end
end
