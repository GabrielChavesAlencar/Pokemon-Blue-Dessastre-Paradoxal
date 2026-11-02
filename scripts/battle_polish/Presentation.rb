# Original presentation schedules, using the installed engine's art/effects.
# PictureEx uses 20 time units per second, not GBA frames.
module BluePresentation
  WILD_SLIDE=40
  PLAYER_WAIT=10
  BALL_FLIGHT=9
  EMERGE=4
  EXP_SECONDS=1.75
  module Intro
    def makeSlideSprite(name,mult,time,origin=nil)
      special=pbInSafari? || (@battle.respond_to?(:slideSpriteStyle) && @battle.slideSpriteStyle)
      return super if special
      wild=@battle.wildBattle? && (name.start_with?('pokemon_') || (name.start_with?('shadow_') && name.split('_').last.to_i.odd?))
      return super(name,mult,12,origin) unless wild
      sprite=@sprites[name]
      return unless sprite
      picture=addSprite(sprite,origin)
      picture.setDelta(0,-Graphics.width,0)
      picture.moveDelta(8,WILD_SLIDE,Graphics.width,0)
      if name.start_with?('pokemon_')
        battler=@battle.battlers[name.split('_').last.to_i]
        BlueWeightEntry.schedule(self,picture,battler,sprite,8+WILD_SLIDE)
      end
    end
  end
  module TrainerExit
    def createProcesses
      @sprites.each do |name,sprite|
        next unless name.match?(/\Atrainer_\d+\z/) && sprite.visible && sprite.x<=Graphics.width
        p=addSprite(sprite,PictureOrigin::BOTTOM)
        p.moveDelta(0,12,Graphics.width/2,0);p.setVisible(12,false)
      end
      BluePresentation.hide_lineup(self,@sprites,1)
    end
  end
  module PlayerExit
    def createProcesses
      @sprites.each do |name,sprite|
        next unless name.match?(/\Aplayer_\d+\z/) && sprite.visible && sprite.x>=0
        p=addSprite(sprite,PictureOrigin::BOTTOM)
        p.moveDelta(0,17,-Graphics.width/2,0);p.setVisible(17,false)
        next unless sprite.bitmap && sprite.bitmap.width>=sprite.bitmap.height*2
        frame=sprite.src_rect.width
        [0,5,7,9].each_with_index { |at,i| p.setSrc(at,frame*[i+1,sprite.bitmap.width/frame-1].min,0) }
      end
      BluePresentation.hide_lineup(self,@sprites,0)
    end
  end
  def self.hide_lineup(animation,sprites,side)
    sprites.each do |name,sprite|
      next unless (name=="partyBar_#{side}" || name.start_with?("partyBall_#{side}_")) && sprite.visible
      p=animation.addSprite(sprite)
      p.moveOpacity(0,8,0);p.setVisible(8,false);p.setOpacity(8,255)
    end
  end
  module Release
    def battlerAppear(p,delay,x,y,sprite,color)
      p.setVisible(delay,true);p.setOpacity(delay,255)
      p.moveXY(delay,EMERGE,x,y)
      p.moveZoom(delay,EMERGE,100,[sprite,:pbPlayIntroAnimation])
      clear=color.clone;clear.alpha=0
      p.moveColor(delay+EMERGE,6,clear)
      # Native Poké Ball glare ends at 19; the landing must remain visible.
      BlueWeightEntry.schedule(self,p,@battler,sprite,delay+19)
    end
    def ballOpenUp(ball,delay,kind,*_args)
      ball.setSE(delay,'Battle recall')
      ballSetOpen(ball,delay,kind)
    end
    def blue_release(delay,ball,x,y,sprite,kind)
      color=getBattlerColorFromPokeBall(kind);color.alpha=255
      ballOpenUp(ball,delay,kind)
      ballBurst(delay,ball,x,y-18,kind)
      ball.moveOpacity(delay+2,2,0)
      p=addSprite(sprite,PictureOrigin::BOTTOM)
      p.setVisible(0,false);p.setXY(0,x,y);p.setZoom(0,0);p.setColor(0,color)
      battlerAppear(p,delay,sprite.x,sprite.y,sprite,color)
      shadowAppear(@battler,delay) if respond_to?(:shadowAppear)
      @blue_release_time=delay
    end
  end
  module PlayerSend
    include Release
    # The follower plugin otherwise bypasses the ball and teleports the lead.
    def createFollowerProcesses;createProcesses;end
    def createProcesses
      sprite=@sprites["pokemon_#{@battler.index}"]
      sprite.visible=false
      @sprites["shadow_#{@battler.index}"].visible=false
      kind=sprite.pkmn.poke_ball
      x,y=Battle::Scene.pbBattlerPosition(@battler.index,sprite.sideSize)
      trainer=@sprites["player_#{@idxTrainer}"]
      if @showingTrainer && trainer && trainer.x>0
        sx=trainer.x-40;sy=trainer.y-trainer.src_rect.height/2
      else
        sx=-12;sy=Graphics.height*0.6
      end
      ball=addBallSprite(sx,sy,kind);ball.setZ(0,sprite.z-1);ball.setVisible(0,false)
      start=(@showingTrainer ? PLAYER_WAIT : 0)+8*@idxOrder
      createBallTrajectory(ball,start,BALL_FLIGHT,sx,sy,0,[sy,y].min-72,x,y-18)
      blue_release(start+BALL_FLIGHT+4,ball,x,y,sprite,kind)
    end
  end
  module OpponentSend
    include Release
    def createProcesses
      sprite=@sprites["pokemon_#{@battler.index}"]
      sprite.visible=false
      @sprites["shadow_#{@battler.index}"].visible=false
      kind=sprite.pkmn.poke_ball
      x,y=Battle::Scene.pbBattlerPosition(@battler.index,sprite.sideSize)
      ball=addBallSprite(x,y-18,kind);ball.setZ(0,sprite.z-1)
      wait=(@showingTrainer ? 12 : 0)+8*@idxOrder
      ball.setVisible(0,false);ball.setVisible(wait,true)
      blue_release(wait+6,ball,x,y,sprite,kind)
    end
  end
  module Exp
    def animate_exp(*args)
      super
      # Small awards must also be visible, while full-bar awards keep their pace.
      @anim_exp_duration_mult=[@anim_exp_duration_mult,0.3/EXP_SECONDS].max if animating_exp?
    end
  end
  def self.install
    return if @installed
    a=Battle::Scene::Animation
    a::Intro.prepend(Intro)
    a::TrainerFade.prepend(TrainerExit);a::PlayerFade.prepend(PlayerExit)
    a::PokeballPlayerSendOut.prepend(PlayerSend)
    a::PokeballTrainerSendOut.prepend(OpponentSend)
    box=Battle::Scene::PokemonDataBox
    box.send(:remove_const,:EXP_BAR_FILL_TIME);box.const_set(:EXP_BAR_FILL_TIME,EXP_SECONDS)
    box.prepend(Exp)
    @installed=true
  end
end
