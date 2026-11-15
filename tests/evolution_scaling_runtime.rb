# Functional regression of dynamic evolutions using native-shaped
# Essentials Species/Evolution records, with no Game.exe and no save changes.
require "ostruct"

module GameData
  module GrowthRate
    def self.max_level; 100; end
  end
  class Species
    attr_reader :species, :id, :form, :flags, :base_stats, :moves
    attr_reader :previous, :evolutions
    DATA={}
    def initialize(id, bst, previous=nil, evolutions=[], flags=[], form=0)
      @id=@species=id;@previous=previous;@evolutions=evolutions
      @form=form;@flags=flags;@base_stats={HP:bst}
      @moves=[[1,:TACKLE]]
      DATA[id]=self
    end
    def self.get(id); DATA.fetch(id); end
    def self.try_get(id); DATA[id]; end
    def self.each(&block); DATA.values.each(&block); end
    def get_evolutions(_exclude=false);@evolutions;end
    def get_previous_species;@previous || @species;end
  end
  module Move
    def self.exists?(_id);true;end
  end
end
class Poke
  attr_accessor :species,:form,:level,:name,:ability,:ability_index,:moves
  attr_accessor :shiny
  attr_reader :refreshes
  def initialize(species,level,shiny=false)
    @species=species;@level=level;@form=0;@name="";@shiny=shiny
    @ability_index=0;@moves=[OpenStruct.new(id: :TACKLE)];@refreshes=0
  end
  def egg?;false;end
  def shadowPokemon?;false;end
  def male?;true;end
  def female?;false;end
  def nicknamed?;false;end
  def reset_moves;@moves=[OpenStruct.new(id: :TACKLE)];end
  def calc_stats;@refreshes+=1;end
  def heal;end
end
module BlueStory
  def self.enabled?;true;end
end
module BlueCampaign
  def self.active?;true;end
end
$player=OpenStruct.new(party:[Poke.new(:BULBASAUR,30)])
module PBDayNight
  def self.isDay?;true;end
  def self.isNight?;false;end
  def self.isMorning?;false;end
  def self.isAfternoon?;false;end
  def self.isEvening?;false;end
end
class PokemonEncounters
  attr_accessor :species,:level
  def choose_wild_pokemon(_type, _rolls=1);[@species,@level];end
end
def check(value,message);raise "EVOLUTION SCALING: #{message}" unless value;end
GameData::Species.new(:BULBASAUR,318,nil,[[:IVYSAUR,:Level,16]])
GameData::Species.new(:IVYSAUR,405,:BULBASAUR,[[:VENUSAUR,:Level,32]])
GameData::Species.new(:VENUSAUR,525,:IVYSAUR)
GameData::Species.new(:RATTATA,253,nil,[[:RATICATE,:Level,20]])
GameData::Species.new(:RATICATE,413,:RATTATA)
GameData::Species.new(:PIKACHU,320,nil,[[:RAICHU,:Item,:THUNDERSTONE]])
GameData::Species.new(:RAICHU,485,:PIKACHU)
GameData::Species.new(:KADABRA,400,nil,[[:ALAKAZAM,:Trade,nil]])
GameData::Species.new(:ALAKAZAM,500,:KADABRA)
GameData::Species.new(:GOLBAT,455,nil,[[:CROBAT,:Happiness,nil]])
GameData::Species.new(:CROBAT,535,:GOLBAT)
GameData::Species.new(:EEVEE,325,nil,[[:VAPOREON,:Item,:WATERSTONE],
  [:JOLTEON,:Item,:THUNDERSTONE],[:FLAREON,:Item,:FIRESTONE]])
GameData::Species.new(:VAPOREON,525,:EEVEE)
GameData::Species.new(:JOLTEON,525,:EEVEE)
GameData::Species.new(:FLAREON,525,:EEVEE)
GameData::Species.new(:PARADOX,590,nil,[[:PARADOXEVOLVED,:Level,20]],["Paradox"])
GameData::Species.new(:PARADOXEVOLVED,650,:PARADOX)
GameData::Species.new(:REGIONAL,350,nil,[[:REGIONALEVOLVED,:Level,20]],[],1)
GameData::Species.new(:REGIONALEVOLVED,400,:REGIONAL)
GameData::Species.new(:TOXEL,242,nil,[[:TOXTRICITY,:Nature,30]])
GameData::Species.new(:TOXTRICITY,502,:TOXEL)

