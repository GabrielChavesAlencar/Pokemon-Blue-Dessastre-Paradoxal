# Read-only Habitat Dex: native visited maps, active encounter version and Dex flags.
module BlueHabitat
  METHODS={Land:'Grass',LandMorning:'Grass / Morning',LandDay:'Grass / Day',LandNight:'Grass / Night',
    Cave:'Cave',CaveMorning:'Cave / Morning',CaveDay:'Cave / Day',CaveNight:'Cave / Night',Water:'Surf',
    WaterMorning:'Surf / Morning',WaterDay:'Surf / Day',WaterNight:'Surf / Night',
    OldRod:'Old Rod',GoodRod:'Good Rod',SuperRod:'Super Rod',RockSmash:'Rock Smash'}.freeze
  def self.map_name(map)
    name=pbGetMapNameFromId(map)
    if name.to_s.empty?
      @map_infos ||= load_data('Data/MapInfos.rxdata')
      name=@map_infos[map]&.name
    end
    name.to_s.empty? ? _INTL('Area {1}',map) : name
  end
  def self.areas
    ids=[];GameData::Encounter.each { |data| ids << data.map }
    ids.uniq.filter_map do |map|
      next unless $PokemonGlobal.visitedMaps[map] || ($game_map && $game_map.map_id==map)
      data=GameData::Encounter.get(map,$PokemonGlobal.encounter_version)
      next unless data && data.types.any? { |type,slots| !slots.empty? }
      {map:map,name:map_name(map),methods:BlueExploration.encounter_types(data.types).reject { |type,slots| slots.empty? }}
    end.sort_by { |area| [area[:name],area[:map]] }
  end
  def self.species(slots)
    slots.map do |slot|
      data=GameData::Species.get(slot[1])
      data=BlueStory.replacement(data,BlueStory.cap) if BlueStory.enabled? && BlueStory.cap
      data.species
    end.uniq
  end
  def self.entries(slots)
    species(slots).map do |id|
      owned=$player.owned?(id);seen=owned || $player.seen?(id)
      {species:seen ? id : nil,name:seen ? GameData::Species.get(id).name : '?',status:owned ? :caught : (seen ? :seen : :unknown)}
    end
  end
  def self.progress(area)
    ids=species(area[:methods].values.flatten(1))
    seen=ids.count { |id| $player.seen?(id) || $player.owned?(id) };caught=ids.count { |id| $player.owned?(id) }
    [seen,caught,ids.length]
  end
  def self.open
    list=areas
    if list.empty?;pbMessage(_INTL('Visit an area with wild Pokémon to fill the Habitat Dex.'));return;end
    loop do
      labels=list.map do |area|
        seen,caught,total=progress(area)
        area[:name]+"  /  #{seen}/#{total} V  #{caught}/#{total} C"+(caught==total ? ' ★' : '')
      end
      chosen=BlueBattleLab.choose(_INTL('Habitat Dex / V: Seen · C: Caught'),labels)
      break if chosen<0
      area=list[chosen];methods=area[:methods].keys
      loop do
        method=BlueBattleLab.choose(area[:name],methods.map { |type| _INTL(METHODS[type] || type.to_s) })
        break if method<0
        Scene.new(area[:name],_INTL(METHODS[methods[method]] || methods[method].to_s),entries(area[:methods][methods[method]])).run
      end
    end
  end
  class Scene
    def initialize(area,method,entries);@area=area;@method=method;@entries=entries;@page=0;@sprites={};end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=999999
      @sprites['canvas']=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
      refresh;Graphics.transition(0)
    end
    def refresh
      @sprites.keys.grep(/^icon/).each { |key| @sprites.delete(key).dispose }
      b=@sprites['canvas'].bitmap;b.clear;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(10,25,42))
      pbSetSmallFont(b);light=Color.new(238,247,255);shadow=Color.new(10,25,42)
      pbDrawTextPositions(b,[[_INTL('Habitat Dex'),16,8,:left,light,shadow],[@area,16,32,:left,light,shadow],
        [@method,16,56,:left,Color.new(135,198,247),shadow]])
      @entries.slice(@page*6,6).to_a.each_with_index do |entry,i|
        x=16+i%3*164;y=88+i/3*100
        b.fill_rect(x,y,152,92,Color.new(25,48,69))
        if entry[:species]
          icon=PokemonSpeciesIconSprite.new(entry[:species],@viewport);icon.x=x+44;icon.y=y-6;icon.z=2;@sprites['icon'+i.to_s]=icon
        else
          pbDrawTextPositions(b,[['?',x+76,y+14,:center,light,shadow]])
          next
        end
        label=entry[:status]==:caught ? _INTL('Caught') : (entry[:status]==:seen ? _INTL('Seen') : '?')
        color=entry[:status]==:caught ? Color.new(113,227,151) : Color.new(180,208,232)
        pbDrawTextPositions(b,[[entry[:name],x+76,y+51,:center,light,shadow],[label,x+76,y+71,:center,color,shadow]])
      end
      pbDrawTextPositions(b,[[_INTL('Seen / Caught / ?: Not yet identified'),16,298,:left,light,shadow],
        [(1+@page).to_s+' / '+pages.to_s,Graphics.width-20,56,:right,light,shadow]])
      [_INTL('Previous'),_INTL('Next'),_INTL('Back')].each_with_index do |label,i|
        x=i*Graphics.width/3;b.fill_rect(x+4,336,Graphics.width/3-8,44,Color.new(30,67,99))
        b.draw_text(x,342,Graphics.width/3,32,label,1)
      end
    end
    def pages;[(@entries.length+5)/6,1].max;end
    def turn(delta);@page=(@page+delta)%pages;refresh;end
    def run
      start
      loop do
        Graphics.update;Input.update;pbUpdateSpriteHash(@sprites)
        break if Input.trigger?(Input::BACK)
        if Input.trigger?(Input::LEFT);turn(-1)
        elsif Input.trigger?(Input::RIGHT);turn(1)
        elsif Input.trigger?(Input::MOUSELEFT)
          point=BlueLabPointer.position
          next unless BlueLabPointer.inside?(point,0,336,Graphics.width,48)
          section=point[0]*3/Graphics.width;break if section==2
          turn(section==0 ? -1 : 1)
        end
      end
    ensure
      dispose
    end
    def dispose;pbDisposeSpriteHash(@sprites);@viewport&.dispose;@viewport=nil;end
  end
  module DexMenu
    def pbStartScreen
      loop do
        choice=BlueBattleLab.choose(_INTL('Pokédex'),[_INTL('Pokémon list'),_INTL('Habitat Dex'),_INTL('Back')])
        break if choice<0 || choice==2
        choice==0 ? super : BlueHabitat.open
      end
    end
  end
end
