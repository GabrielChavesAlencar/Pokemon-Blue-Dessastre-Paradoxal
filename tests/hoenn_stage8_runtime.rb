# Stage 08 runtime doubles: no Game.exe, RXDATA binary or native save touched.
class H8Global;attr_accessor :blue_regions;end
class H8Player
  attr_accessor :party,:gender
  attr_reader :heals
  def initialize;@party=[:TREECKO];@gender=0;@heals=0;end
  def heal_party;@heals+=1;end
end
class H8Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize;@can_add=true;@items=Hash.new(0);end
  def has?(k);@items[k]>0;end
  def add(k,n=1);return false unless @can_add;@items[k]+=n;true;end
  def remove(k,n=1);return false if @items[k]<n;@items[k]-=n;true;end
end
module GameData
  module Item
    ItemRec=Struct.new(:move)
    @items={TM42: :FACADE,TM40: :AERIALACE,
            HM03: :SURF,HM02: :FLY,DEVONSCOPE:nil,GOODROD:nil}
    def self.exists?(id);@items.key?(id);end
    def self.get(id);ItemRec.new(@items.fetch(id));end
  end
  module Species
    def self.exists?(name);name==:CASTFORM;end
  end
end
module BlueRegions
  def self.local_achievements(s,area);s.fetch("achievements",{}).fetch(area,[]);end
  def self.award(s,area,badge)
    return false unless s["initial"]=="HOENN"&&s["current"]=="HOENN"&&
                        area=="HOENN"&&["BALANCE","FEATHER"].include?(badge)
    list=(s["achievements"]["HOENN"]||=[])
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
    def start(*args)
      @calls<<args
      @result!=false
    end
  end
end
class H8Event
  attr_reader :refreshes
  def initialize;@refreshes=0;end
  def refresh;@refreshes+=1;end
end
class H8Map
  attr_accessor :map_id,:events
  def initialize;@map_id=720;@events={101=>H8Event.new};end
end
class H8Avatar
  attr_accessor :x,:y,:direction
  def initialize;@x,@y,@direction=6,5,2;end
  def moveto(x,y);@x,@y=x,y;end
end
class H8Temp
  attr_accessor :in_battle
  def initialize;@in_battle=false;end
end
$messages=[]
$rules=[]
$castform_ok=false
$castform_count=0
def _INTL(s,*values)
  values.each_with_index{|v,i|s=s.gsub("{#{i+1}}",v.to_s)}
  s
end
def pbMessage(s,*args);$messages<<s;0;end
def pbConfirmMessage(s);$messages<<s;true;end
def setBattleRule(s);$rules<<s;end
def pbAddPokemon(species,level)
  return false unless $castform_ok
  $castform_count+=1
  true
end
def assert8(v,msg);raise "[HOENN_STAGE8] #{msg}" unless v;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],{20=>720,68=>768,64=>764,135=>735,137=>737,138=>738,69=>769}]
end
$PokemonGlobal=H8Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=H8Player.new
$bag=H8Bag.new
$game_map=H8Map.new
$game_player=H8Avatar.new
$game_temp=H8Temp.new
$game_self_switches={}
$scene=Object.new

before=Marshal.dump($PokemonGlobal.blue_regions)
assert8(!BlueHoennPilot.norman,"Norman leaked into Decades")
assert8(!BlueHoennPilot.surf_from_wally_family,"Surf leaked into Decades")
assert8(!BlueHoennPilot.weather_shelly,"Shelly leaked into Decades")
assert8(!BlueHoennPilot.weather_castform,"Castform leaked into Decades")
assert8(!BlueHoennPilot.winona,"Winona leaked into Decades")
assert8(!BlueHoennPilot.rival_lilycove,"Lilycove rival leaked into Decades")
assert8(Marshal.dump($PokemonGlobal.blue_regions)==before,"Decades save mutated")

