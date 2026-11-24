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

  PAIR_KEYS = %w[F10B_42_29 F10B_42_30].freeze

  def self.verify_compiled!
    raise "Sinnoh F10B: equipe compilada divergente" unless SPECS.values.all? { |spec| valid_team?(spec) }
    count=PAIR_KEYS.count { |key| SPECS.key?(key) }
    raise "Sinnoh F10B4: dupla incompleta" unless count==0 || count==2
    true
  end

  # Essentials 21.1 assigns party2starts AFTER Battle.new. BlueCampaign
  # expands both opponents in Master, so original offsets can be stale.
  # Correct only during this private, explicit double battle.
  module PairOffsets
    def party2starts=(starts)
      if BlueSinnohF10B.pair_active?
        raise "Sinnoh F10B4: dois oponentes esperados" unless @opponent.is_a?(Array) && @opponent.length==2
        sizes=@opponent.map { |t| t.party.length }
        raise "Sinnoh F10B4: equipe dupla inconsistente" unless sizes.all? { |n| n>0 } && @party2.length==sizes.sum && sizes.sum<=6
        starts=[0,sizes[0]]
      end
      super(starts)
    end
  end

  def self.pair_active?
    @pair_active==true
  end

  def self.double_battle(key)
    return false unless PAIR_KEYS.include?(key) && PAIR_KEYS.all? { |k| SPECS.key?(k) }
    return false unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.private_copy?
    state=BlueSinnohPilot.regional_state
    pair=PAIR_KEYS.map { |k| SPECS[k] }
    return false unless state && $game_map && pair.all? { |s| s[3]==$game_map.map_id }
    victories=state["sinnoh_f10b_victories"]
    return false unless victories.nil? || (victories.is_a?(Array) && victories.uniq==victories &&
      victories.all? { |v| v.is_a?(String) && v.match?(/\AF10B_\d+_\d+\z/) })
    previous=PAIR_KEYS.count { |k| Array(victories).include?(k) }
    if previous==2
      pbMessage(_INTL("Anthony e Lauren: Foi uma ótima batalha em dupla!"))
      return true
    end
    return false unless previous==0
    return false if @busy
    unless defined?($player) && $player && $player.party.count { |p| !p.egg? && p.hp>0 }>=2
      pbMessage(_INTL("Você precisa de dois Pokémon aptos para a batalha em dupla."))
      return false
    end
    return false unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?
    return false unless defined?(BlueCampaign) && BlueCampaign.active? &&
      defined?(BlueCampaign::Teams) && defined?(Battle) && Battle.ancestors.include?(BlueCampaign::Teams)
    return false unless defined?(TrainerBattle) && TrainerBattle.respond_to?(:start_core) && pair.all? { |s| valid_team?(s) }
    return false unless defined?($game_temp) && $game_temp && $game_temp.respond_to?(:waiting_trainer) &&
      !$game_temp.waiting_trainer && $game_temp.respond_to?(:battle_rules) &&
      $game_temp.battle_rules.is_a?(Hash) && $game_temp.battle_rules["size"].nil?
    return false if defined?($DEBUG) && $DEBUG && defined?(Input::CTRL) && Input.press?(Input::CTRL)
    Battle.prepend(PairOffsets) unless Battle.ancestors.include?(PairOffsets)
    @busy=true
    @pair_active=true
    begin
      pbMessage(_INTL("Anthony e Lauren: Vamos batalhar em dupla!"))
      args=pair.map { |s| [s[0].to_sym,s[1],s[2]] }
      # Explicit two trainer arrays in native Essentials 21.1. start_core
      # returns outcome 1 on victory; never use a single-trainer fallback.
      return false unless TrainerBattle.start_core(*args)==1
      return false unless BlueSinnohPilot.regional_state.equal?(state)
      state["sinnoh_f10b_victories"]=(victories || [])+PAIR_KEYS
      pbMessage(_INTL("Anthony e Lauren: Vocês venceram!"))
      true
    ensure
      @pair_active=false
      @busy=false
    end
  rescue StandardError => error
    BlueSinnohPilot.profile_error("f10b4_double",error)
    false
  end

  def self.battle(key)
    return double_battle(key) if PAIR_KEYS.include?(key)
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
