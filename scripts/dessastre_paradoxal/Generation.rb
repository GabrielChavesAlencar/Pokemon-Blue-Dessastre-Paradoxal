# Original support code for the author's named generation.
module BlueDessastreParadoxal
  NAME = 'Dessastre Paradoxal'
  FLAG = 'DessastreParadoxal'
  def self.with_move_user(battle, user)
    previous=battle.instance_variable_get(:@blue_dp_move_user)
    battle.instance_variable_set(:@blue_dp_move_user,user.index)
    yield
  ensure
    battle.instance_variable_set(:@blue_dp_move_user,previous)
  end
end

module BlueDPGenerationLabel
  def generation_label
    return BlueDessastreParadoxal::NAME if flags.include?(BlueDessastreParadoxal::FLAG)
    return "Geracao #{generation}"
  end
end


module BlueDPPersonalSun
  def effectiveWeather
    weather=super
    if @battle.instance_variable_get(:@blue_dp_move_user)==@index && hasActiveAbility?(:MEGASOL)
      return :Sun
    end
    return weather
  end
  def pbUseMove(*args)
    BlueDessastreParadoxal.with_move_user(@battle,self) { super(*args) }
  end
end


# The author's Electrode branch uses a Fast Ball as its evolution item.
# It remains a Poke Ball in battle; only its field use gains evolution support.
module BlueDPFastBallEvolution
  def field_use
    return 1 if @id==:FASTBALL
    super
  end
  def is_evolution_stone?
    return true if @id==:FASTBALL
    super
  end
end
# HandlerHash resolves item IDs, so copy handlers only after GameData.load_all.
module BlueDPLoadedItemHandlers
  def initialize
    super
    ItemHandlers::UseOnPokemon.copy(:FIRESTONE,:FASTBALL)
  end
  public :initialize
end

module BlueDessastreParadoxal
  def self.install
    GameData::Species.prepend(BlueDPGenerationLabel) unless GameData::Species.ancestors.include?(BlueDPGenerationLabel)
    Battle::Battler.prepend(BlueDPPersonalSun) unless Battle::Battler.ancestors.include?(BlueDPPersonalSun)
    GameData::Item.prepend(BlueDPFastBallEvolution) unless GameData::Item.ancestors.include?(BlueDPFastBallEvolution)
    Game.singleton_class.prepend(BlueDPLoadedItemHandlers) unless Game.singleton_class.ancestors.include?(BlueDPLoadedItemHandlers)
  end
end
module Compiler
  class << self
    alias blue_dp_original_main main
    def main
      blue_dp_original_main
      BlueDessastreParadoxal.install
      BlueFutureEevee.install if defined?(BlueFutureEevee)
    end
  end
end
