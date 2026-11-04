# Android distribution uses the same game data, with an explicit offline Hub entry.
module BlueMobile
  def self.enabled?;File.file?('Data/blue-mobile.txt');end
  # JoiPlay treats screen touches as left-clicks, but some plugin builds lack
  # Input.mouse_in_window, which the game's Input script calls on a tap.
  # Install this shim only in the Android distribution; leave Windows untouched.
  def self.install_input_compatibility
    return unless enabled?
    return if Input.respond_to?(:mouse_in_window)
    Input.define_singleton_method(:mouse_in_window) do
      if defined?(System) && System.respond_to?(:mouse_in_window)
        !!System.mouse_in_window
      else
        # In JoiPlay the playable surface is the touch window itself.
        true
      end
    end
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
Object.prepend(BlueMobile::Title)
