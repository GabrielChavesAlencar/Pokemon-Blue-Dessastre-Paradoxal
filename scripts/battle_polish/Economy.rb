# Official Emerald retail anchors; other tiers are Blue's explicit balance choices.
# Reference: https://github.com/pret/pokeemerald/blob/master/src/data/items.h
module BlueCampaign
  RETAIL={POKEBALL:200,GREATBALL:600,ULTRABALL:1200,PREMIERBALL:200,
    POTION:300,SUPERPOTION:700,HYPERPOTION:1200,MAXPOTION:2500,FULLRESTORE:3000,
    ANTIDOTE:100,BURNHEAL:250,ICEHEAL:250,AWAKENING:250,PARALYZEHEAL:200,
    FULLHEAL:600,REVIVE:1500,MAXREVIVE:4000,REPEL:350,SUPERREPEL:500,MAXREPEL:700}.freeze
  GEAR=[:MEGARING,:ZRING,:ZPOWERRING,:TERAORB,:DYNAMAXBAND,:POKEMONBOXLINK,:ADVENTUREGUIDE,:SOUNDTRACKEARBUDS,
    :ABILITYVIAL,:MASTERTERAJEWEL,:HIDDENORB,:VIALOFGLITTER,:SUPERVIAL,:PORTABLEWARDROBE,:REPELCHARM,:DYNAMAXINHIBITOR,
    :BICYCLE,:OLDROD,:GOODROD,:SUPERROD,:ITEMFINDER,:DOWSINGMACHINE,:POKERADAR,:TOWNMAP,
    :GRACIDEA,:REVEALGLASS,:PRISONBOTTLE,:ROTOMCATALOG,:ZYGARDECUBE,:DNASPLICERS,:DNASPLICERSUSED,
    :NSOLARIZER,:NSOLARIZERUSED,:NLUNARIZER,:NLUNARIZERUSED,:REINSOFUNITY,:REINSOFUNITYUSED,
    :OVALCHARM,:SHINYCHARM,:CATCHINGCHARM,:EXPCHARM,:MARKCHARM,:GLIMMERINGCHARM,:EXPALL,:MAXSOUP].freeze
  CONSUMABLES=(RETAIL.keys+[:SACREDASH,:HPUP,:PROTEIN,:IRON,:CALCIUM,:ZINC,:CARBOS,:PPUP,:PPMAX,:RARECANDY,:POKEDOLL,:ESCAPEROPE]).freeze
  BANNED=[:SETPOKEDOLLARSDISK,:SETGYMBADGEDISK,:ANYITEMDISK,:ANYPOKEMONDISK,:NOCLIPDISK,:WILDADJUSTER,:VSRECORDER,:AUTOWINPOLICY,
    :ROTOMPHONE,:INDIGODISK,:TEACHYTV,:MAXLURE,:DOOMCANDY,:METABREAKERAMULET,:CANARIBREAD].freeze
  TABS=['Cura','Poke Balls','Mega Stones','Cristais Z','Treino','TMs / TRs','Equipamentos','Outros'].freeze
  def self.sellable_item?(item)
    return false if restricted_item?(item.id)
    !item.is_important? || GEAR.include?(item.id) || item.is_zcrystal? || item.is_TM? || item.is_TR?
  end
  def self.restricted_item?(id)
    BANNED.include?(id) || id.to_s.match?(/NOCLIP|GENERAT|ADJUSTER|ANY.*DISK|SETPOKEDOLLAR|DEBUG|\ALVL\d+CANDY\z|\A(?:EXP(?:ERIENCE)?CANDY|RARECANDY|XATTACK|XDEFEN|XSP|XSPECIAL|XACCURACY|DIREHIT|GUARDSPEC|MAXMUSHROOMS)/)
  end
  def self.paid_consumable?(id)
    CONSUMABLES.include?(id) || id.to_s.end_with?('MINT')
  end
  module ConsumableItems
    def is_key_item?
      return false if BlueCampaign.active? && BlueCampaign.paid_consumable?(id)
      super
    end
    def consumed_after_use?
      return true if BlueCampaign.active? && BlueCampaign.paid_consumable?(id)
      super
    end
    def show_quantity
      return true if BlueCampaign.active? && BlueCampaign.paid_consumable?(id)
      super
    end
  end
  module NoBagTools
    def trigger(item,*args)
      return 0 if BlueCampaign.active? && BlueCampaign.restricted_item?(GameData::Item.get(item).id)
      super
    end
  end
  module NoFieldTools
    def trigger(item,*args)
      return false if BlueCampaign.active? && BlueCampaign.restricted_item?(GameData::Item.get(item).id)
      super
    end
  end
  def self.category(item)
    return 4 if BlueTraining::CLEANERS.key?(item.id)
    return 4 if item.id==:BLUEEVCLEANER
    return 4 if BlueIVSelectors::STATS.key?(item.id)
    return 2 if item.is_mega_stone?
    return 3 if item.is_zcrystal?
    return 1 if item.is_poke_ball?
    return 5 if item.is_machine?
    return 4 if item.id.to_s.match?(/MINT|CANDY|BOTTLECAP|ABILITY|VITAMIN|^HPUP$|^PROTEIN$|^IRON$|^CALCIUM$|^ZINC$|^CARBOS$|^PPUP$|^PPMAX$|POWER|MACHOBRACE/)
    return 6 if GEAR.include?(item.id) || item.is_important?
    return 0 if item.pocket==2 || item.battle_use==1
    7
  end
  def self.price(item)
    return 750 if BlueTraining::CLEANERS.key?(item.id)
    return 2_000 if item.id==:BLUEEVCLEANER
    return 50_000 if BlueIVSelectors::STATS.key?(item.id)
    return RETAIL[item.id] if RETAIL.key?(item.id)
    return 100_000 if item.id==:MASTERBALL
    return 30_000 if item.is_mega_stone?
    return 20_000 if item.is_zcrystal?
    return EQUIPMENT_PRICES.fetch(item.id,10_000) if GEAR.include?(item.id)
    return 20_000 if item.id.to_s.match?(/ABILITYPATCH|GOLDBOTTLECAP/)
    return 10_000 if item.id.to_s.match?(/ABILITY|BOTTLECAP|MINT|^RARECANDY$/)
    return machine_price(item) if item.is_machine?
    return 1_000 if item.is_poke_ball?
    return 100 if item.is_berry?
    # Convert battle-point rarity to money for competitive items with no retail.
    baseline=[item.price,item.bp_price>1 ? item.bp_price*500 : 0].max
    return [baseline,100].max if baseline>0
    [1_000,1_000,30_000,20_000,5_000,5_000,10_000,3_000][category(item)]
  end
  def self.stock(tab)
    key=[active?,$PokemonSystem.blue_locale,GameData::Item::DATA.length]
    if @shop_stock_key!=key
      @shop_stock_key=key;@shop_stocks=Array.new(TABS.length) { [] }
      GameData::Item.each { |i| @shop_stocks[category(i)] << i if sellable_item?(i) }
      @shop_stocks.map! { |rows| rows.sort_by { |i| i.name.downcase }.map(&:id).freeze }
    end
    @shop_stocks.fetch(tab).dup
  end
  def self.purchase(id,quantity)
    item=GameData::Item.get(id)
    return :unavailable unless sellable_item?(item)
    return :quantity unless quantity.is_a?(Integer) && quantity>0 && quantity<=Settings::BAG_MAX_PER_SLOT
    return :owned if item.is_important? && ($bag.has?(id) || quantity!=1)
    total=price(item)*quantity
    return :funds if $player.money<total
    return :full unless $bag.can_add?(id,quantity)
    return :full unless $bag.add(id,quantity)
    $player.money-=total;$stats.money_spent_at_marts+=total
    :ok
  end
  module Prices
    def getPrice(id,selling=false)
      return super unless BlueCampaign.active?
      item=GameData::Item.get(id)
      cost=BlueCampaign.price(item)
      return cost unless selling
      return 0 unless BlueCampaign.sellable_item?(item) && !item.is_important?
      [super, cost/2].min
    end
  end
  def self.blocked_event?(event)
    event.name.match?(/PKMN Generator|Blue Dessastre Paradoxal|Anti Grind|Auto.?Grind/i)
  end
  def self.nurse?(event)
    event.name.match?(/\A(?:Nurse|Pokemon Center Nurse)\z/i) &&
      event.pages.any? { |p| p.graphic.character_name && !p.graphic.character_name.empty? }
  end
  def self.retail_page(event)
    copy=Marshal.load(Marshal.dump(event))
    copy.pages.each { |p| p.list=[RPG::EventCommand.new(355,0,['BlueCampaign.shop']),RPG::EventCommand.new] }
    copy
  end
  def self.patch_map(game_map)
    return unless active?
    map=game_map.instance_variable_get(:@map)
    # Only replace references in this loaded map; never serialize campaign maps.
    map.events.values.each do |event|
      if blocked_event?(event)
        map.events.delete(event.id);game_map.events.delete(event.id)
      elsif event.name.match?(/\A(?:Mart Trader|Supply Clerk)\z/i)
        replacement=retail_page(event);map.events[event.id]=replacement
        game_map.events[event.id]=Game_Event.new(game_map.map_id,replacement,game_map)
      end
    end
    return unless ($PokemonGlobal&.blue_regions || {}).fetch("current", "DECADES") == "DECADES"
    nurses=map.events.values.select { |e| nurse?(e) }
    nurses.each do |nurse|
      name='Blue Shop / '+nurse.id.to_s
      next if map.events.values.any? { |e| e.name==name }
      positions=[[-1,0],[1,0],[-2,0],[2,0],[0,1],[0,-1]].map { |dx,dy| [nurse.x+dx,nurse.y+dy] }
      position=positions.find do |x,y|
        game_map.valid?(x,y) && !map.events.values.any? { |e| e.x==x && e.y==y } && BlueBattleOptions.reachable_ball?(game_map,x,y)
      end
      raise 'Sem espaco acessivel para vendedor ao lado da Joy: '+game_map.map_id.to_s+'/'+nurse.id.to_s unless position
      template=map.events.values.find { |e| e.name=='Mart Trader' }
      unless template
        @merchant_template ||= load_data('Data/Map079.rxdata').events.values.find { |e| e.name=='Mart Trader' }
        template=@merchant_template
      end
      id=(map.events.keys.max || 0)+1
      event=RPG::Event.new(*position);event.id=id;event.name=name
      event.pages.first.graphic=Marshal.load(Marshal.dump((template || nurse).pages.first.graphic))
      event=retail_page(event);map.events[id]=event
      game_map.events[id]=Game_Event.new(game_map.map_id,event,game_map)
    end
  end
  module Maps
    def setup(*args)
      result=super
      BlueCampaign.patch_map(self)
      result
    end
  end
end
