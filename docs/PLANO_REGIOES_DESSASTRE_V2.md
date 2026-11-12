# Plano técnico — integrar todas as regiões ao Pokémon Blue: Dessastre Paradoxal

**Tipo:** especificação funcional e técnica de implementação  
**Data:** 11/11/2026  
**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Base existente:** Pokémon Decades + RPG Maker XP + Pokémon Essentials v21.1  
**Versão do plano:** 2.0 — inclui pós-jogo global, equipes canônicas definitivas, bloqueio regional de Pokémon especiais, transporte por NPC e regras locais de campo.  
**Status:** planejamento; **este documento não significa que os mapas ou sistemas já foram instalados**.

> **Objetivo central:** usar o Dessastre Paradoxal/Decades como **jogo-mestre** e manter seus Pokémon, sprites, movimentos, habilidades, sistemas de batalha, IA, progressão Blue, interface, PC, saves e ferramentas. Adicionar as demais regiões como **conteúdo de mundo** (mapas, encontros, treinadores, eventos, missões e ligas), sem instalar os motores de batalha dos fangames usados como referência.

---

## 1. Decisões já definidas para o jogo

1. **Escolha da região inicial:** o jogador seleciona onde começar antes de receber o inicial regional. Não existe uma ordem obrigatória de jogo. Decades é uma opção inicial como qualquer outra região do circuito principal.
2. **Desbloqueio ao vencer a Liga:** ao concluir pela primeira vez a Liga de uma região, libera as **duas regiões vizinhas** do circuito, mesmo que uma delas já esteja acessível. Não desbloqueia todas as regiões de uma vez.
3. **Exceções obrigatórias:** Kanto libera **Decades + Johto**; Johto libera **Kanto + Hoenn**; Paldea libera **Galar + Decades**. Para fechar o circuito, Decades libera **Paldea + Kanto**.
4. **Treinadores:** utilizar os treinadores do(s) jogo(s) original(is) que inspiram cada região, mantendo identidades, posições, classes, eventos, Pokémon e movimentos de referência sempre que viável. O sistema atual do Blue aplica o balanceamento **em memória no momento da batalha**, sem destruir a equipe-base original.
5. **Pokémon selvagens:** preservar o habitat e os encontros regionais, **fundindo os exclusivos de versões pares** (ex.: FireRed + LeafGreen). Não substituir os Pokémon locais por uma Pokédex aleatória global.
6. **Insígnia = esmeralda:** cada insígnia única obtida de um ginásio de uma nova região acrescenta **uma unidade à progressão global existente de esmeraldas/cristais**; nunca somar duas vezes a mesma conquista. O cálculo de nível e BST continua o já existente no Dessastre Paradoxal.
7. **Hisui:** não possui Liga Pokémon tradicional. Será tratada como campanha especial de exploração e história, sem alterar as duas liberações automáticas do circuito de Ligas. Sua exceção de acesso é descrita abaixo.
8. **Uma campanha, um save:** conservar equipe, PC, Pokédex, dinheiro, itens, conquistas, modos de batalha e progresso ao viajar entre regiões. Salvar progresso regional sem perder as quests do Decades.
9. **Pós-jogo global:** somente depois de concluir **uma vez as dez campanhas principais do circuito** é ativada a versão mais forte **oficial e documentada** das equipes de líderes, Elite Four (quando existir) e Campeões/chefes equivalentes. Sem inventar combinações de Pokémon.
10. **Pokémon especiais por região:** lendários, míticos, Ultra Beasts e Paradoxos **só podem integrar a equipe ativa se as oito conquistas locais da região atual tiverem sido obtidas**; ao viajar para uma região onde faltam essas conquistas, depositar os especiais na Box e impedir sua retirada para a party até a liberação. Pokémon comuns não sofrem esse bloqueio.
11. **Viagem após a Liga:** concluir a Liga e o encerramento oficial da campanha faz aparecer um NPC de transporte com destinos já desbloqueados; o jogador pode viajar ou permanecer.
12. **Uso de HMs e mobilidade por região:** o acesso a campo usa os pré-requisitos locais de cada jogo; insígnias de uma região não concedem automaticamente permissões de outra. Alola, Galar, Paldea e Hisui usam sistemas próprios de locomoção, sem HMs fictícios.

### O que não fazer

- Não copiar `Scripts.rxdata`, o núcleo Ruby de batalha nem o pacote completo de plugins de outro fangame por cima da instalação Blue.
- Não substituir `game/Data` inteiro, `PBS/pokemon*.txt`, `moves*.txt`, `abilities*.txt` ou scripts próprios.
- Não assumir que um executável de fangame distribuído publicamente tenha projeto editável ou licença de reutilização.
- Não importar os mapas de uma região diretamente com seus IDs originais: isso causaria colisões de mapas, switches, variáveis e eventos.
- Não criar uma segunda fórmula de escalonamento, um segundo contador de esmeraldas ou uma segunda Pokédex.
- Não confundir a contagem **global** de esmeraldas (balanceamento) com a contagem **local** de insígnias/provas (Pokémon especiais, HMs e mobilidade).
- Não liberar Pokémon especiais ao obter 8 esmeraldas **globais**; são exigidas oito conquistas na **região atual**.
- Não criar um Elite Four fictício para Galar nem oito ginásios tradicionais para Alola ou Hisui.

---

## 2. O que foi confirmado na versão atual do repositório

A análise foi realizada sobre a documentação disponível na branch `main` do repositório em 11/11/2026. Os arquivos reais do jogo Decades, seus mapas e suas compilações **não estão versionados no GitHub**; a instalação os mantém localmente. Por isso, os nomes exatos de todos os métodos de runtime e o mecanismo que concede esmeraldas no jogo instalado precisam ser confirmados durante a implementação, antes de alterar plugins ou eventos.

| Componente existente | Estado documentado | Preservação necessária |
|---|---|---|
| RPG Maker XP / Essentials | Base Decades, Essentials v21.1 | Manter como motor principal |
| Pokémon, formas e golpes | Regras restauradas, geração 9 e espécies autorais | Manter os IDs simbólicos e as alterações existentes |
| Batalhas e IA | Campanha Blue, IA Blue Radical, Mega/Z/Tera/Dynamax, duplas | Reutilizar; não transplantar outro sistema de batalha |
| Progressão | Tradicional com 4 faixas por esmeraldas, nível por porcentagem | Reaproveitar **exatamente** as regras existentes |
| Encontros autorais | Manifesto `data/fan-encounters.json`; alocação por mapa | Preservar; IDs de mapas existentes não devem mudar |
| Álbum de Treinadores | Lê NPCs de mapas; histórico e prêmios por área | Expandir para as novas áreas sem duplicações |
| Habitat Dex / Pokégear | Dados e imagens de locais associados a IDs reais de mapas | Regerar referências após adição de mapas |
| Blue Studio | Abas de Pokémon, itens, treinadores e encontros funcionais; editor de mapas ainda planejado na documentação | Criar primeiro um importador seguro por ferramenta/script |
| Save | Múltiplos slots `File A.rxdata`…`File H.rxdata`, autosaves e backups | Migrar por adição de estado, sem apagar saves antigos |
| Instalação | `game/` local, instalador e atualizações com backups | Importar mapas pelo instalador, com plano/rollback |

**Fontes internas do projeto:**

- [`README.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/README.md)
- [`docs/PROGRESSAO_E_ANIMACOES.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PROGRESSAO_E_ANIMACOES.md)
- [`docs/ECONOMIA_E_JORNADA.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ECONOMIA_E_JORNADA.md)
- [`docs/ALBUM_E_MAPAS.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ALBUM_E_MAPAS.md)
- [`docs/ENCONTROS_E_MENUS_ANDROID.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ENCONTROS_E_MENUS_ANDROID.md)
- [`docs/INSTALACAO.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/INSTALACAO.md)

---

## 3. Mapa de desbloqueio: circuito entre regiões

O circuito principal tem **dez posições**: nove regiões da série principal mais Decades. A ordem geográfica/de progressão usada para desbloqueio é:

```text
                         [ DECADES ]
                         /         \
                     [KANTO]      [PALDEA]
                        |             |
                     [JOHTO]       [GALAR]
                        |             |
                     [HOENN]       [ALOLA]
                        |             |
                     [SINNOH]     [KALOS]
                        \             /
                          [UNOVA]

Circuito lógico completo:
Decades ⇄ Kanto ⇄ Johto ⇄ Hoenn ⇄ Sinnoh ⇄ Unova
        ⇄ Kalos ⇄ Alola ⇄ Galar ⇄ Paldea ⇄ Decades
```

| Região cuja Liga foi vencida | Região anterior liberada | Região seguinte liberada |
|---|---|---|
| **Decades** | Paldea | Kanto |
| **Kanto** | Decades | Johto |
| **Johto** | Kanto | Hoenn |
| **Hoenn** | Johto | Sinnoh |
| **Sinnoh** | Hoenn | Unova |
| **Unova** | Sinnoh | Kalos |
| **Kalos** | Unova | Alola |
| **Alola** | Kalos | Galar |
| **Galar** | Alola | Paldea |
| **Paldea** | Galar | Decades |

### Exemplos de jornadas

- **Começar em Johto:** somente Johto está inicialmente disponível; derrotar sua Liga libera Kanto e Hoenn. Vencer Hoenn depois libera Johto (já disponível) e Sinnoh; assim o jogador avança sem perder as regiões anteriores.
- **Começar em Kanto:** derrotar a Liga libera Decades e Johto; depois, ao concluir Decades, Paldea também é liberada.
- **Começar em Paldea:** derrotar a Liga libera Galar e Decades; o jogador pode seguir para o fim do circuito ou para Kanto passando pelo Decades.
- **Começar em Unova:** sua conclusão libera Sinnoh e Kalos, sem obrigar a jogar Kanto primeiro.
- **Começar em Decades:** ao concluir o marco final da campanha-base, libera Paldea e Kanto. **O gatilho exato do “final de Liga” equivalente do Decades precisa ser identificado nos eventos reais**, não inventado ou disparado na metade da história.

### Regras de desbloqueio

- Escolher uma região inicial libera apenas ela **para campanha normal**; outros mapas só aparecem como visualização bloqueada no painel de destinos.
- Concluir a Liga libera vizinhas **independentemente do sentido da jornada**. É um `union`, nunca substituição da lista anterior.
- A primeira vitória na Liga efetua as liberações; revanche dá recompensas normais conforme as regras do jogo, mas **não duplica flags, insígnias, esmeraldas ou destravamentos**.
- A ordem de visita é livre entre regiões já liberadas. A Liga pode ser desafiada novamente, e o jogador pode voltar a qualquer região já visitada.
- O desbloqueio ocorre **apenas após a conclusão real e persistida** da Liga (vitória e evento final, se aplicável), não ao entrar na sala do Campeão.
- Se o jogador completar um arco de região antes de a UI abrir o menu de viagem, a flag já deve estar salva e ser exibida no próximo acesso.

### Hisui: caso sem Liga

Hisui não entra no circuito de Ligas. Para manter a promessa de escolha livre de início, a tela inicial pode listar **Hisui como “Jornada especial”**. Uma escolha por Hisui inicia sua própria campanha; concluir o arco principal da expedição libera **Sinnoh e Decades** como saídas propostas para evitar um save sem novas regiões. Isso é uma **regra especial de design, não uma Liga nem uma terceira região vizinha do circuito**. Para quem começar em outra região, o acesso a Hisui será uma missão temporal opcional em Sinnoh, separada do desbloqueio automático da Liga. Não atribuir insígnias fictícias a Hisui nem contar sua conclusão como esmeralda.

