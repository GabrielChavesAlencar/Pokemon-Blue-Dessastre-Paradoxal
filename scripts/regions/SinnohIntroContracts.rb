# S13: inert read-only checkpoint preflight. NO event registrations.
module BlueSinnohIntroContracts
  CHECKPOINTS = %w[mother_intro barry_intro rowan_briefcase_seen
                   starter_received rival_fought pokedex_received].freeze
  STARTERS = %w[TURTWIG CHIMCHAR PIPLUP].freeze
  VERIFIED_NATIVE_HANDLERS = {}.freeze
  DEFAULT = :blocked_no_native_binding

  def self.preview(state)
    return :wrong_region unless state.is_a?(Hash) && state["current"]=="SINNOH" &&
      state["version"]==1
    return :foreign_initial if state.key?("initial") && state["initial"]!="SINNOH"
    return :runtime_missing unless defined?(BlueSinnohPilot) &&
      BlueSinnohPilot.respond_to?(:valid_flags?)
    flags=state.fetch("sinnoh_pilot",{})
    return :invalid_checkpoint unless flags.is_a?(Hash) &&
      BlueSinnohPilot.valid_flags?(flags)
    current=CHECKPOINTS.take_while { |key| flags[key]==true }
    return :invalid_checkpoint if CHECKPOINTS.drop(current.length).any? { |key| flags[key]==true }
    return :complete_offline_only if current.length==CHECKPOINTS.length
    upcoming=CHECKPOINTS[current.length]
    return :native_events_unverified unless VERIFIED_NATIVE_HANDLERS.key?(upcoming)
    :await_native_callback
  rescue StandardError
    :invalid_checkpoint
  end

  def self.expected_starter_opponent(player_species)
    return nil unless player_species.is_a?(String) && STARTERS.include?(player_species)
    {"TURTWIG"=>"CHIMCHAR","CHIMCHAR"=>"PIPLUP",
     "PIPLUP"=>"TURTWIG"}[player_species]
  end

  def self.native_ready?(state,checkpoint,callback)
    return false unless checkpoint.is_a?(String) && callback.is_a?(String)
    return false unless VERIFIED_NATIVE_HANDLERS.key?(checkpoint)
    return false unless VERIFIED_NATIVE_HANDLERS[checkpoint]==callback
    preview(state)==:await_native_callback
  rescue StandardError
    false
  end
end
