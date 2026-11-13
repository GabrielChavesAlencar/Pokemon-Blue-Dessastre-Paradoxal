import {loadPortal,loadDetails,loadRegularTrainers,effectiveDetail} from './data.js';
import {esc,icon} from './utils.js';
import {home,pokedex,dexResults,locations,locationResults,locationDetail,updates,updateResults as updateTimelineResults,guides,guideDetail,empty} from './views.js';
import {pokemonDetail,moveRows} from './detail.js';
import {storyIndex,bossesIndex,trainerDetail,allTrainers} from './story.js';
import {regularIndex,regularResults,regularTrainerById,regularDetail} from './regular-trainers.js';
import {changesPage} from './changes.js';
import {loadRegions,regionsPage,regionPicker} from './regions.js';
import {loadKanto,kantoIndex,kantoLocation,kantoTrainer} from './kanto.js';
import {loadJohtoPreview,johtoIndex} from './johto.js';
import {downloadsPage} from './downloads.js';
import {bindAndroidRelease} from './android-release.js';

const main=document.getElementById('main');
let model,detailData,currentBase,currentEffective,currentRoute='',renderId=0;
let favorites;try{favorites=new Set(JSON.parse(localStorage.getItem('blue:favorites')??'[]'));}catch{favorites=new Set();}
const initial=()=>({q:'',type:'',generation:'',group:'all',sort:'number',limit:24,locationQ:'',method:'',locationLimit:12,version:'0',category:'all',updateQ:'',updateLimit:24,form:'',moveKind:'level',moveQ:'',moveLimit:40,trainerQ:'',trainerArea:'all',trainerLimit:24});
let state=initial();
const toast=message=>{const el=document.getElementById('toast');el.textContent=message;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),2600);};
function navigate(url){history.pushState({},'',url);render(true);}
function setPage(title){document.title=title==='Início'?'Pokémon Blue — Dessastre Paradoxal':`${title} · Pokémon Blue`;}
function updateResults(){
  if(currentRoute==='pokedex'){
    const result=dexResults(model,state,favorites);document.getElementById('dex-results').innerHTML=result.html;document.getElementById('dex-count').textContent=result.count.toLocaleString('pt-BR');
  }else if(currentRoute==='localizacoes'&&!currentBase){
    const result=locationResults(model,state);document.getElementById('location-results').innerHTML=result.html;document.getElementById('location-count').textContent=result.count;
  }else if(currentRoute==='atualizacoes'){
    const result=updateTimelineResults(model,state);document.getElementById('update-results').innerHTML=result.html;document.getElementById('update-count').textContent=result.count;
  }else if(currentRoute==='treinadores'&&!currentBase&&model.regularData){
    const result=regularResults(model,model.regularData,state);
    document.getElementById('regular-results').innerHTML=result.html;
    document.getElementById('regular-count').textContent=result.count;
  }else if(currentRoute==='pokemon'&&currentEffective){
    const result=moveRows(currentEffective,detailData,state);document.getElementById('moves-body').innerHTML=result.html;document.getElementById('moves-count').textContent=`${result.count} golpes`;
  }
}
function addRegionPicker(route){
  main.firstElementChild?.insertAdjacentHTML('afterbegin',regionPicker(route,'decades'));
}

