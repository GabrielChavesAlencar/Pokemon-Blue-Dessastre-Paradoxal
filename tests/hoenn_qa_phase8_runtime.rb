# QA08: simulated Ruby story/field gates. NO Game.exe or donor ZIP.
class QA8Global; attr_accessor :blue_regions; end
class QA8Pokemon
  attr_accessor :known_moves
  def initialize; @known_moves=[]; end
  def hasMove?(move); @known_moves.include?(move); end
end
class QA8Player
  attr_accessor :party
  attr_reader :healed
  def initialize; @party=[QA8Pokemon.new]; @healed=0; end
  def heal_party; @healed+=1; end
end
class QA8Bag
  attr_reader :items
  def initialize; @items={HM07:1}; end
  def has?(id); @items.fetch(id,0)>0; end
end
module GameData
  module Item
    Rec=Struct.new(:move)
    def self.exists?(id); id==:HM07; end
    def self.get(id); Rec.new(id==:HM07 ? :WATERFALL : nil); end
  end
end
module BlueRegions
  def self.local_achievements(save,region)
    save.fetch("achievements",{}).fetch(region,[])
  end
end
module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args);true;end
end
module TrainerBattle
  @calls=[]
  class << self
    attr_accessor :result
    attr_reader :calls
    def start(*args); @calls << args; @result != false; end
  end
end
class QA8Map; attr_accessor :map_id; end
class QA8Avatar
  attr_accessor :x,:y,:direction
  def initialize; @x,@y,@direction=1,1,2; end
  def moveto(x,y); @x,@y=x,y; end
end
module BlueRegionTravel
  def self.move_to(pos)
    $game_map.map_id=pos[0]
    $game_player.moveto(pos[1],pos[2])
    $game_player.direction=pos[3]
    true
  end
end
def pbFadeOutIn; yield; end
def setBattleRule(_x); end
def pbMessage(msg,*_args); $qa8_messages << msg; end
def _INTL(s,*v); v.each_with_index {|x,i|s=s.gsub("{#{i+1}}",x.to_s)};s; end
def check8(cond,msg); raise "[HOENN_QA8] #{msg}" unless cond; end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],Hash[(1..322).map{|src|[src,src+600]}]]
end
$qa8_messages=[]
$PokemonGlobal=QA8Global.new
$PokemonGlobal.blue_regions={"initial"=>"HOENN","current"=>"DECADES","achievements"=>{},
  "hoenn_pilot"=>{}}
$player=QA8Player.new
$bag=QA8Bag.new
$game_map=QA8Map.new
$game_player=QA8Avatar.new
$game_map.map_id=850
before=Marshal.dump($PokemonGlobal.blue_regions)
check8(!BlueHoennPilot.qa8_league_badges?, "eight badge check leaked to Decades")
check8(!BlueHoennPilot.wally_victory_road, "Wally leaked to Decades")
check8(!BlueHoennPilot.stage10_transfer(250,322,5,5), "league transfer leaked to Decades")
check8(Marshal.dump($PokemonGlobal.blue_regions)==before,"Decades save polluted")

$PokemonGlobal.blue_regions={
  "initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>%w[RAIN]},
  "hoenn_pilot"=>{}
}
flags=BlueHoennPilot.state
check8(!BlueHoennPilot.qa8_league_badges?, "RAIN alone bypasses all eight badges")
check8(!BlueHoennPilot.wally_victory_road,"Wally launched with only RAIN")
check8(TrainerBattle.calls.empty?,"Wally entered battle with one badge")
$game_map.map_id=691
check8(!BlueHoennPilot.stage10_transfer(91,250,7,7),"unearned road entry")
$PokemonGlobal.blue_regions["achievements"]["HOENN"]=BlueHoennPilot::QA8_LEAGUE_BADGES.dup
check8(BlueHoennPilot.qa8_league_badges?,"eight Hoenn badges not detected")
check8(!BlueHoennPilot.stage10_transfer(91,250,7,7),"waterfall HM alone bypassed move")
$player.party.first.known_moves << :WATERFALL
check8(BlueHoennPilot.stage10_transfer(91,250,7,7),"full waterfall prerequisites did not open road")
check8($game_map.map_id==850,"Victory Road mapped entry incorrect")
check8(!BlueHoennPilot.stage10_transfer(250,322,5,5),"unbeaten Wally bypassed road exit")
check8(BlueHoennPilot.stage10_transfer(250,251,5,5),"road descent improperly gated")
check8(BlueHoennPilot.stage10_transfer(251,252,5,5),"B2F descent improperly gated")
check8(BlueHoennPilot.stage10_transfer(252,251,5,5),"B2F retreat softlocked")
check8(BlueHoennPilot.stage10_transfer(251,250,5,5),"Victory Road retreat softlocked")
check8(!BlueHoennPilot.stage10_transfer(250,322,5,5),"Wally exit ignored again")
TrainerBattle.result=false
check8(!BlueHoennPilot.wally_victory_road,"Wally loss counted as win")
check8(!flags["wally_road_defeated"],"Wally flag set on loss")
check8(!BlueHoennPilot.stage10_transfer(250,322,5,5),"loss opened league exit")
TrainerBattle.result=true
$game_map.map_id=851
check8(!BlueHoennPilot.wally_victory_road,"Wally triggered outside Map250")
$game_map.map_id=850
check8(BlueHoennPilot.wally_victory_road,"Wally victory not recorded")
check8(flags["wally_road_defeated"],"Wally win flag absent")
check8(BlueHoennPilot.wally_victory_road,"Wally after victory not idempotent")
check8(TrainerBattle.calls.count([:BLUE_HOENN_WALLY,"Wally",1025])==2,
       "Wally fought extra battles or wrong PBS version")
check8(BlueHoennPilot.stage10_transfer(250,322,5,5),"Victor cannot exit Victory Road")
check8($game_map.map_id==922,"Ever Grande north destination incorrect")
check8(BlueHoennPilot.stage10_transfer(322,93,5,5),"League not reachable after Wally")
$PokemonGlobal.blue_regions["achievements"]["HOENN"].delete("STONE")
$game_map.map_id=922
check8(!BlueHoennPilot.stage10_transfer(322,93,5,5),"League accepted seven local badges")
$PokemonGlobal.blue_regions["achievements"]["HOENN"]<< "STONE"

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
check8(BlueHoennPilot.qa8_league_badges?,"eight badges lost on reload")
check8(BlueHoennPilot.state["wally_road_defeated"],"Wally victory lost on reload")
$PokemonGlobal.blue_regions["current"]="KANTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
$game_map.map_id=850
check8(!BlueHoennPilot.wally_victory_road,"Wally triggered from Kanto")
check8(!BlueHoennPilot.stage10_transfer(250,322,5,5),"Kanto league transfer allowed")
check8(Marshal.dump($PokemonGlobal.blue_regions)==before,"Kanto save mutated")
puts "HOENN_QA8_VICTORY_ROAD_RUNTIME_OK"
