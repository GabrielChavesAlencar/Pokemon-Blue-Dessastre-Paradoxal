# Ruby-only contract tests for the Kanto BlueMusic region adapter.
# No Game.exe/audio playback here; all sound files are empty test fixtures.
require 'tmpdir'
require 'fileutils'

module Compiler
  def self.main; end
end
module RPG
  class AudioFile
    attr_accessor :name, :volume, :pitch
    def initialize(name='', volume=100, pitch=100)
      @name,@volume,@pitch=name,volume,pitch
    end
    def clone
      self.class.new(@name,@volume,@pitch)
    end
  end
end
# Minimal native engine functions to prove the regional vehicle hooks chain
# safely into super when Decades or a save without a Kanto region is active.
class Object
  private
  def pbAutoplayOnTransition(*args); $vehicle_calls << [:native_transition]; :native; end
  def pbAutoplayOnSave(*args); $vehicle_calls << [:native_save]; :native; end
  def pbMountBike(*args)
    $PokemonGlobal.bicycle=true
    $vehicle_calls << [:native_mount]
    :mounted
  end
  def pbBGMPlay(audio); $vehicle_calls << [:play,audio.name]; end
  def pbCueBGM(audio,fade); $vehicle_calls << [:cue,audio.name,fade]; end
end
module BlueRegions
  def self.active?; true; end
end
module BlueRegionalPolicy
  def self.state; @state; end
  def self.region=(region)
    @state=region && {'current'=>region}
  end
end

source=File.expand_path('../scripts/music/BlueMusic.rb', __dir__)
load source
raise 'Ruby adapter not available' unless BlueMusic.respond_to?(:kanto_audio_for)
module MusicAssert
  def self.check(label, condition)
    raise "FAIL: #{label}" unless condition
    puts "PASS: #{label}"
  end
end

