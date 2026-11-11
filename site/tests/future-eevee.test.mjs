import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {mergeFutureCatalog,mergeFutureDetails,mergeRegionalLocations,futureSprite,futureEvolutionPanels} from '../src/assets/future-eevee.js';
import {filterSpecies,pokemonPath} from '../src/assets/utils.js';
import {pokemonCard} from '../src/assets/views.js';
import {pokemonDetail} from '../src/assets/detail.js';
import {teamPokemon} from '../src/assets/story.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(readFileSync(path.join(root,'public/data',name+'.json'),'utf8'));
const manifest=read('future-eevee');
const catalog=read('catalog');
const details=read('details');
mergeFutureCatalog(catalog,manifest);
mergeFutureCatalog(catalog,manifest);
mergeFutureDetails(details,manifest);
const model={catalog,locations:[],futureEevee:manifest,byId:new Map([...catalog.species,...catalog.customForms].map(p=>[p.id,p]))};
const state={q:'',type:'',generation:'dessastre-paradoxal',group:'future',sort:'number',limit:50,moveKind:'level',moveQ:'',moveLimit:50,form:'50'};

test('nove formas regionais futuras são registros adicionais, sem substituir Pokémon originais',()=>{
  assert.equal(manifest.forms.length,9);
  assert.equal(catalog.counts.futureRegionalForms,9);
  assert.equal(new Set(manifest.forms.map(entry=>entry.card.base)).size,9);
  assert.ok(manifest.forms.every(({card,details})=>card.future&&details.future&&card.form===50));
  assert.equal(catalog.species.length,1084,'contagem das espécies originais e autorais é preservada');
  assert.equal(catalog.species.find(p=>p.id==='EEVEE').types[0],'NORMAL');
  assert.equal(model.byId.get('EEVEE,50').types[0],'GHOST');
  assert.equal(filterSpecies([...catalog.species,...catalog.customForms],state).length,9);
  assert.equal(filterSpecies([...catalog.species,...catalog.customForms],{...state,group:'all'}).length,80);
});
test('nove linhas x sete papéis da arte enviada e atributos com BST preservado',()=>{
  const bytes=readFileSync(path.join(root,'public/assets/future-eevee/sprites-atlas.png'));
  assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
  assert.equal(bytes.readUInt32BE(16),896);
  assert.equal(bytes.readUInt32BE(20),1152);
  assert.deepEqual(manifest.atlas.roleOrder,['front','front-shiny','back','back-shiny','icon','icon-shiny','footprint']);
  for(let i=0;i<manifest.forms.length;i++){
    const {card,details:form}=manifest.forms[i];
    assert.equal(card.atlasRow,i);
    assert.equal(card.stats.reduce((sum,n)=>sum+n,0),card.base==='EEVEE'?325:525);
    assert.equal(card.types.length,1);
    assert.equal(form.moves.length,card.base==='EEVEE'?20:19);
    assert.ok(form.tm.length>=30);
    assert.equal(form.egg.length,12);
    assert.ok(futureSprite(card,'front').includes('background-position:'));
    assert.ok(futureSprite(card,'front-shiny').includes('role="img"'));
    assert.ok(futureSprite(card,'back-shiny').includes('sprites-atlas.png'));
    assert.ok(futureSprite(card,'icon-shiny').includes('background-size:700% 900%'));
    assert.ok(futureSprite(card,'footprint').includes('sprites-atlas.png'));
    assert.equal(pokemonPath(card),'/pokedex/'+card.base+'?forma=50');
  }
});
test('cada evolução tem condição única e explicação visível; Eevee fantasma tem oito caminhos',()=>{
  assert.equal(Object.keys(manifest.evolutions).length,8);
  assert.equal(new Set(Object.values(manifest.evolutions).map(x=>x.methodId)).size,8);
  assert.ok(Object.values(manifest.evolutions).every(x=>x.minLevel>=28&&x.conditions.length>=3));
  const ghost=manifest.forms[0].card;
  const panel=futureEvolutionPanels(model,ghost);
  assert.equal((panel.match(/class="future-evo-option"/g)||[]).length,8);
  for(const {card} of manifest.forms.slice(1)){
    const panel=futureEvolutionPanels(model,card);
    assert.ok(panel.includes(manifest.evolutions[card.base].title));
    assert.match(panel,/Eevee regional · Fantasma/);
    assert.match(panel,/Método implementado na engine Blue/);
  }
});
test('ficha da Dex mostra sprites reais, tipos, habilidades, níveis e evolução sem afetar a forma base',()=>{
  for(const {card} of manifest.forms){
    const base=model.byId.get(card.base);
    const html=pokemonDetail(model,base,details,state,new Set());
    assert.match(html,/Forma regional jogável/);
    assert.match(html,/sprites-atlas.png/);
    assert.match(html,/image-rendering|background-size:700% 900%/);
    assert.match(html,/regional jogável|Evoluções regionais/i);
    assert.match(html,/Sprites de/);
    assert.match(html,/Atributos base/);
    assert.match(html,/HABILIDADES/);
    assert.match(html,/Golpes e aprendizado/);
    assert.ok(pokemonCard(card).includes('FORMA REGIONAL DISPONÍVEL'));
    assert.equal(details.species[card.id].evolutions.length,0);
  }
  const eevee=model.byId.get('EEVEE');
  const official=pokemonDetail(model,eevee,details,{...state,form:''},new Set());
  assert.doesNotMatch(official,/Forma regional jogável/);
  assert.match(official,/Forma padrão/);
  assert.match(official,/Eevee regional/);
});
test('mesclagem é idempotente e não coloca formas futuras em encontros ou no banco de batalha',()=>{
  const clone=structuredClone(catalog);
  mergeFutureCatalog(clone,manifest);
  assert.equal(clone.customForms.filter(x=>x.future).length,9);
  assert.ok(manifest.forms.every(x=>x.card.pending===false&&x.card.future===true));
  assert.ok(manifest.forms.every(x=>x.details.learnsetStatus==='design-proposal-only'));
});

