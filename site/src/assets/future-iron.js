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
