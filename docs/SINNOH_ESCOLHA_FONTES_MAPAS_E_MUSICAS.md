# Sinnoh — escolha fundamentada das fontes de mapas e músicas

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Pesquisa:** 13/11/2026  
**Destino:** RPG Maker XP + Pokémon Essentials v21.1 (motor de jogo/batalha Blue/Decades preservado)  
**Estado:** análise documental e pesquisa de fontes; **não houve download, auditoria binária nem importação de mapas ou músicas de Sinnoh**.

> **Decisão:** entre os cinco fangames de Sinnoh já registrados em `docs/ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md`, **Pokémon Ancient Platinum (Phantombass)** é o melhor candidato para **investigar o conjunto de mapas e eventos**, porque a versão 1.0.6 é declarada concluída, usa Essentials v21.1 e se baseia em Platinum. **Não está comprovado que a distribuição inclua projeto RMXP-fonte editável ou permissão para copiar seus mapas/áudios.** Para **fidelidade dos locais e músicas**, a referência principal deve ser **Pokémon Platinum**, complementada por Diamond/Pearl e, opcionalmente, BDSP. **Não foi confirmado um map pack completo, aberto e autorizado de Sinnoh pronto para importar.**

## 1. Documentos da main analisados e contratos a preservar

- [Estudo de todos os fangames](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md): lista **Ancient Platinum, Platinum Dawn, Banished Platinum, Uprising e Fire Ash**; avisa que essa lista é preliminar, não auditoria de assets ou licença; escolhe Platinum como base geográfica.
- [Plano multirregional v2](PLANO_REGIOES_DESSASTRE_V2.md): campanha-base **Platinum + conteúdos distintos de Diamond/Pearl**, BDSP apenas complementar; **Sinnoh libera Hoenn e Unova** depois da primeira vitória na Liga; admite Sinnoh como região inicial quando instalada.
- [Fontes de Johto](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md) e [fontes de Hoenn](HOENN_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md): separar **referência narrativa/visual**, **fonte técnica realmente editável** e **catálogo musical**. Um pacote de mapas não significa eventos, interiores, NPCs ou músicas completos.
- [Implementação definitiva de Johto](JOHTO_IMPLEMENTACAO_DEFINITIVA_MAPAS_EVENTOS_NPCS_ITENS_MUSICAS.md), [plano de Johto](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) e [circuito regional](CIRCUITO_REGIONAL.md): importação isolada, dry-run, manifesto de IDs, backup, rollback, testes e distinção entre **fase tecnicamente preparada** e **aceite jogável**.
- [Editor de músicas](EDITOR_MUSICAS.md), [plano musical de Kanto](KANTO_PLANO_APLICAR_MUSICAS.md) e [mapeamento musical de Kanto](KANTO_MUSICAS_MAPEAMENTO.md): usar BlueMusic, BGM/ME, associação por evento real, sem substituir músicas de Decades e sem confundir publicar um MP3 com aplicá-lo/testá-lo.
- [README](../README.md): `game/` contém a base local Decades, fora do GitHub; os scripts/estudos do repositório não são, por si, cópia jogável completa.

**Regra central:** de Sinnoh vêm somente **conteúdo regional autorizado** (mapas, arte, eventos reescritos, encontros, NPCs, equipes e faixas liberadas); **batalhas, IA, BST/nível escalonados, Pokémon/PBS globais, saves, PC, BlueMusic, pokédex, seleção e viagem entre regiões** continuam sendo os sistemas do Blue/Decades.

### 1.1. Regra obrigatória: criar Sinnoh sem quebrar o que já existe

**Prioridade absoluta:** todas as fases de Sinnoh são **aditivas, isoladas, reversíveis e acompanhadas de provas de não regressão**. O desenvolvimento **não pode quebrar Decades, Kanto, Johto, Hoenn em preparação, Blue Studio, Pokédex/Habitat Dex, site, BlueMusic, multiplayer, saves ou instaladores**.

