"use strict";
// Public, same-origin read-only filters. Never send or modify evidence.
const $=id=>document.getElementById(id);
const make=(tag,text,cls)=>{const x=document.createElement(tag);x.textContent=String(text);if(cls)x.className=cls;return x;};
const cell=(tr,child)=>{const td=document.createElement("td");td.append(child);tr.append(td);};
function verify(d){
 const c=d?.counts||{},s=d?.dependency_semantics||{},a=d?.disclaimer||{};
 if(d?.schema!==1||d.stage!=="L14"||d.region!=="SINNOH"
 ||d.mode!=="PUBLIC_READ_ONLY_DOCUMENTARY_DEPENDENCIES"
 ||d.status!=="ALL_DEPENDENCY_REQUESTS_BLOCKED_NO_NATIVE_QA"
 ||!Array.isArray(d.rows)||d.rows.length!==88
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||c.readiness_rows!==88||c.rows_blocked!==88||c.rows_pending!==88||c.rows_ready!==0
 ||c.public_edges_verified!==1084||c.request_documentary_links!==1084
 ||c.case_to_criterion_request_links!==846||c.case_to_blocker_request_links!==218
 ||c.criterion_to_blocker_request_links!==20||c.anonymous_rows_unassigned!==18
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0||c.native_approved!==0
 ||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||s.links_are_documentary_only!==true||s.priority_is_not_execution_order!==true
 ||s.no_derived_dependencies_for_anonymous_slots!==true||s.no_r09_per_case_links!==true
 ||s.readiness_never_infers_auth!==true||s.readiness_state!=="BLOCKED"
 ||a.no_upload_or_attachments!==true||a.no_game_execution!==true
 ||a.no_joiplay_execution!==true||a.no_windows_sandbox_execution!==true
 ||a.sinnoh_playable!==false||a.none_ready!==true||a.none_physically_approved!==true
 ||new Set(d.rows.map(r=>r.request_id)).size!==88
 ||d.rows.some((r,i)=>r.order!==i+1||r.readiness!=="BLOCKED"||r.status!=="PENDING"
    ||r.human_approval!==false||r.physical_evidence_received!==false
    ||r.native_qa_authorized!==false||r.private_submission_allowed!==false
    ||r.documentary_dependency_count!==r.documentary_dependency_request_ids.length)
 ||d.rows.reduce((n,r)=>n+r.documentary_dependency_count,0)!==1084
 ||d.rows.some(r=>r.anonymous_bookkeeping_slot&&r.documentary_dependency_count!==0)
 ||d.rows.some(r=>r.documentary_dependency_request_ids.includes("L13-GLOBAL-R09"))
 ||d.rows.some(r=>r.kind==="NATIVE_CASE"&&r.platform==="android"&&
    r.documentary_dependency_request_ids.some(z=>z==="L13-BLOCKER-B10"||z==="L13-BLOCKER-B11"))
 ||d.global_r09?.status!=="PENDING"||d.global_r09?.dependency_request_ids.length!==0
 ||d.global_r09?.case_ids.length!==0||d.global_r09?.readiness!=="BLOCKED"
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[1].requires_windows_sandbox_b10_b11!==false
 ||d.platform_partition.some(p=>p.readiness!=="BLOCKED"||p.native_completed!==0||p.authorization!==false)
 ||!["L07","L08","L09","L10","L11","L12","L13"].every(k=>/^[a-f0-9]{40}$/.test(d.baseline_commits?.[k]))
 )throw new Error("Matriz L14 pública inválida");
 return d;
}
function show(data,r){
 const d=$("detail");
 const h=make("h3",r.request_id);
 const p=make("p",r.kind+" · "+r.platform+" · P"+r.priority+" · BLOCKED");
 const label=make("p","Relações públicas: "+r.documentary_dependency_count);
 const chips=document.createElement("div");chips.className="chips";
 if(r.documentary_dependency_count===0)chips.append(make("span","Nenhuma dependência documental vinculada"));
 else for(const id of r.documentary_dependency_request_ids)chips.append(make("span",id));
 const warning=make("p","Nenhuma aprovação humana, QA nativa ou recebimento de provas físicas.","pending");
 d.replaceChildren(h,p,label,chips,warning);
 $("detalhes").scrollIntoView();
}
function filter(data){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR");
 const p=$("priority").value,k=$("kind").value,platform=$("platform").value;
 const ready=$("readiness").value,link=$("link").value;
 const rows=data.rows.filter(r=>(!q||(r.request_id+" "+r.subject_id).toLocaleLowerCase("pt-BR").includes(q))
  &&(!p||r.priority===Number(p))&&(!k||r.kind===k)
  &&(!platform||r.platform===platform)&&(!ready||r.readiness===ready)
  &&(!link||(link==="linked"?r.documentary_dependency_count>0:r.documentary_dependency_count===0)));
 $("matrixRows").replaceChildren(...rows.map(r=>{
  const tr=document.createElement("tr");const btn=make("button",r.request_id);
  btn.type="button";btn.addEventListener("click",()=>show(data,r));
  cell(tr,btn);cell(tr,make("span","P"+r.priority));
  cell(tr,make("span",r.kind+" · "+r.platform));
  cell(tr,make("span",r.documentary_dependency_count));
  cell(tr,make("strong","Pendente / bloqueado","pending"));
  return tr;
 }));
 $("status").textContent=rows.length+" de 88 pedidos exibidos · 0 autorizados.";
}
function render(data){
 const add=(key,str)=>{const op=make("option",str);op.value=str;$(key).append(op);};
 [...new Set(data.rows.map(r=>r.kind))].forEach(x=>add("kind",x));
 $("platformRows").replaceChildren(...data.platform_partition.map(p=>{
  const tr=document.createElement("tr");
  for(const v of [p.platform,p.native_requests,p.native_completed,
   p.requires_windows_sandbox_b10_b11?"Pendente Windows":"Não se aplica","BLOCKED"])cell(tr,make("span",v));
  return tr;
 }));
 for(const id of ["search","priority","kind","platform","readiness","link"])
  $(id).addEventListener("input",()=>filter(data));
 $("reset").addEventListener("click",()=>{
   for(const id of ["search","priority","kind","platform","readiness","link"])$(id).value="";
   filter(data);$("search").focus();
 });
 for(const key of ["L07","L08","L09","L10","L11","L12","L13"])$("sha"+key).textContent=data.baseline_commits[key];
 filter(data);
}
async function main(){
 try{
   const resp=await fetch("/data/sinnoh-l14-public-readiness-matrix.json",{cache:"no-store"});
   if(!resp.ok)throw Error("Dados públicos indisponíveis");
   render(verify(await resp.json()));
 }catch(_e){
   $("status").textContent="Bloqueado: integridade documental não confirmada.";
   $("matrixRows").replaceChildren();$("platformRows").replaceChildren();
 }
}
main();