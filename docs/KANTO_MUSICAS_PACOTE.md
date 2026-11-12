# Trilha de Kanto — 64 músicas presentes no GitHub

## Status após os commits de 12/11/2026

O usuário fez o upload manual dos 64 MP3s diretamente na **raiz** do repositório, em sete commits intitulados `adicionando musicas de kanto p1` até `p7`. O envio funcionou: **64/64 arquivos presentes, totalizando 135.768.381 bytes**.

A correção de organização moveu **sem recodificar ou alterar os hashes dos arquivos**:

- **50 arquivos BGM** → [`assets/music/kanto/BGM/`](../assets/music/kanto/BGM/)
- **14 arquivos ME** → [`assets/music/kanto/ME/`](../assets/music/kanto/ME/)
- **0 MP3s na raiz** depois da mudança

Leia a [análise faixa a faixa com 64 entradas](KANTO_MUSICAS_MAPEAMENTO.md) e o catálogo estruturado [`data/kanto-music.json`](../data/kanto-music.json). A atribuição foi inferida pelo título e pela função prevista no motor (não por playthrough automatizado de cada áudio).

### Verificação de integridade

O ZIP enviado anteriormente, `pkm msc kanto.zip`, tinha hash SHA-256:

`60af6717ee93bc1381b2c38103c6ec5ddf162650bd80cc45432ef0d7f3dd5284`

Os nomes, tamanhos e hashes Git dos 64 MP3s enviados correspondem aos componentes do ZIP. A movimentação preservou os **mesmos 64 blobs Git** e suas dimensões em bytes. A análise incluiu a coleção de 1-01 até 1-60, além de 1-70 até 1-73.

## Como as músicas chegam ao jogo

Como o repositório ignora `game/` (o Decades base não é publicado), as faixas são versionadas em `assets/music/kanto/`. O local de áudio **da instalação local**, reconhecido pelo RPG Maker XP/Pokémon Essentials, é:

```text
game/
└── Audio/
    ├── BGM/Kanto/   (50 MP3: mapas, batalhas, músicas contínuas)
    └── ME/Kanto/    (14 MP3: vinhetas e fanfarras)
```

Para instalar de forma segura, faça `git pull` e execute o [`INSTALAR_MUSICAS_KANTO.bat`](../INSTALAR_MUSICAS_KANTO.bat) na raiz do projeto.

Pelo terminal, sem abrir o BAT:

```powershell
py -3 scripts/music/install_kanto_music.py --audit
py -3 scripts/music/install_kanto_music.py
py -3 scripts/music/install_kanto_music.py --apply
```

O script verifica o checksum Git de todas as 64 músicas, preserva o original se ele já estiver na pasta de destino, recusa arquivos modificados ou conflitos de nome e não toca nos saves. Não altera nem desbloqueia mapas, eventos, insígnias ou configurações de música.

**Atenção:** copiar os arquivos não configura automaticamente os mapas nem as batalhas para reproduzi-los. No Blue Studio, vá a **Editor de ROM → Músicas** e associe as faixas de `Kanto/` aos mapas, eventos e categorias desejados. As músicas de vitória foram classificadas como **BGM** para seguir a convenção do plugin BlueMusic atual.

## E o upload via GitHub Release?

O procedimento anterior com [`SUBIR_MUSICAS_KANTO.bat`](../SUBIR_MUSICAS_KANTO.bat) preparava uma publicação como ZIP em uma release. Depois do upload manual, **isso não é mais necessário para acessar as 64 faixas**: os MP3s já fazem parte do GitHub. Uma Release criaria outra cópia pública desnecessária.

O repositório é **público**, e as faixas parecem ser música oficial de Pokémon. A autorização de redistribuição **não foi verificada**. Reorganizar os MP3s já publicados não muda seus direitos; cabe ao responsável confirmar as permissões e decidir se devem continuar públicos.
