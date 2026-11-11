# Auditoria de escala: sprites Dessastre Paradoxal

## Base analisada

A auditoria lê **todos os sprites realmente fornecidos no pacote**
`site/assets/fan-pokemon.tar.gz` e valida seus hashes com o manifesto
`data/dessastre-paradoxal.json`, sem substituir arte ou alterar saves.

- **64 espécies/formas já compiláveis**: 52 espécies e 12 Mega Evoluções.
- **256 imagens de batalha auditadas**: frente e costas, normais e shiny.
- Os 128 sprites de frente/costas **normais** medidos têm **128×128 pixels** e um quadro; seus desenhos usam tipicamente 100–112 pixels de largura e são centralizados.
- Casos com silhueta mais baixa, como Primaltropical, Razorcarapace e Ravenouscrest, mantêm sua altura e proporção autorais, sem alongamento.
- Os sete cadastros pendentes não receberam dados inventados nem foram liberados à força.

### Referência da engine Decades

A base do Pokémon Decades usa o plugin **[DBK] Animated Pokémon System**, que define os valores-padrão:

| Papel | Padrão da engine | Resolução dos sprites autorais | Valor escolhido |
|---|---:|---:|---:|
| Frente | 2× | 128×128 | **2×** |
| Costas | 3× | 128×128 | **2×** |

O 3× original das costas é apropriado para sprites menores. A conferência da base Decades encontrou, por exemplo, os sprites de Charizard com 91×91 pixels na frente e 98×98 atrás, de Gengar com 79×79 na frente e 73×73 atrás, e de Walrein com 78×78 e 75×75. São **tamanhos por quadro**, não a dimensão total das tiras animadas.

Usar 3× nos sprites autorais de 128 pixels levaria a uma imagem-base de 384×384, grande demais para vários enquadramentos. A escala 1× utilizada anteriormente nas costas apresentava os desenhos com apenas cerca de 100–110 pixels aparentes, muito pequenos em comparação ao jogo. **2×** produz cerca de 200–224 pixels visíveis para os maiores desenhos, dentro da faixa visual de Pokémon grandes na base.

## Mudança aplicada

As entradas de `PBS/pokemon_metrics_dessastre_paradoxal.txt` agora usam:

```ini
FrontSprite = 0,0,2
BackSprite = 0,0,2
ShadowSprite = 0,0,2
```

A regra vale individualmente para todas as **64 entradas jogáveis**, inclusive 12 Mega Evoluções, e para as **nove formas regionais de Eevee** (forma 50) instaladas pelo mesmo importador. A mesma métrica se aplica automaticamente às variantes shiny. A escala da frente não mudou porque já correspondia ao perfil de 128 pixels; a das costas passou de 1× para 2×.

O instalador mantém os PNGs de origem e os PNGs instalados **idênticos byte a byte**. Isso preserva nitidez, animação procedural, shiny e compatibilidade com a seleção de qualidade de sprites. O cálculo de posição e pivô continua sob controle da engine.

## Auditoria reproduzível

```bat
python scripts/dessastre_paradoxal/sprite_size_audit.py
python -m unittest discover -s tests -p test_sprite_size_audit.py -v
```

O primeiro comando lista largura, altura, ocupação real do PNG, origem visível e quadros de cada sprite de frente/costas. O teste verifica os 64 cadastros jogáveis, os 128 pares normal/shiny e a consistência de todas as dimensões.

Para aplicar: atualize a `main`, execute `INSTALAR_JOGO.bat` (ou `IMPORTAR_DESSASTRE_PARADOXAL.bat`) e permita a recompilação do PBS. O jogo instalado e os saves continuam fora do repositório; a verificação visual final do Game.exe deve ser feita no computador que possui a base.
