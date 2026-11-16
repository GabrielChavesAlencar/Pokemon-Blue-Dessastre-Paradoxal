# CH07: pure Ruby state/save tests. No Game.exe, donor data or runtime assets.
require "tmpdir"

class CH07Global
  attr_accessor :blue_regions
end
class CH07Player
  attr_accessor :has_pokedex
  attr_reader :party, :heals
  def initialize
    @party = []
    @has_pokedex = false
    @heals = 0
  end
  def heal_party
    @heals += 1
  end
end
module TrainerBattle
  @calls = []
  class << self
    attr_reader :calls
    def start(*args)
      @calls << args
      $battle_status
    end
  end
end

$messages = []
$rules = []
$battle_status = nil
$grant_allowed = true
$grant_hook = nil
def _INTL(message, *_args)
  message
end
def pbMessage(message)
  $messages << message
end
def setBattleRule(rule)
  $rules << rule
end
def pbAddPokemonSilent(species, level)
  return false unless $grant_allowed
  $grant_hook.call if $grant_hook
  $player.party << [species, level]
  true
end
def check(condition, description)
  raise "CH07: #{description}" unless condition
end
def fresh(region = "SINNOH", initial = "SINNOH")
  $PokemonGlobal = CH07Global.new
  $PokemonGlobal.blue_regions = {
    "version" => 1, "current" => region, "initial" => initial
  }
  $player = CH07Player.new
  $battle_status = nil
  $grant_allowed = true
  $grant_hook = nil
  $messages.clear
  $rules.clear
  TrainerBattle.calls.clear
end
def intro
  check(BlueSinnohPilot.mother, "mother did not advance")
  check(BlueSinnohPilot.barry_intro, "Barry introduction did not advance")
  check(BlueSinnohPilot.rowan_briefcase, "Rowan did not authorize balls")
end

