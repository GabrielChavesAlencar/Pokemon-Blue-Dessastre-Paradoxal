# Native Day Care API fixture. No Game.exe, assets or personal saves.
class DayCare
  Slot = Struct.new(:pokemon, :level_gain, :cost) do
    def filled?; !pokemon.nil?; end
  end
  attr_reader :slots
  attr_accessor :gain_exp, :share_egg_moves, :egg_generated

  def initialize
    @slots = Array.new(2) { Slot.new(nil, 0, 100) }
    @egg_generated = false
  end

  def count; slots.count(&:filled?); end
  def get_compatibility; count == 2 ? 2 : 0; end

  def self.deposit(index)
    care = $PokemonGlobal.day_care
    slot = care.slots.find { |entry| !entry.filled? }
    slot.pokemon = $player.party.delete_at(index)
    care.egg_generated = false
  end

  def self.withdraw(index)
    care = $PokemonGlobal.day_care
    slot = care.slots.fetch(index)
    $player.party << slot.pokemon
    slot.pokemon = nil
    care.egg_generated = false
  end

  def self.collect_egg
    care = $PokemonGlobal.day_care
    $player.party << PokemonFixture.new("egg", 1, true, false, false)
    care.egg_generated = false
  end
end

class PokemonGlobalMetadata
  attr_accessor :blue_regions
  def day_care; @main_day_care ||= DayCare.new; end
end

module KantoDayCareFixture
  def day_care
    return super unless blue_regions["current"] == "KANTO"
    @kanto_day_care ||= DayCare.new
  end
end
PokemonGlobalMetadata.prepend(KantoDayCareFixture)

PokemonFixture = Struct.new(:name, :level, :egg, :cannot_store, :fainted) do
  def egg?; egg; end
  def fainted?; fainted; end
end
PlayerFixture = Struct.new(:party, :money) do
  def party_full?; party.size >= 6; end
end
MapFixture = Struct.new(:map_id)

module BlueRegionStart; end
module EventHandlers
  def self.add(*); end
end

def _INTL(message, *values)
  values.each_with_index { |value, index| message = message.gsub("{#{index+1}}", value.to_s) }
  message
end

def pbMessage(message, commands=nil, _cancel=nil)
  $messages << message
  commands ? $choices.shift : nil
end

def pbConfirmMessage(_message); $confirm; end

def verify(ok, message)
  raise message unless ok
end

require File.expand_path(ARGV.fetch(0))
def BlueHoennPilot.metadata; [nil, {133 => 850}]; end

$PokemonGlobal = PokemonGlobalMetadata.new
$PokemonGlobal.blue_regions = {"current" => "DECADES"}
main = $PokemonGlobal.day_care
main.slots.first.pokemon = PokemonFixture.new("Decades", 8, false, false, false)
$PokemonGlobal.blue_regions["current"] = "KANTO"
kanto = $PokemonGlobal.day_care
kanto.slots.first.pokemon = PokemonFixture.new("Kanto", 9, false, false, false)

first = PokemonFixture.new("Primeiro", 4, false, false, false)
second = PokemonFixture.new("Segundo", 7, false, false, false)
third = PokemonFixture.new("Terceiro", 11, false, false, false)
egg = PokemonFixture.new("ovo existente", 1, true, false, false)
blocked = PokemonFixture.new("bloqueado", 1, false, true, false)
fainted = PokemonFixture.new("desmaiado", 1, false, false, true)
$player = PlayerFixture.new([first, second, third, egg, blocked, fainted], 300)
$game_map = MapFixture.new(850)
$messages = []
$choices = []
$confirm = true

verify(!BlueHoennPilot.daycare_info && !BlueHoennPilot.daycare_deposit(0), "Opened Hoenn daycare in Kanto")
verify(kanto.count == 1 && main.count == 1, "Foreign daycare changed")
$PokemonGlobal.blue_regions["current"] = "HOENN"
hoenn = $PokemonGlobal.day_care
verify(hoenn.count == 0 && hoenn.gain_exp && !hoenn.share_egg_moves, "Hoenn did not get separate native storage")
$game_map.map_id = 849
verify(!BlueHoennPilot.daycare_info, "Opened daycare outside the daycare interior")
$game_map.map_id = 850

verify(!BlueHoennPilot.daycare_deposit(3), "Deposited an egg")
verify(!BlueHoennPilot.daycare_deposit(4), "Deposited a prohibited Pokémon")
$choices = [0, 0]
verify(BlueHoennPilot.daycare_info, "NPC deposit did not reach native method")
$choices = [0, 0]
verify(BlueHoennPilot.daycare_info, "NPC did not accept a second Pokémon")
verify(hoenn.count == 2 && $player.party.first == third, "Two intended Pokémon were not deposited")
verify(!BlueHoennPilot.daycare_deposit(0), "Exceeded native slots")
$choices = [2]
verify(BlueHoennPilot.daycare_info && $messages.last == "Os dois Pokémon se dão bem.", "Compatibility not reported")

hoenn.egg_generated = true
$player.party = [third, egg, blocked, fainted, first.clone, second.clone]
verify(!BlueHoennPilot.daycare_collect_egg && hoenn.egg_generated, "Full party consumed an egg")
verify(!BlueHoennPilot.daycare_withdraw(0) && hoenn.egg_generated, "Withdrawal discarded a pending egg")
$player.party = [third, fainted, egg]
$choices = [3]
verify(BlueHoennPilot.daycare_info, "NPC did not deliver a pending egg")
verify($player.party.count(&:egg?) == 2 && !hoenn.egg_generated, "Egg was not consumed exactly once")
verify(!BlueHoennPilot.daycare_collect_egg, "Duplicate egg")

hoenn.slots.first.cost = 350
verify(!BlueHoennPilot.daycare_withdraw(0) && $player.money == 300, "Withdrawal bypassed fee")
hoenn.slots.first.level_gain = 2
hoenn.slots.first.cost = 300
$choices = [1, 0]
$confirm = false
verify(!BlueHoennPilot.daycare_info && hoenn.count == 2 && $player.money == 300, "Cancellation changed the save")
$choices = [1, 0]
$confirm = true
verify(BlueHoennPilot.daycare_info && hoenn.count == 1 && $player.money == 0, "Native withdrawal or exact fee failed")
verify(!BlueHoennPilot.daycare_withdraw(0) && $player.money == 0, "Empty slot charged again")

$player.party = [third, egg, fainted]
verify(!BlueHoennPilot.daycare_deposit(0), "The last able Pokémon was deposited")
$PokemonGlobal = Marshal.load(Marshal.dump($PokemonGlobal))
verify($PokemonGlobal.day_care.slots.last.pokemon.name == "Segundo", "Hoenn daycare did not survive reload")
$PokemonGlobal.blue_regions["current"] = "KANTO"
verify($PokemonGlobal.day_care.slots.first.pokemon.name == "Kanto", "Kanto daycare was changed on reload")
$PokemonGlobal.blue_regions["current"] = "DECADES"
verify($PokemonGlobal.day_care.slots.first.pokemon.name == "Decades", "Decades daycare was changed on reload")
puts "HOENN H08 DAYCARE FIXTURE PASS"
