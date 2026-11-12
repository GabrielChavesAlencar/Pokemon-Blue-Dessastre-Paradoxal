# Johto phase 08 Ruby regression without a game executable or RMXP data.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.award(state, region, key)
    return false unless region == "JOHTO" && state["current"] == "JOHTO"
    return false unless %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].include?(key)
    badges = (state["achievements"] ||= {})[region] ||= []
    return false if badges.include?(key)
    badges << key
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").length
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO" && action == "SURF"
    return :badge unless local_achievements(state, "JOHTO").include?("FOG")
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
      item == :HM03
    end
  end
end
$messages = []
$items = []
$give_item = true

def _INTL(str, *args)
  args.each_with_index { |val, i| str = str.gsub("{#{i + 1}}", val.to_s) }
  str
end

def pbMessage(message, *args)
  $messages << message
end

def pbReceiveItem(item)
  return false unless $give_item
  $items << item
  true
end

def check(ok, message)
  raise message unless ok
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("johto-phase08-test-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {"starter"=>"CYNDAQUIL", "rival_fought"=>true, "ilex_passed"=>true,
             "azalea_rival_defeated"=>true, "goldenrod_plain_claimed"=>true}
    state = {"version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
             "achievements"=>{"JOHTO"=>["ZEPHYR","HIVE","PLAIN"]}, "johto_pilot"=>flags}
    $PokemonGlobal.blue_regions = state
    original = Marshal.dump(state)
    check(!BlueJohtoEcruteak.route35, "route35 leaked into Decades")
    check(!BlueJohtoEcruteak.national_park, "National Park leaked into Decades")
    check(!BlueJohtoEcruteak.route36, "route36 leaked into Decades")
    check(!BlueJohtoEcruteak.route37, "route37 leaked into Decades")
    check(!BlueJohtoEcruteak.ecruteak_arrive, "Ecruteak leaked into Decades")
    check(!BlueJohtoEcruteak.burned_tower, "tower leaked into Decades")
    check(!BlueJohtoEcruteak.tower_rival, "rival leaked into Decades")
    check(!BlueJohtoEcruteak.legendary_awakening, "beasts leaked into Decades")
    check(!BlueJohtoEcruteak.dance_theater_rocket, "dance leaked into Decades")
    check(!BlueJohtoEcruteak.surf_reward, "reward leaked into Decades")
    check(!BlueJohtoEcruteak.morty, "Morty leaked into Decades")
    check(!BlueJohtoEcruteak.surf_allowed?(true), "Surf leaked into Decades")
    check(Marshal.dump(state) == original, "Decades save changed")
    state["current"] = "KANTO"
    check(!BlueJohtoEcruteak.morty, "Morty battle leaked into Kanto")
    check(!BlueJohtoEcruteak.surf_allowed?(true), "Surf leaked into Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"] = ["ZEPHYR", "HIVE"]
    check(!BlueJohtoEcruteak.route35, "Route35 before Plain")
    check(!BlueJohtoEcruteak.route36, "Route36 before Plain")
    check(!BlueJohtoEcruteak.morty, "Morty before Plain")
    state["achievements"]["JOHTO"] << "PLAIN"
    flags["ilex_passed"] = false
    check(!BlueJohtoEcruteak.route35, "Route35 before Ilex")
    flags["ilex_passed"] = true
    check(BlueJohtoEcruteak.route35, "Route35 not visited")
    check(!BlueJohtoEcruteak.route35, "Route35 duplicated")
    check(BlueJohtoEcruteak.national_park, "National Park missed")
    check(!BlueJohtoEcruteak.national_park, "National Park duplicated")
    check(!flags.key?("national_park_competition_won"), "Fake contest event")
    check(!BlueJohtoEcruteak.route36, "Sudowoodo required")
    flags["goldenrod_squirtbottle_received"] = true
    check(!BlueJohtoEcruteak.route36, "Sudowoodo not actually cleared")
    flags["route36_sudowoodo_cleared"] = true
    check(BlueJohtoEcruteak.route36, "Route36 did not unlock")
    check(!BlueJohtoEcruteak.route36, "Route36 unlocked twice")
    check(BlueJohtoEcruteak.route37, "Route37 missing")
    check(!BlueJohtoEcruteak.route37, "Route37 duplicated")
    check(BlueJohtoEcruteak.ecruteak_arrive, "Ecruteak arrival missing")
    check(!BlueJohtoEcruteak.ecruteak_arrive, "Ecruteak repeated")
    check(!BlueJohtoEcruteak.legendary_awakening, "Beasts before tower")
    check(!BlueJohtoEcruteak.morty, "Gym before tower")
    check(BlueJohtoEcruteak.burned_tower, "Burned Tower not entered")
    check(!BlueJohtoEcruteak.burned_tower, "Burned Tower entered twice")
    check(!BlueJohtoEcruteak.tower_rival, "Rival without compiled PBS")
    check(!BlueJohtoEcruteak.legendary_awakening, "Beasts before rival victory")
    check(!BlueJohtoEcruteak.morty, "Morty before beast awakening")
    File.write(BlueJohtoEcruteak::READY_FILE, "BAD")
    check(!BlueJohtoEcruteak.tower_rival, "Invalid PBS marker")
    File.write(BlueJohtoEcruteak::READY_FILE, "BLUE_JOHTO_ECRUTEAK_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoEcruteak.tower_rival, "Rival defeat marked won")
    check(!BlueJohtoEcruteak.legendary_awakening, "Beasts after rival defeat")
    TrainerBattle.result = true
    check(BlueJohtoEcruteak.tower_rival, "Rival victory not recorded")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_BURNED_TOWER_RIVAL,"Rival",1],
          "Wrong starter rival version")
    check(!BlueJohtoEcruteak.tower_rival, "Rival battle repeated")
    check(BlueJohtoEcruteak.legendary_awakening, "Beasts not awakened")
    check(!BlueJohtoEcruteak.legendary_awakening, "Beasts awakened twice")
    check(!flags.key?("raikou_caught"), "Beasts were incorrectly captured")

    TrainerBattle.result = false
    check(!BlueJohtoEcruteak.morty, "Morty defeat counted")
    check(!BlueJohtoEcruteak.fog_earned?, "FOG given for defeat")
    check(!BlueJohtoEcruteak.surf_allowed?(true), "Surf without FOG")
    check(!BlueJohtoEcruteak.dance_theater_rocket, "Rocket defeat counted")
    check(!BlueJohtoEcruteak.surf_reward, "Surf HM before Rocket victory")
    TrainerBattle.result = true
    check(BlueJohtoEcruteak.dance_theater_rocket, "Dance Rocket not defeated")
    check(!BlueJohtoEcruteak.dance_theater_rocket, "Dance Rocket repeated")
    check(!BlueJohtoEcruteak.surf_reward, "Surf HM without approved item marker")
    check($items.empty?, "Ungrounded Surf HM in inventory")
    File.write(BlueJohtoEcruteak::SURF_REWARD_FILE, "WRONG")
    check(!BlueJohtoEcruteak.surf_reward, "Unapproved Surf marker accepted")
    File.write(BlueJohtoEcruteak::SURF_REWARD_FILE, "BLUE_JOHTO_ECRUTEAK_SURF_V1_READY\n")
    $give_item = false
    check(!BlueJohtoEcruteak.surf_reward, "Failed item delivery advanced state")
    check(!flags["ecruteak_surf_rewarded"], "Failed item delivery changed flags")
    $give_item = true
    check(BlueJohtoEcruteak.surf_reward, "Surf HM was not awarded")
    check($items == [:HM03], "Wrong Surf item delivered")
    check(!BlueJohtoEcruteak.surf_reward, "Surf HM duplicated")
    check(!BlueJohtoEcruteak.surf_allowed?(true), "Surf without badge")

    check(BlueJohtoEcruteak.morty, "Morty victory not recorded")
    check(BlueJohtoEcruteak.fog_earned?, "FOG missing after Morty")
    check(BlueRegions.local_achievements(state,"JOHTO") == %w[ZEPHYR HIVE PLAIN FOG],
          "Wrong local Johto badges")
    check(BlueRegions.crystal_total(state, 5) == 9, "FOG emerald total incorrect")
    check(!BlueJohtoEcruteak.surf_allowed?, "Surf did not require the tool")
    check(BlueJohtoEcruteak.surf_allowed?(true), "FOG plus tool did not enable Surf")
    history = TrainerBattle.history.dup
    check(!BlueJohtoEcruteak.morty, "Morty replayed")
    check(TrainerBattle.history == history, "Morty battle repeated")
    check(BlueRegions.crystal_total(state, 5) == 9, "FOG duplicated global emeralds")

    persisted = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(persisted)
    check(BlueJohtoEcruteak.fog_earned?, "FOG lost on save/reload")
    check(!BlueJohtoEcruteak.morty, "FOG duplicated on reload")
    check(!BlueJohtoEcruteak.surf_reward, "Surf reward duplicated on reload")
    check(!BlueJohtoEcruteak.legendary_awakening, "Beasts repeated on reload")
    check(BlueJohtoEcruteak.surf_allowed?(true), "Surf permission lost on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    saved_kanto = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoEcruteak.fog_earned?, "Johto FOG shown in Kanto")
    check(!BlueJohtoEcruteak.surf_allowed?(true), "Johto Surf used in Kanto")
    check(!BlueJohtoEcruteak.surf_reward, "Surf reward leaked into Kanto")
    check(!BlueJohtoEcruteak.morty, "Morty battle leaked to Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == saved_kanto,
          "Kanto save changed after Johto methods")
  end
end
puts "JOHTO_ECRUTEAK_RUNTIME_OK"
