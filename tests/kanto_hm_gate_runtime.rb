# Kanto-only HM progression, using the real Regions.rb and RegionalPolicy.rb.
# Pure Ruby: no ROM, Game.exe, original saves, or copyrighted source assets.
require "json"
require "tmpdir"

module BlueRegionData
  REGISTRY = JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))
  DECADES_VERIFIED = false
end
class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueCampaign
  def self.active?; true; end
end
module BlueBattleOptions
  def self.battle_area?; false; end
end
module BlueRegionTravel
  def self.installed?; false; end # The Kanto standalone pilot has no main-game install marker.
end
module GameData
  module Item
    def self.exists?(key); key.to_s.match?(/\AHM0[1-8]\z/); end
  end
end
class Bag
  def initialize; @items = []; end
  def add(key); @items << key; end
  def clear; @items.clear; end
  def has?(key); @items.include?(key); end
end
class TestPokemon
  attr_accessor :egg, :fainted
  def initialize(*learnable)
    @learnable = learnable
    @egg = false
    @fainted = false
  end
  def compatible_with_move?(move); @learnable.include?(move); end
  def hasMove?(_move); false; end # Four other moves fill the actual move slots.
  def egg?; @egg; end
  def fainted?; @fainted; end
end
class Trainer
  attr_accessor :party
  def initialize(party); @party = party; end
  def get_pokemon_with_move(move)
    @party.find { |pkmn| pkmn.hasMove?(move) }
  end
end
module HiddenMoveHandlers
  def self.triggerCanUseMove(*_args); true; end
  def self.triggerUseMove(*_args); true; end
end
class PokemonStorage; end
module Battle
  module CatchAndStoreMixin; end
end
module EventHandlers
  def self.add(*_args); end
end
def _INTL(pattern, *values)
  pattern.gsub(/\{(\d+)\}/) { values.fetch($1.to_i - 1).to_s }
end
$messages = []
def pbMessage(value); $messages << value; end
def pbCheckHiddenMoveBadge(*_args); false; end
$used_pokemon = nil
$surf_started = false
$boulder_pushed = false
def pbSurf
  $used_pokemon = $player.get_pokemon_with_move(:SURF)
  return false unless pbCheckHiddenMoveBadge(5, false) && $used_pokemon
  pbStartSurfing
end
def pbStartSurfing
  $surf_started = true
  true
end
def pbCut
  $player.get_pokemon_with_move(:CUT) && pbCheckHiddenMoveBadge(2, false)
end
def pbPushThisBoulder
  $boulder_pushed = true
  true
end
def check(condition, label)
  raise "HM_GATE_FAILURE: #{label}" unless condition
end

