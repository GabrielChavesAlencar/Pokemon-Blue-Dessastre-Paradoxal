# Johto — etapa OFFLINE 06/12: laboratório do Professor Elm (New Bark)

**Preparado em 13/11/2026.** A prévia gerada e os PNG/RXDATA nativos continuam privados, sob `.blue-work/`. O GitHub recebe somente o gerador Python, testes, hashes e documentação. **Não foi executado Game.exe.**

## Implementação

- **Mapa 676**, novo layout próprio de **20×16×3** tiles, usando a instalação Blue/Decades como referência. Substitui o ginásio genérico que havia sido usado provisoriamente como sala interior em Johto.
- **Três Poké Bolas FÍSICAS VISÍVEIS no RXDATA**, não somente em mockup, em cima de três bancadas. Cada bola está associada a uma espécie:
  - CHIKORITA — (7,6), tile **5328**;
  - CYNDAQUIL — (10,6), tile **5329**;
  - TOTODILE — (13,6), tile **5330**.
- Balcões de laboratório, estante, computador de diagnósticos, equipamento de pesquisa, console e porta visual. Posição candidata de **Professor Elm**: (10,4), sem NPC instalado.
- Criada uma variante **privada** do tileset `Inside.png` (8 colunas), com uma linha adicional de 32 pixels, contendo três cópias do primeiro frame do `Graphics/Characters/Object_Ball.png` já instalado. A variante `BLUE_JOHTO_ELM_INSIDE.png` é gerada com **Python padrão, sem Pillow**, não depende de downloads adicionais.
- A cópia do tileset usa o ID **32** em `Tilesets.rxdata` e expande as tabelas reais de `passages`, `priorities` e `terrain_tags` de **5328** para **5336** entradas. Os **32 tilesets anteriores** são preservados integralmente.
- As três bolas são **objetos estáticos bloqueando passagem** no dado RMXP. O gerador registra `event_installed=false` e `remove_static_tile_when_event_added=true` para que a etapa **08/12 substitua os ícones por eventos individuais de escolha** sem bolas duplicadas. **Ainda não se pode escolher um Pokémon ao interagir com elas.**

## Coordenadas propostas para os eventos da etapa 07–08

| Elemento | (x, y) | Validação |
|---|---|---|
| Professor Elm | (10,4) | Somente tile estático |
| Aproximação Chikorita | (7,8) | Somente tile estático |
| Aproximação Cyndaquil | (10,8) | Somente tile estático |
| Aproximação Totodile | (13,8) | Somente tile estático |
| Aproximação da porta | (9,12) | Somente tile estático |
| Chegada vindo de New Bark | (10,11) | Somente tile estático |

Uma busca ortogonal pelos bits do tileset identificou **198 tiles conectados** contendo todos esses pontos. Isso não prova movimentos, câmera, eventos ou colisão do motor.

## Prova técnica

1. Gerado `Map676.rxdata` e reaberto corretamente com **Ruby Marshal**. SHA-256 do RXDATA privado: `5208c36d61c6d7c7473e906f1ea960cb183222774d1c213f44e452f652fca241`.
2. No staging privado, comparados **77 mapas** antes/depois: apenas `Map676.rxdata` mudou, outros **76** idênticos.
3. `MapInfos.rxdata` **idêntico**; `Tilesets.rxdata` estendido **apenas por uma definição nova**, preservando as 32 originais byte a byte ao serializar o prefixo Marshal.
4. PNG privado de tileset SHA-256: `39fef3a3c34a7027fe2e46f9e0cf9282a8d48338cc3bb4491bbac37f888a24d4`.
5. **7 testes sintéticos Python aprovados** em `tests/test_johto_elm_lab_v1.py`: três bolas realmente gravadas na tabela de tiles, caminho entre Elm/porta/iniciais, móveis, validação das tabelas, bloqueios estáticos, codificação/decodificação PNG RGBA e rejeição de PNG corrompido.
6. Nenhum programa executável, save, script estrangeiro, evento de interação ou dado binário da base foi adicionado ao GitHub.

## Gerar o estágio na instalação local, SEM abrir o EXE

Pré-condição: ter as prévias das etapas 04 e 05 em `.blue-work/johto-staging-home1f-v1` e os assets instalados pelo Blue/Decades em `game/`:

```powershell
python scripts/regions/build_johto_elm_lab_v1.py
python -m unittest discover -s tests -p "test_johto_elm_lab_v1.py" -v
```

A rotina verifica o staging de origem, recusa overwrites e salva **exclusivamente** uma cópia nova em `.blue-work/johto-staging-elm-lab-v1`; não altera o `game/` original, preservando Kanto, Decades e saves.

**Instalação automática pelo `Blue-Story.exe` ainda NÃO está concluída.** Não afirmar que um usuário que atualize o jogo já terá Johto instalável; essa integração exige geração segura de mapas e assets, eventos, PBS, direitos de redistribuição e QA de uma cópia isolada antes de liberar a região.

## Progresso

- **Desenvolvimento offline: 6/12 (50%).**
- **Fases jogáveis: 0/13.**
- **Fases testadas no Game.exe: 0/13.**

**Próxima 07/12:** configurar coordenadas, escada quarto↔casa e entradas da casa/laboratório na prévia, preparar os warps reversíveis e avaliar limites/obstáculos estáticos. A integração dos três eventos interativos das Poké Bolas e do diálogo de Elm pertence à **08/12**.
