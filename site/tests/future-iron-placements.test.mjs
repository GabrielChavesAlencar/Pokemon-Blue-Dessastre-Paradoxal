import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {mergeFutureCatalog,mergeFutureDetails,mergeRegionalLocations} from '../src/assets/future-eevee.js';
import {mergeIronCatalog,mergeIronDetails,mergeIronLocations,mergeIronTrainerPlans} from '../src/assets/future-iron.js';
import {regularTeam,regularDetail,regularResults} from '../src/assets/regular-trainers.js';
import {locationDetail} from '../src/assets/views.js';
import {pokemonDetail} from '../src/assets/detail.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>JSON.parse(readFileSync(path.join(root,'public/data',name+'.json'),'utf8'));
const placement=read('future-iron-placements');
const iron=read('future-iron');
const regional=read('eevee-regional-encounters');
const eevee=read('future-eevee');
const sum=slots=>slots.reduce((total,row)=>total+row[3],0);
const chance=(slots,id)=>slots.filter(row=>row[0]===id).reduce((total,row)=>total+row[3],0);
function locationsWithPreviews(){
 const data=read('locations');
 mergeRegionalLocations(data,regional);
 mergeIronLocations(data,placement,regional);
 return data;
}
function prepared(){
 const catalog=read('catalog'),details=read('details');
 mergeFutureCatalog(catalog,eevee);
 mergeIronCatalog(catalog,iron);
 mergeFutureDetails(details,eevee);
 mergeIronDetails(details,iron);
 const loc=locationsWithPreviews();
 const regular=read('regular-trainers');
 mergeIronTrainerPlans(regular,placement);
 const byId=new Map([...catalog.species,...catalog.customForms].map(p=>[p.id,p]));
 for(const {card} of eevee.forms)byId.set(card.base+'_50',{...card,id:card.base,encounterForm:50});
 const model={catalog,byId,locations:loc.locations,encounterPolicy:loc.authorEncounters,
  story:{masters:[]},region:{},futureEevee:eevee,futureIron:iron,futureIronPlacements:placement};
 return {model,details,regular};
}

test('sete habitats coerentes com uma espécie por mapa, método válido e 5% em todas as versões',()=>{
 assert.equal(placement.encounters.length,7);
 assert.equal(placement.trainers.length,7);
 assert.equal(new Set(placement.encounters.map(p=>p.mapId)).size,7);
 assert.deepEqual(new Set(placement.encounters.map(p=>p.species)),
   new Set(iron.forms.map(f=>f.card.id)));
 const base=read('locations');
 mergeRegionalLocations(base,regional);
 const before=structuredClone(base);
 mergeIronLocations(base,placement,regional);
 for(const plan of placement.encounters){
   assert.equal(plan.percent,5);
   const area=base.locations.find(a=>a.id===plan.mapId);
   const original=before.locations.find(a=>a.id===plan.mapId);
   assert.equal(area.name,plan.name);
   assert.equal(area.plannedIronEncounters.length,1);
   assert.ok(area.species.includes(plan.species));
   for(const version of area.versions){
     const target=version.methods.find(m=>m.id===plan.method);
     const originalMethod=original.versions.find(v=>v.id===version.id).methods.find(m=>m.id===plan.method);
     assert.equal(chance(target.slots,plan.species),5,plan.species+' versão '+version.id);
     assert.equal(target.slots.filter(row=>row[0]===plan.species).length,1);
     assert.equal(sum(target.slots),100,plan.species+' versão '+version.id);
     assert.ok(target.slots.every(row=>row[3]>0));
     assert.deepEqual(version.methods.filter(m=>m.id!==plan.method),
       original.versions.find(v=>v.id===version.id).methods.filter(m=>m.id!==plan.method),
       'métodos não planejados permanecem inalterados');
     for(const p of before.authorEncounters?.areas||[]){
       if(p.mapId!==plan.mapId||p.method!==plan.method)continue;
       for(const id of p.species)assert.equal(chance(target.slots,id),chance(originalMethod.slots,id),'Paradoxo já existente: '+id);
     }
     for(const p of regional.areas){
       if(p.mapId!==plan.mapId||p.method!==plan.method)continue;
       assert.equal(chance(target.slots,p.species),p.percent,'Eevee regional preservado: '+p.species);
     }
   }
 }
 const once=JSON.stringify(base);
 mergeIronLocations(base,placement,regional);
 assert.equal(JSON.stringify(base),once,'distribuição idempotente');
});

test('sete treinadores já existentes recebem um Paradoxo só na prévia Master, sem alterar os times PBS',()=>{
 const {regular,model,details}=prepared();
 assert.equal(regular.trainers.length,63);
 assert.equal(regular.trainers.filter(t=>t.plannedIronSpecies).length,7);
 const source=read('regular-trainers');
 for(const plan of placement.trainers){
   const trainer=regular.trainers.find(t=>t.id===plan.trainerId);
   const original=source.trainers.find(t=>t.id===plan.trainerId);
   assert.equal(trainer.name,plan.trainerName);
   assert.equal(trainer.location,plan.location);
   assert.deepEqual(trainer.team,original.team,'team PBS preservado');
   const basic=regularTeam(model,regular,trainer,'beginner',details,50);
   const advanced=regularTeam(model,regular,trainer,'advanced',details,50);
   const master=regularTeam(model,regular,trainer,'master',details,50);
   assert.ok(!basic.team.some(p=>p.species===plan.species));
   assert.ok(!advanced.team.some(p=>p.species===plan.species));
   assert.equal(master.team.filter(p=>p.species===plan.species).length,1);
   assert.equal(master.team.find(p=>p.species===plan.species).planned,true);
   assert.equal(master.team.find(p=>p.species===plan.species).level,45);
   assert.equal(master.team.find(p=>p.species===plan.species).ability,'Quark Drive');
   assert.ok(master.team.length<=6);
   assert.equal(master.team.filter(p=>p.preview&&p.species===plan.species).length,0);
   assert.equal(master.team.find(p=>p.species===plan.species).moves.length,4);
   const html=regularDetail(model,regular,trainer,'master',details,50);
   assert.match(html,/PARADOXO FUTURO PLANEJADO/);
   assert.match(html,/prévia do site/);
 }
 assert.equal(regularResults(model,regular,{trainerQ:'Iron Oracle',trainerArea:'all',trainerLimit:100}).count,1);
});

test('fichas e mapa separam claramente encontros futuros dos disponíveis no Game.exe',()=>{
 const {model,details}=prepared();
 const plan=placement.encounters[0];
 const area=model.locations.find(a=>a.id===plan.mapId);
 const mapHTML=locationDetail(model,area,{version:'0'});
 assert.match(mapHTML,/5%/);
 assert.match(mapHTML,/IRONORACLE|Iron Oracle/);
 assert.match(mapHTML,/Prévia exclusiva do site/);
 assert.match(mapHTML,/sprites-atlas.png/);
 const species=model.byId.get(plan.species);
 const dexHTML=pokemonDetail(model,species,details,{moveKind:'level',moveQ:'',moveLimit:40,form:''},new Set());
 assert.match(dexHTML,/Encontro futuro planejado em/);
 assert.match(dexHTML,/Treinador planejado/);
 assert.match(dexHTML,/não aparece no jogo/);
 assert.match(dexHTML,/treinadores/);
});
