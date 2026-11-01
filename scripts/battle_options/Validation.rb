# Native regression checks run only with the opt-in laboratory smoke request.
module BlueBattleOptions
  module TestMenus
    def choose(title,commands,default=0)
      queue=BlueBattleOptions.instance_variable_get(:@test_menu_choices)
      return super unless queue
      raise 'Test menu exhausted' if queue.empty?
      queue.shift
    end
  end
  singleton_class.prepend(TestMenus)
  def self.run_checks
    lines=[]
    check=proc { |label,ok| lines << "#{ok ? 'PASS' : 'FAIL'} | #{label}";raise label unless ok }
    original_rules=$PokemonSystem.blue_battle_mechanics
    original_lab=@lab_rules
    original_quality=$PokemonSystem.blue_sprite_quality
    original_map=$game_map
    @lab_rules=defaults;$PokemonSystem.blue_battle_mechanics=defaults
    @test_menu_choices=[0,2,6];mechanics_menu(:lab);@test_menu_choices=nil
    check.call('Independent lab menu toggles',rules(:lab)=={'tera'=>false,'dynamax'=>true,'mega'=>false,'zmove'=>true})
    check.call('Lab choices do not change Battle Mode',snapshot==defaults)
    $PokemonSystem.blue_battle_mechanics=defaults.merge('zmove'=>false)
    $game_map=Game_Map.new;$game_map.setup(33)
    scoped=Battle.new(Battle::DebugSceneNoVisuals.new,[BlueBattleLab.build(:PIKACHU,50)],[BlueBattleLab.build(:MAGIKARP,50)],[$player],nil)
    check.call('Battle Mode copies its saved mechanic choices',scoped.instance_variable_get(:@blue_mechanics)['zmove']==false)
    $game_map=original_map
    $PokemonSystem.blue_battle_mechanics=defaults
    @lab_rules=defaults
    MechanicValidation.run(lines,check)
    check.call('Only battle/test areas use mode rules',MAPS.all? { |id| battle_area?(id) } && !battle_area?(1))
    species=author_species
    check.call('Author generator exposes 52 ready species and 12 Mega choices',species.length==64 && species.count { |s| s.form>0 }==12)
    check.call('Incomplete species stay out of generator',!species.any? { |s| [:HORSAND,:SPINEDRA,:STINGDRA,:GILLBLE,:GALBITE,:GARCHOLT,:PRIMALNOTIC].include?(s.id) })
    mon=generate(:CAVEFANG,50)
    check.call('Author Pokemon can be constructed at selected level',mon.species==:CAVEFANG && mon.level==50 && mon.hp==mon.totalhp)
    mega=species.find { |s| s.species==:ARBOK && s.form>0 }
    mon=generate(mega.id,50)
    check.call('Mega choice generates base with its own stone',mon.species==:ARBOK && mon.form==0 && mon.item_id==mega.mega_stone)
    original_mega=BlueBattleLab.build(mega.id,50)
    copied_mega=Marshal.load(Marshal.dump(original_mega))
    prepare_lab_party([copied_mega],defaults.merge('mega'=>false))
    check.call('Disabled Mega normalizes only the battle copy',!copied_mega.mega? && original_mega.mega?)
    begin
      generate(:PRIMALNOTIC,50);raise 'Draft was generated'
    rescue ArgumentError
      check.call('Draft generator request is rejected',true)
    end
    # Both native eligibility and registration are tested on both sides. No
    # numbered switches are changed by disabling a mechanic.
    ally=BlueBattleLab.build(:ARBOK,50);ally.item=:DPARBOKITE
    foe=BlueBattleLab.build(:ARBOK,50);foe.item=:DPARBOKITE
    battle,_=BlueRadicalAI::Validation.fixture([ally],[foe],'single','engine')
    battle.items=[[:MEGARING,:DYNAMAXBAND,:ZRING,:TERAORB]]
    battle.instance_variable_set(:@blue_mechanics,defaults)
    [0,1].each { |index| battle.pbUnregisterMegaEvolution(index) }
    lines << "MEGA_BASELINE | #{[0,1].map { |i| [battle.pbCanMegaEvolve?(i),battle.battlers[i].hasMega?,battle.pbHasMegaRing?(i)] }.inspect}"
    check.call('Mega is eligible before disabling',battle.pbCanMegaEvolve?(0) && battle.pbCanMegaEvolve?(1))
    METHODS.each do |key,names|
      can,register,registered,activate=names
      [0,1].each do |index|
        battle.instance_variable_set(:@blue_mechanics,defaults.merge(key=>false))
        check.call("#{key} eligibility blocked on side #{index}",!battle.public_send('pbCan'+can,index))
        battle.public_send('pbRegister'+register,index)
        battle.public_send('pbToggleRegistered'+register,index)
        check.call("#{key} registration blocked on side #{index}",!battle.public_send('pbRegistered'+registered,index))
        before=[battle.battlers[index].form,battle.battlers[index].pokemon.form]
        battle.public_send('pb'+activate,index) unless key=='zmove'
        check.call("#{key} scripted activation blocked on side #{index}",before==[battle.battlers[index].form,battle.battlers[index].pokemon.form])
        battle.instance_variable_set(:@blue_mechanics,defaults)
        battle.public_send('pbRegister'+register,index)
        check.call("#{key} registration can be restored on side #{index}",battle.public_send('pbRegistered'+registered,index))
        battle.public_send('pbUnregister'+register,index)
      end
    end
    # Construct actual map instances; injection is memory-only and idempotent.
    MAPS.each do |id|
      file=format('Data/Map%03d.rxdata',id);original=File.binread(file)
      map=Game_Map.new;map.setup(id)
      events=map.instance_variable_get(:@map).events
      added=events.values.select { |e| e.name=='Blue Dessastre Paradoxal' }
      check.call("Map #{id} gets exactly one author Poke Ball",added.length==1)
      event=added.first
      check.call("Map #{id} author ball is next to Gen 9",(event.x-30).abs<=4 && (event.y-24).abs<=4 && !event.pages.first.graphic.character_name.empty?)
      check.call("Map #{id} player can approach the ball",reachable_ball?(map,event.x,event.y))
      gen9=events.values.find { |e| e.name=='Gen 9 PKMN Generator' }
      check.call("Map #{id} Gen 9 generator stays accessible",reachable_ball?(map,gen9.x,gen9.y))
      lines << "GENERATOR | map=#{id} x=#{event.x} y=#{event.y}"
      check.call("Map #{id} action opens Blue menu",event.pages.first.list.first.parameters==['BlueBattleOptions.main_menu'])
      inject_generator(map)
      check.call("Map #{id} injection is idempotent",events.values.count { |e| e.name=='Blue Dessastre Paradoxal' }==1)
      check.call("Map #{id} original file preserved",File.binread(file)==original)
    end
    # A real long spritesheet: bounded frame textures, original display size,
    # no changes to source bytes, full native pipeline for Spinda's pixel spots.
    source=GameData::Species.front_sprite_filename(:GREATTUSK);raw=File.binread(source)
    $PokemonSystem.blue_sprite_quality='original'
    wrapper=GameData::Species.sprite_bitmap_from_pokemon(BlueBattleLab.build(:GREATTUSK,50))
    full=[wrapper.width,wrapper.height];count=wrapper.length
    original_bytes=(count+1)*full[0]*full[1]*4;wrapper.dispose
    ['light','minimal'].each do |mode|
      $PokemonSystem.blue_sprite_quality=mode
      wrapper=GameData::Species.sprite_bitmap_from_pokemon(BlueBattleLab.build(:GREATTUSK,50))
      cap,limit=BlueSpriteQuality::PROFILES[mode]
      check.call("#{mode} sprite keeps display size",[wrapper.bitmap.width,wrapper.bitmap.height]==full)
      check.call("#{mode} frame count is bounded",wrapper.length<=limit && wrapper.blue_source_frames==count)
      frames=wrapper.instance_variable_get(:@bitmaps)
      check.call("#{mode} frame resolution is bounded",frames.all? { |b| b.width<=cap && b.height<=cap })
      check.call("#{mode} frame storage is smaller",wrapper.blue_stored_bytes<original_bytes)
      lines << "MEMORY | #{mode}: #{wrapper.blue_stored_bytes} bytes / original #{original_bytes} bytes"
      wrapper.hue_change(30);wrapper.bitmap;wrapper.to_frame('last');wrapper.bitmap
      wrapper.dispose
    end
    wrapper=GameData::Species.sprite_bitmap_from_pokemon(BlueBattleLab.build(:SPINDA,50));wrapper.bitmap;wrapper.dispose
    check.call('Spinda retains native spot pipeline',true)
    check.call('Original sprite file preserved',File.binread(source)==raw)
    check.call('Frame sampling includes first and last',BlueSpriteQuality.indices(154,24).first==0 && BlueSpriteQuality.indices(154,24).last==153)
    $PokemonSystem.blue_sprite_quality='original'
    wrapper=GameData::Species.front_sprite_bitmap(:GREATTUSK)
    check.call('Original quality restores full animation',wrapper.length==count && [wrapper.width,wrapper.height]==full);wrapper.dispose
    lines << 'RESULT=PASS';true
  rescue StandardError => error
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace);lines << 'RESULT=FAIL';false
  ensure
    @test_menu_choices=nil
    @lab_rules=original_lab
    $game_map=original_map if original_map
    $PokemonSystem.blue_battle_mechanics=original_rules
    $PokemonSystem.blue_sprite_quality=original_quality
    wrapper.dispose if wrapper && !wrapper.disposed?
    File.open('Data/blue-battle-options-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
  end
end
