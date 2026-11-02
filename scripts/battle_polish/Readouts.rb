# Read-only battle/Pokedex presentation. No battle decisions or enemy data are changed.
module BlueReadouts
  STATS=[:ATTACK,:DEFENSE,:SPECIAL_ATTACK,:SPECIAL_DEFENSE,:SPEED,:ACCURACY,:EVASION].freeze
  def self.stage_labels(battler)
    names=BlueLocale.enabled? ? %w[Atq Def AtE DeE Vel Prec Eva] : %w[Atk Def SpA SpD Spe Acc Eva]
    STATS.each_with_index.filter_map do |stat,i|
      stage=battler.stages[stat].to_i
      next if stage==0
      base=i>=5 ? 3.0 : 2.0
      factor=stage>0 ? (base+stage)/base : base/(base-stage)
      [(factor.round(2).to_s.sub(/\.0\z/,''))+'x '+names[i],stage>0]
    end
  end
  def self.badge(text,width,height,up)
    @badges ||= {};key=[text,width,height,up]
    return @badges[key] if @badges[key]
    if @badges.length>=96;@badges.each_value(&:dispose);@badges.clear;end
    raw=Bitmap.new(192,64);raw.font.name=['Arial','Verdana'];raw.font.size=14;raw.font.bold=true;raw.font.color=Color.new(255,255,255)
    BlueLocale.with_raw { raw.draw_text(0,0,192,64,text.delete(' '),0) }
    left=192;top=64;right=bottom=-1
    64.times do |y|
      192.times do |x|
        next if raw.get_pixel(x,y).alpha<32
        left=[left,x].min;top=[top,y].min;right=[right,x].max;bottom=[bottom,y].max
      end
    end
    result=Bitmap.new(width,height);result.fill_rect(0,0,width,height,up ? Color.new(38,108,58) : Color.new(139,56,47))
    if right>=left
      w=right-left+1;h=bottom-top+1;scale=[(width-2).to_f/w,(height-2).to_f/h,1.0].min
      dw=[(w*scale).floor,1].max;dh=[(h*scale).floor,1].max
      result.stretch_blt(Rect.new((width-dw)/2,(height-dh)/2,dw,dh),raw,Rect.new(left,top,w,h))
    end
    @badges[key]=result
  ensure
    raw&.dispose
  end
  module DexNumbers
    def drawPageData
      super
      data=GameData::Species.get_species_form(@species,@form)
      bitmap=@sprites['overlay'].bitmap
      rows=[:HP,:ATTACK,:DEFENSE,:SPECIAL_ATTACK,:SPECIAL_DEFENSE,:SPEED].each_with_index.map do |stat,i|
        value=$player.owned?(@species) ? data.base_stats[stat].to_s : '???'
        [value,229,104+i*28,:right,Color.new(248,248,248),Color.new(72,72,72),:outline]
      end
      pbDrawTextPositions(bitmap,rows)
    end
  end
  module DataBox
    def draw_name
      result=super
      labels=BlueReadouts.stage_labels(@battler)
      return result if labels.empty?
      # This eight-pixel strip is between the native name/level and HP rows.
      # Reserve the left side for status/Mega icons and the right for shiny.
      cell=[132/labels.length,60].min
      labels.each_with_index do |(text,up),i|
        label=BlueReadouts.badge(text,cell-1,8,up)
        self.bitmap.blt(@spriteBaseX+68+i*cell,32,label,Rect.new(0,0,label.width,label.height))
      end
      result
    end
  end
  def self.preview_entries(battle)
    battle.pbParty(1).compact.map do |mon|
      known=$player.seen?(mon.species)
      # Unknown slots never carry a species, form, nickname, level, item or move.
      known ? {species:mon.species,name:GameData::Species.get(mon.species).name} : {species:nil,name:'???'}
    end
  end
  class Preview
    attr_reader :sprites
    def initialize(entries)
      @entries=entries;@sprites={}
    end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=999999
      canvas=BitmapSprite.new(Graphics.width,Graphics.height,@viewport);@sprites['canvas']=canvas
      b=canvas.bitmap;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(8,20,36,247));pbSetSystemFont(b)
      pbDrawTextPositions(b,[[_INTL('Opponent team preview'),Graphics.width/2,12,:center,Color.new(235,247,255),Color.new(30,60,90)]])
      rows=[(@entries.length+2)/3,1].max;cell_h=[(Graphics.height-94)/rows,92].min
      @entries.each_with_index do |entry,i|
        x=16+(i%3)*160;y=52+(i/3)*cell_h
        b.fill_rect(x,y,152,cell_h-6,Color.new(25,46,67))
        if entry[:species]
          icon=PokemonSpeciesIconSprite.new(entry[:species],@viewport)
          icon.x=x+48;icon.y=y-6;icon.z=2;@sprites['icon'+i.to_s]=icon
        else
          pbDrawTextPositions(b,[['???',x+76,y+4,:center,Color.new(160,182,202),Color.new(25,46,67)]])
        end
        b.font.size=16
        pbDrawTextPositions(b,[[entry[:name],x+76,y+cell_h-29,:center,Color.new(239,246,255),Color.new(25,46,67)]])
      end
      b.font.size=16
      pbDrawTextPositions(b,[[_INTL('Only previously seen species are shown.'),Graphics.width/2,Graphics.height-46,:center,Color.new(170,205,226),Color.new(8,20,36)],
        [_INTL('Enter / Esc / P / Click: Back'),Graphics.width/2,Graphics.height-24,:center,Color.new(239,246,255),Color.new(8,20,36)]])
    end
    def run
      start
      loop do
        Graphics.update;Input.update;pbUpdateSpriteHash(@sprites)
        break if Input.trigger?(Input::USE) || Input.trigger?(Input::BACK) || Input.triggerex?(:P) || Input.trigger?(Input::MOUSELEFT)
      end
    ensure
      dispose
    end
    def dispose
      pbDisposeSpriteHash(@sprites);@viewport&.dispose;@viewport=nil
    end
  end
  module Scene
    def pbInitSprites
      super
      @sprites['bluePreviewButton']=BitmapSprite.new(64,18,@viewport)
      @sprites['bluePreviewButton'].z=301
    end
    def pbGraphicsUpdate
      @battle.battlers.each do |battler|
        next unless battler && battler.pokemon
        box=@sprites['dataBox_'+battler.index.to_s];next unless box
        key=[battler.pokemon.object_id,BlueReadouts::STATS.map { |s| battler.stages[s] },BlueLocale.enabled?]
        if box.instance_variable_get(:@blue_stage_key)!=key
          box.instance_variable_set(:@blue_stage_key,key);box.refresh
        end
      end
      button=@sprites['bluePreviewButton'];hud=@sprites['blueFieldHUD']
      if button && hud
        rows=BlueBattleUI.field_rows(@battle);i=rows.length-1
        button.x=hud.x+(i%2)*132+66;button.y=hud.y+2+(i/2)*18
        button.visible=!!(@blue_run_scope && hud.visible)
        key=BlueLocale.enabled?
        if @blue_preview_locale!=key || !@blue_preview_drawn
          @blue_preview_locale=key;@blue_preview_drawn=true
          b=button.bitmap;b.clear;b.fill_rect(0,0,64,18,Color.new(26,64,88));b.font.name='Arial';b.font.size=14;b.font.color=Color.new(220,243,255)
          b.draw_text(0,0,64,18,'P: '+_INTL('Opponent'),1)
        end
      end
      super
    end
    def pbUpdate(*args)
      super
      return unless @blue_run_scope && !@blue_preview_open
      button=@sprites['bluePreviewButton']
      clicked=button && button.visible && Input.trigger?(Input::MOUSELEFT) && BlueLabPointer.hit_sprite?(button,BlueLabPointer.position)
      return unless clicked || Input.triggerex?(:P)
      @blue_preview_open=true
      BlueReadouts::Preview.new(BlueReadouts.preview_entries(@battle)).run
      Input.update
    ensure
      @blue_preview_open=false
    end
  end
  def self.install
    return if @installed
    PokemonPokedexInfo_Scene.prepend(DexNumbers)
    Battle::Scene::PokemonDataBox.prepend(DataBox);Battle::Scene.prepend(Scene)
    @installed=true
  end
end