require File.expand_path(ARGV.fetch(0))
Dir.mktmpdir("sinnoh-ch07-") do |directory|
  Dir.chdir(directory) do
    Dir.mkdir("Data")

    fresh
    check(!BlueSinnohPilot.barry_intro, "Barry bypassed mother")
    check(!BlueSinnohPilot.rowan_briefcase, "Rowan bypassed Barry")
    check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "ball bypassed Rowan")
    check(BlueSinnohPilot.starter.nil?, "read-only starter inquiry is not nil")
    check(!$PokemonGlobal.blue_regions.key?("sinnoh_pilot"),
          "rejected events or reads wrote empty flags")

    intro
    flags = $PokemonGlobal.blue_regions["sinnoh_pilot"]
    check(flags.keys.sort == %w[barry_intro mother_intro rowan_briefcase_seen],
          "intro checkpoint order was invalid")
    $grant_allowed = false
    unchanged = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "failed engine grant was accepted")
    check($player.party.empty?, "failed grant modified party")
    check(Marshal.dump($PokemonGlobal.blue_regions) == unchanged,
          "failed grant changed save")
    $grant_allowed = true

    # This simulates reentry while the game engine grants the first Pokémon.
    $grant_hook = proc do
      check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
            "reentrant second ball bypassed lock")
    end
    check(BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "authorized ball rejected")
    $grant_hook = nil
    check($player.party == [[:TURTWIG, 5]], "reentrant starter duplicated")
    check(flags["starter"] == "TURTWIG" &&
          flags["starter_received"] == true, "starter flags not committed")
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "same Poké Ball was duplicated")
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "different Poké Ball granted a second starter")
    check($player.party.size == 1, "party has more than one starter")
    check(!BlueSinnohPilot.rowan_pokedex, "Pokédex bypassed first battle")

    File.write(BlueSinnohPilot::RIVAL_READY, "INVALID")
    check(!BlueSinnohPilot.barry_rival, "invalid PBS proof unlocked Barry")
    check(TrainerBattle.calls.empty?, "Barry battle called without PBS proof")
    File.write(BlueSinnohPilot::RIVAL_READY, BlueSinnohPilot::RIVAL_PROOF)
    $battle_status = nil
    check(!BlueSinnohPilot.barry_rival, "nil battle result was accepted")
    check(!BlueSinnohPilot.rival_fought?, "nil battle wrote flags")
    $battle_status = false
    check(BlueSinnohPilot.barry_rival, "valid canLose defeat did not finish")
    check(BlueSinnohPilot.rival_fought?, "loss did not set rival flag")
    check($player.heals == 1, "party not healed after valid loss")
    check(!BlueSinnohPilot.barry_rival, "completed rival battle repeated")
    check(TrainerBattle.calls.size == 2, "extra rival battles after loss")
    check($rules == ["canLose", "canLose"], "rival should be canLose")
    check(BlueSinnohPilot.rowan_pokedex, "Pokédex missing after valid loss")
    check(!BlueSinnohPilot.rowan_pokedex, "Pokédex was granted twice")

    snapshot = Marshal.dump($PokemonGlobal.blue_regions)
    $PokemonGlobal.blue_regions = Marshal.load(snapshot)
    check(BlueSinnohPilot.starter == :TURTWIG, "reload lost starter")
    check(BlueSinnohPilot.rival_fought?, "reload lost completed battle")
    check(BlueSinnohPilot.progress["pokedex_received"] == true,
          "reload lost Pokédex flag")
    check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "reload allowed another starter")

    %w[DECADES KANTO JOHTO HOENN].each do |region|
      $PokemonGlobal.blue_regions["current"] = region
      untouched = Marshal.dump($PokemonGlobal.blue_regions)
      check(!BlueSinnohPilot.mother, "#{region} ran Sinnoh mother")
      check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
            "#{region} granted Sinnoh ball")
      check(!BlueSinnohPilot.barry_rival, "#{region} ran Sinnoh rival")
      check(!BlueSinnohPilot.rowan_pokedex, "#{region} granted Sinnoh Pokédex")
      check(Marshal.dump($PokemonGlobal.blue_regions) == untouched,
            "#{region} save record was contaminated")
    end
    $PokemonGlobal.blue_regions["current"] = "SINNOH"
    check(BlueSinnohPilot.starter == :TURTWIG, "return lost starter record")

    corrupt = [
      {"barry_intro" => true},
      {"mother_intro" => "true"},
      {"mother_intro" => true, "barry_intro" => true,
       "rowan_briefcase_seen" => true, "starter_received" => true},
      {"mother_intro" => true, "barry_intro" => true,
       "rowan_briefcase_seen" => true, "starter" => "PIKACHU",
       "starter_received" => true},
      {"rival_fought" => true},
      {"pokedex_received" => true}
    ]
    corrupt.each do |invalid|
      $PokemonGlobal.blue_regions["sinnoh_pilot"] = invalid
      unchanged = Marshal.dump($PokemonGlobal.blue_regions)
      check(BlueSinnohPilot.progress.nil?, "corrupt checkpoint was accepted")
      check(!BlueSinnohPilot.mother, "corrupt checkpoint advanced mother")
      check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
            "corrupt checkpoint granted Pokémon")
      check(!BlueSinnohPilot.barry_rival, "corrupt checkpoint allowed battle")
      check(!BlueSinnohPilot.rowan_pokedex, "corrupt checkpoint granted dex")
      check(Marshal.dump($PokemonGlobal.blue_regions) == unchanged,
            "corrupt checkpoint was overwritten")
    end

    fresh("SINNOH", "JOHTO")
    previous = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueSinnohPilot.mother, "foreign initial region accepted as QA")
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "foreign initial region received starter")
    check(Marshal.dump($PokemonGlobal.blue_regions) == previous,
          "foreign-region save was edited")

    fresh
    check(BlueSinnohPilot.progress == {}, "new save inherited old flags")
    check($player.party.empty? && !$player.has_pokedex,
          "new save inherited previous character data")
    intro
    check(BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "new session cannot select its own starter")
    check($player.party == [[:CHIMCHAR, 5]], "fresh session starter incorrect")
  end
end
puts "SINNOH_CH07_FLAGS_BALLS_LOSS_SAVE_GUARDS_OK"
