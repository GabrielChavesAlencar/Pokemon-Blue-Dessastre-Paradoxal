# Two players, two games, one battle: both simulate it from one seed and exchange only decisions.
# Network code lives in the mp_client.py helper; the render loop only reads and writes small files.
module BlueMultiplayer
  ROOT='Data/blue-mp'
  CONFIG=BlueBattleHub::DIR+'/multiplayer.txt'
  PORT=8793
  KNOWN_FILES=/\A(start|state|helper|cmd-\d+|sync-\d+)\.(txt|log|txt\.tmp)\z/
  Finished=Struct.new(:reason,:winner)
  def self.encode_kv(values)
    values.map { |k,v| k.to_s+"\t"+[v.to_s].pack('m0')+"\n" }.join
  end
  def self.decode_kv(raw)
    result={}
    raw.each_line do |line|
      key,value=line.strip.split("\t",2)
      result[key]=value.to_s.unpack1('m0').force_encoding('UTF-8') if key
    end
    result
  end
  def self.load_config
    return {} unless File.file?(CONFIG)
    decode_kv(File.read(CONFIG))
  rescue StandardError
    {}
  end
  def self.save_config(values)
    BlueBattleHub.atomic(CONFIG,encode_kv(values))
  rescue StandardError=>e
    BlueBattleLab.log('MP_CONFIG_WARNING | '+e.message)
  end
  def self.python
    raise BlueBattleHub::ImportError,'O multiplayer usa um auxiliar Windows e nao esta disponivel nesta versao Android.' if defined?(BlueMobile) && BlueMobile.enabled?
    config='Data/blue-hub-python.txt'
    raise BlueBattleHub::ImportError,'Reabra HUB_DE_BATALHA.bat para preparar o multiplayer.' unless File.file?(config)
    File.read(config,encoding:'UTF-8').strip
  end
  # Keep only folders of finished sessions out of the way; nothing else lives here.
  def self.sweep
    Dir[ROOT+'/*'].each do |dir|
      next unless File.directory?(dir) && Time.now-File.mtime(dir)>3600
      Dir.children(dir).each { |name| File.delete(dir+'/'+name) if name.match?(KNOWN_FILES) }
      Dir.rmdir(dir)
    rescue SystemCallError
      next
    end
  end

  class Link
    attr_reader :dir
    def initialize(start)
      BlueMultiplayer.sweep
      Dir.mkdir(ROOT) unless Dir.exist?(ROOT)
      @dir=ROOT+"/#{Process.pid}-#{rand(1000000000)}"
      Dir.mkdir(@dir)
      @cmd=0;@state={};@read_at=0
      File.open(@dir+'/start.txt','wb') { |f| f.write(BlueMultiplayer.encode_kv(start)) }
      worker=File.expand_path('Plugins/ZZZZ Blue Battle Lab/mp_client.py')
      @pid=Process.spawn(BlueMultiplayer.python,worker,'--dir',File.expand_path(@dir),'--game',File.expand_path('.'),'--parent',Process.pid.to_s,out:File::NULL,err:File.expand_path(@dir+'/helper.log'))
      Process.detach(@pid)
    end
    def command(values)
      @cmd+=1
      path=@dir+"/cmd-#{@cmd}.txt"
      File.open(path+'.tmp','wb') { |f| f.write(BlueMultiplayer.encode_kv(values)) }
      File.rename(path+'.tmp',path)
    end
    def state
      if System.uptime-@read_at>=0.1
        @read_at=System.uptime
        begin
          @state=BlueMultiplayer.decode_kv(File.read(@dir+'/state.txt')) if File.file?(@dir+'/state.txt')
        rescue SystemCallError,ArgumentError
          # The helper is replacing the file; the next frame reads the new one.
        end
      end
      @state
    end
    def sync_result(n)
      path=@dir+"/sync-#{n}.txt"
      return nil unless File.file?(path)
      values=BlueMultiplayer.decode_kv(File.read(path))
      File.delete(path)
      [values['a'].to_s,values['b'].to_s]
    rescue SystemCallError,ArgumentError
      nil
    end
    def close
      command(op:'leave') unless @closed
      @closed=true
    rescue SystemCallError=>e
      BlueBattleLab.log('MP_CLOSE_WARNING | '+e.message)
    end
  end

  # Decisions cross the network as one short text per sync point. Battler indexes are mirrored
  # between the two games (my 0 is your 1), so everything on the wire uses the host's numbering.
  class Match < Battle
    MECHANICS=[['M',:pbRegisteredMegaEvolution?,:pbRegisterMegaEvolution],['Z',:pbRegisteredZMove?,:pbRegisterZMove],
               ['T',:pbRegisteredTerastallize?,:pbRegisterTerastallize],['D',:pbRegisteredDynamax?,:pbRegisterDynamax],
               ['U',:pbRegisteredUltraBurst?,:pbRegisterUltraBurst]].select { |row| Battle.method_defined?(row[1]) }.freeze
    attr_accessor :mp_auto,:mp_trace
    attr_reader :mp_outcome
    def mp_setup(link,side,seed,opponent_name)
      @mp_link=link;@mp_side=side;@mp_guest=side==1;@mp_seed=seed;@mp_n=0;@mp_opponent=opponent_name
      @mp_rng=Random.new(seed);@mp_private=0;@mp_forfeit=false
    end
    def mp_canon(index);@mp_guest ? index^1 : index;end
    # Menus and owner-only abilities must not advance the shared random sequence.
    def pbRandom(x)
      (@command_phase || @mp_private>0) ? rand(x) : @mp_rng.rand(x)
    end
    def mp_private
      @mp_private+=1
      yield
    ensure
      @mp_private-=1
    end
    def mp_ordered(list);@mp_guest ? list.sort_by { |b| b.index^1 } : list;end
    def allBattlers;mp_ordered(super);end
    def eachBattler(&block);allBattlers.each(&block);end
    def pbCalculatePriority(fullCalc=false,indexArray=nil)
      return super unless fullCalc && @mp_guest
      original=@battlers
      begin
        reordered=@battlers.dup
        (0..maxBattlerIndex).each { |i| reordered[i]=original[i^1] }
        @battlers=reordered
        super
      ensure
        @battlers=original
      end
    end
    def mp_digest_text
      sides=@mp_guest ? [1,0] : [0,1]
      rows=[@turnCount,@field.weather,@field.weatherDuration,@field.terrain,@field.terrainDuration]
      (0..maxBattlerIndex).each do |canon|
        b=@battlers[mp_canon(canon)]
        next rows << 'x' unless b && b.pokemon
        rows << [canon,b.species,b.form,b.hp,b.totalhp,b.status,b.statusCount,b.stages.values.join(','),b.ability_id,b.item_id,b.pbTypes(true).join('/')].join(':')
      end
      sides.each do |side|
        rows << @sides[side].effects.to_a.flatten.select { |v| v.is_a?(Integer) || v==true || v==false }.join(',')
        pbParty(side).each do |pkmn|
          next unless pkmn
          rows << [pkmn.species,pkmn.form,pkmn.hp,pkmn.status,pkmn.item_id,pkmn.moves.map { |m| "#{m.id}#{m.pp}" }.join(',')].join(':')
        end
      end
      rows.join('|')
    end
    def mp_digest(text)
      hash=0xcbf29ce484222325
      text.each_byte { |byte| hash=((hash^byte)*0x100000001b3)&0xffffffffffffffff }
      format('%016x',hash)
    end
    def mp_exchange(label,choice,text=mp_digest_text)
      n=@mp_n;@mp_n+=1
      digest=mp_digest(text)
      if @mp_trace
        @mp_trace.puts("#{n} #{label} #{digest} #{text}");@mp_trace.flush
      end
      @mp_link.command(op:'sync',n:n,label:label,hash:digest,choice:choice)
      values=mp_wait(n)
      @mp_rng=Random.new((@mp_seed+n+1)&0x7fffffffffffffff)
      values
    end
    def mp_wait(n)
      shown=false;started=System.uptime;down=nil
      loop do
        values=@mp_link.sync_result(n)
        if values
          @scene.sprites['messageWindow'].text='' if shown
          return values
        end
        state=@mp_link.state
        mp_stop(state['reason'],state['winner']) if state['state']=='finished'
        mp_stop('cancelled','') if ['cancelled','expired'].include?(state['state'])
        mp_stop('link','') if state['link']=='failed'
        if state['link']=='down'
          down||=System.uptime
          mp_stop('link','') if System.uptime-down>60
        else
          down=nil
        end
        if @mp_scene_closed
          Graphics.update;Input.update
          sleep(0.005)
          next
        end
        if !shown && System.uptime-started>0.15
          @scene.pbShowWindow(Battle::Scene::MESSAGE_BOX)
          window=@scene.sprites['messageWindow'];window.letterbyletter=false
          window.text=_INTL('Aguardando {1}...',@mp_opponent);shown=true
        end
        @scene.pbUpdate
        sleep(0.005)
      end
    end
    def mp_stop(reason,winner)
      @mp_outcome=Finished.new(reason.to_s,winner.to_s)
      pbAbort
    end
    def mp_encode_choice(index)
      choice=@choices[index]
      head="#{mp_canon(index)}:"
      case choice[0]
      when :UseMove
        flags=MECHANICS.select { |row| send(row[1],index) }.map(&:first).join
        target=choice[3].to_i<0 ? -1 : mp_canon(choice[3])
        head+"m:#{choice[1]}:#{target}:#{flags}"
      when :SwitchOut then head+"s:#{choice[1]}"
      else head+'n'
      end
    end
    def mp_apply_choice(index,row)
      b=@battlers[index]
      kind,value,target,flags=row
      case kind
      when 's'
        slot=value.to_i
        mp_stop('invalid','') unless pbCanSwitch?(index,slot)
        @choices[index][0]=:SwitchOut;@choices[index][1]=slot;@choices[index][2]=nil
      when 'm'
        slot=value.to_i;flags=flags.to_s
        mp_stop('invalid','') unless slot==-1 || (slot.between?(0,b.moves.length-1) && (!flags.empty? || pbCanChooseMove?(index,slot,false)))
        MECHANICS.each { |row2| send(row2[2],index) if flags.include?(row2[0]) }
        # The owner's fight menu swapped these move lists before registering the move.
        b.display_zmoves if flags.include?('Z')
        b.display_dynamax_moves if flags.include?('D')
        b.display_mega_moves if flags.include?('M') && MultipleForms.hasFunction?(b.pokemon,'getMegaMoves')
        @choices[index][0]=:UseMove;@choices[index][1]=slot
        @choices[index][2]=slot==-1 ? @struggle : b.moves[slot]
        @choices[index][3]=target.to_i<0 ? -1 : mp_canon(target.to_i)
      end
    end
    def mp_auto_choose(index)
      b=@battlers[index]
      switches=(pbParty(index).length).times.select { |slot| pbCanSwitch?(index,slot) }
      if !switches.empty? && @mp_auto.rand(100)<20
        return pbRegisterSwitch(index,switches[@mp_auto.rand(switches.length)])
      end
      return pbAutoChooseMove(index,false) unless pbCanShowFightMenu?(index)
      key=@mp_auto.rand(100)<35 ? blue_available_mechanics(index).sample(random:@mp_auto) : nil
      public_send(BlueBattleOptions::REGISTER[key],index) if key
      b.display_dynamax_moves if key==:dynamax
      b.display_zmoves if key==:zmove
      slots=b.moves.each_index.select { |slot| pbCanChooseMove?(index,slot,false) }
      # Mostly attacks, so a test match does not stall on healing moves.
      damaging=slots.select { |slot| b.moves[slot].damagingMove? }
      slots=damaging if !damaging.empty? && @mp_auto.rand(100)<85
      slot=slots[@mp_auto.rand(slots.length)]
      pbRegisterMove(index,slot,false)
      unless singleBattle?
        target=b.moves[slot].pbTarget(b)
        if target.num_targets==1
          legal=allBattlers.select { |other| pbMoveCanTarget?(index,other.index,target) }.map(&:index)
          pbRegisterTarget(index,legal[@mp_auto.rand(legal.length)]) unless legal.empty?
        end
      end
    end
    def pbCommandPhaseLoop(isPlayer)
      if isPlayer
        return super unless @mp_auto
        @battlers.each_with_index do |b,i|
          next if !b || !pbOwnedByPlayer?(i) || @choices[i][0]!=:None || !pbCanShowCommands?(i)
          mp_auto_choose(i)
        end
        return
      end
      if @mp_auto && @turnCount>=2
        @mp_forfeit=true if ENV['BLUE_MP_TEST_SCENARIO']=='forfeit' && @mp_side==0
        Process.exit!(0) if ENV['BLUE_MP_TEST_SCENARIO']=='quit' && @mp_side==0
      end
      own=[];@battlers.each_with_index { |b,i| own << i if b && pbOwnedByPlayer?(i) }
      payload=@mp_forfeit ? 'f' : own.map { |i| mp_encode_choice(i) }.join(';')
      values=mp_exchange("turn#{@turnCount}",payload)
      mine,theirs=@mp_side==0 ? values : values.reverse
      if mine=='f' || theirs=='f'
        @mp_outcome=Finished.new('forfeit',mine=='f' && theirs=='f' ? '' : (mine=='f' ? 1-@mp_side : @mp_side).to_s)
        pbDisplayPaused(_INTL('{1} desistiu da partida.',@mp_opponent)) if theirs=='f' && mine!='f'
        @decision=mine=='f' && theirs=='f' ? 5 : mine=='f' ? 2 : 1
        return
      end
      theirs.split(';').each do |entry|
        canon,*row=entry.split(':',-1)
        index=mp_canon(canon.to_i)
        next mp_stop('invalid','') unless @battlers[index] && !pbOwnedByPlayer?(index)
        mp_apply_choice(index,row) if @choices[index][0]==:None && pbCanShowCommands?(index)
      end
    end
    def pbRun(index,duringBattle=false)
      return 0 unless pbDisplayConfirm(_INTL('Desistir da partida? Seu adversario vence.'))
      @mp_forfeit=true
      1
    end
    def pbCallMenu(index);pbRunMenu(index);end
    def pbDebugMenu;end
    def pbSwitchInBetween(index,checkLaxOnly=false,canCancel=false)
      own=pbOwnedByPlayer?(index);slot=-1
      if own
        if @mp_auto
          options=pbParty(index).length.times.select { |i| pbCanSwitchIn?(index,i) && (checkLaxOnly || pbCanSwitch?(index,i)) }
          slot=options[@mp_auto.rand(options.length)]
        else
          slot=mp_private { pbPartyScreen(index,checkLaxOnly,canCancel) }
        end
      end
      values=mp_exchange("swap#{mp_canon(index)}",own ? slot.to_s : '')
      return slot if own
      other=values[1-@mp_side].to_i
      mp_stop('invalid','') unless pbCanSwitchIn?(index,other)
      other
    end
    # Same as the engine's for a trainer battle, but both games visit the fainted battlers in one order.
    def pbEORSwitch(favorDraws=false)
      return if @decision>0 && !favorDraws
      return if @decision==5 && favorDraws
      pbJudge
      return if @decision>0
      switched=[]
      loop do
        switched.clear
        (0..maxBattlerIndex).each do |canon|
          b=@battlers[mp_canon(canon)]
          next if !b || !b.fainted?
          next if !pbCanChooseNonActive?(b.index)
          slot=pbSwitchInBetween(b.index,true)
          pbRecallAndReplace(b.index,slot)
          switched.push(b.index)
        end
        break if switched.empty?
        pbOnBattlerEnteringBattle(switched)
      end
    end
    def mp_finish
      return if @mp_outcome && @mp_outcome.reason!='forfeit'
      @mp_scene_closed=true
      winner=case @decision
             when 1 then @mp_side
             when 2,3 then 1-@mp_side
             else -1
             end
      result=@mp_outcome||Finished.new('complete',winner<0 ? '' : winner.to_s)
      begin
        # The engine restores items on the owner's party only, so compare just the winner here.
        mp_exchange('end','',"winner #{winner}")
        @mp_outcome=result
      rescue Battle::BattleAbortedException
        # The room may close before this game reads the last sync; only a mismatch changes the result.
        @mp_outcome=result unless @mp_outcome.reason=='desync'
      end
    end
  end

  # Only informs the owner in the engine, so it must not spend shared random numbers.
  module OwnerOnlyAbilities
    def triggerOnSwitchIn(ability,battler,battle,*args)
      return super unless battle.is_a?(Match) && [:ANTICIPATION,:FOREWARN,:FRISK].include?(ability)
      battle.mp_private { super }
    end
  end
  Battle::AbilityEffects.singleton_class.prepend(OwnerOnlyAbilities)

  class Lobby < BlueBattleHub::Screen
    attr_reader :outcome
    def initialize(link,host)
      @link=link;@host=host;@outcome=nil;@notice=''
    end
    def render
      return unless @canvas
      @buttons=[];@bitmap.clear;rect(0,0,W,H,:bg)
      state=@link.state
      text('BLUE / MULTIPLAYER',24,14,700,30)
      rect(24,70,912,480,:panel)
      if state['link']=='failed'
        text('Nao foi possivel entrar na sala.',52,100,850,24,:red)
        state['error'].to_s.scan(/.{1,80}(?:\s|$)/).each_with_index { |line,i| text(line.strip,52,150+28*i,850,18) }
      elsif @host && state['room']
        text('Sala criada. Passe estes dados para o outro jogador:',52,96,850,20)
        text('CODIGO DA SALA',52,146,300,16,:muted)
        text(state['room'],52,172,500,44,:green)
        text('ENDERECO(S) DESTE PC',52,240,500,16,:muted)
        addresses=state['addresses'].to_s.split("\n")
        addresses=['Nenhuma rede encontrada'] if addresses.empty?
        addresses.first(4).each_with_index { |ip,i| text(ip,52,266+34*i,500,26,:blue) }
        text('Rede local: use o endereco 192.168.x.x. Pela internet: Radmin VPN/Hamachi (26.x / 25.x)',52,420,860,16,:muted)
        text('ou abra a porta '+state['port'].to_s+' TCP no roteador. Se o Windows perguntar, permita o Python no firewall.',52,446,860,16,:muted)
        text('Aguardando o outro jogador entrar...',52,496,860,20,:yellow)
        button(:copy,'Copiar codigo',620,172,250,38) { Input.clipboard=state['room'].to_s;@notice='Codigo copiado.';@dirty=true }
      else
        text('Conectando a sala...',52,100,850,22,:yellow)
      end
      button(:cancel,state['link']=='failed' ? 'Voltar' : 'Cancelar',24,662,200,38) { @outcome=:cancel;@finished=true }
      text(@notice,240,668,690,17,:muted)
      @dirty=false
    end
    def update_portraits;end
    def run
      mount
      @last={}
      until @finished
        Graphics.update;Input.update
        state=@link.state
        if state['link']!='failed' && ['selecting','prepared'].include?(state['state']);@outcome=:go;break;end
        @dirty=true if state!=@last
        @last=state
        if Input.trigger?(Input::MOUSELEFT)
          hit=@buttons.reverse.find { |b| inside(Mouse.getMousePos,b[:rect]) };hit[:action].call if hit
        elsif Input.trigger?(Input::BACK)
          @outcome=:cancel;@finished=true
        end
        render if @dirty
      end
      @outcome
    ensure
      unmount
    end
  end

  class OnlinePick < BlueBattleHub::PickFour
    def initialize(team,foes,names,link)
      @link=link
      super([team,foes],names)
    end
    def opponent_status
      foe=@names[1]+(@link.state['ready'+(1-@link.state['you'].to_i).to_s]=='1' ? ' / pronto' : ' / escolhendo')
      @sent ? foe+'  (seus quatro estao confirmados; aguardando)' : foe
    end
    def send_picks
      @link.command(op:'select',picks:@selected.join(','))
      @sent=true;@dirty=true
    end
    def confirm_selection;send_picks if @selected.length==4 && !@sent;end
    def toggle(i);super unless @sent;end
    def expire!
      return if @sent
      @selected=[0,1,2,3];@timed_out=true;send_picks
    end
    def tick
      state=@link.state
      if state['state']!='selecting';@finished=true;return;end
      @dirty=true if state['ready0']!=@last_ready0 || state['ready1']!=@last_ready1
      @last_ready0=state['ready0'];@last_ready1=state['ready1']
      super
      render if @dirty
    end
    def result
      @cancelled ? nil : @selected
    end
  end

  MESSAGES={'complete'=>nil,'forfeit'=>'O adversario desistiu ou saiu da partida.','disconnect'=>'A conexao de um dos jogadores caiu.',
            'timeout'=>'Tempo de decisao esgotado (3 minutos).','desync'=>'Os dois jogos calcularam resultados diferentes; a partida foi encerrada sem vencedor.',
            'invalid'=>'O outro jogo enviou uma escolha invalida; a partida foi encerrada.','cancelled'=>'A sala foi fechada.','expired'=>'A sala expirou.',
            'link'=>'A conexao com a sala foi perdida.'}.freeze
  def self.outcome_text(outcome,side)
    return 'Partida encerrada.' unless outcome
    win=outcome.winner=='' ? nil : outcome.winner.to_i==side
    head=win.nil? ? (outcome.reason=='complete' ? 'Empate.' : 'Sem resultado.') : (win ? 'Vitoria!' : 'Derrota.')
    detail=MESSAGES[outcome.reason]
    outcome.reason=='forfeit' && win==false ? 'Derrota. Voce desistiu da partida.' : [head,detail].compact.join(' ')
  end
  def self.build_team(text)
    entries=BlueBattleHub.preview(text)
    raise BlueBattleHub::ImportError,'Time incompativel: '+entries.filter_map { |e| e['error'] }.join(' ') if entries.any? { |e| e['error'] }
    entries.map { |e| e['pokemon'] }
  end
  def self.preview_team(names)
    names.map do |name|
      BlueBattleLab.build(BlueBattleHub.resolve(:species,name).id,BlueBattleHub::LEVEL)
    end
  end
  def self.mechanics_from(text)
    all=text.to_s.split(',')
    BlueBattleOptions.defaults.keys.to_h { |key| [key,all.include?(key)] }
  end
  def self.battle(link,state,automated=nil,trace=nil)
    side=state['you'].to_i;seed=state['seed'].to_i
    # Pokemon creation can roll hidden values and random forms; both games roll the same ones.
    srand(seed)
    teams=[state['team0'],state['team1']].map { |text| BlueBattleHub.prepare_roster(build_team(text)) }
    srand
    mine,theirs=teams[side],teams[1-side]
    opponent_name=state["name#{1-side}"].to_s
    mechanics=mechanics_from(state['mechanics'])
    [mine,theirs].each { |party| BlueBattleOptions.prepare_lab_party(party,mechanics);party.each(&:heal) }
    previous=[$player.party,$player.name,$DEBUG]
    $player.party=mine;$player.name=state["name#{side}"].to_s
    $player.tera_charged=true if $player.respond_to?(:tera_charged=)
    $DEBUG=false
    trainer=NPCTrainer.new(opponent_name,$player.trainer_type);trainer.party=theirs
    gear=[:MEGARING,:DYNAMAXBAND,:ZRING,:TERAORB].select { |id| GameData::Item.try_get(id) }
    trainer.items=gear if trainer.respond_to?(:items=)
    EventHandlers.trigger(:on_start_battle)
    scene=automated ? BlueBattleLab::SmokeScene.new : Battle::Scene.new
    match=Match.new(scene,mine,theirs,[$player],[trainer])
    match.mp_setup(link,side,seed,opponent_name)
    match.mp_auto=automated;match.mp_trace=trace
    match.instance_variable_set(:@blue_lab_battle,true)
    match.instance_variable_set(:@blue_mechanics,mechanics)
    match.items=[gear] if match.respond_to?(:items=)
    match.setBattleMode(state['format'])
    match.internalBattle=false;match.canLose=true;match.canRun=true;match.expGain=false;match.moneyGain=false
    match.disablePokeBalls=true;match.environment=:None;match.backdrop='indoor1';match.time=0;match.switchStyle=false
    match.showAnims=ENV['BLUE_MP_TEST'] ? ENV['BLUE_MP_TEST_ANIMS']=='1' : true
    $game_temp.in_battle=true
    BlueBattleLab.log("MP_BATTLE | side=#{side} format=#{state['format']} teams=#{mine.length}x#{theirs.length}")
    pbBGMPlay(pbGetTrainerBattleBGM([trainer])) unless automated
    match.pbStartBattle
    match.mp_finish
    BlueBattleLab.log("MP_RESULT | side=#{side} decision=#{match.decision} rounds=#{match.turnCount} outcome=#{match.mp_outcome&.reason}/#{match.mp_outcome&.winner}")
    outcome_text(match.mp_outcome,side)
  ensure
    $game_temp.in_battle=false
    $player.party,$player.name,$DEBUG=previous if previous
    pbBGMStop unless automated
  end
  def self.wait_prepared(link,seconds=75)
    deadline=System.uptime+seconds
    loop do
      state=link.state
      return state if state['state']=='prepared' && state['seed'] && !state['seed'].empty?
      return nil if ['finished','cancelled','expired'].include?(state['state']) || state['link']=='failed' || System.uptime>deadline
      Graphics.update;Input.update
      sleep(0.01)
    end
  end
  def self.start_values(mode,name,team,format,address,code)
    values={mode:mode,name:name,team:BlueBattleHub.export(team).strip,preview:team.map { |mon| BlueBattleHub.form_label(mon.species_data) }.join("\n"),port:PORT}
    if mode=='host'
      values[:format]=format
      values[:mechanics]=BlueBattleOptions.snapshot(:lab).select { |_k,v| v }.keys.join(',')
    else
      values[:address]=address;values[:code]=code
    end
    values
  end

  # Unattended two-window check used by tests/multiplayer_e2e.py. Never runs without its variable.
  module AutoTest
    def main
      role=ENV['BLUE_MP_TEST']
      return super unless role
      if role=='compile';$scene=nil;return;end
      BlueBattleLab.setup
      BlueMultiplayer.autotest(role,ENV['BLUE_MP_TEST_DIR'])
      $scene=nil
    rescue Exception=>e
      File.open(ENV['BLUE_MP_TEST_DIR']+"/result-#{role}.txt",'ab') { |f| f.write("ERROR #{e.class}: #{e.message}\n#{e.backtrace.first(12).join("\n")}\n") } if role
      raise unless e.is_a?(StandardError)
      $scene=nil
    end
  end
  def self.autotest(role,dir)
    seed=ENV['BLUE_MP_TEST_SEED'].to_i
    team=build_team(File.read(dir+"/team-#{role}.txt",encoding:'UTF-8'))
    format=ENV['BLUE_MP_TEST_FORMAT'] || 'single'
    code=nil
    if role=='join'
      deadline=System.uptime+120
      until File.file?(dir+'/code.txt') && !(code=File.read(dir+'/code.txt').strip).empty?
        raise 'Host code never appeared' if System.uptime>deadline
        Graphics.update;Input.update;sleep(0.05)
      end
    end
    link=Link.new(start_values(role=='host' ? 'host' : 'join',role.capitalize,team,format,'127.0.0.1',code))
    begin
      deadline=System.uptime+120
      loop do
        state=link.state
        raise 'Link failed: '+state['error'].to_s if state['link']=='failed'
        if role=='host' && state['room'] && !File.file?(dir+'/code.txt')
          File.open(dir+'/code.tmp','wb') { |f| f.write(state['room']) };File.rename(dir+'/code.tmp',dir+'/code.txt')
        end
        break if ['selecting','prepared'].include?(state['state'])
        raise 'Room never started' if System.uptime>deadline
        Graphics.update;Input.update;sleep(0.02)
      end
      if link.state['state']=='selecting'
        link.command(op:'select',picks:(role=='host' ? [0,1,2,3] : [5,4,3,2]).join(','))
      end
      state=wait_prepared(link)
      raise 'Room was not prepared: '+link.state.inspect unless state
      File.open(dir+"/trace-#{role}.txt",'ab') do |trace|
        text=battle(link,state,Random.new(seed*2+(role=='host' ? 0 : 1)),trace)
        File.open(dir+"/result-#{role}.txt",'ab') { |f| f.write("OK #{text}
") }
      end
    ensure
      link.close
    end
  end
end
BlueBattleLab::Scene.prepend(BlueMultiplayer::AutoTest)

module BlueBattleHub
  class Screen
    def start_multiplayer
      selection=choose('Multiplayer: enfrente outro jogador com o seu MEU TIME',['Criar sala (este PC hospeda)','Entrar na sala de outro jogador','Voltar'])
      return unless [0,1].include?(selection)
      team=BlueBattleHub.prepare_roster(@teams[0])
      if @format=='double' && selection==0 && team.length!=6
        choose('Duplas: prepare seis Pokemon em MEU TIME.',['Voltar']);return
      end
      config=BlueMultiplayer.load_config
      name=prompt('Seu nome na partida',config['name'] || 'Treinador',24)
      return if name.nil? || name.strip.empty?
      address=code=nil
      if selection==1
        address=prompt('Endereco do anfitriao (ex.: 192.168.0.10)',config['address'].to_s,64)
        return if address.nil? || address.strip.empty?
        code=prompt('Codigo da sala','',6)
        return if code.nil? || code.strip.empty?
      end
      BlueMultiplayer.save_config({'name'=>name.strip,'address'=>address || config['address'].to_s})
      changed;unmount;Graphics.resize_screen(*@original_size)
      link=BlueMultiplayer::Link.new(BlueMultiplayer.start_values(selection==0 ? 'host' : 'join',name.strip,team,@format,address,code))
      begin
        @notice=multiplayer_session(link,team,selection==0)
      ensure
        link.close
      end
      mount unless @canvas
      # A result in the footer is easy to miss after a whole match.
      choose('Multiplayer',@notice.scan(/.{1,60}(?:\s|$)/).map(&:strip)+['Voltar'],@notice.scan(/.{1,60}(?:\s|$)/).length)
    ensure
      mount unless @canvas
    end
    def multiplayer_session(link,team,host)
      return 'Multiplayer cancelado.' if BlueMultiplayer::Lobby.new(link,host).run!=:go
      state=link.state
      if state['state']=='selecting'
        side=state['you'].to_i
        foes=BlueMultiplayer.preview_team(state["preview#{1-side}"].to_s.split("\n"))
        picks=BlueMultiplayer::OnlinePick.new(team,foes,[state["name#{side}"].to_s,state["name#{1-side}"].to_s],link).run
        return 'Voce saiu da sala.' if picks.nil?
      end
      state=BlueMultiplayer.wait_prepared(link)
      unless state
        reason=link.state['reason'].to_s
        return BlueMultiplayer::MESSAGES[reason] || 'A sala foi encerrada antes da batalha.'
      end
      Graphics.resize_screen(*@original_size)
      BlueMultiplayer.battle(link,state)
    end
  end
end