> **Ponto de configuração:** a exceção “terminar Hisui libera Sinnoh + Decades” é recomendação de implementação para permitir iniciar por Hisui. As liberações obrigatórias Kanto/Johto/Paldea e o circuito principal acima são as regras já estabelecidas.

---

## 4. Tela inicial: escolher qualquer região de início

**Fluxo de nova partida proposto:**

```text
Nova partida
    ↓
Story Mode / modo de campanha existente
    ↓
Escolher região inicial (10 regiões de Liga + Hisui especial)
    ↓
Escolher modo de iniciais existente (Traditional Starters etc.)
    ↓
Selecionar inicial conforme a região escolhida
    ↓
Definir mecânicas da campanha (Mega / Z / Tera / Dynamax)
    ↓
Salvar escolha, registrar progresso inicial e iniciar no ponto correto
```

- A ordem das telas deve ser integrada ao fluxo atual, sem duplicar as telas de seleção de modo ou mecânicas já existentes.
- A região escolhida fica gravada **uma vez** no save; trocar de região por viagem não altera o campo `initial_region`.
- Iniciais do jogo original por região, com alternativas especiais do Decades mantidas como já funcionam.
- Ponto inicial deve existir como mapa + coordenadas + direção + música + evento de introdução. Verificar transferências de eventos de início para não iniciar inadvertidamente em um mapa do Decades.
- Começar em Kanto ou Unova não deve disparar a introdução do Decades, entregar seus itens de introdução, avançar suas missões ou alterar suas flags.
- Saves existentes continuam na campanha atual. Não mostrar novamente a tela de escolha para um save antigo.
- Para Hisui, selecionar um inicial/apoiador e uma introdução específicos da campanha especial, sem forçar um ginásio inexistente.

### Documento de configuração sugerido

```json
{
  "start_region": "JOHTO",
  "start_map_key": "JOHTO_NEW_BARK_TOWN",
  "starter_set": "JOHTO_ORIGINAL",
  "mode": "TRADITIONAL_STARTERS",
  "initial_version_policy": "MERGED_CANON"
}
```

Esses campos são **especificação de dados**, não nomes de propriedades já existentes no motor.

---

## 5. Preservar e reutilizar a progressão de insígnias/esmeraldas (sem recalcular)

**Exigência:** **1 insígnia de ginásio nova = 1 esmeralda da progressão existente**. O cálculo das batalhas permanece o atual, sem introduzir tabelas alternativas.

### 5.1 Fórmulas comprovadas na documentação atual

Para a equipe atual do jogador, calcule `L = maior nível entre os Pokémon utilizáveis, ignorando ovos`:

| Elemento de batalha | Regra atual documentada |
|---|---|
| Treinador comum | `max(1, floor(L × 0,70))` |
| Líder de ginásio normal (antes do Master) | `max(1, floor(L × 0,70))` |
| Líder de ginásio **Master (11+ esmeraldas)** | `max(1, floor(L × 0,90))` |
| Pokémon selvagem | `max(1, floor(L × 0,45))` |

A engine aplica suas próprias regras antes do adaptador Blue; essas fórmulas são a etapa de ajuste documentada do Blue. Manter as funções/handlers atuais e a ordem de execução, em vez de duplicá-las em eventos dos mapas importados.

**Exemplo com maior Pokémon nível 60:** treinador comum = 42; líder no Master = 54; selvagem = 27.

### 5.2 Faixas atuais de esmeraldas

| Esmeraldas (globais) | Estágio | BST máximo de adversários/selvagens | Poder máximo de golpes de treinadores | Prêmio por classe |
|---|---|---:|---:|---:|
| 0–1 | Inicial | 350 | 60 | 1× |
| 2–4 | Intermediário | 450 | 90 | 2× |
| 5–10 | Avançado | 540 | Sem teto adicional desta fase | 3× |
| 11+ | Master | Sem teto BST | Sem teto adicional desta fase | 4× |

Observações importantes:

- A substituição por BST é aplicada às **equipes temporárias de batalha**, de modo que Charizard ou Gyarados da ficha canônica podem virar pré-evoluções permitidas nos estágios iniciais. **Não apagar nem editar o time original salvo no banco de treinadores.**
- Os limites existentes de golpes, itens, valores de dinheiro e bônus dos ginásios permanecem controlados pelo Blue.
- A progressão precisa considerar o **contador global já usado pelos handlers Blue**, não um novo cálculo por região que ignore esmeraldas do Decades.
- Insígnias de Kanto/Johto/etc. têm sua própria identidade (`KANTO_BOULDER`, `JOHTO_ZEPHYR` etc.) e **cada uma só incrementa o contador uma vez**.
- A execução deve localizar a **API/rotina real** que concede uma esmeralda na instalação; reutilizá-la (ou criar adaptador compatível) após verificar saves e plugins. Evitar escrever diretamente numa variável desconhecida ou somar a insígnia à esmeralda **se a rotina nativa já somou o valor**.
- Os saves antigos de Decades já têm conquistas. A migração **não os zera** e não transforma retroativamente o mesmo cristal em duas unidades.

### 5.3 Exemplo de comportamento

1. Jogador inicia Johto com 0 esmeraldas: aplica o estágio Inicial.
2. Vence Falkner e recebe a primeira insígnia: registra `JOHTO_ZEPHYR` e total global sobe **em uma unidade**, usando a rotina nativa apropriada.
3. Vence Bugsy: total global passa a 2 e, na próxima batalha, vale Intermediário.
4. Ao conquistar cinco insígnias ao longo da jornada, entra na faixa Avançado.
5. Ao obter a décima primeira esmeralda/insígnia no **conjunto das regiões**, entra em Master.
6. Trocar de região **não reseta os totais nem reduz o estágio**. A autorização para usar Pokémon especiais e HMs, porém, consulta **as insígnias/conquistas da região de destino**; essa checagem local não altera o escalonamento global.

**Consequência deliberada das regras atuais:** com oito insígnias de uma região o jogador normalmente está na faixa Avançado; após três novas insígnias entra em Master. Isso segue sua preferência de usar o **mesmo cálculo**, sem inventar uma nova progressão de dez regiões.

### 5.4 Exceções de recompensas nativas

- **Alola:** não possui ginásios convencionais. Adotar as **oito provas oficiais de Ultra Sun/Ultra Moon** como oito conquistas locais equivalentes, cada uma concedendo uma esmeralda **somente na primeira conclusão**. As grandes provas dos kahunas são missões separadas e não duplicam essas esmeraldas. Isso mantém a campanha fundida coerente; Sun/Moon, separadamente, tinha sete provas.
- **Paldea:** as oito insígnias de ginásio podem conceder uma esmeralda cada. As insígnias de Titãs e Equipe Star são missões paralelas: **não contam novamente** para o contador de ginásios na proposta inicial, evitando desbalanceamento e recompensas duplicadas.
- **Decades:** conservar a obtenção de esmeraldas da própria campanha; não converter automaticamente todo NPC ou boss em insígnia adicional. Para o bloqueio de especiais, configurar oito marcos **distintos e reais** da campanha Decades, depois de auditar os eventos instalados; não inventar oito ginásios ou modificar o contador nativo.
- **Hisui:** usar conclusões da pesquisa, nobres e história como flags próprias, **sem falsas insígnias ou esmeraldas**. Para liberar especiais, usar um marco narrativo de conclusão do arco principal de Hisui, em vez de oito insígnias inexistentes.

---

## 6. Quais versões originais fundir em cada região

**Política global: `MERGED_CANON`** — uma campanha principal por região, conteúdo de **todas as versões relevantes** sem duplicar o mesmo ginásio ou treinador por diferença cosmética. Respeitar a cronologia quando duas versões se passam em épocas diferentes.

| Região | Referências originais recomendadas | Política de fusão de Pokémon, treinadores e conteúdo |
|---|---|---|
| **Kanto** | FireRed + LeafGreen (prioridade); Red/Blue/Yellow para conteúdo histórico opcional | Uma Kanto única: união dos exclusivos FR/LG por habitat; NPCs e ginásios sem duplicação; Sevii Islands integradas conforme eventos |
| **Johto** | HeartGold + SoulSilver; Crystal para eventos adicionais | Uma Johto única: fusão de exclusivos HG/SS e encontros/eventos distintos sem duplicar os oito ginásios |
| **Hoenn** | Emerald + Ruby + Sapphire; elementos de Omega Ruby/Alpha Sapphire como conteúdo opcional | Estrutura e campanha-base Emerald; encontros exclusivos Ruby/Sapphire incorporados, com arcos adicionais de Groudon/Kyogre/Rayquaza e conteúdo Delta sem sobrescrever a cronologia |
| **Sinnoh** | Platinum + Diamond + Pearl; BD/SP como referência complementar | Campanha-base Platinum; variantes de encontros, treinadores e áreas de Diamond/Pearl onde agreguem conteúdo sem repetir a mesma Liga |
| **Unova** | Black + White **e** Black 2 + White 2 | **Não fundir cronologias cegamente:** campanha BW em uma fase; B2/W2 em sequência temporal/missões futuras, reutilizando geografia com mudanças de mapa e treinadores quando necessário |
| **Kalos** | X + Y | União de exclusivos e eventos de X/Y; uma Liga; formas e lendários dos dois jogos em arcos separados |
| **Alola** | Ultra Sun + Ultra Moon, com Sun + Moon como referência para conteúdo alternativo | Uma jornada pelas quatro ilhas; fusão de exclusivos e eventos, mantendo provas, kahunas e Liga sem repetição artificial |
| **Galar** | Sword + Shield + Isle of Armor + Crown Tundra | União de exclusivos; **Bea/Allister e Gordie/Melony** podem ser versões alternativas do respectivo desafio ou batalhas adicionais, mas cada vaga de ginásio concede uma insígnia só |
| **Paldea** | Scarlet + Violet + The Teal Mask + The Indigo Disk | Ambas espécies exclusivas e linhas de Paradoxos; academia unificada ou duas facções narrativas sem duplicar o mesmo torneio; DLCs como capítulos extras |
| **Decades** | Campanha atual instalada no projeto | **Não fundir nem substituir:** preservar NPCs, equipes, encounters, missões e roteiro já existentes |
| **Hisui** | Legends: Arceus | Uma campanha especial; encontro de espécies e formas hisuianas, nobres e expedições, sem inventar Liga |

**Nota sobre autenticidade:** versões como Ruby/Sapphire e Emerald ou BW e B2/W2 podem ter **treinadores, níveis, equipes e acontecimentos diferentes**. O importador deve registrar as variantes originais como fontes distintas e definir qual é a campanha principal. “Fundir” não é misturar duas equipes do mesmo NPC numa equipe aleatória de doze Pokémon.

### 6.1 Regra para Pokémon exclusivos

- Para cada rota, mantenha uma tabela-base de encontros **da versão canônica principal**, acrescente os exclusivos da versão parceira nos mesmos biomas/horários/métodos quando plausível e **renormalize pesos para 100% por método/tabela**.
- Diferencie `Land`, `Water`, pesca, cavernas, dia/noite, clima, estações e formas regionais; use apenas mecanismos suportados pela versão instalada do Essentials.
- Se um exclusivo só existia num evento ou área especial, mantenha-o como **evento** ou área adequada; não o adicione arbitrariamente a qualquer grama.
- Lendários exclusivos devem permanecer encontros ou quests especiais, com regras de captura definidas, e não criaturas selvagens comuns.
- Evite listas duplicadas: caso a mesma espécie esteja presente nas duas versões na mesma rota, uma única entrada canônica com peso ajustado pode representar a espécie.
- Registre para a Habitat Dex e o site de qual(is) versão(ões) veio cada encontro.

