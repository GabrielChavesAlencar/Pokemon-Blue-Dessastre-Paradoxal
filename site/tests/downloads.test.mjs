import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {gameDownload,hubDownload,androidDownload,joiplayDownload,downloadStrip,downloadsPage} from '../src/assets/downloads.js';
test('downloads usam a main e o último pacote do Hub, com instalação dos dois modos',()=>{
  assert.ok(gameDownload.endsWith('/releases/download/blue-story-windows/Blue-Story.exe'));
  assert.ok(hubDownload.endsWith('/releases/latest/download/Blue-Battle-Hub.exe'));
  for(const html of [downloadStrip(),downloadsPage()]){assert.ok(html.includes(gameDownload));assert.ok(html.includes(hubDownload));}
  const html=downloadsPage();
  assert.doesNotMatch(html,/\.bat|RUN\.bat|archive\/refs\/heads/);
  assert.ok(html.includes(androidDownload));
  assert.match(html,/Novo Jogo/);assert.match(html,/Kanto/);
  assert.match(html,/integrar automaticamente Kanto e Hoenn/);
  assert.match(html,/ZIP privado de Johto/);
  assert.match(html,/mesmo Game.exe e perfil de saves/);
  assert.match(html,/Testar Kanto, Johto, Hoenn e Sinnoh/);
  assert.match(html,/instalação antiga incompatível/);
  assert.match(html,/Android reais/);
  assert.equal(joiplayDownload,'https://www.joiplay.net/');
  assert.ok(html.includes(`href="${joiplayDownload}"`));
  assert.ok(html.includes('Baixar JoiPlay · site oficial'));
  assert.ok(html.includes('android-download-actions'));
  assert.match(html,/Baixar pilotos · Android/);
  assert.match(html,/data-android-multiregion/);
  assert.match(html,/Decades \+ Kanto \+ Hoenn/);
  assert.doesNotMatch(html,/href="[^"]*Blue-Android-Decades-Kanto-Hoenn\.zip"/);
  assert.match(html,/data-android-pilots/);
  assert.match(html,/data-windows-pilots/);
  assert.doesNotMatch(html,/href="[^"]*Blue-Android-(Kanto|Johto)-Piloto[.]zip"/);

  assert.ok(html.includes('RPG Maker Plugin'));
  assert.match(html,/Python ou Git/);assert.match(html,/cópias portáteis verificadas/);
  assert.equal((html.match(/<ol(?:\s[^>]*)?>/g)||[]).length,3);
  assert.ok(html.includes('130 times prontos'));
  assert.match(html,/Configurações → Teclas → Editar/);
  assert.match(html,/WASD funciona/);
  assert.match(html,/nenhuma tecla F é necessária/);
});
test('downloads ficam acessíveis pela navegação e pela página inicial',()=>{
  const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
  assert.ok(read('../src/index.html').includes('href="/downloads"'));
  assert.ok(read('../src/assets/views.js').includes('${downloadStrip()}'));
  assert.ok(read('../src/assets/app.js').includes("route==='downloads'"));
});
