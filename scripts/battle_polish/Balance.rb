# Prices are Blue balance tiers anchored to the original retail ranges.
module BlueCampaign
  EQUIPMENT_PRICES={MEGARING:15_000,ZRING:15_000,ZPOWERRING:15_000,TERAORB:20_000,DYNAMAXBAND:20_000,
    POKEMONBOXLINK:12_000,ADVENTUREGUIDE:500,SOUNDTRACKEARBUDS:1_000,BICYCLE:5_000,
    OLDROD:1_000,GOODROD:5_000,SUPERROD:15_000,ITEMFINDER:3_000,DOWSINGMACHINE:3_000,POKERADAR:15_000,TOWNMAP:500,
    ABILITYVIAL:25_000,MASTERTERAJEWEL:30_000,HIDDENORB:15_000,VIALOFGLITTER:50_000,SUPERVIAL:75_000,
    PORTABLEWARDROBE:2_000,REPELCHARM:10_000,DYNAMAXINHIBITOR:1_000,
    OVALCHARM:20_000,SHINYCHARM:80_000,CATCHINGCHARM:30_000,EXPCHARM:40_000,MARKCHARM:30_000,GLIMMERINGCHARM:50_000,
    EXPALL:20_000,MAXSOUP:20_000}.freeze
  # Emerald prices span roughly 1,000-5,500; reusable powerful TMs cost more here.
  # https://github.com/pret/pokeemerald/blob/master/src/data/items.h
  def self.machine_price(item)
    move=GameData::Move.try_get(item.move)
    return 1_000 unless move
    power=move.base_damage
    value=if move.category==2
      move.function_code.match?(/Heal|Protect|Substitute|RaiseUser.*[2-9]|Spikes|StealthRock|Tailwind|TrickRoom/) ? 5_000 : 2_500
    elsif power<=40 then 500
    elsif power<=60 then 1_500
    elsif power<=80 then 3_000
    elsif power<=100 then 4_500
    elsif power<=120 then 5_500
    else 7_500
    end
    value=7_500 if power<=1 && move.category!=2 # Variable/fixed damage is not a weak attack.
    item.is_TR? ? (value*0.7/100).ceil*100 : value
  end
end
module BlueTrainerMoves
  CAPS=[60,90,nil,nil].freeze
  VOLATILE=%w[FISSURE GUILLOTINE HORNDRILL SHEERCOLD DESTINYBOND FINALGAMBIT ENDEAVOR SUPERFANG NATURESMADNESS RUINATION
    DRAGONRAGE SONICBOOM COUNTER MIRRORCOAT METALBURST BIDE RETURN FRUSTRATION FLAIL REVERSAL ERUPTION WATERSPOUT
    DRAGONENERGY CRUSHGRIP WRINGOUT LOWKICK GRASSKNOT HEAVYSLAM HEATCRASH GYROBALL ELECTROBALL STOREDPOWER POWERTRIP
    FURYCUTTER ROLLOUT ICEBALL BEATUP TRUMPCARD PRESENT MAGNITUDE FLING NATURALGIFT LASTRESPECTS RAGEFIST
    METRONOME ASSIST COPYCAT MIRRORMOVE MEFIRST MIMIC SKETCH SLEEPTALK NATUREPOWER TRANSFORM].freeze
  def self.safe?(id,cap,battle)
    data=GameData::Move.get(id)
    return false if data.base_damage>cap || VOLATILE.include?(id.to_s)
    code=data.function_code
    return false if code.match?(/OHKO|Reset.*StatStages|Swap.*StatStages|Copy.*StatStages|Invert.*StatStages|Steal.*StatStages/)
    @effects ||= {}
    effects=(@effects[id] ||= begin
      move=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(id))
      [move.instance_variable_get(:@statUp),move.instance_variable_get(:@statDown)].compact
    end)
    return false if effects.any? { |a| a.each_slice(2).sum { |stat,n| n.to_i.abs }>1 }
    return false if code.match?(/(?:Raise|Lower).*?(?:[2-9]|Max)/)
    if code.match?(/Raise|Lower/)
      return false if code.match?(/MainStats|AllStats/) || code.scan(/SpAtk|SpDef|Speed|Atk|Def|Spd|Spe|Acc|Eva/).uniq.length>1
    end
    true
  rescue StandardError
    false # A custom move whose effect cannot be inspected is not an early-game fallback.
  end
  def self.role(data)
    code=data.function_code
    return :heal if code.match?(/Heal|Recover|RestoreUserHP/)
    return :boost if code.start_with?('Raise')
    return :drop if code.start_with?('Lower')
    return :protect if code.match?(/Protect|Endure/)
    return :ailment if code.match?(/Burn|Poison|Paraly|Sleep|Confuse/)
    data.category==2 ? :status : :damage
  end
  def self.adjust(pkmn,cap,battle)
    data=pkmn.species_data
    legal=(data.moves.select { |level,id| level<=pkmn.level }.map(&:last)+data.tutor_moves).uniq
    pool=legal.select { |id| safe?(id,cap,battle) }
    chosen=[]
    pkmn.moves.each do |old|
      original=GameData::Move.get(old.id)
      if pool.include?(old.id) && !chosen.include?(old.id)
        chosen << old.id;next
      end
      candidates=pool-chosen
      pick=candidates.min_by do |id|
        m=GameData::Move.get(id)
        [role(m)==role(original) ? 0 : 1,m.category==original.category ? 0 : 1,m.type==original.type ? 0 : 1,
         m.function_code==original.function_code ? 0 : 1,(m.base_damage-[original.base_damage,cap].min).abs,id.to_s]
      end
      chosen << pick if pick
    end
    chosen=pool.first(1) if chosen.empty?
    pkmn.moves=chosen.first(4).map { |id| Pokemon::Move.new(id) }
    # With no legal candidate the native engine uses Struggle; do not teach an illegal move.
  end
  def self.apply(battle)
    cap=CAPS[BlueStory.stage]
    return unless cap
    battle.pbParty(1).each { |p| adjust(p,cap,battle) }
  end
end
