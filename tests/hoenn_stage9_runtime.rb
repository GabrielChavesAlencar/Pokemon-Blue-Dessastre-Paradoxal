# Stage09 Ruby scenario simulation. No Game.exe, donor ZIP or real saves.
class H9Global;attr_accessor :blue_regions;end
class H9Player
  attr_accessor :party,:gender
  attr_reader :heals
  def initialize;@party=[:TREECKO,:RALTS];@gender=0;@heals=0;end
  def heal_party;@heals+=1;end
end
class H9Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize;@items=Hash.new(0);@can_add=true;end
  def has?(key);@items[key]>0;end
  def add(key,n=1);return false unless @can_add;@items[key]+=n;true;end
  def remove(key,n=1);return false if @items[key]<n;@items[key]-=n;true;end
end
module GameData
  module Item
    Row=Struct.new(:move)
    @data={MAGMAEMBLEM:nil,TM04: :CALMMIND,HM08: :DIVE,SUPERROD:nil}
    def self.exists?(id);@data.key?(id);end
    def self.get(id);Row.new(@data.fetch(id));end
  end
end
module BlueRegions
  def self.local_achievements(state,area)
    state.fetch("achievements",{}).fetch(area,[])
  end
  def self.award(state,area,badge)
    return false unless area=="HOENN"&&badge=="MIND"&&
                        state["initial"]=="HOENN"&&state["current"]=="HOENN"
    list=(state["achievements"]["HOENN"]||=[])
    return false if list.include?(badge)
    list<<badge
    true
  end
end
module BlueRegionStart;def self.select_and_prepare;false;end;end
module EventHandlers;def self.add(*args);true;end;end
module TrainerBattle
  @calls=[]
  class << self
    attr_accessor :result
    attr_reader :calls
    def start(*args);@calls<<args;@result!=false;end
  end
end
class H9Map
  attr_accessor :map_id
  def initialize;@map_id=780;end
end
class H9Avatar
  attr_accessor :x,:y,:direction
  def initialize;@x,@y,@direction=16,19,2;end
  def moveto(x,y);@x,@y=x,y;end
end
module BlueRegionTravel
  @calls=[]
  class << self
    attr_accessor :failure
    attr_reader :calls
    def move_to(point)
      raise "transferencia simulada falhou" if @failure
      @calls<<point
      $game_map.map_id=point[0]
      $game_player.moveto(point[1],point[2])
      $game_player.direction=point[3]
      true
    end
  end
end
$messages=[]
$rules=[]
$allow_double=true
def _INTL(s,*args)
  args.each_with_index{|a,i|s=s.gsub("{#{i+1}}",a.to_s)}
  s
end
def pbMessage(s,*args);$messages<<s;0;end
def pbConfirmMessage(s);$messages<<s;true;end
def pbFadeOutIn;yield;end
def setBattleRule(s);$rules<<s;end
def pbCanDoubleBattle?;$allow_double;end
def assert9(ok,msg);raise "[HOENN_STAGE9] #{msg}" unless ok;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],{
    69=>769,76=>876,79=>879,81=>881,82=>882,
    141=>941,180=>780,182=>782,206=>906,215=>815,
    216=>816,217=>817,213=>913
  }]
end
$PokemonGlobal=H9Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=H9Player.new
$bag=H9Bag.new
$game_map=H9Map.new
$game_player=H9Avatar.new
$game_self_switches={}
$scene=Object.new

initial=Marshal.dump($PokemonGlobal.blue_regions)
assert9(!BlueHoennPilot.pyre_orb_scene,"Mt Pyre flag leaked into Decades")
assert9(!BlueHoennPilot.pyre_aqua_grunt(920),"Aqua leaked into Decades")
assert9(!BlueHoennPilot.enter_magma_hideout,"Magma leaked into Decades")
assert9(!BlueHoennPilot.tate_liza,"Mind badge leaked into Decades")
assert9(!BlueHoennPilot.steven_house_stage9,"Dive leaked into Decades")
assert9(Marshal.dump($PokemonGlobal.blue_regions)==initial,"Decades state changed")

