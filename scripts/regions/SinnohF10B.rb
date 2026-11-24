# Private QA only. Generated rows are validated literals, never donor code.
module BlueSinnohF10B
  SPECS = (__F10B_ROWS__).to_h.freeze

  def self.valid_team?(spec)
    trainer=GameData::Trainer.get(spec[0].to_sym,spec[1],spec[2])
    return false unless trainer && trainer.respond_to?(:pokemon)
    actual=trainer.pokemon.map do |mon|
      [mon[:species].to_s,mon[:level]]
    end
    actual==spec[4]
  rescue StandardError
    false
  end

  def self.verify_compiled!
    raise "Sinnoh F10B: equipe compilada divergente" unless SPECS.values.all? { |spec| valid_team?(spec) }
    true
  end

  def self.battle(key)
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    spec=SPECS[key]
    state=BlueSinnohPilot.regional_state
    return false unless spec && state && $game_map && $game_map.map_id==spec[3]
    return false unless defined?($player) && $player && $player.party.any? { |p| !p.egg? && p.hp>0 }
    victories=state["sinnoh_f10b_victories"]
    return false unless victories.nil? || (victories.is_a?(Array) &&
      victories.uniq==victories && victories.all? { |v| v.is_a?(String) && v.match?(/\AF10B_\d+_\d+\z/) })
    if victories && victories.include?(key)
      pbMessage(_INTL("{1}: Boa batalha! Continue treinando.",spec[1]))
      return true
    end
    return false if @busy
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    # The existing campaign hook supplies Normal 70%, Master 90% and
    # evolution rules. Never launch an unscaled fallback battle.
    return false unless defined?(BlueCampaign) && BlueCampaign.active? && valid_team?(spec)
    @busy=true
    begin
      pbMessage(_INTL("{1}: Vamos batalhar!",spec[1]))
      return false unless TrainerBattle.start(spec[0].to_sym,spec[1],spec[2])==true
      return false unless BlueSinnohPilot.regional_state.equal?(state)
      state["sinnoh_f10b_victories"]=(victories || [])+[key]
      pbMessage(_INTL("{1}: Você venceu! Até a próxima!",spec[1]))
      true
    ensure
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f10b_trainer",error)
    false
  end
end
