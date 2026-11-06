# Return the native storage selector values; all move/deposit/release checks stay
# in PokemonStorageScreen, including the last usable party Pokemon safeguard.
module BlueStorageMouse
  module Scene
    def pbSelectBoxInternal(party)
      previous=@blue_storage_scope;@blue_storage_scope=:box
      loop do
        result=catch(:blue_storage_click) { super }
        return result unless result==:blue_storage_again
      end
    ensure
      @blue_storage_scope=previous
    end
    def pbSelectPartyInternal(party,depositing)
      previous=@blue_storage_scope;@blue_storage_scope=depositing ? :deposit : :party
      catch(:blue_storage_click) { super }
    ensure
      @blue_storage_scope=previous
    end
    def blue_storage_hit(point)
      return nil unless point
      if @blue_storage_scope==:box
        box=@sprites['box'];x,y=BlueLabPointer.origin(box)
        if BlueLabPointer.inside?(point,x+10,y+30,PokemonBox::BOX_WIDTH*48,PokemonBox::BOX_HEIGHT*48)
          return ((point[1]-y-30)/48).floor*PokemonBox::BOX_WIDTH+((point[0]-x-10)/48).floor
        end
        return :left if BlueLabPointer.inside?(point,x,y,32,54)
        return :right if BlueLabPointer.inside?(point,x+box.bitmap.width-32,y,32,54)
        return -1 if BlueLabPointer.inside?(point,x+32,y,box.bitmap.width-64,30)
        return -2 if BlueLabPointer.inside?(point,190,316,160,52)
        return -3 if BlueLabPointer.inside?(point,362,316,146,52)
      else
        panel=@sprites['boxparty'];x,y=BlueLabPointer.origin(panel)
        Settings::MAX_PARTY_SIZE.times do |i|
          return i if BlueLabPointer.inside?(point,x+18+72*(i%2),y+2+16*(i%2)+64*(i/2),64,56)
        end
        return Settings::MAX_PARTY_SIZE if BlueLabPointer.inside?(point,x,y+240,172,56)
      end
      nil
    end
    def update
      super
      return unless @blue_storage_scope && BlueStartMouse.click?
      target=blue_storage_hit(BlueLabPointer.position);return if target.nil?
      BlueLabPointer.claimed=true
      if @blue_storage_scope==:box
        if [:left,:right].include?(target)
          return if @multi && @grabber && @grabber.holding_anything? && !@grabber.carrying
          nextbox=(@storage.currentBox+(target==:left ? -1 : 1))%@storage.maxBoxes
          target==:left ? pbSwitchBoxToLeft(nextbox) : pbSwitchBoxToRight(nextbox)
          @storage.currentBox=nextbox
          throw :blue_storage_click,:blue_storage_again
        end
        return if target==-2 && @multi
        @selection=target;pbSetArrow(@sprites['arrow'],target);pbUpdateOverlay(target);pbSetMosaic(target)
        value=target>=0 ? [@storage.currentBox,target] : (target==-1 ? [-4,-1] : [target,-1])
        throw :blue_storage_click,value
      else
        @selection=target;pbPartySetArrow(@sprites['arrow'],target)
        value=target<Settings::MAX_PARTY_SIZE ? target : (@blue_storage_scope==:deposit ? -3 : -1)
        throw :blue_storage_click,value
      end
    end
  end
end
