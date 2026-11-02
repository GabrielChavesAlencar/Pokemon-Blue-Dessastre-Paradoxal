# Feed the native local selection loop; it retains move restrictions and confirmations.
module BlueLearnMouse
  def pbChooseMoveToForget(move_to_learn)
    @blue_move_picking=true;@blue_move_new=move_to_learn;@blue_move_target=nil
    unless @sprites['blueCancelLearn']
      button=BitmapSprite.new(216,28,@viewport);button.x=8;button.y=352;button.z=50
      button.bitmap.fill_rect(0,0,216,28,Color.new(24,62,91));pbSetSmallFont(button.bitmap)
      button.bitmap.font.color=Color.new(240,248,255);button.bitmap.draw_text(0,0,216,28,_INTL('Cancel / Back'),1)
      @sprites['blueCancelLearn']=button
    end
    @sprites['blueCancelLearn'].visible=true
    super
  ensure
    @blue_move_picking=false;@blue_move_target=nil
    @sprites['blueCancelLearn'].visible=false if @sprites['blueCancelLearn'] && !@sprites['blueCancelLearn'].disposed?
  end
  def pbUpdate
    super
    return unless @blue_move_picking
    cursor=@sprites['movesel'];return unless cursor && !cursor.disposed?
    if BlueStartMouse.click?
      point=BlueLabPointer.position
      if BlueLabPointer.hit_sprite?(@sprites['blueCancelLearn'],point)
        @blue_move_target=nil;BlueLabPointer.emit(Input::BACK);return
      end
      base=cursor.y-cursor.index*64-(@blue_move_new && cursor.index==Pokemon::MAX_MOVES ? 20 : 0)
      indices=(0...@pokemon.numMoves).to_a;indices << Pokemon::MAX_MOVES if @blue_move_new
      selected=indices.find do |i|
        y=base+i*64+(@blue_move_new && i==Pokemon::MAX_MOVES ? 20 : 0)
        BlueLabPointer.inside?(point,cursor.x,y,[cursor.src_rect.width,Graphics.width-cursor.x].min,64)
      end
      if selected;@blue_move_target=selected;BlueLabPointer.claimed=true;end
    end
    return if @blue_move_target.nil?
    if cursor.index==@blue_move_target
      @blue_move_target=nil;BlueLabPointer.emit(Input::USE)
    else
      BlueLabPointer.emit(@blue_move_target>cursor.index ? Input::DOWN : Input::UP)
    end
  end
end

# The reminder paints its rows over an invisible command window, so its actual
# visible row positions need their own scoped hit targets.
module BlueRelearnMouse
  def pbChooseMove
    @blue_relearn_picking=true
    unless @sprites['blueCancelRelearn']
      button=BitmapSprite.new(152,30,@viewport);button.x=352;button.y=8;button.z=50
      button.bitmap.fill_rect(0,0,152,30,Color.new(24,62,91));pbSetSmallFont(button.bitmap)
      button.bitmap.font.color=Color.new(240,248,255);button.bitmap.draw_text(0,0,152,30,_INTL('Back / Esc'),1)
      @sprites['blueCancelRelearn']=button
    end
    @sprites['blueCancelRelearn'].visible=true
    super
  ensure
    @blue_relearn_picking=false
    @sprites['blueCancelRelearn'].visible=false if @sprites['blueCancelRelearn'] && !@sprites['blueCancelRelearn'].disposed?
  end
  def pbUpdate
    super
    return unless @blue_relearn_picking && BlueStartMouse.click?
    point=BlueLabPointer.position;commands=@sprites['commands']
    if BlueLabPointer.hit_sprite?(@sprites['blueCancelRelearn'],point)
      BlueLabPointer.emit(Input::BACK)
    elsif BlueLabPointer.inside?(point,0,80,258,self.class::VISIBLEMOVES*64)
      index=commands.top_item+(point[1]-80)/64
      if index<@moves.length
        commands.index=index;BlueLabPointer.emit(Input::USE)
      end
    elsif BlueLabPointer.inside?(point,48,350,76,32) && commands.index<@moves.length-1
      commands.index+=1;BlueLabPointer.claimed=true
    elsif BlueLabPointer.inside?(point,134,350,76,32) && commands.index>0
      commands.index-=1;BlueLabPointer.claimed=true
    end
  end
end
