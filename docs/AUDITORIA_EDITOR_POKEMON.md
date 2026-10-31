# Auditoria do editor de Pokémon e suporte a sprites estáticos (Blue Studio)

Data: 2026-10-31

## Resumo

O editor de Pokémon **não é 100% funcional** como uma interface completa para todos os sistemas do Pokémon Essentials v21.1. Já é possível editar PBS de espécies, formas, golpes e outros dados, além de importar as quatro imagens de batalha com segurança. As alterações nos PBS precisam ser **recompiladas no modo debug do Pokémon Essentials** para afetar o jogo.

## Descoberta sobre Pokémon Decades

- A pasta original `Graphics/Pokemon/Front` do Decades usa, entre outros, `ABOMASNOW.png`, `CHARIZARD_1.png`, etc.
- O plugin instalado `[DBK_009] Animated Pokemon System`, no arquivo `[008] Deluxe Bitmap.rb`, aceita:
  - **PNG estático**: imagem de um quadro (qualquer tamanho até os limites de segurança do editor);
  - **PNG em faixa horizontal**: múltiplos quadros de largura comparável à altura, desde que largura seja **maior que 2 × altura** para o plugin interpretar como animação;
  - **GIF**: suporte de prévia/importação no Blue Studio; compatibilidade final no jogo deve ser confirmada no runtime Windows.
- PNGs muito largos não são necessariamente GIFs; muitos Pokémon do Decades são spritesheets PNG animadas.

## O que funciona (validado em testes automáticos)

| Recurso | Estado |
|---|---|
| Ler e pesquisar registros PBS `pokemon.txt` | Implementado |
| Editar e criar registros PBS; backups | Implementado |
| Ler `pokemon_forms.txt` pela biblioteca PBS | Implementado |
| Preview de frente, costas, frente shiny e costas shiny | Implementado |
| Importar PNG estático para as quatro variantes | Implementado |
| Importar PNG spritesheet animada (largura > 2× altura) | Implementado |
| Importar GIF preservando GIF | Implementado no editor; testar no jogo |
| Sprites de formas como `CHARIZARD_1` | Implementado no editor |
| Bloquear imagens maiores que 5 MB, inválidas ou caminhos arbitrários | Testado |
| Prevenir sobrescrita concorrente por hash | Testado |
| Backup automático ao substituir imagens | Testado |
| Remover extensão concorrente `.png`/`.gif` após backup | Implementado |
| Testar no Chromium e no GitHub Actions | Implementado |

## Como usar imagens estáticas

1. Abra `RUN.bat`, que sincroniza o editor com a `main`.
2. Entre em **Editor de ROM → Pokédex**, abra um registro Pokémon e role até **Sprites**.
3. Em **Frente normal**, **Costas normal**, **Frente shiny** e **Costas shiny**, escolha **Imagem estática (PNG)** e importe as imagens correspondentes.
4. Se desejar, selecione **Animado (GIF / faixa PNG)** e importe um GIF ou PNG com no mínimo três quadros quadrados em sequência horizontal.
5. O editor guarda a imagem em `game/Graphics/Pokemon/{Front,Back,Front shiny,Back shiny}/ID.png` (ou `.gif`) e salva a anterior em `.blue-backups/sprites/`.
6. Para testar o resultado no jogo, use **Testar jogo**. Alterações nos arquivos PBS exigem recompilação prévia em debug.

Os sprites **não são copiados para o GitHub** automaticamente, pois `game/` é intencionalmente ignorada pelo Git para não republicar assets de terceiros.

## Lacunas para o editor 100%

1. **Validação semântica PBS:** tipos existentes, stats, habilidades, evolução e golpes; editor de campo genérico ainda aceita valores incorretos.
2. **Compilação automatizada:** atualizar os dados PBS no jogo a cada salvamento com relatório de erros (hoje é manual).
3. **Integração de modos de sprite:** teste real em batalha e Pokédex para GIF, PNG faixa e PNG estático, incluindo formas e shiny.
4. **Sprite editor avançado:** posição/pivot, escala, animação, prévia no campo de batalha, conversão e arrastar/soltar.
5. **Referências:** ligação entre espécie, ID da forma, sprite, cry, métricas, movimentos, itens evolutivos e encontros.
6. **Histórico e restauração visual de sprites:** o backup é automático mas sua restauração pela UI ainda não existe.
7. **Mapas e treinadores avançados:** edição gráfica de mapas RXDATA e formulário avançado de times, separados da edição PBS básica.

## Regressão obrigatória

- `python -m unittest discover -s tests -v`: valida parsing, backups, importação PNG/GIF, caminhos permitidos, erros HTTP e concorrência.
- `node --check web/app.js && node --check web/sprites.js`: valida sintaxe.
- `node tests/browser_smoke.cjs`: valida o fluxo real no Chromium, incluindo upload PNG estático para uma espécie artificial e preview.
- `.github/workflows/regression.yml`: executa automaticamente em `push` na `main` e em PR, além do teste do `RUN.bat` no Windows.

Não usar os assets reais do Decades nesses testes. Dados de teste ficam em diretórios temporários.