load File.expand_path(ARGV.fetch(0))
check(BlueEvolutionScaling.progress_level==30,"wrong highest-party cap")
check(BlueEvolutionScaling.options(:RATTATA,24).empty?,"Rattata evolved too early")
check(BlueEvolutionScaling.options(:RATTATA,25)[0][0]==:RATICATE,"Raticate at 25 missing")
check(BlueEvolutionScaling.options(:BULBASAUR,20).empty?,"Bulbasaur at 20 evolved")
check(BlueEvolutionScaling.options(:BULBASAUR,21)[0][0]==:IVYSAUR,"Ivysaur at 21 missing")
check(BlueEvolutionScaling.options(:IVYSAUR,36).empty?,"Venusaur too early")
check(BlueEvolutionScaling.options(:IVYSAUR,37)[0][0]==:VENUSAUR,"Venusaur at 37 missing")
check(BlueEvolutionScaling.options(:PIKACHU,29).empty?,"Stone too early")
check(BlueEvolutionScaling.options(:PIKACHU,30)[0][0]==:RAICHU,"Stone at 30 missing")
check(BlueEvolutionScaling.options(:KADABRA,39).empty?,"Trade too early")
check(BlueEvolutionScaling.options(:KADABRA,40)[0][0]==:ALAKAZAM,"Trade at 40 missing")
check(BlueEvolutionScaling.options(:GOLBAT,44).empty?,"Happiness too early")
check(BlueEvolutionScaling.options(:GOLBAT,45)[0][0]==:CROBAT,"Happiness at 45 missing")
check(BlueEvolutionScaling.options(:EEVEE,50).empty?,"Branching Eevee silently picked a form")
check(BlueEvolutionScaling.options(:PARADOX,99).empty?,"Paradox evolved")
check(BlueEvolutionScaling.options(:REGIONAL,99).empty?,"Regional nonzero form evolved")
check(BlueEvolutionScaling.options(:TOXEL,99).empty?,"Unsupported native condition was guessed")
check(BlueEvolutionScaling.wild_chance(24,25)==0,"Wild before threshold")
check(BlueEvolutionScaling.wild_chance(25,25)==15,"Wild chance 25")
check(BlueEvolutionScaling.wild_chance(30,25)==30,"Wild chance 30")
check(BlueEvolutionScaling.wild_chance(60,25)==60,"Wild max chance not capped")
check(BlueEvolutionScaling.wild_option(:RATTATA,5,30,proc { 0 })==[:RATICATE,25],
      "Wild Raticate at cap30 should be minimum lvl25")
check(BlueEvolutionScaling.wild_option(:RATTATA,5,30,proc { 99 })==[:RATTATA,5],
      "Wild base Rattata must survive selection")
check(BlueEvolutionScaling.available_wild_species(:RATTATA,30)==[:RATTATA,:RATICATE],
      "Habitat listing missed base or evolution")
check(BlueEvolutionScaling.available_wild_species(:BULBASAUR,37)==
      [:BULBASAUR,:IVYSAUR,:VENUSAUR],"Chained habitat evolution missing")
check(BlueEvolutionScaling.available_wild_species(:EEVEE,99)==[:EEVEE],
      "Unproven Eevee branches in Habitat Dex")
check(BlueEvolutionScaling.upgrade_trainer!(Poke.new(:BULBASAUR,21)).species==:IVYSAUR,
      "Trainer Bulbasaur not evolved")
v=BlueEvolutionScaling.upgrade_trainer!(Poke.new(:BULBASAUR,37,true))
check(v.species==:VENUSAUR && v.shiny && v.refreshes==2,
      "Two-stage trainer evolution lost shiny/progress/stats")
check(BlueEvolutionScaling.legitimate_trainer_form?(Poke.new(:RATICATE,25)),
      "Raticate native evolution should bypass old 350 BST restriction")
check(!BlueEvolutionScaling.legitimate_trainer_form?(Poke.new(:RATICATE,21)),
      "Underlevel Raticate must not bypass 350 BST restriction")
enc=PokemonEncounters.new
BlueEvolutionScaling.install
enc.species=:RATTATA;enc.level=6
upgraded=Array.new(500) {enc.choose_wild_pokemon(:Land)}
raticates=upgraded.select { |s,l| s==:RATICATE }
check(raticates.length.between?(70,230),"Wild mixture changed to all-base/all-evolved")
check(raticates.all? { |s,l| l==25 },"Evolved wild under natural level threshold")
check(upgraded.any? { |s,l| s==:RATTATA && l==6 },"Original land slot species lost")
enc.species=:EEVEE
check(Array.new(30){enc.choose_wild_pokemon(:Land)}.all?{|s,l|s==:EEVEE},
      "Branching Eevee corrupted in wild encounters")
puts "PASS: native evolution rules, 3-stage families, trainer grace, stone/trade/happiness, wild mixture, special forms"