$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["STONE","KNUCKLE","DYNAMO","HEAT"]},
  "hoenn_pilot"=>{"starter"=>"TREECKO","wally_captured"=>true,
                   "flannery_defeated"=>true}
}
f=BlueHoennPilot.state
assert8(!BlueHoennPilot.winona,"Winona accepted challenge before Weather Institute")
assert8(!BlueHoennPilot.rival_119,"Route119 rival bypassed Weather Institute")
assert8(!BlueHoennPilot.surf_from_wally_family,"Surf given before Balance")
assert8(BlueHoennPilot.norman_gym_warp(9,8),"Norman gym room door didn't transfer")
assert8([$game_player.x,$game_player.y]==[9,8],"Norman gym door destination wrong")
assert8(!BlueHoennPilot.norman_gym_warp(78,54),"Unlisted Norman destination accepted")
TrainerBattle.result=false
assert8(!BlueHoennPilot.norman,"Norman loss counted as win")
assert8(!BlueHoennPilot.balance_badge?,"Balance granted on loss")
TrainerBattle.result=true
$bag.can_add=false
assert8(BlueHoennPilot.norman,"Norman victory failed")
assert8(BlueHoennPilot.balance_badge?,"Balance missing")
assert8(!f["norman_tm_given"],"Facade granted with full bag")
$bag.can_add=true
assert8(BlueHoennPilot.norman,"Deferred Facade not delivered")
assert8($bag.items[:TM42]==1,"Facade missing")
assert8(!BlueHoennPilot.norman,"Facade duplicated")
assert8(TrainerBattle.calls.count([:BLUE_HOENN_NORMAN,"Norman",820])==2,
       "Norman replayed after win")
$bag.can_add=false
assert8(!BlueHoennPilot.wally_family,"Surf incorrectly granted with full bag")
assert8(!f["hm_surf_received"],"Surf flag recorded with full bag")
$bag.can_add=true
assert8(BlueHoennPilot.wally_family,"Surf not delivered from Wally family")
assert8($bag.items[:HM03]==1,"Surf HM absent")
assert8(BlueHoennPilot.wally_family,"Wally family dialogue missing after Surf")
assert8($bag.items[:HM03]==1,"Surf HM duplicated")
assert8(BlueHoennPilot.good_rod_fisherman,"Good Rod unavailable")
assert8(!BlueHoennPilot.good_rod_fisherman,"Good Rod duplicated")

TrainerBattle.result=false
assert8(!BlueHoennPilot.weather_aqua(851),"Aqua loss counted as victory")
assert8(!f["weather_aqua_851_defeated"],"Aqua flag on loss")
TrainerBattle.result=true
for version in [851,852,853,854]
  assert8(BlueHoennPilot.weather_aqua(version),"Aqua fight #{version} failed")
  assert8(!BlueHoennPilot.weather_aqua(version),"Aqua fight #{version} replayed")
end
TrainerBattle.result=false
assert8(!BlueHoennPilot.weather_shelly,"Shelly loss counted as victory")
assert8(!f["weather_shelly_defeated"],"Shelly flag on loss")
TrainerBattle.result=true
assert8(BlueHoennPilot.weather_shelly,"Shelly victory failed")
assert8(!BlueHoennPilot.weather_shelly,"Shelly replayed")
assert8(!BlueHoennPilot.weather_castform,"Castform delivered without space")
assert8(!f["weather_castform_received"],"Castform flag set on failure")
$castform_ok=true
assert8(BlueHoennPilot.weather_castform,"Castform gift failed")
assert8($castform_count==1,"Castform not delivered exactly once")
assert8(!BlueHoennPilot.weather_castform,"Castform gift repeated")
assert8($castform_count==1,"Castform count duplicated")

TrainerBattle.result=false
assert8(!BlueHoennPilot.rival_119,"Route119 rival loss counted as victory")
assert8(!f["rival_119_done"],"Rival119 saved on loss")
TrainerBattle.result=true
$bag.can_add=false
assert8(BlueHoennPilot.rival_119,"Route119 rival win failed")
assert8(f["rival_119_done"],"Rival119 milestone not saved")
assert8(!f["hm_fly_received"],"Fly granted with full bag")
$bag.can_add=true
assert8(BlueHoennPilot.rival_119,"Pending Fly not delivered")
assert8($bag.items[:HM02]==1,"Fly HM missing")
assert8(!BlueHoennPilot.rival_119,"Fly duplicated")
assert8(TrainerBattle.calls.count([:RIVAL1,"May",819])==2,
       "Rival119 repeated after victory")
