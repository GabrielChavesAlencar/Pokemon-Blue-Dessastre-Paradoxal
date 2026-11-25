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
  def self.rock_reference_valid?
    return false unless defined?(GameData::TerrainTag)
    tag=GameData::TerrainTag.try_get(4)
    tag && tag.id==:Rock && !tag.can_surf && !tag.ice && !tag.ledge &&
      !tag.bridge && !tag.ignore_passability && !tag.must_walk && !tag.must_walk_or_run
  end
  def self.verify_compiled!
    raise "Sinnoh F12D3: terreno Rock incompatível" unless rock_reference_valid?
    raise "Sinnoh F12D3: item regional invalido" unless T.compiled_item_valid?
    raise "Sinnoh F12D lagos: equipes invalidas" unless SPECS.values.all? { |spec| BlueSinnohF10B.valid_team?(spec) }
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
        $game_self_switches[[@map_id,@id,"A"]]=!!(s && BlueSinnohF12DIntegrated::T.cleared?(s))
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