1. **Baseline real:** em cada fase, inventariar SHA da main, hashes de assets, MapIDs/tilesets, plugins, switches, variáveis, saves e testes anteriores. A ausência de arquivos do jogo no GitHub não autoriza presumir que IDs estão livres.
2. **Trabalhar fora do jogo principal:** guardar fonte em \`.blue-work/sinnoh-source/\`, preparar \`.blue-work/sinnoh-pilot/\` com saves exclusivos. **Nunca despejar** \`Data/\`, \`MapInfos.rxdata\`, \`Tilesets.rxdata\`, \`Scripts.rxdata\`, \`System.rxdata\` ou \`PluginScripts.rxdata\` do doador por cima da instalação local Decades.
3. **Remapear, não sobrescrever:** criar manifesto \`source_map_id -> destination_map_id\`, conferir referências de transferências, tilesets, eventos, PBS e músicas. Reservas de Johto e futuras de Hoenn precisam de respeito; **não pressupor que IDs 1000+ são suportados** sem testar.
4. **Sistema único:** níveis, badges/esmeraldas, BST, IA, encontros, equipes, Saves, PC, Box de Pokémon especiais, viagem, HMs e BlueMusic sempre utilizam adaptadores atuais do Blue/Decades; **sem motor de batalha de Ancient Platinum** ou fórmulas de nível paralelas.
5. **Transações e backup:** importar somente depois de \`dry-run\` e validação de licenças, com backups e rollback. Mudanças em registros de mapas, plugin ou save devem ser idempotentes e migráveis.
6. **Estado não enganoso:** Sinnoh fica \`planned\` até obter mapas reais e piloto auditado. A presença do botão ou de documentação **não significa que Sinnoh já é jogável**. Nunca inventar mapas, NPCs, música, logs de teste ou sucesso no Windows/Android.
7. **Prova obrigatória:** rodar testes automáticos e posteriormente execução gráfica no \`Game.exe\` Windows e teste específico no JoiPlay/Android. Sem prova nativa, não elevar a barra de **aceite integral**.

**Documento operacional vinculado:** [SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md) — contém o ciclo seguro de 13 fases, mapas, eventos, NPCs, itens, música, menu, checkpoints, regressões e rollback.

### 1.2. Mesmo menu inicial: Testar Kanto, Testar Johto e Testar Sinnoh

**A opção \`Testar Sinnoh\` já foi acrescentada ao código do menu principal** em [\`scripts/battle_polish/TitleKanto.rb\`](../scripts/battle_polish/TitleKanto.rb), depois de \`Testar Kanto\` e \`Testar Johto\`. A ordem esperada no \`Game.exe\` normal é:

\`\`\`text
Continuar (se houver save)
Novo Jogo
Testar Kanto
Testar Johto
Testar Sinnoh
[demais comandos nativos: Mystery Gift, Opções, Sair, ...]
\`\`\`

- O plugin preserva **os índices originais** do Essentials/Auto Multi Save, os vários slots e as setas negativas do carregador, sem substituir sua lógica de \`Continue\` e \`New Game\`.
- O terceiro piloto **não** reutiliza mapas, saves, BAT ou scripts de Kanto/Johto. Só abrirá quando existirem **ambos** \`SINNOH_JOGAR_EXPERIMENTAL.bat\` e \`scripts/regions/pilot_sinnoh.py\` próprios, com fonte real auditada e marcador \`Sinnoh pilot.json\` dentro da cópia experimental. **Esses dois arquivos ainda não existem**: são entregáveis da **Fase 02**.
- Sem os arquivos, selecionar Sinnoh informa **"Sinnoh ainda está em preparação"**, retorna ao menu sem fechar o jogo principal e mantém as outras regiões intactas.
- O comando não aparece dentro de um piloto, impedindo recursão. Em outra plataforma, não executar \`cmd.exe\`; piloto Windows ou pacote Android só após validação específica.
- Os testes headless \`tests/title_kanto_runtime.rb\` e \`tests/test_title_kanto.py\` foram estendidos para conferir posição da opção, índices do jogo, Mystery Gift, perfis e isolamento. **Ainda não são prova de Game.exe/jogabilidade Sinnoh.**

**Não elevar as barras só por incluir \`Testar Sinnoh\`:** a Fase 02 exige criar e executar **um piloto com mapas reais**, entrar na casa inicial em Twinleaf e salvar/carregar sem tocar nos saves principais. Os testes de contratos devem passar; a aceitação integral exige provas na janela real do jogo e nos ambientes prometidos.


## 2. Comparação dos cinco fangames da lista original

| Candidato | Evidência publicada | Adequação à campanha canônica | Compatibilidade / lacunas | Decisão |
|---|---|---|---|---|
| **Pokémon Ancient Platinum** (Phantombass) | [Página do autor na Eevee Expo](https://eeveeexpo.com/threads/9085/): **v1.0.6**, estado **concluído**, **Essentials v21.1**, mapas feitos pelo autor, história reordenada, novos sistemas de IA, dificuldade e documentos de treinadores/itens | **Alta para inventário geral de Sinnoh**, mas comparar rota por rota com Platinum, pois o enredo foi modificado | Mesmo ramo de Essentials do Blue, mas diferenças de scripts/plugins e **sem prova de licença nem projeto-fonte redistribuível** | **1º — referência de fangame preferida; primeiro pacote a auditar, não instalar diretamente** |
| **Pokémon Banished Platinum** (Zygoat) | [Página do autor](https://eeveeexpo.com/threads/3305/): preserva personagens, layout e elementos de Platinum; adiciona gráficos estilo Gen 5 e músicas remasterizadas de Zame. A própria página ainda descreve o **último conteúdo de demo como 4 ginásios/até Route 213** | **Alta para ambientes já feitos**, mas cobertura integral não demonstrada | Música de arranjador terceiro exige permissão; versões/status da página não provam uma campanha final completa nem mapas-fonte abertos | **2º — excelente comparação visual, não assumir Sinnoh completa** |
| **Pokémon Platinum Dawn** (TEAM FireAsh) | [Ficha secundária](https://www.astartgaming.com/2025/07/pokemon-platinum-dawn-rpgxp-fangame.html): **v1.1**, 01/07/2025, RPGXP, “playable”, nova história, região de Sinnoh. **Não foi localizada nesta pesquisa uma página técnica primária com inventário de mapas/versão de Essentials** | Incerta; nova história e progresso não especificado | Sem confirmação independente de completude, compatibilidade, fonte editável e licenças | **3º provisório — candidato de auditoria apenas** |
| **Pokémon Uprising** (Project Insurgent) | [Site da equipe](https://project-insurgent.github.io/web/Index.html): **v1.3.1** divulgado; história situada **13 anos após Platinum** | Boa inspiração para um **pós-jogo/era alternativa**, não reprodução canônica direta | Site não confirma pacote-fonte RMXP aberto nem equivalência completa de mapas/eventos | **4º — referência narrativa secundária** |
| **Pokémon Fire Ash** | [Publicação da equipe](https://www.pokecommunity.com/threads/pok%C3%A9mon-fire-ash-version-3-7-1-out.531791/): RPG Maker XP + **Essentials v19.1**, diversas regiões, incluindo Sinnoh; acompanha Ash e o anime | Média: fornece visão multirregional, mas ordem da trama/mapas é do anime | Versão do Essentials diferente; nenhum direito ou fonte editável de Sinnoh confirmado | **5º — arquitetura multirregional como referência, não base primária** |

**Critério do ranking:** importância para **reconstruir a Sinnoh de Platinum no Blue**, não qualidade dos fangames como entretenimento. **“Concluído” qualifica o jogo distribuído, não garante que todos os interiores, eventos, tilesets ou arquivos `.rxdata` estejam acessíveis.** Em caso de evidência nova, reavaliar o ranking.

### 2.1. Por que Ancient Platinum vence

1. A página do próprio autor indica **Essentials v21.1**, o mesmo ramo documentado para a base Blue, reduzindo custo de inspeção de dados (mas não de integração de plugins).
2. O jogo é declarado **completo**, vantagem importante sobre demos e referências narrativas alternativas.
3. A origem é diretamente **Platinum**, incluindo um ambiente geral de Sinnoh mais apropriado que uma jornada guiada pelo anime.
4. O autor declara ter feito a maior parte do mapeamento e fornece documentação de equipes/itens, útil para **inspeção comparativa**.
5. **Desvantagem:** é um remake com **história reordenada**, IA e batalhas muito modificadas. Sua geografia e roteiro **não são fonte normativa**: comparar cada trecho com Platinum e nunca importar seus sistemas de batalha.

**Bloqueadores antes de copiar qualquer arquivo:** verificar se o download do autor contém `Data/MapXXX.rxdata`, `MapInfos.rxdata`, `Tilesets.rxdata`, `Graphics/Tilesets`, `Graphics/Autotiles`, `Graphics/Characters`, `PBS` e `Audio`; conferir se esses arquivos estão realmente editáveis; identificar autores de cada asset; obter autorização de uso/distribuição. Se não houver liberação, **usar apenas como referência** e desenhar os mapas/recursos próprios ou de fontes expressamente licenciadas.

## 3. Candidato técnico fora da lista: The Pokémon World Project

- [Página do recurso v21.1](https://eeveeexpo.com/resources/1877/) e [repositório de SocomSeal](https://github.com/SocomSeal/The-PMon-World-Project).
- O repositório **possui** a pasta `The Pokémon World Project - Sinnoh/` e estrutura `Audio/`, `Data/`, `Graphics/`, `PBS/`, mas **ter a pasta não significa ter a região implementada**.
- **Auditoria da listagem em 13/11/2026:** na pasta `Sinnoh/Data` foram encontrados **somente `Map001.rxdata` e `Map002.rxdata`**, além dos arquivos-padrão da engine. A página de andamento do criador declara **SINNOH — 0% de world mapping e história ainda pendente**.
- Portanto, **não** reaproveitar o pacote de Hoenn do World Project como se fosse Sinnoh, nem afirmar que o projeto já tem Sinnoh completa. Se a fonte for atualizada, auditar um **commit específico** antes de mudar o diagnóstico.
- Recursos individuais publicados na comunidade poderão preencher lacunas **somente após auditoria de formato e de licença**. Não foi encontrado nesta pesquisa um map pack de Sinnoh equivalente, em completude e autorização comprovada, ao Map Pack de Kanto/Johto.

### 3.1. Matriz de fontes e prioridade

| Camada | Referência escolhida | Política |
|---|---|---|
| Geografia, ordem da campanha e elementos canônicos | **Pokémon Platinum** | Autoridade narrativa e de progressão; comparar diferenças Diamond/Pearl |
| Primeiro **fangame para investigar mapas** | **Ancient Platinum** | Inventário e comparação em isolamento; uso de assets condicionado à permissão |
| Referência visual secundária | **Banished Platinum** | Usar para ideias de ambientação, não como pacote completo confirmado |
| **Mapas editáveis prontos** | **Nenhum pacote completo confirmado** | Buscar recurso próprio/autorizado; World Project ainda em 0% |
| Encontros/treinadores/itens oficiais | Platinum; variantes Diamond/Pearl onde agreguem conteúdo real | Incorporar sem duplicar um ginásio ou Liga |
| Trilha e funções musicais | **Diamond/Pearl + faixas exclusivas de Platinum** | Apenas catálogo e direção musical até ter áudio legalmente reutilizável |
| Arranjos alternativos | BDSP e remixes autorizados, individualmente | Conferir autorização do arranjador e da composição |
| Regras de batalha, saves, balanceamento | **Blue/Decades** | Não copiar scripts ou IA de fangames doadores |

## 4. Música: melhor repertório e implementação no BlueMusic

**Escolha musical principal:** **Pokémon Platinum**; a maior parte da trilha vem de Diamond/Pearl, mas **Platinum traz faixas próprias** como Distortion World, Giratina e temas adicionais de pós-jogo. Para identificar nomes, versões dia/noite e cenas, usar os catálogos:

- [Pokémon Diamond & Pearl: Super Music Collection — lista de faixas](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_DP_music).
- [Pokémon Jukebox — seleção de temas exclusivos de Platinum](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Jukebox).
- [Guia da campanha Platinum](https://bulbapedia.bulbagarden.net/wiki/Appendix:Platinum_walkthrough) para conferir em quais mapas/cenas cada música deve ser ativada.

**Direitos:** trilhas oficiais e remixes não ficam livres por constarem na internet, em ROM, em pacote de fã ou em Sound Library. Música comercial, seus arranjos e gravações exigem permissões adequadas ao uso pretendido; **não subir MP3/OGG/MIDI não autorizado na main**. Em falta de faixas licenciadas, manter música atual/fallback de Blue/Decades no piloto e registrar o slot como `pending_audio_rights`.

### 4.1. Catálogo funcional proposto (não é inventário de arquivos instalados)

| Chave BlueMusic proposta | Referência temática | Aplicação condicional | Tipo |
|---|---|---|---|
| `SINNOH_TWINLEAF_DAY` / `SINNOH_TWINLEAF_NIGHT` | Twinleaf Town (Day/Night) | Exterior de Twinleaf, por horário | BGM |
| `SINNOH_ROUTE_201_DAY` / `SINNOH_ROUTE_201_NIGHT` | Route 201 (Day/Night) | Route 201, e outras rotas que compartilhem a composição **após conferência** | BGM |
| `SINNOH_LAKE` | Lake | Lagos quando sua música nativa se aplica | BGM |
| `SINNOH_SANDGEM` | Sandgem Town | Sandgem; variante noturna quando comprovada | BGM |
| `SINNOH_ROWAN_LAB` | The Pokémon Lab | Laboratório de Rowan | BGM |
| `SINNOH_JUBILIFE` | Jubilife City | Cidade e seus setores; respeitar dia/noite | BGM |
| `SINNOH_ROUTE_203` | Route 203 | Trechos com esse tema no Platinum | BGM |
| `SINNOH_OREBURGH` | Oreburgh City | Cidade; não confundir com Oreburgh Mine | BGM |
| `SINNOH_OREBURGH_MINE` | Oreburgh Mine | Mina e locais com a mesma composição conferida | BGM |
| `SINNOH_FLOAROMA` | Floaroma Town | Cidade das flores | BGM |
| `SINNOH_ETERNA_FOREST` | Eterna Forest | Floresta, respeitando eventos da Cheryl | BGM |
| `SINNOH_ETERNA_CITY` | Eterna City | Cidade de Gardenia | BGM |
| `SINNOH_ROUTE_206` | Route 206 | Rota/ciclovia conforme composição real | BGM |
| `SINNOH_HEARTHOME` | Hearthome City | Cidade, por horário se aplicável | BGM |
| `SINNOH_ROUTE_209` | Route 209 | Rotas cujo tema real for Route 209 | BGM |
| `SINNOH_VEILSTONE` | Veilstone City | Cidade, respeitando dia/noite | BGM |
| `SINNOH_PASTORIA` | Pastoria City | Cidade e entorno onde o tema couber | BGM |
| `SINNOH_CANALAVE` | Canalave City | Cidade portuária e variantes de horário | BGM |
| `SINNOH_IRON_ISLAND` | Tema da área correspondente em Platinum | Ilha de Ferro; **confirmar nome exato no áudio** | BGM |
| `SINNOH_ROUTE_216` | Route 216 | Neve e estradas glaciais associadas | BGM |
| `SINNOH_SNOWPOINT` | Snowpoint City | Cidade e áreas associadas ao tema | BGM |
| `SINNOH_MT_CORONET` | Mt. Coronet | Caverna, caminhos e escalada; separar cenas especiais | BGM |
| `SINNOH_SPEAR_PILLAR` | Spear Pillar / tema de cena apropriado | Somente ao alcançar o cume e os eventos correspondentes | BGM |
| `SINNOH_DISTORTION_WORLD` | Distortion World **(Platinum)** | Mundo Distorcido, com prioridade de cena | BGM |
| `SINNOH_GALACTIC_HQ` | Team Galactic HQ | Quartel Galáctico | BGM |
| `SINNOH_SUNYSHORE` | Sunyshore City | Cidade final da jornada de insígnias | BGM |
| `SINNOH_VICTORY_ROAD` | Victory Road | Estrada da Vitória | BGM |
| `SINNOH_SURF` | Surf | Apenas enquanto o estado de Surf estiver ativo | BGM campo |
| `SINNOH_WILD` | Battle! (Wild Pokémon) | Selvagens de Sinnoh sem override específico | BGM batalha |
| `SINNOH_TRAINER` | Battle! (Trainer Battle) | Treinadores comuns da região | BGM batalha |
| `SINNOH_RIVAL` | Battle! (Rival) | Barry, somente no contexto da luta correta | BGM batalha |
| `SINNOH_GYM` | Battle! (Gym Leader) | Oito líderes locais | BGM batalha |
| `SINNOH_GALACTIC` | Battle! (Team Galactic) | Recrutas da equipe | BGM batalha |
| `SINNOH_GALACTIC_COMMANDER` | Battle! (Team Galactic Commander) | Mars/Jupiter/Saturn em suas batalhas | BGM batalha |
| `SINNOH_CYRUS` | Battle! (Team Galactic Boss) | Cyrus, quando a luta realmente começar | BGM batalha |
| `SINNOH_GIRATINA` | Battle! (Giratina) **(Platinum)** | Evento/captura de Giratina, sem usar na batalha de Cyrus | BGM batalha |
| `SINNOH_ELITE_FOUR` | Battle! (Elite Four) | Aaron, Bertha, Flint e Lucian | BGM batalha |
| `SINNOH_CYNTHIA_INTRO` | Champion Cynthia | Introdução pré-batalha, não luta comum | BGM cena |
| `SINNOH_CHAMPION` | Battle! (Champion) | Cynthia | BGM batalha |
| `SINNOH_FRONTIER` | Temas da Battle Frontier de Platinum | Pós-jogo **quando implementado** | BGM |
| `SINNOH_BADGE_ME` | Vinheta de insígnia | Após a entrega de cada insígnia, exatamente uma vez | ME |
| `SINNOH_ITEM_ME` | Obtained an Item! | Após recebimento efetivo de item | ME |
| `SINNOH_HALL_OF_FAME` | Hall of Fame e vinheta de confirmação | Entrada confirmada no Hall of Fame | BGM/ME separados |

**Atenção:** são *chaves de planejamento*, não mapa de IDs, filenames, duração, hashes ou quantidade de músicas comprovadas. Confirmar cada associação com Platinum antes do `apply`. Não criar duplicações por cidade para uma composição compartilhada. As faixas de dia/noite só trocam quando há versão efetivamente disponível e o jogo possui o horário correspondente.

### 4.2. Regras de prioridade musical

1. Cena com música forçada (por exemplo Cyrus, Giratina, Hall of Fame) tem prioridade sobre a música do mapa.
2. Batalha tem prioridade sobre BGM de ambiente; ao terminar, restaurar o mapa/horário sem loop duplicado.
3. Surf, bicicleta, cavernas, neve e horário respeitam as prioridades já implementadas no Blue.
4. Não ativar vinhetas ME antes de entrega confirmada de insígnia/item; uma única execução por concessão.
5. Se a faixa regional não existe ou falha, usar fallback seguro **sem silenciar Decades/Kanto/Johto/Hoenn**.
6. Comparar hashes de origem/destino, BGM versus ME, volume/tom, loop/fade, troca de região, derrota e load; validação técnica não substitui **audição manual** no Windows/Android.

## 5. Escopo mínimo de mapas e eventos para Sinnoh

**Linha-base:** Platinum. Referência de ordem canônica: [walkthrough de Platinum](https://bulbapedia.bulbagarden.net/wiki/Appendix:Platinum_walkthrough). Mapear **interiores, entradas, saídas, atalhos, andares de cavernas, portões, NPCs e itens**, não apenas o mapa-múndi.

1. **Abertura:** quarto/casa do jogador em **Twinleaf Town**, Barry, Route 201, Lake Verity, Professor Rowan, evento dos três iniciais no contexto **de Platinum**, Sandgem e Pokédex. Não importar o roteiro de Ancient Platinum se mudar a ordem canônica.
2. **Primeira insígnia:** Jubilife, Route 203, Oreburgh Gate, Oreburgh, mina, Roark.
3. **Segunda:** Floaroma, Valley Windworks, Mars, Eterna Forest/Cheryl, Eterna City, Gardenia e prédio Galactic.
4. **Hearthome a Pastoria:** Cycling Road, Mt. Coronet inicial, Hearthome/Fantina, Solaceon, Veilstone/Maylene, praias e Pastoria/Crasher Wake, Great Marsh.
5. **Canalave a Snowpoint:** Celestic, lagos, Canalave, Iron Island/Riley, Byron, nevasca Route 216/217, Snowpoint/Candice e Lake Acuity.
6. **Clímax Platinum:** Galactic HQ, Cyrus e comandantes, múltiplos andares do **Mt. Coronet**, Spear Pillar, **Distortion World** e Giratina. Testar cada transição, desnível e evento sem presumir que uma caverna inteira seja um mapa único.
7. **Final:** Route 222, Sunyshore/Volkner, Route 223, Victory Road, Elite Four **Aaron, Bertha, Flint, Lucian** e campeã **Cynthia**; Hall of Fame, retorno seguro e viagem regional.
8. **Pós-jogo:** Battle Zone, Fight/Survival/Resort Area, Stark Mountain, Heatran, Turnback Cave, Iron Island, Fullmoon/Newmoon Island, Shaymin e Darkrai **somente quando houver conteúdo e condições narrativas válidas**; Battle Frontier como subsistema separado, sem fingir funcionalidade.
9. **Extras Diamond/Pearl:** exclusivos, encontros, diálogos e personagens que acrescentem conteúdo sem duplicar ginásios/Liga. **BDSP** serve de referência opcional de visual, itens e revanche, não modifica automaticamente os eventos Platinum.

**Sistemas próprios de Sinnoh a estimar separadamente:** neve/pegadas, descidas/escorregões, Rock Climb, Defog, bicicletas, lama da Great Marsh, Honey Trees, Pokétch, Underground, Poké Radar, parceiros NPC (Cheryl, Riley), distorção gravitacional e transportes. Cada item deve ter aceite técnico e jogável; um mapa estático não reproduz esses sistemas.

## 6. Integração com a regra multirregional do Blue

- **Início livre validado:** quando Sinnoh estiver instalada, permitir nova partida em **Twinleaf**, na casa/quarto do jogador; caso contrário, `status: planned`. Não confundir a existência de um botão de teste com campanha pronta.
- **Viagem:** NPC de viagem regional permanente na **cidade inicial Twinleaf**, com destinos já desbloqueados; outro NPC após a Liga oferece viagem e retorno, seguindo `PLANO_REGIOES_DESSASTRE_V2.md`. **Vencer a Liga de Sinnoh pela primeira vez libera Hoenn e Unova**. Regiões previamente liberadas continuam disponíveis.
- **Insígnias/esmeraldas:** oito conquistas locais próprias. **Uma insígnia inédita = uma unidade** na progressão global *já existente* de esmeraldas, com idempotência (sem somar em revanche ou recarregamento). **Não programar fórmula nova nem fixar níveis de treinador**; adaptar equipes e evolução segundo o cálculo global do Blue, preservando equipe canônica e variações.
- **Especial por região:** lendários, míticos, Ultra Beasts e Paradoxos só podem integrar a party em Sinnoh com **8/8 insígnias de Sinnoh**. Ao chegar sem essas insígnias, depositar os especiais na Box com segurança e impedir retirada; manter os Pokémon, os níveis e o save íntegros.
- **Saves:** preservação de ``MapIDs`` existentes, migração de saves antigos e perfis de teste isolados. Testar ida/volta Sinnoh ↔ Hoenn/Unova e mundos anteriores, evitando respawn em mapa inexistente.
- **Site/guia:** mapas por local, treinadores, encontros e times oficiais de cada líder/Elite/Cynthia com variações de pós-jogo, **sem exibir um nível fixo**, porque a regra nativa calcula o nível por progresso.
- **Hub e modos de laboratório:** não misturar dados de campanha com testes, saves alternativos ou saves multiplayer.

### 6.1. HMs de Platinum: exigência local específica

Conforme [`PLANO_REGIOES_DESSASTRE_V2.md`](PLANO_REGIOES_DESSASTRE_V2.md), `19.5:

