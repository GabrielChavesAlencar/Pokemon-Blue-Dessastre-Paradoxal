# QA07 Ruby dispatcher smoke tests. No Game.exe, original ZIP or real saves.
class QA7Global; attr_accessor :blue_regions; end
class QA7Map; attr_accessor :map_id; end
module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args); true; end
end
def qa7_assert(condition, message)
  raise "[HOENN_QA7] #{message}" unless condition
end

require File.expand_path(ARGV.fetch(0))
mapping = BlueHoennPilot::HOENN_QA7_GYMS
qa7_assert(mapping.size == 8, "eight gym records required")
qa7_assert(mapping.keys == [:STONE, :KNUCKLE, :DYNAMO, :HEAT,
                            :BALANCE, :FEATHER, :MIND, :RAIN],
           "gym badge order differs from expected Hoenn")
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708, 25, 6], mapping.transform_values { |source_id, _| source_id + 600 }
                     .each_with_object({}) { |(_key, _value), _| } ]
end
# Stub only the mapping; exercise the REAL QA07 routing method.
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6], Hash[mapping.values.map { |source_id, _| [source_id, source_id + 600] }]]
end

$PokemonGlobal = QA7Global.new
$PokemonGlobal.blue_regions = {
  "initial" => "HOENN", "current" => "HOENN",
  "achievements" => {"HOENN" => []}, "hoenn_pilot" => {}
}
$game_map = QA7Map.new
recorded = []
mapping.each do |badge, (source_id, handler)|
  BlueHoennPilot.define_singleton_method(handler) do
    recorded << badge
    true
  end
end
qa7_assert(!BlueHoennPilot.qa7_gym_battle(:NOT_A_BADGE), "unknown badge accepted")
qa7_assert(recorded.empty?, "unknown badge launched a battle")
mapping.each do |badge, (source_id, _handler)|
  $game_map.map_id = 999
  before = recorded.length
  qa7_assert(!BlueHoennPilot.qa7_gym_battle(badge), "#{badge} started from another map")
  qa7_assert(recorded.length == before, "#{badge} dispatched from wrong map")

  $game_map.map_id = source_id + 600
  qa7_assert(BlueHoennPilot.qa7_gym_battle(badge), "#{badge} did not dispatch in correct gym")
  qa7_assert(recorded[-1] == badge, "#{badge} went to wrong handler")
end
qa7_assert(recorded == mapping.keys, "gym dispatch calls incomplete or duplicated")

# Region isolation: no gym call can run while another region is active.
$PokemonGlobal.blue_regions["current"] = "KANTO"
before = Marshal.dump($PokemonGlobal.blue_regions)
$game_map.map_id = 627
qa7_assert(!BlueHoennPilot.qa7_gym_battle(:STONE), "Stone badge handler leaked to Kanto")
qa7_assert(Marshal.dump($PokemonGlobal.blue_regions) == before, "Kanto save mutated")
qa7_assert(recorded.length == 8, "extra gym dispatched after region change")

# Save/load round-trip keeps map validation and original regional flags.
$PokemonGlobal.blue_regions["current"] = "HOENN"
$PokemonGlobal.blue_regions = Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
$game_map.map_id = 687
qa7_assert(BlueHoennPilot.qa7_gym_battle(:RAIN), "Juan dispatcher lost after save/reload")
qa7_assert(recorded.length == 9 && recorded[-1] == :RAIN, "reload duplicated wrong gym")
puts "HOENN_QA7_GYM_RUNTIME_OK"
