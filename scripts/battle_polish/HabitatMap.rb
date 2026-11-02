# Regional map locations use native metadata, falling back through real map parents.
module BlueHabitatMap
  def self.position(map)
    visited=[];infos=load_data('Data/MapInfos.rxdata')
    while map && map>0 && !visited.include?(map)
      visited << map;data=GameData::MapMetadata.try_get(map)
      return data.town_map_position.dup if data && data.town_map_position
      map=infos[map]&.parent_id
    end
    nil
  end
  def self.current_index(areas,map=$game_map.map_id)
    exact=areas.index { |area| area[:map]==map };return exact if exact
    current=position(map);return nil unless current
    areas.index { |area| position(area[:map])==current }
  end
  def self.open(map)
    point=position(map)
    unless point;pbMessage(_INTL('This habitat has no registered regional map position.'));return;end
    Scene.new(map,point).run
  end
  class Scene
    def initialize(map,point);@map=map;@point=point;@sprites={};end
    def marker(bitmap,point,color,size)
      return unless point && point[0]==@point[0]
      cell_w=defined?(ARMSettings::SquareWidth) ? ARMSettings::SquareWidth : 16
      cell_h=defined?(ARMSettings::SquareHeight) ? ARMSettings::SquareHeight : 16
      x=@map_x+(point[1]+0.5)*cell_w*@scale;y=@map_y+(point[2]+0.5)*cell_h*@scale
      return unless x>=@map_x && x<@map_x+@map_width && y>=@map_y && y<@map_y+@map_height
      bitmap.fill_rect((x-size/2).round,(y-size/2).round,size,size,Color.new(8,20,36))
      bitmap.fill_rect((x-size/2+2).round,(y-size/2+2).round,size-4,size-4,color)
    end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=1_000_005
      canvas=BitmapSprite.new(Graphics.width,Graphics.height,@viewport);@sprites['canvas']=canvas
      b=canvas.bitmap;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(9,24,41));pbSetSmallFont(b)
      data=GameData::TownMap.get(@point[0]);path='Graphics/UI/Town Map/Regions/'+data.filename
      path='Graphics/UI/Town Map/'+data.filename unless pbResolveBitmap(path)
      raw=Bitmap.new(path);@scale=[480.0/raw.width,244.0/raw.height,1.0].min
      @map_width=(raw.width*@scale).round;@map_height=(raw.height*@scale).round
      @map_x=(Graphics.width-@map_width)/2;@map_y=76+(244-@map_height)/2
      b.stretch_blt(Rect.new(@map_x,@map_y,@map_width,@map_height),raw,Rect.new(0,0,raw.width,raw.height))
      marker(b,@point,Color.new(255,210,96),14);marker(b,BlueHabitatMap.position($game_map.map_id),Color.new(102,202,255),8)
      light=Color.new(240,248,255);shadow=Color.new(9,24,41)
      pbDrawTextPositions(b,[[_INTL('Habitat location'),16,8,:left,light,shadow],[BlueHabitat.map_name(@map),16,34,:left,light,shadow],
        [_INTL('Gold: Habitat · Blue: You'),16,322,:left,Color.new(178,212,239),shadow]])
      b.fill_rect(8,352,496,28,Color.new(28,64,94));b.draw_text(8,352,496,28,_INTL('Back / Esc'),1)
      Graphics.transition(0)
    ensure
      raw&.dispose
    end
    def run
      start
      loop do
        Graphics.update;Input.update
        break if Input.trigger?(Input::BACK) || Input.trigger?(Input::USE)
        break if Input.trigger?(Input::MOUSELEFT) && BlueLabPointer.inside?(BlueLabPointer.position,0,352,Graphics.width,32)
      end
    ensure
      dispose
    end
    def dispose;pbDisposeSpriteHash(@sprites);@viewport&.dispose;@viewport=nil;end
  end
end
