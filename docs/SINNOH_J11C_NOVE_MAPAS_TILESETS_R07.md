# Sinnoh J11-C — overlay nativo isolado de nove geometrias e dois tilesets (fail-closed)

Base: J11-B / PR #246 integrado; issue #241. **A J11-C entrega preparação de estrutura RPG Maker XP, não um piloto jogável.**

## Entrega

O script scripts/regions/prepare_sinnoh_nine_original_j11c.py reaudita as NOVE geometrias autorais da J11-B por SHA-256 e valida os eventos simbólicos CH06 (16 portais direcionais em oito pares, cinco NPCs e três Poké Bolas). Não lê nem usa exteriores históricos B00.

O compilador de overlay cria objetos RPG::Map, RPG::MapInfo e dois RPG::Tileset distintos com tabelas Ruby Marshal Table para @passages, @priorities e @terrain_tags (416 entradas). Conservadoramente bloqueia tiles desconhecidos, água, árvores, rochas, paredes e móveis. Remapeia somente @tileset_id dos nove RXDATA e confirma todas as três camadas intactas. Mantém MapInfos e Tilesets anteriores byte a byte na representação serializada. Acrescenta apenas dois PNGs procedurais com nomes exclusivos ao overlay privado.

**Essas tabelas são modelos técnicos, não a passabilidade comprovada no Game.exe.** Máscaras de direções e prioridades, colisões dinâmicas, portas, escadas, água e posições de eventos precisam revisão humana e testes reais.

## Executar auditoria read-only, sem arquivos locais

    python scripts/regions/prepare_sinnoh_nine_original_j11c.py

Também pode usar SINNOH_J11C_AUDITAR_ORIGINAIS.bat. Sem flags, o código não escreve nada, não atribui MapIDs, não lê Game.exe, saves, instalações ou fontes privadas. O CI usa somente fixtures sintéticos, não o PC do usuário.

## Staging em cópia privada (somente se houver dados verdadeiros)

    python scripts/regions/prepare_sinnoh_nine_original_j11c.py --stage --baseline .blue-work/sinnoh-j11-baseline/Data --review .blue-work/sinnoh-j11-reviews/r07.json

Isso exige um baseline isolado genuíno com MapInfos.rxdata, Tilesets.rxdata, Scripts.rxdata e System.rxdata, além de recibo R07 real validado pelo auditor J11. Recusa arquivos ausentes, symlinks, inventários e SHA divergentes, MapIDs repetidos ou ocupados e reservas conflitantes com outras regiões. Não solicite nem falsifique um recibo para apenas fazer o script passar.

Caso as provas locais existam, um overlay **ainda não instalável** é escrito uma única vez, atomicamente, em .blue-work/sinnoh-j11c-private-qa-overlay/, com nove arquivos Data/MapXXX.rxdata, Data/MapInfos.rxdata e Data/Tilesets.rxdata, além de dois Graphics/Tilesets/*.png. A pasta não é o jogo principal e não pode sobrescrever outra. O plano externo é sanitizado e mantém as aprovações independentes falsas.

## Eventos e próximas etapas

Os contratos de 16 portais, cinco NPCs e três Poké Bolas são validados, mas permanecem SEM coordenadas, sprites ou colisão real aprovados. Não são compilados automaticamente em eventos jogáveis. Somente depois de R07 verdadeiro, revisão R08 dos nove gráficos originais, registros de tilesets, posições físicas, evento J04/overlay J06 e 43 testes Windows + 1 JoiPlay R09 será possível anunciar piloto jogável.

**Preservado:** Sinnoh PILOT_NOT_INSTALLED_NOT_PLAYABLE, 0/9 mapas instalados, 0/44 QA nativa, R07/R08/R09 pendentes. Sem mudar Decades, Kanto, Johto, Hoenn, Game.exe, Android ou saves pessoais.

## Testes automatizados

    python -m unittest discover -s tests -p test_sinnoh_j11c_native_overlay.py -v

47 testes positivos e negativos: Ruby Marshal, dois Tilesets reais como objetos, tabela de passagens, remap seguro de nove mapas, preservação de baseline, colisões de MapIDs e reservas, recusa de symlinks, ausência de acessos a saves e bloqueio de staging sem provas. GitHub Actions Linux também roda as regressões J11-B/J11 e o portal. Nenhum artifact publica RXDATA, PNG, MapInfos privados ou recibos locais.
