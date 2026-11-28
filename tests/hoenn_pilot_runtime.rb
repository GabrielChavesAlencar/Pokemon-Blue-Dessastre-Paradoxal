# Isolated pure Ruby contract tests. No Game.exe, ZIP, donor map or saved game.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end

# The native setters clamp offsets on a map with SnapEdges.
class Game_Map
  attr_accessor :map_id
  attr_reader :display_x, :display_y

  def initialize(id)
    @map_id = id
  end

  def events; {}; end

  def display_x=(value)
    @display_x = value.clamp(0, 640)
  end

  def display_y=(value)
    @display_y = value.clamp(0, 640)
  end
end

class Pokemon
  attr_reader :species, :level
  def initialize(species, level)
    @species, @level = species, level
  end
end

class HoennDummyPlayer
  attr_accessor :has_pokedex, :has_running_shoes, :gender
  attr_reader :party, :healed
  def initialize(gender = 0)
    @gender = gender
    @party = []
    @has_pokedex = false
    @has_running_shoes = false
    @healed = 0
  end
  def heal_party
    @healed += 1
  end
  def party_full?
    @party.length >= 6
  end
  def able_pokemon_count
    @party.length
  end
end

class HoennDummyBag
  attr_reader :items
  attr_accessor :can_add
  def initialize
    @items = Hash.new(0)
    @can_add = true
  end
  def add(item, count)
    return false unless @can_add
    @items[item] += count
    true
  end
end

class PokemonMapFactory
  def isPassableFromEdge?(_x, _y)
    true
  end
end

class HoennDummyAvatar
  attr_accessor :transparent
  def refresh_charset; end
  attr_reader :x, :y
  def initialize
    @x, @y = 10, 18
  end
  def moveto(x, y)
    @x, @y = x, y
  end
end

module GameData
  module Species
    def self.get(symbol)
      Struct.new(:name).new(symbol.to_s.capitalize)
    end
  end
end

module BlueRegionStart
  def self.select_and_prepare
    false
  end
end

module EventHandlers
  def self.add(*_args)
    true
  end
end

module TrainerBattle
  @history = []
  class << self
    attr_reader :history
    attr_accessor :result
    def start(*args)
      @history << args
      @result != false
    end
  end
end

module WildBattle
  @history = []
  class << self
    attr_reader :history
    attr_accessor :result
    def start(*args)
      @history << args
      @result
    end
  end
end

$messages = []
$battles = []
$give_pokemon = true
$confirm_starter = true

def _INTL(template, *args)
  args.each_with_index { |value, i| template = template.gsub("{#{i + 1}}", value.to_s) }
  template
end

def pbMessage(message, *_args)
  $messages << message
end

def pbConfirmMessage(message)
  $messages << message
  $confirm_starter
end

def pbAddToPartySilent(pokemon)
  return false if !$give_pokemon || $player.party_full?
  $player.party << pokemon unless $pretend_gift
  true
end

def setBattleRule(*rules)
  $battles.concat(rules)
end

def pbCharacterSelect
  $profile_choices += 1
  $player.gender = $selected_profile
end

def pbGetTimeNow
  Time.utc(2026, 11, 14, 12, 0)
end

$center_registered = 0
def pbMEPlay(name)
  $healing_jingle = name
end

def pbSetPokemonCenter
  $center_registered += 1
end

def check(condition, message)
  raise "[HOENN] #{message}" unless condition
end

require File.expand_path(ARGV.fetch(0))

