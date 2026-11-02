# Native integration checks. Only the laboratory's fresh in-memory data is used.
module BlueReadoutsValidation
  module Keys
    def triggerex?(key)
      if key==:P && BlueReadoutsValidation.instance_variable_get(:@press_preview)
        BlueReadoutsValidation.instance_variable_set(:@press_preview,false);return true
      end
      super
    end
    def trigger?(key)
      return true if key==Input::BACK && BlueReadoutsValidation.instance_variable_get(:@close_preview)
      return true if key==Input::MOUSELEFT && BlueReadoutsValidation.instance_variable_get(:@click_preview)
      super
    end
  end
  module PreviewTrace
    def run
      BlueReadoutsValidation.instance_variable_set(:@preview_runs,(BlueReadoutsValidation.instance_variable_get(:@preview_runs) || 0)+1)
      super
    end
  end
  class TranscriptScene < Battle::Scene
    attr_reader :messages
    def initialize;super;@messages=[];end
    def pbDisplayMessage(message,*args);@messages << message;end
    def pbDisplayPausedMessage(message,*args);@messages << message;end
    def pbDisplayConfirmMessage(message,*args);@messages << message;true;end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(path)
    Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+path+'.png');b.dispose
  end
  def self.choices
    old=$PokemonGlobal.blue_story_mode
    $PokemonGlobal.blue_story_mode=:story
    list=load_data('Data/Map001.rxdata').events[9].pages[0].list
    [226,240,336].each do |index|
      interpreter=Interpreter.new;interpreter.setup(Marshal.load(Marshal.dump(list)),0,1)
      interpreter.instance_variable_set(:@index,index)
      result=interpreter.setup_choices(list[index].parameters)
      case index
      when 226
        check(result[0]==['Yes (Metagame Wiki Dex)'] && result[2]==[1],'Real Story event offers only Metagame Wiki Dex with its original branch')
      when 240
        check(result[0]==['Traditional Starters','Monotype Starters'] && result[2]==[2,3],'Real starter menu keeps only Traditional and Monotype with original branch IDs')
      when 336
        check(result[0].length==18 && result[0].all? { |s| s.start_with?('Mono ') },'Real merged type menu contains all 18 types and excludes random starters')
      end
    end
    $PokemonGlobal.blue_story_mode=:battle
    result=BlueAdventure.filter([['Form Trade','Begin Story Mode','Cancel'],3,[0,1,2]])
    check(result[0]==['Form Trade','Cancel'] && result[2]==[0,2],'Battle Mode removes Begin Story Mode without changing remaining event branches')
    BlueStory.choose_mode(:story)
    check($PokemonGlobal.blue_story_mode==:battle,'A direct mode change cannot convert a Battle save into Story')
    check(pbStoryModeSetup==false && $PokemonGlobal.blue_story_mode==:battle,'Story setup itself also rejects a Battle save')
    event=load_data('Data/Map001.rxdata').events[9].pages[0].list
    index=event.each_index.find { |i| event[i].code==101 && event[i+1]&.code==102 && event[i+1].parameters[0].include?('Intended Soundtrack') }
    check(!!index,'Active new-game event contains the soundtrack question')
    interpreter=Interpreter.new;interpreter.setup(event,0,1);interpreter.instance_variable_set(:@index,index)
    interpreter.instance_variable_set(:@parameters,event[index].parameters)
    check(interpreter.command_101,'Soundtrack question is bypassed without opening a message window')
    next_index=interpreter.instance_variable_get(:@index)+1
    check(event[next_index].code==402 && event[next_index].parameters[1]=='Intended Soundtrack' && !$game_switches[100],'Bypass enters the original default soundtrack branch')
  ensure
    $PokemonGlobal.blue_story_mode=old
  end
  def self.pools
    count=0
    GameData::Type.each do |type|
      next if type.pseudo_type || type.id==:STELLAR
      list=BlueAdventure.monotype_pool(type.id)
      check(list.length>=2,type.id.to_s+': multiple starter choices')
      check(list.all? { |id| s=GameData::Species.get(id);s.types.include?(type.id) && s.base_stats.values.sum<=350 && s.base_stats.values.all? { |v| v>0 } },type.id.to_s+': every candidate currently has the selected type and BST <=350')
      count+=1
    end
    check(count==18,'All 18 ordinary types have a legal native starter pool')
  end
  def self.access
    mode=$PokemonGlobal.blue_story_mode;flags=[62,76].to_h { |id| [id,$game_switches[id]] }
    active=BlueBattleLab::ACTIVE;dex=Marshal.dump($player.pokedex);in_battle=$game_temp.in_battle
    BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,false)
    $game_temp.in_battle=false;$PokemonGlobal.blue_story_mode=:story;$game_switches[62]=false;$game_switches[76]=true
    $player.pokedex.unlock(0)
    check($player.pokedex.accessible_dexes==[0],'Story Dex selector exposes only Metagame Wiki Dex without erasing other registrations')
    check(BlueAdventure.pc_available?,'Portable PC is available in the main Story Mode')
    $PokemonGlobal.blue_story_mode=:battle;$game_switches[62]=true;$game_switches[76]=false
    check(BlueAdventure.pc_available?,'Portable PC is also available in the main Battle Mode')
    found=false;MenuHandlers.each_available(:pause_menu) { |id,hash,name| found=true if id==:blue_pc }
    check(found,'The real pause menu registers the portable PC entry')
    check(!!pbResolveBitmap(MENU_FILE_PATH+$PokemonSystem.from_current_menu_theme('menu_blue_pc')),'Portable PC resolves an existing themed menu icon')
    $game_temp.in_battle=true;check(!BlueAdventure.pc_available?,'Boxes cannot be opened during a battle')
  ensure
    if defined?(active) && !active.nil?
      BlueBattleLab.send(:remove_const,:ACTIVE) if BlueBattleLab.const_defined?(:ACTIVE,false)
      BlueBattleLab.const_set(:ACTIVE,active)
    end
    $game_temp.in_battle=in_battle
    $PokemonGlobal.blue_story_mode=mode
    flags&.each { |id,value| $game_switches[id]=value }
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
  end
  def self.locale
    $PokemonSystem.blue_locale='pt-BR'
    examples={
      'Oh! A wild {1} appeared!'=>['Um Pikachu selvagem apareceu!',['Pikachu']],
      'Go! {1}!'=>['Vai, Charizard!',['Charizard']],
      'You are challenged by {1}!'=>['Rival desafia você!',['Rival']],
      '{1} used {2}!'=>['Charizard usou Flamethrower!',['Charizard','Flamethrower']]
    }
    examples.each { |source,(target,args)| check(_INTL(source,*args)==target,'Live _INTL translates '+source) }
    check(BlueLocale.translate('Oh! A wild Pikachu appeared!')=='Um Pikachu selvagem apareceu!','Already formatted wild intro is translated too')
    check(BlueLocale.translate('Stage 3/6')=='Etapa 3/6','Repeated printf tokens retain separate values')
    check(BlueLocale.translate('HP < 50%').is_a?(String),'A comparison sign is not mistaken for a rich-text tag')
    check(BlueLocale.translate('<c2=FF0000FF>Task:</c2> Look for clues.').include?('Objetivo:'),'Rich quest labels are translated before glyph splitting')
    check(BlueLocale.translate('Quests')=='Missões','Pause menu quest entry has a Portuguese label')
    check(_INTL('{1} tasks','Active')=='Missões Ativas','Substituted UI state labels are translated before interpolation')
    check(BlueLocale.translate('The opposing Blastoise')=='O Blastoise adversário','Battle subject prefixes are translated')
    check(GameData::Move.get(:FLAMETHROWER).name=='Flamethrower' && GameData::Item.get(:CHARIZARDITEY).name=='Charizardite Y','Move and item names remain original')
    check(GameData::Ability.get(:BLAZE).name=='Blaze','Ability names remain in English while their IDs stay intact')
  end
  def self.render
    before=Marshal.dump([$player.party,$PokemonStorage]);dex=Marshal.dump($player.pokedex)
    $player.pokedex.clear;$player.pokedex.set_seen(:BULBASAUR);$player.pokedex.set_owned(:BULBASAUR)
    dex_switch=$game_switches[Settings::POKEDEX_DATA_PAGE_SWITCH];$game_switches[Settings::POKEDEX_DATA_PAGE_SWITCH]=true
    scene=PokemonPokedexInfo_Scene.new
    scene.pbStartScene([{species: :BULBASAUR,name:'Bulbasaur',number:1}],0,0)
    page=scene.instance_variable_get(:@page_list).index(:page_data)+1
    scene.instance_variable_set(:@page,page);scene.drawPage(page);shot('blue-dex-numbers-smoke');scene.pbEndScene;scene=nil
    quests=Marshal.dump($PokemonGlobal.quests)
    $PokemonGlobal.quests.active_quests << Quest.new(:CherryhillCityQuest1,colorQuest(nil),true)
    scene=QuestList_Scene.new;scene.pbStartScene;shot('blue-quest-list-smoke')
    scene.instance_variable_get(:@sprites)['overlay1'].opacity=0
    scene.instance_variable_get(:@sprites)['overlay_control'].opacity=0
    scene.instance_variable_get(:@sprites)['itemlist'].visible=false
    scene.instance_variable_get(:@sprites)['overlay2'].opacity=255;scene.instance_variable_get(:@sprites)['overlay3'].opacity=255
    scene.drawQuestDesc($PokemonGlobal.quests.active_quests.last);shot('blue-quest-detail-smoke');scene.pbEndScene;scene=nil
    $PokemonGlobal.instance_variable_set(:@quests,Marshal.load(quests));quests=nil
    scene=PokemonStorageScene.new;screen=PokemonStorageScreen.new(scene,$PokemonStorage)
    scene.pbStartBox(screen,0);shot('blue-pc-boxes-smoke');scene.pbCloseBox;scene=nil
    check(Marshal.dump([$player.party,$PokemonStorage])==before,'Opening native boxes and Dex does not grant or remove Pokemon')
    battle=BlueBattleOptions::MechanicValidation.fixture(:CHARIZARDITEY,'double')
    scene=BlueBattleUIValidation::Scene.new;battle.instance_variable_set(:@scene,scene)
    battle.backdrop='indoor1';battle.environment=:None;battle.time=0;battle.showAnims=false
    scene.pbStartBattle(battle);BlueBattleOptions::MechanicValidation.show_battlers(scene,battle)
    battle.battlers[0].stages[:DEFENSE]=1;battle.battlers[0].stages[:ATTACK]=-1
    battle.battlers[1].stages[:DEFENSE]=1;battle.battlers[1].stages[:ACCURACY]=-2
    check(BlueReadouts.stage_labels(battle.battlers[0])==[['0.67x Atq',false],['1.5x Def',true]],'Attack/defense stage multipliers and colors distinguish drops from boosts')
    check(BlueReadouts.stage_labels(battle.battlers[1]).include?(['0.6x Prec',false]),'Accuracy uses its native three-based ratio')
    scene.pbShowWindow(Battle::Scene::FIGHT_BOX);scene.instance_variable_set(:@blue_run_scope,:fight)
    scene.instance_variable_get(:@sprites)['fightWindow'].battler=battle.battlers[0]
    scene.pbGraphicsUpdate;shot('blue-stat-stages-smoke')
    $player.pokedex.clear;$player.pokedex.set_seen(:BLASTOISE)
    before_dex=Marshal.dump($player.pokedex);entries=BlueReadouts.preview_entries(battle)
    check(entries[0][:species]==:BLASTOISE && entries[1]=={species:nil,name:'???'},'Preview exposes icons only for previously seen species; unknown slots contain no hidden details')
    preview=BlueReadouts::Preview.new(entries);preview.start;shot('blue-opponent-preview-smoke');preview.dispose;preview=nil
    check(Marshal.dump($player.pokedex)==before_dex,'Viewing an unknown opponent does not mark it as seen')
    Input.singleton_class.prepend(Keys) unless Input.singleton_class.ancestors.include?(Keys)
    BlueReadouts::Preview.prepend(PreviewTrace) unless BlueReadouts::Preview.ancestors.include?(PreviewTrace)
    before_battle=Marshal.dump([battle.pbParty(0),battle.pbParty(1),battle.turnCount,battle.choices])
    @preview_runs=0;@press_preview=true;@close_preview=true
    scene.pbUpdate
    check(@preview_runs==1,'Physical P opens and closes the real preview modal from the battle UI')
    position=BlueLabPointer.method(:position);button=scene.instance_variable_get(:@sprites)['bluePreviewButton']
    BlueLabPointer.define_singleton_method(:position) { [button.x+3,button.y+3] }
    @click_preview=true;scene.pbUpdate;@click_preview=false
    BlueLabPointer.define_singleton_method(:position,position);position=nil
    check(@preview_runs==2,'Clicking P: Rival opens the same native preview modal')
    check(Marshal.dump([battle.pbParty(0),battle.pbParty(1),battle.turnCount,battle.choices])==before_battle,'Preview does not spend a turn, change commands or alter either team')
    @close_preview=false
    battle.battlers[0].stages.each_key { |stat| battle.battlers[0].stages[stat]=0 }
    check(BlueReadouts.stage_labels(battle.battlers[0]).empty?,'Reset stages remove all badges')
    scene.pbEndBattle(0);scene=nil
  ensure
    @press_preview=false;@close_preview=false;@click_preview=false
    BlueLabPointer.define_singleton_method(:position,position) if position
    preview&.dispose
    scene.pbEndBattle(0) if scene.is_a?(Battle::Scene)
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    $PokemonGlobal.instance_variable_set(:@quests,Marshal.load(quests)) if quests
    $game_switches[Settings::POKEDEX_DATA_PAGE_SWITCH]=dex_switch unless dex_switch.nil?
  end
  def self.wild_transcript
    party=$player.party;dex=Marshal.dump($player.pokedex);in_battle=$game_temp.in_battle
    ally=BlueBattleLab.build(:PIKACHU,80);ally.moves=[Pokemon::Move.new(:THUNDERBOLT)]
    foe=BlueBattleLab.build(:MAGIKARP,5);foe.moves=[Pokemon::Move.new(:SPLASH)]
    $player.party=[ally];$game_temp.in_battle=true
    scene=TranscriptScene.new;battle=Battle.new(scene,[ally],[foe],[$player],nil)
    battle.instance_variable_set(:@blue_lab_battle,true)
    battle.instance_variable_set(:@blue_mechanics,BlueBattleOptions.defaults.transform_values { false })
    battle.controlPlayer=true;battle.showAnims=false;battle.internalBattle=false;battle.canLose=true
    battle.expGain=false;battle.moneyGain=false;battle.backdrop='indoor1';battle.environment=:None;battle.time=0
    result=battle.pbStartBattle
    File.open('Data/blue-portuguese-wild-transcript.txt','wb') { |f| f.write(scene.messages.join("\n")+"\n") }
    check(result==1,'A complete native wild battle finishes with Portuguese selected')
    check(scene.messages.any? { |m| m.include?('Um Magikarp selvagem apareceu!') },'Actual wild encounter intro is displayed in Portuguese')
    check(scene.messages.any? { |m| m.include?('Vai, Pikachu!') },'Actual initial send-out is displayed in Portuguese')
    check(scene.messages.any? { |m| m.include?('usou Thunderbolt!') },'Actual turn message translates the sentence and preserves the move name')
    check(scene.messages.none? { |m| m.match?(/\b(?:appeared|sent out|used|fainted|challenged|wild)\b/i) },'No English encounter/action/fainting markers remain in the native battle transcript')
  ensure
    $player.party=party if party
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    $game_temp.in_battle=in_battle
  end
  def self.run
    @lines=[];lang=$PokemonSystem.blue_locale
    choices;pools;access;locale;render;wild_transcript
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    $PokemonSystem.blue_locale=lang if lang
    File.open('Data/blue-readouts-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
