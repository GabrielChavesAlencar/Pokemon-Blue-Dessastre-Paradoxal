# Kanto — árvores Cut e Pokédex regional KantoDex (151)

## 1. Fonte e comportamento

Referência: [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md), seções 2.4, 4.1 e 7. Em FireRed/LeafGreen, o capitão do **S.S. Anne** concede **HM01 Cut**. As árvores bloqueiam a entrada de **Lt. Surge**, o acesso à área do **Old Amber** no Museu de Pewter e à casa do **HM02 Fly** a oeste de Celadon. O detonado é uma referência para entender os locais e requisitos; **não fornece coordenadas de cada árvore**. As posições são sempre extraídas dos eventos reais `CutTree` dos mapas da fonte Essentials FRLG já verificada.

### Implementação de Cut

- `scripts/regions/kanto_overworld.py` reconhece a convenção Essentials `CutTree` e restaura esses eventos com o **MapID de origem, EventID, X/Y e gráfico originais**; adapta o nome `Cut Tree` para `CutTree` exigido pela engine. Não cria árvores fictícias.
- Cada árvore é um obstáculo sólido `Action Button`, com condição nativa `pbCut` e `pbSmashEvent(get_self)` após sucesso. A remoção do evento usa a lógica normal de campo/salvamento; não troca a árvore por um warp nem apaga outros objetos.
- `scripts/regions/pilot.py` recupera os CutTrees **antes das whitelists** restritivas de Celadon/Fuchsia/Saffron e outros locais ativos. **Outros eventos não aprovados continuam excluídos**. As 45 prévias sem eventos continuam sem árvores artificiais; seu conteúdo será liberado somente com a respectiva fase.
- Se faltar o sprite de uma árvore, ela entra em `Data/blue-kanto-field-events.json → missing_graphics`, com nome e posição, sem criar um bloqueio invisível ou abortar toda a construção.
- O capitão já entrega Cut no `BlueKantoPilot.captain`. A autorização continua sujeita ao requisito local de Kanto para Cut (Cascade Badge/HM/uso por Pokémon, segundo `BlueRegionalPolicy`) e não é concedida por atalhos de teste.

### Auditoria

Na cópia de Kanto, abrir `Data/blue-kanto-field-events.json` e filtrar `imported[].kind = "cut"`. Isso mostra a quantidade real de árvores adicionadas, por mapa, EventID e posição. `verify_pilot.py` valida se cada árvore é sólida, mantém `CutTree` no nome e usa os comandos nativos. A whitelist especial aceita **somente** os CutTrees que constam desse relatório.

## 2. KantoDex, além da Nacional

- A lista nativa `PBS/regional_dexes.txt` da **cópia isolada do piloto** recebe/usa uma seção KantoDex com exatamente as **151 espécies originais de Kanto** em sua numeração tradicional, extraídas de `data/national-species.json`.
- **Bulbasaur nº 001**, Ivysaur nº 002, Venusaur nº 003, Charmander nº 004, Squirtle nº 007 e **Mew nº 151**. Formas novas, evoluções posteriores e variantes não aumentam o total da KantoDex.
- Outras Dex regionais existentes mantêm ordem e índices. Se o PBS já contém uma seção exatamente igual à KantoDex 151, o projeto a reutiliza, sem criar outra cópia.
- A **Pokédex Nacional** continua sendo a lista geral produzida pela engine a partir das espécies instaladas. Não são alterados números nacionais, dados de Pokémon, espécies capturadas/vistas ou dados de treinadores.
- `Data/blue-kanto-dex.json` identifica o índice de seção e se ele foi reaproveitado/adicionado. `BlueKantoDex` apresenta `KantoDex` e `Pokédex Nacional` como duas opções nativas ao abrir o menu, após Oak entregar a Pokédex.
- Saves **antigos do piloto** são adaptados sem apagar dados: quando uma nova seção é incluída, preservam-se as flags das Dex regionais anteriores e move-se a antiga flag da Nacional para sua nova posição; os índices de seleção também são ajustados. **Não** chama `pokedex.clear` nem modifica saves do Decades.

### Limitações

Esta implementação abrange o **piloto isolado de Kanto**. Integrar o sistema de múltiplas Dex ao jogo principal, contemplando Johto/Hoenn/Sinnoh e suas regras, deve ocorrer com controle de migração dos saves e índices existentes. **Não sobrescrever PBS/regional_dexes.txt da instalação principal** somente para experimentar Kanto.

A interface e a compilação nativa requerem que o jogo real com a fonte FRLG seja reconstruído e testado. Testes unitários de estrutura não são prova de funcionamento em `Game.exe`.

## 3. Aceite e teste no Windows

1. Atualizar a `main` pelo `Blue-Story.exe`; encerrar qualquer jogo/piloto em execução.
2. No CMD: `cd /d "%LOCALAPPDATA%\PokemonBlueDessastreParadoxal"` seguido de `KANTO_JOGAR_EXPERIMENTAL.bat --rebuild`.
3. Verificar `Data/blue-kanto-field-events.json` (árvores realmente importadas) e `Data/blue-kanto-dex.json` (151 espécies e índice regional).
4. Começar na casa de Pallet, receber a Pokédex de Oak e abrir o menu: devem aparecer **KantoDex** e **Pokédex Nacional**.
5. Conferir Bulbasaur **001**, Mew **151**, espécies fora de Kanto apenas na Nacional, progresso de vistos/capturados preservado e troca de listas sem travar.
6. Em Vermilion, testar árvore antes/depois de ter Cut e a insígnia permitida, a remoção real do obstáculo e comportamento após salvar/recarregar. Repetir nas áreas ativas de Pewter/Celadon quando os acessos estiverem implementados.
7. Verificar que Decades, Johto, saves e os mapas preview-only não tiveram alterações.

**Status técnico:** a auditoria por fonte local é parte do build. A contagem real de árvores somente é conhecida depois que o piloto for reconstruído a partir dos `.rxdata` presentes no seu computador.
