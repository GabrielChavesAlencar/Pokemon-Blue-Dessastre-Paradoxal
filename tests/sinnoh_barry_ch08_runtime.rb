# CH08 - execute actual BlueCampaign scaling in pure Ruby and check Barry PBS gates.
# No native game, donor assets or writes outside a temporary directory.
require "tmpdir"

module BlueStory
  @stage = 0
  @story = true
  class << self
    attr_accessor :stage, :story
    def story?; @story; end
  end
end
module GameData
  module GrowthRate
    def self.max_level; 100; end
  end
  module Trainer
    @table = {}
    class << self
      attr_accessor :table
      def get(type, name, version)
        return nil unless type == :BLUE_SINNOH_RIVAL && name == "Barry"
        @table[version]
      end
    end
  end
end
module BlueBattleOptions
  def self.snapshot(_); {}; end
end
module BlueTrainerMoves
  def self.apply(_); true; end
end
class CH08Mon
  attr_accessor :species, :level
  def initialize(species, level, egg = false)
    @species, @level, @egg = species, level, egg
  end
  def egg?; @egg; end
  def calc_stats; true; end
  def heal; true; end
end
class CH08Trainer
  attr_accessor :party, :name, :trainer_type
  def initialize(species)
    @party = [CH08Mon.new(species, 5)]
    @name = "Barry"
    @trainer_type = :BLUE_SINNOH_RIVAL
  end
end
class CH08Player
  attr_accessor :party, :has_pokedex
  attr_reader :heals
  def initialize
    @party = []
    @has_pokedex = false
    @heals = 0
  end
  def heal_party; @heals += 1; end
end
class CH08Global
  attr_accessor :blue_regions
end
class Battle
  attr_reader :captured
  def initialize(*args); @captured = args; end
  def trainerBattle?; true; end
end
module TrainerBattle
  @history = []
  class << self
    attr_reader :history
    def start(*args)
      @history << args
      $battle_result
    end
  end
end
$messages = []
$rules = []
$battle_result = true
def _INTL(str, *_); str; end
def pbMessage(message); $messages << message; end
def setBattleRule(rule); $rules << rule; end
def check(condition, description)
  raise "SINNOH CH08: #{description}" unless condition
end
def reset_pilot(starter)
  $PokemonGlobal = CH08Global.new
  $PokemonGlobal.blue_regions = {
    "version" => 1, "current" => "SINNOH", "initial" => "SINNOH",
    "sinnoh_pilot" => {
      "mother_intro" => true, "barry_intro" => true,
      "rowan_briefcase_seen" => true,
      "starter" => starter.to_s, "starter_received" => true
    }
  }
  $player = CH08Player.new
  $player.party = [CH08Mon.new(starter, 37)]
  $battle_result = true
  $messages.clear
  $rules.clear
  TrainerBattle.history.clear
end

require File.expand_path(ARGV.fetch(0))
require File.expand_path(ARGV.fetch(1))
Battle.prepend(BlueCampaign::Teams)
# The real BlueCampaign.expand_master_teams is executed. Only the species
# selection of extra Master partners is a deterministic synthetic stub.
BlueCampaign.define_singleton_method(:master_partner) do |party, trainer, level|
  CH08Mon.new(:SYNTHETIC_MASTER_PARTNER, level)
end

