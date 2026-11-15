# Real Campaign/Story Battle.initialize prepend-chain integration regression.
# Runs without assets, PBS writes, or a live save.
class PokemonGlobalMetadata
  attr_accessor :blue_story_mode,:blue_traditional_starters,:blue_regions
end
module Compiler
  def self.main;end
end
module BlueBattleOptions
  def self.battle_area?;false;end
  def self.snapshot(_kind);{};end
end
module GameData
  module GrowthRate
    def self.max_level;100;end
  end
  class Species
    attr_reader :id,:species,:form,:flags,:base_stats,:moves,:tutor_moves,:egg_moves,:types
    DATA={}
    def initialize(id,bst,previous=nil,evolutions=[])
      @id=@species=id;@form=0;@flags=[];@base_stats={HP:bst}
      @previous=previous;@evolutions=evolutions;@moves=[[1,:TACKLE]]
      @tutor_moves=[];@egg_moves=[];@types=[:NORMAL];DATA[id]=self
    end
    def self.get(id);DATA.fetch(id);end
    def self.try_get(id);DATA[id];end
    def self.each(&block);DATA.values.each(&block);end
    def self.get_species_form(id,_form);get(id);end
    def get_evolutions(_ignore=false);@evolutions;end
    def get_previous_species;@previous || @species;end
    def get_baby_species;@previous || @species;end
  end
end
class Pokemon
  class Move
    attr_reader :id
    def initialize(id);@id=id;end
  end
  attr_accessor :species,:form,:level,:name,:ability,:ability_index,:moves,:item
  def initialize(species,level)
    @species=species;@level=level;@form=0;@name=""
    @moves=[Move.new(:TACKLE)];@ability_index=0;@item=nil
  end
  def egg?;false;end
  def shadowPokemon?;false;end
  def nicknamed?;false;end
  def calc_stats;end
  def heal;end
  def reset_moves;@moves=[Move.new(:TACKLE)];end
  def species_data;GameData::Species.get(@species);end
  def male?;true;end
  def female?;false;end
end
module GameData
  module Move
    def self.exists?(_id);true;end
  end
end
Trainer=Struct.new(:trainer_type,:name,:version,:party) do
  def clone;self.class.new(trainer_type,name,version,party);end
end
class Battle
  attr_reader :captured_trainers
  def initialize(*args)
    @captured_trainers=args[4]
  end
  def trainerBattle?;false;end
end
class Player
  attr_accessor :party,:badge_count
  def initialize(party);@party=party;@badge_count=0;end
end
module BlueTrainerMoves
  def self.apply(*);end
end
GameData::Species.new(:BULBASAUR,318,nil,[[:IVYSAUR,:Level,16]])
GameData::Species.new(:IVYSAUR,405,:BULBASAUR,[[:VENUSAUR,:Level,32]])
GameData::Species.new(:VENUSAUR,525,:IVYSAUR)
GameData::Species.new(:RATTATA,253,nil,[[:RATICATE,:Level,20]])
GameData::Species.new(:RATICATE,413,:RATTATA)
GameData::Species.new(:DRAGONITE,600)
load File.expand_path(ARGV.fetch(0))   # EvolutionScaling.rb
load File.expand_path(ARGV.fetch(1))   # Story.rb
load File.expand_path(ARGV.fetch(2))   # Campaign.rb

def check(cond,msg);raise "BATTLE EVOLUTION: #{msg}" unless cond;end
$PokemonGlobal=PokemonGlobalMetadata.new
$PokemonGlobal.blue_story_mode=:story
$PokemonGlobal.blue_traditional_starters=true
$PokemonGlobal.blue_regions={"current"=>"KANTO"}
$player=Player.new([Pokemon.new(:BULBASAUR,30)])
# Same installation precedence as Compiler.main:
Battle.prepend(BlueStory::Teams)
Battle.prepend(BlueCampaign::Teams)
def battler(kind,species)
  original=Pokemon.new(species,5)
  trainer=Trainer.new(kind,"Route trainer",0,[original])
  battle=Battle.new(nil,nil,nil,nil,[trainer])
  [battle.captured_trainers[0].party[0],original]
end
ivysaur,source=battler(:BLUE_KANTO_LASS,:BULBASAUR)
check(ivysaur.level==21 && ivysaur.species==:IVYSAUR,
      "70% scaled Bulbasaur should become Ivysaur even at 350 BST stage")
check(source.level==5 && source.species==:BULBASAUR,
      "Trainer's authored PBS species or level mutated")
raticate,_=battler(:BLUE_KANTO_LASS,:RATTATA)
check(raticate.level==21 && raticate.species==:RATTATA,
      "Level-21 Rattata evolved before trainer grace threshold")
# At 40 highest-party level, 70%=28: Raticate is eligible despite 413 BST.
$player.party[0].level=40
raticate,_=battler(:BLUE_KANTO_LASS,:RATTATA)
check(raticate.level==28 && raticate.species==:RATICATE,
      "Natural Raticate at 28 was replaced by BST 350 adapter")
# Bosses keep the authored roster, even where an ordinary trainer evolves.
$player.party[0].level=30
boss,_=battler(:BLUE_KANTO_LEADER,:BULBASAUR)
check(boss.species==:BULBASAUR && boss.level==21,
      "First Kanto leader's authored species was overwritten")
# Master stage: 90% scaling without old BST restrictions.
$player.badge_count=11
def BlueCampaign.expand_master_teams(trainers,_level);trainers;end
master,_=battler(:BLUE_KANTO_LASS,:BULBASAUR)
check(master.level==27 && master.species==:IVYSAUR,
      "Master 90% team failed its post-scaling evolution")
puts "PASS: actual prepend-chain, 70/90%, BST exception, authored first boss, no PBS mutation"
