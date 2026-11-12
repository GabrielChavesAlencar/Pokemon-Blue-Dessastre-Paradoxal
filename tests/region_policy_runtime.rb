# Standalone Ruby v21.1-style regression, no game assets or player saves.
require "tmpdir"
def assert(value, label)
  raise label unless value
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
module BlueRegionStart
  def self.kanto_spawn; [300,28,14]; end
end
module GameData
  module Species
    def self.get(id)
      Struct.new(:flags).new([])
    end
  end
end

SpeciesInfo = Struct.new(:flags, :form, :species)
class Pokemon
  attr_reader :species
  def initialize(species, level=5, flags=nil)
    @species=species
    @flags=flags || (species==:MEWTWO ? ["Legendary"] : species==:IRONTEST ? ["Paradox"] : [])
  end
  def species_data
    SpeciesInfo.new(@flags,0,@species)
  end
  def record_first_moves; end
  def name; @species.to_s; end
  def egg?; false; end
  def fainted?; false; end
end
class Player
  attr_accessor :party,:badges,:pokedex
  def initialize
    @party=[]
    @badges=Array.new(25,false)
    @pokedex=Object.new
    def @pokedex.set_seen(*);end
    def @pokedex.set_owned(*);end
    def @pokedex.register(*);end
  end
end
class PokemonStorage
  attr_accessor :party
  def initialize; @boxes={}; end
  def maxBoxes; 2; end
  def maxPokemon(box); 4; end
  def [](box,slot)
    box==-1 ? $player.party[slot] : @boxes[[box,slot]]
  end
  def []=(box,slot,pkmn)
    box==-1 ? $player.party[slot]=pkmn : @boxes[[box,slot]]=pkmn
  end
  def full?; @boxes.size>=8; end
  def pbStoreCaught(pkmn)
    2.times do |box|
      4.times do |i|
        if self[box,i].nil?
          self[box,i]=pkmn
          return box
        end
      end
    end
    -1
  end
  def pbMoveCaughtToParty(pkmn)
    $player.party << pkmn
    true
  end
  def pbCopy(dst,dstslot,src,srcslot)
    self[dst,dstslot]=self[src,srcslot]
    true
  end
end
class PokemonStorageScreen
  def pbWithdraw(*);true;end
  def pbPlace(*);true;end
  def pbSwap(*);true;end
end
class Battle
  module CatchAndStoreMixin
    def pbStorePokemon(pkmn)
      $player.party << pkmn
      true
    end
  end
end
class FakeCatchBattle
  include Battle::CatchAndStoreMixin
  def pbDisplayPaused(*);end
end
module HiddenMoveHandlers
  def self.triggerCanUseMove(move,pkmn,showmsg)
    pbCheckHiddenMoveBadge(4, showmsg)
  end
  def self.triggerUseMove(move,pkmn)
    pbCheckHiddenMoveBadge(4, false)
  end
end
module MenuHandlers
  def self.add(*); end
end
module EventHandlers
  def self.add(*); end
end
def pbCheckHiddenMoveBadge(badge=-1,showmsg=true); false; end
def pbRgssExists?(path); File.file?(path); end
def pbMessage(*);end
def _INTL(message,*args)
  args.each_with_index { |arg,i| message=message.gsub("{#{i+1}}",arg.to_s) }
  message
end
def pbAddPokemonSilent(pkmn,level=1,see_form=true)
  $player.party << (pkmn.is_a?(Pokemon) ? pkmn : Pokemon.new(pkmn,level))
  true
end
def pbAddPokemon(pkmn,level=1,see_form=true)
  pbAddPokemonSilent(pkmn,level,see_form)
end
def pbAddToParty(pkmn,level=1,see_form=true)
  pbAddPokemonSilent(pkmn,level,see_form)
end
def pbAddToPartySilent(pkmn,level=1,see_form=true)
  pbAddPokemonSilent(pkmn,level,see_form)
end

require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)
BlueRegionalPolicy.install

