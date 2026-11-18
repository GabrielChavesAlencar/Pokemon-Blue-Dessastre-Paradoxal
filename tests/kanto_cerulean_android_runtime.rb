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

    # 6. Source Map039: three encounter lanes, one unique Gary battle key.
    GameData::Trainer::DATA[[:BLUE_KANTO_RIVAL, "Blue", 33]] = true
    [15, 32, 34].each { |event_id| $game_map.events[event_id] = Object.new }
    $battle_win = false
    check(!BlueKantoPilot.cerulean_rival, "Gary loss counted as victory")
    check(!$PokemonGlobal.blue_regions["pilot_cerulean_rival"], "Gary loss marked")
    $battle_win = true
    check(BlueKantoPilot.cerulean_rival, "Gary battle did not finish")
    check($PokemonGlobal.blue_regions["pilot_cerulean_rival"], "Gary flag missing")
    [15, 32, 34].each do |event_id|
      check($game_self_switches[[501, event_id, "A"]],
            "Gary did not clear all three entrance lanes")
    end
    before = $attempts.size
    check(BlueKantoPilot.cerulean_rival, "Gary's previously won scene failed")
    check($attempts.size == before, "Gary re-challenged a completed scene")

    # 7. Nugget is awarded once, even when Rocket defeats the player.
    class << GameData
      def self.note; end
    end
    module_items = Class.new do
      def self.exists?(item); [:NUGGET, :SSTICKET].include?(item); end
    end
    GameData.const_set(:Item, module_items) unless GameData.const_defined?(:Item)
    bag = Object.new
    def bag.add(item, quantity)
      $granted_items ||= []
      $granted_items << [item, quantity]
      true
    end
    $bag = bag
    GameData::Trainer::DATA[[:BLUE_KANTO_ROCKET, "Grunt", 5]] = true
    (1..5).each { |i| $PokemonGlobal.blue_regions["pilot_wins"] << "KANTO_053_%03d" % i }
    $game_map.events[6] = Object.new
    $battle_win = false
    check(!BlueKantoPilot.nugget_bridge_rocket, "Rocket loss counted as win")
    check($granted_items.count([:NUGGET, 1]) == 1, "Nugget not awarded exactly once")
    $battle_win = true
    check(BlueKantoPilot.nugget_bridge_rocket, "Rocket win did not finish")
    check($granted_items.count([:NUGGET, 1]) == 1, "Nugget duplicated on rematch")

    # 8. Bill's PC remains locked before asking Bill; S.S. Ticket is one-time.
    [3, 4, 5].each { |event_id| $game_map.events[event_id] = Object.new }
    check(!BlueKantoPilot.bill_computer, "Bill PC used before request")
    BlueKantoPilot.bill_request
    check(BlueKantoPilot.bill_computer, "Bill not restored via PC")
    check($PokemonGlobal.blue_regions["pilot_bill_helped"], "Bill quest flag missing")
    check(BlueKantoPilot.bill_reward, "Bill did not grant S.S. Ticket")
    check($granted_items.count([:SSTICKET, 1]) == 1, "Bill ticket duplicated/missing")
    check(BlueKantoPilot.bill_reward, "Bill's post-quest talk failed")
    check($granted_items.count([:SSTICKET, 1]) == 1, "Bill ticket duplicated on talk")
  end
end

puts "PASS: Cerulean gym, Gary, Nugget, Bill, save/retry and Android diagnostics"
