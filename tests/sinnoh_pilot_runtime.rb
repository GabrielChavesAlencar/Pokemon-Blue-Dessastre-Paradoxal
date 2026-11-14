# Pure-Ruby verification for BlueSinnohPilot. No Windows, game/ or donor assets.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end

class FakeSinnohPlayer
  attr_accessor :has_pokedex
  attr_reader :party, :heals
  def initialize
    @has_pokedex = false
    @party = []
    @heals = 0
  end
  def heal_party
    @heals += 1
  end
end

module GameData
  module Species
    def self.get(name)
      Struct.new(:name).new(name.to_s.capitalize)
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

def _INTL(str, *arguments)
  arguments.each_with_index do |arg, index|
    str = str.gsub("{#{index + 1}}", arg.to_s)
  end
  str
end

$messages = []
$rules = []
$can_grant = true
def pbMessage(message)
  $messages << message
end
def pbAddPokemonSilent(species, level)
  return false unless $can_grant
  $player.party << [species, level]
  true
end
def setBattleRule(rule)
  $rules << rule
end
def check(value, label)
  raise label unless value
end

require File.expand_path(ARGV.fetch(0))
Dir.mktmpdir("sinnoh-isolated-runtime-") do |directory|
  Dir.chdir(directory) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    $PokemonGlobal.blue_regions = {"version" => 1, "current" => "DECADES"}
    $player = FakeSinnohPlayer.new
    old_state = Marshal.dump($PokemonGlobal.blue_regions)

    check(!BlueSinnohPilot.mother, "Decades mother handler ran")
    check(!BlueSinnohPilot.barry_intro, "Decades Barry handler ran")
    check(!BlueSinnohPilot.rowan_briefcase, "Decades Rowan handler ran")
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG), "Starter granted in Decades")
    check(!BlueSinnohPilot.barry_rival, "Barry fought in Decades")
    check(!BlueSinnohPilot.rowan_pokedex, "Pokedex granted in Decades")
    check(Marshal.dump($PokemonGlobal.blue_regions) == old_state, "Decades save changed")

    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR), "Johto received Sinnoh starter")
    check(!$PokemonGlobal.blue_regions.key?("sinnoh_pilot"), "Johto state contaminated")
    $PokemonGlobal.blue_regions["current"] = "HOENN"
    check(!BlueSinnohPilot.rowan_briefcase, "Hoenn received Rowan flags")
    check(!$PokemonGlobal.blue_regions.key?("sinnoh_pilot"), "Hoenn state contaminated")

    $PokemonGlobal.blue_regions["current"] = "SINNOH"
    check(!BlueSinnohPilot.barry_intro, "Barry intro skipped mother")
    check(!BlueSinnohPilot.rowan_briefcase, "Rowan briefcase skipped Barry")
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "Starter granted before authorized intro")
    check(BlueSinnohPilot.mother, "Mother introduction missing")
    check(!BlueSinnohPilot.mother, "Mother repeated first introduction")
    check(BlueSinnohPilot.barry_intro, "Barry introduction missing")
    check(!BlueSinnohPilot.barry_intro, "Barry repeated first introduction")
    check(BlueSinnohPilot.rowan_briefcase, "Rowan/briefcase missing")
    check(!BlueSinnohPilot.rowan_briefcase, "Rowan intro repeated")
    check(!BlueSinnohPilot.choose_starter, "Professor dialog granted Pokémon")
    check($player.party.empty?, "Professor dialog created Pokémon")
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIKACHU),
          "Unlisted species was accepted")

    $can_grant = false
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "Failed add was persisted")
    check(BlueSinnohPilot.starter.nil?, "Failed add persisted starter state")
    $can_grant = true
    check(BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "Physical Piplup ball did not grant")
    check($player.party == [[:PIPLUP, 5]], "Wrong starter or level")
    check(BlueSinnohPilot.starter == :PIPLUP, "Starter record missing")
    check(BlueSinnohPilot.rival_species == :TURTWIG, "Barry counter typing wrong")
    check(BlueSinnohPilot.rival_version == 2, "Wrong Barry PBS version")
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "Second starter could be taken")
    check(!BlueSinnohPilot.rowan_pokedex, "Pokedex granted before rival battle")
    check(!$player.has_pokedex, "Dex field changed before battle")

    check(!BlueSinnohPilot.barry_rival, "Barry fought with no PBS marker")
    check(TrainerBattle.history.empty?, "TrainerBattle triggered too early")
    File.write(BlueSinnohPilot::RIVAL_READY, "BAD MARKER")
    check(!BlueSinnohPilot.barry_rival, "Invalid rival marker accepted")
    File.write(BlueSinnohPilot::RIVAL_READY,
               BlueSinnohPilot::RIVAL_PROOF + "\n")
    check(BlueSinnohPilot.barry_rival, "Rival PBS marker did not unlock")
    check(TrainerBattle.history == [[:BLUE_SINNOH_RIVAL, "Barry", 2]],
          "Wrong rival PBS battle/version")
    check($rules == ["canLose"], "Rival tutorial could not lose")
    check($player.heals == 1, "Player not healed after first rival battle")
    check(BlueSinnohPilot.rival_fought?, "Rival flag not set")
    check(!BlueSinnohPilot.barry_rival, "Rival battle repeated")

    check(BlueSinnohPilot.rowan_pokedex, "Pokedex not given after rival")
    check($player.has_pokedex, "Pokedex property not updated")
    check(!BlueSinnohPilot.rowan_pokedex, "Pokedex duplicated")

    save = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = Marshal.load(save)
    check(BlueSinnohPilot.starter == :PIPLUP, "Save/load lost starter")
    check(BlueSinnohPilot.rival_fought?, "Save/load lost rival")
    check(BlueSinnohPilot.progress["pokedex_received"], "Save/load lost dex")
    check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "Save/load could grant another starter")

    $PokemonGlobal.blue_regions["current"] = "KANTO"
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "Kanto received Sinnoh starter")
    check(!BlueSinnohPilot.rowan_pokedex, "Sinnoh handler active in Kanto")
  end
end

puts "SINNOH_STORY_RUNTIME_GUARDS_OK"
