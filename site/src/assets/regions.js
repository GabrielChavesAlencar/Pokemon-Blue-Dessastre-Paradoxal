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
      (['KANTO','JOHTO','HOENN'].includes(key)?
        '<p class="data-note">Regra regional compartilhada: nível selvagem = 45% do maior nível da equipe; evoluções automáticas por nível podem ocupar 35% da vaga da forma base. '+
        (key==='KANTO'?'Kanto exige instalação/reteste do piloto atualizado.':
         key==='JOHTO'?'Johto continua em preparação, sem encontros jogáveis verificados.':
         'Hoenn ainda aguarda mapas e encontros autorizados, compilados e testados.')+'</p>':'')+
      (key==='DECADES'?'<a class="text-link" href="/localizacoes">Ver mapa e encontros '+icon('arrow')+'</a>':'')+
      (key==='KANTO'?'<a class="text-link" href="/localizacoes?regiao=kanto">Explorar piloto '+icon('arrow')+'</a>':'')+
      (key==='JOHTO'?'<a class="text-link" href="/localizacoes?regiao=johto">Ver planejamento de Johto '+icon('arrow')+'</a>':'')+
      '</article>';
  }).join('');
  return '<div class="container detail-container"><a class="back-link" href="/localizacoes">← Localizações</a>'+
    '<header class="article-heading"><span class="eyebrow">EXPANSÃO DA CAMPANHA</span>'+
    '<h1>Circuito de regiões</h1><p>Decades segue jogável. Confira a ordem do circuito e o estado de cada campanha planejada.</p></header>'+
    '<ol class="region-circuit" aria-label="Ordem do circuito">'+order+'</ol><div class="region-entries">'+cards+'</div></div>';
}

export function regionPicker(page,region){
  const choices=[['decades','Decades','/'+page],['kanto','Kanto','/'+page+'?regiao=kanto'],['johto','Johto · prévia','/'+page+'?regiao=johto']];
  return '<nav class="region-picker" aria-label="Selecionar região">'+choices.map(([id,name,href])=>
    '<a class="filter-chip'+(id===region?' active':'')+'" href="'+href+'"'+
    (id===region?' aria-current="page"':'')+'>'+name+'</a>').join('')+'</nav>';
}

