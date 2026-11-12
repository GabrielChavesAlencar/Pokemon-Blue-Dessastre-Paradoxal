# CI-ONLY Phase 6 music smoke, executed inside the real mkxp-z Game.exe.
# File is staged under Data/ on a disposable runner by native_check.py.
# This checks engine APIs, not the actual sound coming out of speakers.
module KantoMusicNativeProbe
  def self.require!(condition,reason)
    raise "Native Kanto F6 music: " + reason unless condition
  end
  def self.run(label)
    require!(defined?(BlueMusic), "BlueMusic plugin missing")
    require!($PokemonGlobal && $PokemonGlobal.blue_regions.is_a?(Hash),
             "No regional save context")
    require!($PokemonGlobal.blue_regions["current"] == "KANTO",
             "Kanto save is not active")
    region = $PokemonGlobal.blue_regions["current"]
    music = BlueMusic.kanto_data
    require!(music[0].length == 142, "Compiled MapID coverage not 142")
    require!([music[1].length,music[2].length,music[3].length,music[4].length,
              music[5].length,music[6].length] == [49,8,2,3,6,5],
             "Kanto manifest category counts do not match approved rules")
    map_id=$game_map.map_id
    require!(music[0].key?(map_id) && !music[0][map_id][1] &&
             music[1].key?(map_id),
             "Native probe must be on a non-preview map with regional music")
    bgm=BlueMusic.kanto_audio_for('map',map_id)
    me=BlueMusic.kanto_me_audio('obtained_item')
    scene=BlueMusic.kanto_scene_audio('rival_appears')
    require!(bgm && me && scene, "Real game did not resolve three kinds of Kanto music")
    require!([bgm,scene].all? { |audio|
      File.file?("Audio/BGM/" + audio.name) },
      "Native BGM resolution points to a nonexistent MP3")
    require!(File.file?("Audio/ME/" + me.name),
             "Native ME resolution points to a nonexistent MP3")
    require!(BlueMusic.kanto_scene_audio('credits').nil?,
             "Unimplemented credits were incorrectly activated")
    require!(BlueMusic.kanto_scene_audio('opening_movie').nil?,
             "Unimplemented Kanto movie was incorrectly activated")
    require!(bgm.volume==100 && bgm.pitch==100 &&
             me.volume==100 && me.pitch==100,
             "Compiled regional volume/pitch changed unexpectedly")
    # Native AudioFile dispatch. Success only proves the engine accepts the
    # sound path; this is NOT proof of audible speakers, seamless loops or fade.
    previous=BlueMusic.current_bgm
    begin
      pbBGMPlay(bgm)
      current=BlueMusic.current_bgm
      require!(current && current.name==bgm.name,
               "Native BGM API did not select the requested Kanto track")
      pbMEPlay(me)
      require!(BlueMusic.current_bgm,
               "Native ME callback unexpectedly erased BGM state")
    ensure
      # The native engine resumes the underlying BGM after an ME. End this
      # one-shot smoke immediately and restore the original state explicitly,
      # avoiding accidental lingering music in subsequent native QA.
      pbMEStop
      previous ? pbBGMPlay(previous) : pbBGMStop
    end
    # Switch ONLY the in-memory regional state for the duration of the probe.
    # No save file or Decades music preference is ever written here.
    begin
      $PokemonGlobal.blue_regions["current"]="DECADES"
      require!(BlueMusic.kanto_audio_for('map',map_id).nil? &&
               BlueMusic.kanto_me_audio('obtained_item').nil? &&
               BlueMusic.kanto_scene_audio('rival_appears').nil?,
               "Decades still receives Kanto music overrides")
    ensure
      $PokemonGlobal.blue_regions["current"]=region
    end
    require!($game_map.map_id==map_id &&
             $PokemonGlobal.blue_regions["current"]=="KANTO",
             "Music probe changed current region or map")
    File.write("Data/blue-kanto-music-native-#{label}.txt",
               "STATUS=PASS_NATIVE_AUDIOFILE_DISPATCH_NOT_AUDIBLE\n" +
               "SCOPE=142;MAP=49;BATTLE=8;TRANSPORT=2;ME=6;SCENE=5\n" +
               "DECODER=SEPARATE_FFMPEG_CI;LOOP_FADE_SPEAKER=BLOCKED_ENV\n")
    puts "KANTO_MUSIC_NATIVE_F6=#{label}|PASS_NATIVE_AUDIOFILE_DISPATCH_NOT_AUDIBLE"
    true
  end
end
