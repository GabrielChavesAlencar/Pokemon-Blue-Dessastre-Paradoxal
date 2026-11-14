# Stage-5 Hoenn story verification with pure Ruby doubles.
# No donor assets, Game.exe, live player save or ROM.
class Hoenn5Global
  attr_accessor :blue_regions
end
class Hoenn5Player
  attr_accessor :party, :money
  attr_reader :heal_count
  def initialize
    @party = [:TREECKO]
    @money = 100
    @heal_count = 0
  end
  def heal_party; @heal_count += 1; end
end
class Hoenn5Bag
  attr_reader :items
  attr_accessor :can_add
  def initialize
    @items = Hash.new(0)
    @can_add = true
  end
  def has?(key); @items[key] > 0; end
  def add(item, quantity=1)
    return false unless @can_add
    @items[item] += quantity
    true
  end
  def remove(item, quantity=1)
    return false if @items[item] < quantity
    @items[item] -= quantity
    true
  end
end
module GameData
  module Item
    ItemRec = Struct.new(:move)
    @registry = {
      HM05: nil, HM01: nil, TM08: :BULKUP, TM47: :STEELWING,
      LETTER: nil, SOOTHEBELL: nil, SOFTSAND: nil,
    }
    def self.exists?(key); @registry.key?(key); end
    def self.get(key); ItemRec.new(@registry.fetch(key)); end
    def self.delete(key); @registry.delete(key); end
  end
end
module BlueRegions
  def self.local_achievements(state, area)
    state.fetch("achievements", {}).fetch(area, [])
  end
  def self.award(state, area, key)
    return false unless state["initial"] == "HOENN" &&
                        state["current"] == area && area == "HOENN" &&
                        key == "KNUCKLE"
    items = (state["achievements"][area] ||= [])
    return false if items.include?(key)
    items << key
    true
  end
end
module BlueRegionStart
  def self.select_and_prepare; false; end
end
module EventHandlers
  def self.add(*_args); true; end
end
module TrainerBattle
  @history = []
  class << self
    attr_accessor :result
    attr_reader :history
    def start(*args)
      @history << args
      @result != false
    end
  end
end
class Hoenn5Avatar
  attr_accessor :x, :y, :direction
  def initialize; @x,@y,@direction = 11,6,2;end
  def moveto(x,y);@x,@y=x,y;end
end
class Hoenn5Map
  attr_accessor :map_id
  def initialize; @map_id = 705;end
end
class Hoenn5Temp
  attr_accessor :in_battle
  def initialize;@in_battle=false;end
end
module BlueRegionTravel
  @history = []
  class << self
    attr_accessor :should_fail
    attr_reader :history
    def move_to(point)
      raise "falha simulada da travessia" if @should_fail
      @history << point
      $game_map.map_id=point[0]
      $game_player.moveto(point[1],point[2])
      $game_player.direction=point[3]
      true
    end
  end
end
$messages=[]
$battles=[]
$confirm = true
def pbMessage(message,*_other);$messages << message;end
def pbConfirmMessage(message);$messages << message;$confirm;end
def pbFadeOutIn;yield;end
def setBattleRule(key);$battles << key;end
def _INTL(message,*args)
  args.each_with_index {|v,i| message=message.gsub("{#{i+1}}",v.to_s)}
  message
end
def check(cond,msg);raise "[HOENN_STAGE5] #{msg}" unless cond;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata) do
  [[708,25,6], {105=>705,28=>728,111=>711}]
end
$PokemonGlobal=Hoenn5Global.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
$player=Hoenn5Player.new
$bag=Hoenn5Bag.new
$game_map=Hoenn5Map.new
$game_player=Hoenn5Avatar.new
$game_temp=Hoenn5Temp.new
$scene=Object.new

snapshot=Marshal.dump($PokemonGlobal.blue_regions)
check(!BlueHoennPilot.brawly,"Brawly ran in Decades")
check(!BlueHoennPilot.flash_hiker,"Flash ran in Decades")
check(!BlueHoennPilot.steven_letter,"Steven ran in Decades")
check(!BlueHoennPilot.museum_entry,"Museum ran in Decades")
check(!BlueHoennPilot.museum_aqua(1),"Museum grunts ran in Decades")
check(!BlueHoennPilot.stern,"Stern ran in Decades")
check(!BlueHoennPilot.boat_to(28),"Ferry ran in Decades")
check(Marshal.dump($PokemonGlobal.blue_regions)==snapshot,"Other regional state mutated")

$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>["STONE"]},
  "hoenn_pilot"=>{"peecko_rescued"=>true,
                   "stone_letter_received"=>true,
                   "devon_goods_delivered"=>true}
}
flags=BlueHoennPilot.state
check(!BlueHoennPilot.knuckle_badge?,"KNUCKLE awarded prematurely")
$bag.add(:LETTER,1)
check(BlueHoennPilot.flash_hiker,"Flash Hiker did not grant HM05")
check($bag.items[:HM05]==1,"Flash absent")
check(!BlueHoennPilot.flash_hiker,"HM Flash duplicated")
check($bag.items[:HM05]==1,"Flash awarded twice")

TrainerBattle.result=false
check(!BlueHoennPilot.brawly,"Brawly loss counted as victory")
check(!BlueHoennPilot.knuckle_badge?,"KNUCKLE granted on loss")
TrainerBattle.result=true
$bag.can_add=false
check(BlueHoennPilot.brawly,"Brawly victory did not grant milestone")
check(BlueHoennPilot.knuckle_badge?,"KNUCKLE not registered")
check(BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")==["STONE","KNUCKLE"],
      "Wrong achievement set")