### 6.2 Regra para treinadores originais

- Recriar NPCs com **nome, classe, localização, aparência, diálogo e Pokémon-base** dos jogos de referência.
- Manter formação, EVs/IVs/nature, golpes e itens quando os dados oficiais existirem; não inventar o que a referência não possui.
- Normalizar IDs de treinadores com **região + NPC + encontro/variante**, sem colisão com o Decades.
- Eventos de duelo e recompensas precisam usar o sistema de batalha do Blue; a equipe original é **modelo de referência imutável** e o Blue executa a adaptação temporária por estágio/nível.
- Se a versão A tiver um treinador numa rota e B não, conservar o NPC sem gerar duplicata da rota inteira.
- Se as versões tiverem NPCs alternativos, representar escolhas/variações em eventos ou desafios extras; evitar que duas versões do mesmo líder concedam duas insígnias.
- Manter sprites, diálogos, música e sons apenas quando houver **fontes apropriadas e direitos de uso verificados**; quando não, recriar com recursos próprios.

### 6.3 Exemplo: FireRed + LeafGreen em Kanto

```text
KANTO_ROUTE_XX
  cenário: mapa aprovado e importado
  eventos: NPCs e treinadores da rota (sem duplicatas)
  encontros-base: tabela FireRed
  complementos: exclusivos LeafGreen compatíveis com a área
  versão do mundo: MERGED_CANON
  batalhas: todos usam o handler atual do Dessastre Paradoxal
  badge: nenhuma em rota comum
```

A Liga, os líderes e o rival têm **uma progressão principal**; conteúdo de versão alternativa entra em encontros, missões, rematches ou variantes sem exigir duas campanhas completas de Kanto.

---

## 7. Processo técnico para importar mapas de RPG Maker XP ao jogo atual

### 7.1 Levantamento obrigatório (antes de importar)

Para cada fonte com uso autorizado, registrar:

- versão do RPG Maker/Essentials e plugins obrigatórios;
- `Data/MapXXX.rxdata`, `MapInfos.rxdata`, `Tilesets.rxdata` e, se presente, sistemas de eventos comuns que os mapas usam;
- imagens e configuração de `Graphics/Tilesets/`, `Graphics/Autotiles/`, `Graphics/Characters/`, panoramas e áudio;
- `PBS/map_metadata.txt`, `PBS/map_connections.txt`, `PBS/town_map.txt`, `PBS/encounters.txt`, `PBS/trainers*.txt`, tipos de treinadores e quaisquer dados correlatos;
- comandos de evento: transferência, switch, variável, self-switch, script Ruby, batalha, teleporte, quest, Fly/Surf/Dive, cutscenes, músicas, objetos de cenário;
- IDs duplicados, mapas órfãos, recursos ausentes, comandos de script que dependam de plugins do jogo doador;
- **licença/autorização** para reutilização de mapas e gráficos. Um download jogável não prova permissão de redistribuição.

### 7.2 Manifesto de importação por região

Sugestão de organização dos arquivos **próprios** no repositório:

```text
Pokemon-Blue-Dessastre-Paradoxal/
├── data/
│   └── regions/
│       ├── registry.json
│       ├── decades.json
│       ├── kanto.json
│       ├── johto.json
│       ├── hoenn.json
│       ├── sinnoh.json
│       ├── unova.json
│       ├── kalos.json
│       ├── alola.json
│       ├── galar.json
│       ├── paldea.json
│       └── hisui.json
├── scripts/
│   └── region_importer/
│       ├── scan.py
│       ├── build_plan.py
│       ├── remap.py
│       ├── apply.py
│       ├── validate.py
│       └── README.md
├── scripts/
│   └── regions/
│       └── install.py
├── tests/
│   └── test_regions.py
├── docs/
│   └── REGIOES_E_PROGRESSAO.md
└── game/                  # instalação local: NÃO versionar
    ├── Data/
    ├── Graphics/
    └── PBS/
```

Esses são **caminhos propostos**; conferir nomes e organização dos plugins e do instalador atual antes de criar pastas. Arquivos de mapa e recursos de terceiros só podem entrar na distribuição com autorização e conforme as regras aplicáveis.

Exemplo conceitual de manifesto — **não aplicar estes IDs literalmente**:

```json
{
  "id": "KANTO",
  "display_name": "Kanto",
  "canonical_games": ["FIRERED", "LEAFGREEN"],
  "encounter_merge": "MERGED_CANON",
  "starter_species": ["BULBASAUR", "CHARMANDER", "SQUIRTLE"],
  "map_keys": ["KANTO_PALLET_TOWN", "KANTO_ROUTE_1", "KANTO_VIRIDIAN_CITY"],
  "league_key": "KANTO_LEAGUE_CHAMPION",
  "badge_keys": ["KANTO_BOULDER", "KANTO_CASCADE"],
  "adjacent_leagues": ["DECADES", "JOHTO"],
  "asset_policy": "AUTHORIZED_ORIGINAL_AND_DERIVED_ASSETS_ONLY"
}
```

`badge_keys` acima está **abreviado como exemplo**; o manifesto real deve listar os oito ginásios correspondentes.

### 7.3 Remapeamento seguro de dados

1. Ler a instalação do Blue e enumerar IDs **reais já ocupados**. Nunca presumir que uma faixa (ex.: 200–299) está vazia.
2. Alocar IDs de destino livres a partir de um catálogo de mapas com chaves simbólicas estáveis (`KANTO_PALLET_TOWN` etc.). Respeitar os limites confirmados do RPG Maker XP/Essentials instalado.
3. Clonar cada `MapXXX.rxdata` para um workspace isolado e atualizar referências locais de ID: mapa de destino, entradas/saídas, eventos, conexões, pontos de cura, Dive/Fly, metadados, spawn, mapas de região, teleportes e dados dependentes.
4. **Não fazer busca/substituição ingênua em binários RXDATA.** Utilizar Ruby/Marshal e estruturas adequadas do motor, executadas em ambiente isolado com backups; bytes de procedência desconhecida não devem ser desserializados sem isolamento.
5. Fazer inventário das referências a números de **switches, variables, common events, self-switches, itens, trainers e scripts**. Remapear por namespace; self-switches dependem de `(map_id, event_id, letra)` e são especialmente sensíveis a mudanças de ID.
6. Se o mapa usar tileset com ID que já existe no destino, importar a definição com novo ID e revisar prioridades, passabilidade, terreno, autotiles, padrões, gráfico, dimensões e nomes. Não basta copiar a imagem PNG.
7. Reescrever scripts embutidos apenas quando o padrão for reconhecido e validado; todo trecho customizado incompatível deve ser colocado em relatório `needs_manual_review`, nunca ignorado silenciosamente.
8. Gerar plano com origem, hash, licença, mapa de IDs, alterações, avisos e destino; fazer **dry-run por padrão** e só aplicar após validação explícita.
9. Aplicar com backup transacional em `.blue-backups/regions-...`; rollback total em falha. Preservar saves e arquivos não envolvidos.
10. Compilar os PBS com a **engine do Dessastre Paradoxal** em modo Debug e testar carregamento dos mapas reais.

### 7.4 Dados de região no Pokémon Essentials

No Essentials, os mapas de jogo são distintos dos mapas de região mostrados na Town Map/Pokégear. Para cada região, é necessário:

- definir mapa visual regional em `PBS/town_map.txt` e a imagem correspondente;
- associar `MapPosition` de **todos** os mapas em `PBS/map_metadata.txt`, inclusive interiores, usando o ID da região e coordenadas corretas;
- declarar conexões de mapas adjacentes em `PBS/map_connections.txt` e teleports/portais para troca entre regiões;
- revisar `HealingSpot`, local de retorno após derrota, Fly, Surf, Dive, teletransportes e interiores;
- ligar a Habitat Dex, o Pokégear e o álbum de treinadores aos **IDs finais**, não aos IDs da fonte;
- verificar o limite total de mapas e recursos do projeto instalado antes de escolher dividir mapas grandes ou combinar áreas.

