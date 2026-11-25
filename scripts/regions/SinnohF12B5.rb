# Private QA authored adaptation: no donor event or global story flag.
module BlueSinnohF12B5
  SPECS=__F12B5_SPECS__.freeze
  KEY=__F12B5_KEY__.to_sym
  ORDER=%w[WINDWORKS_GUARD MEADOW_GRUNT_1 MEADOW_GRUNT_2 WORKS_KEY MARS].freeze
  LEDGER="sinnoh_f12b5_quest".freeze
  def self.ledger(state)
    return nil unless state.is_a?(Hash) && state["version"]==1 &&
      state["current"]=="SINNOH" && BlueRegions.valid_sinnoh_badges?(state)
    history=state.fetch(LEDGER,[])
    return nil unless history.is_a?(Array) && history.length<=ORDER.length && history==ORDER.first(history.length)
    history.dup
  end
  def self.key_valid?
    item=GameData::Item.try_get(KEY)
    item && item.respond_to?(:is_key_item?) && item.is_key_item? &&
      defined?(BlueRegionTravel) && BlueRegionTravel.regional_item?(KEY)
  end
  def self.verify_compiled!
    raise "Sinnoh F12B5: chave regional invalida" unless key_valid?
    raise "Sinnoh F12B5: equipes divergentes" unless ORDER.reject { |s| s=="WORKS_KEY" }.all? { |s| BlueSinnohF10B.valid_team?(SPECS.fetch(s)) }
    true
  end
  def self.mars_opponent?(trainer)
    return false unless @mars_active && trainer && trainer.respond_to?(:trainer_type) &&
      trainer.respond_to?(:name) && trainer.respond_to?(:version)
    spec=SPECS.fetch("MARS")
    trainer.trainer_type.to_s==spec[0] && trainer.name==spec[1] && trainer.version==spec[2]
  end
  module CampaignBoss
    def boss?(trainer)
      BlueSinnohF12B5.mars_opponent?(trainer) || super
    end
  end
  module StoryBoss
    def regional_first_boss?(trainers)
      Array(trainers).any? { |t| BlueSinnohF12B5.mars_opponent?(t) } || super
    end
  end
  def self.interact(key)
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    return false unless ORDER.include?(key) && defined?(BlueSinnohPilot) && defined?(BlueRegions)
    state=BlueSinnohPilot.regional_state
    history=ledger(state)
    spec=SPECS[key]
    return false unless history && spec && !state.frozen? && $game_map && $game_map.map_id==spec[3]
    return true if history.include?(key)
    if ORDER[history.length]!=key
      pbMessage(_INTL("Ainda falta concluir a etapa anterior da missao Galactic."))
      return false
    end
    return false if @busy || !defined?(BlueKantoTitle) || !BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return false unless key_valid? && $bag && $bag.respond_to?(:has?)
    @busy=true
    begin
      if key=="WORKS_KEY"
        # An unrelated pre-existing key is not a verified Sinnoh pickup.
        return false if $bag.has?(KEY) || !$bag.respond_to?(:add)
        return false unless $bag.add(KEY) && $bag.has?(KEY)
        state[LEDGER]=history+[key]
        pbMessage(_INTL("Obrigado por ajudar! Voce recebeu a chave de Valley Windworks."))
        return true
      end
      return false if key=="MARS" && !$bag.has?(KEY)
      return false unless $player && $player.party.any? { |p| !p.egg? && p.hp>0 }
      return false unless defined?(BlueCampaign) && BlueCampaign.active? && defined?(BlueCampaign::Teams) &&
        defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
      return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && BlueSinnohF10B.valid_team?(spec)
      return false unless $game_temp && $game_temp.respond_to?(:waiting_trainer) &&
        !$game_temp.waiting_trainer && $game_temp.respond_to?(:battle_rules) &&
        $game_temp.battle_rules.is_a?(Hash) && $game_temp.battle_rules.empty?
      return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
      if key=="MARS"
        return false unless defined?(BlueStory) && BlueStory.respond_to?(:regional_first_boss?)
        BlueCampaign.singleton_class.prepend(CampaignBoss) unless BlueCampaign.singleton_class.ancestors.include?(CampaignBoss)
        BlueStory.singleton_class.prepend(StoryBoss) unless BlueStory.singleton_class.ancestors.include?(StoryBoss)
        @mars_active=true
      end
      pbMessage(_INTL(key=="MARS" ? "Mars: Voce nao vai atrapalhar os planos da Galactic!" : "Equipe Galactic: Nao vamos deixar voce passar!"))
      return false unless TrainerBattle.start_core([spec[0].to_sym,spec[1],spec[2]])==1
      return false unless BlueSinnohPilot.regional_state.equal?(state) && ledger(state)==history
      state[LEDGER]=history+[key]
      pbMessage(_INTL(key=="MARS" ? "Mars: A Galactic vai se retirar por enquanto." : "Voce venceu o confronto da Galactic."))
      true
    ensure
      @mars_active=false
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f12b5_authored_quest",error)
    false
  end
end
