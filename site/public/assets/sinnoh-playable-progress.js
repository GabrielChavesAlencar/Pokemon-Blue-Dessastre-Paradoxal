"use strict";
// A UI only: it does not submit to ChatGPT, execute builds or accept files.
const $=id=>document.getElementById(id);
const el=(tag,value)=>{const n=document.createElement(tag);n.textContent=String(value);return n;};
const names="J01,J02,J03,J04,J05,J06,J07,J08";
const issuePrefix="https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/issues/";
function validate(d){
 if(d?.schema!==1||d.region!=="SINNOH"||d.track!=="JOGAVEL_TWINLEAF_SANDGEM"
 ||d.status!=="PILOT_NOT_INSTALLED_NOT_PLAYABLE"||d.stages_total!==8
 ||!Number.isInteger(d.stages_code_ready)||d.stages_code_ready<0||d.stages_code_ready>8
 ||d.stages_native_validated!==0||d.native_verified_percent!==0
 ||d.engineering_percent!==d.stages_code_ready*12.5
 ||!Array.isArray(d.stages)||d.stages.length!==8||d.stages.map(s=>s.id).join(",")!==names
 ||d.stages.filter(s=>s.code_ready).length!==d.stages_code_ready
 ||d.stages.some((s,i)=>s.code_ready!==(i<d.stages_code_ready)
   ||s.status!==(i<d.stages_code_ready?"code_ready":"blocked")
   ||s.native_verified!==false||s.playable!==false)
 ||d.game_exe_tested!==false||d.joiplay_tested!==false
 ||d.main_game_modified!==false||d.save_migration_performed!==false
 ||d.native_windows_cases_executed!==0||d.native_android_cases_executed!==0
 ||d.pilot_map_symbols!==9||d.required_warps!==16||d.required_npcs!==5||d.required_starter_balls!==3
 ||!Number.isInteger(d.native_source_terrain_candidates)||d.native_source_terrain_candidates<0||d.native_source_terrain_candidates>9
 ||d.native_source_maps_missing!==9-d.native_source_terrain_candidates
 ||!Number.isInteger(d.native_map_bindings_verified)||d.native_map_bindings_verified<0||d.native_map_bindings_verified>9
 ||!Number.isInteger(d.native_maps_installed)||d.native_maps_installed<0||d.native_maps_installed>d.native_map_bindings_verified
 ||d.next_stage!==(d.stages_code_ready<8?"J0"+(d.stages_code_ready+1):null)
 ||typeof d.next_prompt!=="string"||d.next_prompt.length<30||d.next_prompt.length>2500
 ||typeof d.next_button_label!=="string"||d.next_button_label.length<10||d.next_button_label.length>120
 ||typeof d.next_issue_url!=="string"||!d.next_issue_url.startsWith(issuePrefix)
 ||!/^\d+$/.test(d.next_issue_url.slice(issuePrefix.length)))
 throw Error("SINNOH_PLAYABLE_PROGRESS_INVALID");
 return d;
}
function render(d){
 $("engineering").value=d.stages_code_ready;
 $("native").value=d.stages_native_validated;
 $("engineeringLabel").textContent=d.stages_code_ready+" de 8 ("+d.engineering_percent+"%)";
 $("nativeLabel").textContent=d.stages_native_validated+" de 8 ("+d.native_verified_percent+"%)";
 $("maps").textContent=d.native_maps_installed+"/"+d.pilot_map_symbols;
 $("warps").textContent="0/"+d.required_warps;
 $("windows").textContent=d.native_windows_cases_executed+"/"+d.native_windows_cases_total;
 $("android").textContent=d.native_android_cases_executed+"/"+d.native_android_cases_total;
 $("referenceCount").textContent=d.native_source_terrain_candidates+"/9";
 $("missingCount").textContent=d.native_source_maps_missing+"/9";
 $("runtimeStatus").textContent="Sinnoh ainda não está jogável.";
 $("status").textContent=d.stages_code_ready+" de 8 ferramentas de engenharia preparadas; "
 +d.stages_native_validated+" de 8 fases comprovadas no jogo. "
 +d.native_source_maps_missing+" mapas reais ainda não identificados.";
 const list=$("stages");list.replaceChildren();
 for(const s of d.stages){
  const card=el("article",""),id=el("div",s.id),title=el("h3",s.title);
  id.className="id";
  const state=el("div",s.code_ready?"Código preparado · jogo real pendente":"Implementação pendente");
  state.className=s.code_ready?"state ready":"state";
  const detail=el("p",s.completion_requires);
  card.className="stage";card.append(id,title,state,detail);list.append(card);
 }
 $("nextAction").textContent=d.next_button_label;
 // q= opens a new ChatGPT composer with draft prompt; USER must submit it.
 $("nextAction").href="https://chatgpt.com/?q="+encodeURIComponent(d.next_prompt);
 $("nextIssue").href=d.next_issue_url;
 $("nextIssue").textContent="Ver requisitos da fase "+d.next_stage+" no GitHub";
 $("nextStage").textContent=d.next_stage;
}
async function main(){
 try{
  const r=await fetch("/data/sinnoh-playable-progress.json",{cache:"no-store"});
  if(!r.ok)throw Error("DATA_UNAVAILABLE");
  render(validate(await r.json()));
 }catch(e){
  $("engineering").value=0;$("native").value=0;
  $("status").textContent="Progresso bloqueado: dados versionados inválidos ou indisponíveis.";
  $("stages").replaceChildren();
  $("nextAction").removeAttribute("href");
  $("nextIssue").removeAttribute("href");
  $("nextAction").textContent="Próxima fase indisponível";
 }
}
main();
