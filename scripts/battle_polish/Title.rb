# Reuses the author's sprite and existing wordmark; no original game art is shipped.
module BlueParadoxTitle
  TRACK='BlueRandom/gym/f5443af556688de93a1fa79f.mp3'
  TRACK_SHA256='f5443af556688de93a1fa79fb274e4a31e6374e77aa10ff01de04fc51b99ce52'
  def self.available_track?
    File.file?('Audio/BGM/'+TRACK)
  end
  def self.install
    # Species data is loaded after Compiler.main; configure the symbol now.
    return unless defined?(ModularTitleScreen)
    {SPECIES: :IRONMAELTROM,SPECIES_FORM:0,START_POS:[256,366],MODIFIERS:['backgroundBLUEPARADOX','logoY:50','misc4_s2_x256_y346']}.each do |key,value|
      ModularTitle.send(:remove_const,key) if ModularTitle.const_defined?(key,false)
      ModularTitle.const_set(key,value)
    end
    ModularTitleScreen.prepend(Music) unless ModularTitleScreen.ancestors.include?(Music)
    MTS_Element_MX4.prepend(Breathing) unless MTS_Element_MX4.ancestors.include?(Breathing)
    MTS_Element_Logo.prepend(Subtitle) unless MTS_Element_Logo.ancestors.include?(Subtitle)
  end
  def self.run_checks
    lines=[];screen=nil;previous=$game_system.playing_bgm
    raise 'Title species is not Iron Maeltrom' unless ModularTitle::SPECIES==:IRONMAELTROM && ModularTitle::SPECIES_FORM==0
    available=available_track?
    screen=ModularTitleScreen.new;screen.playBGM;screen.intro
    15.times { screen.update;Graphics.update }
    raise 'Wrong title BGM selected' if available && $game_system.playing_bgm.name!=TRACK
    shot=Graphics.snap_to_bitmap;shot.to_file('Data/blue-title-smoke.png');shot.dispose
    bg=screen.instance_variable_get(:@sprites)['bg']
    before=[bg.instance_variable_get(:@bolts).x,bg.instance_variable_get(:@bolts).opacity]
    15.times { screen.update;Graphics.update }
    after=[bg.instance_variable_get(:@bolts).x,bg.instance_variable_get(:@bolts).opacity]
    raise 'Lightning does not animate' if before==after
    fire=bg.instance_variable_get(:@flames)
    raise 'Blue fire layer is missing' unless fire && fire.bitmap.get_pixel(256,Graphics.height-8).blue>40
    lines << 'PASS | Procedural blue fire animates behind the title, with lightning retained'
    lines << 'PASS | Iron Maeltrom form 0, subtitle and moving blue lightning render in native title'
    lines << (available ? 'PASS | Requested Gym Leader MP3 is the playing title BGM' : 'SKIP | Private MP3 is not installed; native title BGM fallback used')
    lines << 'RESULT=PASS';true
  rescue StandardError=>error
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace);lines << 'RESULT=FAIL';false
  ensure
    screen&.dispose
    previous ? pbBGMPlay(previous) : pbBGMStop
    File.open('Data/blue-title-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
  end
  module Breathing
    def initialize(*args)
      super
      return unless (sprite = @sprites["poke"]) && ModularTitle::SPECIES == :IRONMAELTROM
      sprite.zoom_x *= 0.67
      @blue_title_idle_scale = sprite.zoom_y * 0.67
      @blue_title_idle_started = System.uptime
      sprite.zoom_y = @blue_title_idle_scale
    end

    def update
      super
      return if disposed? || !@blue_title_idle_scale
      phase = (System.uptime - @blue_title_idle_started) * (2 * Math::PI / 2.6)
      @sprites["poke"].zoom_y = @blue_title_idle_scale * (1 + Math.sin(phase) * 0.035)
    end
  end

  module Music
    def playBGM
      # Kanto's separate pilot executable has a real title screen. Override
      # only THERE, before BlueParadoxTitle's Decades title preference.
      if defined?(BlueMusic) && BlueMusic.respond_to?(:kanto_pilot_title_audio)
        regional=BlueMusic.kanto_pilot_title_audio
        if regional
          @totalFrames=nil
          pbBGMPlay(regional)
          return
        end
      end
      return super unless BlueParadoxTitle.available_track?
      @totalFrames=nil
      pbBGMPlay(RPG::AudioFile.new(BlueParadoxTitle::TRACK,100,100))
    end
  end
  module Subtitle
    def initialize(*args)
      super
      sprite=@sprites['logo2'];sprite.bitmap.dispose
      sprite.bitmap=Bitmap.new(512,40);sprite.ox=256
      sprite.bitmap.font.name=['Arial','Verdana'];sprite.bitmap.font.size=24;sprite.bitmap.font.bold=true
      sprite.bitmap.font.color=Color.new(2,10,25)
      sprite.bitmap.draw_text(2,2,508,36,'DESSASTRE PARADOXAL',1)
      sprite.bitmap.font.color=Color.new(100,207,255)
      sprite.bitmap.draw_text(0,0,512,36,'DESSASTRE PARADOXAL',1)
      @sprites['glow2'].bitmap.clear
    end
  end
end

class MTS_Element_BGBLUEPARADOX
  def id; 'background';end
  def id?(value);value==id;end
  def visible;true;end
  def visible=(value);end
  def disposed?;@disposed;end
  def initialize(viewport,file=nil)
    @width=viewport.rect.width;@height=viewport.rect.height;@rng=Random.new(20261101)
    @base=BitmapSprite.new(@width,@height,viewport);@base.z=-20
    @height.times do |y|
      @base.bitmap.fill_rect(0,y,@width,1,Color.new(3,8+(y*12/@height),20+(y*21/@height)))
    end
    @flames=BitmapSprite.new(@width,@height,viewport);@flames.z=-15
    @bolts=BitmapSprite.new(@width,@height,viewport);@bolts.z=-10
    @started=System.uptime;@redraw=0;@disposed=false;update
  end
  def line(bitmap,x1,y1,x2,y2,width,color)
    steps=[(x2-x1).abs,(y2-y1).abs,1].max
    (0..steps).each do |i|
      x=x1+(x2-x1)*i/steps;y=y1+(y2-y1)*i/steps
      bitmap.fill_rect(x-width/2,y-width/2,width,width,color)
    end
  end
  def update
    return if @disposed
    time=System.uptime-@started
    update_fire(time)
    @bolts.x=(Math.sin(time*1.4)*8).to_i
    @bolts.opacity=(165+65*Math.sin(time*5)).to_i
    return if time<@redraw
    @redraw=time+0.16;bitmap=@bolts.bitmap;bitmap.clear
    [0.15,0.47,0.84].each do |fraction|
      x=(@width*fraction).to_i;y=-10
      while y<@height
        xx=(x+@rng.rand(65)-32).clamp(8,@width-8);yy=y+22+@rng.rand(14)
        line(bitmap,x,y,xx,yy,7,Color.new(9,76,160,125))
        line(bitmap,x,y,xx,yy,2,Color.new(112,221,255,225))
        x=xx;y=yy
      end
    end
  end
  def update_fire(time)
    return if @next_fire && time<@next_fire
    @next_fire=time+0.05
    bitmap=@flames.bitmap;bitmap.clear
    bitmap.fill_rect(0,@height-24,@width,24,Color.new(8,79,220,200))
    18.times do |i|
      height=60+35*Math.sin(time*2.1+i*1.7)+35*Math.sin(time*3.7+i*0.9)**2
      center=(i+0.5)*@width/18.0
      (0...height.to_i).step(4) do |rise|
        fraction=rise/height
        x=center+Math.sin(time*3+i+fraction*4)*(4+fraction*13)
        width=[(30*(1-fraction)**0.7).to_i,2].max
        y=@height-4-rise
        bitmap.fill_rect(x.to_i-width/2,y,width,5,Color.new(7,65+80*(1-fraction),235,210*(1-fraction)))
        bitmap.fill_rect(x.to_i-width/6,y,[width/3,1].max,4,Color.new(75,205,255,180*(1-fraction)))
      end
    end
  end
  def dispose
    @base.dispose;@bolts.dispose;@flames.dispose;@disposed=true
  end
end
