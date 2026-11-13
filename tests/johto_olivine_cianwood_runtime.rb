# Phase 09 runtime logic regression. No real maps, executables, music or saves.
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
    return false unless region == "JOHTO" && state["current"] == "JOHTO"
    return false unless BADGES.include?(badge)
    list = (state["achievements"] ||= {})["JOHTO"] ||= []
    return false if list.include?(badge)
    list << badge
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").length
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless region == "JOHTO" && state["current"] == "JOHTO"
    badge = {"SURF"=>"FOG", "FLY"=>"STORM"}[action]
    return :unavailable unless badge
    return :badge unless local_achievements(state, "JOHTO").include?(badge)
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
      [:SECRETPOTION, :HM02].include?(item)
    end
  end
end

$messages = []
$items = []
$gift_ok = true
def _INTL(template, *values)
  values.each_with_index { |value, i| template = template.gsub("{#{i + 1}}", value.to_s) }
  template
end
def pbMessage(string, *args)
  $messages << string
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

Dir.mktmpdir("johto-olivine-cianwood-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {"starter"=>"CYNDAQUIL", "ecruteak_visited"=>true,
             "ecruteak_surf_rewarded"=>false, "ecruteak_morty_defeated"=>true}
    state = {
      "version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
      "achievements"=>{"JOHTO"=>["ZEPHYR", "HIVE", "PLAIN", "FOG"]},
      "johto_pilot"=>flags
    }
    $PokemonGlobal.blue_regions = state
    original = Marshal.dump(state)
    check(!BlueJohtoOlivineCianwood.route38, "Route 38 ran in Decades")
    check(!BlueJohtoOlivineCianwood.olivine_arrive, "Olivine ran in Decades")
    check(!BlueJohtoOlivineCianwood.lighthouse_entrance, "Lighthouse ran in Decades")
    check(!BlueJohtoOlivineCianwood.lighthouse_floor(1), "Lighthouse floor ran in Decades")
    check(!BlueJohtoOlivineCianwood.jasmine_request, "Jasmine ran in Decades")
    check(!BlueJohtoOlivineCianwood.route40(true), "Route 40 ran in Decades")
    check(!BlueJohtoOlivineCianwood.route41(true), "Route 41 ran in Decades")
    check(!BlueJohtoOlivineCianwood.cianwood_arrive, "Cianwood ran in Decades")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Pharmacy ran in Decades")
    check(!BlueJohtoOlivineCianwood.chuck_waterfall, "Gym switch ran in Decades")
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck ran in Decades")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Fly ran in Decades")
    check(!BlueJohtoOlivineCianwood.return_to_olivine(true), "Return ran in Decades")
    check(!BlueJohtoOlivineCianwood.fly_allowed?(true), "Fly allowed in Decades")
    check(Marshal.dump(state) == original, "Decades data mutated")
    state["current"] = "KANTO"
    check(!BlueJohtoOlivineCianwood.route38, "Route38 in Kanto")
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck in Kanto")
    check(!BlueJohtoOlivineCianwood.fly_allowed?(true), "Johto Fly in Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN"]
    check(!BlueJohtoOlivineCianwood.route38, "Route38 before FOG")
    check(!BlueJohtoOlivineCianwood.surf_allowed?(true), "Surf before FOG")
    check(!BlueJohtoOlivineCianwood.route40(true), "Route40 before FOG")
    check(BlueRegions.award(state, "JOHTO", "FOG"), "Cannot set prerequisite FOG")
    flags["ecruteak_visited"] = false
    check(!BlueJohtoOlivineCianwood.route38, "Route38 before Ecruteak visit")
    flags["ecruteak_visited"] = true
    check(BlueJohtoOlivineCianwood.route38, "Route38 missing")
    check(!BlueJohtoOlivineCianwood.route38, "Route38 duplicated")
    check(BlueJohtoOlivineCianwood.route39, "Route39 missing")
    check(!BlueJohtoOlivineCianwood.route39, "Route39 duplicated")
    check(BlueJohtoOlivineCianwood.olivine_arrive, "Olivine arrival missing")
    check(!BlueJohtoOlivineCianwood.olivine_arrive, "Olivine arrival duplicated")

    check(!BlueJohtoOlivineCianwood.route40(true), "Sailing without Surf HM")
    flags["ecruteak_surf_rewarded"] = true
    check(!BlueJohtoOlivineCianwood.route40, "Sailing without Surf tool")
    check(!BlueJohtoOlivineCianwood.route41(true), "Route41 before Route40")
    check(BlueJohtoOlivineCianwood.route40(true), "Route40 did not start")
    check(!BlueJohtoOlivineCianwood.route40(true), "Route40 repeated")
    check(!BlueJohtoOlivineCianwood.route41, "Route41 bypassed Surf tool")
    check(BlueJohtoOlivineCianwood.route41(true), "Route41 missing")
    check(!BlueJohtoOlivineCianwood.route41(true), "Route41 repeated")
    check(BlueJohtoOlivineCianwood.cianwood_arrive, "Cianwood missing")
    check(!BlueJohtoOlivineCianwood.cianwood_arrive, "Cianwood repeated")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Medicine given without Jasmine request")
    check(!BlueJohtoOlivineCianwood.return_to_olivine(true), "Return without medicine")

    check(!BlueJohtoOlivineCianwood.chuck, "Chuck before waterfall switch")
    check(BlueJohtoOlivineCianwood.chuck_waterfall, "Chuck waterfall did not stop")
    check(!BlueJohtoOlivineCianwood.chuck_waterfall, "Gym waterfall toggled twice")
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck without compiled PBS")
    check(TrainerBattle.history.empty?, "No-marker Chuck battle occurred")
    File.write(BlueJohtoOlivineCianwood::TRAINERS_READY, "WRONG")
    check(!BlueJohtoOlivineCianwood.chuck, "Wrong gym marker allowed")
    File.write(BlueJohtoOlivineCianwood::TRAINERS_READY,
               "BLUE_JOHTO_CIANWOOD_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoOlivineCianwood.chuck, "Lost Chuck battle awarded STORM")
    check(!BlueJohtoOlivineCianwood.storm_earned?, "STORM earned on loss")
    check(!BlueJohtoOlivineCianwood.fly_allowed?(true), "Fly before STORM")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Fly reward before STORM")
    check(BlueRegions.crystal_total(state, 4) == 8, "Loss added emerald")
    TrainerBattle.result = true
    check(BlueJohtoOlivineCianwood.chuck, "Chuck win not recorded")
    check(BlueJohtoOlivineCianwood.storm_earned?, "STORM badge missing")
    check(BlueRegions.local_achievements(state, "JOHTO") ==
          %w[ZEPHYR HIVE PLAIN FOG STORM], "STORM badge in wrong list")
    check(BlueRegions.crystal_total(state, 4) == 9, "STORM emerald total incorrect")
    check(!BlueJohtoOlivineCianwood.fly_allowed?, "Fly tool prerequisite bypassed")
    check(BlueJohtoOlivineCianwood.fly_allowed?(true), "STORM + tool blocked Fly")
    battle_count = TrainerBattle.history.size
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck replayed after win")
    check(TrainerBattle.history.size == battle_count, "Chuck battle repeated")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Fly without marker")
    File.write(BlueJohtoOlivineCianwood::FLY_READY, "BAD")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Invalid Fly marker")
    File.write(BlueJohtoOlivineCianwood::FLY_READY, "BLUE_JOHTO_FLY_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Failed Fly gift advanced state")
    check(!flags["cianwood_fly_rewarded"], "Failed Fly persisted")
    $gift_ok = true
    check(BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Fly reward missing")
    check($items == [:HM02], "Fly reward incorrect")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward, "Fly given twice")

    check(!BlueJohtoOlivineCianwood.jasmine_request, "Jasmine without lighthouse")
    check(BlueJohtoOlivineCianwood.lighthouse_entrance, "Lighthouse entrance missing")
    check(!BlueJohtoOlivineCianwood.lighthouse_entrance, "Lighthouse entrance repeated")
    check(!BlueJohtoOlivineCianwood.lighthouse_floor(2), "Skipped lighthouse floor 1")
    check(!BlueJohtoOlivineCianwood.lighthouse_floor(0), "Invalid lighthouse floor zero")
    check(!BlueJohtoOlivineCianwood.lighthouse_floor(7), "Invalid lighthouse floor seven")
    (1..6).each do |level|
      check(BlueJohtoOlivineCianwood.lighthouse_floor(level),
            "Missing Lighthouse floor #{level}")
      check(!BlueJohtoOlivineCianwood.lighthouse_floor(level),
            "Lighthouse floor #{level} repeated")
    end
    check(BlueJohtoOlivineCianwood.jasmine_request, "Jasmine request not recorded")
    check(!BlueJohtoOlivineCianwood.jasmine_request, "Jasmine request duplicated")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Medicine without marker")
    check($items == [:HM02], "Unverified medicine delivered")
    File.write(BlueJohtoOlivineCianwood::MEDICINE_READY, "WRONG")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Invalid medicine marker")
    File.write(BlueJohtoOlivineCianwood::MEDICINE_READY, "BLUE_JOHTO_MEDICINE_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoOlivineCianwood.pharmacy, "Failed medicine delivery recorded")
    check(!flags["cianwood_medicine_received"], "Medicine flag recorded on failed grant")
    $gift_ok = true
    check(BlueJohtoOlivineCianwood.pharmacy, "Medicine not delivered")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Medicine duplicated")
    check($items == [:HM02, :SECRETPOTION], "Medicine item wrong or duplicated")
    check(!flags.key?("olivine_ampharos_healed"), "Phase 09 cured Ampharos prematurely")
    check(!flags.key?("olivine_jasmine_defeated"), "Phase 09 unlocked Jasmine prematurely")
    check(!BlueJohtoOlivineCianwood.return_to_olivine, "Return bypassed Surf tool")
    check(BlueJohtoOlivineCianwood.return_to_olivine(true), "Return with medicine failed")
    check(!BlueJohtoOlivineCianwood.return_to_olivine(true), "Return duplicated")
    check(!flags.key?("olivine_ampharos_healed"), "Return prematurely healed Ampharos")
    check(BlueRegions.crystal_total(state, 4) == 9, "Medicine created an emerald")

    stored = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(stored)
    check(BlueJohtoOlivineCianwood.storm_earned?, "STORM lost on save/reload")
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck replayed after save/reload")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Medicine repeated on save/reload")
    check(!BlueJohtoOlivineCianwood.chuck_wife_fly_reward,
          "Fly repeated on save/reload")
    check(!BlueJohtoOlivineCianwood.return_to_olivine(true), "Return repeated after reload")
    check(BlueJohtoOlivineCianwood.fly_allowed?(true), "Fly status lost on save/reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    kanto_before = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoOlivineCianwood.storm_earned?, "Johto STORM visible in Kanto")
    check(!BlueJohtoOlivineCianwood.fly_allowed?(true), "Johto Fly used in Kanto")
    check(!BlueJohtoOlivineCianwood.chuck, "Chuck usable in Kanto")
    check(!BlueJohtoOlivineCianwood.pharmacy, "Medicine event leaked in Kanto")
    check(!BlueJohtoOlivineCianwood.return_to_olivine(true),
          "Johto return event leaked in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == kanto_before,
          "Johto methods mutated Kanto")
  end
end
puts "JOHTO_OLIVINE_CIANWOOD_RUNTIME_OK"
