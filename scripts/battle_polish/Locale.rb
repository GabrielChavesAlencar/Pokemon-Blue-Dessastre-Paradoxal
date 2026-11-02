# Optional offline locale. Semantic IDs, source events and proper names stay intact.
class PokemonSystem
  attr_writer :blue_locale
  def blue_locale;@blue_locale || 'en';end
end
module BlueLocale
  NAME_TYPES=[1,4,5,7,8,10,14,18,19,21,27,28,29,30].freeze
  MANUAL={
    'Language / Idioma'=>'Language / Idioma','English'=>'Inglês','Portuguese (Brazil)'=>'Português (Brasil)',
    'Interface and story language. Pokémon, item and move names stay unchanged.'=>'Traduz interface e história. Mantém nomes de Pokémon, itens e golpes.',
    'Text Speed'=>'Velocidade do texto','Battle Scene'=>'Animações de batalha','Battle Style'=>'Estilo de batalha',
    'Music Volume'=>'Volume da música','SE Volume'=>'Volume dos efeitos','Speed Up Settings'=>'Aceleração',
    'Battle Speed'=>'Vel. da batalha','Only Battles'=>'Só nas batalhas','All'=>'Sempre',
    'Pokémon Animations'=>'Animações Pokémon','Screen Size'=>'Tamanho da tela','Close the screen.'=>'Fechar esta tela.',
    'Summary'=>'Resumo','Stats'=>'Atributos','Speed'=>'Vel.','Call'=>'Chamar','Launch'=>'Lançar',
    'Level #{level}'=>'Nível #{level}',
    'Slow'=>'Lenta','Mid'=>'Média','Fast'=>'Rápida','On'=>'Ativado','Off'=>'Desativado',
    'Fight'=>'Lutar','Bag'=>'Mochila','Pokémon'=>'Pokémon','Run'=>'Fugir','Cancel'=>'Cancelar',
    'Yes'=>'Sim','No'=>'Não','Options'=>'Configurações','Save/Screenshots'=>'Salvar / Capturas',
    'Save'=>'Salvar','Quit Game'=>'Sair do jogo','Continue'=>'Continuar','New Game'=>'Novo jogo',
    "What will\n{1} do?"=>"O que\n{1} vai fazer?","{1}'s attack missed!"=>'{1} errou o ataque!',
    '{1} avoided the attack!'=>'{1} desviou do ataque!','{1} evaded the attack!'=>'{1} desviou do ataque!',
    'Weather'=>'Clima','Terrain'=>'Terreno','Your side'=>'Seu lado','Opponent'=>'Rival','Field: clear'=>'Campo: normal',
    'Sun'=>'Sol','Rain'=>'Chuva','Sandstorm'=>'Tempestade de areia','Hail'=>'Granizo','Snow'=>'Neve',
    'Harsh Sunlight'=>'Sol intenso','Heavy Rain'=>'Chuva intensa','Strong Winds'=>'Ventos fortes',
    'Electric'=>'Elétrico','Grassy'=>'Grama','Misty'=>'Névoa','Psychic'=>'Psíquico',
    'Double Battle'=>'Batalha em dupla','Full Power Team'=>'Time Full Power','Start Battle (Exp Gain)'=>'Iniciar batalha (ganhar EXP)',
    'Reset all EVs of {1}?'=>'Zerar todos os EVs de {1}?',"{1}'s EVs were reset!"=>'Os EVs de {1} foram zerados!',
    'It will not have any effect.'=>'Não terá efeito.',
    'Resets all EVs of one Pokémon. Consumed only when the EVs change.'=>'Zera todos os EVs de um Pokémon. Consumido apenas quando os EVs mudam.'
  }.freeze
  def self.enabled?;$PokemonSystem && $PokemonSystem.blue_locale=='pt-BR';end
  def self.raw?;!!@raw;end
  def self.with_raw
    previous=@raw;@raw=true;yield
  ensure
    @raw=previous
  end
  def self.translations
    @translations ||= File.file?('Data/blue-pt-br.dat') ? load_data('Data/blue-pt-br.dat').to_h : {}
  end
  def self.proper_names
    @proper_names ||= begin
      result={}
      [GameData::Species,GameData::Move,GameData::Item].each { |klass| klass.each { |data| result[data.name]=true } }
      result
    end
  end
  def self.protect_name(value);proper_names[value]=true if value.is_a?(String);value;end
  def self.field_term(value);enabled? ? (MANUAL[value] || value) : value;end
  def self.dynamic_translation(value)
    @dynamic_cache ||= {}
    return @dynamic_cache[value] if @dynamic_cache.key?(value)
    @templates ||= begin
      rows=[]
      (MANUAL.to_a+translations.reject { |key,value| MANUAL.key?(key) }.to_a).each do |source,target|
        next unless source.include?('#{') && source!=target
        variables=source.scan(/#\{[^{}]*\}/);parts=source.split(/#\{[^{}]*\}/,-1)
        needle=parts.max_by(&:length)
        next if variables.empty? || needle.length<4
        regex=Regexp.new('\\A'+parts.map { |p| Regexp.escape(p) }.join('(.*?)')+'\\z',Regexp::MULTILINE)
        rows << [needle,regex,variables,target]
      end
      rows
    end
    result=value
    @templates.each do |needle,regex,variables,target|
      next unless value.include?(needle)
      match=regex.match(value);next unless match
      substitutions=variables.each_with_index.to_h { |token,i| [token,match[i+1]] }
      result=target.gsub(/#\{[^{}]*\}/) { |token| substitutions.fetch(token,token) }
      break
    end
    @dynamic_cache.clear if @dynamic_cache.length>2048
    @dynamic_cache[value]=result
    result
  end
  def self.translate(value)
    return value unless enabled? && !raw? && value.is_a?(String)
    # Essentials also passes asset filenames through _INTL. Localization must
    # never turn a valid bitmap/audio/data path into a translated filename.
    return value if value.match?(/\A(?:Graphics|Audio|Data|Plugins|Fonts|PBS|Saves?)[\\\/]/i) || value.match?(/\A[^\s]+\.(?:png|bmp|jpg|ogg|mp3|wav|mid|dat|rxdata|rb|dll|txt)\z/i)
    return value if proper_names[value]
    MANUAL[value] || translations[value] || dynamic_translation(value)
  end
  module NameProtection
    def name;BlueLocale.protect_name(super);end
  end
  module CommandLabels
    attr_reader :blue_command_labels
    def setTexts(value)
      @blue_command_labels=value[1,4]
      super
    end
  end
  module Messages
    def get(type,id);value=super;BlueLocale::NAME_TYPES.include?(type) ? value : BlueLocale.translate(value);end
    def getFromHash(type,key);value=super;BlueLocale::NAME_TYPES.include?(type) ? value : BlueLocale.translate(value);end
    def getFromMapHash(*args);BlueLocale.translate(super);end
  end
  module Prompts
    def pbMessage(message,*args,&block)
      args[0]=args[0].map { |s| BlueLocale.translate(s) } if args[0].is_a?(Array)
      super(BlueLocale.translate(message),*args,&block)
    end
    def pbShowCommands(window,commands,*args,&block)
      super(window,commands.map { |s| BlueLocale.translate(s) },*args,&block)
    end
  end
  module ChoiceLogic
    def setup_choices(*args);BlueLocale.with_raw { super };end
  end
  module Menus
    def each_available(menu,*args,&block)
      super(menu,*args) { |id,hash,name| block.call(id,hash,BlueLocale.translate(name)) }
    end
  end
  module BitmapText
    def draw_text(*args)
      index=args.first.is_a?(Rect) ? 1 : 4
      args[index]=BlueLocale.translate(args[index]) if args[index].is_a?(String)
      super(*args)
    end
    def text_size(text);super(BlueLocale.translate(text));end
  end
  module TextSetter
    def text=(value);super(BlueLocale.translate(value));end
  end
  module SetText
    def setText(value,*args);super(BlueLocale.translate(value),*args);end
  end
  module OptionsRefresh
    def blue_refresh_locale
      index=0
      MenuHandlers.each_available(:options_menu) do |id,hash,name|
        option=@options[index]
        option.instance_variable_set(:@name,name)
        option.instance_variable_set(:@values,hash['parameters'].map { |v| _INTL(v) }) if option.is_a?(EnumOption)
        index+=1
      end
      @sprites['title'].text=_INTL('Options')
      @sprites['option'].refresh
      pbChangeSelection
    end
  end
  def self.install
    return if @installed
    MessageTypes.singleton_class.prepend(Messages);Object.prepend(Prompts)
    Pokemon.prepend(NameProtection);NPCTrainer.prepend(NameProtection)
    Interpreter.prepend(ChoiceLogic);MenuHandlers.singleton_class.prepend(Menus)
    Bitmap.prepend(BitmapText)
    Battle::Scene::CommandMenu.prepend(CommandLabels)
    PokemonOption_Scene.prepend(OptionsRefresh)
    [Window_AdvancedTextPokemon,Window_UnformattedTextPokemon].each do |klass|
      klass.prepend(TextSetter) if klass.method_defined?(:text=)
      klass.prepend(SetText) if klass.method_defined?(:setText)
    end
    MenuHandlers.add(:options_menu,:blue_language,{
      'name'=>'Language / Idioma','order'=>5,'type'=>EnumOption,
      'parameters'=>['English','Português'],
      'description'=>'Interface and story language. Pokémon, item and move names stay unchanged.',
      'get_proc'=>proc { $PokemonSystem.blue_locale=='pt-BR' ? 1 : 0 },
      'set_proc'=>proc do |value,scene|
        next_locale=value==1 ? 'pt-BR' : 'en'
        if $PokemonSystem.blue_locale!=next_locale
          $PokemonSystem.blue_locale=next_locale
          scene.blue_refresh_locale if scene.respond_to?(:blue_refresh_locale)
        end
      end
    })
    @installed=true
  end
end
