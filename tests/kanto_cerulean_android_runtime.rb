# Android/JoiPlay regression for source Map042's Luis and Diana callbacks.
# Mocks Essentials APIs only. Never reads a player's saves or starts Game.exe.
require "tmpdir"
require "fileutils"

source = File.expand_path(ARGV.fetch(0))
def check(value, reason)
  raise "KANTO_CERULEAN_ANDROID: #{reason}" unless value
end

class Game_Player
  attr_accessor :x, :y
  attr_reader :moves
  def initialize(x, y); @x, @y, @moves = x, y, []; end
  def turn_generic(*); end
  def move_generic(dir, *); @moves << dir; end
end
class Game_Event
  def initialize(map_id, id); @map_id, @id = map_id, id; end
  def character_name; ""; end
end
def load_data(path)
  raise "Unexpected map lookup: #{path}" unless path == "Data/Map600.rxdata"
  graphic = Struct.new(:character_name).new("FRLG_Pilot_Gary_fixture")
  page = Struct.new(:graphic).new(graphic)
  actor = Struct.new(:pages).new([page])
  Struct.new(:events).new({14=>actor})
end
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
    File.write("Data/blue-kanto-install.json", '{"maps":{"6":600,"39":501,"42":502}}')
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

    # 6b. A save with a generic Blue win and stale lane self-switches
    # must still meet Cerulean Gary. Actual movement entry, not merely
    # direct invocation of the scripted event callback.
    actor = Game_Event.new(501, 32)
    other = Game_Event.new(502, 32)
    [[:BULBASAUR, 31], [:CHARMANDER, 32], [:SQUIRTLE, 33]].each do |species, version|
      state = $PokemonGlobal.blue_regions
      state["pilot_starter"] = species.to_s
      state.delete("pilot_cerulean_rival")
      state["pilot_wins"] = ["Blue"]
      [15, 32, 34].each { |id| $game_self_switches[[501, id, "A"]] = true }
      GameData::Trainer::DATA[[:BLUE_KANTO_RIVAL, "Blue", version]] = true
      check(actor.character_name == "FRLG_Pilot_Gary_fixture", "pending Gary invisible")
      check(other.character_name == "", "Gary leaked outside Cerulean")
      [22, 23, 24].each do |x|
        player = Game_Player.new(x, 7)
        $battle_win = false
        before = $attempts.size
        player.move_generic(8)
        check($attempts.size == before + 1 &&
              $attempts.last == [:BLUE_KANTO_RIVAL, "Blue", version],
              "lane #{x} did not start the correct rival battle")
        check(player.moves.empty?, "player crossed before victory")
        check(!state["pilot_cerulean_rival"], "loss marked rival as defeated")
      end
      player = Game_Player.new(23, 5)
      $battle_win = true
      player.move_generic(2)
      check(state["pilot_wins"].include?("KANTO_CERULEAN_RIVAL"), "exact win missing")
      check(state["pilot_cerulean_rival"], "victory flag missing")
      check(actor.character_name == "", "Gary still visible after victory")
      before = $attempts.size
      player.move_generic(2)
      check(player.moves == [2] && $attempts.size == before, "won scene replayed")
      state.delete("pilot_cerulean_rival")
      check(BlueKantoPilot.cerulean_rival, "exact win did not restore completion")
      check($attempts.size == before, "exact win replayed battle")
    end

    # 7. Nugget is awarded once, even when Rocket defeats the player.
    class << GameData
      def self.note; end
    end
    module_items = Class.new do
      def self.exists?(item); [:NUGGET, :BLUE_KANTO_SSTICKET, :SSTICKET].include?(item); end
    end
    GameData.const_set(:Item, module_items) unless GameData.const_defined?(:Item)
    bag = Object.new
    def bag.has?(item); Array($granted_items).any? { |id,qty| id == item && qty > 0 }; end
    def bag.add(item, quantity)
      return false if $ticket_bag_full && item == :BLUE_KANTO_SSTICKET
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
    check($granted_items.count([:BLUE_KANTO_SSTICKET, 1]) == 1, "Bill ticket duplicated/missing")
    check(BlueKantoPilot.bill_reward, "Bill's post-quest talk failed")
    check($granted_items.count([:BLUE_KANTO_SSTICKET, 1]) == 1, "Bill ticket duplicated on talk")
    state = $PokemonGlobal.blue_regions
    state.delete("pilot_bill_ticket_item_granted")
    $granted_items.delete([:BLUE_KANTO_SSTICKET,1])
    $ticket_bag_full = true
    check(BlueKantoPilot.bill_reward && state["pilot_ss_ticket"] &&
          !state["pilot_bill_ticket_item_granted"], "Full bag revoked old permit")
    $ticket_bag_full = false
    check(BlueKantoPilot.bill_reward && state["pilot_bill_ticket_item_granted"], "Legacy permit upgrade failed")
    check(BlueKantoPilot.bill_reward && $granted_items.count([:BLUE_KANTO_SSTICKET,1]) == 1,
          "Legacy permit duplicated")
    state.delete("pilot_bill_ticket_item_granted")
    $granted_items.delete([:BLUE_KANTO_SSTICKET,1])
    $granted_items << [:SSTICKET,1]
    check(BlueKantoPilot.bill_reward && state["pilot_bill_ticket_item_granted"] &&
          $granted_items.none? { |row| row[0] == :BLUE_KANTO_SSTICKET }, "Legacy real ticket duplicated")
    $granted_items.delete([:SSTICKET,1])
    check(BlueKantoPilot.bill_reward && $granted_items.none? { |row| row[0] == :BLUE_KANTO_SSTICKET },
          "Already materialized ticket granted twice")
  end
end

puts "PASS: Cerulean gym, Gary, Nugget, Bill, save/retry and Android diagnostics"
