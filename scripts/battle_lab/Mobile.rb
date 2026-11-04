# Android distribution uses the same game data, with an explicit offline Hub entry.
module BlueMobile
  def self.enabled?;File.file?('Data/blue-mobile.txt');end
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
Object.prepend(BlueMobile::Title)
