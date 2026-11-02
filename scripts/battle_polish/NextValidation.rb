# Native integration proofs; fresh lab memory only, never a campaign save.
module BlueNextValidation
  module LearningMessages
    def trigger?(key)
      return true if key==Input::USE && BlueNextValidation.instance_variable_get(:@learning_messages)
      super
    end
  end
  class ReminderScene < MoveRelearner_Scene
    def pbConfirm(*args);true;end
    def pbChooseMove
      index=@moves.index(BlueNextValidation.instance_variable_get(:@remember_move))
      @sprites['commands'].index=index
      @sprites['background'].y=78+(index-@sprites['commands'].top_item)*64
      pbDrawMoveList
      y=80+(index-@sprites['commands'].top_item)*64+24
      BlueTouchValidation.drive([[100,y]]) { super }
    end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.training
    pokemon=BlueBattleLab.build(:PIKACHU,30)
    ui=Object.new;ui.define_singleton_method(:pbDisplay) { |*a| };ui.define_singleton_method(:pbConfirm) { |*a| true };ui.define_singleton_method(:pbRefresh) {}
    BlueTraining::CLEANERS.each do |id,stat|
      pokemon.ev.each_key { |key| pokemon.ev[key]=40 };before=pokemon.ev.dup
      check(BlueCampaign.price(GameData::Item.get(id))==750 && BlueCampaign.category(GameData::Item.get(id))==4,'Single-stat cleaner is sold for $750: '+id.to_s)
      check(ItemHandlers.triggerUseOnPokemon(id,1,pokemon,ui) && pokemon.ev[stat]==0 && pokemon.ev.all? { |key,n| key==stat || n==before[key] },'Actual cleaner handler resets only '+stat.to_s)
      check(!ItemHandlers.triggerUseOnPokemon(id,1,pokemon,ui),'Zero EVs do not consume '+id.to_s)
    end
    pokemon.ev[:HP]=40;ui.define_singleton_method(:pbConfirm) { |*a| false };before=pokemon.ev.dup
    check(!ItemHandlers.triggerUseOnPokemon(:BLUEEVHP,1,pokemon,ui) && pokemon.ev==before,'Cancel preserves the EVs and cleaner')
    pokemon.steps_to_hatch=1
    check(!BlueTraining.clean(pokemon,:HP),'Single-stat cleaners reject eggs');pokemon.steps_to_hatch=0
    pokemon.moves=[Pokemon::Move.new(:TACKLE)]
    expected=(pokemon.getMoveList.select { |level,id| level<=30 }.map(&:last)+Array(pokemon.first_moves)).uniq.reject { |id| pokemon.hasMove?(id) }
    check(BlueTraining.moves(pokemon)==expected && expected.include?(:THUNDERSHOCK),'Party reminder includes early moves missed by a Pokemon caught at level 30')
    @remember_move=:THUNDERSHOCK
    scene=ReminderScene.new;screen=BlueTraining::Reminder.new(scene)
    @learning_messages=true
    check(screen.pbStartScreen(pokemon) && pokemon.hasMove?(:THUNDERSHOCK),'Actual native reminder, click, confirmation and learning function teach the forgotten move')
    scene=nil;@learning_messages=false
    party_screen=PokemonPartyScreen.new(PokemonParty_Scene.new,[pokemon]);names=[];MenuHandlers.each_available(:party_menu,party_screen,[pokemon],0) { |id,hash,name| names << id }
    check(names.include?(:blue_remember),'The actual party context menu exposes Remember moves')
    pokemon.steps_to_hatch=1;party_screen=PokemonPartyScreen.new(PokemonParty_Scene.new,[pokemon]);names=[];MenuHandlers.each_available(:party_menu,party_screen,[pokemon],0) { |id,hash,name| names << id }
    check(!names.include?(:blue_remember),'Eggs do not expose the party reminder')
  ensure
    @learning_messages=false;scene&.pbEndScene
  end
  def self.fishing
    before=[];areas=0;different=0
    GameData::Encounter.each do |data|
      source=Marshal.dump(data.types);tables=BlueFishing.tables(data.types)
      original=BlueFishing::RODS.flat_map { |r| data.types[r] || [] }.map { |s| s[1] }.uniq.sort_by(&:to_s)
      next if original.empty?
      areas+=1
      raise 'A fishing species was lost' unless tables[:SuperRod].map { |s| s[1] }.uniq.sort_by(&:to_s)==original
      raise 'Old Rod includes a rare species' unless tables[:OldRod].all? { |s| BlueFishing.rank(s[1])==1 }
      raise 'Good Rod includes an exclusive rare species' unless tables[:GoodRod].all? { |s| BlueFishing.rank(s[1])<=2 }
      raise 'Fishing rewrote PBS or Surf encounters' unless Marshal.dump(data.types)==source && data.types.reject { |k,v| BlueFishing::RODS.include?(k) }==tables.reject { |k,v| BlueFishing::RODS.include?(k) }
      profiles=BlueFishing::RODS.map { |rod| tables[rod] }
      raise 'Different rarity classes still have identical rod profiles' if original.map { |id| BlueFishing.rank(id) }.uniq.length>1 && profiles.uniq.length==1
      different+=1 if profiles.uniq.length>1
    end
    check(areas>0 && different>0,'Audited every compiled fishing map/version: local species preserved, rod rarities differ, Surf and PBS unchanged')
    @lines << 'FISHING_TABLES='+areas.to_s+' DIFFERENT_ROD_TABLES='+different.to_s
    check(BlueFishing.rank(:MAGIKARP)==1 && BlueFishing.rank(:DRATINI)==3 && BlueFishing.rank(:FEEBAS)==3,'Official fishing anchors keep common Magikarp and rare Dratini/Feebas separate')
    methods=BlueFishing.tables({SuperRod:[[50,:MAGIKARP,5,10],[30,:BARBOACH,5,10],[20,:DRATINI,5,10]]})
    seen=Marshal.dump($player.pokedex)
    [:MAGIKARP,:BARBOACH,:DRATINI].each { |id| $player.pokedex.set_seen(id) }
    rows=BlueHabitat.fishing_entries(methods)
    check(rows.length==3 && rows.find { |x| x[:species]==:MAGIKARP }[:rods]==BlueFishing::RODS && rows.find { |x| x[:species]==:DRATINI }[:rods]==[:SuperRod],'Combined Fishing page shows each species once with exactly its usable rods')
    scene=BlueHabitat::Scene.new('Cherryhill City',_INTL('Fishing'),rows)
    BlueTouchValidation.drive([proc { shot('blue-fishing-rods-smoke');[450,356] }]) { scene.run };scene=nil
    method=BlueBattleLab.method(:choose);captured=nil
    BlueBattleLab.define_singleton_method(:choose) { |title,labels,*args| captured=labels;-1 }
    BlueHabitat.open_area({name:'Test',map:77,methods:methods})
    check(captured.count { |s| s==_INTL('Fishing') }==1 && captured.none? { |s| ['Old Rod','Good Rod','Super Rod'].include?(s) },'Habitat encounter menu groups all three rods into one Fishing card')
  ensure
    $player.instance_variable_set(:@pokedex,Marshal.load(seen)) if seen
    BlueBattleLab.define_singleton_method(:choose,method) if method
    scene&.dispose
  end
  def self.ui
    check(GameData::Ability.get(:BLAZE).name=='Blaze' && BlueLocale.translate('Blaze')=='Blaze','Ability names remain English in Portuguese menus and battle text')
    check(BlueCampaign.shop_name(GameData::Item.get(:TM025)).include?(GameData::Move.get(GameData::Item.get(:TM025).move).name),'TM shop labels combine the actual TM number and English move name')
    BlueCampaign::Shop.new.open do |shop|
      shop.instance_variable_set(:@tab,5);shop.refresh;shot('blue-tm-names-smoke')
      check(shop.instance_variable_get(:@list).instance_variable_get(:@commands).any? { |s| s.include?('Protect') },'Native TM stock visibly includes English move names')
    end
    badges=$player.badges.dup;card=nil
    [0,2,5,11].each_with_index do |count,index|
      $player.badges.map! { false };count.times { |i| $player.badges[i]=true }
      card=PokemonTrainerCard_Scene.new;card.pbStartScene
      check(card.instance_variable_get(:@sprites)['blueDifficulty'] && BlueTraining.difficulty==_INTL(BlueTraining::LABELS[index]),'Native trainer card shows current progression: '+BlueTraining::LABELS[index])
      shot('blue-trainer-difficulty-smoke') if index==3
      card.pbEndScene;card=nil
    end
  ensure
    $player.badges.replace(badges) if badges;card&.pbEndScene
  end
  def self.run
    @lines=[];lang=$PokemonSystem.blue_locale;pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?)
    $PokemonSystem.blue_locale='pt-BR'
    BlueLabPointer.define_singleton_method(:enabled?) { true };BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    Input.singleton_class.prepend(LearningMessages) unless Input.singleton_class.ancestors.include?(LearningMessages)
    training;fishing;ui
    if File.file?('Data/blue-reference-export-request.txt')
      battle,_=BlueRadicalAI::Validation.fixture([BlueBattleLab.build(:PIKACHU,50)],[BlueBattleLab.build(:MAGIKARP,50)],'single','engine')
      data=BlueCampaignReference.export(battle)
      check(data[:masters].length==18 && data[:masters].values.all? { |variants| variants.length==4 && variants.all? { |v| v[:team].length==6 } },'Exported all 18 Full Doubles leaders in all four real campaign difficulties')
      File.delete('Data/blue-reference-export-request.txt')
    end
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @learning_messages=false;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer;BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.write('Data/blue-next-validation.txt',@lines.join("\n")+"\n")
  end
end