| Ação de campo | Insígnia de Sinnoh |
|---|---|
| Rock Smash | Coal — Roark |
| Cut | Forest — Gardenia |
| Fly | Cobble — Maylene |
| Defog | **Relic — Fantina** |
| Surf | **Fen — Crasher Wake** |
| Strength | Mine — Byron |
| Rock Climb | Icicle — Candice |
| Waterfall | Beacon — Volkner |

**Ponto sensível:** em Platinum, **Defog → Relic** e **Surf → Fen**; não usar os requisitos trocados de Diamond/Pearl. Insígnias de outras regiões não autorizam automaticamente HMs de Sinnoh.

## 7. Pipeline para importar com segurança quando os arquivos reais estiverem disponíveis

**Não executar agora**: a fonte editável/autorizada de Sinnoh ainda não foi fornecida nem auditada.

1. Criar registro de proveniência por jogo, URL, versão, licença, autores, hash SHA-256 e conteúdo recebido; trabalhar com **cópia isolada**, nunca na `game/` ativa.
2. Inventariar `Data/Map*.rxdata`, `MapInfos.rxdata`, `Tilesets.rxdata`, `Graphics/`, `Audio/`, `PBS/`, versão de Essentials e dependências. Auditar arquivos sem executar scripts de terceiros.
3. Registrar **`source_map_id -> destination_map_id`** e destinos globais; procurar faixas livres **depois** de verificar Decades, Kanto, Johto e Hoenn, sem presumir números de mapas. Congelar IDs previamente publicados.
4. Remapear referências de transferência, conexões, tileset, autotile, switches/variáveis, common events, itens, NPCs, clima, Pokémon selvagens, localização Pokégear/Fly, eventos de derrota e retornos.
5. Recriar/adaptar eventos com APIs próprias do Blue e compilar PBS sem importar motor de batalha, `Scripts.rxdata`, `PluginScripts.rxdata`, `System.rxdata` ou saves do fangame de origem.
6. Associar músicas apenas a cenas/mapas **confirmados**, com fallback e direitos verificados. Preservar globalmente preferências e áudio existentes.
7. Implementar `--dry-run` padrão; gerar diff, relatório de colisões e cópias de segurança com hashes. `--apply` só após pré-requisitos, verificação de licença e rollback disponível.
8. Rodar validação estática e nativa em cópia local Windows, depois JoiPlay Android, incluindo save/reload, colisão, neve, HM, encontros, evolução por progresso, batalhas, retorno e efeitos.
9. Publicar **apenas** documentação, manifests, código próprio de integração e recursos cuja redistribuição esteja autorizada; **não subir pacote de jogo/ROM/audio de terceiros para a main por acidente**.

