# Real Ruby regression for phase 05 battle and badge rules.
# All state is local; no Game.exe, source assets, ROM or existing save files.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.award(state, region, badge)
    return false unless region == "JOHTO" && state["current"] == region
    return false unless state["initial"] == "JOHTO"
    return false unless badge == "ZEPHYR"
    list = (state["achievements"] ||= {})[region] ||= []
    return false if list.include?(badge)
    list << badge
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").size
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless region == "JOHTO" && action == "ROCK_SMASH"
    return :badge unless local_achievements(state, region).include?("ZEPHYR")
    return :tool unless tool_ready
    :allowed
  end
end

module BlueStory
  class << self
    attr_accessor :stage
  end
end

module TrainerBattle
  class << self
    attr_accessor :result
    def history
      @history ||= []
    end
    def start(*params)
      history << params
      @result
    end
  end
end
def _INTL(string, *values)
  values.each_with_index { |v, i| string = string.gsub("{#{i + 1}}", v.to_s) }
  string
end
$messages = []
def pbMessage(string, *args)
  $messages << string
end
def check(value, message)
  raise message unless value
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("blue-johto-violet-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    initial = {"version"=>1, "initial"=>"DECADES", "current"=>"DECADES",
               "achievements"=>{}, "johto_pilot"=>{"starter"=>"CHIKORITA",
                                                    "rival_fought"=>true}}
    $PokemonGlobal.blue_regions = initial
    before = Marshal.dump(initial)
    check(!BlueJohtoViolet.violet_intro, "Violet visit in Decades should be blocked")
    check(!BlueJohtoViolet.sprout_elder, "Elder battle in Decades should be blocked")
    check(!BlueJohtoViolet.falkner, "Falkner battle in Decades should be blocked")
    check(!BlueJohtoViolet.rock_smash_allowed?, "Decades field permission mutated")
    check(Marshal.dump(initial) == before, "Decades state was mutated")
    initial["current"] = "KANTO"
    check(!BlueJohtoViolet.falkner, "Falkner is accessible in Kanto")
    check(initial["achievements"].empty?, "Kanto badges mutated")

    initial["current"] = "JOHTO"
    initial["initial"] = "JOHTO"
    check(BlueJohtoViolet.violet_intro, "First Violet visit not recorded")
    check(!BlueJohtoViolet.violet_intro, "Violet visit repeated")
    initial["johto_pilot"].delete("starter")
    check(!BlueJohtoViolet.falkner, "Gym accepted a missing starter")
    initial["johto_pilot"]["starter"] = "CHIKORITA"
    initial["johto_pilot"]["rival_fought"] = false
    check(!BlueJohtoViolet.falkner, "Gym accepted a missing rival tutorial")
    initial["johto_pilot"]["rival_fought"] = true
    check(!BlueJohtoViolet.sprout_elder, "Sprout battle started without compiled trainers")
    check(!BlueJohtoViolet.falkner, "Gym started without compiled trainers")
    check(!BlueJohtoViolet.rock_smash_allowed?, "Rock Smash enabled without Zephyr")
    check(initial["achievements"].empty?, "Badge awarded without battle")

    File.write(BlueJohtoViolet::READY_FILE, "NOT_READY")
    check(!BlueJohtoViolet.falkner, "Unverified Violet trainer marker accepted")
    File.write(BlueJohtoViolet::READY_FILE, "BLUE_JOHTO_VIOLET_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoViolet.falkner, "Badge awarded for defeat")
    check(!BlueJohtoViolet.sprout_elder, "Elder state awarded for defeat")
    check(initial["achievements"].empty?, "Defeat changed achievements")
    check(!initial["johto_pilot"]["violet_elder_defeated"], "Defeat advanced elder")
    check(!BlueJohtoViolet.rock_smash_allowed?, "Defeat unlocked Rock Smash")
    check(BlueRegions.crystal_total(initial, 3) == 3, "Loss created global emerald")

    TrainerBattle.result = true
    BlueStory.stage = 3
    check(BlueJohtoViolet.trainer_version == 1, "Master must select four-Pokémon PBS v1")
    check(BlueJohtoViolet.sprout_sage(:JH_SPROUT_SAGE_NICO), "First Sprout sage not prepared")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_SAGE, "Nico", 1],
          "Master Sprout sage used wrong PBS team")
    check(!BlueJohtoViolet.sprout_sage(:JH_SPROUT_SAGE_NICO),
          "Sprout sage can battle twice on the same save")
    check(BlueJohtoViolet.sprout_sage(:JH_SPROUT_SAGE_TROY), "Second Sprout sage missing")
    check(!BlueJohtoViolet.badge_earned?, "Sages incorrectly awarded Zephyr")
    check(!BlueJohtoViolet.center_clerk, "Unfinished Center should not claim healing")
    BlueStory.stage = 0
    check(BlueJohtoViolet.sprout_elder, "Elder win not recorded")
    check(!BlueJohtoViolet.sprout_elder, "Elder battle repeated")
    check(!BlueJohtoViolet.badge_earned?, "Elder win awarded gym badge")
    BlueStory.stage = 3
    check(BlueJohtoViolet.falkner, "Falkner victory not recorded")
    check(TrainerBattle.history.last == [:BLUE_JOHTO_FALKNER, "Falkner", 1],
          "Falkner did not use Master four-Pokémon PBS v1")
    BlueStory.stage = 0
    check(BlueJohtoViolet.badge_earned?, "Zephyr badge not awarded")
    check(BlueRegions.crystal_total(initial, 3) == 4, "Zephyr changed emeralds incorrectly")
    check(BlueJohtoViolet.rock_smash_allowed?, "Zephyr did not enable local Rock Smash")
    check(BlueRegions.local_achievements(initial, "JOHTO") == ["ZEPHYR"],
          "Badge duplicated or stored under wrong region")
    history = TrainerBattle.history.dup
    check(!BlueJohtoViolet.falkner, "Falkner repeats after victory")
    check(TrainerBattle.history == history, "Repeated gym battle")
    check(BlueRegions.crystal_total(initial, 3) == 4, "Repeated gym duplicated emerald")

    persisted = Marshal.dump(initial)
    $PokemonGlobal.blue_regions = Marshal.load(persisted)
    check(BlueJohtoViolet.badge_earned?, "Badge lost on save/reload")
    check(!BlueJohtoViolet.falkner, "Save/reload allowed duplicate reward")
    check(BlueJohtoViolet.rock_smash_allowed?, "Field badge lost on reload")

    $PokemonGlobal.blue_regions["current"] = "KANTO"
    check(!BlueJohtoViolet.badge_earned?, "Kanto is using Johto gym badge UI")
    check(!BlueJohtoViolet.rock_smash_allowed?, "Kanto is using Johto field badge")
    check(!BlueJohtoViolet.falkner, "Kanto used Johto trainer after travel")
    check(BlueRegions.crystal_total($PokemonGlobal.blue_regions, 3) == 4,
          "Changing region erased global total")
  end
end
puts "JOHTO_VIOLET_RUNTIME_OK"
