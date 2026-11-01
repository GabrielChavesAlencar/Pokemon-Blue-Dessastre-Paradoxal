# Own music overrides. Original RPG maps, PBS and events remain on disk unchanged.
module BlueMusic
  PATH='Data/blue-music.rxdata'
  def self.config
    return @testing if @testing
    return [1,[],[]] unless File.file?(PATH)
    stamp=[File.mtime(PATH).to_f,File.size(PATH)]
    if stamp!=@stamp
      data=load_data(PATH)
      raise 'Invalid music configuration' unless data.is_a?(Array) && data[0]==1 && data[1].is_a?(Array) && data[2].is_a?(Array)
      @data=data;@stamp=stamp
    end
    @data
  rescue StandardError
    [1,[],[]]
  end
  def self.entry(scope,key)
    config[scope=='map' ? 2 : 1].find { |row| row.is_a?(Array) && row[0].to_s==key.to_s }
  end
  def self.audio_for(scope,key)
    row=entry(scope,key)
    return nil unless row
    return RPG::AudioFile.new('',100,100) if row[1]=='mute'
    return nil unless row[1]=='custom' && row[2].is_a?(String) && !row[2].split('/').include?('..') && !row[2].include?('\\') && !row[2].include?(':') && !row[2].start_with?('/') && File.file?('Audio/BGM/'+row[2])
    RPG::AudioFile.new(row[2],row[3].to_i.clamp(0,100),row[4].to_i.clamp(50,150))
  end
  def self.apply_map(game_map)
    map=game_map.instance_variable_get(:@map)
    return unless map
    original=game_map.instance_variable_get(:@blue_music_original)
    unless original
      original=[map.autoplay_bgm,map.bgm.clone]
      game_map.instance_variable_set(:@blue_music_original,original)
    end
    audio=audio_for('map',game_map.map_id)
    if audio
      map.autoplay_bgm=true;map.bgm=audio
    else
      map.autoplay_bgm=original[0];map.bgm=original[1].clone
    end
  end
  module MapAudio
    def setup(*args)
      @blue_music_original=nil
      result=super
      BlueMusic.apply_map(self)
      result
    end
    def autoplay
      BlueMusic.apply_map(self)
      super
    end
    def autoplayAsCue
      BlueMusic.apply_map(self)
      super
    end
    def bgm_name
      row=BlueMusic.entry('map',map_id)
      return super unless row && row[1]=='custom'
      name=bgm.name
      extension=File.extname(name)
      night=name[0...-extension.length]+'_n'+extension
      return night if PBDayNight.isNight? && File.file?('Audio/BGM/'+night)
      name
    end
  end
  module BattleAudio
    private
    def pbGetWildBattleBGM(*args)
      return super if $PokemonGlobal.nextBattleBGM
      BlueMusic.audio_for('global','wild') || super
    end
    def pbGetTrainerBattleBGM(*args)
      return super if $PokemonGlobal.nextBattleBGM
      BlueMusic.audio_for('global','trainer') || super
    end
    def pbGetTrainerBattleBGMFromType(*args)
      return super if $PokemonGlobal.nextBattleBGM
      BlueMusic.audio_for('global','trainer') || super
    end
    def pbGetWildVictoryBGM(*args)
      return super if $PokemonGlobal.nextBattleVictoryBGM
      audio=BlueMusic.audio_for('global','wildVictory')
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
    def pbGetTrainerVictoryBGM(*args)
      return super if $PokemonGlobal.nextBattleVictoryBGM
      audio=BlueMusic.audio_for('global','trainerVictory')
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
  end
  def self.install
    Game_Map.prepend(MapAudio) unless Game_Map.ancestors.include?(MapAudio)
    Object.prepend(BattleAudio) unless Object.ancestors.include?(BattleAudio)
  end
  def self.run_checks
    lines=[]
    check=proc { |label,ok| lines << "#{ok ? 'PASS' : 'FAIL'} | #{label}";raise label unless ok }
    track=Dir['Audio/BGM/**/*'].find { |p| File.file?(p) && ['.ogg','.mp3','.wav','.mid','.midi'].include?(File.extname(p).downcase) }
    check.call('Local BGM library available',!!track)
    track=track.sub('Audio/BGM/','')
    original=@testing
    @testing=[1,[['wild','custom',track,73,105],['trainer','custom',track,67,95],['wildVictory','custom',track,70,100],['trainerVictory','custom',track,71,100]], [['156','custom',track,61,110]]]
    audio=pbGetWildBattleBGM([])
    check.call('Wild battle override resolves',audio.name==track && audio.volume==73 && audio.pitch==105)
    audio=pbGetTrainerBattleBGM([$player])
    check.call('Trainer battle override resolves',audio.name==track && audio.volume==67 && audio.pitch==95)
    check.call('Trainer-type battle override resolves',pbGetTrainerBattleBGMFromType(:YOUNGSTER).name==track)
    audio=pbGetWildVictoryBGM
    check.call('Wild victory resolves in BGM folder',audio.name=='../../Audio/BGM/'+track && audio.volume==70)
    audio=pbGetTrainerVictoryBGM([$player])
    check.call('Trainer victory resolves in BGM folder',audio.name=='../../Audio/BGM/'+track && audio.volume==71)
    event=$PokemonGlobal.nextBattleBGM
    $PokemonGlobal.nextBattleBGM=RPG::AudioFile.new('event override',100,100)
    check.call('Explicit story music takes precedence',pbGetWildBattleBGM([]).name=='event override')
    $PokemonGlobal.nextBattleBGM=event
    map=Game_Map.allocate
    map.instance_variable_set(:@map_id,156)
    record=RPG::Map.new(1,1);record.autoplay_bgm=false;record.bgm=RPG::AudioFile.new('original city',43,100)
    map.instance_variable_set(:@map,record)
    apply_map(map)
    check.call('City override is applied in memory',map.bgm.name==track && map.bgm.volume==61 && record.autoplay_bgm)
    @testing=[1,[],[]];apply_map(map)
    check.call('Removing city override restores original',map.bgm.name=='original city' && map.bgm.volume==43 && !record.autoplay_bgm)
    @testing=[1,[['wild','mute','',100,100]],[]]
    check.call('Mute option is explicit',pbGetWildBattleBGM([]).name.empty?)
    lines << 'RESULT=PASS'
    true
  rescue StandardError => error
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace);lines << 'RESULT=FAIL'
    false
  ensure
    @testing=original
    $PokemonGlobal.nextBattleBGM=event if defined?(event)
    File.open('Data/blue-music-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
  end
end
module Compiler
  class << self
    alias blue_music_original_main main
    def main
      blue_music_original_main
      BlueMusic.install
    end
  end
end
