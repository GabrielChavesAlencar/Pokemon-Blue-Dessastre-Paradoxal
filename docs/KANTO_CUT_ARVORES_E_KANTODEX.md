# Kanto — árvores Cut e KantoDex 001–151

## Base no detonado e diagnóstico

A referência [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md) informa **HM01 Cut** como recompensa do capitão do S.S. Anne, a árvore em frente ao ginásio do Lt. Surge, o acesso posterior ao Old Amber no Museu de Pewter e outros locais que dependem de Cut. Também distingue a Pokédex obtida de Oak no início da jornada e a **National Dex** como marco posterior de FRLG. Essas regras históricas não justificam bloquear a National Dex pré-existente da campanha Blue.

### Por que árvores estavam ausentes

A importação segura de eventos em `scripts/regions/kanto_overworld.py` tinha suporte a `SmashRock` e `StrengthBoulder`, mas excluía `CutTree` dos NPCs comuns sem convertê-los em obstáculos. Assim, os eventos eram removidos durante `install_events`, embora o mapa original existisse.

**Correção:** importar os eventos da fonte com nome `CutTree` nos **mesmos MapIDs, EventIDs, X/Y e gráficos originais**, sem copiar nenhum script Ruby externo. O evento sólido usa a condição nativa `pbCut` e remove a árvore com `pbSmashThisEvent` apenas quando a engine aceita Cut. O piloto não distribui HM01 por esse evento e preserva a regra do capitão e as permissões de insígnia.

A categoria `cut` passa a aparecer no inventário `Data/blue-kanto-field-events.json` gerado após `--rebuild`, e `verify_pilot.py` comprova que cada árvore importada tem condição Cut, callback correto e posição real. Eventos dos mapas `preview_only` continuam bloqueados, sem árvores fictícias.

### KantoDex e National Dex

- **National Dex**: preservada, com todos os Pokémon existentes, registros/flags, formas, opções de pesquisa e números originais do Blue.
- **KantoDex**: visualização adicional no menu nativo da Pokédex. Pressionar **K** ou clicar em `KantoDex [K]` alterna a lista para as **151 espécies originais da primeira geração**, de **Bulbasaur nº 001** até **Mew nº 151**.
- O número regional vem da correspondência canônica de `data/national-species.json`, não de um índice recalculado a partir das capturas ou do progresso da campanha.
- Pressionar K novamente (botão **National Dex [K]**) restaura a visualização anterior da Pokédex nacional. Busca/filtros na visualização Kanto ficam limitados a espécies Kanto.
- As duas visualizações usam o **mesmo registro de vistos/capturados** do jogo: não concedem capturas, não recriam Pokédex nem mudam saves. A KantoDex não substitui a National Dex e é oferecida no Blue principal e na cópia do piloto.

### Restrições e testes

1. Reconstruir a cópia experimental após atualizar a `main` via `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`.
2. No S.S. Anne, receber Cut do capitão e confirmar a permissão regional da **Cascade Badge** antes de cortar qualquer árvore.
3. Testar árvore próxima ao ginásio de Vermilion, salvar, recarregar, sair e voltar ao mapa. Conferir que não desaparece antes do uso válido de Cut.
4. Abrir a Pokédex: conferir Bulbasaur #001, Ivysaur #002, Venusaur #003 e Mew #151 na KantoDex. Alternar K e confirmar que National Dex permanece intacta.
5. Testar Pokémon vistos, não vistos, capturados, pesquisas e entrada detalhada; assegurar que a KantoDex não revela registros nem altera o save.
6. Os mapas `preview_only` e os eventos condicionais especiais continuam pendentes até auditoria de fase. A CI sem fonte nativa não substitui o teste real com `Game.exe`.

**Arquivos atualizados:** `scripts/regions/kanto_overworld.py`, `scripts/regions/verify_pilot.py`, `scripts/battle_polish/KantoDex.rb`, `scripts/battle_polish/DexControls.rb`, instalador e assinatura de build do piloto, mais testes para Cut e para a numeração completa da KantoDex.
