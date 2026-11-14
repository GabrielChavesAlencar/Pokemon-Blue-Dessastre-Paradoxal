# QA09 pure Ruby contract: Elite Four order, Wallace and regional isolation.
# This is NOT the native Blue Game.exe and cannot certify real battles.
class QA9Global; attr_accessor :blue_regions; end
class QA9Player
  attr_accessor :party
  attr_reader :heals
  def initialize; @party = [:TREECKO,:GARDEVOIR]; @heals=0; end
  def heal_party; @heals+=1; end
end
class QA9Map; attr_accessor :map_id; end
class QA9Avatar
  attr_accessor :x,:y,:direction
  def initialize; @x,@y,@direction=8,7,2; end
  def moveto(x,y); @x,@y=x,y; end
end
module BlueRegions
  def self.local_achievements(region_state, key)
    region_state.fetch("achievements",{}).fetch(key,[])
  end
end
module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args); true; end
end
module TrainerBattle
  @calls=[]
  class << self
    attr_accessor :result
    attr_reader :calls
    def start(*args); @calls << args; @result != false; end
  end
end
module BlueRegionTravel
  def self.move_to(point)
    $game_map.map_id=point[0]
    $game_player.moveto(point[1],point[2])
    $game_player.direction=point[3]
    true
  end
end
$messages=[]
$rules=[]
def pbFadeOutIn;yield;end
def setBattleRule(rule);$rules<<rule;end
def pbMessage(msg,*_args);$messages<<msg;end
def _INTL(msg,*v);v.each_with_index{|x,i|msg=msg.gsub("{#{i+1}}",x.to_s)};msg;end
def verify9(ok,msg);raise "[HOENN_QA9] #{msg}" unless ok;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],Hash[(1..322).map{|src|[src,src+600]}]]
end
$PokemonGlobal=QA9Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=QA9Player.new
$game_map=QA9Map.new
$game_map.map_id=894
$game_player=QA9Avatar.new

old=Marshal.dump($PokemonGlobal.blue_regions)
verify9(!BlueHoennPilot.qa9_elite_unlocked?(0),"Elite opened outside Hoenn")
verify9(!BlueHoennPilot.elite_four(0),"Sidney callable in Decades")
verify9(!BlueHoennPilot.stage10_transfer(94,95,8,7),"league warp leaked to Decades")
verify9(Marshal.dump($PokemonGlobal.blue_regions)==old,"Decades state altered")

$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["RAIN"]},
  "hoenn_pilot"=>{"wally_road_defeated"=>true},
}
flags=BlueHoennPilot.state
verify9(!BlueHoennPilot.qa9_elite_unlocked?(0),"RAIN alone bypassed all badges")
verify9(!BlueHoennPilot.elite_four(0),"Sidney started without eight badges")
$PokemonGlobal.blue_regions["achievements"]["HOENN"]=BlueHoennPilot::QA8_LEAGUE_BADGES.dup
flags["wally_road_defeated"]=false
verify9(!BlueHoennPilot.qa9_elite_unlocked?(0),"Wally can be skipped")
flags["wally_road_defeated"]=true
verify9(BlueHoennPilot.qa9_elite_unlocked?(0),"Sidney remained locked")
verify9(!BlueHoennPilot.qa9_elite_unlocked?(1),"Phoebe opened before Sidney")

# A forged Drake flag cannot replace the missing first three victories.
flags["elite_drake_defeated"]=true
$game_map.map_id=898
verify9(!BlueHoennPilot.qa9_champion_unlocked?,"Wallace unlocked via forged Drake flag")
verify9(!BlueHoennPilot.champion_wallace,"Wallace callable without previous Elite")
flags.delete("elite_drake_defeated")

$game_map.map_id=900 # League corridor; direct boss call must not work.
verify9(!BlueHoennPilot.elite_four(0),"Sidney callable from League lobby")
verify9(TrainerBattle.calls.empty?,"invalid challenge executed a battle")
verify9(!BlueHoennPilot.stage10_transfer(100,95,8,7),"Phoebe warp skipped Sidney")
verify9(BlueHoennPilot.stage10_transfer(100,94,8,7),"Sidney room not accessible")
verify9($game_map.map_id==894,"Sidney room mapped incorrectly")

