# GD03 — desenho 2D e primeiro recorte de Galar

Proposta futura, sem implementação. Cruze o
[atlas GD05](GALAR_GD05_ATLAS_VISUAL_E_TILES_KANTO.md),
[inventário GD02](GALAR_GD02_INVENTARIO_E_PROGRESSAO.md) e
[percurso original](https://bulbapedia.bulbagarden.net/wiki/Appendix:Sword_and_Shield_walkthrough).
A posição dos lugares e as saídas são referência de Sword/Shield; o
visual vem dos tilesets de Kanto já usados no Blue.

| Módulo | Trecho a provar | Limite |
|---|---|---|
| D01 | Casa e vila de Postwick ↔ R01 ↔ Wedgehurst; Slumbering Weald em ramal e evento inicial em estado próprio. | O visitante conserva a equipe; escolher inicial uma vez. Sem saída para a parte profunda antes do seu arco, nem batalha de vitória inventada na floresta. |
| D02 | Wedgehurst ↔ R02/Magnolia; estação → Wild Area Station e corredor sul da Wild Area → Motostoke. Provar a volta após liberar o transporte e a abertura do desafio. | Não transformar estação ou cidade em teleporte de QA. Não liberar ponte/setor ao norte ou rail para DLC não entregue. Táxi em estado separado do trem. |
| D03 | Motostoke ↔ R03 ↔ Galar Mine ↔ R04 ↔ Turffield; Centro, desafio das Wooloo e Milo com retorno real. | Não entrar em Hulbury/R05 antes do marco nem conceder insígnia ou esmeralda por menu ou derrota. Uma recompensa por conquista. |

Os três módulos formam um único recorte futuro. Quando não houver
mapa aprovado, desenhar em 2D portões, rampas, bifurcações, conexões
de mina e rota antes de detalhar cenário. A topologia deve ser
reconhecível em captura aérea e em percurso a pé, mesmo que a câmera 3D
e a escala absolutos não existam no motor.

## Do terreno original para Kanto em 2D

1. Ao estudar cada rota, guardar vista geral, entradas nos dois sentidos,
   andares e marcos, versão e momento da história. Se as fontes discordarem,
   indicar a lacuna. Para Motostoke, separar piso industrial baixo, rampas
   ou elevadores, centro comercial e estádio. Para Wild Area preservar os
   eixos, margens, lagos, trilhas e transições entre setores, não o tamanho
   literal ou a câmera livre.
2. Montar o croqui com famílias de tiles de Kanto já em uso: caminhos
   rurais e cercas para Postwick/R01; rocha, trilhos e níveis para as
   minas; água, barrancos, capim e pontes para Wild Area; fachadas e
   piso para Motostoke. Se uma peça não existir, compor o equivalente
   com o acervo atual e registrar o desvio. Sem substituir o tileset global,
   copiar capturas ou importar mídia 3D. Medir passabilidade e tamanho.
3. Uma porta/saída tem origem e destino, direção, condição e retorno.
   A rota principal fica legível em 2D e o caminho físico funciona
   mesmo com táxi indisponível. Testar retorno depois de salvar e
   reabrir, regressão de saves de fora da região e entradas alternativas.
4. Reusar o [contrato de viagem](VIAGEM_REGIONAL_LIVRE_NPC.md), inventário
   e respawn: visitante não recebe inicial automaticamente, retorno
   por NPC só para regiões instaladas, último Centro válido ou fallback
   seguro em Postwick. Não usar táxi regional para contornar cidades
   bloqueadas. Não renumerar mapas publicados.

Não criar simulador de Dynamax, raids ou caminhos fictícios para
qualificar o primeiro recorte. Prova de gameplay, compatibilidade de
MapIDs, renderização no motor e uso físico: `NOT_RUN`.
