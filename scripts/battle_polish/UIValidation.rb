module BlueBattleUIValidation
  module Keys
    def triggerex?(key)
      if key==:R && BlueBattleUIValidation.instance_variable_get(:@run_key)
        BlueBattleUIValidation.instance_variable_set(:@run_key,false);return true
      end
      super
    end
    def trigger?(key)
      return true if key==Input::USE && BlueBattleUIValidation.instance_variable_get(:@skip_text)
      super
    end
  end
  class Scene < Battle::Scene
    attr_accessor :capture_miss,:capture_field,:capture_command
    def pbDisplayPausedMessage(*args);end
    def pbDisplayConfirmMessage(*args);true;end
    def pbGraphicsUpdate
      super
      if @capture_command && @sprites['blueCommandLocale']&.visible
        shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-portuguese-command-smoke.png');shot.dispose;@capture_command=false
      end
      if @capture_field && @sprites['fightWindow']&.visible && @sprites['fightWindow'].instance_variable_get(:@battler)
        shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-field-hud-smoke.png');shot.dispose;@capture_field=false
      end
      if @capture_miss && BlueBattleUI.clock-@capture_miss>0.7
        shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-miss-readable-smoke.png');shot.dispose;@capture_miss=nil
      end
    end
  end
  def self.check(value,label)
    raise label unless value
    @lines << 'PASS | '+label
  end
  def self.names
    result=[]
    [GameData::Species,GameData::Move,GameData::Item].each { |klass| klass.each { |data| result << [klass.to_s,data.id,data.name] } }
    result
  end
  def self.language(full)
    $PokemonSystem.blue_locale='en';before=names
    check(_INTL('Fight')=='Fight','English preference restores the original interface')
    $PokemonSystem.blue_locale='pt-BR'
    check(_INTL('Fight')=='Lutar' && _INTL("{1}'s attack missed!",'Charizard')=='Charizard errou o ataque!','Portuguese messages preserve the substituted Pokemon name')
    check(names==before,'Every registered Pokemon, move and item keeps its original name in Portuguese')
    check(BlueLocale.translate(GameData::Move.get(:PSYCHIC).name)=='Psychic','Rendered move names are protected even when they are also translatable words')
    nick=BlueBattleLab.build(:EEVEE,10);nick.name='Shadow';nick.name
    check(BlueLocale.translate(nick.name)=='Shadow','Custom Pokemon nicknames also remain unchanged when rendered')
    path='Graphics/UI/Battle/cursor_command'
    check(_INTL(path)==path,'Asset paths passed through _INTL remain valid filenames')
    check(BlueLocale.translate('Level 37')=='Nível 37','Runtime interpolation is translated without evaluating Ruby or changing its value')
    check(Marshal.load(Marshal.dump($PokemonSystem)).blue_locale=='pt-BR','Language choice persists through native save serialization')
    source='\\bHello, \\PN!\\nI can see you calling me over there!'
    translated=_MAPINTL(0,source)
    check(translated!=source && translated.scan(/\\b|\\PN|\\n/)==source.scan(/\\b|\\PN|\\n/),'Actual story dialogue is translated with its message controls intact') if full
    @lines << 'LOCALE_ENTRIES='+BlueLocale.translations.length.to_s
    check(BlueLocale.translations.length>=14_000,'Complete extracted dialogue, menu and description catalogue is installed') if full
    options=PokemonOption_Scene.new;options.pbStartScene
    first=options.instance_variable_get(:@options).first
    check(first.name=='Language / Idioma','Language selector is available at the top of the real Options menu')
    first.set(0,options)
    check($PokemonSystem.blue_locale=='en' && options.sprites['title'].text=='Options','Changing language refreshes the open settings screen to English')
    options.sprites['option'].setValueNoRefresh(0,1);first.set(1,options)
    check($PokemonSystem.blue_locale=='pt-BR' && options.sprites['title'].text=='Configurações','Changing language refreshes the open settings screen to Portuguese')
    Graphics.update;shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-portuguese-options-smoke.png');shot.dispose
    options.pbEndScene;options=nil
  ensure
    options&.pbEndScene
  end
  def self.choices
    active=BlueCampaign.method(:active?);BlueCampaign.define_singleton_method(:active?) { true }
    [ [['Single Battle','Double Battle','Triple Battle'],1],[['1 Pokémon (Singles)','2 Pokémon (Doubles)','3 Pokémon (Triples)','6 Pokémon (Full Team)'],1],[['Full Team Heal','Singles ','Doubles ','Triples'],2] ].each do |labels,wanted|
      commands=[RPG::EventCommand.new(102,0,[labels,1])]
      labels.each_with_index { |s,i| commands << RPG::EventCommand.new(402,0,[i,s]);commands << RPG::EventCommand.new(0,1,[]) }
      commands << RPG::EventCommand.new(404,0,[]);commands << RPG::EventCommand.new
      interpreter=Interpreter.new;interpreter.setup(commands,0)
      result=interpreter.setup_choices([labels,1])
      check(result[0]==[labels[wanted],'Cancel'] && result[2]==[wanted,-999],'Every Story format question keeps Doubles and safe cancellation, even in Portuguese')
    end
    nurse=['Full Team Heal','Form Trade','Cancel']
    commands=[RPG::EventCommand.new(102,0,[nurse,3])]
    nurse.each_with_index { |s,i| commands << RPG::EventCommand.new(402,0,[i,s]);commands << RPG::EventCommand.new(0,1,[]) }
    commands << RPG::EventCommand.new(404,0,[]);commands << RPG::EventCommand.new
    interpreter=Interpreter.new;interpreter.setup(commands,0)
    check(interpreter.setup_choices([nurse,3])[0]==nurse,'Story-wide format filtering preserves the Pokemon Center nurse')
    common=NPCTrainer.new('Normal payout comparison',:HOENNIAN_ORAS_AROMALADY)
    leader=NPCTrainer.new('Marigold (2v2 Full Power)',:HOENNIAN_ORAS_AROMALADY)
    check(leader.base_money==2*common.base_money,'Gym prize rate is twice the normal rate at equal trainer class and stage')
  ensure
    BlueCampaign.define_singleton_method(:active?,active) if active
  end
  def self.cleaner
    active=BlueCampaign.method(:active?);BlueCampaign.define_singleton_method(:active?) { true }
    old_bag=$bag;$bag=PokemonBag.new;$bag.add(:BLUEEVCLEANER,3)
    mon=BlueBattleLab.build(:EEVEE,50);mon.ev[:HP]=252;mon.ev[:ATTACK]=252;mon.ev[:SPEED]=6;mon.calc_stats
    preserved=[mon.iv.dup,mon.nature_id,mon.level,mon.moves.map(&:id),mon.item_id]
    scene=Object.new
    [:pbRefresh,:pbClearAnnotations,:pbHardRefresh,:pbUpdate,:pbDisplay].each { |name| scene.define_singleton_method(name) { |*args| } }
    scene.define_singleton_method(:pbConfirm) { |*args| false }
    check(!pbUseItemOnPokemon(:BLUEEVCLEANER,mon,scene) && $bag.quantity(:BLUEEVCLEANER)==3 && mon.ev.values.sum==510,'Cancelling EV Cleaner preserves EVs and item quantity')
    scene.define_singleton_method(:pbConfirm) { |*args| true }
    check(pbUseItemOnPokemon(:BLUEEVCLEANER,mon,scene) && $bag.quantity(:BLUEEVCLEANER)==2 && mon.ev.values.sum==0,'Native bag use resets all six EVs and consumes exactly one EV Cleaner')
    check([mon.iv,mon.nature_id,mon.level,mon.moves.map(&:id),mon.item_id]==preserved,'EV Cleaner preserves IVs, Nature, level, moves and held item')
    check(!pbUseItemOnPokemon(:BLUEEVCLEANER,mon,scene) && $bag.quantity(:BLUEEVCLEANER)==2,'A Pokemon with zero EVs does not consume EV Cleaner')
    check(BlueCampaign.price(GameData::Item.get(:BLUEEVCLEANER))==2_000 && BlueCampaign.stock(4).include?(:BLUEEVCLEANER),'EV Cleaner is sold in Training for exactly 2000')
  ensure
    $bag=old_bag if old_bag
    BlueCampaign.define_singleton_method(:active?,active) if active
  end
  def self.scene
    battle=BlueBattleOptions::MechanicValidation.fixture(:CHARIZARDITEY,'double')
    scene=Scene.new;battle.instance_variable_set(:@scene,scene)
    battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
    scene.pbStartBattle(battle)
    BlueBattleOptions::MechanicValidation.show_battlers(scene,battle)
    battle.field.weather=:Rain;battle.field.weatherDuration=4
    battle.field.terrain=:Electric;battle.field.terrainDuration=3
    battle.field.effects[PBEffects::TrickRoom]=5
    battle.sides[0].effects[PBEffects::Tailwind]=4;battle.sides[1].effects[PBEffects::Tailwind]=2
    rows=BlueBattleUI.field_rows(battle)
    check(rows.any? { |r| r[0]=='Clima: Chuva (4)' } && rows.any? { |r| r[0]=='Terreno: Elétrico (3)' },'Field HUD shows the active weather, terrain and turn counts')
    check(rows.any? { |r| r[0]=='Trick Room (5)' } && rows.any? { |r| r[0]=='Tailwind / Seu lado (4)' } && rows.any? { |r| r[0]=='Tailwind / Rival (2)' },'Trick Room and both distinct Tailwind sides are shown')
    scene.pbShowWindow(Battle::Scene::FIGHT_BOX);scene.blue_refresh_field_hud;Graphics.update
    shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-field-hud-smoke.png');shot.dispose
    Input.singleton_class.prepend(Keys) unless Input.singleton_class.ancestors.include?(Keys)
    @run_key=true;scene.capture_command=true
    check(scene.pbCommandMenu(0,true)==3,'Physical R shortcut returns the native Run command')
    @run_key=true
    scene.capture_field=true
    scene.pbFightMenu(0,battle.pbGetEligibleBattleMechanic(0)) { |cmd| false }
    check(scene.pbCommandMenu(0,true)==3,'Physical R also leaves the move selector and chooses native Run')
    old_speed=$GameSpeed;$GameSpeed=1
    @skip_text=true;battle.instance_variable_set(:@blue_miss_notice,true)
    started=BlueBattleUI.clock;scene.capture_miss=started
    scene.pbDisplayMessage(_INTL("{1}'s attack missed!",'Charizard'))
    elapsed=BlueBattleUI.clock-started
    check(elapsed>=BlueBattleUI::MISS_SECONDS,'Miss message remains readable for 1.6 real seconds despite turbo and repeated confirmation')
    @lines << 'MISS_REAL_SECONDS='+elapsed.round(3).to_s
    @skip_text=false;$GameSpeed=old_speed
    battle.instance_variable_set(:@blue_miss_notice,false)
    battle.field.weather=:None;battle.field.terrain=:None;battle.field.effects[PBEffects::TrickRoom]=0
    battle.sides.each { |s| s.effects[PBEffects::Tailwind]=0 }
    check(BlueBattleUI.field_rows(battle)==[['Campo: normal',:none],['R: Fugir',:shortcut]],'Expired field effects disappear from the HUD')
  ensure
    @run_key=false;@skip_text=false
    $GameSpeed=old_speed if defined?(old_speed) && !old_speed.nil?
    scene&.pbEndBattle(0)
  end
  def self.run(full=true)
    @lines=[];locale=$PokemonSystem.blue_locale
    language(full);choices;cleaner;scene
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    $PokemonSystem.blue_locale=locale if locale
    File.open('Data/blue-ui-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
