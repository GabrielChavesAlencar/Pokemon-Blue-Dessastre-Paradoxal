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
    check(BlueCampaign.stock(0).include?(:FULLRESTORE) && BlueCampaign.stock(4).include?(:ADAMANTMINT) && !BlueCampaign.stock(4).include?(:RARECANDY),'Medicines and mints remain available; Rare Candy is removed from the shop')
    check([:FULLRESTORE,:ADAMANTMINT,:RARECANDY,:REPEL].all? { |id| i=GameData::Item.get(id);!i.is_important? && i.consumed_after_use? },'Standard consumables cannot act as infinite-use key items in the campaign')
    $bag.add(:FULLRESTORE,2)
    patient=BlueBattleLab.build(:PIKACHU,10);patient.hp-=10
    medicine_scene=Object.new
    [:pbRefresh,:pbClearAnnotations,:pbHardRefresh,:pbUpdate,:pbDisplay].each { |name| medicine_scene.define_singleton_method(name) { |*args| } }
    used=pbUseItemOnPokemon(:FULLRESTORE,patient,medicine_scene)
    check(used && patient.hp==patient.totalhp && $bag.quantity(:FULLRESTORE)==1,'Native medicine use heals and consumes exactly one purchased Full Restore')
    check(items.none? { |i| i.id.to_s.match?(/EXPCANDY|RARECANDY|\AX(?:ATTACK|DEF|SP|ACC)|DIREHIT/) },'No experience candies or direct stat-boosting battle items are sold')
    machine=Object.new;machine.define_singleton_method(:move) { :EMBER };machine.define_singleton_method(:is_TR?) { false }
    ember_price=BlueCampaign.machine_price(machine);machine.define_singleton_method(:move) { :FIREBLAST }
    check(ember_price==500 && BlueCampaign.machine_price(machine)==5_500,'Move-based TM tiers: Ember 500; Fire Blast 5500')
    check(BlueCampaign.price(GameData::Item.get(:ADVENTUREGUIDE))<BlueCampaign.price(GameData::Item.get(:TERAORB)),'Equipment prices reflect utility rather than one universal price')
    check(BlueIVSelectors::STATS.keys.all? { |id| BlueCampaign.stock(4).include?(id) && BlueCampaign.price(GameData::Item.get(id))==50_000 },'All six IV selectors are sold in Training for 50000 each')
    iv_number=BlueIVSelectors.method(:choose_value)
    [0,31,15,-1,15].each do |value|
      $bag.add(:BLUEIVATTACK,2) if $bag.quantity(:BLUEIVATTACK)<2
      before_quantity=$bag.quantity(:BLUEIVATTACK);before_iv=patient.iv.clone
      BlueIVSelectors.define_singleton_method(:choose_value) { |*args| value }
      changed=pbUseItemOnPokemon(:BLUEIVATTACK,patient,medicine_scene)
      expected=value>=0 && before_iv[:ATTACK]!=value
      check(changed==expected && $bag.quantity(:BLUEIVATTACK)==before_quantity-(expected ? 1 : 0),'Native IV selector consumes only a real change; value='+value.to_s)
      check(patient.iv.reject { |k,v| k==:ATTACK }==before_iv.reject { |k,v| k==:ATTACK },'IV selection preserves the other five attributes')
    end
    BlueIVSelectors.define_singleton_method(:choose_value,iv_number)
    check(UIHandlers.get_info(:summary,:page_info,:options).none? { |option| option.is_a?(String) && option.include?('IVs') },'Free IV presets are hidden in the campaign; paid selectors cannot be bypassed')
    check(BlueIVSelectors::STATS.all? { |id,stat| BlueIVSelectors.apply(id,patient,0) && patient.iv[stat]==0 && BlueIVSelectors.apply(id,patient,31) && patient.iv[stat]==31 },'All six selectors accept zero and 31 independently')
    patient.iv[:ATTACK]=0;patient.ivMaxed[:ATTACK]=true;patient.calc_stats
    check(BlueIVSelectors.apply(:BLUEIVATTACK,patient,0) && !patient.ivMaxed[:ATTACK] && patient.iv[:ATTACK]==0,'Choosing zero also clears Hyper Training for that attribute, so the actual battle IV becomes zero')
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
    badges=$player.badges.dup
    $player.badges.replace(Array.new(18,false))
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
    check(bb.pbParty(1).first.level==7,'Bosses use the same 70 percent campaign scaling as every trainer')
    # Master starts at 11 badges: 90 percent of the strongest party Pokemon.
    $player.badges.replace(Array.new(18) { |i| i<11 })
    $player.party[0].level=50;$player.party[0].calc_stats
    check(BlueCampaign.master? && BlueCampaign.common_level==45,'Master trainer level is 90 percent for every trainer')
    first=NPCTrainer.new('Master coverage sample',:YOUNGSTER)
    first.party=[:CHARIZARD,:ARCANINE,:FLAREON].map { |id| BlueBattleLab.build(id,50) }
    original=Marshal.dump(first)
    master_battle=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,first.party,[$player],[first])
    foes=master_battle.pbParty(1)
    check(foes.length==4 && foes.all? { |mon| mon.level==45 },'Master fills 3-member trainer teams to 4 at 90 percent level')
    check(Marshal.dump(first)==original,'Master adds a Pokemon to battle copies, never the source trainer')
    check(!first.party.map(&:species).include?(foes.last.species),'Master partner is a new species, not a duplicate')
    check([:WATER,:GROUND,:ROCK].any? { |type| Effectiveness.calculate(type,*foes.last.species_data.types)<1 },
      'Master extra Pokemon resists a shared Fire team weakness')
    again=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,first.party,[$player],[first])
    check(again.pbParty(1).last.species==foes.last.species,'Master coverage is deterministic for the same trainer')
    full=NPCTrainer.new('Master full roster',:YOUNGSTER)
    full.party=[:PIKACHU,:GENGAR,:BLASTOISE,:VENUSAUR,:DRAGONITE,:LUCARIO].map { |id| BlueBattleLab.build(id,50) }
    full_battle=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,full.party,[$player],[full])
    check(full_battle.pbParty(1).length==6 && full_battle.pbParty(1).all? { |p| p.level==45 },
      'Master keeps complete six-Pokemon boss/leader teams intact at 90 percent')
    copies=[first.clone,first.clone]
    copies.each { |t| t.party=Marshal.load(Marshal.dump(first.party)) }
    BlueCampaign.expand_master_teams(copies,45)
    check(copies.sum { |t| t.party.length }==6,'Two opposing trainers never exceed six party slots')
    $player.badges.replace(Array.new(18,false))
    $player.party[0].level=10;$player.party[0].calc_stats
    test_mon=BlueBattleLab.build(:CHARIZARD,50);test_mon.moves=[:FIREBLAST,:SWORDSDANCE,:DRAGONCLAW,:FLAMETHROWER].map { |id| Pokemon::Move.new(id) }
    [0,2,5,11].each do |badge_count|
      $player.badges.replace(Array.new(18) { |i| i<badge_count })
      sample=Marshal.load(Marshal.dump(test_mon));original_moves=sample.moves.map(&:id)
      cap=BlueTrainerMoves::CAPS[BlueStory.stage]
      BlueTrainerMoves.adjust(sample,cap,battle) if cap
      legal=sample.species_data.moves.select { |level,id| level<=sample.level }.map(&:last)+sample.species_data.tutor_moves
      check(cap ? sample.moves.all? { |m| legal.include?(m.id) && BlueTrainerMoves.safe?(m.id,cap,battle) } : sample.moves.map(&:id)==original_moves,'Trainer moves obey legal '+(cap ? cap.to_s+' power cap' : 'unchanged advanced stage'))
      check(!cap || !sample.moves.any? { |m| m.id==:SWORDSDANCE },'Large stat boosts are excluded before the advanced stage')
    end
    rewards=[0,2,5,11].map { |count| $player.badges.replace(Array.new(18) { |i| i<count });trainer.base_money }
    check(rewards.each_with_index.all? { |value,i| value==rewards[0]*(i+1) },'Trainer prize rates grow 1x / 2x / 3x / 4x with campaign stage')
    $player.badges.replace(badges)
    $PokemonGlobal.blue_campaign_mechanics=BlueBattleOptions.defaults.transform_values { false }
    disabled=Battle.new(BlueBattleLab::SmokeScene.new,$player.party,trainer.party,[$player],[trainer])
    check(BlueBattleOptions::LABELS.keys.none? { |key| BlueBattleOptions.allowed?(disabled,key) },'Journey mechanic choices apply to both sides of every campaign battle')
    BattleCreationHelperMethods.prepare_battle(battle)
    before=$player.money;battle.pbGainMoney
    check($player.money-before==7*trainer.base_money && battle.moneyGain,'Common trainer victory pays exactly native level times class reward')
    metrics=GameData::SpeciesMetrics.get_species_form(:CAVEFANG,0)
    check(metrics.back_sprite_scale==2 && metrics.front_sprite_scale==2,'128px author sprites render at 2x on both battle sides')
    BlueCampaign::Shop.new.open do |shop|
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-campaign-shop-smoke.png');shot.dispose
      shop.instance_variable_set(:@tab,2);shop.refresh
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-campaign-mega-shop-smoke.png');shot.dispose
    end
    check(true,'Native tabbed shop renders medicine and Mega Stone categories')
  ensure
    BlueIVSelectors.define_singleton_method(:choose_value,iv_number) if iv_number
    $player.badges.replace(badges) if badges
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
