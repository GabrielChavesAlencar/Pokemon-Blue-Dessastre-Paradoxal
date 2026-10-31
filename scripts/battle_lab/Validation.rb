# Runtime checks use the installed engine, not a reimplementation of battle.
module BlueBattleLab
  module TestMouseInput
    def trigger?(key)
      return true if BlueBattleLab.instance_variable_get(:@testing_mouse) && key == Input::MOUSELEFT
      super
    end
  end
  def self.check(condition, message)
    raise message unless condition
    log("PASS | #{message}")
  end

  def self.check_hp_animation
    # Exercise the real interpolator and DBK callbacks without loading any map.
    trigger_sink = Object.new
    trigger_sink.define_singleton_method(:pbDeluxeTriggers) { |*args| }
    mon = build(:PIKACHU,50)
    battler = Object.new
    battler.define_singleton_method(:pokemon) { mon }
    battler.define_singleton_method(:species) { mon.species }
    battler.define_singleton_method(:hp) { mon.hp }
    battler.define_singleton_method(:totalhp) { mon.totalhp }
    battler.define_singleton_method(:battle) { trigger_sink }
    battler.define_singleton_method(:fainted?) { mon.fainted? }
    battler.define_singleton_method(:hasLowHP?) { mon.hp <= mon.totalhp / 4 }
    [[100,10], [10,0], [10,100]].each do |from, to|
      box = Battle::Scene::PokemonDataBox.allocate
      box.instance_variable_set(:@battler, battler)
      samples = []
      box.define_singleton_method(:refresh_hp) { samples << hp }
      box.animate_hp(from, to)
      started = System.uptime
      while box.animating_hp?
        Graphics.update
        box.update_hp_animation
        raise 'HP animation timeout' if System.uptime - started > 3
      end
      inside = samples.select { |n| n > [from,to].min && n < [from,to].max }
      check(inside.uniq.length >= 3 && samples.last == to, "HP #{from}->#{to}: intermediate values and exact endpoint")
      check(samples.each_cons(2).all? { |a,b| to < from ? b <= a : b >= a }, 'HP animation is monotonic')
      log("HP_ANIMATION | from=#{from} to=#{to} frames=#{samples.length} intermediate=#{inside.uniq.length} seconds=#{(System.uptime-started).round(2)}")
    end
  end

  def self.run_smoke
    if defined?(BlueDessastreParadoxal)
      check(BlueDessastreParadoxal.run_checks, 'Dessastre Paradoxal checks')
    end
    check(Battle::Scene::PokemonDataBox::HP_BAR_CHANGE_TIME == 1.0, 'HP interpolation restored to one second')
    check_hp_animation
    check_mouse_controls
    check(BlueLabPointer.inside?([15,25],10,20,20,20), 'Mouse coordinate inside button')
    check(!BlueLabPointer.inside?([30,25],10,20,20,20), 'Mouse right edge outside button')
    check(!BlueLabPointer.inside?(nil,10,20,20,20), 'Mouse outside game window ignored')
    begin
      validate_teams([:one],[:one],'double')
      raise 'Double team size validation failed'
    rescue ArgumentError
      log('PASS | Double requires at least two per side')
    end
    begin
      validate_teams(Array.new(7),[:one],'single')
      raise 'Team maximum validation failed'
    rescue ArgumentError
      log('PASS | More than six rejected')
    end
    [['single',1],['single',6],['double',6]].each do |format,size|
      allies = Array.new(size) do
        mon = build(:PIKACHU,80)
        mon.moves = [Pokemon::Move.new(:THUNDERBOLT)]
        mon.item = :SITRUSBERRY
        mon
      end
      foes = Array.new(size) do
        mon = build(:MAGIKARP,5)
        mon.moves = [Pokemon::Move.new(:SPLASH)]
        mon
      end
      before = Marshal.dump([allies,foes])
      result = battle(allies,foes,true,format)
      check(result == 1, "Complete #{format} #{size}x#{size} trainer battle victory")
      check(Marshal.dump([allies,foes]) == before, 'Configured rosters, items, forms and moves unchanged')
    end
    if GameData::Species.try_get(:CAVEFANG)
      result = battle([build(:CAVEFANG,70),build(:ARCHGUTOR,70)],
                      [build(:IRONCRUSHER,10),build(:PIKACHU,10)],true,'double')
      check([1,2].include?(result), 'Complete author double battle')
    end
    check(Game.save == false && Game.auto_save == false && SaveData.exists? == false && SaveData.save_to_file('Data/blue-lab-should-not-save.rxdata') == false, 'Save read/write guards')
    check(!File.file?('Data/blue-lab-should-not-save.rxdata'), 'No campaign save created')
    log('SMOKE=PASS | complete 6x6 single/double battles; HP interpolation, rosters and save guards passed')
  end

  def self.check_mouse_controls
    # Drive actual engine widgets with deterministic click events. This does not
    # send OS input and the test overrides are restored before battle starts.
    original_enabled = BlueLabPointer.method(:enabled?)
    original_position = BlueLabPointer.method(:position)
    BlueLabPointer.define_singleton_method(:enabled?) { true }
    BlueLabPointer.define_singleton_method(:position) { BlueBattleLab.instance_variable_get(:@test_point) }
    Input.singleton_class.prepend(TestMouseInput)
    @testing_mouse = true
    viewport = Viewport.new(20,10,Graphics.width,Graphics.height)
    list = Window_CommandPokemon.newWithSize((1..30).map(&:to_s), 12,16,300,180,viewport)
    list.index = 12
    list.top_row = 10
    rect = list.itemRect(12)
    @test_point = [20+list.x+list.startX+rect.x+5, 10+list.y+list.startY+rect.y+5]
    Input.update; list.update
    check(list.index == 12 && Input.trigger?(Input::USE), 'Mouse selects scrolled list item with viewport offset')
    @test_point = [-1,-1]
    Input.update; list.update
    check(!BlueLabPointer.claimed, 'Click outside list does not confirm')
    list.visible = false
    menu = Battle::Scene::CommandMenu.new(viewport,100)
    menu.visible = true
    button = menu.instance_variable_get(:@buttons)[2]
    x,y = BlueLabPointer.origin(button)
    @test_point = [x+8,y+8]
    Input.update; menu.update
    check(menu.index == 2 && Input.trigger?(Input::USE), 'Mouse confirms actual battle command button')
    menu.visible = false
    target = Battle::Scene::TargetMenu.new(viewport,100,[2,2])
    target.setDetails(['Ally','Foe',nil,'Foe 2'],0)
    target.visible = true
    button = target.instance_variable_get(:@buttons)[3]
    x,y = BlueLabPointer.origin(button)
    @test_point = [x+8,y+8]
    Input.update; target.update
    check(target.index == 3 && Input.trigger?(Input::USE), 'Mouse selects second opponent in doubles')
    button = target.instance_variable_get(:@buttons)[2]
    x,y = BlueLabPointer.origin(button)
    @test_point = [x+8,y+8]
    Input.update; target.update
    check(!BlueLabPointer.claimed, 'Mouse ignores invalid double target')
    target.visible = false
    pkmn = build(:PIKACHU,50)
    trainer = NPCTrainer.new('Test',$player.trainer_type)
    battle = Battle.new(SmokeScene.new,[pkmn],[build(:MAGIKARP,5)],[$player],[trainer])
    battler = Battle::Battler.new(battle,0)
    battler.pbInitialize(pkmn,0)
    battler.moves = [Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:TACKLE))]
    fight = Battle::Scene::FightMenu.new(viewport,100)
    fight.battler = battler
    fight.visible = true
    button = fight.instance_variable_get(:@buttons)[0]
    x,y = BlueLabPointer.origin(button)
    @test_point = [x+8,y+8]
    Input.update; fight.update
    check(fight.index == 0 && Input.trigger?(Input::USE), 'Mouse selects actual move button')
    button = fight.instance_variable_get(:@buttons)[3]
    x,y = BlueLabPointer.origin(button)
    @test_point = [x+8,y+8]
    Input.update; fight.update
    check(!BlueLabPointer.claimed, 'Mouse ignores empty move slot')
    preset(true).flatten.each { |mon| check(!mon.ability.name.empty?, "Team editor ability #{mon.species}") }
  ensure
    @testing_mouse = false
    BlueLabPointer.define_singleton_method(:enabled?, original_enabled) if original_enabled
    BlueLabPointer.define_singleton_method(:position, original_position) if original_position
    BlueLabPointer.reset
    list&.dispose; menu&.dispose; target&.dispose; fight&.dispose; viewport&.dispose
  end
end
