export async function loadPortal(){
  const files=['catalog','locations','updates','guides'];
  const values=await Promise.all(files.map(async name=>{const response=await fetch(`/data/${name}.json`);if(!response.ok)throw new Error(`Não foi possível abrir ${name}.`);return response.json();}));
  const byId=new Map(values[0].species.map(p=>[p.id,p]));
  for(const [id,form] of Object.entries(values[0].encounterForms??{})){const base=byId.get(form.base);if(base)byId.set(id,{...base,name:base.name+' · '+form.name,encounterForm:form.form});}
  return {catalog:values[0],locations:values[1].locations,updates:values[2].commits,guides:values[3].guides,byId};
}
let details;
export async function loadDetails(){if(!details){const response=await fetch('/data/details.json');if(!response.ok)throw new Error('Não foi possível abrir a ficha.');details=await response.json();}return details;}
export function effectiveDetail(base,form,data){
  const parent=data.species[base.id];if(!form)return {...parent,types:base.types,stats:base.stats};
  const result={...parent,...form,types:form.types.length?form.types:base.types,stats:form.stats.length?form.stats:base.stats,catchRate:form.catchRate||parent.catchRate};
  for(const [key,field] of [['abilities','Abilities'],['hidden','HiddenAbilities'],['moves','Moves'],['tutor','TutorMoves'],['egg','EggMoves'],['evolutions','Evolutions']])if(!form.own.includes(field))result[key]=parent[key];
  return result;
}
