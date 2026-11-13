# Johto phase 13: isolated Ruby test for League and Hall of Fame rules.
# No Game.exe, Kanto maps, native Hall of Fame handler or installed saves used.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  CIRCUIT = %w[DECADES KANTO JOHTO HOENN SINNOH UNOVA KALOS ALOLA GALAR PALDEA].freeze
  BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO"
    need = {"SURF"=>"FOG", "WATERFALL"=>"RISING"}[action]
    return :unavailable unless need
    return :badge unless local_achievements(state, "JOHTO").include?(need)
    tool_ready ? :allowed : :tool
  end
  def self.unlocked(state)
    available = [state["initial"]]
    state["leagues"].each do |key|
      index = CIRCUIT.index(key)
      next unless index
      available << CIRCUIT[index - 1]
      available << CIRCUIT[(index + 1) % CIRCUIT.length]
    end
    available.uniq
  end
  def self.complete_league(state, region)
    return false unless CIRCUIT.include?(region) &&
                        state["current"] == region &&
                        unlocked(state).include?(region)
    return false if state["leagues"].include?(region)
    state["leagues"] << region
    true
  end
  def self.crystal_total(state, native = 0)
    native + local_achievements(state, "JOHTO").length
  end
end
module TrainerBattle
  class << self
    attr_accessor :result
    def history
      @history ||= []
    end
    def start(*args)
      history << args
      result
    end
  end
end

$messages = []
def _INTL(message, *values)
  values.each_with_index { |value, i| message = message.gsub("{#{i + 1}}", value.to_s) }
  message
end
def pbMessage(message, *args)
  $messages << message
