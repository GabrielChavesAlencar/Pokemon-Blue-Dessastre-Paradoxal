# CH14 - headless state machine and REAL Blue Regions / RegionTravel guards.
# No Game.exe, no native NPC, no patched maps and no teleport are executed.
require "json"

def check(value, message)
  raise "SINNOH_CH14: #{message}" unless value
end
class PokemonGlobalMetadata; end
module BlueRegionStart
  class << self
    attr_accessor :synthetic_hoenn_present
    def kanto_integrated?; true; end
    def hoenn_integrated?; !!@synthetic_hoenn_present; end
    def hoenn_town_point
      @synthetic_hoenn_present ? [741, 9, 8, 2] : nil
    end
  end
end
load File.expand_path(ARGV.fetch(0))  # tests/regions_data_fixture.rb
load File.expand_path(ARGV.fetch(1))  # scripts/battle_polish/Regions.rb
load File.expand_path(ARGV.fetch(2))  # scripts/battle_polish/RegionTravel.rb
load File.expand_path(ARGV.fetch(3))  # scripts/regions/SinnohStoryContracts.rb
manifest = JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
story = BlueSinnohStoryContracts
steps = manifest.fetch("steps").map { |row| row.fetch("id") }
check(steps == story::STEPS && steps.length == 22,
      "manifest and Ruby order differ")

def copy_state(state)
  Marshal.load(Marshal.dump(state))
end

def must_reject(state, event, **flags)
  prior = Marshal.dump(state)
  check(!BlueSinnohStoryContracts.record(state, event, **flags),
        "improper event was accepted: #{event}")
  check(Marshal.dump(state) == prior, "rejected event mutated regional save")
end

state = BlueRegions.new_state("SINNOH")
check(story.recorded(state) == [] && story.next_event(state) == steps[0],
      "new state has wrong starting checkpoint")
check(!state.key?("sinnoh_ch14"),
      "read-only query initialized a new save field")
check(story.post_cynthia_destination(state, "HOENN") == :story_incomplete,
      "Hoenn available without the Hall of Fame")
check(story.post_cynthia_destination(state, "UNOVA") == :story_incomplete,
      "Unova available without the Hall of Fame")

must_reject(state, steps[1], confirmed: true)
must_reject(state, steps[0], confirmed: false)
must_reject(state, steps[0], confirmed: nil)
must_reject(state, steps[0], confirmed: 1)
must_reject(state, :P05_TEAM_GALACTIC_WINDWORKS, confirmed: true)
must_reject(state, "NOT_A_STORY_FLAG", confirmed: true)

native_badges = Array.new(24, false)
state["leagues"] << "KANTO"
previous_regional_leagues = state["leagues"].dup

steps.each_with_index do |id, index|
  case id
  when "P05_COMMANDER_JUPITER"
    must_reject(state, id, confirmed: true)
    check(BlueRegions.award(state, "SINNOH", "FOREST"),
          "Forest badge prerequisite cannot be awarded synthetically")
  when "P08_CYRUS"
    must_reject(state, id, confirmed: true)
    check(BlueRegions.award(state, "SINNOH", "MINE"), "Mine badge missing")
    check(BlueRegions.award(state, "SINNOH", "ICICLE"), "Icicle badge missing")
  when "P09_VOLKNER_BEACON_BADGE"
    must_reject(state, id, confirmed: true)
    check(BlueRegions.award(state, "SINNOH", "BEACON"), "Beacon badge missing")
  when "SINNOH_LEAGUE_BARRY_GATE"
    must_reject(state, id, confirmed: true)
    %w[COAL COBBLE RELIC FEN].each do |badge|
      check(BlueRegions.award(state, "SINNOH", badge),
            "missing prerequisite Sinnoh badge: " + badge)
    end
    check(BlueRegions.local_achievements(state, "SINNOH").length == 8,
          "not exactly eight Sinnoh badges")
    check(native_badges.none?, "Sinnoh badges wrote Decades native array")
  end
  must_reject(state, id, confirmed: false)
  must_reject(state, "P09_HALL_OF_FAME", confirmed: true,
              hall_of_fame_verified: true) unless id == story::HALL_OF_FAME
  check(story.next_event(state) == id, "wrong required next checkpoint #{index}")
  if id == story::HALL_OF_FAME
    must_reject(state, id, confirmed: true)
    must_reject(state, id, confirmed: true, hall_of_fame_verified: "true")
    must_reject(state, id, confirmed: true, hall_of_fame_verified: 1)
    check(state["leagues"] == previous_regional_leagues,
          "Cynthia victory granted a premature Sinnoh league")
    check(story.record(state, id, confirmed: true,
                       hall_of_fame_verified: true), "native Hall of Fame gate")
  else
    check(story.record(state, id, confirmed: true),
          "failed synthetic confirmed checkpoint: " + id)
  end
  check(story.recorded(state) == steps.first(index + 1),
        "checkpoint record is not an ordered prefix")
  must_reject(state, id, confirmed: true, hall_of_fame_verified: true)
