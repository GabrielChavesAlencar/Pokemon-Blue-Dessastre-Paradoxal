# S21 — Sinnoh League / Elite Four / Cynthia / Hall of Fame contract.
# An inert adapter over the existing CH14 state machine, never loaded by
# Game.exe by default. Native MapIDs, event handlers and battle results are
# NOT installed or discovered by this script.
module BlueSinnohLeagueContracts
  EVENTS = %w[
    P09_VOLKNER_BEACON_BADGE
    SINNOH_LEAGUE_BARRY_GATE
    P09_AARON_BATTLE
    P09_BERTHA_BATTLE
    P09_FLINT_BATTLE
    P09_LUCIAN_BATTLE
    P09_CYNTHIA_BATTLE
    P09_HALL_OF_FAME
  ].freeze
  START_AT = 14
  OUTCOMES = {
    "P09_VOLKNER_BEACON_BADGE" => :beacon_badge_confirmed,
    "SINNOH_LEAGUE_BARRY_GATE" => :battle_won,
    "P09_AARON_BATTLE" => :battle_won,
    "P09_BERTHA_BATTLE" => :battle_won,
    "P09_FLINT_BATTLE" => :battle_won,
    "P09_LUCIAN_BATTLE" => :battle_won,
    "P09_CYNTHIA_BATTLE" => :battle_won,
    "P09_HALL_OF_FAME" => :engine_hall_of_fame_confirmed
  }.freeze
  REQUIRED_BADGES = %w[
    COAL FOREST COBBLE RELIC FEN MINE ICICLE BEACON
  ].freeze
  # Fail-closed native bindings; source IDs may be populated only after
  # actual compilation, local asset rights, battle+HoF callback and QA.
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.checkpoint(state)
    return :unavailable unless defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:recorded) &&
      BlueSinnohStoryContracts.respond_to?(:next_event)
    events = BlueSinnohStoryContracts.recorded(state)
    return :invalid_state unless events.is_a?(Array)
    return :distortion_incomplete if events.length < START_AT
    return :outside_s21 if events.length >= START_AT + EVENTS.length
    key = EVENTS[events.length - START_AT]
    return :invalid_state unless BlueSinnohStoryContracts.next_event(state) == key
    return :missing_beacon_badge if key == EVENTS.first &&
      !local_badges_include?(state, ["BEACON"])
    return :missing_eight_badges if key == EVENTS[1] &&
      !local_badges_include?(state, REQUIRED_BADGES)
    :ready
  rescue StandardError
    :invalid_state
  end

  def self.local_badges_include?(state, required)
    return false unless defined?(BlueRegions) &&
      BlueRegions.respond_to?(:local_achievements)
    list = BlueRegions.local_achievements(state, "SINNOH")
    list.is_a?(Array) && (required - list).empty?
  end
  private_class_method :local_badges_include?

  def self.next_step(state)
    return nil unless checkpoint(state) == :ready
    BlueSinnohStoryContracts.next_event(state)
  end

  def self.completed(state)
    return nil unless defined?(BlueSinnohStoryContracts)
    steps = BlueSinnohStoryContracts.recorded(state)
    return nil unless steps.is_a?(Array)
    return [] if steps.length < START_AT
    steps[START_AT, EVENTS.length] || []
  rescue StandardError
    nil
  end

  # Cynthia's victory does not clear a league; CH14 requires a separate
  # installed engine Hall of Fame handler. No physical travel is unlocked.
  def self.league_cleared?(state)
    checkpoint(state) == :outside_s21 &&
      BlueSinnohStoryContracts.league_cleared?(state)
  rescue StandardError
    false
  end

  def self.record_from_native(state, event, outcome:, source:)
    record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES)
  end

  # Private synthetic test hook only, not an API for compiled native events.
  # Synthetic callbacks must never be described as runtime gameplay proofs.
  def self.record_with_sources(state, event, outcome, source, sources)
    return false unless event.is_a?(String) && EVENTS.include?(event) &&
      outcome.is_a?(Symbol) && OUTCOMES[event] == outcome &&
      source.is_a?(String) && !source.empty? &&
      sources.is_a?(Hash) && sources[event].is_a?(String) &&
      sources[event] == source
    return false unless checkpoint(state) == :ready && next_step(state) == event
    if event == "P09_HALL_OF_FAME"
      # Only a separately confirmed engine callback can complete the League.
      BlueSinnohStoryContracts.record(
        state, event, confirmed: true, hall_of_fame_verified: true)
    else
      BlueSinnohStoryContracts.record(state, event, confirmed: true)
    end
  rescue StandardError
    false
  end
  private_class_method :record_with_sources
end
