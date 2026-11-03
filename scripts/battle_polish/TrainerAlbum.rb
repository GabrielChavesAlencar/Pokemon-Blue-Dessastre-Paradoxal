# Per-event victories and actual received money. No event flags or maps are rewritten.
class PokemonGlobalMetadata
  attr_accessor :blue_trainer_album
end
module BlueTrainerAlbum
  class << self;attr_accessor :interpreter,:context;end
  def self.catalog
    @catalog ||= begin
      path='Data/blue-trainer-album.dat';raw=File.file?(path) ? load_data(path) : [1,[]]
      raise 'Invalid trainer album catalogue' unless raw.is_a?(Array) && raw[0]==1
      raw[1].to_h { |map,name,rows| [map,{map:map,name:name,rows:rows}] }
    end
  end
  def self.identity(kind,name);[kind.to_s,name.to_s];end
  def self.key_counts
    @key_counts ||= begin
      found=Hash.new(0);catalog.each_value { |a| a[:rows].each { |r| r[8].each { |pair| found[pair]+=1 } } };found
    end
  end
  def self.state(map)
    all=($PokemonGlobal.blue_trainer_album ||= {version:1,areas:{}})
    area=(all[:areas][map] ||= {entries:{},paid:false,award:0})
    return area unless catalog[map]
    history=($PokemonGlobal.blue_story_wins || {}).values.flat_map { |r| r[:foes] || [] }.map { |r| identity(r[0],r[1]) }
    catalog[map][:rows].each do |row|
      next if area[:entries][row[0]]
      old=row[8].any? { |pair| key_counts[pair]==1 && history.include?(pair) } || row[9].any? { |s| $game_self_switches[[map,row[0],s]] }
      area[:entries][row[0]]={seen:old,won:old,earned:0,legacy:old}
    end
    area
  end
  def self.complete?(map)
    area=catalog[map];area && !area[:rows].empty? && area[:rows].all? { |r| state(map)[:entries][r[0]][:won] }
  end
  def self.earned(map);state(map)[:entries].values.sum { |r| r[:earned].to_i };end
  def self.reward(map);earned(map)*33/100;end
  def self.claim(map,announce=true)
    row=state(map);return false if row[:paid] || !complete?(map)
    amount=reward(map)
    return false if $player.money+amount>Settings::MAX_MONEY
    row[:paid]=true;row[:award]=amount;$player.money+=amount
    pbMessage(_INTL('Trainer Album: {1} complete! Bonus: ${2}.',catalog[map][:name],amount.to_s_formatted)) if announce && amount>0
    true
  end
  def self.active?
    BlueCampaign.active? && !BlueStory.replaying? && !BlueBattleOptions.battle_area?
  end
  def self.current_event
    source=interpreter;return nil unless source
    map=source.instance_variable_get(:@map_id);event=source.instance_variable_get(:@event_id)
    map=$game_map.map_id if !map || map<=0
    area=catalog[map];row=area && area[:rows].find { |r| r[0]==event }
    row ? [map,row] : nil
  end
  def self.prepare(battle)
    current=context;return unless current && battle.trainerBattle?
    return if current[:battle]==battle.object_id && !current[:members].empty?
    current[:members].clear
    current[:battle]=battle.object_id
    opponents=Array(battle.opponent);used=[]
    opponents.each do |trainer|
      pair=identity(trainer.trainer_type,trainer.name)
      row=catalog[current[:map]][:rows].find { |r| !used.include?(r[0]) && r[8].include?(pair) }
      row ||= current[:row] if opponents.length==1
      next unless row
      used << row[0];entry=state(current[:map])[:entries][row[0]];entry[:seen]=true
      entry[:type]=trainer.trainer_type.to_s;entry[:name]=trainer.name
      current[:members] << [row[0],[trainer.party.map(&:level).max.to_i*trainer.base_money,1].max]
    end
  end
  def self.finish(current,outcome,announce=true)
    return unless current && outcome==1 && !current[:members].empty?
    # Split double-battle receipts by the native trainer-prize weights, once only.
    total=current[:members].sum { |id,w| w };remaining=current[:earned];area=state(current[:map])
    current[:members].each_with_index do |(id,weight),index|
      money=index==current[:members].length-1 ? remaining : current[:earned]*weight/total
      remaining-=money;entry=area[:entries][id]
      next if entry[:won]
      entry[:won]=true;entry[:earned]=money
    end
    claim(current[:map],announce)
  end
  module InterpreterScope
    def execute_command
      previous=BlueTrainerAlbum.interpreter;BlueTrainerAlbum.interpreter=self;super
    ensure
      BlueTrainerAlbum.interpreter=previous
    end
  end
  module Start
    def start_core(*args)
      previous=BlueTrainerAlbum.context;event=BlueTrainerAlbum.active? && BlueTrainerAlbum.current_event
      current=event ? {map:event[0],row:event[1],members:[],earned:0} : nil
      BlueTrainerAlbum.context=current;result=super
      BlueTrainerAlbum.finish(current,result);result
    ensure
      BlueTrainerAlbum.context=previous
    end
  end
  module Preparation
    def prepare_battle(battle);super;BlueTrainerAlbum.prepare(battle);end
  end
  module Money
    def pbGainMoney
      before=pbPlayer.money;result=super;row=BlueTrainerAlbum.context
      row[:earned]+=[pbPlayer.money-before,0].max if row && row[:battle]==object_id && trainerBattle?
      result
    end
  end
  module Theme
    def from_current_menu_theme(data,default=nil)
      return super('menu_trainer_card',nil) if data=='menu_blue_trainer_album'
      super
    end
  end
  def self.areas
    catalog.values.select { |a| $PokemonGlobal.visitedMaps[a[:map]] || $game_map.map_id==a[:map] || state(a[:map])[:entries].values.any? { |r| r[:seen] } }.sort_by { |a| [a[:name],a[:map]] }
  end
  def self.open
    list=areas
    if list.empty?;pbMessage(_INTL('Visit an area with trainers to start the album.'));return;end
    loop do
      labels=list.map do |a|
        s=state(a[:map]);won=s[:entries].values.count { |r| r[:won] }
        a[:name]+" / #{won}/#{a[:rows].length}"+(s[:paid] ? ' ★' : '')
      end
      selected=BlueBattleLab.choose(_INTL('Trainer Album'),labels);break if selected<0
      Scene.new(list[selected]).run
    end
  end
  class Scene
    PER_PAGE=12
    def initialize(area);@area=area;@page=0;@sprites={};end
    def pages;[(@area[:rows].length+PER_PAGE-1)/PER_PAGE,1].max;end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=999999
      @sprites['canvas']=BitmapSprite.new(Graphics.width,Graphics.height,@viewport);refresh;Graphics.transition(0)
    end
    def refresh
      @sprites.keys.grep(/^portrait/).each { |k| @sprites.delete(k).dispose }
      s=BlueTrainerAlbum.state(@area[:map]);b=@sprites['canvas'].bitmap;b.clear
      bg=Color.new(9,24,41);light=Color.new(239,248,255);b.fill_rect(0,0,Graphics.width,Graphics.height,bg);pbSetSmallFont(b)
      won=s[:entries].values.count { |r| r[:won] };money=BlueTrainerAlbum.earned(@area[:map])
      pbDrawTextPositions(b,[[_INTL('Trainer Album'),12,6,:left,light,bg],[@area[:name],12,30,:left,light,bg],
        ["#{won}/#{@area[:rows].length}",492,30,:right,light,bg]])
      b.font.size=16;b.font.color=Color.new(157,207,242)
      line=_INTL('Recorded: ${1} / Bonus 33%: ${2}',money.to_s_formatted,BlueTrainerAlbum.reward(@area[:map]).to_s_formatted)
      b.draw_text(12,53,490,22,line)
      @area[:rows].slice(@page*PER_PAGE,PER_PAGE).to_a.each_with_index do |row,i|
        entry=s[:entries][row[0]];x=10+i%4*124;y=80+i/4*75
        b.fill_rect(x,y,120,72,entry[:seen] ? Color.new(25,48,69) : Color.new(85,116,141))
        path=GameData::TrainerType.front_sprite_filename((entry[:type] || row[2]).to_sym)
        sprite=IconSprite.new(@viewport)
        if path && pbResolveBitmap(path)
          sprite.setBitmap(path)
        else
          path='Graphics/Characters/'+row[4];sprite.setBitmap(path)
          w=sprite.bitmap.width/4;h=sprite.bitmap.height/4
          sprite.src_rect=Rect.new(row[7]*w,((row[6]-2)/2)*h,w,h)
        end
        scale=42.0/[sprite.src_rect.width,sprite.src_rect.height].max;sprite.zoom_x=sprite.zoom_y=scale
        sprite.x=x+(120-sprite.src_rect.width*scale)/2;sprite.y=y+1;sprite.z=2
        sprite.tone=Tone.new(-255,-255,-255) unless entry[:seen]
        @sprites['portrait'+i.to_s]=sprite
        b.font.size=14;b.font.color=light
        b.draw_text(x+2,y+43,116,17,entry[:seen] ? (entry[:name] || row[3]) : '???',1)
        b.font.size=12;b.font.color=entry[:won] ? Color.new(111,239,158) : light
        b.draw_text(x+2,y+59,116,13,entry[:won] ? _INTL('Defeated') : _INTL(entry[:seen] ? 'Encountered' : 'Not encountered'),1)
      end
      b.font.size=16;b.font.color=light
      status=s[:paid] ? _INTL('Reward received: ${1}',s[:award].to_i.to_s_formatted) : _INTL('Defeat every trainer in this area.');b.draw_text(12,307,490,25,status)
      [_INTL('Previous'),_INTL('Next'),_INTL('Back')].each_with_index { |label,i| x=i*Graphics.width/3;b.fill_rect(x+4,336,Graphics.width/3-8,44,Color.new(30,67,99));b.draw_text(x,342,Graphics.width/3,32,label,1) }
      if BlueTrainerAlbum.complete?(@area[:map]) && !s[:paid]
        b.fill_rect(332,4,172,26,Color.new(38,107,105));b.draw_text(332,4,172,26,_INTL('Collect reward'),1)
      end
    end
    def run
      start
      loop do
        Graphics.update;Input.update;pbUpdateSpriteHash(@sprites);break if Input.trigger?(Input::BACK)
        point=BlueLabPointer.position
        if Input.trigger?(Input::USE) || (Input.trigger?(Input::MOUSELEFT) && BlueLabPointer.inside?(point,332,4,172,26))
          unless BlueTrainerAlbum.claim(@area[:map]);pbMessage(_INTL('Reward unavailable, already received, or wallet full.'));end
          refresh
        elsif Input.trigger?(Input::LEFT);@page=(@page-1)%pages;refresh
        elsif Input.trigger?(Input::RIGHT);@page=(@page+1)%pages;refresh
        elsif Input.trigger?(Input::MOUSELEFT) && BlueLabPointer.inside?(point,0,336,Graphics.width,48)
          section=point[0]*3/Graphics.width;break if section==2
          @page=(@page+(section==0 ? -1 : 1))%pages;refresh
        end
      end
    ensure
      pbDisposeSpriteHash(@sprites);@viewport&.dispose
    end
  end
  def self.install
    return if @installed
    Interpreter.prepend(InterpreterScope);TrainerBattle.singleton_class.prepend(Start)
    BattleCreationHelperMethods.singleton_class.prepend(Preparation);Battle.prepend(Money);PokemonSystem.prepend(Theme)
    MenuHandlers.each(:pause_menu) { |id,hash| hash['order']=52 if id==:quests && hash['order'].to_f<=51 }
    MenuHandlers.add(:pause_menu,:blue_trainer_album,{'name'=>'Trainer Album','order'=>51,
      'condition'=>proc { |menu| BlueStory.story? },
      'effect'=>proc { |menu| menu.pbHideMenu;pbFadeOutIn { BlueTrainerAlbum.open };menu.pbShowMenu;menu.pbRefresh;false }})
    @installed=true
  end
end
