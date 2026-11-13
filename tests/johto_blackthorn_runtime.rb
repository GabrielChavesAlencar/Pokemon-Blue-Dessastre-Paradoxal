# Isolated Ruby regression for Johto 12/16. NO game files, maps or saves.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze

  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.award(state, region, badge)
    return false unless state["current"] == "JOHTO" && region == "JOHTO"
    return false unless BADGES.include?(badge)
    list = (state["achievements"] ||= {})[region] ||= []
    return false if list.include?(badge)
    list << badge
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").length
  end
  def self.allow_specials?(state, region)
    local_achievements(state, region).length >= 8
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO"
    need = {"STRENGTH"=>"PLAIN", "WHIRLPOOL"=>"GLACIER",
            "WATERFALL"=>"RISING"}[action]
    return :unavailable unless need
    return :badge unless local_achievements(state, "JOHTO").include?(need)
    tool_ready ? :allowed : :tool
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
module GameData
  module Item
    def self.exists?(item)
      item == :HM07
    end
  end
end
$messages = []
$questions = []
$items = []
$gift_ok = true

def _INTL(text, *values)
  values.each_with_index { |value, i| text = text.gsub("{#{i + 1}}", value.to_s) }
  text
end
def pbMessage(message, options = nil, default = nil)
  $messages << message
  options ? $questions.shift : nil
end
def pbReceiveItem(item)
  return false unless $gift_ok
  $items << item
  true
