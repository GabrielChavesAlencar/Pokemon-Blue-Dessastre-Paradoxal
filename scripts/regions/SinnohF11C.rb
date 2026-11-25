# F11C private QA only; no HM grants or Decades badge mutation.
module BlueSinnohF11C
  SPEC=__F11C_SPEC__.freeze
  def self.verify_compiled!
    raise "Sinnoh F11C: equipe Fantina divergente" unless BlueSinnohF10B.valid_team?(SPEC)
    true
  end
  def self.battle
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    state=BlueSinnohPilot.regional_state
    return false unless state && $game_map && $game_map.map_id==SPEC[3]
    return false unless defined?(BlueRegions) && BlueRegions.valid_sinnoh_badges?(state)
    unless (%w[COAL FOREST]-BlueRegions.local_achievements(state,"SINNOH")).empty?
      pbMessage(_INTL("Fantina: Conquiste primeiro as insígnias de Oreburgh e Eterna."))
      return false
    end
    if BlueRegions.local_achievements(state,"SINNOH").include?("RELIC")
      pbMessage(_INTL("Fantina: Você já conquistou a Insígnia da Relíquia!"))
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
      pbMessage(_INTL("Fantina: Sou a líder de Hearthome. Mostre sua coragem diante dos Pokémon Fantasma!"))
      return false unless TrainerBattle.start_core([SPEC[0].to_sym,SPEC[1],SPEC[2]])==1
      return false unless BlueSinnohPilot.regional_state.equal?(state) && BlueRegions.valid_sinnoh_badges?(state)
      return false unless (%w[COAL FOREST]-BlueRegions.local_achievements(state,"SINNOH")).empty?
      return false unless BlueRegions.award(state,"SINNOH","RELIC")
      pbMessage(_INTL("Fantina: Você conquistou a Insígnia da Relíquia!"))
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f11c_fantina",error)
    false
  end
end
