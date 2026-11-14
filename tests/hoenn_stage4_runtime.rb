# Stage-4 story/field contract, pure Ruby; no RPG Maker XP, Game.exe or save.
class Hoenn4Global
  attr_accessor :blue_regions
end
class Hoenn4Pokemon
  attr_accessor :known_moves
  def initialize
    @known_moves = []
  end
  def hasMove?(move)
    @known_moves.include?(move)
  end
end
class Hoenn4Player
  attr_accessor :party
  attr_reader :healed
  def initialize
    @party = [Hoenn4Pokemon.new]
    @healed = 0
  end
  def heal_party
    @healed += 1
  end
end
class Hoenn4Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize
    @can_add = true
    @items = Hash.new(0)
  end
  def has?(item)
    @items[item] > 0
  end
  def add(item, n = 1)
    return false unless @can_add
    @items[item] += n
    true
  end
  def remove(item, n = 1)
    return false if @items[item] < n
    @items[item] -= n
    true
  end
end
class Hoenn4Event
  attr_reader :refresh_count
  def initialize; @refresh_count = 0; end
  def refresh; @refresh_count += 1; end
end
class Hoenn4Map
  attr_reader :map_id, :events
  def initialize
    @map_id = 783
    @events = {11 => Hoenn4Event.new}
  end
end
module GameData
  module Item
    ItemRec = Struct.new(:move)
    @registered = {
      HM01: nil, TM100: :ROCKTOMB, TM39: :SHADOWBALL, QUICKCLAW: nil,
      DEVONGOODS: nil, LETTER: nil,
    }
    def self.exists?(item); @registered.key?(item); end
    def self.get(item); ItemRec.new(@registered.fetch(item)); end
    def self.delete(item); @registered.delete(item); end
  end
end
module BlueRegions
  def self.local_achievements(state, region)
    state.fetch("achievements", {}).fetch(region, [])
  end
  def self.award(state, region, key)
    return false unless state["current"] == region &&
                        state["initial"] == "HOENN" &&
                        region == "HOENN" && key == "STONE"
    arr = (state["achievements"][region] ||= [])
    return false if arr.include?(key)
    arr << key
    true
  end
end
module BlueRegionStart
  def self.select_and_prepare
    false
  end
end
module EventHandlers
  def self.add(*_args);true;end
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
$confirm = true
def _INTL(message, *args)
  args.each_with_index { |value, index| message = message.gsub("{#{index + 1}}", value.to_s) }
  message
end
def pbMessage(message, *_args);$messages << message;end
def pbConfirmMessage(message);$messages << message;$confirm;end
def setBattleRule(name);$battles << name;end
def assert(cond, msg);raise "[HOENN_STAGE4] #{msg}" unless cond;end

require File.expand_path(ARGV.fetch(0))
$PokemonGlobal = Hoenn4Global.new
$PokemonGlobal.blue_regions = {"current" => "DECADES"}
$player = Hoenn4Player.new
$bag = Hoenn4Bag.new
$game_map = Hoenn4Map.new
$game_self_switches = {}

old = Marshal.dump($PokemonGlobal.blue_regions)
assert(!BlueHoennPilot.roxanne, "Gym leader ran in Decades")
assert(!BlueHoennPilot.cutter, "Cutter ran in Decades")
assert(!BlueHoennPilot.rustboro_theft, "Theft ran in Decades")
assert(!BlueHoennPilot.rusturf_aqua, "Aqua ran in Decades")
assert(!BlueHoennPilot.cut_tree(11), "Cut ran in Decades")
assert(Marshal.dump($PokemonGlobal.blue_regions) == old, "Decades save mutated")

$PokemonGlobal.blue_regions = {
  "version" => 1, "initial" => "HOENN", "current" => "HOENN",
  "achievements" => {}, "hoenn_pilot" => {},
}
flags = BlueHoennPilot.state
assert(!BlueHoennPilot.roxanne, "Roxanne opened before required story")
assert(!BlueHoennPilot.rustboro_theft, "Theft triggered before Roxanne")
assert(!BlueHoennPilot.cut_tree(11), "Cut allowed before Stone")
assert(BlueHoennPilot.cutter, "Cutter did not deliver HM")
assert($bag.items[:HM01] == 1, "HM Cut missing")
assert(!BlueHoennPilot.cutter, "HM Cut duplicated")
assert(!BlueHoennPilot.cut_tree(11), "HM alone bypassed Stone Badge")

flags["wally_captured"] = true
flags["forest_aqua_defeated"] = true
TrainerBattle.result = false
assert(!BlueHoennPilot.roxanne, "Loss marked Stone Badge")
assert(!BlueHoennPilot.stone_badge?, "Stone badge granted on loss")
assert($PokemonGlobal.blue_regions["achievements"] == {}, "Achievement changed on loss")

$bag.can_add = false
TrainerBattle.result = true
assert(BlueHoennPilot.roxanne, "Leader win did not register achievement")
assert(BlueHoennPilot.stone_badge?, "STONE achievement not granted")
assert(BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN") == ["STONE"],
       "Wrong or duplicated badge")
assert($bag.items[:TM100] == 0, "TM granted in full bag")
assert(!flags["roxanne_tm_given"], "Full bag saved item reward")
$bag.can_add = true
assert(BlueHoennPilot.roxanne, "Deferred TM not delivered after freeing bag")
assert($bag.items[:TM100] == 1, "Wrong Rock Tomb TM")
assert($bag.items[:TM39] == 0, "Unrelated TM39 given")
assert(!BlueHoennPilot.roxanne, "Repeated TM reward")
assert($bag.items[:TM100] == 1, "TM duplicated")
assert(TrainerBattle.history.count([:BLUE_HOENN_ROXANNE, "Roxanne", 427]) == 2,
       "Roxanne was fought more than twice, including one loss")

