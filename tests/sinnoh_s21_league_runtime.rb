# S21: actual BlueRegions/CH14 on SYNTHETIC data, never Game.exe.
# Exercises eight local badges, Barry, Elite, Cynthia and a SEPARATE HoF.
require "json"
class PokemonGlobalMetadata; end
load File.expand_path(ARGV.fetch(0)) # regions data fixture
load File.expand_path(ARGV.fetch(1)) # actual BlueRegions
load File.expand_path(ARGV.fetch(2)) # actual CH14
load File.expand_path(ARGV.fetch(3)) # S21 adapter (not installed)
contract = JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
story = BlueSinnohStoryContracts
league = BlueSinnohLeagueContracts

def s21_check(ok, message)
  raise "SINNOH_S21: #{message}" unless ok
end

def s21_fixture(state, event, outcome, source, sources)
  BlueSinnohLeagueContracts.send(:record_with_sources,
    state, event, outcome, source, sources)
end

def s21_reject(state, event, outcome, source, sources)
  snapshot = Marshal.dump(state)
  s21_check(!s21_fixture(state, event, outcome, source, sources),
            "unverified result accepted for #{event}/#{outcome}")
  s21_check(Marshal.dump(state) == snapshot,
            "rejected callback changed league/save")
end

ids = contract.fetch("steps").map { |row| row.fetch("id") }
types = contract.fetch("steps").map { |row| row.fetch("outcome").to_sym }
sources = contract.fetch("steps").to_h { |row|
  [row.fetch("id"), "FAKE_" + row.fetch("source_key")]
}
s21_check(ids == league::EVENTS && ids == story::STEPS[14, 8],
          "CH14/adapter eight-step order mismatch")
s21_check(league::VERIFIED_NATIVE_SOURCES.empty?, "native handlers falsely active")
s21_check(!league.respond_to?(:record_with_sources),
          "fixture-only recorder exposed as a production method")
s21_check(types.last == :engine_hall_of_fame_confirmed,
          "HoF not independently confirmed")
s21_check(types[1..6].all? { |type| type == :battle_won },
          "Barry/Elite/Cynthia require confirmed battle victories")

state = BlueRegions.new_state("SINNOH")
state["leagues"] << "KANTO"  # preexisting independent regional progress
original_leagues = state["leagues"].dup
s21_check(league.checkpoint(state) == :distortion_incomplete,
          "new save skipped Cyrus/Giratina")
s21_check(league.completed(state) == [], "fresh save has League markers")
s21_check(league.next_step(state).nil?, "League enabled before Distortion")
s21_reject(state, ids.first, types.first, sources.fetch(ids.first), sources)

# Prepare CH14 checkpoints through S19/S20 with synthetic, ordered proof.
# No runtime NPC/battle/map is created; badge awards are fixture-only.
story::STEPS.first(14).each do |id|
  if id == "P05_COMMANDER_JUPITER"
    s21_check(BlueRegions.award(state, "SINNOH", "FOREST"),
              "fixture Forest badge failed")
  end
  if id == "P08_CYRUS"
    %w[MINE ICICLE].each do |badge|
      s21_check(BlueRegions.award(state, "SINNOH", badge),
                "fixture regional badge missing #{badge}")
    end
  end
  s21_check(story.next_event(state) == id,
            "CH14 prerequisite out of order for #{id}")
  s21_check(story.record(state, id, confirmed: true),
            "CH14 synthetic prerequisite failed for #{id}")
end
s21_check(story.next_event(state) == ids.first, "league starts at wrong step")
s21_check(league.checkpoint(state) == :missing_beacon_badge,
          "Volkner gate did not require separate Beacon")
s21_reject(state, ids.first, types.first, sources.fetch(ids.first), sources)
s21_check(BlueRegions.award(state, "SINNOH", "BEACON"),
          "fixture Beacon badge could not be awarded")
s21_check(league.checkpoint(state) == :ready, "Beacon did not enable Volkner")
native_badges = Array.new(24, false)

