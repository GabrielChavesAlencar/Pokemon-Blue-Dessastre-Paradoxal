# Pure Ruby: 3 starter choices, Silver versions, save/reload and region guards.
# Not a Game.exe test; does not read or modify game/.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
class JohtoDummyPlayer
  attr_reader :party, :healed
  def initialize
    @party, @healed = [], 0
  end
  def heal_party
    @healed += 1
  end
end
module GameData
  module Species
    def self.get(species)
      Struct.new(:name).new(species.to_s.capitalize)
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
    def clear
      @history.clear
    end
  end
end
$messages, $battles = [], []
def _INTL(s, *args)
  args.each_with_index { |a, i| s = s.gsub("{#{i+1}}", a.to_s) }
  s
end
def pbMessage(message, *args)
  $messages << message
  nil
end
def pbConfirmMessage(message)
  $messages << message
  true
end
def pbAddPokemonSilent(species, level)
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
Dir.mktmpdir("johto-rival-three-versions-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    [
      [:CHIKORITA, :CYNDAQUIL, 0],
      [:CYNDAQUIL, :TOTODILE, 1],
      [:TOTODILE, :CHIKORITA, 2],
    ].each do |chosen, rival_species, version|
      TrainerBattle.clear
      $battles, $messages = [], []
      $player = JohtoDummyPlayer.new
      $PokemonGlobal = PokemonGlobalMetadata.new
      $PokemonGlobal.blue_regions = {"version"=>1, "current"=>"JOHTO"}
      File.delete(BlueJohtoPilot::RIVAL_READY) if File.exist?(BlueJohtoPilot::RIVAL_READY)
      check(!BlueJohtoPilot.choose_starter_from_ball(chosen), "Must talk to Elm")
      check(BlueJohtoPilot.elm, "Elm intro missing")
      check(BlueJohtoPilot.choose_starter_from_ball(chosen), "Starter ball failed")
      check($player.party == [[chosen, 5]], "Wrong starter or level")
      check(BlueJohtoPilot.rival_species == rival_species, "Wrong rival species")
      check(BlueJohtoPilot.rival_version == version, "Wrong PBS version")
      check(!BlueJohtoPilot.choose_starter_from_ball(chosen), "Duplicate starter")
      check(!BlueJohtoPilot.rival, "Uncompiled PBS must block battle")
      check(TrainerBattle.history.empty?, "Battle occurred without ready marker")
      File.write(BlueJohtoPilot::RIVAL_READY, "BAD MARKER")
      check(!BlueJohtoPilot.rival, "Invalid marker enabled battle")
      File.write(BlueJohtoPilot::RIVAL_READY, "BLUE_JOHTO_RIVAL_V1_READY\n")
      check(BlueJohtoPilot.rival, "Valid mock marker did not call trainer")
      check(TrainerBattle.history == [[:BLUE_JOHTO_RIVAL, "Rival", version]],
            "Wrong trainer type/name/version")
      check($battles == ["canLose"], "Missing canLose battle rule")
      check($player.healed == 1, "Party not healed")
      check(!BlueJohtoPilot.rival, "Duplicate rival battle")
      snapshot = Marshal.dump($PokemonGlobal.blue_regions)
      $PokemonGlobal.blue_regions = Marshal.load(snapshot)
      check(BlueJohtoPilot.rival_fought?, "Rival fought flag lost on reload")
      check(!BlueJohtoPilot.choose_starter_from_ball(chosen), "Reload duplicated starter")
      $PokemonGlobal.blue_regions["current"] = "KANTO"
      check(!BlueJohtoPilot.rival, "Kanto executed Johto event")
      check(!BlueJohtoPilot.choose_starter_from_ball(chosen), "Kanto got Johto starter")
      check(TrainerBattle.history.length == 1, "Duplicate battle after travel")
    end
  end
end
puts "JOHTO_RIVAL_THREE_VERSIONS_GUARDS_OK"
