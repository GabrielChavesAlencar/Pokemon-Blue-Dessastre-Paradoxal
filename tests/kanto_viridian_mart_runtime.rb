# Standalone Ruby regression on the real KantoPilot.rb, without Game.exe,
# copyrighted FRLG assets or the player's saved game.
require "tmpdir"

source = File.expand_path(ARGV.fetch(0))
class Game_Player; end
module MenuHandlers
  def self.add(*_args); end
end
module BlueRegions
  def self.new_state(region)
    {"version"=>1, "current"=>region, "achievements"=>{}}
  end
  def self.local_achievements(state, region)
    state.fetch("achievements", {}).fetch(region, [])
  end
end
module BlueMusic
  def self.kanto_me_play(_name); end
  def self.with_kanto_scene(_name)
    yield
  end
end
module BlueLocale
  def self.enabled?; @locale == "pt-BR"; end
  def self.locale=(value); @locale = value; end
  def self.with_raw; yield; end
end
module GameData
  class MapMetadata
    def initialize(id); @id = id; end
    def name; @id == 421 ? "Cidade" : "Cidade vizinha"; end
    def real_name; "Viridian City"; end
  end
end
class MockBag
  attr_reader :items
  def initialize; @items = []; end
  def add(item, qty = 1); @items << [item, qty]; true; end
end
class MockPlayer
  attr_accessor :has_pokedex
end
def _INTL(value, *args)
  value.gsub(/\{(\d+)\}/) { args[$1.to_i - 1].to_s }
end
$dialogue = []
$mart = []
def pbMessage(message, *_args); $dialogue << message; end
def pbPokemonMart(stock); $mart << stock.dup; true; end
def assert(condition, message); raise "VIRIDIAN_REGRESSION: #{message}" unless condition; end

Dir.mktmpdir("kanto-viridian-mart-") do |dir|
  Dir.chdir(dir) do
    File.write("Kanto pilot.json", '{"maps":{"10":421}}')
    load source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    $player = MockPlayer.new
    $bag = MockBag.new

    # A new save without a chosen starter cannot buy in Viridian.
    assert(BlueKantoPilot.viridian_mart == false, "shopping before receiving starter")
    assert($mart.empty?, "Viridian shop opened before starting parcel quest")

    # Shopkeeper may hand out the parcel, but this does not enable shopping.
    BlueKantoPilot.progress["pilot_starter"] = "BULBASAUR"
    assert(BlueKantoPilot.viridian_mart == false, "parcel interaction opened shop")
    assert(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true, "parcel not issued")
    assert(!BlueKantoPilot.progress["pilot_oak_parcel_delivered"], "parcel spontaneously delivered")
    assert($mart.empty?, "shop opened at initial parcel pickup")
    # A repeat visit and a restored save must both remain blocked.
    assert(BlueKantoPilot.viridian_mart == false, "repeat shop visit incorrectly permitted")
    assert($dialogue.any? { |s| s.include?("Professor Oak") }, "no delivery warning")
    assert($mart.empty?, "shop opened before the parcel was delivered")

    # Returning to Oak records the actual delivery and grants the five balls.
    BlueKantoPilot.choose_starter
    assert(BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
           "Oak did not record the delivery")
    assert($bag.items.include?([:POKEBALL, 5]), "Oak delivery reward missing")
    assert($player.has_pokedex == true, "Oak did not unlock the Pokedex")
    assert(BlueKantoPilot.viridian_mart, "shop stayed closed after Oak delivery")
    assert($mart == [BlueKantoPilot::VIRIDIAN_MART_STOCK],
           "wrong stock after delivery")
    assert(BlueKantoPilot.viridian_mart, "shop cannot reopen later")
    assert($mart.length == 2, "shop unexpectedly duplicated on unlock")

    # A badge from an old pilot save must not bypass the actual parcel flag.
    BlueKantoPilot.progress["pilot_oak_parcel_delivered"] = false
    BlueKantoPilot.progress["achievements"]["KANTO"] = ["BOULDER"]
    assert(BlueKantoPilot.viridian_mart == false, "old badge bypassed parcel delivery")
    assert($mart.length == 2, "badge opened the shop before delivering")
    # A legacy Boulder+ save without parcel flags must be able to obtain it,
    # then return to Oak, instead of being permanently excluded from shopping.
    BlueKantoPilot.progress["pilot_oak_parcel_received"] = false
    assert(BlueKantoPilot.parcel_pickup_pending?,
           "legacy Boulder save cannot recover the parcel")
    assert(BlueKantoPilot.viridian_mart == false,
           "legacy recovery opened the store before Oak")
    assert(BlueKantoPilot.progress["pilot_oak_parcel_received"] == true,
           "legacy save cannot collect the parcel")
    assert($mart.length == 2, "legacy recovery bypassed shop lock")
    BlueKantoPilot.choose_starter
    assert(BlueKantoPilot.progress["pilot_oak_parcel_delivered"] == true,
           "Oak refused legacy parcel delivery")
    assert(BlueKantoPilot.viridian_mart, "legacy save remained locked after delivery")
    assert($mart.length == 3, "legacy save did not unlock the shop")

    # Map identity is stable and proper names respect the selected locale.
    metadata = GameData::MapMetadata.new(421)
    other = GameData::MapMetadata.new(422)
    assert(BlueKantoPilot.viridian_map_id == 421, "Viridian source map ID changed")
    BlueLocale.locale = "pt-BR"
    assert(metadata.name == "Cidade de Viridian", "PT-BR Viridian map banner is truncated")
    assert(other.name == "Cidade vizinha", "unrelated map name was modified")
    BlueLocale.locale = "en"
    assert(metadata.name == "Viridian City", "English Viridian map banner changed")
    assert(metadata.real_name == "Viridian City", "compiled map's real name was modified")

    # In a non-pilot Decades launch, the hook is inert.
    File.delete("Kanto pilot.json")
    BlueLocale.locale = "pt-BR"
    assert(metadata.name == "Cidade", "native non-pilot map name was overridden")
  end
end

puts "PASS: Viridian Mart locked until actual Oak parcel delivery; PT-BR/EN city name; other maps and Decades intact"
