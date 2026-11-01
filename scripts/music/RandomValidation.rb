# Optional checks against the real engine and locally imported audio.
module BlueMusic
  def self.run_random_checks(lines,check)
    previous_testing=@testing;previous_context=@battle_context;previous_last=@last_track;previous_rng=@music_rng
    previous_event=$PokemonGlobal.nextBattleBGM
    previous_bgm=$game_system.getPlayingBGM
    @testing=nil;@battle_context=nil;@last_track={};@music_rng=Random.new(20261101)
    reference=categories[3]
    unless reference && !reference.empty?
      lines << 'SKIP | No local random music collection imported'
      return
    end
    regular=NPCTrainer.new('Regular music test',:YOUNGSTER)
    leader=NPCTrainer.new('Leader music test',:LEADER_Brock)
    check.call('Gym Leader type is classified',trainer_category([leader])=='gym')
    check.call('Regular trainer is not classified as Gym Leader',trainer_category([regular])=='trainer')
    master_pair=categories[2].find { |pair| !categories[1].include?(pair[0]) }
    check.call('Type Master reference exists',!!master_pair)
    master=NPCTrainer.new(master_pair[1]+' (2v2 Full Power)',master_pair[0].to_sym)
    same_class=NPCTrainer.new('Ordinary music test',master_pair[0].to_sym)
    check.call('Campaign Type Master is classified by identity',trainer_category([master])=='gym')
    check.call('Ordinary trainer of the same class stays regular',trainer_category([same_class])=='trainer')
    check.call('Mixed double with a Gym Leader uses gym pool',trainer_category([regular,leader])=='gym')
    lookups={
      'wild'=>proc { pbGetWildBattleBGM([]) },
      'trainer'=>proc { pbGetTrainerBattleBGM([regular]) },
      'gym'=>proc { pbGetTrainerBattleBGM([master]) }
    }
    reference.each do |key,tracks|
      check.call("#{key} reference is nonempty",!tracks.empty?)
      check.call("#{key} files are present",tracks.all? { |name| valid_track?(name) })
      row=entry('global',key)
      next unless row && row[1]=='random'
      expected=row[2].select { |name| valid_track?(name) }.uniq
      sequence=[]
      12.times do
        with_battle do
          first=lookups[key].call
          check.call("#{key} selection belongs to its configured pool",expected.include?(first.name))
          check.call("#{key} repeated lookup keeps the same track",3.times.all? { lookups[key].call.name==first.name })
          sequence << first.name
        end
      end
      check.call("#{key} next battle avoids the previous track",expected.length==1 || sequence.each_cons(2).all? { |a,b| a!=b })
      check.call("#{key} draws more than one track",expected.length==1 || sequence.uniq.length>1)
      $PokemonGlobal.nextBattleBGM=RPG::AudioFile.new('fixed event theme',100,100)
      with_battle { check.call("#{key} random pool replaces fixed event theme",expected.include?(lookups[key].call.name)) }
      $PokemonGlobal.nextBattleBGM=previous_event
    end
    with_battle do
      first=pbGetTrainerBattleBGM([master])
      check.call('Trainer-type lookup retains the Master track',pbGetTrainerBattleBGMFromType(master.trainer_type).name==first.name)
    end
    # Native DBK preparation and transition query must share the actual BGM.
    with_battle do
      one=BlueBattleLab.build(:PIKACHU,50);two=BlueBattleLab.build(:MAGIKARP,5)
      leader.party=[two]
      battle=Battle.new(BlueBattleLab::SmokeScene.new,[one],[two],[$player],[leader])
      BattleCreationHelperMethods.prepare_battle(battle)
      selected=pbGetTrainerBattleBGM([leader])
      check.call('Prepared battle and intro resolve the same random track',battle.default_bgm==selected.name)
    end
    # Missing/removed files fall back safely; one-item lists are valid.
    sample=reference.first[1].first
    @testing=[1,[['wild','random',['BlueRandom/missing.mp3',sample],100,100]],[]]
    with_battle { check.call('Missing tracks are filtered from pool',pbGetWildBattleBGM([]).name==sample) }
    @testing=[1,[['wild','random',['BlueRandom/missing.mp3'],100,100]],[]]
    check.call('Empty usable pool has no custom audio',audio_for('global','wild').nil?)
    @testing=nil
    # Open every supplied track with the actual decoder, muted, without changing
    # the system/master volume. Position must advance, not merely return a path.
    reference.flat_map { |row| row[1] }.uniq.each do |name|
      pbBGMPlay(RPG::AudioFile.new(name,0,100))
      started=System.uptime
      while System.uptime-started<0.2
        Graphics.update
      end
      position=Audio.bgm_pos
      check.call("Native audio decoder advances: #{name}",position && position>0)
    end
    lines << "AUDIO_FILES=#{reference.sum { |row| row[1].length }}"
  ensure
    @testing=previous_testing;@battle_context=previous_context;@last_track=previous_last;@music_rng=previous_rng
    $PokemonGlobal.nextBattleBGM=previous_event
    if previous_bgm && !previous_bgm.name.empty?
      pbBGMPlay(previous_bgm)
    else
      pbBGMStop
    end
  end
end
