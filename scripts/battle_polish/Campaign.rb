# Own campaign adapters; loaded saves are never reset or migrated destructively.
class PokemonGlobalMetadata
  attr_accessor :blue_campaign_started, :blue_campaign_departure, :blue_campaign_mechanics
end
module BlueCampaign
  BOSSES=%w[Marigold Reva Keegan Quinn Luis Luna Galen Christopher Atlas Sophia Hermes Cethin Keiko Roho Belinda Gohar Eira Azure Danny].freeze
  def self.active?
    BlueStory.story? && !(defined?(BlueBattleLab) && BlueBattleLab::ACTIVE)
  end
  def self.bulk_setup?;!!@bulk_setup;end
  def self.begin_journey(prompt=true)
    return if $PokemonGlobal.blue_campaign_started
    $PokemonGlobal.blue_campaign_started=true
    $PokemonGlobal.blue_campaign_departure=true
    $PokemonGlobal.blue_campaign_mechanics=BlueBattleOptions.defaults
    $bag.clear
    BlueBattleOptions.mechanics_menu(:campaign) if prompt
  end
  def self.depart
    return unless active? && $PokemonGlobal.blue_campaign_departure && $game_map.map_id!=1
    $bag.clear
    $bag.registered_items.clear
    $PokemonGlobal.blue_campaign_departure=false
  end
  def self.boss?(trainer)
    BOSSES.include?(trainer.name.split(' (').first) || trainer.trainer_type.to_s.match?(/LEADER|MASTER|BOSS|ELITE|CHAMPION|RIVAL|ADMIN/)
  end
  def self.master?
    BlueStory.stage==3
  end
  def self.common_level(party=$player.party)
    scaled_level(party,master? ? 90 : 70)
  end
  def self.scaled_level(party,percent)
    highest=party.reject(&:egg?).map(&:level).max || 1
    [[highest*percent/100,1].max,GameData::GrowthRate.max_level].min
  end
  def self.trainer_level(trainer,party=$player.party)
    common_level(party)
  end

  # Only fill small teams in Master. Native 4-6 Pokemon boss/leader teams
  # remain untouched, and opposing sides can never exceed six Pokemon.
  def self.master_candidates
    @master_candidates ||= begin
      pool=[]
      GameData::Species.each do |species|
        next unless species.form==0
        stats=species.base_stats.values
        next unless stats.all? { |value| value.to_i>0 }
        next unless (440..570).cover?(stats.sum)
        next unless (species.flags & ['Legendary','Mythical','UltraBeast','Paradox','Pending']).empty?
        next if species.moves.empty?
        pool << species
      end
      pool
    end
  end

  def self.master_weaknesses(party)
    threats={}
    GameData::Type.each do |attack|
      next if attack.pseudo_type
      multipliers=party.map { |p| Effectiveness.calculate(attack.id,*p.species_data.types) }
      weakness=multipliers.sum { |value| value>=4 ? 4 : value>1 ? 2 : 0 }
      resistance=multipliers.count { |value| value<1 }
      threats[attack.id]=weakness-resistance if weakness>resistance
    end
    threats
  end

  def self.master_partner(party,trainer,level)
    existing=party.map(&:species)
    types=party.flat_map { |p| p.species_data.types }.uniq
    threats=master_weaknesses(party)
    salt=trainer.name.to_s.bytes.each_with_index.sum { |b,i| b*(i+1) }
    selected=master_candidates.reject { |data| existing.include?(data.species) }.max_by do |data|
      coverage=threats.sum do |attack,risk|
        multiplier=Effectiveness.calculate(attack,*data.types)
        risk*(multiplier==0 ? 6 : multiplier<1 ? 4 : multiplier>1 ? -4 : 0)
      end
      new_types=(data.types-types).length
      strength=data.base_stats.values.sum
      variety=(data.id.to_s.bytes.sum+salt)%7
      [coverage*3+new_types*9+(strength-440)/12+variety,strength,data.id.to_s]
    end
    return nil unless selected
    pkmn=Pokemon.new(selected.species,level,trainer,true,false)
    pkmn.iv.each_key { |stat| pkmn.iv[stat]=31 }
    pkmn.ev.each_key { |stat| pkmn.ev[stat]=0 }
    offense=selected.base_stats[:ATTACK]>=selected.base_stats[:SPECIAL_ATTACK] ? :ATTACK : :SPECIAL_ATTACK
    pkmn.ev[offense]=252
    pkmn.ev[:SPEED]=252
    pkmn.ev[:HP]=4
    pkmn.reset_moves
    pkmn.calc_stats
    pkmn.heal
    pkmn
  end

  def self.expand_master_teams(trainers,level)
    return trainers unless master?
    # Native Essentials parties are limited to six Pokemon per side. For
    # multiple opposing trainers, distribute remaining slots fairly.
    slots=[6-trainers.sum { |trainer| trainer.party.length },0].max
    while slots>0
      eligible=trainers.each_with_index.select { |trainer,i| trainer.party.length.between?(1,3) }
      break if eligible.empty?
      trainer,index=eligible.min_by { |row,i| [row.party.length,i] }
      extra=master_partner(trainer.party,trainer,level)
      break unless extra
      trainer.party << extra
      slots-=1
    end
    trainers
  end
  def self.wild_level(party=$player.party)
    highest=party.reject(&:egg?).map(&:level).max || 1
    [[highest*45/100,1].max,GameData::GrowthRate.max_level].min
  end
  module Teams
    def initialize(*args)
      if BlueCampaign.active? && args[4] && !Array(args[4]).empty?
        level=BlueCampaign.trainer_level(Array(args[4]).first)
        trainers=Array(args[4]).map do |trainer|
          copy=trainer.clone
          copy.party=trainer.party.map do |original|
            pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level;pkmn.calc_stats;pkmn.heal;pkmn
          end
          copy
        end
        args[4]=BlueCampaign.expand_master_teams(trainers,level)
        args[2]=args[4].flat_map(&:party)
      end
      super(*args)
      @blue_mechanics=BlueBattleOptions.snapshot(:campaign) if BlueCampaign.active?
      BlueTrainerMoves.apply(self) if BlueCampaign.active? && trainerBattle?
    end
  end
  module Preparation
    def prepare_battle(battle)
      super
      if BlueCampaign.active? && battle.trainerBattle?
        battle.moneyGain=true;battle.internalBattle=true
      end
    end
  end
  module TrainerMoney
    def base_money
      value=super
      return value unless BlueCampaign.active?
      (value.to_i<=0 ? 30 : value)*[1,2,3,4][BlueStory.stage]*(BlueJourney.gym_name(name) ? 2 : 1)
    end
  end
  module Setup
    def pbStoryModeSetup
      BlueStory.choose_mode(:story) unless BlueStory.story?
      BlueCampaign.begin_journey unless defined?(BlueBattleLab) && BlueBattleLab::ACTIVE
      before=BlueCampaign.bulk_setup?
      BlueCampaign.instance_variable_set(:@bulk_setup,BlueCampaign.active?)
      super
    ensure
      BlueCampaign.instance_variable_set(:@bulk_setup,before)
    end
    def pbAllPokemonSetup5
      return if BlueCampaign.bulk_setup?
      super
    end
    def pbAddPokemonSilent(*args)
      return false if BlueCampaign.bulk_setup?
      super
    end
    def pbPumbInAllItems
      return if BlueCampaign.active?
      super
    end
    def pbStoryModeTrainerItemSuite
      return if BlueCampaign.active?
      super
    end
  end
  module BackSprites
    def back_sprite_scale
      size=super
      data=GameData::Species.get_species_form(species,form)
      data.flags.include?('DessastreParadoxal') && size==1 ? 1.5 : size
    end
  end
  module LoadedMap
    def load_map
      result=super
      BlueCampaign.patch_map($game_map) if $game_map
      result
    end
  end
  def self.install
    return if @installed
    Battle.prepend(Teams);NPCTrainer.prepend(TrainerMoney)
    BattleCreationHelperMethods.singleton_class.prepend(Preparation)
    Object.prepend(Setup);GameData::SpeciesMetrics.prepend(BackSprites)
    Game_Map.prepend(Maps)
    Game.singleton_class.prepend(LoadedMap)
    PokemonMartAdapter.prepend(Prices)
    GameData::Item.prepend(ConsumableItems)
    GameData::Item.singleton_class.prepend(BlueIVSelectors::Icons)
    Game.singleton_class.prepend(BlueIVSelectors::Loaded)
    MenuHandlers.singleton_class.prepend(BlueIVSelectors::PartyOptions)
    UIHandlers.singleton_class.prepend(BlueIVSelectors::SummaryOptions) if defined?(UIHandlers)
    PokemonSummary_Scene.prepend(BlueIVSelectors::SummaryActions)
    ItemHandlers::UseFromBag.singleton_class.prepend(NoBagTools)
    ItemHandlers::UseInField.singleton_class.prepend(NoFieldTools)
    ItemHandlers::ConfirmUseInField.singleton_class.prepend(NoFieldTools)
    ItemHandlers::CanUseInBattle.singleton_class.prepend(NoFieldTools)
    EventHandlers.add(:on_enter_map,:blue_campaign_departure,proc { |*args| BlueCampaign.depart })
    @installed=true
  end
end
