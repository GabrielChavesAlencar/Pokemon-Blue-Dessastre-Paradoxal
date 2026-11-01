# Mechanics follow the primary Showdown implementation referenced by the catalogue.
module BlueZAMegas
  module LegacyStones
    def getMegaForm
      found=super
      return found if found>0
      # Keep existing campaign trainers, inventory and saved teams functional.
      # Dedicated stones remain the standard for newly built/imported teams.
      BlueZAMegas::CATALOG.each do |row|
        next unless row[:species]==species
        data=GameData::Species.get_species_form(species,row[:form])
        next unless data.unmega_form==form_simple
        legacy=:MEGAITE
        legacy=:MEGAITEX if species==:RAICHU && row[:form]==2
        legacy=:MEGAITEY if (species==:RAICHU && row[:form]==3) || species==:GRENINJA
        legacy=:MEGAITEZ if [:ABSOL,:GARCHOMP,:LUCARIO].include?(species)
        return row[:form] if hasItem?(legacy)
      end
      found
    end
  end
  module Battler
    def hasActiveAbility?(check,*args)
      # Preserve the engine's airborne, Ground immunity and Mold Breaker paths.
      return true if check==:LEVITATE && super(:EELEVATE,*args)
      # Scope the engine's existing protection bypass to this one success check.
      return true if check==:UNSEENFIST && @blue_za_piercing_check && super(:PIERCINGDRILL,*args)
      super
    end
    def pbSuccessCheckAgainstTarget(move,user,target,targets)
      target.instance_variable_set(:@blue_za_pierced,nil)
      before=user.instance_variable_get(:@blue_za_piercing_check)
      piercing=user.hasActiveAbility?(:PIERCINGDRILL) && move.contactMove? && move.damagingMove?
      guarded=false
      if piercing
        side=target.pbOwnSide.effects
        guarded=side[PBEffects::WideGuard] && move.pbTarget(user).num_targets>1
        if move.canProtectAgainst?
          guarded ||= side[PBEffects::QuickGuard] && @battle.choices[user.index][4].to_i>0
          guarded ||= side[PBEffects::MatBlock]
          [:Protect,:KingsShield,:SpikyShield,:BanefulBunker,:Obstruct,:SilkTrap,:BurningBulwark].each do |key|
            guarded ||= target.effects[PBEffects.const_get(key)] if PBEffects.const_defined?(key)
          end
        end
      end
      user.instance_variable_set(:@blue_za_piercing_check,piercing)
      success=super
      target.instance_variable_set(:@blue_za_pierced,move.object_id) if success && piercing && guarded
      success
    ensure
      user.instance_variable_set(:@blue_za_piercing_check,before)
    end
  end
  def self.install
    Pokemon.prepend(LegacyStones) unless Pokemon.ancestors.include?(LegacyStones)
    # Essentials' old sex-based handler always forced Meowstic back to 0/1,
    # including when its Mega portrait or Pokemon#form was requested.
    MultipleForms.register(:MEOWSTIC,{'getForm'=>proc { |pokemon|
      next pokemon.female? ? 3 : 2 if pokemon.form_simple>=2
      next pokemon.female? ? 1 : 0
    }})
    Battle::Battler.prepend(Battler) unless Battle::Battler.ancestors.include?(Battler)
    Battle::AbilityEffects::ModifyMoveBaseType.add(:DRAGONIZE,proc { |ability,user,move,type|
      next unless type==:NORMAL
      move.powerBoost=true
      next :DRAGON
    })
    Battle::AbilityEffects::DamageCalcFromUser.copy(:AERILATE,:DRAGONIZE)
    Battle::AbilityEffects::DamageCalcFromUser.add(:FIREMANE,proc { |ability,user,target,move,mults,power,type|
      mults[:attack_multiplier]*=1.5 if type==:FIRE
    })
    Battle::AbilityEffects::DamageCalcFromUser.add(:PIERCINGDRILL,proc { |ability,user,target,move,mults,power,type|
      mults[:final_damage_multiplier]*=0.25 if target.instance_variable_get(:@blue_za_pierced)==move.object_id
    })
    Battle::AbilityEffects::DamageCalcFromTarget.add(:AURAGUARD,proc { |ability,user,target,move,mults,power,type|
      mults[:final_damage_multiplier]*=0.5 if move.contactMove?
    })
    Battle::AbilityEffects::OnEndOfUsingMove.copy(:BEASTBOOST,:EELEVATE)
    Battle::AbilityEffects::OnBeingHit.add(:SPICYSPRAY,proc { |ability,user,target,move,battle|
      next if user.fainted? || user.burned? || user.index==target.index
      battle.pbShowAbilitySplash(target)
      user.pbBurn(target) if user.pbCanBurn?(target,Battle::Scene::USE_ABILITY_SPLASH)
      battle.pbHideAbilitySplash(target)
    })
  end
end
module Compiler
  class << self
    alias blue_za_original_main main
    def main
      blue_za_original_main
      BlueZAMegas.install
    end
  end
end