TrainerBattle.result=false
verify9(!BlueHoennPilot.elite_four(0),"Sidney defeat counted as victory")
verify9(!flags["elite_sidney_defeated"],"Sidney flag set after loss")
verify9(!BlueHoennPilot.stage10_transfer(94,95,8,7),"Phoebe opened after Sidney loss")
TrainerBattle.result=true
verify9(BlueHoennPilot.elite_four(0),"Sidney victory not saved")
verify9(flags["elite_sidney_defeated"],"Sidney flag missing")
verify9(BlueHoennPilot.elite_four(0),"Sidney completed interaction not idempotent")
verify9(TrainerBattle.calls.count([:BLUE_HOENN_ELITE,"Sidney",1094])==2,
        "Sidney trainer battle repeated after victory")

verify9(!BlueHoennPilot.qa9_elite_unlocked?(2),"Glacia opened without Phoebe")
verify9(!BlueHoennPilot.stage10_transfer(94,96,8,7),"Glacia warp skipped Phoebe")
verify9(BlueHoennPilot.stage10_transfer(94,95,8,7),"Phoebe room stayed locked")
verify9(BlueHoennPilot.elite_four(1),"Phoebe win not recorded")
verify9(BlueHoennPilot.stage10_transfer(95,96,8,7),"Glacia room not accessible")
verify9(BlueHoennPilot.elite_four(2),"Glacia win not recorded")
verify9(!BlueHoennPilot.qa9_champion_unlocked?,"Wallace before Drake")
verify9(!BlueHoennPilot.stage10_transfer(96,98,8,7),"Wallace warp bypassed Drake")
verify9(BlueHoennPilot.stage10_transfer(96,97,8,7),"Drake room not accessible")
verify9(BlueHoennPilot.elite_four(3),"Drake win not recorded")
verify9(BlueHoennPilot.qa9_champion_unlocked?,"Wallace still locked after full Elite")
verify9(!BlueHoennPilot.champion_wallace,"Wallace fight started in Drake room")
verify9(BlueHoennPilot.stage10_transfer(97,98,8,7),"Champion room did not open")
TrainerBattle.result=false
verify9(!BlueHoennPilot.champion_wallace,"Wallace loss counted as win")
verify9(!flags["champion_wallace_defeated"],"Wallace flag persisted after loss")
verify9(!BlueHoennPilot.stage10_transfer(98,99,9,18),"Hall opened without defeating Wallace")
TrainerBattle.result=true
verify9(BlueHoennPilot.champion_wallace,"Wallace victory not recorded")
verify9(BlueHoennPilot.champion_wallace,"Wallace interaction replay not idempotent")
verify9(TrainerBattle.calls.count([:BLUE_HOENN_CHAMPION,"Wallace",1098])==2,
        "Wallace battled after victory")
verify9(BlueHoennPilot.stage10_transfer(98,99,9,18),"Hall not reachable after Wallace")
verify9($game_map.map_id==899,"Hall map ID wrong")
verify9(!flags["hoenn_hall_of_fame"],"QA09 must not pre-mark Phase10 Hall of Fame")
verify9(TrainerBattle.calls.length==7,"Wrong number of battle attempts")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
verify9(BlueHoennPilot.qa9_champion_unlocked?,"Elite wins lost on save reload")
verify9(BlueHoennPilot.state["champion_wallace_defeated"],"Wallace win lost on reload")
$PokemonGlobal.blue_regions["current"]="JOHTO"
save=Marshal.dump($PokemonGlobal.blue_regions)
$game_map.map_id=898
verify9(!BlueHoennPilot.champion_wallace,"Wallace leaked into Johto")
verify9(!BlueHoennPilot.elite_four(0),"Sidney leaked into Johto")
verify9(!BlueHoennPilot.stage10_transfer(98,99,9,18),"Hall leaked into Johto")
verify9(Marshal.dump($PokemonGlobal.blue_regions)==save,"Johto save mutated")
puts "HOENN_QA9_ELITE_CHAMPION_RUNTIME_OK"
