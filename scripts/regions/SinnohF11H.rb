# F11H private QA only; no HM grants or Decades badge mutation.
module BlueSinnohF11H
  SPEC=__F11H_SPEC__.freeze
  def self.verify_compiled!
    raise "Sinnoh F11H: equipe Volkner divergente" unless BlueSinnohF10B.valid_team?(SPEC)
    true
  end
  def self.battle
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    state=BlueSinnohPilot.regional_state
    return false unless state && $game_map && $game_map.map_id==SPEC[3]
    return false unless defined?(BlueRegions) && BlueRegions.valid_sinnoh_badges?(state)
    unless (%w[COAL FOREST RELIC COBBLE FEN MINE ICICLE]-BlueRegions.local_achievements(state,"SINNOH")).empty?
      pbMessage(_INTL("Volkner: Conquiste primeiro as sete insígnias anteriores."))
      return false
    end
    if BlueRegions.local_achievements(state,"SINNOH").include?("BEACON")
      pbMessage(_INTL("Volkner: Você já conquistou a Insígnia do Farol!"))
      return true
    end
    return false if @busy || !$player || !$player.party.any? { |p| !p.egg? && p.hp>0 }
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return false unless defined?(BlueCampaign) && BlueCampaign.active? && defined?(BlueCampaign::Teams) &&
      defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
    return false unless defined?(BlueStory) && BlueStory.regional_first_boss?([Struct.new(:trainer_type).new(SPEC[0])])
    return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && BlueSinnohF10B.valid_team?(SPEC)
    return false unless defined?($game_temp) && $game_temp && $game_temp.respond_to?(:waiting_trainer) &&
      !$game_temp.waiting_trainer && $game_temp.respond_to?(:battle_rules) && $game_temp.battle_rules.is_a?(Hash) &&
      $game_temp.battle_rules.empty?
    return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
    @busy=true
    begin
      pbMessage(_INTL("Volkner: Sou o líder de Sunyshore! Mostre a força do seu time no último ginásio de Sinnoh!"))
      return false unless TrainerBattle.start_core([SPEC[0].to_sym,SPEC[1],SPEC[2]])==1
      return false unless BlueSinnohPilot.regional_state.equal?(state) && BlueRegions.valid_sinnoh_badges?(state)
      return false unless (%w[COAL FOREST RELIC COBBLE FEN MINE ICICLE]-BlueRegions.local_achievements(state,"SINNOH")).empty?
      return false unless BlueRegions.award(state,"SINNOH","BEACON")
      pbMessage(_INTL("Volkner: Você conquistou a Insígnia do Farol!"))
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f11h_volkner",error)
    false
  end
end
