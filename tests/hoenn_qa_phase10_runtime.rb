# QA10: real BlueRegions circuit methods + isolated BlueHoennPilot finale.
# Synthetic map/global fixtures ONLY. No Game.exe, Hall animation or travel.
module BlueRegionData
  CIRCUIT = %w[DECADES KANTO JOHTO HOENN SINNOH UNOVA KALOS ALOLA GALAR PALDEA].freeze
  REGISTRY = {
    "circuit" => CIRCUIT,
    "regions" => Hash[CIRCUIT.map { |key| [key, {"name"=>key,"milestones"=>(key=="HOENN" ? %w[STONE KNUCKLE DYNAMO HEAT BALANCE FEATHER MIND RAIN] : [])}] }],
    "hisui" => {"startExits"=>["SINNOH","DECADES"], "questRegion"=>"SINNOH"}
  }
end
require File.expand_path(ARGV.fetch(1))
module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args); true; end
end
class QA10Global; attr_accessor :blue_regions; end
class QA10Map; attr_accessor :map_id; end
def _INTL(str,*args)
  args.each_with_index{|v,i|str=str.gsub("{#{i+1}}",v.to_s)}
  str
end
$messages=[]
def pbMessage(str,*_args); $messages << str; true; end
def assert10(condition,message)
  raise "[HOENN_QA10] #{message}" unless condition
end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],Hash[(1..322).map{|src|[src,src+600]}]]
end
$PokemonGlobal=QA10Global.new
$PokemonGlobal.blue_regions=BlueRegions.new_state("HOENN")
$game_map=QA10Map.new
$game_map.map_id=699
flags=BlueHoennPilot.state
region=$PokemonGlobal.blue_regions
assert10(BlueRegions.unlocked(region)==BlueRegions.circuit,
         "Free transport catalogue still requires a League")
assert10(!BlueHoennPilot.qa10_hall_ready?,"Hall open without badges, Wally and Elite")
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Hall completed too early")
assert10(!flags["hoenn_hall_of_fame"],"Local flag given before Champion")
assert10(region["leagues"].empty?,"League given before Champion")
flags["champion_wallace_defeated"]=true
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Champion flag alone bypasses Elite")
flags["wally_road_defeated"]=true
%w[sidney phoebe glacia drake].each{|key|flags["elite_#{key}_defeated"]=true}
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Eight badges required even with forged Elite flags")
region["achievements"]["HOENN"]=%w[STONE KNUCKLE DYNAMO HEAT BALANCE FEATHER MIND RAIN]
assert10(BlueHoennPilot.qa10_hall_ready?,"Hall ready after all genuine milestones")
$game_map.map_id=698
assert10(!BlueHoennPilot.qa10_hall_ready?,"Hall triggered from Wallace room")
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Wallace room completed League")
$game_map.map_id=699
assert10(!BlueHoennPilot.qa10_postgame_status,"Status available before finale")
assert10(BlueHoennPilot.hall_of_fame_stage10,"Hall completion not recorded")
assert10(flags["hoenn_hall_of_fame"],"Local Hall flag missing")
assert10(region["leagues"]==["HOENN"],"Hoenn completion missing or duplicated")
assert10(BlueRegions.unlocked(region)==BlueRegions.circuit,
         "Hall improperly changed the already-free transport catalogue")
assert10(!region.key?("decades_return"),"Travel happened automatically")
assert10($messages.any?{|s|s.include?("viagem pelo NPC")},"Post-game transport notice not shown")
assert10(BlueHoennPilot.hall_of_fame_stage10,"Hall should allow safe reinteraction")
assert10(region["leagues"]==["HOENN"],"Reentry granted another League")
$game_map.map_id=922
assert10(BlueHoennPilot.sign_stage10(:LEAGUE_GATE),"Postgame League sign unavailable")
assert10($messages.last.include?("viagem pelo NPC"),"Sign no postgame status")
assert10(region["leagues"]==["HOENN"],"Sign mutates League state")
$game_map.map_id=699

