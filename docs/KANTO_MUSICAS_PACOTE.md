# Trilha de Kanto — catálogo do pacote recebido e publicação opcional

## Pacote recebido nesta conversa

| Verificação | Resultado |
|---|---|
| Nome original | `pkm msc kanto.zip` |
| Faixas | **64 arquivos MP3** |
| Tamanho do ZIP | **135.004.227 bytes** (aprox. 135 MB decimais) |
| Tamanho dos MP3 descompactados | **135.768.381 bytes** |
| Primeiras faixas | Game Freak Logo, Opening Movie, Title Screen, Pallet Town, Professor Oak |
| Áreas e batalhas | Viridian Forest, Pewter, Mt. Moon, Vermilion, Lavender, Celadon, Silph Co., Fuchsia, Cinnabar, Pokémon Mansion |
| Finalização | Final Battle! (Rival), Epilogue, Hall of Fame, Staff Credits |
| SHA-256 do ZIP | `60af6717ee93bc1381b2c38103c6ec5ddf162650bd80cc45432ef0d7f3dd5284` |

Todas as 64 faixas foram identificadas como MP3s com cabeçalho `ID3`. Os números das faixas são `1-01` a `1-60` e `1-70` a `1-73`. As lacunas correspondem à própria numeração do pacote recebido.

### Situação da publicação

**Os MP3s não foram enviados ao GitHub nesta alteração.** A conexão de código usada neste chat publica texto e scripts, mas não consegue transportar diretamente o ZIP binário de 135 MB. Não confundir um manifesto ou script publicado com a publicação da trilha.

O repositório é **público**. O conjunto parece conter trilhas musicais oficiais da franquia Pokémon; não há licença de redistribuição confirmada neste pacote. Confira a autorização para publicar antes de tornar os MP3s acessíveis ao público. O projeto já recomenda manter recursos originais de terceiros fora do repositório Git (veja [Editor de músicas](EDITOR_MUSICAS.md) e `.gitignore`).

## Publicação pelo GitHub CLI, quando autorizada

O script [`scripts/music/publish_kanto_release.py`](../scripts/music/publish_kanto_release.py) valida estrutura, cabeçalhos MP3, quantidade, tamanho e **hash exato do ZIP recebido**. Por padrão, ele só audita e **não envia nada**.

A opção de publicar usa uma **GitHub Release** (arquivo ZIP único) em vez de acrescentar 135 MB ao histórico da `main`. Assim, os arquivos de áudio originais e os saves de Decades não são modificados. É necessário um computador com o ZIP local, GitHub CLI `gh` autenticado e autorização para distribuir as faixas publicamente.

```powershell
# 1. Auditar o ZIP local; NÃO publica músicas.
py -3 scripts/music/publish_kanto_release.py --archive "C:\caminho\pkm msc kanto.zip"

# 2. Confirmar acesso ao GitHub, sem divulgar credenciais.
gh auth status

# 3. PUBLICAR SOMENTE se possuir direitos/autorização de distribuição.
py -3 scripts/music/publish_kanto_release.py --archive "C:\caminho\pkm msc kanto.zip" --publish --confirm-rights
```

O script não modifica nem substitui uma release existente; ele recusa duplicidades para preservar o material já publicado. O tag padrão é `kanto-audio-user-supplied-2026-11-12`. Depois de uma publicação **realmente confirmada** pelo GitHub CLI, o endereço esperado será:

`https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/kanto-audio-user-supplied-2026-11-12`

**Este endereço não prova que a release ou os arquivos existam.** Não anunciá-lo como download até verificar sua criação no GitHub.

## Utilização local no jogo

Para ouvir ou atribuir músicas ao jogo **sem distribui-las publicamente**, a interface já suporta importação local via **Blue Studio → Editor de ROM → Músicas**, com armazenamento em `game/Audio/BGM`. A importação individual aceita MP3 sem conversão e mantém backup; faixas originais e músicas locais ficam fora do Git. Consulte [Editor de músicas](EDITOR_MUSICAS.md).

**Não adicionar os arquivos MP3 ao Git sem verificar direitos.** A publicação do código/manifesto não altera automaticamente `Data/blue-music.json`, mapas nem eventos do Kanto. A associação das faixas a cidades/rotas/chefes deve ser testada em ambiente local antes de torná-la padrão.
