# Stage-3 Ruby-only Hoenn integration checks: NO Engine, Game.exe or save file.
class Stage3Global
  attr_accessor :blue_regions
end
class Stage3Player
  attr_accessor :party, :has_pokedex
  def initialize
    @party = [[:TREECKO, 5]]
  end
end
class Stage3Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize
    @can_add = true
    @items = Hash.new(0)
  end
  def add(item, n = 1)
    return false unless @can_add
    @items[item] += n
    true
  end
end
class Stage3Event
  attr_reader :refresh_count
  def initialize
    @refresh_count = 0
  end
  def refresh
    @refresh_count += 1
  end
end
class Stage3Map
  attr_accessor :map_id, :events
  def initialize
    @map_id = 756
    @events = {3 => Stage3Event.new}
  end
end
module TrainerBattle
  @history = []
  class << self
    attr_accessor :result
    attr_reader :history
    def start(*args)
      @history << args
      @result != false
    end
  end
end

$messages = []
$battles = []
def _INTL(message, *args)
  args.each_with_index { |value, i| message = message.gsub("{#{i + 1}}", value.to_s) }
  message
end
def pbMessage(message, *_extra)
  $messages << message
end
def setBattleRule(rule)
  $battles << rule
end
def pbCanDoubleBattle?
  $player.party.size >= 2
end
def assert(value, msg)
  raise "[HOENN_STAGE3] #{msg}" unless value
end

require File.expand_path(ARGV.fetch(0))
$PokemonGlobal = Stage3Global.new
$PokemonGlobal.blue_regions = {"current"=>"DECADES"}
$player = Stage3Player.new
$bag = Stage3Bag.new
$game_map = Stage3Map.new
$game_self_switches = {}

before = Marshal.dump($PokemonGlobal.blue_regions)
assert(!BlueHoennPilot.norman_intro, "Norman triggered in Decades")
assert(!BlueHoennPilot.flower_shop, "Flower gift triggered in Decades")
assert(!BlueHoennPilot.forest_aqua, "Aqua triggered in Decades")
assert(!BlueHoennPilot.pickup(:POTION, "TEST", 3), "Item triggered in Decades")
assert(Marshal.dump($PokemonGlobal.blue_regions) == before, "Foreign save polluted")

$PokemonGlobal.blue_regions = {"current"=>"HOENN", "hoenn_pilot"=>{"pokedex_given"=>true}}
flags = BlueHoennPilot.state
assert(!BlueHoennPilot.forest_aqua, "Aqua should require Wally's story")
assert(BlueHoennPilot.norman_intro, "Norman/Wally capture introduction missing")
assert(flags["wally_captured"], "Wally event not persisted")
assert(BlueHoennPilot.wally_family, "Wally family dialogue unavailable")
assert(BlueHoennPilot.norman_intro, "Norman repeated conversation failed")
assert(BlueHoennPilot.sign(:PETALBURG_CITY), "Petalburg sign missing")
assert(!BlueHoennPilot.sign(:UNLISTED), "Unknown sign accepted")

$bag.can_add = false
assert(!BlueHoennPilot.flower_shop, "Gift granted with full bag")
assert(!flags["wailmer_pail_received"], "Full bag saved gift state")
$bag.can_add = true
assert(BlueHoennPilot.flower_shop, "Flower shop did not give Wailmer Pail")
assert($bag.items[:WAILMERPAIL] == 1, "Incorrect flower gift")
assert(!BlueHoennPilot.flower_shop, "Duplicate Wailmer Pail")
assert($bag.items[:WAILMERPAIL] == 1, "Gift count changed")

$bag.can_add = false
assert(!BlueHoennPilot.pickup(:POTION, "ROUTE104_TEST", 3), "Item saved with full bag")
assert(!flags["pickup_ROUTE104_TEST"], "Item flag saved when bag full")
$bag.can_add = true
assert(BlueHoennPilot.pickup(:POTION, "ROUTE104_TEST", 3), "Ground item missing")
assert($game_self_switches[[756, 3, "A"]] == true, "Ground item did not vanish")
assert($game_map.events[3].refresh_count == 1, "Ground item was not refreshed")
assert(!BlueHoennPilot.pickup(:POTION, "ROUTE104_TEST", 3), "Item duplicated")
assert($bag.items[:POTION] == 1, "Duplicate Potion")

TrainerBattle.result = false
assert(!BlueHoennPilot.battle_stage3(:YOUNGSTER, "Billy", 104), "Loss counted as win")
assert(!flags["trainer_104_YOUNGSTER_Billy"], "Lost battle persisted victory")
TrainerBattle.result = true
assert(BlueHoennPilot.battle_stage3(:YOUNGSTER, "Billy", 104), "Trainer win missing")
assert(!BlueHoennPilot.battle_stage3(:YOUNGSTER, "Billy", 104), "Trainer repeated")
assert(TrainerBattle.history.count([:YOUNGSTER, "Billy", 104]) == 2, "Repeated trainer call")

assert(!BlueHoennPilot.battle_stage3(:TWINS, "Gina & Mia", 104, true),
       "Twins challenged one-Pokémon team")
$player.party << [:POOCHYENA, 5]
assert(BlueHoennPilot.battle_stage3(:TWINS, "Gina & Mia", 104, true),
       "Twins battle missing")
assert($battles.include?("double"), "Double battle not requested")
assert(!BlueHoennPilot.battle_stage3(:TWINS, "Gina & Mia", 104, true),
       "Second twin sprite started a duplicate battle")

TrainerBattle.result = false
assert(!BlueHoennPilot.forest_aqua, "Losing to Aqua marked victory")
assert(!flags["forest_aqua_defeated"], "Aqua defeat flag saved despite losing")
TrainerBattle.result = true
$bag.can_add = false
assert(!BlueHoennPilot.forest_aqua, "Full bag should postpone Great Ball")
assert(flags["forest_aqua_defeated"], "Aqua victory was not saved")
assert(!flags["forest_greatball_received"], "Aqua gift wrongly saved")
assert(TrainerBattle.history.count([:BLUE_HOENN_AQUA, "Recruta", 304]) == 2,
       "Grunt was fought extra times")
$bag.can_add = true
assert(BlueHoennPilot.forest_aqua, "Pending Great Ball unavailable")
assert(flags["forest_greatball_received"], "Great Ball not recorded")
assert($bag.items[:GREATBALL] == 1, "Great Ball missing")
assert(!BlueHoennPilot.forest_aqua, "Aqua gift repeated")
assert($bag.items[:GREATBALL] == 1, "Aqua reward duplicated")

reloaded = Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
$PokemonGlobal.blue_regions = reloaded
assert(!BlueHoennPilot.forest_aqua, "Reload duplicated Aqua reward")
assert(!BlueHoennPilot.pickup(:POTION, "ROUTE104_TEST", 3), "Reload duplicated item")
$PokemonGlobal.blue_regions["current"] = "KANTO"
old = Marshal.dump($PokemonGlobal.blue_regions)
assert(!BlueHoennPilot.forest_aqua, "Aqua ran in Kanto")
assert(!BlueHoennPilot.norman_intro, "Norman ran in Kanto")
assert(Marshal.dump($PokemonGlobal.blue_regions) == old, "Kanto flags changed")

puts "HOENN_STAGE3_RUNTIME_OK"
