# S23 — Sinnoh postgame: offline milestone and strongest-rematch gates.
# This module is NOT autoloaded by Game.exe and MUST NOT grant Pokemon,
# items, new maps, portals, rematch trainer PBS or native quest completion.
module BlueSinnohPostgameContracts
  EVENTS = %w[
    P10_BATTLE_ZONE_ENTRY
    P10_HEATRAN_QUEST
    P10_CRESSELIA_EVENT
    P10_DARKRAI_CONDITIONAL_QUEST
    P10_SHAYMIN_CONDITIONAL_QUEST
    P10_OFFICIAL_STRONGEST_TEAM_REMATCHES
  ].freeze
  SAVE_KEY = "sinnoh_s23".freeze
  EVENT_OUTCOMES = {
    "P10_BATTLE_ZONE_ENTRY" => :arrival_confirmed,
    "P10_HEATRAN_QUEST" => :quest_completed,
    "P10_CRESSELIA_EVENT" => :event_resolved,
    "P10_DARKRAI_CONDITIONAL_QUEST" => :conditional_event_resolved,
    "P10_SHAYMIN_CONDITIONAL_QUEST" => :conditional_event_resolved,
    "P10_OFFICIAL_STRONGEST_TEAM_REMATCHES" => :rematch_won
  }.freeze
  HISTORICAL_ELITE_IDS = %w[
    SINNOH_AARON SINNOH_BERTHA SINNOH_FLINT SINNOH_LUCIAN SINNOH_CYNTHIA
  ].freeze
  # Readiness for a quest is not proof of a real map, handler, species,
  # capture, item or verified Full Power team.
  VERIFIED_NATIVE_SOURCES = {}.freeze

  def self.recorded(state)
    return nil unless defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:recorded) &&
      BlueSinnohStoryContracts.recorded(state).is_a?(Array)
    stored = state.fetch(SAVE_KEY, [])
    return nil unless stored.is_a?(Array) && stored.uniq.length == stored.length &&
      stored.all? { |key| key.is_a?(String) && EVENTS.include?(key) }
    # The postgame ledger is not permitted to coexist with an uncompleted
    # CH14 Hall of Fame or with corrupted save/league records.
    return nil unless stored.empty? || BlueSinnohStoryContracts.league_cleared?(state)
    stored.dup
  rescue StandardError
    nil
  end

  def self.historical_elite_references(state)
    return [] unless valid_postleague?(state)
    HISTORICAL_ELITE_IDS.dup
  end

  def self.valid_postleague?(state)
    defined?(BlueSinnohStoryContracts) &&
      BlueSinnohStoryContracts.respond_to?(:league_cleared?) &&
      BlueSinnohStoryContracts.league_cleared?(state) &&
      recorded(state).is_a?(Array)
  rescue StandardError
    false
  end

  def self.strongest_rematch_eligible?(state, verified_roster: false)
    return false unless valid_postleague?(state) && defined?(BlueRegions) &&
      BlueRegions.respond_to?(:world_champion?) &&
      BlueRegions.respond_to?(:profile) &&
      BlueRegions.world_champion?(state) &&
      verified_roster.equal?(true) &&
      BlueRegions.profile(state, verified_roster) == :world_champion_rematch
    true
  rescue StandardError
    false
  end

  # Pure gating only: local Platinum historical references are not native
  # battles; global "strongest" is a DIFFERENT tier after all 10 leagues.
  def self.gate(state, event, event_item_verified: false,
                verified_rematch_roster: false)
    return :unknown_event unless event.is_a?(String) && EVENTS.include?(event)
    history = recorded(state)
    return :invalid_state unless history.is_a?(Array)
    return :hall_of_fame_required unless valid_postleague?(state)
    return :already_recorded if history.include?(event)
    if event == "P10_HEATRAN_QUEST" && !history.include?("P10_BATTLE_ZONE_ENTRY")
      return :battle_zone_entry_required
    end
    if %w[P10_DARKRAI_CONDITIONAL_QUEST P10_SHAYMIN_CONDITIONAL_QUEST].include?(event)
      return :special_event_item_not_verified unless event_item_verified.equal?(true)
    end
    if event == "P10_OFFICIAL_STRONGEST_TEAM_REMATCHES"
      return :all_ten_leagues_required unless BlueRegions.world_champion?(state)
      return :native_strongest_roster_not_verified unless
        strongest_rematch_eligible?(state, verified_roster: verified_rematch_roster)
    end
    # This result means only that a fake/native test may TRY to supply proof.
    # A native source is still required by record_from_native.
    :ready_for_verified_native_event
  rescue StandardError
    :invalid_state
  end

  def self.record_from_native(state, event, outcome:, source:,
                              event_item_verified: false, verified_rematch_roster: false)
    record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES,
                        event_item_verified, verified_rematch_roster)
  end

  # CI ONLY. Caller-supplied sources here are deliberately NOT the production
  # registry. This private method cannot be used as a trusted game event.
  def self.record_with_sources(state, event, outcome, source, sources,
                               event_item_verified, verified_rematch_roster)
    return false unless event.is_a?(String) && EVENT_OUTCOMES[event] == outcome &&
      outcome.is_a?(Symbol) && source.is_a?(String) && !source.empty? &&
      sources.is_a?(Hash) && sources[event].is_a?(String) &&
      sources[event] == source
    return false unless gate(state, event,
      event_item_verified: event_item_verified,
      verified_rematch_roster: verified_rematch_roster) == :ready_for_verified_native_event
    return false unless state.is_a?(Hash) && !state.frozen?
    stored = recorded(state)
    return false unless stored && !stored.include?(event)
    state[SAVE_KEY] = stored + [event]
    true
  rescue StandardError
    false
  end
  private_class_method :record_with_sources
end
