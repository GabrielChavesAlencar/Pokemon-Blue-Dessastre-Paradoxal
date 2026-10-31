/* Blue Studio: editor de sprites de Pokemon Essentials.
   PNG estatico, PNG faixa com 3+ quadros, ou GIF. Nao exige GIF para Fakemon. */
(function () {
  "use strict";
  const TYPES=[
    ["front","Frente normal"],["back","Costas normal"],
    ["front-shiny","Frente shiny"],["back-shiny","Costas shiny"]
  ];
  function make(tag,css,text){
    const node=document.createElement(tag);
    if(css)node.className=css;
    if(text!==undefined)node.textContent=text;
    return node;
  }
  function path(kind,species,hash){
    return "/api/sprite?kind="+encodeURIComponent(kind)+
      "&species="+encodeURIComponent(species)+"&v="+encodeURIComponent(hash||"");
  }
  function addPanel(species,container){
    const panel=make("section","sprite-panel");
    panel.dataset.species=species;
    panel.setAttribute("aria-label","Editor visual de sprites");
    const title=make("div","sprite-title");
    const heading=make("div");
    heading.append(make("strong","", "🎨 Sprites · "+species));
    heading.append(make("small","", "Imagens estáticas ou animadas; normal e shiny"));
    title.append(heading);
    title.append(make("span","sprite-subtitle","PNG estático · PNG spritesheet · GIF"));
    panel.append(title);
    const grid=make("div","sprite-grid");
    panel.append(grid);
    panel.append(make("p","help",
      "Imagens são gravadas na pasta local Graphics/Pokemon com backup. "+
      "PNG de um único quadro funciona sem GIF. Faixas PNG animadas precisam de 3 ou mais "+
      "quadros horizontais quadrados no motor do Decades."));
    container.prepend(panel);
    for(const [kind,label] of TYPES){
      const tile=make("div","sprite-tile");
      tile.dataset.kind=kind;
      tile.append(make("b","",label));
      const preview=make("div","sprite-preview");
      const image=make("img","");
      image.alt="Sprite "+label;
      image.hidden=true;
      const empty=make("span","sprite-empty","Nenhuma imagem");
      preview.append(image,empty);
      tile.append(preview);
      const info=make("small","sprite-info","Verificando...");
      info.setAttribute("aria-live","polite");
      tile.append(info);
      const wrapper=make("label","sprite-mode-label","Formato de importação");
      const mode=make("select","sprite-mode");
      mode.setAttribute("aria-label","Formato de sprite "+label);
      for(const [value,caption] of [
        ["static","Imagem estática (PNG)"],
        ["animated","Animado (GIF / faixa PNG)"]
      ]){
        const opt=document.createElement("option");
        opt.value=value;opt.textContent=caption;mode.append(opt);
      }
      wrapper.append(mode);
      tile.append(wrapper);
      const button=make("button","btn btn-ghost sprite-import","📁 Importar imagem");
      button.type="button";
      tile.append(button);
      const file=document.createElement("input");
      file.type="file";file.accept=".png,.gif,image/png,image/gif";
      file.className="sprite-file";file.hidden=true;
      tile.append(file);
      grid.append(tile);
      let metadata={file:null,exists:false};

      async function refresh(){
        try{
          const next=await api("/api/sprite-info?species="+encodeURIComponent(species)+"&kind="+encodeURIComponent(kind));
          if(!panel.isConnected)return;
          metadata=next;
          if(!next.exists){
            image.hidden=true;image.removeAttribute("src");
            empty.textContent="Nenhuma imagem";empty.hidden=false;
            info.textContent="Vazio · PNG ou GIF";return;
          }
          const f=next.file;
          mode.value=f.mode==="PNG estático"?"static":"animated";
          info.textContent=f.mode+" · "+f.width+"×"+f.height+" · "+Math.round(f.size/1024)+" KB"+
            (next.conflict?" · arquivos duplicados":"");
          empty.hidden=true;image.hidden=false;
          image.dataset.previewReady="";
          image.onload=function(){
            if(image.dataset.previewReady||!panel.isConnected)return;
            if(f.format==="png" && f.width>f.height*2){
              const canvas=document.createElement("canvas");
              canvas.width=f.height;canvas.height=f.height;
              const context=canvas.getContext("2d");
              if(context){
                context.imageSmoothingEnabled=false;
                context.drawImage(image,0,0,f.height,f.height,0,0,f.height,f.height);
                image.dataset.previewReady="true";
                image.src=canvas.toDataURL("image/png");
              }
            }
          };
          image.onerror=()=>{
            image.hidden=true;empty.hidden=false;
            empty.textContent="Arquivo inválido ou indisponível";
          };
          image.src=path(kind,species,f.hash.slice(0,16));
        }catch(err){
          if(panel.isConnected){image.hidden=true;info.textContent="Falha: "+err.message;}
        }
      }
      button.addEventListener("click",()=>file.click());
      file.addEventListener("change",async function(){
        const chosen=file.files?.[0];
        if(!chosen)return;
        file.value="";
        const ext=chosen.name.split(".").pop().toLowerCase();
        if(!["png","gif"].includes(ext)){
          toast("Selecione um arquivo PNG ou GIF.",true);return;
        }
        if(chosen.size>5000000){
          toast("Imagem maior que 5 MB.",true);return;
        }
        if(ext==="gif")mode.value="animated";
        button.disabled=true;info.textContent="Salvando arquivo e criando backup...";
        try{
          const data=await new Promise((resolve,reject)=>{
            const reader=new FileReader();
            reader.onerror=()=>reject(new Error("Falha ao ler a imagem."));
            reader.onload=()=>resolve(String(reader.result).split(",")[1]||"");
            reader.readAsDataURL(chosen);
          });
          await post("/api/sprite-upload",{
            species,kind,filename:chosen.name,data,
            mode:mode.value,expectedHash:metadata.file?.hash||""
          });
          toast("Imagem "+label+" salva em Graphics/Pokemon com backup!");
          await refresh();
        }catch(err){
          toast(err.message,true);
          await refresh();
        }finally{button.disabled=false;}
      });
      refresh();
    }
  }
  window.mountBlueSpritePanel=addPanel;
}());
