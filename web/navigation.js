/* Blue Studio navigation, adapted from Emerald Studio tabs; no GBA ROM editing is simulated. */
(function () {
  "use strict";
  const byId = id => document.getElementById(id);
  const panels = {
    "project": ["📁", "Projeto", "Base local: Pokémon Decades, motor RPG Maker XP / Pokémon Essentials v21.1.", "Exibir versão, arquivos encontrados e validar a instalação local.", "estrutura"],
    "script": ["📜", "História e eventos", "Eventos e diálogos são definidos nos mapas do RPG Maker XP; não são ROMs binárias de GBA.", "Criar visualizador de eventos RGSS e depois editor compatível com arquivos do RPG Maker XP.", "planejado"],
    "flags": ["🚩", "Flags e vars", "Variáveis e switches de eventos dependem do banco de dados do RPG Maker XP.", "Ler o catálogo de switches/variables de Data e adicionar referências cruzadas.", "planejado"],
    "pokemon": ["🐉", "Pokédex", "Editor PBS de espécies, atributos, habilidades e formas.", "Adicionar fichas visuais de Fakémon e validação de espécies.", "pbs", "pokemon.txt"],
    "pokemon-moves": ["⚔️", "Golpes dos Pokémon", "Editor de golpes por nível, tutor e ovo.", "Salve os Moves, TutorMoves e EggMoves no PBS original.", "custom"],
    "items": ["🎒", "Itens", "Editor PBS de itens e Mega Stones.", "Adicionar categorização por bolso, ícones e validações específicas de itens.", "pbs", "items.txt"],
    "starters": ["⭐", "Iniciais", "Inicialização dos Pokémon e eventos iniciais depende dos scripts e mapas.", "Indexar os eventos iniciais do projeto e criar editor guiado de starters.", "planejado"],
    "trainers": ["⚔️", "Treinadores", "Editor PBS de equipes, níveis, itens e golpes de treinadores.", "Criar formulários visuais com retratos, validação de equipes e dificuldades.", "pbs", "trainers_story_mode.txt"],
    "wild": ["🌿", "Selvagens", "Editor PBS de encontros por mapa, dia e noite.", "Adicionar tabela de probabilidades, mapa visual e teste de encontros.", "pbs", "encounters.txt"],
    "map": ["🗺️", "Mapas", "A edição de terrenos e eventos usa Game.rxproj / Data do RPG Maker XP.", "Implementar visualizador seguro de MapXXX.rxdata e editor de tiles em fase posterior.", "planejado"],
    "title-logo": ["🖼️", "Logo inicial", "Tela inicial e imagens do jogo são recursos locais do projeto Essentials.", "Encontrar recursos de título e adicionar importação com prévia e backup.", "planejado"],
    "title-flames": ["🔥", "Fundo animado", "No Decades não há a mesma animação binária de chamas do Radical Red.", "Criar um sistema de efeitos próprios (ex.: raios azuis) sem depender de offsets GBA.", "planejado"],
    "music": ["🎵", "Músicas", "Biblioteca de áudio com prévia e configuração de batalhas e cidades.", "Importe uma faixa ou escolha um destino para aplicar.", "music"],
    "midi-studio": ["🎹", "Estúdio MIDI", "A aba do Emerald Studio está representada na navegação.", "Implementar importação/exportação MIDI, instrumentos e testes de reprodução.", "planejado"],
    "test-lab": ["🧪", "Test Lab", "Os testes automáticos de software rodam no GitHub Actions; testes dentro do jogo ainda não estão integrados.", "Adicionar cenários de inicialização, captura, batalha e regressão do Essentials.", "planejado"],
    "hex": ["🔢", "Hexadecimal", "Offsets e patches de ROM GBA não se aplicam diretamente a RPG Maker XP.", "Criar inspetor somente leitura de arquivos e esquema de dados do Essentials.", "planejado"],
    "table": ["📋", "Tabelas técnicas", "Tabelas de dados serão construídas sobre PBS em vez de offsets binários.", "Adicionar relacionamentos entre espécies, formas, golpes e habilidades.", "planejado"],
    "graphics": ["🖼️", "Gráficos 4bpp", "Imagens do Essentials usam PNG e outros recursos, não gráficos 4bpp de GBA.", "Adicionar visualizador de sprites PNG com opções de redimensionamento seguro.", "planejado"],
    "sprite": ["🎨", "Importar sprites", "Prévia de sprites já aparece na edição PBS; importação ainda não está implementada.", "Adicionar upload, pivot, sprites normal/shiny, frente/costas e validação de dimensões.", "planejado"],
    "text": ["📝", "Textos Pokémon", "Textos do jogo serão editados por arquivos e mensagens do Essentials.", "Criar pesquisa global e tradução com backups.", "planejado"],
    "patch": ["🩹", "Patch e cabeçalho", "Patches BPS e cabeçalhos GBA pertencem ao editor do Radical Red.", "Criar exportação de modificações do projeto sem redistribuir o Decades original.", "planejado"]
  };
  let currentShell = "rom";
  let currentPanel = "pokemon";
  function announce(message) {
    const el = byId("navNotice");
    if (el) el.textContent = message;
  }
  function selectShell(which, writeHash) {
    if (!["home","rom","movesets"].includes(which)) which = "rom";
    currentShell = which;
    byId("studioHome").hidden = which !== "home";
    byId("romStudio").hidden = which !== "rom";
    byId("movesetPanel").hidden = which !== "movesets";
    document.querySelectorAll("[data-shell]").forEach(button => {
      const active = button.dataset.shell === which;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
    });
    if (writeHash) location.hash = which === "rom" ? "#rom/" + currentPanel : "#" + which;
  }
  async function selectPanel(which, writeHash) {
    if (!Object.prototype.hasOwnProperty.call(panels, which)) which = "pokemon";
    const data = panels[which];
    const file = data[5];
    const musicAlreadyOpen = currentShell === "rom" && currentPanel === "music" &&
      which === "music" && !byId("musicWorkspace").hidden;
    if (currentPanel === "pokemon-moves" && which !== "pokemon-moves" &&
        window.BluePokemonMoves && !window.BluePokemonMoves.canLeave()) return;
    if (currentPanel === "music" && which !== "music" && window.BlueMusic && !window.BlueMusic.canLeave()) return;
    // When changing PBS files, never discard unsaved text without confirmation.
    if (file && typeof state !== "undefined" && state.raw !== state.original &&
        state.file !== file) {
      if (!confirm("Descartar alterações PBS não salvas para trocar de aba?")) return;
      state.original = state.raw;
    }
    currentPanel = which;
    document.querySelectorAll("[data-panel]").forEach(button => {
      const active = button.dataset.panel === which;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
    });
    selectShell("rom", false);
    const work = byId("pbsWorkspace"), placeholder = byId("featurePanel");
    const movesWork = byId("movesWorkspace");
    const ready = data[4] === "pbs";
    const movesMode = which === "pokemon-moves";
    const musicMode = which === "music";
    work.hidden = !ready;
    movesWork.hidden = !movesMode;
    byId("musicWorkspace").hidden = !musicMode;
    placeholder.hidden = ready || movesMode || musicMode;
    if (movesMode) {
      window.BluePokemonMoves?.open();
    } else if (musicMode) {
      if (!musicAlreadyOpen) window.BlueMusic?.open();
    } else if (!ready) {
      byId("featureIcon").textContent = data[0];
      byId("featureTitle").textContent = data[1];
      byId("featureDescription").textContent = data[2];
      byId("featureNext").textContent = data[3];
      byId("featureStatus").textContent = data[4] === "estrutura" ? "ESTRUTURA PRONTA · CONFIGURAÇÃO PENDENTE" : "PLANEJADO · AINDA NÃO FUNCIONAL";
    } else if (typeof refresh === "function" && typeof openFile === "function") {
      try {
        await refresh();
        if (currentPanel !== which) return;
        const available = state.files.find(x => x.name.toLowerCase() === file.toLowerCase());
        if (available && state.file !== available.name) await openFile(available.name);
        if (!available) announce("Arquivo " + file + " indisponível. Importe a base Decades.");
      } catch (error) {
        console.error("Falha ao abrir arquivo PBS:", error);
      }
    }
    if (writeHash) location.hash = "#rom/" + which;
  }
  function routeHash() {
    const hash = decodeURIComponent(location.hash.slice(1));
    if (hash === "home" || hash === "movesets") selectShell(hash, false);
    else selectPanel(hash.startsWith("rom/") ? hash.slice(4) : "pokemon", false);
  }
  document.querySelectorAll("[data-shell]").forEach(button => button.addEventListener("click", () => {
    if (currentShell === "rom" && currentPanel === "pokemon-moves" && button.dataset.shell !== "rom" &&
        window.BluePokemonMoves && !window.BluePokemonMoves.canLeave()) return;
    if (currentShell === "rom" && currentPanel === "music" && button.dataset.shell !== "rom" && window.BlueMusic && !window.BlueMusic.canLeave()) return;
    selectShell(button.dataset.shell, true);
  }));
  document.querySelectorAll("[data-panel]").forEach(button => button.addEventListener("click", () => selectPanel(button.dataset.panel, true)));
  document.querySelectorAll("[data-shortcut]").forEach(button => button.addEventListener("click", () => selectPanel(button.dataset.shortcut, true)));
  window.addEventListener("hashchange", routeHash);
  routeHash();
  window.BlueStudioNavigation = { panels: Object.keys(panels), open: selectPanel };
}());