assert8(!BlueHoennPilot.winona,"Winona allowed without Devon Scope")

$bag.can_add=false
assert8(!BlueHoennPilot.steven_scope,"Devon Scope granted with full bag")
assert8(!f["devon_scope_received"],"Devon Scope flag on failed gift")
$bag.can_add=true
assert8(BlueHoennPilot.steven_scope,"Devon Scope not delivered")
assert8($bag.items[:DEVONSCOPE]==1,"Devon Scope missing")
assert8(BlueHoennPilot.steven_scope,"Steven repeat dialogue missing")
assert8($bag.items[:DEVONSCOPE]==1,"Devon Scope duplicated")
$game_map.map_id=764
assert8(BlueHoennPilot.kecleon_scope(101,:FORTREE),"Fortree Kecleon not revealed")
assert8($game_self_switches[[764,101,"A"]],"Fortree Kecleon still blocking")
assert8(f["kecleon_FORTREE_cleared"],"Fortree Kecleon story missing")

TrainerBattle.result=false
assert8(!BlueHoennPilot.winona,"Winona loss counted as victory")
assert8(!BlueHoennPilot.feather_badge?,"Feather badge set on loss")
TrainerBattle.result=true
$bag.can_add=false
assert8(BlueHoennPilot.winona,"Winona win failed")
assert8(BlueHoennPilot.feather_badge?,"Feather badge missing")
assert8(!f["winona_tm_given"],"Aerial Ace given with full bag")
$bag.can_add=true
assert8(BlueHoennPilot.winona,"Deferred Aerial Ace not delivered")
assert8($bag.items[:TM40]==1,"Aerial Ace TM absent")
assert8(!BlueHoennPilot.winona,"Aerial Ace duplicated")
assert8(TrainerBattle.calls.count([:BLUE_HOENN_WINONA,"Winona",868])==2,
       "Winona battle repeated after win")
$game_map.map_id=738
assert8(BlueHoennPilot.kecleon_scope(101,:ROUTE120),"Route120 Kecleon not revealed")
assert8(f["kecleon_ROUTE120_cleared"],"Route120 Kecleon state missing")
assert8(!BlueHoennPilot.kecleon_scope(101,:UNKNOWN),"Unlisted Kecleon accepted")
TrainerBattle.result=false
assert8(!BlueHoennPilot.rival_lilycove,"Lilycove rival loss counted as win")
TrainerBattle.result=true
assert8(BlueHoennPilot.rival_lilycove,"Lilycove rival win not recorded")
assert8(!BlueHoennPilot.rival_lilycove,"Lilycove rival replayed")
assert8(TrainerBattle.calls.count([:RIVAL1,"May",822])==2,
       "Lilycove rival fought after win")
assert8(!BlueHoennPilot.stage8_future_gate(:AQUA_HIDEOUT),"Aqua Hideout prematurely opened")
assert8(BlueHoennPilot.sign_stage8(:FORTREE),"Fortree sign missing")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
assert8(BlueHoennPilot.balance_badge?&&BlueHoennPilot.feather_badge?,
       "Badges lost after reload")
assert8(!BlueHoennPilot.rival_lilycove,"Lilycove rival restarted after reload")
assert8(!BlueHoennPilot.weather_castform,"Castform duplicated after reload")
assert8($bag.items[:TM42]==1&&$bag.items[:TM40]==1&&
        $bag.items[:HM03]==1&&$bag.items[:HM02]==1,
        "TM/HM duplicated after reload")
$PokemonGlobal.blue_regions["current"]="JOHTO"
snapshot=Marshal.dump($PokemonGlobal.blue_regions)
assert8(!BlueHoennPilot.winona,"Winona leaked to Johto")
assert8(!BlueHoennPilot.weather_aqua(851),"Aqua leaked to Johto")
assert8(!BlueHoennPilot.steven_scope,"Devon Scope leaked to Johto")
assert8(Marshal.dump($PokemonGlobal.blue_regions)==snapshot,"Johto save mutated")
puts "HOENN_STAGE8_RUNTIME_OK"