end
def check(ok, message)
  raise message unless ok
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("blue-johto-blackthorn-") do |root|
  Dir.chdir(root) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {"starter"=>"TOTODILE", "route44_ready"=>true,
             "goldenrod_radio_tower_cleared"=>true}
    state = {"version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
             "achievements"=>{"JOHTO"=>BlueJohtoBlackthorn::REQUIRED_BADGES.dup},
             "johto_pilot"=>flags}
    $PokemonGlobal.blue_regions = state
    before = Marshal.dump(state)
    [
      [:route44], [:ice_path_enter], [:ice_slide], [:ice_boulder, 0, true],
      [:waterfall_item], [:ice_path_exit], [:blackthorn_arrive],
      [:clair_gym_puzzle], [:clair], [:dragons_den_enter],
      [:dragon_shrine_access, true], [:dragon_master_trial],
      [:clair_rising_badge], [:route45], [:route46],
      [:dark_cave_entry], [:league_handoff]
    ].each do |method, *args|
      check(!BlueJohtoBlackthorn.public_send(method, *args),
            "Decades unexpectedly ran #{method}")
    end
    check(!BlueJohtoBlackthorn.waterfall_allowed?(true), "Decades got Waterfall")
    check(!BlueJohtoBlackthorn.specials_unlocked?, "Decades specials unlocked")
    check(Marshal.dump(state) == before, "Decades state modified")
    state["current"] = "KANTO"
    check(!BlueJohtoBlackthorn.clair, "Kanto ran Clair")
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Kanto ran Dragon Master")
    check(!BlueJohtoBlackthorn.league_handoff, "Kanto got League handoff")
    check(!BlueJohtoBlackthorn.strength_allowed?(true), "Kanto got Johto Strength")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"].delete("GLACIER")
    check(!BlueJohtoBlackthorn.seven_badges?, "Seven badges without Glacier")
    check(!BlueJohtoBlackthorn.route44, "Route44 before Glacier")
    check(!BlueJohtoBlackthorn.clair, "Clair before seven badges")
    check(!BlueJohtoBlackthorn.specials_unlocked?, "Specials before eight badges")
    check(BlueRegions.award(state, "JOHTO", "GLACIER"), "Could not setup Glacier")
    flags["goldenrod_radio_tower_cleared"] = false
    check(!BlueJohtoBlackthorn.route44, "Route44 without Radio Tower")
    flags["goldenrod_radio_tower_cleared"] = true
    flags["route44_ready"] = false
    check(!BlueJohtoBlackthorn.route44, "Route44 without previous phase")
    flags["route44_ready"] = true
    check(BlueJohtoBlackthorn.route44, "Route44 start missing")
    check(!BlueJohtoBlackthorn.route44, "Route44 start duplicated")
    check(!BlueJohtoBlackthorn.ice_path_enter, "Ice Path without source marker")
    File.write(BlueJohtoBlackthorn::ICE_READY, "INVALID")
    check(!BlueJohtoBlackthorn.ice_path_enter, "Wrong Ice Path marker")
    File.write(BlueJohtoBlackthorn::ICE_READY,
               "BLUE_JOHTO_ICE_PATH_V1_READY\n")
    check(BlueJohtoBlackthorn.ice_path_enter, "Ice Path did not open")
    check(!BlueJohtoBlackthorn.ice_path_enter, "Ice Path opened twice")
    check(BlueJohtoBlackthorn.ice_slide, "Ice slide checkpoint missing")
    check(!BlueJohtoBlackthorn.ice_slide, "Ice slide duplicated")
    check(!BlueJohtoBlackthorn.ice_boulder(4, true), "Unknown boulder")
    check(!BlueJohtoBlackthorn.ice_boulder("0", true), "Text boulder ID accepted")
    check(!BlueJohtoBlackthorn.ice_boulder(0), "Strength tool bypassed")
    check(!BlueJohtoBlackthorn.ice_boulder(0, true), "Boulder without puzzle marker")
    check(!BlueJohtoBlackthorn.ice_path_exit, "Ice Path cleared without boulders")
    File.write(BlueJohtoBlackthorn::BOULDER_READY, "WRONG")
    check(!BlueJohtoBlackthorn.ice_boulder(0, true), "Wrong boulder marker")
    File.write(BlueJohtoBlackthorn::BOULDER_READY,
               "BLUE_JOHTO_ICE_BOULDERS_V1_READY\n")
    check(BlueJohtoBlackthorn.ice_boulder(2, true), "Boulder2 not recorded")
    check(BlueJohtoBlackthorn.ice_boulder(0, true), "Boulder0 not recorded")
    check(!BlueJohtoBlackthorn.ice_boulder(0, true), "Boulder0 duplicated")
    check(!BlueJohtoBlackthorn.boulders_complete?, "Boulders completed early")
    check(BlueJohtoBlackthorn.ice_boulder(3, true), "Boulder3 not recorded")
    check(BlueJohtoBlackthorn.ice_boulder(1, true), "Boulder1 not recorded")
    check(BlueJohtoBlackthorn.boulders_complete?, "All four boulders not recorded")

    check(!BlueJohtoBlackthorn.waterfall_item, "Unverified Waterfall HM given")
    File.write(BlueJohtoBlackthorn::WATERFALL_READY, "WRONG")
    check(!BlueJohtoBlackthorn.waterfall_item, "Wrong Waterfall marker accepted")
    File.write(BlueJohtoBlackthorn::WATERFALL_READY,
               "BLUE_JOHTO_WATERFALL_ITEM_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoBlackthorn.waterfall_item, "Failed gift marked as received")
    check(!flags["ice_path_waterfall_received"], "Failed gift persisted")
    $gift_ok = true
    check(BlueJohtoBlackthorn.waterfall_item, "Waterfall gift missing")
    check(!BlueJohtoBlackthorn.waterfall_item, "Waterfall gift repeated")
    check($items == [:HM07], "Wrong HM delivered or duplicated")
    check(!BlueJohtoBlackthorn.waterfall_allowed?(true), "Waterfall before Rising")
    check(BlueJohtoBlackthorn.ice_path_exit, "Ice Path exit not recorded")
    check(!BlueJohtoBlackthorn.ice_path_exit, "Ice Path exit repeated")
    check(BlueJohtoBlackthorn.blackthorn_arrive, "Blackthorn arrival missing")
    check(!BlueJohtoBlackthorn.blackthorn_arrive, "Blackthorn arrival repeated")

    check(!BlueJohtoBlackthorn.clair, "Clair before gym puzzle")
    check(!BlueJohtoBlackthorn.clair_gym_puzzle, "Gym puzzle without map marker")
    File.write(BlueJohtoBlackthorn::GYM_PUZZLE_READY, "WRONG")
    check(!BlueJohtoBlackthorn.clair_gym_puzzle, "Invalid gym puzzle marker")
    File.write(BlueJohtoBlackthorn::GYM_PUZZLE_READY,
               "BLUE_JOHTO_BLACKTHORN_PUZZLE_V1_READY\n")
    check(BlueJohtoBlackthorn.clair_gym_puzzle, "Gym puzzle not recorded")
    check(!BlueJohtoBlackthorn.clair_gym_puzzle, "Gym puzzle repeated")
    check(!BlueJohtoBlackthorn.clair, "Uncompiled Clair trainer invoked")
    check(TrainerBattle.history.empty?, "Battle ran without verified PBS")
    File.write(BlueJohtoBlackthorn::GYM_READY, "BAD")
    check(!BlueJohtoBlackthorn.clair, "Bad Clair PBS marker")
    File.write(BlueJohtoBlackthorn::GYM_READY,
               "BLUE_JOHTO_BLACKTHORN_GYM_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoBlackthorn.clair, "Clair defeat awarded victory")
    check(!flags["blackthorn_clair_defeated"], "Clair defeated flag from loss")
    check(!BlueJohtoBlackthorn.rising_earned?, "Rising badge awarded for loss")
    TrainerBattle.result = true
    check(BlueJohtoBlackthorn.clair, "Clair victory not registered")
    check(!BlueJohtoBlackthorn.clair, "Clair battle repeated")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_CLAIR, "Clair", 0],
          "Wrong Clair PBS type/version")
    check(!BlueJohtoBlackthorn.rising_earned?, "Rising awarded before Master")
    check(BlueRegions.crystal_total(state, 5) == 12,
          "Clair battle granted early emerald")
    check(!BlueJohtoBlackthorn.clair_rising_badge, "Rising before Dragon Master")

    check(!BlueJohtoBlackthorn.dragons_den_enter, "Den without map ready marker")
    File.write(BlueJohtoBlackthorn::DEN_READY, "BLUE_JOHTO_DRAGONS_DEN_V1_READY\n")
    check(BlueJohtoBlackthorn.dragons_den_enter, "Den entry missing")
    check(!BlueJohtoBlackthorn.dragons_den_enter, "Den entry repeated")
    check(!BlueJohtoBlackthorn.dragon_shrine_access(true),
          "Shrine reached without Whirlpool item")
    flags["rocket_hq_whirlpool_received"] = true
    check(!BlueJohtoBlackthorn.dragon_shrine_access, "Whirlpool tool bypassed")
    check(BlueJohtoBlackthorn.dragon_shrine_access(true),
          "Shrine could not be reached with Glacier and Whirlpool")
    check(!BlueJohtoBlackthorn.dragon_shrine_access(true), "Shrine repeated")
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Master without marker")
    File.write(BlueJohtoBlackthorn::MASTER_READY, "WRONG")
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Wrong master marker")
    File.write(BlueJohtoBlackthorn::MASTER_READY,
               "BLUE_JOHTO_DRAGON_MASTER_V1_READY\n")
    $questions = [0]
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Wrong answer passed")
    check(!flags["dragon_master_approved"], "Wrong answer persisted")
    $questions = [3]
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Cancel passed")
    $questions = [1, 0, 0]
    check(BlueJohtoBlackthorn.dragon_master_trial, "Correct answers rejected")
    check(!BlueJohtoBlackthorn.dragon_master_trial, "Master repeated")
    check(!BlueJohtoBlackthorn.rising_earned?, "Master automatically awarded badge")
    check(BlueJohtoBlackthorn.clair_rising_badge, "Rising not awarded after Master")
    check(BlueJohtoBlackthorn.rising_earned?, "Rising missing")
    check(!BlueJohtoBlackthorn.clair_rising_badge, "Rising duplicated")
    check(BlueRegions.local_achievements(state, "JOHTO") ==
          BlueJohtoBlackthorn::REQUIRED_BADGES + ["RISING"],
          "Wrong local eighth badge")
    check(BlueRegions.crystal_total(state, 5) == 13,
          "Eighth badge contributed wrong number of emeralds")
    check(BlueJohtoBlackthorn.specials_unlocked?,
          "Specials not permitted after eight local badges")
    check(!BlueJohtoBlackthorn.waterfall_allowed?, "Waterfall bypassed tool")
    check(BlueJohtoBlackthorn.waterfall_allowed?(true),
          "Waterfall unavailable with Rising and tool")
    check(BlueJohtoBlackthorn.route45, "Route45 not recorded")
    check(!BlueJohtoBlackthorn.route45, "Route45 repeated")
    check(BlueJohtoBlackthorn.route46, "Route46 not recorded")
    check(!BlueJohtoBlackthorn.route46, "Route46 repeated")
    check(!BlueJohtoBlackthorn.dark_cave_entry, "Unverified Dark Cave entered")
    check(BlueJohtoBlackthorn.league_handoff, "League approach did not unlock")
    check(!BlueJohtoBlackthorn.league_handoff, "League handoff duplicated")
    check(!flags.key?("johto_league_cleared"),
          "Phase 12 prematurely cleared Johto League")
    check(!flags.key?("league_hall_of_fame"),
          "Phase 12 fabricated Hall of Fame")

    state_saved = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(state_saved)
    check(BlueJohtoBlackthorn.rising_earned?, "Rising lost on reload")
    check(BlueJohtoBlackthorn.specials_unlocked?, "Specials lost on reload")
    check(!BlueJohtoBlackthorn.waterfall_item, "HM duplicated on reload")
    check(!BlueJohtoBlackthorn.clair, "Clair replayed on reload")
    check(!BlueJohtoBlackthorn.clair_rising_badge, "Rising replayed on reload")
    check(!BlueJohtoBlackthorn.league_handoff, "League handoff repeated on reload")
    check(BlueRegions.crystal_total($PokemonGlobal.blue_regions, 5) == 13,
          "Emerald total changed on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    before = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoBlackthorn.rising_earned?, "Rising exposed in Kanto")
    check(!BlueJohtoBlackthorn.waterfall_allowed?(true),
          "Johto Waterfall used in Kanto")
    check(!BlueJohtoBlackthorn.specials_unlocked?,
          "Johto special authorization applied in Kanto")
    check(!BlueJohtoBlackthorn.league_handoff, "Johto League appeared in Kanto")
    check(!BlueJohtoBlackthorn.dark_cave_entry, "Dark Cave event in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before,
          "Kanto was modified by Johto")
  end
end
puts "JOHTO_BLACKTHORN_RUNTIME_OK"
