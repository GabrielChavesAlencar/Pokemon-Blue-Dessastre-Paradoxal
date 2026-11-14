import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {pendingBlocks,pendingPage,pendingOnlyRegion,loadPendingRegions} from '../src/assets/pending.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../');
const pending=JSON.parse(await readFile(path.join(root,'public/data/pending-regions.json'),'utf8'));
const sourceNames=['KANTO','JOHTO','HOENN','SINNOH'];
const normalize=name=>name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');

test('all four regional backlogs have maps, trainers, eight gyms and four elite members',()=>{
  assert.equal(pending.schema,1);
  assert.equal(pending.state,'REFERENCE_NOT_NATIVE_GAMEPLAY');
  assert.deepEqual(Object.keys(pending.regions),sourceNames);
  for(const [name,region] of Object.entries(pending.regions)){
    assert.ok(region.areas.length>20,name+': missing area coverage');
    assert.ok(region.trainers.length>=5,name+': missing common trainer audit coverage');
    assert.equal(region.leaders.length,8,name);
    assert.equal(region.elite_four.length,4,name);
    assert.equal(region.champion.length,1,name);
    for(const [category,rows] of Object.entries(region).filter(([key,val])=>Array.isArray(val))){
      const ids=new Set();
      for(const item of rows){
        assert.ok(['not_added','native_qa_pending'].includes(item.status),name+'/'+category+'/'+item.name);
        assert.ok(item.name?.trim(),name+'/'+category);
        assert.ok(item.notes?.trim(),name+'/'+category);
        assert.ok(!('map_id' in item) && !('x' in item) && !('y' in item),name+'/'+category+'/'+item.name);
        assert.ok(!('rate' in item) && !('level' in item) && !('team' in item),name+'/'+category+'/'+item.name);
        const id=normalize(item.name);
        assert.ok(!ids.has(id),name+'/'+category+' duplicate '+item.name);
        ids.add(id);
      }
    }
  }
});
test('static status appears BELOW names for planned areas, trainers, leaders, Elite Four and champions',()=>{
  for(const region of sourceNames){
    for(const category of ['localizacoes','treinadores','chefes','liga']){
      const html=pendingBlocks(pending,region,category);
      assert.match(html,region==='KANTO'&&['chefes','liga'].includes(category)?/Em validação/:/Ainda não adicionado/);
      assert.ok(html.indexOf('<h3>')<html.indexOf('class="content-pending-tag'));
      assert.match(html,/Sem|pend|MapID|jogo|PBS|treinador|L[ií]ga|local/i);
    }
  }
});
test('existing pilot entries are not repeated in regional pending sections',()=>{
  const html=pendingBlocks(pending,'JOHTO','localizacoes',{excludeNames:['Route 29','New Bark Town']});
  assert.doesNotMatch(html,/<h3>Route 29<\/h3>/);
  assert.doesNotMatch(html,/<h3>New Bark Town<\/h3>/);
  assert.match(html,/<h3>Route 32<\/h3>/);
});
test('four region filters work, Sinnoh has a safe prototype-only page, and HTML escapes',()=>{
  const html=pendingPage(pending,'SINNOH');
  assert.match(html,/pendencias\?regiao=kanto/);
  assert.match(html,/pendencias\?regiao=hoenn/);
  assert.match(html,/pendencias\?regiao=sinnoh/);
  assert.match(html,/Cynthia/);
  const sinnoh=pendingOnlyRegion(pending,'SINNOH','localizacoes');
  assert.match(sinnoh,/Sinnoh/);
  assert.match(sinnoh,/Ainda não adicionado/);
  const injected=structuredClone(pending);
  injected.regions.SINNOH.areas.push({name:'<script>unsafe</script>',notes:'<img src=x>',status:'not_added'});
  const safe=pendingBlocks(injected,'SINNOH','localizacoes');
  assert.doesNotMatch(safe,/<script>unsafe/);
  assert.match(safe,/&lt;script&gt;/);
});
test('pending catalog loader checks schema and source',async()=>{
  // Fresh module-level cache at first test call; use local fixture instead of network.
  const result=await loadPendingRegions(async uri=>({
    ok:uri==='/data/pending-regions.json',json:async()=>pending
  }));
  assert.equal(result.regions.KANTO.leaders[0].name,'Brock');
  assert.equal(result.regions.KANTO.leaders[0].status,'native_qa_pending');
  assert.equal(result.regions.SINNOH.champion[0].name,'Cynthia');
});
