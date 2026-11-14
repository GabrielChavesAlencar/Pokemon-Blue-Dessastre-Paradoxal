# Hoenn teleport tool contract, simulated UI/transfer only; never Game.exe.
require "tmpdir"
require "fileutils"

module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args); true; end
end
module MenuHandlers
  @entries = {}
  def self.add(category, id, settings)
    @entries[[category,id]] = settings
  end
  def self.entries; @entries; end
end
class ChooseNumberParams
  attr_reader :range, :initial, :cancel
  def setRange(a,b); @range = [a,b]; end
  def setInitialValue(x); @initial=x; end
  def setCancelValue(x); @cancel=x; end
end
def _INTL(text,*args)
  args.each_with_index { |x,i| text=text.gsub("{#{i+1}}",x.to_s) }
  text
end
$messages=[]
$selections=[]
$chosen_number=0
$search_text=nil
$confirmation=true
def pbMessage(text,choices=nil,*_args)
  $messages << text
  choices ? ($selections.shift || -1) : true
end
def pbConfirmMessage(text)
  $messages << text
  $confirmation
end
def pbMessageChooseNumber(text,params)
  raise "numeric input out of bounds" unless params.range==[0,999]
  $messages << text
  $chosen_number
end
def pbEnterText(text,min,max)
  raise "search range invalid" unless [min,max]==[0,32]
  $messages << text
  $search_text
end
def pbFadeOutIn
  yield
end
def pbRgssExists?(path)
  path.match?(/\AData\/Map\d{3}\.rxdata\z/)
end
def check(value,message)
  raise "[HOENN_TELEPORT_QA] #{message}" unless value
end

class HoennQA12Global
  attr_accessor :blue_regions
end
class HoennQA12Map
  attr_accessor :map_id
  def initialize(map_id); @map_id=map_id; end
end
class HoennQA12Avatar
  attr_accessor :x,:y,:direction
  def initialize; @x=9;@y=6;@direction=2; end
end
class HoennQA12Temp
  attr_accessor :in_battle,:player_transferring,:transition_processing
  def initialize
    @in_battle=false;@player_transferring=false;@transition_processing=false
  end
end
class HoennQA12Scene
  def transfer_player; true; end
end
class HoennQA12Pokemon
  def egg?; false; end
end
class HoennQA12Player
  attr_accessor :party
  def initialize
    @party=[HoennQA12Pokemon.new]
  end
end
module BlueRegionTravel
  @transfers=[]
  def self.transfers; @transfers; end
  def self.move_to(point)
    raise "outside Hoenn" unless (700..898).include?(point[0])
    raise "failing transfer" if @fail_next
    $game_map.map_id=point[0]
    $game_player.x=point[1]
    $game_player.y=point[2]
    $game_player.direction=point[3]
    @transfers << point.dup
  end
  def self.fail_next=(value);@fail_next=value;end
end

require File.expand_path(ARGV.fetch(0))

menu=MenuHandlers.entries[[:pause_menu,:blue_hoenn_test_teleport]]
check(menu && menu["name"].include?("Testar Hoenn"),"menu must register")
mapped=Hash[(1..199).map { |mid| [mid,699+mid] }]
BlueHoennPilot.define_singleton_method(:metadata) { [[701,25,6],mapped] }
$PokemonGlobal=HoennQA12Global.new
$PokemonGlobal.blue_regions={"current"=>"HOENN","initial"=>"HOENN","leagues"=>[],"hoenn_pilot"=>{}}
$game_map=HoennQA12Map.new(700)
$game_player=HoennQA12Avatar.new
$game_temp=HoennQA12Temp.new
$scene=HoennQA12Scene.new
$player=HoennQA12Player.new

Dir.mktmpdir("hoenn-test-warp-") do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p("Data")
    File.write("Hoenn pilot.json","{}")
    File.write(BlueHoennPilot::MARKER,"BLUE_HOENN_PILOT_V1\n")
    File.open(BlueHoennPilot::TEST_STOPS_FILE,"w:UTF-8") do |file|
      file.puts "BLUE_HOENN_TEST_STOPS_V1"
      mapped.each { |source,native|
        file.puts "#{source}|#{native}|10|8|2|Mapa de teste #{source}"
      }
    end
    check(BlueHoennPilot.test_tools?,"test menu should be visible in Hoenn copy")
    check(menu["condition"].call(nil),"pause menu condition false")
    stops=BlueHoennPilot.test_stops
    check(stops.length==199 && stops.first[0]==1 && stops.last[0]==199,
          "all 199 original maps must be accessible")
    check(BlueHoennPilot.test_teleport([200,999,1,1,2,"forged"])==false,
          "unknown MapID accepted")
    state_before=Marshal.dump($PokemonGlobal.blue_regions)
    target=stops[46]
    check(BlueHoennPilot.test_teleport(target),"legitimate QA teleport failed")
    check($game_map.map_id==746 && [$game_player.x,$game_player.y]==[10,8],
          "teleport coordinates or remapping wrong")
    check(Marshal.dump($PokemonGlobal.blue_regions)==state_before,
          "test teleport changed badges, story or regional state")
    check(BlueHoennPilot.test_return,"return-to-last-map unavailable")
    check($game_map.map_id==700 && [$game_player.x,$game_player.y]==[9,6],
          "return did not restore old coordinates")
    check(Marshal.dump($PokemonGlobal.blue_regions)==state_before,
          "return changed story flags")
    $chosen_number=199
    check(BlueHoennPilot.test_number[0]==199,"original MapID lookup")
    $chosen_number=748
    check(BlueHoennPilot.test_number[0]==49,"remapped native MapID lookup")
    $chosen_number=999
    check(BlueHoennPilot.test_number.nil?,"foreign map 999 available")
    $search_text="Mapa de teste 75"
    $selections << 0
    check(BlueHoennPilot.test_search[0]==75,"search by name must select map")
    $selections << 0
    check(BlueHoennPilot.test_group[0]==1,"group selection invalid")
    $selections += [0,0,5]
    check(BlueHoennPilot.test_menu,"interactive menu fails")
    check(BlueRegionTravel.transfers.length>=3,"interactive menu did not transfer")
    $game_temp.in_battle=true
    check(!BlueHoennPilot.test_tools?,"battle bypasses test-only guard")
    $game_temp.in_battle=false
    $PokemonGlobal.blue_regions["current"]="KANTO"
    check(!BlueHoennPilot.test_tools?,"Kanto incorrectly exposes Hoenn test menu")
    $PokemonGlobal.blue_regions["current"]="HOENN"
    $player.party=[]
    check(!BlueHoennPilot.test_teleport(target),"empty party allowed dangerous wild battle")
    $player.party=[HoennQA12Pokemon.new]
    $confirmation=false
    check(!BlueHoennPilot.test_teleport(target),"declined confirmation transferred")
    $confirmation=true
    File.open(BlueHoennPilot::TEST_STOPS_FILE,"a:UTF-8") { |file| file.puts "999|999|1|1|2|foreign" }
    BlueHoennPilot.instance_variable_set(:@test_stops,nil)
    check(BlueHoennPilot.test_stops.empty?,"altered/foreign manifest accepted")
    check(!BlueHoennPilot.test_menu,"invalid catalog should not open")
  end
end
puts "HOENN_QA_TELEPORT_199_RUNTIME_OK"
