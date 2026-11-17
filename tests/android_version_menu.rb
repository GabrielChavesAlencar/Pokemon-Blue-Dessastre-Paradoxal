# Offline regression for Android "Versao do jogo", including JoiPlay without JSON.
require "tmpdir"
require "fileutils"

def _INTL(value); value; end
module BlueBattleLab
  @last = nil
  def self.choose(title, choices)
    @last = [title, choices]
    choices.length - 1
  end
  def self.last; @last; end
end
module MenuHandlers
  @menus = {}
  def self.add(scope, key, config)
    @menus[[scope, key]] = config
  end
  def self.menus; @menus; end
end
load File.expand_path(ARGV.fetch(0))
raise "Version action is missing" unless BlueMobile.respond_to?(:show_version)
raise "Title lacks Version entry" unless File.read(ARGV.fetch(0)).include?("'Versao do jogo'")
raise "Pause lacks Version entry" unless MenuHandlers.menus.key?([:pause_menu,:blue_android_version])
Object.send(:remove_const, :JSON) if Object.const_defined?(:JSON, false)

Dir.mktmpdir("blue-android-version") do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p("Data")
    File.write("Data/blue-mobile.txt", "experimental-v1\n")
    old = "a" * 40
    File.write("Data/blue-mobile-build.txt",
      "Compatibility: 2\nRevision: #{old}\nBuild-UTC: 2026-11-17T23:09:11Z\n")
    File.write("Data/blue-update.json",
      %Q({"schema":1,"channel":"multiregion","revision":"#{old}","applied_at_local":"2026-11-17T20:13:18-03:00","update_mode":"patch"}))
    raise "must work without JSON" if Object.const_defined?(:JSON, false)
    d = BlueMobile.version_details
    raise "wrong release" unless d[:revision] == old
    raise "wrong release title" unless d[:title].include?("Decades + Kanto + Hoenn")
    raise "wrong local update time" unless d[:applied].include?("17/11/2026 20:13:18")
    raise "wrong compiled time" unless BlueMobile.format_utc(d[:build]) == "17/11/2026 23:09:11"
    raise "missing revision comparison" unless d[:consistency].include?("coincidem")
    BlueMobile.show_version
    title, items = BlueBattleLab.last
    raise "wrong menu title" unless title == "Versao do jogo"
    raise "local version absent" unless items.any? { |item| item.include?(old[0,12]) }
    raise "build date absent" unless items.any? { |item| item.include?("17/11/2026 23:09:11 UTC") }
    raise "last applied date absent" unless items.any? { |item| item.include?("17/11/2026 20:13:18") }
    raise "SHA missing" unless items.any? { |item| item.include?(old[20,20]) }
    File.write("Data/blue-update.json", %Q({"channel":"kanto","revision":"#{"b"*40}"}))
    d = BlueMobile.version_details
    raise "must flag metadata mismatch" unless d[:consistency].include?("divergentes")
    raise "must not invent update timestamp" unless d[:applied].include?("Nao registrado")
    File.delete("Data/blue-mobile-build.txt")
    d = BlueMobile.version_details
    raise "old versions must show missing timestamp" unless d[:build].nil?
    raise "must not invent build revision" unless d[:consistency].include?("incompletos")
  end
end
puts "BLUE_ANDROID_VERSION_MENU_OK"