$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["STONE","KNUCKLE","DYNAMO","HEAT","BALANCE","FEATHER"]},
  "hoenn_pilot"=>{"starter"=>"TREECKO","stern_delivery_ready"=>true,
                   "museum_fee_paid"=>true,"museum_aqua_1_defeated"=>true,
                   "museum_aqua_2_defeated"=>true,"stern_package_delivered"=>true}
}
flags=BlueHoennPilot.state
assert9(!BlueHoennPilot.mind_badge?,"Mind already earned")
assert9(!BlueHoennPilot.pyre_orb_scene,"Pyre orb stolen before grunts")
assert9(!BlueHoennPilot.enter_magma_hideout,"Magma opened without emblem")
TrainerBattle.result=false
assert9(!BlueHoennPilot.pyre_aqua_grunt(920),"Aqua loss granted victory")
assert9(!flags["pyre_aqua_920_defeated"],"Aqua flag set on loss")
TrainerBattle.result=true
for ver in [920,921,922,923]
  assert9(BlueHoennPilot.pyre_aqua_grunt(ver),"Pyre grunt #{ver} didn't complete")
  assert9(!BlueHoennPilot.pyre_aqua_grunt(ver),"Pyre grunt #{ver} repeated")
end
assert9(BlueHoennPilot.pyre_orb_scene,"Orb event failed")
assert9(flags["pyre_orb_stolen"],"Red Orb story flag missing")
assert9(!BlueHoennPilot.pyre_orb_scene,"Orb event duplicated")
$bag.can_add=false
assert9(!BlueHoennPilot.pyre_elder,"Magma Emblem with full bag")
assert9(!flags["magma_emblem_received"],"Emblem flag on failed gift")
$bag.can_add=true
assert9(BlueHoennPilot.pyre_elder,"Magma Emblem not delivered")
assert9($bag.items[:MAGMAEMBLEM]==1,"Emblem missing")
assert9(BlueHoennPilot.pyre_elder,"Elder repeat talk failed")
assert9($bag.items[:MAGMAEMBLEM]==1,"Emblem duplicated")

$game_map.map_id=780
assert9(BlueHoennPilot.enter_magma_hideout,"Magma entrance did not open")
assert9($game_map.map_id==782,"Magma entered wrong map")
BlueRegionTravel.failure=true
previous=[$game_map.map_id,$game_player.x,$game_player.y]
assert9(!BlueHoennPilot.stage9_transfer(182,206,16,20),"Failed transfer returned success")
assert9(previous==[$game_map.map_id,$game_player.x,$game_player.y],
        "Failed transfer changed player location")
BlueRegionTravel.failure=false
TrainerBattle.result=false
assert9(!BlueHoennPilot.magma_hideout_grunt(940),"Magma loss counted as win")
TrainerBattle.result=true
for ver in [940,941]
  assert9(BlueHoennPilot.magma_hideout_grunt(ver),"Magma grunt #{ver} didn't complete")
end
TrainerBattle.result=false
assert9(!BlueHoennPilot.magma_hideout_tabitha,"Tabitha loss counted as victory")
assert9(!flags["hideout_tabitha_defeated"],"Tabitha saved after loss")
TrainerBattle.result=true
assert9(BlueHoennPilot.magma_hideout_tabitha,"Tabitha victory failed")
TrainerBattle.result=false
assert9(!BlueHoennPilot.magma_hideout_maxie,"Maxie loss counted as victory")
TrainerBattle.result=true
assert9(BlueHoennPilot.magma_hideout_maxie,"Maxie victory failed")
assert9(BlueHoennPilot.groudon_hideout,"Groudon did not awaken")
assert9(flags["groudon_awakened"],"Groudon story milestone missing")
assert9(!BlueHoennPilot.groudon_hideout,"Groudon event replayed")
assert9(!flags["slateport_submarine_stolen"],"Submarine stolen too early")
assert9(BlueHoennPilot.stern,"Stern didn't register submarine theft")
assert9(flags["slateport_submarine_stolen"],"Submarine theft missing")
assert9(BlueHoennPilot.stern,"Stern repeat dialogue failed")

$game_map.map_id=769
assert9(BlueHoennPilot.enter_aqua_hideout,"Aqua entrance failed")
assert9($game_map.map_id==815,"Wrong Aqua entrance map")
TrainerBattle.result=false
assert9(!BlueHoennPilot.aqua_hideout_grunt(950),"Aqua grunt loss counted as victory")
TrainerBattle.result=true
for ver in [950,953]
  assert9(BlueHoennPilot.aqua_hideout_grunt(ver),"Aqua hideout grunt #{ver} failed")
