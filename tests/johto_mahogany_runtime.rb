# Phase 11 state machine regression with temporary maps/items/trainers stubs.
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
    list = (state["achievements"] ||= {})["JOHTO"] ||= []
    return false if list.include?(badge)
    list << badge
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").length
  end
  def self.field_access(state, region, action, ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO"
    return :unavailable unless action == "WHIRLPOOL"
    return :badge unless local_achievements(state, "JOHTO").include?("GLACIER")
    ready ? :allowed : :tool
  end
end
module TrainerBattle
  class << self
    attr_accessor :result
    def history
      @history ||= []
    end
    def start(*arguments)
      history << arguments
      result
    end
  end
end
module GameData
  module Item
    def self.exists?(key)
      [:REDSCALE, :HM06].include?(key)
    end
  end
  module Species
    def self.exists?(key)
      [:GYARADOS, :ELECTRODE].include?(key)
    end
  end
end
$items = []
$messages = []
$gift_ok = true
def _INTL(value, *args)
  args.each_with_index { |v, i| value = value.gsub("{#{i + 1}}", v.to_s) }
  value
end
def pbMessage(value, *args)
  $messages << value
end
def pbReceiveItem(id)
  return false unless $gift_ok
  $items << id
  true
end
def check(condition, message)
  raise message unless condition
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("blue-johto-phase11-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {"starter"=>"CYNDAQUIL", "ecruteak_visited"=>true,
             "olivine_jasmine_defeated"=>true}
    state = {"version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
             "achievements"=>{"JOHTO"=>%w[ZEPHYR HIVE PLAIN FOG STORM MINERAL]},
             "johto_pilot"=>flags}
    $PokemonGlobal.blue_regions = state
    previous = Marshal.dump(state)
    operations = [
      [:route42], [:mahogany_arrive], [:route43], [:lake_arrive],
      [:red_gyarados_begin], [:red_gyarados_result, :caught], [:red_scale],
      [:lance_meeting], [:rocket_hq_enter], [:hq_grunt, 0],
      [:hq_security_off], [:hq_door], [:hq_petrel], [:hq_lance_help],
      [:hq_ariana], [:hq_electrode_begin, 0],
      [:hq_electrode_result, 0, :defeated], [:hq_lance_electrodes],
      [:hq_finish], [:whirlpool_reward], [:pryce_ice_puzzle], [:pryce],
      [:radio_takeover], [:radio_petrel], [:radio_rival],
      [:radio_underground_puzzle], [:radio_director_rescue],
      [:radio_executive, 0], [:radio_finish], [:route44]
    ]
    operations.each do |method, *args|
      check(!BlueJohtoMahogany.public_send(method, *args),
            "Johto operation #{method} worked in Decades")
    end
    check(!BlueJohtoMahogany.whirlpool_allowed?(true), "Decades Whirlpool leak")
    check(Marshal.dump(state) == previous, "Decades state was mutated")
    state["current"] = "KANTO"
    check(!BlueJohtoMahogany.route42, "Route42 operated in Kanto")
    check(!BlueJohtoMahogany.pryce, "Pryce operated in Kanto")
    check(!BlueJohtoMahogany.radio_takeover, "Radio takeover leaked into Kanto")
    check(!BlueJohtoMahogany.whirlpool_allowed?(true), "Johto Whirlpool in Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"].delete("MINERAL")
    check(!BlueJohtoMahogany.route42, "Mahogany open before Jasmine/MINERAL")
    check(!BlueJohtoMahogany.radio_takeover, "Radio arc before badges")
    check(BlueRegions.award(state, "JOHTO", "MINERAL"), "Cannot setup MINERAL")
    flags["ecruteak_visited"] = false
    check(!BlueJohtoMahogany.route42, "Route42 without Ecruteak")
    flags["ecruteak_visited"] = true
    check(BlueJohtoMahogany.route42, "Route42 unavailable")
    check(!BlueJohtoMahogany.route42, "Route42 duplicated")
    check(BlueJohtoMahogany.mahogany_arrive, "Mahogany unavailable")
    check(!BlueJohtoMahogany.mahogany_arrive, "Mahogany duplicated")
    check(BlueJohtoMahogany.route43, "Route43 unavailable")
    check(BlueJohtoMahogany.lake_arrive, "Lake unavailable")
    check(!BlueJohtoMahogany.red_gyarados_begin, "Gyarados without map marker")
    File.write(BlueJohtoMahogany::LAKE_READY, "BAD")
    check(!BlueJohtoMahogany.red_gyarados_begin, "Bad lake marker")
    File.write(BlueJohtoMahogany::LAKE_READY,
               "BLUE_JOHTO_LAKE_V1_READY\n")
    check(!BlueJohtoMahogany.red_gyarados_result(:caught), "Result without battle")
    check(BlueJohtoMahogany.red_gyarados_begin, "Red Gyarados did not begin")
    check(!BlueJohtoMahogany.red_gyarados_begin, "Encounter began twice")
    check(!BlueJohtoMahogany.red_gyarados_result(:fled), "Flee counted as clear")
    check(!flags["lake_red_gyarados_resolved"], "Flee cleared Red Gyarados")
    check(!BlueJohtoMahogany.lance_meeting, "Lance appeared before battle")
    check(BlueJohtoMahogany.red_gyarados_begin, "Encounter not retryable after flee")
    check(BlueJohtoMahogany.red_gyarados_result(:caught), "Capture not recorded")
    check(!BlueJohtoMahogany.red_gyarados_result(:caught), "Duplicate result accepted")
    check(!BlueJohtoMahogany.red_gyarados_begin, "Captured Gyarados respawned")
    check(!flags.key?("lake_gyarados_added_to_party"),
          "Script faked a Pokemon capture")
    check(!BlueJohtoMahogany.red_scale, "Red Scale without approved item")
    File.write(BlueJohtoMahogany::SCALE_READY, "BLUE_JOHTO_RED_SCALE_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoMahogany.red_scale, "Red Scale marked granted on failure")
    $gift_ok = true
    check(BlueJohtoMahogany.red_scale, "Red Scale not granted")
    check(!BlueJohtoMahogany.red_scale, "Red Scale duplicated")
    check(BlueJohtoMahogany.lance_meeting, "Lance did not appear")
    check(!BlueJohtoMahogany.lance_meeting, "Lance met twice")
    check(BlueJohtoMahogany.rocket_hq_enter, "HQ not entered")
    check(!BlueJohtoMahogany.rocket_hq_enter, "HQ entered twice")
    check(!BlueJohtoMahogany.hq_grunt(1), "HQ grunt1 skipped grunt0")
    check(!BlueJohtoMahogany.hq_grunt(5), "Unknown HQ grunt accepted")
    check(!BlueJohtoMahogany.hq_grunt(0), "HQ battle without PBS marker")
    check(TrainerBattle.history.empty?, "Uncompiled Rocket battle launched")
    File.write(BlueJohtoMahogany::HQ_READY, "BLUE_JOHTO_ROCKET_HQ_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.hq_grunt(0), "HQ grunt loss marked win")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.hq_grunt(0), "HQ grunt0 not defeated")
    check(!BlueJohtoMahogany.hq_grunt(0), "HQ grunt0 duplicated")
    check(!BlueJohtoMahogany.hq_security_off, "HQ panel worked without map marker")
    File.write(BlueJohtoMahogany::HQ_PUZZLE_READY,
               "BLUE_JOHTO_ROCKET_HQ_PUZZLE_V1_READY\n")
    check(BlueJohtoMahogany.hq_security_off, "HQ panel not disabled")
    check(!BlueJohtoMahogany.hq_door, "HQ door opened before passwords")
    check(BlueJohtoMahogany.hq_grunt(1), "HQ grunt1 not defeated")
    check(BlueJohtoMahogany.hq_door, "HQ door not opened")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.hq_petrel, "Petrel loss advanced HQ")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.hq_petrel, "HQ Petrel win not recorded")
    check(BlueJohtoMahogany.hq_lance_help, "Lance assistance missing")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.hq_ariana, "Ariana loss advanced HQ")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.hq_ariana, "Ariana win not recorded")
    check(!BlueJohtoMahogany.hq_finish, "HQ cleared before Electrodes")
    check(!BlueJohtoMahogany.hq_electrode_begin(0),
          "Electrode began without audited adapter")
    File.write(BlueJohtoMahogany::ELECTRODE_READY,
               "BLUE_JOHTO_ELECTRODE_V1_READY\n")
    check(BlueJohtoMahogany.hq_electrode_begin(0), "Electrode0 did not start")
    check(!BlueJohtoMahogany.hq_electrode_begin(1), "Two simultaneous encounters")
    check(!BlueJohtoMahogany.hq_electrode_result(1, :caught),
          "Wrong Electrode slot resolved")
    check(!BlueJohtoMahogany.hq_electrode_result(0, :fled),
          "Flee resolved Electrode")
    check(BlueJohtoMahogany.hq_electrode_begin(0), "Fled Electrode did not retry")
    check(BlueJohtoMahogany.hq_electrode_result(0, :defeated),
          "Electrode0 defeat not recorded")
    check(!BlueJohtoMahogany.hq_electrode_begin(0), "Electrode0 respawned")
    check(BlueJohtoMahogany.hq_electrode_begin(1), "Electrode1 did not start")
    check(BlueJohtoMahogany.hq_electrode_result(1, :caught),
          "Electrode1 capture not recorded")
    check(BlueJohtoMahogany.hq_electrode_begin(2), "Electrode2 did not start")
    check(BlueJohtoMahogany.hq_electrode_result(2, :defeated),
          "Electrode2 defeat not recorded")
    check(!BlueJohtoMahogany.hq_finish, "HQ finished before Lance's 3 Electrodes")
    check(BlueJohtoMahogany.hq_lance_electrodes, "Lance did not disable electrodes")
    check(BlueJohtoMahogany.hq_finish, "HQ not cleared")
    check(!BlueJohtoMahogany.hq_finish, "HQ cleared twice")
    check(!BlueJohtoMahogany.hq_grunt(0), "Rockets respawned after HQ")
    check(!BlueJohtoMahogany.whirlpool_reward, "Whirlpool given without marker")
    File.write(BlueJohtoMahogany::WHIRLPOOL_READY,
               "BLUE_JOHTO_WHIRLPOOL_ITEM_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoMahogany.whirlpool_reward, "Failed HM delivery advanced state")
    $gift_ok = true
    check(BlueJohtoMahogany.whirlpool_reward, "HM Whirlpool not granted")
    check(!BlueJohtoMahogany.whirlpool_reward, "HM Whirlpool duplicated")
    check($items == [:REDSCALE, :HM06], "Item list incorrect or doubled")

    check(!BlueJohtoMahogany.whirlpool_allowed?(true), "Whirlpool before GLACIER")
    check(!BlueJohtoMahogany.pryce_ice_puzzle, "Ice puzzle without marker")
    File.write(BlueJohtoMahogany::ICE_PUZZLE_READY,
               "BLUE_JOHTO_PRYCE_PUZZLE_V1_READY\n")
    check(BlueJohtoMahogany.pryce_ice_puzzle, "Ice puzzle not recorded")
    check(!BlueJohtoMahogany.pryce_ice_puzzle, "Ice puzzle done twice")
    check(!BlueJohtoMahogany.pryce, "Pryce launched without PBS")
    File.write(BlueJohtoMahogany::PRYCE_READY, "BLUE_JOHTO_PRYCE_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.pryce, "Pryce loss recorded as win")
    check(!BlueJohtoMahogany.glacier_earned?, "GLACIER from loss")
    check(!BlueJohtoMahogany.radio_takeover, "Radio started after Pryce loss")
    check(BlueRegions.crystal_total(state, 3) == 9, "Wrong pre-GLACIER emerald count")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.pryce, "Pryce victory did not award GLACIER")
    check(BlueJohtoMahogany.glacier_earned?, "GLACIER missing")
    check(BlueRegions.local_achievements(state, "JOHTO") ==
          %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER],
          "Badge list incorrect")
    check(BlueRegions.crystal_total(state, 3) == 10, "GLACIER counted incorrectly")
    check(!BlueJohtoMahogany.whirlpool_allowed?, "Whirlpool bypassed tool")
    check(BlueJohtoMahogany.whirlpool_allowed?(true), "GLACIER+tool denied")
    history = TrainerBattle.history.dup
    check(!BlueJohtoMahogany.pryce, "Pryce replayed")
    check(TrainerBattle.history == history, "Duplicate Pryce battle")

    check(!BlueJohtoMahogany.route44, "Route44 before Radio Tower clearance")
    check(BlueJohtoMahogany.radio_takeover, "Goldenrod takeover did not begin")
    check(!BlueJohtoMahogany.radio_takeover, "Takeover began twice")
    check(!BlueJohtoMahogany.radio_petrel, "Radio battle without marker")
    File.write(BlueJohtoMahogany::RADIO_READY,
               "BLUE_JOHTO_RADIO_TOWER_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.radio_petrel, "Petrel loss advanced radio")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.radio_petrel, "Radio Petrel not defeated")
    check(!BlueJohtoMahogany.radio_underground_puzzle, "Puzzle before rival")
    check(!BlueJohtoMahogany.radio_director_rescue, "Director rescued too early")
    check(!BlueJohtoMahogany.radio_executive(0), "Executive before director")
    check(BlueJohtoMahogany.radio_rival, "Radio rival not defeated")
    check(TrainerBattle.history.last ==
          [:BLUE_JOHTO_RADIO_RIVAL, "Rival", 1], "Rival PBS version wrong")
    check(!BlueJohtoMahogany.radio_underground_puzzle,
          "Radio puzzle without map marker")
    File.write(BlueJohtoMahogany::RADIO_PUZZLE_READY,
               "BLUE_JOHTO_RADIO_PUZZLE_V1_READY\n")
    check(BlueJohtoMahogany.radio_underground_puzzle, "Underground puzzle missing")
    check(BlueJohtoMahogany.radio_director_rescue, "Director rescue missing")
    check(!BlueJohtoMahogany.radio_executive(1), "Executive1 skipped executive0")
    check(!BlueJohtoMahogany.radio_executive(7), "Invalid radio executive")
    TrainerBattle.result = false
    check(!BlueJohtoMahogany.radio_executive(0), "Radio loss counted as win")
    TrainerBattle.result = true
    check(BlueJohtoMahogany.radio_executive(0), "Proton not defeated")
    check(BlueJohtoMahogany.radio_executive(1), "Ariana not defeated")
    check(!BlueJohtoMahogany.radio_finish, "Radio cleared before Archer")
    check(BlueJohtoMahogany.radio_executive(2), "Archer not defeated")
    check(BlueJohtoMahogany.radio_finish, "Radio Tower not cleared")
    check(!BlueJohtoMahogany.radio_finish, "Radio Tower cleared twice")
    check(!BlueJohtoMahogany.radio_executive(2), "Archer repeated")
    check(BlueJohtoMahogany.route44, "Route44 not unlocked after Radio Tower")
    check(!BlueJohtoMahogany.route44, "Route44 marked twice")
    check(!flags.key?("lugia_caught"), "Radio story unlocked Lugia")

    snapshot = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(snapshot)
    check(BlueJohtoMahogany.glacier_earned?, "GLACIER missing on reload")
    check(!BlueJohtoMahogany.pryce, "Pryce replayed on reload")
    check(!BlueJohtoMahogany.red_scale, "Red Scale duplicated on reload")
    check(!BlueJohtoMahogany.whirlpool_reward, "Whirlpool item duplicated on reload")
    check(!BlueJohtoMahogany.hq_finish, "HQ cleared again on reload")
    check(!BlueJohtoMahogany.radio_finish, "Radio cleared again on reload")
    check(!BlueJohtoMahogany.route44, "Route44 repeated on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    snapshot = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoMahogany.glacier_earned?, "Johto GLACIER exposed in Kanto")
    check(!BlueJohtoMahogany.route44, "Route44 usable in Kanto")
    check(!BlueJohtoMahogany.pryce, "Pryce playable in Kanto")
    check(!BlueJohtoMahogany.whirlpool_allowed?(true), "Whirlpool used in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == snapshot,
          "Kanto save modified by Johto")
  end
end
puts "JOHTO_MAHOGANY_RUNTIME_OK"
