# Offline runtime test for main-game Hoenn travel and Littleroot agent.
# No Game.exe, map bytes or user saves are required.
module BlueRegionStart
  def self.kanto_integrated?; true; end
  def self.hoenn_integrated?; @ready == true; end
  def self.hoenn_town_point; @ready ? [905,5,10,2] : nil; end
  def self.ready=(value); @ready=value; end
end
module BlueRegions
  def self.known?(region); %w[DECADES KANTO HOENN].include?(region); end
  def self.unlocked(_state); %w[DECADES KANTO HOENN]; end
end
class Game_Event
  attr_reader :name,:x,:y
  def initialize(_map_id,event,_map)
    @name=event.name;@x=event.x;@y=event.y
  end
end
module RPG
  class EventCommand
    attr_reader :parameters
    def initialize(_code,_indent,parameters);@parameters=parameters;end
  end
  class Event
    attr_accessor :x,:y,:id,:name,:pages
    def initialize(x,y)
      @x,@y=x,y
      @pages=[Page.new]
    end
    class Page
      attr_accessor :graphic,:trigger,:list
      def initialize
        @graphic=Struct.new(:character_name).new("")
        @list=[]
      end
    end
  end
end
class FakeMap
  attr_accessor :map_id,:events
  def initialize(id)
    @map_id=id;@events={1=>Struct.new(:name,:x,:y).new("NPC original",3,10)}
  end
  def valid?(x,y); x>=0 && x<20 && y>=0 && y<20; end
  def passable?(_x,_y,_direction); true;end
end
def check(value,msg)
  raise "HOENN_MAIN_TRAVEL: #{msg}" unless value
end
def _INTL(text,*args); text; end
load File.expand_path(ARGV.fetch(0))
module BlueRegionTravel
  # Isolate the policy under test from engine UI/transfers; the production
  # safe_context? method is separately covered by region_travel_runtime.rb.
  def self.safe_context?; true; end
end
$PokemonGlobal=Struct.new(:blue_regions).new({"version"=>1,"current"=>"HOENN"})
$game_map=FakeMap.new(905)
state=$PokemonGlobal.blue_regions
check(!BlueRegionTravel.hoenn_installed?,"fake Hoenn availability accepted")
check(!BlueRegionTravel.available?(state),"missing Hoenn called a valid regional origin")
state["current"]="KANTO"
check(BlueRegionTravel.destination(state,"HOENN").nil?,
      "Hoenn without main import became a destination")
BlueRegionStart.ready=true
check(BlueRegionTravel.hoenn_installed?,"verified Hoenn unavailable")
check(BlueRegionTravel.destination(state,"HOENN")==[905,5,10,2],
      "travel must arrive in Littleroot outdoor, not player bedroom")
state["current"]="HOENN"
check(BlueRegionTravel.source_valid?(state),"installed Hoenn not a valid travel origin")
check(BlueRegionTravel.available?(state),"Hoenn agent unavailable after installation")
check(BlueRegionTravel.at_departure_town?(state),"Littleroot not recognized as departure town")
BlueRegionTravel.attach_hoenn_agent($game_map)
agent=$game_map.events.values.find { |event| event.name=="Agente Regional Hoenn" }
check(agent && [agent.x,agent.y] != [5,10],
      "Hoenn agent absent or blocking verified arrival point")
check($game_map.events.size==2,"source NPC destroyed during agent insertion")
BlueRegionTravel.attach_hoenn_agent($game_map)
check($game_map.events.size==2,"Hoenn agent duplicated after map reload")
state["current"]="KANTO"
other=FakeMap.new(905)
BlueRegionTravel.attach_hoenn_agent(other)
check(other.events.size==1,"Hoenn agent shown in wrong region")
state["current"]="HOENN"
$game_map.map_id=901
check(!BlueRegionTravel.at_departure_town?(state),
      "Hoenn agent usable outside initial town")
BlueRegionStart.ready=false
check(!BlueRegionTravel.hoenn_installed?,"Hoenn remained available after proof revocation")
require "tmpdir"
Dir.mktmpdir("hoenn-npc-diagnostic") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    message = BlueRegionTravel.hoenn_pending_message
    check(message.include?("não está instalada"), "missing status was shown as installed")
    File.write("Data/blue-hoenn-install-status.txt", "awaiting_local_source\n")
    message = BlueRegionTravel.hoenn_pending_message
    check(message.include?("ZIP original"), "missing source did not explain required ZIP")
    File.write("Data/blue-hoenn-install-status.txt", "integration_blocked\n")
    message = BlueRegionTravel.hoenn_pending_message
    check(message.include?("falhou"), "failed merge did not show diagnostic")
    File.write("Data/blue-hoenn-install-status.txt", "existing_install_needs_review\n")
    message = BlueRegionTravel.hoenn_pending_message
    check(message.include?("incompleta"), "partial install did not warn player")
  end
end
puts "PASS: Hoenn travel/NPC and clear missing-source, blocked or partial-install diagnostics"
