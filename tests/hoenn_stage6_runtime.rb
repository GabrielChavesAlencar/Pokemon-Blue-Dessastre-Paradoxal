# Stage 6 Ruby-only tests. Does NOT execute Game.exe or touch native saves.
class Hoenn6Global
  attr_accessor :blue_regions
end
class Hoenn6Player
  attr_accessor :party, :gender
  attr_reader :heals
  def initialize
    @party = [:TREECKO]
    @gender = 0
    @heals = 0
  end
  def heal_party; @heals += 1; end
end
class Hoenn6Bag
  attr_accessor :can_add
  attr_reader :items
  def initialize
    @can_add = true
    @items = Hash.new(0)
  end
  def has?(key); @items[key] > 0; end
  def add(key,n=1); return false unless @can_add;@items[key]+=n;true;end
  def remove(key,n=1);return false if @items[key]<n;@items[key]-=n;true;end
end
module GameData
  module Item
    Rec=Struct.new(:move)
    @entries={
      MACHBIKE:nil, ACROBIKE:nil, ITEMFINDER:nil,
      HM06: :ROCKSMASH, TM34: :SHOCKWAVE,
    }
    def self.exists?(key);@entries.key?(key);end
    def self.get(key);Rec.new(@entries.fetch(key));end
  end
end
module BlueRegions
  def self.local_achievements(state,region)
    state.fetch("achievements",{}).fetch(region,[])
  end
  def self.award(state,region,key)
    return false unless region=="HOENN" && state["current"]=="HOENN" &&
                        state["initial"]=="HOENN" && key=="DYNAMO"
    badges=(state["achievements"]["HOENN"]||=[])
    return false if badges.include?(key)
    badges << key
    true
  end
end
module BlueRegionStart
  def self.select_and_prepare;false;end
end
module EventHandlers
  def self.add(*_args);true;end
end
module TrainerBattle
  @calls=[]
  class << self
    attr_accessor :result
    attr_reader :calls
    def start(*args)
      @calls << args
      @result != false
    end
  end
end
class Hoenn6Event
  attr_reader :refresh_count
  def initialize; @refresh_count=0; end
  def refresh;@refresh_count+=1;end
end
class Hoenn6Map
  attr_accessor :map_id, :events
  def initialize
    @map_id=747
    @events=(21..27).to_h{|id|[id,Hoenn6Event.new]}
  end
end
class Hoenn6Avatar
  attr_accessor :x,:y,:direction
  def initialize;@x,@y,@direction=9,6,2;end
  def moveto(x,y);@x,@y=x,y;end
end
class Hoenn6Temp
  attr_accessor :in_battle
  def initialize;@in_battle=false;end
end
module BlueRegionTravel
  @calls=[]
  class << self
    attr_accessor :failure
    attr_reader :calls
    def move_to(point)
      raise "Falha simulada" if @failure
      @calls << point
      $game_map.map_id=point[0]
      $game_player.moveto(point[1],point[2])
      $game_player.direction=point[3]
    end
  end
end

$messages=[]
$rules=[]
$choice=2
def _INTL(text,*args)
  args.each_with_index{|value,i|text=text.gsub("{#{i+1}}",value.to_s)}
  text
end
def pbMessage(text,*args)
  $messages << text
  args.empty? ? 0 : $choice
end
def pbConfirmMessage(text);$messages<<text;true;end
def pbFadeOutIn;yield;end
def setBattleRule(s);$rules<<s;end
def verify(value,msg);raise "[HOENN_STAGE6] #{msg}" unless value;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6],{41=>741,47=>747,113=>713,114=>714,115=>715}]
end
$PokemonGlobal=Hoenn6Global.new
$PokemonGlobal.blue_regions={"current"=>"KANTO"}
$player=Hoenn6Player.new
$bag=Hoenn6Bag.new
$game_map=Hoenn6Map.new
$game_player=Hoenn6Avatar.new
$game_temp=Hoenn6Temp.new
$scene=Object.new
$game_self_switches={}

