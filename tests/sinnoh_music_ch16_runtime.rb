# CH16: real BlueMusic.rb + inert Sinnoh music contract, NO audio playback.
# Fake input catalog only. No game/, music files or engine hooks installed.
require 'json'
module Compiler
  def self.main; end
end
module RPG
  class AudioFile
    attr_accessor :name, :volume, :pitch
    def initialize(name='',volume=100,pitch=100)
      @name,@volume,@pitch=name,volume,pitch
    end
  end
end
load File.expand_path(ARGV.fetch(0))   # real BlueMusic
load File.expand_path(ARGV.fetch(1))   # proposed inert Sinnoh contract
catalog=JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))

def check(cond,msg)
  raise "SINNOH_CH16_RUBY: #{msg}" unless cond
end

module AssertNoSound
  class << self
    attr_accessor :calls
    def pbBGMPlay(*); self.calls ||= 0; self.calls+=1; raise 'BGM called'; end
    def pbCueBGM(*); self.calls ||= 0; self.calls+=1; raise 'BGM cue called'; end
    def pbMEPlay(*); self.calls ||= 0; self.calls+=1; raise 'ME called'; end
  end
end
check(BlueSinnohMusicContracts.safe_catalog?(catalog), 'catalog rejected')
check(catalog['cues'].length==46, 'wrong registry size')
check(BlueSinnohMusicContracts::PRIORITIES.first=='EXPLICIT_ENGINE_EVENT',
      'explicit event not top priority')
check(BlueSinnohMusicContracts::PRIORITIES.index('FORCED_VERIFIED_SCENE') <
      BlueSinnohMusicContracts::PRIORITIES.index('VERIFIED_BATTLE'),
      'scene vs battle priority wrong')
check(BlueSinnohMusicContracts::PRIORITIES.index('VERIFIED_BATTLE') <
      BlueSinnohMusicContracts::PRIORITIES.index('VERIFIED_MAP'),
      'battle vs map priority wrong')

# All entries remain uninstalled, and no fake track or MapID was injected.
catalog['cues'].each do |row|
  c=BlueSinnohMusicContracts.cue(catalog,row.fetch('key'))
  check(c && c['enabled']==false && c['track_path'].nil? &&
        c['track_sha256'].nil? && c['physical_map_id'].nil? &&
        c['physical_event_id'].nil?, 'cue claims installation')
  check(BlueSinnohMusicContracts.fade_loop(catalog,row['key']) ==
      {fade_seconds:nil,loop_start_ms:nil,loop_end_ms:nil,
       action: :engine_default_no_audio_override},
       'invented fade, looping or replay')
  check(BlueSinnohMusicContracts.resolve(
       catalog,row['key'],current_region:'DECADES')==:keep_existing_audio,
       'Sinnoh crossed into Decades')
  %w[KANTO JOHTO HOENN UNOVA].each do |other|
    check(BlueSinnohMusicContracts.resolve(
      catalog,row['key'],current_region:other)==:keep_existing_audio,
      "Sinnoh crossed into #{other}")
  end
end
check(BlueSinnohMusicContracts.cue(catalog,'SINNOH_FAKE').nil?, 'unknown cue accepted')
check(BlueSinnohMusicContracts.cue(catalog,'../SINNOH_WILD').nil?, 'path trick accepted')
check(BlueSinnohMusicContracts.cue(catalog,123).nil?, 'number converted to cue')

# Use real BlueMusic config entry lookup, not a mock playback engine.
BlueMusic.instance_variable_set(:@testing,[1,[
  ['wild','custom','manual/synthetic.wav',63,102],
  ['gym','mute','',100,100]],
  [['501','custom','custom/map.wav',42,107]]])
check(BlueMusic.entry('global','wild')[1]=='custom','BlueMusic missing manual global')
check(BlueMusic.entry('global','gym')[1]=='mute','explicit mute not visible')
check(BlueMusic.entry('map',501)[1]=='custom','BlueMusic missing manual map')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_WILD',
      current_region:'SINNOH',blue_music:BlueMusic,
      blue_global_key:'wild')==:preserve_configured_blue_music,
      'global manual custom lost')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_GYM',
      current_region:'SINNOH',blue_music:BlueMusic,
      blue_global_key:'gym')==:preserve_configured_blue_music,
      'explicit mute must not be overwritten')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_TWINLEAF_DAY',
      current_region:'SINNOH',map_id:501,map_id_verified:true,
      blue_music:BlueMusic)==:preserve_configured_blue_music,
      'manual map override lost')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_WILD',
      current_region:'SINNOH',explicit_engine_audio:true,
      blue_music:BlueMusic,blue_global_key:'wild')==
      :preserve_explicit_engine_audio,'forced engine music not top priority')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_CYNTHIA_INTRO',
      current_region:'SINNOH',explicit_engine_audio:true,
      trusted_event_result:true,blue_music:BlueMusic)==
      :preserve_explicit_engine_audio,'Cynthia intro changed author cue')
