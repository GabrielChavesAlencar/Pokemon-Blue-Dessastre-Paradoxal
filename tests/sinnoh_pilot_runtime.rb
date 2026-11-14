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
      return nil if $battle_returns_nil
      return false if $battle_returns_false
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

    # A new, separate QA session may TEST Barry without creating a release
    # marker, but only after its native compile/probe proof has been accepted.
    File.delete(BlueSinnohPilot::RIVAL_READY)
    $PokemonGlobal.blue_regions = {"version" => 1, "current" => "SINNOH"}
    $player = FakeSinnohPlayer.new
    $qa_barry_valid = false
    module_eval_code = <<~RUBY
      module BlueSinnohQAStart
        def self.barry_test_authorized?
          $qa_barry_valid == true
        end
      end
    RUBY
    eval(module_eval_code)
    check(BlueSinnohPilot.mother, "QA mother not initialized")
    check(BlueSinnohPilot.barry_intro, "QA Barry intro not initialized")
    check(BlueSinnohPilot.rowan_briefcase, "QA Rowan not initialized")
    check(BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "QA Chimchar ball was not granted")
    before_qa_battle = TrainerBattle.history.length
    check(!BlueSinnohPilot.barry_rival, "QA Barry started without proof")
    check(TrainerBattle.history.length == before_qa_battle,
          "QA battle went through before proof")
    $qa_barry_valid = true
    $battle_returns_nil = true
    check(!BlueSinnohPilot.barry_rival, "QA Barry nil battle result accepted")
    check(!BlueSinnohPilot.rival_fought?, "Nil battle marked as completed")
    $battle_returns_nil = false
    $battle_returns_false = true
    check(BlueSinnohPilot.barry_rival, "Verified QA Barry loss not accepted")
    $battle_returns_false = false
    check(TrainerBattle.history.last == [:BLUE_SINNOH_RIVAL, "Barry", 1],
          "QA rival was not Piplup against Chimchar")
    check(BlueSinnohPilot.rival_fought?, "QA battle win not stored")
    check(!File.exist?(BlueSinnohPilot::RIVAL_READY),
          "QA created release marker")
    check(BlueSinnohPilot.rowan_pokedex, "QA Pokedex missing after Barry")
    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    old_johto = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueSinnohPilot.barry_rival, "QA enabled Barry in Johto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == old_johto,
          "QA altered Johto saves")
  end
end

puts "SINNOH_STORY_RUNTIME_GUARDS_OK"
