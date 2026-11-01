# Offline 6-pick-4 preview. Battle parties are separate from the saved rosters.
module BlueBattleHub
  class PickFour < Screen
    SECONDS=60
    attr_reader :selected,:timed_out
    def initialize(teams,names)
      raise ImportError,'A selecao exige seis Pokemon por time.' unless teams.length==2 && teams.all? { |t| t.length==6 }
      @teams=teams;@names=names;@selected=[];@cursor=0;@dirty=true
      @ai_order=self.class.ai_order(teams[1],teams[0]);@timed_out=false
    end
    def self.ai_order(team,opponents)
      # Use only public species/types; no knowledge of the player's four picks.
      (0...6).sort_by do |i|
        mon=team[i]
        matchup=opponents.sum do |foe|
          mon.types.map { |type| Effectiveness.calculate(type,*foe.types).to_f/Effectiveness::NORMAL_EFFECTIVE }.max || 1.0
        end
        [-matchup,-mon.species_data.base_stats.values.sum,i]
      end.first(4)
    end
    def remaining
      [(@deadline-System.uptime).ceil,0].max
    end
    def expire!
      @selected=[0,1,2,3];@timed_out=true;@finished=true
    end
    def toggle(i)
      if @selected.include?(i);@selected.delete(i)
      elsif @selected.length<4;@selected << i
      end
      @dirty=true
    end
    def confirm_selection
      @finished=true if @selected.length==4
    end
    def render
      return unless @canvas
      @buttons=[];@bitmap.clear;rect(0,0,W,H,:bg)
      text('DUPLAS / ESCOLHA 4 DE 6',24,20,740,30)
      text("#{remaining}s",820,20,110,30,remaining<=10 ? :red : :blue)
      text('A ordem importa: os dois primeiros comecam em campo.',24,66,910,20,:muted)
      text(@names[0]+' / '+@selected.length.to_s+'/4',24,110,660,22,:green)
      text('Adversario / IA pronta',24,350,660,22,:blue)
      2.times do |side|
        @teams[side].each_with_index do |mon,i|
          x=24+i*154;y=side==0 ? 154 : 394
          if side==0
            order=@selected.index(i)
            button("pick#{i}".to_sym,'',x,y,144,166,!!order) { toggle(i) }
            text(order ? (order+1).to_s : (i+1).to_s,x+10,y+5,120,20,order ? :bg : :blue)
            rect(x,y+160,144,4,:yellow) if @cursor==i
          else
            rect(x,y,144,166,:panel)
          end
          text(mon.species_data.name,x+8,y+92,128,18,:text)
          text(mon.types.map { |t| GameData::Type.get(t).name }.join('/'),x+8,y+124,128,14,:muted)
        end
      end
      text('Mouse ou setas + Enter selecionam. Espaco confirma. Esc volta.',24,590,912,19,:muted)
      text('Se o tempo terminar, entram os quatro primeiros, mesmo com selecao parcial.',24,621,912,17,:muted)
      button(:confirm,'Confirmar quatro',24,665,270,38,@selected.length==4) { confirm_selection }
      button(:cancel,'Voltar ao montador',660,665,276,38) { @cancelled=true;@finished=true }
      @dirty=false
    end
    def update_portraits
      return unless @portrait_dirty
      @decorations&.each(&:dispose);@decorations=[]
      @teams.each_with_index do |team,side|
        team.each_with_index do |mon,i|
          icon=PokemonIconSprite.new(mon,@viewport);icon.x=50+i*154;icon.y=(side==0 ? 185 : 425);icon.z=3
          @decorations << icon
        end
      end
      @portrait_dirty=false
    end
    def tick
      if System.uptime>=@deadline;expire!;return;end
      @decorations.each(&:update)
      if Input.trigger?(Input::MOUSELEFT)
        hit=@buttons.reverse.find { |b| inside(Mouse.getMousePos,b[:rect]) };hit[:action].call if hit
      elsif Input.triggerex?(:LEFT) || Input.repeatex?(:LEFT);@cursor=(@cursor-1)%6;@dirty=true
      elsif Input.triggerex?(:RIGHT) || Input.repeatex?(:RIGHT);@cursor=(@cursor+1)%6;@dirty=true
      elsif Input.triggerex?(:RETURN);toggle(@cursor)
      elsif Input.triggerex?(:SPACE);confirm_selection
      elsif Input.trigger?(Input::BACK);@cancelled=true;@finished=true
      end
      @dirty=true if @last_seconds!=remaining
      @last_seconds=remaining
      render if @dirty
    end
    def result
      return nil if @cancelled
      [@selected.map { |i| @teams[0][i] },@ai_order.map { |i| @teams[1][i] }]
    end
    def run
      @deadline=System.uptime+SECONDS;mount
      until @finished
        Graphics.update;Input.update;tick
      end
      BlueBattleLab.log("HUB_PICK_FOUR | timeout=#{@timed_out} player=#{@selected.join(',')} ai=#{@ai_order.join(',')}")
      result
    ensure
      unmount
    end
  end
end
