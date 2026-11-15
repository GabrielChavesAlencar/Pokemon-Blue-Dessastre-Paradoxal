# Tests the real KantoPilot.rb against synthetic, isolated Essentials APIs.
# Does not download FRLG, change user saves, or execute Game.exe.
require "tmpdir"
require "fileutils"

source = File.expand_path(ARGV.fetch(0))
def assert_gary(value, message)
  raise "KANTO_GARY_BATTLE: #{message}" unless value
end

class Game_Player; end
module MenuHandlers
  def self.add(*); end
end
module BlueRegions
  def self.new_state(region)
    {"version"=>1, "current"=>region, "initial"=>region, "leagues"=>[],
     "achievements"=>{}}
  end
end
module BlueMusic
  def self.with_kanto_scene(_name)
    yield
    raise "Mock Kanto music restore failed" if $broken_music
  end
  def self.kanto_me_play(*); end
end
module BlueLocale
  def self.enabled?; true; end
  def self.with_raw; yield; end
end
def _INTL(text, *args)
  text.gsub(/\{(\d+)\}/) { args[$1.to_i - 1].to_s }
end
$messages = []
def pbMessage(text, *_args); $messages << text; end

module GameData
  class TrainerType
    def self.exists?(name); !$missing_type && name == :BLUE_KANTO_RIVAL; end
  end
  class Trainer
    DATA = {}
    def self.exists?(type, name, version)
      DATA.key?([type, name, version])
    end
    def self.register(row)
      DATA[row.fetch(:id)] = row
    end
  end
  class Species
    def self.exists?(name)
      %i[CHARMANDER SQUIRTLE BULBASAUR].include?(name)
    end
  end
  class Move
    def self.exists?(name)
      %i[TACKLE GROWL SCRATCH TAILWHIP].include?(name)
    end
  end
  class Item
    def self.exists?(name); name == :ORANBERRY; end
  end
end

class FakePlayer
  attr_reader :name, :heals
  def initialize
    @name = "P"
    @heals = 0
  end
  def able_pokemon_count; 1; end
  def heal_party; @heals += 1; end
end
class FakeTemp
  attr_reader :clear_count
  def initialize; @clear_count = 0; end
  def clear_battle_rules; @clear_count += 1; end
end
class TrainerBattle
  def self.start(type, name, version)
    $attempted_battles << [type, name, version]
    raise "Mock battle engine failed during transition" if $raise_battle
    $battle_result
  end
end
$rules = []
def setBattleRule(value); $rules << value; end
$attempted_battles = []

