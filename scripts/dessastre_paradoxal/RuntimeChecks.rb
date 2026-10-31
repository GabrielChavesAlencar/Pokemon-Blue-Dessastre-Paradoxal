module BlueDessastreParadoxal
  EXPECTED_SPECIES = [
[:CAVEFANG,0,[85, 130, 65, 155, 50, 85],[:POISON,:DARK]],
[:ABYSSLURE,0,[152, 48, 48, 80, 116, 126],[:WATER,:FAIRY]],
[:ANCESTRASH,0,[120, 130, 130, 50, 50, 90],[:POISON,:GROUND]],
[:BURIALGAZE,0,[60, 70, 150, 40, 100, 150],[:GHOST,:GROUND]],
[:CRAGGYSIPHON,0,[90, 145, 70, 50, 145, 70],[:WATER,:FIGHTING]],
[:DIRERUFF,0,[100, 150, 90, 120, 40, 70],[:DARK,:GROUND]],
[:DREADCREST,0,[133, 40, 45, 90, 146, 116],[:FLYING,:GROUND]],
[:FETIDGULLET,0,[120, 83, 107, 30, 123, 107],[:POISON,:GHOST]],
[:FOSSILHUSK,0,[95, 125, 180, 30, 50, 90],[:BUG,:ROCK]],
[:FOSSLTIDE,0,[141, 103, 93, 49, 102, 82],[:WATER,:STEEL]],
[:JAGGEDMAW,0,[70, 115, 200, 60, 75, 50],[:WATER,:ROCK]],
[:MIASMIC,0,[80, 70, 145, 80, 115, 80],[:POISON,:DARK]],
[:MIRECREST,0,[123, 133, 77, 94, 62, 81],[:DARK,:FIGHTING]],
[:PHANTOMIRE,0,[65, 45, 55, 145, 185, 75],[:GHOST,:DARK]],
[:PRIAMALGONG,0,[100, 70, 80, 55, 105, 160],[:ICE,:DRAGON]],
[:PRIMALCATERPIE,0,[90, 135, 95, 90, 90, 70],[:BUG,:DRAGON]],
[:PRIMALDRENAW,0,[105, 155, 90, 94, 48, 78],[:WATER,:DRAGON]],
[:PRIMALPUNNY,0,[105, 156, 94, 85, 44, 86],[:GROUND,:FIGHTING]],
[:PRIMALTROPICAL,0,[119, 88, 93, 71, 92, 107],[:GRASS,:DRAGON]],
[:PRIMALDUURR,0,[125, 165, 115, 30, 50, 85],[:FIGHTING,:GROUND]],
[:PRIMALGEOT,0,[93, 110, 85, 121, 81, 80],[:FLYING,:FIGHTING]],
[:PRIMALKORCH,0,[130, 145, 50, 50, 100, 95],[:BUG,:DRAGON]],
[:PRIMALMOTH,0,[90, 55, 55, 120, 140, 110],[:BUG,:ICE]],
[:PRIMALMUK,0,[135, 125, 85, 40, 60, 125],[:POISON,:GROUND]],
[:PRIMALSEAKING,0,[110, 132, 75, 98, 55, 100],[:WATER,:POISON]],
[:PRIMALSECT,0,[90, 135, 140, 20, 85, 100],[:GRASS,:ROCK]],
[:PRIMALVIPER,0,[83, 130, 80, 75, 120, 82],[:POISON,:DRAGON]],
[:PRIMATIZER,0,[81, 93, 108, 49, 140, 99],[:WATER,:ROCK]],
[:RAMPAGEHORN,0,[125, 135, 155, 35, 45, 75],[:ROCK,:DRAGON]],
[:RAVENOUSCREST,0,[105, 160, 95, 75, 55, 80],[:FIGHTING]],
[:RAZORCARAPACE,0,[90, 120, 200, 40, 50, 70],[:STEEL,:DRAGON]],
[:SAVEGEJOWL,0,[110, 170, 95, 45, 70, 80],[:FAIRY,:DARK]],
[:SCORCHMANE,0,[80, 135, 50, 145, 100, 60],[:FIRE,:ELECTRIC]],
[:SCORIASHELL,0,[80, 70, 140, 25, 135, 120],[:FIRE,:STEEL]],
[:THORNBASTION,0,[95, 135, 175, 45, 45, 75],[:GROUND,:ROCK]],
[:TITANBALEEN,0,[190, 115, 110, 50, 65, 40],[:WATER,:STEEL]],
[:WOOLYSTING,0,[90, 120, 115, 120, 40, 85],[:FLYING,:FIGHTING]],
[:IRONCRAWLER,0,[70, 135, 100, 165, 40, 60],[:BUG,:POISON]],
[:IRONCRUSHER,0,[75, 170, 145, 65, 50, 65],[:WATER,:STEEL]],
[:IRONFEASTER,0,[170, 120, 85, 20, 55, 120],[:NORMAL,:STEEL]],
[:IRONINVERNOSE,0,[80, 125, 55, 135, 105, 70],[:FIRE,:STEEL]],
[:IRONLEPORIS,0,[75, 46, 64, 155, 154, 76],[:NORMAL,:ELECTRIC]],
[:IRONMAELTROM,0,[105, 65, 109, 61, 130, 100],[:FLYING,:STEEL]],
[:IRONMATRIARCH,0,[125, 120, 120, 70, 45, 90],[:NORMAL,:STEEL]],
[:ARCHGUTOR,0,[120, 105, 105, 35, 135, 90],[:GRASS,:PSYCHIC]],
[:DYNAMOTRODE,0,[60, 40, 80, 165, 130, 80],[:ELECTRIC,:STEEL]],
[:MAGNETRIX,0,[65, 60, 60, 120, 145, 80],[:STEEL,:ELECTRIC]],
[:MAGISCALE,0,[100, 50, 65, 75, 115, 130],[:WATER,:PSYCHIC]],
[:AMMNOID,0,[65, 75, 105, 70, 100, 80],[:ROCK,:PSYCHIC]],
[:CEPHALONID,0,[70, 90, 105, 80, 120, 85],[:ROCK,:PSYCHIC]],
[:STUNDRIFT,0,[129, 76, 104, 22, 101, 109],[:GROUND,:ELECTRIC]],
[:SWADLOADNE,0,[90, 60, 120, 35, 100, 95],[:GRASS,:BUG]],
[:TENTACRUEL,1,[80, 80, 85, 120, 100, 150],[:WATER,:POISON]],
[:SUNFLORA,1,[75, 85, 75, 20, 155, 115],[:GRASS,:FAIRY]],
[:ARBOK,1,[60, 135, 89, 100, 65, 99],[:POISON,:DRAGON]],
[:FEAROW,1,[65, 130, 78, 127, 61, 81],[:FLYING,:POISON]],
[:HYPNO,1,[85, 113, 90, 57, 103, 135],[:PSYCHIC,:FAIRY]],
[:KABUTOPS,1,[60, 155, 75, 130, 95, 80],[:ROCK,:STEEL]],
[:LEDIAN,1,[55, 80, 65, 125, 55, 110],[:BUG,:FIGHTING]],
[:LUDICOLO,1,[80, 50, 100, 90, 140, 120],[:WATER,:GRASS]],
[:MILTANK,1,[95, 90, 155, 95, 40, 95],[:NORMAL,:FIGHTING]],
[:PURUGLY,1,[71, 104, 94, 120, 84, 79],[:NORMAL,:DARK]],
[:VILEPLUME,1,[75, 70, 135, 40, 130, 140],[:GRASS,:POISON]],
[:WALREIN,1,[110, 110, 140, 55, 105, 110],[:ICE,:ROCK]]
  ]
  PENDING = [:HORSAND,:SPINEDRA,:STINGDRA,:GILLBLE,:GALBITE,:GARCHOLT,:PRIMALNOTIC]
  def self.run_checks
    lines=[]
    check=proc { |label,ok| lines << "#{ok ? 'PASS' : 'FAIL'} | #{label}"; raise label unless ok }
    order=[:HP,:ATTACK,:DEFENSE,:SPEED,:SPECIAL_ATTACK,:SPECIAL_DEFENSE]
    EXPECTED_SPECIES.each do |species,form,stats,types|
      data=GameData::Species.get_species_form(species,form)
      check.call("#{species},#{form} stats",order.map { |s| data.base_stats[s] }==stats)
      check.call("#{species},#{form} types",data.types==types)
      check.call("#{species},#{form} generation",data.generation_label==NAME)
      check.call("#{species},#{form} description",data.pokedex_entry=='????')
    end
    PENDING.each { |id| check.call("#{id} draft excluded from battle catalog",!GameData::Species.try_get(id)) }
    EXPECTED_SPECIES.each do |species,form,stats,types|
      next if form==0
      mon=Pokemon.new(species,50,$player,true,false)
      mon.item=('DP'+species.to_s+'ITE').to_sym
      check.call("#{species} mega stone",mon.getMegaForm==form)
    end
    check.call('Laboratory has Mega Ring',$bag.has?(:MEGARING))
    {EXEGGUTOR: :ARCHGUTOR,ELECTRODE: :DYNAMOTRODE,MAGNETON: :MAGNETRIX,MAGIKARP: :MAGISCALE,OMANYTE: :AMMNOID,AMMNOID: :CEPHALONID,STUNFISK: :STUNDRIFT,SWADLOON: :SWADLOADNE}.each do |from,to|
      check.call("Evolution #{from} -> #{to}",GameData::Species.get(from).evolutions.any? { |e| e[0]==to })
    end
    arbok=Pokemon.new(:ARBOK,50,$player,true,false);arbok.item=:DPARBOKITE
    opponent=Pokemon.new(:PIKACHU,50,$player,true,false)
    mega_battle=Battle.new(Battle::DebugSceneNoVisuals.new,[arbok],[opponent],[$player],nil)
    mega_actor=Battle::Battler.new(mega_battle,0);mega_actor.pbInitialize(arbok,0);mega_battle.battlers[0]=mega_actor
    check.call('Arbok can activate the custom Mega Evolution',mega_battle.pbCanMegaEvolve?(0))
    arch=Pokemon.new(:ARCHGUTOR,50,$player,true,false);arch.ability=:MEGASOL
    rival=Pokemon.new(:PIKACHU,50,$player,true,false)
    battle=Battle.new(Battle::DebugSceneNoVisuals.new,[arch],[rival],[$player],nil)
    actor=Battle::Battler.new(battle,0);actor.pbInitialize(arch,0);battle.battlers[0]=actor
    target=Battle::Battler.new(battle,1);target.pbInitialize(rival,0);battle.battlers[1]=target
    check.call('Mega Sol does not create field weather',battle.field.weather==:None)
    check.call('Mega Sol outside own move',actor.effectiveWeather==:None)
    sun=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:SOLARBEAM))
    fire=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:EMBER))
    BlueDessastreParadoxal.with_move_user(battle,actor) do
      check.call('Mega Sol personal sun',actor.effectiveWeather==:Sun)
      check.call('Other Pokemon does not receive personal sun',target.effectiveWeather==:None)
      check.call('Solar Beam without charging',sun.pbIsChargingTurn?(actor)==false)
      multipliers={power_multiplier:1.0,attack_multiplier:1.0,defense_multiplier:1.0,final_damage_multiplier:1.0}
      fire.pbCalcDamageMults_Weather(actor,target,1,:FIRE,40,multipliers)
      check.call('Own Fire move sun multiplier',multipliers[:final_damage_multiplier]==1.5)
      actor.effects[PBEffects::GastroAcid]=true
      check.call('Suppressed ability has no personal sun',actor.effectiveWeather==:None)
      actor.effects[PBEffects::GastroAcid]=false
    end
    BlueDessastreParadoxal.with_move_user(battle,target) do
      multipliers={power_multiplier:1.0,attack_multiplier:1.0,defense_multiplier:1.0,final_damage_multiplier:1.0}
      fire.pbCalcDamageMults_Weather(target,actor,1,:FIRE,40,multipliers)
      check.call('Incoming Fire receives no Mega Sol boost',multipliers[:final_damage_multiplier]==1.0)
    end
    check.call('Field weather remains unchanged',battle.field.weather==:None)
    check.call('Move context cleared',battle.instance_variable_get(:@blue_dp_move_user).nil?)
    check.call('Fast Ball supports author evolution',GameData::Item.get(:FASTBALL).is_evolution_stone?)
    check.call('Official Bulbasaur preserved',order.map { |s| GameData::Species.get(:BULBASAUR).base_stats[s] }==[45,49,49,45,65,65])
    lines << 'RESULT=PASS'
    true
  rescue StandardError => error
    lines << "RESULT=FAIL | #{error.class}: #{error.message}"
    lines.concat(error.backtrace || [])
    false
  ensure
    File.binwrite('Data/blue-generation-validation.txt',lines.join("\n")+"\n")
  end
end
