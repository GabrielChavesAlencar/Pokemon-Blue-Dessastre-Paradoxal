# Stage 07 isolated Ruby scenario tests. Never runs Game.exe or writes saves.
class H7Global;attr_accessor :blue_regions;end
class H7Player
  attr_accessor :party
  attr_reader :heals
  def initialize;@party=[:TREECKO];@heals=0;end
  def heal_party;@heals+=1;end
end
class H7Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize;@items=Hash.new(0);@can_add=true;end
  def has?(k);@items[k]>0;end
  def add(k,n=1);return false unless @can_add;@items[k]+=n;true;end
  def remove(k,n=1);return false if @items[k]<n;@items[k]-=n;true;end
end
module GameData
  module Item
    ItemRec=Struct.new(:move)
    @ids={METEORITE_RSE:nil,TM50: :OVERHEAT}
    def self.exists?(key);@ids.key?(key);end
    def self.get(key);ItemRec.new(@ids.fetch(key));end
  end
end
module BlueRegions
  def self.local_achievements(state,region)
    state.fetch("achievements",{}).fetch(region,[])
  end
  def self.award(state,region,key)
    return false unless state["initial"]=="HOENN"&&
                        state["current"]=="HOENN"&&region=="HOENN"&&key=="HEAT"
    badges=(state["achievements"]["HOENN"]||=[])
    return false if badges.include?(key)
    badges << key
    true
  end
end
module BlueRegionStart;def self.select_and_prepare;false;end;end
module EventHandlers;def self.add(*args);true;end;end
module TrainerBattle
  @history=[]
  class << self
    attr_accessor :result
    attr_reader :history
    def start(*params)
      @history<<params
      @result!=false
    end
  end
end
class H7Event
  attr_reader :count
  def initialize;@count=0;end
  def refresh;@count+=1;end
end
class H7Map
  attr_accessor :map_id,:events
  def initialize;@map_id=721;@events={12=>H7Event.new};end
end
class H7Avatar
  attr_accessor :x,:y,:direction
  def initialize;@x,@y,@direction=8,9,2;end
  def moveto(x,y);@x,@y=x,y;end
end
class H7Temp
  attr_accessor :in_battle
  def initialize;@in_battle=false;end
end
module BlueRegionTravel
  @history=[]
  class << self
    attr_accessor :failure
    attr_reader :history
    def move_to(point)
      raise "travessia simulada falhou" if @failure
      @history<<point
      $game_map.map_id=point[0]
      $game_player.moveto(point[1],point[2])
      $game_player.direction=point[3]
      true
    end
  end
end
$messages=[]
def _INTL(text,*args)
  args.each_with_index{|value,i|text=text.gsub("{#{i+1}}",value.to_s)}
  text
end
def pbMessage(s,*args);$messages<<s;0;end
def pbConfirmMessage(s);$messages<<s;true;end
def pbFadeOutIn;yield;end
def setBattleRule(s);end
def check7(ok,reason);raise "[HOENN_STAGE7] #{reason}" unless ok;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],{63=>763,121=>721,122=>722,179=>779,178=>778}]
end
$PokemonGlobal=H7Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=H7Player.new
$bag=H7Bag.new
$game_map=H7Map.new
$game_player=H7Avatar.new
$game_temp=H7Temp.new
$game_self_switches={}
$scene=Object.new

original=Marshal.dump($PokemonGlobal.blue_regions)
check7(!BlueHoennPilot.meteor_falls_ambush,"Meteor story leaked into Decades")
check7(!BlueHoennPilot.magma_grunt(1),"Magma leaked into Decades")
check7(!BlueHoennPilot.flannery,"Heat badge leaked into Decades")
check7(!BlueHoennPilot.cable_car,"Cable travel leaked into Decades")
check7(Marshal.dump($PokemonGlobal.blue_regions)==original,"Decades save changed")
$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["STONE","KNUCKLE","DYNAMO"]},
  "hoenn_pilot"=>{"stern_package_delivered"=>true}
}
flags=BlueHoennPilot.state
check7(!BlueHoennPilot.heat_badge?,"Heat badge preset")
check7(!BlueHoennPilot.cable_car,"Cable car ignored Meteor Falls story")
check7(!BlueHoennPilot.maxie,"Maxie fought before Tabitha")
check7(!BlueHoennPilot.flannery,"Flannery fought before Meteorite")
check7(BlueHoennPilot.meteor_falls_ambush,"Meteor Falls scene didn't mark theft")
check7(flags["meteorite_stolen"],"Theft flag missing")
check7(!BlueHoennPilot.meteor_falls_ambush,"Meteor scene duplicated")
check7(BlueHoennPilot.magma_blocker(12),"Magma blockers did not clear")
check7($game_self_switches[[721,12,"A"]],"Blocker self switch not set")
check7(flags["cable_car_unlocked"],"Teleferico unlock not saved")
$game_map.map_id=722
check7(BlueHoennPilot.cable_car,"Cable lower station failed")
check7($game_map.map_id==779,"Cable car arrived wrong summit map")
check7(flags["mt_chimney_visited"],"Summit visit flag missing")
check7(BlueHoennPilot.cable_car,"Cable return failed")
check7($game_map.map_id==722,"Cable returned to wrong station")
BlueRegionTravel.failure=true
prior=[$game_map.map_id,$game_player.x,$game_player.y]
check7(!BlueHoennPilot.cable_car,"Failed cable transfer returned success")
check7(prior==[$game_map.map_id,$game_player.x,$game_player.y],
       "Failed cable transfer moved the player")
