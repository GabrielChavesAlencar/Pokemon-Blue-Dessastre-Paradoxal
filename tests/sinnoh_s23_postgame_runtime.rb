# S23: actual BlueRegions and CH14 on synthetic state and event sources.
# No native maps, item, Pokemon, encounter, battle or PC is executed.
require "json"
class PokemonGlobalMetadata; end
load File.expand_path(ARGV.fetch(0)) # historical REGISTRY fixture
load File.expand_path(ARGV.fetch(1)) # real Regions
load File.expand_path(ARGV.fetch(2)) # CH14
load File.expand_path(ARGV.fetch(3)) # S23 adapter, not autoloaded
contract = JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
story = BlueSinnohStoryContracts
post = BlueSinnohPostgameContracts

def check23(ok, msg)
  raise "SINNOH_S23: #{msg}" unless ok
end

def fixture23(state, key, kind, source, sources,
              item: false, strongest: false)
  BlueSinnohPostgameContracts.send(:record_with_sources,
    state, key, kind, source, sources, item, strongest)
end

def reject23(state, key, kind, source, sources, item: false, strongest: false)
  before = Marshal.dump(state)
  check23(!fixture23(state, key, kind, source, sources,
                   item: item, strongest: strongest),
          "untrusted S23 callback accepted #{key}/#{kind}")
  check23(Marshal.dump(state) == before,
          "rejected postgame callback mutated save")
end

rows = contract.fetch("events")
ids = rows.map { |row| row.fetch("id") }
kinds = rows.map { |row| row.fetch("outcome").to_sym }
sources = rows.to_h { |row| [row.fetch("id"), "FAKE_" + row.fetch("reference_area")] }
check23(ids == post::EVENTS, "S23 coverage order mismatches runtime")
check23(post::VERIFIED_NATIVE_SOURCES.empty?, "unverified native sources enabled")
check23(post::HISTORICAL_ELITE_IDS == contract.fetch("historical_elite_refs"),
        "historical Platinum Elite identifiers changed")
check23(!post.respond_to?(:record_with_sources), "synthetic recorder became public")

state = BlueRegions.new_state("SINNOH")
state["leagues"] << "KANTO"
check23(post.recorded(state) == [] && !post.valid_postleague?(state),
        "new save falsely has postgame")
check23(post.gate(state, ids.first) == :hall_of_fame_required,
        "Battle Zone opened before Sinnoh Hall of Fame")
check23(post.historical_elite_references(state).empty?,
        "historical rematch preview enabled before League clear")
check23(post.gate(state, :INVALID) == :unknown_event,
        "unrecognized postgame milestone accepted")
reject23(state, ids.first, kinds.first, sources.fetch(ids.first), sources)

# Use the *real* CH14 ordered story contract to create a fixture Hall of Fame,
# including its separate engine-confirmation prerequisite.
story::STEPS.each do |event|
  case event
  when "P05_COMMANDER_JUPITER"
    check23(BlueRegions.award(state, "SINNOH", "FOREST"), "Forest fixture failed")
  when "P08_CYRUS"
    %w[MINE ICICLE].each do |badge|
      check23(BlueRegions.award(state, "SINNOH", badge), "Cyrus badge #{badge}")
    end
  when "P09_VOLKNER_BEACON_BADGE"
    check23(BlueRegions.award(state, "SINNOH", "BEACON"), "Beacon fixture failed")
  when "SINNOH_LEAGUE_BARRY_GATE"
    %w[COAL COBBLE RELIC FEN].each do |badge|
      check23(BlueRegions.award(state, "SINNOH", badge), "Barry badge #{badge}")
    end
  end
  if event == "P09_HALL_OF_FAME"
    prior = Marshal.dump(state)
    check23(!story.record(state, event, confirmed: true),
            "unverified Hall completed Sinnoh League")
    check23(Marshal.dump(state) == prior, "fake HoF mutated save")
    check23(story.record(state, event, confirmed: true,
                         hall_of_fame_verified: true), "fixture HoF failed")
  else
    check23(story.record(state, event, confirmed: true),
            "missing S23 synthetic story checkpoint #{event}")
  end