end
TrainerBattle.result=false
assert9(!BlueHoennPilot.aqua_hideout_matt,"Matt loss counted as win")
assert9(!flags["aqua_matt_defeated"],"Matt flag on loss")
TrainerBattle.result=true
assert9(BlueHoennPilot.aqua_hideout_matt,"Matt battle failed")
assert9(BlueHoennPilot.submarine_escape,"Submarine escape event failed")
assert9(flags["submarine_escaped"],"Submarine not escaped")
assert9(!BlueHoennPilot.submarine_escape,"Submarine duplicated")
assert9(!BlueHoennPilot.space_center_steven,"Space invasion skipped before Mind")

$game_map.map_id=882
$allow_double=false
assert9(!BlueHoennPilot.tate_liza,"Twin leaders bypassed double battle requirement")
$allow_double=true
TrainerBattle.result=false
assert9(!BlueHoennPilot.tate_liza,"Tate/Liza loss counted as badge")
assert9(!BlueHoennPilot.mind_badge?,"Mind granted on loss")
$bag.can_add=false
TrainerBattle.result=true
assert9(BlueHoennPilot.tate_liza,"Tate/Liza victory failed")
assert9(BlueHoennPilot.mind_badge?,"Mind badge missing")
assert9($rules.include?("double"),"Twin battle wasn't designated double")
assert9(!flags["tate_liza_tm_given"],"TM granted with full bag")
$bag.can_add=true
assert9(BlueHoennPilot.tate_liza,"Delayed Calm Mind not delivered")
assert9($bag.items[:TM04]==1,"Calm Mind TM missing")
assert9(!BlueHoennPilot.tate_liza,"Calm Mind duplicate")
assert9(TrainerBattle.calls.count([:BLUE_HOENN_TATE_LIZA,"Tate & Liza",982])==2,
       "Tate/Liza battle repeated after win")
TrainerBattle.result=false
assert9(!BlueHoennPilot.space_magma_grunt(991),"Space grunt loss counted as win")
TrainerBattle.result=true
for ver in [991,994]
  assert9(BlueHoennPilot.space_magma_grunt(ver),"Space grunt #{ver} failed")
end
TrainerBattle.result=false
assert9(!BlueHoennPilot.space_center_steven,"Space battle loss counted as win")
assert9(!flags["space_center_saved"],"Space was saved despite loss")
TrainerBattle.result=true
# First Tabitha then Maxie: lose only to Maxie, keep Tabitha win.
assert9(BlueHoennPilot.space_center_steven,"Space Magma boss sequence failed")
assert9(flags["space_center_saved"],"Space mission flag missing")
assert9(BlueHoennPilot.space_center_steven,"Steven post-battle talk missing")

$bag.can_add=false
assert9(!BlueHoennPilot.steven_house_stage9,"Dive granted with full bag")
assert9(!flags["hm_dive_received"],"Dive flag set despite no gift")
$bag.can_add=true
assert9(BlueHoennPilot.steven_house_stage9,"Dive not delivered")
assert9($bag.items[:HM08]==1,"HM Dive missing")
assert9(!BlueHoennPilot.steven_house_stage9,"Dive duplicated")
assert9(BlueHoennPilot.super_rod_stage9,"Super Rod gift failed")
assert9(!BlueHoennPilot.super_rod_stage9,"Super Rod duplicated")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
assert9(BlueHoennPilot.mind_badge?,"Mind lost after save/reload")
assert9(!BlueHoennPilot.tate_liza,"Tate/Liza repeated after reload")
assert9(!BlueHoennPilot.submarine_escape,"Submarine repeated after reload")
assert9($bag.items[:HM08]==1&&$bag.items[:TM04]==1,"Dive/TM duplicated")
$PokemonGlobal.blue_regions["current"]="JOHTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
assert9(!BlueHoennPilot.pyre_elder,"Pyre leaked to Johto")
assert9(!BlueHoennPilot.tate_liza,"Tate/Liza leaked to Johto")
assert9(!BlueHoennPilot.space_center_steven,"Steven leaked to Johto")
assert9(Marshal.dump($PokemonGlobal.blue_regions)==before,"Johto save changed")
puts "HOENN_STAGE9_RUNTIME_OK"