end
def check(value, message)
  raise message unless value
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("blue-johto-league-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {
      "starter"=>"CYNDAQUIL", "blackthorn_rising_claimed"=>true,
      "dragon_master_approved"=>true,
      "goldenrod_radio_tower_cleared"=>true,
      "johto_league_approach_ready"=>true,
      "ice_path_waterfall_received"=>true
    }
    state = {
      "version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
      "achievements"=>{"JOHTO"=>BlueJohtoLeague::BADGES.dup, "KANTO"=>["BOULDER"]},
      "leagues"=>[], "johto_pilot"=>flags
    }
    $PokemonGlobal.blue_regions = state
    before = Marshal.dump(state)
    [:new_bark_return, :route27, :tohjo_falls_enter, :tohjo_waterfall,
     :route26, :victory_road, :victory_road_rival, :indigo_plateau_arrive,
     :begin_challenge, :champion_lance, :hall_of_fame_begin,
     :travel_agent_intro].each do |method|
      check(!BlueJohtoLeague.public_send(method), "#{method} ran in Decades")
    end
    check(!BlueJohtoLeague.elite_four(0), "Elite Four ran in Decades")
    check(!BlueJohtoLeague.hall_of_fame_result(:recorded), "HoF in Decades")
    check(BlueJohtoLeague.region_unlock_preview == [], "Johto unlock in Decades")
    check(Marshal.dump(state) == before, "Johto methods modified Decades save")
    state["current"] = "KANTO"
    check(!BlueJohtoLeague.new_bark_return, "Johto New Bark ran in Kanto")
    check(!BlueJohtoLeague.begin_challenge, "Johto League ran in Kanto")
    check(!BlueJohtoLeague.hall_of_fame_result(:recorded), "Johto HoF in Kanto")
    check(!BlueJohtoLeague.waterfall_allowed?(true), "Johto Waterfall in Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"].delete("RISING")
    check(!BlueJohtoLeague.eight_badges?, "League had eight badges before RISING")
    check(!BlueJohtoLeague.eligible?, "League eligible before eighth badge")
    check(!BlueJohtoLeague.new_bark_return, "League opened before RISING")
    state["achievements"]["JOHTO"] << "RISING"
    flags["johto_league_approach_ready"] = false
    check(!BlueJohtoLeague.eligible?, "League approach flag ignored")
    flags["johto_league_approach_ready"] = true
    flags["dragon_master_approved"] = false
    check(!BlueJohtoLeague.eligible?, "Dragon Master bypassed")
    flags["dragon_master_approved"] = true
    check(BlueJohtoLeague.eight_badges?, "All eight local badges not recognized")
    check(BlueJohtoLeague.eligible?, "League still locked after prerequisites")

    check(BlueJohtoLeague.new_bark_return, "New Bark intro missing")
    check(!BlueJohtoLeague.new_bark_return, "New Bark intro duplicated")
    check(!BlueJohtoLeague.route27(true), "Route27 without real map marker")
    File.write(BlueJohtoLeague::MAP_READY, "WRONG")
    check(!BlueJohtoLeague.route27(true), "Invalid map marker accepted")
    File.write(BlueJohtoLeague::MAP_READY, "BLUE_JOHTO_LEAGUE_ROUTE_V1_READY\n")
    check(!BlueJohtoLeague.route27, "Surf tool bypassed")
    check(BlueJohtoLeague.route27(true), "Route27 failed with Surf and FOG")
    check(!BlueJohtoLeague.route27(true), "Route27 repeated")
    check(BlueJohtoLeague.tohjo_falls_enter, "Tohjo Falls not entered")
    check(!BlueJohtoLeague.tohjo_waterfall, "Waterfall tool bypassed")
    flags["ice_path_waterfall_received"] = false
    check(!BlueJohtoLeague.tohjo_waterfall(true), "Waterfall HM bypassed")
    flags["ice_path_waterfall_received"] = true
    check(BlueJohtoLeague.tohjo_waterfall(true), "Tohjo Falls not cleared")
    check(!BlueJohtoLeague.tohjo_waterfall(true), "Tohjo Falls repeated")
    check(BlueJohtoLeague.route26, "Route26 not visited")
    check(!BlueJohtoLeague.victory_road_rival, "Rival without Victory Road")
    check(BlueJohtoLeague.victory_road, "Victory Road not entered")
    check(!BlueJohtoLeague.indigo_plateau_arrive, "Indigo before rival")
    check(!BlueJohtoLeague.victory_road_rival, "Rival before marker")
    check(TrainerBattle.history.empty?, "Uncompiled Rival battle launched")
    File.write(BlueJohtoLeague::RIVAL_READY, "BLUE_JOHTO_VICTORY_RIVAL_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoLeague.victory_road_rival, "Rival loss marked win")
    check(!flags["johto_victory_rival_defeated"], "Rival defeat flag after loss")
    TrainerBattle.result = true
    check(BlueJohtoLeague.victory_road_rival, "Rival victory missing")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_VICTORY_ROAD_RIVAL, "Rival", 1],
          "Victory Road Rival wrong starter version")
    check(!BlueJohtoLeague.victory_road_rival, "Rival repeated")
    check(BlueJohtoLeague.indigo_plateau_arrive, "Indigo Plateau intro failed")

    check(!BlueJohtoLeague.begin_challenge, "League entered without trainer PBS")
    check(!BlueJohtoLeague.elite_four(0), "Elite Four callable without active run")
    File.write(BlueJohtoLeague::PBS_READY, "WRONG")
    check(!BlueJohtoLeague.begin_challenge, "Bad PBS marker accepted")
    File.write(BlueJohtoLeague::PBS_READY, "BLUE_JOHTO_LEAGUE_TRAINERS_V1_READY\n")
    check(BlueJohtoLeague.begin_challenge, "League did not start")
    check(!BlueJohtoLeague.begin_challenge, "Double-activated League")
    check(!BlueJohtoLeague.elite_four(1), "Skipped Will")
    check(!BlueJohtoLeague.elite_four(-1), "Negative Elite index allowed")
    check(!BlueJohtoLeague.elite_four("0"), "String Elite index allowed")
    check(!BlueJohtoLeague.champion_lance, "Champion before Elite Four")
    TrainerBattle.result = false
    check(!BlueJohtoLeague.elite_four(0), "Lost Will battle counted win")
    check(!flags["johto_league_active"], "League stayed active after loss")
    check(flags["johto_league_step"] == 0, "Loss retained Elite progress")
    check(BlueJohtoLeague.begin_challenge, "Cannot restart League after loss")

    TrainerBattle.result = true
    check(BlueJohtoLeague.elite_four(0), "Will victory failed")
    check(!BlueJohtoLeague.elite_four(0), "Will replayed within attempt")
    check(BlueJohtoLeague.elite_four(1), "Koga victory failed")
    check(BlueJohtoLeague.elite_four(2), "Bruno victory failed")
    check(BlueJohtoLeague.elite_four(3), "Karen victory failed")
    check(!BlueJohtoLeague.elite_four(4), "Elite index four was accepted")
    check(!BlueJohtoLeague.hall_of_fame_begin, "HoF started before Lance")

    TrainerBattle.result = false
    check(!BlueJohtoLeague.champion_lance, "Lost Lance battle counted win")
    check(!flags["johto_league_active"], "Lance loss did not reset challenge")
    check(flags["johto_league_step"] == 0, "Lance loss retained four victories")
    check(state["leagues"].empty?, "Loss completed regional League")
    check(BlueJohtoLeague.region_unlock_preview == [], "Kanto/Hoenn unlocked on loss")

    check(BlueJohtoLeague.begin_challenge, "Could not restart after Lance loss")
    TrainerBattle.result = true
    4.times do |index|
      check(BlueJohtoLeague.elite_four(index),
            "Elite victory not restored in retry stage #{index}")
    end
    check(BlueJohtoLeague.champion_lance, "Lance victory not recorded")
    check(!BlueJohtoLeague.champion_lance, "Duplicate Lance battle")
    check(state["leagues"].empty?, "Lance alone completed the League")
    check(!BlueJohtoLeague.hall_of_fame_begin, "Unverified Hall of Fame started")
    File.write(BlueJohtoLeague::HOF_READY, "WRONG")
    check(!BlueJohtoLeague.hall_of_fame_begin, "Bad Hall of Fame marker accepted")
    File.write(BlueJohtoLeague::HOF_READY, "BLUE_JOHTO_HALL_OF_FAME_V1_READY\n")
    check(BlueJohtoLeague.hall_of_fame_begin, "Hall of Fame not pending")
    check(!BlueJohtoLeague.hall_of_fame_begin, "Hall of Fame pending twice")
    check(!BlueJohtoLeague.hall_of_fame_result(:failed),
          "Failed Hall of Fame recorded as League clear")
    check(!flags["johto_league_hof_pending"], "Failed Hall of Fame blocked retry")
    check(state["leagues"].empty?, "Hall of Fame failure unlocked other regions")
    check(BlueJohtoLeague.hall_of_fame_begin, "Hall of Fame retry unavailable")
    check(!BlueJohtoLeague.hall_of_fame_result(:cancelled),
          "Cancelled Hall of Fame recorded as clear")
    check(BlueJohtoLeague.hall_of_fame_begin, "Hall of Fame after cancel failed")
    check(!BlueJohtoLeague.region_unlock_preview.any?,
          "Other regions unlocked before Hall of Fame confirmation")
    check(BlueJohtoLeague.hall_of_fame_result(:recorded),
          "Verified Hall of Fame failed to complete Johto")
    check(BlueJohtoLeague.league_cleared?, "JOHTO not registered in leagues")
    check(state["leagues"] == ["JOHTO"], "Wrong regional League completed")
    check(flags["johto_league_cleared"] == true, "Johto story flag absent")
    check(!BlueJohtoLeague.hall_of_fame_result(:recorded), "HoF recorded twice")
    check(!BlueJohtoLeague.begin_challenge, "League replayed with first-clear rewards")
    check(!BlueJohtoLeague.champion_lance, "Lance replayed after completion")
    check(BlueJohtoLeague.region_unlock_preview == %w[KANTO HOENN],
          "Johto League did not expose both neighboring regions")
    check(BlueRegions.unlocked(state) == %w[JOHTO KANTO HOENN],
          "Unexpected regional unlocks")
    check(BlueRegions.crystal_total(state, 3) == 11,
          "League fabricated an extra emerald")
    check(state["achievements"]["KANTO"] == ["BOULDER"],
          "Kanto badges modified by Johto completion")
    check(BlueJohtoLeague.travel_agent_intro, "Travel NPC introduction missing")
    check(!BlueJohtoLeague.travel_agent_intro, "Travel NPC introduction repeated")
    check(!flags.key?("kanto_league_cleared"), "Kanto league flag fabricated")
    check(!flags.key?("hoenn_installed"), "Hoenn maps falsely installed")

    persisted = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(persisted)
    check(BlueJohtoLeague.league_cleared?, "League lost after save/reload")
    check(!BlueJohtoLeague.travel_agent_intro, "Travel NPC intro repeated on reload")
    check(!BlueJohtoLeague.hall_of_fame_result(:recorded),
          "League completed twice after reload")
    check(BlueJohtoLeague.region_unlock_preview == %w[KANTO HOENN],
          "Unlocked regions lost on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    kanto_before = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoLeague.begin_challenge, "Johto League callable from Kanto")
    check(!BlueJohtoLeague.league_cleared?, "Johto League active view leaked into Kanto")
    check(!BlueJohtoLeague.travel_agent_intro, "Johto travel NPC in Kanto")
    check(!BlueJohtoLeague.hall_of_fame_result(:recorded), "Johto HoF in Kanto")
    check(BlueJohtoLeague.region_unlock_preview == [], "Johto preview in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == kanto_before,
          "Kanto state modified by Johto League")
  end
end
puts "JOHTO_LEAGUE_RUNTIME_OK"
