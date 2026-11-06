# Lightweight menu assets and a native on-screen keyboard for Android.
module BlueMenuSupport
  def self.mobile?;defined?(BlueMobile) && BlueMobile.enabled?;end
  def self.entry(title,value,max)
    scene=PokemonEntryScene2.new
    scene.pbStartScene(title,0,max,value,0);scene.pbEntry
  ensure
    scene&.pbEndScene
  end
  class Art
    def initialize;@bitmaps={};end
    def sprite(mon,size,viewport)
      key=[mon.species,mon.form,mon.gender,mon.shiny?,mon.egg?,size]
      bitmap=@bitmaps.delete(key)
      unless bitmap
        source=PokemonIconSprite.new(mon,viewport)
        frame=source.src_rect;bitmap=Bitmap.new(size,size)
        ratio=[size.to_f/[frame.width,1].max,size.to_f/[frame.height,1].max].min
        w=(frame.width*ratio).round;h=(frame.height*ratio).round
        bitmap.stretch_blt(Rect.new((size-w)/2,(size-h)/2,w,h),source.bitmap,frame)
        source.dispose;source=nil
      end
      @bitmaps[key]=bitmap
      @bitmaps.shift.last.dispose while @bitmaps.length>64
      sprite=Sprite.new(viewport);sprite.bitmap=bitmap;sprite.z=3;sprite
    ensure
      source&.dispose
    end
    def dispose;@bitmaps.each_value(&:dispose);@bitmaps.clear;end
  end
end
