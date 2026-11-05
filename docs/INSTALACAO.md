# Baixar e instalar Pokémon Blue

Abra [Downloads](https://pokemondessastreparadosal.vercel.app/downloads) e escolha **Blue-Story.exe** para a campanha ou **Blue-Battle-Hub.exe** para a arena. Use Windows 10/11 de 64 bits.

1. Abra o EXE escolhido. A primeira instalação baixa a base e as modificações do projeto.
2. Aguarde a preparação e a compilação. Python e Git portáteis são obtidos automaticamente, com verificação SHA-256; não é necessário instalá-los no Windows.
3. Jogue. O inicializador confere a main pública ao abrir e atualiza os scripts quando existe uma revisão nova.

Os dois EXEs usam uma instalação compartilhada. Em um PC novo, ela fica em `%LOCALAPPDATA%/PokemonBlueDessastreParadoxal`. Quando o inicializador está dentro de uma instalação existente, reconhece a pasta do projeto. Feche o jogo antes de atualizar. Saves, equipes, `game/` e ferramentas privadas são preservados na atualização do código; arquivos substituídos recebem backup.

## Conteúdo instalado

- Base Decades no commit fixado `ff6091b23603b3298ad72a7584b02a51e1d01c0e`.
- Regras oficiais do projeto, geração Dessastre Paradoxal, sprites, cries, descrições e pedras autorais.
- Campanha Blue, IA, opções de mecânicas, controles por mouse e Hub com multiplayer.
- 130 times prontos por jogo/regulamento, disponíveis sem internet.
- As mesmas listas compartilhadas de música: 12 faixas de treinador, 8 selvagens e 9 de líderes.

## Configurar o teclado no Windows (sem setas e sem F1–F12)

No **Modo História** ou no **Hub de Batalha**, abra **Configurações → Teclas → Editar**. A tela permite atribuir outras teclas a cada ação (movimento, confirmar, cancelar, menu, navegação entre páginas e itens registrados). Escolha uma ação, selecione **Replace new key** ou **Add key**, pressione a tecla desejada e confirme **Keep changes?** ao sair. **Default** restaura os controles.

Os dois conjuntos de movimento já estão disponíveis desde a primeira abertura: **W/A/S/D** e as **setas**. Para evitar conflitos com WASD, os padrões de rolagem passam a ser **Q/E**, e o menu de itens registrados fica em **R**. **Enter/Espaço/C** confirmam, **X/Esc** cancelam e **Z/Shift** abrem o menu. É possível trocar todas essas teclas sem usar F1, F2 ou qualquer tecla de função.

As escolhas ficam salvas separadamente dos saves em `blue-keyboard-controls.txt`, no diretório de dados do usuário utilizado pelo motor. São compartilhadas entre História e Hub. O jogo continua com o menu de controles acessível no próprio menu de opções. Ao baixar uma atualização, a pasta do usuário e os saves são preservados.

## Android experimental

Baixe **Blue-Android-JoiPlay.zip**, instale JoiPlay e RPG Maker Plugin pelos [downloads oficiais](https://www.joiplay.net/), extraia o ZIP inteiro e adicione `Pokemon-Blue-Android/Game.exe` ao JoiPlay. Na abertura, escolha História ou Hub offline. O pacote já contém os dados compilados e as músicas.

É um pacote para o interpretador, não um APK nativo. Ainda requer validação em aparelhos Android reais. O multiplayer e o download de links PokéPaste usam o auxiliar Windows; no Android, utilize os times prontos ou o texto do time.

## Desenvolvimento e verificação

Os arquivos BAT continuam disponíveis no código-fonte para manutenção e instalações antigas. A página pública de downloads usa os EXEs. `RUN.bat` abre o editor, e `ABRIR_SITE.bat` abre o portal local com Node.

O build testa extração segura, proteção dos arquivos existentes, instalação sem Python/Git no PATH, hashes dos áudios, importação dos times, recompilação nativa e exclusão de saves/logs do pacote Android. Consulte [Distribuição e presets](DISTRIBUICAO_E_PRESETS.md) e [Álbum e mapas](ALBUM_E_MAPAS.md).