Dir.mktmpdir("sinnoh-ch08-barry-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    File.write(BlueSinnohPilot::RIVAL_READY, BlueSinnohPilot::RIVAL_PROOF)

    matchup = {
      :TURTWIG => [0, :CHIMCHAR],
      :CHIMCHAR => [1, :PIPLUP],
      :PIPLUP => [2, :TURTWIG]
    }
    GameData::Trainer.table = {
      0 => CH08Trainer.new(:CHIMCHAR),
      1 => CH08Trainer.new(:PIPLUP),
      2 => CH08Trainer.new(:TURTWIG)
    }
    matchup.each do |selected, (version, rival)|
      reset_pilot(selected)
      check(BlueSinnohPilot.rival_version == version, "#{selected}: wrong version")
      check(BlueSinnohPilot.rival_species == rival, "#{selected}: wrong counter")
      check(BlueSinnohPilot.compiled_rival_valid?, "#{selected}: PBS not resolved")

      # Missing, wrong team, wrong seed and extra Pokemon must ALL block.
      original = GameData::Trainer.table.delete(version)
      check(!BlueSinnohPilot.compiled_rival_valid?, "#{selected}: missing PBS accepted")
      check(!BlueSinnohPilot.barry_rival, "#{selected}: battle allowed without PBS")
      check(TrainerBattle.history.empty?, "#{selected}: missing PBS started battle")
      check(!BlueSinnohPilot.rival_fought?, "#{selected}: missing PBS stored flag")
      GameData::Trainer.table[version] = original
      wrong = original.party
      original.party = [CH08Mon.new(:RATTATA, 5)]
      check(!BlueSinnohPilot.barry_rival, "#{selected}: wrong rival accepted")
      original.party = [CH08Mon.new(rival, 7)]
      check(!BlueSinnohPilot.barry_rival, "#{selected}: wrong seed accepted")
      original.party = [CH08Mon.new(rival, 5), CH08Mon.new(rival, 5)]
      check(!BlueSinnohPilot.barry_rival, "#{selected}: two PBS starters accepted")
      original.party = wrong
      check(BlueSinnohPilot.compiled_rival_valid?, "#{selected}: restored PBS blocked")

      # Normal 70% and Master 90% use ACTUAL Campaign.rb, not a copy.
      input = CH08Trainer.new(rival)
      before = Marshal.dump(input)
      BlueStory.story = true
      BlueStory.stage = 0
      battle = Battle.new(nil, nil, [], nil, [input])
      trainers = battle.captured[4]
      check(trainers.length == 1 && trainers[0].party.length == 1,
            "#{selected}: Normal changed party size")
      check(trainers[0].party[0].species == rival, "#{selected}: Normal counter wrong")
      check(trainers[0].party[0].level == 25, "#{selected}: Normal must floor(37*70%)")
      check(input.party[0].level == 5 && Marshal.dump(input) == before,
            "#{selected}: Normal modified PBS seed")
      BlueStory.stage = 3
      battle = Battle.new(nil, nil, [], nil, [input])
      team = battle.captured[4][0].party
      check(team.length == 4, "#{selected}: Master expansion should reach 4")
      check(team[0].species == rival && team[0].level == 33,
            "#{selected}: Master counter must floor(37*90%)")
      check(team.all? { |mon| mon.level == 33 },
            "#{selected}: Master partners not scaled")
      check(input.party.length == 1 && input.party.first.level == 5,
            "#{selected}: Master mutated PBS fixture")

      # The safe canLose path may end in victory or a valid defeat, not nil.
      $battle_result = false
      check(BlueSinnohPilot.barry_rival, "#{selected}: canLose loss refused")
      check(BlueSinnohPilot.rival_fought?, "#{selected}: loss flag missing")
      check(TrainerBattle.history == [[:BLUE_SINNOH_RIVAL, "Barry", version]],
            "#{selected}: battle started with wrong PBS version")
      check($player.heals == 1, "#{selected}: loss did not heal team")
      check(!BlueSinnohPilot.barry_rival, "#{selected}: replayed rival")
    end

    # A missing or empty player party cannot produce zero/negative levels.
    BlueStory.stage = 0
    $player = CH08Player.new
    check(BlueCampaign.trainer_level(nil, []) == 1, "empty party normal minimum")
    check(BlueCampaign.trainer_level(nil, [CH08Mon.new(:EGG, 99, true)]) == 1,
          "eggs must be ignored")
    check(BlueCampaign.trainer_level(nil, [CH08Mon.new(:TEST, 125)]) == 87,
          "Normal high level arithmetic")
    BlueStory.stage = 3
    check(BlueCampaign.trainer_level(nil, [CH08Mon.new(:TEST, 125)]) == 100,
          "Master level must respect max-level cap")
    check(BlueCampaign.trainer_level(nil, [CH08Mon.new(:TEST, 1)]) == 1,
          "Master must never produce level 0")

    # Outside story mode the regular Battle constructor must be unchanged.
    BlueStory.story = false
    base = CH08Trainer.new(:CHIMCHAR)
    battle = Battle.new(nil, nil, [], nil, [base])
    check(battle.captured[4].first.equal?(base), "non-story Battle was replaced")
    check(battle.captured[4].first.party.first.level == 5,
          "non-story PBS seed was modified")
    BlueStory.story = true
    BlueStory.stage = 0
  end
end
puts "SINNOH_CH08_THREE_PBS_NORMAL70_MASTER90_GUARDS_OK"
