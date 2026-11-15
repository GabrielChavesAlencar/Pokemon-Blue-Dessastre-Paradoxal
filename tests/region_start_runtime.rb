# Standalone regression: no RMXP, graphics, saves or external game data.
require "tmpdir"
require "fileutils"

class PokemonGlobalMetadata
  attr_accessor :blue_regions, :blue_story_mode, :blue_traditional_starters,
                :blue_campaign_started, :blue_campaign_departure,
                :blue_campaign_mechanics
end

class FakeSystem
  attr_accessor :start_map_id, :start_x, :start_y
  def initialize
    @start_map_id, @start_x, @start_y = 4, 7, 8
  end
end

module Game
  class << self
    attr_reader :seen
    def start_new
      SaveData.load_new_game_values
      @seen = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]
    end
    def load(old_data)
      $PokemonGlobal.blue_regions = old_data
    end
  end
end

module SaveData
  def self.load_new_game_values
    $PokemonGlobal = PokemonGlobalMetadata.new
  end
end

module BlueRegions
  def self.circuit
    %w[DECADES KANTO JOHTO HOENN SINNOH UNOVA KALOS ALOLA GALAR PALDEA]
  end
  def self.info(region)
    {"name" => region.capitalize}
  end
  def self.new_state(region)
    {"initial" => region, "current" => region, "leagues" => []}
  end
  def self.snapshot
    $PokemonGlobal.blue_regions
  end
end

module BlueStory
  def self.choose_mode(mode)
    $PokemonGlobal.blue_story_mode = mode
  end
end
module BlueCampaign
  def self.begin_journey(prompt=true)
    $PokemonGlobal.blue_campaign_started = true
    $PokemonGlobal.blue_campaign_departure = true
    $PokemonGlobal.blue_campaign_mechanics={
      "tera"=>true,"mega"=>true,"zmove"=>true,"dynamax"=>
        ($PokemonGlobal.blue_regions["current"]!="DECADES")
    }
  end
end
module GameData
  module Species
    def self.exists?(species); [:BULBASAUR,:CHARMANDER,:SQUIRTLE].include?(species); end
  end
end
class Pokemon
  attr_reader :species,:level
  def initialize(species,level,_owner);@species,@level=species,level;end
end
class Interpreter
  attr_accessor :map_id,:parameters,:list,:index,:branch
  def initialize
    @map_id=4;@index=0;@branch={}
    @list=[Struct.new(:indent).new(0)]
  end
  def command_102
    $native_intro_menus ||= 0
    $native_intro_menus += 1
    true
  end
end
def pbCharacterSelect
  $native_profile_menus ||= 0
  $native_profile_menus += 1
  true
end
def pbPokemonSelection(*_args)
  $native_starter_menus ||= 0
  $native_starter_menus += 1
  nil
end

def pbRgssExists?(path)
  File.file?(path)
end

$choices = []
$messages = 0
$last_options = nil
class FakePlayer
  attr_accessor :character_id, :transparent
  attr_reader :visible
  def refresh_charset
    @visible = [0,1].include?(character_id) && !transparent
  end
end

def pbChangePlayer(id)
  $game_player.character_id = id
end
def pbMessage(message, choices=nil, default=nil)
  $messages += 1
  $last_options = choices if choices
  choices ? $choices.shift : nil
end

def pbConfirmMessage(message)
  true
end

def _INTL(text, *args)
  args.each_with_index { |value, index| text = text.gsub("{#{index+1}}", value.to_s) }
  text
end

def check(condition, message)
  raise message unless condition
end

