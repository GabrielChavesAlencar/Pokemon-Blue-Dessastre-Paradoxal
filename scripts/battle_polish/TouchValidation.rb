# Integration proof for actual title/menu/name/level windows and starter event dispatch.
module BlueTouchValidation
  module InputDriver
    def update
      super
      BlueTouchValidation.tick
    end
    def trigger?(key)
      return true if key==Input::MOUSELEFT && BlueTouchValidation.instance_variable_get(:@click)
      super
    end
  end
  module Picker
    def pbPokemonSelection(list,*args)
      if BlueTouchValidation.instance_variable_get(:@mono_mock)
        picks=BlueTouchValidation.instance_variable_get(:@picks)
        picks << [list.dup,args]
        return BlueBattleLab.build(list[(picks.length-1)%list.length],5)
      end
      super
    end
  end
  def self.tick
    @click=false
    return unless @queue
    raise 'Mouse test exceeded 15 real seconds' if BlueBattleUI.clock>@deadline
    return if @ready && !@ready.call
    next_point=@queue.first
    @point=next_point.respond_to?(:call) ? next_point.call : next_point
    @queue.shift if @point || !next_point.respond_to?(:call)
    @click=!!@point
  end
  def self.drive(points)
    @queue=points;@deadline=BlueBattleUI.clock+15;yield
  ensure
    @queue=nil;@ready=nil;@click=false;BlueLabPointer.reset
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.startup
    klass=Class.new(Scene_Intro) do
      attr_reader :closed
      def closeTitle;@closed=true;end
    end
    intro=klass.new;screen=Object.new;screen.define_singleton_method(:update) {}
    intro.instance_variable_set(:@screen,screen)
    drive([[200,200]]) { intro.update }
    check(intro.closed,'Clicking the native title loop acts as Start')
    check(BlueStartMouse.scope.nil?,'Title click scope is cleared after leaving the title')
    scene=PokemonLoad_Scene.new
    scene.pbStartScene(['New Game','Options'],false,nil,nil,0)
    shot('blue-load-mouse-smoke')
    result=drive([[70,94]]) { scene.pbChoose(['New Game','Options'],-1) }
    check(result==1,'Clicking the second native load-menu panel selects and confirms Options')
    scene.pbCloseScene;scene=nil
    scene=PokemonEntryScene2.new;scene.pbStartScene('Name?',1,8,'',0)
    shot('blue-name-mouse-smoke')
    @ready=proc { scene.instance_variable_get(:@sprites)['cursor'].visible }
    result=drive([[66,190],[98,190],[350,132],[130,190],[430,132]]) { scene.pbEntry }
    check(result=='Ac','Native on-screen naming supports letters, automatic lowercase, backspace and OK by mouse')
    scene.pbEndScene;scene=nil
    scene=PokemonEntryScene.new;scene.pbStartScene('Name?',1,8,'Blue',0)
    shot('blue-name-keyboard-mouse-smoke')
    result=drive([[450,260]]) { scene.pbEntry }
    check(result=='Blue','Keyboard naming also has a mouse confirmation button')
    scene.pbEndScene;scene=nil
    mon=BlueBattleLab.build(:PIKACHU,10);old=[mon.totalhp,mon.attack,mon.defense,mon.spatk,mon.spdef,mon.speed]
    mon.level=11;mon.calc_stats
    drive([[5,380],[5,380]]) { Battle::Scene.allocate.pbLevelUp(mon,nil,*old) }
    check(mon.level==11,'Both native level-up stat windows can be dismissed by clicking outside the window')
    check(BlueStartMouse.scope.nil?,'Level-up clicks do not become global attack confirmations')
    scene=ModularSelection_Scene.new;scene.pbStartScene([:POOCHYENA,:ZORUA],PokemonSelections::STARTER.merge(blue_monotype_pick:1))
    shot('blue-monotype-picker-smoke')
    confirm=proc do
      window=ObjectSpace.each_object(Window_CommandPokemon).find { |w| !w.disposed? && w.visible && w.active && w.itemCount==2 }
      if window
        x,y=BlueLabPointer.origin(window);rect=window.itemRect(0)
        [x+window.startX+rect.x+8,y+window.startY+rect.y+8]
      end
    end
    result=drive([[104,206],confirm]) { scene.pbScene(true) }
    check(result.species==:POOCHYENA,'Clicking the current starter artwork confirms the native Pokemon selector')
    scene.pbEndScene;scene=nil
  ensure
    scene.pbCloseScene if scene.is_a?(PokemonLoad_Scene)
    scene.pbEndScene if scene && !scene.is_a?(PokemonLoad_Scene)
    Input.text_input=false
  end
  def self.monotype
    party=$player.party;dex=Marshal.dump($player.pokedex);mode=$PokemonGlobal.blue_story_mode;traditional=$PokemonGlobal.blue_traditional_starters
    choose=BlueBattleLab.method(:choose)
    @picks=[];@mono_mock=true;$player.party=[];$PokemonGlobal.blue_story_mode=:story
    BlueBattleLab.define_singleton_method(:choose) do |title,labels,*args|
      BlueTouchValidation.instance_variable_set(:@type_labels,labels)
      labels.index(GameData::Type.get(:DARK).name)
    end
    list=load_data('Data/Map001.rxdata').events[9].pages[0].list
    index=list.each_index.find { |i| list[i].code==402 && list[i].parameters[1]=='Any Pokémon' }
    interpreter=Interpreter.new;interpreter.setup(list,0,1)
    interpreter.instance_variable_set(:@index,index);interpreter.instance_variable_set(:@parameters,list[index].parameters)
    interpreter.instance_variable_set(:@branch,{list[index].indent=>list[index].parameters[0]})
    check(interpreter.command_402,'Actual Monotype root branch executes the dedicated picker')
    check(@type_labels.length==18 && @picks.length==2,'Monotype opens an 18-type second menu and exactly two Pokemon selections')
    check($player.party.length==2 && $player.party.all? { |p| p.types.include?(:DARK) && p.species_data.base_stats.values.sum<=350 && p.level==5 },'Choosing Dark grants exactly two legal Dark starters at level 5')
    check(@picks.all? { |list,args| list.all? { |id| s=GameData::Species.get(id);s.types.include?(:DARK) && s.base_stats.values.sum<=350 } },'Every selectable candidate is actually Dark and at most 350 BST')
    check(@picks.map { |list,args| args.last[:blue_monotype_pick] }==[1,2],'The selector displays which of the two starters is being chosen')
    check(interpreter.instance_variable_get(:@index)>index+1,'The old Any Pokemon branch is skipped after the two selections')
    $player.party=[];BlueBattleLab.define_singleton_method(:choose) { |*args| -1 }
    check(!BlueAdventure.choose_monotype_starters && $player.party.empty?,'Back at the type menu grants no Pokemon')
    index=list.each_index.find { |i| list[i].code==101 && list[i].parameters[0].include?('What do you think about Emulator Speed Up/Delta Speed Up?') }
    interpreter=Interpreter.new;interpreter.setup(list,0,1);interpreter.instance_variable_set(:@index,index);interpreter.instance_variable_set(:@parameters,list[index].parameters)
    check(interpreter.command_101 && interpreter.instance_variable_get(:@index)>index+20 && !$game_switches[90],'New-game speed quiz is skipped and does not activate its punitive branch')
    found=[];MenuHandlers.each(:options_menu) { |id,hash| found << hash['name'] if id==:only_speedup_battles }
    check(found==['Delta Speed Up'] && SPEEDUP_STAGES==[1,3],'The existing 1x/3x Delta accelerator remains the only labeled speed system')
  ensure
    @mono_mock=false
    BlueBattleLab.define_singleton_method(:choose,choose) if choose
    $player.party=party if party;$PokemonGlobal.blue_story_mode=mode;$PokemonGlobal.blue_traditional_starters=traditional
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
  end
  def self.readouts
    scene=nil;battle=BlueBattleOptions::MechanicValidation.fixture(:CHARIZARDITEY,'double')
    scene=BlueBattleUIValidation::Scene.new;battle.instance_variable_set(:@scene,scene)
    battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
    scene.pbStartBattle(battle);BlueBattleOptions::MechanicValidation.show_battlers(scene,battle)
    battle.field.weather=:Rain;battle.field.weatherDuration=4;battle.field.terrain=:Electric;battle.field.terrainDuration=3;battle.field.effects[PBEffects::TrickRoom]=5
    battle.sides.each { |side| side.effects[PBEffects::Tailwind]=4 }
    battle.sides[0].effects[PBEffects::Reflect]=4;battle.sides[0].effects[PBEffects::LightScreen]=2;battle.sides[1].effects[PBEffects::AuroraVeil]=3
    rows=BlueBattleUI.field_rows(battle)
    check(rows.any? { |r| r[0].include?('R4 LS2') } && rows.any? { |r| r[0].include?('AV3') },'HUD distinguishes Reflect/Light Screen on our side and Aurora Veil on the rival side, with durations')
    check(rows.length<=8,'The maximum combined field summary fits the expanded HUD')
    battle.battlers.each { |b| b.stages[:DEFENSE]=1 if b && b.pokemon }
    scene.pbGraphicsUpdate
    battle.battlers.each do |b|
      next unless b && b.pokemon
      box=scene.instance_variable_get(:@sprites)['dataBox_'+b.index.to_s]
      badge=box.instance_variable_get(:@sprites)['blueStages'];bar=box.instance_variable_get(:@hpBar)
      check(badge.y>=bar.y+bar.src_rect.height,'Modifier badges are below the actual HP bar: battler '+b.index.to_s)
      check(badge.y+badge.bitmap.height<=Graphics.height-96,'Double-battle modifier badges stay above the move buttons: battler '+b.index.to_s)
    end
    shot('blue-below-hp-and-screens-smoke')
    before=Marshal.dump(battle.sides.map(&:effects))
    preview=BlueReadouts::Preview.new(BlueReadouts.preview_entries(battle),BlueBattleUI.screen_details(battle))
    preview.start;shot('blue-screen-preview-smoke');preview.dispose;preview=nil
    check(Marshal.dump(battle.sides.map(&:effects))==before,'Opening full screen details cannot spend screen turns or change side effects')
    battle.sides.each { |side| [:Reflect,:LightScreen,:AuroraVeil].each { |effect| side.effects[PBEffects.const_get(effect)]=0 } }
    check(BlueBattleUI.field_rows(battle).none? { |r| r[0].include?('R4 LS2') || r[0].include?('AV3') },'Expired screens disappear from the HUD')
    scene.pbEndBattle(0);scene=nil
  ensure
    preview&.dispose;scene&.pbEndBattle(0)
  end
  def self.run
    @lines=[];lang=$PokemonSystem.blue_locale;pointer=BlueLabPointer.method(:position)
    enabled=BlueLabPointer.method(:enabled?);BlueLabPointer.define_singleton_method(:enabled?) { true }
    BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(InputDriver) unless Input.singleton_class.ancestors.include?(InputDriver)
    Object.prepend(Picker) unless Object.ancestors.include?(Picker)
    $PokemonSystem.blue_locale='pt-BR'
    startup;monotype;readouts;@lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @queue=nil;@click=false;@mono_mock=false;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer
    BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.open('Data/blue-touch-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