end
check23(post.valid_postleague?(state) && story.league_cleared?(state),
        "postgame did not read separate CH14 Hall")
check23(post.recorded(state) == [], "Hall gave optional postgame rewards")
check23(post.historical_elite_references(state) == post::HISTORICAL_ELITE_IDS,
        "historical Elite/Cynthia after Sinnoh Hall missing")
check23(!post.strongest_rematch_eligible?(state, verified_roster: true),
        "one regional League falsely allowed global strongest rematch")
check23(post.gate(state, ids.last, verified_rematch_roster: true) ==
        :all_ten_leagues_required,
        "Full Power enabled without ten global Leagues")
check23(BlueRegions.profile(state, true) == :first_clear,
        "global rematch profile changed before world champion")
check23(post.gate(state, "P10_HEATRAN_QUEST") == :battle_zone_entry_required,
        "Heatran quest available before verified Battle Zone entry")
%w[P10_DARKRAI_CONDITIONAL_QUEST P10_SHAYMIN_CONDITIONAL_QUEST].each do |event|
  check23(post.gate(state, event) == :special_event_item_not_verified,
          "event-only legendary unlocked without event item")
end
check23(post.gate(state, ids.first) == :ready_for_verified_native_event,
        "Battle Zone logical gate not prepared")
check23(post.gate(state, "P10_CRESSELIA_EVENT") ==
        :ready_for_verified_native_event,
        "Cresselia optional postgame blocked incorrectly")
check23(BlueRegions.allow_specials?(state, "SINNOH"),
        "eight badges did not permit party specials")

# The only possible mutation is from the private synthetic recorder after a
# correctly typed, source-matching proof; public production API always rejects.
ids.each_with_index do |event, i|
  kind = kinds[i]
  source = sources.fetch(event)
  special = i == 3 || i == 4
  strongest = i == 5
  if strongest
    check23(post.gate(state, event) == :all_ten_leagues_required,
            "full power gate skipped global League progression")
    # Forge the global titles IN THE FIXTURE ONLY. Never grant a real League.
    BlueRegions.circuit.each do |region|
      state["leagues"] << region unless state["leagues"].include?(region)
    end
    check23(BlueRegions.world_champion?(state), "ten-league fixture unavailable")
    check23(post.gate(state, event) == :native_strongest_roster_not_verified,
            "champion status incorrectly verified a rematch team")
    check23(post.strongest_rematch_eligible?(state, verified_roster: true),
            "independent roster proof not recognized by fixture")
    check23(BlueRegions.profile(state, true) == :world_champion_rematch,
            "world champion rematch profile missing")
  end
  if special
    check23(post.gate(state, event) == :special_event_item_not_verified,
            "Darkrai/Shaymin event item requirement dropped")
  end
  reject23(state, event, kind, source, sources, item: special, strongest: strongest)
    if !special && !strongest && event == "P10_HEATRAN_QUEST" &&
      !post.recorded(state).include?(ids.first)
  reject23(state, event, kind, source + "_WRONG", sources,
           item: special, strongest: strongest)
  reject23(state, event, kind.to_s, source, sources,
           item: special, strongest: strongest)
  reject23(state, event, :talked, source, sources,
           item: special, strongest: strongest)
  reject23(state, event, :battle_lost, source, sources,
           item: special, strongest: strongest)
  reject23(state, event, kind, 123, sources,
           item: special, strongest: strongest)
  reject23(state, :FAKE, kind, source, sources,
           item: special, strongest: strongest)
  reject23(state, event, kind, source, {},
           item: special, strongest: strongest)
  if special
    reject23(state, event, kind, source, sources, item: false, strongest: false)
  end
  if strongest
    reject23(state, event, kind, source, sources, strongest: false)
  end
  pre_native = Marshal.dump(state)
  check23(!post.record_from_native(state, event, outcome: kind, source: source,
                                    event_item_verified: special,
                                    verified_rematch_roster: strongest),
          "uninstalled event accepted by native recorder")
  check23(Marshal.dump(state) == pre_native, "native false proof mutated save")
  old_badges = BlueRegions.local_achievements(state, "SINNOH")
  old_leagues = state["leagues"].dup
  old_keys = state.keys.dup
  before = post.recorded(state)
  check23(fixture23(state, event, kind, source, sources,
                    item: special, strongest: strongest),
          "valid SYNTHETIC S23 milestone not accepted #{event}")
  check23(post.recorded(state) == before + [event],
          "optional event ledger lost order/idempotence")
  check23(BlueRegions.local_achievements(state, "SINNOH") == old_badges &&
          state["leagues"] == old_leagues,
          "postgame event modified league/badges")
  check23(state.keys == old_keys + (i.zero? ? [post::SAVE_KEY] : []),
          "unexpected save/reward flag from postgame")
  reject23(state, event, kind, source, sources,
           item: special, strongest: strongest)
