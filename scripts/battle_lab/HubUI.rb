# Native canvas; no browser or campaign save is involved.
module BlueBattleHub
  class Screen
    W=960;H=720
    COLORS={bg:[9,15,27],panel:[18,28,46],field:[25,39,60],line:[44,63,87],text:[230,240,252],muted:[150,172,198],blue:[79,173,255],green:[99,223,177],red:[255,132,142],yellow:[243,200,112]}.freeze
    attr_reader :teams,:buttons
    def initialize
      @teams=BlueBattleLab.preset(true);@names=['Meu time','Adversario'];@side=0;@slot=0
      @format='single';@ai=BlueRadicalAI::CONFIG['defaultProfile'];@tab=:species;@query='';@page=0;@move_slot=0;@row=0;@free_moves=false;@fan=false;@sort=:name
      saved=BlueBattleHub.load_session unless BlueBattleLab::SMOKE
      if saved
        @teams,@names,@format,@ai,rules,quality=saved
        BlueBattleOptions.rules(:lab).merge!(rules) if rules.is_a?(Hash)
        $PokemonSystem.blue_sprite_quality=quality if BlueSpriteQuality::LABELS.key?(quality)
      end
      @dirty=true;@notice='Monte os dois times e entre em batalha contra a IA.'
      @teams=@teams.map { |team| BlueBattleHub.prepare_roster(team) }
    end
    def color(key);Color.new(*COLORS.fetch(key));end
    def rect(x,y,w,h,key)
      @bitmap.fill_rect(x,y,w,h,color(key))
    end
    def text(value,x,y,w,size=19,key=:text)
      @bitmap.font.name=['Arial','Verdana'];@bitmap.font.size=size;@bitmap.font.bold=false;@bitmap.font.color=color(key)
      str=value.to_s.gsub(/\n/,' ')
      while str.length>2 && @bitmap.text_size(str).width>w;str=str[0...-2]+'…';end
      @bitmap.draw_text(x,y,w,30,str)
    end
    def button(id,label,x,y,w,h=32,active=false,&action)
      rect(x,y,w,h,active ? :blue : :field)
      text(label,x+9,y+(h-30)/2,w-18,18,active ? :bg : :text)
      @buttons << {id:id,rect:[x,y,w,h],action:action}
    end
    def inside(point,box);BlueLabPointer.inside?(point,*box);end
    def mon;@teams[@side][@slot];end
    def render
      return unless @canvas
      @buttons=[];@bitmap.clear;rect(0,0,W,H,:bg)
      text('BLUE / HUB DE BATALHA',24,14,480,30)
      text('OFFLINE / CONTRA A IA',440,18,220,16,:blue)
      button(:multiplayer,'MULTIPLAYER',690,14,246,38,true) { start_multiplayer }
      button(:side0,'MEU TIME',24,62,130,34,@side==0) { change_side(0) }
      button(:side1,'ADVERSARIO',162,62,150,34,@side==1) { change_side(1) }
      button(:name,@names[@side],328,62,230) { value=prompt('Nome do time',@names[@side],40);@names[@side]=value if value && !value.strip.empty?;changed }
      button(:save,'Salvar',570,62,84) { save_library }
      button(:library,'Biblioteca',662,62,100) { load_library }
      button(:import,'Importar',770,62,80) { import_menu }
      button(:export,'Exportar',858,62,78) { export_team }
      6.times do |i|
        p=@teams[@side][i];x=24+154*i
        button("slot#{i}".to_sym,'',x,110,144,78,@slot==i) { select_slot(i) }
        if p
          text(p.name,x+10,114,125,17,@slot==i ? :bg : :text)
          text('Nv. '+p.level.to_s,x+63,151,72,16,@slot==i ? :bg : :muted)
        else
          text('+',x+12,129,25,26,@slot==i ? :bg : :blue)
          text('Adicionar',x+46,134,90,17,@slot==i ? :bg : :muted)
        end
      end
      rect(24,204,912,188,:panel)
      if mon
        m=mon
        text(m.species_data.types.map { |t| GameData::Type.get(t).name }.join(' / '),38,355,122,15,:blue)
        button(:species,BlueBattleHub.display(GameData::Species.get(m.instance_variable_get(:@blue_hub_mega) || m.species_data.id)),174,220,232,40,@tab==:species) { tab(:species) }
        button(:nickname,m.nicknamed? ? m.name : 'Apelido...',174,266,232) { value=prompt('Apelido',m.nicknamed? ? m.name : '',24);m.name=value if value;changed }
        button(:item,m.item ? m.item.name : 'Item: nenhum',174,306,232,32,@tab==:item) { tab(:item) }
        button(:ability,m.ability.name,174,346,232,32,@tab==:ability) { tab(:ability) }
        text('Nv. 50 fixo',422,224,85,16,:blue)
        button(:gender,m.genderless? ? 'Sem sexo' : m.female? ? 'Femea' : 'Macho',507,220,89) { m.gender=1-m.gender unless m.genderless?;changed }
        button(:shiny,m.shiny? ? 'Shiny: sim' : 'Shiny: nao',422,262,174,32,m.shiny?) { m.shiny=!m.shiny?;changed }
        button(:tera,'Tera: '+(m.respond_to?(:tera_type) ? GameData::Type.get(m.tera_type).name : '-'),422,304,174,32,@tab==:type) { tab(:type) }
        button(:stats,'Atributos / EVs / IVs',422,346,174,32,@tab==:stats) { tab(:stats) }
        4.times do |i|
          mv=m.moves[i]
          button("move#{i}".to_sym,mv ? mv.name : '+ Adicionar golpe',614,220+42*i,304,34,@tab==:move && @move_slot==i) { @move_slot=i;tab(:move) }
        end
      else
        text('Escolha um Pokemon na lista abaixo.',52,247,730,28)
      end
      rect(24,404,912,244,:panel)
      @tab==:stats && mon ? render_stats : render_picker
      button(:format,@format=='double' ? 'Dupla / 6 escolhe 4' : 'Individual / 1 em campo',24,662,214,38) { @format=@format=='single' ? 'double' : 'single';changed }
      button(:ai,'IA: '+BlueRadicalAI::CONFIG['profiles'][@ai]['label'],248,662,188,38) { keys=BlueRadicalAI::CONFIG['profiles'].keys;@ai=keys[(keys.index(@ai).to_i+1)%keys.length];changed }
      button(:mechanics,'Mecanicas',446,662,110,38) { menu_action { BlueBattleOptions.mechanics_menu(:lab) };changed }
      button(:more,'Opcoes',566,662,86,38) { options_menu }
      button(:battle,'BATALHAR  →',668,662,184,38,true) { start_battle }
      button(:exit,'Sair',862,662,74,38) { @exit=true }
      text(@notice,26,703,908,13,:muted)
      @keyboard_index=[@keyboard_index,@buttons.length-1].min if @keyboard_index
      @dirty=false
    end
    def render_stats
      m=mon;total=m.ev.values.sum
      button(:nature,'Nature: '+m.nature.name,40,414,270,32) { tab(:nature) }
      text("EVs: #{total}/510 · Restam #{510-total}",350,416,470,19,:green)
      text('BASE',182,452,92,14,:muted);text('EVs',338,452,80,14,:muted);text('IVs',718,452,62,14,:muted);text('FINAL',832,452,80,14,:muted)
      final=[m.totalhp,m.attack,m.defense,m.spatk,m.spdef,m.speed]
      STATS.each_with_index do |s,i|
        y=480+26*i;base=m.species_data.base_stats[s]
        text(SHORT[i],40,y,90,18);text(base,120,y,50,18)
        rect(182,y+10,(base*120.0/255).clamp(1,120).to_i,8,:green)
        button("ev#{i}".to_sym,m.ev[s].to_s,328,y,66,25) { v=number(SHORT[i]+' EVs',m.ev[s],0,[252,510-total+m.ev[s]].min);m.ev[s]=v if v;changed }
        rect(412,y+10,274,7,:line);rect(412,y+10,(274*m.ev[s]/252.0).to_i,7,:blue)
        @buttons << {id:"slider#{i}".to_sym,rect:[406,y,286,25],action:proc { @drag_stat=s;drag_ev }}
        button("iv#{i}".to_sym,m.iv[s].to_s,714,y,74,25) { v=number(SHORT[i]+' IVs',m.iv[s],0,31);m.iv[s]=v if v;changed }
        text(final[i],836,y,70,20,:yellow)
      end
    end
    def data_rows
      list=case @tab
      when :species then BlueBattleHub.species.select { |s| !@fan || s.flags.include?('DessastreParadoxal') }
      when :ability then mon ? mon.getAbilityList.map { |a| GameData::Ability.get(a[0]) }.uniq : []
      when :move
        all=[];GameData::Move.each { |m| all << m }
        if mon && !@free_moves
          sp=mon.species_data;ids=(sp.moves.map(&:last)+sp.tutor_moves+sp.egg_moves).uniq
          all=all.select { |m| ids.include?(m.id) }
        end
        all
      else
        all=[];GameData.const_get(@tab.to_s.capitalize).each { |d| all << d };all
      end
      list=list.select { |d| !d.respond_to?(:pseudo_type) || !d.pseudo_type } if @tab==:type
      needle=BlueBattleHub.token(@query)
      list=list.select do |d|
        label=@tab==:species ? BlueBattleHub.display(d)+' '+d.types.join(' ')+' '+(d.abilities+d.hidden_abilities).join(' ') : d.name+' '+d.id.to_s
        BlueBattleHub.token(label).include?(needle)
      end
      list.sort_by { |d| @sort==:bst && @tab==:species ? [-d.base_stats.values.sum,d.id.to_s] : (@tab==:species ? BlueBattleHub.display(d) : d.name).downcase }
    end
    def render_picker
      labels={species:'Pokemon',item:'Item',ability:'Habilidade',move:'Golpe',nature:'Nature',type:'Tera Type'}
      button(:search,(@query.empty? ? 'Buscar '+labels.fetch(@tab,'Pokemon')+'...' : @query)+(@focus ? ' |' : ''),40,416,394,32,@focus) { @focus=true;Input.text_input=true;@dirty=true }
      if @tab==:species
        button(:fan,@fan ? 'Dessastre Paradoxal' : 'Todas as geracoes',446,416,195,32,@fan) { @fan=!@fan;@page=0;@dirty=true }
        button(:sort,@sort==:bst ? 'BST ↓' : 'Nome A–Z',652,416,100) { @sort=@sort==:name ? :bst : :name;@dirty=true }
      elsif @tab==:move
        button(:free,@free_moves ? 'Todos (livre)' : 'Learnset da especie',446,416,240,32,@free_moves) { @free_moves=!@free_moves;@page=0;@dirty=true }
      elsif @tab==:item && mon
        button(:noitem,'Retirar item',446,416,195) { mon.item=nil;mon.instance_variable_set(:@blue_hub_mega,nil);changed }
      end
      list=data_rows;pages=[(list.length/5.0).ceil,1].max;@page=@page.clamp(0,pages-1)
      button(:prev,'‹',776,416,34) { @page=(@page-1).clamp(0,pages-1);@dirty=true }
      text("#{@page+1}/#{pages}",814,417,66,16,:muted)
      button(:next,'›',884,416,34) { @page=(@page+1).clamp(0,pages-1);@dirty=true }
      text('NOME / FORMA',48,452,280,14,:muted)
      if @tab==:species
        text('TIPOS',334,452,145,14,:muted);text('HABILIDADES',488,452,175,14,:muted)
        SHORT.each_with_index { |s,i| text(s.upcase,674+i*30,452,29,11,:muted) };text('BST',862,452,44,13,:muted)
      else
        text('DADOS / DESCRICAO',334,452,568,14,:muted)
      end
      @visible_rows=list[@page*5,5] || []
      @row=@row.clamp(0,[@visible_rows.length-1,0].max)
      @visible_rows.each_with_index do |d,i|
        y=482+32*i
        button("result#{i}".to_sym,'',40,y,878,30,false) { choose_data(d) }
        rect(40,y,3,30,:blue) if i==@row
        if @tab==:species
          text(BlueBattleHub.display(d),48,y,280,17)
          text(d.types.map { |t| GameData::Type.get(t).name }.join('/'),334,y,154,15,:blue)
          text((d.abilities+d.hidden_abilities).uniq.map { |a| GameData::Ability.get(a).name }.join('/'),488,y,177,14,:muted)
          STATS.each_with_index { |s,j| text(d.base_stats[s],674+j*30,y,29,14) }
          text(d.base_stats.values.sum,862,y,44,15,:green)
        else
          text(d.name,48,y,270,18)
          detail=case @tab
          when :move then "#{GameData::Type.get(d.type).name} · #{['Fisico','Especial','Status'][d.category]} · Poder #{d.power} · Acerto #{d.accuracy} · PP #{d.total_pp} · #{d.description}"
          when :nature then d.stat_changes.empty? ? 'Neutra' : d.stat_changes.map { |s,n| (n>0 ? '+' : '')+n.to_s+' '+s.to_s }.join(' / ')
          else d.respond_to?(:description) ? d.description : d.name
          end
          text(detail,334,y,568,15,:muted)
        end
      end
      text('Nenhum resultado. Tente outro nome ou filtro.',48,518,820,20,:muted) if list.empty?
    end
    def tab(kind)
      @tab=kind;@query='';@page=0;@row=0;@focus=false;Input.text_input=false;@dirty=true
    end
    def changed(persist=true)
      @teams.flatten.each do |pokemon|
        next if pokemon.level==BlueBattleHub::LEVEL
        pokemon.level=BlueBattleHub::LEVEL;pokemon.calc_stats;pokemon.heal
      end
      mon&.calc_stats;mon&.heal;@dirty=true;@portrait_dirty=true
      BlueBattleHub.save_session(@teams,@names,@format,@ai) if persist
    rescue StandardError=>e
      @notice='Nao foi possivel salvar: '+e.message;@dirty=true
    end
    def change_side(side);@side=side;@slot=[@slot,@teams[@side].length-1].min;@slot=0 if @slot<0;@portrait_dirty=true;tab(:species);end
    def select_slot(i)
      @slot=[i,@teams[@side].length].min;@portrait_dirty=true;tab(:species)
    end
    def choose_data(data)
      case @tab
      when :species
        p=BlueBattleLab.build(data.id,BlueBattleHub::LEVEL)
        if data.mega_stone || data.mega_move
          base=GameData::Species.get_species_form(data.species,data.unmega_form)
          p=BlueBattleLab.build(base.id,p.level);p.item=data.mega_stone if data.mega_stone
          p.learn_move(data.mega_move) if data.mega_move
          p.instance_variable_set(:@blue_hub_mega,data.id)
        end
        p.moves=p.moves.map { |m| BlueBattleHub.make_move(m.id) }
        @teams[@side][@slot]=p
      when :item then mon.item=data.id;mon.instance_variable_set(:@blue_hub_mega,nil);mon.instance_variable_set(:@blue_hub_source_item,nil)
      when :ability then mon.ability_index=mon.getAbilityList.find { |a| a[0]==data.id }[1]
      when :move
        if mon.moves.any? { |m| m.id==data.id } && mon.moves[@move_slot]&.id!=data.id
          @notice='Esse golpe ja esta no moveset.';@dirty=true;return
        end
        slot=[@move_slot,mon.moves.length].min;mon.moves[slot]=BlueBattleHub.make_move(data.id)
      when :nature then mon.nature=data.id;@tab=:stats
      when :type then mon.tera_type=data.id
      end
      @notice='Configuracao atualizada. Time salvo nesta instalacao do Hub.';changed
    end
    def update_portraits
      return unless @portrait_dirty
      @decorations&.each(&:dispose);@decorations=[]
      @teams[@side].each_with_index do |p,i|
        icon=PokemonIconSprite.new(p,@viewport);icon.x=32+i*154;icon.y=136;icon.zoom_x=icon.zoom_y=0.7;icon.z=3;@decorations << icon
      end
      if mon
        p=mon.clone;target=p.instance_variable_get(:@blue_hub_mega);p.form=GameData::Species.get(target).form if target
        portrait=PokemonSprite.new(@viewport);portrait.setPokemonBitmap(p);portrait.x=96;portrait.y=340;portrait.z=4
        size=[portrait.src_rect.width,portrait.src_rect.height,1].max
        scale=[124.0/size,1.5].min;portrait.zoom_x=portrait.zoom_y=scale
        portrait.setOffset(PictureOrigin::BOTTOM);@decorations << portrait
      end
      @portrait_dirty=false
    end
    def mount
      Graphics.resize_screen(W,H)
      # The window keeps its old corner when it grows; on small screens the bottom buttons would be cut off.
      Graphics.center if Graphics.respond_to?(:center)
      @viewport=Viewport.new(0,0,W,H);@viewport.z=99999
      @canvas=BitmapSprite.new(W,H,@viewport);@bitmap=@canvas.bitmap;@decorations=[]
      @portrait_dirty=true;render;update_portraits;Graphics.transition(0);Input.update
    end
    def unmount
      @focus=false;Input.text_input=false
      @decorations&.each(&:dispose);@decorations=[]
      @canvas&.dispose;@viewport&.dispose;@canvas=nil
    end
    def run
      @original_size=[Graphics.width,Graphics.height];mount
      BlueBattleLab.log('MENU_READY | hub=true native=true teams=6x6')
      until @exit
        frame
      end
      changed
    ensure
      unmount
      Graphics.resize_screen(*@original_size) if @original_size
      BlueBattleLab.log('HUB_CLOSED | campaign save untouched')
    end
    def frame
      Graphics.update;Input.update
      @decorations.each(&:update)
      handle_input
      render if @dirty;update_portraits
    end
    def handle_input
      point=Mouse.getMousePos
      if @drag_stat
        if Input.press?(Input::MOUSELEFT);drag_ev;else;@drag_stat=nil;changed;end
      elsif Input.trigger?(Input::MOUSELEFT)
        hit=@buttons.reverse.find { |b| inside(point,b[:rect]) }
        if hit
          @keyboard_index=nil
          @focus=false;Input.text_input=false;hit[:action].call
        end
      end
      if @focus
        if Input.triggerex?(:ESCAPE);@focus=false;Input.text_input=false;@dirty=true
        elsif Input.triggerex?(:RETURN);choose_data(@visible_rows[@row]) if @visible_rows && !@visible_rows.empty?;@focus=false;Input.text_input=false
        elsif Input.triggerex?(:DOWN) || Input.repeatex?(:DOWN);@row=(@row+1).clamp(0,[@visible_rows.length-1,0].max);@dirty=true
        elsif Input.triggerex?(:UP) || Input.repeatex?(:UP);@row=(@row-1).clamp(0,[@visible_rows.length-1,0].max);@dirty=true
        elsif Input.press?(Input::CTRL) && Input.triggerex?(:A);@query='';@row=0;@page=0;@dirty=true
        elsif Input.press?(Input::CTRL) && Input.triggerex?(:V);@query=Input.clipboard.to_s.gsub(/[\r\n]/,' ')[0,48];@row=0;@page=0;@dirty=true
        elsif Input.triggerex?(:BACKSPACE) || Input.repeatex?(:BACKSPACE);@query=@query[0...-1];@row=0;@page=0;@dirty=true
        else
          chars=Input.gets
          unless chars.empty?;@query=(@query+chars.gsub(/[\r\n]/,''))[0,48];@row=0;@page=0;@dirty=true;end
        end
      elsif Input.trigger?(Input::BACK)
        @exit=true if confirm('Sair do Hub de Batalha?')
      elsif Input.triggerex?(:TAB)
        @keyboard_index=((@keyboard_index || -1)+1)%@buttons.length;@notice='Teclado: '+@buttons[@keyboard_index][:id].to_s+' / Enter para escolher';@dirty=true
      elsif Input.triggerex?(:RETURN) && @keyboard_index
        @buttons[@keyboard_index][:action].call
      elsif Input.trigger?(Input::DOWN) && @visible_rows && @tab!=:stats
        @keyboard_index=nil;@row=(@row+1).clamp(0,[@visible_rows.length-1,0].max);@dirty=true
      elsif Input.trigger?(Input::UP) && @visible_rows && @tab!=:stats
        @keyboard_index=nil;@row=(@row-1).clamp(0,[@visible_rows.length-1,0].max);@dirty=true
      elsif Input.triggerex?(:RETURN) && @visible_rows && @tab!=:stats && !@visible_rows.empty?
        choose_data(@visible_rows[@row])
      end
    rescue StandardError=>e
      @notice=e.message;@dirty=true;BlueBattleLab.log('HUB_UI_ERROR | '+e.message+' '+e.backtrace.first.to_s)
    end
    def drag_ev
      point=Mouse.getMousePos;return unless point && mon
      max=[252,510-mon.ev.values.sum+mon.ev[@drag_stat]].min
      mon.ev[@drag_stat]=(((point[0]-412)*252.0/274).round).clamp(0,max)
      changed(false)
    end
    def menu_action
      @focus=false;Input.text_input=false
      @decorations.each { |s| s.visible=false }
      result=yield
      result
    ensure
      @decorations.each { |s| s.visible=true };@dirty=true;Input.update
    end
    def choose(title,labels,default=0)
      menu_action { BlueBattleLab.choose(title,labels,default) }
    end
    def confirm(title);choose(title,['Sim','Cancelar'])==0;end
    def prompt(title,value='',max=256)
      overlay=BitmapSprite.new(W,H,@viewport);overlay.z=100;backup=@bitmap;@bitmap=overlay.bitmap
      input=value.to_s;selected=true;Input.text_input=true;Input.update
      loop do
        @bitmap.clear;rect(102,220,756,242,:panel);text(title,126,236,706,24)
        rect(126,294,708,48,:field);text(input+'|',138,300,684,21)
        text('Digite ou Ctrl+V para colar. Ctrl+A seleciona. Enter confirma.',126,347,708,17,:muted)
        rect(552,394,134,38,:blue);text('Confirmar',568,398,102,19,:bg)
        rect(700,394,134,38,:field);text('Cancelar',716,398,102,19)
        Graphics.update;Input.update
        point=Mouse.getMousePos;click=Input.trigger?(Input::MOUSELEFT)
        return input if Input.triggerex?(:RETURN) || (click && inside(point,[552,394,134,38]))
        return nil if Input.triggerex?(:ESCAPE) || (click && inside(point,[700,394,134,38]))
        if Input.press?(Input::CTRL) && Input.triggerex?(:A);selected=true
        elsif Input.press?(Input::CTRL) && Input.triggerex?(:V)
          clip=Input.clipboard.to_s.gsub(/[\r\n]/,' ');input=selected ? clip[0,max] : (input+clip)[0,max];selected=false
        elsif Input.triggerex?(:BACKSPACE) || Input.repeatex?(:BACKSPACE)
          input=selected ? '' : input[0...-1];selected=false
        else
          chars=Input.gets.gsub(/[\r\n]/,'')
          unless chars.empty?;input=selected ? chars[0,max] : (input+chars)[0,max];selected=false;end
        end
      end
    ensure
      Input.text_input=false;overlay&.dispose;@bitmap=backup;@dirty=true;Input.update
    end
    def number(title,current,min,max)
      value=prompt(title+' / '+min.to_s+' a '+max.to_s,current.to_s,4)
      return nil unless value
      raise ImportError,'Digite um numero entre '+min.to_s+' e '+max.to_s unless value.match?(/\A\d+\z/) && value.to_i.between?(min,max)
      value.to_i
    end
    def import_menu
      selection=choose('Importar para '+@names[@side],['Colar time ou link da area de transferencia','Digitar link Pokepaste','Times prontos por jogo e regulamento','Voltar'])
      return import_preset if selection==2
      return unless [0,1].include?(selection)
      raw=selection==0 ? Input.clipboard.to_s : prompt('Link https://pokepast.es/...','',2048)
      return if raw.nil?
      raise ImportError,'A area de transferencia esta vazia. Copie o link ou o texto do time primeiro.' if raw.strip.empty?
      if raw.strip.start_with?('https://')
        raw=fetch_with_progress(raw)
        return unless raw
      end
      confirm_import(raw)
    rescue StandardError=>error
      @notice='Importacao nao aplicada: '+error.message;@dirty=true
      BlueBattleLab.log('HUB_IMPORT_ERROR | '+error.message)
      choose('Nao foi possivel importar. Seu time foi mantido.',error.message.scan(/.{1,62}/)+['Voltar'])
    end
    def import_preset
      path='Data/blue-hub-presets.dat'
      raise ImportError,'Catalogo de times ausente. Atualize a instalacao.' unless File.file?(path)
      data=load_data(path);raise ImportError,'Catalogo de times invalido.' unless data.is_a?(Array) && data[0]==1
      rows=data[1];games=rows.map { |row| row[0] }.uniq
      g=choose('Times prontos / jogo',games+['Voltar']);return unless g>=0 && g<games.length
      regs=rows.select { |r| r[0]==games[g] }.map { |r| r[1] }.uniq
      r=choose(games[g]+' / regulamento',regs.map { |v| 'Regulamento '+v }+['Voltar']);return unless r>=0 && r<regs.length
      teams=rows.select { |row| row[0]==games[g] && row[1]==regs[r] }
      n=choose('Regulamento '+regs[r]+' / time',teams.map { |row| row[2]+(row[6] ? '' : ' [indisponivel]') }+['Voltar'])
      return unless n>=0 && n<teams.length
      team=teams[n];raise ImportError,'Este Pokepaste nao estava disponivel na ultima sincronizacao.' unless team[6]
      confirm_import(team[5],team[4].to_sym)
    end
    def confirm_import(raw,format_hint=nil)
      format=format_hint || :classic
      if !format_hint && BlueBattleHub.champions_candidate?(raw)
        mode=choose('Valores ate 32: qual e o formato dos atributos?',['Champions: converter pontos para EVs (limite 510)','EVs classicos: manter valores literais','Cancelar'])
        return unless [0,1].include?(mode)
        format=:champions if mode==0
      end
      entries=BlueBattleHub.preview(raw,format);valid=entries.select { |e| e['pokemon'] };bad=entries.select { |e| e['error'] }
      lines=entries.map do |e|
        if e['error'];'ERRO '+e['name']+': '+e['error']
        else
          note=e['pokemon'].instance_variable_get(:@blue_hub_import_note)
          'OK '+e['name']+(note ? ' / '+note : '')
        end
      end
      title=bad.empty? ? "Importar #{valid.length} Pokemon para #{@names[@side]}?" : "#{bad.length} incompatibilidade(s). Confira a lista; nada foi aplicado."
      command=-1
      loop do
        command=choose(title,lines+[valid.empty? ? 'Nenhum Pokemon compativel' : "IMPORTAR #{valid.length} COMPATIVEIS (substituir time)",'Cancelar'],lines.length)
        break unless command>=0 && command<lines.length
        choose('Detalhe da importacao',lines[command].scan(/.{1,65}/)+['Voltar'])
      end
      return unless command==lines.length && !valid.empty?
      @teams[@side]=valid.map { |e| e['pokemon'] };@slot=0
      @notice=bad.empty? ? 'Time importado no nivel 50. '+(format==:champions ? 'Pontos Champions convertidos; confira os atributos.' : 'EVs/IVs preservados.') : 'Importados apenas os Pokemon compativeis que voce confirmou.'
      changed
    end
    def fetch_with_progress(raw)
      raise ImportError,'No Android, use Times prontos ou cole o texto do time. O download por link requer o auxiliar Python do Windows.' if defined?(BlueMobile) && BlueMobile.enabled?
      url=BlueBattleHub.url(raw)
      config='Data/blue-hub-python.txt'
      raise ImportError,'Reabra HUB_DE_BATALHA.bat para preparar a importacao.' unless File.file?(config)
      python=File.read(config,encoding:'UTF-8').strip
      path=File.expand_path("Data/blue-hub-import-#{Process.pid}-#{rand(1000000000)}.txt")
      worker=File.expand_path('Plugins/ZZZZ Blue Battle Lab/pokepaste.py')
      # HTTPLite is an engine API and is unsafe on a Ruby background thread.
      # A bounded helper process downloads bytes while the native UI keeps running.
      pid=Process.spawn(python,worker,url,path,out:File::NULL,err:File::NULL)
      waiter=Process.detach(pid)
      started=System.uptime
      until File.file?(path)
        @notice='Baixando Pokepaste... Esc cancela.';render;Graphics.update;Input.update
        if Input.trigger?(Input::BACK) || System.uptime-started>25
          raise ImportError,'Download cancelado ou tempo esgotado. Voce tambem pode colar o texto do time.'
        end
        raise ImportError,'O processo de download encerrou sem resposta. Reabra o Hub pelo atalho.' unless waiter.alive? || File.file?(path)
      end
      result=File.read(path,encoding:'UTF-8');status,body=result.split("\n",2)
      raise ImportError,body.to_s unless status=='OK'
      raise ImportError,'Pokepaste vazio ou muito grande.' unless body && body.bytesize.between?(1,65536)
      body
    ensure
      begin;Process.kill('KILL',pid) if waiter && waiter.alive?;rescue Errno::ESRCH,Errno::EINVAL;end
      [path,path && path+'.tmp'].compact.each { |p| File.delete(p) if File.file?(p) }
      @dirty=true
    end
    def save_library
      path=BlueBattleHub.save_team(@teams[@side],@names[@side]);@notice='Time salvo na biblioteca: '+File.basename(path);@dirty=true
    end
    def load_library
      files=BlueBattleHub.library
      if files.empty?;@notice='Biblioteca vazia. Use Salvar para guardar um time.';@dirty=true;return;end
      labels=files.map { |f| File.open(f,'rb', &:readline).strip.sub(/^# /,'') rescue File.basename(f) }
      i=choose('Biblioteca / carregar em '+@names[@side],labels+['Voltar'])
      return if i<0 || i>=files.length
      entries=BlueBattleHub.preview(File.read(files[i],encoding:'UTF-8'))
      raise ImportError,entries.filter_map { |e| e['error'] }.join(' ') if entries.any? { |e| e['error'] }
      @teams[@side]=entries.map { |e| e['pokemon'] };@names[@side]=labels[i];@slot=0;changed
    end
    def export_team
      Input.clipboard=BlueBattleHub.export(@teams[@side]);@notice='Time copiado em formato Showdown / Pokepaste. Cole para compartilhar.';@dirty=true
    end
    def options_menu
      i=choose('Opcoes do Hub',['Qualidade dos sprites','Mover este Pokemon para o primeiro slot','Remover este Pokemon','Preparar times oficiais','Preparar times Dessastre Paradoxal','Voltar'])
      case i
      when 0 then menu_action { BlueBattleOptions.quality_menu }
      when 1 then @teams[@side].unshift(@teams[@side].delete_at(@slot)) if mon;@slot=0
      when 2
        if mon && @teams[@side].length>1;@teams[@side].delete_at(@slot);@slot=[@slot,@teams[@side].length-1].min
        else;@notice='Mantenha pelo menos um Pokemon no time.';end
      when 3 then @teams=BlueBattleLab.preset;@slot=0
      when 4 then @teams=BlueBattleLab.preset(true);@slot=0
      end
      changed
    end
    def start_battle
      BlueBattleLab.validate_teams(*@teams,@format)
      if @format=='double' && @teams.any? { |team| team.length!=6 }
        choose('Duplas: prepare seis Pokemon em cada time.',['Voce escolhe quatro na tela seguinte.','Voltar']);return
      end
      parties=@teams.map { |team| BlueBattleHub.prepare_roster(team) }
      changed;unmount;Graphics.resize_screen(*@original_size)
      if @format=='double'
        parties=select_four(parties)
        return unless parties
        Graphics.resize_screen(*@original_size)
      end
      result=BlueBattleLab.battle(*parties,false,@format,@ai)
      @notice={1=>'Vitoria!',2=>'Derrota.',3=>'Batalha encerrada.',5=>'Empate.'}[result] || 'Batalha concluida.'
    ensure
      mount unless @canvas
    end
    def select_four(parties)
      PickFour.new(parties,@names).run
    end
  end
  module HubScene
    def main
      return super if BlueBattleLab::SMOKE
      BlueBattleLab.setup
      Screen.new.run
      $scene=nil
    rescue StandardError=>e
      BlueBattleLab.log("HUB_ERROR | #{e.class}: #{e.message}\n#{e.backtrace.join("\n")}")
      raise
    end
  end
end
BlueBattleLab::Scene.prepend(BlueBattleHub::HubScene)
