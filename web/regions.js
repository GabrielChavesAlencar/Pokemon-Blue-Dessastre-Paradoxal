(() => {
  "use strict";
  const el=(tag,text)=>{
    const node=document.createElement(tag);
    if(text) node.textContent=text;
    return node;
  };
  window.BlueStudioRegions={
    async open(){
      const panel=document.getElementById("regionsWorkspace");
      const result=document.getElementById("regionsResults");
      panel.setAttribute("aria-busy","true");
      try {
        const response=await fetch("/api/regions");
        if(!response.ok) throw new Error();
        const {registry,preview}=await response.json();
        const list=el("ul");
        const labels={playable:"Jogável",prototype:"Piloto em preparação",planned:"Planejada"};
        for(const key of [...registry.circuit,"HISUI"]){
          const region=registry.regions[key];
          list.append(el("li",region.name+" — "+labels[region.status]+" · "+region.base));
        }
        result.replaceChildren(list);
        if(preview.length){
          result.append(el("h2","Mapas preparados para inspeção"));
          const maps=el("ul");
          for(const row of preview){
            maps.append(el("li",row.name+" — mapa "+row.source_id+" → "+row.proposed_id+
              " · "+row.review_count+" comandos para revisão"));
          }
          result.append(maps);
        } else {
          result.append(el("p","A prévia local de Kanto ainda não foi preparada nesta instalação."));
        }
      } catch {
        result.textContent="Não foi possível consultar o catálogo de regiões.";
      } finally {
        panel.removeAttribute("aria-busy");
      }
    }
  };
})();
