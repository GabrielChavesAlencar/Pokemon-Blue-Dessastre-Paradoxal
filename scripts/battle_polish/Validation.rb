# Integration checks run inside Essentials; no campaign save is loaded by the lab.
module BluePolishValidation
  def self.assert(value,label)
    raise label unless value
    @lines << 'PASS | '+label
  end
  def self.run
    @lines=[]
    test_exp
    test_pointer_order
    test_story
    test_entries
    @lines << 'RESULT=PASS'
    true
  rescue StandardError => error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace);@lines << 'RESULT=FAIL'
    false
  ensure
    File.open('Data/blue-polish-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
  def self.test_exp
    box=Battle::Scene::PokemonDataBox.allocate
    box.instance_variable_set(:@show_exp_bar,true)
    [[0,90,100],[90,91,100]].each do |from,to,range|
      values=[]
      box.define_singleton_method(:refresh_exp) { values << instance_variable_get(:@anim_exp_current) }
      box.animate_exp(from,to,range)
      started=System.uptime
      while box.animating_exp?
        Graphics.update;box.update_exp_animation
        raise 'EXP animation timeout' if System.uptime-started>4
      end
      duration=System.uptime-started
      assert(values.uniq.length>3 && values.last==to,'EXP samples include intermediate values and exact endpoint')
      assert(values.each_cons(2).all? { |a,b| b>=a },'EXP is monotonic')
      assert(duration>=0.28,'Even a small EXP award takes at least 0.3 seconds')
      @lines << "EXP | #{from}->#{to} frames=#{values.length} seconds=#{duration.round(2)}"
    end
  end
  def self.test_pointer_order
    original=BlueLabPointer.method(:enabled?)
    BlueLabPointer.define_singleton_method(:enabled?) { true }
    BlueLabPointer.reset;BlueLabPointer.emit(Input::USE)
    Input.update
    assert(Input.trigger?(Input::USE),'Campaign window-before-input order retains an unread click')
    Input.update
    assert(!BlueLabPointer.key?(Input::USE),'A consumed click is not repeated in the next menu')
    BlueLabPointer.emit(Input::USE)
    assert(Input.trigger?(Input::USE),'Lab input-before-window order retains a click')
    Input.update
    assert(!BlueLabPointer.key?(Input::USE),'Lab clicks also expire after consumption')
  ensure
    BlueLabPointer.define_singleton_method(:enabled?,original) if original
    BlueLabPointer.keys={};BlueLabPointer.reset
  end
  def self.test_story
    old_global=Marshal.dump($PokemonGlobal)
    old_enabled=BlueStory.method(:enabled?)
    BlueStory.choose_mode(:story);$PokemonGlobal.blue_traditional_starters=true
    assert(!BlueStory.enabled?,'Lab battles do not receive campaign balancing')
    assert([0,1,2,3,4,18].map { |n| BlueStory.stage(n) }==[0,0,1,1,2,2],'Stage boundaries 0/1, 2/3 and 4+ badges')
    BlueStory.define_singleton_method(:enabled?) { true }
    $PokemonGlobal.blue_story_wins={}
    # Choose ordering must preserve the original event's branch indices.
    names=['Options Details','VGC Starters','Traditional Starters','Any Pokémon']
    commands=[RPG::EventCommand.new(102,0,[names,3])]
    names.each_with_index { |name,i| commands << RPG::EventCommand.new(402,0,[i,name]);commands << RPG::EventCommand.new(0,1,[]) }
    commands << RPG::EventCommand.new(404,0,[]);commands << RPG::EventCommand.new
    interpreter=Interpreter.new;interpreter.setup(commands,0)
    choices=interpreter.setup_choices([names,3])
    assert(choices[0].first=='Traditional Starters' && choices[2]==[2,0,1,3] && choices[1]==1,'Traditional Starters first; branch and cancel mappings retained')
    assert(names.first=='Options Details','Original choice data remains unchanged')
    # Exercise every non-Mega species/form against both native stat ceilings.
    checked=0;examples=[]
    GameData::Species.each do |s|
      next unless BlueStory.bst(s)>0
      [350,450].each do |limit|
        selected=BlueStory.replacement(s,limit)
        assert(BlueStory.bst(selected)<=limit,"#{s.id} replacement obeys #{limit} BST")
      end
      checked+=1;Graphics.update if checked%20==0
    end
    [350,450].each do |limit|
      [:CHARIZARD,:GYARADOS,:GARCHOMP,:FERROTHORN,:WISHIWASHI,:CAVEFANG,:MEWTWO,:BLISSEY,:LUCARIO,:DRAGONITE].each do |id|
        p=BlueBattleLab.build(id,50);before=Marshal.dump(p)
        replacement=BlueStory.adjust(p,limit)
        assert(Marshal.dump(p)==before,'Opponent replacement leaves source Pokemon intact')
        assert(BlueStory.bst(replacement.species_data)<=limit && replacement.level==p.level && replacement.moves.length>0,'Native replacement has valid stats, level and moves')
        replacement.moves.first.pp=0
        assert(Marshal.dump(p)==before,'Battle PP changes cannot mutate the cached original team')
        examples << "#{id}=>#{replacement.species_data.id} (#{limit})"
      end
    end
    @lines << "SPECIES_CHECKED=#{checked}";@lines << examples.join('; ')
    # Real constructor/preparation path, including two opposing trainers.
    ally=BlueBattleLab.build(:PIKACHU,50)
    trainers=[:CHARIZARD,:GYARADOS].map do |id|
      t=NPCTrainer.new(id.to_s,:YOUNGSTER);t.party=[BlueBattleLab.build(id,50)];t
    end
    original=Marshal.dump(trainers)
    previous_badges=$player.badges.dup;$player.badges.map! { false }
    battle=Battle.new(BlueBattleLab::SmokeScene.new,[ally],trainers.flat_map(&:party),[$player],trainers)
    assert(battle.pbParty(1).all? { |p| BlueStory.bst(p.species_data)<=350 },'Real two-trainer constructor receives only capped opponents')
    assert(Marshal.dump(trainers)==original && battle.pbParty(0).first.equal?(ally),'Player party and source trainer data are preserved')
    fish=NPCTrainer.new('Form test',:YOUNGSTER);fish.party=[BlueBattleLab.build(:WISHIWASHI,50)]
    fb=Battle.new(BlueBattleLab::SmokeScene.new,[ally],fish.party,[$player],[fish])
    fb.pbEnsureParticipants;fb.pbSetUpSides
    fb.battlers[1].pbSimpleFormChange(1,nil)
    assert(fb.battlers[1].form==0,'Schooling cannot bypass the Story BST limit')
    $game_temp.clear_battle_rules
    battle.party2starts=[0,1]
    BlueStory.instance_variable_set(:@replaying,true)
    BattleCreationHelperMethods.prepare_battle(battle)
    assert(!battle.expGain && battle.moneyGain && battle.internalBattle,'Revanche awards money and disables EXP')
    previous_money=$player.money
    previous_bag=Marshal.dump($bag);previous_exp=ally.exp
    battle.pbGainMoney
    assert($player.money>previous_money && Marshal.dump($bag)==previous_bag && ally.exp==previous_exp,'Native revanche payout changes money, with no bag or EXP reward')
    context={foes:[[:YOUNGSTER,'Test history',0]],stage:0,size:'single'}
    BlueStory.record(context,2);assert(BlueStory.history.empty?,'Losing does not unlock a completed revanche')
    BlueStory.record(context,1)
    $player.badges[0]=true;$player.badges[1]=true
    row=BlueStory.rematches.first
    assert(row && row[:stages]==[0],'Previously beaten trainer becomes available in intermediate stage')
    BlueStory.record(context.merge(stage:1),1)
    assert(BlueStory.rematches.empty?,'Victory consumes that stage revanche')
    $player.badges[2]=true;$player.badges[3]=true
    assert(BlueStory.rematches.length==1,'Advanced stage unlocks a new revanche')
    $PokemonGlobal=Marshal.load(Marshal.dump($PokemonGlobal))
    assert(BlueStory.history.values.first[:stages]==[0,1],'Save-compatible history survives Marshal round-trip')
  ensure
    $player.badges.replace(previous_badges) if previous_badges
    $player.money=previous_money if previous_money
    $PokemonGlobal=Marshal.load(old_global) if old_global
    BlueStory.define_singleton_method(:enabled?,old_enabled) if old_enabled
    BlueStory.instance_variable_set(:@replaying,false)
    $game_temp.clear_battle_rules
  end
  def self.test_entries
    # Construct the real picture schedules and inspect them before rendering.
    scene=BlueBattleLab::SmokeScene.new
    one=BlueBattleLab.build(:PIKACHU,50);two=BlueBattleLab.build(:MAGIKARP,5)
    one.poke_ball=:ULTRABALL;two.poke_ball=:GREATBALL
    trainer=NPCTrainer.new('Presentation',:YOUNGSTER);trainer.party=[two]
    battle=Battle.new(scene,[one],[two],[$player],[trainer])
    battle.pbEnsureParticipants;battle.pbSetUpSides
    scene.instance_variable_set(:@battle,battle)
    viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    scene.instance_variable_set(:@viewport,viewport)
    scene.pbInitSprites
    sprites=scene.instance_variable_get(:@sprites)
    [0,1].each { |i| scene.pbChangePokemon(i,[one,two][i]) }
    a=Battle::Scene::Animation
    player=a::PokeballPlayerSendOut.new(sprites,viewport,1,battle.battlers[0],true,0)
    opponent=a::PokeballTrainerSendOut.new(sprites,viewport,1,battle.battlers[1],true,1)
    switch=a::PokeballPlayerSendOut.new(sprites,viewport,1,battle.battlers[0],false,0)
    assert(player.instance_variable_get(:@blue_release_time)==23,'Player waits for throw and arc before materialization')
    assert(opponent.instance_variable_get(:@blue_release_time)==26,'Second opponent release is staggered after trainer exit')
    assert(switch.instance_variable_get(:@blue_release_time)==13,'Switch skips the opening trainer delay')
    [player,opponent,switch].each(&:dispose)
    assert(!sprites['pokemon_0'].visible && !sprites['pokemon_1'].visible,'Pokemon sprites remain hidden until their ball opens')
    # Render the real animation, not just a schedule: observe the ball before
    # release, intermediate Pokemon scale and a completed normal-sized sprite.
    draw=a::PokeballPlayerSendOut.new(sprites,viewport,1,battle.battlers[0],true,0)
    fade=a::PlayerFade.new(sprites,viewport,true)
    ball=draw.instance_variable_get(:@ballSprite)
    observed=[];captured=false;started=System.uptime
    Graphics.transition(0)
    until draw.animDone? && fade.animDone?
      Graphics.update;draw.update;fade.update;scene.pbUpdate
      elapsed=System.uptime-started
      observed << [ball.visible,sprites['pokemon_0'].visible,sprites['pokemon_0'].zoom_x]
      if !captured && ball.visible && !sprites['pokemon_0'].visible
        shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-entry-ball-smoke.png');shot.dispose;captured=true
      end
      raise 'Entry rendering timeout' if elapsed>8
    end
    assert(observed.any? { |ball_visible,visible,zoom| ball_visible && !visible },'Rendered ball is visible before the Pokemon')
    assert(observed.any? { |ball_visible,visible,zoom| visible && zoom>0 && zoom<1 },'Rendered Pokemon grows through intermediate scales')
    assert(sprites['pokemon_0'].visible && sprites['pokemon_0'].zoom_x>0,'Rendered Pokemon finishes visible at normal scale')
    shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-entry-release-smoke.png');shot.dispose
    draw.dispose;fade.dispose
    # A real wild intro must start offscreen to the left and end at its metric position.
    battle.instance_variable_set(:@opponent,nil)
    sprites['pokemon_1'].visible=true
    destination=sprites['pokemon_1'].x
    wild=a::Intro.new(sprites,viewport,battle)
    pictures=wild.instance_variable_get(:@pictureEx)
    originals=wild.instance_variable_get(:@pictureSprites)
    p=pictures[originals.index(sprites['pokemon_1'])]
    assert(p && p.totalDuration>=48,'Wild introduction includes the full two-second slide')
    positions=[];started=System.uptime
    until wild.animDone?
      Graphics.update;wild.update;scene.pbUpdate
      positions << sprites['pokemon_1'].x
      raise 'Wild entry timeout' if System.uptime-started>6
    end
    assert(positions.first<0 && positions.last==destination && positions.uniq.length>20,'Rendered wild sprite travels from offscreen left to the exact metric position')
    wild.dispose
  ensure
    pbDisposeSpriteHash(sprites) if sprites
    viewport&.dispose
  end
end
