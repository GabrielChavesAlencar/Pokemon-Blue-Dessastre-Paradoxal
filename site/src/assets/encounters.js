import {esc} from './utils.js';

export function rareEncounterNote(model,area=null,species=null){
  const policy=model.encounterPolicy;
  if(policy?.version!==2)return '';
  const rows=policy.areas.filter(row=>(!area||row.mapId===area.id)&&(!species||row.species.includes(species.id)));
  if(!rows.length)return '';
  const count=new Set(rows.flatMap(row=>row.species)).size;
  const title=species?`${species.name} · encontro raro de ${policy.chancePerSpecies}%`:area?`Paradoxos autorais nesta área · ${policy.chancePerSpecies}% por espécie`:`${count} Paradoxos autorais espalhados pelo mapa`;
  return `<aside class="rare-encounter-note"><strong>${esc(title)}</strong><p>Na campanha, as espécies de 570 BST aparecem a partir de ${policy.unlocks.crystals} cristais, na fase Master. Antes disso, seus espaços geram Pokémon compatíveis com os limites de 350, 450 e 540 BST. A chance é dentro do método de encontro indicado.</p>${area?`<p class="rare-habitat-reason">${rows.map(row=>esc(row.reason)).join(' ')}</p>`:''}</aside>`;
}
