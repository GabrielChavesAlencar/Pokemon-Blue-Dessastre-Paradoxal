# Novo Jogo — seleção da região inicial

O Blue-Story.exe prepara a instalação e abre o jogo. A escolha de região acontece no `Game.exe` principal, antes de executar o novo jogo. [Instruções de integração de Kanto](KANTO_INTEGRACAO_DECADES.md).

## Opções

- **Decades:** inicia a campanha nativa e preserva o fluxo original de Story/Battle Mode, sem outro seletor de região.
- **Kanto:** usa **o mesmo Game.exe e sistema de saves de Decades**, começando no quarto em Pallet, mas **só após a instalação validada do pacote atual de 152 mapas, PBS, sprites, traduções e plugins** em `game/`. Sem o pacote, o menu informa **instalação necessária**, sem abrir outro jogo nem sobrescrever o save. Para instalar localmente: `KANTO_INSTALAR_NO_JOGO.bat`, seguido de `ABRIR_JOGO.bat`.
- **Johto e Hoenn** usam o mesmo jogo e perfil de saves quando instalados.
- **Sinnoh** começa no quarto do jogador e usa o Agente Regional de Twinleaf para visitar as demais regiões. No Windows, o inicializador integra os mapas quando encontra os dois ZIPs de origem verificados junto ao Blue-Story.exe. [Arquivos de instalação](../README.md).
- **Unova, Kalos, Alola, Galar, Paldea e Hisui:** indisponíveis, sem mapa fictício ou progresso concedido.
- **Voltar ao menu:** cancela a escolha sem criar partida.

`Continue`, Auto Multi Save e Mystery Gift mantêm seus handlers e índices nativos. A escolha de Kanto fica numa variável temporária e somente vira `initial=KANTO/current=KANTO` na criação real de um novo jogo. Nenhum save antigo é migrado automaticamente.

## Regras do Kanto integrado

A campanha usa o motor de batalha, escalonamento, Pokédex, PC e progressão de Decades/Blue. Cada uma das oito insígnias de Kanto contribui no máximo uma unidade para as esmeraldas globais, enquanto HMs e a regra de oito insígnias para Pokémon especiais consultam **o estado local**. A mãe entrega os Tênis de Corrida após Brock, na Rota 3. **Viagem regional livre:** desde o início, o jogador pode falar com o NPC de **Pallet Town** para visitar Decades; em **Cherryhill City** encontra o NPC para voltar a Kanto, sem exigir vitória na Liga. A chegada a Decades usa um ponto real capturado de `System.rxdata` antes da troca temporária do mapa inicial. A prévia instalada de Johto usa o Agente Regional de New Bark. O transporte não utiliza pilotos separados. [Regras completas](VIAGEM_REGIONAL_LIVRE_NPC.md).

## O que não é certificado automaticamente

A disponibilidade do seletor, um manifesto JSON válido, a recompilação de PBS e os testes Ruby/Python não provam que o jogador consegue atravessar todos os mapas, concluir os eventos ou fazer a transição para Decades sem bugs. Kanto ainda tem mapas `preview_only`. Seu aceite completo exige execução e evidência em `Game.exe`, além de save/reload, traduções, habilidades de campo, batalhas, história e regressão do Decades. Não subir a Barra 2 de Kanto sem esse QA.

## Verificações de código

```powershell
ruby -c scripts/battle_polish/TitleKanto.rb
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
ruby tests/region_start_runtime.rb scripts/battle_polish/RegionStart.rb
ruby tests/region_travel_runtime.rb tests/regions_data_fixture.rb scripts/battle_polish/Regions.rb scripts/battle_polish/RegionTravel.rb
python -m unittest tests.test_kanto_integrated_locale -v
```

O teste dos mapas reais é privado e exige a fonte local `Essentials FRLG 21.1 / 1.1`, além de uma cópia do jogo principal instalada. Consulte [roteiro E2E de Kanto](KANTO_CODEX_TESTES_E2E.md) e [guia de integração](KANTO_INTEGRACAO_DECADES.md).
