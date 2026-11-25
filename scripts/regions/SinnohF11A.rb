# F11A private QA only; no HM grants or Decades badge mutation.
module BlueSinnohF11A
  SPEC=__F11A_SPEC__.freeze
  def self.verify_compiled!
    raise "Sinnoh F11A: equipe Roark divergente" unless BlueSinnohF10B.valid_team?(SPEC)
    true
  end
  def self.battle
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    state=BlueSinnohPilot.regional_state
    return false unless state && $game_map && $game_map.map_id==SPEC[3]
    return false unless defined?(BlueRegions) && BlueRegions.valid_sinnoh_badges?(state)
    if BlueRegions.local_achievements(state,"SINNOH").include?("COAL")
      pbMessage(_INTL("Roark: Você já conquistou a Insígnia de Carvão!"))
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
      pbMessage(_INTL("Roark: Sou o líder de Oreburgh. Mostre a força dos seus Pokémon!"))
      return false unless TrainerBattle.start_core([SPEC[0].to_sym,SPEC[1],SPEC[2]])==1
      return false unless BlueSinnohPilot.regional_state.equal?(state) && BlueRegions.valid_sinnoh_badges?(state)
      return false unless BlueRegions.award(state,"SINNOH","COAL")
      pbMessage(_INTL("Roark: Você conquistou a Insígnia de Carvão!"))
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f11a_roark",error)
    false
  end
end
