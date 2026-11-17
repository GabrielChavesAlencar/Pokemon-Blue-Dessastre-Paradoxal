# S25. Bridge read-only: nenhum hook instalado em Compiler/BlueMusic.
module BlueSinnohMusicBridge
  DEFAULT = :keep_existing_audio
  PRIORITY = %w[EXPLICIT_ENGINE MANUAL_BLUE_MUSIC VERIFIED_SINNOH KEEP_NATIVE].freeze
  VERIFIED_NATIVE_SOURCES = {}.freeze
  BATTLES = {
    'SINNOH_WILD'=>'wild', 'SINNOH_TRAINER'=>'trainer',
    'SINNOH_RIVAL'=>'trainer', 'SINNOH_GYM'=>'gym',
    'SINNOH_GALACTIC'=>'trainer', 'SINNOH_GALACTIC_COMMANDER'=>'trainer',
    'SINNOH_CYRUS'=>'trainer', 'SINNOH_GIRATINA'=>'wild',
    'SINNOH_ELITE_FOUR'=>'gym', 'SINNOH_CHAMPION'=>'trainer'
  }.freeze

  def self.safe_manifest?(m)
    m.is_a?(Hash) && m['schema']==1 && m['region']=='SINNOH' &&
      m['stage']=='S25' && m['status']=='BRIDGE_OFFLINE_NOT_INSTALLED' &&
      m['cue_count']==46 && m['priority']==PRIORITY &&
      m['approved_tracks']==[] && m['licensed_sources']==[] &&
      m['native_maps']==[] && m['native_events']==[] &&
      m['compiled_bindings']==[] && m['enabled']==false &&
      m['installed']==false && m['autoplay']==false &&
      m['audio_copied']==false && m['game_exe_tested']==false &&
      m['joiplay_tested']==false && m['native_qa_approved']==false &&
      VERIFIED_NATIVE_SOURCES.empty?
  rescue StandardError
    false
  end

  # Consultar BlueMusic.entry sem tocar som. Preferencia da engine e do
  # usuario (inclusive mute e random) prevalece sobre musica regional.
  def self.resolve(manifest,catalog,key,current_region:,map_id:nil,
                   map_id_verified:false,explicit_engine_audio:false,
                   committed_event:false,confirmed_me:false,blue_music:nil)
    return DEFAULT unless current_region=='SINNOH' && safe_manifest?(manifest)
    return DEFAULT unless defined?(BlueSinnohMusicContracts) &&
      BlueSinnohMusicContracts.safe_catalog?(catalog)
    cue=BlueSinnohMusicContracts.cue(catalog,key)
    return DEFAULT unless cue
    return :preserve_explicit_engine_audio if explicit_engine_audio==true
    blue_music ||= (defined?(BlueMusic) ? BlueMusic : nil)
    if blue_music && blue_music.respond_to?(:entry)
      if map_id_verified==true && map_id.is_a?(Integer) && map_id>0
        return :preserve_configured_blue_music if blue_music.entry('map',map_id)
      end
      if cue['scope']=='battle' && (category=BATTLES[key])
        return :preserve_configured_blue_music if blue_music.entry('global',category)
      end
    end
    # CH16 e S24 sempre mantem os fallbacks ate a origem ser autorizada.
    BlueSinnohMusicContracts.resolve(
      catalog,key,current_region:current_region,map_id:map_id,
      map_id_verified:map_id_verified,blue_music:blue_music,
      blue_global_key:BATTLES[key],trusted_event_result:committed_event,
      confirmed_me:confirmed_me)
    DEFAULT
  rescue StandardError
    DEFAULT
  end

  def self.native_ready?(manifest,key)
    safe_manifest?(manifest) && key.is_a?(String) &&
      VERIFIED_NATIVE_SOURCES.key?(key)
  rescue StandardError
    false
  end
end