# The player must actually teach Cut, after acquiring both HM and STONE.
assert(!BlueHoennPilot.cut_tree(11), "Cut allowed with no Pokémon knowing it")
$player.party.first.known_moves << :CUT
$confirm = false
assert(!BlueHoennPilot.cut_tree(11), "Declining Cut removed tree")
assert(!$game_self_switches[[783, 11, "A"]], "Decline set self switch")
$confirm = true
assert(BlueHoennPilot.cut_tree(11), "Cut failed after permission")
assert($game_self_switches[[783, 11, "A"]], "Cut did not hide event")
assert($game_map.events[11].refresh_count == 1, "Tree event did not refresh")
assert(BlueHoennPilot.cut_tree(11), "Cleared tree not reload-safe")
assert($game_map.events[11].refresh_count == 2, "Cleared tree didn't self-heal")
assert(BlueHoennPilot.teacher, "Quick Claw missing")
assert($bag.items[:QUICKCLAW] == 1, "Quick Claw not delivered")
assert(!BlueHoennPilot.teacher, "Duplicate Quick Claw")

assert(BlueHoennPilot.rustboro_theft, "Devon theft not triggered")
assert(!BlueHoennPilot.rustboro_theft, "Devon theft duplicated")
assert(BlueHoennPilot.briney_route116, "Briney didn't know about Peecko")
assert(!BlueHoennPilot.rusturf_goods_reward, "Devon goods available before fight")
TrainerBattle.result = false
assert(!BlueHoennPilot.rusturf_aqua, "Aqua defeat counted as victory")
assert(!flags["rusturf_aqua_defeated"], "Aqua defeat flag on loss")
TrainerBattle.result = true
$bag.can_add = false
assert(!BlueHoennPilot.rusturf_aqua, "Full bag should postpone goods")
assert(flags["rusturf_aqua_defeated"], "Win not saved before reward")
assert(flags["peecko_rescued"], "Peecko not rescued on win")
assert(!flags["devon_goods_recovered"], "Full bag granted Devon Goods")
assert(TrainerBattle.history.count([:BLUE_HOENN_AQUA, "Recruta", 405]) == 2,
       "Aqua trainer replayed after victory")
$bag.can_add = true
assert(BlueHoennPilot.rusturf_aqua, "Deferred Devon Goods unavailable")
assert($bag.items[:DEVONGOODS] == 1, "Devon Goods missing")
assert(!BlueHoennPilot.rusturf_aqua.nil?, "Aqua postgame interaction failed")
assert($bag.items[:DEVONGOODS] == 1, "Devon Goods duplicated")
assert(BlueHoennPilot.peeko, "Rescued Peeko can't be spoken to")
assert(BlueHoennPilot.devon_route116, "Route116 Devon NPC missing")

assert(BlueHoennPilot.devon_employee, "Devon couldn't receive recovered goods")
assert(flags["devon_goods_delivered"], "Devon delivery not saved")
assert($bag.items[:DEVONGOODS] == 0, "Devon Goods not removed after delivery")
assert(BlueHoennPilot.devon_employee, "Devon second dialog missing")
assert($bag.items[:DEVONGOODS] == 0, "Devon removed Goods twice")

$bag.can_add = false
assert(!BlueHoennPilot.mr_stone, "Letter delivered with full bag")
assert(!flags["stone_letter_received"], "Full bag marked Stone letter received")
$bag.can_add = true
assert(BlueHoennPilot.mr_stone, "Mr Stone didn't deliver LETTER")
assert($bag.items[:LETTER] == 1, "Letter missing")
assert(BlueHoennPilot.mr_stone, "Mr Stone repeat dialogue missing")
assert($bag.items[:LETTER] == 1, "Letter duplicated")
assert(!BlueHoennPilot.rusturf_east_gate, "Verdanturf premature exit")
assert(BlueHoennPilot.sign_stage4(:RUSTBORO_GYM), "Gym sign missing")
assert(!BlueHoennPilot.sign_stage4(:MISSING), "Unknown sign accepted")

# Persisted save cannot duplicate badge, CUT, loot, HM, letter or battles.
$PokemonGlobal.blue_regions = Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
assert(BlueRegions.local_achievements($PokemonGlobal.blue_regions, "HOENN") == ["STONE"],
       "STONE lost after reload")
assert(!BlueHoennPilot.roxanne, "Roxanne reward repeated after reload")
assert(BlueHoennPilot.cut_tree(11), "Cut flag not saved")
assert($bag.items[:TM100] == 1 && $bag.items[:HM01] == 1 &&
       $bag.items[:LETTER] == 1, "Reload duplicated rewards")

$PokemonGlobal.blue_regions["current"] = "KANTO"
prev = Marshal.dump($PokemonGlobal.blue_regions)
assert(!BlueHoennPilot.roxanne, "Roxanne ran in Kanto")
assert(!BlueHoennPilot.cut_tree(11), "Cut permission leaked to Kanto")
assert(!BlueHoennPilot.devon_employee, "Devon ran in Kanto")
assert(Marshal.dump($PokemonGlobal.blue_regions) == prev, "Kanto save polluted")
puts "HOENN_STAGE4_RUNTIME_OK"
