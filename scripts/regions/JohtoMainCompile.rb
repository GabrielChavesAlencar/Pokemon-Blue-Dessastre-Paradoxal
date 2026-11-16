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

  # Called ONLY after Essentials Compiler.main finishes without error.
  # Never trust a manifest or a skipped compile as evidence of trainer data.
  def self.refresh
    return false unless integrated?
    unless valid_compilation?
      STAMPS.each_key do |path|
        File.delete(path) if File.file?(path) && !File.symlink?(path)
      end
      return false
    end
    STAMPS.each do |path, value|
      raise "Unsafe Johto ready file" if File.symlink?(path)
      filename = path + ".pending"
      raise "Johto compile pending file exists" if File.exist?(filename)
      begin
        File.open(filename, "wb") { |file| file.write(value + "\n") }
        File.rename(filename, path)
      ensure
        File.delete(filename) if File.file?(filename)
      end
    end
    true
  end

  module CompilerHook
    def main(*args)
      result = super
      BlueJohtoMainCompile.refresh
      result
    end
  end
end

if defined?(Compiler)
  Compiler.singleton_class.prepend(BlueJohtoMainCompile::CompilerHook) unless
    Compiler.singleton_class.ancestors.include?(BlueJohtoMainCompile::CompilerHook)
end