previous=Marshal.dump($PokemonGlobal.blue_regions)
verify(!BlueHoennPilot.rival_110,"Rival started in Kanto")
verify(!BlueHoennPilot.wally_mauville,"Wally started in Kanto")
verify(!BlueHoennPilot.wattson,"Wattson started in Kanto")
verify(!BlueHoennPilot.rydel_bikes,"Rydel opened in Kanto")
verify(!BlueHoennPilot.cycling_gate(114,18,16),"Cycling route opened in Kanto")
verify(!BlueHoennPilot.rock_smash_teacher,"Rock Smash granted in Kanto")
verify(Marshal.dump($PokemonGlobal.blue_regions)==previous,"Kanto state changed")

$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["STONE","KNUCKLE"]},
  "hoenn_pilot"=>{"starter"=>"TREECKO","rival_103_done"=>true,
                   "wally_captured"=>true,"stern_package_delivered"=>false},
}
flags=BlueHoennPilot.state
verify(!BlueHoennPilot.slateport_north_gate,"Slateport opened without Stern")
verify(!BlueHoennPilot.rival_110,"Rival ignored Stern prerequisite")
verify(!BlueHoennPilot.wattson,"Wattson bypassed story")
flags["stern_package_delivered"]=true
verify(BlueHoennPilot.slateport_north_gate,"Route110 remained closed after Stern")

# Rival on Route110 uses May+COMBUSKEN against Treecko; defeat allows retry.
TrainerBattle.result=false
verify(!BlueHoennPilot.rival_110,"Rival loss counted as win")
verify(!flags["rival_110_done"],"Rival win persisted on loss")
TrainerBattle.result=true
$bag.can_add=false
verify(BlueHoennPilot.rival_110,"Rival victory missing")
verify(flags["rival_110_done"],"Rival story not saved")
verify(!$bag.has?(:ITEMFINDER),"Itemfinder awarded with full bag")
$bag.can_add=true
verify(BlueHoennPilot.rival_110,"Pending Itemfinder not delivered")
verify($bag.items[:ITEMFINDER]==1,"Wrong Itemfinder count")
verify(!BlueHoennPilot.rival_110,"Repeated Itemfinder")
verify(TrainerBattle.calls.count([:RIVAL1,"May",610])==2,"Route110 rival battled extra times")

TrainerBattle.result=false
verify(!BlueHoennPilot.wally_mauville,"Wally loss counted as win")
TrainerBattle.result=true
verify(BlueHoennPilot.wally_mauville,"Wally victory missing")
verify(flags["wally_mauville_done"],"Wally milestone not set")
verify(!BlueHoennPilot.wally_mauville,"Wally battled twice")
verify(BlueHoennPilot.wally_uncle_mauville,"Wally uncle dialogue missing")
verify(TrainerBattle.calls.count([:BLUE_HOENN_WALLY,"Wally",641])==2,"Wally replayed")

# Wattson awards a regional milestone ONLY after a battle win.
TrainerBattle.result=false
verify(!BlueHoennPilot.wattson,"Wattson loss counted as win")
verify(!BlueHoennPilot.dynamo_badge?,"Dynamo Badge on loss")
TrainerBattle.result=true
$bag.can_add=false
verify(BlueHoennPilot.wattson,"Wattson victory did not award Dynamo")
verify(BlueHoennPilot.dynamo_badge?,"Dynamo Badge missing")
verify(BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")==
       ["STONE","KNUCKLE","DYNAMO"],"Incorrect regional badge count")
verify(!flags["wattson_tm_given"],"TM granted with full bag")
$bag.can_add=true
verify(BlueHoennPilot.wattson,"Pending Shock Wave unavailable")
verify($bag.items[:TM34]==1,"Wrong Shock Wave TM")
verify(!BlueHoennPilot.wattson,"Duplicate Shock Wave TM")
verify(TrainerBattle.calls.count([:BLUE_HOENN_WATTSON,"Wattson",647])==2,
       "Wattson battle replayed after a victory")
