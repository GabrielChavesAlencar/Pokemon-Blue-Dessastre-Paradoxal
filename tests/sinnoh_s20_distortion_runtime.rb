# S20 offline runtime using REAL BlueRegions and CH14 state machine.
# No Game.exe, callbacks, maps, puzzles, Giratina graphics or teleports run.
require "json"
class PokemonGlobalMetadata; end
load File.expand_path(ARGV.fetch(0)) # synthetic regions data fixture
load File.expand_path(ARGV.fetch(1)) # real BlueRegions
load File.expand_path(ARGV.fetch(2)) # real CH14 contract
load File.expand_path(ARGV.fetch(3)) # S20 gate adapter
contract = JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
story = BlueSinnohStoryContracts
distortion = BlueSinnohDistortionContracts

def s20_check(truth, reason)
  raise "SINNOH_S20: #{reason}" unless truth
end

def s20_unchanged(state, reason)
  before = Marshal.dump(state)
  yield
  s20_check(Marshal.dump(state) == before, reason)
end

steps = contract.fetch("steps")
ids = steps.map { |row| row.fetch("id") }
sources = steps.to_h { |row| [row.fetch("id"), "SYNTHETIC_" + row.fetch("source_key")] }
s20_check(ids == distortion::EVENTS, "contract order changed")
s20_check(ids == story::STEPS[5, 9], "S20 incompatible with CH14 prefix")
s20_check(steps.map { |row| row.fetch("phase") }.uniq == [8], "phase 8 changed")
s20_check(distortion::VERIFIED_NATIVE_SOURCES.empty?, "native callbacks falsely enabled")
s20_check(distortion::OUTCOMES.values.uniq.sort ==
  [:battle_won, :encounter_resolved, :puzzles_solved,
   :safe_return_confirmed, :scene_completed].sort, "event outcome types lost")
s20_check(!distortion.respond_to?(:record_with_sources),
          "internal synthetic callback unexpectedly public")

def s20_fixture(state, event, outcome, source, sources)
  # Private helper only; never a public production callback.
  BlueSinnohDistortionContracts.send(
    :record_with_sources, state, event, outcome, source, sources)
end

def s20_reject(state, event, outcome, source, sources)
  s20_unchanged(state, "failed step changed save: #{event}/#{outcome}") do
    s20_check(!s20_fixture(state, event, outcome, source, sources),
              "invalid proof accepted #{event}/#{outcome}")
  end
end

state = BlueRegions.new_state("SINNOH")
s20_check(distortion.checkpoint(state) == :galactic_incomplete,
          "new Sinnoh save skipped S19")
s20_check(distortion.next_step(state).nil?, "unearned S20 available")
s20_check(distortion.completed(state) == [], "fresh save has S20 progress")
s20_check(!distortion.return_ready?(state), "fresh save claims safe return")
s20_reject(state, ids.first, :battle_won, sources.fetch(ids.first), sources)

# Prepare synthetic *prior* milestones using the already audited CH14
# machine. The S20 adapter MUST NOT reimplement or auto-complete S19.
s19_ids = story::STEPS.first(5)
s19_ids.each do |id|
  if id == "P05_COMMANDER_JUPITER"
    s20_check(BlueRegions.award(state, "SINNOH", "FOREST"),
              "fixture Forest badge could not be awarded")
  end
  s20_check(story.next_event(state) == id, "S19 synthetic prerequisite out of order")
  s20_check(story.record(state, id, confirmed: true),
            "S19 synthetic prerequisite failed")
end
s20_check(story.recorded(state) == s19_ids, "S19 previous save prefix corrupted")
s20_check(distortion.checkpoint(state) == :missing_mine_icicle_badges,
          "Cyrus without Mine+Icicle became available")
s20_check(distortion.next_step(state).nil?, "Cyrus missing badges returned step")
s20_reject(state, ids.first, :battle_won, sources.fetch(ids.first), sources)
s20_check(BlueRegions.award(state, "SINNOH", "MINE"), "Mine fixture not recordable")
s20_check(distortion.checkpoint(state) == :missing_mine_icicle_badges,
          "Mine alone bypassed Icicle")
s20_check(BlueRegions.award(state, "SINNOH", "ICICLE"),
          "Icicle fixture not recordable")
s20_check(distortion.checkpoint(state) == :ready, "Mine+Icicle did not open Cyrus")

