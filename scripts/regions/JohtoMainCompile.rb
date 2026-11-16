# Validate actual native Essentials trainer/encounter compilation before
# enabling the Johto early-access battles in the shared Decades game.
# This module is NOT bundled in the isolated Johto QA build.
module BlueJohtoMainCompile
  STAMPS = {
    "Data/blue-johto-rival-ready.txt" => "BLUE_JOHTO_RIVAL_V1_READY",
    "Data/blue-johto-routes-ready.txt" => "BLUE_JOHTO_ROUTES10_TESTED_READY",
    "Data/blue-johto-violet-ready.txt" => "BLUE_JOHTO_VIOLET_V1_READY"
  }.freeze
  ROUTE = [
    [:YOUNGSTER, "Johto Mikey"], [:YOUNGSTER, "Johto Joey"],
    [:BUGCATCHER, "Johto Don"], [:BUGCATCHER, "Johto Wade"],
    [:YOUNGSTER, "Johto Ian"]
  ].freeze
  TOWER = [
    [:BLUE_JOHTO_SAGE, "Nico"], [:BLUE_JOHTO_SAGE, "Troy"],
    [:BLUE_JOHTO_ELDER, "Li"]
  ].freeze

  def self.integrated?
    defined?(BlueRegionStart) &&
      BlueRegionStart.respond_to?(:johto_preview_proof) &&
      !!BlueRegionStart.johto_preview_proof &&
      !File.file?("Johto pilot.json")
  rescue StandardError
    false
  end

  def self.trainer?(kind, name, version)
    defined?(GameData::Trainer) &&
      GameData::Trainer.exists?(kind, name, version)
  rescue StandardError
    false
  end

  def self.valid_compilation?
    return false unless integrated?
    return false unless defined?(GameData::Trainer) && defined?(GameData::Encounter)
    return false unless GameData::Trainer.respond_to?(:exists?) &&
                        GameData::Encounter.respond_to?(:exists?)
    rival = (0..2).all? { |v| trainer?(:BLUE_JOHTO_RIVAL, "Rival", v) }
    falkner = (0..1).all? { |v| trainer?(:BLUE_JOHTO_FALKNER, "Falkner", v) }
    routes = (ROUTE + TOWER).all? { |type, name|
      (0..1).all? { |v| trainer?(type, name, v) }
    }
    encounters = (625..627).all? { |id| GameData::Encounter.exists?(id, 0) }
    rival && falkner && routes && encounters
  rescue StandardError
    false
  end

  # Essentials and several Blue plugins ALIAS Compiler.main. Prepending a
  # CompilerHook here forms a cycle when another plugin aliases the method
  # after our plugin loads (old Boot.rb line 774: SystemStackError). Never
  # monkey-patch Compiler.main. On first map entry the game's native
  # Compiler.main has already finished, and GameData registries are loaded.
  # Recheck the actual compiled trainer/encounter data at that point.
  def self.refresh
    return false unless integrated?
    unless valid_compilation?
      # Do not assert readiness from the ZIP alone. Remove only our own old
      # readiness tokens, never unrelated game/region files.
      STAMPS.each do |path, value|
        if File.file?(path) && !File.symlink?(path) &&
           File.read(path).strip == value
          File.delete(path)
        end
      end
      @verified = false
      return false
    end
    return true if @verified && STAMPS.all? { |path, value|
      File.file?(path) && !File.symlink?(path) &&
        File.read(path).strip == value
    }
    STAMPS.each do |path, value|
      return false if File.symlink?(path) || File.symlink?(path + ".pending")
      next if File.file?(path) && File.read(path).strip == value
      # Abort if an unexpected file is present. Never overwrite a file
      # owned by another plugin or leave a half-written completion marker.
      return false if File.exist?(path) || File.exist?(path + ".pending")
      pending = path + ".pending"
      begin
        File.open(pending, "wb") { |file| file.write(value + "\n") }
        File.rename(pending, path)
      ensure
        File.delete(pending) if File.file?(pending)
      end
    end
    @verified = true
  rescue StandardError
    # A read-only game directory or unavailable registry may postpone
    # Johto trainer battles, but must never crash Decades/Kanto/Hoenn.
    false
  end
end

if defined?(EventHandlers) && EventHandlers.respond_to?(:add)
  EventHandlers.add(:on_enter_map, :blue_johto_main_compile_status,
                    proc { |_old_map| BlueJohtoMainCompile.refresh })
end