Dir.mktmpdir('blue-kanto-music-runtime-') do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p('Data')
    FileUtils.mkdir_p('Audio/BGM/Kanto')
    File.write('Audio/BGM/Kanto/sample.mp3','synthetic audio')
    File.write('Audio/BGM/manual.mp3','synthetic manual audio')
    File.write('Data/blue-kanto-music.txt',
               "BLUE_KANTO_MUSIC_V1\tKANTO\t#{'f'*64}\n"+
               "SCOPE\t701\tPALLET_TOWN\t0\n"+
               "SCOPE\t702\tOAK_LAB\t0\n"+
               "SCOPE\t703\tPREVIEW\t1\n"+
               "MAP\t701\tKanto/sample.mp3\t72\t101\n"+
               "BATTLE\twild\tKanto/sample.mp3\t91\t99\n")
    $game_map=Struct.new(:map_id).new(701)
    $PokemonGlobal=Struct.new(:nextBattleBGM,:blue_regions,:bicycle,:surfing).new(nil,nil,false,false)
    BlueMusic.instance_variable_set(:@testing,[1,[],[]])
    BlueRegionalPolicy.region=nil
    MusicAssert.check('Legacy save without region never switches sound',
                      BlueMusic.kanto_audio_for('map',701).nil?)
    BlueRegionalPolicy.region='DECADES'
    MusicAssert.check('Decades never switches sound',
                      BlueMusic.kanto_audio_for('map',701).nil?)
    # Isolated pilot has no installed Kanto manifest. It still must use
    # the actual Kanto save and never a Decades or uninitialized save.
    File.write('Kanto pilot.json','{"maps":{}}')
    $PokemonGlobal.blue_regions={'version'=>1,'current'=>'KANTO'}
    MusicAssert.check('Isolated pilot fallback honors its Kanto save',
                      BlueMusic.kanto_region?)
    $PokemonGlobal.blue_regions={'version'=>1,'current'=>'DECADES'}
    MusicAssert.check('Isolated pilot cannot assign music to a Decades save',
                      !BlueMusic.kanto_region?)
    File.delete('Kanto pilot.json')
    $PokemonGlobal.blue_regions=nil
    BlueRegionalPolicy.region='KANTO'
    regional=BlueMusic.kanto_audio_for('map',701)
    MusicAssert.check('Real compiled MapID and volume are used',
                      regional && regional.name=='Kanto/sample.mp3' &&
                      regional.volume==72 && regional.pitch==101)
    MusicAssert.check('FRLG source ID cannot masquerade as compiled MapID',
                      BlueMusic.kanto_audio_for('map',5).nil?)
    MusicAssert.check('Preview and unconfigured Kanto maps remain original',
                      BlueMusic.kanto_audio_for('map',703).nil? &&
                      BlueMusic.kanto_audio_for('map',702).nil?)
    wild=BlueMusic.battle_audio('wild')
    MusicAssert.check('Kanto battle lookup is scoped to compiled map',
                      wild && wild.volume==91 && wild.pitch==99)
    $game_map.map_id=5
    MusicAssert.check('Battle lookup outside Kanto map is inert',
                      BlueMusic.battle_audio('wild').nil?)
    $game_map.map_id=701
    BlueMusic.instance_variable_set(:@testing,[1,
       [['wild','custom','manual.mp3',57,104]],
       [['701','custom','manual.mp3',60,90]]])
    MusicAssert.check('Explicit player battle music wins',
                      BlueMusic.battle_audio('wild').name=='manual.mp3')
    native_map=Struct.new(:autoplay_bgm,:bgm).new(
        false,RPG::AudioFile.new('original decades-style',43,100))
    game_map=Object.new
    game_map.instance_variable_set(:@map_id,701)
    game_map.instance_variable_set(:@map,native_map)
    def game_map.map_id; @map_id; end
    BlueMusic.apply_map(game_map)
    MusicAssert.check('Manual map override wins',native_map.bgm.name=='manual.mp3')
    BlueMusic.instance_variable_set(:@testing,[1,[],[]])
    BlueMusic.apply_map(game_map)
    MusicAssert.check('Kanto default applies only to the current map',
                      native_map.bgm.name=='Kanto/sample.mp3')
    BlueRegionalPolicy.region='DECADES'
    BlueMusic.apply_map(game_map)
    MusicAssert.check('Returning to Decades restores native map music',
                      native_map.bgm.name=='original decades-style' &&
                      native_map.bgm.volume==43 && !native_map.autoplay_bgm)
    # Vehicle themes only when explicitly mounted in Kanto, and after the
    # original Essentials commands have established the vehicle state.
    File.write('Audio/BGM/Kanto/cycling.mp3','synthetic')
    File.write('Audio/BGM/Kanto/surfing.mp3','synthetic')
    File.write('Data/blue-kanto-music.txt',File.read('Data/blue-kanto-music.txt')+
               "TRANSPORT\tbicycle\tKanto/cycling.mp3\t80\t100\n"+
               "TRANSPORT\tsurf\tKanto/surfing.mp3\t75\t100\n")
    $vehicle_calls=[]
    Object.prepend(BlueMusic::VehicleAudio)
    BlueRegionalPolicy.region='DECADES'
    $PokemonGlobal.bicycle=false
    send(:pbMountBike)
    MusicAssert.check('Native Decades bicycle theme preserved',
                      $vehicle_calls==[[:native_mount]])
    BlueRegionalPolicy.region='KANTO'
    $PokemonGlobal.bicycle=false
    $vehicle_calls=[]
    send(:pbMountBike)
    MusicAssert.check('Kanto bicycle only while mounted',
                      $vehicle_calls==[[:native_mount],[:cue,'Kanto/cycling.mp3',0.4]])
    $PokemonGlobal.bicycle=false
    $PokemonGlobal.surfing=true
    $vehicle_calls=[]
    send(:pbAutoplayOnSave)
    MusicAssert.check('Kanto Surf theme on save load',
                      $vehicle_calls==[[:play,'Kanto/surfing.mp3']])
    $game_map.map_id=703
    $vehicle_calls=[]
    send(:pbAutoplayOnTransition)
    MusicAssert.check('Preview map cannot use Kanto transport theme',
                      $vehicle_calls==[[:native_transition]])
    $game_map.map_id=701
    BlueRegionalPolicy.region='DECADES'
    $vehicle_calls=[]
    send(:pbAutoplayOnTransition)
    MusicAssert.check('Region transfer restores Decades vehicle audio',
                      $vehicle_calls==[[:native_transition]])
    BlueRegionalPolicy.region='KANTO'
    $PokemonGlobal.surfing=false
    $vehicle_calls=[]
    send(:pbAutoplayOnSave)
    MusicAssert.check('Surf stop restores native map autoplay',
                      $vehicle_calls==[[:native_save]])
    $PokemonGlobal.bicycle=false
    $PokemonGlobal.surfing=false
    File.delete('Audio/BGM/Kanto/sample.mp3')
    BlueRegionalPolicy.region='KANTO'
    MusicAssert.check('Absent MP3 gives safe fallback',
                      BlueMusic.kanto_audio_for('map',701).nil?)
    # A malformed runtime file cannot change native audio.
    File.write('Data/blue-kanto-music.txt',"bad file\n")
    MusicAssert.check('Malformed regional data is inert',
                      BlueMusic.kanto_audio_for('map',701).nil?)
    puts 'KANTO_MUSIC_RUBY_PHASE_1=PASS_STATIC_RUNTIME'
  end
end