# Check every typed outcome, prevent early capture, defeat, replays, wrong
# source tokens, skipped puzzles, forged arrival and source registry spoofing.
ids.each_with_index do |id, i|
  outcome = steps[i].fetch("outcome").to_sym
  source = sources.fetch(id)
  s20_check(distortion.next_step(state) == id, "wrong S20 next event ##{i}")
  s20_check(distortion.checkpoint(state) == :ready, "phase-8 gate blocked ##{i}")
  s20_reject(state, id, outcome, source, {})
  s20_reject(state, id, outcome, source + "_FAKE", sources)
  s20_reject(state, id, "battle_won", source, sources)
  s20_reject(state, id, :talked, source, sources)
  s20_reject(state, id, :capture_confirmed, source, sources)
  s20_reject(state, id, outcome, 123, sources)
  s20_reject(state, :FAKE_EVENT, outcome, source, sources)
  s20_reject(state, id, outcome, source, { id.to_sym => source }) # wrong key type
  if i < ids.length - 1
    next_id = ids[i + 1]
    s20_reject(state, next_id, steps[i + 1]["outcome"].to_sym,
               sources.fetch(next_id), sources)
  end
  if i > 0
    prev_id = ids[i - 1]
    s20_reject(state, prev_id, steps[i - 1]["outcome"].to_sym,
               sources.fetch(prev_id), sources)
  end
  s20_unchanged(state, "synthetic result was treated as native verified ##{i}") do
    s20_check(!distortion.record_from_native(state, id, outcome: outcome, source: source),
              "missing native MapID/callback was considered verified")
  end
  old_leagues = state["leagues"].dup
  old_badges = BlueRegions.local_achievements(state, "SINNOH").dup
  old_keys = state.keys.dup
  before = story.recorded(state).dup
  s20_check(s20_fixture(state, id, outcome, source, sources),
            "valid synthetic S20 checkpoint rejected ##{i}")
  s20_check(story.recorded(state) == before + [id], "CH14 ordered prefix lost")
  s20_check(distortion.completed(state) == ids.first(i + 1),
            "S20 report does not match the ledger")
  s20_check(old_leagues == state["leagues"], "S20 awarded a league")
  s20_check(BlueRegions.local_achievements(state, "SINNOH") == old_badges,
            "S20 awarded a badge")
  s20_check(state.keys == old_keys, "S20 wrote parallel flags, items or maps")
  s20_reject(state, id, outcome, source, sources)
  if id == "P08_GIRATINA_ENCOUNTER"
    s20_check(!state.key?("giratinacaptured") && !state.key?("giratina_reward"),
              "Giratina became forced capture/reward")
    s20_check(!distortion.return_ready?(state),
              "Giratina result alone falsely certified safe return")
    s20_reject(state, "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
               :scene_completed, sources.fetch("P08_SAFE_RETURN_FROM_DISTORTION_WORLD"),
               sources)
  end
end

s20_check(distortion.checkpoint(state) == :outside_s20, "post-return gate active")
s20_check(distortion.next_step(state).nil?, "S21/S15 gate leaked into S20")
s20_check(distortion.return_ready?(state), "completed S20 not recognized")
s20_check(story.next_event(state) == "P09_VOLKNER_BEACON_BADGE",
          "after safe return must be Volkner checkpoint, not League")
s20_check(!state["leagues"].include?("SINNOH"),
          "safe return auto-approved the Sinnoh League")
s20_check(!state.key?("teleport") && !state.key?("distortion_map_id"),
          "safe return wrote an imaginary physical map/teleport")

saved = Marshal.load(Marshal.dump(state))
s20_check(distortion.return_ready?(saved), "Marshal save/load lost S20 progress")
copy = distortion.completed(saved)
copy.clear
s20_check(distortion.completed(saved) == ids,
          "read-only completed() returned shared mutable state")

# A traveler can return to Sinnoh; CH14 state is still protected from other
# regional scripts and does not touch previous regional league achievements.
saved["current"] = "HOENN"
s20_unchanged(saved, "foreign save mutated by S20") do
  s20_check(distortion.checkpoint(saved) == :invalid_state, "foreign region enabled S20")
  s20_check(!distortion.record_from_native(saved, ids.last,
            outcome: :safe_return_confirmed, source: sources.fetch(ids.last)),
            "foreign save accepted native S20 callback")
  s20_check(distortion.completed(saved).nil?, "foreign save leaked S20 history")
end
saved["current"] = "SINNOH"
s20_check(distortion.return_ready?(saved), "regional return lost S20")

corrupt = Marshal.load(Marshal.dump(state))
corrupt["sinnoh_ch14"] = story::STEPS.first(6) + [ids.first]
s20_unchanged(corrupt, "invalid duplicate checkpoint fixed itself") do
  s20_check(distortion.checkpoint(corrupt) == :invalid_state, "forged prefix accepted")
  s20_check(distortion.completed(corrupt).nil?, "corrupt save reported ready")
end

%w[DECADES KANTO JOHTO HOENN].each do |region|
  foreign = BlueRegions.new_state(region)
  s20_unchanged(foreign, "S20 mutated regional save #{region}") do
    s20_check(distortion.checkpoint(foreign) == :galactic_incomplete ||
              distortion.checkpoint(foreign) == :invalid_state,
              "S20 checkpoint improperly activated in #{region}")
    s20_check(!distortion.record_from_native(
      foreign, ids.first, outcome: :battle_won, source: sources.fetch(ids.first)),
      "foreign native call accepted")
  end
end

puts "SINNOH_S20_DISTORTION_PUZZLES_GIRATINA_SAFE_RETURN_OFFLINE_OK"
