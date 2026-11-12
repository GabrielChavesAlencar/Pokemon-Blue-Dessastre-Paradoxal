# F5 scene contract with fake audio objects; no Game.exe, save, or real sound.
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
Map=Struct.new(:map_id)
SystemBGM=Struct.new(:playing_bgm) do
  def getPlayingBGM; playing_bgm; end
end
class Object
  private
  def pbBGMPlay(audio,*args)
    file=audio.is_a?(RPG::AudioFile) ? audio : RPG::AudioFile.new(audio,*args)
    $bgm_calls << file.name
    $game_system.playing_bgm=file
  end
  def pbBGMStop(*args)
    $bgm_calls << ':STOP'
    $game_system.playing_bgm=nil
  end
end
class FakeTitle
  attr_reader :native_calls
  def initialize; @native_calls=0; end
  def playBGM
    @native_calls+=1
    pbBGMPlay(RPG::AudioFile.new('default Decades title',91,101))
  end
end
def check(label,result)
  raise "FAIL: #{label}" unless result
  puts "PASS: #{label}"
end
load File.expand_path('../scripts/music/BlueMusic.rb',__dir__)
load File.expand_path('../scripts/battle_polish/Title.rb',__dir__)
Object.prepend(BlueMusic::EvolutionSceneAudio)
FakeTitle.prepend(BlueParadoxTitle::Music)