Dir.mktmpdir("blue-hoenn-runtime-") do |dir|
  Dir.chdir(dir) do
    $PokemonGlobal = PokemonGlobalMetadata.new
    $PokemonGlobal.blue_regions = { "current" => "DECADES" }
    $player = HoennDummyPlayer.new
    $bag = HoennDummyBag.new
    $game_player = HoennDummyAvatar.new

    old = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueHoennPilot.mother, "Mother ran outside Hoenn")
    check(!BlueHoennPilot.route_birch, "Rescue ran outside Hoenn")
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Starter granted outside Hoenn")
    check(!BlueHoennPilot.rival_103, "Rival ran outside Hoenn")
    check(Marshal.dump($PokemonGlobal.blue_regions) == old, "Other regional save modified")

    $PokemonGlobal.blue_regions["current"] = "HOENN"
    BlueHoennPilot.define_singleton_method(:metadata) { [[701,25,6],{7=>700,8=>701,101=>703}] }
    $game_map = Game_Map.new(700)
    route = Game_Map.new(703)
    $game_map.display_x = -128
    $game_map.display_y = 3008
    route.display_x = -128
    route.display_y = 3008
    check([$game_map.display_x, $game_map.display_y] == [0, 640], "Town camera must snap")
    check([route.display_x, route.display_y] == [-128, 3008], "Neighbor offset snapped into town")
    town = $game_map
    $game_map = route
    route.display_y = 3008
    town.display_y = -1920
    check(route.display_y == 640, "Route camera must snap after entering it")
    check(town.display_y == -1920, "Town snapped into the route after crossing the border")
    $game_map = Game_Map.new(1)
    route.display_y = 3008
    check(route.display_y == 640, "Unrelated map must retain the native offset behavior")

    $game_map = Game_Map.new(701)
    check(!BlueHoennPilot.home_exit_allowed?, "Player can leave without clock or mother")
    check(BlueHoennPilot.mother, "Intro with mother missing")
    check(!BlueHoennPilot.home_exit_allowed?, "Mother alone opens the home door")
    $game_player.moveto(11,11)
    check(BlueHoennPilot.home_exit_blocked(11), "No directions at inside threshold")
    check([$game_player.x,$game_player.y] == [11,10], "Blocked exit displaced player")
    BlueHoennPilot.clock
    check(BlueHoennPilot.mother, "Mother after clock missing")
    check(BlueHoennPilot.home_exit_allowed?, "Completed home introduction blocks exit")
    $game_map.map_id=703
    check(!BlueHoennPilot.home_exit_allowed?, "House gate reachable outdoors")
    BlueHoennPilot.state.delete("clock_set") # old save that was already outside
    $game_player.moveto(10,18)
    check(BlueHoennPilot.route_birch, "Birch encounter not triggered")
    check([$game_player.x,$game_player.y] == [10,18], "Route pushed a saved player backward")
    check(BlueHoennPilot.state["birch_rescue_active"], "Rescue flag missing")
    check(!BlueHoennPilot.choose_starter(:TREECKO), "Old lab object must not give starter")
    check(!BlueHoennPilot.choose_birch_ball(:PIKACHU), "Unlisted species accepted")
    $game_map.map_id = 701
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Bag outside Route 101 awarded a starter")
    $game_map.map_id = 703
    occupied_party = Array.new(6) { Pokemon.new(:POOCHYENA, 5) }
    $player.party.replace(occupied_party)
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Full party got a misplaced starter")
    check(BlueHoennPilot.starter.nil? && $player.party == occupied_party, "Full party changed save")
    $player.party.clear
    $give_pokemon = false
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Failed party add granted starter")
    check(BlueHoennPilot.starter.nil?, "Failed starter persisted")
    $give_pokemon = true
    $confirm_starter = false
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Declining selection granted starter")
    $confirm_starter = true
    $pretend_gift = true
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO) && BlueHoennPilot.starter.nil?,
          "Engine response alone persisted a gift without inserting it in the party")
    $pretend_gift = false
    WildBattle.result = false
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Defeat completed the rescue")
    check(!BlueHoennPilot.state["birch_rescued"] && !BlueHoennPilot.state["met_birch"] &&
          BlueHoennPilot.state["birch_rescue_active"], "Loss closed the rescue retry")
    check($player.party.map { |pkmn| [pkmn.species, pkmn.level] } == [[:TREECKO, 5]], "Wrong starter")
    check(!BlueHoennPilot.rival_103 && !BlueHoennPilot.birch, "Defeat unlocked later opening events")
    saved_rescue = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = Marshal.load(saved_rescue)
    WildBattle.result = true
    check(BlueHoennPilot.route_birch, "The actual route entrance did not retry after reload")
    check(BlueHoennPilot.starter == :TREECKO && $player.party.length == 1,
          "Retry changed the claimed starter or added another")
    check(!BlueHoennPilot.route_birch, "Rescue repeated after victory")
    BlueHoennPilot.heal
    check($center_registered == 1, "Oldale did not register respawn point")
    check($healing_jingle == "Pkmn healing", "Center did not play the recovery fanfare")
    check(WildBattle.history == [[:ZIGZAGOON, 2], [:ZIGZAGOON, 2]],
          "Zigzagoon battle did not start once per attempt")
    check(BlueHoennPilot.state["birch_rescued"], "Rescue not saved")
    check($bag.items[:POKEBALL] == 0, "Five balls awarded too early")
    check(!BlueHoennPilot.choose_birch_ball(:TORCHIC), "Second initial duplicated")
    check(!BlueHoennPilot.birch, "Pokédex available before rival")

    check(BlueHoennPilot.rival_103, "Route 103 rival battle not started")
    check(TrainerBattle.history == [[:RIVAL1, "May", 210]], "Wrong May starter counter")
    check(!BlueHoennPilot.rival_103, "Rival replayed after first battle")
    check($battles == ["canLose", "cannotRun", "disablePokeballs",
                       "canLose", "cannotRun", "disablePokeballs", "canLose"],
          "Rescue or rival battle rules changed")
    $bag.can_add = false
    check(!BlueHoennPilot.birch, "Full bag did not postpone reward")
    check(!$player.has_pokedex, "Full bag granted Pokédex")
    $bag.can_add = true
    check(BlueHoennPilot.birch, "Pokédex reward not granted")
    check($player.has_pokedex, "Pokédex not activated")
    check($bag.items[:POKEBALL] == 5, "Lab must grant five balls once")
    check(BlueHoennPilot.mother, "Running Shoes handoff missing")
    check($player.has_running_shoes, "Running Shoes not enabled")
    check(!BlueHoennPilot.mother.nil?, "Mother conversation failed")
    check(!BlueHoennPilot.birch, "Second Pokédex reward happened")
    check($bag.items[:POKEBALL] == 5, "Duplicate balls after revisit")

    saved = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = Marshal.load(saved)
    check(!BlueHoennPilot.rival_103, "Rival repeated after save/reload")
    check(!BlueHoennPilot.choose_birch_ball(:MUDKIP), "Starter duplicated after reload")
    check($bag.items[:POKEBALL] == 5, "Reload changed bag reward")

    # Loss is a completed tutorial encounter; the next story event must open.
    $PokemonGlobal.blue_regions["hoenn_pilot"] = {
      "starter" => "MUDKIP", "met_birch" => true
    }
    $player.gender = 1
    TrainerBattle.result = false
    check(BlueHoennPilot.rival_103, "Rival loss did not complete")
    check(TrainerBattle.history.last == [:RIVAL1, "Brendan", 212],
          "Wrong Brendan team counter")
    check(BlueHoennPilot.state["rival_103_done"], "Loss not persisted")

    # Legacy pilot saves got five Poké Balls during starter selection.
    # Missing pending flag must NOT grant them again on migration.
    check(BlueHoennPilot.birch, "Legacy game cannot receive Pokédex")
    check($bag.items[:POKEBALL] == 5, "Migrated legacy reward duplicated")
    check($player.has_pokedex, "Legacy Pokédex lost")

    factory = PokemonMapFactory.new
    BlueHoennPilot::STARTERS.product([0, 1]).each do |species, profile|
      $profile_choices = 0
      $selected_profile = profile
      $player = HoennDummyPlayer.new
      $bag = HoennDummyBag.new
      $game_player = HoennDummyAvatar.new
      $PokemonGlobal.blue_regions = {
        "initial" => "HOENN", "current" => "HOENN", "hoenn_pilot" => {"profile_pending" => true}
      }
      $game_map = Game_Map.new(701)
      BlueHoennPilot.choose_profile
      BlueHoennPilot.choose_profile
      check($profile_choices == 1 && $player.gender == profile && $game_player.transparent == false,
            "Opening profile was repeated or applied incorrectly")
      BlueHoennPilot.clock
      BlueHoennPilot.mother
      check(BlueHoennPilot.home_exit_allowed?, "Clock and mother did not open the exit")
      $game_map.map_id = 703
      check(BlueHoennPilot.route_birch, "Birch event missing for #{species}/#{profile}")
      check(!factory.isPassableFromEdge?(10, -1), "Rescue allowed walking north into Oldale")
      check(factory.isPassableFromEdge?(10, 20), "Rescue blocked walking back toward Littleroot")
      WildBattle.result = false
      check(!BlueHoennPilot.choose_birch_ball(species), "Loss completed the rescue")
      check(!factory.isPassableFromEdge?(10, -1), "Defeat lifted the north exit gate")
      $PokemonGlobal.blue_regions, $player = Marshal.load(Marshal.dump([$PokemonGlobal.blue_regions, $player]))
      WildBattle.result = true
      check(BlueHoennPilot.route_birch, "Rescue did not reopen after loading #{species}/#{profile}")
      check(factory.isPassableFromEdge?(10, -1), "Victory kept Oldale blocked")
      check($player.party.map(&:species) == [species], "Reload changed the starter species or count")
      check(!BlueHoennPilot.choose_birch_ball(species), "Reload allowed a second starter")
    end

    $PokemonGlobal.blue_regions = {"initial" => "DECADES", "current" => "HOENN"}
    $game_map = Game_Map.new(700)
    $profile_choices = 0
    BlueHoennPilot.choose_profile
    check($profile_choices == 0 && factory.isPassableFromEdge?(10, -1),
          "Interregional arrival started the new-game profile or blocked normal movement")

    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    previous = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueHoennPilot.rival_103, "Hoenn event ran in Johto")
    check(!BlueHoennPilot.mother, "Hoenn mother ran in Johto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == previous, "Johto save polluted")
  end
end
puts "HOENN_PILOT_STORY_RUNTIME_OK"
