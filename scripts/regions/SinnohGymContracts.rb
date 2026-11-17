# S15 — Sinnoh gyms: inert validation adapter, NOT installed in Game.exe.
# No event hooks, native map IDs, PBS or save writes on load.
module BlueSinnohGymContracts
  GYMS = %w[SINNOH_ROARK SINNOH_GARDENIA SINNOH_FANTINA SINNOH_MAYLENE SINNOH_CRASHER_WAKE SINNOH_BYRON SINNOH_CANDICE SINNOH_VOLKNER].freeze
  BADGES = %w[COAL FOREST RELIC COBBLE FEN MINE ICICLE BEACON].freeze
  # Must be populated only after independent native source / callback QA.
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.local_badges(state)
    return nil unless defined?(BlueRegions) &&
      BlueRegions.respond_to?(:valid_sinnoh_badges?) &&
      BlueRegions.respond_to?(:local_achievements)
    return nil unless BlueRegions.valid_sinnoh_badges?(state)
    return nil unless state.is_a?(Hash) && state['current']=='SINNOH'
    list=BlueRegions.local_achievements(state,'SINNOH')
    return nil unless list.is_a?(Array) && (list-BADGES).empty?
    list
  rescue StandardError
    nil
  end

  # Preview statuses distinguish regional access and previous Gym sequence.
  # CH11 milestone storage order (COBBLE before RELIC) remains unchanged.
  def self.checkpoint(state, gym_id)
    return :unknown_gym unless gym_id.is_a?(String) && GYMS.include?(gym_id)
    return :wrong_region unless state.is_a?(Hash) && state['current']=='SINNOH'
    badges=local_badges(state)
    return :invalid_badges unless badges
    index=GYMS.index(gym_id)
    badge=BADGES[index]
    return :already_awarded if badges.include?(badge)
    return :missing_prior_badges unless (BADGES.take(index)-badges).empty?
    return :native_source_missing unless VERIFIED_NATIVE_SOURCES.key?(gym_id)
    :await_verified_native_battle
  rescue StandardError
    :invalid_state
  end

  # Won, lost, escaped, event spoofing: NEVER grant a badge without an
  # audited native callback. No source is registered in the repository.
  def self.record_from_native(state, gym_id, result, source_id: nil)
    return false unless result == :engine_battle_won
    return false unless source_id.is_a?(String) && !source_id.empty?
    return false unless VERIFIED_NATIVE_SOURCES.key?(gym_id)
    return false unless VERIFIED_NATIVE_SOURCES[gym_id] == source_id
    return false unless checkpoint(state,gym_id)==:await_verified_native_battle
    return false unless defined?(BlueRegions) && BlueRegions.respond_to?(:award)
    BlueRegions.award(state,'SINNOH',BADGES[GYMS.index(gym_id)])
  rescue StandardError
    false
  end

  def self.badge_for(gym_id)
    index=GYMS.index(gym_id) if gym_id.is_a?(String)
    index ? BADGES[index] : nil
  end
end
