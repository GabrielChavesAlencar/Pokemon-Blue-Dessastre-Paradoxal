# Piloto local de Sinnoh: de Twinleaf a Sandgem

O piloto usa seis mapas da edição pública do Pokémon Ancient Platinum, publicada por Phantombass, com eventos próprios do Blue e perfil de save separado. O Game.exe compilou e confirmou o quarto de Twinleaf, os dois destinos das bordas da Rota 201 e a concessão do inicial pelo Rowan. A travessia manual, as batalhas e o restante das fases seguem em teste.

Use o ZIP publicado em [Pokémon Ancient Platinum](https://eeveeexpo.com/threads/9085/) com o [montador](../scripts/regions/pilot_sinnoh.py). O SHA-256 da edição verificada é a8480968f93a81e81a0b2b0aedb00bd3069aed828432ec78ed890602e2d5d697.

~~~powershell
python scripts/regions/pilot_sinnoh.py --game game --source "Pokemon-Ancient-Platinum-Release.zip" --output .blue-work/sinnoh-pilot
~~~

Abra o Game.exe do piloto uma vez para compilar. Depois, use Testar Sinnoh no menu principal ou abra novamente a cópia isolada.
