# S13 isolated pilot + read-only intro contract; no Game.exe/JoiPlay.
require 'json'
class S13Global
  attr_accessor :blue_regions
end
class S13Player
  attr_accessor :has_pokedex
  attr_reader :party,:heals
  def initialize
    @has_pokedex=false
    @party=[]
    @heals=0
  end
  def heal_party;@heals+=1;end
end
module GameData
  module Trainer
    @teams={
      0=>[{:species=>:CHIMCHAR,:level=>5}],
      1=>[{:species=>:PIPLUP,:level=>5}],
      2=>[{:species=>:TURTWIG,:level=>5}]
    }
    def self.get(type,name,version)
      return nil unless type==:BLUE_SINNOH_RIVAL && name=="Barry"
      team=@teams[version]
      team && Struct.new(:pokemon).new(team)
    end
  end
end
module TrainerBattle
  @calls=[]
  def self.calls;@calls;end
  def self.start(*args)
    @calls << args
    $battle_result
  end
end
def _INTL(x,*_args);x;end
def pbMessage(x);$messages<<x;end
def pbAddPokemonSilent(species,level)
  $player.party<<[species,level]
  true
end
def setBattleRule(rule);$rules<<rule;end
def check(ok,why)
  raise "SINNOH_S13_RUBY: #{why}" unless ok
end
load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
manifest=JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))
check(manifest['steps'].length==6,'missing checkpoints')
check(manifest['native_maps_compiled']==0,'invented native maps')
check(BlueSinnohIntroContracts::VERIFIED_NATIVE_HANDLERS.empty?,'installed callback spoof')
def fresh(region='SINNOH',initial='SINNOH')
  $PokemonGlobal=S13Global.new
  $PokemonGlobal.blue_regions={'version'=>1,'current'=>region,'initial'=>initial}
  $player=S13Player.new
  $messages=[];$rules=[];$battle_result=nil
  TrainerBattle.calls.clear
end
fresh
s=$PokemonGlobal.blue_regions
check(BlueSinnohIntroContracts.preview(s)==:native_events_unverified,'first stage unexpectedly enabled')
check(!BlueSinnohPilot.commit_flag('pokedex_received'),'early pokedex direct commit')
check(!BlueSinnohPilot.commit_flag('rival_fought'),'battle direct commit')
check(!BlueSinnohPilot.commit_flag('starter_received'),'starter direct commit')
check(!BlueSinnohPilot.commit_flag('arbitrary'),'unknown flag direct commit')
check(!s.key?('sinnoh_pilot'),'rejected direct commit mutated save')
check(BlueSinnohPilot.mother,'mother not committed')
check(!BlueSinnohPilot.commit_flag('mother_intro'),'repeat mother commit')
check(!BlueSinnohPilot.commit_flag('rowan_briefcase_seen'),'rowan skipped Barry')
check(BlueSinnohPilot.barry_intro,'Barry intro missing')
check(BlueSinnohPilot.rowan_briefcase,'Rowan explanation missing')
check(BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),'physical Turtwig missing')
check(BlueSinnohIntroContracts.expected_starter_opponent('TURTWIG')=='CHIMCHAR','Barry Turtwig counter wrong')
check(BlueSinnohIntroContracts.expected_starter_opponent('CHIMCHAR')=='PIPLUP','Barry Chimchar counter wrong')
check(BlueSinnohIntroContracts.expected_starter_opponent('PIPLUP')=='TURTWIG','Barry Piplup counter wrong')
check(BlueSinnohIntroContracts.expected_starter_opponent('PIKACHU').nil?,'invalid opponent')
check(!BlueSinnohPilot.commit_flag('rival_fought'),'direct rival event bypassed')
check(!BlueSinnohPilot.commit_flag('pokedex_received'),'direct dex event bypassed')
check(!BlueSinnohPilot.rowan_pokedex,'early dex awarded')
check(!$player.has_pokedex,'early dex changed player')
check(!BlueSinnohIntroContracts.native_ready?(s,'mother_intro','forged'),'fake callback trusted')
check(BlueSinnohIntroContracts.preview(s)==:native_events_unverified,'pilot allows unverified event')
# This marker is only a fixture, created in an isolated temp cwd.
require 'tmpdir'
Dir.mktmpdir('s13-rival-') do |dir|
  Dir.chdir(dir) do
    Dir.mkdir('Data')
    File.write(BlueSinnohPilot::RIVAL_READY,BlueSinnohPilot::RIVAL_PROOF)
    check(!BlueSinnohPilot.barry_rival,'nil battle advanced')
    check(!$player.has_pokedex,'nil battle granted dex')
    $battle_result=false
    check(BlueSinnohPilot.barry_rival,'completed canLose loss not recorded')
    check(TrainerBattle.calls.length==2,'battle was not called twice')
    check($player.heals==1,'player not healed after battle')
    check(BlueSinnohPilot.rowan_pokedex,'Rowan Dex did not complete')
    check($player.has_pokedex,'Dex engine field not updated')
    check(!BlueSinnohPilot.commit_flag('pokedex_received'),'duplicate pokedex flag')
  end
end
check(BlueSinnohIntroContracts.preview(s)==:complete_offline_only,'final flags not recognized')
check(s['sinnoh_pilot']['pokedex_received']==true,'save dex flag missing')
check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),'starter duplicated')
snapshot=Marshal.dump(s)
%w[KANTO JOHTO HOENN DECADES].each do |region|
  s['current']=region
  before=Marshal.dump(s)
  check(BlueSinnohIntroContracts.preview(s)==:wrong_region,'foreign region preview')
  check(!BlueSinnohPilot.mother,'foreign region ran mother')
  check(!BlueSinnohPilot.commit_flag('mother_intro'),'foreign region wrote checkpoint')
  check(Marshal.dump(s)==before,'foreign region save modified')
end
s['current']='SINNOH'
s['sinnoh_pilot']['unexpected_flag']=true
check(BlueSinnohIntroContracts.preview(s)==:invalid_checkpoint,'extra flag accepted')
check(BlueSinnohPilot.progress.nil?,'corrupted flags exposed')
check(!BlueSinnohPilot.rowan_pokedex,'corrupted flag advanced story')
puts 'SINNOH_S13_INTRO_RUNTIME_OK_OFFLINE_ONLY'