ids.each_with_index do |id, index|
  if id == "SINNOH_LEAGUE_BARRY_GATE"
    s21_check(league.checkpoint(state) == :missing_eight_badges,
              "Barry gate ignored missing regional badges")
    s21_reject(state, id, types[index], sources.fetch(id), sources)
    %w[COAL COBBLE RELIC FEN].each do |badge|
      s21_check(BlueRegions.award(state, "SINNOH", badge),
                "fixture eighth regional badge missing #{badge}")
    end
    s21_check(BlueRegions.local_achievements(state, "SINNOH").sort ==
              league::REQUIRED_BADGES.sort,
              "Barry gate does not have exactly 8 Sinnoh badges")
    s21_check(native_badges.none?, "Sinnoh medals overwrote Decades badges")
  end

  s21_check(league.checkpoint(state) == :ready,
            "league gate not ready at step #{index}")
  s21_check(league.next_step(state) == id,
            "next League opponent not in story order #{index}")
  outcome = types[index]
  source = sources.fetch(id)
  s21_reject(state, id, outcome, source, {})
  s21_reject(state, id, outcome, source + "_WRONG", sources)
  s21_reject(state, id, outcome.to_s, source, sources)
  s21_reject(state, id, :talked, source, sources)
  s21_reject(state, id, :battle_lost, source, sources)
  s21_reject(state, id, outcome, 777, sources)
  s21_reject(state, :FORGED_BATTLE, outcome, source, sources)
  s21_reject(state, id, outcome, source, { id.to_sym => source })
  if index < ids.length - 1
    future = ids[index + 1]
    s21_reject(state, future, types[index + 1],
               sources.fetch(future), sources)
  end
  if index > 0
    prior = ids[index - 1]
    s21_reject(state, prior, types[index - 1],
               sources.fetch(prior), sources)
  end
  snapshot = Marshal.dump(state)
  s21_check(!league.record_from_native(state, id, outcome: outcome, source: source),
            "empty native source registry certified a League fight")
  s21_check(Marshal.dump(state) == snapshot,
            "blocked native record mutated save")
  old_keys = state.keys.dup
  old_badges = BlueRegions.local_achievements(state, "SINNOH").dup
  old_events = story.recorded(state)
  old_leagues = state["leagues"].dup
  s21_check(s21_fixture(state, id, outcome, source, sources),
            "synthetic, correctly ordered step rejected: #{id}")
  s21_check(story.recorded(state) == old_events + [id],
            "CH14 ordered prefix after #{id} corrupted")
  s21_check(league.completed(state) == ids.first(index + 1),
            "League read-only progress inconsistent")
  s21_check(state.keys == old_keys, "League created false reward/save flags")
  s21_check(BlueRegions.local_achievements(state, "SINNOH") == old_badges,
            "League callback auto-awarded badge")
  if id == "P09_HALL_OF_FAME"
    s21_check(state["leagues"] == old_leagues + ["SINNOH"],
              "distinct HoF did not update existing league ledger once")
    s21_check(league.league_cleared?(state),
              "HoF confirmation did not complete Sinnoh League")
  else
    s21_check(state["leagues"] == old_leagues,
              "Cynthia/Elite prematurely completed the League")
    s21_check(!league.league_cleared?(state),
              "League marked clear before separate Hall of Fame")
  end
  s21_reject(state, id, outcome, source, sources)
  s21_check(native_badges.none?, "league modified native Decades badge array")
end

s21_check(league.checkpoint(state) == :outside_s21,
          "Hall of Fame reopened Elite battle")
s21_check(league.next_step(state).nil?, "phantom extra Elite after Cynthia")
s21_check(story.next_event(state).nil?, "story has phantom post-HoF checkpoint")
s21_check(state["leagues"] == original_leagues + ["SINNOH"],
          "Hall of Fame rewrote historical Kanto league")
s21_check(!state.key?("hoenn_unlocked") && !state.key?("unova_unlocked"),
          "League created unverified travel unlock flags")
s21_check(story.post_cynthia_destination(state, "KANTO") == :unsupported_destination,
          "unlisted post-Cynthia trip allowed")
s21_check(story.post_cynthia_destination(state, "UNOVA") == :travel_service_missing,
          "Unova teleported without native service")

saved = Marshal.load(Marshal.dump(state))
s21_check(league.completed(saved) == ids && league.league_cleared?(saved),
          "serialized save lost Elite/Cynthia/HoF")
read_copy = league.completed(saved)
read_copy.clear
s21_check(league.completed(saved) == ids,
          "read-only League progress leaked mutable regional save")
saved["current"] = "HOENN"
before = Marshal.dump(saved)
s21_check(league.checkpoint(saved) == :invalid_state,
          "foreign region treated Sinnoh as current")
s21_check(league.completed(saved).nil?,
          "foreign save leaked Sinnoh Hall of Fame")
s21_check(!league.record_from_native(saved, ids.last, outcome: types.last,
          source: sources.fetch(ids.last)), "foreign callback accepted")
s21_check(Marshal.dump(saved) == before, "foreign region save changed")
saved["current"] = "SINNOH"
saved["initial"] = "JOHTO"
s21_check(league.league_cleared?(saved),
          "traveler starting in Johto lost Sinnoh Hall of Fame")

corrupt = Marshal.load(Marshal.dump(state))
corrupt["sinnoh_ch14"] = story::STEPS.first(21) + ["P09_CYNTHIA_BATTLE"]
before = Marshal.dump(corrupt)
s21_check(league.checkpoint(corrupt) == :invalid_state,
          "duplicate Cynthia accepted from corrupt save")
s21_check(league.completed(corrupt).nil?,
          "corrupt save presented as valid")
s21_check(!league.record_from_native(corrupt, ids.last,
          outcome: types.last, source: sources.fetch(ids.last)),
          "native callback repaired corrupt save")
s21_check(Marshal.dump(corrupt) == before, "corrupt save mutated")
corrupt = Marshal.load(Marshal.dump(state))
corrupt["leagues"].delete("SINNOH")
s21_check(league.completed(corrupt).nil? && !league.league_cleared?(corrupt),
          "Hall of Fame without existing league ledger accepted")

%w[DECADES KANTO JOHTO HOENN].each do |region|
  foreign = BlueRegions.new_state(region)
  snapshot = Marshal.dump(foreign)
  s21_check(league.checkpoint(foreign) == :distortion_incomplete ||
            league.checkpoint(foreign) == :invalid_state,
            "foreign region allowed Sinnoh League")
  s21_check(!league.record_from_native(foreign, ids.first,
            outcome: types.first, source: sources.fetch(ids.first)),
            "foreign save accepted native League")
  s21_check(Marshal.dump(foreign) == snapshot,
            "foreign save mutated by Sinnoh League")
end

puts "SINNOH_S21_EIGHT_BADGES_ELITE_CYNTHIA_HOF_SEPARATE_OFFLINE_OK"