require ARGV.fetch(0)
BlueRegionStart.install
Dir.mktmpdir("blue-region-start-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    File.binwrite("Data/Map004.rxdata", "native Decades opening")
    $data_system = FakeSystem.new
    $game_map = Struct.new(:map_id).new(4)
    $game_temp = Struct.new(:begun_new_game).new(true)
    $game_player = FakePlayer.new

    # Without a completed install, new game stays in native Decades.
    Game.start_new
    check(Game.seen == [4,7,8], "Decades location changed")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Decades default missing")
    check($messages == 0, "Empty Kanto must not prompt or hang")

    # The regional choice opens after Story Mode and never on Game.start_new.
    File.binwrite("Data/Map321.rxdata", "pilot")
    File.write("Data/blue-kanto-start.txt", "BLUE_KANTO_START_V1,KANTO,321,28,14\n")
    Game.start_new
    check(Game.seen == [4,7,8] && $messages == 0, "Integrated start bypassed the mode choice")
    $choices = [0, 1]
    check(BlueRegionStart.story_spawn.nil?, "Decades must use the original story")
    check($last_options == ["Decades", "Kanto"], "Wrong installed story options")
    check(BlueRegionStart.story_spawn == ["KANTO", [321,28,14]], "Kanto story destination is wrong")
    $game_temp.begun_new_game = false
    check(BlueRegionStart.story_spawn.nil?, "Loaded save unexpectedly showed a region menu")
    $game_temp.begun_new_game = true
    BlueRegionStart.prepare_regional_story("KANTO")
    check($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto was not persisted")
    check($PokemonGlobal.blue_story_mode == :story, "Kanto did not use Story Mode")
    check($PokemonGlobal.blue_traditional_starters == true, "Traditional starters not enabled")
    check($PokemonGlobal.blue_campaign_departure == false, "Kanto starter bag would be cleared")

    # A Johto map alone is not enough; only a verified local install/pilot
    # will write the dedicated Johto start and installation markers.
    File.binwrite("Data/Map712.rxdata", "synthetic Johto player room")
    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,712,9,6\n")
    check(!BlueRegionStart.playable?("JOHTO"), "Uninstalled Johto was enabled by a lone marker")
    check(BlueRegionStart.johto_spawn.nil?, "Johto start without install proof was accepted")

    File.write("Data/blue-johto-install.json", "{}")
    check(!BlueRegionStart.playable?("JOHTO"),
          "Empty Johto install manifest spoofed playable maps")
    File.binwrite("Data/MapInfos.rxdata", "base map infos")
    File.binwrite("Data/Tilesets.rxdata", "base tilesets")
    File.binwrite("Data/Map713.rxdata", "audited Johto town map")
    hashes = %w[Data/MapInfos.rxdata Data/Tilesets.rxdata
                Data/Map712.rxdata Data/Map713.rxdata].map do |name|
      [name, Digest::SHA256.file(name).hexdigest]
    end.to_h
    proof = {
      "schema"=>1, "region"=>"JOHTO", "status"=>"VERIFIED_PLAYABLE",
      "source_archive_sha256"=>"a" * 64,
      "checks"=>BlueRegionStart::JOHTO_PROOFS.map { |key| [key, true] }.to_h,
      "start"=>[712,9,6,2], "travel_point"=>[713,10,11,2],
      "npc_point"=>[713,11,11,4],
      "file_hashes"=>hashes
    }
    File.write("Data/blue-johto-install.json", JSON.generate(proof))
    check(BlueRegionStart.playable?("JOHTO"), "Approved synthetic Johto pilot was blocked")
    check(BlueRegionStart.johto_town_point == [713,10,11,2],
          "Approved Johto town travel point is wrong")
    proof["checks"]["trainers_pbs"] = false
    File.write("Data/blue-johto-install.json", JSON.generate(proof))
    check(!BlueRegionStart.playable?("JOHTO"), "Uncompiled PBS enabled Johto")
    proof["checks"]["trainers_pbs"] = true
    proof["file_hashes"] = hashes.merge("Data/Map713.rxdata" => "0" * 64)
    File.write("Data/blue-johto-install.json", JSON.generate(proof))
    check(!BlueRegionStart.playable?("JOHTO"), "Modified Johto town map passed hash check")
    proof["file_hashes"] = hashes
    File.write("Data/blue-johto-install.json", JSON.generate(proof))
    Game.start_new
    $choices = [2]
    check(BlueRegionStart.story_spawn == ["JOHTO", [712,9,6]], "Johto story destination is wrong")
    check($last_options == ["Decades", "Kanto", "Johto"], "Installed Johto was dropped")
    check([$data_system.start_map_id,$data_system.start_x,$data_system.start_y] == [4,7,8],
          "Johto changed the native Decades start coordinates")

    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,321,-1,5\n")
    check(BlueRegionStart.johto_spawn.nil?, "Invalid Johto spawn was accepted")
    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,712,9,6\n")

    # Both regional pilot switches must be isolated: Kanto's pilot remains
    # Kanto, Johto's pilot goes to Johto, neither opens the region picker.
    File.write("Johto pilot.json", "{}")
    $messages = 0
    Game.start_new
    check(Game.seen == [712,9,6], "Johto pilot did not start in Johto")
    check($messages == 0, "Johto pilot unexpectedly opened region picker")
    File.delete("Johto pilot.json")

    # The MAIN Decades executable must not accept a standalone Kanto marker:
    # require the audited, merged map manifest, PBS and runtime plugin.
    check(!BlueRegionStart.kanto_integrated?, "Stray Kanto marker enabled main campaign")
    check(!BlueRegionStart.request_initial("KANTO"), "Uninstalled Kanto could start")
    FileUtils.mkdir_p("PBS")
    %w[encounters trainers trainer_types map_metadata map_connections].each do |name|
      File.write("PBS/#{name}_kanto.txt", "[KANTO]\n")
    end
    FileUtils.mkdir_p("Plugins/ZZZZZ Blue Kanto Pilot")
    File.write("Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb", "# mock native plugin")
    %w[blue-kanto-locale.dat blue-kanto-npc-dialogues.dat
       blue-kanto-pewter-route3-gate.txt blue-kanto-pewter-mom-sprite.txt
       blue-kanto-viridian-route2-line.txt blue-kanto-silph-floors.txt].each do |name|
      File.write("Data/#{name}", "mock Kanto data")
    end
    mapping = (1..142).map { |n| [n.to_s, n == 7 ? 321 : (n == 5 ? 713 : 400+n)] }.to_h
    install = {"schema"=>1, "source"=>"Essentials FRLG 21.1", "maps"=>mapping}
    File.write("Data/blue-kanto-install.json", JSON.generate(install))
    check(BlueRegionStart.kanto_integrated?, "Audited main Kanto install was not recognized")
    File.write("Data/blue-kanto-ready.txt", "BLUE_KANTO_READY_V1,142,321\n")
    check(BlueRegionStart.kanto_ready_gate?([321,28,14]),
          "JSON-free Kanto runtime gate was not recognized")
    check(!BlueRegionStart.kanto_ready_gate?([322,28,14]),
          "Kanto runtime gate accepted a wrong map ID")
    File.write("Data/blue-kanto-ready.txt", "BLUE_KANTO_READY_V1,25,321\n")
    check(!BlueRegionStart.kanto_ready_gate?([321,28,14]),
          "Old 25-map Kanto gate was incorrectly accepted")
    File.write("Data/blue-kanto-ready.txt", "BLUE_KANTO_READY_V1,142,321\n")
    install["schema"] = 99
    File.write("Data/blue-kanto-install.json", JSON.generate(install))
    check(!BlueRegionStart.kanto_integrated?, "Malformed Kanto installation was accepted")
    install["schema"] = 1
    File.write("Data/blue-kanto-install.json", JSON.generate(install))
    check(BlueRegionStart.request_initial("KANTO"), "Integrated Kanto title selection blocked")
    $game_temp.begun_new_game = true
    Game.start_new
    check(Game.seen == [321,28,14], "Integrated Kanto did not start in Pallet home")
    check($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto initial region missing")
    check($PokemonGlobal.blue_regions["current"] == "KANTO", "Kanto current region missing")
    check($PokemonGlobal.blue_regions["decades_first_arrival"] == [4,7,8,2],
          "Native Decades arrival point was not preserved for free early travel")
    check($PokemonGlobal.blue_regions["pilot_profile_pending"], "Kanto profile scene skipped")
    check($PokemonGlobal.blue_campaign_departure == false, "Kanto starter bag cleared")
    check([$data_system.start_map_id,$data_system.start_x,$data_system.start_y] == [4,7,8],
          "Main Decades start in System was modified permanently")
    check(BlueRegionStart.choose_initial == "DECADES", "Kanto choice leaked into next new game")

    # Choosing Decades on the title must not display the second, old Story
    # Mode region picker. It must keep Decades coordinates and save context.
    check(BlueRegionStart.request_initial("DECADES"), "Decades title selection rejected")
    Game.start_new
    check(Game.seen == [4,7,8], "Decades start was displaced by Kanto")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Decades original save altered")
    check(BlueRegionStart.story_spawn.nil?, "Decades got a duplicate region prompt")
    check($PokemonGlobal.blue_story_mode == :story, "Decades new game did not auto-start Story Mode")
    check($PokemonGlobal.blue_campaign_mechanics ==
          {"tera"=>true,"mega"=>true,"zmove"=>true,"dynamax"=>false},
          "Decades new game did not disable only Dynamax")
    check(BlueRegionStart.decades_auto_intro?, "Decades native intro did not use auto setup")
    $native_profile_menus=0
    pbCharacterSelect
    check($native_profile_menus==0 && $game_player.character_id==0,
          "Decades new game reopened the character menu")
    $native_intro_menus=0
    interpreter=Interpreter.new
    interpreter.parameters=[["Battle Mode","Story Mode"]]
    interpreter.command_102
    check(interpreter.branch[0]==1 && $native_intro_menus==0,
          "Decades introduction asked for the game mode")
    interpreter.parameters=[["Any Pokémon","Traditional Starters","Cancel"]]
    interpreter.command_102
    check(interpreter.branch[0]==1 && $native_intro_menus==0,
          "Decades introduction asked for the starter-selection mode")
    $native_starter_menus=0
    $player=Object.new
    selected=[pbPokemonSelection(:Traditional_Starters),
              pbPokemonSelection(:Traditional_Starters)]
    check(selected.map(&:species)==[:BULBASAUR,:CHARMANDER] &&
          $native_starter_menus==0,
          "Decades native traditional starters reopened their selection UI")
    $game_map.map_id=77
    check(!BlueRegionStart.decades_auto_intro?, "Decades setup leaked into Cherryhill")
    pbCharacterSelect
    check($native_profile_menus==1,
          "Loaded maps outside Decades intro had profile UI intercepted")
    $game_map.map_id=4

    old_save = {"version"=>1,"initial"=>"DECADES","current"=>"DECADES","leagues"=>["DECADES"]}
    # A load must never start a new game, irrespective of the last tested
    # regional spawn. Johto tests above intentionally changed Game.seen.
    before_load = Game.seen.dup
    Game.load(old_save)
    check($PokemonGlobal.blue_regions.equal?(old_save), "Legacy load was modified")
    check(Game.seen == before_load, "Loading old save unexpectedly restarted game")

    # The stand-alone pilot is always Kanto and never opens a region picker.
    File.write("Kanto pilot.json", "{}")
    $messages = 0
    Game.start_new
    check(Game.seen == [321,28,14], "Standalone pilot no longer starts in Kanto")
    check($messages == 0, "Pilot should bypass region picker")
    check($game_player.visible, "Pilot character invisible before the first step")
    check($PokemonGlobal.blue_regions["pilot_profile_pending"], "Pilot profile event not requested")
  end
end
puts "Blue regional new-game selection OK"