Dir.mktmpdir("blue-regional-policy-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    $player=Player.new
    $PokemonGlobal=PokemonGlobalMetadata.new
    $PokemonStorage=PokemonStorage.new
    $game_switches=Hash.new(false)
    special=Pokemon.new(:MEWTWO)
    paradox=Pokemon.new(:IRONTEST)
    normal=Pokemon.new(:PIDGEY)
    # Codex finding: no Kanto installed means NO regional PC policy.
    assert(!BlueRegionalPolicy.restricted?(special),"Legacy Decades PC locked without Kanto")
    File.write("Data/blue-kanto-install.json", "{}")
    File.write("Data/Map300.rxdata", "marker")
    $PokemonGlobal.blue_regions=BlueRegions.new_state("DECADES")
    assert(!BlueRegionalPolicy.restricted?(special),"Old Decades save locked after Kanto installation")
    assert(pbAddPokemonSilent(special),"Legacy Decades gift unavailable")
    assert($player.party.include?(special),"Legacy Decades gift was wrongly auto-boxed")
    $player.party.clear

    $PokemonGlobal.blue_regions=BlueRegions.new_state("KANTO")
    assert(BlueRegionalPolicy.restricted?(special),"Kanto should lock Legendary")
    assert(BlueRegionalPolicy.restricted?(paradox),"Kanto should lock Paradox")
    assert(!BlueRegionalPolicy.restricted?(normal),"Kanto should allow normal Pokémon")
    assert(!HiddenMoveHandlers.triggerCanUseMove(:FLASH,normal,true),"Flash allowed without Boulder")
    assert(BlueRegions.award($PokemonGlobal.blue_regions,"KANTO","BOULDER"),"Boulder not awarded")
    assert(!BlueRegions.award($PokemonGlobal.blue_regions,"KANTO","BOULDER"),"Boulder awarded twice")
    assert(HiddenMoveHandlers.triggerCanUseMove(:FLASH,normal,true),"Boulder should allow Flash")
    assert(!HiddenMoveHandlers.triggerCanUseMove(:SURF,normal,true),"Surf allowed without Soul")
    assert(BlueRegions.award($PokemonGlobal.blue_regions,"KANTO","SOUL"),"Soul not awarded")
    assert(HiddenMoveHandlers.triggerUseMove(:SURF,normal),"Surf still blocked by native Decades badge")

    assert(pbAddPokemonSilent(special),"Special gift failed")
    assert($player.party.empty?,"Special gift entered Kanto party")
    assert($PokemonStorage[0,0]==special,"Special gift not sent to box")
    assert(!($PokemonStorage.pbMoveCaughtToParty(paradox)),"Direct party move bypassed")
    assert(!$PokemonStorage.pbCopy(-1,0,0,0),"Box-to-party bypassed")
    assert(!$PokemonStorage.send(:[]=,-1,0,special),"Direct party assignment bypassed")
    assert($player.party.empty?,"Direct PC bypass entered party")

    $player.party << normal
    $player.party << paradox
    assert(BlueRegionalPolicy.auto_deposit,"Safe auto-deposit failed")
    assert($player.party==[normal],"Common Pokémon should remain active")
    assert($PokemonStorage[0,1]==paradox,"Paradox not auto-boxed")
    assert(!BlueRegionalPolicy.restricted?(normal),"Normal Pokémon locked")

    stored=$PokemonGlobal.blue_regions
    BlueRegions.info("KANTO")["milestones"].each { |badge| BlueRegions.award(stored,"KANTO",badge) }
    assert(BlueRegions.local_achievements(stored,"KANTO").length==8,"Local badges not unique")
    assert(BlueRegions.crystal_total(stored,3)==11,"Global balance double counted badges")
    assert(!BlueRegionalPolicy.restricted?(special),"Eight Kanto badges did not unlock special")
    assert($PokemonStorage.pbCopy(-1,1,0,0),"Special still blocked after eight badges")
    assert($player.party[1]==special,"Special not withdrawn after unlock")

    # Decades travel must retain native HM logic; region HM rules never apply.
    $PokemonGlobal.blue_regions["current"]="DECADES"
    $PokemonGlobal.blue_regions["travel_history"]=[["KANTO","DECADES"]]
    assert(!HiddenMoveHandlers.triggerCanUseMove(:FLASH,normal,false),"Native Decades HM badge bypassed")
  end
end
puts "Regional PC, gifts, 8-badge unlock, balanced crystals and HM tests OK"
