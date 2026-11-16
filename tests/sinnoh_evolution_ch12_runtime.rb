# CH12: actual Blue runtime chain, author-only synthetic Sinnoh Pokémon.
# No Game.exe, PBS, source ROM, saves or native Sinnoh maps are used.
require "json"

def check(condition, label)
  raise "SINNOH_CH12: #{label}" unless condition
end

class PokemonGlobalMetadata
  attr_accessor :blue_regions, :blue_story_mode, :blue_traditional_starters
end
module BlueBattleOptions
  def self.battle_area?; false; end
  def self.snapshot(_); {}; end
end
module BlueTrainerMoves
  def self.apply(_); true; end
end
module GameData
  module GrowthRate
    def self.max_level; 100; end
  end
  module Move
    def self.exists?(_); true; end
  end
  class Species
    DATA = {}
    attr_reader :id, :species, :form, :flags, :base_stats, :moves
    attr_reader :tutor_moves, :egg_moves, :types
    def initialize(id, bst, previous = nil, evolutions = [], flags = [])
      @id = @species = id
      @form = 0
      @previous = previous
      @evolutions = evolutions
      @flags = flags
      @base_stats = {:HP => bst}
      @moves = [[1, :TACKLE]]
      @tutor_moves = []
      @egg_moves = []
      @types = [:NORMAL]
      DATA[id] = self
    end
    def self.get(id); DATA.fetch(id); end
    def self.try_get(id); DATA[id]; end
    def self.each(&block); DATA.values.each(&block); end
    def self.get_species_form(id, _form); get(id); end
    def get_evolutions(_exclude_invalid = false); @evolutions; end
    def get_previous_species; @previous || @species; end
    def get_baby_species; @previous || @species; end
  end
end

class Pokemon
  class Move
    attr_reader :id
    def initialize(id); @id = id; end
  end
  attr_accessor :species, :form, :level, :name, :ability, :ability_index
  attr_accessor :moves, :item, :shiny
  def initialize(species, level, egg = false, shadow = false)
    @species, @level, @egg, @shadow = species, level, egg, shadow
    @form = 0
    @name = ""
    @ability_index = 0
    @moves = [Move.new(:TACKLE)]
    @item = nil
    @shiny = false
  end
  def egg?; @egg; end
  def shadowPokemon?; @shadow; end
  def nicknamed?; false; end
  def male?; true; end
  def female?; false; end
  def reset_moves; @moves = [Move.new(:TACKLE)]; end
  def calc_stats; end
  def heal; end
  def species_data; GameData::Species.get(@species); end
end

Trainer = Struct.new(:trainer_type, :name, :version, :party) do
  def clone; self.class.new(trainer_type, name, version, party); end
end
class Battle
  attr_reader :captured
  def initialize(*args); @captured = args; end
  def trainerBattle?; true; end
end
class Player
  attr_accessor :party, :badge_count, :badges
  def initialize
    @party = [Pokemon.new(:TURTWIG, 50)]
    @badge_count = 0
    @badges = Array.new(24, false)
  end
end
module PBDayNight
  @day = true
  class << self
    attr_accessor :day
    def isDay?; @day; end
    def isNight?; !@day; end
    def isMorning?; @day; end
    def isAfternoon?; @day; end
    def isEvening?; !@day; end
  end
end

# These fixtures mirror *only* minimum evolution thresholds, not any real
# compiled Pokémon data or trainer rosters of the game installation.
GameData::Species.new(:TURTWIG, 318, nil, [[:GROTLE, :Level, 18]])
GameData::Species.new(:GROTLE, 405, :TURTWIG, [[:TORTERRA, :Level, 32]])
GameData::Species.new(:TORTERRA, 525, :GROTLE)
GameData::Species.new(:CHIMCHAR, 309, nil, [[:MONFERNO, :Level, 14]])
GameData::Species.new(:MONFERNO, 405, :CHIMCHAR, [[:INFERNAPE, :Level, 36]])
GameData::Species.new(:INFERNAPE, 534, :MONFERNO)
GameData::Species.new(:PIPLUP, 314, nil, [[:PRINPLUP, :Level, 16]])
GameData::Species.new(:PRINPLUP, 405, :PIPLUP, [[:EMPOLEON, :Level, 36]])
GameData::Species.new(:EMPOLEON, 530, :PRINPLUP)
GameData::Species.new(:ROSELIA, 400, nil, [[:ROSERADE, :Item, :SHINYSTONE]])
GameData::Species.new(:ROSERADE, 515, :ROSELIA)
GameData::Species.new(:GRAVELER, 390, nil, [[:GOLEM, :Trade, nil]])
GameData::Species.new(:GOLEM, 495, :GRAVELER)
GameData::Species.new(:RIOLU, 285, nil, [[:LUCARIO, :HappinessDay, nil]])
GameData::Species.new(:LUCARIO, 525, :RIOLU)
GameData::Species.new(:SHINX, 263, nil, [[:LUXIO, :Level, 15]])
GameData::Species.new(:LUXIO, 363, :SHINX)
GameData::Species.new(:EEVEE, 325, nil,
                      [[:VAPOREON, :Item, :WATERSTONE],
                       [:JOLTEON, :Item, :THUNDERSTONE]])
