// Website-only preview of seven fan-made future Paradox Pokémon.
// Never writes to the Decades game, PBS, trainers, encounters or saves.
export function mergeIronCatalog(catalog,manifest){
  if(!manifest?.forms?.length)return catalog;
  const known=new Set(catalog.species.map(p=>p.id));
  const incoming=manifest.forms.map(x=>x.card).filter(p=>!known.has(p.id));
  catalog.species.push(...incoming);
  catalog.counts.species=catalog.species.length;
  catalog.counts.paradox=catalog.species.filter(p=>p.flags?.includes('Paradox')).length;
  catalog.counts.plannedFutureParadoxes=manifest.forms.length;
  return catalog;
}
export function mergeIronDetails(details,manifest){
  if(!manifest?.forms?.length)return details;
  for(const {card,details:profile} of manifest.forms){
    if(!details.species[card.id]||details.species[card.id].designOnly){
      details.species[card.id]={...profile};
    }
  }
  return details;
}

/** Planned encounters on the portal only, never exportable to the game. */
export function mergeIronLocations(data,placements,regionalPlans){
  if(!placements?.encounters?.length)return data;
  const planned=placements.encounters;
  if(planned.length!==7||new Set(planned.map(p=>p.species)).size!==7||new Set(planned.map(p=>p.mapId)).size!==7)
    throw new Error('O plano dos sete Paradoxos futuros está incompleto ou duplicado.');
  const authorRare=data.authorEncounters?.areas||[];
  for(const p of planned){
    if(p.percent!==5)throw new Error('Paradoxo futuro precisa de 5%: '+p.species);
    const area=data.locations.find(a=>a.id===p.mapId);
    if(!area||area.name!==p.name)throw new Error('Mapa futuro não encontrado: '+p.name);
    const fixed=new Set([
      ...authorRare.filter(a=>a.mapId===p.mapId&&a.method===p.method).flatMap(a=>a.species),
      ...(regionalPlans?.areas||[]).filter(a=>a.mapId===p.mapId&&a.method===p.method).map(a=>a.species)
    ]);
    for(const version of area.versions){
      const method=version.methods.find(m=>m.id===p.method);
      if(!method)throw new Error('Método ausente: '+p.name+' '+p.method+' '+version.id);
      const previous=method.slots.filter(row=>row[0]===p.species);
      const total=()=>method.slots.reduce((sum,row)=>sum+row[3],0);
      if(previous.length){
        if(previous.length!==1||previous[0][3]!==5||total()!==100)throw new Error('Encontro futuro incorreto: '+p.species);
        continue;
      }
      const held=method.slots.filter(row=>fixed.has(row[0]));
      const ordinary=method.slots.filter(row=>!fixed.has(row[0]));
      const reserved=held.reduce((sum,row)=>sum+row[3],0);
      const remainder=100-p.percent-reserved;
      if(!ordinary.length||remainder<ordinary.length)throw new Error('Sem espaço para Paradoxo futuro: '+p.name);
      const available=ordinary.reduce((sum,row)=>sum+row[3],0);
      if(available<=0)throw new Error('Pesos inválidos: '+p.name);
      // Reserve one point per original slot before proportional apportionment.
      const balance=remainder-ordinary.length;
      const weights=ordinary.map(row=>1+Math.floor(Math.max(0,row[3]-1)*(balance)/Math.max(1,available-ordinary.length)));
      // For normal encounter tables, allocate by their current weights.
      // Largest remainder preserves the total precisely and is deterministic.
      const fractions=ordinary.map((row,i)=>({i,value:row[3]/available*remainder}));
      const normalized=fractions.map(x=>Math.floor(x.value));
      if(normalized.some(x=>x<1)){
        // Use the reserved-one distribution only for very small individual slots.
        const target=ordinary.map(row=>Math.max(0,row[3]-1));
        const sum=target.reduce((a,b)=>a+b,0);
        const exact=target.map(w=>sum?w*balance/sum:balance/target.length);
        for(let i=0;i<weights.length;i++)weights[i]=1+Math.floor(exact[i]);
        const leftovers=balance-weights.reduce((a,b)=>a+b-1,0);
        const order=exact.map((v,i)=>({i,f:v-Math.floor(v)})).sort((a,b)=>b.f-a.f||a.i-b.i);
        for(const {i} of order.slice(0,leftovers))weights[i]++;
      }else{
        const leftovers=remainder-normalized.reduce((a,b)=>a+b,0);
        const order=fractions.map((x,i)=>({i,f:x.value-Math.floor(x.value)})).sort((a,b)=>b.f-a.f||a.i-b.i);
        for(const {i} of order.slice(0,leftovers))normalized[i]++;
        for(let i=0;i<weights.length;i++)weights[i]=normalized[i];
      }
      // Preserve all protected 5% Paradox and Eevee regional 5% / 20% rows.
      const levelRow=ordinary.find(row=>row[1]>1||row[2]>1)??ordinary[0];
      method.slots=[...ordinary.map((row,i)=>[row[0],row[1],row[2],weights[i]]),...held,
        [p.species,levelRow[1],levelRow[2],p.percent]];
      if(total()!==100)throw new Error('Probabilidades não somam 100: '+p.name);
    }
    area.plannedIronEncounters=[...(area.plannedIronEncounters||[]).filter(x=>x.species!==p.species),{...p}];
    area.species=[...new Set(area.versions.flatMap(v=>v.methods.flatMap(m=>m.slots.map(row=>row[0]))))].sort();
  }
  return data;
}

/** Attach planned Master teams without ever mutating source PBS team arrays. */
export function mergeIronTrainerPlans(data,placements){
  if(!placements?.trainers?.length)return data;
  if(placements.trainers.length!==7||new Set(placements.trainers.map(p=>p.trainerId)).size!==7)
    throw new Error('Plano de treinadores Paradoxos futuros incompleto.');
  for(const plan of placements.trainers){
    const trainer=data.trainers.find(t=>t.id===plan.trainerId);
    if(!trainer||trainer.name!==plan.trainerName||trainer.location!==plan.location||trainer.team.length>=6)
      throw new Error('Treinador futuro não encontrado ou equipe cheia: '+plan.trainerName);
    if(plan.mode!=='master')throw new Error('Paradoxo planejado deve ser para o modo Master.');
    trainer.plannedIronSpecies=plan.species;
    trainer.plannedIronReason=plan.reason;
  }
  return data;
}
