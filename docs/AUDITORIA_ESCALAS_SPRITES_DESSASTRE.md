# Auditoria de escala dos sprites Dessastre Paradoxal

Os Pokémon autorais usam **1,5× na frente e nas costas**. A escala é
aplicada pelo plugin Blue às espécies e formas com a marca
`DessastreParadoxal`, incluindo as 12 Mega Evoluções e as nove formas
regionais da família de Eevee. Normal e shiny usam a mesma métrica.

| Conteúdo | Entradas | Imagens de batalha |
| --- | ---: | ---: |
| Espécies autorais prontas | 52 | 208 |
| Mega Evoluções autorais | 12 | 48 |
| Formas regionais da família de Eevee | 9 | 36 |
| Total | **73** | **292** |

Os quadros de batalha têm **128×128 px** e são carregados em **192×192 px**
a 1,5×. A área visível varia conforme a silhueta da espécie. Os sete
cadastros pendentes continuam fora da lista jogável.

## Como a escala funciona

O Animated Pokémon System aceita números inteiros nos campos
`FrontSprite` e `BackSprite` do PBS. Por isso os valores inteiros ficam
como padrão de compatibilidade e
[`Campaign.rb`](../scripts/battle_polish/Campaign.rb) aplica 1,5× quando
a engine carrega o sprite autoral. O mesmo carregador lê as versões
normais e shiny. O ajuste mantém as proporções e os pixels dos PNGs.

A validação nativa do Hub confere a escala em todas as formas autorais
carregadas e as dimensões resultantes de Cave Fang nos quatro casos de
frente, costas, normal e shiny. Também confere as métricas de Charizard
como referência para espécies oficiais.

## Auditoria reproduzível

```bat
python scripts/dessastre_paradoxal/sprite_size_audit.py
python -m unittest discover -s tests -p test_sprite_size_audit.py -v
python -m unittest discover -s tests -p test_future_eevee_game.py -v
```

A auditoria do pacote autoral verifica os hashes, as dimensões e a área
visível de cada imagem. Os testes de Eevee conferem os gráficos gerados
do atlas regional. Para aplicar a escala em outra instalação, atualize a
`main` e abra o jogo pelo atalho normal para recompilar o plugin.
