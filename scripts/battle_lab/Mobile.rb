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
  def self.show_updates
    # The game must NOT replace loaded RGSS maps or scripts while running.
    # ATUALIZAR-ANDROID.py performs a verified, backed-up update outside JoiPlay.
    marker='Data/blue-update.json'
    unless File.file?(marker)
      BlueBattleLab.choose('Atualizacoes Android',['Pacote antigo: instale primeiro um ZIP com atualizador.','Voltar'])
      return
    end
    region=File.file?('Kanto pilot.json') ? 'Kanto (piloto)' : 'Decades'
    revision=File.read(marker)[/"revision"\s*:\s*"([a-f0-9]{40})"/,1] rescue nil
    revision=revision ? revision[0,12] : 'nao identificada'
    BlueBattleLab.choose('Atualizacoes Android',[
      'Canal: '+region,
      'Versao instalada: '+revision,
      'Feche totalmente o JoiPlay para atualizar.',
      'Use Python no Termux e abra a pasta do jogo.',
      'python ATUALIZAR-ANDROID.py  (verificar)',
      'python ATUALIZAR-ANDROID.py --update',
      'O programa baixa somente o patch compativel.',
      'Backup automatico; saves preservados.',
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
          'Modo historia','Hub de batalha offline','Atualizacoes Android',
          'Onde fica meu save?','Sair'
        ])
        if choice==2;BlueMobile.show_updates;next;end
        if choice==3;BlueMobile.show_save_location;next;end
        BlueMobile.title_selected=true
        return nil if choice<0 || choice==4
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
