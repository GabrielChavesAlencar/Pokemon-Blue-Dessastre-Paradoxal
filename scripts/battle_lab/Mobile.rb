# Android distribution uses the same game data, with an explicit offline Hub entry.
module BlueMobile
  def self.enabled?;File.file?('Data/blue-mobile.txt');end
  # JoiPlay treats screen touches as left-clicks, but some plugin builds lack
  # Input.mouse_in_window, which the game's Input script calls on a tap.
  # Install this shim only in the Android distribution; leave Windows untouched.
  def self.install_input_compatibility
    return unless enabled?
    return if Input.respond_to?(:mouse_in_window)
    # The Android game surface is the input window; do not consult System's
    # physical-mouse state (it can be false even when a finger is touching).
    Input.define_singleton_method(:mouse_in_window) { true }
  end
  # JoiPlay's error popup only displays "EventScriptError", hiding the
  # underlying exception, event, and Ruby script. Keep a local diagnostic log.
  module EventDiagnostics
    def execute_script(script)
      super
    rescue Exception => error
      if BlueMobile.enabled?
        begin
          File.open('Data/blue-android-event-error.txt','ab') do |log|
            log.puts("\n=== #{Time.now} ===")
            log.puts("Map: #{defined?(@map_id) ? @map_id : '?'} | Event: #{defined?(@event_id) ? @event_id : '?'} | Command: #{defined?(@index) ? @index : '?'}")
            log.puts("Error: #{error.class}: #{error.message}")
            log.puts("Full script:\n#{script}")
            log.puts("Backtrace:\n#{Array(error.backtrace).first(20).join("\n")}")
          end
        rescue StandardError
          # Logging must never replace the original interpreter failure.
        end
      end
      raise
    end
  end
  def self.install_event_diagnostics
    return unless enabled? && defined?(Interpreter)
    Interpreter.prepend(EventDiagnostics) unless Interpreter.ancestors.include?(EventDiagnostics)
  end
  # The title callback can be invoked with self=nil by JoiPlay/RGSS.
  # Keep the selection state on this module instead of the callback receiver.
  class << self
    attr_accessor :title_selected
  end
  module Title
    def pbCallTitle
      return super unless BlueMobile.enabled? && !BlueBattleLab::ACTIVE
      unless BlueMobile.title_selected
        BlueMobile.title_selected=true
        choice=BlueBattleLab.choose('Pokemon Blue / Android experimental',['Modo historia','Hub de batalha offline','Sair'])
        return nil if choice<0 || choice==2
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
Object.prepend(BlueMobile::Title)
