module BlueIVSelectors
  STATS={BLUEIVHP: :HP,BLUEIVATTACK: :ATTACK,BLUEIVDEFENSE: :DEFENSE,
    BLUEIVSPATK: :SPECIAL_ATTACK,BLUEIVSPDEF: :SPECIAL_DEFENSE,BLUEIVSPEED: :SPEED}.freeze
  def self.apply(id,pkmn,value)
    stat=STATS[id]
    return false unless stat && !pkmn.egg? && value.is_a?(Integer) && (0..31).include?(value)
    trained=pkmn.ivMaxed && pkmn.ivMaxed[stat]
    return false if pkmn.iv[stat]==value && !(trained && value!=31)
    pkmn.iv[stat]=value;pkmn.ivMaxed[stat]=false if pkmn.ivMaxed
    pkmn.calc_stats;true
  end
  def self.use(id,pkmn,scene)
    return false if pkmn.egg?
    stat=STATS.fetch(id)
    current=pkmn.ivMaxed && pkmn.ivMaxed[stat] ? 31 : pkmn.iv[stat]
    params=ChooseNumberParams.new;params.setRange(0,31);params.setInitialValue(current);params.setCancelValue(-1)
    value=choose_value(stat,pkmn,params)
    return false if value<0
    unless apply(id,pkmn,value)
      scene.pbDisplay('O IV ja tem esse valor. O seletor nao foi gasto.');return false
    end
    scene.pbRefresh
    scene.pbDisplay('IV de '+GameData::Stat.get(stat).name+' definido como '+value.to_s+'.')
    true
  end
  def self.choose_value(stat,pkmn,params)
    current=pkmn.ivMaxed && pkmn.ivMaxed[stat] ? 31 : pkmn.iv[stat]
    pbMessageChooseNumber('IV de '+GameData::Stat.get(stat).name+' de '+pkmn.name+' / atual '+current.to_s,params)
  end
  def self.install_handlers
    STATS.each_key { |id| ItemHandlers::UseOnPokemon.add(id,proc { |item,qty,pkmn,scene| BlueIVSelectors.use(item,pkmn,scene) }) }
  end
  module Loaded
    def initialize
      super
      BlueIVSelectors.install_handlers
    end
    public :initialize
  end
  module Icons
    def icon_filename(item)
      data=try_get(item)
      return super(:BOTTLECAP) if data && BlueIVSelectors::STATS.key?(data.id)
      super
    end
  end
  module SummaryOptions
    def get_info(menu,option,type=nil)
      value=super
      return value unless BlueCampaign.active? && menu==:summary && option==:page_info
      return 'Info' if type==:name
      type==:options && value.is_a?(Array) ? value.reject { |entry| entry.is_a?(String) && entry.include?('IVs') } : value
    end
  end
  module SummaryActions
    def pbPageCustomOption(command)
      return false if BlueCampaign.active? && command.is_a?(String) && command.include?('IVs')
      super
    end
  end
  module PartyOptions
    def each_available(menu,*args,&block)
      super(menu,*args) do |option,hash,name|
        next if BlueCampaign.active? && ((menu==:party_menu && [:hidden_values,:debug].include?(option)) || (menu==:pause_menu && option==:debug))
        block.call(option,hash,name)
      end
    end
    def call(menu,option,function,*args)
      return nil if BlueCampaign.active? && menu==:party_menu && [:hidden_values,:debug].include?(option)
      super
    end
  end
end
