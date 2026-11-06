# Opt-in engine regressions. Uses the lab's fresh, non-saving in-memory player.
module BlueMenuValidation
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;image=Graphics.snap_to_bitmap;image.to_file('Data/'+name+'.png');image.dispose;end
  def self.gates
    old_mode=$PokemonGlobal.blue_story_mode;old_traditional=$PokemonGlobal.blue_traditional_starters
    active=BlueBattleLab::ACTIVE;badges=$player.badges.dup
    BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,false)
    $PokemonGlobal.blue_story_mode=:story;$PokemonGlobal.blue_traditional_starters=true
    ids=[];GameData::Species.each { |s| ids << s.id if s.form==0 && s.flags.include?('DessastreParadoxal') && s.flags.include?('Paradox') }
    check(ids.length==44,'44 ready author Paradoxes compiled')
    [0,2,5,11].each do |count|
      $player.badges.map! { false };count.times { |i| $player.badges[i]=true }
      generated=ids.map { |id| pbGenerateWildPokemon(id,10).species_data }
      cap=BlueStory.cap
      check(generated.all? { |s| cap ? s.base_stats.values.sum<=cap : ids.include?(s.id) },'Real wild generator applies the crystal gate at '+count.to_s+' crystals')
      habitat=BlueHabitat.species(ids.map { |id| [5,id,5,5] })
      check(habitat.sort==generated.map(&:species).uniq.sort,'Habitat Dex agrees with actual wild replacements at '+count.to_s+' crystals')
    end
  ensure
    $PokemonGlobal.blue_story_mode=old_mode;$PokemonGlobal.blue_traditional_starters=old_traditional
    $player.badges.replace(badges) if badges
    if defined?(active);BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,active);end
  end
  def self.storage
    party=$player.party;storage=$PokemonStorage
    $player.party=[:BULBASAUR,:CHARMANDER,:SQUIRTLE].map { |id| BlueBattleLab.build(id,10) }
    $PokemonStorage=PokemonStorage.new;$PokemonStorage[0,0]=BlueBattleLab.build(:EEVEE,10)
    scene=PokemonStorageScene.new;screen=PokemonStorageScreen.new(scene,$PokemonStorage);scene.pbStartBox(screen,0)
    selected=BlueTouchValidation.drive([[216,72]]) { scene.pbSelectBoxInternal($player.party) }
    check(selected==[0,0],'PC mouse/touch returns the actual first box slot')
    shot('blue-pc-touch-smoke')
    scene.pbShowPartyTab
    panel=scene.instance_variable_get(:@sprites)['boxparty'];x,y=BlueLabPointer.origin(panel)
    selected=BlueTouchValidation.drive([[x+104,y+34]]) { scene.pbSelectPartyInternal($player.party,false) }
    check(selected==1,'PC party touch returns the actual second party slot')
    scene.pbHidePartyTab
    selected=BlueTouchValidation.drive([[420,338]]) { scene.pbSelectBoxInternal($player.party) }
    check(selected==[-3,-1],'PC Exit touch uses the native close action')
    scene.pbCloseBox;scene=nil
  ensure
    scene&.pbCloseBox;$player.party=party if party;$PokemonStorage=storage if storage
  end
  def self.hub
    mobile=BlueMobile.method(:enabled?);entry=BlueMenuSupport.method(:entry)
    BlueMobile.define_singleton_method(:enabled?) { true }
    screen=BlueBattleHub::Screen.new;screen.mount
    check(Graphics.width==640 && Graphics.height==480,'Android Hub uses a reduced 640x480 render surface')
    rows=screen.data_rows;started=BlueBattleUI.clock
    200.times { raise 'Picker cache rebuilt' unless screen.data_rows.equal?(rows) }
    @lines << 'HUB_200_CACHED_READS_SECONDS='+(BlueBattleUI.clock-started).round(4).to_s
    sprites=screen.instance_variable_get(:@decorations)
    check(sprites.all? { |s| s.class==Sprite && s.bitmap.width<=96 && s.bitmap.height<=96 },'Builder uses bounded static icons, without high-resolution Pokemon animations')
    before=sprites.map(&:object_id);screen.changed(false);screen.update_portraits
    check(before==screen.instance_variable_get(:@decorations).map(&:object_id),'Changing stats does not reload unchanged portrait assets')
    button=screen.buttons.find { |b| b[:id]==:side1 };x,y,w,h=button[:rect];scale=screen.instance_variable_get(:@ui_scale)
    BlueTouchValidation.drive([[((x+w/2)*scale).round,((y+h/2)*scale).round]]) { Input.update;screen.handle_input }
    check(screen.instance_variable_get(:@side)==1,'Scaled Android touch selects the correct team')
    screen.render
    BlueMenuSupport.define_singleton_method(:entry) { |*args| 'Cave' };screen.search
    check(screen.instance_variable_get(:@query)=='Cave' && screen.instance_variable_get(:@bitmap),'Android search opens the native keyboard path and keeps its canvas')
    check(screen.data_rows.all? { |row| BlueBattleHub.token(BlueBattleHub.display(row)).include?('cave') },'Cached species search still filters correctly')
    screen.render;shot('blue-hub-light-smoke');screen.unmount;screen=nil
    teams=BlueBattleLab.preset
    preview=BlueBattleHub::PickFour.new(teams,['Jogador','Rival']);preview.instance_variable_set(:@deadline,System.uptime+60);preview.mount
    [3,0,5,1].each do |i|
      b=preview.buttons.find { |item| item[:id]==('pick'+i.to_s).to_sym };x,y,w,h=b[:rect];scale=preview.instance_variable_get(:@ui_scale)
      BlueTouchValidation.drive([[((x+w/2)*scale).round,((y+h/2)*scale).round]]) { Input.update;preview.tick }
    end
    check(preview.selected==[3,0,5,1],'Android touch picks four Pokemon in the requested lead order')
    check(teams.all? { |t| t.length==6 } && preview.result.all? { |t| t.length==4 },'Pick-four never truncates the saved six-member rosters')
    shot('blue-pick-four-light-smoke');preview.unmount;preview=nil
  ensure
    screen&.unmount;preview&.unmount
    BlueMobile.define_singleton_method(:enabled?,mobile) if mobile
    BlueMenuSupport.define_singleton_method(:entry,entry) if entry
    Graphics.resize_screen(512,384)
  end
  def self.shop
    BlueCampaign::Shop.new.open do |shop|
      shop.instance_variable_set(:@tab,5);shop.instance_variable_set(:@query,'Protect');shop.refresh
      stock=shop.instance_variable_get(:@stock)
      check(!stock.empty? && stock.all? { |id| BlueCampaign.shop_name(GameData::Item.get(id)).downcase.include?('protect') },'Shop search matches the actual TM/TR move names')
      shop.instance_variable_set(:@query,'');shop.refresh
      check(shop.instance_variable_get(:@list).instance_variable_get(:@commands).length<=5,'Shop only draws five results regardless of catalog size')
      shop.page(1)
      stock=shop.instance_variable_get(:@stock);index=shop.instance_variable_get(:@page)*BlueCampaign::Shop::PAGE_SIZE
      check(shop.instance_variable_get(:@last_icon)==stock[index],'Shop paging displays the correct underlying item')
      shop.instance_variable_set(:@filter,2);shop.refresh
      check(shop.instance_variable_get(:@stock).none? { |id| $bag.has?(id) },'Shop not-owned filter respects the real bag')
      shop.instance_variable_set(:@filter,1);shop.refresh
      check(shop.instance_variable_get(:@stock).all? { |id| BlueCampaign.price(GameData::Item.get(id))<=$player.money },'Shop affordable filter respects the real wallet')
      shot('blue-shop-search-smoke')
    end
    check(BlueMobile.save_directory==File.expand_path(SaveData::SAVE_DIR),'Android save helper reports the engine actual multi-save directory')
  end
  def self.run
    @lines=[];old_size=[Graphics.width,Graphics.height];pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?)
    BlueLabPointer.define_singleton_method(:enabled?) { true }
    BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    Graphics.resize_screen(512,384);gates;storage;hub;shop
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(Array(error.backtrace));@lines << 'RESULT=FAIL';false
  ensure
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer
    BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    Graphics.resize_screen(*old_size) if old_size
    File.write('Data/blue-menu-validation.txt',@lines.join("\n")+"\n")
  end
end
