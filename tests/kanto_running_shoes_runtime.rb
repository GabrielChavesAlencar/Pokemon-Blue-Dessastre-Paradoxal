# Standalone regression for the REAL KantoPilot.rb running shoes handoff.
# Uses no FRLG archive, Game.exe or the player's saved game.
require "tmpdir"

ruby_source = File.expand_path(ARGV.fetch(0))
class Game_Player
  attr_accessor :x, :y
  attr_reader :native_steps, :turns
  def initialize(x = 19, y = 6)
    @x, @y, @native_steps, @turns = x, y, 0, 0
  end
  def move_generic(dir, turn_enabled = true)
    @native_steps += 1
    true
  end
  def turn_generic(dir, enabled)
    @turns += 1 if enabled
  end
end
module MenuHandlers
  def self.add(*_args); end
end
module BlueRegions
  def self.new_state(region)
    {"version" => 1, "current" => region, "achievements" => {}}
  end
  def self.local_achievements(state, region)
    state.fetch("achievements", {}).fetch(region, [])
  end
end
module BlueMusic
  def self.kanto_me_play(name); ($music ||= []) << name; end
end
module BlueLocale
  def self.enabled?; true; end
  def self.with_raw; yield; end
end
def _INTL(text, *args)
  text.gsub(/\{(\d+)\}/) { args[$1.to_i - 1].to_s }
end
class FakePlayer
  attr_accessor :has_running_shoes
  attr_reader :name
  def initialize
    @name = "Red"
    @has_running_shoes = false
  end
end
class FakeSystem
  attr_accessor :runstyle
  def initialize; @runstyle = 0; end
end
class FakeMother
  attr_accessor :character_name, :direction
  attr_reader :name, :frames, :coords
  def initialize
    @name = "Kanto Running Shoes Mom"
    @character_name = ""
    @frames = []
  end
  def character_name=(value)
    @character_name = value
    @frames << value
  end
  def moveto(x, y)
    @coords = [x, y]
  end
end
class FakeMap
  attr_accessor :map_id
  attr_reader :events
  def initialize(id)
    @map_id = id
    @events = {25 => FakeMother.new}
  end
end
$dialogues = []
def pbMessage(text, *_args); $dialogues << text; end
def verify(condition, label); raise "RUNNING_SHOES_FAILURE: #{label}" unless condition; end

Dir.mktmpdir("kanto-running-shoes-") do |tmp|
  Dir.chdir(tmp) do
    Dir.mkdir("Data")
    File.write("Kanto pilot.json", "{}")
    File.write("Data/blue-kanto-pewter-route3-gate.txt", "777|20|5|9\n")
    File.write("Data/blue-kanto-pewter-mom-sprite.txt", "FRLG_Pilot_Pallet_Mom\n")
    load ruby_source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    $PokemonSystem = FakeSystem.new
    $player = FakePlayer.new
    $game_map = FakeMap.new(777)
    player = Game_Player.new(19, 6)

    # Brock still controls entry; the gift is not awarded prematurely.
    player.move_generic(6)
    verify(player.native_steps == 0, "route3 opened without Boulder")
    verify(!BlueKantoPilot.progress["pilot_mom_running_shoes"], "gift given before Brock")
    verify(!$player.has_running_shoes && $PokemonSystem.runstyle == 0, "running unlocked early")

    BlueKantoPilot.progress["achievements"]["JOHTO"] = ["BOULDER"]
    player.move_generic(6)
    verify(player.native_steps == 0, "badge from other region opened gate")
    BlueKantoPilot.progress["achievements"]["KANTO"] = ["BOULDER"]

    # Only east-edge crossing from Pewter can trigger the handoff.
    player.x = 18
    player.move_generic(6)
    verify(player.native_steps == 1 && !$player.has_running_shoes, "gift too far from exit")
    player.x = 19
    player.y = 4
    player.move_generic(6)
    verify(!$player.has_running_shoes, "gift outside connected Route 3 rows")
    player.y = 6
    player.move_generic(2)
    verify(!$player.has_running_shoes, "gift when moving south")
    $game_map.map_id = 888
    player.move_generic(6)
    verify(!$player.has_running_shoes, "gift from another map")

    $game_map.map_id = 777
    player.move_generic(6)
    verify($player.has_running_shoes, "mother did not grant native Running Shoes")
    verify($PokemonSystem.runstyle == 1, "running is not the default movement speed")
    verify(BlueKantoPilot.progress["pilot_mom_running_shoes"] == true, "reward flag not persisted")
    verify($dialogues.any? { |msg| msg.include?("Mãe") } &&
           $dialogues.any? { |msg| msg.include?("Tênis de Corrida") },
           "mother's gift and item messages are missing")
    verify(($music || []).count("obtained_item") == 1, "item fanfare missing")
    mother = $game_map.events[25]
    verify(mother.frames.include?("FRLG_Pilot_Pallet_Mom"),
           "actual mother sprite never appeared during the gift")
    verify(mother.frames.last == "", "mother sprite remained blocking the exit")
    verify(mother.coords == [18, 6] && mother.direction == 6,
           "mother did not appear beside and facing the player")

    before = $dialogues.length
    player.move_generic(6)
    verify($dialogues.length == before, "shoes were awarded twice in one save")
    verify(($music || []).count("obtained_item") == 1, "reward fanfare replayed")

    # Simulate an old save that already defeated Brock but lacks new flag.
    old_state = BlueRegions.new_state("KANTO")
    old_state["achievements"]["KANTO"] = ["BOULDER"]
    $PokemonGlobal.blue_regions = old_state
    $player = FakePlayer.new
    $PokemonSystem = FakeSystem.new
    player.move_generic(6)
    verify($player.has_running_shoes && BlueKantoPilot.progress["pilot_mom_running_shoes"],
           "existing Brock save cannot collect shoes")
    # Save/load does not reaward and retains native player capability.
    restored = Marshal.load(Marshal.dump([$PokemonGlobal.blue_regions, $player, $PokemonSystem]))
    $PokemonGlobal.blue_regions, $player, $PokemonSystem = restored
    before = $dialogues.length
    player.move_generic(6)
    verify($dialogues.length == before && $player.has_running_shoes &&
           $PokemonSystem.runstyle == 1, "save/reload lost shoes or repeated mother scene")

    # Another, fresh Decades instance must never receive the Kanto reward.
    File.delete("Kanto pilot.json")
    $PokemonGlobal.blue_regions = BlueRegions.new_state("DECADES")
    $PokemonGlobal.blue_regions["achievements"]["KANTO"] = ["BOULDER"]
    $player = FakePlayer.new
    $PokemonSystem = FakeSystem.new
    player.move_generic(6)
    verify(!$player.has_running_shoes && $PokemonSystem.runstyle == 0,
           "Decades inherited Kanto running shoes")
  end
end
puts "PASS: Brock-gated Route 3 mother gives Running Shoes once, auto-run enabled, save persists and Decades isolated"
