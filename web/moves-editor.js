/* Dedicated Pokémon moveset editor for Pokémon Essentials PBS.
   Each save updates only Moves/TutorMoves/EggMoves of the selected species. */
(function () {
  "use strict";
  const KEY_NAMES={level:"Golpes aprendidos por nível",tutor:"Golpes de tutor / TM",egg:"Golpes de ovo"};
  const KINDS=["level","tutor","egg"];
  let root, catalog=null, selected=null, entry=null, working=null, inherited=new Set(), baseline="";
  let moveNames=new Map(), busy=false, search="", token=0;
  const node=(tag,klass,text)=>{
    const el=document.createElement(tag);
    if(klass)el.className=klass;
    if(text!==undefined)el.textContent=text;
    return el;
  };
  function clone(v){return JSON.parse(JSON.stringify(v));}
  function snapshot(){
    return JSON.stringify({level:working?.level||[],tutor:working?.tutor||[],
      egg:working?.egg||[],inherit:[...inherited].sort()});
  }
  function dirty(){return Boolean(entry&&working&&snapshot()!==baseline);}
  function announce(message,isError=false){
    const area=document.getElementById("movesMessage");
    if(!area)return;
    area.textContent=message;
    area.classList.toggle("error",isError);
  }
  function toggleSave(){
    const button=document.getElementById("movesSave");
    if(button){button.disabled=!dirty()||busy;button.textContent=busy?"Salvando...":dirty()?"● Salvar moveset":"Salvar moveset";}
    const mark=document.getElementById("movesDirty");
    if(mark)mark.textContent=dirty()?"● Alterações não salvas":"Todas as alterações salvas";
  }
  function canLeave(){
    return !dirty()||confirm("Existem alterações de golpes não salvas. Deseja descartá-las?");
  }
  function paint(){
    if(!root)return;
    root.innerHTML="";
    const header=node("header","moves-header");
    const title=node("div","");
    title.append(node("span","kicker","POKÉMON ESSENTIALS · EDITOR DE MOVESETS"));
    title.append(node("h1","","⚔️ Golpes dos Pokémon"));
    title.append(node("p","moves-description","Edite golpes por nível, tutor/TM e ovo sem modificar atributos, sprites ou os Pokémon de outras espécies."));
    header.append(title);
    const tools=node("div","moves-header-actions");
    const reload=node("button","btn btn-ghost","↻ Atualizar catálogo");
    reload.type="button";reload.onclick=()=>loadCatalog(true);
    tools.append(reload);
    header.append(tools);
    root.append(header);
    const layout=node("div","moves-layout");
    const left=node("aside","moves-sidebar");
    left.append(node("h2","","Espécies e formas"));
    const searchBox=node("input","moves-search");
    searchBox.type="search";searchBox.id="movesSearch";searchBox.placeholder="Pesquisar Pokémon ou ID...";
    searchBox.setAttribute("aria-label","Pesquisar Pokémon para editar golpes");
    searchBox.value=search;
    searchBox.addEventListener("input",()=>{search=searchBox.value;renderSpecies();});
    left.append(searchBox);
    left.append(node("div","moves-count",""));
    const records=node("div","moves-records");
    records.id="movesRecords";left.append(records);
    layout.append(left);
    const right=node("section","moves-editor-card");
    right.id="movesEditorCard";
    const msg=node("p","moves-message","Selecione uma espécie.");
    msg.id="movesMessage";msg.setAttribute("role","status");right.append(msg);
    layout.append(right);
    root.append(layout);
    renderSpecies();
    renderEntry();
  }
  function renderSpecies(){
    const box=document.getElementById("movesRecords");
    const count=document.querySelector(".moves-count");
    if(!box||!count)return;
    box.replaceChildren();
    if(!catalog){count.textContent="Carregando...";return;}
    const q=search.trim().toLocaleLowerCase("pt-BR");
    const filtered=catalog.species.filter(s=>!q ||
      (s.id+" "+s.name+" "+s.file).toLocaleLowerCase("pt-BR").includes(q));
    count.textContent=filtered.length+" resultados · "+Math.min(filtered.length,200)+" exibidos";
    const frag=document.createDocumentFragment();
    for(const item of filtered.slice(0,200)){
      const button=node("button","moves-species-item"+(selected&&selected.file===item.file&&selected.index===item.index?" selected":""));
      button.type="button";button.dataset.movesIndex=String(item.index);
      button.dataset.movesFile=item.file;
      button.setAttribute("aria-label","Selecionar "+item.name+" ("+item.id+")");
      button.append(node("strong","",item.name));
      button.append(node("small","",item.id+(item.form?" · forma":"")+" · "+item.file));
      button.onclick=()=>select(item);
      frag.append(button);
    }
    box.append(frag);
    if(!filtered.length)box.append(node("p","moves-hint","Nenhuma espécie encontrada."));
  }
  async function loadCatalog(force=false){
    if(!root)return;
    if(dirty()&&!canLeave())return;
    const previous=selected&&{file:selected.file,index:selected.index};
    const paintToken=++token;
    if(force){catalog=null;selected=null;entry=null;working=null;inherited=new Set();baseline="";paint();}
    announce("Carregando espécies e golpes do Decades...");
    try{
      const result=await api("/api/pokemon-moves/catalog");
      if(paintToken!==token)return;
      catalog=result;
      moveNames=new Map(result.moves.map(m=>[m.id,m.name]));
      renderSpecies();
      announce(result.species.length+" espécies e formas · "+result.moves.length+" golpes disponíveis.");
      if(previous){
        const choice=result.species.find(s=>s.file===previous.file&&s.index===previous.index);
        if(choice)await select(choice,true);
      }
    }catch(e){announce("Erro ao carregar PBS: "+e.message,true);}
  }
  async function select(item,skipConfirm=false){
    if(!skipConfirm&&dirty()&&!canLeave())return;
    const request=++token;
    busy=true;announce("Carregando golpes de "+item.name+"...");
    try{
      const result=await api("/api/pokemon-moves/entry?file="+encodeURIComponent(item.file)+
        "&index="+encodeURIComponent(item.index));
      if(request!==token)return;
      selected=item;
      entry=result;
      inherited=new Set(result.inherited);
      working=clone(result.own);
      baseline=snapshot();
      renderSpecies();
      renderEntry();
      announce("Exibindo "+result.id+" · "+result.file+". Use Salvar moveset para gravar no PBS.");
    }catch(e){announce(e.message,true);}
    finally{busy=false;toggleSave();}
  }
  function setupAutocomplete(input){
    input.setAttribute("list","movesAvailable");
    input.placeholder="ID do golpe (ex.: TACKLE)";
    input.autocomplete="off";
    input.addEventListener("blur",()=>{
      input.value=input.value.trim().toUpperCase();
      input.dispatchEvent(new Event("input",{bubbles:true}));
    });
  }
  function renderEntry(){
    const card=document.getElementById("movesEditorCard");
    if(!card)return;
    card.replaceChildren();
    if(!entry){
      card.append(node("div","moves-empty","Selecione um Pokémon ou forma alternativa para visualizar seus golpes."));
      return;
    }
    const head=node("div","moves-editor-head");
    const identity=node("div","");
    identity.append(node("small","kicker",entry.form?"FORMA ALTERNATIVA":"ESPÉCIE BASE"));
    identity.append(node("h2","",entry.name));
    identity.append(node("p","moves-description",entry.id+" · "+entry.file));
    head.append(identity);
    const action=node("div","moves-save-actions");
    const dirtyMark=node("small","moves-dirty","");dirtyMark.id="movesDirty";action.append(dirtyMark);
    const reset=node("button","btn btn-ghost","↶ Descartar mudanças");
    reset.type="button";reset.onclick=()=>{
      if(!dirty()||confirm("Descartar alterações feitas neste moveset?")){
        working=clone(entry.own);inherited=new Set(entry.inherited);
        renderEntry();announce("Dados restaurados a partir do último carregamento.");
      }
    };
    const save=node("button","btn btn-primary","Salvar moveset");
    save.type="button";save.id="movesSave";save.onclick=saveMoves;
    action.append(reset,save);head.append(action);
    card.append(head);
    const message=node("p","moves-message","");
    message.id="movesMessage";message.setAttribute("role","status");card.append(message);
    const dl=node("datalist","");dl.id="movesAvailable";
    for(const [id,name] of moveNames){
      const option=document.createElement("option");
      option.value=id;option.label=name+" ("+id+")";dl.append(option);
    }
    card.append(dl);
    for(const kind of KINDS){
      const section=node("section","moves-kind");
      const heading=node("div","moves-kind-heading");
      heading.append(node("h3","",KEY_NAMES[kind]));
      const info=node("small","",kind==="level"?"Nível 1–100 · ordem preservada":
        kind==="tutor"?"Aprendizado por tutor, TM/TR conforme o jogo":"Golpes herdáveis por reprodução");
      heading.append(info);section.append(heading);
      const inheritedCheck=entry.form&&entry.baseAvailable?node("label","moves-inherit-label"):null;
      if(inheritedCheck){
        const cb=document.createElement("input");cb.type="checkbox";cb.checked=inherited.has(kind);
        cb.setAttribute("aria-label","Herdar "+KEY_NAMES[kind]+" da espécie base");
        cb.addEventListener("change",()=>{
          if(cb.checked){inherited.add(kind);working[kind]=[];}
          else {
            inherited.delete(kind);
            if(!working[kind].length)working[kind]=clone((entry.base&&entry.base[kind])||[]);
          }
          renderEntry();
        });
        inheritedCheck.append(cb,node("span","","Herdar da espécie base (não gravar campo na forma)"));
        section.append(inheritedCheck);
      }
      const isInherited=inherited.has(kind);
      const values=isInherited?((entry.base&&entry.base[kind])||[]):working[kind];
      if(isInherited)section.append(node("p","moves-inherited","Visualizando golpes herdados. Desmarque a opção de herança para personalizar esta forma."));
      const rows=node("div","moves-kind-rows");rows.dataset.kind=kind;
      values.forEach((record,index)=>{
        const row=node("div","moves-row"+(isInherited?" locked":""));
        if(kind==="level"){
          const level=node("input","moves-level");
          level.type="number";level.min="1";level.max="100";level.step="1";
          level.value=String(record.level);
          level.setAttribute("aria-label","Nível do golpe "+(index+1));
          level.disabled=isInherited;
          level.addEventListener("input",()=>{working.level[index].level=Number(level.value);toggleSave();});
          row.append(node("span","moves-level-label","Nv."),level);
        }
        const move=node("input","moves-move-input");
        move.type="text";move.value=kind==="level"?record.move:record;
        move.disabled=isInherited;setupAutocomplete(move);
        move.setAttribute("aria-label","Golpe "+(index+1)+" de "+kind);
        move.addEventListener("input",()=>{
          if(kind==="level")working.level[index].move=move.value.trim().toUpperCase();
          else working[kind][index]=move.value.trim().toUpperCase();
          toggleSave();
          const name=moveNames.get(move.value.trim().toUpperCase());
          const label=row.querySelector(".moves-name");
          if(label)label.textContent=name||"Golpe não localizado no catálogo";
        });
        row.append(move);
        row.append(node("small","moves-name",moveNames.get(move.value.trim().toUpperCase())||""));
        const remove=node("button","btn btn-ghost moves-remove","Remover");
        remove.type="button";remove.disabled=isInherited;
        remove.setAttribute("aria-label","Remover golpe "+(index+1)+" de "+kind);
        remove.onclick=()=>{working[kind].splice(index,1);renderEntry();};
        row.append(remove);rows.append(row);
      });
      if(!values.length)rows.append(node("p","moves-hint","Nenhum golpe cadastrado nesta categoria."));
      section.append(rows);
      const add=node("button","btn btn-ghost","＋ Adicionar golpe");
      add.type="button";add.disabled=isInherited;add.dataset.addMove=kind;
      add.onclick=()=>{
        const first=moveNames.keys().next().value||"";
        working[kind].push(kind==="level"?{level:1,move:first}:first);
        renderEntry();
      };
      section.append(add);
      if(kind==="level"&&!isInherited){
        const sort=node("button","btn btn-ghost moves-sort","Ordenar por nível");
        sort.type="button";sort.onclick=()=>{
          working.level.sort((a,b)=>a.level-b.level);renderEntry();
        };
        section.append(sort);
      }
      card.append(section);
    }
    card.append(node("p","moves-note","As alterações afetam somente esta espécie/formulário PBS. O histórico é salvo em .blue-backups. Depois de salvar, recompile os PBS no modo Debug do Pokémon Essentials para aplicar os golpes no jogo."));
    toggleSave();
  }
  async function saveMoves(){
    if(!entry||!dirty()||busy)return;
    busy=true;toggleSave();
    announce("Validando IDs dos golpes e salvando no PBS...");
    try{
      const payload={file:entry.file,index:entry.index,id:entry.id,hash:entry.hash,
        level:working.level,tutor:working.tutor,egg:working.egg,inherit:[...inherited]};
      const result=await post("/api/pokemon-moves/save",payload);
      if(!result.ok)throw Error("O servidor não confirmou a gravação.");
      // Refresh full selected record, preserving its exact file and form.
      const next=await api("/api/pokemon-moves/entry?file="+encodeURIComponent(entry.file)+
         "&index="+entry.index);
      entry=next;inherited=new Set(next.inherited);
      working=clone(next.own);baseline=snapshot();
      renderEntry();
      announce("Moveset salvo com sucesso! Backup criado. Recompile os PBS para aplicar no jogo.");
    }catch(e){announce(e.message,true);}
    finally{busy=false;toggleSave();}
  }
  function open(){
    root=document.getElementById("movesWorkspace");
    if(!root)return;
    if(!root.querySelector(".moves-layout"))paint();
    if(!catalog)loadCatalog();
  }
  window.BluePokemonMoves={open,canLeave,get hasUnsaved(){return dirty();}};
}());