load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
BlueRegionalPolicy.install
Dir.mktmpdir("kanto-hm-") do |folder|
  Dir.chdir(folder) do
    File.write("Kanto pilot.json", "{}")
    $PokemonGlobal = PokemonGlobalMetadata.new
    $PokemonGlobal.blue_regions = BlueRegions.new_state("KANTO")
    $bag = Bag.new
    bulbasaur = TestPokemon.new(:CUT)
    pidgey = TestPokemon.new(:FLY)
    squirtle = TestPokemon.new(:SURF)
    machop = TestPokemon.new(:STRENGTH)
    $player = Trainer.new([bulbasaur])

    check(BlueRegionalPolicy.state["current"] == "KANTO",
          "isolated pilot did not activate regional protection")
    check(BlueRegionalPolicy.field_result(:SURF) == :badge, "Surf without Soul Badge")
    check(pbSurf == false && !$surf_started, "Surf entered without Soul Badge")
    check(pbStartSurfing == false && !$surf_started, "direct Surf bypassed the badge")

    BlueRegions.award($PokemonGlobal.blue_regions, "KANTO", "SOUL")
    check(BlueRegionalPolicy.field_result(:SURF) == :hm, "Surf missing HM03")
    $bag.add(:HM03)
    check(BlueRegionalPolicy.field_result(:SURF) == :pokemon,
          "Bulbasaur incorrectly qualified for Surf")
    check(pbSurf == false && !$surf_started, "Surf entered without a compatible Pokemon")
    $player.party << squirtle
    check(BlueRegionalPolicy.field_result(:SURF) == :allowed,
          "Surf not allowed after all 3 prerequisites")
    check(!squirtle.hasMove?(:SURF), "Test Pokemon must have no Surf move slot")
    check(pbSurf && $surf_started && $used_pokemon.equal?(squirtle),
          "native Surf did not pick the compatible, move-slot-free Pokemon")
    check(HiddenMoveHandlers.triggerCanUseMove(:SURF, squirtle, false), "party Surf rejected")

    # Hidden Move menu can't let a different Pokemon use Squirtle's ability.
    check(!HiddenMoveHandlers.triggerCanUseMove(:SURF, bulbasaur, false),
          "incompatible Pokemon activated party Surf")
    check(!HiddenMoveHandlers.triggerUseMove(:SURF, bulbasaur),
          "incompatible Pokemon bypassed the use handler")

    # Direct map events must not bypass the badge + item + species gate.
    check(BlueRegionalPolicy.field_result(:CUT) == :badge, "Cut without Cascade Badge")
    check(!pbCut, "Cut allowed without badge and HM")
    BlueRegions.award($PokemonGlobal.blue_regions, "KANTO", "CASCADE")
    check(BlueRegionalPolicy.field_result(:CUT) == :hm, "Cut missing HM01")
    $bag.add(:HM01)
    check(BlueRegionalPolicy.field_result(:CUT) == :allowed, "Bulbasaur should be able to Cut")
    check(pbCut, "native Cut failed even though species need not know it")
    $player.party = [pidgey]
    check(BlueRegionalPolicy.field_result(:CUT) == :pokemon,
          "Pidgey incorrectly qualified for Cut")
    check(!pbCut, "Cut allowed with incompatible Pokemon")

    # Fly: a Pidgey with 4 unrelated moves is enough, but only with HM02/Thunder Badge.
    check(BlueRegionalPolicy.field_result(:FLY) == :badge, "Fly without Thunder Badge")
    BlueRegions.award($PokemonGlobal.blue_regions, "KANTO", "THUNDER")
    check(BlueRegionalPolicy.field_result(:FLY) == :hm, "Fly missing HM02")
    $bag.add(:HM02)
    check(BlueRegionalPolicy.field_result(:FLY) == :allowed, "Pidgey cannot use earned Fly")
    check(!pidgey.hasMove?(:FLY), "Fly should not require a move slot")
    check(BlueRegionalPolicy.with_field(:FLY) {
      $player.get_pokemon_with_move(:FLY).equal?(pidgey)
    }, "native Fly did not find compatible Pidgey")

    $player.party = [machop]
    check(BlueRegionalPolicy.field_result(:STRENGTH) == :badge, "Strength without Rainbow")
    $boulder_pushed = false
    check(!pbPushThisBoulder && !$boulder_pushed, "boulder pushed without badge")
    BlueRegions.award($PokemonGlobal.blue_regions, "KANTO", "RAINBOW")
    $bag.add(:HM04)
    check(pbPushThisBoulder && $boulder_pushed, "earned Strength cannot push boulder")

    # Additional Kanto field HMs also require the badge, item and compatible species.
    [[:FLASH, "BOULDER", :HM05], [:ROCKSMASH, "MARSH", :HM06],
     [:WATERFALL, "VOLCANO", :HM07]].each do |move, badge, item|
      check(BlueRegionalPolicy.field_result(move) == :badge, "#{move} without badge")
      BlueRegions.award($PokemonGlobal.blue_regions, "KANTO", badge)
      check(BlueRegionalPolicy.field_result(move) == :hm, "#{move} missing HM")
      $bag.add(item)
      check(BlueRegionalPolicy.field_result(move) == :pokemon, "#{move} missing Pokemon")
      pkmn = TestPokemon.new(move)
      $player.party << pkmn
      check(BlueRegionalPolicy.field_result(move) == :allowed, "#{move} all prerequisites")
      $player.party.delete(pkmn)
    end

    # Fainted, Egg, and boxed Pokemon cannot act as an HM user.
    $player.party = [squirtle]
    squirtle.fainted = true
    check(BlueRegionalPolicy.field_result(:SURF) == :pokemon, "fainted Surf user accepted")
    squirtle.fainted = false
    squirtle.egg = true
    check(BlueRegionalPolicy.field_result(:SURF) == :pokemon, "egg Surf user accepted")
    squirtle.egg = false
    check(BlueRegionalPolicy.field_result(:SURF, TestPokemon.new(:SURF)) == :pokemon,
          "Pokemon outside the party activated Surf")

    File.delete("Kanto pilot.json")
    check(BlueRegionalPolicy.field_result(:SURF) == :native,
          "legacy Decades context was locked by the pilot policy")
    check($player.get_pokemon_with_move(:SURF).nil?, "legacy move slot behavior changed")
  end
end
puts "PASS: isolated Kanto 7 HMs need regional badge + owned HM + compatible party Pokemon; no move slot required"
