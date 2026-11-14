# Hoenn QA04 Ruby contract. All fixtures synthetic; NOT Game.exe acceptance.
class HQ4Global;attr_accessor :blue_regions;end
class HQ4Pkmn
  attr_accessor :moves
  def initialize(*moves);@moves=moves;end
  def hasMove?(move);@moves.include?(move);end
end
class HQ4Trainer
  attr_accessor :party
  def initialize;@party=[HQ4Pkmn.new];end
end
class HQ4Bag
  attr_accessor :items,:space
  def initialize;@items=Hash.new(0);@space=true;end
  def has?(id);@items[id]>0;end
  def add(id,n=1);return false unless @space;@items[id]+=n;true;end
end
module GameData
  module Item
    Row=Struct.new(:move)
    @moves={HM01: :CUT,HM05: :FLASH,HM06: :ROCKSMASH,HM04: :STRENGTH,
            HM03: :SURF,HM08: :DIVE,HM07: :WATERFALL}
    def self.exists?(id);@moves.key?(id);end
    def self.get(id);Row.new(@moves.fetch(id));end
  end
end
module BlueRegions
  def self.local_achievements(state,area);state.fetch("achievements",{}).fetch(area,[]);end
end
module BlueRegionStart;def self.select_and_prepare;false;end;end
module EventHandlers;def self.add(*args);true;end;end
class HQ4Event
  attr_accessor :x,:y,:can_move,:refreshes
  def initialize;@x=9;@y=8;@can_move=true;@refreshes=0;end
  def refresh;@refreshes+=1;end
  def move_straight(dir);@x+=1 if @can_move && dir==6;end
end
class HQ4Map
  attr_accessor :map_id,:events
  def initialize;@map_id=950;@events={7=>HQ4Event.new};end
end
class HQ4Avatar
  attr_accessor :x,:y,:direction
  def initialize;@x=6;@y=6;@direction=6;end
  def moveto(x,y);@x=x;@y=y;end
end
module BlueRegionTravel
  @calls=[]
  class << self
    attr_reader :calls
    def move_to(position)
      @calls << position
      $game_map.map_id=position[0]
      $game_player.moveto(position[1],position[2])
      $game_player.direction=position[3]
      true
    end
  end
end
$messages=[]
def _INTL(message,*args)
  args.each_with_index{|x,i|message=message.gsub("{#{i+1}}",x.to_s)}
  message
end
def pbMessage(message,*args);$messages << message;0;end
def pbConfirmMessage(message);$messages<<message;true;end
def pbFadeOutIn;yield;end
def q4assert(value,label);raise "[HOENN_QA4] #{label}" unless value;end

require File.expand_path(ARGV.fetch(0))
BlueHoennPilot.define_singleton_method(:metadata){
  [[708,25,6],Hash[(1..322).map{|i|[i,i+700]}]]
}
$PokemonGlobal=HQ4Global.new
$PokemonGlobal.blue_regions={
  "version"=>1,"initial"=>"HOENN","current"=>"HOENN",
  "achievements"=>{"HOENN"=>[],"KANTO"=>%w[STONE KNUCKLE DYNAMO HEAT BALANCE MIND RAIN]},
  "hoenn_pilot"=>{"rusturf_aqua_defeated"=>true}
}
$player=HQ4Trainer.new
$bag=HQ4Bag.new
$game_map=HQ4Map.new
$game_player=HQ4Avatar.new
$game_self_switches={}
$scene=Object.new
$game_temp=Object.new

# Other regions' badges must never enable Hoenn field moves.
q4assert(!BlueHoennPilot.field_move_ready?(:SURF),"Kanto badge leaked into Hoenn")
$bag.add(:HM03)
$player.party[0].moves=[:SURF]
q4assert(!BlueHoennPilot.field_move_ready?(:SURF),"Surf without Hoenn Balance")
$PokemonGlobal.blue_regions["achievements"]["HOENN"] << "BALANCE"
q4assert(BlueHoennPilot.field_move_ready?(:SURF),"Surf after Balance, HM, move")
$player.party[0].moves=[]
q4assert(!BlueHoennPilot.field_move_ready?(:SURF),"Surf without party move")
$player.party[0].moves=[:SURF]

