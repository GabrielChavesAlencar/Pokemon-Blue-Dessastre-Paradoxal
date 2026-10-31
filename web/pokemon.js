/* Blue Studio Pokémon editor: new independent species, guided fields and battle metrics.
   Uses native Essentials PBS. All UI actions are backed by API writes. */
(function () {
  "use strict";
  const labels=[
    ["Name","Nome","text"],["Types","Tipos (separados por vírgula)","text"],
    ["Abilities","Habilidades","text"],["HiddenAbilities","Habilidades ocultas","text"],
    ["Moves","Golpes por nível (nível,golpe,...)","textarea"],
    ["TutorMoves","Golpes tutor","textarea"],["EggMoves","Golpes de ovo","textarea"],
    ["Evolutions","Evoluções (espécie,método,parâmetro)","text"],
    ["Pokedex","Descrição na Pokédex","textarea"],["Generation","Geração","generation"]
  ];
  const statNames=["HP","Ataque","Defesa","Velocidade","Ataque Esp.","Defesa Esp."];
  const node=(tag,name,text)=>{
    const el=document.createElement(tag);
    if(name)el.className=name;
    if(text!==undefined)el.textContent=text;
    return el;
  };
  const field=(label,value,type="text")=>{
    const wrap=node("label","pokemon-input");
    wrap.append(node("span","",label));
    const input=node(type==="textarea"?"textarea":"input","");
    if(type!=="textarea")input.type=type;
    input.value=value;
    wrap.append(input);
    return [wrap,input];
  };
  const allFields=()=>{
    const data={};
    for(const match of state.raw.matchAll(/^[ \t]*([A-Za-z]\w*)[ \t]*=[ \t]*(.*)$/gm))
      data[match[1]]=match[2].trim();
    return data;
  };
  function editRaw(key,value){
    value=String(value).replace(/[\r\n]+/g," ").trim();
    const rx=new RegExp("^([ \\t]*"+key+"[ \\t]*=[ \\t]*).*$","m");
    if(rx.test(state.raw)){
      state.raw=state.raw.replace(rx,(_line,prefix)=>prefix+value);
    }else{
      state.raw=state.raw.replace(/\s*$/,"")+"\n"+key+" = "+value+"\n";
    }
    setSaveEnabled();
  }
  function showError(message,bad){
    toast(message,bad);
  }
  async function validate(){
    try{
      const res=await post("/api/pokemon/validate",{raw:state.raw});
      showError(res.name+": dados verificados, "+res.totalStats+" pontos base, "+res.levelMoves+" golpes por nível.");
    }catch(error){showError(error.message,true);}
  }
  function attachForm(container){
    const values=allFields();
    const card=node("section","pokemon-info-card");
    card.setAttribute("aria-label","Ficha completa do Pokémon");
    const head=node("div","pokemon-card-head");
    head.append(node("h3","","📋 Ficha Pokémon"));
    const actions=node("div","pokemon-card-actions");
    const check=node("button","btn btn-ghost","✓ Validar dados");
    check.type="button";
    check.onclick=validate;
    actions.append(check);head.append(actions);card.append(head);
    const grid=node("div","pokemon-form-grid");
    for(const [key,label,kind] of labels){
      if(kind==="generation"){
        const wrapper=node("label","pokemon-input");wrapper.append(node("span","",label));
        const input=node("select","");
        for(const [id,name] of [["dessastre-paradoxal","Dessastre Paradoxal"],...Array.from({length:9},(_,i)=>[String(i+1),"Geração "+(i+1)])]){const option=node("option","",name);option.value=id;input.append(option);}
        input.value=(values.Flags||"").split(",").map(x=>x.trim()).includes("DessastreParadoxal")?"dessastre-paradoxal":values.Generation||"9";
        input.addEventListener("change",()=>{const special=input.value==="dessastre-paradoxal";editRaw("Generation",special?"0":input.value);const flags=(allFields().Flags||"").split(",").map(x=>x.trim()).filter(x=>x&&x!=="DessastreParadoxal");if(special)flags.push("DessastreParadoxal");editRaw("Flags",flags.join(","));});
        wrapper.append(input);grid.append(wrapper);continue;
      }
      const [wrapper,input]=field(label,values[key]||"",kind);
      input.dataset.pbs=key;
      input.addEventListener("change",()=>editRaw(key,input.value));
      grid.append(wrapper);
    }
    const stats=node("fieldset","pokemon-stat-editor");
    stats.append(node("legend","","Atributos base · Sem limite de espécies"));
    const statGrid=node("div","pokemon-stats-grid");
    const s=(values.BaseStats||"70,70,70,70,70,70").split(",");
    for(let i=0;i<6;i++){
      const [wrapper,input]=field(statNames[i],s[i]||"70","number");
      input.min=1;input.max=255;input.step=1;
      input.addEventListener("change",()=>{
        const old=(allFields().BaseStats||"70,70,70,70,70,70").split(",");
        old[i]=input.value;
        editRaw("BaseStats",old.join(","));
        total.textContent="Total: "+old.reduce((x,y)=>x+(Number(y)||0),0);
      });
      statGrid.append(wrapper);
    }
    stats.append(statGrid);
    const total=node("strong","pokemon-stat-total","Total: "+s.reduce((a,b)=>a+(Number(b)||0),0));
    stats.append(total);
    card.append(stats,grid);
    const tip=node("p","help","Use Salvar alterações para persistir os dados PBS. A validação detecta tipos, habilidades, golpes e evoluções inexistentes; novas espécies não substituem Pokémon oficiais.");
    card.append(tip);
    const build= node("p","pokemon-build-status","Verificando se há PBS aguardando compilação...");
    build.setAttribute("role","status");
    card.append(build);
    api("/api/pokemon/compile-status").then(status=>{
      if(!card.isConnected)return;
      build.textContent=(status.needsCompile?"⚠ "+status.status:"✓ "+status.status)+
        ". Para confirmar, abra o modo Debug e compile os dados dentro do jogo.";
    }).catch(error=>{if(card.isConnected)build.textContent="Verificação de compilação: "+error.message;});
    container.append(card);
  }
  function newForm(){
    if(state.raw!==state.original &&
       !confirm("Há edições PBS não salvas. Deseja abrir o cadastro de nova espécie?"))return;
    const modal=node("div","pokemon-dialog-overlay");
    modal.setAttribute("role","dialog");modal.setAttribute("aria-modal","true");
    modal.setAttribute("aria-label","Adicionar nova espécie");
    const box=node("div","pokemon-dialog");
    const title=node("div","pokemon-dialog-header");
    title.append(node("h2","","✨ Adicionar Pokémon novo"));
    const close=node("button","btn btn-ghost","Fechar");
    close.onclick=()=>modal.remove();title.append(close);box.append(title);
    box.append(node("p","help","Crie uma espécie nova no Pokémon Essentials com seu próprio ID. Nenhuma espécie existente será substituída. O editor adiciona os dados em pokemon.txt e pokemon_metrics.txt."));
    const grid=node("div","pokemon-dialog-grid");
    const defs=[
      ["id","ID único (ex.: CAVEFANG)","CAVEFANG"],
      ["name","Nome exibido","Cave Fang"],
      ["type1","Tipo principal","WATER"],
      ["type2","Tipo secundário (opcional)",""],
      ["abilities","Habilidades (IDs)","SWIFTSWIM"],
      ["hiddenAbilities","Habilidades ocultas",""],
      ["moves","Golpes por nível","1,TACKLE"],
      ["evolutions","Evoluções (opcional)",""],
      ["category","Categoria","Paradox"],
      ["description","Descrição","????"],["generation","Geração (nome especial ou número oficial)","Dessastre Paradoxal"]
    ];
    const fields={};
    for(const [key,label,initial] of defs){
      const [wrap,input]=field(label,initial);
      fields[key]=input;grid.append(wrap);
    }
    const six=node("fieldset","pokemon-stat-editor");
    six.append(node("legend","","Atributos de base"));
    const statgrid=node("div","pokemon-stats-grid");
    const stats=[];
    for(let i=0;i<6;i++){
      const [wrap,input]=field(statNames[i],"70","number");
      input.min=1;input.max=255;stats.push(input);statgrid.append(wrap);
    }
    six.append(statgrid);
    box.append(grid,six);
    const message=node("p","pokemon-dialog-message","");
    message.setAttribute("role","status");
    box.append(message);
    const create=node("button","btn btn-primary","＋ Criar nova espécie sem substituir");
    create.type="button";
    create.onclick=async()=>{
      const body={stats:stats.map(i=>Number(i.value))};
      for(const [key,input] of Object.entries(fields))body[key]=input.value;
      create.disabled=true;message.textContent="Validando referências e criando espécie...";
      try{
        const result=await post("/api/pokemon/new",body);
        modal.remove();
        showError("Espécie "+result.name+" ("+result.id+") criada sem substituir outras!");
        await openFile("pokemon.txt",true);
        // Search new species using existing PBS list; selection remains stable.
        $("entrySearch").value=result.id;state.page=0;renderRecords();
        const item=state.sections.find(x=>x.id===result.id);
        if(item)await openSection(item.index);
      }catch(e){message.textContent="Erro: "+e.message;message.classList.add("bad");}
      finally{create.disabled=false;}
    };
    box.append(create);modal.append(box);
    modal.addEventListener("click",event=>{if(event.target===modal)modal.remove();});
    document.body.append(modal);
    fields.id.focus();
  }
  async function attachMetrics(species,container){
    const card=node("section","pokemon-metrics-card");
    card.setAttribute("aria-label","Posição e escala de sprites em batalha");
    card.append(node("h3","","🎯 Posição, escala e animação (PBS Metrics)"));
    const note=node("p","help","Ajustes reais de FrontSprite, BackSprite e AnimationSpeed; efeitos no jogo somente após compilação dos PBS.");
    card.append(note);
    const body=node("div","pokemon-metrics-body");
    const msg=node("small","pokemon-metrics-message","Carregando métricas...");
    card.append(body,msg);
    container.append(card);
    try{
      const info=await api("/api/pokemon/metrics?species="+encodeURIComponent(species));
      if(!card.isConnected)return;
      body.replaceChildren();
      const values={
        front:[info.front[0]||0,info.front[1]||0,info.front[2]||2],
        back:[info.back[0]||0,info.back[1]||0,info.back[2]||3],
        speed:[info.speed[0]||0,info.speed[1]||0]
      };
      const battle=node("div","pokemon-battle-preview");
      const foe=node("div","pokemon-battle-mon foe");
      const ally=node("div","pokemon-battle-mon ally");
      const foeImg=node("img","");
      const allyImg=node("img","");
      foeImg.alt="Frente na batalha";allyImg.alt="Costas na batalha";
      foeImg.src="/api/sprite?kind=front&species="+encodeURIComponent(species);
      allyImg.src="/api/sprite?kind=back&species="+encodeURIComponent(species);
      foe.append(foeImg);ally.append(allyImg);
      battle.append(foe,ally);body.append(battle);
      function updatePreview(){
        foeImg.style.transform="translate("+values.front[0]*1.5+"px,"+values.front[1]*1.5+"px) scale("+values.front[2]/2+")";
        allyImg.style.transform="translate("+values.back[0]*1.5+"px,"+values.back[1]*1.5+"px) scale("+values.back[2]/3+")";
      }
      updatePreview();
      const grid=node("div","pokemon-metrics-grid");
      for(const [section,title,keys] of [
        ["front","Frente (inimigo)",["X","Y","Escala"]],
        ["back","Costas (jogador)",["X","Y","Escala"]],
        ["speed","Velocidade",["Costas","Frente"]]
      ]){
        const panel=node("div","pokemon-metric-group");
        panel.append(node("b","",title));
        for(let i=0;i<keys.length;i++){
          const [label,input]=field(keys[i],String(values[section][i]),"number");
          input.min=section==="speed"?0:i===2?1:-250;
          input.max=section==="speed"?4:i===2?8:250;
          input.step=1;
          input.addEventListener("input",()=>{
            values[section][i]=Number(input.value);updatePreview();
          });
          panel.append(label);
        }
        grid.append(panel);
      }
      body.append(grid);
      const save=node("button","btn btn-primary","Salvar posição/escala no jogo");
      save.type="button";
      save.onclick=async()=>{
        save.disabled=true;msg.textContent="Salvando métricas com backup...";
        try{
          const updated=await post("/api/pokemon/metrics",{
            species,expectedHash:info.hash,...values
          });
          info.hash=updated.hash;
          msg.textContent="Métricas salvas em "+updated.file+". Compile os PBS para aplicar.";
          toast("Métricas salvas com backup!");
        }catch(e){msg.textContent="Erro: "+e.message;}
        finally{save.disabled=false;}
      };
      body.append(save);
    }catch(e){msg.textContent="Métricas indisponíveis: "+e.message;}
  }
  function attach(container,species){
    attachForm(container);
    attachMetrics(species,container);
  }
  async function launchCompile(){
    try{
      const check=await api("/api/pokemon/compile-status");
      const data=await post("/api/pokemon/compile",{});
      toast((check.needsCompile?"Dados modificados; ":"")+
            data.message+" O Blue Studio não pode garantir a compilação até o runtime confirmar.");
    }catch(e){toast(e.message,true);}
  }
  window.mountPokemonDataPanel=attach;
  window.blueCreateSpecies=newForm;
  window.blueCompilePokemon=launchCompile;
}());
