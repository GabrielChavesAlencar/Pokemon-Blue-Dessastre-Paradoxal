module BlueRadicalAI
  SETUP = [:SWORDSDANCE,:NASTYPLOT,:DRAGONDANCE,:QUIVERDANCE,:SHELLSMASH,:CALMMIND,:BULKUP,:AGILITY,:ROCKPOLISH,:COIL,:GEOMANCY,:BELLYDRUM,:WORKUP,:IRONDEFENSE,:AMNESIA,:VICTORYDANCE,:SHIFTGEAR]
  RECOVERY = [:RECOVER,:ROOST,:SOFTBOILED,:SLACKOFF,:MILKDRINK,:SYNTHESIS,:MORNINGSUN,:MOONLIGHT,:SHOREUP,:REST,:WISH,:HEALORDER,:STRENGTHSAP]
  PROTECT = [:PROTECT,:DETECT,:SPIKYSHIELD,:BANEFULBUNKER,:SILKTRAP,:BURNINGBULWARK,:KINGSSHIELD,:OBSTRUCT]
  HAZARDS = [:STEALTHROCK,:SPIKES,:TOXICSPIKES,:STICKYWEB]
  REMOVAL = [:RAPIDSPIN,:DEFOG,:MORTALSPIN,:TIDYUP,:COURTCHANGE]
  PIVOTS = [:UTURN,:VOLTSWITCH,:FLIPTURN,:PARTINGSHOT,:CHILLYRECEPTION,:TELEPORT,:BATONPASS]

  class Snapshot
    def score_move(user,move,targets)
      targets = targets&.map { |b| battler(b.index) }
      score = baseline(user,move,targets).to_f
      reasons = {engine:score.round}
      return {score:score.round,reasons:reasons} if score <= Battle::AI::MOVE_FAIL_SCORE
      delta = 0.0
      hits = []
      target_list = targets || []
      if move.damagingMove?
        target_list.each do |target|
          hit = damage(user,target,move)
          next if hit[:immune]
          hits << [target,hit]
          if target.opposes?(user)
            fraction = [hit[:damage].to_f / [target.hp,1].max,1.0].min
            add = fraction * 28 * hit[:accuracy] / 100.0
            if hit[:damage] * 0.85 >= target.hp && hit[:accuracy] >= 95
              add += 65
              add += 18 if acts_first?(user,target,hit[:priority])
              reasons[:safe_ko] = target.index
            elsif hit[:damage] >= target.hp
              add += 28 * hit[:accuracy] / 100.0
              reasons[:possible_ko] = target.index
            elsif hit[:damage] * 2 * 0.85 >= target.hp
              add += 10
            end
            add -= (100-hit[:accuracy]) * 0.25
            if BlueRadicalAI.repeated_switches?(@live,target.index)
              history=BlueRadicalAI.memory(@live)[:history][target.index]
              previous=history.reverse.find { |i| i != target.pokemonIndex }
              if previous && @live.pbParty(target.index)[previous] && !@live.pbParty(target.index)[previous].fainted?
                observed=reserve(target.index,previous)
                forecast=damage(user,observed,move)
                coverage=forecast[:immune] ? -10 : 15*[forecast[:damage].to_f/[observed.hp,1].max,1.0].min
                add+=coverage
                reasons[:observed_switch_coverage]=coverage.round
              end
            end
            planned = BlueRadicalAI.memory(@live)[:plans] || {}
            if planned.any? { |index,p| index != user.index && index%2 == user.index%2 && p[:turn] == @live.turnCount && p[:target] == target.index && p[:damage] >= target.hp }
              add -= 45
              reasons[:avoid_overkill] = target.index
            end
            delta += add
          else
            plans = BlueRadicalAI.memory(@live)[:plans] || {}
            protected = plans[target.index] && plans[target.index][:turn] == @live.turnCount && plans[target.index][:protect]
            unless protected
              loss = [hit[:damage].to_f / [target.hp,1].max,1.0].min * 80
              loss += 90 if hit[:damage] >= target.hp
              delta -= loss
              reasons[:friendly_fire] = loss.round
            end
          end
        end
        if !target_list.empty? && hits.empty?
          return {score:Battle::AI::MOVE_FAIL_SCORE,reasons:{no_effect:true}}
        end
        reasons[:damage] = delta.round
      end

      threats = incoming(user)
      incoming_damage = threats.sum { |x| x[:hit][:damage] }
      danger = incoming_damage.to_f / [user.hp,1].max
      before_user = threats.any? { |x| x[:hit][:damage] >= user.hp && !acts_first?(user,x[:foe],0,x[:hit][:priority]) }
      if SETUP.include?(move.id)
        adjustment = before_user ? -115 : danger >= 0.8 ? -65 : danger < 0.35 ? 18 : -12
        delta += adjustment; reasons[:setup_safety] = adjustment
      end
      if RECOVERY.include?(move.id)
        missing = user.totalhp-user.hp
        heal = [missing,user.totalhp/2].min
        adjustment = missing == 0 ? -90 : 12 + 25 * missing.to_f/user.totalhp
        adjustment -= 95 if before_user
        adjustment -= 65 if incoming_damage >= user.hp+heal
        delta += adjustment; reasons[:recovery_timing] = adjustment.round
      end
      if HAZARDS.include?(move.id)
        reserves = @battle.pbParty((user.index+1)%2).compact.count { |p| !p.fainted? } - foes(user.index).length
        bonus = reserves > 0 ? 10 : -20
        bonus += 12 if foes(user.index).any? { |b| BlueRadicalAI.repeated_switches?(@live,b.index) }
        bonus -= 65 if before_user
        delta += bonus; reasons[:hazard_pressure] = bonus
      end
      if REMOVAL.include?(move.id)
        side = user.pbOwnSide.effects
        active = side[PBEffects::Spikes] > 0 || side[PBEffects::ToxicSpikes] > 0 || side[PBEffects::StealthRock] || side[PBEffects::StickyWeb]
        bonus = active ? 22 : 0
        delta += bonus; reasons[:hazard_removal] = bonus if bonus > 0
      end
      if PIVOTS.include?(move.id)
        has_reserve = @battle.pbParty(user.index).each_index.any? { |i| @battle.pbCanSwitchIn?(user.index,i) }
        bonus = has_reserve && danger > 0.3 && danger < 1.0 ? 12 : 0
        delta += bonus; reasons[:pivot] = bonus if bonus > 0
      end
      if [:HEALPULSE,:FLORALHEALING,:POLLENPUFF].include?(move.id) && targets&.length == 1
        target = targets.first
        if !target.opposes?(user)
          bonus = target.hp == target.totalhp ? -95 : 35*(1.0-target.hp.to_f/target.totalhp)
          delta += bonus; reasons[:ally_healing] = bonus.round
        end
      end
      if move.id == :HELPINGHAND
        ally = targets&.first
        useful = ally && !ally.opposes?(user) && !legal_moves(ally).all?(&:statusMove?)
        bonus = useful ? 18 : -100
        delta += bonus; reasons[:ally_support] = bonus
      end
      if [:TAILWIND,:TRICKROOM].include?(move.id)
        own = [user,*allies(user.index)]
        opponents = foes(user.index)
        slow = own.count { |b| opponents.any? { |f| b.pbSpeed < f.pbSpeed } }
        bonus = slow > 0 ? 15*slow : -15
        bonus = -35 if move.id == :TRICKROOM && @battle.field.effects[PBEffects::TrickRoom] > 0
        delta += bonus; reasons[:speed_control] = bonus
      end
      weather = {RAINDANCE: :WATER,SUNNYDAY: :FIRE,SANDSTORM: :ROCK,SNOWSCAPE: :ICE,HAIL: :ICE}[move.id]
      if weather
        own = @battle.pbParty(user.index).compact.reject(&:fainted?)
        synergy = own.count { |p| p.types.include?(weather) }
        bonus = [synergy*5,20].min
        delta += bonus; reasons[:weather_team] = bonus
      end
      if PROTECT.include?(move.id)
        residual = foes(user.index).any? { |b| b.status == :POISON || b.effects[PBEffects::LeechSeed] >= 0 }
        bonus = residual && user.effects[PBEffects::ProtectRate] <= 1 ? 12 : 0
        delta += bonus; reasons[:protect_residual] = bonus if bonus > 0
      end
      strength = BlueRadicalAI.profile(@live)['strength']
      result = [(score + delta * strength).round,0].max
      {score:result,reasons:reasons}
    end
  end
end
