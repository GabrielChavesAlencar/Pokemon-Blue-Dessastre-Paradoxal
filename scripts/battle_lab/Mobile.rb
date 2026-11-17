# Android distribution uses the same game data, with an explicit offline Hub entry.
module BlueMobile
  def self.enabled?;File.file?('Data/blue-mobile.txt');end
  # JoiPlay treats screen touches as left-clicks, but some plugin builds lack
  # Input.mouse_in_window, which the game's Input script calls on a tap.
  # Install this shim only in the Android distribution; leave Windows untouched.
  def self.install_input_compatibility
    return unless enabled? && defined?(Input)
    return if Input.respond_to?(:mouse_in_window)
    # The Android game surface is the input window; do not consult System's
    # physical-mouse state (it can be false even when a finger is touching).
    Input.define_singleton_method(:mouse_in_window) { true }
  end
  # JoiPlay's error popup only displays "EventScriptError", hiding the
  # underlying exception, event, and Ruby script. Keep a local diagnostic log.
  def self.build_info
    path='Data/blue-mobile-build.txt'
    File.file?(path) ? File.read(path).strip : 'Revision: unknown (older package)'
  end
  def self.save_directory
    return File.expand_path(SaveData::SAVE_DIR) if defined?(SaveData::SAVE_DIR)
    return File.dirname(File.expand_path(SaveData::FILE_PATH)) if defined?(SaveData::FILE_PATH)
    File.expand_path('.')
  end
  def self.show_save_location
    directory=save_directory
    lines=['Pasta real de saves:',*directory.scan(/.{1,48}/),
      'Copie File A.rxdata ate File H.rxdata, Auto 1-3.rxdata, Game.rxdata e arquivos .bak existentes.',
      'Guarde essa copia fora da pasta do jogo antes de atualizar.','Voltar']
    File.write('Data/blue-save-location.txt',directory+"\nFile A-H.rxdata | Auto 1-3.rxdata | Game.rxdata | *.bak\n") rescue nil
    BlueBattleLab.choose('Onde fica meu save?',lines)
  end
  # Metadata is read locally, never guessed from the current clock and never
  # dependent on JSON (JoiPlay's Ruby may not ship JSON).
  def self.file_field(path, key)
    return nil unless File.file?(path)
    content=File.read(path)
    match=content.match(/^#{Regexp.escape(key)}:\\s*(.+?)\\s*$/)
    match && match[1]
  rescue IOError, SystemCallError
    nil
  end
  def self.marker_field(key)
    marker='Data/blue-update.json'
    return nil unless File.file?(marker)
    match=File.read(marker).match(/"#{Regexp.escape(key)}"\\s*:\\s*"([^"]+)"/)
    match && match[1]
  rescue IOError, SystemCallError
    nil
  end
  def self.format_utc(value)
    return 'Nao registrada (versao antiga)' if value.nil? || value.empty?
    match=value.match(/\\A(\\d{4})-(\\d{2})-(\\d{2})T(\\d{2}):(\\d{2})(?::(\\d{2}))?/)
    return value unless match
    "#{match[3]}/#{match[2]}/#{match[1]} #{match[4]}:#{match[5]}:#{match[6] || '00'}"
  end
  def self.version_details
    channel=marker_field('channel')
    revision=marker_field('revision')
    embedded=file_field('Data/blue-mobile-build.txt','Revision') ||
             file_field('Data/blue-kanto-android-build.txt','Revision')
    build_utc=file_field('Data/blue-mobile-build.txt','Build-UTC') ||
              file_field('Data/blue-kanto-android-build.txt','Build-UTC')
    title=case channel
    when 'multiregion' then 'Android / Decades + Kanto + Hoenn'
    when 'kanto'       then 'Android / Kanto piloto'
    when 'decades'     then 'Android / Decades'
    else 'Android / canal desconhecido'
    end
    applied=marker_field('applied_at_local')
    applied_utc=marker_field('applied_at_utc')
    local_display=applied ? format_utc(applied)+' (celular)' :
      (applied_utc ? format_utc(applied_utc)+' UTC' : 'Nao registrado (instalacao antiga)')
    consistency=if !revision || !embedded
      'Metadados incompletos'
    elsif revision == embedded
      'Revisoes locais coincidem'
    else
      'ATENCAO: revisoes divergentes'
    end
    {
      :title=>title, :revision=>revision || embedded || '',
      :embedded=>embedded, :build=>build_utc,
      :applied=>local_display, :consistency=>consistency,
      :mode=>marker_field('update_mode')
    }
  end
  def self.show_version
    info=version_details
    sha=info[:revision]
    lines=[
      'Pokemon Blue: Dessastre Paradoxal',
      'Edicao: '+info[:title],
      'Versao: '+(sha.empty? ? 'desconhecida' : sha[0,12]),
      'Build: '+format_utc(info[:build])+(info[:build] ? ' UTC' : ''),
      'Atualizada: '+info[:applied],
      'Conferencia: '+info[:consistency],
      'SHA parte 1: '+(sha.empty? ? '-' : sha[0,20]),
      'SHA parte 2: '+(sha.empty? ? '-' : (sha[20,20] || '-')),
      'O jogo mostra a revisao LOCAL, sem acessar a internet.',
      'Compare o SHA com a release publicada no GitHub.',
      'Voltar'
    ]
    BlueBattleLab.choose('Versao do jogo',lines)
  end
  def self.show_updates
    # The game must NOT replace loaded RGSS maps or scripts while running.
    # ATUALIZAR-ANDROID.py patches verified files with the game fully closed.
    marker='Data/blue-update.json'
    unless File.file?(marker)
      BlueBattleLab.choose('Atualizacoes Android',['Pacote antigo: instale primeiro um ZIP com atualizador.','Voltar'])
      return
    end
    info=version_details
    region=info[:title]
    revision=info[:revision].empty? ? 'nao identificada' : info[:revision][0,12]
    BlueBattleLab.choose('Atualizacoes Android',[
      'Canal: '+region,
      'Versao instalada: '+revision,
      'Feche totalmente o JoiPlay para atualizar.',
      'Use Python no Termux e abra a pasta do jogo.',
      'python ATUALIZAR-ANDROID.py  (verificar)',
      'python ATUALIZAR-ANDROID.py --update',
      'O programa baixa somente o patch compativel.',
      'Sem backup automatico. Saves nao sao modificados.',
      'Guia: github.com/'+ 'GabrielChavesAlencar',
      'Pokemon-Blue-Dessastre-Paradoxal',
      'Voltar'
    ])
  end
  def self.write_event_error(error,context)
    return if error.is_a?(SystemExit) || error.class.to_s=='Reset'
    interpreter=context[:interpreter]
    File.open('Data/blue-android-event-error.txt','ab') do |log|
      log.puts("\n=== #{Time.now} ===\n#{build_info}")
      values=[:@map_id,:@event_id,:@index].map { |key| interpreter.instance_variable_get(key) || '?' }
      log.puts("Map: #{values[0]} | Event: #{values[1]} | Command: #{values[2]}")
      log.puts("Full script:\n#{context[:script]}")
      visited=[]
      while error && !visited.include?(error.object_id) && visited.length<6
        visited << error.object_id
        log.puts("Error: #{error.class}: #{error.message}")
        log.puts("Backtrace:\n#{Array(error.backtrace).first(20).join("\n")}")
        error=error.respond_to?(:cause) ? error.cause : nil
      end
    end
    context[:logged]=true
  rescue StandardError
    # Diagnostics must not replace the original failure, including write errors.
  end
  module EventDiagnostics
    def execute_script(script)
      return super unless BlueMobile.enabled?
      previous=Thread.current[:blue_mobile_event]
      context={interpreter:self,script:script,logged:false}
      Thread.current[:blue_mobile_event]=context
      begin
        super
      rescue Exception => error
        BlueMobile.write_event_error(error,context) unless context[:logged]
        raise
      ensure
        Thread.current[:blue_mobile_event]=previous
      end
    end
  end
  # The stock Interpreter asks for this message BEFORE wrapping the exception.
  # Record that original error while keeping JoiPlay's eval overrides intact.
  module EventExceptionMessages
    def pbGetExceptionMessage(error,*args)
      context=Thread.current[:blue_mobile_event]
      BlueMobile.write_event_error(error,context) if BlueMobile.enabled? && context && !context[:logged]
      super
    end
  end
  def self.install_event_diagnostics
    return unless enabled? && defined?(Interpreter)
    Interpreter.prepend(EventDiagnostics) unless Interpreter.ancestors.include?(EventDiagnostics)
    Object.prepend(EventExceptionMessages) unless Object.ancestors.include?(EventExceptionMessages)
  end
  def self.log_boot
    return unless enabled? && !@boot_logged
    @boot_logged=true
    File.open('Data/blue-android-runtime.txt','ab') do |log|
      log.puts("\n=== #{Time.now} ===\n#{build_info}\nRuby: #{RUBY_VERSION} / #{RUBY_PLATFORM}")
      [:mouse_in_window,:mouse_x,:mouse_y,:press?,:trigger?].each { |name| log.puts("Input.#{name}: #{defined?(Input) && Input.respond_to?(name)}") }
    end
  rescue StandardError
  end
  # The title callback can be invoked with self=nil by JoiPlay/RGSS.
  # Keep the selection state on this module instead of the callback receiver.
  class << self
    attr_accessor :title_selected
  end
  module Title
    def pbCallTitle
      return super unless BlueMobile.enabled? && !BlueBattleLab::ACTIVE
      BlueMobile.install_input_compatibility
      BlueMobile.log_boot
      until BlueMobile.title_selected
        choice=BlueBattleLab.choose('Pokemon Blue / Android experimental',[
          'Modo historia','Hub de batalha offline','Versao do jogo',
          'Atualizacoes Android','Onde fica meu save?','Sair'
        ])
        if choice==2;BlueMobile.show_version;next;end
        if choice==3;BlueMobile.show_updates;next;end
        if choice==4;BlueMobile.show_save_location;next;end
        BlueMobile.title_selected=true
        return nil if choice<0 || choice==5
        if choice==1
          BlueBattleLab.send(:remove_const,:ACTIVE);BlueBattleLab.const_set(:ACTIVE,true)
          BlueBattleLab.install;return BlueBattleLab::Scene.new
        end
      end
      super
    end
  end
end
BlueMobile.install_input_compatibility
BlueMobile.install_event_diagnostics
BlueMobile.log_boot
Object.prepend(BlueMobile::Title)

# Both Android installations can access the updater guide from the pause menu.
# The item is hidden on Windows and on packages without the installed manifest.
if defined?(MenuHandlers)
  MenuHandlers.add(:pause_menu, :blue_android_version, {
    "name"=>_INTL("Versao do jogo"),
    "order"=>71,
    "condition"=>proc { |_menu| BlueMobile.enabled? && File.file?('Data/blue-update.json') },
    "effect"=>proc do |menu|
      menu.pbHideMenu
      BlueMobile.show_version
      menu.pbShowMenu
      false
    end
  })
  MenuHandlers.add(:pause_menu, :blue_android_updates, {
    "name"=>_INTL("Atualizacoes Android"),
    "order"=>72,
    "condition"=>proc { |_menu| File.file?('Data/blue-update.json') && (BlueMobile.enabled? || File.file?('Kanto pilot.json')) },
    "effect"=>proc do |menu|
      menu.pbHideMenu
      BlueMobile.show_updates
      menu.pbShowMenu
      false
    end
  })
end
