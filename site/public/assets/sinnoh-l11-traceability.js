"use strict";
// This is only a static same-origin reader and local in-memory filter.
const $=id=>document.getElementById(id);
const elt=(tag,content,className)=>{
  const x=document.createElement(tag);
  x.textContent=String(content);
  if(className)x.className=className;
  return x;
};
const opt=(v,label)=>{const x=elt("option",label);x.value=v;return x;};
function check(data){
 const counts=data?.counts || {};
 const g=data?.gates || {};
 if(data?.schema!==1 || data.stage!=="L11"
   || data.status!=="PUBLIC_TRACEABILITY_ALL_NATIVE_AND_HUMAN_PENDING"
   || data.mode!=="PUBLIC_READ_ONLY_NO_NATIVE_QA"
   || !Array.isArray(data.case_nodes) || data.case_nodes.length!==44
   || !Array.isArray(data.criterion_nodes) || data.criterion_nodes.length!==20
   || !Array.isArray(data.blocker_nodes) || data.blocker_nodes.length!==6
   || !Array.isArray(data.platform_lanes) || data.platform_lanes.length!==2
   || counts.cases_total!==44 || counts.criteria_total!==20
   || counts.windows!==43 || counts.android!==1 || counts.human_approved!==0
   || counts.native_completed!==0 || counts.native_approved!==0 || counts.local_reports!==0
   || counts.phase_bcd_completed!==0 || counts.phase_bcd_total!==13
   || counts.case_to_criterion_edges!==846 || counts.case_to_blocker_edges!==218
   || counts.criterion_to_blocker_edges!==20
   || g.r07!=="PENDING" || g.r08!=="PENDING" || g.r09!=="PENDING"
   || !data.public_drift_audit?.zero_drift || data.public_drift_audit.differences_found!==0
   || !Array.isArray(data.edges?.case_to_criterion) || data.edges.case_to_criterion.length!==846
   || !Array.isArray(data.edges?.case_to_blocker) || data.edges.case_to_blocker.length!==218
   || !Array.isArray(data.edges?.criterion_to_blocker) || data.edges.criterion_to_blocker.length!==20
   || new Set(data.case_nodes.map(x=>x.id)).size!==44
   || new Set(data.criterion_nodes.map(x=>x.id)).size!==20
   || data.case_nodes.filter(x=>x.platform==="windows").length!==43
   || data.case_nodes.filter(x=>x.platform==="android").length!==1
   || data.case_nodes.some(x=>x.native_status!=="pending"
      || x.review_state!=="NOT_REVIEWED" || x.native_qa_authorized!==false
      || x.human_signoff!==false
      || (x.platform==="android" && (x.blocker_ids.includes("B10")||x.blocker_ids.includes("B11")))
      || (x.platform==="windows" && (!x.blocker_ids.includes("B10")||!x.blocker_ids.includes("B11"))))
   || data.criterion_nodes.some(x=>x.review_state!=="NOT_REVIEWED"||x.human_signoff!==false)
   || JSON.stringify(data.blocker_nodes.map(x=>x.id))!==JSON.stringify(["B09","B10","B11","R07","R08","R09"])
   || data.blocker_nodes.at(-1).case_ids.length!==0
   || data.blocker_nodes.at(-1).scope!=="GLOBAL_REGION_PENDING_NOT_CASE_GATE"
   || data.global_region_gate?.id!=="R09"
   || data.global_region_gate.is_case_scoped!==false
   || data.global_region_gate.case_ids.length!==0
   || data.guarantees?.sinnoh_playable!==false
   || data.guarantees.local_android_l05_complete!==false
   || !["L07","L08","L09","L10"].every(k=>/^[0-9a-f]{40}$/.test(data.baseline_commits?.[k]))){
     throw new Error("Fonte documental incompatível");
   }
 // Cross-link consistency: the UI cannot display a modified projection as approved.
 const pair=(x,y)=>x+"\x1f"+y;
 const realCriteria=data.case_nodes.flatMap(c=>c.criteria_ids.map(id=>pair(c.id,id)));
 const realBlockers=data.case_nodes.flatMap(c=>c.blocker_ids.map(id=>pair(c.id,id)));
 const realCriterionStages=data.criterion_nodes.map(c=>pair(c.id,c.stage));
 if(JSON.stringify(realCriteria)!==JSON.stringify(data.edges.case_to_criterion.map(x=>pair(x[0],x[1])))
   || JSON.stringify(realBlockers)!==JSON.stringify(data.edges.case_to_blocker.map(x=>pair(x[0],x[1])))
   || JSON.stringify(realCriterionStages)!==JSON.stringify(data.edges.criterion_to_blocker.map(x=>pair(x[0],x[1])))
   || data.edges.case_to_blocker.some(x=>x[1]==="R09")){
   throw new Error("Vínculos públicos divergentes");
 }
 return data;
}
const cell=(row,child)=>{const td=document.createElement("td");td.append(child);row.append(td);};
function filter(data){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR");
 const platform=$("platform").value,criterion=$("criterionFilter").value,blocker=$("blockerFilter").value;
 const filtered=data.case_nodes.filter(c=>(!q||(c.id+" "+c.kind).toLocaleLowerCase("pt-BR").includes(q))
 &&(!platform||c.platform===platform)&&(!criterion||c.criteria_ids.includes(criterion))
 &&(!blocker||c.blocker_ids.includes(blocker)));
 $("caseRows").replaceChildren(...filtered.map(c=>{
   const tr=document.createElement("tr");
   const btn=elt("button",c.id);
   btn.type="button";
   btn.addEventListener("click",()=>selectCase(data,c.id));
   cell(tr,btn);
   cell(tr,elt("span",c.kind+" / "+(c.platform==="windows"?"Windows":"Android/JoiPlay"),"pill"));
   cell(tr,elt("span",String(c.criteria_ids.length)));
   cell(tr,elt("span",c.blocker_ids.join(", ")));
   cell(tr,elt("strong","Pendente, sem QA","pending"));
   return tr;
 }));
 $("status").textContent=filtered.length+" de 44 casos listados · 0/44 QA nativa.";
}
function selectCase(data,id){
 const c=data.case_nodes.find(x=>x.id===id);
 if(!c)return;
 const container=$("caseDetail");
 const heading=elt("h3",c.id);
 const meta=elt("p",c.kind+" · "+c.platform+" · pendente / não revisado");
 const criteria=elt("p","Critérios associados:");
 const criterionButtons=document.createElement("div");criterionButtons.className="links";
 c.criteria_ids.forEach(cid=>{
   const btn=elt("button",cid);btn.type="button";
   btn.addEventListener("click",()=>{$("criterionFilter").value=cid;filter(data);$("casos").scrollIntoView();});
   criterionButtons.append(btn);
 });
 const blockers=elt("p","Bloqueios:");
 const blockerButtons=document.createElement("div");blockerButtons.className="links";
 c.blocker_ids.forEach(bid=>{
   const btn=elt("button",bid);btn.type="button";
   btn.addEventListener("click",()=>{$("blockerFilter").value=bid;filter(data);$("casos").scrollIntoView();});
   blockerButtons.append(btn);
 });
 const status=elt("p","Não autorizado: Game.exe, Windows Sandbox, JoiPlay, instalação ou testes nativos.","pending");
 container.replaceChildren(heading,meta,criteria,criterionButtons,blockers,blockerButtons,status);
 $("detalhes").scrollIntoView();
}
function render(data){
 data.criterion_nodes.forEach(c=>$("criterionFilter").append(opt(c.id,c.id)));
 data.blocker_nodes.filter(b=>b.id!=="R09").forEach(b=>$("blockerFilter").append(opt(b.id,b.id)));
 $("criteriaRows").replaceChildren(...data.criterion_nodes.map(c=>{
   const tr=document.createElement("tr");const btn=elt("button",c.id);btn.type="button";
   btn.addEventListener("click",()=>{$("criterionFilter").value=c.id;filter(data);$("casos").scrollIntoView();});
   cell(tr,btn);cell(tr,elt("span",c.stage));
   cell(tr,elt("span",String(c.case_ids.length)));
   cell(tr,elt("strong","Não revisado","pending"));
   return tr;
 }));
 $("blockerRows").replaceChildren(...data.blocker_nodes.map(b=>{
   const tr=document.createElement("tr");
   const btn=elt("button",b.id);btn.type="button";
   btn.addEventListener("click",()=>{
      if(b.id==="R09")$("proveniencia").scrollIntoView();
      else{$("blockerFilter").value=b.id;filter(data);$("casos").scrollIntoView();}
   });
   cell(tr,btn);cell(tr,elt("span",b.scope));
   cell(tr,elt("span",b.id==="R09"?"Global; sem vínculo adicional":String(b.case_ids.length)));
   cell(tr,elt("strong","Pendente","pending"));
   return tr;
 }));
 ["search","platform","criterionFilter","blockerFilter"].forEach(id=>$(id).addEventListener("input",()=>filter(data)));
 $("reset").addEventListener("click",()=>{
   ["search","platform","criterionFilter","blockerFilter"].forEach(id=>{$(id).value="";});
   filter(data);$("search").focus();
 });
 ["L07","L08","L09","L10"].forEach(k=>{$("sha"+k).textContent=data.baseline_commits[k];});
 filter(data);
}
async function main(){
 try{
   const response=await fetch("/data/sinnoh-l11-public-traceability.json",{cache:"no-store"});
   if(!response.ok)throw new Error("Fonte indisponível");
   render(check(await response.json()));
 }catch(_error){
   $("status").textContent="Bloqueado: integridade da trilha pública não confirmada.";
   $("caseRows").replaceChildren();$("criteriaRows").replaceChildren();$("blockerRows").replaceChildren();
   $("caseDetail").replaceChildren(elt("p","Dados bloqueados: não há autorização de execução."));
 }
}
main();
