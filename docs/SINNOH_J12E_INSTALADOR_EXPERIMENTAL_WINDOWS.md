# Sinnoh — Instalador experimental Windows (J12-E)

**Objetivo:** instalar os NOVE mapas originais gerados pelo projeto em uma **cópia privada QA** do Pokémon Blue, sem modificar o jogo instalado ou seus saves. Este instalador é **experimental e requer o jogo original já instalado no seu Windows**. Não inclui Game.exe, ROM, mídia, dados privados nem saves.

## Como usar no Windows

1. Baixe o artifact **Sinnoh Experimental Windows Installer (sources-only)** do workflow CI J12-E (ou baixe o código do repositório após a aprovação e merge). Extraia em uma pasta normal com permissão de gravação, fora da instalação do jogo.
2. Requer **Windows 10/11 e Python 3.11+**, com o launcher `py -3` disponível.
3. Dê duplo clique em **`SINNOH_EXPERIMENTAL_INSTALAR_WINDOWS.bat`**. O instalador detecta `%LOCALAPPDATA%\PokemonBlueDessastreParadoxal\game`. Se a instalação estiver em outra pasta, informe-a quando solicitado. Não execute dentro da pasta `game`.
4. O instalador lê apenas os arquivos do jogo, valida MapInfos e Tilesets, inventaria MapIDs ocupados nos mapas e PBS, seleciona **nove IDs temporários sem colisão dentro de 442–517**, gera nove RXDATA originais, dois `RPG::Tileset` e sprites autorais, prepara 16 warps / cinco NPCs / três Poké Bolas com coordenadas derivadas da própria geometria e testa passabilidade **estática**. Também valida as versões de Barry a partir do PBS local.
5. A cópia é criada em **`.blue-work/game-sinnoh-experimental-<token>`**, com `Game.exe`, gráficos, scripts, plugins e PBS herdados **somente como cópia** e `mkxp.json`/`Game.ini` com namespace de save exclusivo.
6. Dentro dessa nova pasta, duplo clique **`INICIAR_SINNOH_EXPERIMENTAL.bat`**. O primeiro início deve compilar os arquivos PBS do Barry no Game.exe da CÓPIA; o launcher só abre o jogo quando existir o marcador de compilação gerado pela engine. Se a compilação ou inicialização falhar, inspecione `Data/sinnoh-experimental-compile-error.txt` (não execute o Game.exe original).
7. Teste **Novo Jogo**. A cópia tenta começar no quarto de Sinnoh, permitir caminhar pelos mapas, entrar nos interiores, conversar com personagens e escolher o inicial. **Isso ainda não foi comprovado pela QA nativa**; reporte crashes, eventos inacessíveis e imagens faltando sem usar seus saves principais.

Alternativa para verificar sem copiar nada:

    py -3 scripts\regions\install_sinnoh_experimental_windows.py --game "CAMINHO\game"

Instalar em cópia explicitamente:

    py -3 scripts\regions\install_sinnoh_experimental_windows.py --game "CAMINHO\game" --install

## Segurança e escopo

- **Nunca** escreve no Game.exe, `game/Data`, `game/Plugins` nem em saves da instalação principal. Só copia arquivos regulares de diretórios de runtime permitidos; pastas Save/Saves/Savedata, backups, logs e padrões de save são excluídos.
- Rejeita links simbólicos/junctions, paths inseguros, duplicidade de IDs, acesso a cópia antiga e sobrescrita de mapas nativos. O processo é atômico: ou cria a pasta QA completa, ou remove a pasta temporária.
- O título e as pastas de save App/Org são exclusivos por instalação experimental, com 12 dígitos hexadecimais, para não colidir com Decades/Kanto/Johto/Hoenn.
- As coordenadas de evento e chegada são calculadas por BFS sobre as nove geometrias originais, e verificadas com as tabelas RMXP propostas. **Isso NÃO equivale à revisão humana ou colisão real no motor**. Os mapas são originais programáticos, não cópias de Diamond/Pearl.
- O instalador **não solicita nem cria atestado R07/R08**. MapIDs são temporários e só locais à cópia QA; nenhuma reserva global foi aprovada. Direitos R08, avaliação final R07 e os testes R09 (43 Windows + 1 JoiPlay) continuam pendentes. Não atualiza as barras de progresso jogável antes de evidência de Game.exe real.
- Se a engine não conseguir compilar PBS ou se o loader de plugins/BlueRegions não existir na versão instalada, a execução falhará com segurança e o piloto não deve ser anunciado como funcional.

## O que a CI J12-E testa

Testes unitários verificam geração de 24 eventos, destinos e chegadas, acessibilidade estática, ausência de colisões de event tiles, mapas Ruby Marshal com três camadas preservadas, sprites PNG originais, ISBN de MapIDs locais, isolamento de save, cópia atômica, tentativas de sobrescrita/symlink, regressões J11-C/J11-B e site. **Nenhum runner baixa Game.exe nem acessa saves reais; 0/9 mapas instalados na base principal, 0/44 QA nativa reportada.** O artifact de instalação traz **somente código e o BAT**, não um jogo pronto.

## Limitações reais

Esta etapa reduz a barreira para **testar** Sinnoh no seu Windows, mas não pode garantir que a batalha contra Barry, o save/load, o menu de regiões e as interações rodem corretamente sem uma execução nativa. Um teste manual após instalar na cópia QA é necessário. O botão de instalação/execução está separado da instalação oficial do Blue-Story para evitar danificar a campanha.