Referências do Essentials: [Múltiplas regiões](https://essentialsdocs.fandom.com/wiki/Multiple_regions), [Map metadata](https://essentialsdocs.fandom.com/wiki/Map_metadata), [schema de metadata v21.1](https://github.com/silveredmeadow/pokemon-essentials-v21.1-github/blob/master/Data/Scripts/010_Data/002_PBS%20data/018_MapMetadata.rb).

---

## 8. Integração de treinadores, encontros e Ligas ao sistema atual

### 8.1 Treinadores

O importador gera registros compatíveis com a estrutura de treinadores que o Blue já lê (na documentação atual, `trainers_story_mode.txt` e outras fontes PBS, conforme o projeto instalado). Registrar os dados **canônicos** e usar a rotina de batalha existente:

```text
Evento do NPC da região
    → identificar region_id + trainer_key + variante
    → buscar equipe canônica da versão fundida
    → Blue prepara a equipe temporária em memória
    → aplicar níveis atuais e limite de BST/esmeraldas
    → aplicar seleção de golpes/IA/mecânicas existentes
    → iniciar batalha pela engine do Dessastre Paradoxal
    → registrar vitória por NPC/região e atualizar Álbum
```

Não escrever uma “versão ajustada” do treinador permanentemente de volta ao PBS. Em Master, manter a lógica atual de dificuldade e formato do jogo sem criar um novo escalonador por região.

### 8.2 Encontros selvagens

- Usar `PBS/encounters*.txt` ou os arquivos efetivos de encontros suportados no build instalado.
- Cada área recebe habitats fiéis à versão principal e exclusivos agregados da versão parceira.
- Validar chance total por método, forma, espécie, estação e horário quando aplicáveis.
- Todos os encontros passam pelo mesmo adaptador Blue de **45% do nível máximo** e pelos limites de BST de cada fase.
- As 44 espécies autorais já distribuídas no Decades, segundo documentação da instalação, permanecem nas áreas existentes; **não multiplicar automaticamente 5% em cada mapa novo**. Quais espécies autorais aparecerão fora de Decades será uma decisão separada de design.
- Integrar as tabelas novas ao site, à Habitat Dex e aos mapas regionais sem remover locais antigos.

### 8.3 Ginásios e Ligas

- Cada insígnia tem `badge_key`, `region_id`, `gym_key` e uma flag única de recompensa.
- Vitória do líder confirma `badge_key` e entrega **uma esmeralda** mediante a rotina já existente. Revanche não incrementa.
- A Liga valida requisitos regionais de acesso — insígnias/provas e marcos de história — sem bloquear a troca livre entre **regiões já liberadas**.
- Vitória definitiva no Campeão (ou evento final equivalente do Decades) marca `league_completed[region]` e chama uma única vez `unlock_neighbors(region)`.
- Cada região possui status: `LOCKED`, `UNLOCKED`, `VISITED`, `LEAGUE_COMPLETED` e histórico de revanches independente.
- A contagem global de esmeraldas não deve ser confundida com o número de insígnias daquela região: são dados relacionados, mas com finalidades diferentes.

### 8.4 Compromisso com a fidelidade ao original

Os times **originais** continuam visíveis no editor, na Dex de treinadores e nas fichas das regiões, com informações de qual versão do jogo foram obtidos. Durante a batalha normal, **o Blue pode substituir temporariamente espécies de BST alto por pré-evoluções válidas**, como já faz hoje. Para consultar a equipe canônica sem escalonamento, o site pode oferecer um modo “Equipe original”, separado do preview “Equipe esperada no meu estágio”.

---

## 9. Pseudocódigo dos desbloqueios e da persistência

O exemplo abaixo especifica o **comportamento esperado**. Não é código Ruby pronto para copiar no Essentials; os identificadores e o acesso ao save deverão ser ligados às estruturas reais.

```ruby
# PSEUDOCÓDIGO — adaptador do jogo Blue
RING = %w[
  DECADES KANTO JOHTO HOENN SINNOH
  UNOVA KALOS ALOLA GALAR PALDEA
].freeze

def choose_initial_region(region_id, save)
  raise 'Já iniciou' if save.initial_region
  raise 'Região inválida' unless RING.include?(region_id) || region_id == 'HISUI'
  save.initial_region = region_id
  save.unlocked_regions.add(region_id)
  start_at_manifest_spawn(region_id)
end

def complete_league(region_id, save)
  return if save.league_completed.include?(region_id)
  raise 'Hisui não tem Liga' unless RING.include?(region_id)
  raise 'Vitória não confirmada' unless final_event_verified?(region_id)
  save.league_completed.add(region_id)
  i = RING.index(region_id)
  prev_region = RING[(i - 1) % RING.length]
  next_region = RING[(i + 1) % RING.length]
  save.unlocked_regions.add(prev_region)
  save.unlocked_regions.add(next_region)
  save_progress_atomically(save)
end

def obtain_badge(region_id, badge_key, save)
  assert_real_gym_or_trial?(region_id, badge_key)
  return if save.claimed_badge_keys.include?(badge_key)
  # Vincular à API que JÁ concede esmeraldas no Dessastre/Decades.
  existing_blue_crystal_award_adapter!(1)
  save.claimed_badge_keys.add(badge_key)
  save_progress_atomically(save)
end
```

**Requisito de transação:** a entrega da esmeralda, a marcação da insígnia e a persistência devem ser **atômicas ou reconciliáveis**. Um crash entre “dar esmeralda” e “marcar insígnia” pode causar duplicidade se não houver um registro de transação. Implementar ledger idempotente por `badge_key` e reconciliar migrações com segurança.

### Estado proposto para o save

```json
{
  "regions_schema_version": 1,
  "initial_region": "JOHTO",
  "current_region": "JOHTO",
  "unlocked_regions": ["JOHTO", "KANTO", "HOENN"],
  "completed_leagues": ["JOHTO"],
  "claimed_badge_keys": ["JOHTO_ZEPHYR", "JOHTO_HIVE"],
  "region_story_flags": {},
  "hisui_expedition_completed": false
}
```

**Importante:** o save acima não armazena outro `emerald_count`: o **contador de esmeraldas continua sendo o nativo**. O histórico de `claimed_badge_keys` existe apenas para impedir ganho duplo e mostrar conquistas por região. O instalador deve migrar saves anteriores sem tocar nos arquivos de slot originais; gerar cópias de segurança antes de testar.

---

## 10. Mecânica de transporte entre regiões

**Criar um Hub de Viagem Regional** acessível em locais apropriados (porto, estação, aeroporto ou portal), além do menu de regiões do Pokégear quando o local permitir. Preferir inserir portais por eventos controlados em mapas já existentes, sem substituir a introdução de Decades.

- Lista mostra todas as regiões; as não liberadas aparecem bloqueadas, com a condição “Conclua a Liga de X ou Y”.
- A primeira chegada usa o `start_map` ou terminal principal da região, sem ignorar eventos de introdução e acesso a itens de história.
- Depois de visitar uma região, permite retornar ao ponto de chegada e a destinos locais autorizados; **Fly não deve alcançar automaticamente regiões bloqueadas**.
- Viagens não alteram equipe, dinheiro, PC, insígnias, progresso ou esmeraldas. Troca de mapa só altera `current_region`.
- Se o jogador desmaiar, volta ao ponto de cura válido da região atual; eventos de emergência impedem pontos inválidos ou inexistentes.
- Durante cutscenes que exigem presença local, bloquear viagem temporariamente por estado do evento, não por perder o desbloqueio.
- O acesso a Hisui usa uma viagem/quest temporal própria, e não uma aresta automática extra do circuito de Ligas.

---

## 11. Impacto no Blue Studio, no site e nos sistemas atuais

### Blue Studio

Novas funcionalidades por fases:

1. **Regiões:** lista das 11 áreas, jogo-base, fontes, status e chaves de mapa.
2. **Importar mapas:** preview do `dry-run`, conflitos de IDs, dependências e diff de arquivos.
3. **Treinadores por região:** região → mapa → NPC → equipe original → variantes de versão → preview da equipe após progressão Blue.
4. **Encontros por região:** tabelas originais, exclusivos fundidos, chance final, método e horário; alerta quando peso ≠ 100%.
5. **Ginásios/Ligas:** lista dos oito desafios (ou equivalente), insígnias, eventos de conclusão, vizinhos a desbloquear.
6. **Validar projeto:** referências quebradas, scripts de evento sem adaptação, mapas sem `MapPosition`, colisões de switch e regressões de save.

**Não apresentar um painel de mapas como funcional antes de implementar leitura/gravação real e testes.** A documentação atual registra essa parte como planejada.

### Site e Pokédex

- Selecionar região no mapa e na Habitat Dex; preservar o mapa Decades.
- Selecionar versão original usada como fonte dos encontros/treinadores (FireRed, LeafGreen etc.) e visualizar a tabela **fundida** para o jogador.
- Álbum de treinadores segmentado por região, sem esquecer as 61 entradas originais documentadas do Decades.
- Indicador de progresso: mapas visitados, insígnias/provas, Liga concluída, locais de captura.
- Dados exportados sempre de IDs **efetivos** do jogo após a importação; não inventar disponibilidade de Pokémon que a engine ainda não compilou.

---

## 12. Planejamento por etapas de implementação

| Etapa | Entregável | Critério de aceite |
|---|---|---|
| **0 — Auditoria da instalação** | Inventário de mapas, eventos, runtime de esmeraldas, trainers, scripts de save, versão dos plugins e licenças das fontes | Nenhum ID ou handler essencial indefinido |
| **1 — Núcleo regional** | Registry do circuito, tela de região inicial, estados persistidos e desbloqueio de vizinhas | Todos os 10 exemplos de Liga corretos, Decades preservado |
| **2 — Importador em modo leitura** | Scanner de RXDATA, PBS, tilesets e grafo de dependências | Relatórios sem modificar o jogo |
| **3 — Importador transacional** | Remap de IDs e referências, plano, backup, apply e rollback | Copiar mapa pequeno e restaurar sem alterar original |
| **4 — Piloto Kanto** | Pallet Town, Route 1, Viridian, primeiro rival e Brock, encontros FireRed/LeafGreen fundidos | Jogar, batalhar, ganhar uma insígnia, salvar e voltar a Decades |
| **5 — Kanto completo** | Oito ginásios, Liga, Sevii (conforme escopo), treinadores/encontros auditados | Liga Kanto libera Decades e Johto; sem duplicatas |
| **6 — Johto completo** | HG/SS fundidos + Liga e viagens | Johto libera Kanto e Hoenn |
| **7 — Hoenn e Sinnoh** | Emerald/Ruby/Sapphire; Platinum/Diamond/Pearl | Conexões, encontros, treinadores, Ligas e metadados íntegros |
| **8 — Unova, Kalos, Alola** | BW/B2W2 por eras; XY; ilhas/provas | Cronologia, alternativas e recompensas sem conflitos |
| **9 — Galar e Paldea** | Sword/Shield e Scarlet/Violet com DLC opcional | Ginásios variantes e Paldea → Galar + Decades |
| **10 — Hisui** | Expedição e viagem temporal opcional | História especial sem falsificar Liga ou esmeraldas |
| **11 — Portal, QA e Android** | Integrar Pokégear, Habitat Dex, álbum, site, distribuição e testes | Save preservado, testes integrados e desempenho aceitável |

**Prioridade absoluta:** antes de dezenas de mapas, concluir **um fluxo vertical** com uma cidade, uma rota, um treinador, uma batalha selvagem, um ginásio, save e viagem inter-regional.

---

## 13. Testes obrigatórios de regressão

### 13.1 Lógica de desbloqueio

- Nova partida pode começar em qualquer uma das dez regiões do circuito; opção especial Hisui possui fluxo próprio.
- Início em Kanto → concluir Kanto → libera **Decades e Johto**, não Galar.
- Início em Johto → concluir Johto → libera **Kanto e Hoenn**.
- Início em Paldea → concluir Paldea → libera **Galar e Decades**.
- Início em Decades → conclusão confirmada da campanha-base → libera **Paldea e Kanto**.
- Verificar todas as demais linhas da tabela do circuito.
- Concluir duas vezes a mesma Liga **não duplica regiões** nem concede novas esmeraldas indevidas.
- Antes da Liga, viagem por uma região bloqueada é recusada; uma região já liberada nunca volta a ser bloqueada.

### 13.2 Insígnias/esmeraldas e balanceamento

- Primeiro ganho único por `badge_key`: **+1** na progressão global Blue; revanche: **+0**.
- Testar fronteiras **1→2**, **4→5** e **10→11** esmeraldas para os quatro estágios.
- Testar jogador nível 10, 50, 60 e 100; treinador comum 70%, selvagem 45%, líder 90% só no Master.
- Confirmar que equipe canônica do treinador no PBS **não foi modificada** pela troca temporária de espécies BST/nível.
- Confirmar que evoluções, formas regionais, Megas, Z, Terastal, Dynamax e IA atual funcionam depois de importar um mapa.
- Confirmar que Alola não concede esmeraldas duplas por prova + kahuna e Paldea não dá recompensa automática adicional por Titãs/Equipe Star.

### 13.3 Mundo e dados

- Testar todos os portais, transições de mapa, colisões, interiores, escadas, curas, Fly/Surf/Dive, controles, música, eventos e cutscenes.
- Verificar `MapPosition`, Town Map e Habitat Dex em todas as áreas e interiores.
- Verificar pesos de encontros somando 100% em cada tabela e ausência de Pokémon inexistente.
- Verificar IDs de espécie, trainer, item e moves; referências a eventos comuns/switches/variáveis e scripts Ruby customizados.
- Verificar que IDs originais do Decades e as 30 áreas com espécies autorais documentadas não foram deslocados.
- Confirmar geração de preview do site e retratos do Álbum por mapa de ID final.

### 13.4 Saves, instalação e desempenho

- Abrir save antigo Decades e conferir equipe, PC, esmeraldas, missões, revanches e derrotas registradas.
- Salvar em Kanto, fechar, reabrir e continuar em Kanto; repetir em Johto e após liberação de Liga.
- Atualizar o instalador sem sobrescrever `game/` nem arquivos de save; backup e rollback funcionando.
- Executar `python -m unittest discover -s tests -v`; validar JS e testes de navegador disponíveis no repositório; observar GitHub Actions.
- Após integrar conteúdo real, compilar PBS pela engine instalada, executar o smoke nativo (`scripts/battle_lab/launch.py --smoke-test`, conforme os scripts atuais) e conferir relatórios `blue-polish-validation.txt`, `blue-journey-validation.txt` e `blue-world-validation.txt` quando pertinentes.
- Testar **Windows primeiro** e depois o pacote experimental **JoiPlay/Android**, incluindo RAM, áudio, carregamento de mapas e controles de toque. Suporte Android não deve ser declarado validado sem teste no dispositivo.

---

## 14. Riscos reais e como mitigá-los

| Risco | Medida preventiva |
|---|---|
| Conflito de IDs de mapas e eventos | Mapeamento simbólico persistente; alocação livre e auditoria das referências |
| Excesso de mapas ou peso de recursos | Inventário/capacidade antes da importação; dividir conteúdo em etapas e evitar carregar assets globais desnecessários |
| Diferenças entre Essentials de fangames | Converter **dados e eventos**, sem substituir o motor Blue |
| Eventos originais que dependem de plugins proprietários ou não presentes | Relatório de incompatibilidade, reimplementação pontual e teste manual |
| Treinadores do mesmo nome em vários jogos | Identificador por região, localização, batalha e variante |
| Mesma insígnia paga duas vezes | Ledger idempotente por `badge_key` e integração transacional à API nativa |
| Nível 100 em campanhas longas | Preservar os percentuais Blue solicitados; avaliar dificuldade em QA sem mudar a fórmula automaticamente |
| Exclusivos de versões bagunçam raridades | Política de fusão por habitat e método com pesos controlados |
| Missões originais de Decades são acionadas por engano | Namespaces separados e validação de pré-condições nos eventos |
| Sincronização site ↔ jogo divergente | Exportar manifestos e IDs efetivos após compilação e testar consistência |
| Copyright/licenças de mapas, imagens, músicas e scripts | Obter autorização explícita ou recriar os recursos; não publicar arquivos de outros fangames sem licença |
| Save antigo corrompido | Migração aditiva com versionamento, backups, rollback e testes de carregamento |

---

## 15. Checklist de pronto para a primeira entrega

- [ ] O jogo permite escolher Kanto, Johto ou Decades como início, sem quebrar a seleção de iniciais e mecânicas atuais.
- [ ] O registro completo das 10 regiões do circuito está implementado e testado, mesmo que mapas das demais ainda não existam.
- [ ] A campanha mantém os **mesmos Pokémon e sistema de batalha** do Dessastre Paradoxal.
- [ ] Pelo menos uma cidade, uma rota, um NPC, um treinador, um encontro selvagem e um líder de Kanto funcionam no jogo instalado.
- [ ] A fusão FireRed/LeafGreen preserva Pokémon exclusivos e não duplica treinadores ou insígnias.
- [ ] Ganhar uma insígnia nova aumenta **uma única vez** a progressão de esmeraldas existente.
- [ ] As fórmulas **70% / 90% Master / 45%** e faixas **0–1 / 2–4 / 5–10 / 11+** permanecem idênticas.
- [ ] Um save antigo do Decades continua carregando sem perda de progresso.
- [ ] Vencer a Liga Kanto libera **Decades e Johto**; Johto libera **Kanto e Hoenn**; Paldea libera **Galar e Decades**.
- [ ] A UI mostra regiões bloqueadas e o motivo do bloqueio.
- [ ] Instalação e rollback não apagam os dados originais.
- [ ] A Habitat Dex, Pokégear e Álbum apresentam IDs e mapas corretos.
- [ ] Os jogos-fonte possuem permissão de uso ou os recursos são reimplementados de forma adequada.

---

## 16. Pós-jogo global: líderes, Elite Four e Campeões com seus times oficiais mais fortes

### 16.1 Momento exato de ativação

**Pedido funcional:** depois que o jogador **zerar uma vez todas as regiões do circuito principal**, os líderes de ginásio, integrantes da Elite Four e Campeões passam a utilizar **o time mais forte que cada personagem apresentou oficialmente**, mantendo o escalonamento de batalha que o Blue já implementou.

Condição sugerida:

```text
world_champion_mode =
  completed_leagues contém exatamente todas as 10 chaves obrigatórias:
  DECADES, KANTO, JOHTO, HOENN, SINNOH, UNOVA,
  KALOS, ALOLA, GALAR, PALDEA
```

- O avanço pode ocorrer em qualquer ordem. A conclusão de **uma** Liga isolada não aciona o pós-jogo mundial.
- A flag é **persistente, monotônica e idempotente**: uma vez ativada, não é desativada por voltar de região, perder uma revanche ou repetir a Liga.
- A aventura especial de **Hisui não bloqueia** a ativação do pós-jogo das dez regiões, pois não possui Liga. Ela ganha revanches próprias ao concluir sua história, mas não entra na lista dos dez títulos de Liga.
- O `completed_leagues` só marca a vitória depois do **evento final validado**, não na derrota do quarto membro da Elite Four nem no início da batalha do Campeão.
- Antes de completar as dez campanhas, líderes, Elite e Campeões usam os perfis **normais, fiéis à região e às versões fundidas**. Depois, em **todas** as próximas batalhas contra esses personagens, o perfil passa a ser `WORLD_CHAMPION_REMATCH`.
- Não alterar retrospectivamente um confronto já iniciado; ler a flag ao **preparar a próxima batalha**, como o sistema Blue faz com suas faixas de progressão.
- Uma única vitória na Liga não concede novamente as mesmas oito insígnias ao repetir a campanha. A revanche fornece EXP, dinheiro e recompensas legítimas já definidas, sem multiplicar esmeraldas ou liberação de regiões.

**Exemplo:** após vencer a última Liga que faltava (digamos, Kalos), o jogo registra `KALOS` como concluída, verifica as dez conquistas e ativa o pós-jogo. Ao retornar a Pewter City, Brock usa o **perfil mais forte referenciado oficialmente para ele**; a luta ainda usa o motor e o balanceamento Blue.

### 16.2 Critério para descobrir o time mais forte — sem inventar times

Para **cada personagem**, catalogar *todas as equipes oficiais pertinentes* disponíveis nos jogos principais: batalha inicial, revanche, pós-jogo, torneios e aparições como líder/campeão, sempre guardando a versão de origem. **Não presumir que o time da primeira Liga seja o mais forte.**

**Escolha do perfil definitivo, nesta ordem:**

1. Preferir a **versão de revanche/postgame mais avançada do personagem** que seja um time oficial de jogos principais (não anime ou equipe criada por fãs).
2. Entre aparições comparáveis, escolher **a equipe oficial mais completa e desenvolvida**, com até seis integrantes, considerando composição, evoluções finais, cobertura, itens e mecânicas; documentar a decisão e a fonte.
3. **Não usar o nível bruto como único critério**: o Blue recalcula os níveis, portanto uma equipe nível 75 não é necessariamente superior à equipe oficial de seis Pokémon nível 65 com estratégia mais forte.
4. Se duas equipes oficiais forem alternativas legitimamente diferentes (ex.: versões ou formações por inicial), registrar **variantes oficiais** e definir uma principal estável ou rotação explícita de revanches. Não montar um time artificial juntando Pokémon de várias versões.
5. Usar nomes, espécies, formas, golpes, itens, habilidades, estratégias e IA compatíveis com o cadastro vigente do Blue. Caso um dado oficial não exista, sinalizar `not_confirmed`; não inventar IVs/EVs/itens como se fossem dados oficiais. Melhorias competitivas **autorais** são permitidas apenas como camada separada e identificada.
6. Nunca ultrapassar **seis Pokémon na party de um NPC**. Treinadores de duplas usam o mesmo formato de batalha já definido pelo jogo. Manter os times históricos para a primeira campanha.
7. Para personagens sem revanche oficial (ou sem formação de seis), escolher a formação oficial mais desenvolvida disponível e registrar a limitação; **não criar espécies extras em nome da fidelidade**.

**Balanceamento permanece idêntico ao implementado no Blue:**

| Regra atual | Pós-jogo mundial |
|---|---|
| Treinadores comuns: `floor(max_party_level × 0.70)` | Sem mudanças |
| Líderes no Master: `floor(max_party_level × 0.90)` | Sem mudanças; usar o handler Blue já existente |
| Selvagens: `floor(max_party_level × 0.45)` | Sem mudanças |
| Faixas globais 0–1, 2–4, 5–10, 11+ esmeraldas | Sem mudanças |
| Limites de BST, golpes e ajustes por estágio | Reutilizar o adaptador em memória; no pós-jogo mundial o jogador já estará no Master se tiver 11+ esmeraldas |
| Dificuldade, itens, IA Blue Radical, Mega/Z/Tera/Dynamax e duplas | Preservar opções e permissões reais da campanha |

**Elite Four e Campeões:** a documentação atual confirma explicitamente **90% apenas para líderes de ginásio no Master**; não atribuir 90% automaticamente à Elite Four ou aos Campeões. Inspecionar os handlers da instalação e **preservar a regra real já aplicada a essas classes**. Se for preciso criar uma regra especial, isso deverá ser uma decisão adicional, não uma alteração silenciosa do cálculo solicitado.

### 16.3 Catálogo obrigatório de adversários por região

As equipes **não estão inventariadas aqui como se tivessem sido importadas**. Esta tabela é o checklist de NPCs cujas **equipes oficiais de primeiro encontro e equipes oficiais mais fortes** devem ser coletadas, verificadas e cadastradas antes de publicar a expansão.

| Região | Líderes, provas ou rivais de desafios | Elite Four e Campeão / equivalente |
|---|---|---|
| **Kanto** | Brock, Misty, Lt. Surge, Erika, Koga (época FRLG), Sabrina, Blaine, Giovanni; Janine e Blue em eventos de Johto/HGSS | Lorelei, Bruno, Agatha, Lance; Campeão Blue (ou variante histórica Trace em desafio extra separado) |
| **Johto** | Falkner, Bugsy, Whitney, Morty, Chuck, Jasmine, Pryce, Clair | Will, Koga, Bruno, Karen; Campeão Lance |
| **Hoenn** | Roxanne, Brawly, Wattson, Flannery, Norman, Winona, Tate e Liza, Wallace (Emerald) ou Juan (variante Emerald); registrar a configuração da campanha principal | Sidney, Phoebe, Glacia, Drake; Campeão Wallace (Emerald) e Steven como desafio especial de Campeão |
| **Sinnoh** | Roark, Gardenia, Maylene, Crasher Wake, Fantina, Byron, Candice, Volkner | Aaron, Bertha, Flint, Lucian; Campeã Cynthia |
| **Unova** | BW: Cilan/Chili/Cress, Lenora, Burgh, Elesa, Clay, Skyla, Brycen, Drayden/Iris. B2W2: Cheren, Roxie, Burgh, Elesa, Clay, Skyla, Drayden, Marlon. Guardar por era/slot | Shauntal, Grimsley, Caitlin, Marshal; Campeões Alder (BW) e Iris (B2W2) como perfis de suas respectivas eras; N é confronto narrativo distinto |
| **Kalos** | Viola, Grant, Korrina, Ramos, Clemont, Valerie, Olympia, Wulfric | Malva, Siebold, Wikstrom, Drasna; Campeã Diantha |
| **Alola** | Capitães Ilima, Lana, Kiawe, Mallow, Sophocles, Acerola e Mina; kahunas Hala, Olivia, Nanu e Hapu; oito provas oficiais USUM (uma não corresponde a oitavo capitão) | USUM: Molayne, Olivia, Acerola, Kahili; desafio final Hau; manter Kukui e os defensores de título de SM/USUM como variantes de história, **não um Campeão anterior inventado** |
| **Galar** | Milo, Nessa, Kabu, Bea/Allister (uma posição), Opal/Bede (sucessão de história), Gordie/Melony (uma posição), Piers, Raihan | **Sem Elite Four oficial**: usar Champion Cup, líderes/rivais das finais e Campeão Leon; incluir Galarian Star Tournament como revanche, quando pertinente |
| **Paldea** | Katy, Brassius, Iono, Kofu, Larry, Ryme, Tulip, Grusha | Rika, Poppy, Larry, Hassel; Campeã de topo Geeta e confronto final com Nemona; Blueberry Elite Four e Kieran são capítulo extra separado |
| **Decades** | Preservar os mestres, líderes e chefes que **existirem de fato** na instalação local | Usar chefes e encerramento reais da campanha; auditar identidade e times antes de criar perfis finais |
| **Hisui (especial)** | Chefes e adversários de história (Adaman, Irida, Kamado, Ingo e outros conforme mapas recriados) | Não inventar ginásios ou Liga; Volo é confronto especial, não "Campeão da Liga de Hisui" |

**Observação de fusão:** quando dois jogos utilizam o mesmo slot de ginásio com personagens diferentes (ex.: Bea/Allister), são **dois oponentes possíveis**, mas **uma única recompensa de insígnia**. Quando há mudança temporal (Unova BW → B2W2) a equipe do personagem depende do arco/era do evento; não transformar os dois jogos em uma única cronologia impossível.

**Fontes oficiais de equipes/rematches a conferir personagem por personagem:**

- [Bulbapedia — Rematch](https://bulbapedia.bulbagarden.net/wiki/Rematch) (panorama de revanche por geração e Liga).
- [Serebii — HGSS Gym Rematches](https://www.serebii.net/heartgoldsoulsilver/gym-rematch.shtml) (Johto e Kanto).
- [Serebii — BDSP Gym Rematches](https://www.serebii.net/brilliantdiamondshiningpearl/gymrematch.shtml) (Sinnoh).
- [Serebii — BDSP Elite Four e Cynthia](https://www.serebii.net/brilliantdiamondshiningpearl/elitefour.shtml).
- [Bulbapedia — Alola Title Defense](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_League_%28Alola%29/Title_Defense).
- [Site oficial Pokémon Sword/Shield — Champion Cup](https://swordshield.pokemon.com/en-us/story/strive-to-become-next-champion/).
- [Bulbapedia — Galar League](https://bulbapedia.bulbagarden.net/wiki/Galar_League).

**Exemplos confirmáveis de uso dos dados oficiais (não equipes inteiras transcritas):** em HGSS, Falkner possui uma equipe de **seis Pokémon** na revanche do Fighting Dojo; em BDSP, a revanche de Roark utiliza **seis**, e Cynthia possui múltiplos perfis fortes de revanche. Esses conjuntos são candidatos a perfil `WORLD_CHAMPION_REMATCH`, **sem substituir seus encontros iniciais**.

---

## 17. Pokémon especiais: regra das oito insígnias da região atual

### 17.1 O que fica bloqueado

**Interpretação operacional do pedido:** somente os grupos **lendários, míticos, Ultra Beasts e Pokémon Paradoxos** ficam sujeitos à exigência das oito conquistas **da região atual**. **Pokémon comuns**, iniciais, pseudo-lendários, formas regionais comuns e Megas de espécies comuns **não são bloqueados por essa regra**.

- **Lendários:** espécies oficialmente marcadas como lendárias, incluindo mascotes dos jogos. Não inferir a classe apenas pelo BST.
- **Míticos:** catálogo separado e explícito; não confundir com lendários por mera força.
- **Ultra Beasts:** todas as espécies catalogadas como Ultra Beast; uma espécie que tenha outra categoria também pode manter ambas as tags.
- **Paradoxos:** formas do passado e futuro oficiais, bem como os Paradoxos autorais de Dessastre Paradoxal. Identificar por IDs e manifestos; não bloquear erroneamente toda evolução autoral ou toda forma regional.
- **Megas / forma temporária:** a classificação de restrição acompanha a **espécie-base** e eventuais categorias explícitas, não o item Mega Stone; uma Mega comum continua permitida.
- **Ovos/transformações/formas:** classificar a espécie efetiva que entraria na party ou batalha; impedir bypass por evolução, forma, ovo, presente, troca, retirada em massa ou plugins externos.

**Regra principal:**

```text
can_join_party(pokemon, current_region):
  se pokemon NÃO é especial: PERMITIR
  se região está totalmente habilitada para especiais: PERMITIR
  caso contrário: BLOQUEAR, explicando o motivo

region_allows_specials(region):
  regiões de oito ginásios: obter as 8 badge_keys LOCAIS
  ALOLA: concluir as 8 provas oficiais da campanha USUM fundida
  DECADES: concluir os 8 marcos nativos auditados para essa função
  HISUI: exceção explícita = concluir o arco principal histórico
```

Em Kanto com 8 insígnias, um lendário ou Paradoxo pode ser usado. Ao entrar em Johto com 0 insígnias locais, esse Pokémon **deixa a party e fica indisponível no PC para a party de Johto**. Ao conquistar a oitava insígnia de Johto, a retirada se torna disponível de novo **sem alterar a propriedade, o nível ou o armazenamento do Pokémon**.

### 17.2 Transferência automática para a Box ao mudar de região

**A regra também vale para o primeiro spawn, load de save e eventos que troquem a região atual**, não só para o NPC pós-Liga.

Fluxo transacional proposto:

1. O jogador seleciona uma região de destino já desbloqueada.
2. Verificar quais Pokémon da party possuem tags especiais.
3. Verificar se o destino **já possui as oito conquistas locais** (ou exceção equivalente para Decades/Hisui).
4. Se não possuir, identificar os especiais que terão de sair da party. Reservar vagas reais em Boxes; **não sobrescrever slots nem descartar Pokémon**.
5. **Se não houver espaço**, oferecer gerenciamento de PC antes da viagem ou cancelar com a party intacta. **Não liberar a viagem de modo que o save perca Pokémon.**
6. Se os Pokémon restantes formarem uma party vazia, exigir que o jogador selecione um Pokémon comum do PC **antes da transferência**; no começo de uma nova jornada, conceder o inicial regional no fluxo normal sem burlar a restrição. Nunca iniciar uma partida com equipe inválida.
7. Efetuar a operação atômica: depositar especiais, registrar a procedência/estado de retenção, trocar a região e salvar; em falha, restaurar a party e os slots originais.
8. Ao abrir o PC na região restrita, mostrar as criaturas com cadeado e texto: "Disponível após as 8 insígnias de [Região]"; permitir visualização, organização e consulta à Pokédex, mas **não retirada para a party**.
9. Ao ganhar a oitava conquista local, remover o bloqueio **dessa região** automaticamente. Pokémon depositados não voltam à party sozinhos; o jogador os retira do PC quando quiser.
10. Voltar para uma região onde as oito insígnias **já estão completas** permite retirar especiais normalmente. Os Pokémon continuam na Box até o jogador escolher sua party.

**Não criar uma Box isolada que impossibilite a gestão.** Um marcador opcional de "depósito automático por viagem" é metadado, não um novo proprietário nem outra espécie.

### 17.3 Bloqueios obrigatórios que evitam contornar a regra

A checagem deve ser centralizada num serviço de regras de party, chamado por todos os caminhos de entrada/uso de Pokémon:

- PC: retirar, trocar, mover para party, retirar múltiplos, organização rápida e trocas de box.
- Captura e recebimento: após capturar/receber especial numa região sem oito marcos, enviá-lo **diretamente para o PC**; manter a captura válida e o registro na Pokédex.
- Presentes, trocas, criação via script, importação, evolução/formas e soluções da campanha que alterem Pokémon da party.
- Carregamento de saves antigos, scripts de teleporte/Fly, eventos de transição, New Game+ futuro e menus de equipamento de equipe.
- Antes de iniciar **batalha na campanha**, validar a party por segurança, para não permitir que um plugin coloque um especial ilegal nela.
- O **Hub de Batalha, laboratório e multiplayer de arena** permanecem separados do save de campanha e da restrição de oito insígnias, conforme seu isolamento atual. Não alterar os times livres do Hub.
- Pokémon de montaria por história (**Koraidon/Miraidon**) podem liberar travessia de Paldea, mas isso **não concede permissão de usá-los como combatentes** antes das oito insígnias locais; manter ações de montaria e party de batalha separadas.

### 17.4 Fonte de verdade: local vs. global

| Controle | Fonte de verdade | Pode ser liberado por 8 esmeraldas globais? |
|---|---|---|
| Faixa de BST, golpes, dinheiro e níveis Blue | Contador **global** de esmeraldas existente | Sim, usa as faixas nativas já implementadas |
| Desbloqueio de Pokémon especiais na party | **Oito insígnias/provas da região atual** | **Não** |
| Viagem a outras regiões | Conclusão da Liga atual e circuito de destinos desbloqueados | Não, exige Liga/encerramento |
| HM de campo e transporte regional | Insígnia, missão ou ferramenta **local específica** | **Não** |
| Equipes definitivas de líderes/Elite/Campeões | Dez Ligas concluídas uma vez no save | **Não** |

> **Atenção:** o jogador pode somar 60 esmeraldas globais e continuar sem permissão para usar especiais em uma região com apenas três insígnias locais. Isso **não é bug**: é a regra multirregional solicitada. O combate continua em Master porque o estágio global não foi resetado.

---

## 18. NPC de transporte após a Elite Four / Liga

### 18.1 Condição de aparição e localização

- Adicionar um NPC de transporte **na saída segura do complexo da Liga**, após finalizar as batalhas obrigatórias da Elite Four **e do Campeão ou evento final equivalente**.
- **Não** aparecer em uma sala que interrompa a sequência Elite Four → Campeão; uma vitória parcial não basta para liberar viagem.
- Em Galar, o gatilho é a vitória no **Champion Cup** e seu encerramento, pois **não existe Elite Four oficial**.
- Em Paldea, utilizar a conclusão do **Champion Assessment / Victory Road** conforme a campanha fundida (Elite Four, Geeta e encerramento com Nemona, se adotado como evento final).
- Em Alola, usar a conclusão do primeiro desafio de título e do encerramento da Liga; a defesa do título depois não repete desbloqueios.
- Em Decades, só colocar o NPC **após localizar o encerramento real da campanha-base**. Não colocar um NPC que permita pular o roteiro atual.
- Hisui é exceção sem Elite Four; a viagem fica disponível depois do evento final da expedição.

### 18.2 Menu do NPC

```text
Agente de Transporte Regional

"Parabéns! Você concluiu esta Liga.
 Para onde deseja seguir sua jornada?"

  > Viajar para outra região
      - Kanto        [disponível / bloqueada]
      - Johto        [disponível / bloqueada]
      - ...
      - Decades      [disponível / bloqueada]
  > Consultar mapa das regiões
  > Ver regras da região escolhida
  > Acessar PC / organizar equipe
  > Curar equipe
  > Permanecer nesta região
```

- O NPC mostra **todas as regiões já desbloqueadas** (incluindo região inicial e outras Ligas vencidas), e informa por que outras estão bloqueadas. As duas recém-liberadas aparecem em destaque.
- A viagem é **opcional**, nunca forçada. Fechar o diálogo devolve o jogador à Liga.
- A confirmação informa que especiais ficarão no PC se o destino tiver menos de oito insígnias; executa a validação e a transferência atômica descritas na seção 17.
- O destino é o **ponto de chegada aprovado** da região (cidade inicial, estação ou porto), não uma coordenada genérica ou mapa inexistente.
- A opção de retorno deve existir em pontos oficiais (portos, estações, aeroportos) ou menu de transporte já alcançado, para evitar que o jogador fique preso após viajar.
- O NPC pode ter sprite e falas regionais próprios, mas deve chamar **um só serviço de viagem**. Não duplicar a lógica de desbloqueio, PC e save em cada mapa.

### 18.3 Sequência de finalização segura

```text
Vencer a última batalha obrigatória da Liga
  → executar cena de campeão / encerramento
  → registrar league_completed[região] UMA vez
  → liberar anterior e próxima pela regra do circuito
  → verificar world_champion_mode (10/10)
  → gravar flags e save de maneira segura
  → abrir/ativar NPC de transporte após o encerramento
  → usuário escolhe destino ou permanece
  → validar PC / especiais / party / mapa de chegada
  → viajar e salvar posição
```

**Exemplo:** finalizar a Liga de Johto libera **Kanto e Hoenn**. O agente aparece na saída e oferece essas regiões, além de outras anteriormente desbloqueadas; escolher Hoenn com apenas duas insígnias de Hoenn faz depositar automaticamente os Paradoxos/lendários da party.

---

## 19. HMs e mobilidade: permissões locais e fidelidade a cada região

### 19.1 Princípio de implementação

**Cada região consulta suas próprias insígnias, provas, eventos e itens-chave**, não o total global de esmeraldas. O golpe aprendido no Pokémon pode ser usado **em batalha** conforme a engine, mas o **efeito no cenário** exige permissão regional e, quando cabível, possuir a habilidade/movimento/ferramenta.

Isso evita que um jogador que obteve Surf em Hoenn atravesse os obstáculos de Johto sem a Fog Badge, ou use uma montaria de Paldea para ignorar missões de Alola.

As tabelas a seguir usam os critérios oficiais das **versões escolhidas como base**; mudanças por fusão devem ser registradas no manifesto da região, não inferidas do número total de insígnias.

### 19.2 Kanto — FireRed/LeafGreen

| HM de campo | Insígnia local exigida |
|---|---|
| Flash | Boulder Badge (Brock) |
| Cut | Cascade Badge (Misty) |
| Fly | Thunder Badge (Lt. Surge) |
| Strength | Rainbow Badge (Erika) |
| Surf | Soul Badge (Koga) |
| Rock Smash | Marsh Badge (Sabrina; Sevii) |
| Waterfall | Volcano Badge (Blaine; Sevii) |

O Earth Badge de Giovanni continua sendo necessário para a conclusão dos oito ginásios e a Liga, mas **não desbloqueia um HM adicional na lista principal de FRLG**.

### 19.3 Johto — HeartGold/SoulSilver

| HM de campo | Insígnia exigida |
|---|---|
| Rock Smash | Zephyr Badge (Falkner) |
| Cut | Hive Badge (Bugsy) |
| Strength | Plain Badge (Whitney) |
| Surf | Fog Badge (Morty) |
| Fly | Storm Badge (Chuck) |
| Whirlpool | Glacier Badge (Pryce) |
| Waterfall | Rising Badge (Clair) |
| Rock Climb | Earth Badge de **Kanto**, conforme HGSS; desbloqueio posterior específico, não concedido pelo total de Johto |

A Mineral Badge de Jasmine permanece conquista local do ginásio, mesmo sem liberar um HM nessa tabela.

### 19.4 Hoenn — Emerald (fundida com Ruby/Sapphire)

| HM de campo | Insígnia local exigida |
|---|---|
| Cut | Stone Badge (Roxanne) |
| Flash | Knuckle Badge (Brawly) |
| Rock Smash | Dynamo Badge (Wattson) |
| Strength | Heat Badge (Flannery) |
| Surf | Balance Badge (Norman) |
| Fly | Feather Badge (Winona) |
| Dive | Mind Badge (Tate e Liza) |
| Waterfall | Rain Badge (Wallace/Juan, conforme arco) |

### 19.5 Sinnoh — Platinum como base

| HM de campo | Insígnia local exigida |
|---|---|
| Rock Smash | Coal Badge (Roark) |
| Cut | Forest Badge (Gardenia) |
| Fly | Cobble Badge (Maylene) |
| Defog | Relic Badge (Fantina) |
| Surf | Fen Badge (Crasher Wake) |
| Strength | Mine Badge (Byron) |
| Rock Climb | Icicle Badge (Candice) |
| Waterfall | Beacon Badge (Volkner) |

**Atenção à fusão:** Diamond/Pearl inverte os requisitos de Surf/Defog em relação a Platinum. Como **Platinum é a campanha principal definida**, usar **Fen→Surf e Relic→Defog**; não criar dois requisitos incompatíveis no mesmo mapa.

### 19.6 Unova — Black/White e Black 2/White 2

**Particularidade oficial:** na geração V, o uso de HMs fora de batalha **não depende de uma insígnia específica**. O avanço é controlado pelo **momento em que o golpe/ferramenta é obtido e pelos bloqueios do roteiro**. Portanto:

- Preservar os HMs **Cut, Fly, Surf, Strength, Waterfall e Dive** e as condições reais de obtenção de cada era BW/B2W2.
- Não conceder uma autorização global de HM só porque o usuário trouxe o golpe de outra região; ao entrar em Unova, respeitar ao menos as condições narrativas e locais da versão fundida.
- Se futuramente for preferida uma regra customizada "HM só após uma insígnia" em Unova, isso deverá constar como **adaptação autoral**, pois não corresponde aos jogos originais.
- **As oito insígnias de Unova continuam exigidas para usar Pokémon especiais na party**, independentemente dessa ausência de requisito de HM.

### 19.7 Kalos — X/Y

| HM de campo | Insígnia local exigida |
|---|---|
| Cut | Bug Badge (Viola) |
| Strength | Cliff Badge (Grant) |
| Surf | Rumble Badge (Korrina) |
| Fly | Plant Badge (Ramos) |
| Waterfall | Iceberg Badge (Wulfric) |

Rock Smash existe como ação de campo em X/Y sem ser HM; tratar como habilidade/evento local apropriado.

### 19.8 Alola — Ultra Sun/Ultra Moon

**Não há ginásios nem HMs de exploração tradicionais.** Usar o sistema **Poké Ride** por marcos da aventura, não um painel de badges falsificado:

| Ação / montaria | Desbloqueio narrativo de referência |
|---|---|
| Tauros Charge (quebrar rochas) | Grande Prova de Hala em Melemele |
| Stoutland Search | Evento de Mallow em Paniola Ranch |
| Lapras Paddle (água) | Evento de Lana em Brooklet Hill |
| Charizard Glide (viagem) | Prova/evento de Kiawe |
| Mudsdale Gallop | Hapu, ao chegar à Route 12 |
| Sharpedo Jet (água/obstáculos) | Evento de Grimsley na Route 15 |
| Machamp Shove (pedras) | Evento da avó de Hapu em Ancient Poni Path |

Para a **regra de oito conquistas antes de especiais**, usar **as oito provas oficiais de USUM**; os quatro kahunas não geram uma segunda esmeralda. Acompanhar o progresso das provas e o das montarias em flags independentes.

### 19.9 Galar — Sword/Shield

**Não existem HMs obrigatórios para exploração:** usar **Flying Taxi**, **Rotom Bike** e sua capacidade de andar sobre a água, obtidos por eventos da história, conforme Sword/Shield.

- **Flying Taxi:** desbloquear após o evento correspondente na campanha em Motostoke.
- **Rotom Bike:** conceder pela progressão do roteiro; **Water Mode** após o encontro de Route 9, depois de Circhester.
- **Oito insígnias de Galar:** continuam exigidas para permitir lendários/míticos/Ultra Beasts/Paradoxos na party de Galar.
- Ginásios variantes Sword/Shield são **o mesmo slot de insígnia**, não duas recompensas.

### 19.10 Paldea — Scarlet/Violet

**Não existem HMs tradicionais:** usar montaria **Koraidon/Miraidon** e desbloqueios das cinco missões de Titãs (Path of Legends):

| Titã / marco | Habilidade de travessia |
|---|---|
| Stony Cliff Titan | Correr mais rápido (Dash) |
| Open Sky Titan | Nadar (Surf equivalente) |
| Lurking Steel Titan | Saltar mais alto |
| Quaking Earth Titan | Planar |
| False Dragon Titan | Escalar paredes |

- As **oito insígnias de ginásio** de Paldea (Victory Road) liberam Pokémon especiais para **batalhas** na região; as insígnias de Titã/Team Star não contam como oito ginásios, nem somam esmeraldas de ginásio novamente.
- O uso narrativo de Koraidon/Miraidon como **montaria** não contorna o bloqueio de combate da espécie até obter as oito insígnias locais.

### 19.11 Hisui e Decades

- **Hisui:** sem HMs e sem ginásios; usar montarias e permissões por eventos de história para Wyrdeer, Ursaluna, Basculegion, Sneasler e Hisuian Braviary. Liberação de Pokémon especiais na party ao **concluir o arco principal de Hisui**, sem inventar oito insígnias.
- **Decades:** **não substituir** as regras atuais de campo. Identificar como seus mapas/eventos já liberam Surf, Fly, Cut e afins e manter as precondições reais; o bloqueio de especiais usa **oito marcos distintos auditados** da campanha, sem duplicar recompensas ou flags.

### 19.12 Contrato único para a checagem de campo

```ruby
# PSEUDOCÓDIGO — os nomes NÃO são métodos existentes verificados
# Chamado pelo evento do obstáculo, menu de campo, Fly, Surf, Ride etc.
def can_use_field_action?(region, action, save)
  cfg = REGIONAL_FIELD_RULES[region][action]
  return false unless cfg
  return false unless has_required_field_tool_or_move?(action, save)
  return false unless has_required_local_badge_or_story_flag?(region, cfg, save)
  true
end
```

- Sempre validar também **obstáculos/eventos reais**, não apenas o menu visual.
- O jogador pode **aprender e usar** Surf em batalha antes de desbloquear seu uso **no cenário**.
- Uma HM ensinada em Kanto não transfere automaticamente sua permissão de campo para Johto ou Hoenn.
- Os itens e modos de campo do Decades não podem ser apagados pelo importador; adicionar apenas as validações regionais onde necessárias.

**Fontes das regras de campo:** [Bulbapedia — HMs por geração](https://bulbapedia.bulbagarden.net/wiki/HM), [Serebii — Platinum HMs](https://www.serebii.net/platinum/tmhm.shtml), [Bulbapedia — Poké Ride](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9_Ride), [Bulbapedia — Rotom Bike](https://bulbapedia.bulbagarden.net/wiki/Rotom_Bike), [Bulbapedia — Koraidon](https://bulbapedia.bulbagarden.net/wiki/Koraidon_%28game%29).

---

## 20. Persistência e integração técnica das novas regras

### 20.1 Dados adicionais de save — conceitual

Não gravar os campos abaixo como variáveis soltas no jogo antes de verificar como o Blue/Essentials salva o estado. Integrá-los ao módulo de persistência existente, com migração de versão e backups.

```json
{
  "schema_version": 2,
  "initial_region": "JOHTO",
  "current_region": "HOENN",
  "unlocked_regions": ["JOHTO", "KANTO", "HOENN"],
  "completed_leagues": ["JOHTO"],
  "world_champion_mode": false,
  "regional_progress": {
    "JOHTO": {
      "badges": ["JOHTO_ZEPHYR", "JOHTO_HIVE"],
      "local_badge_count": 2,
      "field_actions": ["ROCK_SMASH", "CUT"],
      "special_party_unlocked": false
    },
    "HOENN": {
      "badges": [],
      "local_badge_count": 0,
      "field_actions": [],
      "special_party_unlocked": false
    }
  },
  "alola_trials_completed": [],
  "paldea_titan_abilities": [],
  "hisui_story_complete": false,
  "decades_special_milestones": [],
  "region_transfer_history": [],
  "auto_box_origin_notes": []
}
```

O campo `local_badge_count` deve ser **derivado do conjunto de IDs únicos**, nunca um contador mutável isolado. `special_party_unlocked` deve ser **derivado das conquistas** ou cache recalculado, não fonte de verdade contraditória. `global_emeralds` permanece no **contador nativo atual**, sem espelho gravável independente.

### 20.2 Separação de responsabilidades

```text
Blue Story Runtime — sistema existente, preservar
├── Balanceador de níveis / BST / golpes / IA / economia
├── Pokémon / formas / captura / batalha / PC / save
└── Novos adaptadores regionais (propostos)
    ├── LeagueProgress: conclusão real + desbloqueio do circuito
    ├── WorldChampionMode: 10 Ligas concluídas + times máximos oficiais
    ├── RegionalBadges: insígnias/provas locais + esmeraldas nativas
    ├── SpecialSpeciesPolicy: lendários/míticos/UB/Paradoxos
    ├── SafeRegionTransfer: mover especiais à Box antes da viagem
    ├── RegionalFieldAccess: HM, ride, mapa e pré-requisitos locais
    ├── LeagueTravelNPC: menu único, destinos e transições
    └── TrainerProfiles: first_run vs world_champion_rematch
```

### 20.3 Manifestos sugeridos

```text
data/regions/
├── registry.json                 # circuito já documentado
├── legendary-mythical-ub-paradox.json
├── league-completions.json
├── official-trainer-profiles.json # equipes com fonte, versão e licença
├── field-permissions.json        # [região][ação] => pré-requisito local
├── badge-registry.json           # IDs únicos para cada região
├── travel-npcs.json              # mapa da Liga, condição e chegada
└── alola-trials.json             # oito provas USUM
```

**Exemplo de perfil de treinador (forma, não dados reais):**

```json
{
  "key": "SINNOH_ROARK",
  "region": "SINNOH",
  "trainer_type": "LEADER",
  "profiles": {
    "FIRST_CLEAR": "reference_to_verified_original_team",
    "WORLD_CHAMPION_REMATCH": "reference_to_verified_strongest_official_team"
  },
  "sources": [
    "https://www.serebii.net/brilliantdiamondshiningpearl/gymrematch.shtml"
  ],
  "battle_balance": "USE_EXISTING_BLUE_RUNTIME"
}
```

**Exemplo de regra de campo (forma, não ID já implementado):**

```json
{
  "region": "SINNOH",
  "action": "SURF",
  "source_game": "PLATINUM",
  "requires_local_badge": "SINNOH_FEN",
  "requires_move_or_tool": true
}
```

**Integração obrigatória:** ligar esses manifestos à documentação do Blue Studio, à Habitat Dex/Pokégear e ao site, sem criar um segundo cadastro de Pokémon. A importação deve **validar** que todos os IDs simbólicos de espécies, itens, golpes, badges, mapas e trainers realmente existam.

### 20.4 Sem modificação destrutiva de saves

- Saves anteriores recebem os novos campos com padrão seguro e são migrados com backup; não apagar a equipe ou a Box ao entrar em um save antigo.
- Não recontar retroativamente conquistas **sem evidência inequívoca** dos eventos existentes. Em Decades, primeiro auditar e migrar marcos comprovados.
- O primeiro carregamento em mapa de outra região precisa conciliar `current_region`, posição real, restrições da party e flags de campo antes de permitir ações.
- A instalação conserva `game/`, `.blue-backups/`, gráficos, DBK/Essentials e saves; mapas importados são assets separados de origem licenciada.
- Não publicar equipes oficiais completas e artes de projetos de terceiros sem observar direitos e autorizações aplicáveis; manter metadados, fontes e autorização da importação.

---

## 21. Plano de testes do pós-jogo, Box, NPC e HMs

### 21.1 Pós-jogo e equipes definitivas

- [ ] 9/10 Ligas concluídas: `world_champion_mode == false`.
- [ ] 10/10 Ligas concluídas: ativar o modo uma só vez, persistir após reload.
- [ ] Hisui incompleta com 10/10 Ligas: modo mundial ainda ativa; Hisui não é Liga.
- [ ] Brock, Falkner, Roxanne, Cynthia, Iris, Diantha, Geeta e Leon: seleção correta de perfil **oficial** após ativar o modo, mantendo o perfil de primeira campanha arquivado.
- [ ] Galar sem Elite Four fictício; Alola com provas e liga corretas; Decades sem inventar equipe de campeão.
- [ ] Verificar um líder Master com maior nível do jogador 60 → Pokémon dele ajustado pelo handler nativo para 54; treinador comum → 42; selvagem → 27.
- [ ] A equipe-fonte oficial não é regravada pelo balanceamento; recompensas de revanche não somam novas insígnias/esmeraldas.
- [ ] Treinador de dupla mantém o formato de duplas que o Blue já usa, mesmo com equipe-base de seis.

### 21.2 Regra dos Pokémon especiais

- [ ] Kanto 7/8 insígnias: lendários, míticos, UB e Paradoxos não entram na party; 8/8: entram.
- [ ] Johto com 0/8: trocar Kanto (8/8) → Johto deposita especiais na Box sem perda de itens/IVs/EVs/forma/shiny.
- [ ] Pokémon comum, pseudo-lendário e Mega de espécie comum permanecem elegíveis na party.
- [ ] Captura de especial com 0/8: vai direto à Box e aparece na Pokédex.
- [ ] PC não permite retirar especial com 7/8; permite com 8/8 sem precisar reiniciar o jogo.
- [ ] Se a Box estiver cheia, viagem aborta sem modificar equipe nem posição.
- [ ] Se sobrariam 0 Pokémon na party, exigir escolher comum antes de viajar; não criar save injogável.
- [ ] Fluxo de troca, presente, script, evolução, carregamento de save e plugin não burlam bloqueio.
- [ ] Hub de Batalha e laboratório continuam livres e isolados das restrições da campanha.
- [ ] 80 esmeraldas globais e apenas 3 insígnias locais → especial bloqueado, mas o estágio Master permanece.

### 21.3 NPC de transporte

- [ ] Vencer só o quarto membro da Elite Four não cria transporte prematuro.
- [ ] Concluir Campeão/encerramento mostra NPC na saída da Liga e salva antes da escolha.
- [ ] Johto → libera Kanto + Hoenn; Kanto → Decades + Johto; Paldea → Galar + Decades.
- [ ] NPC lista destinos bloqueados com motivo e oferece cancelar, PC, cura e mapa.
- [ ] Escolher destino testa espaço de Box e party, deposita especiais necessários e só então transfere.
- [ ] Existe retorno por posto/estação/porto após viagem; não há softlock.
- [ ] Revanche não cria duplicata de NPC, desbloqueia região extra ou incrementa esmeralda.
- [ ] Galar ativa NPC após Champion Cup, não após Elite Four inexistente.

### 21.4 HMs, montarias e pré-requisitos locais

- [ ] Kanto: Cut exige Cascade, Surf exige Soul; Surf pode ser golpe em batalha antes da badge, mas não usado no cenário.
- [ ] Johto: Surf exige Fog, Rock Smash exige Zephyr; possuir Soul Badge de Kanto não substitui Fog de Johto.
- [ ] Hoenn: Dive exige Mind; Waterfall exige Rain.
- [ ] Sinnoh Platinum: Surf exige Fen e Defog exige Relic; não aplicar inversão Diamond/Pearl.
- [ ] Unova: sistema oficial de HM sem badge de campo; respeitar obtenção e bloqueios narrativos da campanha fundida.
- [ ] Kalos: Waterfall exige Iceberg.
- [ ] Alola: Ride Pager e montarias por eventos, sem HM artificial; oito provas distintas para especiais.
- [ ] Galar: Flying Taxi e Rotom Bike/Water Mode por história; ginásios alternativos contam uma badge por slot.
- [ ] Paldea: habilidades de Koraidon/Miraidon por Titãs; oito ginásios para uso de especiais na party.
- [ ] Hisui: montarias por história; sem badges fictícias.
- [ ] Decades: regressão de todas as condições originais de campo antes e depois do importador.
- [ ] O carregamento de saves e o retorno por Fly/teleporte não permitem atravessar travas regionais.

---

## 22. Critérios de pronto adicionais à primeira versão

- [ ] Manifesto completo dos dez conjuntos de líderes, Elite e Campeões (ou desafios equivalentes), com **fonte exata** para cada equipe oficial mais forte; sem campos inventados.
- [ ] `world_champion_mode` só ativa depois das **dez** conquistas de Liga, com Hisui especial fora do requisito.
- [ ] Todas as regiões registram suas oito conquistas locais (Alola = oito provas USUM; Decades = oito marcos auditados; Hisui = exceção de história).
- [ ] A política de especiais distingue lendários, míticos, UB e Paradoxos, incluindo os autorais, sem bloquear espécies comuns.
- [ ] Troca de região move a party especial à Box automaticamente quando necessário, com guarda de capacidade e rollback.
- [ ] PC, captura, trocas, presentes e batalha da campanha aplicam **a mesma** regra de elegibilidade regional.
- [ ] NPC pós-Liga presente nas saídas de todas as regiões, respeitando encerramentos alternativos de Galar, Paldea, Alola e Decades.
- [ ] HMs/ride usam mapeamentos **locais**, com testes das diferenças entre FRLG, HGSS, Emerald, Platinum, Unova, XY, Alola, Galar, Paldea e Hisui.
- [ ] O balanceador existente do Blue continua responsável por níveis, BST, golpes, IA e prêmios; nenhuma fórmula nova substituiu seus handlers.
- [ ] Windows, autosave/save antigo, PC e Android/JoiPlay foram testados; originais e backups preservados.

---

## 23. Conclusão e ordem de decisão

A solução mais segura é transformar o Blue Dessastre Paradoxal num **único projeto Pokémon Essentials com múltiplas regiões**, não em uma fusão de dez executáveis. O **Decades continua sendo o núcleo**, e cada região adiciona conteúdo de exploração, batalhas e história por meio de manifestos e importações controladas.

**Regras fixas do planejamento:** escolher a região inicial; preservar as equipes canônicas e os encontros das versões fundidas; usar o cálculo atual por esmeraldas; uma Liga libera seus dois vizinhos; Decades liga Kanto e Paldea; Hisui é especial e sem Liga. **Após as dez Ligas vencidas uma vez**, os líderes, Elite e Campeões passam para os perfis oficiais mais fortes. **Pokémon lendários, míticos, Ultra Beasts e Paradoxos** exigem oito conquistas na região atual (com exceções próprias para Decades/Hisui); viagens depositam esses Pokémon na Box quando a região de destino os restringe. O NPC de transporte é habilitado após o encerramento da Liga; HMs e montarias respeitam requisitos locais. As únicas definições que dependem de auditoria técnica do jogo instalado são os **pontos exatos de gancho**, a **rotina de concessão de esmeraldas**, o **evento de conclusão do Decades**, a **capacidade real de mapas** e as **licenças dos projetos-fonte**.

**Primeira implementação sugerida:** construir o registro de regiões e o mecanismo de save/desbloqueio, depois importar **Pallet Town + Route 1 + Viridian + um confronto de rival + Brock**, mantendo as batalhas Blue. Isso testa todos os pontos arquiteturais que depois serão repetidos em Johto, Hoenn, Sinnoh, Unova, Kalos, Alola, Galar, Paldea e Hisui.

### Fontes técnicas adicionais

- [Documentação de múltiplas regiões no Essentials](https://essentialsdocs.fandom.com/wiki/Multiple_regions)
- [Documentação de metadados de mapas](https://essentialsdocs.fandom.com/wiki/Map_metadata)
- [Estrutura de dados de treinadores no Essentials v21.1](https://github.com/silveredmeadow/pokemon-essentials-v21.1-github/blob/master/Data/Scripts/010_Data/002_PBS%20data/015_Trainer.rb)

**Observação final:** dados oficiais de jogos diferentes podem conflitar em cronologia, times de treinadores e eventos. O documento define regras de integração, mas a extração dos dados e a confirmação de permissões precisam ser feitas fonte a fonte. Não foi realizada importação de mapas ou alteração de código neste documento.
