# Regression of connected-map agent dispatch against the real RegionTravel.rb.
# No game executable, native map, saves, JoiPlay or external region files.
source = File.expand_path(ARGV.fetch(0))
load source
def verify(condition, message)
  raise "REGION_MAP_HITCH: #{message}" unless condition
end
FakeMap = Struct.new(:map_id)
FakeGlobal = Struct.new(:blue_regions)
$PokemonGlobal = FakeGlobal.new(nil)
$data_mapinfos = Array.new(900)
checks = Hash.new(0)
events = []
BlueRegionStart = Module.new
BlueRegionStart.define_singleton_method(:johto_agent_point) { [902, 10, 11, 2] }
BlueRegionStart.define_singleton_method(:hoenn_town_point) { [903, 5, 6, 2] }
BlueRegionTravel.define_singleton_method(:decades_city_map_id) do
  checks[:decades_id] += 1
  77
end
BlueRegionTravel.define_singleton_method(:installed?) do
  checks[:kanto_install] += 1
  checks[:permit_kanto] != 0
end
BlueRegionTravel.define_singleton_method(:kanto_town_point) do
  checks[:kanto_id] += 1
  [901, 18, 8, 2]
end
BlueRegionTravel.define_singleton_method(:johto_installed?) do
  checks[:johto_install] += 1
  true
end
BlueRegionTravel.define_singleton_method(:hoenn_installed?) do
  checks[:hoenn_install] += 1
  true
end
%w[decades kanto johto hoenn].each do |name|
  BlueRegionTravel.define_singleton_method("attach_#{name}_agent") do |map|
    events << [name.upcase, map.map_id]
  end
end

# No save loaded: only the original Decades town can show the default agent.
100.times { |n| BlueRegionTravel.attach_agents(FakeMap.new(1000 + n)) }
verify(checks[:decades_id] == 1, "Decades target scanned on each connected route")
BlueRegionTravel.attach_agents(FakeMap.new(77))
verify(events == [["DECADES", 77]], "Decades agent did not stay in its real town")

# No shortcut from a forged/invalid regional save.
$PokemonGlobal.blue_regions = {"version" => 0, "current" => "KANTO"}
BlueRegionTravel.attach_agents(FakeMap.new(901))
verify(events.length == 1, "invalid regional state created an agent")
$PokemonGlobal.blue_regions = {"version" => 1, "current" => "KANTO"}
BlueRegionTravel.attach_agents(FakeMap.new(1000))
verify(checks[:kanto_install] == 1 && checks[:kanto_id] == 0,
       "a missing Kanto integration was accepted")
checks[:permit_kanto] = 1
BlueRegionTravel.attach_agents(FakeMap.new(500))
verify(checks[:kanto_install] == 2 && checks[:kanto_id] == 1,
       "failed integration result was cached or Kanto target was not resolved")
100.times { |n| BlueRegionTravel.attach_agents(FakeMap.new(1000 + n)) }
verify(checks[:kanto_install] == 2 && checks[:kanto_id] == 1,
       "Kanto verified all source maps for every connected route")
verify(events.length == 1, "regional NPC appeared outside its town")
BlueRegionTravel.attach_agents(FakeMap.new(901))
verify(events.last == ["KANTO", 901], "verified Kanto agent missing at Pallet")

# Switch regions within one process; routing cache cannot leak agents.
$PokemonGlobal.blue_regions = {"version" => 1, "current" => "JOHTO"}
BlueRegionTravel.attach_agents(FakeMap.new(901))
100.times { |n| BlueRegionTravel.attach_agents(FakeMap.new(1000 + n)) }
verify(checks[:johto_install] == 1, "Johto gate checked for every map")
BlueRegionTravel.attach_agents(FakeMap.new(902))
verify(events.last == ["JOHTO", 902], "Johto destination mismatch")

$PokemonGlobal.blue_regions = {"version" => 1, "current" => "HOENN"}
BlueRegionTravel.attach_agents(FakeMap.new(902))
100.times { |n| BlueRegionTravel.attach_agents(FakeMap.new(1000 + n)) }
verify(checks[:hoenn_install] == 1, "Hoenn verified its installed maps on every route")
BlueRegionTravel.attach_agents(FakeMap.new(903))
verify(events.last == ["HOENN", 903], "Hoenn destination mismatch")
verify(events == [["DECADES", 77], ["KANTO", 901], ["JOHTO", 902], ["HOENN", 903]],
       "unexpected event insertion or cross-region route")
puts "PASS: 400+ connected-map setups, authorized regional NPCs and zero repeated positive scans"
