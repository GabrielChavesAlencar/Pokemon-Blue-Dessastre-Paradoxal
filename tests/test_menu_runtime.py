import shutil,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class MenuRuntimeTests(unittest.TestCase):
    def run_ruby(self,script,source):
        ruby=shutil.which('ruby')
        if not ruby:self.skipTest('Ruby is required for native menu compatibility fixtures')
        result=subprocess.run([ruby,'-e',script,str(ROOT/source)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
    def test_pc_touch_preserves_native_return_values_and_keyboard_fallback(self):
        self.run_ruby(r'''
module Settings;MAX_PARTY_SIZE=6;end
module PokemonBox;BOX_WIDTH=6;BOX_HEIGHT=5;end
module BlueLabPointer
  class << self;attr_accessor :position,:claimed;end
  def self.origin(s);[s.x,s.y];end
  def self.inside?(p,x,y,w,h);p && p[0]>=x && p[0]<x+w && p[1]>=y && p[1]<y+h;end
end
module BlueStartMouse
  class << self;attr_accessor :click;end
  def self.click?;v=click;self.click=false;v;end
end
Bitmap=Struct.new(:width)
Sprite=Struct.new(:x,:y,:bitmap)
Storage=Struct.new(:currentBox,:maxBoxes)
class NativeStorage
  attr_reader :storage
  def initialize
    @storage=Storage.new(0,32)
    @sprites={'box'=>Sprite.new(184,18,Bitmap.new(324)),'boxparty'=>Sprite.new(182,32),'arrow'=>Object.new}
  end
  def pbSelectBoxInternal(party);update;:keyboard_box;end
  def pbSelectPartyInternal(party,depositing);update;:keyboard_party;end
  def update;end
  def pbSetArrow(*);end
  def pbPartySetArrow(*);end
  def pbUpdateOverlay(*);end
  def pbSetMosaic(*);end
  def pbSwitchBoxToLeft(*);end
  def pbSwitchBoxToRight(*);end
end
load ARGV.fetch(0)
class StorageScene < NativeStorage;prepend BlueStorageMouse::Scene;end
scene=StorageScene.new
[[[216,72],[0,0]],[[442,250],[0,29]],[[420,338],[-3,-1]],[[250,338],[-2,-1]]].each do |point,expected|
  BlueLabPointer.position=point;BlueStartMouse.click=true
  raise "wrong native action #{point}" unless scene.pbSelectBoxInternal([])==expected
  raise 'pointer scope leaked' unless scene.instance_variable_get(:@blue_storage_scope).nil?
end
BlueLabPointer.position=[286,66];BlueStartMouse.click=true
raise 'wrong party slot' unless scene.pbSelectPartyInternal([],false)==1
BlueLabPointer.position=[216,300];BlueStartMouse.click=true
raise 'deposit Back differs from native' unless scene.pbSelectPartyInternal([],true)==-3
BlueLabPointer.position=[0,0];BlueStartMouse.click=true
raise 'outside tap overrides keyboard' unless scene.pbSelectBoxInternal([])==:keyboard_box
BlueLabPointer.position=[190,30];BlueStartMouse.click=true
scene.pbSelectBoxInternal([])
raise 'box arrow did not use native wrap' unless scene.storage.currentBox==31
''','scripts/battle_polish/StorageMouse.rb')
    def test_hub_reuses_catalog_between_pages_but_search_stays_correct(self):
        self.run_ruby(r'''
module BlueBattleLab;class Scene;end;end
Species=Struct.new(:id,:name,:types,:abilities,:hidden_abilities,:flags,:base_stats)
module BlueBattleHub
  class << self;attr_accessor :calls;end
  self.calls=0
  def self.species
    self.calls+=1
    [Species.new(:PIKACHU,'Pikachu',[:ELECTRIC],[],[],[],{}),Species.new(:EEVEE,'Eevee',[:NORMAL],[],[],[],{})]
  end
  def self.display(data);data.name;end
  def self.token(s);s.to_s.downcase.gsub(/[^a-z0-9]/,'');end
end
$PokemonSystem=Struct.new(:blue_locale).new('en')
load ARGV.fetch(0)
screen=BlueBattleHub::Screen.allocate
{teams:[[],[]],side:0,slot:0,tab: :species,query:'',fan:false,sort: :name,free_moves:false}.each { |k,v| screen.instance_variable_set('@'+k.to_s,v) }
first=screen.data_rows
200.times { raise 'catalog rescanned per render' unless screen.data_rows.equal?(first) }
screen.instance_variable_set(:@page,2)
raise 'paging rescanned catalog' unless screen.data_rows.equal?(first) && BlueBattleHub.calls==1
screen.instance_variable_set(:@query,'pika')
raise 'search stale after caching' unless screen.data_rows.map(&:id)==[:PIKACHU]
screen.instance_variable_set(:@query,'')
raise 'cleared search not restored' unless screen.data_rows.equal?(first)
''','scripts/battle_lab/HubUI.rb')

if __name__=='__main__':unittest.main()
