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
    return false unless area=="HOENN"&&%w[MIND RAIN].include?(badge)&&
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
  [[708,25,6],Hash[(1..322).map{|src|[src,src+600]}]]
end
$PokemonGlobal=H9Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=H9Player.new
$bag=H9Bag.new
$game_map=H9Map.new
$game_player=H9Avatar.new
$game_self_switches={}
$scene=Object.new


# Stage10 story acceptance is simulated only; no Game.exe or source assets.
$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>%w[STONE KNUCKLE DYNAMO HEAT BALANCE FEATHER MIND]},
  "hoenn_pilot"=>{
    "starter"=>"TREECKO","hm_dive_received"=>true,
    "submarine_escaped"=>true,"groudon_awakened"=>true
  }
}
flags=BlueHoennPilot.state
assert9(!BlueHoennPilot.sootopolis_crisis,"crisis before Kyogre")
assert9(!BlueHoennPilot.juan,"Juan before Rayquaza")
assert9(!BlueHoennPilot.wally_victory_road,"Wally before RAIN")
assert9(!BlueHoennPilot.elite_four(1),"Phoebe before RAIN")
assert9(!BlueHoennPilot.champion_wallace,"Wallace early")
assert9(!BlueHoennPilot.hall_of_fame_stage10,"Hall without champion")
TrainerBattle.result=false
assert9(!BlueHoennPilot.seafloor_archie,"Archie loss counted as win")
assert9(!flags["seafloor_archie_defeated"],"Archie loss flagged")
TrainerBattle.result=true
assert9(BlueHoennPilot.seafloor_archie,"Archie battle")
assert9(flags["seafloor_archie_defeated"],"Archie flag")
assert9(BlueHoennPilot.seafloor_awakening,"Kyogre awakening")
assert9(flags["kyogre_awakened"],"Kyogre missing")
assert9(!BlueHoennPilot.seafloor_awakening,"Kyogre repeated")
assert9(BlueHoennPilot.sootopolis_crisis,"Sootopolis crisis")
assert9(!BlueHoennPilot.rayquaza_stage10,"Rayquaza without Wallace")
assert9(BlueHoennPilot.origin_wallace_stage10,"Wallace origin")
assert9(!BlueHoennPilot.rayquaza_stage10,"Rayquaza without tower opening")
assert9(BlueHoennPilot.sky_pillar_wallace,"Wallace Sky Pillar")
assert9(BlueHoennPilot.rayquaza_stage10,"Rayquaza resolution")
assert9(flags["crisis_resolved"],"climate still active")
assert9(!BlueHoennPilot.rayquaza_stage10,"Rayquaza repeated")
assert9(!BlueHoennPilot.rain_badge?,"RAIN too early")
TrainerBattle.result=false
assert9(!BlueHoennPilot.juan,"Juan loss counted")
assert9(!BlueHoennPilot.rain_badge?,"RAIN granted on loss")
TrainerBattle.result=true
assert9(BlueHoennPilot.juan,"Juan victory")
assert9(BlueHoennPilot.rain_badge?,"RAIN not granted")
assert9(!flags["juan_tm_given"],"TM granted while mock TM unavailable")
assert9(!BlueHoennPilot.elite_four(0),"Elite before Wally")
TrainerBattle.result=false
assert9(!BlueHoennPilot.wally_victory_road,"Wally loss counted")
TrainerBattle.result=true
assert9(BlueHoennPilot.wally_victory_road,"Wally win")
assert9(!BlueHoennPilot.elite_four(1),"Elite skipped Sidney")
TrainerBattle.result=false
assert9(!BlueHoennPilot.elite_four(0),"Sidney loss counted")
assert9(!flags["elite_sidney_defeated"],"Sidney flag on loss")
TrainerBattle.result=true
for index in 0..3
  assert9(BlueHoennPilot.elite_four(index),"Elite index #{index} failed")
  assert9(BlueHoennPilot.elite_four(index),"Elite index #{index} replay not idempotent")
end
TrainerBattle.result=false
assert9(!BlueHoennPilot.champion_wallace,"Champion loss counted")
assert9(!flags["champion_wallace_defeated"],"Champion flag on loss")
TrainerBattle.result=true
assert9(BlueHoennPilot.champion_wallace,"Champion victory")
assert9(BlueHoennPilot.hall_of_fame_stage10,"Hoenn Hall")
assert9(flags["hoenn_hall_of_fame"],"Hoenn Hall flag")
assert9(BlueHoennPilot.hall_of_fame_stage10,"Hall reentry")
$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
assert9(BlueHoennPilot.rain_badge?,"RAIN lost after save/reload")
assert9(BlueHoennPilot.hall_of_fame_stage10,"Hall flag lost after save")
$PokemonGlobal.blue_regions["current"]="JOHTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
assert9(!BlueHoennPilot.rain_badge?,"RAIN leaked into Johto")
assert9(!BlueHoennPilot.champion_wallace,"Champion leaked into Johto")
assert9(!BlueHoennPilot.seafloor_archie,"Archie leaked into Johto")
assert9(Marshal.dump($PokemonGlobal.blue_regions)==before,"Johto flags mutated")
puts "HOENN_STAGE10_RUNTIME_OK"
