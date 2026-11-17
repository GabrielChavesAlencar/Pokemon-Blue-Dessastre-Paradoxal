// G06.3: pure, URL-shareable filters on UNOVA PLANNED references only.
// Never unlocks gameplay or turns a symbolic field into native data.
export const UNOVA_FILTER_TABS=Object.freeze([
  'areas','capitulos','missoes','npcs','treinadores','ginasios','liga','pendencias'
]);
export const UNOVA_PENDING_LABELS=Object.freeze({
  maps:'MapIDs e propriedade regional',events:'Eventos e scripts',
  npcSprites:'Sprites de NPCs e direitos',trainerTeams:'Times Trainer PBS',
  levels:'Níveis nativos',wildEncounters:'Encontros e taxas',
  rights:'Direitos e licenças',gameExe:'QA no Game.exe'
});
export const UNOVA_PENDING_TYPES=Object.freeze({
  mapas:'MapIDs',eventos:'Eventos',equipes:'Equipes e PBS',
  niveis:'Níveis',encontros:'Encontros',sprites:'Sprites',
  direitos:'Direitos',qa:'QA Game.exe'
});
const requireTab=tab=>{
  if(!UNOVA_FILTER_TABS.includes(tab))throw new Error('unova-filter-invalid-tab');
};
const string=x=>typeof x==='string'?x:'';
const clean=(x,max)=>string(x).trim().slice(0,max);
export const normalizeUnovaText=value=>String(value??'').normalize('NFKD')
 .replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
