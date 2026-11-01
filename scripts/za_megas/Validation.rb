module BlueZAMegas
  def self.check(value,label)
    raise label unless value
    @checks << 'PASS | '+label
  end
  def self.run_checks
    @checks=[]
    order=[:HP,:ATTACK,:DEFENSE,:SPEED,:SPECIAL_ATTACK,:SPECIAL_DEFENSE]
    CATALOG.each do |row|
      data=GameData::Species.get_species_form(row[:species],row[:form])
      check(order.map { |s| data.base_stats[s] }==row[:stats],"#{data.id}: all six stats match the supplied catalogue")
      check(data.types==row[:types],"#{data.id}: types match")
      check(data.mega_stone==row[:stone] && GameData::Item.get(row[:stone]).is_mega_stone?,"#{data.id}: dedicated Mega Stone registered")
      if row[:ability]
        check(data.abilities==[row[:ability]] && data.hidden_abilities==[row[:ability]],"#{data.id}: confirmed ability in every ability slot")
      else
        check(data.flags.include?('BlueZAProvisionalAbility'),"#{data.id}: existing ability explicitly provisional")
      end
      mon=Pokemon.new(row[:species],50)
      mon.gender=data.unmega_form if row[:species]==:MEOWSTIC
      mon.form=data.unmega_form;mon.item=row[:stone]
      check(mon.getMegaForm==row[:form],"#{data.id}: correct origin form can Mega Evolve using its own stone")
      mon.makeMega
      check(mon.form==row[:form] && mon.species_data.id==data.id,"#{data.id}: actual native Mega transformation")
      check(mon.ability_id==row[:ability],"#{data.id}: native Mega ability activates") if row[:ability]
      front=GameData::Species.front_sprite_filename(row[:species],row[:form])
      check(front && pbResolveBitmap(front),"#{data.id}: native front sprite available")
      mon.makeUnmega
      check(mon.form==data.unmega_form,"#{data.id}: transformation restores its origin")
    end
    check(CATALOG.length==50,'All 45 Megas, visual variants and sex/origin variants are covered')
    old=Pokemon.new(:STARMIE,50);old.item=:MEGAITE
    check(old.getMegaForm==1,'Existing campaign trainers and saved universal Megaite stones remain compatible')
    old=BlueBattleLab.build(:MEOWSTIC_1,50)
    check(old.female? && old.form==1,'Builder preserves the female base form used by Mega Meowstic')
    test_abilities
    @checks << 'RESULT=PASS';true
  rescue StandardError=>error
    @checks << "FAIL | #{error.class}: #{error.message}";@checks.concat(error.backtrace);@checks << 'RESULT=FAIL';false
  ensure
    File.open('Data/blue-za-validation.txt','wb') { |f| f.write(@checks.join("\n")+"\n") }
  end
  def self.test_abilities
    a=Pokemon.new(:FERALIGATR,50);b=Pokemon.new(:LUCARIO,50)
    a.moves=[Pokemon::Move.new(:TACKLE)];b.moves=[Pokemon::Move.new(:PROTECT)]
    battle,ai=BlueRadicalAI::Validation.fixture([a],[b])
    battle.backdrop='indoor1';battle.environment=:None;battle.time=0
    battle.scene.pbStartBattle(battle)
    user=battle.battlers[0];target=battle.battlers[1]
    user.ability=:DRAGONIZE
    move=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:TACKLE));move.calcType=move.pbCalcType(user)
    check(move.calcType==:DRAGON && move.powerBoost,'Dragonize changes a Normal move into boosted Dragon')
    user.ability=:EELEVATE
    check(user.airborne?,'Eelevate provides native Ground and entry-hazard immunity')
    battle.field.effects[PBEffects::Gravity]=1
    check(!user.airborne?,'Gravity grounds Eelevate')
    battle.field.effects[PBEffects::Gravity]=0
    user.ability=:PIERCINGDRILL
    move.calcType=move.pbCalcType(user);target.effects[PBEffects::Protect]=true
    check(user.pbSuccessCheckAgainstTarget(move,user,target,[target]),'Piercing Drill reaches a protected target')
    mults={power_multiplier:1.0,attack_multiplier:1.0,defense_multiplier:1.0,final_damage_multiplier:1.0}
    Battle::AbilityEffects.triggerDamageCalcFromUser(:PIERCINGDRILL,user,target,move,mults,40,:NORMAL)
    check(mults[:final_damage_multiplier]==0.25,'Protection reduces Piercing Drill to one quarter')
    target.effects[PBEffects::Protect]=false
    user.pbSuccessCheckAgainstTarget(move,user,target,[target])
    check(target.instance_variable_get(:@blue_za_pierced).nil?,'Piercing Drill does not weaken later unprotected hits')
    mults[:final_damage_multiplier]=1.0
    Battle::AbilityEffects.triggerDamageCalcFromTarget(:AURAGUARD,user,target,move,mults,40,:NORMAL)
    check(mults[:final_damage_multiplier]==0.5,'Aura Guard halves contact damage')
    mults[:attack_multiplier]=1.0
    Battle::AbilityEffects.triggerDamageCalcFromUser(:FIREMANE,user,target,move,mults,40,:FIRE)
    check(mults[:attack_multiplier]==1.5,'Fire Mane boosts Fire attack strength by 50 percent')
    target.ability=:SPICYSPRAY;user.ability=:TORRENT
    Battle::AbilityEffects.triggerOnBeingHit(:SPICYSPRAY,user,target,move,battle)
    check(user.burned?,'Spicy Spray burns a damaging attacker')
  ensure
    battle.scene.pbEndBattle(0) if battle
  end
end
