# CH16: planning-only Sinnoh music contract; NOT hooked into BlueMusic.install.
# Does not play sound, change maps, load files or write any game data.
module BlueSinnohMusicContracts
  PRIORITIES = %w[
    EXPLICIT_ENGINE_EVENT FORCED_VERIFIED_SCENE CONFIGURED_BLUE_MUSIC
    VERIFIED_BATTLE VERIFIED_TRANSPORT VERIFIED_MAP PRESERVE_NATIVE
  ].freeze
  DEFAULT = :keep_existing_audio

  def self.safe_catalog?(catalog)
    return false unless catalog.is_a?(Hash) &&
      catalog['schema']==1 && catalog['region']=='SINNOH' &&
      catalog['status']=='SYMBOLIC_CUES_PLANNED_NOT_INSTALLED' &&
      catalog['default_enabled']==false && catalog['can_install']==false &&
      catalog['active_audio_overrides']==false &&
      catalog['redistribution_approved']==false &&
      catalog['recordings']==[] && catalog['verified_tracks']==0 &&
      catalog['priority_policy']==PRIORITIES &&
      catalog['cues'].is_a?(Array)
    catalog['cues'].all? do |c|
      c.is_a?(Hash) && c['key'].is_a?(String) &&
        c['key'].match?(/\ASINNOH_[A-Z0-9_]+\z/) &&
        c['enabled']==false && c['track_path'].nil? &&
        c['track_sha256'].nil? && c['physical_map_id'].nil? &&
        c['physical_event_id'].nil? && c['license_verified']==false &&
        c['native_hook_verified']==false && c['compiled_binding_verified']==false
    end
  rescue StandardError
    false
  end

  def self.cue(catalog, key)
    return nil unless safe_catalog?(catalog) && key.is_a?(String)
    catalog['cues'].find { |entry| entry['key']==key }
  end

  def self.cue_priority(catalog, key)
    row=cue(catalog,key)
    row ? row['priority'] : nil
  end

  # No RPG::AudioFile is produced: CH16 has no verified, licensed files or
  # native Sinnoh bindings. BlueMusic remains the exclusive playback owner.
  def self.resolve(catalog,key,current_region:,explicit_engine_audio: false,
                   map_id: nil,map_id_verified: false,
                   blue_music: nil,blue_global_key: nil,
                   trusted_event_result: false,confirmed_me: false)
    return DEFAULT unless current_region=='SINNOH'
    row=cue(catalog,key)
    return DEFAULT unless row
    return :preserve_explicit_engine_audio if explicit_engine_audio==true
    if ['scene','me','transport'].include?(row['scope']) &&
       trusted_event_result!=true
      return DEFAULT
    end
    return DEFAULT if row['kind']=='ME' && confirmed_me!=true
    if ['city','route','cave','post_game'].include?(row['scope']) &&
       map_id_verified!=true
      return DEFAULT
    end
    if blue_music && blue_music.respond_to?(:entry)
      if map_id_verified==true && map_id.is_a?(Integer) && map_id>0
        existing=blue_music.entry('map',map_id)
        return :preserve_configured_blue_music if existing
      end
      if row['scope']=='battle' && %w[wild trainer gym].include?(blue_global_key)
        existing=blue_music.entry('global',blue_global_key)
        return :preserve_configured_blue_music if existing
      end
    end
    DEFAULT
  rescue StandardError
    DEFAULT
  end

  # Only an ownership policy, no audio calls, no hardcoded fade/loop.
  def self.transition(from:,to:,region_changed: false,map_changed: false,
                      same_track: false,still_owns_audio: false,
                      new_explicit_event: false)
    return :keep_new_region_audio if region_changed==true
    return :keep_new_event_audio if new_explicit_event==true
    return :no_replay if same_track==true
    return :leave_engine_to_restore_after_battle if from=='battle'
    return :leave_engine_to_resume_after_me if from=='me'
    if from=='scene'
      return :leave_new_map_audio if map_changed==true
      return :restore_previous_only_if_owned if still_owns_audio==true
    end
    :keep_existing_audio
  rescue StandardError
    :keep_existing_audio
  end

  def self.fade_loop(catalog,key)
    row=cue(catalog,key)
    return nil unless row
    {fade_seconds:nil,loop_start_ms:nil,loop_end_ms:nil,
     action: :engine_default_no_audio_override}
  end
end
