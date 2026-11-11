import {esc,icon,types,pokemonPath} from './utils.js';

export const FUTURE_EEVEE_FORM=50;
const roles=['front','front-shiny','back','back-shiny','icon','icon-shiny','footprint'];

export function mergeFutureCatalog(catalog,manifest){
  if(!manifest?.forms?.length)return catalog;
  const existing=new Set((catalog.customForms??[]).map(x=>x.id));
  const newForms=manifest.forms.map(x=>x.card).filter(x=>!existing.has(x.id));
  catalog.customForms=[...(catalog.customForms??[]),...newForms];
  catalog.counts.futureRegionalForms=(catalog.customForms??[]).filter(x=>x.future===true).length;
  return catalog;
}
export function mergeFutureDetails(details,manifest){
  if(!manifest?.forms?.length)return details;
  for(const entry of manifest.forms){
    const id=entry.card.id;
    details.species[id]={...entry.details};
  }
  for(const [id,entry] of Object.entries(manifest.moveNames??{})){
    if(details.moves[id])continue;
    details.moves[id]={name:entry.name,type:entry.type||'NORMAL',category:entry.category||'Status',
      power:0,accuracy:0,pp:0,futureProposal:true};
  }
  return details;
}
export function futureSprite(p,role='front',className=''){
  if(!p?.future||!p.spriteAtlas||!Number.isInteger(p.atlasRow))return '';
  const col=roles.indexOf(role);
  if(col<0)return '';
  const x=Number((col/6*100).toFixed(4)),y=Number((p.atlasRow/8*100).toFixed(4));
  const style='background-image:url('+JSON.stringify(p.spriteAtlas)+');background-size:700% 900%;'+
    'background-position:'+x+'% '+y+'%;';
  return '<span class="future-sprite '+esc(className)+'" role="img" aria-label="'+
    esc(p.name+' · '+({'front':'frente','front-shiny':'frente shiny','back':'costas','back-shiny':'costas shiny',
      'icon':'ícone','icon-shiny':'ícone shiny','footprint':'pegada'}[role]))+'" style="'+esc(style)+'"></span>';
}
export function futureEvolutionPanels(model,profile){
  if(!profile?.future)return '';
  const manifest=model.futureEevee;
  if(!manifest?.forms?.length)return '';
  if(profile.base==='EEVEE'){
    const links=manifest.forms.filter(x=>x.card.base!=='EEVEE').map(entry=>{
      const rule=manifest.evolutions[entry.card.base];
      return '<a class="future-evo-option" href="'+pokemonPath(entry.card)+'">'+
        futureSprite(entry.card,'icon','future-evo-icon')+
        '<span><b>'+esc(entry.card.name)+'</b><small>'+esc(types[entry.card.types[0]]??entry.card.types[0])+
        ' · '+esc(rule?.title||'Evolução planejada')+'</small><em>'+esc(rule?.summary??'')+'</em></span>'+icon('arrow')+'</a>';
    }).join('');
    return '<section class="panel future-evo-panel"><div class="panel-heading"><div><span class="eyebrow">OITO CAMINHOS REGIONAIS</span>'+
      '<h2>Evoluções futuras do Eevee Fantasma</h2></div></div><p class="panel-note">'+
      'As condições abaixo são propostas inéditas e ainda não funcionam no jogo. Eevee original mantém suas evoluções.</p>'+
      '<div class="future-evo-grid">'+links+'</div></section>';
  }
  const rule=manifest.evolutions[profile.base];
  if(!rule)return '';
  const eevee=manifest.forms.find(x=>x.card.base==='EEVEE')?.card;
  return '<section class="panel future-evo-panel"><div class="panel-heading"><div><span class="eyebrow">EVOLUÇÃO REGIONAL · PROPOSTA</span>'+
    '<h2>'+esc(rule.title)+'</h2></div></div>'+
    (eevee?'<a class="future-evo-origin" href="'+pokemonPath(eevee)+'">'+
      futureSprite(eevee,'icon','future-evo-icon')+'<span>Evolui de <b>Eevee regional · Fantasma</b></span>'+icon('arrow')+'</a>':'')+
    '<p class="panel-note">'+esc(rule.summary)+'</p><ul class="future-requirements">'+
    (rule.conditions||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>'+
    '<p class="future-requirements-note">Local sugerido: '+esc(rule.location||'não definido')+
    '. Requer método próprio na engine; não disponível em saves ou batalhas atuais.</p></section>';
}
