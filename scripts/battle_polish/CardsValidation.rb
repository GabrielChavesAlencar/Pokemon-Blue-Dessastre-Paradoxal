# Native UI/sprite proofs with fresh laboratory data and campaign save guards.
module BlueDexCardsValidation
  class HomeScene < BlueDexCards::Scene
    def start;super;BlueDexCardsValidation.shot('blue-dex-home-cards-smoke');end
  end
  class MethodsScene < BlueDexCards::Scene
    def start;super;BlueDexCardsValidation.shot('blue-habitat-method-cards-smoke');end
    def turn(delta);super;BlueDexCardsValidation.shot('blue-habitat-method-page-smoke');end
  end
  class ZoomScene < BlueHabitatMap::Scene
    attr_reader :states
    def refresh
      super
      (@states ||= []) << [@zoom_index,@source_x,@source_y,@map_width/@scale,@map_height/@scale,@raw.width,@raw.height]
    end
    def start
      super
      BlueDexCardsValidation.shot('blue-habitat-zoom-smoke')
      pan(100_000,100_000);center;refresh
    end
  end
  module LearnTrace
    def pbUpdate
      super
      if @blue_move_picking && BlueDexCardsValidation.instance_variable_get(:@learn_shot)
        BlueDexCardsValidation.instance_variable_set(:@learn_shot,false)
        BlueDexCardsValidation.shot('blue-learn-move-mouse-smoke')
      end
    end
  end
  module RelearnTrace
    def pbUpdate
      super
      if @blue_relearn_picking && BlueDexCardsValidation.instance_variable_get(:@relearn_shot)
        BlueDexCardsValidation.instance_variable_set(:@relearn_shot,false)
        BlueDexCardsValidation.shot('blue-relearn-mouse-smoke')
      end
    end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.cards
    commands=[_INTL('Pokémon list'),_INTL('Habitat Dex'),_INTL('Back')]
    scene=HomeScene.new(_INTL('Pokédex'),commands,BlueDexCards.home)
    chosen=BlueTouchValidation.drive([[368,188]]) { scene.run }
    check(chosen==1,'Large Habitat Dex card selects its original native menu branch by mouse')
    scene=BlueDexCards::Scene.new(_INTL('Pokédex'),commands,BlueDexCards.home)
    check(BlueTouchValidation.drive([[450,356]]) { scene.run }==2,'Card Back button preserves the original Dex cancel branch')
    open=BlueHabitat.method(:open);@opened=0
    BlueHabitat.define_singleton_method(:open) { BlueDexCardsValidation.instance_variable_set(:@opened,1) }
    BlueTouchValidation.drive([[368,188],nil,[450,356]]) { PokemonPokedexScreen.new(Object.new).pbStartScreen }
    check(@opened==1,'The actual Pokedex entrance uses the square-card renderer and opens Habitat Dex')
    BlueHabitat.define_singleton_method(:open,open);open=nil
    types=[:Land,:RockSmash,:SuperRod,:Water,:HeadbuttHigh,:HeadbuttLow,:OldRod,:GoodRod]
    labels=[_INTL('View on map')]+types.map { |type| _INTL(BlueHabitat::METHODS[type]) }+[_INTL('Other habitats')]
    scene=MethodsScene.new('Cherryhill City',labels,BlueDexCards.methods(types))
    chosen=BlueTouchValidation.drive([[230,356],[104,124]]) { scene.run }
    check(chosen==6,'Encounter-card paging preserves the selected method index on the second page')
    check(scene.pages==2,'Long habitat method menus fit six square cards per page')
  ensure
    BlueHabitat.define_singleton_method(:open,open) if open
  end
  def self.learn
    mon=BlueBattleLab.build(:PIKACHU,50);mon.moves=[:TACKLE,:GROWL,:QUICKATTACK,:THUNDERWAVE].map { |id| Pokemon::Move.new(id) }
    scene=PokemonSummary_Scene.new;scene.pbStartForgetScene([mon],0,:THUNDERBOLT);before=Marshal.dump(mon);@learn_shot=true
    result=BlueTouchValidation.drive([[370,176]]) { scene.pbChooseMoveToForget(:THUNDERBOLT) }
    check(result==2,'Clicking the third move returns slot 2 through the native learning loop')
    check(Marshal.dump(mon)==before,'Selecting a replacement does not bypass native learning confirmations or alter moves/PP itself')
    scene.pbEndScene;scene=nil
    scene=PokemonSummary_Scene.new;scene.pbStartForgetScene([mon],0,:THUNDERBOLT)
    result=BlueTouchValidation.drive([[40,366]]) { scene.pbChooseMoveToForget(:THUNDERBOLT) }
    check(result==-1,'The learning Cancel button returns the native cancel value by mouse')
    scene.pbEndScene;scene=nil
    mon.moves=mon.moves.first(2)
    scene=PokemonSummary_Scene.new;scene.pbStartForgetScene([mon],0,:THUNDERBOLT)
    result=BlueTouchValidation.drive([[370,176],[40,366]]) { scene.pbChooseMoveToForget(:THUNDERBOLT) }
    check(result==-1,'Empty move slots cannot be selected by clicking')
    scene.pbEndScene;scene=nil
    mon.moves=[:TACKLE,:GROWL,:QUICKATTACK,:THUNDERWAVE].map { |id| Pokemon::Move.new(id) }
    scene=PokemonSummary_Scene.new;scene.pbStartForgetScene([mon],0,nil)
    result=BlueTouchValidation.drive([[370,316]]) { scene.pbChooseMoveToForget(nil) }
    check(result==3,'The existing-move forgetting screen also selects the correct fourth slot by mouse')
    scene.pbEndScene;scene=nil
    moves=[:TACKLE,:GROWL,:QUICKATTACK,:THUNDERWAVE,:THUNDERBOLT,:PROTECT]
    scene=MoveRelearner_Scene.new;scene.pbStartScene(mon,moves);@relearn_shot=true
    result=BlueTouchValidation.drive([[100,240]]) { scene.pbChooseMove }
    check(result==:QUICKATTACK,'The native move reminder also accepts a click on its painted third row')
    result=BlueTouchValidation.drive([[80,366],[80,366],[80,366],[100,304]]) { scene.pbChooseMove }
    check(result==moves[scene.instance_variable_get(:@sprites)['commands'].index] && result==:PROTECT,'Move reminder arrows scroll and clicks retain the real scrolled move index')
    result=BlueTouchValidation.drive([[430,22]]) { scene.pbChooseMove }
    check(result.nil?,'Move reminder Back button uses its native cancel path')
    scene.pbEndScene;scene=nil
  ensure
    @learn_shot=false;@relearn_shot=false;scene&.pbEndScene
  end
  def self.zoom
    map=$game_map;$game_map=Game_Map.new;$game_map.setup(77)
    scene=ZoomScene.new(77,BlueHabitatMap.position(77))
    BlueTouchValidation.drive([[90,364],[310,364],[180,364],[450,364]]) { scene.run }
    check(scene.states.first[0]==2,'Habitat map opens at 3x, centered on the selected habitat')
    check(scene.states.any? { |s| s[0]==3 } && scene.states.last[0]==0,'Map plus, region overview and center controls work by mouse')
    check(scene.states.all? { |i,x,y,w,h,rw,rh| x>=0 && y>=0 && x+w<=rw+1 && y+h<=rh+1 },'Zoom and extreme panning never sample outside the regional map')
  ensure
    $game_map=map if map
  end
  def self.facings
    quality=$PokemonSystem.blue_sprite_quality
    allies=[:AMMNOID,:CEPHALONID].map { |id| BlueBattleLab.build(id,50) }
    foes=[:AMMNOID,:PIKACHU].map { |id| BlueBattleLab.build(id,50) }
    battle,_=BlueRadicalAI::Validation.fixture(allies,foes,'double','engine')
    battle.instance_variable_set(:@blue_lab_battle,true);battle.backdrop='indoor1';battle.environment=:None;battle.time=0
    scene=BlueBattleUIValidation::Scene.new;battle.instance_variable_set(:@scene,scene)
    scene.pbStartBattle(battle);BlueBattleOptions::MechanicValidation.show_battlers(scene,battle)
    sprites=scene.instance_variable_get(:@sprites);shot('blue-ammnoid-facing-smoke')
    check(sprites['pokemon_0'].mirror && !sprites['pokemon_1'].mirror && !sprites['pokemon_2'].mirror,'Doubles mirror only the inverted Ammnoid back; opponent/front and Cephalonid stay unchanged')
    check(!!scene.pbFindMoveAnimation(:ROLLOUT,0,0),'Native Rollout animation exists for the orientation regression')
    scene.pbAnimation(:ROLLOUT,battle.battlers[0],[battle.battlers[1]],0)
    check(sprites['pokemon_0'].mirror && !sprites['pokemon_1'].mirror,'A real Rollout animation restores the corrected Ammnoid back orientation')
    ['original','light','minimal'].each do |mode|
      $PokemonSystem.blue_sprite_quality=mode
      [false,true].each do |shiny|
        mon=BlueBattleLab.build(:AMMNOID,50);mon.shiny=shiny
        scene.pbChangePokemon(0,mon);scene.pbChangePokemon(2,mon)
        check(sprites['pokemon_0'].mirror && sprites['pokemon_2'].mirror,'Both allied Ammnoid slots face right: '+mode+' shiny='+shiny.to_s)
        scene.pbChangePokemon(0,BlueBattleLab.build(:PIKACHU,50))
        check(!sprites['pokemon_0'].mirror,'Replacing Ammnoid restores ordinary sprite orientation: '+mode)
      end
    end
    $PokemonSystem.blue_sprite_quality='minimal';count=0
    GameData::Species.each do |data|
      next unless data.flags.include?('DessastreParadoxal')
      mon=BlueBattleLab.build(data.id,50);scene.pbChangePokemon(0,mon)
      check(sprites['pokemon_0'].mirror==BlueFanBackFacing::FLIPPED.include?(mon.species),'Native author back-facing rule: '+data.id.to_s)
      count+=1;Graphics.update if count%10==0
    end
    check(count>=60,'All battle-ready author species and Mega forms were checked in the engine')
    @lines << 'NATIVE_AUTHOR_FORMS_CHECKED='+count.to_s
    scene.pbEndBattle(0);scene=nil
  ensure
    $PokemonSystem.blue_sprite_quality=quality if quality;scene&.pbEndBattle(0)
  end
  def self.run
    @lines=[];pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?);lang=$PokemonSystem.blue_locale
    BlueLabPointer.define_singleton_method(:enabled?) { true };BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    PokemonSummary_Scene.prepend(LearnTrace) unless PokemonSummary_Scene.ancestors.include?(LearnTrace)
    MoveRelearner_Scene.prepend(RelearnTrace) unless MoveRelearner_Scene.ancestors.include?(RelearnTrace)
    $PokemonSystem.blue_locale='pt-BR';Graphics.transition(0)
    cards;learn;zoom;facings;@lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @learn_shot=false;@relearn_shot=false;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer;BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.open('Data/blue-dex-cards-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
