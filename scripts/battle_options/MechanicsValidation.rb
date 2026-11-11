module BlueBattleOptions
  module MechanicValidation
    module Keys
      def trigger?(key)
        return true if key==Input::MOUSELEFT && BlueBattleOptions::MechanicValidation.instance_variable_get(:@mouse)
        super
      end
      def triggerex?(key)
        if key==:F6 && BlueBattleOptions::MechanicValidation.instance_variable_get(:@f6)
          BlueBattleOptions::MechanicValidation.instance_variable_set(:@f6,false)
          return true
        end
        super
      end
    end
    module Pointer
      def getMousePos
        BlueBattleOptions::MechanicValidation.instance_variable_get(:@point) || super
      end
    end
    class Scene < Battle::Scene
      def pbDisplayMessage(*args);end
      def pbDisplayPausedMessage(*args);end
      def pbDisplayConfirmMessage(*args);true;end
      attr_accessor :blue_driver,:blue_expect
      attr_reader :blue_captured
      def pbFightMenu_Extra(battler,special,cw)
        @blue_frames=(@blue_frames || 0)+1
        raise 'Mechanic selector UI did not return within 90 frames' if @blue_frames>90
        if @blue_driver && @blue_frames==1
          Graphics.update;shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-mechanic-default-smoke.png');shot.dispose
          if @blue_driver==:mouse
            button=@blue_mechanic_button
            BlueBattleOptions::MechanicValidation.instance_variable_set(:@mouse,true)
            BlueBattleOptions::MechanicValidation.instance_variable_set(:@point,[button.x+97,button.y+11])
          end
        end
        super
        wanted=@blue_expect || :tera
        if @blue_driver && @battle.pbBattleMechanicIsRegistered?(battler.index,wanted)
          @blue_captured=[special,cw.mode,cw.instance_variable_get(:@chosenButton),@battle.pbRegisteredMegaEvolution?(battler.index)]
          Graphics.update
          shot=Graphics.snap_to_bitmap;shot.to_file("Data/blue-mechanic-#{wanted}-smoke.png");shot.dispose
          throw :blue_selector_test_done
        end
      ensure
        BlueBattleOptions::MechanicValidation.instance_variable_set(:@mouse,false)
        BlueBattleOptions::MechanicValidation.instance_variable_set(:@point,nil)
      end
    end
    def self.fixture(item=:CHARIZARDITEY,format='single')
      mon=BlueBattleLab.build(:CHARIZARD,50);mon.item=item
      mon.moves=[:SOLARBEAM,:HEATWAVE,:WEATHERBALL,:PROTECT].map { |m| Pokemon::Move.new(m) };mon.tera_type=:FLYING
      foe=BlueBattleLab.build(:BLASTOISE,50)
      allies=[mon];foes=[foe]
      if format=='double'
        allies << BlueBattleLab.build(:GARDEVOIR,50);foes << BlueBattleLab.build(:SNEASLER,50)
      end
      battle,_=BlueRadicalAI::Validation.fixture(allies,foes,format,'engine')
      battle.items=[[:MEGARING,:ZRING,:TERAORB,:DYNAMAXBAND]]
      battle.instance_variable_set(:@blue_lab_battle,true)
      battle.instance_variable_set(:@blue_mechanics,BlueBattleOptions.defaults)
      battle
    end
    def self.show_battlers(scene,battle)
      scene.pbSendOutBattlers(battle.battlers.compact.select { |b| b.opposes? }.map { |b| [b.index,b.pokemon] },true)
      scene.pbSendOutBattlers(battle.battlers.compact.reject { |b| b.opposes? }.map { |b| [b.index,b.pokemon] },true)
    end
    def self.run(lines,check)
      charge=$player.tera_charged?;$player.tera_charged=true
      logger=PBDebug.method(:logonerr);PBDebug.define_singleton_method(:logonerr) { |*args,&block| block.call }
      BlueBattleOptions::CLASSIC_STONES.each do |stone,(species,form)|
        data=GameData::Species.get_species_form(species,form)
        next unless data && data.mega_stone && GameData::Item.exists?(stone)
        mon=BlueBattleLab.build(species,50);mon.form=data.unmega_form;mon.item=stone
        check.call("#{stone} unlocks the matching classic Mega form",mon.getMegaForm==form)
      end
      mon=BlueBattleLab.build(:CHARIZARD,50);mon.item=:MEGAITEY
      check.call('Existing universal Megaite Y still works',mon.getMegaForm==2)
      wrong=BlueBattleLab.build(:VENUSAUR,50);wrong.item=:CHARIZARDITEY
      check.call('A stone for a different species does not grant Mega evolution',!wrong.hasMegaForm?)
      battle=fixture
      check.call('Directly equipped Charizardite Y offers Mega and Terastal together',battle.blue_available_mechanics(0)==[:mega,:tera,:dynamax])
      check.call('Default priority selects Mega before the other alternatives',battle.pbGetEligibleBattleMechanic(0)==:mega)
      16.times do |mask|
        rules=BlueBattleOptions::PRIORITY.each_with_index.to_h { |key,i| [key.to_s,mask[i]==1] }
        battle.instance_variable_set(:@blue_mechanics,rules)
        expected=[:mega,:tera,:dynamax].select { |key| rules[key.to_s] }
        check.call("Mechanic flags respected for combination #{mask}",battle.blue_available_mechanics(0)==expected && battle.pbGetEligibleBattleMechanic(0)==expected.first)
      end
      battle.instance_variable_set(:@blue_mechanics,BlueBattleOptions.defaults)
      battle.blue_choose_mechanic(0,:mega)
      battle.blue_choose_mechanic(0,:tera)
      check.call('Selecting Terastal clears pending Mega and registers only Tera',battle.pbRegisteredTerastallize?(0) && !battle.pbRegisteredMegaEvolution?(0) && !battle.pbRegisteredDynamax?(0))
      battle.blue_choose_mechanic(0,:dynamax)
      check.call('Selecting Dynamax clears the previous Tera selection',battle.pbRegisteredDynamax?(0) && !battle.pbRegisteredTerastallize?(0))
      battle.blue_choose_mechanic(0,nil)
      check.call('No mechanic clears pending registrations without spending them',!BlueBattleOptions::PRIORITY.any? { |key| battle.pbBattleMechanicIsRegistered?(0,key) })
      battle.terastallize[0][0]=-2;battle.blue_choose_mechanic(0,nil)
      check.call('Changing selection never restores a spent Tera use',battle.terastallize[0][0]==-2)
      pikachu=BlueBattleLab.build(:PIKACHU,50);pikachu.item=:ELECTRIUMZ;pikachu.moves=[Pokemon::Move.new(:THUNDERBOLT)]
      z,_=BlueRadicalAI::Validation.fixture([pikachu],[BlueBattleLab.build(:MAGIKARP,50)],'single','engine')
      z.instance_variable_set(:@blue_lab_battle,true);z.instance_variable_set(:@blue_mechanics,BlueBattleOptions.defaults)
      check.call('Z-Move has priority over Tera and Dynamax with a compatible crystal',z.blue_available_mechanics(0)==[:zmove,:tera,:dynamax] && z.pbGetEligibleBattleMechanic(0)==:zmove)
      z.blue_choose_mechanic(0,:zmove);z.battlers[0].display_zmoves;z.blue_choose_mechanic(0,:tera)
      check.call('Switching from Z restores original moves and clears its registration',z.battlers[0].moves[0].id==:THUNDERBOLT && !z.pbRegisteredZMove?(0) && z.pbRegisteredTerastallize?(0))
      battle=fixture
      scene=Scene.new;battle.instance_variable_set(:@scene,scene);battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
      scene.pbStartBattle(battle);show_battlers(scene,battle);scene.blue_driver=true
      Input.singleton_class.prepend(Keys) unless Input.singleton_class.ancestors.include?(Keys)
      Mouse.singleton_class.prepend(Pointer) unless Mouse.singleton_class.ancestors.include?(Pointer)
      @f6=true;BlueBattleOptions.instance_variable_set(:@test_menu_choices,[1])
      catch(:blue_selector_test_done) { scene.pbFightMenu(0,battle.pbGetEligibleBattleMechanic(0)) { |cmd| false } }
      BlueBattleOptions.instance_variable_set(:@test_menu_choices,nil)
      check.call('F6 selector reopens the real move menu with Terastal activated',scene.blue_captured==[:tera,2,:tera,false])
      battle.blue_choose_mechanic(0,:mega)
      battle.pbMegaEvolve(0)
      check.call('Charizard with Charizardite Y actually Mega Evolves in the real scene',battle.battlers[0].mega? && battle.battlers[0].form==2)
      check.call('An already Mega Evolved Pokemon cannot also Terastallize',!battle.pbCanTerastallize?(0))
      scene.pbEndBattle(0);scene=nil
      battle=fixture(:CHARIZARDITEY,'double');scene=Scene.new;battle.instance_variable_set(:@scene,scene)
      battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
      scene.pbStartBattle(battle);show_battlers(scene,battle);scene.blue_driver=:mouse;scene.blue_expect=:mega
      BlueBattleOptions.instance_variable_set(:@test_menu_choices,[0])
      catch(:blue_selector_test_done) { scene.pbFightMenu(0,battle.pbGetEligibleBattleMechanic(0)) { |cmd| false } }
      check.call('Mouse selector activates Mega in the real double battle menu',scene.blue_captured==[:mega,2,:mega,true])
      scene.pbEndBattle(0);scene=nil
      # Regression: a partner with Chlorophyll must jump ahead of a faster foe
      # on the SAME turn that Charizard Y Mega Evolves and starts Drought.
      battle=fixture(:CHARIZARDITEY,'double')
      scene=Scene.new;battle.instance_variable_set(:@scene,scene)
      battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
      scene.pbStartBattle(battle);show_battlers(scene,battle)
      chlorophyll=battle.battlers[2];foe=battle.battlers[3]
      chlorophyll.ability=:CHLOROPHYLL
      check.call('Chlorophyll fixture starts with no Sun',battle.field.weather==:None)
      check.call('Chlorophyll partner initially slower than opposing Sneasler',chlorophyll.pbSpeed<foe.pbSpeed)
      battle.pbCalculatePriority(true)
      check.call('Initial turn order puts fast foe before Chlorophyll',battle.pbPriority.index(foe)<battle.pbPriority.index(chlorophyll))
      battle.blue_choose_mechanic(0,:mega);battle.pbMegaEvolve(0)
      check.call('Mega Charizard Y starts Sun immediately',battle.battlers[0].form==2 && battle.field.weather==:Sun)
      check.call('Chlorophyll receives Sun Speed boost immediately',chlorophyll.pbSpeed>foe.pbSpeed)
      check.call('Weather change reorders other battlers before their moves',battle.pbPriority.index(chlorophyll)<battle.pbPriority.index(foe))
      scene.pbEndBattle(0);scene=nil
      battle=fixture;scene=Scene.new;battle.instance_variable_set(:@scene,scene)
      battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
      scene.pbStartBattle(battle);battle.blue_choose_mechanic(0,:tera);battle.pbTerastallize(0)
      check.call('Charizard holding its Mega Stone can actually choose and use Terastal instead',battle.battlers[0].tera? && !battle.battlers[0].mega?)
      check.call('An active Terastal form cannot also Mega Evolve or Dynamax',!battle.pbCanMegaEvolve?(0) && !battle.pbCanDynamax?(0))
      scene.pbEndBattle(0);scene=nil
    ensure
      @f6=false;@mouse=false;@point=nil;BlueBattleOptions.instance_variable_set(:@test_menu_choices,nil)
      $player.tera_charged=charge unless charge.nil?
      PBDebug.define_singleton_method(:logonerr,logger) if logger
      scene&.pbEndBattle(0)
    end
  end
end
