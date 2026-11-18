# J05: isolated test of real authored handlers, starter transaction and saves.
# Fake Essentials services ONLY. No Game.exe, files outside mkdtemp, saves,
# donor assets, map IDs, ROMs or any claims about native QA.
require "tmpdir"

class J05Global
  attr_accessor :blue_regions
end

class J05Player
  attr_reader :party, :heals
  def initialize
    @party=[]
    @heals=0
    @has_pokedex=false
    @dex_mode=:normal
  end
  attr_accessor :dex_mode
  def has_pokedex
    @has_pokedex
  end
  def has_pokedex=(value)
    case @dex_mode
    when :raise_before
      raise "native dex unavailable"
    when :ignore
      return value
    when :raise_after_once
      @has_pokedex=value
      @dex_mode=:normal
      raise "native dex interrupted"
    end
    @has_pokedex=value
  end
  def heal_party
    @heals+=1
  end
end

module GameData
  module Trainer
    @entries={
      0=>[{:species=>:CHIMCHAR,:level=>5}],
      1=>[{:species=>:PIPLUP,:level=>5}],
      2=>[{:species=>:TURTWIG,:level=>5}],
    }
    class << self
      attr_accessor :entries
      def get(type,name,version)
        return nil unless type==:BLUE_SINNOH_RIVAL && name=="Barry"
        value=@entries[version]
        value && Struct.new(:pokemon).new(value)
      end
    end
  end
end

module TrainerBattle
  @history=[]
  class << self
    attr_reader :history
    def start(*args)
      @history<<args
      raise "uncompiled native encounter" if $battle_mode==:raise
      $battle_result
    end
  end
end

$messages=[]
$rules=[]
def _INTL(message,*_args);message;end
def pbMessage(message);$messages<<message;end
def setBattleRule(value);$rules<<value;end

def check(cond,message)
  raise "J05_REGRESSION: #{message}" unless cond
end

$grant_mode=:normal
def pbAddPokemonSilent(species,level)
  case $grant_mode
  when :fail
    return false
  when :append_false
    $player.party<<[species,level]
    return false
  when :wrong_species
    $player.party<<[:EEVEE,level]
  when :wrong_level
    $player.party<<[species,9]
  when :switch_region
    $player.party<<[species,level]
    $PokemonGlobal.blue_regions["current"]="HOENN"
  when :switch_player
    old=$player
    old.party<<[species,level]
    $player=J05Player.new
  when :reenter
    $player.party<<[species,level]
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
          "reentrant ball duplicated a starter")
  when :raise_after
    $player.party<<[species,level]
    raise "engine grant interrupted"
  else
    $player.party<<[species,level]
  end
  true
end

def fresh(region="SINNOH",initial="SINNOH")
  $PokemonGlobal=J05Global.new
  $PokemonGlobal.blue_regions={
    "version"=>1,"current"=>region,"initial"=>initial
  }
  $player=J05Player.new
  $grant_mode=:normal
  $battle_mode=:normal
  $battle_result=nil
  $messages.clear
  $rules.clear
  TrainerBattle.history.clear
  GameData::Trainer.entries={
    0=>[{:species=>:CHIMCHAR,:level=>5}],
    1=>[{:species=>:PIPLUP,:level=>5}],
    2=>[{:species=>:TURTWIG,:level=>5}],
  }
end

def intro
  check(BlueSinnohPilot.mother,"mother handler not implemented")
  check(BlueSinnohPilot.barry_intro,"Barry intro not implemented")
  check(BlueSinnohPilot.rowan_briefcase,"Rowan briefcase not implemented")
end

