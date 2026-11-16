# CH14: isolated, explicit Sinnoh story contract; never installed by default.
# Native map event handlers, once audited and installed, may call record AFTER
# a real confirmed event result. No global hooks, grants, map IDs or teleports.
module BlueSinnohStoryContracts
  STEPS = %w[
    P05_TEAM_GALACTIC_WINDWORKS P05_COMMANDER_MARS P05_COMMANDER_JUPITER
    P06_TEAM_GALACTIC_PASTORIA_ENCOUNTER P07_TEAM_GALACTIC_LAKE_EVENTS
    P08_CYRUS P08_COMMANDER_SATURN P08_COMMANDER_MARS
    P08_COMMANDER_JUPITER P08_DIALGA_PALKIA_STORY_SCENE
    P08_DISTORTION_WORLD_PUZZLES SINNOH_DISTORTION_CYRUS_FINAL
    P08_GIRATINA_ENCOUNTER P08_SAFE_RETURN_FROM_DISTORTION_WORLD
    P09_VOLKNER_BEACON_BADGE SINNOH_LEAGUE_BARRY_GATE
    P09_AARON_BATTLE P09_BERTHA_BATTLE P09_FLINT_BATTLE
    P09_LUCIAN_BATTLE P09_CYNTHIA_BATTLE P09_HALL_OF_FAME
  ].freeze
  SAVE_KEY = "sinnoh_ch14".freeze
  HALL_OF_FAME = "P09_HALL_OF_FAME".freeze
  BEACON_GATE = "P09_VOLKNER_BEACON_BADGE".freeze
  ELITE_GATE = "SINNOH_LEAGUE_BARRY_GATE".freeze
  BADGE_REQUIREMENTS = {
    "P05_COMMANDER_JUPITER" => %w[FOREST],
    "P08_CYRUS" => %w[MINE ICICLE],
    BEACON_GATE => %w[BEACON],
    ELITE_GATE => %w[COAL FOREST COBBLE RELIC FEN MINE ICICLE BEACON]
  }.freeze
  POST_LEAGUE_DESTINATIONS = %w[HOENN UNOVA].freeze

  # Read-only: invalid, newer, contradictory and cross-region saves fail closed.
  # A different initial region is valid for shared travel, but the current
  # region must be Sinnoh; do not overwrite native Decades league/badges.
  def self.recorded(state)
    return nil unless state.is_a?(Hash) && state["version"] == 1 &&
                      state["current"] == "SINNOH" &&
                      defined?(BlueRegions) &&
                      BlueRegions.respond_to?(:known?) &&
                      BlueRegions.known?("SINNOH") &&
                      BlueRegions.valid_sinnoh_badges?(state)
    return nil unless BlueRegions.known?(state["initial"]) &&
                      state["leagues"].is_a?(Array) &&
                      state["leagues"].uniq.length == state["leagues"].length &&
                      state["leagues"].all? { |key| key.is_a?(String) &&
                                                  BlueRegions.circuit.include?(key) }
    events = state.fetch(SAVE_KEY, [])
    return nil unless events.is_a?(Array) &&
                      events.length <= STEPS.length &&
                      events == STEPS.first(events.length)
    league_cleared = state["leagues"].include?("SINNOH")
    return nil if league_cleared != events.include?(HALL_OF_FAME)
    earned = BlueRegions.local_achievements(state, "SINNOH")
    events.each do |event|
      required = BADGE_REQUIREMENTS.fetch(event, [])
      return nil unless (required - earned).empty?
    end
    events.dup
  rescue StandardError
    nil
  end

  def self.next_event(state)
    events = recorded(state)
    events && STEPS[events.length]
  end

  # confirmed must come from a trusted, INSTALLED native handler. There are
  # no such handlers for CH14 yet. A synthetic confirmed=true is NOT evidence
  # of actual engine completion. Hall of Fame additionally needs its own
  # separately verified native completion callback.
  def self.record(state, event, confirmed: false, hall_of_fame_verified: false)
    return false unless confirmed.equal?(true) && event.is_a?(String)
    events = recorded(state)
    return false unless events && STEPS[events.length] == event
    required = BADGE_REQUIREMENTS.fetch(event, [])
    return false unless (required - BlueRegions.local_achievements(state, "SINNOH")).empty?
    is_hall = event == HALL_OF_FAME
    return false if is_hall && !hall_of_fame_verified.equal?(true)
    return false if state.frozen? || state["leagues"].frozen?
    next_events = events + [event]
    if is_hall
      # Use the single existing league ledger, not a parallel boolean.
      # Cynthia's battle is NOT sufficient proof for league completion.
      return false unless BlueRegions.complete_league(state, "SINNOH")
    end
    state[SAVE_KEY] = next_events
    true
  rescue StandardError
    false
  end

  def self.league_cleared?(state)
    events = recorded(state)
    !!events && events.include?(HALL_OF_FAME)
  end

  # Read-only destination preflight. The shared circuit lists both regions
  # even before installation, but it is NOT proof of a valid physical trip.
  # Sinnoh currently lacks a native departure agent/source; Unova lacks
  # an arrival implementation. Neither is enabled by this contract.
  def self.post_cynthia_destination(state, destination)
    return :unsupported_destination unless POST_LEAGUE_DESTINATIONS.include?(destination)
    return :story_incomplete unless league_cleared?(state)
    return :travel_service_missing unless defined?(BlueRegionTravel) &&
      BlueRegionTravel.respond_to?(:destination) &&
      BlueRegionTravel.respond_to?(:source_valid?) &&
      BlueRegionTravel.respond_to?(:available?)
    point = BlueRegionTravel.destination(state, destination)
    return :destination_not_installed unless point.is_a?(Array) &&
      point.length == 4 && point.first.is_a?(Integer) &&
      point.first > 0 && point[1..2].all? { |n| n.is_a?(Integer) && n >= 0 } &&
      [2, 4, 6, 8].include?(point[3])
    return :source_not_installed unless BlueRegionTravel.source_valid?(state)
    return :npc_context_unavailable unless BlueRegionTravel.available?(state)
    :eligible_only_via_verified_npc
  rescue StandardError
    :destination_not_installed
  end
end