**Entregáveis a pedir quando o insumo for disponibilizado:** projeto-fonte editável completo/permitido, termo de uso, manifesto de arquivos/hash, amostra `MapXXX.rxdata` + `MapInfos.rxdata` + `Tilesets.rxdata`, tilesets/autotiles/characters dependentes, PBS de treinadores/encontros/conexões e lista de áudio com licença. Sem isso, a integração real fica **bloqueada**, não substituída por mapas inventados.

## 8. Fases e critérios objetivos de progresso

**Plano de execução detalhado:** [SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md). Cada uma das 13 fases abaixo só avança com as evidências especificadas no plano, e o menu Testar Sinnoh já codificado não conta como piloto jogável.

**Barra 1 — fases jogáveis: 0/13 (planejadas)**  
**Barra 2 — fases com aceite integral: 0/13 (não auditadas)**

> Valores do **plano novo de Sinnoh**, não do progresso global do projeto. Publicar o MD **não** incrementa nenhuma barra. Avanço de Barra 1 requer um núcleo que inicie/ande/interaja em runtime; Barra 2 exige os testes correspondentes em jogo real, mais ausência de regressão.

| Fase | Escopo | Prova exigida |
|---|---|---|
| **0** | Auditoria de versão, fontes, licenças, IDs e baseline | Inventário real, autoria, backups, testes existentes |
| **1** | Fonte editável/autorizada e manifesto de Sinnoh | Arquivos reais, hashes, mapa de IDs, sem colisões |
| **2** | Piloto isolado e menu `Testar Sinnoh` | Windows abre piloto próprio; Kanto/Johto/Decades sem alteração |
| **3** | Twinleaf, inicial, Rowan/Barry, Sandgem | Caminhada, evento, escolha, NPCs, save/load |
| **4** | Jubilife, Oreburgh, Roark | Mapas conectados, combate Blue, primeira insígnia válida |
| **5** | Floaroma, Eterna, Galactic, Gardenia | Eventos Mars/Jupiter, obstáculos, segunda insígnia |
| **6** | Hearthome, Veilstone, Pastoria | Fantina, Maylene, Wake, sistemas de campo |
| **7** | Canalave, Iron Island, Snowpoint | Byron, Candice, nevasca e Rock Climb |
| **8** | Mt. Coronet, Spear Pillar, Distortion World | Puzzle, Cyrus, Giratina, retornos e autosave seguro |
| **9** | Sunyshore, Victory Road, Elite Four, Cynthia | 8 insígnias, Liga e primeiro desbloqueio Hoenn/Unova |
| **10** | Battle Zone, pós-jogo e lendários | Requisitos de quest, respawn, prevenção de softlock |
| **11** | Música de toda a campanha e site | BGM/ME por evento, dia/noite, loop/fallback, guias dinâmicos |
| **12** | Auditoria integral e integração sem regressões | Windows + JoiPlay + saves antigos, viagens, rollback e documentação |

