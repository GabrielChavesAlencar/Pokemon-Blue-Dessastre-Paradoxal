# Johto phase 07 pure Ruby regression. Never loads Game.exe, source maps or saves.
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
    native + local_achievements(state, "JOHTO").size
  end
  def self.field_access(state, region, action, ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO"
    badge = {"CUT"=>"HIVE", "STRENGTH"=>"PLAIN"}[action]
    return :unavailable unless badge
    return :badge unless local_achievements(state, "JOHTO").include?(badge)
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
    def self.exists?(item)
      [:HM01, :SQUIRTBOTTLE].include?(item)
    end
  end
  module Species
    def self.exists?(species)
      species == :SUDOWOODO
    end
  end
end

class LocalBag
  def initialize
    @items = {}
  end
  def add(id)
    @items[id] = true
  end
  def has?(id)
    @items[id] == true
  end
end

$messages = []
$questions = []
$items = []
$gift_ok = true
$wild_ok = true
$wild_history = []
$bag = LocalBag.new

def _INTL(string, *values)
  values.each_with_index { |v, i| string = string.gsub("{#{i + 1}}", v.to_s) }
  string
end

def pbMessage(message, options = nil, default = nil)
  $messages << message
  options ? $questions.shift : nil
end

def pbReceiveItem(item)
  return false unless $gift_ok
  $items << item
  $bag.add(item)
  true
end

def pbWildBattle(species, level)
  $wild_history << [species, level]
  $wild_ok
end

def check(condition, why)
  raise why unless condition
end

require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)

