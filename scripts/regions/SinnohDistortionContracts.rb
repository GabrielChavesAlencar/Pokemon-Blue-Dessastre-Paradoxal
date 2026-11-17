# S20: Cyrus / Spear Pillar / Distortion World story gates, OFFLINE ONLY.
# Not automatically loaded by Game.exe; no MapIDs, NPCs, portals, battle
# callbacks or Giratina encounters are installed by this file.
# The only story/save ledger is BlueSinnohStoryContracts (sinnoh_ch14).
module BlueSinnohDistortionContracts
  EVENTS = %w[
    P08_CYRUS
    P08_COMMANDER_SATURN
    P08_COMMANDER_MARS
    P08_COMMANDER_JUPITER
    P08_DIALGA_PALKIA_STORY_SCENE
    P08_DISTORTION_WORLD_PUZZLES
    SINNOH_DISTORTION_CYRUS_FINAL
    P08_GIRATINA_ENCOUNTER
    P08_SAFE_RETURN_FROM_DISTORTION_WORLD
  ].freeze
  START_AT = 5
  OUTCOMES = {
    "P08_CYRUS" => :battle_won,
    "P08_COMMANDER_SATURN" => :battle_won,
    "P08_COMMANDER_MARS" => :battle_won,
    "P08_COMMANDER_JUPITER" => :battle_won,
    "P08_DIALGA_PALKIA_STORY_SCENE" => :scene_completed,
    "P08_DISTORTION_WORLD_PUZZLES" => :puzzles_solved,
    "SINNOH_DISTORTION_CYRUS_FINAL" => :battle_won,
    "P08_GIRATINA_ENCOUNTER" => :encounter_resolved,
    "P08_SAFE_RETURN_FROM_DISTORTION_WORLD" => :safe_return_confirmed
  }.freeze
  # Never infer a native handler from CH14 planning references or screenshots.
  # Empty until verified MapIDs, scripts, battle results and return map are
  # installed, bound and witnessed inside a private Windows/Android build.
  VERIFIED_NATIVE_SOURCES = {}.freeze
  REQUIRED_FIRST_BADGES = %w[MINE ICICLE].freeze

  def self.checkpoint(state)
    return :unavailable unless defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:recorded) &&
      BlueSinnohStoryContracts.respond_to?(:next_event)
    events = BlueSinnohStoryContracts.recorded(state)
    return :invalid_state unless events.is_a?(Array)
    return :galactic_incomplete if events.length < START_AT
    return :outside_s20 if events.length >= START_AT + EVENTS.length
    next_step = EVENTS[events.length - START_AT]
    return :invalid_state unless BlueSinnohStoryContracts.next_event(state) == next_step
    if next_step == EVENTS.first
      return :missing_mine_icicle_badges unless defined?(BlueRegions) &&
        BlueRegions.respond_to?(:local_achievements) &&
        (REQUIRED_FIRST_BADGES -
          BlueRegions.local_achievements(state, "SINNOH")).empty?
    end
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
    return [] if events.length < START_AT
    events[START_AT, EVENTS.length] || []
  rescue StandardError
    nil
  end

  def self.return_ready?(state)
    events = completed(state)
    events.is_a?(Array) && events.length == EVENTS.length &&
      checkpoint(state) == :outside_s20
  end

  def self.record_from_native(state, event, outcome:, source:)
    record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES)
  end

  # Internal helper: exercised with synthetic sources through Ruby `send`
  # solely inside tests. There is NO public fixture callback. A caller's
  # symbols are never interpreted as proof from a real Game.exe.
  def self.record_with_sources(state, event, outcome, source, sources)
    return false unless event.is_a?(String) && EVENTS.include?(event) &&
      outcome.is_a?(Symbol) && OUTCOMES[event] == outcome &&
      source.is_a?(String) && !source.empty? &&
      sources.is_a?(Hash) &&
      sources[event].is_a?(String) && sources[event] == source
    return false unless checkpoint(state) == :ready && next_step(state) == event
    # Validation of CH14 ordered prefix and local badge requirements is
    # delegated to the already versioned regional state machine.
    BlueSinnohStoryContracts.record(state, event, confirmed: true)
  rescue StandardError
    false
  end
  private_class_method :record_with_sources
end
