module BlueBattleOptions
  def self.choose(title,commands,default=0)
    if defined?(BlueBattleLab) && BlueBattleLab::ACTIVE
      BlueBattleLab.choose(title,commands,default)
    else
      pbMessage(title,commands,-1,nil,default)
    end
  end
  def self.mechanics_menu(scope=:mode)
    loop do
      labels=LABELS.map { |key,label| "#{label}: #{rules(scope)[key]==false ? 'DESATIVADO' : 'ATIVADO'}" }
      choice=choose('Mecanicas / vale para os dois lados na proxima batalha',labels+['Ativar todas','Desativar todas','Voltar'])
      if choice>=0 && choice<LABELS.length
        key=LABELS.keys[choice];rules(scope)[key]=rules(scope)[key]==false
      elsif choice==4 then rules(scope).merge!(defaults)
      elsif choice==5 then rules(scope).merge!(defaults.transform_values { false })
      else break
      end
    end
  end
  def self.quality_menu
    keys=BlueSpriteQuality::LABELS.keys
    selected=choose('Qualidade dos sprites / novos carregamentos',BlueSpriteQuality::LABELS.values+['Voltar'],keys.index(BlueSpriteQuality.mode))
    $PokemonSystem.blue_sprite_quality=keys[selected] if selected>=0 && selected<keys.length
  end
  def self.author_species
    list=[]
    GameData::Species.each { |s| list << s if s.flags.include?('DessastreParadoxal') }
    list.sort_by { |s| (s.form>0 ? s.form_name : s.name).downcase }
  end
  def self.generate(species,level)
    raise ArgumentError,'Especie autoral indisponivel.' unless author_species.any? { |s| s.id==species }
    data=GameData::Species.get(species)
    pkmn=Pokemon.new(data.species,level,$player)
    if data.form>0
      pkmn.item=data.mega_stone if data.respond_to?(:mega_stone) && data.mega_stone
    end
    pkmn.iv.each_key { |stat| pkmn.iv[stat]=31 }
    pkmn.ev.each_key { |stat| pkmn.ev[stat]=0 }
    pkmn.calc_stats;pkmn.heal
    pkmn
  end
  def self.generator
    list=author_species
    if list.empty?
      pbMessage('Instale a geracao Dessastre Paradoxal antes de usar o gerador.');return
    end
    index=choose('Dessastre Paradoxal / cadastros prontos para batalha',list.map { |s| s.form>0 ? s.form_name+' (pedra Mega)' : s.name })
    return if index<0 || index>=list.length
    params=ChooseNumberParams.new;params.setRange(1,100);params.setInitialValue(50);params.setCancelValue(0)
    level=pbMessageChooseNumber('Nivel do Pokemon (1 a 100)',params)
    return if level<=0
    if $player.party_full? && !pbConfirmMessage('Equipe cheia. Enviar o novo Pokemon para o PC?')
      return
    end
    pbAddPokemon(generate(list[index].id,level))
  end
  def self.main_menu
    loop do
      choice=choose('BLUE / Battle Mode',['Gerar Pokemon Dessastre Paradoxal','Mecanicas de batalha','Qualidade dos sprites','Voltar'])
      case choice
      when 0 then generator
      when 1 then mechanics_menu
      when 2 then quality_menu
      else break
      end
    end
  end
  def self.inject_generator(game_map)
    return unless battle_area?(game_map.map_id)
    map=game_map.instance_variable_get(:@map)
    return if map.events.values.any? { |e| e.name=='Blue Dessastre Paradoxal' }
    template=map.events.values.find { |e| e.name=='Gen 9 PKMN Generator' }
    return unless template
    nearby=(-4..4).flat_map { |dx| (-4..4).map { |dy| [template.x+dx,template.y+dy] } }
    nearby.sort_by! { |x,y| [(x-template.x).abs+(y-template.y).abs,(y-template.y).abs,x] }
    candidates=([[32,24],[28,24],[34,24],[26,24]]+nearby).uniq
    location=candidates.find { |x,y| x>=0 && y>=0 && x<map.width && y<map.height && !map.events.values.any? { |e| e.x==x && e.y==y } && reachable_ball?(game_map,x,y) }
    return unless location
    id=(map.events.keys.max || 0)+1
    event=RPG::Event.new(*location);event.id=id;event.name='Blue Dessastre Paradoxal'
    page=event.pages.first;page.graphic=Marshal.load(Marshal.dump(template.pages.first.graphic))
    page.list=[RPG::EventCommand.new(355,0,['BlueBattleOptions.main_menu']),RPG::EventCommand.new]
    map.events[id]=event
    game_map.events[id]=Game_Event.new(game_map.map_id,event,game_map)
  end
  def self.reachable_ball?(map,x,y)
    directions={2=>[0,1],4=>[-1,0],6=>[1,0],8=>[0,-1]}
    # A ball may sit on a table/solid tile: the player only needs a reachable
    # adjacent floor tile to press Use. Do not require walking onto the ball.
    directions.values.any? do |delta|
      nx=x+delta[0];ny=y+delta[1]
      next false unless map.valid?(nx,ny) && !map.events.values.any? { |e| e.x==nx && e.y==ny }
      directions.any? do |direction,step|
        tx=nx+step[0];ty=ny+step[1]
        next false if tx==x && ty==y
        map.valid?(tx,ty) && !map.events.values.any? { |e| e.x==tx && e.y==ty } &&
          map.passable?(nx,ny,direction,$game_player) && map.passable?(tx,ty,10-direction,$game_player)
      end
    end
  end
  module MapEvents
    def setup(*args)
      result=super
      BlueBattleOptions.inject_generator(self)
      result
    end
  end
  def self.install_menus
    MenuHandlers.add(:options_menu,:blue_sprite_quality,{
      'name'=>'Sprites Blue','order'=>36,'type'=>EnumOption,
      'parameters'=>['Original','Leve','Economico'],
      'description'=>'Reduz resolucao e quadros em memoria. Vale para os proximos sprites carregados.',
      'get_proc'=>proc { BlueSpriteQuality::LABELS.keys.index(BlueSpriteQuality.mode) },
      'set_proc'=>proc { |value,scene| $PokemonSystem.blue_sprite_quality=BlueSpriteQuality::LABELS.keys[value] }
    })
    EventHandlers.add(:on_enter_map,:blue_author_generator,proc { |*args| BlueBattleOptions.inject_generator($game_map) if $game_map })
    MenuHandlers.add(:pause_menu,:blue_battle_options,{
      'name'=>'Opcoes de batalha Blue','order'=>65,
      'condition'=>proc { |menu| BlueBattleOptions.battle_area? },
      'effect'=>proc { |menu| menu.pbHideMenu;pbFadeOutIn { BlueBattleOptions.main_menu };menu.pbShowMenu;false }
    })
  end
end
