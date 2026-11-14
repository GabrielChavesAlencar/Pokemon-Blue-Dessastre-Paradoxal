# Real KantoPilot.rb regression: Route 2 gate at the red screenshot line.
# Runs with no FRLG archive, Game.exe or user saves.
require "tmpdir"

pilot_source = File.expand_path(ARGV.fetch(0))
class Game_Player; end
module MenuHandlers
  def self.add(*_args); end
end
def _INTL(source, *_args); source; end
module BlueRegions
  def self.new_state(region)
    {"version"=>1, "current"=>region, "achievements"=>{}}
  end
  def self.local_achievements(state, region)
    state.fetch("achievements", {}).fetch(region, [])
  end
end
class FakeEvent
  attr_reader :name, :x, :y, :erases
  def initialize(name, x, y)
    @name, @x, @y = name, x, y
    @erases = 0
    @erased = false
  end
  def erase; @erases += 1; @erased = true; end
end
class FakeMap
  attr_accessor :map_id
  attr_reader :events
  def initialize(map_id, events = {})
    @map_id, @events = map_id, events
  end
end
FakePlayer = Struct.new(:x, :y)
def verify(value, message)
  raise "VIRIDIAN_LINE_ERROR: #{message}" unless value
end

Dir.mktmpdir("kanto-viridian-line-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    File.write("Kanto pilot.json", '{"maps":{"10":421}}')
    # The original north house front-door fixture is x=9, y=6. Builder
    # emits y=5, x=[3,8), rather than north-edge y=0.
    File.write("Data/blue-kanto-viridian-route2-line.txt", "421|5|3|8\n")
    load pilot_source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    stale = FakeEvent.new("Kanto Viridian Route 2 Parcel Gate", 5, 0)
    npc = FakeEvent.new("Viridian NPC", 4, 5)
    $game_map = FakeMap.new(421, {20=>stale, 21=>npc})

    verify(BlueKantoPilot.viridian_route2_line == [421, 5, 3, 8],
           "pilot marker did not read the new interior line")
    verify(BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 6), 8),
           "approaching red line from south was not blocked before Oak")
    verify(stale.erases == 1, "legacy north-border gate from old save was not removed")
    verify(npc.erases == 0, "unrelated NPC was wrongly erased")
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 0), 8),
           "old top-border y=0 gate is still active")
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(2, 6), 8),
           "gate wrongly extends to the west of the corridor")
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(8, 6), 8),
           "gate wrongly extends to the house to the east")
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 6), 2),
           "returning south was blocked")
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 7), 8),
           "one tile below the new red line is blocked")
    verify(stale.erases == 1, "legacy gate was erased repeatedly")

    BlueKantoPilot.progress["pilot_oak_parcel_received"] = true
    verify(BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 6), 8),
           "receiving parcel wrongly unlocked the road before delivery")
    BlueKantoPilot.progress["pilot_oak_parcel_delivered"] = true
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 6), 8),
           "Oak delivery did not unlock the new barrier")
    BlueKantoPilot.progress["pilot_oak_parcel_delivered"] = false

    $game_map = FakeMap.new(422, {20=>FakeEvent.new(stale.name, 5, 0)})
    verify(!BlueKantoPilot.route2_exit_blocked?(FakePlayer.new(5, 6), 8),
           "gate affected a different map")
    verify($game_map.events[20].erases == 0,
           "legacy erasure affected a map other than Viridian")
  end
end
puts "PASS: Viridian north gate moved to internal screenshot line; old save gate removed; Oak unlock intact"
