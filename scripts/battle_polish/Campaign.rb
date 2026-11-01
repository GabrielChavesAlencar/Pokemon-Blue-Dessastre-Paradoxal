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
  def self.common_level(party=$player.party)
    highest=party.reject(&:egg?).map(&:level).max || 1
    [[highest*7/10,1].max,GameData::GrowthRate.max_level].min
  end
  module Teams
    def initialize(*args)
      if BlueCampaign.active? && args[4] && !Array(args[4]).empty?
        level=BlueCampaign.common_level
        args[4]=Array(args[4]).map do |trainer|
          copy=trainer.clone
          copy.party=trainer.party.map do |original|
            pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level unless BlueCampaign.boss?(trainer);pkmn.calc_stats;pkmn.heal;pkmn
          end
          copy
        end
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
      (value.to_i<=0 ? 30 : value)*[1,2,3][BlueStory.stage]
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