test('nove encontros regionais aparecem em áreas distintas com probabilidades precisas',()=>{
  const base=read('locations'),plans=read('eevee-regional-encounters');
  assert.equal(plans.areas.length,9);
  assert.equal(new Set(plans.areas.map(p=>p.mapId)).size,9);
  assert.equal(plans.areas.find(p=>p.species==='EEVEE_50').percent,20);
  assert.ok(plans.areas.filter(p=>p.species!=='EEVEE_50').every(p=>p.percent===5));
  mergeRegionalLocations(base,plans);
  const snapshot=JSON.stringify(base);
  mergeRegionalLocations(base,plans);
  assert.equal(JSON.stringify(base),snapshot,'nunca duplicar encontros regionais');
  for(const plan of plans.areas){
    const area=base.locations.find(a=>a.id===plan.mapId);
    assert.ok(area,'área existente '+plan.name);
    for(const version of area.versions){
      const method=version.methods.find(m=>m.id===plan.method);
      if(!method)continue;
      const chance=method.slots.filter(row=>row[0]===plan.species).reduce((sum,row)=>sum+row[3],0);
      assert.equal(chance,plan.percent,plan.name+' versão '+version.id);
      assert.equal(method.slots.reduce((sum,row)=>sum+row[3],0),100,'pesos somam 100');
      const rare=(base.authorEncounters?.areas||[]).filter(a=>a.mapId===plan.mapId&&a.method===plan.method);
      for(const record of rare)for(const id of record.species)
        assert.equal(method.slots.find(row=>row[0]===id)?.[3],5,'paradoxos preservados');
    }
    assert.ok(area.species.includes(plan.species));
  }
});

test('a ficha de treinador renderiza sprite regional também quando Form vem como texto no PBS',()=>{
  const p={species:'VAPOREON',form:'50',level:35};
  const html=teamPokemon(p,model,details);
  assert.match(html,/future-team-sprite/);
  assert.match(html,/sprites-atlas\.png/);
  assert.match(html,/Vaporeon regional/);
});
