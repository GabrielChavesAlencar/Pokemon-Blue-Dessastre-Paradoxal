# Private authored chase, only after verified geometry and compiled PBS.
module BlueSinnohF12D
  LOCATIONS=__F12D_LOCATIONS__.freeze
  SPEC=__F12D_SPEC__.freeze
  ORDER=%w[PASTORIA ROUTE_213 VALOR_BATTLE].freeze
  LEDGER="sinnoh_f12d_quest".freeze
  def self.history(s)
    h=s.fetch(LEDGER,[])
    return nil unless h.is_a?(Array) && h.length<=ORDER.length && h==ORDER.first(h.length)
    h.dup
  end
  def self.ready?(s)
    s && !s.frozen? && BlueSinnohF12C3.mars_complete?(s) &&
      BlueSinnohF12C3.history(s)==BlueSinnohF12C3::ORDER &&
      BlueRegions.local_achievements(s,"SINNOH").include?("FEN") &&
      defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
  end
  def self.verify_compiled!
    raise "Sinnoh F12D: equipe compilada divergente" unless BlueSinnohF10B.valid_team?(SPEC)
    true
  end
  def self.interact(key)
    return false unless defined?(BlueSinnohF12C3)
    s=BlueSinnohF12C3.state
    loc=LOCATIONS[key]
    return false unless ready?(s) && loc && $game_map && $game_map.map_id==loc[0] && $game_player
    return false unless ($game_player.x-loc[1]).abs+($game_player.y-loc[2]).abs==1
    h=history(s)
    return false unless h && !@busy
    return true if h.include?(key)
    return false unless ORDER[h.length]==key
    @busy=true
    begin
      if key=="VALOR_BATTLE"
        return false unless $player && $player.party.any? { |p| !p.egg? && p.hp>0 }
        return false unless defined?(BlueCampaign) && BlueCampaign.active? && defined?(BlueCampaign::Teams) &&
          defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
        return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && BlueSinnohF10B.valid_team?(SPEC)
        return false unless $game_temp && $game_temp.respond_to?(:waiting_trainer) && !$game_temp.waiting_trainer &&
          $game_temp.respond_to?(:battle_rules) && $game_temp.battle_rules.is_a?(Hash) && $game_temp.battle_rules.empty?
        return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
        pbMessage(_INTL("Equipe Galactic: Chega de me seguir!"))
        return false unless TrainerBattle.start_core([SPEC[0].to_sym,SPEC[1],SPEC[2]])==1
      else
        pbMessage(_INTL(key=="PASTORIA" ? "Equipe Galactic: Nao tenho tempo para voce! Vou para a Rota 213!" : "Equipe Galactic: Ainda me seguindo? Vou para Valor Lakefront!"))
      end
      return false unless BlueSinnohF12C3.state.equal?(s) && ready?(s) && history(s)==h
      s[LEDGER]=h+[key]
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f12d_chase",error)
    false
  end
end