GameData::Species.new(:VAPOREON, 525, :EEVEE)
GameData::Species.new(:JOLTEON, 525, :EEVEE)
GameData::Species.new(:IRON_TEST, 590, nil,
                      [[:IRON_TEST_EVOLVED, :Level, 5]], ["Paradox"])
GameData::Species.new(:IRON_TEST_EVOLVED, 630, :IRON_TEST)
GameData::Species.new(:SUPPORT, 330)

load File.expand_path(ARGV.fetch(0))  # regional source-of-truth fixture
load File.expand_path(ARGV.fetch(1))  # Regions.rb
load File.expand_path(ARGV.fetch(2))  # EvolutionScaling.rb
load File.expand_path(ARGV.fetch(3))  # Story.rb
load File.expand_path(ARGV.fetch(4))  # Campaign.rb
contract = JSON.parse(File.read(File.expand_path(ARGV.fetch(5))))
check(contract["region"] == "SINNOH" &&
      contract["gameplay_verified"] == false, "contract claims playability")

$PokemonGlobal = PokemonGlobalMetadata.new
$PokemonGlobal.blue_story_mode = :story
$PokemonGlobal.blue_traditional_starters = true
$PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")
$player = Player.new

# Actual prepend order in the Blue engine: the outer campaign scales the
# trainer first, while the story module enforces its independent BST tier.
Battle.prepend(BlueStory::Teams)
Battle.prepend(BlueCampaign::Teams)
BlueCampaign.define_singleton_method(:master_partner) do |_party, _trainer, level|
  Pokemon.new(:SUPPORT, level)  # only the partner selection is a stub
end

def battle(species, type = :BLUE_SINNOH_HIKER)
  pokemon = Pokemon.new(species, 5)
  original = Trainer.new(type, "Synthetic Sinnoh trainer", 0, [pokemon])
  before = Marshal.dump(original)
  result = Battle.new(nil, nil, [], nil, [original])
  check(Marshal.dump(original) == before,
        "#{species}: live PBS trainer was mutated")
  [result.captured[4][0].party, original]
end

def player_level(level, eggs = [])
  $player.party = [Pokemon.new(:TURTWIG, level)] + eggs
end

# Progress is additive via local badge achievements. This is the actual
# BlueStory.stage implementation, NOT a fabricated numeric cap by badge.
check(BlueStory.stage == 0 && BlueStory.cap == 350,
      "base badge stage/BST cap incorrect")
s = $PokemonGlobal.blue_regions
BlueRegions.info("SINNOH")["milestones"].each do |badge|
  check(BlueRegions.award(s, "SINNOH", badge), "Sinnoh badge award blocked")
end
check(BlueStory.stage == 2 && BlueStory.cap == 540,
      "eight Sinnoh badges must count as eight unique achievements")
check($player.badges.none? && $player.badge_count == 0,
      "Sinnoh badges were copied into native Decades badges")
$player.badge_count = 3
check(BlueStory.stage == 3 && BlueStory.cap.nil?,
      "11 global emeralds must reach Master")
$player.badge_count = 0
# Return to an early stage by moving to a fresh regional story state.
$PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")

# Normal 70% then Master 90% after reaching Blue's existing 11-emerald stage.
player_level(50, [Pokemon.new(:SUPPORT, 99, true)])
check(BlueEvolutionScaling.progress_level == 50,
      "egg incorrectly increased progress reference")
check(BlueCampaign.trainer_level(nil) == 35, "Normal not floor(50*70%)")
[
  [:TURTWIG, :GROTLE, :TORTERRA],
  [:CHIMCHAR, :MONFERNO, :INFERNAPE],
  [:PIPLUP, :PRINPLUP, :EMPOLEON],
].each do |base, normal, master|
  team, _ = battle(base)
  check(team.length == 1 && team.first.level == 35 &&
        team.first.species == normal,
        "#{base}: Normal 70%/evolution or BST exception wrong")
end
s = $PokemonGlobal.blue_regions
BlueRegions.info("SINNOH")["milestones"].each do |badge|
  BlueRegions.award(s, "SINNOH", badge)
end
$player.badge_count = 3
check(BlueCampaign.master? && BlueCampaign.trainer_level(nil) == 45,
      "Master not floor(50*90%)")