Dir.mktmpdir('kanto-f5-') do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p('Data')
    FileUtils.mkdir_p('Audio/BGM/Kanto')
    FileUtils.mkdir_p('Audio/BGM/BlueRandom/gym')
    File.write("Audio/BGM/#{BlueParadoxTitle::TRACK}",'test-only synthetic bytes')
    names={'pilot_title'=>'title','oak_talk'=>'oak','rival_appears'=>'rival',
           'evolution'=>'evolution','hall_of_fame'=>'hall'}
    names.each_value { |x| File.write("Audio/BGM/Kanto/#{x}.mp3",'synthetic') }
    entries=["BLUE_KANTO_MUSIC_V1\tKANTO\t#{'f'*64}"]
    142.times do |i|
      symbol=(i==0 ? 'PALLET_TOWN' : (i==1 ? 'OAK_LAB' : "MAP_#{i}"))
      entries << "SCOPE\t#{705+i}\t#{symbol}\t#{i==2 ? 1 : 0}"
    end
    names.each { |key,name| entries << "SCENE\t#{key}\tKanto/#{name}.mp3\t80\t100" }
    File.write('Data/blue-kanto-music.txt',entries.join("\n")+"\n")
    $game_map=Map.new(705)
    $game_system=SystemBGM.new(RPG::AudioFile.new('original/route.mp3',57,93))
    $PokemonGlobal=Object.new
    $bgm_calls=[]
    BlueRegionalPolicy.region='DECADES'
    count=0
    BlueMusic.with_kanto_scene('oak_talk') { count+=1 }
    check('Decades scene never changes BGM', count==1 && $bgm_calls.empty?)
    title=FakeTitle.new
    title.playBGM
    check('Decades title retains existing music',
          $bgm_calls.last==BlueParadoxTitle::TRACK && title.native_calls==0)
    $bgm_calls.clear
    BlueRegionalPolicy.region='KANTO'
    check('Only allowed scene has valid audio',
          BlueMusic.kanto_scene_audio('oak_talk').name=='Kanto/oak.mp3')
    check('Unverified Kanto credits are absent',
          BlueMusic.kanto_scene_audio('credits').nil?)
    before=RPG::AudioFile.new('original/route.mp3',57,93)
    $game_system.playing_bgm=before
    BlueMusic.with_kanto_scene('oak_talk') do
      check('Oak scene plays only during actual story block',
            $game_system.playing_bgm.name=='Kanto/oak.mp3')
    end
    check('Exact previous BGM volume/pitch restored',
          $bgm_calls.last(2)==['Kanto/oak.mp3','original/route.mp3'] &&
          $game_system.playing_bgm.equal?(before))
    # Proven F6 defect fix: a silent native map must play a dialogue cue and
    # become silent again, even if there was no old music to restore.
    $bgm_calls.clear
    $game_system.playing_bgm=nil
    BlueMusic.with_kanto_scene('oak_talk') do
      check('Silent map still receives its scene', $game_system.playing_bgm.name=='Kanto/oak.mp3')
    end
    check('After scene, a previously silent map is silent again',
          $bgm_calls==['Kanto/oak.mp3', ':STOP'] && $game_system.playing_bgm.nil?)
    # The ensure block must restore audio even when a scene raises; no
    # permanently stuck Oak/rival music is allowed.
    previous=RPG::AudioFile.new('custom/previous.mp3',37,114)
    $game_system.playing_bgm=previous
    $bgm_calls.clear
    begin
      BlueMusic.with_kanto_scene('oak_talk') { raise 'synthetic story failure' }
    rescue RuntimeError => error
      check('Story error is propagated',error.message=='synthetic story failure')
    end
    check('Previous BGM volume/pitch restored after story error',
          $game_system.playing_bgm.equal?(previous) &&
          $bgm_calls==['Kanto/oak.mp3','custom/previous.mp3'])
    # Nested scenes restore their immediate predecessor, then original route.
    $bgm_calls.clear
    BlueMusic.with_kanto_scene('oak_talk') do
      BlueMusic.with_kanto_scene('rival_appears') do
        check('Nested scene starts rival track',
              $game_system.playing_bgm.name=='Kanto/rival.mp3')
      end
      check('Nested scene returns to Oak', $game_system.playing_bgm.name=='Kanto/oak.mp3')
    end
    check('Outer scene restores original after nested cue',
          $game_system.playing_bgm.equal?(previous) &&
          $bgm_calls==['Kanto/oak.mp3','Kanto/rival.mp3','Kanto/oak.mp3','custom/previous.mp3'])
    $bgm_calls.clear
    BlueMusic.with_kanto_scene('rival_appears') do
      # A battle changing map before the hook exits must not resurrect old BGM.
      $game_map.map_id=706
    end
    check('Map transition cannot restore old map BGM',
          $bgm_calls==['Kanto/rival.mp3'])
    $game_map.map_id=705
    $bgm_calls.clear
    BlueMusic.with_kanto_scene('rival_appears') do
      BlueRegionalPolicy.region='DECADES'
    end
    check('Region transfer cannot overwrite Decades music',
          $bgm_calls==['Kanto/rival.mp3'])
    BlueRegionalPolicy.region='KANTO'
    $bgm_calls.clear
    BlueMusic.with_kanto_scene('oak_talk') do
      $game_system.playing_bgm=RPG::AudioFile.new('event-special.mp3')
    end
    check('A new event-specific soundtrack remains prioritized',
          $bgm_calls==['Kanto/oak.mp3'] &&
          $game_system.playing_bgm.name=='event-special.mp3')
    $bgm_calls.clear
    $game_map.map_id=707
    BlueMusic.with_kanto_scene('oak_talk') { }
    check('Preview map cannot play story music',$bgm_calls.empty?)
    $game_map.map_id=999
    BlueMusic.with_kanto_scene('rival_appears') { }
    check('Non-Kanto map IDs cannot play story music',$bgm_calls.empty?)
    $game_map.map_id=705
    $game_system.playing_bgm=RPG::AudioFile.new('route-restored.mp3')
    Object.new.send(:pbBGMPlay,'Evolution')
    check('Native evolution BGM replaced, not doubled',
          $bgm_calls==['Kanto/evolution.mp3'])
    $bgm_calls.clear
    Object.new.send(:pbBGMPlay,'Another BGM')
    check('Unrelated native BGM stays native',$bgm_calls==['Another BGM'])
    $bgm_calls.clear
    File.write('Kanto pilot.json','{"maps":{}}')
    title2=FakeTitle.new
    title2.playBGM
    check('Isolated title has scoped Kanto theme',
          $bgm_calls==['Kanto/title.mp3'] && title2.native_calls==0)
    $bgm_calls.clear
    File.write('Data/blue-kanto-install.json','{}')
    FakeTitle.new.playBGM
    check('Main integrated game cannot use pilot title theme',
          $bgm_calls==[BlueParadoxTitle::TRACK])
    File.unlink('Data/blue-kanto-install.json')
    File.unlink('Kanto pilot.json')
    File.unlink('Audio/BGM/Kanto/oak.mp3')
    $bgm_calls.clear
    BlueMusic.with_kanto_scene('oak_talk') { }
    check('Missing regional scene MP3 fails closed',$bgm_calls.empty?)
    File.write('Data/blue-kanto-music.txt','corrupt')
    check('Invalid manifest fails closed',
          BlueMusic.kanto_scene_audio('hall_of_fame').nil?)
    puts 'KANTO_MUSIC_SCENES_PHASE_5=PASS_STATIC_RUNTIME'
  end
end
