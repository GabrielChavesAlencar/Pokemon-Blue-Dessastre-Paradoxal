# Original in-game shop: native scrolling windows and bag/money transactions.
module BlueCampaign
  def self.shop_name(item)
    return item.name unless item.is_machine? && GameData::Move.exists?(item.move)
    item.name+' '+GameData::Move.get(item.move).name
  end
  class ShopList < Window_CommandPokemon
    def drawItem(index,_count,rect)
      rect=drawCursor(index,rect)
      rect.width=[rect.width-12,1].max
      contents.font.name=['Arial','Verdana'];contents.font.size=18
      name,separator,cost=@commands[index].rpartition('  $')
      if separator.empty?
        name=@commands[index];cost=''
      else
        cost='$'+cost
      end
      price_width=contents.text_size(cost).width+8
      width=rect.width-price_width
      label=name.dup
      label=label[0...-1] while label.length>1 && contents.text_size(label+'…').width>width
      label+='…' if label!=name
      pbDrawShadowText(contents,rect.x,rect.y,width,rect.height,label,baseColor,shadowColor)
      pbDrawShadowText(contents,rect.x+width,rect.y,price_width,rect.height,cost,baseColor,shadowColor,2)
    end
  end
  class Shop
    PAGE_SIZE=5
    FILTERS=['Todos','Posso comprar','Nao possuo','Na mochila'].freeze
    def draw_text(bitmap,x,y,w,h,text,size=18,color=Color.new(222,236,250))
      bitmap.font.name=['Arial','Verdana'];bitmap.font.size=size;bitmap.font.color=color
      bitmap.draw_text(x,y,w,h,text)
    end
    def refresh
      b=@background.bitmap;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(11,20,34))
      b.fill_rect(0,0,Graphics.width,42,Color.new(24,47,73))
      draw_text(b,14,7,220,28,'BLUE / POKE MART',23)
      draw_text(b,Graphics.width-188,7,180,28,'$ '+$player.money.to_s_formatted,21,Color.new(113,229,178))
      BlueCampaign::TABS.each_with_index do |name,i|
        x=8+(i%4)*((Graphics.width-16)/4);y=48+(i/4)*26;w=(Graphics.width-20)/4
        b.fill_rect(x,y,w,23,i==@tab ? Color.new(42,128,179) : Color.new(27,44,63))
        draw_text(b,x+6,y,w-8,23,name,17)
      end
      b.fill_rect(8,104,306,28,Color.new(27,44,63))
      draw_text(b,14,104,292,28,@query.to_s.empty? ? 'Pesquisar item / golpe [F]' : 'Busca: '+@query.to_s,17)
      b.fill_rect(322,104,Graphics.width-332,28,Color.new(27,44,63))
      draw_text(b,330,104,170,28,FILTERS[@filter || 0]+' [Filtro]',16)
      b.fill_rect(322,138,Graphics.width-332,196,Color.new(21,36,54))
      @query ||= '';@filter ||= 0;@page ||= 0;@catalog ||= {}
      rows=(@catalog[@tab] ||= BlueCampaign.stock(@tab).map do |id|
        item=GameData::Item.get(id);name=BlueCampaign.shop_name(item)
        {id:id,name:name,cost:BlueCampaign.price(item),token:BlueBattleHub.token(name+' '+id.to_s)}
      end)
      needle=BlueBattleHub.token(@query)
      rows=rows.select do |row|
        owned=$bag.has?(row[:id]);item=GameData::Item.get(row[:id])
        row[:token].include?(needle) && case @filter
        when 1 then row[:cost]<=$player.money && !(item.is_important? && owned)
        when 2 then !owned
        when 3 then owned
        else true
        end
      end
      @stock=rows.map { |row| row[:id] };@pages=[(rows.length.to_f/PAGE_SIZE).ceil,1].max;@page=@page.clamp(0,@pages-1)
      commands=rows.slice(@page*PAGE_SIZE,PAGE_SIZE).to_a.map { |row| row[:name]+'  $'+row[:cost].to_s_formatted }
      @list.commands=commands.empty? ? ['Sem itens nesta aba'] : commands
      @list.index=0;@last_index=nil
      draw_text(b,12,338,135,28,'< Anterior',17)
      draw_text(b,145,338,180,28,"#{@page+1}/#{@pages} · #{@stock.length} itens",16)
      draw_text(b,330,338,120,28,'Proxima >',17)
      draw_text(b,452,338,60,28,'Sair',16)
      draw_text(b,12,367,Graphics.width-24,17,'Setas: abas / lista · Q/E: pagina · Enter: comprar · Esc: sair',13)
      details
    end
    def details
      return if @last_index==@list.index
      @last_index=@list.index;b=@details.bitmap;b.clear
      id=@stock[@page*PAGE_SIZE+@list.index]
      if @last_icon!=id;@icon.item=id;@last_icon=id;end
      return unless id
      item=GameData::Item.get(id)
      draw_text(b,0,0,170,24,'Na mochila: '+$bag.quantity(id).to_s,17)
      draw_text(b,0,24,138,26,GameData::Move.get(item.move).name,17) if item.is_machine? && GameData::Move.exists?(item.move)
      words=item.description.split;lines=['']
      words.each do |word|
        candidate=(lines[-1]+' '+word).strip
        b.font.size=17
        if b.text_size(candidate).width>158 && !lines[-1].empty?
          lines << word
        else
          lines[-1]=candidate
        end
      end
      lines.first(7).each_with_index { |line,i| draw_text(b,0,70+i*17,166,20,line,17) }
    end
    def buy
      id=@stock[@page*PAGE_SIZE+@list.index];return unless id
      item=GameData::Item.get(id);cost=BlueCampaign.price(item)
      return pbMessage('Voce ja possui este equipamento.') if item.is_important? && $bag.has?(id)
      return pbMessage('Dinheiro insuficiente.') if $player.money<cost
      max=[Settings::BAG_MAX_PER_SLOT,$player.money/cost].min
      max=1 if item.is_important?
      params=ChooseNumberParams.new;params.setRange(1,max);params.setInitialValue(1);params.setCancelValue(0)
      qty=max==1 ? 1 : pbMessageChooseNumber('Quantos '+BlueCampaign.shop_name(item)+'? Preco unitario: $'+cost.to_s_formatted,params)
      return if qty<=0
      return unless pbConfirmMessage('Comprar '+qty.to_s+' x '+BlueCampaign.shop_name(item)+' por $'+(cost*qty).to_s_formatted+'?')
      result=BlueCampaign.purchase(id,qty)
      pbMessage(result==:ok ? 'Compra realizada!' : {funds:'Dinheiro insuficiente.',full:'Sem espaco na mochila.',owned:'Equipamento ja adquirido.'}[result] || 'Este item nao esta disponivel.')
      selected=@list.index;refresh;@list.index=selected.clamp(0,[@list.itemCount-1,0].max);details
    end
    def page(delta)
      @page=(@page+delta).clamp(0,@pages-1);refresh
    end
    def search
      @viewport.visible=false
      value=BlueMenuSupport.entry('Pesquisar item ou golpe',@query,32)
      if value;@query=value;@page=0;refresh;end
    ensure
      @viewport.visible=true;Input.update
    end
    def filters
      @viewport.visible=false
      choice=BlueBattleLab.choose('Filtrar itens',FILTERS+['Voltar'],@filter)
      if choice>=0 && choice<FILTERS.length;@filter=choice;@page=0;refresh;end
    ensure
      @viewport.visible=true;Input.update
    end
    def open
      @tab=0;@query='';@filter=0;@page=0;@viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=99999
      @background=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
      @list=ShopList.newWithSize([],8,134,306,200,@viewport)
      @list.active=true;@list.z=2
      @details=BitmapSprite.new(172,196,@viewport);@details.x=332;@details.y=138
      @icon=ItemIconSprite.new(493,164,nil,@viewport);@icon.zoom_x=@icon.zoom_y=0.5
      refresh
      if block_given?
        Graphics.update;yield self
        return
      end
      loop do
        Graphics.update;Input.update;@list.update;@icon.update
        break if Input.trigger?(Input::BACK)
        if Input.triggerex?(:F);search;next;end
        if Input.trigger?(Input::JUMPUP);page(-1);next;end
        if Input.trigger?(Input::JUMPDOWN);page(1);next;end
        target=nil
        target=(@tab-1)%BlueCampaign::TABS.length if Input.trigger?(Input::LEFT)
        target=(@tab+1)%BlueCampaign::TABS.length if Input.trigger?(Input::RIGHT)
        if Input.trigger?(Input::MOUSELEFT)
          point=BlueLabPointer.position
          if point && point[1]>=48 && point[1]<100 && point[0]>=8 && point[0]<Graphics.width-8
            target=(point[1]-48)/26*4+(point[0]-8)/((Graphics.width-16)/4)
          elsif BlueLabPointer.inside?(point,8,104,306,28)
            search;next
          elsif BlueLabPointer.inside?(point,322,104,190,28)
            filters;next
          elsif point && point[1]>=338 && point[1]<366
            break if point[0]>=452
            page(point[0]<145 ? -1 : 1);next
          end
        end
        if target && target>=0 && target<BlueCampaign::TABS.length && target!=@tab
          @tab=target;@page=0;refresh
        elsif Input.trigger?(Input::USE)
          buy
        end
        details
      end
    ensure
      [@icon,@details,@list,@background,@viewport].each { |s| s.dispose if s && !s.disposed? }
      Input.update
    end
  end
  def self.shop
    pbFadeOutIn { Shop.new.open }
  end
end
