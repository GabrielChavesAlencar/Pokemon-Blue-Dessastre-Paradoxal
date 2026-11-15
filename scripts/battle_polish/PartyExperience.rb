# Modern party-wide Exp. Share for normal single-player adventures.
# Uses Essentials 21.1 native pbGainExp/pbGainExpOne calculations (100% active,
# 50% nonparticipants, EVs, level scaling, cap, animations and move learning).
# The existing Exp All implementation already excludes fainted/egg/boxed
# Pokémon. Do not award experience manually or change the battle formula.
module BluePartyExperience
  module NativeExpAll
    def pbGainExp
      return super unless BluePartyExperience.adventure_battle?(self)
      # Temporarily expose Essentials' built-in Exp All mode. Avoid modifying
      # inventory or the saved Player flag: old saves and Exp All ownership
      # remain intact, and non-adventure battles retain their own rules.
      old_value = $player.has_exp_all
      return super if old_value
      $player.has_exp_all = true
      begin
        super
      ensure
        $player.has_exp_all = old_value
      end
    end
  end

  def self.adventure_battle?(battle)
    return false unless battle && battle.respond_to?(:internalBattle) &&
                        battle.respond_to?(:expGain)
    return false unless battle.internalBattle && battle.expGain
    return false unless $player && $player.respond_to?(:has_exp_all) &&
                        $player.respond_to?(:has_exp_all=)
    return false if battle.instance_variable_get(:@blue_lab_battle)
    return false if defined?(BlueBattleLab) && BlueBattleLab::ACTIVE
    return false if defined?(BlueBattleOptions) &&
                    BlueBattleOptions.respond_to?(:battle_area?) &&
                    BlueBattleOptions.battle_area?
    true
  end

  def self.install
    return if Battle.ancestors.include?(NativeExpAll)
    Battle.prepend(NativeExpAll)
  end
end
