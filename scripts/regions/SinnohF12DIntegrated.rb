# Private project-authored gameplay candidate.
module BlueSinnohF12DIntegrated
  LOCATIONS=__LOCATIONS__.freeze
  SPECS=__SPECS__.freeze
  EDIT_CELLS=__EDIT_CELLS__.freeze
  CHASE_LANES=__CHASE_LANES__.freeze
  CELESTIC_LANES=__CELESTIC_LANES__.freeze
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
    [[214,215],[215,214],[215,217],[217,215]].include?([a,b])
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
  def self.verify_compiled!
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
        return true if T.history(s).include?(T::ORDER[0])
        return false unless commit_item(s,T::ORDER[0])
        pbMessage(_INTL("Cynthia: Use esta SecretPotion para ajudar os Psyduck da Rota 210."))
        return true
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
  def self.bind_pages!
    return false unless defined?(Game_Event) && defined?(Game_Player)
    Game_Event.prepend(BarrierPages) unless Game_Event.ancestors.include?(BarrierPages)
    Game_Player.prepend(ProgressionMovement) unless Game_Player.ancestors.include?(ProgressionMovement)
    true
  end
end
