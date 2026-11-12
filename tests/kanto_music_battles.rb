# Kanto phase 3 Ruby contract: no copyrighted audio or native game saves.
require 'tmpdir'
require 'fileutils'
require 'digest'

module Compiler
  def self.main; end
end
module RPG
  class AudioFile
    attr_accessor :name,:volume,:pitch
    def initialize(name='',volume=100,pitch=100);@name,@volume,@pitch=name,volume,pitch;end
  end
end
module BlueRegionalPolicy
  def self.state;@state;end
  def self.region=(key);@state=key && {'current'=>key};end
end
module BlueKantoPilot
  def self.league_active?;@league_active==true;end
  def self.league_active=(state);@league_active=state;end
end
module GameData
  module TrainerType
    def self.try_get(id)
      Struct.new(:id,:real_name).new(id.to_s,id.to_s)
    end
  end
  module Species
    def self.try_get(species)
      return nil unless species
      mapping={'MEWTWO'=>['Legendary'],'ARTICUNO'=>['Legendary'],
               'MEW'=>['Mythical'],'PIKACHU'=>[],'CHARMANDER'=>[]}
      flags=mapping[species.to_s]
      flags && Struct.new(:flags,:form,:species).new(flags,0,species.to_s)
    end
  end
end
class Object
  private
  def pbGetWildBattleBGM(*args); RPG::AudioFile.new('native-wild'); end
  def pbGetTrainerBattleBGM(*args); RPG::AudioFile.new('native-trainer'); end
  def pbGetTrainerBattleBGMFromType(*args); RPG::AudioFile.new('native-type'); end
  def pbGetWildVictoryBGM(*args); RPG::AudioFile.new('native-wild-win'); end
  def pbGetTrainerVictoryBGM(*args); RPG::AudioFile.new('native-trainer-win'); end
end
NPC=Struct.new(:name,:trainer_type)
Map=Struct.new(:map_id)
Pokemon=Struct.new(:species_data)
def assert_music(label,value,expected)
  raise "FAIL #{label}: #{value.inspect}, expected #{expected.inspect}" unless value==expected
  puts "PASS #{label}"
end
def bgm(method,*args);Object.new.send(method,*args).name;end