async function render(scroll=false){
  const id=++renderId;const url=new URL(location.href);const parts=url.pathname.split('/').filter(Boolean);const section=parts[0]??'home';const route=section==='pokedex'&&parts[1]?'pokemon':section;
  const identity=[route,parts[1],url.searchParams.get('regiao')].join('/');
  if(main.dataset.identity!==identity){state=initial();if(['paradox','future'].includes(url.searchParams.get('grupo')))state.group=url.searchParams.get('grupo');if(url.searchParams.get('pokemon'))state.locationQ=model?.byId.get(url.searchParams.get('pokemon'))?.name??url.searchParams.get('pokemon');state.form=url.searchParams.get('forma')??'';state.generation=url.searchParams.get('geracao')??'';}
  main.dataset.identity=identity;currentRoute=route;currentBase=null;currentEffective=null;
  document.getElementById('nav').classList.remove('open');document.getElementById('menu-toggle').setAttribute('aria-expanded','false');
  document.querySelectorAll('[data-nav]').forEach(link=>{const active=link.dataset.nav===section;link.classList.toggle('active',active);if(active)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
  main.setAttribute('aria-busy','true');
  try{
    if(route==='home'){main.innerHTML=home(model,favorites);setPage('Início');}
    else if(route==='pokedex'){main.innerHTML=pokedex(model,state,favorites);setPage('Pokédex');}
    else if(route==='pokemon'){
      const base=model.byId.get(decodeURIComponent(parts[1]).toUpperCase());if(!base)throw new Error('not-found');
      main.innerHTML='<div class="loading"><span class="loader"></span> Consultando a ficha…</div>';
      detailData=await loadDetails();if(id!==renderId)return;
      currentBase=base;const form=state.form?detailData.species[`${base.id},${state.form}`]:null;currentEffective=effectiveDetail(base,form,detailData);
      main.innerHTML=pokemonDetail(model,base,detailData,state,favorites);setPage(base.name);
    }else if(['localizacoes','treinadores','chefes'].includes(route) &&
      !parts[1] && url.searchParams.get('regiao')==='johto'){
      const data=await loadJohtoPreview();if(id!==renderId)return;
      main.innerHTML=johtoIndex(data,route);
      setPage({localizacoes:'Localizações de Johto · prévia',treinadores:'Treinadores de Johto · prévia',
        chefes:'Líderes e Elite de Johto · prévia'}[route]);
    }else if(['localizacoes','treinadores','chefes'].includes(route) &&
      (parts[1]?.startsWith('kanto-') || (!parts[1] && url.searchParams.get('regiao')==='kanto'))){
      const data=await loadKanto();if(id!==renderId)return;
      if(!parts[1]){
        main.innerHTML=kantoIndex(model,data,route);
        setPage({localizacoes:'Localizações de Kanto',treinadores:'Treinadores de Kanto',chefes:'Líderes de Kanto'}[route]);
      }else if(route==='localizacoes'){
        const area=data.locations.find(row=>row.id===parts[1]);
        if(!area)throw new Error('not-found');
        currentBase=area;main.innerHTML=kantoLocation(model,data,area);setPage(area.name);
      }else{
        const trainer=data.trainers.find(row=>row.id===parts[1] && row.leader===(route==='chefes'));
        if(!trainer)throw new Error('not-found');
        const details=await loadDetails();if(id!==renderId)return;
        currentBase=trainer;main.innerHTML=kantoTrainer(model,data,trainer,details);setPage(trainer.name);
      }
    }else if(route==='localizacoes'){
      if(parts[1]){const area=model.locations.find(x=>x.id===Number(parts[1]));if(!area)throw new Error('not-found');currentBase=area;main.innerHTML=locationDetail(model,area,state);setPage(area.name);}
      else{main.innerHTML=locations(model,state);addRegionPicker(route);setPage('Localizações');}
    }else if(route==='regioes'){
      const registry=await loadRegions();if(id!==renderId)return;
      main.innerHTML=regionsPage(registry);setPage('Circuito de regiões');
    }else if(route==='atualizacoes'){main.innerHTML=updates(model,state);setPage('Atualizações');}
    else if(route==='o-que-mudou'){main.innerHTML=changesPage();setPage('O que mudou');}
    else if(route==='downloads'){main.innerHTML=downloadsPage();setPage('Downloads');void bindAndroidRelease(main);}
    else if(route==='historia'){main.innerHTML=storyIndex(model);setPage('Guia da História');}
    else if(route==='treinadores'){
      const data=await loadRegularTrainers();if(id!==renderId)return;
      model.regularData=data;
      if(parts[1]){
        const trainer=regularTrainerById(data,decodeURIComponent(parts[1]));
        if(!trainer)throw new Error('not-found');
        detailData=await loadDetails();if(id!==renderId)return;
        currentBase=trainer;
        main.innerHTML=regularDetail(model,data,trainer,url.searchParams.get('modo'),detailData,url.searchParams.get('nivel')??50);
        setPage(trainer.name);
      }else{main.innerHTML=regularIndex(model,data,state);addRegionPicker(route);setPage('Treinadores');}
    }
    else if(route==='chefes'){
      if(parts[1]){
        const trainer=allTrainers(model.story).find(x=>x.id===decodeURIComponent(parts[1]));
        if(!trainer)throw new Error('not-found');
        detailData=await loadDetails();if(id!==renderId)return;
        main.innerHTML=trainerDetail(model,trainer,url.searchParams.get('modo'),detailData,url.searchParams.get('nivel')??50);setPage(trainer.name);
      }else{main.innerHTML=bossesIndex(model);addRegionPicker(route);setPage('Mestres e Chefes');}
    }
    else if(route==='guias'){
      if(parts[1]){const guide=model.guides.find(x=>x.id===parts[1]);if(!guide)throw new Error('not-found');main.innerHTML=guideDetail(model,guide);setPage(guide.title);}
      else{main.innerHTML=guides(model);setPage('Guias');}
    }else throw new Error('not-found');
  }catch(error){
    main.innerHTML=`<div class="container">${empty(error.message==='not-found'?'Este caminho ainda não foi descoberto.':'Não foi possível abrir esta página.',error.message==='not-found'?'Volte ao início e encontre um novo destino.':'Tente recarregar a página em alguns instantes.')}<div class="load-more"><a class="button button-primary" href="/">Voltar ao início ${icon('arrow')}</a></div></div>`;setPage('Página não encontrada');
  }finally{if(id===renderId){main.removeAttribute('aria-busy');if(scroll){window.scrollTo({top:0,behavior:'instant'});main.focus({preventScroll:true});}}}
}
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href]');if(!link||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||link.target==='_blank'||link.hasAttribute('download'))return;
  const href=link.getAttribute('href');if(href.startsWith('#'))return;
  const url=new URL(link.href,location.href);if(url.origin!==location.origin)return;
  event.preventDefault();navigate(url.pathname+url.search+url.hash);
});
main.addEventListener('click',event=>{
  const favorite=event.target.closest('[data-favorite]');if(favorite){
    const id=favorite.dataset.favorite;const active=!favorites.has(id);if(active)favorites.add(id);else favorites.delete(id);
    try{localStorage.setItem('blue:favorites',JSON.stringify([...favorites]));}catch{}
    document.querySelectorAll(`[data-favorite="${id}"]`).forEach(button=>{button.classList.toggle('is-favorite',active);button.setAttribute('aria-pressed',String(active));button.setAttribute('aria-label',`${active?'Remover dos':'Adicionar aos'} favoritos`);});
    const counter=document.querySelector('[data-group="favorites"] small');if(counter)counter.textContent=favorites.size;
    if(state.group==='favorites'&&currentRoute==='pokedex')updateResults();toast(active?'Pokémon adicionado aos favoritos.':'Pokémon removido dos favoritos.');return;
  }
  const group=event.target.closest('[data-group]');if(group){state.group=group.dataset.group;state.limit=24;document.querySelectorAll('[data-group]').forEach(b=>{b.classList.toggle('active',b===group);b.setAttribute('aria-pressed',String(b===group));});updateResults();return;}
  const category=event.target.closest('[data-category]');if(category){state.category=category.dataset.category;state.updateLimit=24;document.querySelectorAll('[data-category]').forEach(b=>{b.classList.toggle('active',b===category);b.setAttribute('aria-pressed',String(b===category));});updateResults();return;}
  const kind=event.target.closest('[data-move-kind]');if(kind){state.moveKind=kind.dataset.moveKind;state.moveLimit=40;document.querySelectorAll('[data-move-kind]').forEach(b=>{b.classList.toggle('active',b===kind);b.setAttribute('aria-pressed',String(b===kind));});updateResults();return;}
  const more=event.target.closest('[data-more]');if(more){if(more.dataset.more==='dex')state.limit+=24;else if(more.dataset.more==='locations')state.locationLimit+=12;else if(more.dataset.more==='updates')state.updateLimit+=24;else if(more.dataset.more==='trainers')state.trainerLimit+=24;else state.moveLimit+=40;updateResults();return;}
  const reset=event.target.closest('[data-reset]');if(reset){state=initial();render(false);}
});
main.addEventListener('input',event=>{
  const input=event.target;if(!input.dataset.search)return;
  if(input.dataset.search==='dex'){state.q=input.value;state.limit=24;}
  else if(input.dataset.search==='locations'){state.locationQ=input.value;state.locationLimit=12;}
  else if(input.dataset.search==='updates'){state.updateQ=input.value;state.updateLimit=24;}
  else if(input.dataset.search==='trainers'){state.trainerQ=input.value;state.trainerLimit=24;}
  else{state.moveQ=input.value;state.moveLimit=40;}
  updateResults();
});
function updateTrainerLevel(value){const url=new URL(location.href);url.searchParams.set('nivel',String(Math.min(100,Math.max(1,Math.trunc(Number(value))||50))));history.replaceState({},'',url);render(false);}
main.addEventListener('keydown',event=>{if(event.target.dataset.select==='trainerLevel'&&event.key==='Enter'){event.preventDefault();updateTrainerLevel(event.target.value);}});
main.addEventListener('change',event=>{
  const key=event.target.dataset.select;if(!key)return;state[key]=event.target.value;
  if(key==='version')render(false);
  else if(key==='trainerVariant'){const url=new URL(location.href);url.searchParams.set('modo',state.trainerVariant);history.replaceState({},'',url);render(false);}
  else if(key==='trainerLevel')updateTrainerLevel(state.trainerLevel);
  else if(key==='trainerArea'){state.trainerLimit=24;updateResults();}
  else if(key==='form'){const url=new URL(location.href);if(state.form)url.searchParams.set('forma',state.form);else url.searchParams.delete('forma');history.replaceState({},'',url);render(false);}
  else{state.limit=24;state.locationLimit=12;updateResults();}
});
document.addEventListener('error',event=>{const image=event.target;if(image.tagName!=='IMG')return;if(image.dataset.fallback){const fallback=image.dataset.fallback;delete image.dataset.fallback;image.src=fallback;}else{image.classList.add('image-unavailable');image.alt=image.alt||'Imagem indisponível';}},true);
document.getElementById('menu-toggle').addEventListener('click',()=>{const nav=document.getElementById('nav');nav.classList.toggle('open');document.getElementById('menu-toggle').setAttribute('aria-expanded',String(nav.classList.contains('open')));});
window.addEventListener('popstate',()=>render(true));
try{model=await loadPortal();await render();}catch(error){main.innerHTML=`<div class="container">${empty('O arquivo não abriu desta vez.','Não foi possível carregar os dados do portal.')}<div class="load-more"><button class="button button-primary" id="reload-page">Tentar novamente ${icon('arrow')}</button></div></div>`;document.getElementById('reload-page').addEventListener('click',()=>location.reload());}
