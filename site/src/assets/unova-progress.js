import {esc} from './utils.js';

const STATES=new Set(['done','pending','in_progress','blocked']);
export async function loadUnovaGithubProgress(fetcher=fetch){
  const response=await fetcher('/data/unova-github-progress.json');
  if(!response.ok)throw new Error('unova-progress-unavailable');
  return response.json();
}

export function unovaGithubStats(data){
  if(data?.schema!==1 || data?.region!=='UNOVA' ||
      data.track!=='GITHUB_ONLY_DEVELOPMENT' ||
      !Array.isArray(data.groups) || data.groups.length!==8) {
    throw new Error('unova-progress-schema-invalid');
  }
  const seen=new Set();
  const groups=data.groups.map(group=>{
    if(!/^G0[1-8]$/.test(group.id) || !Array.isArray(group.tasks) ||
        group.tasks.length!==4)throw new Error('unova-progress-group-invalid');
    const tasks=group.tasks;
    for(const task of tasks){
      if(!/^G0[1-8]\.[1-4]$/.test(task.id) ||
          !task.id.startsWith(group.id+'.') || !STATES.has(task.status) ||
          seen.has(task.id) || !task.title || !task.acceptance ||
          (task.status==='done'&&!task.evidence)) {
        throw new Error('unova-progress-task-invalid');
      }
      seen.add(task.id);
    }
    return {...group,completed:tasks.filter(t=>t.status==='done').length,
      inProgress:tasks.filter(t=>t.status==='in_progress').length};
  });
  if(seen.size!==32)throw new Error('unova-progress-incomplete');
  if(data.status!=='PLANNED_NOT_NATIVE_PLAYABLE' ||
      data.native_technical_bar?.completed!==0 ||
      data.native_playable_bar?.completed!==0 ||
      data.native_technical_bar?.total!==8 ||
      data.native_playable_bar?.total!==32) {
    throw new Error('unova-progress-native-status-false');
  }
  const completed=groups.reduce((n,g)=>n+g.completed,0);
  return {groups,total:32,completed,inProgress:groups.reduce((n,g)=>n+g.inProgress,0),
    remaining:32-completed,percent:Math.round(completed/32*100)};
}

const evidenceLink=path=>{
  if(!/^(?:site\/|scripts\/|data\/|docs\/|tests\/)[a-zA-Z0-9_./-]+$/.test(path) ||
      path.includes('..'))return '';
  return '<a class="text-link" href="https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/'+
    encodeURI(path)+'" target="_blank" rel="noopener noreferrer">Ver evidência no GitHub</a>';
};

export function unovaGithubProgressPage(data){
  const stats=unovaGithubStats(data);
  const groupMarkup=stats.groups.map(group=>{
    const tasks=group.tasks.map(task=>'<li class="unova-progress-task">'+
      '<div class="unova-progress-task-head"><strong>'+esc(task.id+' · '+task.title)+'</strong>'+
      '<span class="unova-progress-status '+(task.status==='done'?'is-done':'')+'">'+
      (task.status==='done'?'Concluída':task.status==='in_progress'?'Em andamento':task.status==='blocked'?'Bloqueada':'Pendente')+'</span></div>'+
      '<p>'+esc(task.acceptance)+'</p>'+
      (task.evidence?'<p>'+evidenceLink(task.evidence)+'</p>':'')+'</li>').join('');
    return '<section class="panel unova-progress-group" aria-labelledby="unova-'+esc(group.id)+'">'+
      '<header><span class="eyebrow">Bloco '+esc(group.id)+'</span>'+
      '<h2 id="unova-'+esc(group.id)+'">'+esc(group.title)+'</h2>'+
      '<p>'+esc(group.description)+'</p>'+
      '<p><strong>'+group.completed+'/4 entregas concluídas</strong></p>'+
      '<progress max="4" value="'+group.completed+'" aria-label="Progresso '+esc(group.id)+'">'+group.completed+' de 4</progress>'+
      '</header><ol class="unova-progress-tasks">'+tasks+'</ol></section>';
  }).join('');
  return '<div class="container detail-container unova-github-progress">'+
    '<a class="back-link" href="/regioes">← Circuito de regiões</a>'+
    '<header class="article-heading"><span class="eyebrow">UNOVA · TRABALHO PELO GITHUB</span>'+
    '<h1>Progresso das tarefas de Unova</h1>'+
    '<p>Esta barra acompanha entregas de código, catálogos, testes e site que podemos executar sem o PC. Ela é independente do progresso jogável e dos testes locais.</p></header>'+
    '<section class="panel unova-progress-overview" aria-label="Progresso total">'+
    '<p class="eyebrow">DESENVOLVIMENTO PELO GITHUB</p>'+
    '<div class="unova-progress-total"><strong>'+stats.completed+'/'+stats.total+'</strong>'+
    '<span>'+stats.percent+'% concluído</span></div>'+
    '<progress value="'+stats.completed+'" max="'+stats.total+'" aria-label="Desenvolvimento GitHub: '+stats.completed+' de '+stats.total+' tarefas">'+stats.percent+'%</progress>'+
    '<p>'+stats.remaining+' tarefas restantes · '+stats.inProgress+' em andamento · atualização '+esc(data.updated)+'</p>'+
    '<p class="unova-progress-warning">Aprovado apenas como código e planejamento. Unova continua não jogável; nenhuma conclusão aqui comprova instalação, saves ou Game.exe.</p>'+
    '<div class="unova-progress-native"><span><strong>Barra A técnica: 0/8</strong> · precisa de provas reais</span>'+
    '<span><strong>Unova jogável: 0/32</strong> · nenhum mapa nativo aprovado</span></div></section>'+
    '<div class="unova-progress-grid">'+groupMarkup+'</div>'+
    '<p class="unova-progress-footer">Etapas G01–G08 são frentes de desenvolvimento GitHub. Não são as fases U01–U32 da campanha nem as auditorias A04–A14.</p>'+
    '</div>';
}
