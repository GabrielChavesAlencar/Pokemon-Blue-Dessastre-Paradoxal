# Optional authoritative command worker. Not installed by offline launchers.
module BlueNativeTurns
  DIR='Data/blue-native-turns'
  REQUEST='Data/blue-native-turns-request.txt'
  def self.write(value)
    path=DIR+'/state.json';temp=path+'.tmp'
    File.open(temp,'wb') { |f| f.write(BlueOnlineProbe.json(value)) }
    File.rename(temp,path)
  end
  def self.public_state(battle)
    battle.battlers.compact.map { |b| {index:b.index,side:b.index%2,species:b.species.to_s,form:b.form,hp:b.hp,totalHP:b.totalhp,status:b.status.to_s} }
  end
  def self.ask(battle,index,kind,options)
    raise 'Native worker has no legal command' if options.empty?
    @seq=(@seq || 0)+1
    request={seq:@seq,side:index%2,battler:index,kind:kind,options:options}
    state={protocol:2,state:'choosing',turn:battle.turnCount,active:public_state(battle),messages:battle.scene.messages.last(200),request:request}
    write(state)
    deadline=System.uptime+60
    loop do
      path=DIR+'/command.tsv'
      if File.file?(path)
        raise 'Oversized native command' if File.size(path)>256
        line=File.read(path).strip.split("\t");File.delete(path)
        if line.length==4 && line[0]==@seq.to_s
          selected=options.find { |o| [o[:kind],o[:slot].to_s,o[:target].to_s]==line[1,3] }
          if selected
            @commands << {seq:@seq,side:index%2,kind:selected[:kind],turn:battle.turnCount}
            return selected
          end
        end
      end
      raise 'Remote player did not choose within 60 seconds' if System.uptime>deadline
      Graphics.update;Input.update;sleep 0.01
    end
  end
  class Match < Battle
    def pbCommandPhaseLoop(isPlayer)
      @battlers.each_with_index do |b,i|
        next if !b || pbOwnedByPlayer?(i)!=isPlayer || @choices[i][0]!=:None || !pbCanShowCommands?(i)
        options=[]
        b.moves.each_with_index do |move,slot|
          next unless pbCanChooseMove?(i,slot,false)
          target=move.pbTarget(b)
          targets=target.num_targets==1 ? @battlers.compact.reject(&:fainted?).select { |other| pbMoveCanTarget?(i,other.index,target) }.map(&:index) : [-1]
          targets.each { |t| options << {kind:'move',slot:slot,target:t,move:move.id.to_s,pp:move.pp} }
        end
        pbParty(i).each_index { |slot| options << {kind:'switch',slot:slot,target:-1} if pbCanSwitch?(i,slot) }
        if options.empty?
          pbAutoChooseMove(i);next
        end
        selected=BlueNativeTurns.ask(self,i,'action',options)
        if selected[:kind]=='switch'
          raise 'Native switch rejected' unless pbRegisterSwitch(i,selected[:slot])
        else
          raise 'Native move rejected' unless pbRegisterMove(i,selected[:slot],false)
          pbRegisterTarget(i,selected[:target])
        end
      end
    end
    def pbSwitchInBetween(index,checkLaxOnly=false,canCancel=false)
      options=[]
      pbParty(index).each_index { |slot| options << {kind:'replace',slot:slot,target:-1} if pbCanSwitchIn?(index,slot) }
      BlueNativeTurns.ask(self,index,'replacement',options)[:slot]
    end
  end
  def self.pokemon(row)
    side,species,ability,item,nature,moves,ivs,evs=row
    data=GameData::Species.get(species.to_sym)
    raise 'Initial Mega form is forbidden' if data.mega_stone || data.mega_move
    pkmn=Pokemon.new(data.species,50,$player);pkmn.form=data.form
    raise 'Unknown species ability' unless (data.abilities+data.hidden_abilities).include?(ability.to_sym)
    pkmn.ability=ability.to_sym;pkmn.item=item.to_sym unless item=='-';pkmn.nature=nature.to_sym
    pkmn.moves=moves.split(',').map { |id| Pokemon::Move.new(id.to_sym) }
    [:HP,:ATTACK,:DEFENSE,:SPECIAL_ATTACK,:SPECIAL_DEFENSE,:SPEED].each_with_index do |stat,i|
      iv=ivs.split(',')[i].to_i;ev=evs.split(',')[i].to_i
      raise 'Invalid native IV/EV' unless (0..31).include?(iv) && (0..252).include?(ev)
      pkmn.iv[stat]=iv;pkmn.ev[stat]=ev
    end
    raise 'Invalid native EV total' if pkmn.ev.values.sum>510
    pkmn.calc_stats;pkmn.heal;[side.to_i,pkmn]
  end
  def self.run
    lines=[];@seq=0;@commands=[];before=Marshal.dump($player.party)
    logger=PBDebug.method(:logonerr);PBDebug.define_singleton_method(:logonerr) { |*args,&block| block.call }
    watchdog=Thread.new { sleep 180;write({protocol:2,state:'failed',error:'Worker timeout'});exit! 1 }
    rows=File.readlines(DIR+'/roster.tsv',chomp:true)
    raise 'Invalid native roster header' unless rows.shift=='BLUE_NATIVE_TURNS_1'
    format=rows.shift;raise 'Invalid battle format' unless ['single','double'].include?(format)
    pairs=rows.map { |row| pokemon(row.split("\t")) }
    teams=[0,1].map { |side| pairs.select { |s,p| s==side }.map(&:last) }
    raise 'Invalid team sizes' unless teams.all? { |t| (1..4).include?(t.length) && (format!='double' || t.length>=2) }
    scene=BlueOnlineProbe::Scene.new;foe=NPCTrainer.new('Remote opponent',$player.trainer_type);foe.party=teams[1]
    battle=Match.new(scene,teams[0],teams[1],[$player],[foe]);battle.setBattleMode(format)
    battle.internalBattle=false;battle.canLose=true;battle.canRun=false;battle.expGain=false;battle.moneyGain=false
    battle.disablePokeBalls=true;battle.controlPlayer=false;battle.showAnims=false;battle.switchStyle=false
    battle.instance_variable_set(:@blue_mechanics,{'mega'=>false,'zmove'=>false,'tera'=>false,'dynamax'=>false})
    $game_temp.in_battle=true
    result=battle.pbStartBattle
    raise 'Native match did not finish normally' unless [1,2,5].include?(result)
    raise 'Offline party changed' unless Marshal.dump($player.party)==before
    raise 'Both remote sides must submit real decisions' unless @commands.map { |c| c[:side] }.uniq.sort==[0,1]
    write({protocol:2,state:'finished',result:result,winner:result==1 ? 0 : result==2 ? 1 : nil,turn:battle.turnCount,active:public_state(battle),messages:scene.messages.last(200),commands:@commands})
    lines << 'PASS | Both HTTP participants control native decisions; result='+result.to_s
    lines << 'PASS | Original offline party preserved; no campaign save access'
    lines << 'RESULT=PASS'
    true
  rescue StandardError,SystemStackError=>error
    write({protocol:2,state:'failed',error:error.message})
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace || []);lines << 'RESULT=FAIL';false
  ensure
    $game_temp.in_battle=false
    watchdog.kill if watchdog && watchdog.alive?
    PBDebug.define_singleton_method(:logonerr,logger) if logger
    File.open('Data/blue-native-turns-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
    File.delete(REQUEST) if File.file?(REQUEST)
  end
  module Smoke
    def run_smoke
      check(BlueNativeTurns.run,'Native remote commands; Data/blue-native-turns-validation.txt')
      log('NATIVE_TURNS=PASS')
    end
  end
end
module Compiler
  class << self
    alias blue_turns_original_main main
    def main
      blue_turns_original_main
      if BlueBattleLab::SMOKE && File.file?(BlueNativeTurns::REQUEST) && Time.now-File.mtime(BlueNativeTurns::REQUEST)<120
        BlueBattleLab.singleton_class.prepend(BlueNativeTurns::Smoke)
      end
    end
  end
end
