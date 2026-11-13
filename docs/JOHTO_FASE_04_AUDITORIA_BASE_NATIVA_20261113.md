# Johto Fase 04 — análise da exportação nativa recebida (13/11/2026)

**Fonte:** ZIP privado `johto-pilot-inputs.zip` exportado da instalação real do Blue/Decades instalada pelo `Blue-Story.exe`. **Não adicionar ZIP, imagens ou RXDATA ao GitHub.**

## Resultado da auditoria

- Arquivo SHA-256: `f34b13b56fd42f089c6df525c54e11ad0f5b64acef9027911867efc4be89fee4`.
- **2.460 arquivos**: manifesto verificado individualmente (tamanho + SHA-256), sem divergências ou arquivos de exec/saves/plugins.
- **207 mapas nativos RMXP** (IDs até 275; nenhum em 600–999 no snapshot); **95 arquivos PBS**; **2.155 gráficos**.
- `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata` presentes e legíveis, mapas Ruby Marshal auditados sem executar scripts.
- **Pokémon iniciais** CHIKORITA/CYNDAQUIL/TOTODILE e tipo de treinador `RIVAL1` confirmados no PBS real.
- **Sprites** presentes e PNG válidos: `NPC_GSC_Mom`, `NPC_HGSS_Professor_Elm`, `NPC_HGSS_Silver`, `Object_Ball`.

## Três candidatos de geometria que existem mesmo

| Símbolo de New Bark | Base nativa (Decades) | Tamanho | SHA-256 | Resultado |
|---|---|---|---|---|
| `JOHTO_NEW_BARK_PLAYER_HOME_2F` | Map084 — Abandoned Cabin | 40×40 | `cd8f99436db0fa1328e0b3176fac6e5791031e29bece8ca2dadadb8c1ea2ac64` | Sala com piso de madeira e objetos, **não é quarto HGSS** |
| `JOHTO_NEW_BARK_PLAYER_HOME_1F` | Map079 — Cherryhill Center | 24×26 | `84e9316fb24465a87834d69a0b2aecdbe264b17bfda95a1bae2131048f63a19d` | Centro Pokémon com balcão, **não é casa** |
| `JOHTO_NEW_BARK_ELM_LAB` | Map080 — Cherryhill Gym | 30×30 | `c47ee5e1149f03c104c29c569d835d452a4189c81c276e51ad6c4bcb9ce09b59` | Ginásio genérico, **não é laboratório** |

Foram renderizados previews reais das três bases para revisão (pacote privado entregue no chat). **Não marcar `native_template_reviewed` nem `room_geometry_reviewed` como verdadeiros simplesmente por ver o nome dos arquivos:** eles são estruturalmente possíveis, mas **não são interiores fiéis nem autorizam instalação**. A base possui o tileset `Inside.png`, permitindo desenhar os três interiores de Johto com recursos já instalados, sem copiar scripts externos.

As fachadas do exterior New Bark do Map Pack são as quatro candidatas documentadas em `docs/JOHTO_FASE_04_ENTRADAS_REAIS_V1.md`. Os pontos (5,21), (14,23), (4,31) e (13,33) continuam hipóteses de entrada, não tiles/colisões confirmados.

## Impacto real no 1/13

A dependência de **dados nativos (mapas + sprites + PBS)** foi resolvida para a **auditoria offline**. A dependência de **três interiores corretos + eventos com XY/passabilidade + execução no Game.exe** permanece. O ZIP intencionalmente não inclui Game.exe, plugins, Game.ini e mkxp.json; portanto, não constitui um executável Johto e **não prova comportamento do RPG Maker/Essen­tials**.

### Próxima implementação

1. Gerar os três interiores efetivos New Bark 2F/casa 1F/Elm usando tileset nativo e **layout adequado**, em uma nova preview isolada, sem clonar ginásio e Centro Pokémon como casas.
2. Definir MapIDs livres no momento da construção; o snapshot confirma nenhum nativo entre 600 e 999, mas a alocação definitiva depende do stage Johto e da instalação atual.
3. Renderizar/prever coordenadas de spawn, portas, escada, mãe, Elm, três bolas e Silver. **Verificar passabilidade na engine.**
4. Compilar os eventos próprios, montar `.blue-work/johto-pilot` com saves próprios e executar a primeira sequência na engine real.
5. Só com comprovação executada no Windows elevar a **1/13 JOGÁVEIS** e depois **1/13 TESTADAS**.

**Barras comprovadas nesta entrega:** 0/13 jogáveis; 0/13 testadas. **Não enviar dados nativos ao GitHub.**