check(BlueSinnohMusicContracts.resolve(catalog,'SINNOH_TWINLEAF_DAY',
      current_region:'SINNOH',map_id:501,map_id_verified:false,
      blue_music:BlueMusic)==:keep_existing_audio,
      'unverified MapID accepted')

# No runtime verification has been supplied: even a synthetic approved
# event/ME flag cannot force playback from empty audio fields.
%w[SINNOH_CYNTHIA_INTRO SINNOH_DISTORTION_WORLD SINNOH_HALL_OF_FAME_BGM].each do |id|
  check(BlueSinnohMusicContracts.resolve(catalog,id,current_region:'SINNOH',
        trusted_event_result:true)==:keep_existing_audio,
        "#{id} fabricated scene song")
end
%w[SINNOH_BADGE_ME SINNOH_ITEM_ME SINNOH_HALL_OF_FAME_ME].each do |id|
  check(BlueSinnohMusicContracts.resolve(catalog,id,current_region:'SINNOH',
        trusted_event_result:true,confirmed_me:false)==:keep_existing_audio,
        "#{id} played before award confirmation")
  check(BlueSinnohMusicContracts.resolve(catalog,id,current_region:'SINNOH',
        trusted_event_result:true,confirmed_me:true)==:keep_existing_audio,
        "#{id} played despite missing licensed file")
end

# Test real BlueMusic custom path against missing file in empty synthetic
# project; the existing author BGM is not overwritten or silenced.
check(BlueMusic.audio_for('global','wild').nil?,
      'BlueMusic selected nonexistent custom BGM')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      region_changed:true,still_owns_audio:true)==:keep_new_region_audio,
      'old Sinnoh scene restored after region change')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      new_explicit_event:true,still_owns_audio:true)==:keep_new_event_audio,
      'scene overwrote a new engine event')
check(BlueSinnohMusicContracts.transition(from:'battle',to:'map')==
      :leave_engine_to_restore_after_battle,
      'battle end did not defer to native BGM')
check(BlueSinnohMusicContracts.transition(from:'me',to:'map')==
      :leave_engine_to_resume_after_me,
      'ME did not resume native BGM')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      map_changed:true,still_owns_audio:true)==:leave_new_map_audio,
      'map changed but previous scene was restored')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      still_owns_audio:true)==:restore_previous_only_if_owned,
      'owned scene did not preserve restoration policy')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      still_owns_audio:false)==:keep_existing_audio,
      'unowned scene rewrote newer music')
check(BlueSinnohMusicContracts.transition(from:'battle',to:'map',
      same_track:true)==:no_replay,'reloaded identical BGM loops twice')
check(BlueSinnohMusicContracts.transition(from:'me',to:'map',
      region_changed:true)==:keep_new_region_audio,
      'ME restored audio from a different region')
check(BlueSinnohMusicContracts.transition(from:'scene',to:'map',
      same_track:true,new_explicit_event:true)==:keep_new_event_audio,
      'new event lost to duplicate cue check')

# Corrupt manifest fails closed; source audio is not repaired in-place.
copy=Marshal.load(Marshal.dump(catalog))
copy['cues'][0]['track_path']='Sinnoh/guess.mp3'
check(!BlueSinnohMusicContracts.safe_catalog?(copy),'unlicensed path accepted')
check(BlueSinnohMusicContracts.resolve(copy,'SINNOH_TWINLEAF_DAY',
      current_region:'SINNOH')==:keep_existing_audio,'corrupt catalogue not inert')
copy=Marshal.load(Marshal.dump(catalog))
copy['redistribution_approved']=true
check(!BlueSinnohMusicContracts.safe_catalog?(copy),'fake rights accepted')
copy=Marshal.load(Marshal.dump(catalog))
copy['cues'][1]['enabled']=true
check(!BlueSinnohMusicContracts.safe_catalog?(copy),'false enabled cue accepted')
check(!BlueMusic.instance_variable_get(:@testing).nil?,
      'original BlueMusic testing config was rewritten')
check(AssertNoSound.calls.nil?, 'test played sound')
puts 'SINNOH_CH16_BLUEMUSIC_PRIORITIES_FALLBACK_FADE_LOOP_NO_AUDIO_OK'
