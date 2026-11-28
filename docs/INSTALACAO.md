# Baixar e instalar Pokémon Blue

Abra [Downloads](https://pokemondessastreparadosal.vercel.app/downloads) e escolha **Blue-Story.exe** para a campanha ou **Blue-Battle-Hub.exe** para a arena. Use Windows 10/11 de 64 bits.

1. Abra o EXE escolhido. A primeira instalação baixa a base e as modificações do projeto.
2. Aguarde a preparação e a compilação. Python e Git portáteis são obtidos automaticamente, com verificação SHA-256; não é necessário instalá-los no Windows.
3. Jogue. O inicializador confere a main pública ao abrir e atualiza os scripts quando existe uma revisão nova.

Os dois EXEs usam uma instalação compartilhada. Em um PC novo, ela fica em `%LOCALAPPDATA%/PokemonBlueDessastreParadoxal`. Quando o inicializador está dentro de uma instalação existente, reconhece a pasta do projeto. Feche o jogo antes de atualizar. Saves, equipes, `game/` e ferramentas privadas são preservados na atualização do código; arquivos substituídos recebem backup.

## Kanto automático no instalador do site (Windows)

O **Blue-Story.exe** da página de downloads confere a `main` ao abrir e executa o instalador normal `scripts/install_game.py --apply`. **Esse fluxo agora integra automaticamente Kanto ao Decades principal**; não é preciso executar `KANTO_INSTALAR_NO_JOGO.bat` manualmente.

Na primeira instalação com internet, após preparar a base Decades/Blue, o instalador:

1. Obtém a fonte editável FRLG no endereço do autor original, a partir da versão fixada no manifesto. Valida o **SHA-256 antes de extrair** e só aceita mapas, PBS e gráficos permitidos (nunca executáveis/scripts da fonte).
2. Monta e audita o **catálogo regional (178 MapIDs em K05/K06)** em `.blue-work`, preservando IDs e recusando colisões; grava os arquivos regionais em `game/` com backup/rollback.
3. Atualiza os plugins Blue, mescla as traduções de Kanto com as originais de Decades e solicita recompilação dos dados do Essentials.
4. Abre o **mesmo Game.exe**. Em **Novo Jogo**, selecione **Kanto** para começar na casa de Pallet ou **Decades** para manter a campanha original. Os saves existentes não são migrados nem excluídos.

**Em atualizações posteriores**, o instalador reconhece o pacote já integrado, verifica seus arquivos e pode atualizar o **plugin Ruby próprio de Kanto** quando o hash corresponder ao instalado anteriormente. As migrações autorizadas podem atualizar arquivos de Kanto verificados, preservando os MapIDs e recusando arquivos locais modificados. No primeiro lote K06, a alteração se limita aos sete mapas da passagem para Celadon. O procedimento de migração de instalações antigas com 13/25 mapas continua bloqueado, para não corromper saves.

**Falha de download/offline?** O **Blue-Story.exe não declara mais a instalação completa** quando Kanto está ausente. Ele interrompe a conclusão, informa que é necessário tentar novamente e salva os detalhes em `.blue-work/kanto-install-status.json` e `.blue-work/kanto-install.log`. A instalação e os saves de **Decades permanecem preservados**. O download tenta dois endpoints do mesmo arquivo FRLG, sempre exigindo o SHA-256 fixado; também pode reutilizar o piloto Kanto em cache. Se já existirem 13/25 mapas, uma atualização automática destrutiva continua bloqueada. Consulte [KANTO_INTEGRACAO_DECADES.md](KANTO_INTEGRACAO_DECADES.md). O pacote Android/JoiPlay permanece separado e não recebe essa montagem automática do EXE Windows.

A opção **Testar Kanto** continua disponível para o piloto isolado, com saves separados. A integração automática não equivale a uma aprovação jogável dos mapas/eventos: a campanha principal ainda precisa passar por testes reais no Game.exe.

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

**Kanto/Hoenn multirregional:** use o [atualizador pela fonte original](ANDROID_K06_ATUALIZACAO_PELA_FONTE.md) da receita Kanto publicada. Não instale o ZIP de Decades por cima da edição multirregional. A compilação é local e a receita não redistribui os arquivos do jogo.

**Decades, sem a edição multirregional:** baixe **Blue-Android-JoiPlay.zip**, instale JoiPlay e RPG Maker Plugin pelos [downloads oficiais](https://www.joiplay.net/), extraia o ZIP inteiro e adicione `Pokemon-Blue-Android/Game.exe` ao JoiPlay. Na abertura, escolha História ou Hub offline. O pacote já contém os dados compilados e as músicas.

É um pacote para o interpretador, não um APK nativo. Ainda requer validação em aparelhos Android reais. O multiplayer e o download de links PokéPaste usam o auxiliar Windows; no Android, utilize os times prontos ou o texto do time.

## Desenvolvimento e verificação

Os arquivos BAT continuam disponíveis no código-fonte para manutenção e instalações antigas. A página pública de downloads usa os EXEs. `RUN.bat` abre o editor, e `ABRIR_SITE.bat` abre o portal local com Node.

O build testa extração segura, proteção dos arquivos existentes, instalação sem Python/Git no PATH, hashes dos áudios, importação dos times, recompilação nativa e exclusão de saves/logs do pacote Android. Consulte [Distribuição e presets](DISTRIBUICAO_E_PRESETS.md) e [Álbum e mapas](ALBUM_E_MAPAS.md).
