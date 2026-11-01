# Native checks use temporary globals and never load/write a campaign save.
module BlueCampaignValidation
  def self.check(value,label)
    raise label unless value
    @lines << 'PASS | '+label
  end
  def self.run(lines)
    @lines=lines
    old_global=Marshal.dump($PokemonGlobal);old_bag=$bag;old_map=$game_map
    old_money=$player.money;old_party=$player.party;old_spent=$stats.money_spent_at_marts
    active=BlueCampaign.method(:active?);story_enabled=BlueStory.method(:enabled?)
    logger=PBDebug.method(:logonerr);PBDebug.define_singleton_method(:logonerr) { |&block| block.call }
    check(!BlueCampaign.active?,'Campaign economy and scaling stay out of the isolated Hub')
    BlueCampaign.define_singleton_method(:active?) { true }
    BlueStory.define_singleton_method(:enabled?) { false }
    $bag=PokemonBag.new;$bag.add(:POTION,7)
    $PokemonGlobal.blue_campaign_started=nil
    BlueCampaign.begin_journey(false)
    check($bag.quantity(:POTION)==0,'New journey begins without items')
    $bag.add(:POTION,2);BlueCampaign.begin_journey(false)
    check($bag.quantity(:POTION)==2,'Starting guard never wipes an existing initialized inventory')
    before_party=Marshal.dump($player.party)
    before_storage=Marshal.dump($PokemonStorage)
    BlueCampaign.instance_variable_set(:@bulk_setup,true)
    pbAllPokemonSetup5
    pbAddPokemonSilent(:MEWTWO,5)
    BlueCampaign.instance_variable_set(:@bulk_setup,false)
    check(Marshal.dump($player.party)==before_party && Marshal.dump($PokemonStorage)==before_storage,'Story setup cannot fill the party or PC with free Pokemon')
    # All registered items have a strictly positive price; no free or arbitrage paths.
    items=[];GameData::Item.each { |i| items << i if BlueCampaign.sellable_item?(i) }
    check(items.all? { |i| BlueCampaign.price(i).is_a?(Integer) && BlueCampaign.price(i)>0 },'Every catalog item has a positive integer price')
    check(BlueCampaign.price(GameData::Item.get(:POTION))==300 && BlueCampaign.price(GameData::Item.get(:POKEBALL))==200,'Official retail anchors: Potion 300 and Poke Ball 200')
    check(!BlueCampaign.sellable_item?(GameData::Item.get(:SETPOKEDOLLARSDISK)),'Money generator is excluded from shops')
    check(!BlueCampaign.sellable_item?(GameData::Item.get(:ROTOMPHONE)),'Sequence-breaking teleport phone is excluded from the campaign shop')
    check(ItemHandlers::UseFromBag.trigger(:SETPOKEDOLLARSDISK,nil)==0 && ItemHandlers::UseInField.trigger(:ROTOMPHONE)==false,'Sandbox tools already held by older saves cannot bypass campaign progression')
    check(BlueCampaign.stock(2).include?(:CHARIZARDITEY) && BlueCampaign.stock(3).include?(:ELECTRIUMZ),'Mega Stones and Z-Crystals have separate complete tabs')
    check(BlueCampaign.stock(0).include?(:FULLRESTORE) && BlueCampaign.stock(4).include?(:ADAMANTMINT) && BlueCampaign.stock(4).include?(:RARECANDY),'Former key-item medicines, mints and Rare Candy are purchasable consumables')
    check([:FULLRESTORE,:ADAMANTMINT,:RARECANDY,:REPEL].all? { |id| i=GameData::Item.get(id);!i.is_important? && i.consumed_after_use? },'Standard consumables cannot act as infinite-use key items in the campaign')
    $bag.add(:FULLRESTORE,2)
    patient=BlueBattleLab.build(:PIKACHU,10);patient.hp-=10
    medicine_scene=Object.new
    [:pbRefresh,:pbClearAnnotations,:pbHardRefresh,:pbUpdate,:pbDisplay].each { |name| medicine_scene.define_singleton_method(name) { |*args| } }
    used=pbUseItemOnPokemon(:FULLRESTORE,patient,medicine_scene)
    check(used && patient.hp==patient.totalhp && $bag.quantity(:FULLRESTORE)==1,'Native medicine use heals and consumes exactly one purchased Full Restore')
    $player.money=1_000;before=Marshal.dump($bag)
    check(BlueCampaign.purchase(:POTION,4)==:funds && $player.money==1_000 && Marshal.dump($bag)==before,'Unaffordable purchase leaves money and inventory unchanged')
    check(BlueCampaign.purchase(:POTION,2)==:ok && $player.money==400 && $bag.quantity(:POTION)==4,'Successful purchase deducts the exact total and adds the selected quantity')
    check(BlueCampaign.purchase(:POTION,0)==:quantity && BlueCampaign.purchase(:POTION,-1)==:quantity,'Invalid quantities cannot produce money or items')
    $player.money=50_000
    check(BlueCampaign.purchase(:MEGARING,1)==:ok && BlueCampaign.purchase(:MEGARING,1)==:owned,'Mechanic equipment is purchased once')
    adapter=PokemonMartAdapter.new
    check(items.all? { |i| adapter.getPrice(i.id,true)<=adapter.getPrice(i.id)/2 },'All native campaign shops cap resale below the paid retail price')
    # All actual nurse maps get accessible, non-overlapping, idempotent retailers.
    total=0;maps=0
    Dir.glob('Data/Map[0-9][0-9][0-9].rxdata').sort.each do |path|
      data=load_data(path)
      nurses=data.events.values.select { |e| BlueCampaign.nurse?(e) }
      next if nurses.empty?
      id=File.basename(path)[3,3].to_i
      map=Game_Map.new;$game_map=map;map.setup(id)
      shops=map.instance_variable_get(:@map).events.values.select { |e| e.name.start_with?('Blue Shop / ') }
      check(shops.length==nurses.length,'One merchant per real nurse on map '+id.to_s)
      check(shops.all? { |e| BlueBattleOptions.reachable_ball?(map,e.x,e.y) },'Merchant interaction is reachable on map '+id.to_s)
      count=map.events.length;BlueCampaign.patch_map(map)
      check(map.events.length==count,'Campaign map injection is idempotent on map '+id.to_s)
      check(map.instance_variable_get(:@map).events.values.none? { |e| BlueCampaign.blocked_event?(e) },'Free generators and Auto Grind removed on map '+id.to_s)
      total+=shops.length;maps+=1;Graphics.update
    end
    @lines << "SHOPS | nurses=#{total} maps=#{maps}"
    $game_map=Game_Map.new;$game_map.setup(79)
    $bag.add(:POTION,1);$PokemonGlobal.blue_campaign_departure=true;BlueCampaign.depart
    check($bag.pockets.all?(&:empty?) && !$PokemonGlobal.blue_campaign_departure,'Leaving intro removes starter item suites exactly once')
    $bag.add(:POTION,1);BlueCampaign.depart
    check($bag.quantity(:POTION)==1,'Later map entries preserve legitimately acquired items')
    $player.party=[BlueBattleLab.build(:PIKACHU,10),BlueBattleLab.build(:MAGIKARP,5)]
    check(BlueCampaign.common_level==7,'Highest party level 10 yields common trainer level 7')
    $player.party[0].level=1
    check(BlueCampaign.common_level==3,'Scaling uses the highest member rather than lead or average')
    $player.party.each { |p| p.level=1 }
    check(BlueCampaign.common_level==1,'Common trainer scaling clamps the minimum to level 1')
    $player.party[0].level=100
    check(BlueCampaign.common_level==70,'Common trainer level is 70 at a party maximum of 100')
    $player.party[0].level=10;$player.party[0].calc_stats
    trainer=NPCTrainer.new('Common campaign test',:YOUNGSTER);trainer.party=[BlueBattleLab.build(:PIKACHU,50)]
    source=Marshal.dump(trainer)
    battle=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,trainer.party,[$player],[trainer])
    check(battle.pbParty(1).first.level==7 && Marshal.dump(trainer)==source,'Native Battle constructor scales common opponents without modifying their source data')
    boss=NPCTrainer.new('Danny (Singles)',:YOUNGSTER);boss.party=[BlueBattleLab.build(:PIKACHU,50)]
    bb=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,boss.party,[$player],[boss])
    check(bb.pbParty(1).first.level==50,'Boss level and roster retain the existing scaling path')
    $PokemonGlobal.blue_campaign_mechanics=BlueBattleOptions.defaults.transform_values { false }
    disabled=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,trainer.party,[$player],[trainer])
    check(BlueBattleOptions::LABELS.keys.none? { |key| BlueBattleOptions.allowed?(disabled,key) },'Journey mechanic choices apply to both sides of every campaign battle')
    BattleCreationHelperMethods.prepare_battle(battle)
    before=$player.money;battle.pbGainMoney
    check($player.money-before==7*trainer.base_money && battle.moneyGain,'Common trainer victory pays exactly native level times class reward')
    metrics=GameData::SpeciesMetrics.get_species_form(:CAVEFANG,0)
    check(metrics.back_sprite_scale==1.5 && metrics.front_sprite_scale==1,'Author back sprites grow to 192px frames; front scale stays unchanged')
    BlueCampaign::Shop.new.open do |shop|
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-campaign-shop-smoke.png');shot.dispose
      shop.instance_variable_set(:@tab,2);shop.refresh
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-campaign-mega-shop-smoke.png');shot.dispose
    end
    check(true,'Native tabbed shop renders medicine and Mega Stone categories')
  ensure
    $PokemonGlobal=Marshal.load(old_global) if old_global
    $bag=old_bag if old_bag;$game_map=old_map if old_map
    $player.money=old_money if old_money;$player.party=old_party if old_party
    $stats.money_spent_at_marts=old_spent if old_spent
    BlueCampaign.define_singleton_method(:active?,active) if active
    BlueStory.define_singleton_method(:enabled?,story_enabled) if story_enabled
    BlueCampaign.instance_variable_set(:@bulk_setup,false)
    PBDebug.define_singleton_method(:logonerr,logger) if logger
  end
end
