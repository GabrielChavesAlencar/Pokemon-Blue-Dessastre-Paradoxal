# Exercita o KantoPilot.rb real. O blackout nativo e o centro de cura sao
# representados por fixtures sem ROM, Game.exe ou saves pessoais.
require "tmpdir"

source = File.expand_path(ARGV.fetch(0))
class Game_Player
  attr_accessor :x, :y, :direction
  def initialize; @x=0; @y=0; @direction=2; end
end
module MenuHandlers
  def self.add(*_args); end
end
module BlueRegions
  def self.new_state(region)
    {"version"=>1,"current"=>region,"achievements"=>{region=>[]}}
  end
  def self.local_achievements(state, region)
    state.fetch("achievements",{}).fetch(region,[])
  end
  def self.award(state,region,badge)
    badges = (state["achievements"] ||= {})[region] ||= []
    return false if badges.include?(badge)
    badges << badge
    true
  end
  def self.snapshot; $PokemonGlobal.blue_regions; end
  def self.profile(_state,_full); :world_champion_rematch; end
end
# This fixture tests blackout semantics, not Kanto PBS compilation.
# The production Gary test checks all three real trainer registry versions.
module GameData
  class TrainerType
    def self.exists?(_type); true; end
  end
  class Trainer
    def self.exists?(_type, _name, _version); true; end
  end
end
module BlueMusic
  def self.kanto_me_play(*_args); end
  def self.with_kanto_scene(_scene); yield; end
end
module BlueStory
  def self.with_regional_full_power; yield; end
end
module BlueLocale
  def self.enabled?; true; end
  def self.with_raw; yield; end
end
def _INTL(s,*args)
  s.gsub(/\{(\d+)\}/) { args[$1.to_i-1].to_s }
end
def pbMessage(*_args); end
def pbConfirmMessage(*_args); true; end
def verify(condition,reason)
  raise "KANTO_BLACKOUT_FAILURE: #{reason}" unless condition
end
class FakePlayer
  attr_reader :heal_count, :name
  def initialize; @name="Red"; @heal_count=0; end
  def able_pokemon_count; 1; end
  def heal_party; @heal_count += 1; end
end
class FakeMap
  attr_accessor :map_id
  def initialize; @map_id=0; end
end
class GlobalState
  attr_accessor :blue_regions, :pokecenterMapId, :pokecenterX,
                :pokecenterY, :pokecenterDirection
end
def pbSetPokemonCenter
  $PokemonGlobal.pokecenterMapId=$game_map.map_id
  $PokemonGlobal.pokecenterX=$game_player.x
  $PokemonGlobal.pokecenterY=$game_player.y
  $PokemonGlobal.pokecenterDirection=$game_player.direction
end
$rules=[]
$blackouts=0
def setBattleRule(*args); $rules.concat(args); end
def pbStartOver
  $blackouts += 1
  verify($PokemonGlobal.pokecenterMapId, "missing native center checkpoint")
  $player.heal_party
  $game_map.map_id=$PokemonGlobal.pokecenterMapId
  $game_player.x=$PokemonGlobal.pokecenterX
  $game_player.y=$PokemonGlobal.pokecenterY
  $game_player.direction=$PokemonGlobal.pokecenterDirection
end
class TrainerBattle
  def self.start(*_args)
    verify($rules.include?("cannotLose") && !$rules.include?("canLose"),
           "Kanto fight still suppresses native blackout")
    result = $next_battle_result
    pbStartOver if !result
    result
  ensure
    $rules=[]
  end
end
def travel(map,x,y)
  $game_map.map_id=map
  $game_player.x=x
  $game_player.y=y
end
def checkpoint(map,x,y,dir)
  travel(map,x,y)
  $game_player.direction=dir
  BlueKantoPilot.heal
  verify([$PokemonGlobal.pokecenterMapId,$PokemonGlobal.pokecenterX,
          $PokemonGlobal.pokecenterY,$PokemonGlobal.pokecenterDirection]==[map,x,y,dir],
         "nurse failed to register the last center")
end
def run_loss
  $next_battle_result=false
  $blackouts_before=$blackouts
  $heals_before=$player.heal_count
end
def check_loss(map,x,y,dir,reason)
  verify($blackouts==$blackouts_before+1, "#{reason}: native blackout skipped")
  verify([$game_map.map_id,$game_player.x,$game_player.y,$game_player.direction]==[map,x,y,dir],
         "#{reason}: respawned at battlefield instead of last center")
  verify($player.heal_count==$heals_before+1,
         "#{reason}: healed outside native blackout or healed twice")
