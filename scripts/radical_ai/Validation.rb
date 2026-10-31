# Deterministic battle-state fixtures executed with the installed Essentials.
module BlueRadicalAI
  module Validation
    REPORT='Data/blue-radical-ai-validation.txt'
    class << self
      def assert(value,label)
        raise label unless value
        @lines << "PASS | #{label}"
      end
      def mon(species,moves,level=50)
        pokemon=BlueBattleLab.build(species,level)
        pokemon.ability_index=0
        pokemon.moves=moves.map { |id| Pokemon::Move.new(id) }
        pokemon
      end
      def fixture(allies,foes,format='single',profile='radical')
        trainer=NPCTrainer.new('AI test',$player.trainer_type)
        trainer.party=foes
        battle=Battle.new(BlueBattleLab::SmokeScene.new,allies,foes,[$player],[trainer])
        battle.instance_variable_set(:@blue_radical_profile,profile)
        battle.instance_variable_set(:@blue_radical_rng,Random.new(20261031))
        battle.setBattleMode(format)
        battle.internalBattle=false
        battle.pbEnsureParticipants
        battle.pbSetUpSides
        ai=battle.instance_variable_get(:@battleAI)
        ai.create_ai_objects
        ai.set_up(1)
        [battle,ai]
      end
      def ranked(ai)
        ai.pbGetMoveScores.map { |c| {move:c[4].id,target:c[2],score:c[1]} }
      end
      def score(rows,move)
        rows.select { |r| r[:move]==move }.map { |r| r[:score] }.max || -9999
      end
      def winner(ai)
        choices=ai.pbGetMoveScores
        ai.pbChooseMove(choices)
        chosen=ai.battle.choices[ai.user.index]
        [chosen[2]&.id,chosen[3]]
      end
      def fingerprint(battle)
        Marshal.dump([
          [0,1].map { |side| battle.pbParty(side) },battle.field,battle.sides,battle.positions,
          battle.battlers.map do |b|
            next nil unless b
            [b.hp,b.form,b.ability_id,b.item_id,b.stages,b.effects,b.moves.map { |m| [m.id,m.pp,m.calcType] }]
          end,
          battle.choices,battle.moldBreaker
        ])
      end
      def run
        @lines=[]
        begin
          test_attacks
          test_status_and_setup
          test_switches
          test_doubles
          test_mega_and_state
          test_memory
          @lines << 'RESULT=PASS'
          true
        rescue StandardError => error
          @lines << "FAIL | #{error.class}: #{error.message}"
          @lines.concat(error.backtrace)
          @lines << 'RESULT=FAIL'
          false
        ensure
          File.open(REPORT,'wb') { |f| f.write(@lines.join("\n")+"\n") }
        end
      end

      def test_attacks
        battle,ai=fixture([mon(:GYARADOS,[:SPLASH])],[mon(:PIKACHU,[:THUNDERBOLT,:TACKLE,:NASTYPLOT,:THUNDERWAVE])])
        battle.battlers[0].hp=2
        assert(winner(ai)[0]==:THUNDERBOLT,'Reliable OHKO preferred over setup and status')
        battle,ai=fixture([mon(:DUGTRIO,[:SPLASH])],[mon(:PIKACHU,[:THUNDERBOLT,:TACKLE])])
        assert(winner(ai)[0]==:TACKLE,'Electric immunity avoided')
        battle,ai=fixture([mon(:BLASTOISE,[:SPLASH])],[mon(:PIKACHU,[:THUNDERBOLT,:TACKLE])])
        battle.battlers[1].moves[0].pp=0
        assert(ranked(ai).none? { |x| x[:move]==:THUNDERBOLT },'No-PP move excluded from legal actions')
        battle.battlers[1].moves[1].pp=0
        assert(ai.pbGetMoveScores.empty?,'All empty PP leaves no illegal move candidates')
        ai.pbChooseMove([])
        assert(battle.choices[1][2].id==:STRUGGLE,'Struggle fallback registered')
        battle,ai=fixture([mon(:ALAKAZAM,[:PSYCHIC],80)],[mon(:SCIZOR,[:IRONHEAD,:BULLETPUNCH,:SWORDSDANCE],30)])
        battle.battlers[0].hp=1
        assert(winner(ai)[0]==:BULLETPUNCH,'Priority revenge KO preferred when slower')
        target=mon(:MAGIKARP,[:SPLASH],5);target.item=:FOCUSSASH
        battle,ai=fixture([target],[mon(:PIKACHU,[:THUNDERBOLT],80)])
        snap=ai.instance_variable_get(:@blue_rr_snapshot)
        hit=snap.damage(snap.battler(1),snap.battler(0),snap.battler(1).moves[0])
        assert(hit[:damage]==battle.battlers[0].hp-1,'Full-HP Focus Sash prevents false guaranteed KO')
      end

      def test_status_and_setup
        battle,ai=fixture([mon(:GROUDON,[:EARTHQUAKE],80)],[mon(:PIKACHU,[:TACKLE,:NASTYPLOT],10)])
        rows=ranked(ai)
        assert(score(rows,:TACKLE)>score(rows,:NASTYPLOT),'Suicidal setup penalized under faster OHKO')
        battle,ai=fixture([mon(:BLASTOISE,[:SPLASH])],[mon(:PIKACHU,[:THUNDERWAVE,:TACKLE])])
        battle.battlers[0].instance_variable_set(:@status,:PARALYSIS)
        battle.battlers[0].pokemon.status=:PARALYSIS
        assert(winner(ai)[0]==:TACKLE,'Status already present is not repeated')
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH])],[mon(:ALAKAZAM,[:RECOVER,:PSYCHIC])])
        full=score(ranked(ai),:RECOVER)
        battle.battlers[1].hp=battle.battlers[1].totalhp/4
        ai.set_up(1)
        assert(score(ranked(ai),:RECOVER)>full,'Recovery valued more when HP is missing')
      end

      def test_switches
        charizard=mon(:CHARIZARD,[:FLAMETHROWER]);charizard.hp=1
        battle,ai=fixture([mon(:PIKACHU,[:TACKLE])],[mon(:MAGIKARP,[:SPLASH]),charizard,mon(:BLASTOISE,[:SURF])])
        battle.sides[1].effects[PBEffects::StealthRock]=true
        battle.battlers[1].hp=0
        ai.set_up(1)
        assert(ai.choose_best_replacement_pokemon(1,true)==2,'Forced replacement avoids lethal hazards even for reserved ace')
        snapshot=ai.instance_variable_get(:@blue_rr_snapshot)
        reserve=snapshot.reserve(1,1)
        expected=(reserve.totalhp*0.5).floor
        assert(snapshot.hazard_damage(reserve)==expected,'Stealth Rock uses correct 4x weakness fraction')
        reserve.pokemon.item=:HEAVYDUTYBOOTS
        reserve.item=:HEAVYDUTYBOOTS
        assert(snapshot.hazard_damage(reserve)==0,'Heavy-Duty Boots prevent entry damage')
        locked=mon(:PIKACHU,[:THUNDERBOLT,:TACKLE]);locked.item=:CHOICESPECS
        battle,ai=fixture([mon(:DUGTRIO,[:EARTHQUAKE])],[locked,mon(:LANDORUS,[:EARTHQUAKE])])
        battle.battlers[1].effects[PBEffects::ChoiceBand]=:THUNDERBOLT
        ai.set_up(1)
        assert(ai.pbChooseToSwitchOut,'Choice-locked immunity prompts safe voluntary switch')
        assert(battle.choices[1][0]==:SwitchOut && battle.choices[1][1]==1,'Legal replacement is actually registered')
        battle,ai=fixture([mon(:GROUDON,[:EARTHQUAKE],100)],[mon(:PIKACHU,[:TACKLE],5),mon(:PIKACHU,[:TACKLE],5)])
        assert(!ai.pbChooseToSwitchOut(true),'Voluntary switch rejected when every reserve suffers free OHKO')
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:TACKLE]),mon(:BLASTOISE,[:SURF])])
        battle.battlers[1].effects[PBEffects::PerishSong]=1
        ai.set_up(1)
        assert(ai.pbChooseToSwitchOut,'Perish Song escapes to a safe reserve')
      end

      def test_doubles
        own=[mon(:PIKACHU,[:DISCHARGE,:THUNDERBOLT]),mon(:GYARADOS,[:SPLASH])]
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH]),mon(:MAGIKARP,[:SPLASH])],own,'double')
        battle.battlers[3].hp=1
        risky=score(ranked(ai),:DISCHARGE)
        assert(winner(ai)[0]==:THUNDERBOLT,'Double attack avoids knocking out vulnerable ally')
        battle2,ai2=fixture([mon(:MAGIKARP,[:SPLASH]),mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:DISCHARGE,:THUNDERBOLT]),mon(:GARCHOMP,[:SPLASH])],'double')
        assert(score(ranked(ai2),:DISCHARGE)>risky,'Spread attack improves when ally is immune')
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH]),mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:HELPINGHAND,:TACKLE]),mon(:BLASTOISE,[:SURF])],'double')
        helpers=ranked(ai).select { |r| r[:move]==:HELPINGHAND }
        assert(!helpers.empty? && helpers.all? { |r| r[:target]==3 },'Helping Hand targets teammate only')
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH]),mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:THUNDERBOLT]),mon(:PIKACHU,[:THUNDERBOLT])],'double')
        battle.battlers[0].hp=1;battle.battlers[2].hp=1
        first=winner(ai)[1]
        ai.set_up(3)
        second=winner(ai)[1]
        assert(first!=second,'Two AI allies avoid duplicate overkill on same target')
      end

      def test_mega_and_state
        battle,ai=fixture([mon(:BLASTOISE,[:SURF])],[mon(:PIKACHU,[:THUNDERBOLT,:TACKLE,:NASTYPLOT])])
        before=fingerprint(battle)
        scores=ranked(ai)
        assert(fingerprint(battle)==before,'Scoring leaves live HP, PP, items, effects and field unchanged')
        snap=ai.instance_variable_get(:@blue_rr_snapshot)
        assert(snap.battle.pbPriority.all? { |b| !b.equal?(battle.battlers[b.index]) },'Analysis priority order has no live battler references')
        battle.choices[0]=[:SwitchOut,0,nil,-1]
        ai.set_up(1)
        assert(ranked(ai)==scores,'Hidden player switch input does not affect scoring')
        battle.choices[0]=[:UseMove,0,battle.battlers[0].moves[0],1]
        ai.set_up(1)
        assert(ranked(ai)==scores,'Hidden player attack input does not affect scoring')
        values=[{score:100,value:1},{score:100,value:2}]
        battle.instance_variable_set(:@blue_radical_rng,Random.new(17))
        a=Array.new(12) { BlueRadicalAI.best(values,battle)[:value] }
        battle.instance_variable_set(:@blue_radical_rng,Random.new(17))
        assert(a==Array.new(12) { BlueRadicalAI.best(values,battle)[:value] },'Tie-break RNG reproducible with fixed seed')
        if GameData::Species.try_get(:CAVEFANG)
          arbok=mon(:ARBOK,[:CRUNCH]);arbok.item=:DPARBOKITE
          battle,ai=fixture([mon(:MAGIKARP,[:SPLASH])],[arbok])
          snapshot=ai.instance_variable_get(:@blue_rr_snapshot)
          original=fingerprint(battle)
          projected=snapshot.mega(snapshot.battler(1))
          assert(projected.form==1 && projected.pokemon.mega?,'Author Mega projected from actual stone and form')
          assert(projected.pbTypes(true)!=battle.battlers[1].pbTypes(true),'Mega projection recalculates typing')
          assert(fingerprint(battle)==original,'Mega projection never transforms live Pokemon')
        end
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:TACKLE])],'single','engine')
        assert(!BlueRadicalAI.enabled?(battle),'Original engine profile can be selected')
        assert(ai.trainer.skill==battle.opponent.first.skill_level,'Engine profile preserves original trainer skill')
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH])],[mon(:PIKACHU,[:TACKLE])])
        assert(ai.trainer.skill>=100,'Radical profile activates expert flags')
      end

      def test_memory
        battle,ai=fixture([mon(:MAGIKARP,[:SPLASH]),mon(:BLASTOISE,[:SURF])],[mon(:PIKACHU,[:STEALTHROCK,:TACKLE])])
        initial=score(ranked(ai),:STEALTHROCK)
        [1,0,1].each_with_index do |position,i|
          battle.instance_variable_set(:@turnCount,i+1)
          battle.battlers[0].instance_variable_set(:@pokemonIndex,position)
          BlueRadicalAI.observe(battle)
        end
        assert(BlueRadicalAI.repeated_switches?(battle,0),'Observed A-B-A-B switching loop recognized')
        ai.set_up(1)
        assert(score(ranked(ai),:STEALTHROCK)>initial,'Observed switch loop increases hazard pressure')
        battle.pbParty(0)[1].hp=0
        battle.instance_variable_set(:@turnCount,4)
        BlueRadicalAI.observe(battle)
        assert(!BlueRadicalAI.repeated_switches?(battle,0),'Switch-loop memory resets after knockout')
      end
    end
  end
end
