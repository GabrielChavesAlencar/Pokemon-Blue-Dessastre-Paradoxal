module BlueRadicalAI

  module TrainerSkill
    def set_up_skill
      super
      @skill=[@skill,BlueRadicalAI.profile(@ai.battle)['skill']].max if @trainer && BlueRadicalAI.enabled?(@ai.battle)
    end
  end

  module BlankBattler
    def initialize(*args)
      super
      @blue_rr_blank_effects=@effects.dup
    end
  end

  module Decisions
    def set_up(index)
      super
      return if @blue_rr_probe || !BlueRadicalAI.enabled?(@battle)
      BlueRadicalAI.observe(@battle)
      @blue_rr_snapshot=BlueRadicalAI::Snapshot.new(self)
    end

    def pbGetMoveScores
      return super if @blue_rr_probe || !BlueRadicalAI.enabled?(@battle)
      @blue_rr_snapshot=BlueRadicalAI::Snapshot.new(self)
      snapshot=@blue_rr_snapshot
      user=snapshot.battler(@user.index)
      if @battle.pbRegisteredMegaEvolution?(@user.index)
        snapshot.replace_battler(snapshot.mega(user))
      end
      BlueRadicalAI::BASE_ENUMERATOR.bind(snapshot.probe).call
    end

    def pbGetMoveScore(targets=nil)
      return super unless BlueRadicalAI.enabled?(@battle)
      snapshot=@blue_rr_snapshot || BlueRadicalAI::Snapshot.new(self)
      source=@user.battler
      source=snapshot.battler(source.index) unless @blue_rr_probe
      result=snapshot.score_move(source,@move.move,targets)
      BlueRadicalAI.trace('MOVE_SCORE',{turn:@battle.turnCount,user:source.index,move:@move.id,target:targets&.map(&:index),score:result[:score],reasons:result[:reasons]})
      result[:score]
    end

    def pbChooseMove(choices)
      return super unless BlueRadicalAI.enabled?(@battle)
      if choices.empty?
        return @battle.pbAutoChooseMove(@user.index)
      end
      candidates=choices.map { |choice| {score:choice[1],choice:choice} }
      selected=BlueRadicalAI.best(candidates,@battle)[:choice]
      if selected[1] <= Battle::AI::MOVE_USELESS_SCORE && pbChooseToSwitchOut(true)
        @battle.pbUnregisterMegaEvolution(@user.index)
        return
      end
      pbRegisterEnemySpecialActionFromMove(@user.battler,selected[4]) if selected[4] && respond_to?(:pbRegisterEnemySpecialActionFromMove)
      unless @battle.pbRegisterMove(@user.index,selected[0],false)
        return @battle.pbAutoChooseMove(@user.index)
      end
      @battle.pbRegisterTarget(@user.index,selected[2]) if selected[2] && selected[2]>=0
      plans=BlueRadicalAI.memory(@battle)[:plans] ||= {}
      snapshot=@blue_rr_snapshot
      move=@user.battler.moves[selected[0]]
      amount=0
      if move && selected[2] && selected[2]>=0 && move.damagingMove?
        amount=snapshot.damage(snapshot.battler(@user.index),snapshot.battler(selected[2]),move)[:damage]
      end
      plans[@user.index]={turn:@battle.turnCount,target:selected[2],damage:amount,protect:BlueRadicalAI::PROTECT.include?(move&.id)}
      BlueRadicalAI.trace('CHOOSE_MOVE',{turn:@battle.turnCount,user:@user.index,move:move&.id,target:selected[2],score:selected[1],profile:BlueRadicalAI.profile_id(@battle)})
    end

    def choose_best_replacement_pokemon(index,forced=false)
      return super unless BlueRadicalAI.enabled?(@battle)
      snapshot=@blue_rr_snapshot || BlueRadicalAI::Snapshot.new(self)
      options=snapshot.switch_candidates(index,forced)
      if !forced
        options=options.select { |x| x[:entry_hp]>0 && x[:safe] }
      else
        alive=options.select { |x| x[:entry_hp]>0 }
        options=alive unless alive.empty?
      end
      best=BlueRadicalAI.best(options,@battle)
      BlueRadicalAI.trace('REPLACEMENT',{turn:@battle.turnCount,user:index,forced:forced,candidates:options,selected:best && best[:party]})
      best ? best[:party] : -1
    end

    def pbChooseToSwitchOut(terrible_moves=false)
      return super unless BlueRadicalAI.enabled?(@battle)
      return false if !@battle.canSwitch || !@battle.pbCanSwitchOut?(@user.index)
      return false unless @trainer.has_skill_flag?('ConsiderSwitching') || terrible_moves
      snapshot=@blue_rr_snapshot || BlueRadicalAI::Snapshot.new(self)
      user=snapshot.battler(@user.index)
      options=snapshot.switch_candidates(user.index).select { |x| x[:entry_hp]>0 && x[:safe] }
      return false if options.empty?
      current=snapshot.evaluate_candidate(user)
      best=BlueRadicalAI.best(options,@battle)
      perish=user.effects[PBEffects::PerishSong]==1
      return false if current[:revenge] && !perish
      state=BlueRadicalAI.memory(@battle)
      last=(state[:last_switch] || {})[user.index]
      return false if last && @battle.turnCount-last<2 && !perish
      stalled=terrible_moves || current[:outgoing]==0
      losing=current[:incoming]>=user.hp
      cure=user.status!=:NONE && user.hasActiveAbility?(:NATURALCURE)
      regenerate=user.hp<user.totalhp*0.5 && user.hasActiveAbility?(:REGENERATOR)
      debuffed=user.stages[:ATTACK]<=-3 || user.stages[:SPECIAL_ATTACK]<=-3
      drowsy=user.effects[PBEffects::Yawn]>0 && user.status==:NONE
      boosted=user.stages.values.sum { |x| [x,0].max }>=2
      margin=boosted ? 25 : 12
      want=perish || (best[:score]>=current[:score]+margin) || ((losing || stalled || cure || regenerate || debuffed || drowsy) && best[:score]>current[:score])
      return false unless want
      # A safe, faster pivot retains initiative; immediate danger still hard-switches.
      if !perish && !losing
        pivot=snapshot.legal_moves(user).find { |m| PIVOTS.include?(m.id) && m.damagingMove? }
        if pivot
          useful=snapshot.foes(user.index).any? { |foe| snapshot.acts_first?(user,foe) && snapshot.damage(user,foe,pivot)[:damage]>0 }
          return false if useful
        end
      end
      return false unless @battle.pbRegisterSwitch(user.index,best[:party])
      state[:last_switch] ||= {}; state[:last_switch][user.index]=@battle.turnCount
      state[:plans] ||= {}; state[:plans][user.index]={turn:@battle.turnCount,party:best[:party]}
      BlueRadicalAI.trace('SWITCH',{turn:@battle.turnCount,user:user.index,party:best[:party],current:current,candidate:best,perish:perish})
      true
    end
  end

  def self.install
    unless @installed
      const_set(:BASE_SCORER,Battle::AI.instance_method(:pbGetMoveScore))
      const_set(:BASE_ENUMERATOR,Battle::AI.instance_method(:pbGetMoveScores))
      @installed=true
    end
    Battle::AI::AITrainer.prepend(TrainerSkill) unless Battle::AI::AITrainer.ancestors.include?(TrainerSkill)
    Battle::Battler.prepend(BlankBattler) unless Battle::Battler.ancestors.include?(BlankBattler)
    Battle::AI.prepend(Decisions) unless Battle::AI.ancestors.include?(Decisions)
  end
end
# Use the same late compiler chain as the project's other installers. A prepend
# here can be captured by a later plugin's alias and recursively call itself.
module Compiler
  class << self
    alias blue_radical_original_main main
    def main
      blue_radical_original_main
      BlueRadicalAI.install
    end
  end
end
