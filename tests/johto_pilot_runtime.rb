# Pure Ruby harness. No game/ files, no engine, no map source required.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end

class JohtoDummyPlayer
  attr_reader :party, :healed
  def initialize
    @party = []
    @healed = 0
  end
  def heal_party
    @healed += 1
  end
end

module GameData
  module Species
    def self.get(symbol)
      Struct.new(:name).new(symbol.to_s.capitalize)
    end
  end
end

module TrainerBattle
  @history = []
  class << self
    attr_reader :history
    def start(*args)
      @history << args
      true
    end
  end
end

def _INTL(template, *args)
  args.each_with_index { |value, idx| template = template.gsub("{#{idx + 1}}", value.to_s) }
  template
end

$questions = []
$messages = []
$give_pokemon = true
$battles = []
def pbMessage(message, choices = nil, default = nil)
  $messages << message
  choices ? $questions.shift : nil
end
def pbConfirmMessage(message)
  $messages << message
  $confirm_starter != false
end
def pbAddPokemonSilent(species, level)
  return false unless $give_pokemon
  $player.party << [species, level]
  true
end
def setBattleRule(rule)
  $battles << rule
end

def check(condition, description)
  raise description unless condition
end

require ARGV.fetch(0)
Dir.mktmpdir("johto-pilot-test-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data") # Isolated pilot marker folder; never the actual game/Data.
    $PokemonGlobal = PokemonGlobalMetadata.new
    $PokemonGlobal.blue_regions = {"version"=>1, "current"=>"DECADES"}
    $player = JohtoDummyPlayer.new
    previous = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoPilot.mother, "Johto mother should not run in Decades")
    check(!BlueJohtoPilot.elm, "Johto Elm should not run in Decades")
    check(!BlueJohtoPilot.choose_starter, "Johto starter cannot be taken from Decades")
    check(!BlueJohtoPilot.choose_starter_from_ball(:CHIKORITA), "Decades cannot receive Johto starter from ball")
    check(!BlueJohtoPilot.rival, "Johto rival cannot run in Decades")
    check(Marshal.dump($PokemonGlobal.blue_regions) == previous, "Johto polluted Decades")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    check(!BlueJohtoPilot.choose_starter, "Johto starter cannot be taken from Kanto")
    check(!BlueJohtoPilot.choose_starter_from_ball(:TOTODILE), "Kanto cannot receive Johto ball starter")
    check(!$PokemonGlobal.blue_regions.key?("johto_pilot"), "Kanto save got Johto flags")

    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    check(BlueJohtoPilot.mother, "Initial mother conversation missing")
    check(!BlueJohtoPilot.mother, "Mother intro repeated")
    check(!BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL), "Must talk to Elm first")
    check(BlueJohtoPilot.elm, "Elm intro missing")
    check(!BlueJohtoPilot.choose_starter, "Old Elm dialogue must not grant starter")
    check(!BlueJohtoPilot.choose_starter_from_ball(:PIKACHU), "Unlisted ball species granted")
    check($player.party.empty?, "Elm dialogue gave starter without clicking ball")

    $give_pokemon = false
    check(!BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL), "Failed party add was marked successful")
    check(BlueJohtoPilot.starter.nil?, "Failed starter persisted")
    $give_pokemon = true
    $confirm_starter = false
    check(!BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL), "Declining a ball must not grant it")
    $confirm_starter = true
    check(BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL), "Cyndaquil ball did not grant starter")
    check($player.party == [[:CYNDAQUIL, 5]], "Wrong starter or level")
    check(BlueJohtoPilot.starter == :CYNDAQUIL, "Starter not saved")
    check(BlueJohtoPilot.rival_species == :TOTODILE, "Rival must counter Cyndaquil")
    check(BlueJohtoPilot.rival_version == 1, "Wrong rival PBS version")
    check(!BlueJohtoPilot.choose_starter_from_ball(:TOTODILE), "Second ball gave duplicate")
    check(!BlueJohtoPilot.choose_starter, "Elm dialogue gave duplicate")
    check($player.party.size == 1, "Extra starter was duplicated")

    check(!BlueJohtoPilot.rival, "Uninstalled rival PBS should be blocked")
    check(TrainerBattle.history.empty?, "Rival started without approved PBS")
    File.write(BlueJohtoPilot::RIVAL_READY, "BAD MARKER")
    check(!BlueJohtoPilot.rival, "Invalid rival marker allowed")
    File.write(BlueJohtoPilot::RIVAL_READY, "BLUE_JOHTO_RIVAL_V1_READY\n")
    check(BlueJohtoPilot.rival, "Rival battle did not start when vetted marker exists")
    check(TrainerBattle.history == [[:BLUE_JOHTO_RIVAL, "Rival", 1]],
          "Trainer selection or version mismatched")
    check($battles == ["canLose"], "Rival did not use canLose")
    check($player.healed == 1, "Player was not healed after tutorial battle")
    check(BlueJohtoPilot.rival_fought?, "Rival battle flag missing")
    check(!BlueJohtoPilot.rival, "Rival battle repeated on same save")
    check(TrainerBattle.history.size == 1, "Rival battle duplicated")

    saved = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = Marshal.load(saved)
    check(BlueJohtoPilot.starter == :CYNDAQUIL, "Save/reload lost starter")
    check(BlueJohtoPilot.rival_fought?, "Save/reload lost rival progress")
    check(!BlueJohtoPilot.choose_starter_from_ball(:CHIKORITA), "Reload re-awarded starter")
    $PokemonGlobal.blue_regions["current"] = "DECADES"
    check(!BlueJohtoPilot.rival, "Old region got Johto event after travel")
  end
end

puts "JOHTO_PILOT_STORY_GUARDS_OK"