### 8.1. Regressões que devem ser testadas antes de toda fase

- Decades: jogo normal, save antigo, batalhas, Pokédex, músicas, progresso e esmeraldas.
- Kanto: menu de teste, eventos/IDs, níveis dinâmicos, batalha e música.
- Johto: fonte original auditada, mapas, piloto, treinadores e nenhuma troca de IDs ou eventos.
- Hoenn: documentos, fonte auditada, mapa/áudio preparado e ausência de sobrescritas.
- Blue Studio/site: integração de mapa, treinadores e guias sem nível fixo; compilação e rotas do site.
- Android/JoiPlay: abertura de mapa, toque/movimento, encontro selvagem, batalha, carregamento, sem travamento.
- Provas **reais**: `Game.exe` no Windows e JoiPlay no Android. Testes headless/CI e documentação **não aprovam** por si uma fase jogável.

## 9. Fontes e data de verificação

Fontes públicas consultadas em **13/11/2026**; são páginas de autores/projetos e catálogos, não prova de liberação de assets:

1. [Ancient Platinum — autor, estado, versão e engine](https://eeveeexpo.com/threads/9085/).
2. [Banished Platinum — autor e alcance anunciado da demo](https://eeveeexpo.com/threads/3305/).
3. [Platinum Dawn — ficha secundária; informação incompleta](https://www.astartgaming.com/2025/07/pokemon-platinum-dawn-rpgxp-fangame.html).
4. [Uprising — site da equipe](https://project-insurgent.github.io/web/Index.html).
5. [Fire Ash — equipe, Essentials v19.1 e regiões](https://www.pokecommunity.com/threads/pok%C3%A9mon-fire-ash-version-3-7-1-out.531791/).
6. [The Pokémon World Project — recurso e status Sinnoh 0%](https://eeveeexpo.com/resources/1877/) e [árvore do repositório](https://github.com/SocomSeal/The-PMon-World-Project/tree/main/The%20Pok%C3%A9mon%20World%20Project%20-%20Sinnoh).
7. [Platinum walkthrough — sequência de cidades e pós-jogo](https://bulbapedia.bulbagarden.net/wiki/Appendix:Platinum_walkthrough).
8. [Trilha Diamond/Pearl — catálogo de identificação](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_DP_music).
9. [Platinum — faixas adicionais](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Jukebox).

## 10. Próxima ação concreta

**Executar a Fase 00 segundo [o plano de implementação](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)**; depois construir o piloto próprio na Fase 02 somente quando a fonte editável estiver auditada e autorizada.

**Fase 0:** obter um download **legítimo e permitido** da fonte candidata Ancient Platinum e **inspecionar os arquivos**, sem copiar para `game/`. Confirmar `.rxdata` reais, interiores, gráficos, PBS, compatibilidade de versões, autorização de cada classe de asset e mapa da campanha comparado a Platinum. Se a fonte estiver fechada ou o uso não for permitido, tratar Ancient Platinum apenas como referência visual e **buscar/construir uma base de mapas com permissão**, sem substituir por Hoenn ou por outro map pack.

**Decisão de arquitetura congelada:** **Platinum como história e música de referência; Ancient Platinum como fangame prioritário para auditoria; Blue/Decades como único motor de batalha e progressão; Johto/Kanto/Hoenn preservados; nenhuma fase de Sinnoh marcada como pronta sem prova.**
