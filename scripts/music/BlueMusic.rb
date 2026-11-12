# Own music overrides. Original RPG maps, PBS and events remain on disk unchanged.
module BlueMusic
  PATH='Data/blue-music.rxdata'
  CATEGORIES_PATH='Data/blue-music-categories.rxdata'
  def self.valid_track?(name)
    name.is_a?(String) && !name.empty? && !name.split('/').any? { |p| ['', '.', '..'].include?(p) } && !name.include?('\\') && !name.include?(':') && !name.start_with?('/') && File.file?('Audio/BGM/'+name)
  end
  def self.categories
    return @testing_categories if @testing_categories
    return [1,[],[]] unless File.file?(CATEGORIES_PATH)
    stamp=[File.mtime(CATEGORIES_PATH).to_f,File.size(CATEGORIES_PATH)]
    if @categories_stamp!=stamp
      value=load_data(CATEGORIES_PATH)
      raise 'Invalid trainer music categories' unless value.is_a?(Array) && value[0]==1 && value[1].is_a?(Array) && value[2].is_a?(Array)
      @categories_data=value;@categories_stamp=stamp
    end
    @categories_data
  rescue StandardError
    [1,[],[]]
  end
  def self.gym_trainer?(trainer)
    id=trainer.respond_to?(:trainer_type) ? trainer.trainer_type : trainer
    data=GameData::TrainerType.try_get(id)
    return false unless data
    name=data.respond_to?(:real_name) ? data.real_name : data.name
    return true if categories[1].include?(data.id.to_s) || name.to_s.match?(/\bgym\s+leader\b/i)
    return false unless trainer.respond_to?(:name)
    name=trainer.name.to_s.sub(/\s*\([^()]*\)\s*\z/,'').strip
    categories[2].any? { |row| row[0]==data.id.to_s && row[1]==name }
  end
  def self.trainer_category(trainers)
    Array(trainers).any? { |t| gym_trainer?(t) } ? 'gym' : 'trainer'
  end
  def self.begin_battle
    @battle_context={selected:{},category:nil}
  end
  def self.end_battle; @battle_context=nil; end
  def self.with_battle
    previous=@battle_context
    begin_battle
    yield
  ensure
    @battle_context=previous
  end
  def self.random_track(key,tracks)
    available=tracks.is_a?(Array) ? tracks.select { |p| valid_track?(p) }.uniq : []
    return nil if available.empty?
    cached=@battle_context && @battle_context[:selected][key]
    return cached if available.include?(cached)
    @last_track ||= {}
    choices=available.length>1 ? available.reject { |p| p==@last_track[key] } : available
    @music_rng ||= Random.new
    selected=choices[@music_rng.rand(choices.length)]
    @last_track[key]=selected
    @battle_context[:selected][key]=selected if @battle_context
    selected
  end
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
  # Kanto-only compiled map scope. Never write to the Decades music config.
  KANTO_PATH='Data/blue-kanto-music.txt'
  def self.kanto_region?
    return false unless defined?(BlueRegionalPolicy) && BlueRegionalPolicy.respond_to?(:state)
    state=BlueRegionalPolicy.state
    state.is_a?(Hash) && state['current']=='KANTO'
  rescue StandardError
    false
  end
  def self.kanto_data
    return [{},{},{}] unless File.file?(KANTO_PATH)
    stamp=[File.mtime(KANTO_PATH).to_f,File.size(KANTO_PATH)]
    return @kanto_data if @kanto_stamp==stamp && @kanto_data
    lines=File.readlines(KANTO_PATH)
    header=lines.shift.to_s.chomp.split("\t")
    raise 'Invalid Kanto music version' unless header.length==3 && header[0]=='BLUE_KANTO_MUSIC_V1' && header[1]=='KANTO' && header[2].match?(/\A[0-9a-f]{64}\z/)
    scope={};maps={};battles={}
    lines.each do |line|
      parts=line.chomp.split("\t")
      case parts[0]
      when 'SCOPE'
        raise 'Invalid Kanto map scope' unless parts.length==4 && parts[1].match?(/\A[1-9]\d*\z/) && parts[2].match?(/\A[A-Z0-9_]+\z/) && ['0','1'].include?(parts[3])
        id=parts[1].to_i
        raise 'Duplicate Kanto map scope' if scope.key?(id)
        scope[id]=[parts[2],parts[3]=='1']
      when 'MAP','BATTLE'
        raise 'Invalid Kanto BGM binding' unless parts.length==5 && parts[2].start_with?('Kanto/') && parts[3].match?(/\A\d+\z/) && parts[4].match?(/\A\d+\z/)
        id=parts[1]
        if parts[0]=='MAP'
          raise 'Invalid Kanto map binding' unless id.match?(/\A[1-9]\d*\z/) && scope.key?(id.to_i) && !scope[id.to_i][1]
          id=id.to_i
          dest=maps
        else
          raise 'Invalid Kanto battle binding' unless ['wild','trainer','gym','legendary','champion','wildVictory','trainerVictory','gymVictory'].include?(id)
          dest=battles
        end
        raise 'Duplicate Kanto binding' if dest.key?(id)
        volume=parts[3].to_i; pitch=parts[4].to_i
        raise 'Invalid Kanto music volume/pitch' unless (0..100).include?(volume) && (50..150).include?(pitch)
        dest[id]=[parts[2],volume,pitch]
      else
        raise 'Unknown Kanto music binding'
      end
    end
    @kanto_data=[scope,maps,battles]
    @kanto_stamp=stamp
    @kanto_data
  rescue StandardError
    [{},{},{}]
  end
  def self.kanto_audio_for(kind,key)
    return nil unless kanto_region?
    scope,maps,battles=kanto_data
    map_id=(kind=='map' ? key : ($game_map && $game_map.map_id))
    return nil unless map_id && scope.key?(map_id.to_i)
    row=(kind=='map' ? maps[map_id.to_i] : battles[key.to_s])
    return nil unless row && valid_track?(row[0])
    RPG::AudioFile.new(row[0],row[1],row[2])
  end
  def self.entry(scope,key)
    rows=config[scope=='map' ? 2 : 1]
    found=rows.find { |row| row.is_a?(Array) && row[0].to_s==key.to_s }
    found
  end
  def self.audio_for(scope,key)
    row=entry(scope,key)
    return nil unless row
    return RPG::AudioFile.new('',100,100) if row[1]=='mute'
    if row[1]=='random' && scope=='global' && ['wild','trainer','gym'].include?(key)
      name=random_track(key,row[2])
    elsif row[1]=='custom'
      name=row[2] if valid_track?(row[2])
    end
    name ? RPG::AudioFile.new(name,row[3].to_i.clamp(0,100),row[4].to_i.clamp(50,150)) : nil
  end
  def self.battle_audio(key)
    key=(@battle_context[:category] ||= key) if @battle_context
    row=entry('global',key)
    # The author's random pools replace fixed event themes in these categories.
    if row && row[1]=='random'
      selected=audio_for('global',key)
      return selected if selected
    end
    return nil if $PokemonGlobal.nextBattleBGM
    return nil if row && row[1]=='random'
    return audio_for('global',key) if row
    kanto_audio_for('battle',key)
  end
  def self.apply_map(game_map)
    map=game_map.instance_variable_get(:@map)
    return unless map
    original=game_map.instance_variable_get(:@blue_music_original)
    unless original
      original=[map.autoplay_bgm,map.bgm.clone]
      game_map.instance_variable_set(:@blue_music_original,original)
    end
    row=entry('map',game_map.map_id)
    audio=row ? audio_for('map',game_map.map_id) : kanto_audio_for('map',game_map.map_id)
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
      BlueMusic.battle_audio('wild') || super
    end
    def pbGetTrainerBattleBGM(*args)
      BlueMusic.battle_audio(BlueMusic.trainer_category(args[0])) || super
    end
    def pbGetTrainerBattleBGMFromType(*args)
      BlueMusic.battle_audio(BlueMusic.trainer_category(args[0])) || super
    end
    def pbGetWildVictoryBGM(*args)
      return super if $PokemonGlobal.nextBattleVictoryBGM
      row=BlueMusic.entry('global','wildVictory')
      audio=row ? BlueMusic.audio_for('global','wildVictory') : BlueMusic.kanto_audio_for('battle','wildVictory')
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
    def pbGetTrainerVictoryBGM(*args)
      return super if $PokemonGlobal.nextBattleVictoryBGM
      row=BlueMusic.entry('global','trainerVictory')
      audio=row ? BlueMusic.audio_for('global','trainerVictory') : BlueMusic.kanto_audio_for('battle','trainerVictory')
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
  end
  module EntryScope
    def start_core(*args)
      BlueMusic.with_battle { super(*args) }
    end
  end
  module PrepareMusic
    def prepare_battle(battle)
      context=BlueMusic.instance_variable_get(:@battle_context)
      context[:category]=battle.wildBattle? ? 'wild' : BlueMusic.trainer_category(battle.opponent) if context
      super
    end
  end
  module LabScope
    def battle(*args)
      BlueMusic.with_battle { super(*args) }
    end
  end
  def self.install
    Game_Map.prepend(MapAudio) unless Game_Map.ancestors.include?(MapAudio)
    Object.prepend(BattleAudio) unless Object.ancestors.include?(BattleAudio)
    [WildBattle,TrainerBattle].each { |k| k.singleton_class.prepend(EntryScope) unless k.singleton_class.ancestors.include?(EntryScope) }
    BattleCreationHelperMethods.singleton_class.prepend(PrepareMusic) unless BattleCreationHelperMethods.singleton_class.ancestors.include?(PrepareMusic)
    if defined?(BlueBattleLab) && BlueBattleLab.respond_to?(:battle)
      BlueBattleLab.singleton_class.prepend(LabScope) unless BlueBattleLab.singleton_class.ancestors.include?(LabScope)
    end
    EventHandlers.add(:on_start_battle,:blue_random_music,proc { |*args| BlueMusic.begin_battle })
    EventHandlers.add(:on_end_battle,:blue_random_music,proc { |*args| BlueMusic.end_battle })
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
    run_random_checks(lines,check) if respond_to?(:run_random_checks)
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
