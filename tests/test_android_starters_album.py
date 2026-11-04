"""Runtime regressions for the Poco starter failure and current-area album."""
import shutil, subprocess, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class AndroidStarterAlbumTests(unittest.TestCase):
    def ruby(self,code,*sources):
        ruby=shutil.which('ruby')
        if not ruby:self.skipTest('Ruby is required for runtime compatibility fixtures')
        result=subprocess.run([ruby,'-e',code,*[str(ROOT/p) for p in sources]],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

    def test_starter_overlay_works_on_rgss_without_clear_rect(self):
        self.ruby(r'''
Color=Struct.new(:red,:green,:blue,:alpha)
class Bitmap
  attr_reader :fills
  def initialize;@fills=[];end
  def fill_rect(*args);@fills << args;end
end
Sprite=Struct.new(:bitmap)
class Object
  def pbSetSmallFont(*);end
  def pbSetSystemFont(*);end
  def pbDrawTextPositions(bitmap,positions);@text=positions.first[0];end
  def _INTL(text,*args);args.each_with_index { |v,i| text=text.gsub('{'+(i+1).to_s+'}',v.to_s) };text;end
end
load ARGV.fetch(0)
class NativePicker
  attr_reader :bitmap,:text
  def initialize
    @bitmap=Bitmap.new;@sprites={'overlay'=>Sprite.new(@bitmap)};@pokemonlist=[:BULBASAUR,:CHARMANDER]
  end
  def drawPage;:native_page;end
end
class Picker < NativePicker;prepend BlueStartMouse::Selection;end
picker=Picker.new
raise 'native draw result changed' unless picker.drawPage==:native_page
raise 'header was not replaced transparently' unless picker.bitmap.fills.last.first(4)==[294,74,218,26] && picker.bitmap.fills.last.last.alpha==0
raise 'options count lost' unless picker.text=='Options: 2'
picker.instance_variable_set(:@blue_monotype_pick,2);picker.drawPage
raise 'second starter label lost' unless picker.text=='Starter 2/2 · 2 options'
raise 'fake Bitmap unexpectedly supports clear_rect' if picker.bitmap.respond_to?(:clear_rect)
''','scripts/battle_polish/StartMouse.rb')

    def test_album_opens_current_route_city_and_interior_without_inventing_rewards(self):
        self.ruby(r'''
class PokemonGlobalMetadata
  attr_accessor :blue_trainer_album,:blue_story_wins
  def visitedMaps;{86=>true,87=>true};end
end
Map=Struct.new(:map_id)
Info=Struct.new(:parent_id)
Metadata=Struct.new(:outdoor_map)
module GameData
  module MapMetadata
    def self.try_get(id);Metadata.new([77,86,87].include?(id));end
  end
end
module BlueHabitat
  def self.map_name(id);{77=>'Cherryhill City',79=>'Cherryhill Center',86=>'Route 1',87=>'Shimmer Coast City'}[id] || id.to_s;end
end
def load_data(path);{77=>Info.new(76),79=>Info.new(78),78=>Info.new(77),92=>Info.new(87),93=>Info.new(92)};end
def _INTL(text,*args);text;end
def pbMessage(*);raise 'unexpected blocking message';end
module BlueBattleLab
  class << self;attr_accessor :selected;end
  def self.choose(title,labels,selected);self.selected=selected;-1;end
end
$PokemonGlobal=PokemonGlobalMetadata.new;$game_map=Map.new(86)
load ARGV.fetch(0)
module BlueTrainerAlbum
  def self.catalog
    @catalog ||= {86=>{map:86,name:'Route 1',rows:[]},87=>{map:87,name:'Shimmer Coast City',rows:[]},93=>{map:93,name:'Volcano',rows:[]}}
  end
  class Scene
    def run;BlueTrainerAlbum.instance_variable_set(:@opened,@area[:map]);end
  end
end
[[86,86],[92,87],[93,93],[77,77],[79,77]].each do |here,expected|
  $game_map.map_id=here
  areas=BlueTrainerAlbum.areas
  index=BlueTrainerAlbum.initial_index(areas)
  raise "wrong location #{here}" unless areas[index][:map]==expected
  BlueTrainerAlbum.open
  raise 'wrong first page' unless BlueTrainerAlbum.instance_variable_get(:@opened)==expected
  raise 'area list lost current selection' unless BlueBattleLab.selected==index
  raise 'empty current town awarded money' if BlueTrainerAlbum.complete?(expected) || BlueTrainerAlbum.claim(expected,false)
end
''','scripts/battle_polish/TrainerAlbum.rb')

if __name__=='__main__':unittest.main()