Dir.mktmpdir("blue-johto-goldenrod-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    state = {
      "version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
      "achievements"=>{"JOHTO"=>["ZEPHYR", "HIVE"]},
      "johto_pilot"=>{"starter"=>"CYNDAQUIL", "rival_fought"=>true,
                      "azalea_rival_defeated"=>true}
    }
    $PokemonGlobal.blue_regions = state
    before = Marshal.dump(state)
    check(!BlueJohtoGoldenrod.ilex_entrance, "Ilex began in Decades")
    check(!BlueJohtoGoldenrod.woodcutter, "Woodcutter ran in Decades")
    check(!BlueJohtoGoldenrod.farfetchd(0), "Farfetch'd ran in Decades")
    check(!BlueJohtoGoldenrod.cut_reward, "Cut rewarded in Decades")
    check(!BlueJohtoGoldenrod.forest_exit(true), "Ilex exited in Decades")
    check(!BlueJohtoGoldenrod.radio_quiz, "Radio quiz ran in Decades")
    check(!BlueJohtoGoldenrod.whitney, "Whitney ran in Decades")
    check(!BlueJohtoGoldenrod.whitney_badge, "Plain awarded in Decades")
    check(!BlueJohtoGoldenrod.flower_shop, "SquirtBottle awarded in Decades")
    check(!BlueJohtoGoldenrod.sudowoodo, "Sudowoodo fought in Decades")
    check(Marshal.dump(state) == before, "Decades save mutated")
    state["current"] = "KANTO"
    check(!BlueJohtoGoldenrod.whitney, "Whitney ran in Kanto")
    check(!BlueJohtoGoldenrod.strength_allowed?(true), "Johto Strength in Kanto")

    state["current"] = "JOHTO"
    state["achievements"]["JOHTO"] = ["ZEPHYR"]
    check(!BlueJohtoGoldenrod.ilex_entrance, "Ilex allowed without HIVE")
    check(!BlueJohtoGoldenrod.farfetchd(0), "Farfetch'd without HIVE")
    state["achievements"]["JOHTO"] << "HIVE"
    state["johto_pilot"]["azalea_rival_defeated"] = false
    check(!BlueJohtoGoldenrod.ilex_entrance, "Ilex allowed before Azalea rival")
    state["johto_pilot"]["azalea_rival_defeated"] = true
    check(BlueJohtoGoldenrod.ilex_entrance, "Ilex entrance not recorded")
    check(!BlueJohtoGoldenrod.ilex_entrance, "Ilex entrance recorded twice")
    check(!BlueJohtoGoldenrod.farfetchd(0), "Farfetch'd found before woodcutter")
    check(BlueJohtoGoldenrod.woodcutter, "Woodcutter interaction not recorded")
    check(!BlueJohtoGoldenrod.woodcutter, "Woodcutter interaction repeated")
    check(!BlueJohtoGoldenrod.farfetchd(1), "Skipped first Farfetch'd")
    check(!BlueJohtoGoldenrod.farfetchd("0"), "Invalid Farfetch'd step accepted")
    check(BlueJohtoGoldenrod.farfetchd(0), "First Farfetch'd not returned")
    check(!BlueJohtoGoldenrod.farfetchd(0), "First Farfetch'd duplicated")
    check(!BlueJohtoGoldenrod.forest_puzzle_complete?, "Puzzle completed too early")
    check(BlueJohtoGoldenrod.farfetchd(1), "Second Farfetch'd not returned")
    check(BlueJohtoGoldenrod.forest_puzzle_complete?, "Puzzle not completed")
    check(!BlueJohtoGoldenrod.cut_reward, "Cut given without ready marker")
    check($items.empty?, "Inventory changed without ready marker")
    check(!BlueJohtoGoldenrod.forest_exit(true), "Forest opened without Cut reward")

    File.write(BlueJohtoGoldenrod::CUT_REWARD_READY, "INVALID")
    check(!BlueJohtoGoldenrod.cut_reward, "Invalid Cut marker accepted")
    File.write(BlueJohtoGoldenrod::CUT_REWARD_READY,
               "BLUE_JOHTO_ILEX_CUT_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoGoldenrod.cut_reward, "Failed Cut item delivery counted")
    check(!state["johto_pilot"]["ilex_cut_rewarded"], "Cut marked granted despite failure")
    $gift_ok = true
    check(BlueJohtoGoldenrod.cut_reward, "Cut reward not delivered")
    check($items == [:HM01], "Wrong Cut item or duplicate")
    check(!BlueJohtoGoldenrod.cut_reward, "Duplicate Cut item allowed")
    check(!BlueJohtoGoldenrod.forest_exit, "Cut gate ignores tool")
    check(BlueJohtoGoldenrod.forest_exit(true), "Forest not passed with Cut and HIVE")
    check(!BlueJohtoGoldenrod.forest_exit(true), "Ilex exit counted twice")

    check(BlueJohtoGoldenrod.day_care, "Day Care intro missing")
    check(!BlueJohtoGoldenrod.day_care, "Day Care intro duplicated")
    check(BlueJohtoGoldenrod.goldenrod_arrive, "Goldenrod arrival not recorded")
    check(!BlueJohtoGoldenrod.goldenrod_arrive, "Goldenrod arrival duplicated")
    check(BlueJohtoGoldenrod.underground, "Underground introduction missing")
    check(!BlueJohtoGoldenrod.underground, "Underground repeated")
    check(!BlueJohtoGoldenrod.whitney, "Gym opened before radio quest")
    check(!BlueJohtoGoldenrod.whitney_badge, "Plain given without battle")

    $questions = [0]
    check(!BlueJohtoGoldenrod.radio_quiz, "Wrong radio answer accepted")
    check(!state["johto_pilot"]["goldenrod_radio_quiz"], "Wrong answer persisted")
    $questions = [3]
    check(!BlueJohtoGoldenrod.radio_quiz, "Radio cancel accepted")
    $questions = [1, 1, 0]
    check(BlueJohtoGoldenrod.radio_quiz, "Correct radio quiz not recorded")
    check(!BlueJohtoGoldenrod.radio_quiz, "Radio quiz recorded twice")
    check(!BlueJohtoGoldenrod.whitney, "Whitney started before trainer PBS marker")
    check(TrainerBattle.history.empty?, "Trainer invoked without PBS marker")
    File.write(BlueJohtoGoldenrod::TRAINERS_READY, "WRONG")
    check(!BlueJohtoGoldenrod.whitney, "Wrong trainer marker accepted")
    File.write(BlueJohtoGoldenrod::TRAINERS_READY,
               "BLUE_JOHTO_GOLDENROD_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoGoldenrod.whitney, "Loss registered as victory")
    check(!BlueJohtoGoldenrod.whitney_badge, "Plain given after lost battle")
    check(BlueRegions.crystal_total(state, 4) == 6, "Loss added a global emerald")
    check(!BlueJohtoGoldenrod.strength_allowed?(true), "Strength before PLAIN")
    TrainerBattle.result = true
    check(BlueJohtoGoldenrod.whitney, "Whitney victory not recorded")
    check(!BlueJohtoGoldenrod.plain_earned?, "Whitney gave badge before followup")
    check(!BlueJohtoGoldenrod.whitney, "Repeated Whitney battle while crying")
    check(BlueJohtoGoldenrod.whitney_badge, "Plain not awarded after followup")
    check(BlueJohtoGoldenrod.plain_earned?, "Plain Badge missing after followup")
    check(BlueRegions.local_achievements(state, "JOHTO") ==
          ["ZEPHYR", "HIVE", "PLAIN"], "Wrong local badge list")
    check(BlueRegions.crystal_total(state, 4) == 7, "Plain increment wrong")
    count = TrainerBattle.history.size
    check(!BlueJohtoGoldenrod.whitney_badge, "Duplicate Plain claim")
    check(!BlueJohtoGoldenrod.whitney, "Whitney repeated after badge")
    check(TrainerBattle.history.size == count, "Duplicate Whitney battle")
    check(!BlueJohtoGoldenrod.strength_allowed?, "Strength bypassed tool")
    check(BlueJohtoGoldenrod.strength_allowed?(true), "Plain/tool failed Strength")

    check(!BlueJohtoGoldenrod.flower_shop, "SquirtBottle without marker")
    File.write(BlueJohtoGoldenrod::FLOWER_READY, "WRONG")
    check(!BlueJohtoGoldenrod.flower_shop, "Wrong flower marker accepted")
    File.write(BlueJohtoGoldenrod::FLOWER_READY,
               "BLUE_JOHTO_FLOWER_SHOP_V1_READY\n")
    $gift_ok = false
    check(!BlueJohtoGoldenrod.flower_shop, "Failed SquirtBottle counted")
    $gift_ok = true
    check(BlueJohtoGoldenrod.flower_shop, "SquirtBottle not awarded")
    check($items == [:HM01, :SQUIRTBOTTLE], "SquirtBottle duplicated or bad item")
    check(!BlueJohtoGoldenrod.flower_shop, "SquirtBottle awarded twice")

    check(!BlueJohtoGoldenrod.sudowoodo, "Sudowoodo without readiness marker")
    File.write(BlueJohtoGoldenrod::SUDOWOODO_READY,
               "BLUE_JOHTO_SUDOWOODO_V1_READY\n")
    $wild_ok = false
    check(!BlueJohtoGoldenrod.sudowoodo, "Failed Sudowoodo marked cleared")
    check(!state["johto_pilot"]["route36_sudowoodo_cleared"],
          "Failed Sudowoodo flag persisted")
    $wild_ok = true
    check(BlueJohtoGoldenrod.sudowoodo, "Sudowoodo clear not recorded")
    check($wild_history == [[:SUDOWOODO, 20], [:SUDOWOODO, 20]],
          "Unexpected Sudowoodo level or replay")
    check(!BlueJohtoGoldenrod.sudowoodo, "Sudowoodo repeated after clear")

    old = Marshal.dump(state)
    $PokemonGlobal.blue_regions = Marshal.load(old)
    check(BlueJohtoGoldenrod.plain_earned?, "Plain lost on save/reload")
    check(BlueJohtoGoldenrod.forest_puzzle_complete?, "Farfetch'd lost on reload")
    check(!BlueJohtoGoldenrod.cut_reward, "Cut duplicated on reload")
    check(!BlueJohtoGoldenrod.whitney_badge, "Plain duplicated on reload")
    check(!BlueJohtoGoldenrod.sudowoodo, "Sudowoodo repeated on reload")
    check(BlueRegions.crystal_total($PokemonGlobal.blue_regions, 4) == 7,
          "Reload changed emerald count")

    $PokemonGlobal.blue_regions["current"] = "KANTO"
    before = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoGoldenrod.plain_earned?, "Johto badge appears in Kanto view")
    check(!BlueJohtoGoldenrod.cut_reward, "Cut repeated in Kanto")
    check(!BlueJohtoGoldenrod.whitney, "Whitney fought in Kanto")
    check(!BlueJohtoGoldenrod.strength_allowed?(true), "Johto Strength applied in Kanto")
    check(!BlueJohtoGoldenrod.sudowoodo, "Johto Sudowoodo triggered in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before,
          "Kanto was modified by Johto story events")
  end
end
puts "JOHTO_GOLDENROD_RUNTIME_OK"
