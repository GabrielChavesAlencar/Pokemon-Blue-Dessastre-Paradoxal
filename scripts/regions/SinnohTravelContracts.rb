# S22: Sinnoh -> Hoenn/Unova POST-LEAGUE journey preflight only.
# NOT autoloaded into Game.exe; does not inject an NPC, map, warp or unlock.
# BlueRegions maintains the existing free-travel circuit in OTHER regions.
module BlueSinnohTravelContracts
  POST_LEAGUE_DESTINATIONS = %w[HOENN UNOVA].freeze
  # An actual source-side event and map must be audited/compiled in a private
  # build before any native handler may be allowed. No such source exists.
  VERIFIED_NATIVE_DEPARTURES = {}.freeze

  def self.valid_arrival?(point)
    point.is_a?(Array) && point.length == 4 &&
      point.all? { |item| item.is_a?(Integer) } &&
      point[0] > 0 && point[1] >= 0 && point[2] >= 0 &&
      [2, 4, 6, 8].include?(point[3])
  end

  # Read only. A boolean npc_context is not proof of a compiled native NPC.
  # Even if a test stubs source/destination/context, the empty immutable
  # registry above keeps the physical departure blocked.
  def self.preview(state, destination, npc_context: false)
    return :unsupported_destination unless
      destination.is_a?(String) && POST_LEAGUE_DESTINATIONS.include?(destination)
    return :unavailable unless defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:recorded) &&
      BlueSinnohStoryContracts.respond_to?(:league_cleared?)
    return :invalid_state unless BlueSinnohStoryContracts.recorded(state).is_a?(Array)
    return :story_incomplete unless BlueSinnohStoryContracts.league_cleared?(state)
    return :travel_service_missing unless defined?(BlueRegionTravel) &&
      BlueRegionTravel.respond_to?(:destination) &&
      BlueRegionTravel.respond_to?(:source_valid?) &&
      BlueRegionTravel.respond_to?(:available?)
    point = BlueRegionTravel.destination(state, destination)
    return :destination_not_installed unless valid_arrival?(point)
    return :source_not_installed unless BlueRegionTravel.source_valid?(state)
    return :npc_context_required unless npc_context.equal?(true)
    return :npc_context_unavailable unless BlueRegionTravel.available?(state)
    # Only the real native handler should ever invoke a future travel API.
    # Never infer source validity from league progress or user-supplied flags.
    return :departure_handler_not_verified unless
      VERIFIED_NATIVE_DEPARTURES[state["current"]].is_a?(String) &&
      !VERIFIED_NATIVE_DEPARTURES[state["current"]].empty?
    :eligible_only_via_verified_npc
  rescue StandardError
    :invalid_state
  end

  def self.available?(state, destination, npc_context: false)
    preview(state, destination, npc_context: npc_context) ==
      :eligible_only_via_verified_npc
  end

  def self.destinations(state, npc_context: false)
    POST_LEAGUE_DESTINATIONS.to_h do |region|
      [region, preview(state, region, npc_context: npc_context)]
    end
  end

  # Explicitly never perform transfer, grant HM/Key Item or mutate a save.
  # BlueRegionTravel's native agent, inventory staging and rollback are
  # separate production APIs and cannot be bypassed by S22.
end
