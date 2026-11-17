# S25: fixture real BlueMusic, sem Game.exe e sem som.
require 'json'
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
load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
load File.expand_path(ARGV.fetch(2))
catalog=JSON.parse(File.read(File.expand_path(ARGV.fetch(3))))
manifest=JSON.parse(File.read(File.expand_path(ARGV.fetch(4))))
def check(condition,message)
  raise "SINNOH_S25: #{message}" unless condition
end
def choice(manifest,catalog,key,region='SINNOH',**kw)
  BlueSinnohMusicBridge.resolve(manifest,catalog,key,current_region:region,
                                 blue_music:BlueMusic,**kw)
end
check(BlueSinnohMusicBridge.safe_manifest?(manifest),'manifest unsafe')
check(BlueSinnohMusicContracts.safe_catalog?(catalog),'CH16 unsafe')
BlueMusic.instance_variable_set(:@testing, [
  1,
  [['wild','custom','personal/wild.wav',80,100],
   ['trainer','random',['personal/a.wav'],90,100],
   ['gym','mute','',100,100]],
  [['501','custom','personal/map.wav',90,100]]
])
catalog['cues'].each do |c|
  %w[DECADES KANTO JOHTO HOENN UNOVA KALOS ALOLA GALAR PALDEA HISUI].each do |region|
    check(choice(manifest,catalog,c['key'],region)==:keep_existing_audio,
          "audio crossed region #{region}")
  end
  check(!BlueSinnohMusicBridge.native_ready?(manifest,c['key']),
        "unverified sound enabled")
end
check(choice(manifest,catalog,'SINNOH_WILD')==:preserve_configured_blue_music,
      'custom wild lost')
check(choice(manifest,catalog,'SINNOH_RIVAL')==:preserve_configured_blue_music,
      'random trainer lost')
check(choice(manifest,catalog,'SINNOH_GYM')==:preserve_configured_blue_music,
      'manual mute lost')
check(choice(manifest,catalog,'SINNOH_TWINLEAF_DAY',map_id:501,
      map_id_verified:true)==:preserve_configured_blue_music,'map custom lost')
check(choice(manifest,catalog,'SINNOH_TWINLEAF_DAY',map_id:501,
      map_id_verified:false)==:keep_existing_audio,'unverified map played')
check(choice(manifest,catalog,'SINNOH_WILD',
      explicit_engine_audio:true)==:preserve_explicit_engine_audio,
      'engine event was overridden')
check(choice(manifest,catalog,'SINNOH_BADGE_ME',
      confirmed_me:true,committed_event:true)==:keep_existing_audio,
      'unlicensed ME leaked')
check(choice(manifest,catalog,'SINNOH_CYNTHIA_INTRO',
      committed_event:true)==:keep_existing_audio,
      'unlicensed scene leaked')
fake=manifest.dup
fake['approved_tracks']=['fake.mp3']
check(!BlueSinnohMusicBridge.safe_manifest?(fake),'fake tracks accepted')
check(choice(fake,catalog,'SINNOH_WILD')==:keep_existing_audio,
      'unsafe manifest overrode user')
puts 'SINNOH_S25_BRIDGE_RUNTIME_OK_NO_AUDIO'
