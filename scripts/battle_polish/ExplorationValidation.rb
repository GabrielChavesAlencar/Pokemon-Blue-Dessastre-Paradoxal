# Native integration probes, restricted to the laboratory's disposable memory.
module BlueExplorationValidation
  module FishingHarness
    def pbFishingBegin
      return super unless BlueExplorationValidation.instance_variable_get(:@fish_test)
      $PokemonGlobal.fishing=true
    end
    def pbFishingEnd
      return super unless BlueExplorationValidation.instance_variable_get(:@fish_test)
      $PokemonGlobal.fishing=false;yield if block_given?
    end
    def pbWaitMessage(*args)
      return false if BlueExplorationValidation.instance_variable_get(:@fish_test)
      super
    end
    def pbWaitForInput(*args)
      return BlueExplorationValidation.instance_variable_get(:@hook) if BlueExplorationValidation.instance_variable_get(:@fish_test)
      super
    end
    def pbMessageDisplay(*args)
      return if BlueExplorationValidation.instance_variable_get(:@fish_test)
      super
    end
    def pbEncounter(type,*args)
      if BlueExplorationValidation.instance_variable_get(:@fish_test)
        BlueExplorationValidation.instance_variable_set(:@encounter,[type,$PokemonEncounters.choose_wild_pokemon(type)])
        return true
      end
      super
    end
  end
  class HabitatScene < BlueHabitat::Scene
    def start;super;BlueExplorationValidation.shot('blue-habitat-dex-smoke');end
    def turn(delta);super;BlueExplorationValidation.shot('blue-habitat-page-smoke');end
  end
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  def self.shot(name);Graphics.update;b=Graphics.snap_to_bitmap;b.to_file('Data/'+name+'.png');b.dispose;end
  def self.confirm_click
    window=ObjectSpace.each_object(Window_CommandPokemon).find { |w| !w.disposed? && w.visible && w.active && w.itemCount==2 }
    return unless window
    x,y=BlueLabPointer.origin(window);r=window.itemRect(0)
    [x+window.startX+r.x+8,y+window.startY+r.y+8]
  end
  def self.mouse
    viewport=Viewport.new(0,0,Graphics.width,Graphics.height)
    scene=ButtonEventScene.new(viewport);shot('blue-controls-mouse-smoke')
    BlueTouchValidation.drive([[200,200]]) { scene.main }
    check(scene.disposed?,'A mouse click closes the actual opening controls help screen')
    viewport.dispose;viewport=nil;scene=nil
    scene=CharacterSelectionScene.new
    scene.pbStartScene(['trainer_PLAYER_TRAINER_FRLG_Red','trainer_PLAYER_TRAINER_FRLG_Leaf'],['PLAYER_TRAINER_FRLG_Red','PLAYER_TRAINER_FRLG_Leaf'])
    shot('blue-character-mouse-smoke')
    sprite=scene.instance_variable_get(:@sprites)['icon1'];x,y=BlueLabPointer.origin(sprite)
    result=BlueTouchValidation.drive([[x,y-sprite.oy+8],proc { confirm_click }]) { scene.pbMidScene }
    check(result==1,'Clicking a different character and native Yes chooses that character')
    scene.pbEndScene;scene=nil
    check(BlueStartMouse.scope.nil?,'Controls and character clicks do not leak into normal gameplay')
  ensure
    scene.pbEndScene if scene.is_a?(CharacterSelectionScene)
    scene.dispose if scene.is_a?(ButtonEventScene) && !scene.disposed?
    viewport&.dispose
  end
  def self.fishing
    old_encounters=$PokemonEncounters;old_scene=$scene;old_flag=$PokemonGlobal.fishing
    old_count=$stats.fishing_count;old_battles=$stats.fishing_battles
    passable=$game_map.method(:passable?);terrain=$game_player.method(:pbFacingTerrainTag)
    $game_map.define_singleton_method(:passable?) { |*args| true }
    $game_player.define_singleton_method(:pbFacingTerrainTag) { Struct.new(:can_fish).new(true) }
    map=nil;infos=load_data('Data/MapInfos.rxdata')
    GameData::Encounter.each { |data| map ||= data.map if infos[data.map] && data.types[:SuperRod]&.any? && !data.types[:OldRod]&.any? && BlueFishing.tables(data.types)[:OldRod]&.any? }
    check(!!map,'A real current map has Super Rod encounters but no Old Rod table in the base')
    original=Marshal.dump(GameData::Encounter.get(map,$PokemonGlobal.encounter_version).types)
    $PokemonEncounters=PokemonEncounters.new;$PokemonEncounters.setup(map)
    check($PokemonEncounters.has_encounter_type?(:OldRod) && Marshal.dump(GameData::Encounter.get(map,$PokemonGlobal.encounter_version).types)==original,'Rod-specific local fishing tables are generated in memory without changing original encounter data')
    animation=Object.new;animation.define_singleton_method(:addUserAnimation) { |*args| }
    $scene=Struct.new(:spriteset).new(animation)
    Object.prepend(FishingHarness) unless Object.ancestors.include?(FishingHarness)
    @fish_test=true;@hook=true;@encounter=nil
    ItemHandlers.triggerUseInField(:OLDROD)
    check(@encounter && @encounter[0]==:OldRod && @encounter[1],'Actual Old Rod item handler reaches its real wild table after a successful manual hook')
    check($stats.fishing_battles==old_battles+1 && !$PokemonGlobal.fishing,'A successful cast records one fishing battle and resets the fishing state')
    @hook=false;@encounter=nil;ItemHandlers.triggerUseInField(:OLDROD)
    check(@encounter.nil? && !$PokemonGlobal.fishing,'Missing the manual hook starts no battle and resets the fishing state')
    @hook=true;$PokemonEncounters=PokemonEncounters.new;@encounter=nil
    ItemHandlers.triggerUseInField(:OLDROD)
    check(@encounter.nil?,'Water with no Old Rod table does not invent an encounter')
    @fish_test=false
    BlueStartMouse.with_scope(:fishing) do
      BlueTouchValidation.drive([[200,200]]) { Input.update;check(Input.trigger?(Input::USE),'A click can perform the fishing reaction inside its input scope') }
    end
  ensure
    @fish_test=false
    $game_map.define_singleton_method(:passable?,passable) if passable
    $game_player.define_singleton_method(:pbFacingTerrainTag,terrain) if terrain
    $PokemonEncounters=old_encounters;$scene=old_scene;$PokemonGlobal.fishing=old_flag
    $stats.fishing_count=old_count;$stats.fishing_battles=old_battles
  end
  def self.habitat
    dex=Marshal.dump($player.pokedex);visited=$PokemonGlobal.visitedMaps.dup;version=$PokemonGlobal.encounter_version
    enabled=BlueStory.method(:enabled?);BlueStory.define_singleton_method(:enabled?) { false }
    $player.pokedex.clear;$player.pokedex.set_seen(:PIKACHU);$player.pokedex.set_owned(:MAGIKARP)
    slots=[:MAGIKARP,:PIKACHU,:MEWTWO].map { |id| [1,id,5,5] }
    entries=BlueHabitat.entries(slots)
    check(entries.map { |e| e[:status] }==[:caught,:seen,:unknown],'Habitat distinguishes captured, seen and unknown Pokemon using the actual Dex flags')
    check(entries.last=={species:nil,name:'?',status: :unknown},'Unknown habitat slots contain no species ID, name, sprite or other hidden detail')
    map=nil;infos=load_data('Data/MapInfos.rxdata')
    GameData::Encounter.each { |data| map ||= data.map if infos[data.map] && data.types[:SuperRod]&.any? }
    $PokemonGlobal.visitedMaps.clear;$PokemonGlobal.visitedMaps[map]=true
    areas=BlueHabitat.areas
    check(areas.any? { |a| a[:map]==map } && areas.all? { |a| a[:map]==map || a[:map]==$game_map.map_id },'Habitats list visited/current maps and hide all unvisited maps')
    area=areas.find { |a| a[:map]==map }
    check(area[:name]!='Area '+map.to_s && !area[:name].empty?,'A real visited habitat shows its actual map name')
    expected=BlueExploration.encounter_types(GameData::Encounter.get(map,version).types).reject { |type,list| list.empty? }
    check(area[:methods]==expected,'Habitat methods match the active encounter version, native base fallback and usable rod tables')
    check(BlueHabitat.species(slots+slots).length==3,'Repeated encounter slots count each species only once')
    before=Marshal.dump([$player.pokedex,$PokemonGlobal.visitedMaps])
    scene=HabitatScene.new('Habitat / '+area[:name],'Old Rod',entries*5)
    BlueTouchValidation.drive([[250,354],[450,354]]) { scene.run }
    check(scene.instance_variable_get(:@page)==1,'Habitat Next and Back buttons work by mouse through the real scene loop')
    choose=BlueBattleLab.method(:choose);open=BlueHabitat.method(:open);@opened=0;selections=[1,-1]
    BlueBattleLab.define_singleton_method(:choose) { |*args| selections.shift }
    BlueHabitat.define_singleton_method(:open) { BlueExplorationValidation.instance_variable_set(:@opened,1) }
    PokemonPokedexScreen.new(Object.new).pbStartScreen
    check(@opened==1,'The actual Pokedex screen exposes the Habitat Dex entry and returns safely')
    check(Marshal.dump([$player.pokedex,$PokemonGlobal.visitedMaps])==before,'Browsing habitats never registers seen/caught species or marks extra maps visited')
  ensure
    BlueBattleLab.define_singleton_method(:choose,choose) if choose
    BlueHabitat.define_singleton_method(:open,open) if open
    BlueStory.define_singleton_method(:enabled?,enabled) if enabled
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    $PokemonGlobal.visitedMaps.replace(visited) if visited
  end
  def self.tiers
    active=BlueCampaign.method(:active?);enabled=BlueStory.method(:enabled?)
    party=$player.party;badges=$player.badges.dup
    BlueCampaign.define_singleton_method(:active?) { true };BlueStory.define_singleton_method(:enabled?) { true }
    $player.party=[BlueBattleLab.build(:PIKACHU,100)]
    source=BlueBattleLab.build(:GARCHOMP,99);before=Marshal.dump(source)
    trainer=NPCTrainer.new('Test',:YOUNGSTER);trainer.party=[source]
    gym=NPCTrainer.new('Marigold (2v2 Full Power)',:HOENNIAN_ORAS_AROMALADY);gym.party=[source]
    rates=[]
    [[0,0,350],[1,0,350],[2,1,450],[4,1,450],[5,2,540],[10,2,540],[11,3,nil],[18,3,nil]].each do |count,stage,cap|
      $player.badges.replace(Array.new(18) { |i| i<count })
      check(BlueStory.stage==stage && BlueStory.cap==cap,"#{count} crystals select tier #{stage} and BST #{cap || 'unlimited'}")
      b=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,trainer.party,[$player],[trainer])
      g=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,gym.party,[$player],[gym])
      w=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,[source],[$player],nil)
      check(b.pbParty(1).first.level==70 && g.pbParty(1).first.level==(stage==3 ? 90 : 70) && w.pbParty(1).first.level==45,'Native trainer/gym/wild constructors apply the correct ratios at '+count.to_s+' crystals')
      check([b,g,w].all? { |battle| p=battle.pbParty(1).first;cap ? BlueStory.bst(p.species_data)<=cap : p.species==:GARCHOMP },'Trainers and wild Pokemon share the BST ceiling, removed only at Master '+count.to_s)
      rates << [stage,trainer.base_money]
    end
    check(rates.all? { |stage,value| value==rates.first[1]*(stage+1) },'Native monetary reward rates are 1x, 2x, 3x and 4x across the four tiers')
    check(Marshal.dump(source)==before,'Campaign scaling leaves the original Pokemon and cached trainer teams intact')
  ensure
    BlueCampaign.define_singleton_method(:active?,active) if active;BlueStory.define_singleton_method(:enabled?,enabled) if enabled
    $player.party=party if party;$player.badges.replace(badges) if badges
  end
  def self.run
    @lines=[];pointer=BlueLabPointer.method(:position);enabled=BlueLabPointer.method(:enabled?);lang=$PokemonSystem.blue_locale
    BlueLabPointer.define_singleton_method(:enabled?) { true }
    BlueLabPointer.define_singleton_method(:position) { BlueTouchValidation.instance_variable_get(:@point) }
    Input.singleton_class.prepend(BlueTouchValidation::InputDriver) unless Input.singleton_class.ancestors.include?(BlueTouchValidation::InputDriver)
    $PokemonSystem.blue_locale='pt-BR'
    mouse;fishing;habitat;tiers;@lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    @fish_test=false;$PokemonSystem.blue_locale=lang if lang
    BlueLabPointer.define_singleton_method(:position,pointer) if pointer
    BlueLabPointer.define_singleton_method(:enabled?,enabled) if enabled
    File.open('Data/blue-exploration-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
