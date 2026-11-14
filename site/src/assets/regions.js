import {esc,icon} from './utils.js';

export async function loadRegions(){
  const response=await fetch('/data/regions.json');
  if(!response.ok) throw new Error('regions-unavailable');
  return response.json();
}

export function regionsPage(registry){
  const {regions,circuit,hisui}=registry;
  const labels={playable:'Jogável',prototype:'Piloto em preparação',planned:'Planejada'};
  const order=circuit.map(key=>'<li>'+esc(regions[key].name)+'</li>').join('');
  const cards=[...circuit,'HISUI'].map((key,i)=>{
    const region=regions[key];
    const description=key==='HISUI'
      ? 'Expedição sem Liga. Quem começa em Hisui libera '+hisui.startExits.map(id=>regions[id].name).join(' e ')+' ao terminar o arco principal.'
      : 'O final da Liga libera '+[circuit.at(i-1),circuit[(i+1)%circuit.length]].map(id=>regions[id].name).join(' e ')+'.';
    return '<article class="panel region-entry"><span class="eyebrow">'+labels[region.status]+
      '</span><h2>'+esc(region.name)+'</h2><p><strong>'+esc(region.base)+'</strong></p><p>'+esc(description)+'</p>'+
      (region.pilot?'<p>Trecho em preparação: '+region.pilot.map(esc).join(', ')+'.</p>':'')+
      (key==='DECADES'?'<a class="text-link" href="/localizacoes">Ver mapa e encontros '+icon('arrow')+'</a>':'')+
      (key==='KANTO'?'<a class="text-link" href="/localizacoes?regiao=kanto">Explorar piloto '+icon('arrow')+'</a>':'')+
      (key==='JOHTO'?'<a class="text-link" href="/localizacoes?regiao=johto">Explorar piloto de Johto '+icon('arrow')+'</a>':'')+
      (key==='HOENN'?'<a class="text-link" href="/localizacoes?regiao=hoenn">Explorar piloto de Hoenn '+icon('arrow')+'</a>':'')+
      (key==='SINNOH'?'<a class="text-link" href="/localizacoes?regiao=sinnoh">Ver pendências de Sinnoh '+icon('arrow')+'</a>':'')+
      (['KANTO','JOHTO','HOENN','SINNOH'].includes(key)?'<p><a class="text-link" href="/pendencias?regiao='+key.toLowerCase()+'">Próximas fases · Não adicionado '+icon('arrow')+'</a></p>':'')+
      '</article>';
  }).join('');
  return '<div class="container detail-container"><a class="back-link" href="/localizacoes">← Localizações</a>'+
    '<header class="article-heading"><span class="eyebrow">EXPANSÃO DA CAMPANHA</span>'+
    '<h1>Circuito de regiões</h1><p>Decades segue jogável. Confira a ordem do circuito e o estado de cada campanha planejada.</p></header>'+
    '<ol class="region-circuit" aria-label="Ordem do circuito">'+order+'</ol><div class="region-entries">'+cards+'</div></div>';
}

export function regionPicker(page,region){
  const choices=[['decades','Decades','/'+page],['kanto','Kanto','/'+page+'?regiao=kanto'],['johto','Johto','/'+page+'?regiao=johto'],['hoenn','Hoenn','/'+page+'?regiao=hoenn'],['sinnoh','Sinnoh','/'+page+'?regiao=sinnoh']];
  return '<nav class="region-picker" aria-label="Selecionar região">'+choices.map(([id,name,href])=>
    '<a class="filter-chip'+(id===region?' active':'')+'" href="'+href+'"'+
    (id===region?' aria-current="page"':'')+'>'+name+'</a>').join('')+'</nav>';
}

