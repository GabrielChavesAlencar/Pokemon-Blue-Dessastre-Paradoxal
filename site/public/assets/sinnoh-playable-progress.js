"use strict";
// Read-only static report; never uploads assets, accepts save files or executes games.
const $=id=>document.getElementById(id);
const node=(tag,content)=>{const n=document.createElement(tag);n.textContent=String(content);return n;};
function validate(d){
 if(d?.schema!==1||d.region!=="SINNOH"||d.track!=="JOGAVEL_TWINLEAF_SANDGEM"
 ||d.status!=="PILOT_NOT_INSTALLED_NOT_PLAYABLE"
 ||d.stages_total!==8||d.stages_code_ready!==1||d.stages_native_validated!==0
 ||d.engineering_percent!==12.5||d.native_verified_percent!==0
 ||!Array.isArray(d.stages)||d.stages.length!==8
 ||d.stages.map(x=>x.id).join(",")!=="J01,J02,J03,J04,J05,J06,J07,J08"
 ||d.stages.filter(x=>x.code_ready).length!==1||d.stages[0].status!=="code_ready"
 ||d.stages.some((x,i)=>i>0&&x.status!=="blocked"||x.native_verified!==false||x.playable!==false)
 ||d.game_exe_tested!==false||d.joiplay_tested!==false
 ||d.main_game_modified!==false||d.save_migration_performed!==false
 ||d.native_windows_cases_executed!==0||d.native_android_cases_executed!==0
 ||d.pilot_map_symbols!==9||d.required_warps!==16
 ||d.required_npcs!==5||d.required_starter_balls!==3
 ||d.next_stage!=="J02")throw Error("SINNOH_JOGAVEL_PROGRESS_BLOCKED");
 return d;
}
function render(d){
 $("engineering").value=d.stages_code_ready;
 $("native").value=d.stages_native_validated;
 $("engineeringLabel").textContent=d.stages_code_ready+" de 8 ("+d.engineering_percent+"%)";
 $("nativeLabel").textContent=d.stages_native_validated+" de 8 ("+d.native_verified_percent+"%)";
 $("maps").textContent="0/"+d.pilot_map_symbols;
 $("warps").textContent="0/"+d.required_warps;
 $("windows").textContent=d.native_windows_cases_executed+"/"+d.native_windows_cases_total;
 $("android").textContent=d.native_android_cases_executed+"/"+d.native_android_cases_total;
 $("runtimeStatus").textContent="Sinnoh ainda não está jogável.";
 $("status").textContent="1 fase de engenharia executável pronta; 7 fases de integração bloqueadas. Nenhum teste nativo confirmado.";
 const el=$("stages");el.replaceChildren();
 for(const s of d.stages){
  const card=node("article",""),id=node("div",s.id),title=node("h3",s.title);
  id.className="id";
  const state=node("div",s.code_ready?"Código J01 preparado · QA real pendente":"Ainda não implementado");
  state.className=s.code_ready?"state ready":"state";
  const detail=node("p",s.completion_requires);
  card.className="stage";card.append(id,title,state,detail);el.append(card);
 }
}
async function main(){
 try{
  const r=await fetch("/data/sinnoh-playable-progress.json",{cache:"no-store"});
  if(!r.ok)throw Error("MISSING");
  render(validate(await r.json()));
 }catch(err){
  $("engineering").value=0;$("native").value=0;
  $("status").textContent="Progresso bloqueado: arquivo versionado não pôde ser validado.";
  $("stages").replaceChildren();
 }
}
main();