verify(BlueHoennPilot.rock_smash_teacher,"Rock Smash technique missing")
verify($bag.items[:HM06]==1,"Rock Smash HM missing")
verify(!BlueHoennPilot.rock_smash_teacher,"Rock Smash duplicate")

# Bicycle exchange is atomic: one chosen bike, no duplication.
$bag.can_add=false
$choice=0
verify(!BlueHoennPilot.rydel_bikes,"Mach Bike granted with full bag")
verify(!$bag.has?(:MACHBIKE),"No-space Mach Bike was added")
$bag.can_add=true
verify(BlueHoennPilot.rydel_bikes,"Mach Bike not awarded")
verify($bag.items[:MACHBIKE]==1,"Wrong Mach Bike count")
verify(!BlueHoennPilot.rydel_bikes,"Duplicate Mach Bike")
$choice=1
verify(BlueHoennPilot.rydel_bikes,"Acro Bike exchange failed")
verify($bag.items[:ACROBIKE]==1 && $bag.items[:MACHBIKE]==0,
       "Bike exchange lost/duplicated items")
verify(BlueHoennPilot.has_hoenn_bike?,"No bicycle after exchange")

# Item-gated cycling road allows entry and safe exit even if bike disappears.
verify(!BlueHoennPilot.cycling_gate(999,0,0),"Cycling gate accepted unknown map")
verify(BlueHoennPilot.cycling_gate(114,18,16),"Cycling road denied a bike")
verify($game_map.map_id==714,"Cycling gate arrived in wrong map")
verify(flags["cycling_road_visited"],"Cycling visit not saved")
$bag.remove(:ACROBIKE,1)
verify(!BlueHoennPilot.cycling_gate(114,19,88),"Bike road bypassed item check")
verify(BlueHoennPilot.cycling_gate(115,14,9),"Cycling road exit blocked without bike")
verify($game_map.map_id==715,"Wrong cycling gate return")
BlueRegionTravel.failure=true
current=[$game_map.map_id,$game_player.x,$game_player.y]
$bag.add(:MACHBIKE,1)
verify(!BlueHoennPilot.cycling_gate(114,18,16),"Failed transfer returned success")
verify([$game_map.map_id,$game_player.x,$game_player.y]==current,
       "Failed transfer corrupted player position")
BlueRegionTravel.failure=false

$game_map.map_id=747
blue=[21,22,23,24];pink=[25,26,27]
verify(BlueHoennPilot.wattson_switch(blue,pink),"Switch did not toggle")
verify(blue.all?{|id|$game_self_switches[[747,id,"A"]]},
       "Blue gates not open after switch")
verify(pink.all?{|id|$game_self_switches[[747,id,"A"]]==false},
       "Pink gates not closed after switch")
verify(BlueHoennPilot.wattson_switch(blue,pink),"Second switch did not toggle")
verify(blue.all?{|id|$game_self_switches[[747,id,"A"]]==false},
       "Blue gates not closed on second toggle")
verify(pink.all?{|id|$game_self_switches[[747,id,"A"]]},
       "Pink gates did not open on second toggle")
verify(!BlueHoennPilot.sign_stage6(:UNKNOWN),"Unknown sign was accepted")
verify(BlueHoennPilot.sign_stage6(:MAUVILLE_GYM),"Gym sign missing")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
verify(BlueHoennPilot.dynamo_badge?,"Dynamo Badge disappeared on reload")
verify(!BlueHoennPilot.rival_110,"Rival reward duplicated after reload")
verify(!BlueHoennPilot.wattson,"Wattson TM duplicated after reload")
verify($bag.items[:TM34]==1 && $bag.items[:ITEMFINDER]==1,
       "Reload duplicated TM or Itemfinder")
$PokemonGlobal.blue_regions["current"]="DECADES"
old=Marshal.dump($PokemonGlobal.blue_regions)
verify(!BlueHoennPilot.rydel_bikes,"Bike access leaked to Decades")
verify(!BlueHoennPilot.wattson,"Wattson leaked to Decades")
verify(Marshal.dump($PokemonGlobal.blue_regions)==old,"Decades save polluted")
puts "HOENN_STAGE6_RUNTIME_OK"
