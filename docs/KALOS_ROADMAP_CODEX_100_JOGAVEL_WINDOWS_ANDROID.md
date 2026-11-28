# Kalos — roadmap Codex até 100% jogável (Windows + Android)

**Projeto:** Pokémon Blue: Dessastre Paradoxal · **Data:** 27/11/2026 · **Fases:** KA00–KA31.
**Alvo:** campanha X/Y unificada em 2D, no Game.exe principal Decades/Blue (RPG Maker XP + Essentials 21.1), 16 cidades, rotas 1–22, interiores, oito ginásios, Equipe Flare, Mega Evolução, Liga e pós-jogo. Um único save e uma única instalação multirregional. Pokémon Legends: Z-A e Kalos histórica são expansões fora deste escopo.
**Estado:** plano operacional; nenhuma etapa de gameplay foi executada. A
[frente de pesquisa e planejamento KD00–KD05](KALOS_PESQUISA_E_PLANEJAMENTO.md)
não ativa Kalos. Execute KA00–KA31 somente após autorização explícita
para implementar; este roadmap não é uma ordem permanente para modificar o jogo.

## 0. Contrato obrigatório de execução

Se a implementação for autorizada, leia [AGENTS.md](../AGENTS.md), este documento e main atual. Não produza apenas contratos, stubs ou novos documentos quando for possível executar e provar a implementação. Priorize lotes pequenos e verticais, reaproveitando o código real. Não copie engine, scripts, banco global ou saves de outro fangame.
- Um lote/PR por vez; confira HEAD SHA completo, base atual e PRs concorrentes. Não force-push, não reverta trabalho alheio, não altere Gary, chefes autorais, Decades, Kanto, Johto, Hoenn, Sinnoh, Unova ou suas reservas. Merge somente após checks obrigatórios e pertinentes aprovados na revisão correta.
- Cada lote perceptível exige publicação Windows **Blue-Story.exe** + Android multirregional **pela fonte** no mesmo produto, hashes e receita validados antes de avançar. Documentação pura e staging privado sem mudança distribuída não exigem releases. Use [regra vigente](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md). Não publique fonte de terceiros sem direitos.
- QA física é diferente de CI, fixture, execução headless ou publicação. Se faltar ambiente, registre BLOCKED_ENV e o teste exato; somente com autorização explícita para adiar QA pode avançar como DELIVERED_WITH_QA_PENDING. Não contabilize como 100% jogável.
- Não use teleportes QA, flags forçadas, mapa fictício, alteração de coordenadas sem auditoria, recompensa concedida por debug ou testes enfraquecidos como prova de campanha. Nunca exponha saves, tokens, ZIP privado ou binários de terceiros em logs/artifacts públicos.
- Preserve saves, MapIDs publicados, IDs de eventos persistentes e chaves de estado; migração aditiva, backup dos arquivos tocados, rollback atômico. Não sobrescreva MapInfos.rxdata, Tilesets.rxdata, System.rxdata, Scripts.rxdata, CommonEvents.rxdata ou PBS globais com arquivos de doador.
- Não importe ROMs comerciais ou OSTs sem autorização. Use fontes legítimas, arquivos próprios/autorizados e atribuições. Disponibilidade de download não comprova licença. Reescreva diálogos e crie arte 2D própria onde necessário.
- Regras compartilhadas: uma insígnia local inédita = uma esmeralda global; Normal 70% / Master 90% do maior Pokémon quando aplicável; level cap e evolução dinâmica vigentes (+5 por nível, pedra >=30, troca >=40, felicidade >=45), XP party ligado, Dynamax desligado, chefes e times-base protegidos. Primeiro desafio de líder/Elite/Campeão sem tetos BST/potência conforme [contrato](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md), Full Power somente após gate global vigente. Não implementar regra paralela de balanceamento em Kalos.
- Viagem livre desde o começo entre regiões efetivamente integradas, exclusivamente por NPC da cidade inicial. Kalos: Vaniville. Respeite implementação atual de depósito da party e Pokémon especiais; teste pré-reserva de Boxes, rollback e chegada sem duplicar inicial. Itens-chave/HMs/atalhos/PC de itens locais, itens comuns compartilhados. Blackout último Centro válido da região, fallback Vaniville. Leia [contrato de viagem](VIAGEM_REGIONAL_LIVRE_NPC.md) e reconcilie divergências históricas com código e testes atuais.

## 1. Baseline e bloqueios

Auditoria de árvore main: tree 0217069c75555709176b144b72e962aac240ad94, 2240 entradas, não truncada (snapshot da consulta inicial; KA00 deve atualizar). Busca de arquivos, issues e commits específicos de Kalos não retornou implementação. Não foi inspecionada instalação privada.
| Evidência | Resultado / ação |
|---|---|
| [Registro regional](../site/public/data/regions.json) | KALOS = planned; base X/Y; oito milestones BUG, CLIFF, RUMBLE, PLANT, VOLTAGE, FAIRY, PSYCHIC, ICEBERG. Reusar chaves sem renomear. |
| Mesmo registro, field | CUT=BUG, STRENGTH=CLIFF, SURF=RUMBLE, FLY=PLANT, WATERFALL=ICEBERG, ROCK_SMASH=ROCK_SMASH_LOCAL; confirmar fonte e compatibilidade nativa, Rock Smash é TM em X/Y. |
| [Novo jogo](NOVO_JOGO_SELECAO_REGIONAL.md) | Kalos indisponível; não adicionar destino falso. |
| [Estudo geral](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md) / [plano v2](PLANO_REGIOES_DESSASTRE_V2.md) | X/Y unificados, Lumiose em distritos, conversão 3D→2D, exclusivos e lendários separados, uma Liga. |
| [MapIDs históricos](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) | 648 ocupados em snapshot 17/11, faixas protegidas e IDs >999 ainda não homologados naquele relatório. Não assumir disponibilidade hoje. |
| [RegionStart](../scripts/battle_polish/RegionStart.rb) / [RegionTravel](../scripts/battle_polish/RegionTravel.rb) | Infraestrutura compartilhada, checagem de origem/destino e manifestos; sem prova Kalos. |
| [Android package](../scripts/android/package.py) | Verificação de regiões existentes, perfil compartilhado e compilação; ampliar sem enfraquecer gates. |
| Kalos-specific workflows, fonte pinada, mapas nativos, release | Nenhum encontrado na árvore auditada. Zero mapas/cidades/rotas/ginásios com aceite comprovado; não equivale a inspeção do disco pessoal. |