source=File.expand_path('../scripts/music/BlueMusic.rb',__dir__)
load source
Object.prepend(BlueMusic::BattleAudio)
Dir.mktmpdir('kanto-battle-music-') do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p('Data')
    FileUtils.mkdir_p('Audio/BGM/Kanto')
    FileUtils.mkdir_p('Audio/BGM/BlueRandom')
    tracks={'wild'=>'wild.mp3','trainer'=>'trainer.mp3','gym'=>'gym.mp3',
            'legendary'=>'legendary.mp3','champion'=>'champion.mp3',
            'wildVictory'=>'wild-win.mp3','trainerVictory'=>'trainer-win.mp3',
            'gymVictory'=>'gym-win.mp3'}
    tracks.values.each { |name| File.write("Audio/BGM/Kanto/#{name}",'synthetic') }
    %w[wild trainer gym].each { |k| File.write("Audio/BGM/BlueRandom/#{k}.mp3",'fixture') }
    lines=["BLUE_KANTO_MUSIC_V1\tKANTO\t#{'f'*64}",
           "SCOPE\t701\tPALLET_TOWN\t0",
           "SCOPE\t702\tCHAMPION_HALL\t0",
           "SCOPE\t703\tSILPH_LOBBY\t1"]
    tracks.each { |key,file| lines << "BATTLE\t#{key}\tKanto/#{file}\t80\t100" }
    %w[wild trainer gym].each do |key|
      pool="BlueRandom/#{key}.mp3"
      hash=Digest::SHA256.hexdigest(["100","100",pool].join("\n"))
      lines << "BASEPOOL\t#{key}\t#{hash}"
    end
    File.write('Data/blue-kanto-music.txt',lines.join("\n")+"\n")
    $game_map=Map.new(701)
    $PokemonGlobal=Struct.new(:nextBattleBGM,:nextBattleVictoryBGM,:blue_regions).
                   new(nil,nil,nil)
    default_config=[1,%w[wild trainer gym].map { |k|
      [k,'random',["BlueRandom/#{k}.mp3"],100,100]
    },[]]
    BlueMusic.instance_variable_set(:@testing,default_config)
    common=NPC.new('Rick',:BLUE_KANTO_BUGCATCHER)
    rocket=NPC.new('Giovanni',:BLUE_KANTO_ROCKETBOSS)
    leader=NPC.new('Blaine',:BLUE_KANTO_LEADER_BLAINE)
    surge=NPC.new('Lt. Surge',:BLUE_KANTO_LEADER_SURGE)
    blue=NPC.new('Blue',:BLUE_KANTO_RIVAL)
    champion=NPC.new('Blue',:BLUE_KANTO_CHAMPION_BLUE)
    foreign=NPC.new('Brock',:LEADER_Brock)
    BlueRegionalPolicy.region='DECADES'
    assert_music('Decades default wild random unchanged',
                 bgm(:pbGetWildBattleBGM,[]),'BlueRandom/wild.mp3')
    $PokemonGlobal.nextBattleBGM=RPG::AudioFile.new('native-event')
    assert_music('Decades event/random precedence unchanged',
                 bgm(:pbGetWildBattleBGM,[]),'BlueRandom/wild.mp3')
    BlueRegionalPolicy.region='KANTO'
    assert_music('Kanto explicit event beats factory pool',
                 bgm(:pbGetWildBattleBGM,[]),'native-wild')
    $PokemonGlobal.nextBattleBGM=nil
    assert_music('Kanto wild BGM',bgm(:pbGetWildBattleBGM,[:PIKACHU]),
                 'Kanto/wild.mp3')
    assert_music('Kanto legendary by species flags only',
                 bgm(:pbGetWildBattleBGM,[:MEWTWO]),'Kanto/legendary.mp3')
    assert_music('Mythical does not imply legendary',
                 bgm(:pbGetWildBattleBGM,[:MEW]),'Kanto/wild.mp3')
    assert_music('Ordinary Kanto rival is not champion',
                 bgm(:pbGetTrainerBattleBGM,[blue]),'Kanto/trainer.mp3')
    assert_music('Kanto ordinary trainer',
                 bgm(:pbGetTrainerBattleBGM,[common]),'Kanto/trainer.mp3')
    assert_music('Kanto Rocket boss is not gym leader',
                 bgm(:pbGetTrainerBattleBGM,[rocket]),'Kanto/trainer.mp3')
    assert_music('Leader identity not name or provisional portrait',
                 bgm(:pbGetTrainerBattleBGM,[leader]),'Kanto/gym.mp3')
    assert_music('Second Kanto leader type',bgm(:pbGetTrainerBattleBGM,[surge]),
                 'Kanto/gym.mp3')
    assert_music('Kanto mixed doubles with leader',
                 bgm(:pbGetTrainerBattleBGM,[common,leader]),'Kanto/gym.mp3')
    assert_music('Decades trainer type in Kanto preserves native',
                 bgm(:pbGetTrainerBattleBGM,[foreign]),'BlueRandom/trainer.mp3')
    assert_music('Kanto gym victory dedicated BGM',
                 bgm(:pbGetTrainerVictoryBGM,[leader]),
                 '../../Audio/BGM/Kanto/gym-win.mp3')
    assert_music('Trainer victory not gym',
                 bgm(:pbGetTrainerVictoryBGM,[common]),
                 '../../Audio/BGM/Kanto/trainer-win.mp3')
    assert_music('Foreign trainer victory remains native',
                 bgm(:pbGetTrainerVictoryBGM,[foreign]),'native-trainer-win')
    assert_music('Wild victory',
                 bgm(:pbGetWildVictoryBGM,[]),
                 '../../Audio/BGM/Kanto/wild-win.mp3')
    BlueKantoPilot.league_active=true
    assert_music('Champion type outside Hall of Fame is not final',
                 bgm(:pbGetTrainerBattleBGM,[champion]),'BlueRandom/trainer.mp3')
    $game_map.map_id=702
    assert_music('Blue League champion uses 1-70',
                 bgm(:pbGetTrainerBattleBGM,[champion]),'Kanto/champion.mp3')
    BlueKantoPilot.league_active=false
    assert_music('Champion with inactive League is not final',
                 bgm(:pbGetTrainerBattleBGM,[champion]),'BlueRandom/trainer.mp3')
    BlueKantoPilot.league_active=true
    $game_map.map_id=703
    assert_music('Preview map gets no Kanto BGM',
                 bgm(:pbGetTrainerBattleBGM,[common]),'BlueRandom/trainer.mp3')
    $game_map.map_id=701
    # User-modified random list, volume and custom choice must never become
    # Kanto defaults. No writing to blue-music.rxdata or any save occurs.
    custom=[1,[['wild','random',['BlueRandom/wild.mp3'],75,100]],[]]
    BlueMusic.instance_variable_set(:@testing,custom)
    assert_music('Custom random volume remains user priority',
                 bgm(:pbGetWildBattleBGM,[]),'BlueRandom/wild.mp3')
    custom=[1,[['gym','custom','BlueRandom/gym.mp3',73,100]],[]]
    BlueMusic.instance_variable_set(:@testing,custom)
    assert_music('Manual gym BGM wins',bgm(:pbGetTrainerBattleBGM,[leader]),
                 'BlueRandom/gym.mp3')
    BlueMusic.instance_variable_set(:@testing,default_config)
    $PokemonGlobal.nextBattleVictoryBGM=RPG::AudioFile.new('story-victory')
    assert_music('Event victory overrides Kanto',
                 bgm(:pbGetTrainerVictoryBGM,[leader]),'native-trainer-win')
    $PokemonGlobal.nextBattleVictoryBGM=nil
    BlueMusic.with_battle do
      context=BlueMusic.instance_variable_get(:@battle_context)
      context[:category]='gym';context[:kanto_eligible]=true
      assert_music('Trainer type lookup cannot replace selected gym theme',
                   bgm(:pbGetTrainerBattleBGMFromType,:BLUE_KANTO_BUGCATCHER),
                   'Kanto/gym.mp3')
      assert_music('Gym victory follows battle context',
                   bgm(:pbGetTrainerVictoryBGM,[]),
                   '../../Audio/BGM/Kanto/gym-win.mp3')
    end
    BlueRegionalPolicy.region='DECADES'
    assert_music('Returning to Decades restores trainer random',
                 bgm(:pbGetTrainerBattleBGM,[leader]),'BlueRandom/gym.mp3')
    puts 'KANTO_MUSIC_BATTLE_PHASE_3=PASS_STATIC_RUNTIME'
  end
end
