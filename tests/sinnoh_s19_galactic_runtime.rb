# S19 regression: actual BlueRegions + CH14 ledger + proposed Galactic
# adapter. All native sources below are SYNTHETIC and never installed.
require "json"
class PokemonGlobalMetadata; end
load File.expand_path(ARGV.fetch(0))  # tests/regions_data_fixture.rb
load File.expand_path(ARGV.fetch(1))  # scripts/battle_polish/Regions.rb
load File.expand_path(ARGV.fetch(2))  # scripts/regions/SinnohStoryContracts.rb
load File.expand_path(ARGV.fetch(3))  # scripts/regions/SinnohGalacticContracts.rb
manifest = JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
story = BlueSinnohStoryContracts
galactic = BlueSinnohGalacticContracts

def check19(value, reason)
  raise "SINNOH_S19: #{reason}" unless value
end

steps = manifest.fetch("steps")
events = steps.map { |s| s.fetch("id") }
sources = steps.to_h { |s| [s.fetch("id"), "FIXTURE_" + s.fetch("source_key")] }
check19(events == galactic::EVENTS, "S19 event order differs from Ruby")
check19(events == story::STEPS.first(5), "S19 broke CH14 ordered prefix")
check19(galactic::VERIFIED_NATIVE_SOURCES.empty?, "fictional sources enabled in production")
check19(steps.map { |s| s.fetch("phase") } == [5, 5, 5, 6, 7],
        "Galactic phases 5-7 changed")

state = BlueRegions.new_state("SINNOH")
snapshot = Marshal.dump(state)
check19(galactic.checkpoint(state) == :ready, "new save not eligible for first scene")
check19(galactic.next_step(state) == events.first, "next scene mismatch")
check19(galactic.completed(state) == [], "new save already has Galactic progress")
check19(Marshal.dump(state) == snapshot, "read-only query mutated save")

def rejects(state, event, outcome, source, synthetic_sources)
  old = Marshal.dump(state)
  check19(!BlueSinnohGalacticContracts.fixture_record(
    state, event, outcome: outcome, source: source,
    synthetic_sources: synthetic_sources
  ), "untrusted Galactic callback accepted: #{event}/#{outcome}")
  check19(Marshal.dump(state) == old, "rejected Galactic callback changed save")
end

# No native Game.exe MapID, callback or installed PBS exists. The public API
# must reject even the correct synthetic event with a "trusted" result.
events.each_with_index do |event, index|
  source = sources.fetch(event)
  kind = steps[index].fetch("outcome").to_sym
  old = Marshal.dump(state)
  check19(!galactic.record_from_native(state, event, outcome: kind, source: source),
          "native callback accepted without registered native source")
  check19(Marshal.dump(state) == old, "missing native hook changed state")
  rejects(state, event, kind, source + "_FAKE", sources)
  rejects(state, event, :unknown_outcome, source, sources)
  rejects(state, event, kind, source, {})    # unverified registry
  rejects(state, event, "battle_won", source, sources)  # must be exact symbol
  rejects(state, event, kind, 123, sources)
  rejects(state, :NOT_A_NATIVE_EVENT, kind, source, sources)
  unless index.zero?
    rejects(state, events[index - 1], steps[index - 1]["outcome"].to_sym,
            sources.fetch(events[index - 1]), sources)
  end
  if index < 4
    rejects(state, events[index + 1], steps[index + 1]["outcome"].to_sym,
            sources.fetch(events[index + 1]), sources)
  end

  if event == "P05_COMMANDER_JUPITER"
    check19(galactic.checkpoint(state) == :missing_forest_badge,
            "Jupiter gate did not require local Forest badge")
    check19(galactic.next_step(state).nil?, "unearned badge allowed next event")
    rejects(state, event, kind, source, sources)
    check19(BlueRegions.award(state, "SINNOH", "FOREST"),
            "synthetic Forest badge could not be awarded")
    check19(galactic.checkpoint(state) == :ready, "Forest badge did not open Jupiter")
  end

  previous = story.recorded(state).dup
  old_leagues = state["leagues"].dup
  check19(galactic.fixture_record(state, event, outcome: kind, source: source,
                                  synthetic_sources: sources),
          "confirmed synthetic event did not record: #{event}")
  check19(story.recorded(state) == previous + [event],
          "nonsequential story prefix after Galactic event")
  check19(galactic.completed(state) == events.first(index + 1),
          "Galactic report did not match stored CH14 state")
  check19(state["leagues"] == old_leagues, "Galactic auto-awarded a regional league")
  check19(!state.key?("galactic_defeated") && !state.key?("reward_items"),
          "new false rewards or parallel Galactic flags written")
  rejects(state, event, kind, source, sources)
end

check19(galactic.checkpoint(state) == :outside_s19, "post-lakes incorrectly entered S19")
check19(galactic.next_step(state).nil?, "Cyrus should belong to S20")
check19(story.next_event(state) == "P08_CYRUS", "S20 next stage changed")
check19(!state["leagues"].include?("SINNOH"), "S19 marked League cleared")
check19(BlueRegions.local_achievements(state, "SINNOH") == ["FOREST"],
        "S19 auto-added local badges or mutated achievements")

persisted = Marshal.load(Marshal.dump(state))
check19(galactic.completed(persisted) == events, "save/load loses Galactic milestones")
copy = galactic.completed(persisted)
copy.clear
check19(galactic.completed(persisted) == events, "read-only view returned mutable save")
persisted["current"] = "KANTO"
old = Marshal.dump(persisted)
check19(galactic.checkpoint(persisted) == :invalid_state, "foreign save unlocked Galactic")
rejects(persisted, events.first, :scene_completed, sources.fetch(events.first), sources)
check19(Marshal.dump(persisted) == old, "Kanto save modified")
persisted["current"] = "SINNOH"
check19(galactic.completed(persisted) == events, "regional return lost progress")

broken = Marshal.load(Marshal.dump(state))
broken["sinnoh_ch14"] = [events.first, events.first]
old = Marshal.dump(broken)
check19(galactic.checkpoint(broken) == :invalid_state, "duplicate save prefix accepted")
check19(galactic.completed(broken).nil?, "corrupt save progress reported as valid")
rejects(broken, events.first, :scene_completed, sources.fetch(events.first), sources)
check19(Marshal.dump(broken) == old, "corrupt save repaired")

# Decades and other regional achievements remain independent.
%w[DECADES KANTO JOHTO HOENN].each do |region|
  foreign = BlueRegions.new_state(region)
  before = Marshal.dump(foreign)
  check19(galactic.completed(foreign).nil?, "foreign save read Galactic ledger")
  check19(galactic.checkpoint(foreign) == :invalid_state,
          "#{region} improperly enabled Galactic")
  rejects(foreign, events.first, :scene_completed, sources.fetch(events.first), sources)
  check19(Marshal.dump(foreign) == before, "#{region} changed by Galactic")
end
puts "SINNOH_S19_GALACTIC_FIVE_PHASES_BADGE_ORDER_SAVE_ISOLATION_OFFLINE_OK"