const matches=(text,query)=>{
 if(!query)return true;
 const hay=normalizeUnovaText(text);
 return normalizeUnovaText(query).split(' ').every(term=>hay.includes(term));
};
const uniqueSorted=values=>[...new Set(values.filter(x=>typeof x==='string'&&x.length))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
const chapterBy=(data,key)=>data.chapters.find(c=>c.key===key);
const areaBy=(data,key)=>data.areas.find(a=>a.key===key);
const chapterForArea=(data,key)=>areaBy(data,key)?.chapterKey??null;
const phaseForArea=(data,key)=>areaBy(data,key)?.plannedPhase??null;
const rowFields=(data,tab,row)=>{
 if(tab==='areas')return {
  searchable:[row.key,row.name,row.kind,row.plannedPhase,row.storyScope,chapterBy(data,row.chapterKey)?.title],
  fase:row.plannedPhase,capitulo:row.chapterKey,tipo:row.kind,area:row.key,
  pending:['mapas','eventos','encontros','niveis','qa','direitos']
 };
 if(tab==='capitulos')return {
  searchable:[row.key,row.title,row.index,row.plannedPhase,row.missionKey,row.requiredMissionKey,
    areaBy(data,row.referenceAreaKey)?.name],
  fase:row.plannedPhase,capitulo:row.key,tipo:row.arc,area:row.referenceAreaKey,
  pending:['eventos','qa']
 };
 if(tab==='missoes')return {
  searchable:[row.key,row.chapterTitle,row.chapterKey,row.kind,row.areaKey,areaBy(data,row.areaKey)?.name],
  fase:row.plannedPhase,capitulo:row.chapterKey,tipo:row.kind,area:row.areaKey,
  pending:['eventos','qa']
 };
 if(tab==='npcs')return {
  searchable:[row.key,row.name,row.role,row.areaKey,areaBy(data,row.areaKey)?.name,
    ...row.relatedAreaKeys.map(key=>areaBy(data,key)?.name)],
  fase:phaseForArea(data,row.areaKey),
  capitulo:chapterForArea(data,row.areaKey),
  tipo:row.role,area:row.areaKey,
  relatedAreas:row.relatedAreaKeys,pending:['sprites','eventos','direitos','qa']
 };
 if(tab==='treinadores')return {
  searchable:[row.key,row.actor,row.policy,row.sourceMode,row.npcKey,row.trainerRef,
    row.chapterKey,chapterBy(data,row.chapterKey)?.title,row.areaKey,areaBy(data,row.areaKey)?.name],
  fase:phaseForArea(data,row.areaKey),capitulo:row.chapterKey,
  tipo:row.actor,area:row.areaKey,pending:['equipes','niveis','eventos','qa']
 };
 if(tab==='ginasios')return {
  searchable:[row.key,row.badge,row.leaderKey,...Object.values(row.leaderByStarter||{}),
    row.chapterKey,areaBy(data,row.cityAreaKey)?.name,areaBy(data,row.gymAreaKey)?.name],
  fase:row.sourcePhase,capitulo:row.chapterKey,
  tipo:'gym',area:row.gymAreaKey,relatedAreas:[row.cityAreaKey],
  pending:['equipes','niveis','eventos','qa']
 };
 if(tab==='liga')return {
  searchable:[row.key,row.name,row.specialty,row.description,row.chapterKey,
    areaBy(data,row.areaKey)?.name,row.areaKey],
  fase:phaseForArea(data,row.areaKey),capitulo:row.chapterKey,
  tipo:row.entryKind,area:row.areaKey,pending:['equipes','niveis','eventos','qa']
 };
 if(tab==='pendencias')return {
  searchable:[row.key,row.label,row.value,row.category],
  fase:null,capitulo:null,tipo:row.category,area:null,pending:[row.category]
 };
 throw new Error('unova-filter-invalid-tab');
};
const combine=(data,tab)=>{
 switch(tab){
 case 'areas':return data.areas;
 case 'capitulos':return data.chapters;
 case 'missoes':return data.missions;
 case 'npcs':return data.npcs;
 case 'treinadores':return data.trainers;
 case 'ginasios':return data.gyms;
 case 'liga':return [
  ...data.elite.map(row=>({...row,entryKind:'elite'})),
  ...data.castle.map(row=>({...row,entryKind:'castelo',name:row.description??row.key}))
 ];
 case 'pendencias':return Object.entries(data.pending).map(([key,value])=>({
   key,label:UNOVA_PENDING_LABELS[key]??key,value:String(value),
   category:({maps:'mapas',events:'eventos',npcSprites:'sprites',
     trainerTeams:'equipes',levels:'niveis',wildEncounters:'encontros',
     rights:'direitos',gameExe:'qa'})[key]??'qa'
 }));
 default:throw new Error('unova-filter-invalid-tab');
 }
};
const options=(data,tab)=>{
 const records=combine(data,tab);
 const all=records.map(row=>rowFields(data,tab,row));
 return {
  fases:uniqueSorted(all.map(v=>v.fase)),
  capitulos:uniqueSorted(all.map(v=>v.capitulo)),
  tipos:uniqueSorted(all.map(v=>v.tipo)),
  areas:uniqueSorted(all.flatMap(v=>[v.area,...(v.relatedAreas||[])])),
  pendencias:uniqueSorted(all.flatMap(v=>v.pending||[]))
 };
};
const rawParams=value=>{
 if(value instanceof URLSearchParams)return value;
 if(typeof value==='string')return new URLSearchParams(value.startsWith('?')?value.slice(1):value);
 if(value&&typeof value==='object'&&!Array.isArray(value)){
  const q=new URLSearchParams();
  for(const key of ['busca','fase','capitulo','tipo','pendencia','area'])
   if(typeof value[key]==='string')q.set(key,value[key]);
  return q;
 }
 return new URLSearchParams();
};
export const unovaGuideOptions=(data,tab)=>{
 requireTab(tab);return options(data,tab);
};
export function sanitizeUnovaFilters(data,tab,params){
 requireTab(tab);
 const q=rawParams(params);
 const optionsForTab=options(data,tab);
 const allow=(name,allowed)=>allowed.includes(q.get(name))?q.get(name):'todos';
 return {
  busca:clean(q.get('busca'),100),
  fase:allow('fase',optionsForTab.fases),
  capitulo:allow('capitulo',optionsForTab.capitulos),
  tipo:allow('tipo',optionsForTab.tipos),
  pendencia:allow('pendencia',optionsForTab.pendencias),
  area:allow('area',optionsForTab.areas)
 };
}
export const unovaFilterUrl=(data,tab,params={})=>{
 requireTab(tab);
 const filter=sanitizeUnovaFilters(data,tab,params);
 const q=new URLSearchParams();
 for(const k of ['busca','fase','capitulo','tipo','pendencia','area'])
  if(filter[k]&&filter[k]!=='todos')q.set(k,filter[k]);
 return '/unova/'+tab+(q.size?'?'+q.toString():'');
};
export function filterUnovaGuide(data,tab,params={}){
 requireTab(tab);
 const opts=options(data,tab);
 const filters=sanitizeUnovaFilters(data,tab,params);
 const all=combine(data,tab);
 const hits=all.filter(row=>{
  const props=rowFields(data,tab,row);
  return matches(props.searchable.flat(Infinity).filter(x=>x!==null&&x!==undefined).join(' '),filters.busca)
   &&(filters.fase==='todos'||props.fase===filters.fase)
   &&(filters.capitulo==='todos'||props.capitulo===filters.capitulo)
   &&(filters.tipo==='todos'||props.tipo===filters.tipo)
   &&(filters.pendencia==='todos'||props.pending.includes(filters.pendencia))
   &&(filters.area==='todos'||props.area===filters.area||(props.relatedAreas||[]).includes(filters.area));
 });
 return {tab,items:hits,count:hits.length,total:all.length,filters,options:opts};
}
