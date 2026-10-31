# Read-only analysis: calculations run on detached battlers, moves and field.
module BlueRadicalAI
  class Snapshot
    attr_reader :battle, :probe, :live
    def initialize(ai)
      @live = ai.battle
      @battle = @live.dup
      @battle.instance_variable_set(:@choices, Array.new(@live.battlers.length) { [:None,0,nil,-1] })
      [:field,:sides,:positions].each do |name|
        value = @live.instance_variable_get("@#{name}")
        @battle.instance_variable_set("@#{name}", Marshal.load(Marshal.dump(value)))
      end
      @battle.instance_variable_set(:@party1, Marshal.load(Marshal.dump(@live.pbParty(0))))
      @battle.instance_variable_set(:@party2, Marshal.load(Marshal.dump(@live.pbParty(1))))
      battlers = @live.battlers.map { |b| b ? copy_battler(b) : nil }
      @battle.instance_variable_set(:@battlers, battlers)
      # Discard cached live actor references and move-dependent priority. The
      # analysis queue is empty, so its order may use only visible speed/state.
      order=battlers.compact.sort_by { |b| [-b.pbSpeed,b.index] }
      order.reverse! if @battle.field.effects[PBEffects::TrickRoom]>0
      @battle.instance_variable_set(:@priority,order.map { |b| [b,b.pbSpeed,0,0,0,0,-b.index] })
      @probe = Battle::AI.new(@battle)
      @probe.instance_variable_set(:@blue_rr_probe, true)
      @battle.instance_variable_set(:@battleAI,@probe)
      @probe.instance_variable_set(:@trainer,ai.trainer)
      @probe.instance_variable_set(:@blue_rr_snapshot,self)
      @wrappers = battlers.each_index.map { |i| battlers[i] ? Battle::AI::AIBattler.new(@probe,i) : nil }
      @probe.instance_variable_set(:@battlers,@wrappers)
      @probe.instance_variable_set(:@user,@wrappers[ai.user.index]) if ai.user
      @probe.instance_variable_set(:@move,Battle::AI::AIMove.new(@probe))
      @damage_cache = {}
    end

    def copy_battler(source)
      copy = source.dup
      source.instance_variables.each do |key|
        value = source.instance_variable_get(key)
        if value.is_a?(Array) || value.is_a?(Hash)
          copy.instance_variable_set(key,value.dup)
        end
      end
      copy.instance_variable_set(:@battle,@battle)
      copy.instance_variable_set(:@pokemon,Marshal.load(Marshal.dump(source.pokemon))) if source.pokemon
      copy.instance_variable_set(:@damageState,source.damageState.dup)
      copy.instance_variable_set(:@moves,source.moves.map do |move|
        dup = move.dup
        dup.instance_variable_set(:@battle,@battle)
        real=move.instance_variable_get(:@realMove)
        dup.instance_variable_set(:@realMove,Marshal.load(Marshal.dump(real))) if real
        dup
      end)
      copy
    end

    def battler(index); @battle.battlers[index]; end
    def replace_battler(value)
      @battle.battlers[value.index]=value
      @wrappers[value.index].refresh_battler
      @battle.instance_variable_get(:@priority).each do |entry|
        next unless entry[0].index==value.index
        entry[0]=value;entry[1]=value.pbSpeed
      end
    end
    def foes(index); @battle.allOtherSideBattlers(index).to_a.reject(&:fainted?); end
    def allies(index); @battle.allSameSideBattlers(index).to_a.reject { |b| b.index == index || b.fainted? }; end

    def with_context(user, target, move)
      previous = [@probe.user,@probe.target,@probe.move,@battle.moldBreaker,@wrappers[user.index],target && @wrappers[target.index]]
      old_user = @battle.battlers[user.index]
      old_target = target && @battle.battlers[target.index]
      @battle.battlers[user.index] = user
      @battle.battlers[target.index] = target if target
      uw = Battle::AI::AIBattler.new(@probe,user.index)
      tw = target ? Battle::AI::AIBattler.new(@probe,target.index) : nil
      @probe.instance_variable_set(:@user,uw)
      @probe.instance_variable_set(:@target,tw)
      @wrappers[user.index] = uw
      @wrappers[target.index] = tw if target
      am = Battle::AI::AIMove.new(@probe)
      @probe.instance_variable_set(:@move,am)
      @battle.moldBreaker = uw.has_mold_breaker?
      analysis_move=move.dup
      analysis_move.instance_variable_set(:@battle,@battle)
      am.set_up(analysis_move)
      # Mega Sol is a personal sun context even while calculating AI damage.
      if defined?(BlueDessastreParadoxal)
        BlueDessastreParadoxal.with_move_user(@battle,user) { yield am,uw,tw }
      else
        yield am,uw,tw
      end
    ensure
      if previous
        @probe.instance_variable_set(:@user,previous[0])
        @probe.instance_variable_set(:@target,previous[1])
        @probe.instance_variable_set(:@move,previous[2])
        @battle.moldBreaker = previous[3]
        @battle.battlers[user.index] = old_user
        @battle.battlers[target.index] = old_target if target
        @wrappers[user.index] = previous[4]
        @wrappers[target.index] = previous[5] if target
      end
    end

    def legal_moves(user)
      previous = @battle.battlers[user.index]
      @battle.battlers[user.index] = user
      user.moves.each_with_index.select { |move,i| @battle.pbCanChooseMove?(user.index,i,false) }.map(&:first)
    ensure
      @battle.battlers[user.index] = previous
    end

    def damage(user, target, move)
      key = [user.object_id,target.object_id,move.object_id]
      return @damage_cache[key] if @damage_cache.key?(key)
      result = with_context(user,target,move) do |am,uw,tw|
        fail = @probe.pbPredictMoveFailure || @probe.pbPredictMoveFailureAgainstTarget
        if fail || move.statusMove?
          {damage:0,accuracy:0,priority:am.rough_priority(uw),immune:fail}
        else
          value = am.rough_damage
          if value >= target.hp && target.hp == target.totalhp && !move.multiHitMove?
            sash = target.hasActiveItem?(:FOCUSSASH)
            sturdy = target.hasActiveAbility?(:STURDY) && !uw.has_mold_breaker? && !move.function_code.include?('IgnoreTargetAbility')
            value = target.hp - 1 if sash || sturdy
          end
          accuracy = am.rough_accuracy
          accuracy = 100 if accuracy == 0
          {damage:[value,0].max,accuracy:accuracy.clamp(0,100),priority:am.rough_priority(uw),immune:false}
        end
      end
      @damage_cache[key] = result
    end

    def baseline(user,move,targets)
      with_context(user,targets&.first,move) do
        if @probe.respond_to?(:aai_pbGetMoveScore,true)
          @probe.send(:aai_pbGetMoveScore,targets)
        else
          BlueRadicalAI::BASE_SCORER.bind(@probe).call(targets)
        end
      end
    end

    def incoming(user)
      foes(user.index).map do |foe|
        options=legal_moves(foe).reject(&:statusMove?).map { |move| [move,damage(foe,user,move)] }
        pair=options.max_by { |move,hit| hit[:damage] * hit[:accuracy] / 100.0 }
        {foe:foe,move:pair&.first,hit:pair ? pair.last : {damage:0,accuracy:0,priority:0,immune:false}}
      end
    end

    def acts_first?(user,target,priority=0,other_priority=0)
      return priority > other_priority if priority != other_priority
      fast=user.pbSpeed; slow=target.pbSpeed
      return false if fast == slow
      (fast > slow) ^ (@battle.field.effects[PBEffects::TrickRoom] > 0)
    end

    def reserve(index,party_index)
      template=battler(index)
      copy=copy_battler(template)
      pokemon=Marshal.load(Marshal.dump(@live.pbParty(index)[party_index]))
      copy.pbInitPokemon(pokemon,party_index)
      copy.instance_variable_set(:@effects,template.instance_variable_get(:@blue_rr_blank_effects).dup)
      stages={}; GameData::Stat.each_battle { |s| stages[s.id]=0 }
      copy.instance_variable_set(:@stages,stages)
      copy.instance_variable_set(:@turnCount,0)
      copy.instance_variable_set(:@lastMoveUsed,nil)
      copy.instance_variable_set(:@lastRegularMoveUsed,nil)
      copy.instance_variable_set(:@fainted,false)
      copy
    end

    def mega(user)
      pokemon=Marshal.load(Marshal.dump(user.pokemon))
      pokemon.makeMega
      copy=copy_battler(user)
      copy.pbInitPokemon(pokemon,user.pokemonIndex)
      copy
    end
  end
end