load File.expand_path(ARGV.fetch(0))
Dir.mktmpdir("sinnoh-j05-owned-runtime-") do |tmp|
  Dir.chdir(tmp) do
    Dir.mkdir("Data")

    # 1. Bad region and inconsistent save snapshots never mutate anything.
    %w[KANTO JOHTO HOENN DECADES].each do |region|
      fresh(region,region)
      snapshot=Marshal.dump($PokemonGlobal.blue_regions)
      check(!BlueSinnohPilot.mother,"foreign mother active #{region}")
      check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),"foreign ball #{region}")
      check(!BlueSinnohPilot.barry_rival,"foreign Barry #{region}")
      check(!BlueSinnohPilot.rowan_pokedex,"foreign Rowan #{region}")
      check(Marshal.dump($PokemonGlobal.blue_regions)==snapshot,"foreign save mutated")
      check($player.party.empty?,"foreign region got starter")
    end
    fresh("SINNOH","KANTO")
    check(!BlueSinnohPilot.mother,"foreign initial bypassed gate")

    # 2. Fail closed when no actual engine grant occurred; rollback any new
    # party member and keep the same scoped flag Hash without fabricated save.
    [:fail,:append_false,:wrong_species,:wrong_level,:switch_region,
     :switch_player,:raise_after].each do |mode|
      fresh
      intro
      state=$PokemonGlobal.blue_regions
      player=$player
      flags=state["sinnoh_pilot"]
      before=Marshal.dump(flags)
      $grant_mode=mode
      check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
            "#{mode} accepted unverified starter")
      check(flags.equal?(state["sinnoh_pilot"]),"#{mode} replaced story flags")
      check(Marshal.dump(flags)==before,"#{mode} stored failed grant")
      check(player.party.empty?,"#{mode} left duplicated starter in original party")
      check($player.party.empty?,"#{mode} left Pokémon in switched player party")
      state["current"]="SINNOH"
      $player=player
      $grant_mode=:normal
      check(BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
            "#{mode} permanently locked starter after rollback")
      check(player.party==[[:TURTWIG,5]],"#{mode} retry gave extra Pokémon")
    end

    # 3. Full party must not send an untracked starter to PC storage.
    fresh
    intro
    6.times{|i|$player.party<<[:OLD_MON,i+1]}
    flags=Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
          "full party accepted grant without storage transaction")
    check($player.party.size==6,"full party was overwritten")
    check(Marshal.dump($PokemonGlobal.blue_regions)==flags,
          "full party save was modified")

    # 4. Reentrant ball, three choices, save/load and regional travel isolation.
    [:TURTWIG,:CHIMCHAR,:PIPLUP].each do |selected|
      fresh
      intro
      $grant_mode=:reenter
      check(BlueSinnohPilot.choose_starter_from_ball(selected),
            "#{selected} could not be granted")
      check($player.party==[[selected,5]], "#{selected} party duplicated")
      check(BlueSinnohPilot.starter==selected, "#{selected} not persisted")
      check(!BlueSinnohPilot.choose_starter_from_ball(selected),
            "#{selected} same ball duplicated starter")
      ([:TURTWIG,:CHIMCHAR,:PIPLUP]-[selected]).each do |other|
        check(!BlueSinnohPilot.choose_starter_from_ball(other),
              "#{selected} allowed second ball #{other}")
      end
      saved=Marshal.dump($PokemonGlobal.blue_regions)
      $PokemonGlobal.blue_regions=Marshal.load(saved)
      check(BlueSinnohPilot.starter==selected,"#{selected} lost on save reload")
      check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),
            "#{selected} permitted another starter after reload")
      %w[KANTO JOHTO HOENN DECADES].each do |region|
        $PokemonGlobal.blue_regions["current"]=region
        snap=Marshal.dump($PokemonGlobal.blue_regions)
        check(!BlueSinnohPilot.choose_starter_from_ball(:CHIMCHAR),
              "cross region grant after #{selected} save")
        check(Marshal.dump($PokemonGlobal.blue_regions)==snap,
              "foreign save changed while traveling #{region}")
      end
      $PokemonGlobal.blue_regions["current"]="SINNOH"
      check(BlueSinnohPilot.starter==selected,
            "Sinnoh checkpoint lost after regional round-trip")
    end

    # 5. Barry: all three official opponent mappings, never arbitrary teams.
    [:TURTWIG,:CHIMCHAR,:PIPLUP].each do |selected|
      fresh
      intro
      check(BlueSinnohPilot.choose_starter_from_ball(selected),
            "failed starter before Barry")
      check(BlueSinnohPilot.all_rival_versions_valid?,
            "all three authored Barry teams not recognized")
      check(!BlueSinnohPilot.barry_rival,"Barry triggered without native marker")
      File.write(BlueSinnohPilot::RIVAL_READY,BlueSinnohPilot::RIVAL_PROOF)
      begin
        version=BlueSinnohPilot.rival_version
        expected=BlueSinnohPilot.rival_species
        wrong=(version+1)%3
        saved=GameData::Trainer.entries[wrong]
        GameData::Trainer.entries.delete(wrong)
        check(!BlueSinnohPilot.barry_rival,
              "missing other Barry variant allowed battle")
        check(TrainerBattle.history.empty?,"uncompiled trainer triggered")
        GameData::Trainer.entries[wrong]=saved
        bad=GameData::Trainer.entries[version]
        GameData::Trainer.entries[version]=[{:species=>:RATTATA,:level=>5}]
        check(!BlueSinnohPilot.barry_rival,"wrong rival species allowed")
        GameData::Trainer.entries[version]=[{:species=>expected,:level=>7}]
        check(!BlueSinnohPilot.barry_rival,"wrong seed level allowed")
        GameData::Trainer.entries[version]=bad
        $battle_mode=:raise
        check(!BlueSinnohPilot.barry_rival,"engine failure committed Barry")
        check(!BlueSinnohPilot.rival_fought?,"engine failure stored battle flag")
        $battle_mode=:normal
        $battle_result=nil
        check(!BlueSinnohPilot.barry_rival,"nil battle result accepted")
        check(!BlueSinnohPilot.rival_fought?,"nil battle flag persisted")
        $battle_result=false
        check(BlueSinnohPilot.barry_rival,
              "canLose defeat not treated as completed battle")
        check(BlueSinnohPilot.rival_fought?,"confirmed battle flag missing")
        check($player.heals==1,"confirmed battle did not heal player")
        check(!BlueSinnohPilot.barry_rival,"Barry battle replayed after flag")
        check(TrainerBattle.history[-1]==[:BLUE_SINNOH_RIVAL,"Barry",version],
              "Barry started wrong version")
      ensure
        File.delete(BlueSinnohPilot::RIVAL_READY) if File.file?(BlueSinnohPilot::RIVAL_READY)
      end
    end

    # 6. Dex flag must be reverted if the engine's setter rejects or raises.
    [:raise_before,:ignore,:raise_after_once].each do |mode|
      fresh
      intro
      check(BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),"dex prep starter")
      saved=BlueSinnohPilot.progress
      saved["rival_fought"]=true
      check(BlueSinnohPilot.valid_flags?(saved),"dex fixture invalid")
      $player.dex_mode=mode
      before=Marshal.dump(saved)
      check(!BlueSinnohPilot.rowan_pokedex,"#{mode} accepted failed Dex setter")
      check(Marshal.dump(saved)==before,"#{mode} persisted a failed Dex save")
      $player.dex_mode=:normal
      check(BlueSinnohPilot.rowan_pokedex,"#{mode} blocked valid Dex retry")
      check(saved["pokedex_received"]==true && $player.has_pokedex,
            "#{mode} valid Dex did not persist")
      check(!BlueSinnohPilot.rowan_pokedex,"#{mode} duplicated Dex")
    end

    # 7. Corrupted or malicious save flags are read-only and fail closed.
    fresh
    $PokemonGlobal.blue_regions["sinnoh_pilot"]={
      "mother_intro"=>true,"barry_intro"=>true,
      "rowan_briefcase_seen"=>true,
      "starter"=>"NOT_A_REAL_STARTER","starter_received"=>true
    }
    saved=Marshal.dump($PokemonGlobal.blue_regions)
    check(BlueSinnohPilot.progress.nil?,"corrupt starter loaded")
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "corrupt starter accepted physical ball")
    check(Marshal.dump($PokemonGlobal.blue_regions)==saved,
          "corrupt save overwritten")
  end
end
puts "SINNOH_J05_SCOPED_ATOMIC_STARTER_BARRY_DEX_SAVE_OFFLINE_OK"
