import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gameDownload,hubDownload,downloadStrip,downloadsPage} from '../src/assets/downloads.js';
test('downloads usam a main e o último pacote do Hub, com instalação dos dois modos',()=>{
  assert.ok(gameDownload.endsWith('/archive/refs/heads/main.zip'));
  assert.ok(hubDownload.endsWith('/releases/latest/download/Blue-Battle-Hub.zip'));
  for(const html of [downloadStrip(),downloadsPage()]){assert.ok(html.includes(gameDownload));assert.ok(html.includes(hubDownload));}
  const html=downloadsPage();
  for(const filename of ['INSTALAR_JOGO.bat','ABRIR_JOGO.bat','INSTALAR_HUB.bat','HUB_DE_BATALHA.bat'])assert.ok(html.includes(filename));
  assert.equal((html.match(/<ol>/g)||[]).length,2);
  assert.ok(html.includes('base Pokémon Decades separadamente'));
});
test('downloads ficam acessíveis pela navegação e pela página inicial',()=>{
  const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
  assert.ok(read('../src/index.html').includes('href="/downloads"'));
  assert.ok(read('../src/assets/views.js').includes('${downloadStrip()}'));
  assert.ok(read('../src/assets/app.js').includes("route==='downloads'"));
});
