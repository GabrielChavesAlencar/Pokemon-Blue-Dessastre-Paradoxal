# Actual compiled trainers, EV order and held Mega Stones, inside the native engine.
module BlueFullPowerValidation
  def self.run
    lines=[]
    path='Plugins/ZZZZ Blue Story and Presentation/leader-teams.tsv'
    raise 'Full-power leader manifest was not installed' unless File.file?(path)
    stats=[:HP,:ATTACK,:DEFENSE,:SPEED,:SPECIAL_ATTACK,:SPECIAL_DEFENSE]
    rows=File.readlines(path,chomp:true).map { |line| line.split("\t") }
    raise 'Expected 18 full-power replacements' unless rows.length==18
    rows.each do |leader,species,nature,ability,item,evs,ivs,moves,old|
      matches=[];GameData::Trainer.each { |t| matches << t if t.real_name==leader+' (2v2 Full Power)' }
      raise 'Ambiguous compiled trainer: '+leader unless matches.length==1
      trainer=matches.first.to_trainer
      raise 'Full-power team size changed: '+leader unless trainer.party.length==6
      found=trainer.party.select { |p| p.species==species.to_sym && p.form==0 }
      raise 'Wrong replacement: '+leader unless found.length==1 && trainer.party.none? { |p| p.species==old.to_sym }
      pkmn=found.first
      raise 'Wrong moves/nature/item: '+leader unless pkmn.moves.map(&:id)==moves.split(',').map(&:to_sym) && pkmn.nature_id==nature.to_sym && pkmn.item_id==item.to_sym
      raise 'Wrong ability: '+leader unless pkmn.ability_index==ability.to_i && pkmn.ability
      raise 'EV field order/distribution mismatch: '+leader unless stats.map { |s| pkmn.ev[s] }==evs.split(',').map(&:to_i)
      raise 'IV field order mismatch: '+leader unless stats.map { |s| pkmn.iv[s] }==ivs.split(',').map(&:to_i)
      raise 'Invalid EV total: '+leader unless pkmn.ev.values.sum<=510 && pkmn.ev.values.all? { |n| n<=252 }
      lines << 'PASS | '+leader+' / '+pkmn.name+' / '+item+' / EVs and moves exact'
      if leader=='Reva'
        raise 'Ludicolo cannot Mega Evolve with its own stone' unless pkmn.getMegaForm==1
        pkmn.makeMega
        raise 'Ludicolo Mega form failed' unless pkmn.mega? && pkmn.form==1
        lines << 'PASS | Ludicolo transforms to its author Mega form with DPLUDICOLOITE'
      elsif leader=='Cethin'
        arbok=trainer.party.find { |p| p.species==:ARBOK }
        raise 'Arbok stone/eligibility mismatch' unless arbok && arbok.item_id==:DPARBOKITE && arbok.getMegaForm==1
        arbok.makeMega
        raise 'Arbok Mega form failed' unless arbok.mega? && arbok.form==1
        lines << 'PASS | Arbok transforms to its author Mega form with DPARBOKITE'
      end
    end
    lines << 'RESULT=PASS';true
  rescue StandardError=>error
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace || []);lines << 'RESULT=FAIL';false
  ensure
    File.open('Data/blue-full-power-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
  end
end