end

Dir.mktmpdir("kanto-blackout-") do |tmp|
  Dir.chdir(tmp) do
    File.write("Kanto pilot.json","{}")
    load source
    $PokemonGlobal=GlobalState.new
    $PokemonGlobal.blue_regions=BlueRegions.new_state("KANTO")
    $PokemonGlobal.blue_regions["pilot_starter"]="BULBASAUR"
    $player=FakePlayer.new
    $game_player=Game_Player.new
    $game_map=FakeMap.new

    # First healing center is not necessarily the most recent.
    checkpoint(701,8,9,2)
    checkpoint(742,5,6,8)
    travel(799,11,13)
    run_loss
    verify(BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER,"Rick","KANTO_024_016")==false,
           "losing a trainer battle returned a victory result")
    check_loss(742,5,6,8,"ordinary trainer")
    verify(!BlueKantoPilot.progress.fetch("pilot_wins",[]).include?("KANTO_024_016"),
           "lost trainer is marked as defeated")

    # A loss does not make a trainer one-time-only: retry and win still work.
    $next_battle_result=true
    BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER,"Rick","KANTO_024_016")
    verify(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_024_016"),
           "trainer cannot be defeated after blacking out")

    travel(811,6,7)
    run_loss
    BlueKantoPilot.battle(:BLUE_KANTO_LEADER,"Brock","KANTO_028_007")
    check_loss(742,5,6,8,"Brock")
    verify(!BlueRegions.local_achievements(BlueKantoPilot.progress,"KANTO").include?("BOULDER"),
           "lost battle awarded Boulder Badge")

    # Tutorial rival must be retriable after blackout and cannot advance story.
    travel(705,9,7)
    run_loss
    verify(BlueKantoPilot.rival==false,"tutorial rival loss was treated as success")
    check_loss(742,5,6,8,"tutorial rival")
    verify(!BlueKantoPilot.progress["pilot_rival"],"lost rival battle advanced story")

    # Postgame Full Power trainer: the reward must not be recorded on loss.
    BlueKantoPilot.progress["leagues"]=["KANTO"]
    travel(811,6,7)
    run_loss
    BlueKantoPilot.full_power_gym("Brock", :BLUE_KANTO_LEADER)
    check_loss(742,5,6,8,"Full Power gym")
    verify(BlueKantoPilot.progress.fetch("pilot_full_power_gym_wins",[]).empty?,
           "lost Full Power rematch granted victory")

    # Double battle also uses native blackout, without marking either NPC.
    travel(818,12,10)
    run_loss
    verify(BlueKantoPilot.victory_couple==false,"double loss returned success")
    check_loss(742,5,6,8,"Victory Road double")
    verify(!BlueKantoPilot.progress.fetch("pilot_wins",[]).include?("KANTO_213_PAIR"),
           "double trainer pair marked defeated on loss")

    # League run resets while the party respawns at the most recent Center,
    # NEVER at an old, hard-coded League lobby.
    BlueKantoPilot.progress["leagues"]=[]
    BlueKantoPilot.progress["achievements"]["KANTO"] = BlueKantoPilot::LEAGUE_REQUIRED_BADGES.dup
    BlueKantoPilot.progress["pilot_league_active"]=true
    BlueKantoPilot.progress["pilot_league_full_power"]=false
    BlueKantoPilot.progress["pilot_league_wins"]=[]
    checkpoint(850,11,16,2)
    travel(860,14,18)
    run_loss
    verify(BlueKantoPilot.league_battle("LORELEI",:BLUE_KANTO_ELITE,"Lorelei",999)==false,
           "League loss returned success")
    check_loss(850,11,16,2,"League")
    verify(BlueKantoPilot.progress["pilot_league_active"]==false &&
           BlueKantoPilot.progress["pilot_league_wins"]==[],
           "League loss did not reset the current attempt")
    verify(BlueKantoPilot.progress["achievements"]["KANTO"]==
           BlueKantoPilot::LEAGUE_REQUIRED_BADGES,
           "League loss erased earned Kanto badges")
    verify(BlueKantoPilot.progress["pilot_wins"].include?("KANTO_024_016"),
           "League loss erased previous trainer victory")
  end
end
puts "PASS: Kanto native blackout goes to last healed Pokemon Center; all battle types; no story progression or double healing"
