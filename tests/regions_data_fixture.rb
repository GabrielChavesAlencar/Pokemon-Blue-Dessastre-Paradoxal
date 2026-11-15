# Synthetic replacement for installed RegionsData.rb in isolated Ruby tests.
# Read the actual versioned rules; never download Decades or touch saves.
require "json"
module BlueRegionData
  REGISTRY = JSON.parse(File.read(File.expand_path("../site/public/data/regions.json", __dir__)))
  # This fixture models a known-good audited Decades ending, not a global
  # assertion about the user's installed Decades Map136.
  DECADES_VERIFIED = true
end
