# S16 — isolated local-HM receipt adapter. NOT loaded by Game.exe.
# No global event handler, registration, direct item gift, or save mutation.
module BlueSinnohHMContracts
  HM_BADGES = {
    'ROCK_SMASH'=>['COAL', :HM06],
    'CUT'=>['FOREST', :HM01],
    'FLY'=>['COBBLE', :HM02],
    'DEFOG'=>['RELIC', :HM05],
    'SURF'=>['FEN', :HM03],
    'STRENGTH'=>['MINE', :HM04],
    'ROCK_CLIMB'=>['ICICLE', :HM08],
    'WATERFALL'=>['BEACON', :HM07]
  }.freeze
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.preview(state, action, bag)
    return :invalid_move unless action.is_a?(String) && HM_BADGES.key?(action)
    return :wrong_region unless state.is_a?(Hash) && state['current']=='SINNOH'
    return :invalid_state unless defined?(BlueRegions) &&
      BlueRegions.respond_to?(:valid_sinnoh_badges?) &&
      BlueRegions.valid_sinnoh_badges?(state) &&
      BlueRegions.respond_to?(:sinnoh_local_hms) &&
      BlueRegions.sinnoh_local_hms(state)
    result=BlueRegions.field_access(state,'SINNOH',action,true)
    return result unless result==:allowed
    expected=HM_BADGES[action][1]
    return :hm unless bag && bag.respond_to?(:has?) && bag.has?(expected)
    :allowed
  rescue StandardError
    :invalid_state
  end

  # Direct callers cannot manufacture an acquisition event by passing true.
  # Native ownership proofs must be added after real compilation + QA,
  # independent from any externally supplied event ID.
  def self.record_from_native(state, action, bag, outcome, source_id: nil)
    return false unless outcome==:engine_pickup_committed &&
      source_id.is_a?(String) && !source_id.empty?
    return false unless state.is_a?(Hash) && state['current']=='SINNOH' &&
      action.is_a?(String) && HM_BADGES.key?(action)
    return false unless VERIFIED_NATIVE_SOURCES.key?(action) &&
      VERIFIED_NATIVE_SOURCES[action]==source_id
    return false unless defined?(BlueRegions) &&
      BlueRegions.respond_to?(:record_sinnoh_hm)
    BlueRegions.record_sinnoh_hm(state,action,HM_BADGES[action][1],bag,true)
  rescue StandardError
    false
  end
end
