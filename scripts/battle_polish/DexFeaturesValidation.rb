# Integration probes for actual native screens; no campaign save is opened.
module BlueDexFeaturesValidation
  module Keys
    def trigger?(key)
      return true if key==Input::BACK && BlueDexFeaturesValidation.instance_variable_get(:@close_dex)
      super
    end
  end
  module DexTrace
    def pbStartScene(list,*args)
      BlueDexFeaturesValidation.instance_variable_set(:@opened_species,list.first[:species])
      super
    end
  end
  module Numbers
    def pbMessageChooseNumber(*args)
      numbers=BlueDexFeaturesValidation.instance_variable_get(:@numbers)
      return numbers.shift if numbers
      super
    end
  end
  class MapScene < BlueHabitatMap::Scene
    def start;super;BlueDexFeaturesValidation.shot('blue-habitat-map-smoke');end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.dex_flags
    flags={};GameData::Species.each_species { |data| flags[data.id]=[$player.seen?(data.id),$player.owned?(data.id)] };flags
  end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.click(point);BlueTouchValidation.drive([point]) { Input.update;yield };end
  def self.pause
    map=$game_map;party=$player.party;dex_flag=$player.has_pokedex;dex=Marshal.dump($player.pokedex)
    $game_map=Game_Map.new;$game_map.setup(79);$player.party=[BlueBattleLab.build(:PIKACHU,50)];$player.has_pokedex=true
    $player.pokedex.unlock(0);$player.pokedex.set_seen(:PIKACHU)
    menu=VoltseonsPauseMenu_Scene.new;menu.pbStartScene;shot('blue-pause-mouse-smoke')
    component=menu.instance_variable_get(:@pause_menu);entries=component.instance_variable_get(:@entries)
    targets={};MenuHandlers.each_available(:pause_menu) { |id,hash,name| targets[id]=name }
    [:party,:pokedex,:save].map { |id| targets.fetch(id) }.each do |name|
      index=entries.index { |e| e[:name]==name };check(!!index,'Native pause menu has '+name)
      called=false
      component.instance_variable_set(:@current_selection,index)
      # Rebuild native indices without replacing the callback under test.
      component.calc_display_index
      component.send(:recalc_menu_entries)
      entries=component.instance_variable_get(:@entries);entries[index][:proc]=proc { |m| called=true;false }
      component.calc_display_index;component.recalc_icon_positions(true);component.refresh_menu
      middle=component.instance_variable_get(:@disp_indices).length/2;sprite=component.sprites['icon_'+middle.to_s]
      click([sprite.x,sprite.y]) do
        component.update
      end
      check(called,'A real native carousel icon click executes exactly the '+name+' callback')
      entries=component.instance_variable_get(:@entries)
    end
    before=component.instance_variable_get(:@current_selection);arrow=component.sprites['rightarrow']
    click([arrow.x+8,arrow.y+8]) { component.update }
    check(component.instance_variable_get(:@current_selection)!=(before),'Pause carousel arrows also navigate by mouse')
    entries=component.instance_variable_get(:@entries);index=component.instance_variable_get(:@current_selection)
    entries[index][:proc]=proc { |m| m.pbEndScene;true }
    sprite=component.sprites['icon_'+(component.instance_variable_get(:@disp_indices).length/2).to_s]
    BlueTouchValidation.drive([[sprite.x,sprite.y]]) { menu.update }
    check(menu.instance_variable_get(:@has_terminated),'Clicking a callback that closes Save does not update disposed pause components')
    menu=nil
  ensure
    menu.pbEndScene if menu && !menu.instance_variable_get(:@has_terminated)
    $game_map=map if map;$player.party=party if party;$player.has_pokedex=dex_flag
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
  end
  def self.summary
    dex_flag=$player.has_pokedex;dex=Marshal.dump($player.pokedex);$player.has_pokedex=true
    $player.pokedex.set_seen(:SNORLAX);$player.pokedex.set_owned(:SNORLAX)
    mon=BlueBattleLab.build(:SNORLAX,50);party=[mon]
    scene=PokemonSummary_Scene.new;scene.pbStartScene(party,0)
    scene.instance_variable_set(:@blue_summary_active,true);scene.pbUpdate;shot('blue-summary-dex-button-smoke')
    before=Marshal.dump(party)
    button=scene.instance_variable_get(:@sprites)['blueDexButton'];@opened_species=nil;@close_dex=true
    click([button.x+12,button.y+12]) { scene.pbUpdate }
    @close_dex=false
    check(@opened_species==:SNORLAX,'Summary Pokedex button opens the selected Pokemon through the native single-entry screen')
    check(Marshal.dump(party)==before && scene.instance_variable_get(:@partyindex)==0,'Returning from the Dex preserves party, selected Pokemon, moves and stats')
    scene.pbEndScene;scene=nil
  ensure
    @close_dex=false;scene&.pbEndScene
    $player.has_pokedex=dex_flag;$player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
  end
  def self.filters
    dex=Marshal.dump($player.pokedex);$player.pokedex.clear
    $player.pokedex.set_seen(:PIKACHU);$player.pokedex.set_owned(:SNORLAX);$player.pokedex.set_seen(:SNORLAX)
    list=[:PIKACHU,:SNORLAX,:MEWTWO].each_with_index.map do |id,i|
      d=GameData::Species.get(id);{species:id,name:d.name,types:d.types,number:i+1,height:d.height,weight:d.weight,shift:false}
    end
    f=BlueDexFilters.defaults
    check(BlueDexFilters.apply(list,f.merge(status: :seen)).map { |r| r[:species] }==[:PIKACHU,:SNORLAX],'Seen-only filter includes discovered Pokemon and excludes unknown ones')
    check(BlueDexFilters.apply(list,f.merge(status: :caught)).map { |r| r[:species] }==[:SNORLAX],'Caught-only filter uses ownership flags')
    check(BlueDexFilters.apply(list,f.merge(name:'pIkA')).map { |r| r[:species] }==[:PIKACHU],'Name search is case-insensitive and partial')
    check(BlueDexFilters.apply(list,f.merge(name:'Mewtwo')).empty?,'Name search cannot expose an unseen species')
    check(BlueDexFilters.apply(list,f.merge(type: :ELECTRIC)).map { |r| r[:species] }==[:PIKACHU],'Type filtering uses current species data')
    before=dex_flags
    scene=PokemonPokedex_Scene.new;scene.pbStartScene
    check(scene.blue_apply_filters(f.merge(status: :caught)),'Actual native Dex list accepts a captured-only result set')
    shot('blue-dex-filters-smoke')
    check(scene.instance_variable_get(:@dexlist).all? { |r| $player.owned?(r[:species]) },'Every displayed native result is actually captured')
    scene.blue_apply_filters(f)
    check(!scene.instance_variable_get(:@searchResults),'Clear filters restores native Dex mode and numbering')
    choose=BlueBattleLab.method(:choose);answers=[2,2,4]
    BlueBattleLab.define_singleton_method(:choose) { |*args| answers.shift }
    scene.instance_variable_get(:@sprites)['pokedex'].active=true
    button=scene.instance_variable_get(:@sprites)['blueSearchButton']
    click([button.x+8,button.y+8]) { scene.pbUpdate }
    BlueBattleLab.define_singleton_method(:choose,choose);choose=nil
    check(scene.instance_variable_get(:@blue_filters)[:status]==:caught && scene.instance_variable_get(:@viewport).visible,'The native filter button opens the menu by mouse and returns to captured-only results')
    check(dex_flags==before,'Filtering does not grant seen/owned status')
    scene.pbEndScene;scene=nil
  ensure
    BlueBattleLab.define_singleton_method(:choose,choose) if choose
    scene&.pbEndScene;$player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
  end
  def self.habitats
    map=$game_map;visited=$PokemonGlobal.visitedMaps.dup
    $game_map=Game_Map.new;$game_map.setup(77);$PokemonGlobal.visitedMaps[77]=true
    list=BlueHabitat.areas;index=BlueHabitatMap.current_index(list)
    check(index && list[index][:map]==77,'Habitat Dex resolves the current route/city before the full area list')
    choose=BlueBattleLab.method(:choose);calls=[]
    BlueBattleLab.define_singleton_method(:choose) { |title,*args| calls << title;-1 }
    BlueHabitat.open;BlueBattleLab.define_singleton_method(:choose,choose)
    check(calls.first==BlueHabitat.map_name(77),'Opening Habitat Dex immediately enters the current habitat')
    point=BlueHabitatMap.position(77);check(point && point.length==3,'Current habitat has native region/grid metadata')
    scene=MapScene.new(77,point);BlueTouchValidation.drive([[450,364]]) { scene.run }
    check(scene.instance_variable_get(:@map_width)>0,'Habitat map renders the installed regional artwork and location markers')
    open_map=BlueHabitatMap.method(:open);@map_opened=nil
    BlueHabitatMap.define_singleton_method(:open) { |id| BlueDexFeaturesValidation.instance_variable_set(:@map_opened,id) }
    habitat=BlueHabitat::Scene.new(BlueHabitat.map_name(77),'Old Rod',[],77)
    BlueTouchValidation.drive([[350,16],nil,[450,364]]) { habitat.run }
    check(@map_opened==77,'The M map button opens the selected habitat by mouse')
    BlueHabitatMap.define_singleton_method(:open,open_map);open_map=nil
    check(BlueHabitatMap.position(79),'Indoor maps can resolve a regional position without inventing coordinates')
  ensure
    BlueBattleLab.define_singleton_method(:choose,choose) if choose
    BlueHabitatMap.define_singleton_method(:open,open_map) if open_map
    $PokemonGlobal.visitedMaps.replace(visited) if visited;$game_map=map if map
  end
  def self.comparisons
    dex=Marshal.dump($player.pokedex);height=$PokemonGlobal.blue_player_height_cm;weight=$PokemonGlobal.blue_player_weight_kg
    $PokemonGlobal.blue_player_height_cm=170;$PokemonGlobal.blue_player_weight_kg=60
    $player.pokedex.set_seen(:SNORLAX);$player.pokedex.set_owned(:SNORLAX)
    scene=PokemonPokedexInfo_Scene.new;scene.pbStartScene([{species: :SNORLAX,name:'Snorlax',number:143}],0,0)
    pages=scene.instance_variable_get(:@page_list)
    check((BlueDexCompare::PAGES-pages).empty?,'Height and weight are two actual native Pokedex tabs')
    scene.instance_variable_set(:@page,pages.index(:blue_height)+1);scene.drawPage(0);shot('blue-dex-height-smoke')
    pixels=scene.instance_variable_get(:@blue_height_pixels);data=GameData::Species.get(:SNORLAX)
    check((pixels[0]/pixels[1]-data.height*10.0/170).abs<0.001,'Pokemon and player figures use the same physical height scale')
    scene.instance_variable_set(:@page,pages.index(:blue_weight)+1);scene.drawPage(0);scene.blue_draw_comparison(:blue_weight,1.0);shot('blue-dex-weight-smoke')
    check(scene.instance_variable_get(:@blue_beam_offset)>0 && BlueDexCompare.beam_offset(6)<0,'The balance tilts in opposite directions for heavier and lighter Pokemon')
    tab=scene.blue_tab_rects.find { |i,x,y,w,h| pages[i]==:blue_height };@close_dex=true
    BlueTouchValidation.drive([[tab[1]+8,tab[2]+8]]) { scene.pbScene };@close_dex=false
    check(scene.instance_variable_get(:@page_id)==:blue_height,'Clicking the Height tab works in the actual Pokedex scene loop')
    old_page=scene.instance_variable_get(:@page);scene.instance_variable_set(:@brief,true)
    click([tab[1]+8,tab[2]+8]) { scene.pbUpdate }
    check(scene.instance_variable_get(:@page)==old_page,'Brief capture entries keep their native single-page behavior')
    scene.instance_variable_set(:@brief,false)
    choose=BlueBattleLab.method(:choose);answers=[0,1,-1];@numbers=[185,80]
    BlueBattleLab.define_singleton_method(:choose) { |*args| answers.shift }
    BlueDexCompare.settings
    check(BlueDexCompare.height_cm==185 && BlueDexCompare.weight_kg==80,'Reference height and weight can be changed through the real settings menu')
    restored=Marshal.load(Marshal.dump($PokemonGlobal))
    check(restored.blue_player_height_cm==185 && restored.blue_player_weight_kg==80,'Player comparison references serialize with the native save metadata')
    scene.pbEndScene;scene=nil
  ensure
    @numbers=nil;BlueBattleLab.define_singleton_method(:choose,choose) if choose
    scene&.pbEndScene;$player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    $PokemonGlobal.blue_player_height_cm=height;$PokemonGlobal.blue_player_weight_kg=weight
  end
  def self.weight_entries
    check(BlueWeightEntry.profile(BlueBattleLab.build(:PIKACHU,50)).nil?,'Light Pokemon do not trigger a heavy landing')
    check(BlueWeightEntry.profile(BlueBattleLab.build(:CHARIZARD,50)).nil?,'Flying Pokemon do not raise ground dust')
    check(BlueWeightEntry.profile(BlueBattleLab.build(:SNORLAX,50))[:tier]==3 && BlueWeightEntry.profile(BlueBattleLab.build(:TYRANITAR,50))[:tier]==2,'Weight selects different impact/dust tiers using the current species weight')
    battle=BlueBattleOptions::MechanicValidation.fixture(:CHARIZARDITEY,'double')
    mon=BlueBattleLab.build(:SNORLAX,50);battle.pbParty(0)[0]=mon;battle.battlers[0].pbInitialize(mon,0)
    scene=BlueBattleUIValidation::Scene.new;battle.instance_variable_set(:@scene,scene)
    battle.backdrop='indoor1';battle.environment=:None;battle.time=0
    scene.pbStartBattle(battle);BlueBattleOptions::MechanicValidation.show_battlers(scene,battle)
    sprites=scene.instance_variable_get(:@sprites);viewport=scene.instance_variable_get(:@viewport)
    before=Marshal.dump(mon);sprite=sprites['pokemon_0'];final=[sprite.x,sprite.y]
    animation=Battle::Scene::Animation::PokeballPlayerSendOut.new(sprites,viewport,0,battle.battlers[0],false,0)
    event=animation.instance_variable_get(:@blue_weight_events).first
    check(event[:dust]==12 && event[:at]>=animation.instance_variable_get(:@blue_release_time)+19,'Heavy impact starts after the native Pokeball glare ends and schedules twelve dust particles')
    check(event[:ground][1]<=Graphics.height-108,'Heavy landing dust stays on the battlefield above the command panel')
    shown=false;started=BlueBattleUI.clock
    until animation.animDone?
      Graphics.update;animation.update;scene.pbUpdate
      particles=animation.instance_variable_get(:@tempSprites).select { |s| s.is_a?(BitmapSprite) && s.bitmap.width==20 }
      if !shown && particles.any? { |s| s.visible && s.opacity>0 }
        shot('blue-heavy-entry-smoke');shown=true
      end
      raise 'Heavy entry animation timeout' if BlueBattleUI.clock-started>12
    end
    check(shown && [sprite.x,sprite.y]==final,'Dust is rendered and the Pokemon returns to its exact battle position')
    check(Marshal.dump(mon)==before,'Weight effects do not change Pokemon stats, moves, HP or form')
    temp=animation.instance_variable_get(:@tempSprites).dup;animation.dispose;animation=nil
    check(temp.all?(&:disposed?),'Animation disposal releases every temporary dust sprite')
    scene.pbEndBattle(0);scene=nil
  ensure
    animation&.dispose;scene&.pbEndBattle(0)
  end
  def self.run
    @lines=[];pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?);lang=$PokemonSystem.blue_locale
    BlueLabPointer.define_singleton_method(:enabled?) { true };BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    Input.singleton_class.prepend(Keys) unless Input.singleton_class.ancestors.include?(Keys)
    PokemonPokedexInfo_Scene.prepend(DexTrace) unless PokemonPokedexInfo_Scene.ancestors.include?(DexTrace)
    Object.prepend(Numbers) unless Object.ancestors.include?(Numbers)
    $PokemonSystem.blue_locale='pt-BR'
    Graphics.transition(0)
    started=BlueBattleUI.clock
    while Graphics.average_frame_rate<30
      Graphics.update;Input.update
      raise 'Native frame-rate meter did not initialize' if BlueBattleUI.clock-started>4
    end
    pause;summary;filters;habitats;comparisons;weight_entries;@lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @close_dex=false;@numbers=nil;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer;BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.open('Data/blue-dex-features-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
