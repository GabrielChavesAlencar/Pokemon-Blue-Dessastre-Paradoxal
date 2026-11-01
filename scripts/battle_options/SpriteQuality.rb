# Low-resolution frame storage; original assets and on-screen dimensions stay intact.
module BlueSpriteQuality
  PROFILES={'original'=>nil,'light'=>[128,24],'minimal'=>[96,1]}.freeze
  LABELS={'original'=>'Original','light'=>'Leve (128 px / ate 24 quadros)','minimal'=>'Economico (96 px / estatico)'}.freeze
  def self.mode
    value=$PokemonSystem && $PokemonSystem.blue_sprite_quality
    PROFILES.key?(value) ? value : 'original'
  end
  def self.indices(count,limit)
    return [0] if limit==1 || count==1
    kept=[count,limit].min
    (0...kept).map { |i| (i*(count-1).to_f/(kept-1)).round }
  end
  module Wrapper
    attr_reader :blue_source_frames, :blue_stored_bytes
    def refresh(bitmaps=nil)
      @blue_frame_key=nil
      profile=BlueSpriteQuality::PROFILES[BlueSpriteQuality.mode]
      unless profile && !@blue_force_original && bitmaps.nil? && @bmp_file.is_a?(String) && @bmp_file.tr('\\','/').include?('Graphics/Pokemon/')
        @blue_lowres=false
        return super
      end
      dispose
      source=Bitmap.new(@bmp_file)
      animated=source.animated?
      strip=!animated && source.width>source.height*2
      fw=strip ? source.height : source.width;fh=source.height
      @width=[(fw*@scale).round,1].max;@height=[(fh*@scale).round,1].max
      @blue_source_frames=animated ? source.frame_count : strip ? (source.width.to_f/fh).ceil : 1
      cap,limit=profile
      limit=1 if $PokemonSystem.animated_sprites>0
      ratio=[cap.to_f/[@width,@height].max,1.0].min
      small_w=[(@width*ratio).round,1].max;small_h=[(@height*ratio).round,1].max
      @bitmaps=[]
      BlueSpriteQuality.indices(@blue_source_frames,limit).each do |index|
        source.goto_and_stop(index) if animated
        frame=Bitmap.new(small_w,small_h)
        frame.stretch_blt(Rect.new(0,0,small_w,small_h),source,Rect.new(strip ? index*fw : 0,0,fw,fh))
        @bitmaps << frame
      end
      @total_frames=@bitmaps.length;@frame_idx=0
      @temp_bmp=Bitmap.new(@width,@height)
      @blue_stored_bytes=(@bitmaps.sum { |b| b.width*b.height }+@width*@height)*4
      @blue_lowres=true
    ensure
      source.dispose if source && !source.disposed?
    end
    def compile_strip(pkmn=nil,back=false)
      return super unless @blue_lowres
      # Pixel-specific form painting (e.g. Spinda spots) keeps its native pipeline.
      return unless pkmn && MultipleForms.getFunction(pkmn.species,'alterBitmap')
      @blue_force_original=true
      refresh
      super
    ensure
      @blue_force_original=false
    end
    def bitmap
      return super unless @blue_lowres
      return nil if disposed?
      x,y,w,h=box
      key=[@frame_idx,x,y,w,h]
      if key!=@blue_frame_key
        frame=@bitmaps[@frame_idx];@temp_bmp.clear
        rx=frame.width.to_f/@width;ry=frame.height.to_f/@height
        @temp_bmp.stretch_blt(Rect.new(x,y,w,h),frame,Rect.new((x*rx).floor,(y*ry).floor,[(w*rx).ceil,1].max,[(h*ry).ceil,1].max))
        @blue_frame_key=key
      end
      @temp_bmp
    end
    def copy; @blue_lowres ? bitmap.clone : super; end
    def hue_change(value)
      @blue_frame_key=nil
      super
    end
    def update
      return super unless @blue_lowres
      return false if disposed? || $PokemonSystem.animated_sprites>0 || @speed<=0 || @total_frames<=1
      now=System.uptime
      delay=((@speed/2.0)*Settings::ANIMATION_FRAME_DELAY).round/1000.0
      delay*=@blue_source_frames.to_f/@total_frames
      return if now-@last_uptime<delay
      @frame_idx=(@frame_idx+(@reversed ? -1 : 1))%@total_frames
      @last_uptime=now
    end
  end
end