end
check23(post.recorded(state) == ids, "postgame events did not persist")
check23(!state.key?("caught_heatran") && !state.key?("darkrai_given") &&
        !state.key?("shaymin_given") && !state.key?("battle_zone_map"),
        "legendary or map reward fabricated")
check23(BlueRegions.local_achievements(state, "SINNOH").length == 8,
        "optional events created/doubled regional badges")

saved = Marshal.load(Marshal.dump(state))
post.recorded(saved).clear
check23(post.recorded(saved) == ids, "read-only event history leaked save")
saved["current"] = "HOENN"
before = Marshal.dump(saved)
check23(post.recorded(saved).nil? &&
        post.gate(saved, ids.first) == :invalid_state &&
        post.historical_elite_references(saved).empty?,
        "foreign region accepted Sinnoh postgame")
check23(Marshal.dump(saved) == before, "foreign preview changed save")
saved["current"] = "SINNOH"
check23(post.recorded(saved) == ids, "regional return erased optional history")

# Duplicate/unknown event ids, invalid HOF, false region never get repaired.
[
  proc { |s| s[post::SAVE_KEY] << ids.first },
  proc { |s| s[post::SAVE_KEY] << "NOT_SINNOH" },
  proc { |s| s[post::SAVE_KEY] = "P10_HEATRAN_QUEST" },
  proc { |s| s["leagues"].delete("SINNOH") },
  proc { |s| s["sinnoh_ch14"] = ["P09_HALL_OF_FAME"] },
  proc { |s| s["version"] = 2 },
].each_with_index do |mutation, index|
  broken = Marshal.load(Marshal.dump(state))
  mutation.call(broken)
  snap = Marshal.dump(broken)
  check23(post.recorded(broken).nil?, "invalid optional save accepted ##{index}")
  check23(post.gate(broken, ids.first) == :invalid_state,
          "invalid optional milestone gate unlocked ##{index}")
  check23(Marshal.dump(broken) == snap, "corrupt postgame save modified ##{index}")
end

# 8 local badges gate for Legendary/Mythical/UB/Paradox; local progress is
# distinct from the world champion/full power condition.
limited = BlueRegions.new_state("SINNOH")
%w[COAL FOREST COBBLE RELIC FEN MINE ICICLE].each do |badge|
  check23(BlueRegions.award(limited, "SINNOH", badge), "synthetic badge failed")
end
check23(!BlueRegions.allow_specials?(limited, "SINNOH"),
        "seven badges enabled forbidden party specials")
check23(BlueRegions.award(limited, "SINNOH", "BEACON"),
        "eighth local badge fixture failed")
check23(BlueRegions.allow_specials?(limited, "SINNOH"),
        "eighth badge did not permit Sinnoh party specials")
check23(!BlueRegions.allow_specials?(limited, "UNOVA"),
        "Sinnoh badges incorrectly unlocked Unova specials")

%w[DECADES KANTO JOHTO HOENN].each do |region|
  foreign = BlueRegions.new_state(region)
  before = Marshal.dump(foreign)
  check23(post.recorded(foreign).nil? &&
          post.gate(foreign, ids.first) == :invalid_state,
          "foreign region received optional Sinnoh state")
  check23(Marshal.dump(foreign) == before,
          "foreign region mutated by optional event")
end
puts "SINNOH_S23_POSTGAME_QUESTS_HISTORICAL_VS_GLOBAL_REMATCH_IDEMPOTENT_OFFLINE_OK"
