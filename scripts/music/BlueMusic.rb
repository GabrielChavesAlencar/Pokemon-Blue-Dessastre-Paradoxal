# Own music overrides. Original RPG maps, PBS and events remain on disk unchanged.
require 'digest'
module BlueMusic
  PATH='Data/blue-music.rxdata'
  CATEGORIES_PATH='Data/blue-music-categories.rxdata'
  KANTO_GYM_TYPES=%w[BLUE_KANTO_LEADER BLUE_KANTO_LEADER_MISTY BLUE_KANTO_LEADER_SURGE BLUE_KANTO_LEADER_ERIKA BLUE_KANTO_LEADER_KOGA BLUE_KANTO_LEADER_SABRINA BLUE_KANTO_LEADER_BLAINE BLUE_KANTO_LEADER_GIOVANNI].freeze
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
    # on_start_battle can fire after the preparer classified the opponents.
    # Keep the selected class and track for the *same* ongoing encounter.
    @battle_context ||= {selected:{},category:nil}
  end
  def self.end_battle; @battle_context=nil; end
  def self.with_battle
    previous=@battle_context
    # A genuinely new encounter gets a fresh selection, including doubles.
    @battle_context={selected:{},category:nil}
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
    return true if state.is_a?(Hash) && state['current']=='KANTO'
    # The disposable standalone pilot has Kanto pilot.json, but deliberately
    # has no Data/blue-kanto-install.json (required by RegionalPolicy.state).
    # Only permit this fallback inside that isolated pilot with a real Kanto save.
    return false unless File.file?('Kanto pilot.json') && defined?(BlueRegions) && BlueRegions.active?
    stored=$PokemonGlobal && $PokemonGlobal.blue_regions
    stored.is_a?(Hash) && stored['version']==1 && stored['current']=='KANTO'
  rescue StandardError
    false
  end
  def self.kanto_data
    return [{},{},{},{},{},{},{}] unless File.file?(KANTO_PATH)
    stamp=[File.mtime(KANTO_PATH).to_f,File.size(KANTO_PATH)]
    return @kanto_data if @kanto_stamp==stamp && @kanto_data
    lines=File.readlines(KANTO_PATH)
    header=lines.shift.to_s.chomp.split("\t")
    raise 'Invalid Kanto music version' unless header.length==3 && header[0]=='BLUE_KANTO_MUSIC_V1' && header[1]=='KANTO' && header[2].match?(/\A[0-9a-f]{64}\z/)
    scope={};maps={};battles={};transports={};defaults={};me_events={};scenes={}
    lines.each do |line|
      parts=line.chomp.split("\t")
      case parts[0]
      when 'SCOPE'
        raise 'Invalid Kanto map scope' unless parts.length==4 && parts[1].match?(/\A[1-9]\d*\z/) && parts[2].match?(/\A[A-Z0-9_]+\z/) && ['0','1'].include?(parts[3])
        id=parts[1].to_i
        raise 'Duplicate Kanto map scope' if scope.key?(id)
        scope[id]=[parts[2],parts[3]=='1']
      when 'BASEPOOL'
        raise 'Invalid Kanto default pool signature' unless parts.length==3 && %w[wild trainer gym].include?(parts[1]) && parts[2].match?(/\A[0-9a-f]{64}\z/)
        raise 'Duplicate default pool signature' if defaults.key?(parts[1])
        defaults[parts[1]]=parts[2]
      when 'ME'
        raise 'Invalid Kanto ME binding' unless parts.length==5 &&
          %w[obtained_pokemon obtained_item healed badge_awarded evolved caught].include?(parts[1]) &&
          parts[2].start_with?('Kanto/') && parts[2].end_with?('.mp3') &&
          parts[3].match?(/\A\d+\z/) && parts[4].match?(/\A\d+\z/)
        raise 'Duplicate Kanto ME event' if me_events.key?(parts[1])
        volume=parts[3].to_i; pitch=parts[4].to_i
        raise 'Invalid Kanto ME volume/pitch' unless (0..100).include?(volume) && (50..150).include?(pitch)
        me_events[parts[1]]=[parts[2],volume,pitch]
      when 'SCENE'
        raise 'Invalid Kanto scene binding' unless parts.length==5 &&
          %w[pilot_title oak_talk rival_appears evolution hall_of_fame].include?(parts[1]) &&
          parts[2].start_with?('Kanto/') && parts[2].end_with?('.mp3') &&
          parts[3].match?(/\A\d+\z/) && parts[4].match?(/\A\d+\z/)
        raise 'Duplicate Kanto scene' if scenes.key?(parts[1])
        volume=parts[3].to_i; pitch=parts[4].to_i
        raise 'Invalid Kanto scene volume/pitch' unless (0..100).include?(volume) && (50..150).include?(pitch)
        scenes[parts[1]]=[parts[2],volume,pitch]
      when 'MAP','BATTLE','TRANSPORT'
        raise 'Invalid Kanto BGM binding' unless parts.length==5 && parts[2].start_with?('Kanto/') && parts[3].match?(/\A\d+\z/) && parts[4].match?(/\A\d+\z/)
        id=parts[1]
        if parts[0]=='MAP'
          raise 'Invalid Kanto map binding' unless id.match?(/\A[1-9]\d*\z/) && scope.key?(id.to_i) && !scope[id.to_i][1]
          id=id.to_i
          dest=maps
        elsif parts[0]=='BATTLE'
          raise 'Invalid Kanto battle binding' unless ['wild','trainer','gym','legendary','champion','wildVictory','trainerVictory','gymVictory'].include?(id)
          dest=battles
        else
          raise 'Invalid Kanto transport mode' unless ['bicycle','surf'].include?(id)
          dest=transports
        end
        raise 'Duplicate Kanto binding' if dest.key?(id)
        volume=parts[3].to_i; pitch=parts[4].to_i
        raise 'Invalid Kanto music volume/pitch' unless (0..100).include?(volume) && (50..150).include?(pitch)
        dest[id]=[parts[2],volume,pitch]
      else
        raise 'Unknown Kanto music binding'
      end
    end
    @kanto_data=[scope,maps,battles,transports,defaults,me_events,scenes]
    @kanto_stamp=stamp
    @kanto_data
  rescue StandardError
    [{},{},{},{},{},{},{}]
  end
  def self.kanto_audio_for(kind,key)
    return nil unless kanto_region?
    scope,maps,battles,transports,defaults=kanto_data
    map_id=(kind=='map' ? key : ($game_map && $game_map.map_id))
    return nil unless map_id && scope.key?(map_id.to_i)
    return nil if scope[map_id.to_i][1]
    row=case kind
        when 'map' then maps[map_id.to_i]
        when 'transport' then transports[key.to_s]
        else battles[key.to_s]
        end
    if kind == 'map' && scope[map_id.to_i][0] == 'VIRIDIAN_CITY'
      row ||= maps.find { |id, _| scope[id] && scope[id][0] == 'PEWTER_CITY' }&.last
    end
    return nil unless row && valid_track?(row[0])
    RPG::AudioFile.new(row[0],row[1],row[2])
  end
  # The current map/region must be verified, including before any native
  # Essentials battle or victory hook has a trainer/species to inspect.
  def self.kanto_battle_scope?
    return false unless kanto_region? && $game_map
    scope=kanto_data[0]
    item=scope[$game_map.map_id]
    !!(item && !item[1])
  rescue StandardError
    false
  end
  def self.kanto_factory_pool?(key,row)
    return false unless row && row[1]=='random' && row[2].is_a?(Array)
    expected=kanto_data[4][key]
    return false unless expected
    payload=[row[3].to_i.to_s,row[4].to_i.to_s,*row[2]]
    Digest::SHA256.hexdigest(payload.join("\n"))==expected
  end
  def self.kanto_map_symbol?(symbol)
    return false unless kanto_battle_scope?
    kanto_data[0][$game_map.map_id][0]==symbol
  end
  def self.kanto_trainer_kind(trainers)
    return nil unless kanto_battle_scope?
    list=Array(trainers).compact
    return nil if list.empty?
    types=list.map { |t| (t.respond_to?(:trainer_type) ? t.trainer_type : t).to_s }
    return nil unless types.all? { |t| t.start_with?('BLUE_KANTO_') }
    if types.include?('BLUE_KANTO_CHAMPION_BLUE')
      # The final Blue and the early rival have different verified types.
      # Also demand the exact League room and the active League sequence.
      return nil unless types==['BLUE_KANTO_CHAMPION_BLUE'] &&
        list[0].respond_to?(:name) && list[0].name.to_s=='Blue' &&
        kanto_map_symbol?('CHAMPION_HALL') && defined?(BlueKantoPilot) &&
        BlueKantoPilot.respond_to?(:league_active?) && BlueKantoPilot.league_active?
      return 'champion'
    end
    if types.length == 1 && (elite = types[0].match(/\ABLUE_KANTO_ELITE_(LORELEI|BRUNO|AGATHA|LANCE)\z/))
      return 'gym' if kanto_map_symbol?("ELITE_#{elite[1]}_ROOM")
    end
    return 'gym' if types.any? { |t| KANTO_GYM_TYPES.include?(t) }
    'trainer'
  end
  def self.legendary_wild?(pkmn)
    return false unless pkmn
    data=pkmn.respond_to?(:species_data) ? pkmn.species_data : nil
    if !data && defined?(GameData::Species)
      species=pkmn.respond_to?(:species) ? pkmn.species : pkmn
      data=GameData::Species.try_get(species)
    end
    return false unless data && data.respond_to?(:flags)
    flags=data.flags
    if data.respond_to?(:form) && data.form!=0 && data.respond_to?(:species) &&
       defined?(GameData::Species)
      base=GameData::Species.try_get(data.species)
      flags=flags+base.flags if base && base.respond_to?(:flags)
    end
    flags.include?('Legendary')
  rescue StandardError
    false
  end
  def self.kanto_wild_kind(encounters)
    return nil unless kanto_battle_scope?
    Array(encounters).compact.any? { |pkmn| legendary_wild?(pkmn) } ? 'legendary' : 'wild'
  end
  def self.kanto_trainer_victory_kind(opponents=nil)
    return nil unless kanto_battle_scope?
    context=@battle_context
    if context && context.key?(:kanto_eligible)
      return nil unless context[:kanto_eligible]
      return context[:category]=='gym' ? 'gymVictory' : 'trainerVictory'
    end
    # Without context, use the actual Kanto trainer identity, not the name
    # or a provisional borrowed Decades portrait. Foreign types stay native.
    kind=kanto_trainer_kind(opponents)
    return nil unless kind
    kind=='gym' ? 'gymVictory' : 'trainerVictory'
  end
  # ME uses the native Essentials sound engine (Audio/ME), which pauses and
  # resumes the already playing map/battle BGM. Never force a new BGM on return.
  # No global title override: Kanto has a distinct experimental executable,
  # and the regional title track must not touch the Decades Game.exe title.
  def self.kanto_pilot_title_audio
    return nil unless File.file?('Kanto pilot.json') &&
      !File.file?('Data/blue-kanto-install.json') && kanto_data[0].length==142
    row=kanto_data[6]['pilot_title']
    return nil unless row && valid_track?(row[0])
    RPG::AudioFile.new(row[0],row[1],row[2])
  end
  def self.kanto_scene_audio(name)
    return nil if name.to_s=='pilot_title' || !kanto_battle_scope?
    row=kanto_data[6][name.to_s]
    return nil unless row && valid_track?(row[0])
    RPG::AudioFile.new(row[0],row[1],row[2])
  end
  def self.current_bgm
    return nil unless defined?($game_system) && $game_system
    if $game_system.respond_to?(:getPlayingBGM)
      $game_system.getPlayingBGM
    elsif $game_system.respond_to?(:playing_bgm)
      $game_system.playing_bgm
    end
  end
  def self.with_kanto_scene(name)
    audio=kanto_scene_audio(name)
    return yield unless audio
    previous=current_bgm
    old_map=$game_map.map_id
    # Even a truly silent map must be allowed a story cue. A missing
    # previous BGM means restore *silence*, never keep the scene theme looping.
    pbBGMPlay(audio)
    begin
      yield
    ensure
      # Restore the exact previous audio (or silence) only when the scene
      # still owns playback on this same regional map. Never interrupt a
      # newly selected battle/event cue or music after a region transfer.
      current=current_bgm
      if kanto_battle_scope? && $game_map.map_id==old_map &&
        current && current.name==audio.name
        if previous && previous.respond_to?(:name) && !previous.name.to_s.empty?
          pbBGMPlay(previous)
        else
          pbBGMStop
        end
      end
    end
  end
  # Essentials starts "Evolution" BGM only in the actual evolution animation.
  # Replacing this *one* native play call retains the engine's cancellation,
  # success jingle, and subsequent BGM restoration.
  module EvolutionSceneAudio
    private
    def pbBGMPlay(param,volume=nil,pitch=nil)
      replacement=(param=='Evolution' && volume.nil? && pitch.nil?) ?
        BlueMusic.kanto_scene_audio('evolution') : nil
      replacement ? super(replacement) : super(param,volume,pitch)
    end
  end
  def self.kanto_me_audio(event)
    return nil unless kanto_battle_scope?
    row=kanto_data[5][event.to_s]
    return nil unless row
    track=row[0]
    return nil unless track.is_a?(String) &&
      track.start_with?('Kanto/') &&
      !track.include?('..') && !track.include?('\\') &&
      File.file?('Audio/ME/'+track)
    RPG::AudioFile.new(track,row[1],row[2])
  end
  def self.kanto_me_play(event)
    audio=kanto_me_audio(event)
    return false unless audio
    pbMEPlay(audio)
    true
  end
  # Essentials v21.1 plays "Evolution success" only after evolution really
  # completed. "Pkmn get" can precede the actual storage commit, so only the
  # verified KantoPilot silent-gift paths use the regional gift ME.
  module NativeME
    private
    def pbMEPlay(param, volume=nil, pitch=nil)
      event=if param.is_a?(String) && volume.nil? && pitch.nil?
              case param
              when 'Evolution success' then 'evolved'
              end
            end
      replacement=event && BlueMusic.kanto_me_audio(event)
      replacement ? super(replacement) : super(param,volume,pitch)
    end
  end
  # Essentials v21.1 calls pbRecordAndStoreCaughtPokemon after the battle was
  # decided and clears @caughtPokemon *after* storing. Trigger only on a
  # successful return and a genuinely non-empty, now-consumed capture list.
  module CaptureME
    def pbRecordAndStoreCaughtPokemon(*args)
      captured=instance_variable_get(:@caughtPokemon)
      count=captured.is_a?(Array) ? captured.length : 0
      successful=(count>0 && respond_to?(:wildBattle?) && wildBattle?)
      result=super(*args)
      remaining=instance_variable_get(:@caughtPokemon)
      if successful && remaining.is_a?(Array) && remaining.empty?
        BlueMusic.kanto_me_play('caught')
      end
      result
    end
  end
  def self.kanto_vehicle_audio
    return nil unless $PokemonGlobal && $game_map
    return nil if defined?($game_temp) && $game_temp && $game_temp.in_battle
    mode=if $PokemonGlobal.surfing
           'surf'
         elsif $PokemonGlobal.bicycle
           'bicycle'
         end
    mode ? kanto_audio_for('transport',mode) : nil
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
  def self.battle_audio(key,kanto_allowed=true)
    if @battle_context
      key=(@battle_context[:category] ||= key)
      kanto_allowed=false if @battle_context.key?(:kanto_eligible) &&
                              !@battle_context[:kanto_eligible]
    end
    regional=kanto_allowed && kanto_battle_scope?
    pool_key=case key
             when 'legendary' then 'wild'
             when 'champion' then 'trainer'
             else key
             end
    row=entry('global',pool_key)
    # Explicit story music must beat Kanto defaults; Decades keeps the
    # existing author-selected random pool behavior unchanged.
    return nil if regional && $PokemonGlobal && $PokemonGlobal.nextBattleBGM
    if row && row[1]=='random'
      if regional && kanto_factory_pool?(pool_key,row)
        kanto=kanto_audio_for('battle',key)
        return kanto if kanto
      end
      selected=audio_for('global',pool_key)
      return selected if selected
    end
    return nil if $PokemonGlobal && $PokemonGlobal.nextBattleBGM
    return nil if row && row[1]=='random'
    return audio_for('global',pool_key) if row
    regional ? kanto_audio_for('battle',key) : nil
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
      kind=BlueMusic.kanto_wild_kind(args[0]) || 'wild'
      BlueMusic.battle_audio(kind) || super
    end
    def pbGetTrainerBattleBGM(*args)
      kind=BlueMusic.kanto_trainer_kind(args[0])
      BlueMusic.battle_audio(kind || BlueMusic.trainer_category(args[0]),!!kind) || super
    end
    def pbGetTrainerBattleBGMFromType(*args)
      kind=BlueMusic.kanto_trainer_kind(args[0])
      context=BlueMusic.instance_variable_get(:@battle_context)
      kind=context[:category] if context && context[:kanto_eligible]
      BlueMusic.battle_audio(kind || BlueMusic.trainer_category(args[0]),!!kind) || super
    end
    def pbGetWildVictoryBGM(*args)
      return super if $PokemonGlobal && $PokemonGlobal.nextBattleVictoryBGM
      row=BlueMusic.entry('global','wildVictory')
      audio=row ? BlueMusic.audio_for('global','wildVictory') :
                  BlueMusic.kanto_audio_for('battle','wildVictory')
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
    def pbGetTrainerVictoryBGM(*args)
      return super if $PokemonGlobal && $PokemonGlobal.nextBattleVictoryBGM
      row=BlueMusic.entry('global','trainerVictory')
      kind=BlueMusic.kanto_trainer_victory_kind(args[0])
      audio=row ? BlueMusic.audio_for('global','trainerVictory') :
                  (kind && BlueMusic.kanto_audio_for('battle',kind))
      return super unless audio
      audio.name='../../Audio/BGM/'+audio.name unless audio.name.empty?
      audio
    end
  end
  # Essentials uses these entry points when changing maps/loading while mounted;
  # the native dismount/surf-stop already calls map autoplay, restoring its BGM.
  module VehicleAudio
    private
    def pbAutoplayOnTransition(*args)
      audio=BlueMusic.kanto_vehicle_audio
      return super(*args) unless audio
      pbBGMPlay(audio)
    end
    def pbAutoplayOnSave(*args)
      audio=BlueMusic.kanto_vehicle_audio
      return super(*args) unless audio
      pbBGMPlay(audio)
    end
    def pbMountBike(*args)
      result=super(*args)
      audio=BlueMusic.kanto_vehicle_audio
      pbCueBGM(audio,0.4) if audio
      result
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
      if context
        if battle.wildBattle?
          # Essentials v21.1 exposes the opposing side via pbParty(1), not party2.
          # This runs before the first wild encounter transitions to battle.
          regional=BlueMusic.kanto_wild_kind(battle.pbParty(1))
          context[:category]=regional || 'wild'
          context[:kanto_eligible]=!!regional
        else
          regional=BlueMusic.kanto_trainer_kind(battle.opponent)
          context[:category]=regional || BlueMusic.trainer_category(battle.opponent)
          context[:kanto_eligible]=!!regional
        end
      end
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
    Object.prepend(VehicleAudio) unless Object.ancestors.include?(VehicleAudio)
    Object.prepend(NativeME) unless Object.ancestors.include?(NativeME)
    Object.prepend(EvolutionSceneAudio) unless Object.ancestors.include?(EvolutionSceneAudio)
    if defined?(Battle::CatchAndStoreMixin)
      Battle::CatchAndStoreMixin.prepend(CaptureME) unless Battle::CatchAndStoreMixin.ancestors.include?(CaptureME)
    end
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
