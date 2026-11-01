/* Local music library and battle/city assignments. */
(() => {
  'use strict';
  const root=document.getElementById('musicWorkspace');
  const state={model:null,selected:null,assignment:null,dirty:false,busy:false,request:0};
  const $=id=>root.querySelector('#'+id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function api(path,body){
    const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json','X-Blue-Studio':'1'},body:JSON.stringify(body)}:{});
    const data=await response.json();if(!response.ok)throw Error(data.error||'Não foi possível concluir a operação.');return data;
  }
  function notice(message,error=false){$('musicNotice').textContent=message;$('musicNotice').classList.toggle('music-error',error);}
  function dirty(value=true){state.dirty=value;$('musicSave').disabled=!value||state.busy||!state.assignment;$('musicUnsaved').textContent=value?'Alterações ainda não aplicadas':'Configuração atual';}
  function busy(value){state.busy=value;$('musicSave').disabled=value||!state.dirty||!state.assignment;$('musicImport').disabled=value;}
  function setup(){
    if(root.dataset.ready)return;
    root.dataset.ready='1';root.innerHTML=`<header class="music-header"><div><div class="eyebrow">ÁUDIO DO JOGO</div><h1>Músicas <strong>do Blue</strong></h1><p>Ouça sua biblioteca e escolha as músicas das batalhas e das cidades.</p></div><button id="musicReload" class="btn btn-ghost">↻ Atualizar biblioteca</button></header>
      <div id="musicNotice" class="music-notice" role="status" aria-live="polite">Carregando biblioteca…</div>
      <div class="music-columns"><section class="card music-library"><div class="cardhead"><div><div class="eyebrow">BIBLIOTECA LOCAL</div><h2>Faixas disponíveis</h2></div><span id="musicCount"></span></div><input id="musicSearch" type="search" placeholder="Buscar música…" aria-label="Buscar música"><div id="musicTracks" class="music-tracks"></div>
      <div class="music-listen"><b id="musicSelected">Selecione uma faixa</b><audio id="musicPreview" controls preload="none" aria-label="Prévia da música"></audio><p id="musicPreviewNote"></p><button id="musicUse" class="btn btn-ghost" disabled>Usar esta faixa</button></div></section>
      <div class="music-right"><section class="card music-assignment"><div class="cardhead"><div><div class="eyebrow">ONDE TOCAR</div><h2>Batalhas e cidades</h2></div><span id="musicUnsaved">Configuração atual</span></div>
      <div class="music-form"><label>Categoria<select id="musicScope"><option value="global">Batalhas</option><option value="map">Cidade / mapa</option></select></label><label>Destino<select id="musicTarget"></select></label><p id="musicOriginal" class="music-hint"></p>
      <label>Reprodução<select id="musicMode"><option value="original">Música original do jogo</option><option value="custom">Escolher uma faixa</option><option value="mute">Sem música</option></select></label><label>Faixa<select id="musicTrack" disabled></select></label>
      <label>Volume <output id="musicVolumeValue">100%</output><input id="musicVolume" type="range" min="0" max="100" value="100" disabled></label><label>Tom / velocidade <output id="musicPitchValue">100%</output><input id="musicPitch" type="range" min="50" max="150" value="100" disabled></label>
      <button id="musicSave" class="btn btn-primary" disabled>Aplicar música</button><p class="music-hint">As mudanças ficam disponíveis ao reabrir o jogo. Eventos da história podem escolher uma música própria.</p></div></section>
      <section class="card music-import"><div class="cardhead"><div><div class="eyebrow">SUA TRILHA SONORA</div><h2>Importar ou substituir</h2></div></div><div class="music-form"><label>Arquivo de áudio<input id="musicUpload" type="file" accept=".ogg,.wav,.mp3,.mid,.midi"></label><label>Nome na biblioteca<input id="musicFilename" type="text" placeholder="Minha música.ogg"></label><label class="music-check"><input id="musicReplace" type="checkbox">Substituir a faixa selecionada</label><p id="musicReplaceHint" class="music-hint" hidden>Isso afeta todos os locais que já usam esse arquivo. O arquivo anterior recebe um backup.</p><p class="music-hint">WAV, OGG, MP3 ou MIDI, até 20 MB. MIDI é reproduzido no jogo; sua prévia não está disponível no navegador.</p><button id="musicImport" class="btn btn-primary">Importar áudio</button></div></section></div></div>`;
    $('musicSearch').addEventListener('input',renderTracks);
    $('musicReload').addEventListener('click',()=>{if(canLeave())open();});
    $('musicScope').addEventListener('change',()=>{if(!confirmDraft()){$('musicScope').value=state.assignment?.scope||'global';return;}targets();loadAssignment();});
    $('musicTarget').addEventListener('change',()=>{if(confirmDraft())loadAssignment();else $('musicTarget').value=state.assignment?.target||'';});
    ['musicMode','musicTrack','musicVolume','musicPitch'].forEach(id=>$(id).addEventListener('input',()=>{controls();dirty();}));
    $('musicTracks').addEventListener('click',event=>{const button=event.target.closest('[data-music-track]');if(button)selectTrack(button.dataset.musicTrack);});
    $('musicUse').addEventListener('click',()=>{if(!state.selected)return;$('musicMode').value='custom';$('musicTrack').value=state.selected.id;controls();dirty();});
    $('musicSave').addEventListener('click',save);
    $('musicUpload').addEventListener('change',()=>{const file=$('musicUpload').files[0];if(file&&!$('musicReplace').checked)$('musicFilename').value=file.name;});
    $('musicReplace').addEventListener('change',replacement);
    $('musicImport').addEventListener('click',upload);
  }
  function confirmDraft(){return !state.dirty||window.confirm('Descartar a configuração de música ainda não aplicada?');}
  function controls(){
    const custom=$('musicMode').value==='custom';
    ['musicTrack','musicVolume','musicPitch'].forEach(id=>$(id).disabled=!custom);
    $('musicVolumeValue').textContent=$('musicVolume').value+'%';$('musicPitchValue').textContent=$('musicPitch').value+'%';
    $('musicPreview').volume=Number($('musicVolume').value)/100;
    $('musicPreview').preservesPitch=false;$('musicPreview').playbackRate=Number($('musicPitch').value)/100;
  }
  function targets(){
    const maps=$('musicScope').value==='map';const list=maps?state.model.maps:state.model.global;
    $('musicTarget').innerHTML=list.map(p=>`<option value="${esc(p.id)}">${esc(p.name)}${maps?' · #'+p.id:''}</option>`).join('');
  }
  function renderTracks(){
    if(!state.model)return;
    const term=$('musicSearch').value.toLocaleLowerCase();const list=state.model.tracks.filter(t=>t.id.toLocaleLowerCase().includes(term));
    $('musicCount').textContent=list.length+' faixas';
    $('musicTracks').innerHTML=list.length?list.map(t=>`<button class="music-track ${state.selected?.id===t.id?'active':''}" data-music-track="${esc(t.id)}" type="button"><b>${esc(t.name)}</b><small>${esc(t.id)} · ${(t.size/1_000_000).toFixed(2)} MB</small></button>`).join(''):'<p class="music-hint">Nenhuma faixa encontrada. Você pode importar um áudio abaixo.</p>';
  }
  function replacement(){
    const replace=$('musicReplace').checked;$('musicFilename').disabled=replace;$('musicReplaceHint').hidden=!replace;
    if(replace)$('musicFilename').value=state.selected?.id||'';
    else $('musicFilename').value=$('musicUpload').files[0]?.name||'';
  }
  async function selectTrack(id){
    const track=state.model.tracks.find(t=>t.id===id);if(!track)return;
    try{
      const response=await fetch('/api/music/track?id='+encodeURIComponent(id));const info=await response.json();
      if(!response.ok&&response.status!==413)throw Error(info.error);
      state.selected={...track,...(response.ok?info:{})};$('musicSelected').textContent=track.name;$('musicUse').disabled=false;
      const audio=$('musicPreview');audio.pause();audio.hidden=!track.preview;
      if(track.preview)audio.src='/api/music/audio?id='+encodeURIComponent(id);else {audio.removeAttribute('src');audio.load();}
      $('musicPreviewNote').textContent=track.preview?'A prévia usa o volume e o tom selecionados ao lado.':'MIDI: teste a reprodução no jogo.';
      renderTracks();replacement();
    }catch(error){notice(error.message,true);}
  }
  async function loadAssignment(){
    const request=++state.request;state.assignment=null;dirty(false);
    if(!$('musicTarget').value){notice('Não há mapas disponíveis nessa base.');return;}
    try{
      const value=await api('/api/music/assignment?scope='+encodeURIComponent($('musicScope').value)+'&target='+encodeURIComponent($('musicTarget').value));
      if(request!==state.request)return;
      state.assignment=value;const selected=value.value;
      $('musicMode').value=selected?.mode||'original';$('musicTrack').value=selected?.track||state.selected?.id||state.model.tracks[0]?.id||'';
      $('musicVolume').value=selected?.volume??100;$('musicPitch').value=selected?.pitch??100;
      $('musicOriginal').textContent='Original: '+(value.original.track||'definida pela base/eventos')+(value.original.enabled?'':' · sem reprodução automática');
      controls();dirty(false);
    }catch(error){notice(error.message,true);}
  }
  async function open(){
    setup();busy(true);
    try{
      const selected=state.selected?.id;state.model=await api('/api/music/catalog');
      $('musicTrack').innerHTML=state.model.tracks.map(t=>`<option value="${esc(t.id)}">${esc(t.id)}</option>`).join('');
      targets();renderTracks();await loadAssignment();
      if(selected&&state.model.tracks.some(t=>t.id===selected))await selectTrack(selected);
      notice('Biblioteca pronta. Escolha onde a música deve tocar.');
    }catch(error){notice(error.message,true);}finally{busy(false);}
  }
  async function save(){
    const a=state.assignment;if(!a)return;busy(true);
    try{
      const result=await api('/api/music/assignment',{scope:a.scope,target:a.target,hash:a.hash,mode:$('musicMode').value,track:$('musicTrack').value,volume:Number($('musicVolume').value),pitch:Number($('musicPitch').value)});
      a.hash=result.hash;a.value=result.value;dirty(false);notice(result.message);
    }catch(error){notice(error.message,true);}finally{busy(false);}
  }
  async function upload(){
    const file=$('musicUpload').files[0];if(!file){notice('Escolha um arquivo de áudio.',true);return;}
    if(file.size>20_000_000){notice('O arquivo ultrapassa 20 MB.',true);return;}
    const replace=$('musicReplace').checked;
    if(replace&&!state.selected?.hash){notice('Selecione uma faixa de até 20 MB para substituir.',true);return;}
    busy(true);
    try{
      const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
      for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));
      const result=await api('/api/music/upload',{filename:replace?state.selected.id:$('musicFilename').value.trim(),mode:replace?'replace':'create',hash:replace?state.selected.hash:'',data:btoa(binary)});
      const chosen=$('musicTrack').value;
      state.model=await api('/api/music/catalog');$('musicTrack').innerHTML=state.model.tracks.map(t=>`<option value="${esc(t.id)}">${esc(t.id)}</option>`).join('');
      if(state.model.tracks.some(t=>t.id===chosen))$('musicTrack').value=chosen;
      renderTracks();await selectTrack(result.id);notice(result.replaced?'Faixa substituída. O arquivo anterior recebeu um backup.':'Áudio importado. Use esta faixa no destino desejado.');
      $('musicUpload').value='';
    }catch(error){notice(error.message,true);}finally{busy(false);}
  }
  function canLeave(){
    if(!confirmDraft())return false;
    $('musicPreview')?.pause();return true;
  }
  window.BlueMusic={open,canLeave};
})();
