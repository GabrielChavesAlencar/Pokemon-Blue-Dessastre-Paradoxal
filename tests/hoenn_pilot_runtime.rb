# Isolated pure Ruby contract tests. No Game.exe, ZIP, donor map or saved game.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
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

class HoennDummyAvatar
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
    def start(*args)
      @history << args
      true
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

def pbAddPokemonSilent(species, level)
  return false unless $give_pokemon
  $player.party << [species, level]
  true
end

def setBattleRule(rule)
  $battles << rule
end

def pbGetTimeNow
  Time.utc(2026, 11, 14, 12, 0)
end

def check(condition, message)
  raise "[HOENN] #{message}" unless condition
end

require ARGV.fetch(0)

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
    check(BlueHoennPilot.mother, "Intro with mother missing")
    check(BlueHoennPilot.route_birch, "Intro guard not triggered")
    check(!BlueHoennPilot.state["birch_rescue_active"], "Clock guard bypassed")
    check($game_player.y == 19, "Player was not kept south of Birch")
    BlueHoennPilot.clock
    check(BlueHoennPilot.mother, "Mother after clock missing")
    check(BlueHoennPilot.route_birch, "Birch encounter not triggered")
    check(BlueHoennPilot.state["birch_rescue_active"], "Rescue flag missing")
    check(!BlueHoennPilot.choose_starter(:TREECKO), "Old lab object must not give starter")
    check(!BlueHoennPilot.choose_birch_ball(:PIKACHU), "Unlisted species accepted")
    $give_pokemon = false
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Failed party add granted starter")
    check(BlueHoennPilot.starter.nil?, "Failed starter persisted")
    $give_pokemon = true
    $confirm_starter = false
    check(!BlueHoennPilot.choose_birch_ball(:TREECKO), "Declining selection granted starter")
    $confirm_starter = true
    check(BlueHoennPilot.choose_birch_ball(:TREECKO), "Starter/rescue not completed")
    check($player.party == [[:TREECKO, 5]], "Wrong starter")
    check(WildBattle.history == [[:ZIGZAGOON, 2]], "Zigzagoon battle missing/repeated")
    check(BlueHoennPilot.state["birch_rescued"], "Rescue not saved")
    check($bag.items[:POKEBALL] == 0, "Five balls awarded too early")
    check(!BlueHoennPilot.choose_birch_ball(:TORCHIC), "Second initial duplicated")
    check(!BlueHoennPilot.birch, "Pokédex available before rival")

    check(BlueHoennPilot.rival_103, "Route 103 rival battle not started")
    check(TrainerBattle.history == [[:RIVAL1, "May", 210]], "Wrong May starter counter")
    check(!BlueHoennPilot.rival_103, "Rival replayed after first battle")
    check($battles == ["canLose", "canLose"], "Tutorial battles cannot lose")
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

    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    previous = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueHoennPilot.rival_103, "Hoenn event ran in Johto")
    check(!BlueHoennPilot.mother, "Hoenn mother ran in Johto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == previous, "Johto save polluted")
  end
end
puts "HOENN_PILOT_STORY_RUNTIME_OK"
