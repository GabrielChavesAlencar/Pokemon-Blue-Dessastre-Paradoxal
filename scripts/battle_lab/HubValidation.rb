module BlueBattleHub
  module Validation
    module ClickInput
      def trigger?(key)
        return key==Input::MOUSELEFT if BlueBattleHub::Validation.instance_variable_get(:@click)
        super
      end
    end
    PASTE="Charizard-Mega-Y @ Charizardite Y\nAbility: Blaze\nLevel: 50\nEVs: 15 HP / 18 Def / 1 SpA / 32 Spe\nModest Nature\nIVs: 0 Atk\n- Heat Wave\n- Solar Beam\n- Protect\n- Flamethrower\n\nIndeedee [Male] @ Focus Sash\nAbility: Psychic Surge\nEVs: 32 SpA / 2 SpD / 32 Spe\nTimid Nature\n- Expanding Force\n- Hyper Voice\n- Trick Room\n- Imprison\n"
    def self.check(value,label)
      raise label unless value
      @lines << 'PASS | '+label
    end
    def self.run
      @lines=[]
      preview=BlueBattleHub.preview(PASTE.gsub("\n","\r\r\n"))
      check(preview.length==2 && preview.all? { |p| p['pokemon'] },'Pokepaste with doubled CR line endings imports two complete Pokemon')
      team=preview.map { |r| r['pokemon'] }
      check(team[0].species==:CHARIZARD && team[0].form==0 && team[0].item_id==:MEGAITEY,'Mega paste prepares base Pokemon and the actual stone used by this engine')
      @lines << "MEGA | target=#{team[0].getMegaForm} ability=#{team[0].ability_id} ability_data=#{team[0].ability.id} item=#{team[0].item_id}"
      check(team[0].getMegaForm>0 && team[0].ability.id==:BLAZE,'Pre-Mega ability is retained and Mega evolution remains available')
      check(team[0].level==50 && team[0].iv[:ATTACK]==0 && team[0].ev[:SPEED]==32,'Levels, zero IVs and small literal EV values are retained')
      check(team[1].male? && team[1].level==100,'Male bracket syntax and default Showdown level work')
      text=BlueBattleHub.export(team);again=BlueBattleHub.preview(text)
      check(again.all? { |p| p['pokemon'] },'Exported Showdown text reimports without errors')
      a=again.map { |r| r['pokemon'] }
      fingerprint=proc { |m| [m.species,m.form,m.level,m.item_id,m.ability_id,m.nature.id,m.ev,m.iv,m.gender,m.shiny?,m.moves.map(&:id)] }
      check(team.map(&fingerprint)==a.map(&fingerprint),'Showdown round-trip preserves species, form, moves, item, nature, EVs and IVs')
      invalids=[PASTE.sub('15 HP','253 HP'),PASTE.sub('15 HP / 18 Def / 1 SpA / 32 Spe','252 HP / 252 Def / 252 Spe'),PASTE.sub('Focus Sash','Missing item'),PASTE.sub('Charizardite Y','Missing item'),PASTE.sub('Heat Wave','Missing move'),PASTE*4]
      invalids.each do |bad|
        rejected=false
        begin;rejected=BlueBattleHub.preview(bad).any? { |r| r['error'] };rescue BlueBattleHub::ImportError;rejected=true;end
        check(rejected,'Invalid team is rejected before replacing a roster')
      end
      ['http://pokepast.es/bf2e74c7e8b615a6','https://evil.example/a','https://pokepast.es.evil.example/bf2e74c7e8b615a6','https://pokepast.es/../../secret'].each do |url|
        blocked=false;begin;BlueBattleHub.url(url);rescue BlueBattleHub::ImportError;blocked=true;end
        check(blocked,'Only the exact HTTPS Pokepaste host and ID are accepted')
      end
      check(BlueBattleHub.url('https://pokepast.es/bf2e74c7e8b615a6')=='https://pokepast.es/bf2e74c7e8b615a6/raw','User Pokepaste link resolves to its raw team')
      check(BlueBattleHub.url('https://pokepast-es.translate.goog/0aa2fa5b1738e3c7?_x_tr_sl=en&_x_tr_tl=pt')=='https://pokepast.es/0aa2fa5b1738e3c7/raw','Google translated Pokepaste URL normalizes to the original unmodified English team')
      check(BlueBattleHub.resolve(:species,'Tauros-Paldea-Aqua').id==:TAUROS_3,'Showdown Paldea Aqua alias maps to the existing water Tauros')
      female=BlueBattleHub.build(BlueBattleHub.parse("Meowstic-Mega-F @ Meowsticite\nAbility: Trace\n- Psychic\n").first)
      check(female.female? && female.form==1 && female.getMegaForm==3,'Female Mega Meowstic import keeps its correct sex and origin')
      original=[Graphics.width,Graphics.height]
      screen=Screen.new;screen.instance_variable_set(:@original_size,original);screen.mount
      3.times { Graphics.update;Input.update }
      check(Graphics.width==960 && Graphics.height==720,'Native team builder renders at its dedicated resolution')
      check([:import,:export,:battle,:side0,:side1,:stats].all? { |id| screen.buttons.any? { |b| b[:id]==id } },'Hub exposes both teams, import/export, stats and battle actions')
      before_error=Marshal.dump(screen.teams)
      ['','https://evil.example/8206474502b1a3be'].each do |bad|
        messages=[]
        screen.define_singleton_method(:choose) { |title,labels,default=0| messages << title;title.start_with?('Importar para') ? 1 : -1 }
        screen.define_singleton_method(:prompt) { |*args| bad }
        screen.import_menu
        check(messages.any? { |title| title.start_with?('Nao foi possivel importar') } && Marshal.dump(screen.teams)==before_error,'Empty or invalid import shows a visible error and preserves both teams')
        screen.singleton_class.send(:remove_method,:choose);screen.singleton_class.send(:remove_method,:prompt)
      end
      source=Marshal.dump(screen.teams.map { |t| t.map(&fingerprint) })
      [:species,:item,:ability,:move,:nature,:type,:stats].each do |tab|
        screen.tab(tab);screen.render
        check(!screen.buttons.empty?,"Native #{tab} panel renders with the real engine catalog")
      end
      screen.change_side(1);screen.render
      check(screen.instance_variable_get(:@side)==1 && Marshal.dump(screen.teams.map { |t| t.map(&fingerprint) })==source,'Changing opponent editor does not mutate either roster')
      player_before=Marshal.dump(screen.teams[0].map(&fingerprint))
      screen.define_singleton_method(:choose) { |title,labels,default=0| default }
      screen.confirm_import(PASTE)
      check(screen.teams[1].length==2 && Marshal.dump(screen.teams[0].map(&fingerprint))==player_before,'Confirmed opponent import changes only the opponent roster')
      opponent_before=Marshal.dump(screen.teams[1].map(&fingerprint))
      screen.change_side(0);screen.confirm_import(PASTE)
      check(screen.teams[0].length==2 && Marshal.dump(screen.teams[1].map(&fingerprint))==opponent_before,'Confirmed player import changes only the player roster')
      screen.singleton_class.send(:remove_method,:choose)
      screen.change_side(0);screen.tab(:species);screen.render;screen.update_portraits
      Graphics.update
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-hub-builder-smoke.png');shot.dispose
      screen.tab(:stats);screen.render;Graphics.update
      shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-hub-stats-smoke.png');shot.dispose
      test_clicks(screen)
      request='Data/blue-hub-test-pokepaste.txt'
      if File.file?(request)
        File.read(request).lines.map(&:strip).reject(&:empty?).each do |url|
          raw=screen.fetch_with_progress(url)
          check(raw && !raw.empty?,'Native process-based HTTPS import downloads '+url)
          rows=BlueBattleHub.preview(raw)
          @lines << rows.map { |r| r['name']+': '+r['error'].to_s }.join('; ')
          check(rows.length==6 && rows.all? { |r| r['pokemon'] },'Actual supplied paste imports all six Pokemon')
          screen.define_singleton_method(:choose) { |title,labels,default=0| title.start_with?('Importar para') ? 1 : default }
          screen.define_singleton_method(:prompt) { |*args| url }
          screen.import_menu
          check(screen.teams[0].length==6 && screen.teams[0].map(&:species)==rows.map { |r| r['pokemon'].species },'Actual native import action downloads, previews and applies the intended roster')
          screen.singleton_class.send(:remove_method,:choose)
          screen.singleton_class.send(:remove_method,:prompt)
        end
        File.delete(request)
      end
      test_storage(team)
      # Use the production Hub battle action and real engine, with only the
      # smoke controller replacing human move input for this short match.
      original_battle=BlueBattleLab.method(:battle)
      original_battle=original_battle.super_method while original_battle.owner!=BlueBattleLab.singleton_class
      BlueBattleLab.define_singleton_method(:battle) do |*args|
        args[2]=true;original_battle.call(*args)
      end
      attacker=BlueBattleLab.build(:PIKACHU,100);attacker.moves=[Pokemon::Move.new(:THUNDERBOLT)]
      defender=BlueBattleLab.build(:MAGIKARP,5);defender.moves=[Pokemon::Move.new(:SPLASH)]
      screen.instance_variable_set(:@teams,[[attacker],[defender]])
      screen.instance_variable_set(:@format,'single');screen.start_battle
      check(Graphics.width==Screen::W && Graphics.height==Screen::H && screen.instance_variable_get(:@canvas),'Real Hub battle returns to the native builder with its resolution restored')
      @lines << 'RESULT=PASS';true
    rescue StandardError,SystemStackError=>e
      @lines << "FAIL | #{e.class}: #{e.message}";@lines.concat(e.backtrace);@lines << 'RESULT=FAIL';false
    ensure
      screen&.unmount
      BlueBattleLab.define_singleton_method(:battle,original_battle) if original_battle
      Graphics.resize_screen(*original) if original
      File.open('Data/blue-hub-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
    end
    def self.test_clicks(screen)
      original=Mouse.method(:getMousePos)
      Mouse.define_singleton_method(:getMousePos) { BlueBattleHub::Validation.instance_variable_get(:@point) }
      Input.singleton_class.prepend(ClickInput) unless Input.singleton_class.ancestors.include?(ClickInput)
      @click=true
      button=screen.buttons.find { |b| b[:id]==:side1 }
      box=button[:rect];@point=[box[0]+box[2]/2,box[1]+box[3]/2]
      screen.handle_input;screen.render
      check(screen.instance_variable_get(:@side)==1,'Native mouse click changes the editable team')
      screen.change_side(0);screen.tab(:stats);screen.render
      pokemon=screen.teams[0][0]
      pokemon.ev.each_key { |s| pokemon.ev[s]=0 }
      [0,1,2].each do |i|
        screen.instance_variable_set(:@drag_stat,nil)
        button=screen.buttons.find { |b| b[:id]=="slider#{i}".to_sym }
        box=button[:rect];@point=[686,box[1]+12]
        screen.handle_input;screen.render
      end
      check(pokemon.ev.values.sum==510 && pokemon.ev[:HP]==252 && pokemon.ev[:ATTACK]==252 && pokemon.ev[:DEFENSE]==6,'Actual EV slider clicks obey 252 per stat and 510 total')
    ensure
      @click=false
      Mouse.define_singleton_method(:getMousePos,original) if original
      screen.instance_variable_set(:@drag_stat,nil)
    end
    def self.test_storage(team)
      old=BlueBattleHub::DIR
      temporary='BlueHub-Test-'+Time.now.strftime('%Y%m%d%H%M%S')+'-'+rand(1000000).to_s
      BlueBattleHub.send(:remove_const,:DIR);BlueBattleHub.const_set(:DIR,temporary)
      path=BlueBattleHub.save_team(team,'Native library test')
      restored=BlueBattleHub.preview(File.read(path,encoding:'UTF-8'))
      check(restored.all? { |r| r['pokemon'] } && BlueBattleHub.library.include?(path),'Native library persists and reloads a complete team')
      row=[1,BlueBattleHub.export(team),BlueBattleHub.export(team),['Player','Foe'],'double','radical',BlueBattleOptions.snapshot(:lab),'original']
      BlueBattleHub.atomic(temporary+'/session.rxdata',Marshal.dump(row))
      saved=BlueBattleHub.load_session
      check(saved && saved[0].map(&:length)==[2,2] && saved[2]=='double','Both rosters and battle format survive session reload')
    ensure
      if temporary && temporary.start_with?('BlueHub-Test-') && Dir.exist?(temporary)
        Dir[temporary+'/*'].each { |file| File.delete(file) if File.file?(file) };Dir.rmdir(temporary)
      end
      if old;BlueBattleHub.send(:remove_const,:DIR);BlueBattleHub.const_set(:DIR,old);end
    end
  end
end
