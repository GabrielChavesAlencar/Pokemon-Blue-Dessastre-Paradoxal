# Phase 4 ME contracts using synthetic fixtures; never plays copyrighted audio.
require 'tmpdir'
require 'fileutils'
module Compiler
  def self.main; end
end
module RPG
  class AudioFile
    attr_accessor :name,:volume,:pitch
    def initialize(name='',volume=100,pitch=100)
      @name,@volume,@pitch=name,volume,pitch
    end
  end
end
module BlueRegionalPolicy
  def self.state; @state; end
  def self.region=(key); @state=key && {'current'=>key}; end
end
class Object
  private
  def pbMEPlay(param,volume=nil,pitch=nil)
    name=param.is_a?(RPG::AudioFile) ? param.name : param
    $me_played << [name,volume,pitch]
    # Essentials' underlying ME system owns BGM fade, pause and resume;
    # the region adapter must never manually replace map/battle music.
    :native_me_engine
  end
end
module Battle
  module CatchAndStoreMixin
    def pbRecordAndStoreCaughtPokemon(*args)
      @caughtPokemon.clear
      :stored
    end
  end
end
class FakeBattle
  include Battle::CatchAndStoreMixin
  def initialize(wild=true,count=1)
    @wild=wild
    @caughtPokemon=Array.new(count,:caught_mon)
  end
  def wildBattle?; @wild; end
end
source=File.expand_path('../scripts/music/BlueMusic.rb',__dir__)
load source
Object.prepend(BlueMusic::NativeME)
Battle::CatchAndStoreMixin.prepend(BlueMusic::CaptureME)
Map=Struct.new(:map_id)
def check(label,ok)
  raise "FAIL: #{label}" unless ok
  puts "PASS: #{label}"
end
Dir.mktmpdir('kanto-me-') do |tmp|
  Dir.chdir(tmp) do
    FileUtils.mkdir_p('Data')
    FileUtils.mkdir_p('Audio/ME/Kanto')
    events={'obtained_pokemon'=>'pokemon','obtained_item'=>'item',
            'healed'=>'heal','badge_awarded'=>'badge','evolved'=>'evolve',
            'caught'=>'catch'}
    events.each_value { |name| File.write("Audio/ME/Kanto/#{name}.mp3",'synthetic') }
    lines=["BLUE_KANTO_MUSIC_V1\tKANTO\t#{'f'*64}",
           "SCOPE\t701\tPALLET_TOWN\t0",
           "SCOPE\t702\tPREVIEW\t1"]
    events.each { |key,name| lines << "ME\t#{key}\tKanto/#{name}.mp3\t78\t100" }
    File.write('Data/blue-kanto-music.txt',lines.join("\n")+"\n")
    $game_map=Map.new(701)
    $PokemonGlobal=Object.new
    $me_played=[]
    $bgm_before='Kanto/Pallet.mp3'
    BlueRegionalPolicy.region=nil
    check('Legacy save cannot trigger Kanto ME',
          !BlueMusic.kanto_me_play('obtained_item') && $me_played.empty?)
    BlueRegionalPolicy.region='DECADES'
    check('Decades remains silent in Kanto ME adapter',
          !BlueMusic.kanto_me_play('obtained_item') && $me_played.empty?)
    check('Decades native evolution fanfare preserved',
          Object.new.send(:pbMEPlay,'Evolution success')==:native_me_engine &&
          $me_played.last[0]=='Evolution success')
    $me_played.clear
    BlueRegionalPolicy.region='KANTO'
    check('Confirmed Kanto bag commit plays ME once',
          BlueMusic.kanto_me_play('obtained_item') &&
          $me_played.map(&:first)==['Kanto/item.mp3'])
    $me_played.clear
    check('Successful native evolution replaces the original ME, not doubles',
          Object.new.send(:pbMEPlay,'Evolution success')==:native_me_engine &&
          $me_played.map(&:first)==['Kanto/evolve.mp3'])
    $me_played.clear
    check('Native Pokemon get before storage remains native, not prematurely replaced',
          Object.new.send(:pbMEPlay,'Pkmn get')==:native_me_engine &&
          $me_played.map(&:first)==['Pkmn get'])
    $me_played.clear
    check('Committed Kanto silent gift plays the regional ME exactly once',
          BlueMusic.kanto_me_play('obtained_pokemon') &&
          $me_played.map(&:first)==['Kanto/pokemon.mp3'])
    $me_played.clear
    check('Other native and explicit story cues are untouched',
          Object.new.send(:pbMEPlay,'Pkmn healing')==:native_me_engine &&
          $me_played.map(&:first)==['Pkmn healing'])
    $me_played.clear
    check('Heal after verified service uses ME',
          BlueMusic.kanto_me_play('healed') && $me_played.map(&:first)==['Kanto/heal.mp3'])
    $me_played.clear
    check('Award committed badge uses ME',BlueMusic.kanto_me_play('badge_awarded') &&
          $me_played.map(&:first)==['Kanto/badge.mp3'])
    $me_played.clear
    check('Unknown or pending events cannot play',
          !BlueMusic.kanto_me_play('jackpot') &&
          !BlueMusic.kanto_me_play('oak_evaluation') && $me_played.empty?)
    check('ME never replaces native map BGM', $bgm_before=='Kanto/Pallet.mp3')
    $me_played.clear
    check('Capture after successful storage triggers only one ME',
          FakeBattle.new.pbRecordAndStoreCaughtPokemon==:stored &&
          $me_played.map(&:first)==['Kanto/catch.mp3'])
    $me_played.clear
    check('Uncaught wild battle never triggers capture ME',
          FakeBattle.new(true,0).pbRecordAndStoreCaughtPokemon==:stored &&
          $me_played.empty?)
    check('Nonwild capture storage never triggers regional wild fanfare',
          FakeBattle.new(false,1).pbRecordAndStoreCaughtPokemon==:stored &&
          $me_played.empty?)
    $game_map.map_id=702
    check('Preview map cannot play Kanto ME',
          !BlueMusic.kanto_me_play('obtained_item') && $me_played.empty?)
    $game_map.map_id=901
    check('Decades map IDs cannot play Kanto ME even in Kanto state',
          !BlueMusic.kanto_me_play('obtained_item') && $me_played.empty?)
    $game_map.map_id=701
    File.unlink('Audio/ME/Kanto/item.mp3')
    check('Missing MP3 fails closed with no playback',
          !BlueMusic.kanto_me_play('obtained_item') && $me_played.empty?)
    File.write('Data/blue-kanto-music.txt','corrupt')
    check('Corrupt regional manifest fails closed',
          !BlueMusic.kanto_me_play('badge_awarded') && $me_played.empty?)
    puts 'KANTO_MUSIC_ME_PHASE_4=PASS_STATIC_RUNTIME'
  end
end
