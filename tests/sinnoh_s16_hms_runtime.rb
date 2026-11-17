# S16: real BlueRegions with fixtures, no native callbacks or Game.exe.
require 'json'
load File.expand_path(ARGV.fetch(0)) # mocked BlueRegionData
load File.expand_path(ARGV.fetch(1)) # real BlueRegions
load File.expand_path(ARGV.fetch(2)) # inert S16 adapter
manifest=JSON.parse(File.read(File.expand_path(ARGV.fetch(3))))
def check(value,label)
  raise "SINNOH_S16_RUBY: #{label}" unless value
end
module GameData
  module Item
    Entry=Struct.new(:move) do
      def is_HM?;true;end
    end
    def self.try_get(item)
      mapping={
        :HM01=>:CUT,:HM02=>:FLY,:HM03=>:SURF,:HM04=>:STRENGTH,
        :HM05=>:DEFOG,:HM06=>:ROCKSMASH,:HM07=>:WATERFALL,:HM08=>:ROCKCLIMB
      }
      mapping[item] && Entry.new(mapping[item])
    end
  end
end
class SyntheticBag
  def initialize;@owned=[];end
  def add(item);@owned<<item unless @owned.include?(item);end
  def delete(item);@owned.delete(item);end
  def has?(item);@owned.include?(item);end
end
bag=SyntheticBag.new
state=BlueRegions.new_state('SINNOH')
contract=BlueSinnohHMContracts
check(contract::VERIFIED_NATIVE_SOURCES.empty?,'native sources not empty')
check(manifest['hms'].length==8,'HM count invalid')
check(contract.preview(state,'DIVE',bag)==:invalid_move,'non Sinnoh move recognized')
check(!contract.record_from_native(state,'CUT',bag,:engine_pickup_committed,source_id:'forged'),'forged pickup accepted')
manifest['hms'].each do |row|
  action=row.fetch('action');badge=row.fetch('badge');item=row.fetch('hm_item').to_sym
  check(contract::HM_BADGES[action]==[badge,item],'HM and local badge mapping drift')
  check(contract.preview(state,action,bag)==:badge,'badge gate bypassed')
  bag.add(item) # test a Bag with an item originating from elsewhere
  check(contract.preview(state,action,bag)==:badge,'foreign HM bypassed missing badge')
  check(BlueRegions.award(state,'SINNOH',badge),'synthetic badge failed')
  check(contract.preview(state,action,bag)==:hm,'foreign Bag item bypassed local receipt')
  before=Marshal.dump(state)
  [:engine_pickup_committed,:failed,:canceled,nil,true].each do |outcome|
    check(!contract.record_from_native(state,action,bag,outcome,source_id:'fake'),
          'unverified event awarded a local HM')
  end
  check(before==Marshal.dump(state),'rejected event modified save')
  # Trusted pickup shown ONLY as an isolated fixture for the real CH11 method.
  check(!BlueRegions.record_sinnoh_hm(state,action,item,bag),'missing local proof accepted')
  check(BlueRegions.record_sinnoh_hm(state,action,item,bag,true),'fixture local pickup failed')
  check(contract.preview(state,action,bag)==:allowed,'local badge+HM not recognized')
  check(!BlueRegions.record_sinnoh_hm(state,action,item,bag,true),'duplicated receipt')
  bag.delete(item)
  check(contract.preview(state,action,bag)==:hm,'lost HM item still authorized')
  bag.add(item)
end
check(BlueRegions.local_achievements(state,'SINNOH').length==8,'gym badge drift')
state['current']='KANTO'
check(contract.preview(state,'CUT',bag)==:wrong_region,'cross-region preview')
check(!contract.record_from_native(state,'CUT',bag,:engine_pickup_committed,source_id:'fake'),'foreign region pickup')
state['current']='SINNOH'
state['region_local_hms']['SINNOH'] << 'CUT'
check(contract.preview(state,'CUT',bag)==:invalid_state,'corrupt receipts accepted')
check(!contract.record_from_native(state,'CUT',bag,:engine_pickup_committed,source_id:'fake'),'corrupt receipt awarded')
puts 'SINNOH_S16_HMS_RUNTIME_OK_OFFLINE'
