# S26: policy regression against REAL BlueMusic + planning-only Sinnoh adapter.
# Does NOT create or play audio files. No native Sinnoh hooks are enabled.
require 'json'
module Compiler
  def self.main; end
end
module RPG
  class AudioFile
    attr_accessor :name, :volume, :pitch
    def initialize(name='', volume=100, pitch=100)
      @name, @volume, @pitch = name, volume, pitch
    end
  end
end
load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
catalog = JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))

def check(ok, message)
  raise "SINNOH_S26: #{message}" unless ok
end

def expect(catalog, key, region: 'SINNOH', **opts)
  BlueSinnohMusicContracts.resolve(
    catalog, key, current_region: region, **opts)
end

check(BlueSinnohMusicContracts.safe_catalog?(catalog), 'real catalog invalid')
check(catalog['recordings'].empty? && catalog['verified_tracks']==0 &&
      catalog['active_audio_overrides']==false &&
      catalog['compiled_event_hooks_verified']==false,
      'unlicensed audio or native hooks claimed')
check(catalog['cues'].length==46, 'expected 46 symbolic cues')
check(BlueSinnohMusicContracts::PRIORITIES ==
      catalog['priority_policy'], 'runtime priority differs from manifest')
check(catalog['fallback_policy']['no_force_silence']==true &&
      catalog['fallback_policy']['no_repeat_same_track']==true,
      'missing safe fallback policy')

# Mock only EXISTING music settings, not playback.
BlueMusic.instance_variable_set(:@testing, [
  1,
  [['wild', 'custom', 'manual/s26.wav', 87, 98],
   ['gym', 'mute', '', 100, 100]],
  [['501', 'custom', 'manual/twinleaf.wav', 67, 100]]
])
def check_no_override(catalog, key, region)
  result = expect(catalog, key, region: region)
  check(result == :keep_existing_audio,
        "unverified #{key} switched audio in #{region}")
end

# Every cue in every other region must be inert; Sinnoh's placeholders never
# emit audio objects or extra playback requests in Sinnoh either.
catalog['cues'].each do |row|
  key = row['key']
  %w[DECADES KANTO JOHTO HOENN UNOVA KALOS ALOLA GALAR PALDEA HISUI].each do |region|
    check_no_override(catalog, key, region)
  end
  check_no_override(catalog, key, 'SINNOH')
  fade = BlueSinnohMusicContracts.fade_loop(catalog,key)
  check(fade == {fade_seconds:nil, loop_start_ms:nil, loop_end_ms:nil,
                 action: :engine_default_no_audio_override},
        "invented fade/loop for #{key}")
  check(row['enabled']==false && row['track_path'].nil? &&
        row['track_sha256'].nil? && row['physical_map_id'].nil? &&
        row['native_hook_verified']==false, "fake track installed #{key}")
end

# Strict precedence: engine event > manual BlueMusic > unlicensed cue.
check(expect(catalog,'SINNOH_WILD',
     explicit_engine_audio:true, blue_music:BlueMusic,
     blue_global_key:'wild') == :preserve_explicit_engine_audio,
     'engine explicit audio must win')
check(expect(catalog,'SINNOH_WILD',
     blue_music:BlueMusic, blue_global_key:'wild') ==
     :preserve_configured_blue_music, 'manual wild override lost')
check(expect(catalog,'SINNOH_GYM',
     blue_music:BlueMusic, blue_global_key:'gym') ==
     :preserve_configured_blue_music, 'manual gym mute lost')
check(expect(catalog,'SINNOH_TWINLEAF_DAY', map_id:501,
     map_id_verified:true,blue_music:BlueMusic) ==
     :preserve_configured_blue_music, 'verified manual map override lost')
check(expect(catalog,'SINNOH_TWINLEAF_DAY', map_id:501,
     map_id_verified:false,blue_music:BlueMusic) ==
     :keep_existing_audio, 'unverified MapID changed music')
check(expect(catalog,'SINNOH_BADGE_ME',
     confirmed_me:false,trusted_event_result:true) ==
     :keep_existing_audio, 'ME played before confirmed award')
check(expect(catalog,'SINNOH_BADGE_ME',
     confirmed_me:true,trusted_event_result:true) ==
     :keep_existing_audio, 'ME played with no licensed recording')
check(expect(catalog,'SINNOH_CYNTHIA_INTRO',
     trusted_event_result:false) == :keep_existing_audio,
     'untrusted scene changed music')
check(expect(catalog,'SINNOH_CYNTHIA_INTRO',
     trusted_event_result:true) == :keep_existing_audio,
     'scene played without licensed audio')
check(expect(catalog,'NOT_A_CUE') == :keep_existing_audio,
     'unknown cue overrode audio')

# State transitions: no replay of an identical track, no stale music across
# map/region changes and never restore a scene once ownership is lost.
policy = BlueSinnohMusicContracts
cases = [
  [{from:'battle',to:'map'}, :leave_engine_to_restore_after_battle],
  [{from:'me',to:'map'}, :leave_engine_to_resume_after_me],
  [{from:'scene',to:'map',still_owns_audio:true}, :restore_previous_only_if_owned],
  [{from:'scene',to:'map',still_owns_audio:false}, :keep_existing_audio],
  [{from:'scene',to:'map',map_changed:true,still_owns_audio:true}, :leave_new_map_audio],
  [{from:'battle',to:'map',same_track:true}, :no_replay],
  [{from:'scene',to:'map',same_track:true}, :no_replay],
  [{from:'scene',to:'map',new_explicit_event:true}, :keep_new_event_audio],
  [{from:'scene',to:'map',region_changed:true}, :keep_new_region_audio],
  [{from:'me',to:'map',region_changed:true,same_track:true}, :keep_new_region_audio],
  [{from:'battle',to:'map',new_explicit_event:true,same_track:true}, :keep_new_event_audio]
]
cases.each do |input, expected|
  result = policy.transition(**input)
  check(result == expected, "transition #{input.inspect} -> #{result}, not #{expected}")
end

# Reject malicious/fictitious "enabled" tracks rather than accepting fake
# SHA/loop/fade or restoring music from Johto/Decades.
mutations = [
  proc { |r| r['enabled']=true },
  proc { |r| r['track_path']='Audio/BGM/fake.ogg' },
  proc { |r| r['track_sha256']='a'*64 },
  proc { |r| r['physical_map_id']=501 },
  proc { |r| r['license_verified']=true },
  proc { |r| r['native_hook_verified']=true }
]
mutations.each do |edit|
  fake = Marshal.load(Marshal.dump(catalog))
  edit.call(fake['cues'].first)
  check(!policy.safe_catalog?(fake), 'unverified musical mutation accepted')
  check(expect(fake,fake['cues'].first['key'])==:keep_existing_audio,
        'mutated cue overrode BGM')
end
check(catalog['native_game_installed']==false,
      'planning catalog became native without QA')
puts 'SINNOH_S26_FALLBACK_PRIORITY_FADE_LOOP_REGRESSION_OFFLINE_OK'