end

check(story.next_event(state).nil?, "extra checkpoint after Hall of Fame")
check(story.league_cleared?(state), "Hall of Fame did not finish Sinnoh league")
check(state["leagues"] == previous_regional_leagues + ["SINNOH"],
      "league ledger duplicated or overwrote Kanto")
check(native_badges.none?, "native Decades badges were modified")
check(!state.key?("hoenn_unlocked") && !state.key?("unova_unlocked"),
      "invented post-Cynthia travel flags")
check(story.post_cynthia_destination(state, "KANTO") == :unsupported_destination,
      "unsupported postleague region was accepted")
check(story.post_cynthia_destination(state, "UNOVA") == :destination_not_installed,
      "Unova unlocked without a destination")
check(story.post_cynthia_destination(state, "HOENN") == :destination_not_installed,
      "Hoenn unlocked without native integration proof")

# Simulate a valid Hoenn arrival but leave Sinnoh source uninstalled. Existing
# RegionTravel.source_valid?(SINNOH) returns FALSE; no false physical travel.
BlueRegionStart.synthetic_hoenn_present = true
check(BlueRegionTravel.hoenn_installed?, "fixture's Hoenn verification missing")
check(!BlueRegionTravel.source_valid?(state),
      "Sinnoh became a physical regional departure without source")
check(story.post_cynthia_destination(state, "HOENN") == :source_not_installed,
      "verified Hoenn arrival allowed departure from uninstalled Sinnoh")
check(story.post_cynthia_destination(state, "UNOVA") == :destination_not_installed,
      "Unova reused Hoenn's arrival point")
check(BlueRegions.unlocked(state).include?("UNOVA"),
      "existing Blue free-travel circuit unexpectedly changed")
check(BlueRegionTravel.destination(state, "UNOVA").nil?,
      "logical circuit incorrectly became a teleport")
BlueRegionStart.synthetic_hoenn_present = false

saved = copy_state(state)
check(saved == state && story.league_cleared?(saved),
      "Marshal save/load lost final Sinnoh checkpoint")
recorded_copy = story.recorded(saved)
recorded_copy.clear
check(story.recorded(saved) == steps,
      "read-only checkpoint inspection leaked mutable save array")
saved["current"] = "HOENN"
foreign_snapshot = Marshal.dump(saved)
check(story.recorded(saved).nil?, "foreign region read Sinnoh checkpoint")
check(story.post_cynthia_destination(saved, "HOENN") == :story_incomplete,
      "foreign region reused Sinnoh league unlock")
must_reject(saved, steps[0], confirmed: true)
check(Marshal.dump(saved) == foreign_snapshot,
      "foreign region mutated its save")
saved["current"] = "SINNOH"
check(story.league_cleared?(saved), "return to Sinnoh lost regional progress")

# A different initial region is legitimate in the shared circuit, unlike a
# forged current region. Sinnoh checkpoint remains stored region-locally.
saved["initial"] = "KANTO"
check(story.league_cleared?(saved),
      "regional travel lost Sinnoh progression for Kanto-start player")

# Corrupt save permutations must not be repaired or have new flags granted.
[
  proc { |s| s["sinnoh_ch14"] = [steps[0], steps[0]] },
  proc { |s| s["sinnoh_ch14"] = [steps[0], steps[2]] },
  proc { |s| s["sinnoh_ch14"] = ["FORGED"] },
  proc { |s| s["sinnoh_ch14"] = "P09_HALL_OF_FAME" },
  proc { |s| s["sinnoh_ch14"] = steps.first(5) + [steps[4]] },
  proc { |s| s["leagues"].delete("SINNOH") },
  proc { |s| s["leagues"] << "SINNOH" },
  proc { |s| s["version"] = 2 },
  proc { |s| s["achievements"]["SINNOH"] << "FORGED" },
  proc { |s| s["achievements"]["SINNOH"] << "FOREST" },
  proc { |s| s["current"] = "JOHTO" },
  proc { |s| s["initial"] = "UNKNOWN" },
].each_with_index do |edit, i|
  broken = copy_state(saved)
  edit.call(broken)
  before = Marshal.dump(broken)
  check(story.recorded(broken).nil?, "corrupted save accepted ##{i}")
  must_reject(broken, steps[0], confirmed: true)
  check(Marshal.dump(broken) == before, "corrupted save repaired ##{i}")
end

# The separate global league method is not overwritten by CH14.
legacy = BlueRegions.new_state("DECADES")
check(!legacy.key?("sinnoh_ch14"),
      "creating a Decades save injected Sinnoh story keys")
check(BlueRegions.complete_league(legacy, "DECADES"),
      "existing Decades league behavior changed")
check(!legacy.key?("sinnoh_ch14"),
      "Decades league wrote Sinnoh story state")
puts "SINNOH_CH14_GALACTIC_CYRUS_CYNTHIA_SAVE_AND_TRAVEL_GUARDS_OK"
