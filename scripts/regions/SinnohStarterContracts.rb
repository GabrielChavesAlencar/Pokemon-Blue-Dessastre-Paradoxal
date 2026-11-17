# S14: read-only state of the three authored physical balls.
# No native event registered, no global hook, no grant, save or bag mutation.
module BlueSinnohStarterContracts
  BALLS = {
    "TURTWIG" => ["SN_BALL_TURTWIG", "SINNOH_LAKE_VERITY", "CHIMCHAR", 0],
    "CHIMCHAR" => ["SN_BALL_CHIMCHAR", "SINNOH_LAKE_VERITY", "PIPLUP", 1],
    "PIPLUP" => ["SN_BALL_PIPLUP", "SINNOH_LAKE_VERITY", "TURTWIG", 2]
  }.freeze
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.preview(state, species)
    return :unknown_species unless species.is_a?(String) && BALLS.key?(species)
    return :wrong_region unless state.is_a?(Hash) &&
      state["version"] == 1 && state["current"] == "SINNOH"
    return :foreign_initial if state.key?("initial") && state["initial"] != "SINNOH"
    return :runtime_missing unless defined?(BlueSinnohPilot) &&
      BlueSinnohPilot.respond_to?(:valid_flags?)
    flags = state.fetch("sinnoh_pilot", {})
    return :invalid_flags unless flags.is_a?(Hash) &&
      BlueSinnohPilot.valid_flags?(flags)
    return :rowan_not_ready unless flags["rowan_briefcase_seen"] == true
    if flags["starter_received"] == true
      return flags["starter"] == species ? :already_selected : :other_selected
    end
    event_key = BALLS[species][0]
    return :native_event_missing unless VERIFIED_NATIVE_SOURCES.key?(event_key)
    :await_verified_native_ball
  rescue StandardError
    :invalid_flags
  end

  # Read-only; never call BlueSinnohPilot.choose_starter_from_ball here.
  # Actual dispatch requires an audited RMXP event in a private QA copy.
  def self.native_event_ready?(state, species, source_id)
    return false unless source_id.is_a?(String) && !source_id.empty?
    return false unless species.is_a?(String) && BALLS.key?(species)
    event_key = BALLS[species][0]
    return false unless VERIFIED_NATIVE_SOURCES.key?(event_key) &&
      VERIFIED_NATIVE_SOURCES[event_key] == source_id
    preview(state, species) == :await_verified_native_ball
  rescue StandardError
    false
  end
end