Bloqueios prioritários: origem autorizada e cobertura real; alocador multirregional e compatibilidade de IDs; ausência de mapa de abertura; nenhuma prova de execução nativa e atualização. A campanha original é 3D: adapte topologia, puzzles e gameplay, não câmera literal. Aplique a regra por mapa: sem um mapa RPG Maker XP pronto ou quase pronto e aprovado, refaça o local em 2D com os tilesets de Kanto já usados no Blue. Antes de desenhar, consulte o [atlas visual KD05](KALOS_KD05_ATLAS_VISUAL_E_TILES_KANTO.md) e confronte vistas, percurso, saídas e marcos para se aproximar do traçado de X/Y sem copiar seus assets.

## 2. Downloads e fontes verificáveis

| Recurso | Link | Uso e restrição |
|---|---|---|
| Blue | [GitHub](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal) · [ZIP main](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/archive/refs/heads/main.zip) | Clonar main, fixar SHA, usar os instaladores existentes. ZIP não contém jogo comercial. |
| Fire Ash 3.7.1 | [Publicação do autor e downloads MEGA/GDrive](https://www.eeveeexpo.com/threads/9489/) | Candidato primário de topologia 2D. Essentials 19.1, campanha do anime e HMs diferentes; não importar scripts/eventos cegamente. Não foi baixado nem homologado. |
| Virtualization V14 | [Publicação do autor](https://eeveeexpo.com/threads/8573/) · [ZIP indicado na publicação](https://www.mediafire.com/file/jfp2uta28hyncm3/Virtualization_V14.zip/file) | Candidato secundário; campanha própria, cobertura/editabilidade/direitos pendentes. Não assumir compatibilidade. |
| World Project | [GitHub do autor](https://github.com/SocomSeal/The-PMon-World-Project) · [recurso Eevee Expo](https://mail.eeveeexpo.com/resources/1877/) | A publicação consultada informa Kalos 0%; não usar como se já contivesse Kalos completa. Reauditar versão real; pode servir de modelo de estrutura. |
| Recursos | [Eevee Expo](https://eeveeexpo.com/resources/) | Tiles/sprites permitidos, conferir licença individual e atribuição. |
| Jornada X/Y | [Walkthrough X/Y](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_X_and_Y) · [Kalos Serebii](https://www.serebii.net/xy/kalos.shtml) · [Pokéarth](https://www.serebii.net/pokearth/kalos/) | Referências de ordem, topologia, encontros, equipes e serviços; não copiar textos/imagens inteiros. |
| Engine | [Essentials](https://github.com/Maruno17/pokemon-essentials) · [Docs](https://essentialsdocs.fandom.com/wiki/Essentials_Docs_Wiki) · [RPG Maker XP](https://www.rpgmakerweb.com/products/rpg-maker-xp) · [Decades](https://github.com/HazyCrazy/Pokemon-Decades) | APIs v21.1; pin vigente do Blue. Editor licenciado, sem atualização de engine neste lote. |
| Windows | [Releases](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) · [Downloads Blue](https://pokemondessastreparadosal.vercel.app/downloads) · [manual](INSTALACAO.md) | Blue-Story.exe da revisão comprovada. |
| Android | [JoiPlay + RPG Maker Plugin](https://www.joiplay.net/) · [Termux](https://termux.dev/en/) · [manual](ANDROID_ATUALIZACOES_INCREMENTAIS.md) · [releases](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases) | Mesmo canal multiregion, não APK nem piloto independente. |
| CI | [Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions) · [GitHub CLI](https://cli.github.com/) | Consultar workflows, logs, assets e revisões reais. |

Procedimento: adquirir na página original, confirmar autorização de reutilização/distribuição por arquivo, anotar URL final, versão, data, tamanho, SHA-256, créditos, licença, arquivos permitidos e exclusões. Nenhum SHA das fontes Kalos foi verificado; não inventar. Usar cache privado .blue-work/kalos/sources/ (verificar gitignore), SHA256 antes de descompactar; em PowerShell Get-FileHash -Algorithm SHA256 -LiteralPath <arquivo>; Linux sha256sum <arquivo>. Rejeitar traversal, symlinks, arquivos duplicados, bombas ZIP e executáveis do doador; parser inerte isolado, jamais executar código desconhecido ou desserializar objetos arbitrários no processo principal. Se fonte mudar, quarentena e nova auditoria; não alterar hash para fazer teste passar. Criar manifesto de autoria própria se bloqueada. Não usar downloads de ROM ou OST.

## 3. Pontos reais de integração e artefatos propostos

| Camada | Arquivos existentes a inspecionar |
|---|---|
| Instalação | [install_game.py](../scripts/install_game.py), [Bootstrap.cs](../scripts/windows/Bootstrap.cs), [install_kanto.py](../scripts/regions/install_kanto.py), [install_hoenn.py](../scripts/regions/install_hoenn.py), [release_gate.py](../scripts/regions/release_gate.py) |
| Runtime | [RegionStart.rb](../scripts/battle_polish/RegionStart.rb), [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb), [Regions.rb](../scripts/battle_polish/Regions.rb), [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb), TitleKanto.rb, Story.rb, Balance.rb; localizar respawn, Trainer Card, Dex e menu reais. |
| Android | [update_client.py](../scripts/android/update_client.py), [source_update.py](../scripts/android/source_update.py) e [modelo de receita K06](ANDROID_K06_ATUALIZACAO_PELA_FONTE.md); ferramentas binárias apenas para baselines históricas |
| CI | [blue-story-windows.yml](../.github/workflows/blue-story-windows.yml), [android-multiregion.yml](../.github/workflows/android-multiregion.yml), [android-multiregion-repack.yml](../.github/workflows/android-multiregion-repack.yml), [android-updater-regression.yml](../.github/workflows/android-updater-regression.yml), [decades-regional-start.yml](../.github/workflows/decades-regional-start.yml), regression.yml, regional-respawn.yml, evolution-scaling.yml, kanto-gary-regression.yml |
| Site/editor | [regions.json](../site/public/data/regions.json), scripts/export_site_data.py; localizar catálogo de pilotos, downloads e versão in-game. |

Propostas (não existem ainda): data/regions/kalos-source.json, kalos-content-inventory.json, kalos-mapids.json, kalos-story-events.json, kalos-progress.json; scripts/regions/ensure_kalos_source.py, audit_kalos_source.py, prepare_kalos.py, install_kalos.py, auto_integrate_kalos.py, KalosEvents.rb, KalosQATeleport.rb; tests/test_kalos_install.py, kalos_runtime.rb; TESTAR_KALOS.bat. Preferir função genérica existente se suficiente. Não multiplicar plugins/workflows apenas para gerar marcadores. Manifesto instalado deve conter schema_version, revision, source_sha256, map_key→ID estável, ownership, hashes, tileset mapping, spawn, agent, respawn, links, compile receipt, estado e compatibilidade de saves. Publicar apenas relatórios sanitizados.

## 4. Inventário obrigatório e matriz de cobertura

**16 cidades:** Vaniville, Aquacorde, Santalune, Lumiose, Camphrier, Ambrette, Cyllage, Geosenge, Shalour, Coumarine, Laverre, Dendemille, Anistar, Couriway, Snowbelle, Kiloude. Liga é área independente. **22 rotas:** R01–R22, incluindo R08 alta/baixa, R07 leste/oeste, R15/16 e ramificações opcionais; contabilizar submapas físicos separadamente.
| Grupo | Cobertura mínima e vínculos a auditar |
|---|---|
| Abertura | Quarto e térreo Vaniville, casas, R01, Aquacorde, R02, Santalune Forest, R03, Santalune (ginásio/centro/lojas), R04 |
| Centro | Lumiose sul/norte, avenidas e cinco praças, Prism Tower, laboratório Sycamore, cafés, estação, museu, hotel, boutiques, táxis, restaurantes, Looker Bureau, Lysandre Labs; R05, Camphrier, Shabboneau Castle, R06, Parfum Palace e jardins, R07, Berry Fields, Battle Chateau, Connecting Cave |
| Costa | R08 alta/baixa, Ambrette, aquário e Fossil Lab, R09, Glittering Cave, Cyllage, Bike Shop, ginásio, R10, Geosenge, R11, Reflection Cave |
| Mega e energia | Shalour, Tower of Mastery, R12, Skiddo ranch, Azure Bay, Coumarine (marina, teleférico/monotrilho adaptado, ginásio), R13, Power Plant e acessos, Lumiose completa |
| Montanha | R14, Laverre, fábrica de Poké Bolas, R15, Lost Hotel, R16, Dendemille, Frost Cavern, R17, Anistar, Sundial |
| Final | Lysandre Labs, Geosenge Secret HQ, R18, Terminus Cave, Couriway, R19, Snowbelle, R20, Pokémon Village, R21, R22, Chamber of Emptiness, Victory Road, Liga |
| Pós-jogo | Kiloude, estação, Battle Maison, Friend Safari, Unknown Dungeon, Sea Spirit's Den; Looker Bureau, Mega Stones, restaurantes, Chateau, retorno a todos os locais opcionais |

Auditar interiores de cada área, centros, lojas, casas, escadas, caves, elevadores, portas, itens visíveis/ocultos, NPCs, encontros, placas, sinais, puzzles, áreas inacessíveis canonicamente e variantes. Cada entrada do inventário: area_key, tipo, fonte e versão, map_ids, links de origem/retorno, spawn, terreno, tileset, gráficos/áudio, flags, encontros, treinador e eventos, estado windows/android, evidência e motivo de exclusão. Não inventar total de MapIDs a partir do total de cidades. Registrar cada porta transitável e passagem legítima; não criar corredor mágico para conectar mapas desconexos.

## 5. Arquitetura de mapas, eventos e saves

- Ler inventário real de MapInfos/Tilesets/Data e manifestos de TODAS as regiões; reconhecer nomes Map1/Map001/Map1000 e normalizar números, rejeitar duplicatas e colisões. Testar >999 no Game.exe, editor, map factory, compilador, scripts, manifestos, ZIP e JoiPlay antes de usar. Se incompatível, migrar ferramentas (não IDs existentes) e revalidar. Não escolher faixa fixa sem reserva confirmada. Mapear todos os comandos de transferência, páginas, self-switches, mapas conectados, encounter/map_metadata e common events. Remapear referências tipadas; expressões dinâmicas exigem revisão manual.
- Preservar camadas, tiles, autotiles, prioridades, passabilidade, terrain tags e escala do player; bordas com floresta/rocha/água em vez de vazios pretos. Testar portas nos dois sentidos, altura, escadas, pontes, surf embarque/desembarque e obstáculos. Gerar grafo dirigido com arestas condicionais e flood-fill por tile, confirmar alcance e retorno desde o spawn para cada destino, não apenas existência de evento.
- Lumiose: distritos South/North, avenidas/praças e Prism Tower; setores 2D pequenos com conexões físicas e interiores. Gate blackout por energia antes/depois da usina; táxi não contorna flags. Medir memória, FPS, carregamento, transições, áudio e performance em aparelho. Não inventar coordenadas canônicas 3D.
- Eventos com identificador estável Kalos + area + event + versão. Guardar flags no estado regional existente; transações idempotentes para presentes, fósseis, HMs, insígnias, captura, Hall e desbloqueios. Se Bolsa/Box cheia, não consumir recompensa/quest antes de entrega; derrota, cancelamento, exception e reload restauram estado consistente. Não colidir com switches/variáveis de Decades. Testar save/reload em cada marco.
- PBS: merge incremental por chave e versão de treinador; validar espécie/form/move/ability/item contra GameData real, não duplicar espécies; compilar no Essentials nativo. Dados de X/Y unificados por habitat/método, exclusivos plausíveis, pesos normalizados por tabela. Manter originais de referência separados de adaptações. Não gerar encontros de lendários comuns. Registrar source→runtime por treinador/mapa/evento e provar batalha.
- QA: menu Testar Kalos isolado ou com perfil descartável, catálogo de TODOS os MapIDs físicos instalados, mapa/ID/nome/ponto validado, filtros e barra de cobertura. Modo normal não oferece teleporte arbitrário. Nunca usar QA para declarar progressão.

## 6. Sequência das 32 fases

Ordem operacional: KA00–03, depois um corte vertical KA04–08 + KA10–11 (Vaniville até Viola), com KA26–30 aplicados desde o primeiro lote perceptível. Repetir mapas/interiores/conexões/encontros/áudio/QA por corredor até a Liga; KA04–09 são frentes incrementais e só fecham quando a cobertura global estiver comprovada. Não bloquear a abertura esperando todas as cidades. Cada subfase tem PR, implementação real, testes negativos, save/reload, relatório e gate de publicação. Marcadores abaixo são **propostos**, emitidos somente após assertions reais.

### KA00 — baseline reproduzível
Clonar repo, git fetch, git rev-parse HEAD, gh pr list, gh run list, gh release list. Inventariar instalação limpa e instalada, hashes, versão engine, MapIDs, plugins, manifestos, save schema, asset names e release revisions; registrar gates e ferramentas atuais. Testar baseline sem mudanças. Criar tracker Kalos e uma issue de acompanhamento se não houver equivalente. Gate KALOS_KA00_BASELINE_OK: nenhuma lacuna tratada como sucesso; dados privados sanitizados.

### KA01 — fonte e direitos
Adquirir candidatos da seção 2, em sandbox privada, calcular hashes, auditar licença, árvore, formato de mapas, eventos, tilesets, PBS, arte/áudio. Comparar cobertura com seção 4 e selecionar por área, não por nome parecido. Se não houver geometria autorizada, construir terreno próprio com mapa de referência conceitual. Gate KALOS_KA01_SOURCE_AUDIT_OK com proveniência e cobertura; bloqueio explícito para arquivos não autorizados.

### KA02 — MapIDs e referências
Alocar globalmente com auditor de todas as regiões; testar limite real (inclusive >999 se necessário), persistir manifesto imutável, remapear portas, bordas, metadata, encounters, script transfers e eventos; preservar IDs publicados. Testar colisão, mapa ausente, referências dinâmicas, instalação repetida. Gate KALOS_KA02_MAPIDS_NO_COLLISION_OK e recibo nativo.

### KA03 — conversão de assets
Converter tilesets/autotiles autorizados para XP, colisão por camada, sprites jogador/NPC com escala Blue e movimento, animações e áudio autorizado; inventário de paths e hashes. Importar amostra em cópia descartável; testar render e movimento em Windows e JoiPlay, bordas sem preto, transparência e memória. Gate KALOS_KA03_RENDER_RUNTIME_OK.

### KA04 — cidades
Implementar as 16 cidades por grupos da seção 4. Começar Vaniville e Aquacorde: quarto/térreo, ruas, spawn, portas, agente e lojas pertinentes. Para cada grupo instalar exteriores e serviços em mesmo Game.exe, gerar mapa de região/Dex/habitat. Gate por cidade: entrada/saída, cura, compra, interação, save e reload; final KALOS_KA04_16_CITIES_OK.

### KA05 — rotas
Construir R01–R22 com passabilidade, grama/água/pesca, treinadores, itens, obstáculos e mudanças narrativas; iniciar R01–04. Cobrir R06, R07 ambas partes, R08 níveis, R12/13 e todas ramificações; nenhum salto artificial. Gate final KALOS_KA05_22_ROUTES_OK.

### KA06 — áreas naturais
Santalune Forest primeiro; Connecting/Glittering/Reflection Cave, Azure Bay, Frost Cavern, Lost Hotel, Terminus Cave, Pokémon Village, Victory Road e demais locais do inventário. Puzzles, níveis, gelo, escadas, água, spawns e saídas; testar volta segura após blackout. Gate KALOS_KA06_NATURAL_AREAS_OK.

### KA07 — interiores e serviços
Casas, centros, lojas, castelo, palácio, laboratório, aquário, Bike Shop, Day Care, fábrica, estações, ginásios e serviços secundários. Testar portas, retorno, compra/venda, cura, PC, depósito/retirada, ovo, fósseis e diálogos; não aceitar porta decorativa marcada funcional. Gate KALOS_KA07_INTERIORS_SERVICES_OK.

### KA08 — grafo de navegação
Auditar cada aresta nativa com x/y/direção, terreno e flags; flood-fill origem→destino→retorno; paths de surf, strength, cut e montaria. Testar bloqueios negativos, travessias reais, respawn, sem auto-transfer loop. Gate KALOS_KA08_PHYSICAL_CONNECTIVITY_OK. Repetir a cada lote.

### KA09 — Lumiose
Dividir cidade em setores; laboratório, cafés, lojas e torre, energia desligada/ligada, acessos R04/05/13/14/16 conforme referência, táxis, estações, restaurante e museu. Não liberar Prism Tower ou norte prematuramente; após usina restaurar energia persistente, com rollback. Teste completo de ida/volta de cada distrito e benchmark no Android. Gate KALOS_KA09_LUMIOSE_OK.

### KA10 — abertura e inicial
Intro de Sycamore, escolha Lucas/Dawn não se aplica: usar Calem/Serena, nome e aparência conforme UI Blue. Acordar no quarto, amigos em Aquacorde, escolher Chespin/Fennekin/Froakie exatamente uma vez, batalha de Shauna e carta à mãe; Pokédex, Poké Bolas e tutorial conforme fonte. Bloquear grama/combate sem Pokémon apto, preservar escolha após save; visitantes não ganham novo inicial indevidamente. Gate KALOS_KA10_STARTER_OPENING_OK.

### KA11 — Viola
R02/Forest/R03, treinadores e Santalune; patins, puzzle e Viola, Bug Badge, TM correta, Cut local e acesso à R04. Derrota/retry, prêmio único, treinador previamente vencido não duplica. Gate KALOS_KA11_VIOLA_BADGE_OK.

### KA12 — Sycamore, Camphrier, palácio
R04→Lumiose sul, laboratório e batalha do professor, escolha única Bulbasaur/Charmander/Squirtle, Café Soleil/Diantha/Lysandre, R05→Camphrier, castelo, R06/palácio, puzzle Furfrou, Poké Flute, Snorlax R07, Day Care, Berry Fields, Chateau e Connecting Cave. Garantir ordem, alternativas captura/derrota Snorlax, flauta local e retorno. Gate KALOS_KA12_PALACE_SNORLAX_OK.

### KA13 — fósseis e Grant
R08 alta, Dex Coastal, Ambrette lab/aquário, R09 Rhyhorn, Glittering Cave e Flare, escolha Jaw/Sail Fossil única, reviver Tyrunt/Amaura e retorno R08 baixa; bicicleta e ginásio Grant, Cliff Badge/Strength. Testar montaria, escolha, reviver, derrota e saída. Gate KALOS_KA13_FOSSILS_GRANT_OK.

### KA14 — Korrina
R10, Geosenge, R11, Reflection Cave, Shalour, eventos Lucario e rival, Tower of Mastery e puzzle de ginásio Korrina. Rumble Badge e Surf após sequência canônica; teste sem badge/HM/Pokémon apto. Gate KALOS_KA14_KORRINA_OK.

### KA15 — Mega
Reusar sistema existente e catálogo autoral/ZA; Mega Ring, Mega Stone, tutorial de Korrina, escolha/obtenção Lucario conforme fonte, regras de um Mega por batalha, espécie/forma/item corretos, habilidades e stats, animação e retorno após fuga/derrota/save. Não substituir dados globais; testar Charizard X/Y, Lucario, Gardevoir e uma Mega autoral. Gate KALOS_KA15_MEGA_RUNTIME_OK.

### KA16 — Ramos
R12/Skiddo, Azure Bay, Coumarine/ligação marina, rival, ginásio Ramos/Plant Badge, Fly local e acesso R13. Testar retorno, montaria, gate de Fly, Pokédex Mountain no ponto de história correto. Gate KALOS_KA16_RAMOS_OK.

### KA17 — energia e Clemont
R13, Power Plant, luta Flare, restauração persistente, Lumiose norte, Prism Tower quiz, Clemont/Voltage Badge e TM; assegurar que derrota não restaura energia, táxi não contorna gate, save/reload consistente. Gate KALOS_KA17_POWER_CLEMONT_OK.

### KA18 — Valerie e fábrica
R14, Laverre, puzzle de portas e Valerie/Fairy Badge, Poké Ball Factory, Flare, recompensas e liberação R15/16 conforme fonte; testar capturar/reabrir portas, não repetir prêmio. Gate KALOS_KA18_VALERIE_FACTORY_OK.

### KA19 — gelo e Olympia
R15/16, Lost Hotel, Dendemille, Frost Cavern e Flare, Mamoswine R17 após resolução, Anistar Sundial, ginásio Olympia/Psychic Badge. Testar neve, montaria, puzzle, Holo Caster e gate de história. Gate KALOS_KA19_OLYMPIA_OK.

### KA20 — Lysandre, Xerneas/Yveltal
Lysandre Labs, cientistas Aliana/Bryony/Celosia/Mable, Xerosic, chaves/elevadores/puzzles e Secret HQ Geosenge; arma e confrontos conforme X/Y. Definir campanha unificada: um lendário central por escolha/variante; segundo arco separado pós-jogo, sem duplicar clímax. Captura obrigatória se o fluxo canônico exigir, com re-tentativa e Box cheia sem softlock; uso restrito até oito badges quando política exige. Não inventar decisão narrativa definitiva sem registrar aprovação do mantenedor. Gate KALOS_KA20_FLARE_LEGENDARY_OK.

### KA21 — Wulfric
R18, Couriway, R19, Snowbelle, R20/Pokémon Village, retorno Wulfric, puzzle e Iceberg Badge; Waterfall local, R21/R22 acessos. Testar caminho real, oito badges únicos e gates. Gate KALOS_KA21_WULFRIC_OK.

### KA22 — Liga
Victory Road, rival, entrada com oito badges KALOS e marco de história. Malva (fogo), Siebold (água), Wikstrom (aço), Drasna (dragão), Diantha (Mega Gardevoir), Hall da Fama e confronto AZ. Equipes canônicas via PBS, estado Elite e reinício conforme design; derrota em cada sala, retry, cura/itens, Hall único, desbloqueio pós-jogo. Full Power separado e gate global. Gate KALOS_KA22_LEAGUE_HALL_OK.

### KA23 — encontros e Pokédex
Fundir X/Y por habitat/método, Central/Coastal/Mountain Dex, rotas e interiores elegíveis, pesca/surf/caverna/rock smash, hordas e encounters especiais; balanceamento global em runtime, não alterar tabelas canônicas para simular scaling. Validar pesos, IDs, método, forms (Flabébé, Vivillon etc.), site/Habitat Dex. Testar encontros reais de cada método. Gate KALOS_KA23_ENCOUNTERS_DEX_OK.

### KA24 — lendários e especiais
Terminus Cave/Zygarde, Unknown Dungeon/Mewtwo, aves itinerantes e Sea Spirit's Den (regra da escolha original ou adaptação aprovada), segundo lendário X/Y separado; Diancie/Hoopa/Volcanion somente eventos autorizados/adaptação explicitamente definida, não inventar distribuição oficial. Teste fuga/KO/captura, persistência, gating e reaquisição conforme fonte. Gate KALOS_KA24_SPECIALS_OK.

### KA25 — pós-jogo e sistemas secundários
Trem para Kiloude, Battle Maison (formatos suportados, regras/streak/prêmios e derrotas), rival pós-Liga, upgrade Mega Ring, Mega Stones, Looker/Emma/Essentia, Friend Safari offline, Chateau, restaurantes, personalização, patins, bicicleta, Rhyhorn/Mamoswine/Skiddo, Sky/Horde Battles, Amie e Super Training. Catalogar todos os serviços e missões, adaptar dependências de rede desativadas (PSS opcional via sistema Blue, Friend Safari equivalente local); decisões de fidelidade e exclusões aprovadas antes do aceite final. Não obrigar a reproduzir minigames 3D idênticos se equivalente funcional for aprovado. Gate KALOS_KA25_POSTGAME_OK.

### KA26 — áudio e PT-BR (transversal)
Catálogo de cue por mapa, rota, batalha, ginásio, Mega, Flare e Liga; fallback autoral/licenciado explícito, loops, volume e troca de mapas, sem silêncio indevido. Falas PT-BR próprias, nomes consistentes e placeholders, fonte legível no Android, menus, placas e itens. Testar áudio efetivo e textos nos dois runtimes. Gate KALOS_KA26_AUDIO_LOCALE_OK.

### KA27 — multirregional (desde o primeiro piloto integrado)
Estender gate real RegionStart/RegionTravel, spawn quarto e agente Vaniville, seleção Novo Jogo e Testar Kalos, pause Trainer Card e catálogo QA. Disponibilidade somente com manifesto validado, não por flag isolada. Viagens Decades↔Kalos e cada destino efetivamente instalado, em ambos sentidos, desde início sem Liga; party/Box conforme política real, itens-chave regionais e retorno correto. Testar Box cheia, sem espaço na Bolsa, cancelamento, erro e rollback, save antigo e blackout regional. Gate KALOS_KA27_SHARED_TRAVEL_OK.

### KA28 — Windows (desde primeiro lote publicado)
Estender install_game.py e Bootstrap.cs no fluxo normal, não EXE Kalos separado. Fonte pinada, staging, verificação de ownership/MapIDs, compilação e commit atômico, recovery e status claro. Fresh install e upgrade em cópia de release anterior, offline com cache, download interrompido, ZIP corrompido, execução repetida, arquivo local modificado. Validar Game.exe principal com Kalos e regiões existentes; versão/data/revisão visíveis. Gate KALOS_KA28_WINDOWS_INSTALL_OK.

### KA29 — Android (mesmo lote Windows)
Integrar ao Android multirregional pela fonte, preservando canal e baselines existentes. Criar receita com SHA próprio, produto S e fonte original autorizada por SHA-256; compilar localmente em cópia descartável, validar e instalar com confirmação de arquivos e marcador por último. Não redistribuir ZIP ou patch de jogo. Testar cadeia anterior compatível, atualização/repetição, rollback, arquivo modificado, rede, espaço e save; aceitar jogo físico somente com prova no JoiPlay. Gate KALOS_KA29_ANDROID_INSTALL_OK.

### KA30 — migração e regressão (a cada lote)
Fixture real anonimizada/autorizada antes/depois e fresh install. Preservar todos MapIDs/eventIDs, estado regional, flags, item/PC/party/Box, Dex, dinheiro, opções, save slots, checksums e progresso; testar migração N→M aditiva, idempotência, drift, instalação parcial e interrupção. Rodar Gary, balanceamento, evolução, policy, regional respawn, viagens, Kanto/Johto/Hoenn/Sinnoh/Unova conforme integração real. Gate KALOS_KA30_SAVE_REGRESSION_OK.

### KA31 — aceite e publicação final
Playthrough inteiro Vaniville→Diantha/AZ→pós-jogo sem teleporte QA, nas duas plataformas; cobertura 16/16 cidades, 22/22 rotas, 8/8 badges, 4/4 Elite, 1/1 campeão, todos os interiores/áreas/eventos/inventário aprovados ou exclusões explícitas aceitas, zero softlock e falha bloqueante. Publicar par funcional, instalar e atualizar com assets baixados, verificar hashes, revisar site e docs, issue/tracker; gate KALOS_KA31_FULL_NATIVE_ACCEPTANCE_OK somente com recibos.

## 7. Matriz de ginásios, campo e progressão

| Ordem | Líder / cidade / tipo | Chave existente | Aceite |
|---|---|---|---|
| 1 | Viola / Santalune / inseto | KALOS:BUG | Puzzle, TM, Cut |
| 2 | Grant / Cyllage / pedra | KALOS:CLIFF | Escalada, TM, Strength |
| 3 | Korrina / Shalour / lutador | KALOS:RUMBLE | Patins, TM, Surf e Mega em sequência própria |
| 4 | Ramos / Coumarine / planta | KALOS:PLANT | Puzzle, TM, Fly |
| 5 | Clemont / Lumiose / elétrico | KALOS:VOLTAGE | Energia e quiz, TM |
| 6 | Valerie / Laverre / fada | KALOS:FAIRY | Portas, TM |
| 7 | Olympia / Anistar / psíquico | KALOS:PSYCHIC | Puzzle, TM |
| 8 | Wulfric / Snowbelle / gelo | KALOS:ICEBERG | Puzzle, TM, Waterfall |

Conferir recompensas, equipes, níveis e localização de HMs em duas referências antes de gravar PBS/evento. Para cada campo: sem item/recibo local, sem insígnia/flag, sem Pokémon compatível, com Pokémon elegível, save/reload, outra região com item igual, retorno e rollback. Rock Smash é TM, mas evento local conforme registro atual; não tratá-lo como sexto HM. Todas as 8 vitórias são atômicas e únicas; derrota e rematch não contam. Validar 0→8 esmeraldas incrementais, inclusive com esmeraldas prévias.

## 8. Esteira de teste: aproveitar workflows em vez de duplicar

Criar inicialmente um kalos-ci.yml com jobs selecionáveis source/mapids, topology, events/PBS, regional/save, native-private; dividir em workflows específicos se tempo/permissões justificarem. Nomes de jobs/markers propostos, não resultados. Usar paths filters para todos arquivos Kalos e dependências compartilhadas, sem interromper CI das outras regiões. Testes em PR não publicam. Workflows de publicação exigem main, SHA fixo e gates existentes; permissions mínimos; runner descartável, sem segredos em PR de fork, sem salvar dumps privados em artifacts públicos.

Comandos iniciais (confirmar versão/argumentos na main e nos YAMLs; não inventar CLI):
~~~sh
git clone https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal.git
cd Pokemon-Blue-Dessastre-Paradoxal
git fetch origin main
git rev-parse origin/main
gh pr list --state open
gh run list --limit 30
gh release list --limit 30
python -m unittest discover -s tests
ruby tests/region_travel_runtime.rb # conferir argumentos reais do workflow
ruby tests/region_policy_runtime.rb # conferir argumentos reais do workflow
~~~
Usar os comandos reais dos workflows e fixtures isoladas, não executar scripts não auditados. Para Ruby/Python, primeiro usar testes pertinentes e rodar regressão completa antes do merge. Compilação nativa v21.1, GameData carregado e recibo de execução; distinguir sintaxe/fixture do motor real.

Matriz por fase:
| Grupo | Casos positivos e negativos |
|---|---|
| Acesso | spawn, portas ida/volta, colisão, bordas, bloqueio de história, retorno após mudança |
| Eventos | primeira visita, pré-requisito ausente, cancelamento, derrota, retry, repetição, save/reload, prêmio único, Box/Bolsa cheia |
| Batalha | time esperado, formas, nível, movimentos, habilidades, Mega, Normal/Master, chefe protegido, derrota |
| Dados | compilação PBS, links, hashes, cobertura, MapIDs, referencias nativas e nenhum duplicado |
| Viagem | ida/volta, NPC não duplicado em save carregado, itens locais, party/Box, rollback, blackout |
| Plataforma | Windows Game.exe e Android JoiPlay, imagem/áudio, performance, input, atualização, save e retomada |

Recibo por caso: phase, test_id, revision SHA, workflow/job URL, platform/version, fixture hash, map IDs, precondition, ação, resultado observado, expected vs actual, duração e evidência. Sem dado real = NOT_RUN. Guardar logs/prints sanitizados; não usar screenshot de outro build. O gate nativo deve provar que o evento foi executado pelo jogo, não por chamada artificial a handler.

## 9. Instalar e publicar no produto principal

### 9.1 Windows
1. Em runner Windows autorizado, instalar base pela rota real de [install_game.py](../scripts/install_game.py) / Blue-Story, inspecionar --help e comandos do workflow. Cópia descartável, nunca PC/saves do usuário.
2. Montar Kalos via instalador incremental; preparar origem e mapas em staging, verificar manifesto/reservas/hashes, merge PBS/plugins, compilar, verificar, commit atômico e marcar readiness somente após sucesso. Se falhar manter base válida, log e recovery; não travar silenciosamente.
3. Testar fresh, upgrade e repetição com versão anterior efetivamente publicada, sem sobrescrever Game.exe e sem lançar piloto; abrir Game.exe principal, novo jogo Kalos, outro save, viagem, versão in-game com revisão/data/hora.
4. Após merge com checks verdes, verificar [workflow Blue Story](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/blue-story-windows.yml) e eventual workflow compartilhado que gera o EXE. Conferir run/HEAD/base/tag/asset reais, baixar Blue-Story.exe da tag S, SHA-256, testar em instalação limpa e existente. Não presumir que releases/latest é o instalador correto.

### 9.2 Android
1. Usar a mesma revisão funcional S de Windows, em receita própria R declarando S, predecessor compatível e SHA-256 da fonte original autorizada. Usar a origem da receita: sem redistribuir jogo, patch, binários de terceiros ou saves. O ZIP multirregional antigo fica apenas como referência de baselines históricas.
2. Conferir versão e pasta real em leitura, fechar o JoiPlay, preparar cópia temporária e compilar nela. O atualizador verifica dados, plugins, referências/MapIDs e hashes, só depois aplica as alterações previstas e grava o marcador. Em falha, manter/repor o estado anterior.
3. Qualificar separadamente atualização sobre baseline publicada e instalação limpa quando suportada. Evitar troca de canal, cache de outra receita ou downgrade. Ver [plano de validação](KALOS_KD04_VALIDACAO_E_HANDOFF.md) e os [modelos existentes](ANDROID_K06_ATUALIZACAO_PELA_FONTE.md).
4. Testar no aparelho: toque, combate, desempenho, áudio, save/reload, versão e retomada. Sem teste físico, registrar NOT_RUN/BLOCKED_ENV, não alegar aceite.

### 9.3 Gate de publicação sincronizada
Após CI pertinente e merge, verificar Blue-Story.exe público com tamanho/SHA-256 e a tag da receita Android com vínculo comprovado ao mesmo produto S. Conferir baselines e versão de fato instalada, sem misturar canais. Sem uma das publicações ou com regressão, corrigir este lote antes do próximo. Documentação pura não publica versão jogável.

## 10. Progresso e definição de pronto

Tracker proposto site/public/data/kalos-progress.json com 32 fases, subcasos e três dimensões independentes: implementação técnica (fases aceitas/32), cobertura de mundo (áreas/MapIDs/arestas validados sobre inventário congelado revisado), jogabilidade nativa (casos aceitos por plataforma sobre total). Inicialmente 0/32 fases aceitas, 0/16 cidades, 0/22 rotas, 0/8 badges comprovados; fase conceitual não é implementação. Denominador de mapas definido após KA01/02; não fixar percentual arbitrário. Status: NOT_STARTED, IN_PROGRESS, BLOCKED_SOURCE, BLOCKED_ENV, TECH_VERIFIED, DELIVERED_WITH_QA_PENDING, ACCEPTED. Sem omitir bloqueios ao exibir barras. Não reduzir denominador para atingir 100%.
- [ ] 16 cidades, 22 rotas, todos interiores e áreas do inventário, conexões físicas com retorno e sem placeholders.
- [ ] Abertura, rivais, oito badges, Flare, Mega, Liga, AZ, Hall, pós-jogo e todas missões aprovadas.
- [ ] Encontros, serviços, Pokédex, itens, música, PT-BR e mecânicas de campo verificadas.
- [ ] Viagens livres por Vaniville, save compartilhado, PC, itens locais, blackout, regras Blue e regressão preservados.
- [ ] Windows instalação limpa/upgrade e playthrough real, Android JoiPlay e atualização pela fonte/playthrough real; publicações do mesmo produto, hashes e receita.
- [ ] Nenhum bug bloqueante, softlock, porta faltante, recompensa duplicada ou save corrompido; decisões de equivalentes offline e exclusões aprovadas.
- [ ] Documentação, tracker, issue, links de release e recibos atualizados; nenhum dado privado publicado.

## 11. Prompt de retomada (somente após autorizar a implementação)

> Com autorização para implementar, leia AGENTS.md, este roadmap e a frente documental KD00–KD04. Reconfirme main, PRs, workflows e releases atuais; inicie KA00 e execute KA01–03 com fontes autorizadas e auditoria real, não apenas planejamento. Priorize o primeiro corredor Vaniville→Aquacorde→Santalune até Viola, implementando mapas, portas, eventos e testes nativos em lotes verticais. Reaproveite RegionStart, RegionTravel, instalador principal e canal Android multiregion; preserve saves, MapIDs, Gary, balanceamento e demais regiões. Não force flags, não invente recibos, não afrouxe testes. Merge somente após aprovação integral; para cada mudança jogável publique Windows e Android na mesma revisão, valide EXE, hashes e receita Android pela fonte, disponibilize Blue-Story.exe e registre documentação/issue. Quando fonte ou hardware estiver bloqueado, registre insumo exato, continue somente trabalho independente e não marque 100%. Informe concisamente fase, PR, SHA, CI, evidência real, publicação, bloqueio e próximo passo.

**Regra final:** 100% só quando o jogo principal distribuído nas duas plataformas realmente permite a campanha e pós-jogo completos, não quando a documentação ou CI estiver verde.
