# Sinnoh — detonado de Pokémon Platinum organizado para o Dessastre Paradoxal

**Projeto:** [Pokémon Blue: Dessastre Paradoxal](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal)  
**Data da compilação:** 13/11/2026  
**Referência narrativa principal:** [Pokémon Mythology — Detonado Platinum](https://www.pokemythology.net/detonados/detonado-platinum/)  
**Finalidade:** documento de consulta para construir, verificar e publicar a campanha de Sinnoh no Blue.  
**Natureza:** síntese própria de fatos do jogo, marcos, localizações, progressão, personagens, equipes históricas, atividades opcionais e requisitos técnicos; **não é transcrição nem reprodução** do detonado, de seus diálogos, imagens ou mapas.

> **ATENÇÃO — ESTADO REAL:** este MD descreve o conteúdo de referência de Pokémon Platinum. Não significa que os mapas, eventos, músicas, NPCs ou batalhas estejam funcionando no Blue. As barras de aceite e as evidências reais permanecem em [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md). Nenhuma fase deve ser declarada jogável só porque está descrita aqui.

## 0. Índice e convenções

1. Premissas do projeto e integração segura.
2. Visão geral e circuito de Sinnoh.
3. Os oito ginásios, equipes e HMs.
4. Campanha completa dividida em 43 marcos.
5. Equipe Galactic, eventos e dependências.
6. Personagens, rivais e parceiros.
7. Locais, encontros notáveis, itens e serviços.
8. Eventos diários, sazonais e atividades opcionais.
9. Liga Pokémon: Elite Four e Cynthia.
10. Pós-Liga e National Dex.
11. Lendários, míticos e eventos especiais.
12. Battle Zone, Battle Frontier e revanches.
13. Inventário dos mapas/rotas e conexões.
14. Matriz de flags, testes e checklist para Codex.
15. Fontes, limites e pendências de auditoria.

**Etiquetas usadas:** **PLATINUM** indica um fato do jogo de referência; **BLUE — REQUISITO** indica o que deve ser adaptado; **OPCIONAL** não pode travar a Liga; **PÓS-LIGA** pressupõe Hall of Fame; **VALIDAR** exige inspeção do jogo e/ou da fonte real.

### 0.1 Documentos que continuam sendo a fonte de verdade técnica

- [SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md): execução técnica, gates, salvaguardas e ordem das fases.
- [SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](SINNOH_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md): análise de fontes, direitos e compatibilidade de mapas/áudio.
- [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md): barras separadas de preparação, integração e jogabilidade nativa.
- [SINNOH_CODEX_PENDENCIAS.md](SINNOH_CODEX_PENDENCIAS.md): tarefas que dependem do ambiente local.
- [SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md): evento autoral de introdução e três Poké Bolas físicas.
- [PLANO_REGIOES_DESSASTRE_V2.md](PLANO_REGIOES_DESSASTRE_V2.md) e [CIRCUITO_REGIONAL.md](CIRCUITO_REGIONAL.md): regras globais e viagem entre regiões.
- [KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md](KANTO_DETONADO_FIRERED_LEAFGREEN_REFERENCIA_ORGANIZADA.md), [JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md](JOHTO_DETONADO_HEARTGOLD_SOULSILVER_REFERENCIA_ORGANIZADA.md), [HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md](HOENN_DETONADO_EMERALD_REFERENCIA_ORGANIZADA.md): padrão de documentação das campanhas.

### 0.2 Regras obrigatórias do Blue

1. Platinum determina **o mundo e a sequência narrativa**, não substitui o motor de batalha/IA, balanceamento, espécies, golpes, habilidades, saves, BlueMusic, interface ou sistema de progressão já existente.
2. **Um badge local de Sinnoh = uma conquista regional e +1 unidade global de esmeralda**, sem duplicar conquistas ao revisitar ou repetir batalha. A autorização dos HMs de Sinnoh obedece às **insígnias locais e respectivos eventos**.
3. **Não gravar níveis fixos nos painéis públicos do site.** Os níveis deste arquivo são exclusivamente a fotografia histórica de Platinum. Treinadores, evolução por level cap e dificuldade Normal/Master seguem o algoritmo do Blue.
4. Lendários, míticos, Ultra Beasts e Paradoxos podem ser sujeitos à regra regional existente: **uso na party somente após oito badges locais**; ao mudar para região sem oito badges, transferência segura à Box e impedimento de retirá-los enquanto bloqueados.
5. Uma nova partida que começar em Sinnoh usa o roteiro regional uma única vez; chegar por viagem **não pode entregar outro inicial**, limpar flags, sobrescrever inventário ou repetir recompensas.
6. O NPC de viagem do circuito deve ficar na **cidade inicial (Twinleaf)** após o desbloqueio correspondente; o barco de Snowpoint para Battle Zone é transporte **interno a Sinnoh**, não substitui o circuito de outras regiões.
7. O pós-jogo forte **global** só é liberado após as dez Ligas previstas no projeto; os rematches próprios de Platinum podem existir como conteúdo local, com gatilhos próprios.
8. Preservar integralmente **Decades, Kanto, Johto, Hoenn, Sinnoh experimental, Blue Studio, site, Windows, Android/JoiPlay e saves**. ID de mapa, switch, variável, trainer, encounter e música deve ser isolado por região e validado.
9. **Nunca sobrepor a pasta Data de outra fonte ao jogo principal**. Importar com inventário de IDs, backups, conversão, transação e rollback; nenhuma geometria inventada.
10. Validação significa **teste no Game.exe real e no Android** com entrada/saída, combate, derrotas, eventos, save/reload, portais e ausência de regressões. Testes de fixture não são certificado de gameplay.
11. Música de cura, BGM de locais, batalhas especiais e fanfarras devem ser cadastradas individualmente no BlueMusic e testadas; este documento **não fornece OSTs nem licença de redistribuição**.
12. Não copiar o roteiro integral ou diálogos proprietários de Platinum. Redigir diálogos autorais coerentes com as cenas e manter o original apenas como referência externa.

---

## 1. Panorama de Sinnoh em Pokémon Platinum

**Protagonista:** Lucas ou Dawn, conforme a escolha inicial; **rival:** Barry; **professor:** Rowan; **assistente do professor:** Dawn/Lucas; **campeã:** Cynthia. **Antagonistas:** Team Galactic, comandada por Cyrus, com Mars, Jupiter, Saturn e o cientista Charon. **Aliado da investigação:** Looker.

**Iniciais:** Turtwig (Planta), Chimchar (Fogo), Piplup (Água). Barry escolhe a opção que tem vantagem de tipo contra a opção do jogador: Turtwig → Chimchar; Chimchar → Piplup; Piplup → Turtwig. O assistente fica com a terceira espécie.

### 1.1 Caminho crítico resumido

Twinleaf → Route 201 / Lake Verity → Sandgem → Route 202 → Jubilife → Route 203 / Oreburgh Gate → Oreburgh **[1]** → Jubilife → Floaroma / Valley Windworks → Eterna Forest → Eterna **[2]** → Galactic Eterna HQ → Cycling Road / Route 207 / Mt. Coronet → Hearthome **[3]** → Solaceon → Route 215 → Veilstone **[4]** → Route 214 / Valor Lakefront → Pastoria **[5]** → Route 210 / Celestic → Route 218 / Canalave **[6]** → Iron Island → Biblioteca de Canalave → Lake Valor / Lake Verity → Mt. Coronet / Snowpoint **[7]** → Lake Acuity → Galactic HQ → Spear Pillar → Distortion World / Giratina → Route 222 / Sunyshore **[8]** → Route 223 / Victory Road → Elite Four / Cynthia → Hall of Fame.

**Observação:** algumas áreas são visitadas antes e depois do desbloqueio de um HM. O percurso acima agrupa **a ordem dos fatos obrigatórios de Platinum**, não é ordem absoluta de todos os itens opcionais.

### 1.2 Distinções importantes entre Platinum e Diamond/Pearl

- Fantina é a **terceira** líder de ginásio; Maylene quarta e Crasher Wake quinto.
- A história principal envolve **Giratina e o Distortion World** após a invocação de Dialga/Palkia.
- **Defog** é obtido nas Solaceon Ruins; **Strength** está associado a Iron Island, em vez da Lost Tower.
- O esconderijo Galactic, puzzles dos ginásios, elenco de algumas equipes e encontros da Pokédex apresentam diferenças.
- Wayward Cave tem entrada oculta para Gible acessível mais cedo do que em Diamond/Pearl; o mesmo vale para diversos encontros e áreas expandidas.
- Battle Frontier tem cinco instalações; Battle Zone também reúne Survival Area, Resort Area e Stark Mountain.
- A documentação e o piloto do Blue devem usar **Platinum como cânone central**, sem colar eventos conflitantes de Diamond/Pearl.

---

## 2. Ginásios de Sinnoh — ordem, recompensas e equipes históricas

| Badge | Cidade | Líder / foco | Equipe de Platinum (níveis históricos) | Puzzle | HM liberado / consequência |
|---|---|---|---|---|---|
| 1 — Coal Badge | Oreburgh | Roark — Pedra | Geodude 12, Onix 12, Cranidos 14 | Líder localizado primeiro na mina | Rock Smash fora de batalha |
| 2 — Forest Badge | Eterna | Gardenia — Planta | Turtwig 20, Cherrim 20, Roserade 22 | Relógio/ponte e obstáculos | Cut fora de batalha |
| 3 — Relic Badge | Hearthome | Fantina — Fantasma | Duskull 24, Haunter 24, Mismagius 26 | Símbolos corretos, salas escuras e luzes | Progressão regional e acesso de campo conforme tabela HM |
| 4 — Cobble Badge | Veilstone | Maylene — Lutador | Meditite 28, Machoke 29, Lucario 32 | Sacos de pancada e barreiras | Fly fora de batalha |
| 5 — Fen Badge | Pastoria | Crasher Wake — Água | Gyarados 33, Quagsire 34, Floatzel 37 | Mudar níveis de água | Avanço do arco Galactic; liberação de campo conforme Platinum |
| 6 — Mine Badge | Canalave | Byron — Aço | Magneton 37, Steelix 38, Bastiodon 41 | Plataformas +/− | Strength fora de batalha |
| 7 — Icicle Badge | Snowpoint | Candice — Gelo | Sneasel 40, Piloswine 40, Abomasnow 42, Froslass 44 | Gelo deslizante e bolas de neve | Rock Climb fora de batalha |
| 8 — Beacon Badge | Sunyshore | Volkner — Elétrico | Jolteon 46, Raichu 46, Luxray 48, Electivire 50 | Engrenagens e interruptores | Waterfall após receber HM de Jasmine |

**TMs históricos de líder:** Roark — Stealth Rock (TM76); Gardenia — Grass Knot (TM86); Fantina — Shadow Claw (TM65); Maylene — Drain Punch (TM60); Crasher Wake — Brine (TM55); Byron — Flash Cannon (TM91); Candice — Avalanche (TM72); Volkner — Charge Beam (TM57). **VALIDAR** IDs exatos dos movimentos no PBS do Blue antes de oferecer recompensas equivalentes.

**Notas de combate:** Geodude/Onix/Cranidos têm respostas de Água/Planta/Lutador; a Roserade de Gardenia exige cuidado com status; Fantina neutraliza Normal e Lutador com vários integrantes; Lucario de Maylene exige cobertura; Quagsire do Wake é imune a Elétrico; o ginásio de Aço incentiva Fogo/Terra/Lutador; Candice usa Froslass; Electivire é o destaque de Volkner. **Não transferir estratégias antigas de tipos de Geração IV sem revisar a tabela de tipos vigente no Blue.**

### 2.1 HMs de Sinnoh: obtenção e uso

| Técnica histórica | Como obter em Platinum | Uso fora de batalha e dependências |
|---|---|---|
| HM01 Cut | Cynthia, próximo ao ginásio de Eterna | Forest Badge (Gardenia) |
| HM02 Fly | Depósito Galactic de Veilstone após o roubo da Pokédex de Dawn/Lucas | Cobble Badge (Maylene) |
| HM03 Surf | Avó de Cynthia, após eventos das ruínas de Celestic | Relic Badge (Fantina); exige obter HM e insígnia |
| HM04 Strength | Riley, em Iron Island | Mine Badge (Byron) |
| HM05 Defog | Solaceon Ruins | Relic Badge (Fantina) |
| HM06 Rock Smash | Oreburgh Gate, antes de Roark | Coal Badge (Roark) |
| HM07 Waterfall | Jasmine na praia de Sunyshore após Volkner | Beacon Badge (Volkner) |
| HM08 Rock Climb | Route 217, próximo a uma cabana | Icicle Badge (Candice) |

**BLUE — REQUISITO:** conferir permissões de HMs reais da engine antes de ligar switches; não sobrescrever a lógica global com estes nomes. A regra do projeto pede HM desbloqueado por **badge da região correspondente**, não por badges de outras regiões.

---

## 3. Campanha completa — 43 marcos com eventos e desbloqueios

Cada marco abaixo é um **roteiro de implementação/teste**: cena principal, caminho, consequências e pontos que não podem ser ignorados. Os nomes de flags na seção 14 são simbólicos; não são MapIDs nem switches RPG Maker reais.

### S01 — Twinleaf: quarto do jogador e primeiro encontro com Barry

- **Local:** quarto do protagonista, andar inferior da casa, casa de Barry e caminho para Route 201.
- **PLATINUM:** abertura com o programa na televisão, Barry procura o protagonista, a mãe indica a casa do rival, e ambos tentam seguir para a área norte.
- **BLUE:** spawn deve ocorrer **dentro do quarto**, não na rua. Barry deve ter trigger de entrada e saída, deslocamento e retorno sem repetir diálogos.
- **Condição de saída:** conversa com a mãe e encontro obrigatório com Barry, sem conceder Pokémon antes do evento correto.

### S02 — Route 201: Rowan, maleta e três Poké Bolas

- **Local:** entrada da Route 201, perto do caminho para Lake Verity.
- **PLATINUM:** Rowan impede a entrada no mato sem Pokémon; o assistente traz a maleta e o jogador escolhe Turtwig/Chimchar/Piplup; Barry escolhe o Pokémon com vantagem e desafia para a primeira batalha.
- **BLUE:** **três Poké Bolas físicas** interativas, como no template de [Twinleaf](SINNOH_FASE_03_TWINLEAF_EVENTOS_PILOTO.md), não um menu genérico do professor. Impedir segunda escolha, manter rollback se a entrega falhar e registrar a espécie correta de Barry.
- **Saída:** primeira batalha de Barry concluída; em seguida, retorno ao lar e obtenção do mecanismo de corrida/Running Shoes, quando aplicável.

### S03 — Lake Verity: primeira manifestação do mistério

- **Local:** desvio a oeste da Route 201.
- **PLATINUM:** Barry acompanha o jogador até o lago; Cyrus é encontrado observando a área; o lago sugere a presença de um Pokémon lendário, mas não há captura.
- **BLUE:** cutscene curta com Cyrus e gatilho único; acesso ao lago permitido, captura do guardião bloqueada pelo arco principal.

### S04 — Sandgem: laboratório, Pokédex e primeira missão de entrega

- **Local:** Route 201 leste → Sandgem; laboratório de Rowan; Twinleaf.
- **PLATINUM:** Dawn/Lucas conduz até Rowan; Pokédex obtida; TM27 Return; assistência mostra serviços da cidade; retorno à mãe para Journal e Parcel destinado a Barry.
- **BLUE:** marcar separadamente recebimento de starter, Pokédex, pacote e tutorias; evitar repetição do TM ou dos itens em saves recarregados.
- **Saída:** entrega do Parcel ainda pendente; Route 202 aberta após tutorial.

### S05 — Route 202: tutorial de captura

- **PLATINUM:** Dawn/Lucas demonstra captura, oferece cinco Poké Balls e a rota contém três treinadores. Shinx, Starly e Bidoof são exemplos de encontros úteis da fase inicial.
- **BLUE:** tutorial pode usar seu sistema autoral, porém deve conceder o conjunto de captura uma única vez; validar encontros e luta sem travar no Android.
- **Saída:** passagem para Jubilife.

### S06 — Jubilife: Looker, Escola, Town Map e Pokétch

- **PLATINUM:** Looker se apresenta; Barry recebe o Parcel na Trainer School e fornece uma cópia do Town Map; um NPC promove busca de três cupons com palhaços para obter o Pokétch. Há Old Rod a oeste.
- **BLUE:** portais para escola, Centro, lojas e saídas precisam funcionar; a entrega do pacote deve ser persistente. Se a interface do Pokétch não for portada, registrar substituto funcional sem travar a história.
- **Opcional:** treinadores da escola, brinde Quick Claw, Route 204 norte e pequena exploração inicial.

### S07 — Route 203, Oreburgh Gate e primeiro HM

- **PLATINUM:** Barry chama para outra batalha no trecho leste de Jubilife; Oreburgh Gate contém o HM Rock Smash entregue por NPC; sem a primeira insígnia ainda não é possível remover todos os obstáculos.
- **BLUE:** trainer Barry versionado por inicial e progressão, não um time fixo; manter gate da técnica fora de batalha.
- **Saída:** chegar a Oreburgh sem pular a batalha obrigatória do rival.

### S08 — Oreburgh Mine e primeiro ginásio

- **PLATINUM:** Roark está na mina, mostra Rock Smash e retorna ao ginásio; somente então é possível concluir o desafio de Pedra.
- **BLUE:** Roark deve desaparecer da mina e reaparecer no ginásio após a conversa; receber Coal Badge apenas após vitória válida.
- **Recompensas:** Coal Badge, TM do líder e desbloqueio de Rock Smash; impedir farm de badge/recompensa por rematch.

### S09 — Retorno a Jubilife: primeira dupla Galactic

- **PLATINUM:** após Roark, o grupo Galactic aborda Rowan e Dawn/Lucas próximo da entrada de Route 204; ocorre batalha em dupla. Looker continua investigação.
- **BLUE:** usar batalha dupla real do Blue, com aliado correto e retorno dos NPCs à posição pós-cena.
- **Saída:** Route 204 norte e Ravaged Path liberados.

### S10 — Floaroma e Route 205 bloqueada

- **PLATINUM:** o povoado oferece atividades de berries, acessórios e regador; a ponte de Route 205 fica ocupada pela Galactic. A filha de um funcionário pede ajuda.
- **BLUE:** o bloqueio deve ficar **na ponte da Route 205**, com desvio navegável para Valley Windworks; usar flag do incidente de Mars.
- **Opcional:** Floaroma Meadow, Honey, árvores de encontro, Pluck.

### S11 — Valley Windworks e Commander Mars

- **PLATINUM:** derrotar guarda no moinho, obter Works Key após vencer recrutas em Floaroma Meadow, entrar no prédio e derrotar Mars; o pai da criança é libertado.
- **Time histórico de Mars:** Zubat 15, Purugly 17.
- **BLUE:** portas precisam exigir a chave, sem rota alternativa que contorne o evento; a ponte é liberada somente depois da vitória em Mars.
- **Evento periódico:** Drifloon aparece às sextas após a missão, sujeito ao calendário real do Blue.

### S12 — Route 205 e Eterna Forest com Cheryl

- **PLATINUM:** cura intermediária na rota; Cheryl acompanha durante o trajeto florestal, com Chansey, transformando encontros e treinadores em batalhas duplas com cura após lutas.
- **BLUE:** implementar seguidora temporária, batalhas duplas e despedida na saída; validar que companheiro não entra em portais incompatíveis e não duplica eventos.
- **Opcional:** Old Chateau somente quando o acesso por Cut estiver liberado.

### S13 — Eterna: Gardenia e segundo badge

- **PLATINUM:** visita à cidade, encontro com Cynthia e HM Cut, puzzle de relógio no ginásio; batalha contra Gardenia.
- **BLUE:** preservar ordem NPC → HM → luta → badge → liberar árvores cortáveis; desbloqueio do prédio Galactic só após usar Cut.
- **Recompensas:** Forest Badge e Grass Knot.

### S14 — Galactic Eterna Building, Jupiter, bicicleta e Togepi

- **PLATINUM:** investigar prédio no norte de Eterna; Looker aparece disfarçado; derrotar Jupiter (Zubat 21, Skuntank 23); libertar o dono da loja de bicicletas.
- **Consequências:** bicicleta recebida em Eterna; Cynthia oferece ovo de Togepi se houver vaga na equipe.
- **BLUE:** registrar ovo pendente se party cheia sem perdê-lo; rota ciclística só é útil após bicicleta; evitar conceder bicicleta em duplicidade.

### S15 — Cycling Road, Wayward Cave e Route 207

- **PLATINUM:** Route 206 tem ciclistas, Gligar e entrada de Wayward Cave; entrada oculta sob a ponte dá acesso a Gible. Mira, na parte principal da caverna, acompanha com Kadabra.
- **BLUE:** Wayward Cave e Mira são **opcionais**, mas mapear ambas as entradas; bicicleta deve respeitar rampas, inclinações e restrições de terreno.
- **Conquista:** Dawn/Lucas oferece VS Seeker e Dowsing Machine na aproximação ao Mt. Coronet.

### S16 — Mt. Coronet sul, Route 208 e Hearthome

- **PLATINUM:** primeiro encontro relevante com Cyrus dentro de Mt. Coronet; Route 208 contém Berry Master; Hearthome contém Contest Hall, Amity Square e serviços.
- **BLUE:** o Monte Coronet tem múltiplos acessos que devem usar o mesmo mapa lógico e bloqueios de HM; não permitir travessias prematuras.
- **Opcional:** Odd Keystone, Bebe e Eevee, atividades de concurso.

### S17 — Hearthome: Fantina, terceiro ginásio

- **PLATINUM:** conversar com Fantina no Contest Hall antes de ela voltar ao ginásio; puzzle escuro de símbolos; equipe Duskull, Haunter e Mismagius.
- **BLUE:** não depender do quinto badge como em Diamond/Pearl; registrar Relic Badge e habilitar o trecho leste após a cena.
- **Saída:** Barry desafia na saída leste; Route 209 acessível.

### S18 — Route 209, Lost Tower e Solaceon

- **PLATINUM:** pescador fornece Good Rod; Lost Tower é área opcional, com itens e batalhas; Solaceon contém Day Care, serviços, selos, missões diárias e Ruins com Unown.
- **Importante:** em **Platinum, Strength NÃO é prêmio da Lost Tower**; será obtido na fase Iron Island. Defog fica nas Solaceon Ruins.
- **BLUE:** ovo/breeding, se disponível, deve preservar o serviço global; não ativar HM errado herdado de Diamond/Pearl.

### S19 — Route 210 sul, Route 215 e chegada a Veilstone

- **PLATINUM:** Route 210 possui grama alta e Psyduck bloqueando caminho norte; o trecho para Veilstone prossegue pela Route 215, sob chuva.
- **BLUE:** bloquear apenas o ramo que vai a Celestic, sem fechar a saída de Route 215; permitir retornar mais tarde com SecretPotion.
- **Opcional:** Roost, treinadores, Scyther, coleta de berries e Honey.

### S20 — Veilstone: Maylene, quarta insígnia

- **PLATINUM:** entrar no ginásio de Lutador, acionar sacos de pancada para abrir o caminho, enfrentar Maylene.
- **Recompensas:** Cobble Badge, Drain Punch e permissão de Fly.
- **BLUE:** implementar puzzle espacial e impedir que a porta da líder seja alcançada sem completar a sequência.

### S21 — Recuperar Pokédex de Dawn/Lucas e Fly

- **PLATINUM:** Galactic toma Pokédex do assistente, e uma batalha em dupla perto de Veilstone resolve o roubo. Looker leva ao depósito e o HM Fly pode ser obtido ali.
- **BLUE:** validar o roubo/devolução como evento de estado e não remover realmente a Pokédex do sistema global sem necessidade. O item Fly deve ser persistente e não duplicável.

### S22 — Route 214, Valor Lakefront e Route 213

- **PLATINUM:** caminho sul de Veilstone conduz a Valor Lakefront e ao trecho costeiro de Route 213, com hospedagem, treinadores, itens e Shellos de aparência diferente.
- **BLUE:** manter saídas coerentes para Pastoria e Lake Valor, cujo acesso interno é parcialmente bloqueado até os eventos da Galactic.

### S23 — Pastoria: Barry, Crasher Wake e quinta insígnia

- **PLATINUM:** Barry trava a aproximação ao ginásio para uma batalha; puzzle interno altera a altura da água; Wake usa Gyarados, Quagsire e Floatzel.
- **Recompensas:** Fen Badge, Brine; incidente no Great Marsh logo após sair do ginásio.
- **BLUE:** puzzle e batalhas independentes, mas todos os switches do ginásio são locais; não duplicar a batalha com Barry quando recarregar.

### S24 — Explosão do Great Marsh, perseguição Galactic e SecretPotion

- **PLATINUM:** após Wake, recruta foge de Pastoria por Route 213 e Valor Lakefront; o jogador o alcança, batalha e recebe SecretPotion de Cynthia para os Psyduck da Route 210.
- **BLUE:** a perseguição não deve depender apenas de conversas manuais não sinalizadas; ativar NPCs por segmentos sucessivos da rota, com bloqueio de diálogo fora da ordem.
- **Saída:** retorno à Route 210 para desbloquear o acesso norte.

### S25 — Route 210 norte, Defog e Celestic

- **PLATINUM:** curar Psyduck, receber Old Charm de Cynthia, atravessar área de neblina (Defog das Solaceon Ruins) e chegar a Celestic.
- **BLUE:** conceder HM por descoberta real das ruínas, usar efeito de neblina/visibilidade se suportado e manter alternativa visual segura no Android.
- **Saída:** evento de Cyrus em Celestic.

### S26 — Celestic Ruins e primeiro confronto direto com Cyrus

- **PLATINUM:** derrotar recruta em Celestic, entregar Old Charm à avó de Cynthia; investigar mural com Uxie, Mesprit e Azelf; lutar com Cyrus (Murkrow 36, Sneasel 34, Golbat 34); receber Surf.
- **BLUE:** Old Charm e pintura são objetos de evento, não itens duplicáveis; registrar Cyrus derrotado separadamente dos outros encontros.
- **Saída:** pedido para investigar Canalave e biblioteca.

### S27 — Exploração opcional com Surf

- **PLATINUM:** Surf abre passagens nas Routes 204, 205, 208, 210, 219–221, Valley Windworks, Oreburgh Gate, Ravaged Path, Mt. Coronet e acesso a Fuego Ironworks.
- **BLUE:** listar e testar todos os tiles de Surf, conexões de água e retorno à margem; esses itens opcionais não são chaves para a história principal.
- **Atenção:** Pal Park exige outra condição; acessar sua rota não significa desbloquear transferência de Pokémon.

### S28 — Route 218 e Canalave: Barry e sexto ginásio

- **PLATINUM:** surfar a oeste de Jubilife pela Route 218; em Canalave ocorre batalha com Barry na ponte; Byron usa Magneton, Steelix e Bastiodon.
- **BLUE:** registrar batalha da ponte com equipe escalável e separar o badge Mine do evento da biblioteca.
- **Recompensas:** Mine Badge e Flash Cannon.

### S29 — Iron Island: Riley, Strength e ovo de Riolu

- **PLATINUM:** barco de Canalave leva a Iron Island; Riley entrega Strength na chegada e acompanha o jogador nas galerias, usando Lucario; batalha contra Galactic; recompensa de ovo de Riolu após ajudar o parceiro.
- **BLUE:** barco e ilha precisam funcionar como transporte local bidirecional; parceiro remove-se do grupo ao concluir; ovo pode ficar aguardando vaga.
- **Saída:** retornar a Canalave para o encontro na biblioteca.

### S30 — Biblioteca de Canalave e crise dos três lagos

- **PLATINUM:** Rowan convoca protagonista, Barry e assistente para investigar o trio dos lagos; explosão no Lake Valor altera toda a fase narrativa.
- **BLUE:** disparar crise apenas uma vez após Mine Badge e avanço da biblioteca. A seca do lago e os NPCs Galactic precisam usar um estado global de história de Sinnoh persistido em save.

### S31 — Lake Valor e Saturn

- **PLATINUM:** Lake Valor perde a água e está ocupado por recrutas; Saturn mantém Azelf sob controle e desafia o protagonista (Golbat 38, Toxicroak 40, Bronzor 38).
- **BLUE:** a versão seca e a inundada do lago devem ter transição/estado reversível sem perder NPCs ou prender o jogador.
- **Saída:** Rowan e assistente requerem ajuda no Lake Verity.

### S32 — Lake Verity e Mars

- **PLATINUM:** recrutas atacam a área; Dawn/Lucas participa do incidente, e Mars reaparece; o lago está relacionado a Mesprit.
- **BLUE:** marcar liberação do lago, diálogo de Rowan e derrota de Mars como eventos únicos, sem desbloquear captura do lendário ainda.

### S33 — Mt. Coronet norte, Routes 216/217 e HM Rock Climb

- **PLATINUM:** subida nevada por Route 216/217, cabana de repouso, visibilidade reduzida e HM Rock Climb na Route 217; Lake Acuity é visto antes de estar acessível.
- **BLUE:** travessia em neve, interiores, HM e recuperação da cabana devem funcionar mesmo sem animação exata da versão DS; Rock Climb permanece bloqueado até Candice.
- **Saída:** Snowpoint.

### S34 — Snowpoint: Candice e sétima insígnia

- **PLATINUM:** puzzle com blocos/bolas de neve e piso escorregadio; Candice usa Sneasel, Piloswine, Abomasnow e Froslass.
- **BLUE:** puzzle precisa de reset se o jogador sair/reentrar; após vitória, conceder Icicle Badge e Rock Climb no mapa.

### S35 — Lake Acuity: Barry, Jupiter e retorno a Veilstone

- **PLATINUM:** subir até o lago e encontrar Barry após seu confronto com Jupiter; ela anuncia o plano final da Galactic.
- **BLUE:** Barry não inicia batalha nesta cena; a saída para o quartel Galactic aparece como próximo objetivo.

### S36 — Veilstone Galactic Warehouse e Headquarters

- **PLATINUM:** investigar guarda do quartel, conversar com Looker, obter Storage Key, atravessar o depósito por escadas e teletransportadores e conseguir Galactic Key.
- **BLUE:** portas e chaves devem ser verificadas por evento, evitando teletransportadores sem volta; a missão não pode iniciar antes de Lake Acuity.
- **Itens históricos:** diversos TMs incluindo Sludge Bomb (TM36); tratar distribuição exata como **VALIDAR**.

### S37 — Confrontos com Cyrus, Saturn e liberação dos guardiões

- **PLATINUM:** encontro no auditório da Galactic, batalha contra Cyrus (Sneasel 44, Honchkrow 46, Crobat 44), recebimento da Master Ball; confrontar Saturn no laboratório e libertar o trio.
- **BLUE:** Master Ball entregável uma vez; guardar derrotas de Cyrus e Saturn em flags distintas; a liberação do trio só ocorre após evento correto da cápsula.
- **Saída:** acesso a Spear Pillar no Mt. Coronet.

### S38 — Mt. Coronet e Spear Pillar: Mars + Jupiter

- **PLATINUM:** montanha com trechos internos/externos, Rock Climb e bloqueios Galactic. No topo, Barry auxilia em batalha dupla contra Mars e Jupiter.
- **BLUE:** preservar combate 2x2 e equipe de Barry dependente do inicial, escalonada; impedir entrada no Distortion World sem vitória da dupla e cutscene de Cyrus.
- **Importante:** após o confronto, Cyrus convoca Dialga e Palkia; a interferência de Giratina abre o portal do Distortion World.

### S39 — Distortion World: cenário espacial e Cyrus final

- **PLATINUM:** Cynthia acompanha parte da travessia por plataformas móveis, gravidade alterada, caminhos horizontais/verticais e puzzle relacionado a Uxie, Mesprit e Azelf; confrontar Cyrus pela última vez.
- **Equipe histórica do Cyrus final:** Houndoom 45, Honchkrow 47, Gyarados 46, Weavile 48, Crobat 46.
- **BLUE:** cenário exige prova visual e de passabilidade, câmera, teleporte, plataformas e retorno; se a engine não reproduzir efeito 3D, usar **representação autoral 2D testada**, nunca fingir que a importação dos mapas já o implementou.

### S40 — Giratina e Sendoff Spring

- **PLATINUM:** após a derrota de Cyrus, enfrentar/capturar Giratina em sua forma Origin no Distortion World (nível histórico 47); portal retorna a Sendoff Spring/Route 214.
- **BLUE:** permitir capturar ou derrotar sem travar roteiro; usar flags de batalha/conclusão separadas da autorização de Giratina na party por badges locais.
- **Saída:** visitar Rowan em Sandgem para fechar o arco central.

### S41 — Route 222 e Sunyshore: Volkner, oitava insígnia

- **PLATINUM:** após o retorno a Sandgem, abrir Route 222; Flint recebe o jogador em Sunyshore; Volkner está no farol e precisa ser chamado ao ginásio; engrenagens e botões compõem o puzzle.
- **Equipe:** Jolteon, Raichu, Luxray, Electivire; após vitória, Beacon Badge.
- **BLUE:** farol e ginásio com flags próprias; depois do badge Jasmine fornece Waterfall na praia, sem entrega antecipada.

### S42 — Route 223, Victory Road e Barry pré-Liga

- **PLATINUM:** surfar pela Route 223, subir cachoeira, atravessar Victory Road com Rock Climb, Strength, Rock Smash, Surf e Waterfall; Barry desafia na antessala da Liga.
- **BLUE:** último rival com equipe evoluída por level cap e versão do inicial; verificar uso real dos cinco HMs, salvamento nas cavernas e todos os warps.
- **Saída:** portão da Elite Four aberto após a batalha de Barry e condições locais da Liga.

### S43 — Elite Four, Cynthia e Hall of Fame

- **PLATINUM:** vencer Aaron → Bertha → Flint → Lucian → Cynthia, assistir à cerimônia e créditos.
- **BLUE:** registrar **SINNOH_LEAGUE_CLEARED** uma única vez após Hall of Fame **confirmado pelo motor**, atualizar contador global das Ligas, painel regional e desbloqueios de viagem do circuito. Não antecipar progresso durante a batalha com Cynthia.
- **PÓS-LIGA:** retorno à casa do protagonista e habilitação gradual de National Dex, Battle Zone e atividades extras conforme sua condição própria.

---

## 4. Matriz de eventos da Team Galactic

| Arco | Vilão(s) | Local | Precisa de | Efeito depois da vitória |
|---|---|---|---|---|
| Primeiro confronto | Recrutas | Jubilife / Route 204 | Coal Badge | Ida para Floaroma |
| Works Key | Recrutas | Floaroma Meadow | Guarda de Windworks derrotado | Abrir Valley Windworks |
| Moinho | Mars | Valley Windworks | Works Key | Libertar funcionário; Route 205 aberta |
| Prédio Eterna | Jupiter | Galactic Eterna HQ | Forest Badge + Cut | Libertar dono da bicicleta |
| Pokédex roubada | Recrutas | Veilstone | Maylene | Fly no depósito |
| Explosão Great Marsh | Recruta | Pastoria → Valor Lakefront | Fen Badge | Receber SecretPotion |
| Ruínas ancestrais | Recruta e Cyrus | Celestic | Psyduck curados + Old Charm | Surf e destino Canalave |
| Lake Valor | Saturn | Lake Valor | Reunião em Canalave | Impedir captura de Azelf |
| Lake Verity | Mars | Lake Verity | Evento dos lagos | Resgate de assistente/mesprit |
| Lake Acuity | Jupiter (cena com Barry) | Lake Acuity | Candice + Rock Climb | Direção ao quartel |
| Quartel | Cyrus e Saturn | Veilstone HQ | Storage Key e Galactic Key | Master Ball e trio libertado |
| Spear Pillar | Mars e Jupiter | Mt. Coronet | HQ concluído | Dupla com Barry; portal |
| Mundo paralelo | Cyrus final | Distortion World | Portal aberto | Liberar batalha Giratina |
| Stark Mountain | Charon e Looker | Battle Zone / Stark Mountain | Pós-Liga e quests de Buck | Encerrar remanescente Galactic, abrir Heatran |

**Implementação:** chaves, diálogos, cutscenes, estado dos NPCs e resultados de combate pertencem ao namespace **Sinnoh**; não usar variáveis globais compartilhadas com Equipe Rocket de Kanto nem com outros antagonistas.

---

## 5. Barry, aliados e variações de equipe

### 5.1 Barry em todas as etapas importantes

| Encontro | Gatilho/local | Mudança de equipe em Platinum |
|---|---|---|
| Rival 01 | Route 201, após escolher starter | Inicial com vantagem, primeira batalha |
| Rival 02 | Route 203 | Starly + inicial |
| Rival 03 | Saída de Hearthome / Route 209 | Staravia + 2 coberturas + inicial evoluído |
| Rival 04 | Entrada do ginásio Pastoria | Staravia + coberturas + evolução intermediária |
| Rival 05 | Ponte de Canalave | Staraptor, Heracross + coberturas + inicial final |
| Aliado 01 | Spear Pillar | Participa da dupla Mars/Jupiter |
| Rival 06 | Antessala da Liga | Equipe completa com Snorlax, Heracross e inicial final |
| Aliado 02 | Fight Area | Ajuda contra Flint/Volkner |
| Rival pós-jogo | Survival Area / Battleground | Revanches nos fins de semana, com estágios superiores |

**Núcleo variável da equipe do rival (referência de Platinum):**

- **Jogador escolhe Turtwig:** Barry usa a família Chimchar → Monferno → Infernape; coberturas principais incluem Roselia → Roserade e Buizel → Floatzel.
- **Jogador escolhe Chimchar:** Barry usa a família Piplup → Prinplup → Empoleon; coberturas incluem Roselia → Roserade e Ponyta → Rapidash.
- **Jogador escolhe Piplup:** Barry usa a família Turtwig → Grotle → Torterra; coberturas incluem Buizel → Floatzel e Ponyta → Rapidash.
- Em fases avançadas surgem Staraptor, Heracross e Snorlax. **Níveis e estágio evolutivo devem acompanhar o level cap do Blue**, sem forçar níveis históricos.

**BLUE:** o arquivo [SINNOH_FASE_03_BARRY_PBS.md](SINNOH_FASE_03_BARRY_PBS.md) contém o contrato do piloto inicial e seus testes. **Não reutilizar a mesma versão PBS para todos os encontros**: criar IDs simbólicos por confronto e variação, validar dados e impedir batalha se o PBS real ainda não estiver pronto.

### 5.2 Parceiros temporários

| Parceiro | Local | Pokémon histórico | Uso narrativo |
|---|---|---|---|
| Cheryl | Eterna Forest | Chansey | Travessia e cura entre duplas |
| Mira | Wayward Cave | Kadabra | Ajudar a encontrar saída da caverna |
| Riley | Iron Island | Lucario | Enfrentar recrutas e obter ovo Riolu |
| Marley | trecho pós-Liga da Victory Road | Arcanine | Acesso ao caminho da Route 224 |
| Buck | Stark Mountain | Claydol | Exploração e história da Magma Stone |
| Barry | Spear Pillar / Fight Area | Time variável | Apoio em dupla e cenas de história |

**BLUE:** entrada/saída de acompanhantes, cura, ações de Surf/Rock Climb, batalha dupla, derrota do jogador e teleporte devem ser testados independentemente. Nenhum parceiro pode ficar preso na party ou no save de outra região.

---

## 6. Locais, NPCs e encontros notáveis

### 6.1 Cidades, serviços e pontos de interesse

| Local | Conteúdo característico | Papel no Blue |
|---|---|---|
| Twinleaf Town | Casas do jogador e Barry; mãe; início; acesso Lake Verity | Spawn, retorno, NPC de viagem regional conforme circuito |
| Sandgem Town | Laboratório Rowan, assistente, Pokédex, rotas costeiras | Centro da narrativa / National Dex |
| Jubilife City | Escola, Pokétch, Looker, TV, Town Map, Old Rod | Tutoriais, utilidades, primeiro incidente Galactic |
| Oreburgh City | Mina, museu, primeiro ginásio | Rock Smash e Coal Badge |
| Floaroma Town | Berries, mel, Floaroma Meadow | Desbloqueio Works Key |
| Eterna City | Ginásio, prédio Galactic, bicicleta, passagem para Old Chateau | Cut, Gardenia, Jupiter, Togepi |
| Hearthome City | Contest Hall, Fantina, Amity Square, Bebe, Eevee | Terceiro badge, eventos sociais |
| Solaceon Town | Day Care, Ruins, Lost Tower próxima, Seal Case | Defog, Unown, reprodução |
| Veilstone City | Departamento de lojas, ginásio, Galactic Warehouse/HQ, Porygon | Maylene, Fly, enredo central |
| Pastoria City | Great Marsh, Move Relearner, ginásio | Crasher Wake, explosão e perseguição |
| Celestic Town | Avó de Cynthia, mural do trio, ruínas | Cyrus, Surf e mitologia |
| Canalave City | Biblioteca, porto, Move Deleter, ginásio | Byron, Iron Island, crise dos lagos |
| Snowpoint City | Ginásio, templo, acesso Lake Acuity e barco | Candice, Snowpoint Temple, Battle Zone |
| Sunyshore City | Farol, praia, Jasmine, ginásio, selos | Volkner, Waterfall |
| Pokémon League | Victory Road, Centro, Elite Four e Hall of Fame | Fechamento da Liga |
| Fight Area | Porto de Battle Zone, acesso Battle Frontier | PÓS-LIGA |
| Survival Area | Battleground, rematches, acesso Stark Mountain | PÓS-LIGA |
| Resort Area | Villa, atividades, Pokémon Ribbon Society | PÓS-LIGA |

### 6.2 Rotas e locais de encontro (amostra para o catálogo Habitat Dex)

| Área | Exemplos de espécies/atividades citadas em Platinum | Nota |
|---|---|---|
| Routes 201–203 | Starly, Bidoof, Shinx, encontros iniciais | Encounters por horário/método precisam ser auditados |
| Oreburgh Mine / Gate | Geodude, Onix, Rock Smash, TM Flash | Portais e pisos múltiplos |
| Valley Windworks | Shellos, Buizel, Pachirisu, Drifloon de sexta | Evento semanal separado |
| Eterna Forest | Buneary, Gastly e Pokémon dependentes de horário | Companheira Cheryl |
| Route 206 / Wayward Cave | Gligar e Gible na entrada escondida | Não substituir Wayward pelo Cycling Road |
| Mt. Coronet | Clefairy, Nosepass, caverna/montanha/gelo | Múltiplos níveis e acessos |
| Route 208 / 209 | Ralts, Bibarel, itens, Odd Keystone | Good Rod disponível na 209 |
| Route 210 / 215 | Scyther, Swablu; neblina em 210 norte | Psyduck bloqueando corredor norte |
| Route 212 | Chuva, lama, Quagsire | Pokémon Mansion e Trophy Garden |
| Route 213 / Great Marsh | Shellos leste, Wingull, Chatot; Wooper, Yanma, Skorupi | Grande área opcional |
| Routes 216–217 | Snover, Snorunt, Sneasel, Swinub | Neve, Rock Climb |
| Route 222 | Electabuzz, Magnemite/Magneton, Pelipper | Acesso após Distortion World |
| Route 223 / Victory Road | Pokémon de água; Onix/Steelix | Caminho da Liga |
| Route 224 | Acesso pós-Liga por Victory Road | White Rock / evento Shaymin |
| Routes 225–230 | Pokémon mais fortes; areia em 228 | Battle Zone |
| Stark Mountain | Encontros de área vulcânica; Heatran fixo | Quest de Buck/Charon |
| Old Chateau | Gastly/Haunter e Rotom conforme evento | Exploração opcional |

**VALIDAR:** espécies, percentuais, horários, pesca, surfe, métodos especiais e níveis **não podem ser inferidos somente do nome da rota**. Exportar dados reais dos encontros do Blue depois da instalação e cruzar com a referência Platinum; evitar encontros inventados. O balanceamento de espécie/evolução por cap é separado do peso de spawn.

### 6.3 Inventário funcional de itens e serviços

| Conteúdo | Local | Dependência |
|---|---|---|
| Town Map | Trainer School de Jubilife, após Parcel | Entrega da missão |
| Pokétch e aplicativos | Jubilife, Rotas, Solaceon e lojas | NPCs e tarefas específicas |
| Old Rod | Jubillife, passagem oeste | Falar com pescador |
| Good Rod | Route 209 | Falar com pescador |
| Super Rod | Fight Area | Pós-Liga |
| Quick Claw | Jubilife, NPC em casa | Opcional |
| Works Key | Floaroma Meadow | Recrutas derrotados |
| Honey | Floaroma Meadow / comerciantes | Acessa árvores específicas |
| Bicycle | Eterna Shop | Jupiter derrotada |
| Egg de Togepi | Cynthia em Eterna | Espaço na equipe |
| Odd Keystone | Route 208, alternativa por exploração | Opcional Spiritomb |
| VS Seeker / Dowsing Machine | Route 207, com Dawn/Lucas | Depois de Cycling Road |
| Eevee | Bebe em Hearthome | Espaço na party |
| Porygon | Residência em Veilstone | NPC de presente |
| Defog | Solaceon Ruins | Explorar caverna |
| SecretPotion | Cynthia em Valor Lakefront | Recruta perseguido |
| Old Charm | Cynthia após Psyduck | Entregar à avó em Celestic |
| Surf | Avó de Cynthia | Cyrus derrotado em Celestic |
| Move Relearner | Pastoria | Heart Scale |
| Move Deleter | Canalave | Serviço |
| Strength | Riley / Iron Island | Evento da ilha |
| Riolu Egg | Riley / Iron Island | Parceiro auxiliado e vaga |
| Rock Climb | Route 217 | Coleta no mapa |
| Storage/Galactic Key | Veilstone | Quartel após Acuity |
| Master Ball | Cyrus / quartel | Batalha da sede |
| Waterfall | Jasmine / Sunyshore | Oito badges de Sinnoh |
| National Dex | Rowan / Oak em Sandgem | Hall of Fame + 210 espécies vistas |
| Poké Radar | Rowan / Sandgem | National Dex |
| Lunar Wing | Fullmoon Island | Quest de Cresselia |
| Adamant Orb / Lustrous Orb | Mt. Coronet | Pós-arco central e Waterfall |
| Magma Stone | Stark Mountain | Quest de Buck/Charon |

**Observação:** alguns itens do cartucho foram alterados em gerações recentes ou no Blue. Criar uma tabela de equivalências antes de tentar forçar funcionalidades não existentes (Pokétch, Capture Park, Wi-Fi, transferências GBA, DS Download Play, etc.).

---

## 7. Atividades opcionais e eventos dependentes de horário

### 7.1 Explorações que devem ser opcionais

- **Old Chateau (Eterna Forest):** casarão, encontros de Fantasma, móveis e evento Rotom em horário noturno, após acesso com Cut. As formas de Rotom em Platinum dependem de Secret Key especial.
- **Wayward Cave:** rota subterrânea de Mira e acesso escondido com Gible sob Cycling Road; validar escuridão/Flash e colisões.
- **Lost Tower:** batalhas, itens e ambiente espiritual; não oferece Strength em Platinum.
- **Solaceon Ruins:** Unown, itens e HM Defog; múltiplos corredores.
- **Amity Square:** parque de caminhada com espécies elegíveis, itens colecionáveis e portais internos. Verificar elegibilidade do seguidor Pokémon no Blue.
- **Pokémon Mansion / Trophy Garden (Route 212):** livro com Manaphy, encontros de jardim e rotação de espécies pelo Sr. Backlot.
- **Great Marsh (Pastoria):** seis zonas, Safari Balls, passos limitados, binocular de observação e encontros raros.
- **Fuego Ironworks (Route 205):** fábrica acessível com Surf, caminhos por correias/tapetes, itens e encontros.
- **Iron Island:** também pode ser revisitada para itens/encounters após a história de Riley.
- **Pal Park (Routes 219–221):** referência histórica de transferência DS/GBA; no Blue substituir por recurso compatível ou marcar como não implementado, sem simular migração real.
- **Turnback Cave/Sendoff Spring:** acesso pós-Liga, orientação por salas e pilares, portal do Distortion World em Platinum.
- **Route 224:** missão de Marley na Victory Road e caminho até a White Rock.
- **Snowpoint Temple:** Regigigas e requisito da família Regi; pós-Liga.
- **Ribbon Syndicate / Villa de Resort Area:** compras, decoração e atividades econômicas opcionais.

### 7.2 Eventos por dia ou tempo

| Evento | Gatilho de Platinum | Regra no Blue |
|---|---|---|
| Drifloon em Valley Windworks | Sexta-feira, depois de Mars | Usar relógio/calendário real da engine; não criar duplicação por reload |
| Berries diárias | Floaroma, Route 208, Pastoria e NPCs afins | Uma recompensa por dia, por NPC |
| Honey Trees | Aplicar Honey, aguardar janela de tempo | Relógio persistente e espécie/área auditadas; sem evoluções artificiais |
| Spiritomb | Odd Keystone + interação original com Underground | Definir alternativa legal no Blue se Underground não existe |
| Rotom | Old Chateau à noite | Regras da edição Platinum, adaptar se relógio/forma forem diferentes |
| Batalhas em Pokémon Centers | NPCs móveis conforme dia da semana | Opcionais, equipes escaláveis, sem bloquear cura |
| Batalhas com Barry pós-jogo | Fins de semana em Survival Area | Progresso de revanche local, não confundir com pós-jogo global |
| Top Trainer Café | Treinadores em rotação diária | Escalonar com política regional |
| Encontros diários | Swarms com irmã de Dawn/Lucas | Só depois de National Dex |
| Trophy Garden | Pool adicional após conversa com Mr. Backlot | Preservar rotação por save |

**BLUE:** evitar que alterar o relógio do dispositivo corrompa a save; recompensas e encontros temporais devem ser reentrantes e seguros no Android.

---

## 8. Elite Four e Cynthia — equipes históricas de Platinum

| Ordem | Treinador | Especialidade | Pokémon históricos e níveis |
|---|---|---|---|
| 1 | Aaron | Inseto | Yanmega 49; Scizor 49; Vespiquen 50; Heracross 51; Drapion 53 |
| 2 | Bertha | Terra | Whiscash 50; Hippowdon 52; Golem 52; Gliscor 53; Rhyperior 55 |
| 3 | Flint | Fogo | Houndoom 52; Rapidash 53; Flareon 55; Infernape 55; Magmortar 57 |
| 4 | Lucian | Psíquico | Mr. Mime 53; Bronzong 54; Espeon 55; Alakazam 56; Gallade 59 |
| Campeã | Cynthia | Equipe mista | Spiritomb 58; Roserade 58; Milotic 58; Togekiss 60; Lucario 60; Garchomp 62 |

**Pontos de QA:** healing entre membros, transições para salões, impossibilidade de pular batalhas, derrota/retry, música de campeã, Hall of Fame real, badge/região correta e persistência após créditos. O número da equipe deve ser **versão de treinador**, não fixa em NPC do mapa sem escalar.

### 8.1 Rematch histórico de Elite Four após avanço pós-jogo

| Treinador | Equipe histórica de revanche |
|---|---|
| Aaron | Yanmega 65, Scizor 65, Vespiquen 66, Heracross 67, Drapion 69 |
| Bertha | Whiscash 66, Hippowdon 68, Golem 68, Gliscor 69, Rhyperior 71 |
| Flint | Houndoom 68, Rapidash 69, Flareon 71, Infernape 71, Magmortar 73 |
| Lucian | Mr. Mime 69, Bronzong 70, Espeon 71, Alakazam 72, Gallade 75 |
| Cynthia | Spiritomb 74, Roserade 74, Milotic 74, Togekiss 76, Lucario 76, Garchomp 78 |

**BLUE:** estes valores são **referência de composição/evolução**, jamais níveis para publicar no site. O pós-jogo global forte do projeto é um sistema diferente da revanche de Platinum; o time de referência precisa ser conciliado com o documento mestre de equipes mais fortes.

---

## 9. Pós-Liga, Pokédex nacional e exploração

### 9.1 National Dex

1. Terminar a Liga e registrar o Hall of Fame.
2. **Ver** as 210 espécies da Sinnoh Dex em Platinum (não é necessário capturá-las).
3. Inspecionar a ilustração de **Manaphy** em um livro do Pokémon Mansion, caso ainda não registrado.
4. Voltar ao laboratório de Sandgem; Professor Oak libera National Dex; Rowan entrega Poké Radar.
5. Depois disso, eventos como swarms diários, espécies extras em certas áreas, Pal Park e áreas pós-Liga podem abrir.

**BLUE — ADAPTAÇÃO:** a Pokédex multi-regional existente não deve ser apagada, substituída ou reduzida a 210 entradas. Implementar o requisito como **marco histórico opcional ou sub-Dex de Sinnoh**, com espécies vistas por região, sem impedir a viagem inter-regional definida pelo circuito.

### 9.2 Reconhecimento da Battle Zone

- O navio de **Snowpoint** alcança Fight Area, usando as condições originais pós-Liga.
- **Fight Area:** primeiro encontro com Barry e dupla de Barry contra Flint/Volkner; liberada entrada de Battle Frontier e outros caminhos.
- **Survival Area:** acesso ao Battleground, revanches, caminhos rumo a Stark Mountain.
- **Resort Area:** Villa e atividades facultativas.
- **Rotas 225–230:** treinadores de alto nível, terrenos especiais e ramificações entre as áreas. Route 228 contém tempestade de areia e instrutor de golpes especiais dos iniciais.
- **Stark Mountain:** história de Buck, Charon e Looker conclui remanescentes do Team Galactic; Magma Stone é devolvida e Heatran pode aparecer.

### 9.3 Conteúdo pós-jogo que não deve travar o circuito regional

National Dex, Pal Park, Pallet/transferência de gerações antigas, Battle Frontier, Battleground, Villa, eventos Nintendo de míticos e todos os lendários opcionais **não podem ser condição adicional inventada para liberar as duas regiões vizinhas**. O marco do circuito é a Liga vencida e os critérios já previstos no documento de regiões.

---

## 10. Lendários, míticos e formas especiais

| Pokémon ou grupo | Área/evento em Platinum | Condição essencial | Observação de implementação |
|---|---|---|---|
| Giratina (Origin) | Distortion World | Final contra Cyrus | Nível histórico 47; pode ser capturado ou derrotado |
| Uxie | Lake Acuity | Trio libertado após Distortion World | Encontro estático |
| Azelf | Lake Valor | Trio libertado | Encontro estático |
| Mesprit | Lake Verity → roaming | Trio libertado | Foge e passa a circular por Sinnoh |
| Dialga | Spear Pillar | Arco Galactic concluído; orbs, eventos de Celestic | Portal distinto, nível histórico 70 |
| Palkia | Spear Pillar | Condição semelhante à de Dialga | Portal distinto, nível histórico 70 |
| Cresselia | Fullmoon Island → roaming | National Dex, missão do menino em Canalave | Lunar Wing cura menino; nível histórico 50 |
| Heatran | Stark Mountain | Quest de Buck, Magma Stone devolvida | Nível histórico 50 |
| Regigigas | Snowpoint Temple | Acesso pós-Liga/National Dex + Regis | Verificar pré-requisitos originais da versão |
| Regirock / Regice / Registeel | Route 228 / Mt. Coronet / Iron Island | Regigigas de evento especial no cartucho | Evento de distribuição, não desbloqueio normal |
| Rotom | Old Chateau | Noite, interação com TV | Formas adicionais dependem de Secret Key histórica |
| Darkrai | Newmoon Island | Member Card do evento Nintendo | Evento histórico limitado, não acesso livre |
| Shaymin | Flower Paradise, além de Route 224 | Oak's Letter do evento Nintendo | Gracidea permite Sky Forme sob condições |
| Arceus | Hall of Origin, Spear Pillar | Azure Flute, evento planejado na geração original | Distribuição/evento histórico; **não tratar como encontro normal garantido** |
| Manaphy / Phione | Ovo de Pokémon Ranger / Day Care | Interoperabilidade externa | No Blue, exige distribuição/mecânica própria, não emular link DS inexistente |

**Atenção:** os itens event-only (Member Card, Oak's Letter, Azure Flute, Secret Key e Regigigas de distribuição) **não são fornecidos automaticamente pela campanha normal de Platinum**. A adaptação para o Blue precisa de decisão autoral e testes; jamais declarar esses míticos capturáveis normalmente sem evento projetado. A distinção **capturável no mundo** versus **autorizado na party por oito insígnias locais** deve ser mantida em todos os casos.

### 10.1 Outros Pokémon especiais e presentes

- **Togepi:** ovo concedido por Cynthia em Eterna após salvar o empresário.
- **Riolu:** ovo concedido por Riley em Iron Island após finalizar a exploração.
- **Eevee:** presente de Bebe em Hearthome, com vaga na equipe.
- **Porygon:** presente de um NPC em Veilstone.
- **Drifloon:** encontro fixo de sexta em Valley Windworks, após Mars.
- **Spiritomb:** Hallowed Tower na Route 209 após Odd Keystone e condição original do Underground.
- **Gible:** entrada camuflada de Wayward Cave, acessível por baixo do Cycling Road.
- **Unown:** Solaceon Ruins; variantes e caminhos devem ser auditados por mapa.

---

## 11. Battle Frontier e batalhas de revanche

### 11.1 As cinco instalações de Platinum

| Instalação | Frontier Brain | Regra principal | Lutas importantes no formato Single |
|---|---|---|---|
| Battle Tower | Palmer | Sequências, equipes próprias, itens distintos | 21ª e 49ª batalha |
| Battle Factory | Thorton | Pokémon alugados, possibilidade de troca após a vitória | 21ª e 49ª batalha |
| Battle Arcade | Dahlia | Roleta com efeitos de campo, status, vantagem/desvantagem | 21ª e 49ª batalha |
| Battle Castle | Darach / Caitlin | Castle Points; cura e serviços adquiridos | 21ª e 49ª batalha |
| Battle Hall | Argenta | Um Pokémon, escolha de tipos, sequência especial | 50ª e 170ª batalha |

**Platinum:** Battle Points são concedidos por vitórias e trocados por itens. Single costuma exigir três Pokémon e Double quatro, com exceções por instalação; regras de nível e restauração variam. Muitos lendários/míticos têm restrições próprias.

**BLUE:** não considerar a Battle Frontier completa só porque os cinco prédios têm mapas. Cada instalação exige seu **modo de combate**, regras, persistência de streak, recuperação, prêmios, IA, desafios, derrota e menu próprio. Se for incompatível com o motor atual, manter **OPCIONAL / não implementado** sem afetar Liga nem viagens.

### 11.2 Times dos Frontier Brains que são determinísticos em Platinum

- **Palmer (Tower):** primeiro Dragonite/Rhyperior/Milotic; segundo Cresselia/Heatran/Regigigas.
- **Darach (Castle):** primeiro Staraptor/Houndoom/Empoleon; segundo Empoleon/Gallade/Entei.
- **Dahlia (Arcade):** primeiro Dusknoir/Medicham/Ludicolo; segundo Blaziken/Togekiss/Zapdos.
- **Thorton (Factory):** time de aluguel variável, sem equipe única.
- **Argenta (Hall):** espécie variável e adversário adaptado ao desafio.

### 11.3 Battleground / Top Trainer Cafe — composição histórica para rematches

| Líder | Equipe de revanche em Platinum (não confundir com time inicial) |
|---|---|
| Roark | Aerodactyl, Probopass, Rampardos, Golem, Tyranitar |
| Gardenia | Jumpluff, Cherrim, Bellossom, Torterra, Roserade |
| Fantina | Banette, Mismagius, Gengar, Drifblim, Dusknoir |
| Maylene | Hitmontop, Breloom, Medicham, Lucario, Machamp |
| Crasher Wake | Sharpedo, Floatzel, Quagsire, Gyarados, Ludicolo |
| Byron | Skarmory, Magnezone, Steelix, Bastiodon, Aggron |
| Candice | Weavile, Abomasnow, Mamoswine, Froslass, Glaceon |
| Volkner | Jolteon, Raichu, Luxray, Electivire, Lanturn |

Parceiros também podem aparecer como oponentes no café: **Cheryl, Mira, Riley, Marley e Buck**. Estes perfis são referências históricas e exigem comparação com a política do pós-jogo forte global, além de checagem das espécies/moves no PBS instalado.

### 11.4 Barry no pós-jogo

- Após liberar Battleground, Barry pode desafiar o jogador em finais de semana na Survival Area.
- Platinum aumenta o estágio de sua equipe em novas revanches; o detonado também descreve um estágio adicional depois de muitas vitórias na Elite Four.
- **BLUE:** usar estágios de dificuldade/level cap compatíveis com a estrutura do próprio jogo, sem copiar níveis absolutos de 61–85 ou exigir artificialmente vinte Ligas para o pós-jogo global.

---

## 12. Catálogo de mapas e conexões a conferir

**Nomes são lógicos, NÃO são IDs numéricos.** O grafo real deve ser exportado de uma fonte autorizada e conciliado com [SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md). Existem IDs de um piloto legado em 800–805, faixa protegida pelo planejamento de Johto; portanto **não reaproveitar esses números** em jogo compartilhado sem remapeamento e auditoria.

### 12.1 Superfície e cidades

- Cidades: Twinleaf, Sandgem, Jubilife, Oreburgh, Floaroma, Eterna, Hearthome, Solaceon, Veilstone, Pastoria, Celestic, Canalave, Snowpoint, Sunyshore, Pokémon League, Fight Area, Survival Area e Resort Area.
- Rotas: 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229 e 230.
- Lagos: Verity, Valor e Acuity, com entradas, bordas, cavernas internas e mudanças de enredo.
- Litorais e conexões: Valor Lakefront, caminhos de acesso a Iron Island, Route 219–221, Battle Zone, Sendoff Spring e Spear Pillar.

### 12.2 Cavernas, torres, prédios e áreas especiais

Oreburgh Gate; Oreburgh Mine; Ravaged Path; Eterna Forest; Old Chateau; Valley Windworks; Floaroma Meadow; Galactic Eterna Building; Cycling Road; Wayward Cave (incluindo entrada sob a ponte); Mt. Coronet (subsolos, andares e entradas regionais); Lost Tower; Solaceon Ruins; Amity Square; Contest Hall; Great Marsh; Pokémon Mansion/Trophy Garden; Fuego Ironworks; Iron Island; Galactic Veilstone Warehouse e HQ; Canalave Library; Snowpoint Temple; Sunyshore Lighthouse; Victory Road; Distortion World; Turnback Cave; Fullmoon Island; Newmoon Island; Flower Paradise / Seabreak Path; Hall of Origin; Stark Mountain; Battle Frontier e suas cinco instalações; Battleground; Villa; Ribbon Syndicate.

### 12.3 Interiores mínimos que não podem ficar vazios

- Casas do protagonista, mãe e Barry; laboratório de Rowan; escolas e museu; ginásios completos; Centros Pokémon com cura, som e spawn; PokéMarts/Department Store; casa de Bebe; Day Care; biblioteca; galpões Galactic e depósitos; Pokémon Mansion; café do Battleground; hospedagens; porto/barcos; farol; instalações Frontier.
- Para **cada** interior: entrada, saída, colisão, spawn, facing, NPC, itens, condições de acesso, música, cura, retorno via Fly/teleport e save/reload.

**VALIDAR:** nenhum ponto da lista autoriza atribuir um MapID, número de NPCs, coordenada, tileset ou música fictícia. Extraia sempre do conteúdo real ou crie arte original auditável.

---

## 13. Matriz de flags e contrato de eventos para implementação

Nomes abaixo são **chaves simbólicas recomendadas**. Devem ser transformados em chaves isoladas compatíveis com o contrato atual do Blue, jamais em números arbitrários de switch.

| Flag proposta | Ativação | Consumidores / desbloqueios |
|---|---|---|
| SINNOH_INTRO_BARRY_MET | Conversar em Twinleaf | Barry na Route 201 |
| SINNOH_STARTER_CHOSEN | Poké Bola física concluída | Primeiro rival, posse inicial |
| SINNOH_BARRY_01_WON | Batalha após Rowan | Running Shoes / Sandgem |
| SINNOH_POKEDEX_GIVEN | Rowan no laboratório | Tutorial e funcionalidades |
| SINNOH_PARCEL_RECEIVED | Mãe após Sandgem | Escola Jubilife |
| SINNOH_PARCEL_DELIVERED | Entrega a Barry | Town Map |
| SINNOH_CATCH_TUTORIAL_DONE | Route 202 | Cinco Poké Balls uma vez |
| SINNOH_BADGE_01_ROARK | Roark vencido | Rock Smash / Jubilife Galactic |
| SINNOH_WORKS_KEY_GIVEN | Floaroma Meadow | Porta Windworks |
| SINNOH_MARS_WINDWORKS_WON | Mars vencida | Route 205 e Drifloon |
| SINNOH_BADGE_02_GARDENIA | Gardenia vencida | Cut / Galactic Eterna HQ |
| SINNOH_JUPITER_ETERNA_WON | Jupiter vencida | Bicicleta e Togepi |
| SINNOH_BICYCLE_GIVEN | Loja Eterna | Cycling Road |
| SINNOH_BADGE_03_FANTINA | Fantina vencida | Progressão a Route 209 / Surf e Defog via HM |
| SINNOH_BADGE_04_MAYLENE | Maylene vencida | Fly / recuperação Pokédex |
| SINNOH_ASSISTANT_DEX_RETURNED | Galactic em Veilstone | Conclusão do arco e Fly |
| SINNOH_BADGE_05_WAKE | Wake vencido | Explosão e perseguir recruta |
| SINNOH_SECRETPOTION_RECEIVED | Cynthia em Valor Lakefront | Psyduck da Route 210 |
| SINNOH_PSYDUCK_HEALED | Aplicar item | Rota norte / Old Charm |
| SINNOH_OLD_CHARM_DELIVERED | Avó de Cynthia | Cyrus em Celestic |
| SINNOH_CYRUS_CELESTIC_WON | Batalha na caverna | Surf |
| SINNOH_BADGE_06_BYRON | Byron vencido | Strength |
| SINNOH_IRON_ISLAND_RILEY_DONE | Galactic derrotada na ilha | Ovo Riolu |
| SINNOH_LIBRARY_MEETING_DONE | Evento biblioteca | Crise dos lagos |
| SINNOH_SATURN_VALOR_WON | Lake Valor | Arco Verity |
| SINNOH_MARS_VERITY_WON | Lake Verity | Avanço para Acuity |
| SINNOH_BADGE_07_CANDICE | Candice vencida | Rock Climb / Lake Acuity |
| SINNOH_ACUITY_JUPITER_SCENE | Cena de Barry no lago | HQ Galactic |
| SINNOH_GALACTIC_KEY_ACQUIRED | Warehouse | Portões HQ |
| SINNOH_CYRUS_HQ_WON | Batalha na HQ | Master Ball, Saturn |
| SINNOH_SATURN_HQ_WON | Libertar trio | Acesso Spear Pillar |
| SINNOH_SPEAR_PILLAR_DUO_WON | Barry + Mars/Jupiter | Portal Distortion World |
| SINNOH_CYRUS_DISTORTION_WON | Cyrus final | Giratina |
| SINNOH_GIRATINA_ENCOUNTER_CLEARED | Captura/derrota | Portal de saída |
| SINNOH_ROWAN_POST_DISTORTION | Laboratório Sandgem | Route 222 |
| SINNOH_BADGE_08_VOLKNER | Volkner vencido | Jasmine / Waterfall |
| SINNOH_WATERFALL_RECEIVED | Jasmine | Route 223 / Liga |
| SINNOH_BARRY_LEAGUE_WON | Antessala Liga | Portão Elite Four |
| SINNOH_HALL_OF_FAME_DONE | Entrada real no Hall of Fame | Liga global + pós-Liga |
| SINNOH_NATIONAL_DEX_UNL | Vistas 210 + Rowan/Oak | Conteúdo pós-Liga opcional |
| SINNOH_STARK_MOUNTAIN_DONE | Buck/Charon/Looker | Heatran |
| SINNOH_BATTLEGROUND_UNL | Buck após Stark Mountain | Rematches regionais |

**Eventos repetíveis** (diários/semanal/pós-jogo) devem usar estruturas separadas de período, não reativar flags irreversíveis. Validação do item/espécie/trainer deve ocorrer **antes** da marcação de recompensa.

### 13.1 Critérios de aceite de uma cena

Para cada cena obrigatória, exigir:

1. Player alcança o gatilho real pelo mapa anterior, sem teleporte de desenvolvedor.
2. NPCs caminham, giram, iniciam diálogo e executam movimento automático onde necessário.
3. Batalha inicia exatamente uma vez; derrota do jogador não marca vitória.
4. Todo item e badge chega ao inventário/sistema previsto uma só vez; party cheia não perde ovos.
5. Portas e obstáculos mudam estado, sem acesso prematuro ou softlock.
6. Música da cena, batalha, vitória, cura, fade e retorno são testados no jogo real.
7. Save/reload antes e depois da cena preserva o estado; retorno entre regiões não repete intro.
8. Windows e JoiPlay/Android conseguem executar interação, encontros e controles.
9. Regredir Decades, Kanto, Johto e Hoenn antes de mesclar na main.

### 13.2 Casos de testes de ponta a ponta

- **T01 — Nova partida Sinnoh:** spawn no quarto → mãe → Barry → Rowan → três Poké Bolas físicas → só um inicial → rival com vantagem.
- **T02 — Introdução e tutoriais:** Lake Verity → Sandgem → Pokédex → Parcel → Route 202 → Jubilife → Town Map/Pokétch.
- **T03 — Badge 1:** Route 203 → Oreburgh Gate → Mine → Roark → uso de Rock Smash.
- **T04 — Mars:** Jubilife dupla → Floaroma → Works Key → moinho → Mars → ponte libera.
- **T05 — Gardenia/Jupiter:** Cheryl sai corretamente → Cut → Gardenia → HQ Eterna → bicicleta/Togepi.
- **T06 — Fantina:** Contest Hall ativa ginásio 3 → puzzle → badge → Barry Route 209.
- **T07 — Maylene:** Veilstone puzzle → Galactic rouba Pokédex → dupla → Fly.
- **T08 — Wake/Celestic:** Barry Pastoria → Wake → perseguição → SecretPotion → Psyduck → Defog → Cyrus → Surf.
- **T09 — Byron/Riley:** Surf Route 218 → Barry Canalave → Byron → Iron Island → Strength/Riolu → biblioteca.
- **T10 — Lagos/Candice:** Saturn/Valor → Mars/Verity → neve/217 → Rock Climb coletado → Candice → Jupiter/Acuity.
- **T11 — HQ/Spear Pillar:** Keys → Master Ball → libertar trio → Mars/Jupiter com Barry → portal.
- **T12 — Distortion World:** atravessar todos os segmentos, puzzle, Cyrus, Giratina e saída sem travar.
- **T13 — Volkner/Liga:** Route 222 → farol → gym 8 → Jasmine → Waterfall → Victory Road → Barry → Elite Four/Cynthia → Hall of Fame.
- **T14 — Multi-regiões:** Sinnoh vencida libera vizinhos do circuito correto, badges globais/local corretos, especiais transferidos à Box em região bloqueada e retorno sem reiniciar Twinleaf.
- **T15 — Pós-jogo:** National Dex, Battle Zone, Buck/Charon, Heatran, Battleground, lendários e áreas opcionais com estados independentes.
- **T16 — Regressões:** atualizar/adicionar Sinnoh sem sobrescrever MapIDs 800–805 do legado ou faixa protegida de Johto, sem quebrar saves, lançadores, música, Kanto/Hoenn/Decades e site.

### 13.3 Mapa de conteúdo para o site

Para cada área de Sinnoh, expor somente após dados reais aprovados:

- Página **História/Detonado**: objetivo, região, etapa, mapa real, NPC/eventos, requisitos e próximo destino.
- Página **Ginásios**: líder, tipo, badge, equipe histórica vs equipe atual do Blue, habilidades/moves quando auditados — **sem nível numérico fixo**.
- Página **Treinadores**: filtro **Sinnoh local** e visão **todas as regiões**, com soma correta de insígnias e esmeraldas.
- Página **Elite Four e campeã**: times próprios e de revanche, sem copiar níveis fixos do cartucho.
- **Onde capturar / Habitat Dex**: encontros validados, dia/noite, percentuais reais do PBS, rota e link do mapa.
- **Lendários e eventos**: condicionais reais e aviso de especiais bloqueados para party até 8 insígnias locais.
- **Teste de Sinnoh**: permanecer experimental enquanto os gates técnicos e nativos não estiverem aprovados.
- Exportar dados de uma fonte única do jogo, não digitar times contraditórios em páginas separadas.

---

## 14. Checklist de entrega e responsabilidade

| Camada | O que deve existir | Prova |
|---|---|---|
| Fonte autorizada | Mapas/interiores de Sinnoh em formato editável, com licença/autorização | Inventário + hashes + atribuição |
| Geometria | Rotas, interiores, tilesets, passabilidade e IDs sem colisão | Grafo e teste visual |
| Eventos | 43 marcos e subeventos em sequência | Logs, flags e vídeo/screenshots do Game.exe |
| Pokédex/treinadores | Espécies, PBS e equipes existentes no Blue | Compilação PBS sem conflito |
| Áudio | BGM de rotas/cidades, cura, Galactic, Distortion, Liga | Audição real/fades/fallback |
| Batalhas | Líderes, rivais, vilões, parceiros, Elite Four | Testes de vitória/derrota |
| Progressão | 8 insígnias locais e esmeraldas globais | Save de teste e portal |
| Site | Conteúdo de Sinnoh derivado de dados efetivos | Verificação visual e links |
| Android | Entrada, encontros, menu, touch/teclado, save | JoiPlay testado |
| CI | Validadores estáticos e contrato | Checks aprovados, sem declarar jogabilidade por isso |
| Publicação | Backup, staging, rollback e regressões | Relatório final da fase |

**Estado ao redigir:** o projeto já possui plano, ferramentas de preparação, especificação Twinleaf/Barry e um piloto legado com conflitos de IDs a reconciliar; **não há base para afirmar que a campanha inteira esteja instalada ou que 13 fases jogáveis tenham sido aprovadas**. Confirmar sempre a documentação de progresso mais recente antes de implementar.

## 15. Referências e limites

- **Fonte principal consultada:** [Pokémon Mythology — Detonado Pokémon Platinum](https://www.pokemythology.net/detonados/detonado-platinum/). Referência de ordem narrativa, locais, personagens, equipes, presentes, atividades e pós-jogo. Para explicações detalhadas de puzzles e imagens originais, consultar essa página.
- **Fonte normativa interna:** [Plano de implementação Sinnoh](SINNOH_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md); [Progresso Sinnoh](SINNOH_PROGRESSO.md); [Plano global de regiões](PLANO_REGIOES_DESSASTRE_V2.md).
- **Pontos que exigem auditoria adicional:** microposições de NPCs, índices MapID, número exato de eventos de cada mapa, todas as tabelas de encontro/PBS/itens, alguns requisitos/eventos especiais históricos, inventário de BGM, licenças e diferenças entre implementação do Blue e cartucho Platinum.
- **Direitos:** nenhum trecho longo da narrativa, imagem, mapa ilustrado, diálogo proprietário ou áudio da Pokémon Mythology/Platinum foi incorporado. Esta é uma documentação original de referência factual e especificação de integração, não uma cópia alternativa do guia.
- **Limite de precisão:** se houver divergência entre este índice, o detonado e os dados reais da edição Platinum, registrar a diferença e auditar no jogo; se houver divergência com as regras já programadas do Blue, preservar a regra do Blue salvo decisão expressa do autor.

**Resultado esperado:** Sinnoh completa, com eventos e regiões coerentes, mas desenvolvida **em etapas verificáveis, isoladas e reversíveis**. O texto acima é a referência para construir e testar, não uma confirmação de implementação.