check($bag.items[:TM08]==0 && !flags["brawly_tm_given"],"TM granted with full bag")
$bag.can_add=true
check(BlueHoennPilot.brawly,"Deferred Bulk Up unavailable")
check($bag.items[:TM08]==1,"Bulk Up missing")
check(!BlueHoennPilot.brawly,"Bulk Up duplicated")
check(TrainerBattle.history.count([:BLUE_HOENN_BRAWLY,"Brawly",531])==2,
      "Brawly was replayed after being defeated")

$bag.can_add=false
check(!BlueHoennPilot.steven_letter,"Steel Wing incorrectly awarded with full bag")
check(flags["steven_letter_delivered"],"Letter story stage not recorded")
check($bag.items[:LETTER]==0,"Letter not consumed")
check(!flags["steven_tm_given"],"No-space TM falsely saved")
$bag.can_add=true
check(BlueHoennPilot.steven_letter,"Deferred Steel Wing not available")
check($bag.items[:TM47]==1,"Steel Wing missing")
check(!BlueHoennPilot.steven_letter,"TM repeated")
check($bag.items[:LETTER]==0 && $bag.items[:TM47]==1,"Letter or TM duplicated")

# Briney only travels to verified source landing maps, never a new region.
check(BlueHoennPilot.briney,"Rescue/letter did not unlock ferry")
check($game_map.map_id==728,"Briney did not travel to Dewford")
check(BlueHoennPilot.dewford_boat,"Dewford did not connect to Slateport")
check($game_map.map_id==711,"Dewford ferry did not arrive at Route 109")
check(BlueHoennPilot.slateport_boat,"Slateport did not return to Dewford")
check($game_map.map_id==728,"Return ferry wrong map")
BlueRegionTravel.should_fail=true
before=[$game_map.map_id,$game_player.x,$game_player.y]
check(!BlueHoennPilot.boat_to(111),"A failed transfer claimed success")
check([$game_map.map_id,$game_player.x,$game_player.y]==before,
      "Failed transfer corrupted current position")
BlueRegionTravel.should_fail=false

# Stern needs the Shipyard, museum ticket and two victories.
check(!BlueHoennPilot.stern,"Stern accepted goods before shipyard")
check(BlueHoennPilot.shipyard,"Shipyard did not activate Stern quest")
check(!BlueHoennPilot.stern,"Stern bypassed museum")
$player.money=49
check(!BlueHoennPilot.museum_entry,"Museum allowed insufficient funds")
check($player.money==49,"Museum charged insufficient funds")
$player.money=100
$confirm=false
check(!BlueHoennPilot.museum_entry,"Decline charged museum")
check($player.money==100,"Museum deducted funds on decline")
$confirm=true
check(BlueHoennPilot.museum_entry,"Museum ticket failed")
check($player.money==50 && flags["museum_fee_paid"],"Incorrect museum price")
check(BlueHoennPilot.museum_entry,"Return to museum denied")
check($player.money==50,"Museum charged entrance twice")
check(!BlueHoennPilot.stern,"Stern bypassed Aqua")

TrainerBattle.result=false
check(!BlueHoennPilot.museum_aqua(1),"Aqua loss was recorded")
check(!flags["museum_aqua_1_defeated"],"Aqua flag granted on loss")
TrainerBattle.result=true
check(BlueHoennPilot.museum_aqua(1),"First Aqua win missing")
check(!BlueHoennPilot.stern,"Stern bypassed second Aqua")
check(BlueHoennPilot.museum_aqua(2),"Second Aqua win missing")
check(!BlueHoennPilot.museum_aqua(2),"Second Aqua replayed")
check(BlueHoennPilot.stern,"Stern did not accept package after battles")
check(flags["stern_package_delivered"],"Stern flag not persisted")
check(BlueHoennPilot.stern,"Stern repeat dialog missing")
check(TrainerBattle.history.count([:BLUE_HOENN_AQUA,"Recruta",540])==1,
      "Second Aqua battled twice")

check(BlueHoennPilot.soothe_bell,"Soothe Bell gift missing")
check(BlueHoennPilot.soft_sand,"Soft Sand gift missing")
check(!BlueHoennPilot.soothe_bell,"Soothe Bell repeated")
check(!BlueHoennPilot.soft_sand,"Soft Sand repeated")
check($bag.items[:SOOTHEBELL]==1 && $bag.items[:SOFTSAND]==1,
      "Gift counts incorrect")
check(BlueHoennPilot.slateport_north_gate,"Route110 remained blocked after Stern")
check(!BlueHoennPilot.sign_stage5(:UNKNOWN),"Unknown sign accepted")
check(BlueHoennPilot.sign_stage5(:DEWFORD_GYM),"Dewford Gym sign missing")

$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
check(!BlueHoennPilot.museum_aqua(1),"Aqua repeated after save/reload")
check(BlueHoennPilot.stern,"Stern not saved after reload")
check(BlueRegions.local_achievements($PokemonGlobal.blue_regions,"HOENN")==["STONE","KNUCKLE"],
      "KNUCKLE lost after reload")
check($bag.items[:TM08]==1 && $bag.items[:TM47]==1,
      "TM duplicated on save/reload")
$PokemonGlobal.blue_regions["current"]="JOHTO"
snapshot=Marshal.dump($PokemonGlobal.blue_regions)
check(!BlueHoennPilot.brawly,"Brawly leaked into Johto")
check(!BlueHoennPilot.slateport_boat,"Boat leaked into Johto")
check(!BlueHoennPilot.stern,"Stern leaked into Johto")
check(Marshal.dump($PokemonGlobal.blue_regions)==snapshot,"Johto flags mutated")
puts "HOENN_STAGE5_RUNTIME_OK"
