# S15: test the real shared BlueRegions via the existing fixture, no Game.exe.
require 'json'
fixture=File.expand_path(ARGV.fetch(0))
require fixture
load File.expand_path(ARGV.fetch(1))
spec=JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))
def check(ok,why)
  raise "SINNOH_S15_RUBY: #{why}" unless ok
end
check(spec['gyms'].length==8,'wrong gym count')
check(BlueSinnohGymContracts::VERIFIED_NATIVE_SOURCES.empty?,'native sources forged')
check(BlueSinnohGymContracts::BADGES==spec['gyms'].map{|g|g['badge']},'badges drift')

s=BlueRegions.new_state('SINNOH')
check(BlueSinnohGymContracts.checkpoint(s,'SINNOH_ROARK')==:native_source_missing,'first gym not ready for binding')
check(BlueSinnohGymContracts.checkpoint(s,'SINNOH_FANTINA')==:missing_prior_badges,'order bypass')
check(!BlueSinnohGymContracts.record_from_native(s,'SINNOH_ROARK',:engine_battle_won,source_id:'forged'),'fake win minted badge')
check(BlueRegions.local_achievements(s,'SINNOH').empty?,'fake win mutated progress')

spec['gyms'].each_with_index do |gym,idx|
  key=gym['id'];badge=gym['badge']
  check(BlueSinnohGymContracts.badge_for(key)==badge,'badge mismatch')
  check(BlueSinnohGymContracts.checkpoint(s,key)==:native_source_missing,'missing native binding not rejected')
  [:engine_battle_won,:lost,:escaped,nil,true].each do |outcome|
    check(!BlueSinnohGymContracts.record_from_native(s,key,outcome,source_id:'fake'),'forged outcome minted badge')
  end
  check(BlueRegions.local_achievements(s,'SINNOH').length==idx,'untrusted mutations')
  # Trusted Engine callbacks are absent. Simulated award uses BlueRegions directly
  # ONLY in a fixture, to verify CH11 badge state and sequence.
  check(BlueRegions.award(s,'SINNOH',badge),'fixture could not award '+badge)
  check(BlueSinnohGymContracts.checkpoint(s,key)==:already_awarded,'duplicate badge allowed')
  check(!BlueSinnohGymContracts.record_from_native(s,key,:engine_battle_won,source_id:'fake'),'duplicate awarded')
end
check(BlueRegions.local_achievements(s,'SINNOH').length==8,'missing local gyms')
check(BlueRegions.allow_specials?(s,'SINNOH'),'8 local badges not recognized')
check(!BlueSinnohGymContracts.record_from_native(s,'SINNOH_UNKNOWN',:engine_battle_won,source_id:'x'),'unknown gym awarded')
check(BlueSinnohGymContracts.badge_for('SINNOH_UNKNOWN').nil?,'unknown badge')
check(BlueSinnohGymContracts.checkpoint(s,'SINNOH_UNKNOWN')==:unknown_gym,'unknown gym selected')

s['current']='KANTO'
check(BlueSinnohGymContracts.checkpoint(s,'SINNOH_ROARK')==:wrong_region,'foreign region accepted')
check(!BlueSinnohGymContracts.record_from_native(s,'SINNOH_ROARK',:engine_battle_won,source_id:'fake'),'cross-region award')
s['current']='SINNOH'
s['achievements']['SINNOH'] << 'COAL'
check(BlueSinnohGymContracts.checkpoint(s,'SINNOH_VOLKNER')==:invalid_badges,'corrupt save accepted')
check(!BlueSinnohGymContracts.record_from_native(s,'SINNOH_VOLKNER',:engine_battle_won,source_id:'fake'),'corrupt save awarded')
puts 'SINNOH_S15_GYMS_RUNTIME_OK_OFFLINE_ONLY'