# Each HM must have the corresponding badge, item and party move.
{
  CUT:["STONE",:HM01],FLASH:["KNUCKLE",:HM05],
  ROCKSMASH:["DYNAMO",:HM06],STRENGTH:["HEAT",:HM04],
  DIVE:["MIND",:HM08],WATERFALL:["RAIN",:HM07]
}.each do |move,(badge,hm)|
  $bag.add(hm)
  $player.party[0].moves << move
  q4assert(!BlueHoennPilot.field_move_ready?(move),"#{move} without badge")
  $PokemonGlobal.blue_regions["achievements"]["HOENN"] << badge
  q4assert(BlueHoennPilot.field_move_ready?(move),"#{move} with badge+HM+party move")
end

# Regional HM rewards cannot duplicate or be granted before story gates.
$PokemonGlobal.blue_regions["achievements"]["HOENN"].delete("RAIN")
q4assert(!BlueHoennPilot.waterfall_from_juan,"Waterfall before Rain badge")
$PokemonGlobal.blue_regions["achievements"]["HOENN"] << "RAIN"
old_count=$bag.items[:HM07]
q4assert(BlueHoennPilot.waterfall_from_juan,"Juan Waterfall reward")
q4assert(!BlueHoennPilot.waterfall_from_juan,"Juan Waterfall duplicated")
q4assert($bag.items[:HM07]==old_count+1,"Waterfall item duplicated")
q4assert(BlueHoennPilot.state["hm_waterfall_received"],"Waterfall flag missing")

flags=BlueHoennPilot.state
q4assert(BlueHoennPilot.tunnelers,"Strength obtained after story conditions")
q4assert(!BlueHoennPilot.tunnelers,"Strength reward repeated")
q4assert(flags["hm_strength_received"],"Strength flag missing")

# RockSmash only after correct Hoenn badge + move; persistence uses regional
# flags and self-switch A, with no global Kanto/Johto flags.
$game_map.map_id=950
$bag.items[:HM06]=0
q4assert(!BlueHoennPilot.rock_smash_obstacle(7),"RockSmash without HM")
$bag.add(:HM06)
q4assert(BlueHoennPilot.rock_smash_obstacle(7),"RockSmash after requirements")
q4assert($game_self_switches[[950,7,"A"]],"RockSmash switch not saved")
q4assert(flags["rock_smash_950_7"],"RockSmash regional flag not saved")
q4assert(BlueHoennPilot.rock_smash_obstacle(7),"RockSmash repeat not idempotent")

# Strength boulder moves one step toward the avatar's facing direction and
# must not be marked as moved if the engine collision blocks it.
event=$game_map.events[7]
event.can_move=false
q4assert(!BlueHoennPilot.strength_boulder(7),"Strength moved through collision")
event.can_move=true
q4assert(BlueHoennPilot.strength_boulder(7),"Strength did not push")
q4assert([event.x,event.y]==[10,8],"Strength moved wrong direction")

# Waterfall is required to reach upper Ever Grande. No direct shortcut.
_,mapping=BlueHoennPilot.metadata
$game_map.map_id=mapping[91]
$bag.items[:HM07]=0
q4assert(!BlueHoennPilot.stage10_transfer(91,322,3,4),"Ever Grande bypassed Waterfall")
$bag.add(:HM07)
q4assert(BlueHoennPilot.stage10_transfer(91,322,3,4),"Waterfall map gate failed")
q4assert(BlueRegionTravel.calls.last[0]==mapping[322],"Waterfall target map wrong")

# Dive must be ready before entering a submerged map, and a region switch
# must make all our field handlers inert.
$game_map.map_id=mapping[147]
$bag.items[:HM08]=0
q4assert(!BlueHoennPilot.stage10_transfer(147,255,4,4),"Dive bypassed HM")
$bag.add(:HM08)
q4assert(BlueHoennPilot.stage10_transfer(147,255,4,4),"Dive entrance gate failed")
$PokemonGlobal.blue_regions=Marshal.load(Marshal.dump($PokemonGlobal.blue_regions))
q4assert(BlueHoennPilot.state["rock_smash_950_7"],"RockSmash lost after save/load")
$PokemonGlobal.blue_regions["current"]="KANTO"
before=Marshal.dump($PokemonGlobal.blue_regions)
q4assert(!BlueHoennPilot.field_move_ready?(:SURF),"Hoenn move leaked to Kanto")
q4assert(!BlueHoennPilot.rock_smash_obstacle(7),"Hoenn rock leaked to Kanto")
q4assert(!BlueHoennPilot.strength_boulder(7),"Hoenn boulder leaked to Kanto")
q4assert(Marshal.dump($PokemonGlobal.blue_regions)==before,"Kanto save mutated")

puts "HOENN_QA4_FIELD_GATES_RUNTIME_OK"
