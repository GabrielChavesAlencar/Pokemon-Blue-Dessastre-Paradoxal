# Instalar Pokémon Blue no Android pelas fontes originais

O ZIP inicial contém o atualizador e este guia. Ele não contém mapas,
gráficos, áudios, executáveis do jogo ou saves. O atualizador baixa a receita
publicada no GitHub do Blue e obtém os arquivos da base Decades, de Kanto e de
Hoenn das fontes já fixadas e verificadas pelo instalador do projeto.

## Primeira instalação

1. Instale o JoiPlay e o RPG Maker Plugin. No Termux, instale Python, Git e
   libarchive para ter o comando bsdtar. Conceda ao Termux acesso ao
   armazenamento compartilhado com termux-setup-storage.
2. Extraia o ZIP em uma pasta nova no armazenamento compartilhado. Feche o
   JoiPlay e execute lá:

       python ATUALIZAR-ANDROID.py

   O próprio atualizador escolhe a receita oficial mais recente, baixa os
   arquivos necessários e prepara uma pasta terminada em -Compilar-Fontes.
3. Adicione ao JoiPlay somente o Game.exe indicado pelo atualizador para
   compilar. Abra-o uma vez e espere fechar. Execute o atualizador de novo.
   A pasta final Pokemon-Blue-Android é criada após a verificação. Adicione o
   Game.exe da pasta final ao JoiPlay e use esse atalho para jogar.

O Termux precisa de Internet e espaço para a receita, os arquivos originais
e a cópia de compilação. Na atualização, a instalação atual fica disponível
enquanto a cópia é preparada. Use seu atalho final apenas após concluir a
aplicação. A compilação no JoiPlay é necessária para gerar os dados do motor.

## Atualizações seguintes

Com o JoiPlay fechado, execute o mesmo ATUALIZAR-ANDROID.py novamente,
na pasta do instalador ou na pasta final. O atualizador procura uma receita
mais nova. Se houver, repete a preparação e verifica os MapIDs e o perfil
instalado antes de aplicar os arquivos alterados. Saves ficam na instalação
original. Caso a aplicação seja interrompida, use novamente o mesmo comando.

Este fluxo cria um canal de instalação pela fonte. A edição 247 e as
instalações pelas receitas K05/K06 conservam seus atualizadores e seus
procedimentos de migração. Para começar pelo novo instalador, use uma pasta
nova. A verificação automatizada roda no Windows, e o teste em aparelho
JoiPlay continua adiado.
