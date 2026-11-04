# Focused native proof: imports, every cached team, memo compositing and rewards.
module BlueReleaseValidation
  def self.check(value,label);raise label unless value;@lines << 'PASS | '+label;end
  module StarterPick
    def pbScene(*args)
      return super unless BlueReleaseValidation.instance_variable_get(:@starter_probe)
      BlueReleaseValidation.shot_starter
      @pokemon
    end
  end
  def self.shot_starter
    return if @starter_shot
    @starter_shot=true;BlueWorldValidation.shot('blue-android-starter-smoke')
  end
  def self.starters
    party=$player.party;dex=Marshal.dump($player.pokedex);mode=$PokemonGlobal.blue_story_mode;active=BlueBattleLab::ACTIVE
    clear=Bitmap.instance_method(:clear_rect) if Bitmap.method_defined?(:clear_rect)
    Bitmap.send(:undef_method,:clear_rect) if clear
    bitmap=Bitmap.new(3,3);bitmap.fill_rect(0,0,3,3,Color.new(255,0,0,255));bitmap.fill_rect(1,1,1,1,Color.new(0,0,0,0))
    check(bitmap.get_pixel(1,1).alpha==0 && bitmap.get_pixel(0,0).alpha==255,'RGSS transparent fill clears only the starter header region without clear_rect')
    bitmap.dispose;bitmap=nil
    ModularSelection_Scene.prepend(StarterPick) unless ModularSelection_Scene.ancestors.include?(StarterPick)
    @starter_probe=true;@starter_shot=false
    BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,false)
    $PokemonGlobal.blue_story_mode=:story
    lists=load_data('Data/Map001.rxdata').events.values.flat_map { |event| event.pages.map { |page| [event.id,page.list] } }
    [1,2].each do |count|
      found=nil
      lists.each do |event,list|
        root=list.index { |c| c.code==402 && c.parameters[1]=='Traditional Starters' };next unless root
        finish=(root+1...list.length).find { |i| list[i].indent<=list[root].indent } || list.length
        branch=(root+1...finish).find do |i|
          c=list[i];c.code==402 && c.indent==list[root].indent+1 &&
            c.parameters[1].to_s.match?(count==1 ? /Single/ : /Double/)
        end
        next unless branch
        script=(branch+1...finish).find { |i| list[i].code==355 }
        found=[event,list,script] if script
        break if found
      end
      raise 'Traditional starter event branch missing: '+count.to_s unless found
      event,list,index=found;$player.party=[]
      interpreter=Interpreter.new;interpreter.setup(list,event,1)
      interpreter.instance_variable_set(:@index,index);interpreter.instance_variable_set(:@parameters,list[index].parameters)
      interpreter.command_355
      check($player.party.length==count && $player.party.all? { |p| p.level==5 && p.hp>0 && PokemonSelections::Traditional_Starters.include?(p.species_data.id) },
        'Native Traditional '+count.to_s+' starter event renders, grants exactly the requested Pokemon, and returns without Bitmap.clear_rect')
    end
  ensure
    @starter_probe=false;bitmap&.dispose
    Bitmap.send(:define_method,:clear_rect,clear) if clear
    $player.party=party if party;$PokemonGlobal.blue_story_mode=mode
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    if defined?(active);BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,active);end
  end
  def self.album_location
    original_map=$game_map
    {86=>86,92=>90,93=>93,77=>77,79=>77}.each do |here,wanted|
      $game_map=Game_Map.new;$game_map.setup(here)
      areas=BlueTrainerAlbum.areas;selected=areas[BlueTrainerAlbum.initial_index(areas)]
      check(selected[:map]==wanted,'Trainer Album starts in the current area including parent cities and towns without trainers: '+here.to_s)
      check(!BlueTrainerAlbum.complete?(wanted),'An empty town never creates a trainer reward') if selected[:rows].empty?
    end
  ensure
    $game_map=original_map if original_map
  end
  def self.imports
    aliases={'Ogerpon-Wellspring'=>[:OGERPON,1],'Ogerpon-Hearthflame'=>[:OGERPON,2],'Ogerpon-Cornerstone'=>[:OGERPON,3],
      'Urshifu'=>[:URSHIFU,0],'Urshifu-Single-Strike'=>[:URSHIFU,0],'Urshifu-Rapid-Strike'=>[:URSHIFU,1],
      'Floette-Eternal'=>[:FLOETTE,5],'Eternal Floette'=>[:FLOETTE,5]}
    aliases.each { |label,expected| data=BlueBattleHub.resolve(:species,label);check([data.species,data.form]==expected,'Showdown alias '+label) }
    text="Ogerpon-Wellspring (F) @ Wellspring Mask\nAbility: Water Absorb\nEVs: 252 HP / 4 Def / 252 Spe\nJolly Nature\n- Ivy Cudgel\n- Horn Leech\n- Spiky Shield\n- Follow Me\n\nUrshifu-Rapid-Strike @ Mystic Water\nAbility: Unseen Fist\nAdamant Nature\n- Surging Strikes\n- Aqua Jet\n- Close Combat\n- Detect\n\nFloette-Eternal @ Eviolite\nAbility: Flower Veil\nModest Nature\n- Light of Ruin\n- Moonblast\n- Protect\n- Psychic\n"
    result=BlueBattleHub.preview(text);check(result.all? { |r| r['pokemon'] },'Ogerpon, Urshifu and Eternal Floette import with their real items, abilities and moves: '+result.filter_map { |r| r['error'] }.join('; '))
    team=result.map { |r| r['pokemon'] };roundtrip=BlueBattleHub.preview(BlueBattleHub.export(team))
    check(roundtrip.all? { |r| r['pokemon'] } && roundtrip.map { |r| [r['pokemon'].species,r['pokemon'].form] }==team.map { |p| [p.species,p.form] },'Special forms survive export and reimport')
    data=load_data('Data/blue-hub-presets.dat');check(data[0]==1 && data[1].length==130,'All 130 source Pokepastes are cached for offline import')
    groups=data[1].group_by { |r| r.first(2) };check(groups.length==13 && groups.values.all? { |rows| rows.length==10 },'Presets contain ten teams in each of thirteen game/regulation groups')
    audit=[]
    data[1].each do |game,reg,title,url,format,raw,available|
      result=BlueBattleHub.preview(raw,format.to_sym)
      errors=result.filter_map { |r| r['error'] }
      audit << [game,reg,title,result.count { |r| r['pokemon'] },errors.join(' | ')].join("\t")
      Graphics.update
    end
    File.write('Data/blue-presets-audit.tsv',audit.join("\n")+"\n")
    @lines << 'PRESETS_FULLY_COMPATIBLE='+audit.count { |row| row.split("\t")[3]=='6' }.to_s
    check(audit.all? { |row| row.split("\t")[3]=='6' },'Every one of the 130 presets imports all six Pokemon in the native engine')
  end
  def self.rewards
    old=$PokemonGlobal.blue_habitat_rewards;money=$player.money;dex=Marshal.dump($player.pokedex)
    campaign=BlueCampaign.method(:active?);battle_area=BlueBattleOptions.method(:battle_area?)
    BlueCampaign.define_singleton_method(:active?) { true };BlueBattleOptions.define_singleton_method(:battle_area?) { false }
    $PokemonGlobal.blue_habitat_rewards=nil;$player.money=1000
    area={map:86,name:'Route 1',methods:{Land:[[50,:PIKACHU,5,5],[50,:MAGIKARP,5,5],[50,:PIKACHU,5,5]]}}
    $player.pokedex.set_owned(:PIKACHU)
    check(!BlueHabitatRewards.claim(area,false),'Incomplete habitats never pay a completion reward')
    $player.pokedex.set_owned(:MAGIKARP)
    check(BlueHabitatRewards.claim(area,false) && $player.money==2000,'Two unique captured species award $500 each; duplicate encounter rows do not inflate the prize')
    check(!BlueHabitatRewards.claim(area,false),'Reopening a completed habitat never repeats its reward')
    $PokemonGlobal.blue_habitat_rewards=Marshal.load(Marshal.dump($PokemonGlobal.blue_habitat_rewards))
    check(!BlueHabitatRewards.claim(area,false),'Habitat paid state persists across serialization')
    $PokemonGlobal.blue_habitat_rewards=nil;$player.money=Settings::MAX_MONEY
    check(!BlueHabitatRewards.claim(area,false) && !$PokemonGlobal.blue_habitat_rewards[86],'A full wallet leaves the reward pending')
    $player.money-=1000;check(BlueHabitatRewards.claim(area,false) && $player.money==Settings::MAX_MONEY,'A pending reward can be collected after making room in the wallet')
  ensure
    $PokemonGlobal.blue_habitat_rewards=old;$player.money=money if money
    $player.instance_variable_set(:@pokedex,Marshal.load(dex)) if dex
    BlueCampaign.define_singleton_method(:active?,campaign) if campaign;BlueBattleOptions.define_singleton_method(:battle_area?,battle_area) if battle_area
  end
  def self.summary
    party=[:CHARIZARD,:AMMNOID,:SOLGALEO].map { |id| BlueBattleLab.build(id,50) }
    party_scene=PokemonParty_Scene.new;party_scene.pbStartScene(party,'Party')
    scene=PokemonSummary_Scene.new;scene.pbStartScene(party,0)
    scene.instance_variable_set(:@page,2);scene.drawPage(2)
    backdrop=scene.instance_variable_get(:@sprites)['blue_opaque_background']
    check(backdrop && backdrop.bitmap.get_pixel(450,200).alpha==255,'Native memo page has an opaque backdrop above the still-open party screen')
    BlueWorldValidation.shot('blue-memo-background-smoke')
    scene.pbEndScene;scene=nil;party_scene.pbEndScene;party_scene=nil
    original_map=$game_map;$game_map=Game_Map.new;$game_map.setup(86)
    list=BlueTrainerAlbum.areas;index=BlueHabitatMap.current_index(list,86)
    check(index && list[index][:map]==86,'Trainer Album selects the exact current route before showing the area list')
  ensure
    scene&.pbEndScene;party_scene&.pbEndScene
    $game_map=original_map if original_map
  end
  def self.maps
    point=BlueHabitatMap.position(86);scene=BlueHabitatMap::Scene.new(86,point,false);scene.start
    check(scene.highlighted_cells.include?(point[1,2]),'Selected route is included in the regional highlight')
    BlueWorldValidation.shot('blue-route-highlight-smoke');scene.dispose;scene=nil
    BlueRouteCaptures.export if File.file?(BlueRouteCaptures::REQUEST)
  ensure
    scene&.dispose
  end
  def self.mobile
    enabled=BlueMobile.method(:enabled?);choose=BlueBattleLab.method(:choose);active=BlueBattleLab::ACTIVE
    BlueMobile.define_singleton_method(:enabled?) { true }
    BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,false)
    klass=Class.new { def pbCallTitle;:story_title;end };klass.prepend(BlueMobile::Title)
    BlueBattleLab.define_singleton_method(:choose) { |*args| 0 }
    check(klass.new.pbCallTitle==:story_title,'Mobile Story choice preserves the normal campaign title path')
    BlueBattleLab.define_singleton_method(:choose) { |*args| 1 }
    check(klass.new.pbCallTitle.is_a?(BlueBattleLab::Scene) && !SaveData.exists?,'Mobile Hub choice opens a fresh sandbox with campaign saves blocked')
    blocked=false
    begin;BlueMultiplayer.python;rescue BlueBattleHub::ImportError;blocked=true;end
    check(blocked,'Mobile blocks the Windows-only multiplayer helper with an explanatory error')
  ensure
    BlueMobile.define_singleton_method(:enabled?,enabled) if enabled;BlueBattleLab.define_singleton_method(:choose,choose) if choose
    if defined?(active);BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,active);end
  end
  def self.run
    @lines=[];language=$PokemonSystem.blue_locale;$PokemonSystem.blue_locale='pt-BR'
    starters;album_location;imports;rewards;summary;maps;mobile;@lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    $PokemonSystem.blue_locale=language if language
    File.write('Data/blue-release-validation.txt',@lines.join("\n")+"\n")
  end
end
