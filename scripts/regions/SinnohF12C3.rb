# Authored private QA mission; compiler and regional gates required.
module BlueSinnohF12C3
  SPECS=__F12C3_SPECS__.freeze
  ENTRY=__F12C3_ENTRY__.freeze
  BIKE=__F12C3_BIKE__.to_sym
  ORDER=%w[GRUNT_1 GRUNT_2 GRUNT_3 JUPITER RESCUE BICYCLE].freeze
  LEDGER="sinnoh_f12c3_quest".freeze
  def self.state
    return nil unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    return nil unless defined?(BlueSinnohPilot) && defined?(BlueRegions)
    s=BlueSinnohPilot.regional_state
    return nil unless s.is_a?(Hash) && s["current"]=="SINNOH" && BlueRegions.valid_sinnoh_badges?(s)
    s
  end
  def self.history(s)
    h=s.fetch(LEDGER,[])
    return nil unless h.is_a?(Array) && h.length<=ORDER.length && h==ORDER.first(h.length)
    h.dup
  end
  def self.cut_allowed?(s)
    return false unless s && BlueRegions.local_achievements(s,"SINNOH").include?("FOREST")
    return false unless $bag && $bag.respond_to?(:has?) && $bag.has?(:HM01)
    item=GameData::Item.try_get(:HM01)
    return false unless item && item.respond_to?(:is_HM?) && item.is_HM? && item.move==:CUT
    return false unless $player && $player.party.any? { |p| !p.egg? && p.hp>0 && p.respond_to?(:compatible_with_move?) && p.compatible_with_move?(:CUT) }
    BlueRegions.field_access(s,"SINNOH","CUT",true)==:allowed
  end
  def self.mars_complete?(s)
    s.fetch("sinnoh_f12b5_quest",[])==%w[WINDWORKS_GUARD MEADOW_GRUNT_1 MEADOW_GRUNT_2 WORKS_KEY MARS]
  end
  def self.hm_valid?
    item=GameData::Item.try_get(:HM01)
    item && item.respond_to?(:is_HM?) && item.is_HM? && item.move==:CUT
  end
  def self.offer_cut(s)
    return false unless s && !s.frozen? && mars_complete?(s) && hm_valid?
    return false unless BlueRegions.local_achievements(s,"SINNOH").include?("FOREST")
    claims=BlueRegions.sinnoh_local_hms(s)
    return false unless claims && !claims.include?("CUT")
    return false unless $bag && $bag.respond_to?(:has?) && $bag.respond_to?(:add) && $bag.respond_to?(:remove)
    return false if $bag.has?(:HM01)
    return false unless pbConfirmMessage(_INTL("Guia de Eterna: deseja receber a HM Cut de Sinnoh?"))
    return false unless $bag.add(:HM01) && $bag.has?(:HM01)
    unless BlueRegions.record_sinnoh_hm(s,"CUT",:HM01,$bag,true)
      $bag.remove(:HM01,1)
      return false
    end
    pbMessage(_INTL("Voce recebeu a HM Cut regional!"))
    true
  end
  def self.enter
    s=state
    return false unless s && $game_map && $game_map.map_id==ENTRY[0] && $game_player
    return false unless ($game_player.x-ENTRY[1]).abs+($game_player.y-ENTRY[2]).abs==1
    return false unless mars_complete?(s)
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return true if offer_cut(s)
    unless cut_allowed?(s)
      pbMessage(_INTL("Voce precisa da Insignia da Floresta, HM Cut de Sinnoh e um Pokemon compativel."))
      return false
    end
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return false unless $game_temp && $scene && $scene.respond_to?(:transfer_player)
    pbFadeOutIn do
      $game_temp.player_new_map_id=ENTRY[3]
      $game_temp.player_new_x=ENTRY[4]
      $game_temp.player_new_y=ENTRY[5]
      $game_temp.player_new_direction=2
      pbDismountBike
      $scene.transfer_player
      $game_map.autoplay
      $game_map.refresh
    end
    true
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f12c3_entry",error)
    false
  end
  def self.bike_valid?
    item=GameData::Item.try_get(BIKE)
    item && item.respond_to?(:is_key_item?) && item.is_key_item? &&
      defined?(BlueRegionTravel) && BlueRegionTravel.regional_item?(BIKE)
  end
  def self.verify_compiled!
    raise "Sinnoh F12C3: bicicleta regional invalida" unless bike_valid?
    raise "Sinnoh F12C4: HM01 invalida" unless hm_valid?
    raise "Sinnoh F12C3: equipes divergentes" unless ORDER.first(4).all? { |key| BlueSinnohF10B.valid_team?(SPECS.fetch(key)) }
    true
  end
  def self.jupiter_opponent?(trainer)
    return false unless @jupiter_active && trainer && trainer.respond_to?(:trainer_type) &&
      trainer.respond_to?(:name) && trainer.respond_to?(:version)
    spec=SPECS.fetch("JUPITER")
    trainer.trainer_type.to_s==spec[0] && trainer.name==spec[1] && trainer.version==spec[2]
  end
  module CampaignBoss
    def boss?(trainer)
      BlueSinnohF12C3.jupiter_opponent?(trainer) || super
    end
  end
  module StoryBoss
    def regional_first_boss?(trainers)
      Array(trainers).any? { |t| BlueSinnohF12C3.jupiter_opponent?(t) } || super
    end
  end
  def self.interact(key)
    s=state
    spec=SPECS[key]
    return false unless s && spec && !s.frozen? && $game_map && $game_map.map_id==spec[3]
    h=history(s)
    return false unless h && cut_allowed?(s)
    return true if h.include?(key)
    return false unless ORDER[h.length]==key && !@busy
    return false unless s.fetch("sinnoh_f12b5_quest",[])==%w[WINDWORKS_GUARD MEADOW_GRUNT_1 MEADOW_GRUNT_2 WORKS_KEY MARS]
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    @busy=true
    begin
      if key=="RESCUE"
        s[LEDGER]=h+[key]
        pbMessage(_INTL("Obrigado por resgatar os Pokemon!"))
        return true
      elsif key=="BICYCLE"
        return false unless bike_valid? && $bag && $bag.respond_to?(:has?) && $bag.respond_to?(:add)
        return false if $bag.has?(BIKE)
        return false unless $bag.add(BIKE) && $bag.has?(BIKE)
        s[LEDGER]=h+[key]
        pbMessage(_INTL("Voce recebeu a bicicleta de Sinnoh!"))
        return true
      end
      return false unless $player && $player.party.any? { |p| !p.egg? && p.hp>0 }
      return false unless defined?(BlueCampaign) && BlueCampaign.active? && defined?(BlueCampaign::Teams) &&
        defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
      return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && BlueSinnohF10B.valid_team?(spec)
      return false unless $game_temp && $game_temp.respond_to?(:waiting_trainer) && !$game_temp.waiting_trainer &&
        $game_temp.respond_to?(:battle_rules) && $game_temp.battle_rules.is_a?(Hash) && $game_temp.battle_rules.empty?
      return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
      if key=="JUPITER"
        return false unless defined?(BlueStory) && BlueStory.respond_to?(:regional_first_boss?)
        BlueCampaign.singleton_class.prepend(CampaignBoss) unless BlueCampaign.singleton_class.ancestors.include?(CampaignBoss)
        BlueStory.singleton_class.prepend(StoryBoss) unless BlueStory.singleton_class.ancestors.include?(StoryBoss)
        @jupiter_active=true
      end
      pbMessage(_INTL(key=="JUPITER" ? "Jupiter: Nao interfira nos planos da Galactic!" : "Equipe Galactic: Voce nao vai passar!"))
      return false unless TrainerBattle.start_core([spec[0].to_sym,spec[1],spec[2]])==1
      return false unless state.equal?(s) && history(s)==h
      s[LEDGER]=h+[key]
      true
    ensure
      @busy=false
      @jupiter_active=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f12c3_quest",error)
    false
  end
end
