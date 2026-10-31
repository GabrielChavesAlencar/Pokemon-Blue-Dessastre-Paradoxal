/* Blue Studio — edit Pokémon Essentials PBS files directly, offline. */
const $ = id => document.getElementById(id);
const state = {files:[], file:'', sections:[], hash:'', index:null, raw:'', original:'', mode:'fields', newSection:false, documentMode:false, page:0, busy:false};
const CHUNK = 250;
const categories = [
  [/^pokemon(_|\.)/, 'POKÉMON E FORMAS'],
  [/^moves?(_|\.)/, 'GOLPES'],
  [/^abilities(_|\.)/, 'HABILIDADES'],
  [/^items?(_|\.)/, 'ITENS'],
  [/^trainers?|^trainer_types/, 'TREINADORES'],
  [/^encounters/, 'ENCONTROS'],
  [/^map_|^town_map/, 'MAPAS'],
];
const templates = {
  'pokemon': id => `[${id}]\nName = ${id}\nTypes = WATER\nBaseStats = 70,70,70,70,70,70\nGenderRatio = Female50Percent\nGrowthRate = Medium\nBaseExp = 150\nEVs = ATTACK,1\nCatchRate = 45\nHappiness = 70\nAbilities = SWIFTSWIM\nMoves = 1,TACKLE,5,WATERGUN,15,BITE\nTutorMoves = PROTECT,SURF\nEggGroups = Water1\nHatchSteps = 5120\nHeight = 1.0\nWeight = 25.0\nColor = Blue\nShape = Fish\nCategory = Paradox\nPokedex = Novo Pokémon. Edite esta descrição.\nGeneration = 9\n`,
  'pokemon_forms': id => `[${id}]\nFormName = Forma Alternativa\nTypes = WATER\nBaseStats = 70,70,70,70,70,70\nAbilities = SWIFTSWIM\n`,
  'moves': id => `[${id}]\nName = Novo Golpe\nType = WATER\nCategory = Special\nPower = 70\nAccuracy = 100\nTotalPP = 15\nTarget = NearOther\nFunctionCode = None\nFlags = CanProtect,CanMirrorMove\nDescription = Descrição do golpe.\n`,
  'abilities': id => `[${id}]\nName = Nova Habilidade\nDescription = Descrição da habilidade.\n`,
  'items': id => `[${id}]\nName = Novo Item\nNamePlural = Novos Itens\nPocket = 1\nPrice = 1000\nFieldUse = Direct\nDescription = Descrição do item.\n`,
  'trainers': id => `[${id}]\nLoseText = Boa batalha!\nPokemon = PIKACHU,10\n\tMoves = THUNDERSHOCK,QUICKATTACK\n`,
  'encounters': id => `[${id}] # Novo mapa\nLand,21\n    100,PIDGEY,3,5\n`
};
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function toast(message,error=false){const t=$('toast');t.textContent=message;t.className=error?'visible error':'visible';clearTimeout(t.timer);t.timer=setTimeout(()=>t.className='',5000);}
async function api(url,opt={}){
  const r=await fetch(url,{...opt,headers:{'X-Blue-Studio':'1',...(opt.body?{'Content-Type':'application/json'}:{}),...(opt.headers||{})}});
  let data;try{data=await r.json();}catch{throw new Error('Resposta inválida do servidor.');}
  if(!r.ok)throw new Error(data.error||`HTTP ${r.status}`);
  return data;
}
async function post(path,obj){return api(path,{method:'POST',body:JSON.stringify(obj)});}
async function refresh(){
  try{
    const [status,files]=await Promise.all([api('/api/status'),api('/api/files')]);
    $('status').innerHTML=`<span class="chip ${status.pbsReady?'':'off'}">${status.pbsReady?'● PBS conectado':'○ Jogo não importado'}</span><span>${esc(status.pbsFiles)} arquivos PBS</span><span class="chip ${status.gameReady?'':'off'}">${status.gameReady?'● Game.exe encontrado':'○ Sem executável'}</span><small>Pasta local: ${esc(status.gameDir)}</small>`;
    state.files=files.files;renderFiles();
    if(!status.pbsReady){$('records').innerHTML='<div class="empty">Execute BAIXAR_BASE_DECADES.bat ou copie os arquivos para a pasta game/.</div>';}
    return status;
  }catch(e){toast(e.message,true);return null;}
}
function categoryOf(file){const n=file.toLowerCase();const found=categories.find(([r])=>r.test(n));return found?found[1]:'OUTROS ARQUIVOS';}
function renderFiles(){
  const filter=$('fileSearch').value.trim().toLowerCase();const list=state.files.filter(f=>f.name.toLowerCase().includes(filter));
  let group='';$('fileList').innerHTML=list.map(f=>{
    const c=categoryOf(f.name),head=c!==group?`<div class="file-group">${esc(c)}</div>`:'';group=c;
    return head+`<button class="file-btn ${f.name===state.file?'active':''}" data-file="${esc(f.name)}"><span class="dot"></span><span>${esc(f.name)}</span></button>`;
  }).join('')||'<div class="empty">Nenhum arquivo.</div>';
  $('fileList').querySelectorAll('[data-file]').forEach(b=>b.addEventListener('click',()=>openFile(b.dataset.file)));
}
function maybeUnsaved(){return state.raw!==state.original && !confirm('Descartar alterações não salvas?');}
async function openFile(file,force=false){
  if(!force&&maybeUnsaved())return;
  state.file=file;state.index=null;state.newSection=false;state.documentMode=false;state.page=0;state.raw=state.original='';
  renderFiles();$('fileTitle').textContent=file;$('recordTitle').textContent='Selecione um registro';$('editorBody').innerHTML='<div class="empty">Carregando registros...</div>';setSaveEnabled();
  try{
    const res=await api('/api/sections?file='+encodeURIComponent(file));
    if(state.file!==file)return;
    state.sections=res.sections;state.hash=res.hash;
    $('entrySearch').value='';renderRecords();
    if(res.sections.length===0){await openWholeFile();}
    else{$('editorBody').innerHTML='<div class="hero-empty"><div class="illustration">✦</div><h3>'+esc(res.sections.length)+' registros disponíveis</h3><p>Pesquise e selecione um registro para editar, ou use + para adicionar um novo.</p></div>';}
  }catch(e){toast(e.message,true);}
}
function filteredRecords(){const q=$('entrySearch').value.toLowerCase().trim();return state.sections.filter(s=>!q||s.id.toLowerCase().includes(q)||s.label.toLowerCase().includes(q));}
function renderRecords(){
  const list=filteredRecords(),shown=list.slice(0,(state.page+1)*CHUNK);
  $('recordCount').textContent=`${list.length.toLocaleString('pt-BR')} registros • ${shown.length} exibidos`;
  $('records').innerHTML=shown.map(s=>`<button class="record ${s.index===state.index&&!state.newSection?'selected':''}" data-index="${s.index}"><span>${esc(s.id)}</span>${s.label?`<small>${esc(s.label)}</small>`:''}</button>`).join('')+(shown.length<list.length?'<button id="more" class="btn btn-ghost" style="width:100%">Mostrar mais</button>':'')||'<div class="empty">Nenhum resultado.</div>';
  $('records').querySelectorAll('[data-index]').forEach(b=>b.addEventListener('click',()=>openSection(Number(b.dataset.index))));
  $('more')?.addEventListener('click',()=>{state.page++;renderRecords();});
}
async function openWholeFile(){
  try{
    const res=await api('/api/file?file='+encodeURIComponent(state.file));
    state.hash=res.hash;state.index=null;state.documentMode=true;state.newSection=false;state.mode='raw';state.original=state.raw=res.raw;
    $('recordTitle').textContent=state.file+' (texto integral)';$('editingHint').textContent='ARQUIVO SEM SEÇÕES PBS';
    renderEditor();
  }catch(e){toast(e.message,true);}
}
async function openSection(index){
  if(maybeUnsaved())return;
  const file=state.file;
  try{
    const res=await api(`/api/section?file=${encodeURIComponent(file)}&index=${index}`);
    if(file!==state.file)return;
    state.index=index;state.hash=res.hash;state.raw=state.original=res.raw;state.newSection=false;state.documentMode=false;state.mode='fields';
    $('editingHint').textContent='REGISTRO PBS';$('recordTitle').textContent=res.id;renderRecords();renderEditor();
  }catch(e){toast(e.message,true);}
}
function templateFor(file,id){const name=file.replace(/\.txt$/i,'');let type=Object.keys(templates).sort((a,b)=>b.length-a.length).find(k=>name.startsWith(k));return templates[type]?templates[type](id):`[${id}]\nName = Novo Registro\n`;}
function newRecord(){
  if(!state.file){toast('Selecione um arquivo PBS.',true);return;}
  if(maybeUnsaved())return;
  const answer=prompt('Identificador do registro novo (ex.: CAVEFANG ou GARCHOMP,8):','NOVOPOKEMON');
  if(answer===null)return;
  const id=answer.trim();
  if(!id||id.length>110||/[\]\[\r\n]/.test(id)){toast('Identificador inválido.',true);return;}
  if(state.sections.some(s=>s.id.toLowerCase()===id.toLowerCase())){toast('O identificador já existe neste arquivo.',true);return;}
  state.newSection=true;state.documentMode=false;state.index=-1;state.mode='fields';state.original='';state.raw=templateFor(state.file,id);
  $('recordTitle').textContent='Novo: '+id;$('editingHint').textContent='CRIAR REGISTRO';renderRecords();renderEditor();
}
function setSaveEnabled(){
  const dirty=state.raw!==state.original;
  $('save').disabled=!state.file||(!state.documentMode&&state.index===null)||(!dirty&&!state.newSection);
  $('save').textContent=dirty||state.newSection?'● Salvar alterações':'Salvar alterações';
}
function parseFields(text){return text.split(/\r?\n/).map((s,i)=>{const m=s.match(/^(\s*)([A-Za-z][\w]*)\s*=\s*(.*)$/);return m?{line:i,indent:m[1],key:m[2],value:m[3]}:null;}).filter(Boolean);}
function updateLine(lineno,newval){const lines=state.raw.split('\n');const line=lines[lineno];if(line===undefined)return;const m=line.match(/^(\s*[A-Za-z][\w]*\s*=\s*)(.*)$/);if(!m)return;lines[lineno]=m[1]+newval;state.raw=lines.join('\n');setSaveEnabled();}
function renderEditor(){
  const spriteHeader=state.raw.match(/^\[([A-Za-z][\w]*)(?:,(\d+))?\]/);
  const spriteID=spriteHeader
    ? spriteHeader[1]+(spriteHeader[2]&&Number(spriteHeader[2])>0?'_'+Number(spriteHeader[2]):'')
    : null;
  const showSprite=state.file.startsWith('pokemon')&&!!spriteID;
  $('editorBody').innerHTML=`<div class="meta"><span class="tag">${esc(state.file)}</span><small>As mudanças são gravadas no PBS local. Para aplicá-las, recompile os dados no modo debug do Essentials.</small></div><div class="tabs"><button class="tab ${state.mode==='fields'?'active':''}" id="tabFields">Campos</button><button class="tab ${state.mode==='raw'?'active':''}" id="tabRaw">PBS avançado</button></div><div id="editArea"></div>`;
  $('tabFields').addEventListener('click',()=>{state.mode='fields';renderEditor();});
  $('tabRaw').addEventListener('click',()=>{state.mode='raw';renderEditor();});
  if(showSprite&&typeof window.mountBlueSpritePanel==='function') window.mountBlueSpritePanel(spriteID,$('editorBody'));
  if(showSprite&&typeof window.mountPokemonDataPanel==='function') window.mountPokemonDataPanel($('editorBody'),spriteID);

  renderEditArea();setSaveEnabled();
}
function renderEditArea(){
  const area=$('editArea');
  if(state.mode==='raw'){
    area.innerHTML=`<textarea id="rawEditor" class="code" spellcheck="false" aria-label="Código PBS"></textarea><p class="help">Edite o conteúdo original. Para registros individuais, mantenha apenas um cabeçalho [ID]. Atenção aos formatos definidos pelo Pokémon Essentials v21.1.</p>`;
    const ta=$('rawEditor');ta.value=state.raw;ta.addEventListener('input',()=>{state.raw=ta.value;setSaveEnabled();});return;
  }
  const entries=parseFields(state.raw);
  const inputs=entries.map((f,i)=>`<div class="field ${f.value.length>80?'wide':''}"><label for="f${i}">${esc(f.key)} ${entries.filter(x=>x.key===f.key).length>1?'('+String(i+1)+')':''}</label><input type="text" id="f${i}" data-line="${f.line}" value="${esc(f.value)}" autocomplete="off"></div>`).join('');
  area.innerHTML=`<div class="fieldgrid">${inputs||'<p class="empty-label">Não há campos chave = valor neste registro. Use PBS avançado para editar.</p>'}</div><div class="editor-toolbar"><button id="addField" class="btn btn-ghost">＋ Adicionar campo</button><button id="advanced" class="btn btn-ghost">{ } Editar código PBS</button></div><p class="help">Campos repetidos são preservados (ex.: Pokemon, Moves). Para ajustar encontros e treinadores complexos, prefira o modo PBS avançado.</p>`;
  area.querySelectorAll('input[data-line]').forEach(inp=>inp.addEventListener('input',()=>{updateLine(Number(inp.dataset.line),inp.value);}));
  $('addField').addEventListener('click',()=>{
    const key=prompt('Nome do campo (ex.: TutorMoves):','');if(key===null)return;
    if(!/^[A-Za-z][A-Za-z0-9_]*$/.test(key)){toast('Use somente letras, números e _.',true);return;}
    let txt=state.raw.replace(/\s*$/,'');txt+='\n'+key+' = \n';state.raw=txt;renderEditor();setSaveEnabled();
  });
  $('advanced').addEventListener('click',()=>{state.mode='raw';renderEditor();});
}
async function save(){
  if(!state.file||(!state.documentMode&&state.index===null))return;
  if(state.busy)return;state.busy=true;$('save').disabled=true;
  try{
    const obj={file:state.file,hash:state.hash,raw:state.raw,index:state.index};
    const res=state.documentMode?await post('/api/file',obj):await post('/api/save',obj);
    toast('Salvo! Um backup da versão anterior foi criado.');
    await openFileAfterSave(res.index);
  }catch(e){toast(e.message,true);setSaveEnabled();}finally{state.busy=false;}
}
async function openFileAfterSave(index){
  const file=state.file;state.original=state.raw;
  const res=await api('/api/sections?file='+encodeURIComponent(file));state.sections=res.sections;state.hash=res.hash;state.newSection=false;
  renderRecords();
  if(state.documentMode){await openWholeFile();return;}
  if(index!==null&&index!==undefined){await openSection(index);}else{state.index=null;renderEditor();}
}
async function launchGame(){try{const r=await post('/api/launch',{});toast(r.message);}catch(e){toast(e.message,true);}}
async function showHistory(){
  if(!state.file){toast('Selecione um arquivo primeiro.',true);return;}
  $('modal').classList.remove('hidden');$('modalTitle').textContent='Backups • '+state.file;$('modalBody').textContent='Carregando...';
  try{
    const res=await api('/api/backups?file='+encodeURIComponent(state.file));
    $('modalBody').innerHTML=res.backups.length?res.backups.map((b,i)=>`<div class="backup"><div><b>${esc(b.name)}</b><br><small>${(b.size/1024).toFixed(1)} KB</small></div><button class="btn btn-ghost" data-backup="${i}">Restaurar</button></div>`).join(''):'<p class="empty-label">Ainda não existem backups para este arquivo.</p>';
    $('modalBody').querySelectorAll('[data-backup]').forEach(b=>b.addEventListener('click',async()=>{
      if(!confirm('Restaurar este backup? O estado atual será salvo como um novo backup.'))return;
      try{await post('/api/restore',{file:state.file,backup:res.backups[Number(b.dataset.backup)].name,hash:state.hash});$('modal').classList.add('hidden');state.original=state.raw;await openFile(state.file,true);toast('Backup restaurado.');}catch(e){toast(e.message,true);}
    }));
  }catch(e){toast(e.message,true);}
}
$('fileSearch').addEventListener('input',renderFiles);
$('entrySearch').addEventListener('input',()=>{state.page=0;renderRecords();});
$('new').addEventListener('click',()=>{
  if(state.file==='pokemon.txt'&&typeof window.blueCreateSpecies==='function') window.blueCreateSpecies();
  else newRecord();
});
$('save').addEventListener('click',save);
$('play').addEventListener('click',launchGame);
$('compilePokemon').addEventListener('click',()=>window.blueCompilePokemon?.());
$('history').addEventListener('click',showHistory);
$('closeModal').addEventListener('click',()=>$('modal').classList.add('hidden'));
$('modal').addEventListener('click',e=>{if(e.target===$('modal'))$('modal').classList.add('hidden');});
$('reload').addEventListener('click',async()=>{if(state.file){await openFile(state.file)}else{await refresh()} });
window.addEventListener('beforeunload',e=>{if(state.raw!==state.original){e.preventDefault();e.returnValue='';}});
refresh();
