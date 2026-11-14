# Optional offline locale. Semantic IDs, source events and proper names stay intact.
class PokemonSystem
  attr_writer :blue_locale
  def blue_locale;@blue_locale || 'en';end
end
module BlueLocale
  NAME_TYPES=[1,4,5,7,8,14,18,19,21,27,28,29,30,MessageTypes::ABILITY_NAMES].uniq.freeze
  MANUAL={
    # Screen-confirmed Kanto FRLG NPC guard. Keep this fallback in native
    # runtime even when an old save has not rebuilt its compiled locale.
    'I absolutely forbid you from going through here!'=>'Está terminantemente proibido passar por aqui!',
    'Clefairy came from the moon.'=>'Clefairy veio da Lua.',
    "That's what the rumor is."=>'É isso que dizem por aí.',
    "Clefairy came from the moon. That's what the rumor is."=>'Clefairy veio da Lua. É isso que dizem por aí.',
    'Pink: Selected area · Blue: You'=>'Rosa: Área selecionada · Azul: Você',
    'Habitat complete: {1}! {2} Pokémon × $500 = ${3}.'=>'Habitat completo: {1}! {2} Pokémon × $500 = ${3}.',
    'Trainer Album'=>'Álbum de treinadores','Encountered'=>'Enfrentado','Not encountered'=>'Não enfrentado','Defeated'=>'Derrotado',
    'Visit an area with trainers to start the album.'=>'Visite uma área com treinadores para iniciar o álbum.',
    'No trainers registered in this area.'=>'Nenhum treinador registrado nesta área.',
    'Trainer Album: {1} complete! Bonus: ${2}.'=>'Álbum: {1} concluída! Bônus: ${2}.',
    'Recorded: ${1} / Bonus 33%: ${2}'=>'Registrado: ${1} / Bônus 33%: ${2}',
    'Reward received: ${1}'=>'Prêmio recebido: ${1}','Defeat every trainer in this area.'=>'Derrote todos os treinadores desta área.',
    'Collect reward'=>'Resgatar prêmio','Reward unavailable, already received, or wallet full.'=>'Prêmio indisponível, já recebido ou carteira cheia.',
    'Beginner'=>'Iniciante','Intermediate'=>'Intermediário','Advanced'=>'Avançado','Difficulty'=>'Dificuldade',
    '{1} crystals'=>'{1} cristais','Remember moves'=>'Relembrar golpes',
    'No forgotten moves are available at this level.'=>'Não há golpes esquecidos disponíveis neste nível.',
    'Reset {1} EVs of {2}?'=>'Zerar os EVs de {1} de {2}?',
    'Fishing'=>'Pesca','Old / Good / Super Rod'=>'Old / Good / Super Rod',
    'Choose a section'=>'Escolha uma seção','Encounters and location'=>'Encontros e localização',
    'Cancel / Back'=>'Cancelar / Voltar','Center'=>'Centralizar','Region'=>'Região',
    'I/O: Zoom · Arrows / Drag: Move'=>'I/O: Zoom · Setas / Arraste: Mover',
    'Headbutt / High'=>'Headbutt / Alto','Headbutt / Low'=>'Headbutt / Baixo',
    'Search Pokémon name'=>'Pesquisar nome de Pokémon','Search / Filters [F]'=>'Pesquisa / Filtros [F]',
    'Pokédex / Search and filters'=>'Pokédex / Pesquisa e filtros','All entries'=>'Todas as entradas',
    'Seen only'=>'Só vistos','Caught only'=>'Só capturados','Dex number'=>'Número na Dex',
    'Tallest first'=>'Maior altura','Heaviest first'=>'Maior peso','Show'=>'Mostrar','Order'=>'Ordenar',
    'Apply filters'=>'Aplicar filtros','Clear filters'=>'Limpar filtros','Advanced search'=>'Busca avançada',
    'No Pokémon match these filters.'=>'Nenhum Pokémon corresponde a esses filtros.',
    'Height comparison'=>'Comparação de altura','Weight comparison'=>'Comparação de peso',
    'Height'=>'Altura','Weight'=>'Peso','Player'=>'Jogador','Player reference'=>'Referência jogador',
    'Player height in cm'=>'Altura do jogador em cm','Player weight in kg'=>'Peso do jogador em kg',
    'Reset to 1.70 m / 60 kg'=>'Restaurar 1,70 m / 60 kg',
    'View on map'=>'Ver no mapa','Other habitats'=>'Outros habitats','Map [M]'=>'Mapa [M]',
    'Habitat location'=>'Localização do habitat','Gold: Habitat · Blue: You'=>'Dourado: Habitat · Azul: Você',
    'Habitat Dex / Here: {1}'=>'Habitat Dex / Aqui: {1}',
    'Back / Esc'=>'Voltar / Esc',
    'This habitat has no registered regional map position.'=>'Este habitat não tem posição cadastrada no mapa regional.',
    'Habitat Dex'=>'Habitat Dex','Pokémon list'=>'Lista de Pokémon',
    'Habitat Dex / V: Seen · C: Caught'=>'Habitat Dex / V: Vistos · C: Capturados',
    'Visit an area with wild Pokémon to fill the Habitat Dex.'=>'Visite uma área com Pokémon selvagens para preencher a Habitat Dex.',
    'Seen / Caught / ?: Not yet identified'=>'Visto / Capturado / ?: Ainda não identificado',
    'Caught'=>'Capturado','Seen'=>'Visto','Previous'=>'Anterior','Next'=>'Próximo',
    'Grass'=>'Grama','Grass / Morning'=>'Grama / Manhã','Grass / Day'=>'Grama / Dia','Grass / Night'=>'Grama / Noite',
    'Cave / Morning'=>'Caverna / Manhã','Cave / Day'=>'Caverna / Dia','Cave / Night'=>'Caverna / Noite',
    'Surf / Morning'=>'Surf / Manhã','Surf / Day'=>'Surf / Dia','Surf / Night'=>'Surf / Noite',
    'Choose the type for your two starters.'=>'Escolha o tipo dos seus dois iniciais.',
    'Your screens'=>'Suas telas','Foe screens'=>'Telas rivais','No screens'=>'Nenhuma tela',
    'Confirm name'=>'Confirmar nome','Delta Speed Up'=>'Delta Speed Up',
    'Use Delta Speed Up at 1x or 3x.'=>'Aceleração Delta em 1x ou 3x.',
    'Starter {1}/2 · {2} options'=>'Inicial {1}/2 · {2} opções','Options: {1}'=>'Opções: {1}',
    'PC / Pokémon Boxes'=>'PC / Boxes Pokémon','Opponent team preview'=>'Prévia do time rival',
    'Only previously seen species are shown.'=>'Só aparecem espécies que você já viu.',
    'Enter / Esc / P / Click: Back'=>'Enter / Esc / P / Clique: Voltar',
    'Monotype Starters'=>'Iniciais de um tipo','Traditional Starters'=>'Iniciais tradicionais',
    'Yes (Metagame Wiki Dex)'=>'Metagame Wiki Dex',
    'Quests'=>'Missões','Quest'=>'Missão','Active'=>'Ativas','Completed'=>'Concluídas','Failed'=>'Falhas',
    'Active tasks'=>'Missões ativas','Completed tasks'=>'Missões concluídas','Failed tasks'=>'Missões falhas',
    '{1} tasks'=>'Missões {1}',
    'Trouble in The Woods'=>'Problemas na floresta',
    'Investigate Cloakfall Forest'=>'Investigue a Floresta Cloakfall',
    'An trio of troublesome Pokémon have made it dangerous for Cherryhill City\'s Gardener to gather fertilizer material. Find and best the trio in battle to make them leave Cloakfall Forest. (Cloakfall Forest is East of Cherryhill City)'=>'Um trio de Pokémon impede a jardineira de Cherryhill City de coletar adubo. Vá à Floresta Cloakfall, a leste da cidade, e vença os três em batalha para fazê-los ir embora.',
    'Party: {1}'=>'Equipe: {1}',
    'Moves'=>'Golpes','Abilities'=>'Habilidades','Encounters'=>'Encontros',
    'Number Defeated: {1}'=>'Derrotados: {1}','Number Captured: {1}'=>'Capturados: {1}',
    'New quest discovered!'=>'Nova missão descoberta!','Check your quest log for more details!'=>'Confira os detalhes no diário de missões!',
    'ARROWS:'=>'SETAS:','Navigate'=>'Navegar','Jump Down/Up'=>'Pular abaixo/acima','New Activity:'=>'Nova atividade:',
    'Overview:'=>'Resumo:','Task:'=>'Objetivo:','Location:'=>'Local:','Reward:'=>'Recompensa:',
    'Quest received from:'=>'Missão recebida de:','Quest discovered in:'=>'Missão descoberta em:',
    'Quest discovered on:'=>'Missão descoberta em:','Quest start time:'=>'Início da missão:',
    'Quest completion time:'=>'Conclusão da missão:','Quest failure time:'=>'Falha na missão:',
    'Stage %d/%d'=>'Etapa %d/%d','Stage {1}/{2}'=>'Etapa {1}/{2}',
    'Change Quest'=>'Mudar missão','Hide Quest'=>'Ocultar missão','View Quest'=>'Ver missão',
    'You have {1} new quest!'=>'Você tem {1} missão nova!','You have {1} new quests!'=>'Você tem {1} missões novas!',
    'Oh! A wild {1} appeared!'=>'Um {1} selvagem apareceu!',
    'Oh! A wild {1} and {2} appeared!'=>'{1} e {2} selvagens apareceram!',
    'Oh! A wild {1}, {2} and {3} appeared!'=>'{1}, {2} e {3} selvagens apareceram!',
    'You are challenged by {1}!'=>'{1} desafia você!',
    'You are challenged by {1} and {2}!'=>'{1} e {2} desafiam você!',
    'You are challenged by {1}, {2} and {3}!'=>'{1}, {2} e {3} desafiam você!',
    'Go! {1}!'=>'Vai, {1}!','Go! {1} and {2}!'=>'Vão, {1} e {2}!',
    'Go! {1}, {2} and {3}!'=>'Vão, {1}, {2} e {3}!',
    '{1} sent out {2}!'=>'{1} enviou {2}!','{1} sent out {2} and {3}!'=>'{1} enviou {2} e {3}!',
    '{1} sent out {2}, {3} and {4}!'=>'{1} enviou {2}, {3} e {4}!',
    'The opposing {1}'=>'O {1} adversário','the opposing {1}'=>'o {1} adversário',
    'The wild {1}'=>'O {1} selvagem','the wild {1}'=>'o {1} selvagem',
    '{1} used {2}!'=>'{1} usou {2}!','Turn {1}'=>'Turno {1}',
    'Language / Idioma'=>'Language / Idioma','English'=>'Inglês','Portuguese (Brazil)'=>'Português (Brasil)',
    'Interface and story language. Pokémon, item and move names stay unchanged.'=>'Traduz interface e história. Mantém nomes de Pokémon, itens e golpes.',
    'Interface and story language. Pokémon, item, move and ability names stay unchanged.'=>'Traduz interface e história. Mantém nomes de Pokémon, itens, golpes e habilidades.',
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
      [GameData::Species,GameData::Move,GameData::Item,GameData::Ability].each { |klass| klass.each { |data| result[data.name]=true } }
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
        next unless source.match?(/#\{[^{}]*\}|\{\d+(?::[^}]+)?\}|%[ds]/) && source!=target
        tokens=/#\{[^{}]*\}|\{\d+(?::[^}]+)?\}|%[ds]/
        variables=source.scan(tokens);parts=source.split(tokens,-1)
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
      printf=variables.each_index.select { |i| variables[i].match?(/\A%[ds]\z/) }.map { |i| match[i+1] }
      result=target.gsub(/#\{[^{}]*\}|\{\d+(?::[^}]+)?\}|%[ds]/) { |token| token.start_with?('%') ? (printf.shift || token) : substitutions.fetch(token,token) }
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
    direct=MANUAL[value] || translations[value]
    return direct if direct
    # Imported Essentials events can prefix speech with a literal \b / \r
    # text-colour control. Preserve that control, but resolve the body against
    # the exact reviewed catalogue key. Never strip variables or name codes.
    if (colour=/\A((?:\\[br])+)(.+)\z/m.match(value))
      translated=translate(colour[2])
      return colour[1]+translated if translated!=colour[2]
    end
    dynamic=dynamic_translation(value)
    return dynamic if dynamic!=value
    # Translate before rich-text renderers split their input into individual glyphs.
    if value.match?(/<[^>]+>/)
      return value.split(/(<[^>]+>)/).map { |part| part.start_with?('<') ? part : translate(part) }.join
    end
    if value.include?("\n")
      return value.split(/(\n)/).map { |line| line=="\n" ? line : translate(line) }.join
    end
    stripped=value.strip
    return value.sub(stripped,translate(stripped)) if stripped!=value && !stripped.empty?
    value
  end
  module NameProtection
    def name;BlueLocale.protect_name(super);end
  end
  module AbilityNames
    def name;BlueLocale.with_raw { super };end
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
    def _INTL(*args)
      super(args[0],*args.drop(1).map { |value| value.is_a?(String) ? BlueLocale.translate(value) : value })
    end
    def _ISPRINTF(*args)
      super(args[0],*args.drop(1).map { |value| value.is_a?(String) ? BlueLocale.translate(value) : value })
    end
    def drawFormattedTextEx(bitmap,x,y,width,text,*args)
      super(bitmap,x,y,width,BlueLocale.translate(text),*args)
    end
    def drawTextEx(bitmap,x,y,width,numlines,text,*args)
      super(bitmap,x,y,width,numlines,BlueLocale.translate(text),*args)
    end
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
    Pokemon.prepend(NameProtection);Trainer.prepend(NameProtection)
    GameData::Ability.prepend(AbilityNames)
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
    'description'=>'Interface and story language. Pokémon, item, move and ability names stay unchanged.',
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
