# Johto phase 06: pure Ruby regression, without game/ or original map assets.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  MILESTONES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.award(state, region, badge)
    return false unless state["current"] == "JOHTO" && region == "JOHTO"
    return false unless MILESTONES.include?(badge)
    list = (state["achievements"] ||= {})["JOHTO"] ||= []
    return false if list.include?(badge)
    list << badge
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").size
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless region == "JOHTO" && action == "CUT"
    return :badge unless local_achievements(state, "JOHTO").include?("HIVE")
    return :tool unless tool_ready
    :allowed
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
def _INTL(template, *args)
  args.each_with_index { |value, index| template = template.gsub("{#{index + 1}}", value.to_s) }
  template
end
$messages = []
def pbMessage(message, *args)
  $messages << message
end
def check(condition, explanation)
  raise explanation unless condition
end

require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)

Dir.mktmpdir("blue-johto-azalea-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    state = {"version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
             "achievements"=>{"JOHTO"=>["ZEPHYR"]},
             "johto_pilot"=>{"starter"=>"CYNDAQUIL", "rival_fought"=>true}}
    $PokemonGlobal.blue_regions = state
    saved_decades = Marshal.dump(state)
    check(!BlueJohtoAzalea.arrive, "Azalea event ran in Decades")
    check(!BlueJohtoAzalea.kurt, "Kurt event ran in Decades")
    check(!BlueJohtoAzalea.well_entrance, "Well event ran in Decades")
    check(!BlueJohtoAzalea.rocket_grunt(0), "Rocket event ran in Decades")
    check(!BlueJohtoAzalea.rocket_executive, "Executive ran in Decades")
    check(!BlueJohtoAzalea.bugsy, "Bugsy battle ran in Decades")
    check(!BlueJohtoAzalea.azalea_rival, "Rival ran in Decades")
    check(!BlueJohtoAzalea.cut_allowed?(true), "Johto CUT applied in Decades")
    check(Marshal.dump(state) == saved_decades, "Decades save was modified")
    state["current"] = "KANTO"
    check(!BlueJohtoAzalea.bugsy, "Bugsy ran in Kanto")
    check(!state["johto_pilot"].key?("azalea_visited"), "Azalea flag leaked into Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"] = []
    check(!BlueJohtoAzalea.arrive, "Arrived in Azalea before Zephyr")
    check(!BlueJohtoAzalea.kurt, "Kurt spoke before Zephyr")
    check(!BlueJohtoAzalea.bugsy, "Bugsy fought before Zephyr")
    check(!BlueJohtoAzalea.rocket_grunt(0), "Rockets fought before Zephyr")
    check(!BlueJohtoAzalea.cut_allowed?(true), "CUT allowed before Hive")
    check(BlueRegions.award(state, "JOHTO", "ZEPHYR"), "Cannot setup prior gym badge")

    check(BlueJohtoAzalea.arrive, "Azalea arrival not recorded")
    check(!BlueJohtoAzalea.arrive, "Azalea arrival repeated")
    check(!BlueJohtoAzalea.well_entrance, "Well started before speaking with Kurt")
    check(BlueJohtoAzalea.kurt, "First Kurt dialogue not recorded")
    check(!BlueJohtoAzalea.kurt, "Kurt first dialogue repeated")
    check(BlueJohtoAzalea.well_entrance, "Well quest did not start")
    check(!BlueJohtoAzalea.well_entrance, "Well entrance repeated")
    check(!BlueJohtoAzalea.rocket_grunt(1), "Second Rocket skipped first Rocket")
    check(!BlueJohtoAzalea.rocket_executive, "Executive allowed before grunts")
    check(!BlueJohtoAzalea.rocket_grunt(3), "Unknown Rocket PBS version accepted")
    check(!BlueJohtoAzalea.rocket_grunt("0"), "Noninteger Rocket version accepted")
    check(!BlueJohtoAzalea.bugsy, "Bugsy unlocked before saving Slowpoke")

    File.write(BlueJohtoAzalea::READY_FILE, "WRONG_PBS")
    check(!BlueJohtoAzalea.rocket_grunt(0), "Invalid trainer marker accepted")
    File.delete(BlueJohtoAzalea::READY_FILE)
    check(!BlueJohtoAzalea.rocket_grunt(0), "No trainer marker accepted")
    check(TrainerBattle.history.empty?, "An uncompiled battle was launched")
    File.write(BlueJohtoAzalea::READY_FILE, "BLUE_JOHTO_AZALEA_V1_READY\n")

    TrainerBattle.result = false
    check(!BlueJohtoAzalea.rocket_grunt(0), "Rocket defeat marked won")
    check(!BlueJohtoAzalea.rocket_executive, "Executive unlocked after lost grunt")
    check(!BlueJohtoAzalea.bugsy, "Gym unlocked after lost grunt")
    check(!BlueJohtoAzalea.cut_allowed?(true), "CUT before HIVE")
    check(BlueRegions.local_achievements(state, "JOHTO") == ["ZEPHYR"],
          "Defeat created a badge")

    TrainerBattle.result = true
    check(BlueJohtoAzalea.rocket_grunt(0), "First Rocket victory not recorded")
    check(!BlueJohtoAzalea.rocket_grunt(0), "First Rocket battle repeated")
    check(!BlueJohtoAzalea.rocket_executive, "Executive skipped second grunt")
    check(BlueJohtoAzalea.rocket_grunt(1), "Second Rocket victory not recorded")
    check(!BlueJohtoAzalea.rocket_grunt(1), "Second Rocket battle repeated")
    TrainerBattle.result = false
    check(!BlueJohtoAzalea.rocket_executive, "Losing to Proton cleared the Well")
    check(!BlueJohtoAzalea.bugsy, "Bugsy unlocked after losing to Proton")
    TrainerBattle.result = true
    check(BlueJohtoAzalea.rocket_executive, "Winning Proton did not save Slowpoke")
    check(!BlueJohtoAzalea.rocket_executive, "Proton replayed after rescue")
    check(state["johto_pilot"]["slowpoke_well_cleared"], "Well victory flag missing")
    check(BlueJohtoAzalea.kurt, "Kurt did not thank after rescue")
    check(!BlueJohtoAzalea.kurt, "Kurt thanked twice")
    check(!BlueJohtoAzalea.rocket_grunt(0), "Grunt respawned after Rocket clearance")
    check(BlueRegions.crystal_total(state, 4) == 5, "Rocket event created global emerald")

    TrainerBattle.result = false
    check(!BlueJohtoAzalea.bugsy, "Bugsy defeat awarded badge")
    check(!BlueJohtoAzalea.hive_earned?, "HIVE awarded on loss")
    check(!BlueJohtoAzalea.cut_allowed?(true), "CUT enabled after loss")
    check(!BlueJohtoAzalea.azalea_rival, "Rival appeared without Hive")
    check(BlueRegions.crystal_total(state, 4) == 5, "Bugsy loss created emerald")

    TrainerBattle.result = true
    check(BlueJohtoAzalea.bugsy, "Winning Bugsy did not award Hive")
    check(BlueJohtoAzalea.hive_earned?, "Hive missing after victory")
    check(BlueRegions.local_achievements(state, "JOHTO") == ["ZEPHYR", "HIVE"],
          "Hive duplicated or saved in wrong order/region")
    check(BlueRegions.crystal_total(state, 4) == 6, "Hive counted incorrectly as emerald")
    check(!BlueJohtoAzalea.cut_allowed?, "CUT bypassed tool requirement")
    check(BlueJohtoAzalea.cut_allowed?(true), "Hive and tool did not authorize CUT")

    count = TrainerBattle.history.length
    check(!BlueJohtoAzalea.bugsy, "Duplicate Bugsy battle allowed")
    check(TrainerBattle.history.length == count, "Bugsy was fought twice")
    check(BlueRegions.crystal_total(state, 4) == 6, "Duplicate Hive increased emeralds")
    check(BlueJohtoAzalea.azalea_rival, "Ilex entrance rival victory missing")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_AZALEA_RIVAL, "Rival", 1],
          "Azalea rival chose wrong PBS version for Cyndaquil")
    check(!BlueJohtoAzalea.azalea_rival, "Azalea rival repeated")

    before_reload = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(before_reload)
    check(BlueJohtoAzalea.hive_earned?, "Hive badge disappeared after save reload")
    check(!BlueJohtoAzalea.bugsy, "Bugsy repeated after save reload")
    check(!BlueJohtoAzalea.rocket_executive, "Rocket cleared state vanished after reload")
    check(!BlueJohtoAzalea.azalea_rival, "Rival flags lost on reload")
    check(BlueJohtoAzalea.cut_allowed?(true), "CUT privilege lost on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    check(!BlueJohtoAzalea.hive_earned?, "Johto badge shown while in Kanto")
    check(!BlueJohtoAzalea.cut_allowed?(true), "Kanto got Johto CUT ability")
    check(!BlueJohtoAzalea.bugsy, "Bugsy ran after returning to Kanto")
    check(BlueRegions.crystal_total($PokemonGlobal.blue_regions, 4) == 6,
          "Regional travel erased the global badge count")
  end
end
puts "JOHTO_AZALEA_RUNTIME_OK"
