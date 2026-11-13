# Phase 14: isolated Johto legendary state tests (no native encounters/maps).
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.allow_specials?(state, region)
    local_achievements(state, region).length == 8
  end
  def self.field_access(state, region, action, tool_ready = false)
    return :unavailable unless region == "JOHTO" && state["current"] == "JOHTO"
    badge = {"SURF"=>"FOG", "WHIRLPOOL"=>"GLACIER"}[action]
    return :unavailable unless badge
    return :badge unless local_achievements(state, region).include?(badge)
    tool_ready ? :allowed : :tool
  end
end
module GameData
  module Species
    def self.exists?(species)
      [:RAIKOU, :ENTEI, :LUGIA, :HOOH, :SUICUNE].include?(species)
    end
  end
  module Item
    def self.exists?(item)
      [:RAINBOWWING, :SILVERWING, :CLEARBELL, :TIDALBELL].include?(item)
    end
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
class MockBag
  def initialize
    @items = {}
  end
  def quantity(item)
    @items.fetch(item, 0)
  end
  def add(item)
    @items[item] = quantity(item) + 1
  end
end
$bag = MockBag.new
$gift_success = true
$messages = []
def pbReceiveItem(item)
  return false unless $gift_success
  $bag.add(item)
  true
end
def _INTL(str, *args)
  args.each_with_index { |value, index| str = str.gsub("{#{index + 1}}", value.to_s) }
  str
end
def pbMessage(message, *args)
  $messages << message
end
def check(ok, message)
  raise message unless ok
end

require ARGV.fetch(0)
require ARGV.fetch(1)

