# Original Blue policy inspired by documented CFRU principles, not RR ROM code.
module BlueRadicalAI
  VERSION = '0.1'
  LOG = 'Data/blue-radical-ai.log'
  class << self
    def profile_id(battle)
      value = battle.instance_variable_get(:@blue_radical_profile) || CONFIG['defaultProfile']
      CONFIG['profiles'].key?(value.to_s) ? value.to_s : CONFIG['defaultProfile']
    end
    def profile(battle); CONFIG['profiles'][profile_id(battle)]; end
    def enabled?(battle); battle.trainerBattle? && profile_id(battle) != 'engine'; end
    def rng(battle)
      battle.instance_variable_get(:@blue_radical_rng) || battle.instance_variable_set(:@blue_radical_rng, Random.new)
    end
    def best(values, battle)
      return nil if values.empty?
      score = values.map { |v| v[:score] }.max
      ties = values.select { |v| v[:score] == score }
      ties[rng(battle).rand(ties.length)]
    end
    def trace(kind, data)
      return unless CONFIG['trace']
      return if File.file?(LOG) && File.size(LOG) > 2_000_000
      File.open(LOG,'ab') { |f| f.puts("#{Time.now} | #{kind} | #{data.map { |k,v| "#{k}=#{v.inspect}" }.join(' ')}") }
    rescue SystemCallError
      nil
    end
    def memory(battle)
      battle.instance_variable_get(:@blue_radical_memory) || battle.instance_variable_set(:@blue_radical_memory,
        {turn:nil, positions:{}, counters:Hash.new(0), history:Hash.new { |h,k| h[k]=[] }, fainted:0})
    end
    # Observe completed turns/positions, never the current command queue.
    def observe(battle)
      state = memory(battle)
      return state if state[:turn] == battle.turnCount
      fainted = [0,1].sum { |side| battle.pbParty(side).compact.count(&:fainted?) }
      reset = fainted > state[:fainted]
      state[:counters].clear if reset
      state[:history].clear if reset
      battle.allBattlers.each do |b|
        prior = state[:positions][b.index]
        changed = prior && prior != b.pokemonIndex
        state[:counters][b.index] = [state[:counters][b.index] - 1,0].max
        state[:counters][b.index] += 3 if changed && !reset
        history = state[:history][b.index]
        history << b.pokemonIndex if history.empty? || history.last != b.pokemonIndex
        history.shift while history.length > 4
        state[:positions][b.index] = b.pokemonIndex
      end
      state[:turn] = battle.turnCount
      state[:fainted] = fainted
      state
    end
    def repeated_switches?(battle,index)
      return false unless profile(battle)['antiLoop']
      state = memory(battle)
      list = state[:history][index]
      state[:counters][index] >= 9 || (list.length >= 4 && list[-1] == list[-3] && list[-2] == list[-4])
    end
  end
end