BlueRegionTravel.failure=false
$game_map.map_id=778
check7(!BlueHoennPilot.tabitha,"Tabitha bypassed grunts")
TrainerBattle.result=false
check7(!BlueHoennPilot.magma_grunt(1),"Magma loss counted as win")
check7(!flags["magma_grunt_1_defeated"],"Magma defeat flag on loss")
TrainerBattle.result=true
check7(BlueHoennPilot.magma_grunt(1),"First Magma win failed")
check7(BlueHoennPilot.magma_grunt(2),"Second Magma win failed")
check7(!BlueHoennPilot.magma_grunt(2),"Second grunt replayed")
TrainerBattle.result=false
check7(!BlueHoennPilot.tabitha,"Tabitha loss counted as win")
check7(!flags["tabitha_defeated"],"Tabitha granted on loss")
TrainerBattle.result=true
check7(BlueHoennPilot.tabitha,"Tabitha win not recorded")
check7(!BlueHoennPilot.tabitha,"Tabitha replayed")
TrainerBattle.result=false
check7(!BlueHoennPilot.maxie,"Maxie loss counted as win")
check7(!flags["maxie_defeated"],"Maxie win set on loss")
TrainerBattle.result=true
check7(BlueHoennPilot.maxie,"Maxie win failed")
check7(!BlueHoennPilot.maxie,"Maxie replayed")
$bag.can_add=false
check7(!BlueHoennPilot.meteorite_machine,"Meteorite granted with full bag")
check7(!flags["meteorite_recovered"],"Meteorite flag set despite full bag")
$bag.can_add=true
check7(BlueHoennPilot.meteorite_machine,"Meteorite recovery failed")
check7($bag.items[:METEORITE_RSE]==1,"Meteorite missing")
check7(!BlueHoennPilot.meteorite_machine,"Meteorite duplicated")
$game_map.map_id=763
TrainerBattle.result=false
check7(!BlueHoennPilot.flannery,"Flannery loss counted as win")
check7(!BlueHoennPilot.heat_badge?,"Heat badge on loss")
TrainerBattle.result=true
$bag.can_add=false
check7(BlueHoennPilot.flannery,"Flannery win didn't register badge")
check7(BlueHoennPilot.heat_badge?,"Heat badge missing")
check7(BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")==
       ["STONE","KNUCKLE","DYNAMO","HEAT"],"Wrong Hoenn achievement count")
check7(!flags["flannery_tm_given"],"Full bag wrongly saved Overheat")
$bag.can_add=true
check7(BlueHoennPilot.flannery,"Deferred Overheat TM missing")
check7($bag.items[:TM50]==1,"TM Overheat missing")
check7(!BlueHoennPilot.flannery,"Flannery TM duplicated")
check7(TrainerBattle.history.count([:BLUE_HOENN_FLANNERY,"Flannery",763])==2,
       "Flannery fought twice after win")
check7(BlueHoennPilot.gym_steam_vent(37,24),"Gym vent could not move")
check7([$game_player.x,$game_player.y]==[37,24],"Gym vent position wrong")
check7(!BlueHoennPilot.gym_steam_vent(50,50),"Unlisted vent was accepted")
check7(!BlueHoennPilot.stage7_future_gate(:MAGMA_HIDEOUT),"Hideout incorrectly unlocked")
check7(BlueHoennPilot.sign_stage7(:LAVARIDGE_GYM),"Gym sign not available")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
check7(BlueHoennPilot.heat_badge?,"Heat badge lost after reload")
check7(!BlueHoennPilot.flannery,"Flannery repeated after reload")
check7($bag.items[:METEORITE_RSE]==1 && $bag.items[:TM50]==1,
       "Reload duplicated quest items")
$PokemonGlobal.blue_regions["current"]="JOHTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
check7(!BlueHoennPilot.meteor_falls_ambush,"Story leaked into Johto")
check7(!BlueHoennPilot.flannery,"Flannery leaked into Johto")
check7(Marshal.dump($PokemonGlobal.blue_regions)==before,"Johto save mutated")
puts "HOENN_STAGE7_RUNTIME_OK"