Dir.mktmpdir("blue-johto-phase14-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    flags = {
      "starter"=>"CYNDAQUIL", "burned_tower_beasts_awakened"=>true,
      "ecruteak_visited"=>true, "route41_visited"=>true,
      "rocket_hq_whirlpool_received"=>true,
      "goldenrod_radio_tower_cleared"=>true
    }
    state = {"version"=>1,"initial"=>"JOHTO","current"=>"DECADES",
             "achievements"=>{"JOHTO"=>BlueRegions::BADGES.dup,
                                "KANTO"=>["BOULDER"]},
             "leagues"=>[],"johto_pilot"=>flags}
    $PokemonGlobal.blue_regions = state
    baseline = Marshal.dump(state)
    check(!BlueJohtoLegendaries.choose_version("HEARTGOLD"), "Variant leaked into Decades")
    check(!BlueJohtoLegendaries.register_roamer(:RAIKOU, :registered),
          "Raikou leaked into Decades")
    check(!BlueJohtoLegendaries.roamer_result(:ENTEI, :caught),
          "Entei leaked into Decades")
    check(!BlueJohtoLegendaries.kimono_girl(0), "Kimono ran in Decades")
    check(!BlueJohtoLegendaries.radio_wing_reward, "Wing in Decades")
    check(!BlueJohtoLegendaries.whirl_entrance("NE", true, true),
          "Island gate in Decades")
    check(!BlueJohtoLegendaries.bell_tower_enter, "Bell Tower in Decades")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH), "Ho-Oh in Decades")
    check(!BlueJohtoLegendaries.ruins_enter, "Ruins in Decades")
    check(!BlueJohtoLegendaries.eight_badges?, "Decades eight Johto badges")
    check(Marshal.dump(state) == baseline, "Decades state modified")
    state["current"] = "KANTO"
    check(!BlueJohtoLegendaries.choose_version("HEARTGOLD"), "Variant set in Kanto")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA), "Lugia event in Kanto")
    check(!BlueJohtoLegendaries.ruins_enter, "Ruins in Kanto")
    check(!BlueJohtoLegendaries.field_allowed?("SURF", true),
          "Johto Surf available in Kanto")
    state["current"] = "JOHTO"
    check(!BlueJohtoLegendaries.choose_version("HEARTGOLD"),
          "Variant selected without audit marker")
    File.write(BlueJohtoLegendaries::VERSION_READY, "BAD")
    check(!BlueJohtoLegendaries.choose_version("HEARTGOLD"), "Wrong variant marker")
    File.write(BlueJohtoLegendaries::VERSION_READY,
               "BLUE_JOHTO_VERSION_V1_READY\n")
    check(!BlueJohtoLegendaries.choose_version("GOLD"),
          "Unapproved version name accepted")
    check(BlueJohtoLegendaries.choose_version("HEARTGOLD"),
          "HeartGold version not recorded")
    check(BlueJohtoLegendaries.version == "HEARTGOLD", "Wrong version")
    check(!BlueJohtoLegendaries.choose_version("SOULSILVER"),
          "Version changed after selection")
    check(!BlueJohtoLegendaries.register_roamer(:SUICUNE, :registered),
          "Suicune incorrectly marked HGSS roamer")
    check(!BlueJohtoLegendaries.register_roamer(:RAIKOU, :registered),
          "Roamer registered without audited adapter")
    File.write(BlueJohtoLegendaries::ROAMER_READY,
               "BLUE_JOHTO_ROAMING_V1_READY\n")
    check(!BlueJohtoLegendaries.register_roamer(:RAIKOU, :fake),
          "Unverified roamer result accepted")
    check(BlueJohtoLegendaries.register_roamer(:RAIKOU, :registered),
          "Raikou roamer not registered")
    check(!BlueJohtoLegendaries.register_roamer(:RAIKOU, :registered),
          "Roamer duplicated")
    check(!BlueJohtoLegendaries.roamer_result(:RAIKOU, :fled),
          "Roamer escape marked caught")
    check(BlueJohtoLegendaries.roamer_result(:RAIKOU, :caught),
          "Raikou capture not recorded")
    check(!BlueJohtoLegendaries.roamer_result(:RAIKOU, :caught),
          "Raikou captured twice")
    check(!BlueJohtoLegendaries.reactivate_roamer(:RAIKOU, :rematch_recorded),
          "Captured Raikou reactivated")
    check(BlueJohtoLegendaries.register_roamer(:ENTEI, :registered),
          "Entei not registered")
    check(BlueJohtoLegendaries.roamer_result(:ENTEI, :defeated),
          "Entei defeat not recorded")
    check(!BlueJohtoLegendaries.reactivate_roamer(:ENTEI, :rematch_recorded),
          "Defeated Entei returned without Hall of Fame")
    check(!flags.key?("raikou_party_added"), "Roamer test fabricated Pokemon")

    check(!BlueJohtoLegendaries.radio_wing_reward,
          "Radio Wing without item adapter")
    File.write(BlueJohtoLegendaries::ITEM_READY,
               "BLUE_JOHTO_LEGENDARY_ITEMS_V1_READY\n")
    $gift_success = false
    check(!BlueJohtoLegendaries.radio_wing_reward,
          "Failed gift was registered")
    check(!flags["johto_radio_wing_received"], "Gift failure modified state")
    $gift_success = true
    check(BlueJohtoLegendaries.radio_wing_reward, "Rainbow Wing not given")
    check(!BlueJohtoLegendaries.radio_wing_reward, "Rainbow Wing duplicated")
    check($bag.quantity(:RAINBOWWING) == 1, "Rainbow Wing quantity not 1")
    check(!BlueJohtoLegendaries.kimono_girl(0),
          "Kimono battle without compiled trainer marker")
    File.write(BlueJohtoLegendaries::KIMONO_READY,
               "BLUE_JOHTO_KIMONO_V1_READY\n")
    check(!BlueJohtoLegendaries.kimono_girl(1), "Kimono order skipped first")
    TrainerBattle.result = false
    check(!BlueJohtoLegendaries.kimono_girl(0), "Kimono loss marked victory")
    check(!flags["johto_kimono_step"], "Kimono step advanced on loss")
    TrainerBattle.result = true
    5.times do |i|
      check(BlueJohtoLegendaries.kimono_girl(i), "Kimono girl #{i} not defeated")
      check(!BlueJohtoLegendaries.kimono_girl(i),
            "Kimono girl #{i} repeated in same sequence")
    end
    check(TrainerBattle.history.last ==
          [:BLUE_JOHTO_KIMONO_GIRL,"Kimono Girl",4],
          "Wrong Kimono trainer PBS version")
    check(!BlueJohtoLegendaries.kimono_girl(5), "Sixth Kimono accepted")
    check(BlueJohtoLegendaries.kimono_bell_reward, "Clear Bell not delivered")
    check(!BlueJohtoLegendaries.kimono_bell_reward, "Clear Bell duplicated")
    check($bag.quantity(:CLEARBELL) == 1, "Clear Bell quantity wrong")
    check(BlueJohtoLegendaries.kimono_ritual, "HGSS ritual missing")
    check(!BlueJohtoLegendaries.kimono_ritual, "Ritual duplicated")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH),
          "Ho-Oh started without real room/encounter markers")
    check(!BlueJohtoLegendaries.bell_tower_enter,
          "Bell Tower without map/exits markers")
    File.write(BlueJohtoLegendaries::BELL_READY,
               "BLUE_JOHTO_BELL_TOWER_V1_READY\n")
    check(!BlueJohtoLegendaries.bell_tower_enter,
          "Bell Tower before safe exits verified")
    File.write(BlueJohtoLegendaries::SAFE_EXIT_READY,
               "BLUE_JOHTO_LEGENDARY_EXITS_V1_READY\n")
    check(BlueJohtoLegendaries.bell_tower_enter, "Bell Tower not entered")
    check(BlueJohtoLegendaries.bell_tower_roof, "Bell Tower roof not reached")
    File.write(BlueJohtoLegendaries::ENCOUNTER_READY,
               "BLUE_JOHTO_LEGENDARY_BATTLES_V1_READY\n")
    check(BlueJohtoLegendaries.legendary_begin(:HOOH), "Ho-Oh not started")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Second legendary began during Ho-Oh")
    check(!BlueJohtoLegendaries.legendary_result(:LUGIA, :caught),
          "Wrong species result accepted")
    check(!BlueJohtoLegendaries.legendary_result(:HOOH, :fled),
          "Ho-Oh escape marked done")
    check(BlueJohtoLegendaries.legendary_begin(:HOOH),
          "Ho-Oh retry after flee failed")
    check(BlueJohtoLegendaries.legendary_result(:HOOH, :caught),
          "Ho-Oh capture not recorded")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH),
          "Captured Ho-Oh respawned")
    check(!BlueJohtoLegendaries.legendary_rematch_reset(:HOOH, :rematch_recorded),
          "Captured Ho-Oh revived")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Secondary Lugia available before League")

    check(!BlueJohtoLegendaries.whirl_entrance("INVALID",true,true),
          "Unknown Whirl Island entrance")
    check(!BlueJohtoLegendaries.whirl_entrance("NE", true, true),
          "Island without verified map marker")
    File.write(BlueJohtoLegendaries::WHIRL_READY,
               "BLUE_JOHTO_WHIRL_ISLANDS_V1_READY\n")
    check(!BlueJohtoLegendaries.whirl_entrance("NE",true,false),
          "Whirlpool tool bypassed")
    check(!BlueJohtoLegendaries.whirl_entrance("NE",false,true),
          "Surf tool bypassed")
    check(BlueJohtoLegendaries.whirl_entrance("NE",true,true),
          "Whirl Island NE not entered")
    check(!BlueJohtoLegendaries.whirl_entrance("SW",true,true),
          "Changed Whirl Island in same visit")
    check(BlueJohtoLegendaries.whirl_chamber, "Whirl Island chamber not reached")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Secondary legendary available without League")
    state["leagues"] << "JOHTO"
    check(!BlueJohtoLegendaries.reactivate_roamer(:ENTEI, :fake),
          "Fake Hall of Fame reactivated Entei")
    check(BlueJohtoLegendaries.reactivate_roamer(:ENTEI, :rematch_recorded),
          "Verified rematch did not reactivate Entei")
    check(!BlueJohtoLegendaries.reactivate_roamer(:RAIKOU, :rematch_recorded),
          "Caught Raikou reactivated after League")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Lugia appeared without Silver Wing")
    $bag.add(:SILVERWING) # Future separately audited Pewter NPC reward.
    check(BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Postgame Lugia unavailable with verified prerequisite state")
    check(BlueJohtoLegendaries.legendary_result(:LUGIA, :defeated),
          "Lugia defeat not recorded")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Defeated Lugia respawned before rematch")
    check(!BlueJohtoLegendaries.legendary_rematch_reset(:LUGIA, :fake),
          "Lugia revived without verified Hall of Fame rematch")
    check(BlueJohtoLegendaries.legendary_rematch_reset(:LUGIA, :rematch_recorded),
          "Lugia did not reset after confirmed rematch")
    check(BlueJohtoLegendaries.legendary_begin(:LUGIA), "Lugia retry not available")
    check(BlueJohtoLegendaries.legendary_result(:LUGIA, :caught),
          "Postgame Lugia catch not recorded")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA), "Lugia duplicated")
    check(BlueJohtoLegendaries.whirl_exit, "Island exit did not clear travel checkpoint")
    check(!BlueJohtoLegendaries.whirl_exit, "Island exit repeated without entrance")
    check(BlueJohtoLegendaries.whirl_entrance("SW", true, true),
          "Safe return did not permit another island entrance")
    check(BlueJohtoLegendaries.whirl_chamber,
          "Alternate island entrance could not reach audited chamber")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "Captured Lugia reappeared after returning through another island")
    check(!BlueJohtoLegendaries.hgss_suicune_route25,
          "Uninstalled Kanto Route25 Suicune event allowed")

    check(!BlueJohtoLegendaries.ruins_enter, "Ruins without source map marker")
    File.write(BlueJohtoLegendaries::RUINS_READY,
               "BLUE_JOHTO_RUINS_V1_READY\n")
    check(BlueJohtoLegendaries.ruins_enter, "Ruins not entered")
    check(!BlueJohtoLegendaries.unown_research_ready?,
          "Unown research ready without puzzle")
    check(!BlueJohtoLegendaries.ruins_puzzle(5), "Unknown Unown puzzle allowed")
    check(!BlueJohtoLegendaries.ruins_puzzle(1.0),
          "Non-integer puzzle number accepted")
    flags["johto_ruins_puzzles"] = "corrupted"
    check(!BlueJohtoLegendaries.unown_research_ready?,
          "Corrupted save incorrectly enabled Unown research")
    check(!BlueJohtoLegendaries.ruins_puzzle(0),
          "Corrupted save allowed ruins mutation")
    flags.delete("johto_ruins_puzzles")
    [2, 0, 3, 1].each do |i|
      check(BlueJohtoLegendaries.ruins_puzzle(i), "Ruins puzzle #{i} failed")
      check(!BlueJohtoLegendaries.ruins_puzzle(i), "Ruins puzzle #{i} repeated")
    end
    check(BlueJohtoLegendaries.unown_research_ready?,
          "Unown notes not enabled after puzzle")
    check(!BlueJohtoLegendaries.bug_contest, "Fake Bug Catching Contest")
    check(!BlueJohtoLegendaries.pokeathlon, "Fake Pokeathlon")
    check(!BlueJohtoLegendaries.mt_silver, "Mt. Silver opened without map")
    check(!BlueJohtoLegendaries.red_battle, "Red available without real map/team")
    check(!flags.key?("red_defeated"), "Red completion fabricated")

    saved = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(saved)
    check(BlueJohtoLegendaries.version == "HEARTGOLD", "Version lost on reload")
    check(!BlueJohtoLegendaries.radio_wing_reward, "Wing duplicated on reload")
    check(!BlueJohtoLegendaries.legendary_begin(:LUGIA), "Caught Lugia reset on reload")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH), "Caught Ho-Oh reset on reload")
    check(!BlueJohtoLegendaries.register_roamer(:RAIKOU, :registered),
          "Raikou roamer duplicated after reload")
    check(!BlueJohtoLegendaries.ruins_puzzle(0), "Unown puzzle reset on reload")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    kanto_snapshot = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH), "Johto Ho-Oh in Kanto")
    check(!BlueJohtoLegendaries.ruins_enter, "Ruins event in Kanto")
    check(!BlueJohtoLegendaries.radio_wing_reward, "Wing in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == kanto_snapshot,
          "Kanto state mutated")

    # Independent new SoulSilver and Crystal pilots must not inherit HG rewards.
    ss_flags = {"johto_campaign_version"=>"SOULSILVER",
                "burned_tower_beasts_awakened"=>true,
                "ecruteak_visited"=>true, "route41_visited"=>true,
                "rocket_hq_whirlpool_received"=>true,
                "goldenrod_radio_tower_cleared"=>true}
    $PokemonGlobal.blue_regions = {
      "version"=>1,"initial"=>"JOHTO","current"=>"JOHTO",
      "achievements"=>{"JOHTO"=>BlueRegions::BADGES.dup},
      "leagues"=>[], "johto_pilot"=>ss_flags
    }
    $bag = MockBag.new
    check(BlueJohtoLegendaries.radio_wing_reward, "SoulSilver Silver Wing missing")
    check($bag.quantity(:SILVERWING) == 1, "SoulSilver wrong wing")
    TrainerBattle.result = true
    5.times { |i| check(BlueJohtoLegendaries.kimono_girl(i), "SS Kimono #{i} failed") }
    check(BlueJohtoLegendaries.kimono_bell_reward, "Tidal Bell not given")
    check($bag.quantity(:TIDALBELL) == 1, "SoulSilver wrong bell")
    check(BlueJohtoLegendaries.kimono_ritual, "SS ritual failed")
    check(BlueJohtoLegendaries.whirl_entrance("NE",true,true), "SS Whirl entrance failed")
    check(BlueJohtoLegendaries.whirl_chamber, "SS Chamber missing")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH),
          "SoulSilver Ho-Oh started preleague")
    check(BlueJohtoLegendaries.legendary_begin(:LUGIA),
          "SoulSilver primary Lugia not available")
    check(BlueJohtoLegendaries.legendary_result(:LUGIA, :caught),
          "SoulSilver Lugia capture failed")
    $PokemonGlobal.blue_regions["johto_pilot"] = {
      "johto_campaign_version"=>"CRYSTAL",
      "burned_tower_beasts_awakened"=>true,
      "ecruteak_visited"=>true
    }
    check(!BlueJohtoLegendaries.radio_wing_reward,
          "Crystal received an HGSS radio wing")
    check(!BlueJohtoLegendaries.kimono_girl(0),
          "Crystal received HGSS Kimono sequence")
    check(!BlueJohtoLegendaries.legendary_begin(:HOOH),
          "Crystal inherited HGSS Ho-Oh storyline")
    check(!BlueJohtoLegendaries.crystal_suicune,
          "Unimplemented Crystal Suicune fight allowed")
    check(!BlueJohtoLegendaries.hgss_suicune_route25,
          "Crystal received HGSS Kanto Suicune route")
  end
end
puts "JOHTO_LEGENDARIES_RUNTIME_OK"