[
  [:TURTWIG, :TORTERRA], [:CHIMCHAR, :INFERNAPE], [:PIPLUP, :EMPOLEON]
].each do |base, evolved|
  team, _ = battle(base)
  check(team.length == 4, "#{base}: Master did not expand 1 to 4")
  check(team.first.level == 45 && team.first.species == evolved,
        "#{base}: Master 90% did not evolve after scaling")
  check(team.all? { |p| p.level == 45 },
        "#{base}: Master partners at inconsistent level")
end
# Authored gym/elite/champion/rival species must be retained (levels still
# scaled). Never replace their PBS roster with automatic evolutions.
%w[LEADER ELITE CHAMPION RIVAL].each do |boss|
  team, original = battle(:TURTWIG, ("BLUE_SINNOH_" + boss).to_sym)
  check(team.first.species == :TURTWIG && team.first.level == 45,
        "#{boss}: authored Sinnoh boss team evolved automatically")
  check(original.party.first.species == :TURTWIG && original.party.first.level == 5,
        "#{boss}: authored PBS input changed")
end

# Test threshold boundaries in the shared runtime, no duplicated policy.
$player.badge_count = 0
$PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")
def threshold(base, evolved, low_player, high_player)
  player_level(low_player)
  early, = battle(base)
  check(early.first.species == base, "#{base}: evolved below native threshold")
  player_level(high_player)
  late, = battle(base)
  check(late.first.species == evolved,
        "#{base}: missing evolved form above native threshold")
end
threshold(:TURTWIG, :GROTLE, 31, 33)      # floor(31*.7)=21; floor(33*.7)=23
threshold(:ROSELIA, :ROSERADE, 42, 43)     # 29 -> 30 (stone)
threshold(:GRAVELER, :GOLEM, 57, 58)       # 39 -> 40 (trade)
threshold(:RIOLU, :LUCARIO, 63, 65)       # 44 -> 45 (friendship)
PBDayNight.day = false
player_level(65)
night, = battle(:RIOLU)
check(night.first.species == :RIOLU,
      "day-only happiness evolved during night")
PBDayNight.day = true
day, = battle(:RIOLU)
check(day.first.species == :LUCARIO,
      "day-only happiness did not evolve in day")
branch, = battle(:EEVEE)
check(branch.first.species == :EEVEE,
      "ambiguous stone branch picked a form without player choice")
special, = battle(:IRON_TEST)
check(special.first.species != :IRON_TEST_EVOLVED,
      "Paradox special evolved by generic scaler")

# Native level maximum and empty/egg-only team cannot produce level zero.
$player.badge_count = 3
player_level(250)
check(BlueCampaign.trainer_level(nil) == 100,
      "maximum level not capped by GameData::GrowthRate")
check(BlueEvolutionScaling.progress_level == 100,
      "evolution reference exceeded engine's max level")
$player.party = [Pokemon.new(:SUPPORT, 99, true)]
check(BlueCampaign.trainer_level(nil) == 1,
      "egg-only party produced nonminimum enemy level")
$player.party.clear
check(BlueCampaign.trainer_level(nil) == 1,
      "empty party produced level zero")

# Wild slots follow their original species, threshold and deterministic
# roll; the script must never rewrite encounter PBS or a player's save.
$player.party = [Pokemon.new(:TURTWIG, 25)]
check(BlueEvolutionScaling.available_wild_species(:SHINX, 19) == [:SHINX],
      "wild under threshold offered Luxio")
check(BlueEvolutionScaling.available_wild_species(:SHINX, 20) ==
      [:SHINX, :LUXIO], "wild cap20 omitted Luxio")
check(BlueEvolutionScaling.wild_option(:SHINX, 6, 20, proc { 0 }) ==
      [:LUXIO, 20], "eligible roll didn't evolve wild Shinx")
check(BlueEvolutionScaling.wild_option(:SHINX, 6, 20, proc { 99 }) ==
      [:SHINX, 6], "eligible wild Shinx erased the original slot")
check(BlueEvolutionScaling.wild_option(:SHINX, 6, 19, proc { 0 }) ==
      [:SHINX, 6], "wild Shinx evolved before threshold")

# Switching off Story must not alter opponents, player or save.
$PokemonGlobal.blue_story_mode = :battle
player_level(55)
raw, input = battle(:TURTWIG)
check(raw.first.level == 5 && raw.first.species == :TURTWIG,
      "non-story trainer was scaled/evolved")
check(input.party.first.level == 5,
      "non-story PBS was changed")

puts "SINNOH_CH12_REAL_CAMPAIGN_STORY_EVOLUTION_NORMAL_MASTER_LEVEL_CAP_OK"