# Same save survives serialization and tracks the completed circuit state.
$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
region=$PokemonGlobal.blue_regions
flags=BlueHoennPilot.state
assert10(BlueRegions.unlocked(region)==BlueRegions.circuit,
         "Free region catalogue was lost on reload")
assert10(BlueHoennPilot.hall_of_fame_stage10,"Hall progression lost on reload")
assert10(region["leagues"]==["HOENN"],"Save reload duplicated League")

# A locally marked Hall flag in an older QA save can be reconciled only
# AFTER rechecking physical Map99 + all wins. No bootstrap from arbitrary data.
region["leagues"].clear
flags["hoenn_hall_of_fame"]=true
assert10(BlueHoennPilot.hall_of_fame_stage10,"Old Hall flag could not be reconciled")
assert10(region["leagues"]==["HOENN"],"Older Hoenn save not reconciled")

# Previously completed regional League never creates duplicate entries.
flags["hoenn_hall_of_fame"]=false
assert10(BlueHoennPilot.hall_of_fame_stage10,"Existing circuit completion not reconciled")
assert10(region["leagues"]==["HOENN"],"Duplicate Hoenn completion created")

# An unlocked Hoenn from a completed Johto campaign must preserve Johto
# and add Sinnoh; it cannot overwrite the previous region's achievements.
$PokemonGlobal.blue_regions=BlueRegions.new_state("JOHTO")
region=$PokemonGlobal.blue_regions
region["leagues"] << "JOHTO"
region["achievements"]["JOHTO"]=["ZEPHYR"]
region["current"]="HOENN"
flags=BlueHoennPilot.state
region["achievements"]["HOENN"]=BlueHoennPilot::QA8_LEAGUE_BADGES.dup
flags["wally_road_defeated"]=true
flags["champion_wallace_defeated"]=true
%w[sidney phoebe glacia drake].each{|key|flags["elite_#{key}_defeated"]=true}
assert10(BlueHoennPilot.hall_of_fame_stage10,"Started Johto, Hoenn victory not registered")
assert10(region["leagues"]==["JOHTO","HOENN"],"Johto League overwritten")
assert10(region["achievements"]["JOHTO"]==["ZEPHYR"],"Johto badges overwritten")
assert10(BlueRegions.unlocked(region)==BlueRegions.circuit,
         "Johto's previous League must not restrict free transport")

# A completed League cannot be awarded by an event outside its region.
# Starting in Kanto is valid; the player must actually travel to Hoenn.
$PokemonGlobal.blue_regions=BlueRegions.new_state("KANTO")
region=$PokemonGlobal.blue_regions
region["achievements"]["HOENN"]=BlueHoennPilot::QA8_LEAGUE_BADGES.dup
# The Hoenn plugin correctly returns nil for its active state while standing
# in Kanto, even when old Hoenn milestone flags exist in this shared save.
flags=region["hoenn_pilot"]={}
assert10(BlueHoennPilot.state.nil?, "Hoenn event script ran in Kanto")
flags["wally_road_defeated"]=true
flags["champion_wallace_defeated"]=true
%w[sidney phoebe glacia drake].each{|key|flags["elite_#{key}_defeated"]=true}
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Hoenn Hall awarded while current region was Kanto")
assert10(region["leagues"].empty? && !flags["hoenn_hall_of_fame"],"Wrong-region Hall saved a victory")

region["current"]="DECADES"
before=Marshal.dump(region)
assert10(!BlueHoennPilot.hall_of_fame_stage10,"Decades Hall falsely triggered")
assert10(!BlueHoennPilot.qa10_postgame_status,"Decades postgame status leaked")
assert10(Marshal.dump(region)==before,"Decades state mutated")
puts "HOENN_QA10_HALL_CIRCUIT_RUNTIME_OK"
