import {esc,icon} from './utils.js';

const phaseLabel=phase=>String(phase).padStart(2,'0')+'/16';
const stateNote='Prévia de documentação. Os mapas de Johto não foram instalados no jogo; nenhuma equipe PBS ou localização de captura foi validada.';
const classified=(trainers,route)=>route==='chefes'?
  trainers.filter(t=>['leader','elite'].includes(t.role)):
  trainers;
const listEntry=(title,detail)=>'<li><strong>'+esc(title)+'</strong><span>'+esc(detail)+'</span></li>';

export async function loadJohtoPreview(){
  const response=await fetch('/data/johto-preview.json');
  if(!response.ok)throw new Error('johto-preview-unavailable');
  const data=await response.json();
  if(data.schema!==1||data.region!=='JOHTO'||data.status!=='preview_only_not_playable'||
      !Array.isArray(data.trainers)||!Array.isArray(data.locations))throw new Error('johto-preview-invalid');
  return data;
}
export function johtoIndex(data,route){
  const names={localizacoes:'Locais planejados de Johto',treinadores:'Treinadores planejados de Johto',chefes:'Líderes e Elite planejados de Johto'};
  const isMap=route==='localizacoes';
  const items=isMap?data.locations:classified(data.trainers,route);
  const groups=[...new Set(items.map(row=>row.phase))].sort((a,b)=>a-b);
  const grouped=groups.map(phase=>{
    const entries=items.filter(row=>row.phase===phase);
    return '<section class="panel region-entry"><span class="eyebrow">ETAPA '+esc(phaseLabel(phase))+' · NÃO INSTALADA</span>'+
      '<h2>Planejamento da etapa '+esc(phaseLabel(phase))+'</h2>'+
      '<ul class="johto-preview-list">'+entries.map(row=>isMap?
        listEntry(row.name,'Mapa simbólico · sem MapID compilado e sem encontros verificados'):
        listEntry(row.name+' · '+row.id,
          row.badge?'Líder · insígnia '+row.badge+' · equipe PBS pendente':
          'Papel: '+row.role+' · versões previstas: '+row.versions.join(', ')+' · equipe PBS pendente')
      ).join('')+'</ul></section>';
  }).join('');
  const navigation=[['localizacoes','Localizações'],['treinadores','Treinadores'],['chefes','Líderes e Elite']].
    map(([key,label])=>'<a class="filter-chip'+(route===key?' active':'')+'" href="/'+key+'?regiao=johto"'+
      (route===key?' aria-current="page"':'')+'>'+esc(label)+'</a>').join('');
  return '<div class="container detail-container">'+
    '<a class="back-link" href="/regioes">← Circuito de regiões</a>'+
    '<header class="article-heading"><span class="eyebrow">JOHTO · PRÉVIA EXPERIMENTAL</span>'+
    '<h1>'+esc(names[route]||'Johto')+'</h1><p>'+esc(stateNote)+'</p></header>'+
    '<nav class="region-picker" aria-label="Seções planejadas de Johto">'+navigation+'</nav>'+
    '<section class="panel"><h2>Status da implementação</h2><p>'+esc(String(data.locations.length))+
    ' pontos simbólicos e '+esc(String(data.trainers.length))+
    ' tipos de treinadores documentados · <strong>0 mapas instalados, 0 equipes PBS compiladas, 0 músicas liberadas</strong>.</p>'+
    '<p>As oito insígnias locais de Johto e a página global de esmeraldas seguem o contrato regional do jogo. '+
    'As duas visualizações ainda dependem da integração real do piloto, sem dados fictícios de jogador.</p>'+
    '<p><a class="text-link" href="'+esc(data.links.tracker)+'" target="_blank" rel="noopener noreferrer">'+
    'Acompanhar progresso técnico '+icon('arrow')+'</a></p>'+'<p><a class="text-link" href="/liga?regiao=johto">Elite Four e campeão · referências históricas '+icon('arrow')+'</a></p></section>'+
    '<div class="region-entries">'+grouped+'</div></div>';
}