Dir.mktmpdir("kanto-gary-regression-") do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p("PBS")
    FileUtils.mkdir_p("Data")
    # Exact Kanto author-PBS section shape; the fixture team is NOT injected
    # into production. Production reads the installed verified PBS instead.
    File.write("PBS/trainers_kanto.txt", <<~PBS)
      # Source: [RIVAL1,Blue,11]
      [BLUE_KANTO_RIVAL,Blue,11]
      Pokemon = CHARMANDER,5
      Moves = SCRATCH,GROWL

      # Source: [RIVAL1,Blue,12]
      [BLUE_KANTO_RIVAL,Blue,12]
      Pokemon = SQUIRTLE,5
      Moves = TACKLE,TAILWHIP

      # Source: [RIVAL1,Blue,13]
      [BLUE_KANTO_RIVAL,Blue,13]
      Pokemon = BULBASAUR,5
      Moves = TACKLE,GROWL
    PBS
    File.write("Data/blue-kanto-install.json", '{"schema":1}')
    load source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    $player = FakePlayer.new
    $game_temp = FakeTemp.new
    assert_gary(!BlueKantoPilot::PILOT_OVERWORLD_SCALE &&
                BlueKantoPilot::INTEGRATED_KANTO,
                "Test didn't exercise the merged Decades/Kanto runtime")

    # A clean integrated game must resolve all three rival versions from the
    # original PBS, without inventing a roster or overwriting Decades.
    {"BULBASAUR"=>11, "CHARMANDER"=>12, "SQUIRTLE"=>13}.each do |starter, version|
      $PokemonGlobal.blue_regions["pilot_starter"] = starter
      $PokemonGlobal.blue_regions["pilot_rival"] = false
      $battle_result = true
      $raise_battle = false
      assert_gary(BlueKantoPilot.rival == true,
                  "Starter #{starter} could not battle Gary")
      assert_gary($attempted_battles.last == [:BLUE_KANTO_RIVAL,"Blue",version],
                  "Rival trainer type/name/version changed")
      assert_gary(GameData::Trainer.exists?(:BLUE_KANTO_RIVAL,"Blue",version),
                  "Version #{version} was not registered from verified PBS")
      assert_gary(GameData::Trainer::DATA[[:BLUE_KANTO_RIVAL,"Blue",version]]
                         .fetch(:pokemon).first.fetch(:level) == 5,
                  "Original level not preserved from PBS")
      assert_gary($PokemonGlobal.blue_regions["pilot_rival"] == true,
                  "Victory did not progress the tutorial")
    end
    assert_gary(File.read("Data/blue-compile-request.txt") == "compile",
                "Missing compiled trainer failed to schedule native compilation")

    # A broken optional music-restoration callback must not block the
    # scripted trainer battle when its data are available.
    $PokemonGlobal.blue_regions["pilot_rival"] = false
    $PokemonGlobal.blue_regions["pilot_starter"] = "BULBASAUR"
    $broken_music = true
    assert_gary(BlueKantoPilot.rival == true,
                "Optional Kanto music error blocked Gary battle")
    assert_gary(File.read("Data/blue-kanto-rival-error.log").include?(
                  "Mock Kanto music restore failed"),
                "Audio exception wasn't recorded")
    $broken_music = false

    # Once compiled, no PBS rewriting or second registration takes place.
    $PokemonGlobal.blue_regions["pilot_rival"] = false
    $PokemonGlobal.blue_regions["pilot_starter"] = "BULBASAUR"
    before = GameData::Trainer::DATA[[:BLUE_KANTO_RIVAL,"Blue",11]]
    assert_gary(BlueKantoPilot.rival, "Compiled trainer couldn't replay")
    assert_gary(GameData::Trainer::DATA[[:BLUE_KANTO_RIVAL,"Blue",11]].equal?(before),
                "Existing compiled trainer overwritten by fallback")

    # A normal loss still blacks out through native Essentials; no false win.
    $PokemonGlobal.blue_regions["pilot_rival"] = false
    $battle_result = false
    assert_gary(BlueKantoPilot.rival == false, "Defeat counted as a win")
    assert_gary($PokemonGlobal.blue_regions["pilot_rival"] == false,
                "Battle loss set rival completion flag")
    $battle_result = true

    # An actual engine exception should be logged and should not become a
    # generic EventScriptError that permanently blocks the save.
    $raise_battle = true
    assert_gary(BlueKantoPilot.rival == false, "Crash returned victory")
    assert_gary(!$PokemonGlobal.blue_regions["pilot_rival"],
                "Crash falsely completed Gary event")
    assert_gary(File.read("Data/blue-kanto-rival-error.log").include?(
                  "Mock battle engine failed during transition"),
                "Real underlying battle exception not logged")
    assert_gary($game_temp.clear_count > 0, "Failed battle rules not reset")
    $raise_battle = false
    assert_gary(BlueKantoPilot.rival == true, "Gary could not retry after error")

    # Missing trainer type must not overwrite a native type or fabricate a
    # battle. Leave tutorial pending and show instructions instead.
    GameData::Trainer::DATA.delete([:BLUE_KANTO_RIVAL,"Blue",13])
    $PokemonGlobal.blue_regions["pilot_starter"] = "SQUIRTLE"
    $PokemonGlobal.blue_regions["pilot_rival"] = false
    $missing_type = true
    count = $attempted_battles.size
    assert_gary(BlueKantoPilot.rival == false, "Missing type started battle")
    assert_gary($attempted_battles.size == count, "Unregistered trainer was used")
    assert_gary($messages.any? { |msg| msg.include?("Blue-Story.exe") },
                "Repair message wasn't displayed")
    assert_gary(!$PokemonGlobal.blue_regions["pilot_rival"],
                "Missing type bypassed mandatory Gary challenge")
  end
end
puts "PASS: Gary 3 native variants, PBS fallback, loss/retry, diagnostics, save safety"
