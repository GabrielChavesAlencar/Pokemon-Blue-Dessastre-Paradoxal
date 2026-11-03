# Native integration: map opening, per-frame facing, 4x3 Dex and real prize receipts.
module BlueWorldValidation
  module Keys
    def trigger?(key)
      return true if key==Input::BACK && BlueWorldValidation.instance_variable_get(:@close_map)
      return true if key==Input::USE && BlueWorldValidation.instance_variable_get(:@auto_messages)
      super
    end
  end
  module AnimationFrames
    def update
      super
      if BlueWorldValidation.instance_variable_get(:@sample_frames) && @frame && @frame>=0
        [@usersprite,@targetsprite].compact.each do |sprite|
          next unless sprite.respond_to?(:blue_fan_normalized?) && sprite.blue_fan_normalized? && sprite.visible
          BlueWorldValidation.instance_variable_set(:@sampled,(BlueWorldValidation.instance_variable_get(:@sampled)||0)+1)
          raise 'Animation displayed the uncorrected back bitmap' if sprite.bitmap.equal?(sprite.instance_variable_get(:@_iconBitmap).bitmap)
        end
      end
    end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.maps
    original=$game_map;visited=$PokemonGlobal.visitedMaps.dup;scene=nil
    [77,92].each do |id|
      $game_map=Game_Map.new;$game_map.setup(id);$PokemonGlobal.visitedMaps.clear
      scene=PokemonRegionMap_Scene.new(-1,false);scene.pbStartScene
      check(scene.instance_variable_get(:@regionLimits)[:mapWidth]>0,'Pokegear native map opens with no visited flags, including interior map '+id.to_s)
      shot('blue-pokegear-map-smoke') if id==77
      @close_map=true;result=scene.pbMapScene;@close_map=false;scene.pbEndScene;scene=nil
      check(!result && $PokemonGlobal.visitedMaps.empty?,'Closing the map grants no Fly destination or artificial visited flags')
    end
  ensure
    @close_map=false;$game_map=original if original;$PokemonGlobal.visitedMaps.replace(visited) if visited
    if scene
      [:@sprites,:@spritesMap].each { |key| hash=scene.instance_variable_get(key);pbDisposeSpriteHash(hash) if hash }
      [:@viewport,:@viewportCursor,:@viewportMap,:@FadeSprite,:@FadeViewport].each { |key| obj=scene.instance_variable_get(key);obj.dispose if obj && !obj.disposed? }
    end
  end
  def self.dex
    ids=[:PIKACHU,:BULBASAUR,:CHARMANDER,:SQUIRTLE,:EEVEE,:MAGIKARP,:DRATINI,:AMMNOID,:CEPHALONID,:CAVEFANG,:ARCHGUTOR,:GASTLY,:SNORLAX]
    rows=ids.map { |id| {species:id,name:GameData::Species.get(id).name,status: :seen,rods:BlueFishing::RODS} }
    scene=BlueHabitat::Scene.new('Route 1',_INTL('Fishing'),rows);scene.start
    sprites=scene.instance_variable_get(:@sprites)
    check(sprites.keys.grep(/^icon/).length==12 && scene.pages==2,'Habitat Dex renders exactly 12 Pokemon in four columns and three rows')
    shot('blue-habitat-12-smoke')
    scene.dispose;scene=nil
    scene=BlueHabitat::Scene.new('Route 1',_INTL('Fishing'),rows)
    BlueTouchValidation.drive([[250,354],[450,354]]) { scene.run }
    check(scene.instance_variable_get(:@page)==1,'The thirteenth Pokemon is reachable by the real Next button')
    scene=nil
  ensure
    scene&.dispose
  end
  def self.pixels(sprite)
    wrapper=sprite.instance_variable_get(:@_iconBitmap);original=wrapper.bitmap;shown=sprite.bitmap;visible=0
    step=[original.width/12,1].max
    (0...original.width).step(step) do |x|
      (0...original.height).step(step) do |y|
        a=original.get_pixel(original.width-1-x,y);b=shown.get_pixel(x,y)
        next if a.alpha==0 && b.alpha==0
        visible+=1
        raise 'Canonical back pixel mismatch' unless [a.red,a.green,a.blue,a.alpha]==[b.red,b.green,b.blue,b.alpha]
      end
    end
    raise 'No visible canonical back pixels checked' if visible==0
  end
  def self.facing
    allies=[:AMMNOID,:AMMNOID].map { |id| BlueBattleLab.build(id,50) };foes=[:PIKACHU,:MAGIKARP].map { |id| BlueBattleLab.build(id,50) }
    battle,_=BlueRadicalAI::Validation.fixture(allies,foes,'double','engine');battle.backdrop='indoor1';battle.environment=:None;battle.time=0
    scene=BlueBattleUIValidation::Scene.new;battle.instance_variable_set(:@scene,scene);scene.pbStartBattle(battle)
    BlueBattleOptions::MechanicValidation.show_battlers(scene,battle);sprites=scene.instance_variable_get(:@sprites)
    pixels(sprites['pokemon_0']);pixels(sprites['pokemon_2']);check(true,'Both allied slots contain reflected pixels, independently of Sprite.mirror')
    @sample_frames=true;@sampled=0;moves=0;effects=0
    [:ROLLOUT,:TACKLE,:ROCKSLIDE,:BODYSLAM,:HYDROPUMP,:SWORDSDANCE].each do |id|
      next unless scene.pbFindMoveAnimation(id,0,0)
      scene.pbAnimation(id,battle.battlers[0],[battle.battlers[1]],0);moves+=1
      pixels(sprites['pokemon_0']);check(!sprites['pokemon_0'].mirror && sprites['pokemon_0'].angle==0,'Canonical back survives native move animation '+id.to_s)
    end
    %w[Poison Burn Paralysis StatDown Confusion].each do |name|
      animation=pbLoadBattleAnimations.get_from_name('Common:'+name);next unless animation
      # Direct player exercises asynchronous/effect callers outside pbCommonAnimation.
      player=PBAnimationPlayerX.new(animation,battle.battlers[1],battle.battlers[2],scene)
      player.start;until player.animDone?;player.update;scene.pbUpdate;end
      player.dispose;effects+=1;pixels(sprites['pokemon_2'])
      check(!sprites['pokemon_2'].mirror,'Canonical back survives direct status/effect player '+name)
    end
    check(moves>=4 && effects>=2 && @sampled>10,'Visible animation frames use canonical artwork for moves and received effects')
    shot('blue-ammnoid-canonical-smoke');scene.pbEndBattle(0);scene=nil
  ensure
    @sample_frames=false;scene&.pbEndBattle(0)
  end
  def self.album
    old_catalog=BlueTrainerAlbum.instance_variable_get(:@catalog);old_counts=BlueTrainerAlbum.instance_variable_get(:@key_counts)
    old_state=$PokemonGlobal.blue_trainer_album;history=$PokemonGlobal.blue_story_wins;money=$player.money;stats=$stats.battle_money_gained
    active=BlueTrainerAlbum.method(:active?);old_map=$game_map;old_interp=BlueTrainerAlbum.interpreter
    actual=BlueTrainerAlbum.catalog[86];check(actual && actual[:rows].length>=2,'Catalogue contains real Route 1 trainer NPCs')
    small=actual.merge(rows:actual[:rows].first(2));BlueTrainerAlbum.instance_variable_set(:@catalog,{86=>small});BlueTrainerAlbum.instance_variable_set(:@key_counts,nil)
    $PokemonGlobal.blue_trainer_album=nil;$PokemonGlobal.blue_story_wins={};$player.money=1000
    $game_map=Game_Map.new;$game_map.setup(86);BlueTrainerAlbum.define_singleton_method(:active?) { true }
    starter=Object.new
    # The wrapped starter uses the real native prize function and preparation hooks.
    starter.define_singleton_method(:start_core) do |*args|
      outcome=instance_variable_get(:@outcome);battle=instance_variable_get(:@battle)
      if outcome!=0
        BlueTrainerAlbum.prepare(battle)
        battle.pbGainMoney if outcome==1
      end
      outcome
    end
    # Prepend AFTER defining the base method, preserving the actual super chain.
    starter.singleton_class.prepend(BlueTrainerAlbum::Start)
    $blue_album_test_starter=starter;@auto_messages=true
    run=proc do |row,outcome,happy=false|
      battle,_=BlueRadicalAI::Validation.fixture([BlueBattleLab.build(:PIKACHU,50)],[BlueBattleLab.build(:MAGIKARP,10)],'single','engine')
      trainer=battle.opponent.first;trainer.name=row[3];trainer.trainer_type=row[2].to_sym
      trainer.define_singleton_method(:base_money) { 31 };battle.internalBattle=true;battle.moneyGain=true
      battle.field.effects[PBEffects::HappyHour]=happy
      starter.instance_variable_set(:@battle,battle);starter.instance_variable_set(:@outcome,outcome)
      interpreter=Interpreter.new;interpreter.instance_variable_set(:@map_id,86);interpreter.instance_variable_set(:@event_id,row[0])
      interpreter.instance_variable_set(:@list,[RPG::EventCommand.new(355,0,['$blue_album_test_starter.start_core']),RPG::EventCommand.new])
      interpreter.instance_variable_set(:@index,0);interpreter.execute_command
    end
    run.call(small[:rows][0],0);check(!BlueTrainerAlbum.state(86)[:entries][small[:rows][0][0]][:seen],'Cancelled battle before loading does not reveal a trainer')
    run.call(small[:rows][0],2);check(BlueTrainerAlbum.state(86)[:entries][small[:rows][0][0]][:seen] && !BlueTrainerAlbum.complete?(86) && BlueTrainerAlbum.earned(86)==0,'A loss reveals the portrait but grants no victory, money or completion')
    run.call(small[:rows][0],1);check(BlueTrainerAlbum.earned(86)==310 && !BlueTrainerAlbum.complete?(86),'First native trainer prize is recorded exactly once')
    run.call(small[:rows][1],1,true)
    check(BlueTrainerAlbum.earned(86)==930 && BlueTrainerAlbum.state(86)[:award]==306 && $player.money==2236,'Completing Route 1 awards floor(33% of actual $930), including Happy Hour receipts')
    before=$player.money;run.call(small[:rows][0],1)
    check(BlueTrainerAlbum.earned(86)==930 && $player.money==before+310 && !BlueTrainerAlbum.claim(86,false),'Rematches still pay their normal battle prize but never duplicate album credit or bonus')
    $PokemonGlobal.blue_trainer_album=Marshal.load(Marshal.dump($PokemonGlobal.blue_trainer_album))
    check(!BlueTrainerAlbum.claim(86,false),'Album completion and claimed reward survive serialization without duplicate payouts')
    # Import only known old wins, preserving zero historical money.
    $PokemonGlobal.blue_trainer_album=nil
    row=small[:rows][0];$PokemonGlobal.blue_story_wins={'old'=>{foes:[[row[2].to_sym,row[3],0]],stages:[0]}}
    check(BlueTrainerAlbum.state(86)[:entries][row[0]][:won] && BlueTrainerAlbum.earned(86)==0,'Existing recorded victories are recognized without inventing historical receipts')
    @auto_messages=false;scene=BlueTrainerAlbum::Scene.new(small)
    BlueTouchValidation.drive([proc { shot('blue-trainer-album-smoke');[450,356] }]) { scene.run };scene=nil
    check(BlueTrainerAlbum.interpreter==old_interp && BlueTrainerAlbum.context.nil?,'Interpreter and battle context are restored after every battle')
    handlers=[];MenuHandlers.each(:pause_menu) { |id,h| handlers << [id,h['order']] }
    orders=handlers.to_h
    check(orders[:trainer_card]<orders[:blue_trainer_album] && orders[:blue_trainer_album]<orders[:quests],'Album is ordered between Trainer Card and Quests with a valid native icon')
    check(!!pbResolveBitmap(MENU_FILE_PATH+$PokemonSystem.from_current_menu_theme('menu_blue_trainer_album')),'Album menu reuses a valid themed trainer-card icon')
  ensure
    @auto_messages=false;$blue_album_test_starter=nil
    BlueTrainerAlbum.instance_variable_set(:@catalog,old_catalog);BlueTrainerAlbum.instance_variable_set(:@key_counts,old_counts)
    BlueTrainerAlbum.define_singleton_method(:active?,active) if active;BlueTrainerAlbum.interpreter=old_interp;BlueTrainerAlbum.context=nil
    $PokemonGlobal.blue_trainer_album=old_state;$PokemonGlobal.blue_story_wins=history;$player.money=money if money
    $stats.battle_money_gained=stats if stats;$game_map=old_map if old_map
  end
  def self.run
    @lines=[];pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?);lang=$PokemonSystem.blue_locale
    $PokemonSystem.blue_locale='pt-BR'
    BlueLabPointer.define_singleton_method(:enabled?) { true };BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(Keys) unless Input.singleton_class.ancestors.include?(Keys)
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    PBAnimationPlayerX.prepend(AnimationFrames) unless PBAnimationPlayerX.ancestors.include?(AnimationFrames)
    maps;dex;facing;album
    if File.file?(BlueRouteCaptures::REQUEST)
      captures=BlueRouteCaptures.export;check(captures.length>100,'Captured every installed encounter map through the actual Habitat Dex renderer')
      @lines << 'ROUTE_CAPTURES='+captures.length.to_s
    end
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @close_map=false;@auto_messages=false;@sample_frames=false;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer;BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.write('Data/blue-world-validation.txt',@lines.join("\n")+"\n")
  end
end
