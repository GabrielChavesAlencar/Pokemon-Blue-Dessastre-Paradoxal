# Líderes: duplas Full Power

As alterações abaixo afetam exclusivamente os registros **2v2 Full Power** do Story Mode. São 18 substituições e uma alteração adicional de item no Arbok de Cethin. As variantes Basic Power, 1v1, 3v3 e os treinadores do Battle Mode mantêm seus registros. O online permanece para uma etapa posterior.

Nature, quatro golpes e EVs seguem o pedido do autor. Os EVs não especificados ficam em zero; as distribuições solicitadas somam 504, sem acrescentar os seis pontos restantes. A ordem de serialização no PBS é HP, Ataque, Defesa, Speed, Ataque Especial e Defesa Especial. As habilidades dos novos Pokémon são válidas para suas espécies: Archgutor usa Mega Sol, Magiscale usa Psychic Surge e Dynamotrode usa Transistor; os demais usam a habilidade regular correspondente.

| Líder | Sai | Entra | Nature | Item |
|---|---|---|---|---|
| Marigold | Sunflora | Archgutor | Quiet | Life Orb |
| Reva | Bruxish | Ludicolo | Modest | Ludicoloita DP |
| Keegan | Emboar | Scorch Mane | Adamant | Heat Rock |
| Quinn | Wyrdeer | Magiscale | Modest | Psychic Seed |
| Luis | Infernape | Burrow Brawler | Adamant | Booster Energy |
| Luna | Absol | Mire Crest | Adamant | Choice Scarf |
| Galen | Ninjask | Rime Shroud | Timid | Focus Sash |
| Christopher | Nosepass | Spore Rampart | Brave | Sitrus Berry |
| Atlas | Iron Treads | Dread Crest | Bold | Power Herb |
| Sophia | Squawkabilly | Iron Feaster | Brave | Choice Band |
| Hermes | Magnezone | Dynamotrode | Modest | Air Balloon |
| Cethin | Beedrill | Ancestrash | Sassy | Black Sludge |
| Keiko | Alcremie | Savege Jowl | Brave | Assault Vest |
| Roho | Runerigus | Phantomire | Timid | Booster Energy |
| Belinda | Appletun | Tidal Tyrant | Adamant | White Herb |
| Gohar | Empoleon | Titan Baleen | Sassy | Leftovers |
| Eira | Baxcalibur | Frost Plume | Modest | Life Orb |
| Azure | Celesteela | Iron Maeltrom | Modest | Terrain Extender |

O Arbok de Cethin recebe **Arbokita DP** (`DPARBOKITE`). Ludicolo recebe `DPLUDICOLOITE` na forma base para poder Mega Evoluir durante a batalha. As regras e limites normais de Mega Evolução da engine continuam sendo aplicados.

Os itens escolhidos respeitam os sets: Heat Rock estende Sunny Day; Psychic Seed combina com Psychic Surge; Power Herb remove o turno de preparação de Meteor Beam; White Herb recupera as quedas de Shell Smash; Black Sludge cura Ancestrash, que é do tipo Poison; Assault Vest é usado em um set só de ataques; Terrain Extender prolonga o Electric Terrain que ativa Quark Drive do Iron Maeltrom. Air Balloon protege Dynamotrode de Ground, sua fraqueza quádrupla.

Para os novos sets, os IVs ofensivos necessários são 31. Quiet, Brave e Sassy usam Speed IV 0; atacantes especiais sem Fake Out/U-turn usam Attack IV 0. Isso evita herdar, por exemplo, Special Attack IV 0 do atacante físico substituído. Nível, posição do integrante, Tera Type e regras de Dynamax do slot são preservados. Outros integrantes permanecem intactos, exceto o item solicitado do Arbok.

## Instalação e verificação

O manifesto próprio fica em `scripts/battle_polish/leaders_full_power.json`. O instalador prepara todas as alterações antes de escrever, exige identificar exatamente os 18 registros e os Pokémon esperados, faz backup e aplica a substituição apenas nos slots correspondentes de `game/PBS/trainers_story_mode.txt`. Reaplicar não duplica Pokémon nem muda os outros times.

`ABRIR_JOGO.bat`, `HUB_DE_BATALHA.bat` e o instalador normal reaplicam o patch e recompilam quando necessário. A página História do portal acompanha os 18 times atualizados. Os arquivos originais da base e os backups continuam fora do Git; o manifesto e o patcher próprios reproduzem a mudança em uma instalação nova.

O smoke nativo grava `game/Data/blue-full-power-validation.txt`: verifica os 18 times compilados, espécie/forma, quatro golpes, habilidade, Nature, item, EVs/IVs na ordem correta e transformação das duas Megas autorais. O balanceamento de golpes 60/90 das fases iniciante/intermediária continua valendo; no avançado os sets Full Power são usados integralmente.
