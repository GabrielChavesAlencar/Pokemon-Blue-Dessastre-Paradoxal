# Android/JoiPlay regression for source Map042's Luis and Diana callbacks.
# Mocks Essentials APIs only. Never reads a player's saves or starts Game.exe.
require "tmpdir"
require "fileutils"

source = File.expand_path(ARGV.fetch(0))
def check(value, reason)
  raise "KANTO_CERULEAN_ANDROID: #{reason}" unless value
end

class Game_Player; end
module MenuHandlers
  def self.add(*); end
end
module BlueRegions
  def self.new_state(region)
    {"version"=>1, "current"=>region, "pilot_wins"=>[]}
  end
end
module BlueLocale
  def self.enabled?; true; end
  def self.with_raw; yield; end
end
def _INTL(value, *args)
  value.gsub(/\{(\d+)\}/) { args[$1.to_i - 1].to_s }
end

$messages = []
$intro_count = 0
$notice_count = 0
$outro_count = 0
def pbMessage(text, *_args); $messages << text; end
def pbTrainerIntro(*)
  $intro_count += 1
  raise "JoiPlay trainer intro failed" if $intro_fail
end
def pbNoticePlayer(event)
  $notice_count += 1
  raise "Missing gym NPC" if event.nil?
end
def pbTrainerEnd; $outro_count += 1; end
def setBattleRule(rule); $rules << rule; end

module GameData
  class Trainer
    DATA = {
      [:BLUE_KANTO_SWIMMER, "Luis", 0] => true,
      [:BLUE_KANTO_PICNICKER, "Diana", 0] => true
    }
    def self.exists?(type, name, version)
      DATA.key?([type, name, version])
    end
  end
end
class FakeMap
  attr_reader :map_id, :events
  attr_accessor :need_refresh
  def initialize
    @map_id = 501
    @events = {11=>Object.new, 16=>Object.new}
    @need_refresh = false
  end
end
class FakeTemp
  attr_reader :clears
  def initialize; @clears = 0; end
  def clear_battle_rules; @clears += 1; end
end
class TrainerBattle
  def self.start(type, name, version)
    $attempts << [type, name, version]
    raise "JoiPlay native trainer engine failed" if $battle_error
    $battle_win
  end
end

Dir.mktmpdir("kanto-cerulean-android-") do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p("Data")
    File.write("Data/blue-kanto-install.json", '{"maps":{"42":501}}')
    load source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    $PokemonGlobal.blue_regions["pilot_starter"] = "SQUIRTLE"
    $game_map = FakeMap.new
    $game_temp = FakeTemp.new
    $game_self_switches = {}
    $rules, $attempts = [], []
    $battle_win, $battle_error, $intro_fail = true, false, false

    # 1. Native error: no badge, victory, self-switch or false success.
    $battle_error = true
    check(!BlueKantoPilot.cerulean_gym_trainer(:BLUE_KANTO_SWIMMER,
          "Luis", "KANTO_042_011", 11), "crash returned success")
    check($PokemonGlobal.blue_regions["pilot_wins"].empty?, "crash granted victory")
    check(!$game_self_switches[[501, 11, "A"]], "crash marked NPC as defeated")
    check(File.read("Data/blue-kanto-trainer-error.log").include?(
          "JoiPlay native trainer engine failed"), "missing underlying error")
    check($game_temp.clears == 1, "failed battle rules were not cleared")
    check($messages.last.include?("A batalha do treinador"), "Android message missing")

    # 2. Trainer PBS omitted from compiled Android package: reject, report.
    $battle_error = false
    before = $attempts.length
    check(!BlueKantoPilot.cerulean_gym_trainer(:BLUE_KANTO_SWIMMER,
          "Inexistente", "KANTO_042_099", 11), "missing trainer was accepted")
    check($attempts.length == before, "missing trainer invoked native battle")
    check(File.read("Data/blue-kanto-trainer-error.log").include?(
          "Compiled Kanto trainer is missing"), "missing PBS was not reported")

    # 3. Legitimate loss must not mark the NPC as defeated.
    $battle_win = false
    check(!BlueKantoPilot.cerulean_gym_trainer(:BLUE_KANTO_PICNICKER,
          "Diana", "KANTO_042_016", 16), "loss returned success")
    check(!$game_self_switches[[501, 16, "A"]], "loss set victory switch")

    # 4. Intro failure is logged without blocking an otherwise valid battle.
    $intro_fail = true
    $battle_win = true
    check(BlueKantoPilot.cerulean_gym_trainer(:BLUE_KANTO_SWIMMER,
          "Luis", "KANTO_042_011", 11), "intro failure prevented retry")
    check($game_self_switches[[501, 11, "A"]], "victory switch missing")
    check($PokemonGlobal.blue_regions["pilot_wins"].include?("KANTO_042_011"),
          "map-local win key missing")
    check(File.read("Data/blue-kanto-trainer-error.log").include?(
          "phase=intro"), "optional intro failure was not logged")

    # 5. Re-entering a won event must not replay its trainer battle.
    $intro_fail = false
    before = $attempts.length
    BlueKantoPilot.cerulean_gym_trainer(:BLUE_KANTO_SWIMMER,
      "Luis", "KANTO_042_011", 11)
    check($attempts.length == before, "victory replayed trainer battle")
    check($outro_count > 0 && $notice_count > 0, "trainer callbacks did not run")
  end
end

puts "PASS: Cerulean 2 trainers, Android diagnostics, loss, retry, victory flags"
