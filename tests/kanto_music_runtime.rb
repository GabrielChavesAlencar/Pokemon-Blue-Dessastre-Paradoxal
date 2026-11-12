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
    $PokemonGlobal=Struct.new(:nextBattleBGM).new(nil)
    BlueMusic.instance_variable_set(:@testing,[1,[],[]])
    BlueRegionalPolicy.region=nil
    MusicAssert.check('Legacy save without region never switches sound',
                      BlueMusic.kanto_audio_for('map',701).nil?)
    BlueRegionalPolicy.region='DECADES'
    MusicAssert.check('Decades never switches sound',
                      BlueMusic.kanto_audio_for('map',701).nil?)
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
