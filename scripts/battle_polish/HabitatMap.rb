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
    ZOOMS=[1,2,3,4,6].freeze
    BUTTONS=[[8,52,:out,'-'],[64,52,:in,'+'],[120,132,:center,'Center'],[256,104,:region,'Region'],[364,140,:back,'Back']].freeze
    def initialize(map,point,show_player=true);@map=map;@point=point;@sprites={};@zoom_index=2;@show_player=show_player;end
    def marker(bitmap,point,color,size)
      return unless point && point[0]==@point[0]
      cell_w=defined?(ARMSettings::SquareWidth) ? ARMSettings::SquareWidth : 16
      cell_h=defined?(ARMSettings::SquareHeight) ? ARMSettings::SquareHeight : 16
      x=@map_x+((point[1]+0.5)*cell_w-@source_x)*@scale;y=@map_y+((point[2]+0.5)*cell_h-@source_y)*@scale
      return unless x>=@map_x && x<@map_x+@map_width && y>=@map_y && y<@map_y+@map_height
      bitmap.fill_rect((x-size/2).round,(y-size/2).round,size,size,Color.new(8,20,36))
      bitmap.fill_rect((x-size/2+2).round,(y-size/2+2).round,size-4,size-4,color)
    end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=1_000_005
      canvas=BitmapSprite.new(Graphics.width,Graphics.height,@viewport);@sprites['canvas']=canvas
      data=GameData::TownMap.get(@point[0]);path='Graphics/UI/Town Map/Regions/'+data.filename
      path='Graphics/UI/Town Map/'+data.filename unless pbResolveBitmap(path)
      @raw=Bitmap.new(path);@base_scale=[480.0/@raw.width,244.0/@raw.height,1.0].min
      center;refresh;Graphics.transition(0)
    end
    def center
      cell_w=defined?(ARMSettings::SquareWidth) ? ARMSettings::SquareWidth : 16
      cell_h=defined?(ARMSettings::SquareHeight) ? ARMSettings::SquareHeight : 16
      @center_x=(@point[1]+0.5)*cell_w;@center_y=(@point[2]+0.5)*cell_h
    end
    def highlighted_cells
      points=GameData::TownMap.get(@point[0]).point
      anchor=points.find { |row| row[0]==@point[1] && row[1]==@point[2] }
      cells=anchor ? points.select { |row| row[2]==anchor[2] }.map { |row| row.first(2) } : []
      cells << @point[1,2] if cells.empty?
      cells.uniq
    end
    def highlight(bitmap)
      cw=defined?(ARMSettings::SquareWidth) ? ARMSettings::SquareWidth : 16
      ch=defined?(ARMSettings::SquareHeight) ? ARMSettings::SquareHeight : 16
      highlighted_cells.each do |cx,cy|
        x=(@map_x+(cx*cw-@source_x)*@scale).round;y=(@map_y+(cy*ch-@source_y)*@scale).round
        right=[(x+cw*@scale).round,@map_x+@map_width].min;bottom=[(y+ch*@scale).round,@map_y+@map_height].min
        x=[x,@map_x].max;y=[y,@map_y].max;w=right-x;h=bottom-y;next if w<=0 || h<=0
        bitmap.fill_rect(x,y,w,h,Color.new(255,66,133,135))
        edge=Color.new(255,54,121);bitmap.fill_rect(x,y,w,2,edge);bitmap.fill_rect(x,bottom-2,w,2,edge)
        bitmap.fill_rect(x,y,2,h,edge);bitmap.fill_rect(right-2,y,2,h,edge)
      end
    end
    def zoom(delta);@zoom_index=(@zoom_index+delta).clamp(0,ZOOMS.length-1);refresh;end
    def pan(dx,dy);@center_x+=dx/@scale;@center_y+=dy/@scale;refresh;end
    def refresh
      b=@sprites['canvas'].bitmap;b.clear;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(9,24,41));pbSetSmallFont(b)
      @scale=@base_scale*ZOOMS[@zoom_index]
      sw=[(480/@scale).floor,@raw.width].min;sh=[(244/@scale).floor,@raw.height].min
      @source_x=(@center_x-sw/2.0).round.clamp(0,@raw.width-sw);@source_y=(@center_y-sh/2.0).round.clamp(0,@raw.height-sh)
      @center_x=@source_x+sw/2.0;@center_y=@source_y+sh/2.0
      @map_width=(sw*@scale).round;@map_height=(sh*@scale).round
      @map_x=(Graphics.width-@map_width)/2;@map_y=76+(244-@map_height)/2
      b.stretch_blt(Rect.new(@map_x,@map_y,@map_width,@map_height),@raw,Rect.new(@source_x,@source_y,sw,sh))
      highlight(b)
      marker(b,BlueHabitatMap.position($game_map.map_id),Color.new(102,202,255),8) if @show_player
      light=Color.new(240,248,255);shadow=Color.new(9,24,41)
      pbDrawTextPositions(b,[[_INTL('Habitat location'),16,8,:left,light,shadow],[BlueHabitat.map_name(@map),16,34,:left,light,shadow],
        [ZOOMS[@zoom_index].to_s+'x',492,8,:right,light,shadow],[_INTL('Pink: Selected area · Blue: You'),16,322,:left,Color.new(178,212,239),shadow]])
      b.font.size=16;pbDrawTextPositions(b,[[_INTL('I/O: Zoom · Arrows / Drag: Move'),16,58,:left,Color.new(157,193,224),shadow]])
      b.font.size=18;b.font.color=light
      BUTTONS.each { |x,w,id,label| b.fill_rect(x,352,w,28,Color.new(28,64,94));b.draw_text(x,352,w,28,_INTL(label),1) }
    end
    def run
      start
      loop do
        Graphics.update;Input.update
        break if Input.trigger?(Input::BACK) || Input.trigger?(Input::USE)
        if Input.triggerex?(:I);zoom(1)
        elsif Input.triggerex?(:O);zoom(-1)
        elsif Input.repeat?(Input::LEFT);pan(-32,0)
        elsif Input.repeat?(Input::RIGHT);pan(32,0)
        elsif Input.repeat?(Input::UP);pan(0,-32)
        elsif Input.repeat?(Input::DOWN);pan(0,32)
        elsif Input.trigger?(Input::MOUSELEFT)
          point=BlueLabPointer.position
          button=BUTTONS.find { |x,w,id,label| BlueLabPointer.inside?(point,x,352,w,28) }
          if button
            case button[2]
            when :back then break
            when :in then zoom(1)
            when :out then zoom(-1)
            when :center then center;refresh
            when :region then @zoom_index=0;center;refresh
            end
          elsif BlueLabPointer.inside?(point,@map_x,@map_y,@map_width,@map_height)
            @drag_point=point
          end
        elsif @drag_point && Input.press?(Input::MOUSELEFT)
          point=BlueLabPointer.position
          if point && point!=@drag_point;pan(@drag_point[0]-point[0],@drag_point[1]-point[1]);@drag_point=point;end
        else
          @drag_point=nil
        end
      end
    ensure
      dispose
    end
    def capture(path,label)
      start
      photo=Bitmap.new(480,274);photo.fill_rect(0,0,480,274,Color.new(9,24,41))
      photo.blt((480-@map_width)/2,(244-@map_height)/2,@sprites['canvas'].bitmap,Rect.new(@map_x,@map_y,@map_width,@map_height))
      pbSetSmallFont(photo);photo.font.size=18;photo.font.color=Color.new(239,248,255)
      photo.draw_text(8,246,464,26,label,1);photo.to_file(path)
    ensure
      photo&.dispose;dispose
    end
    def dispose;pbDisposeSpriteHash(@sprites);@raw&.dispose;@raw=nil;@viewport&.dispose;@viewport=nil;end
  end
end

module BlueRouteCaptures
  REQUEST='Data/blue-route-captures-request.dat'
  def self.export
    rows=load_data(REQUEST);result=[];missing=[];folder='Data/blue-route-captures'
    Dir.mkdir(folder) unless Dir.exist?(folder)
    rows.each do |id,name|
      point=BlueHabitatMap.position(id)
      if !File.file?(sprintf('Data/Map%03d.rxdata',id)) || !point
        missing << [id,name];next
      end
      file='route-'+id.to_s+'.png'
      BlueHabitatMap::Scene.new(id,point,false).capture(folder+'/'+file,name)
      result << [id,name,file,*point,480,274]
      Graphics.update;Input.update
    end
    File.binwrite('Data/blue-route-captures.dat',Marshal.dump([1,result,missing]))
    File.delete(REQUEST);result
  end
end
