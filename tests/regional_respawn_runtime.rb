# Regression for the actual Object.prepend hook before Essentials pbStartOver.
# No Game.exe, save migration, PBS or original map file is changed.
require "tmpdir"
require "ostruct"
class GlobalState
  attr_accessor :blue_regions,:pokecenterMapId,:pokecenterX,:pokecenterY,:pokecenterDirection
end
class MapState
  attr_accessor :map_id
  def initialize(id); @map_id=id; end
end
class FakePlayer
  attr_reader :heals
  def initialize; @heals=0; end
  def heal_party; @heals+=1; end
end
module GameData
  class MapMetadata
    DATA={}
    def self.try_get(id); DATA[id]; end
  end
end
module BlueRegionTravel
  def self.decades_city_map_id;77;end
  def self.decades_town_point;[77,13,18,2];end
end
module BlueRegionStart
  def self.johto_install_proof
    {"file_hashes" => {"Data/Map601.rxdata"=>"test", "Data/Map602.rxdata"=>"test",
                       "Data/Map713.rxdata"=>"test"}}
  end
  def self.johto_town_point;[713,10,11,2];end
end
module BlueBattleLab
  ACTIVE=false
end
MapInfo=Struct.new(:name)
$global_original_call=0
$global_set_call=0
def pbSetPokemonCenter
  $global_set_call+=1
  g=$PokemonGlobal
  g.pokecenterMapId=$game_map.map_id
  g.pokecenterX=$player_x
  g.pokecenterY=$player_y
  g.pokecenterDirection=$player_dir
end
def pbStartOver
  $global_original_call+=1
  g=$PokemonGlobal
  $game_map.map_id=g.pokecenterMapId
  $player_x=g.pokecenterX
  $player_y=g.pokecenterY
  $player_dir=g.pokecenterDirection
  $player.heal_party
end
def check(value,msg)
  raise "REGIONAL_RESPAWN: #{msg}" unless value
