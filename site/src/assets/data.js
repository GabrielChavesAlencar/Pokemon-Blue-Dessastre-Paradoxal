export function activeLocations(locations,region){const hidden=new Set(region?.inactiveAreaIds??[]);return locations.filter(a=>!hidden.has(a.id));}
export async function loadPortal(){
  const files=['catalog','locations','updates','guides','story-trainers','region-points'];
  const values=await Promise.all(files.map(async name=>{const response=await fetch(`/data/${name}.json`);if(!response.ok)throw new Error(`Não foi possível abrir ${name}.`);return response.json();}));
  const approvedResponse=await fetch('/data/pokedex-approved.json');
  if(!approvedResponse.ok)throw new Error('Não foi possível abrir as descrições aprovadas.');
  const approved=(await approvedResponse.json()).species;
  for(const pokemon of values[0].species){
    const entry=approved[pokemon.id];
    if(entry){
      if(!pokemon.description||pokemon.description==='????')pokemon.description=entry.description;
      if(pokemon.height==null)pokemon.height=entry.height;
      if(pokemon.weight==null)pokemon.weight=entry.weight;
    }
  }
  const byId=new Map([...values[0].species,...(values[0].customForms??[])].map(p=>[p.id,p]));
  for(const [id,form] of Object.entries(values[0].encounterForms??{})){const base=byId.get(form.base);if(base)byId.set(id,{...base,name:base.name+' · '+form.name,encounterForm:form.form});}
  return {catalog:values[0],locations:activeLocations(values[1].locations,values[5]),encounterPolicy:values[1].authorEncounters,updates:values[2].commits,guides:values[3].guides,story:values[4],region:values[5],byId};
}
let regularData;
export async function loadRegularTrainers(){
  if(!regularData){const response=await fetch('/data/regular-trainers.json');if(!response.ok)throw new Error('Não foi possível carregar os treinadores.');regularData=await response.json();}
  return regularData;
}
let details;
export async function loadDetails(){if(!details){const response=await fetch('/data/details.json');if(!response.ok)throw new Error('Não foi possível abrir a ficha.');details=await response.json();}return details;}
export function effectiveDetail(base,form,data){
  const parent=data.species[base.id];if(!form)return {...parent,types:base.types,stats:base.stats};
  const result={...parent,...form,types:form.types.length?form.types:base.types,stats:form.stats.length?form.stats:base.stats,catchRate:form.catchRate||parent.catchRate};
  for(const [key,field] of [['abilities','Abilities'],['hidden','HiddenAbilities'],['moves','Moves'],['tutor','TutorMoves'],['egg','EggMoves'],['evolutions','Evolutions']])if(!form.own.includes(field))result[key]=parent[key];
  return result;
}
