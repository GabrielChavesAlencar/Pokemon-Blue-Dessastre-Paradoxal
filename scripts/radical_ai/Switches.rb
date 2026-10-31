module BlueRadicalAI
  class Snapshot
    def hazard_damage(candidate)
      return 0 if candidate.hasActiveAbility?(:MAGICGUARD) || candidate.hasActiveItem?(:HEAVYDUTYBOOTS)
      side=candidate.pbOwnSide.effects
      total=0
      if side[PBEffects::StealthRock]
        modifier=Effectiveness.calculate(:ROCK,*candidate.pbTypes(true)).to_f / Effectiveness::NORMAL_EFFECTIVE_MULTIPLIER
        total += (candidate.totalhp * modifier / 8).floor
      end
      layers=side[PBEffects::Spikes]
      total += (candidate.totalhp / [8,6,4][layers-1]).floor if layers > 0 && !candidate.airborne?
      total
    end

    def evaluate_candidate(user,party_index=nil)
      hazard=party_index ? hazard_damage(user) : 0
      hp=user.hp-hazard
      return {party:party_index,score:-10_000+hp,hazards:hazard,entry_hp:hp,incoming:0,outgoing:0,safe:false,reasons:{lethal_hazards:true}} if hp <= 0
      user.hp=hp if party_index
      weights=CONFIG['switchWeights']
      threats=incoming(user)
      incoming_damage=threats.sum { |x| x[:hit][:damage] }
      outgoing=[]
      foes(user.index).each do |target|
        legal_moves(user).reject(&:statusMove?).each do |move|
          hit=damage(user,target,move)
          outgoing << {target:target,move:move,hit:hit,first:acts_first?(user,target,hit[:priority])}
        end
      end
      score=100.0; reasons={}
      max_out=outgoing.map { |x| x[:hit][:damage] }.max || 0
      ko=outgoing.any? { |x| x[:hit][:damage]*0.85 >= x[:target].hp && x[:hit][:accuracy]>=95 }
      revenge=outgoing.any? { |x| x[:first] && x[:hit][:damage]*0.85 >= x[:target].hp && x[:hit][:accuracy]>=95 }
      faster=foes(user.index).all? { |target| acts_first?(user,target) }
      if ko; score+=weights['ko']; reasons[:ko]=weights['ko']; end
      if revenge; score+=weights['revenge']; reasons[:revenge]=weights['revenge']; end
      if faster; score+=weights['faster']; reasons[:speed]=weights['faster']; end
      if incoming_damage <= hp/4
        score+=weights['resistAll']; reasons[:defensive_wall]=weights['resistAll']
      elsif incoming_damage <= hp/3
        score+=weights['wall']; reasons[:wall]=weights['wall']
      elsif incoming_damage >= hp
        penalty=faster ? weights['faintsButFaster'] : weights['faints']
        score+=penalty; reasons[:risk_of_ko]=penalty
      else
        score+=weights['weak'] if incoming_damage*2 >= hp
      end
      score+=weights['twoHit'] if outgoing.any? { |x| x[:hit][:damage]*2*0.85 >= x[:target].hp }
      score-=20*hazard.to_f/[user.totalhp,1].max
      if party_index && !user.airborne? && !user.hasActiveItem?(:HEAVYDUTYBOOTS)
        side=user.pbOwnSide.effects
        score-=8 if side[PBEffects::ToxicSpikes]>0 && user.pbCanPoison?(nil,false)
        score-=6 if side[PBEffects::StickyWeb] && !user.hasActiveAbility?([:CLEARBODY,:WHITESMOKE,:FULLMETALBODY,:CONTRARY])
      end
      {party:party_index,score:score.round,hazards:hazard,entry_hp:hp,incoming:incoming_damage,
       outgoing:max_out,safe:incoming_damage < hp,revenge:revenge,reasons:reasons}
    end

    def switch_candidates(index,forced=false)
      trainer=@probe.trainer
      party=@live.pbParty(index)
      _start,finish=@live.pbTeamIndexRangeFromBattlerIndex(index)
      reserved=BlueRadicalAI.memory(@live)[:plans] || {}
      indices=party.each_index.select do |i|
        next false unless @live.pbCanSwitchIn?(index,i)
        next false if reserved.any? { |other,plan| other != index && other%2 == index%2 && plan[:turn]==@live.turnCount && plan[:party]==i }
        true
      end
      if trainer.has_skill_flag?('UsePokemonInOrder')
        indices=indices.first ? [indices.first] : []
      end
      options=indices.map { |i| evaluate_candidate(reserve(index,i),i) }
      if trainer.has_skill_flag?('ReserveLastPokemon') && options.length>1
        others=options.reject { |x| x[:party]==finish-1 }
        options=others if others.any? { |x| x[:entry_hp]>0 && (forced || x[:safe]) }
      end
      options
    end
  end
end
