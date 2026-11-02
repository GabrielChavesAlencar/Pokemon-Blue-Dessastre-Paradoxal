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
      b.fill_rect(322,108,Graphics.width-332,230,Color.new(21,36,54))
      draw_text(b,12,Graphics.height-34,Graphics.width-24,28,'Setas / abas: categoria     Confirmar: comprar     Esc: sair',16)
      @stock=BlueCampaign.stock(@tab)
      commands=@stock.map { |id| i=GameData::Item.get(id);BlueCampaign.shop_name(i)+'  $'+BlueCampaign.price(i).to_s_formatted }
      @list.commands=commands.empty? ? ['Sem itens nesta aba'] : commands
      @list.index=0;@last_index=nil
      details
    end
    def details
      return if @last_index==@list.index
      @last_index=@list.index;b=@details.bitmap;b.clear
      id=@stock[@list.index]
      @icon.item=id
      return unless id
      item=GameData::Item.get(id)
      draw_text(b,0,0,170,24,'Na mochila: '+$bag.quantity(id).to_s,17)
      draw_text(b,0,24,170,26,GameData::Move.get(item.move).name,17) if item.is_machine? && GameData::Move.exists?(item.move)
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
      lines.first(9).each_with_index { |line,i| draw_text(b,0,70+i*17,166,20,line,17) }
    end
    def buy
      id=@stock[@list.index];return unless id
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
      selected=@list.index;refresh;@list.index=selected;details
    end
    def open
      @tab=0;@viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=99999
      @background=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
      @list=ShopList.newWithSize([],8,106,306,238,@viewport)
      @list.active=true;@list.z=2
      @details=BitmapSprite.new(172,238,@viewport);@details.x=332;@details.y=112
      @icon=ItemIconSprite.new(410,162,nil,@viewport)
      refresh
      if block_given?
        Graphics.update;yield self
        return
      end
      loop do
        Graphics.update;Input.update;@list.update;@icon.update
        break if Input.trigger?(Input::BACK)
        target=nil
        target=(@tab-1)%BlueCampaign::TABS.length if Input.trigger?(Input::LEFT)
        target=(@tab+1)%BlueCampaign::TABS.length if Input.trigger?(Input::RIGHT)
        if Input.trigger?(Input::MOUSELEFT)
          point=Mouse.getMousePos
          if point && point[1]>=48 && point[1]<100 && point[0]>=8 && point[0]<Graphics.width-8
            target=(point[1]-48)/26*4+(point[0]-8)/((Graphics.width-16)/4)
          end
        end
        if target && target>=0 && target<BlueCampaign::TABS.length && target!=@tab
          @tab=target;refresh
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
