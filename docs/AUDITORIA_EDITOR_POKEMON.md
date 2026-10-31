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

## Atualização v0.3 — Pokémon novos sem substituir espécies

Implementados nesta fase:
- **Cadastro próprio de espécie nova:** grava em `pokemon.txt` e adiciona uma entrada em `pokemon_metrics.txt`; não modifica as espécies existentes. Identificadores são nomes simbólicos, não slots GBA.
- **Prevenção de duplicação:** procura o ID em todos os arquivos base `pokemon*.txt` (excluindo definições de formas e métricas), incluindo os pacotes adicionais do Decades.
- **Ficha visual:** nome, tipos, seis atributos, habilidades, golpes por nível/tutor/ovo, evoluções e descrição; o botão **Validar dados** verifica tipos, habilidades, golpes, estatísticas e destinos de evolução nos dados PBS disponíveis.
- **Battle Metrics reais:** X, Y, escala de frente/costas e velocidade de animação; grava em `pokemon_metrics.txt` ou `pokemon_metrics_forms.txt`, com controle de concorrência e backups. A prévia é aproximada; o resultado exato depende do runtime do jogo.
- **Diagnóstico de compilação:** endpoint `/api/pokemon/compile-status` compara os tempos de `PBS/pokemon*.txt` com `Data/species.dat` e `Data/species_metrics.dat`. O botão Debug abre o jogo para realizar a compilação **dentro do Essentials**.
- **Regressão de ponta a ponta:** a suíte usa Pokémon de teste para criar nova espécie, garantir preservação das anteriores e salvar coordenadas de batalha. GitHub Actions testa Python, Chromium e RUN.bat no Windows.

### O que permanece pendente de verificação no jogo real

1. **Compilação integral sem interação:** o Blue Studio abre o atalho de debug e oferece diagnóstico, mas não controla de forma comprovada o compilador do Essentials; requer confirmação do runtime Windows.
2. **Execução de batalha real:** não foi possível testar `Game.exe` do Decades com uma espécie personalizada no ambiente do GitHub Actions. Verificar no Windows batalha, Pokédex, captura, evolução, save/load e shiny.
3. **Integração completa de registros:** encontros, Pokédex regional, NPCs, evoluções condicionais, cries, métricas de gênero e plugins podem exigir ajustes específicos além da definição PBS.
4. **Editor de sprites avançado:** preview de posição é aproximada; pivot exato em runtime, animação de quadro, arrastar-e-soltar e restauração de imagens pela UI requerem próximos ciclos.

## Lacunas para o editor 100%

1. **Validação semântica ampliada:** nova espécie já valida tipos, stats, habilidades, golpes e evoluções; ainda falta validação de todas as regras de plugins, itens evolutivos e mudanças antigas pelo editor genérico.
2. **Compilação automatizada integral:** o botão de Debug já inicia a compilação assistida, mas o compilador interno do Essentials ainda exige operação/verificação no jogo.
3. **Integração de modos de sprite:** teste real em batalha e Pokédex para GIF, PNG faixa e PNG estático, incluindo formas e shiny.
4. **Sprite editor avançado:** posição, escala e velocidade já são gravados em PBS; ainda faltam preview pixel-perfect no jogo, conversão e arrastar/soltar.
5. **Referências:** ligação entre espécie, ID da forma, sprite, cry, métricas, movimentos, itens evolutivos e encontros.
6. **Histórico e restauração visual de sprites:** o backup é automático mas sua restauração pela UI ainda não existe.
7. **Mapas e treinadores avançados:** edição gráfica de mapas RXDATA e formulário avançado de times, separados da edição PBS básica.

## Regressão obrigatória

- `python -m unittest discover -s tests -v`: valida parsing, backups, importação PNG/GIF, caminhos permitidos, erros HTTP e concorrência.
- `node --check web/app.js && node --check web/sprites.js`: valida sintaxe.
- `node tests/browser_smoke.cjs`: valida o fluxo real no Chromium, incluindo upload PNG estático para uma espécie artificial e preview.
- `.github/workflows/regression.yml`: executa automaticamente em `push` na `main` e em PR, além do teste do `RUN.bat` no Windows.

Não usar os assets reais do Decades nesses testes. Dados de teste ficam em diretórios temporários.
