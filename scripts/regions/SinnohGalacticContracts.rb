# S19 — Galactic Phase 5–7 contracts ONLY; not loaded by the production
# engine or bound to native events. This adapter NEVER grants badges, items,
# warps or flags in another region. The only persistent ledger is CH14.
module BlueSinnohGalacticContracts
  EVENTS = [
    "P05_TEAM_GALACTIC_WINDWORKS",
    "P05_COMMANDER_MARS",
    "P05_COMMANDER_JUPITER",
    "P06_TEAM_GALACTIC_PASTORIA_ENCOUNTER",
    "P07_TEAM_GALACTIC_LAKE_EVENTS"
  ].freeze
  OUTCOMES = {
    "P05_TEAM_GALACTIC_WINDWORKS" => :scene_completed,
    "P05_COMMANDER_MARS" => :battle_won,
    "P05_COMMANDER_JUPITER" => :battle_won,
    "P06_TEAM_GALACTIC_PASTORIA_ENCOUNTER" => :scene_completed,
    "P07_TEAM_GALACTIC_LAKE_EVENTS" => :scene_completed
  }.freeze
  PHASES = [5, 5, 5, 6, 7].freeze
  # Real source and MapID verification is REQUIRED before adding entries.
  # An empty immutable registry means this module cannot independently mark
  # any event completed in a user's Game.exe.
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.checkpoint(state)
    return :unavailable unless defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:recorded) &&
      BlueSinnohStoryContracts.respond_to?(:next_event)
    events = BlueSinnohStoryContracts.recorded(state)
    return :invalid_state unless events.is_a?(Array)
    return :outside_s19 if events.length >= EVENTS.length
    expected = EVENTS[events.length]
    return :outside_s19 unless BlueSinnohStoryContracts.next_event(state) == expected
    required = expected == "P05_COMMANDER_JUPITER" ? ["FOREST"] : []
    return :missing_forest_badge unless
      (required - BlueRegions.local_achievements(state, "SINNOH")).empty?
    :ready
  rescue StandardError
    :invalid_state
  end

  def self.next_step(state)
    return nil unless checkpoint(state) == :ready
    BlueSinnohStoryContracts.next_event(state)
  end

  def self.completed(state)
    return nil unless defined?(BlueSinnohStoryContracts)
    events = BlueSinnohStoryContracts.recorded(state)
    return nil unless events.is_a?(Array)
    events.first(EVENTS.length)
  rescue StandardError
    nil
  end

  # Must be called *after* a verified native handler completes. A boolean or
  # a scene name from UI alone is NOT proof. Production uses the empty registry
  # until real native MapIDs and callbacks have been audited and installed.
  def self.record_from_native(state, event, outcome:, source:)
    record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES)
  end

  # For CI synthetic fixtures ONLY. Never wire this method into native maps:
  # its supplied sources are fake evidence, incapable of proving gameplay.
  def self.fixture_record(state, event, outcome:, source:, synthetic_sources:)
    record_with_sources(state, event, outcome, source, synthetic_sources)
  end

  def self.record_with_sources(state, event, outcome, source, sources)
    return false unless event.is_a?(String) && EVENTS.include?(event) &&
      OUTCOMES[event] == outcome && source.is_a?(String) &&
      !source.empty? && sources.is_a?(Hash) &&
      sources[event].is_a?(String) && sources[event] == source
    return false unless checkpoint(state) == :ready && next_step(state) == event
    # CH14 provides strict ordered-prefix, local badge and save guards.
    BlueSinnohStoryContracts.record(state, event, confirmed: true)
  rescue StandardError
    false
  end
  private_class_method :record_with_sources
end