end
load File.expand_path(ARGV.fetch(0))
BlueRegionalRespawn.install
BlueRegionalRespawn.install
check(Object.ancestors.count(BlueRegionalRespawn::NativeCheckpoints)==1,"double prepend")
Dir.mktmpdir("blue-region-blackout") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    [77,79,300,301,302,310,311,326,601,602,605,606,713,813].each do |id|
      File.write(sprintf("Data/Map%03d.rxdata",id),"fixture")
    end
    File.write("Kanto pilot.json",'{"maps":{"5":300,"6":301,"7":302,"10":310,"11":311,"26":326,"87":605,"88":606}}')
    $data_mapinfos=Array.new(815)
    $data_mapinfos[77]=MapInfo.new("Cherryhill City")
    $data_mapinfos[79]=MapInfo.new("Cherryhill Pokémon Center")
    $data_mapinfos[300]=MapInfo.new("Pallet Town")
    $data_mapinfos[311]=MapInfo.new("Viridian Pokémon Center")
    $data_mapinfos[601]=MapInfo.new("Cherrygrove City")
    $data_mapinfos[602]=MapInfo.new("Cherrygrove Pokémon Center")
    GameData::MapMetadata::DATA[77]=OpenStruct.new(healing_spot:[79,3,5])
    GameData::MapMetadata::DATA[601]=OpenStruct.new(healing_spot:[602,8,9])
    $PokemonGlobal=GlobalState.new
    $PokemonGlobal.blue_regions={"version"=>1,"current"=>"KANTO"}
    $player=FakePlayer.new
    $game_map=MapState.new(300)
    $player_x=9;$player_y=9;$player_dir=2
    # Before visiting any Center, Oak remains the native Kanto checkpoint.
    pbSetPokemonCenter
    check($PokemonGlobal.blue_regions["regional_pokecenters"].nil?,"Oak incorrectly became a Pokemon Center")
    pbStartOver
    check($game_map.map_id==300,"original native Pallet checkpoint was lost")
    # Enter Kanto with a stale native checkpoint from Decades.
    $game_map.map_id=310
    $PokemonGlobal.pokecenterMapId=79
    $PokemonGlobal.blue_regions["regional_pokecenter_owner"]=nil
    $heals_before=$player.heals;$calls_before=$global_original_call
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[311,7,8,2],
          "stale Decades checkpoint did not fall back to Viridian Center")
    check($player.heals==$heals_before+1 && $global_original_call==$calls_before+1,
          "blackout did not use the native engine exactly once")
    # Heal in a later Kanto Center, then travel Decades and Johto and back.
    $game_map.map_id=326;$player_x=11;$player_y=15;$player_dir=8
    $data_mapinfos[326]=MapInfo.new("Cerulean Pokémon Center")
    pbSetPokemonCenter
    state=$PokemonGlobal.blue_regions
    check(state["regional_pokecenters"]["KANTO"]==[326,11,15,8],
          "Kanto nurse did not remember local checkpoint")
    state["current"]="DECADES"
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[79,3,5,2],
          "Decades did not use verified Cherryhill healing spot")
    # Healing in Decades must not erase Kanto.
    $game_map.map_id=79;$player_x=4;$player_y=6;$player_dir=2
    pbSetPokemonCenter
    check(state["regional_pokecenters"]["DECADES"]==[79,4,6,2],
          "Decades nurse was not recorded")
    state["current"]="KANTO"
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[326,11,15,8],
          "return to Kanto did not restore latest regional healing spot")
    # New Johto player: should not be sent to Kanto, even if never healed.
    state["current"]="JOHTO"
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[602,8,9,2],
          "Johto did not use Cherrygrove's verified healing spot")
    # Back to Decades must remember its last native Center.
    state["current"]="DECADES"
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[79,4,6,2],
          "Decades nurse visit forgotten after returning")
    # The new Center must be identified through the campaign registry even
    # if the engine has not provided any localized map-info name.
    state["current"]="KANTO"
    $data_mapinfos=nil
    $game_map.map_id=606;$player_x=7;$player_y=4;$player_dir=8
    pbSetPokemonCenter
    check(state["regional_pokecenters"]["KANTO"]==[606,7,4,8],
          "Rock Tunnel Center was not remembered without MapInfos")
    $game_map.map_id=605;$player_x=9;$player_y=30;$player_dir=2
    pbSetPokemonCenter
    check(state["regional_pokecenters"]["KANTO"]==[606,7,4,8],
          "outdoor Route 10 was incorrectly remembered as a Center")
    $PokemonGlobal.pokecenterMapId=79
    state["regional_pokecenter_owner"]="DECADES"
    pbStartOver
    check([$game_map.map_id,$player_x,$player_y,$player_dir]==[606,7,4,8],
          "cross-region blackout did not restore the Rock Tunnel Center point")
    # A loaded legacy save with no regional campaign must remain native.
    $PokemonGlobal.blue_regions=nil
    $PokemonGlobal.pokecenterMapId=311
    pbStartOver
    check($game_map.map_id==311,"legacy nonregional save was modified")
    # Corrupt remembered values must never redirect to a missing map.
    state={"version"=>1,"current"=>"KANTO",
           "regional_pokecenter_owner"=>"JOHTO",
           "regional_pokecenters"=>{"KANTO"=>[9999,5,5,2]}}
    $PokemonGlobal.blue_regions=state
    $PokemonGlobal.pokecenterMapId=602
    pbStartOver
    check($game_map.map_id==311,"unverified remembered map bypassed regional fallback")
    # Never remove the default game-over handler or transfer twice.
    check($global_original_call==$player.heals,"blackout recovery healed twice or skipped")
  end
end
puts "PASS: Kanto/Viridian, Decades/Cherryhill, Johto/Cherrygrove, save isolation and native blackout"
