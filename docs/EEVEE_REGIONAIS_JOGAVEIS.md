# Eevee regional no Pokémon Blue: Dessastre Paradoxal

**Escopo:** nove formas regionais com ID de forma `50`, sem modificar Eevee e Eeveelutions originais.

Os dados de stats, habilidades e learnsets vêm do estudo `Estudo_Formas_Regionais_Eevee_Base_Stats_Learnsets_Completos_Gen9`, já cadastrado no portal (`site/public/data/future-eevee.json`). Os sprites são extraídos do atlas oficial do projeto em `site/public/assets/future-eevee/sprites-atlas.png`: frente/costas normais/shiny, ícones e pegadas (63 PNGs). As habilidades e os golpes não reconhecidos pelo PBS local são auditados antes da instalação: habilidades incompatíveis bloqueiam a instalação e golpes ausentes são omitidos e registrados em `game/Data/blue-future-eevee-compatibility.txt`.

## Encontros regionais

As chances indicadas são relativas **a cada encontro do método especificado**, em todas as versões existentes da tabela, não às capturas em geral. A distribuição preserva outros encontros e os 5% dos Paradoxos previamente instalados.

| Forma | Área | Mapa | Método | Chance |
|---|---|---:|---|---:|
| Eevee Fantasma | Abandoned Cabin | 84 | Land | **20%** |
| Vaporeon Veneno | Noxious City | 121 | Water | **5%** |
| Jolteon Aço | Circuit City | 119 | Land | **5%** |
| Flareon Terra | Desert Zone | 175 | Land | **5%** |
| Espeon Dragão | Draco Cave | 167 | Land | **5%** |
| Umbreon Inseto | Cloakfall Forest | 82 | Land | **5%** |
| Leafeon Pedra | Gemstone Cave | 162 | Land | **5%** |
| Glaceon Voador | Stratos Horizon | 171 | Land | **5%** |
| Sylveon Lutador | Bulwark City | 113 | Land | **5%** |

Os níveis individuais de encontro são herdados da respectiva tabela do mapa. Nos encontros selvagens regionais o Pokémon já nasce na forma 50.

## Treinadores

Um Pokémon regional é acrescentado, sem substituir os existentes, a cada treinador:

| Treinador | Forma |
|---|---|
| Salvadore | Eevee Fantasma |
| Horace | Vaporeon Veneno |
| Ball Guy | Jolteon Aço |
| Maxence | Flareon Terra |
| Vincent | Espeon Dragão |
| Mariano | Umbreon Inseto |
| Layton | Leafeon Pedra |
| Julia | Glaceon Voador |
| Alfie | Sylveon Lutador |

O novo membro recebe inicialmente o maior nível já cadastrado no time; o sistema de progressão da campanha adapta níveis, golpes e limites de BST em runtime conforme a dificuldade. A aba de Treinadores do site mostra esses integrantes, com `Form = 50`.

## Evoluções do Eevee Fantasma

Todas requerem ganhar um nível na **forma 50**, sem modificar as evoluções do Eevee oficial:

- Vaporeon: nível 28+, Poison Barb, status Poison, em Noxious City.
- Jolteon: nível 28+, Metal Coat, em Circuit City, Iron City ou Industrial Zone.
- Flareon: nível 28+, conhecer Mud-Slap e subir de nível com Sandstorm.
- Espeon: nível 30+, amizade 160+, Dragon Fang, no período da manhã.
- Umbreon: nível 28+, Silver Powder, floresta à noite.
- Leafeon: nível 30+, Hard Stone, conhecer Curse, em cavernas selecionadas.
- Glaceon: nível 30+, Sky Plate, conhecer Swift, no Stratos Horizon ou Mt. Vile.
- Sylveon: nível 30+, amizade 180+, usar Helping Hand com sucesso três vezes em batalhas duplas no nível anterior.

Os métodos estão no plugin `FutureEevee.rb`. Alterações de clima, amizade e mapas são checadas ao subir de nível. As regras são propostas autorais do site agora integradas como mecânica do Blue.

## Aplicação local e verificação

1. Atualizar a `main` (ou executar o atalho de atualização).
2. Executar `INSTALAR_JOGO.bat` com a base Decades no diretório `game`.
3. Permitir a recompilação dos dados PBS/plugins na primeira abertura.
4. Conferir as nove formas no laboratório, encontros em cada mapa, times dos nove treinadores e evolução do Eevee Fantasma.
5. Revisar `game/Data/blue-future-eevee-compatibility.txt` para eventuais golpes indisponíveis na engine.

O instalador efetua backup dos PBS e não altera saves diretamente. **Testes automatizados com fixtures não substituem um teste jogável no Game.exe/JoiPlay**. Se algum mapa não existir no PBS local, o instalador não aplica mudanças parciais; indica o erro para correção.

