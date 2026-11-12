# Johto — escolha fundamentada das fontes de mapas e músicas

**Projeto:** Pokémon Blue: Dessastre Paradoxal  
**Data da pesquisa:** 12/11/2026  
**Escopo:** selecionar fontes para preparar a região de Johto em RPG Maker XP / Pokémon Essentials v21.1, sem modificar Decades nem o conteúdo de Kanto já desenvolvido.  
**Estado:** estudo e plano de implantação; **não** significa que os mapas ou os áudios de Johto foram baixados, auditados ou instalados.

## 1. Decisão executiva

**Se a escolha deve ser feita somente entre os fangames da lista atual do projeto, selecionar _Pokémon Grueling Gold_ como referência principal dos mapas e da jornada clássica de Johto.** Trata-se de uma releitura de segunda geração feita em RPG Maker XP e Essentials v20.1, mais próxima do roteiro tradicional do que as adaptações baseadas em anime, linha do tempo alternativa ou Johto parcial. Isso **não comprova** que seu pacote distribuído contenha projeto RMXP editável, mapas reutilizáveis ou autorização para copiá-los.

**Para realmente obter uma fonte técnica de mapas editáveis, a melhor opção encontrada não é um jogo da lista:** o recurso comunitário **[Remastered Kanto and Johto Overworld and Caves Map Pack](https://www.eeveeexpo.com/resources/828/)**, de AenaonDogsky/AenaonDusky. Ele foi concebido para uso em projetos RMXP, inclui o mundo exterior de Johto com conexões e cavernas (exceto Mt. Silver) e explica a incorporação em projetos existentes. **Não instalar diretamente no jogo-mestre**: é necessário auditar e remapear IDs e dependências. O pacote não constitui, por si só, uma campanha pronta com todos os interiores, eventos e treinadores.

**Para música, tomar como referência o repertório oficial de _Pokémon HeartGold / SoulSilver_**, com _Crystal_ como referência opcional de arranjos clássicos. Fazer uma seleção regional com fontes de áudio cujo uso e redistribuição tenham sido verificados; o catálogo da trilha original serve para identificar quais composições pertencem a cada evento, **não** autoriza incorporar MP3s da Nintendo/Game Freak em um repositório público.

**Arquitetura recomendada:** mapa-base editável do Map Pack + auditoria de fidelidade pelo HG/SS + narrativa/eventos HG/SS/Crystal + catálogo musical HG/SS + engine, progressão, saves e sistemas de batalha **exclusivamente do Dessastre Paradoxal/Decades**.

## 2. O que a documentação do Blue já exige

Arquivos consultados na `main`:

- [`docs/ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md): lista **GS Vitro, Grueling Gold, Giovanni Origins, Fire Ash e Infinite Fusion** como candidatos de Johto, mas avisa que não tinha auditado fontes, mapas, editabilidade e licenças. Indica **HeartGold/SoulSilver ou Crystal** como base geográfica.
- [`docs/PLANO_REGIOES_DESSASTRE_V2.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PLANO_REGIOES_DESSASTRE_V2.md): define **HeartGold + SoulSilver**, com eventos complementares de Crystal; juntar exclusivos sem duplicar ginásios; após a Liga de Johto, desbloquear **Kanto e Hoenn**.
- [`docs/CIRCUITO_REGIONAL.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/CIRCUITO_REGIONAL.md): mostra o fluxo seguro já usado em Kanto — fonte externa auditada, leitura sem executar scripts, prévia isolada, remapeamento, backup, rollback e testes.
- [`docs/KANTO_ETAPAS.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_ETAPAS.md): diferencia **núcleos tecnicamente implementados** de **jogabilidade integralmente aceita**; o mesmo rigor deve valer para Johto.
- [`docs/KANTO_PLANO_APLICAR_MUSICAS.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_PLANO_APLICAR_MUSICAS.md) e [`docs/KANTO_MUSICAS_MAPEAMENTO.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_MUSICAS_MAPEAMENTO.md): catálogo por faixas, BGM/ME, eventos comprovados, regras de prioridade, proteção da trilha de Decades e auditoria por fases.
- [`README.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/README.md): base em **RPG Maker XP + Pokémon Essentials v21.1**, derivada localmente de Pokémon Decades. A pasta do jogo e seus recursos-base não integram integralmente o GitHub.

**Requisitos inegociáveis:**

1. Começar Johto na **casa do jogador em New Bark Town**, com saída/retorno funcionais, introdução, Professor Elm e inicial regional; o ponto inicial deve ser auditado contra mapas reais.
2. NPC de viagem regional na cidade inicial, conforme as regras do projeto, sem habilitar regiões ainda bloqueadas.
3. Oito insígnias de Johto próprias; cada conquista única alimenta **uma única vez** a progressão **global** de esmeraldas nativa, sem criar fórmula paralela. HMs/mobilidade dependem das insígnias e eventos **locais**.
4. Treinadores, encontros e níveis originais servem como dados-base; o balanceamento dinâmico já implementado no Blue decide a dificuldade em memória.
5. Após a Liga, liberar Kanto e Hoenn; Pokémon especiais (lendários, míticos, Ultra Beasts e Paradoxos) continuam sujeitos ao bloqueio da **região atual** até suas oito conquistas locais, com depósito seguro na Box.
6. Manter intactos IDs e dados de Decades e Kanto, conteúdo dos saves, Blue Studio, site, Pokédex, sistemas de música global e modo de batalha.
7. **Não** confundir o pacote de mapa com uma fonte pronta de NPCs, eventos de ginásio, interiores, encontros e músicas: essas camadas exigem auditorias separadas.

## 2.1. Regra obrigatória: implementar Johto sem quebrar o que já foi feito

**Prioridade máxima:** toda alteração de Johto deve ser **aditiva, isolada, reversível e comprovada por testes**, sem regressões em **Decades, Kanto, Blue Studio, Pokédex, site, músicas, saves ou multiplayer**. Um novo recurso regional nunca justifica substituir diretamente a instalação original.

1. **Linha de base antes de cada fase:** registrar commit/branch, testes de referência, hashes dos arquivos da instalação local, lista de MapIDs e IDs de tilesets em uso, scripts do plugin, catálogo de treinadores e estado dos saves.
2. **Separar fontes e jogo-mestre:** manter o download e os mapas doadores em `.blue-work/johto-source/`, preparar a cópia em `.blue-work/johto-pilot/` e usar perfis de save específicos de Johto. Nunca sobrescrever mapas de Decades ou Kanto por cima de IDs existentes, nem copiar `Scripts.rxdata`, `System.rxdata`, `MapInfos.rxdata` ou toda a pasta `game/Data` de outro jogo.
3. **IDs imutáveis:** criar chaves simbólicas para Johto e um manifesto `source_id -> destination_id`, reservando IDs realmente livres e congelando os IDs já publicados. Se for indispensável migrar algum dado, fornecer ferramenta de migração versionada, testes com saves antigos e rollback antes do `apply`.
4. **Serviços compartilhados com compatibilidade retroativa:** estender `RegionStart.rb`, `RegionTravel.rb`, `Regions.rb`, `RegionalPolicy.rb`, `RegionalCards.rb` e `BlueMusic.rb` de forma que operações em Decades e Kanto tenham comportamento idêntico ao atual. **Nunca** substituir seus adaptadores por versões exclusivas de Johto.
5. **Instalação segura:** implementar `dry-run` e comparação de hashes primeiro; `apply` só após auditoria e com backups. Toda escrita em arquivo existente deve ser atômica e reversível. Em erro, restaurar integralmente a versão anterior.
6. **Feature flag / disponibilidade real:** registrar Johto como `planned` enquanto não for jogável. A presença do mapa de terreno ou de um botão de teste **não** libera Johto no fluxo normal de nova partida nem no NPC de viagem.
7. **Testes de não regressão:** rodar testes anteriores de Decades, Kanto, seleção de saves, batalha, áudio e portal **antes e depois** de cada fase. Não avançar uma etapa quando falhar teste preexistente; identificar e corrigir a regressão na mesma entrega.
8. **Prova nativa:** toda atualização precisa distinguir CI/simulação de caminhada, entradas de casa, batalha e save/reload executados na janela real do jogo. Os testes estruturais não equivalem a aceitação integral.

### 2.2. Botão `Testar Johto` junto de `Testar Kanto`

No **mesmo menu inicial do `Game.exe` aberto pelo `Blue-Story.exe`**, preservar as opções existentes e mostrar nesta sequência:

```text
Continuar  (se houver save)
Novo Jogo
Testar Kanto
Testar Johto
[demais comandos já existentes: Mystery Gift, Opções, Sair, ...]
```

**Implementação inicial no repositório:** a opção foi adicionada em [`scripts/battle_polish/TitleKanto.rb`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/scripts/battle_polish/TitleKanto.rb), mantendo o contrato de retorno dos **índices originais** do Essentials/Auto Multi Save. O teste Kanto continua usando `KANTO_JOGAR_EXPERIMENTAL.bat` e seu perfil independente. A opção Johto, separadamente, só pode abrir **`JOHTO_JOGAR_EXPERIMENTAL.bat` + `scripts/regions/pilot_johto.py`**, quando ambos forem implementados e auditados.

Enquanto a infraestrutura de Johto não existe, clicar em **Testar Johto** informa **"Johto ainda está em preparação"** e permanece no menu; **jamais** lança Kanto como substituto nem cria save de Johto dentro de Decades. Quando o piloto for entregue, deverá abrir outra instância/cópia isolada, com perfil próprio, sem sobrescrever o `Game.exe` principal, arquivos locais ou saves existentes. O botão não deve aparecer dentro de nenhum piloto, evitando inicialização recursiva.

**Testes de regressão do menu:** preservar `Continue`, múltiplos slots, setas negativas dos saves, `New Game`, `Mystery Gift` e `Quit Game`; confirmar que o teste de Kanto segue na terceira opção e Johto na quarta, que cliques em Johto ausente retornam ao menu e que ambos os lançadores apontam para arquivos próprios dentro da raiz do projeto. Os testes de contrato estão em `tests/title_kanto_runtime.rb` e `tests/test_title_kanto.py`.

**Aceite:** o botão presente significa apenas **acesso ao teste**; não significa que Johto está pronta ou que `0/16` etapas do plano foram aprovadas. Para a ordem de implementação, consultar [`docs/JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md`](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md).

## 3. Comparação dos cinco fangames da lista

| Candidato | O que foi verificado externamente | Vantagem no Blue | Problema para copiar mapas/músicas | Decisão |
|---|---|---|---|---|
| **Grueling Gold** | Remake desafiador de Johto em RMXP e **Essentials v20.1**; foco em evolução da campanha Gen 2; há versão com Kanto anunciada | Melhor candidato **da lista** para analisar a progressão e geografia tradicional | Versão diferente do Blue v21.1; projeto editável, licenças de mapas e acervo musical **não confirmados** | **1º para referência de fangame** |
| **GS Vitro** | O site dos criadores apresenta a versão **v1.0** de um remake de Crystal com **Johto em mundo aberto**, com rotas menos bloqueadas e movimentos de campo em vez de HMs | Bom para ideias de navegação e melhorias de mapas | Mundo aberto e regras de campo divergem da campanha canônica e das HMs locais previstas no Blue; fonte editável e reutilização não auditadas | **2º, referência visual/alternativa** |
| **Giovanni Origins** | Projeto marcado como concluído, versão **2.13**; Kanto e Johto se passam cerca de **20 anos antes** de Red/Blue | Pode inspirar cenas e variantes históricas | Cidades, história e personagens são intencionalmente de outra época; traz músicas de Gen 1/2, mas a presença de áudios não licencia sua cópia | Referência narrativa, **não** mapa-base |
| **Fire Ash** | Feito em RMXP com **Essentials v19.1**, cobre várias regiões incluindo Johto, seguindo a viagem de Ash pelo anime | Bom para ver eventos entre regiões e uma campanha extensa | Mapas e eventos subordinados ao anime; maior distância de engine; não há fonte editável/uso de assets confirmado | Referência de estrutura multirregional |
| **Infinite Fusion** | Johto aparece no pós-jogo, mas **o oeste de Johto, incluindo Olivine, não existe** nessa versão; ginásios deslocados para Sevii Islands | Pode inspirar pós-jogo e conexões | **Região incompleta e reestruturada** para o propósito do Blue | **Não usar como base integral** |

### Grau de certeza

- **Confirmado por descrição pública do autor ou página do projeto:** conceito e escopo anunciados; versões indicadas nas fontes abaixo.
- **Não confirmado:** inspeção direta dos downloads de cada jogo, conteúdo de `Data/MapXXX.rxdata`, licença específica de redistribuição dos tiles e MP3s, integridade de um pacote baixado, compatibilidade real com a versão atual do Dessastre.
- O ranking acima é **adequação ao objetivo do Blue**, e não nota de qualidade geral dos jogos.

## 4. Fonte recomendada para mapas editáveis (fora da lista)

**[Remastered Kanto and Johto Overworld and Caves Map Pack — Eevee Expo](https://www.eeveeexpo.com/resources/828/)**  
**Autor publicado:** AenaonDogsky (também creditado como AenaonDusky no conteúdo)  
**Última atualização informada na página:** 16/02/2024.

**Pontos positivos comprovados na página:** mapas exteriores de Johto conectados; gráficos inspirados em HG/SS; tilesets compactos, autotiles e configuração básica de passabilidade; cavernas de Johto **exceto Mt. Silver**; instruções específicas para integrar mapas a projetos preexistentes.

**Limites críticos:**

- O pacote tem **mais de 140 mapas somando os conteúdos de Kanto e Johto**, e não 140 mapas exclusivos de Johto; **não presumir** que todos os interiores ou roteiros estejam prontos.
- Em projetos existentes, o próprio autor adverte para **não copiar `MapInfos.rxdata`**. Também é inadequado sobrescrever `Tilesets.rxdata`, `map_connections.txt`, metadados ou IDs fixos do Blue.
- Os tilesets citados na documentação do recurso ocupam IDs **21–24 na configuração de exemplo**, mas **esses IDs não podem ser copiados cegamente** para o Blue: devem ser realocados e todas as referências ajustadas.
- O recurso alerta que conexões automáticas se aplicam a projetos novos. Para o Blue, **reconectar** seus mapas e revisar cada warp e entrada/saída.
- O recurso inclui remixes de **Kanto/FRLG** e informa que arranjos de Johto seriam algo futuro; **não é uma fonte confirmada do pacote de músicas de Johto**.
- Há obrigação expressa de **créditos** a JohtoBlaziken, Earthescape/Orbitender, AenaonDusky, PS: The First Journey, Red's Journey West e autores dos tilesets. Os elementos de Pokémon/Game Freak e recursos derivados podem ter condições de propriedade intelectual adicionais. Registrar permissões antes de redistribuir qualquer recurso.

**Conclusão prática:** usar o pacote como **entrada técnica de mapas** somente depois de verificar seus arquivos e termos; preencher Mt. Silver, interiores, eventos e liga com trabalho próprio ou fontes adicionais autorizadas. Comparar a geografia final com HG/SS e consultar Grueling Gold como referência complementar, **sem misturar scripts e sistemas**.

## 5. Melhor fonte para músicas

A referência musical é o repertório de **Pokémon HeartGold & SoulSilver Super Music Collection**; como a referência geográfica principal é HG/SS, isso preserva a identidade auditiva de Johto. Há arranjos **GB Sounds** associados à estética de Gold/Silver/Crystal que podem ser considerados como opção estética, sujeitos às mesmas restrições de direitos.

**Fonte apenas para identificar títulos e funções:** [catálogo da trilha HG/SS no MusicBrainz](https://musicbrainz.org/release/216a467d-ccdb-4568-93db-b4ff13af8263). O catálogo **não** fornece autorização de uso ou MP3s licenciados. Não baixar e republicar gravações protegidas sem direitos necessários; usar áudio original ou composições/arranjos com autorização expressa para o projeto.

### Matriz inicial de músicas por função

| Chave funcional planejada | Referência de composição HG/SS | Ativação correta | Categoria no Blue |
|---|---|---|---|
| `JOHTO_NEW_BARK_TOWN` | New Bark Town | Rua/casas em que a música for devida | BGM ambiente |
| `JOHTO_ELM_LAB` | Elm Pokémon Lab | Laboratório | BGM ambiente |
| `JOHTO_ROUTE_29` | Route 29 | Rotas efetivamente correspondentes, após conferir mapa | BGM ambiente |
| `JOHTO_CHERRYGROVE` | Cherrygrove City | Cidade | BGM ambiente |
| `JOHTO_VIOLET` | Violet City | Cidade | BGM ambiente |
| `JOHTO_SPROUT_TOWER` | Sprout Tower | Torre e andares comprovados | BGM ambiente |
| `JOHTO_UNION_CAVE` | Union Cave | Caverna e andares apropriados | BGM ambiente |
| `JOHTO_RUINS_OF_ALPH` | Ruins of Alph | Exterior/interiores conforme fonte | BGM ambiente |
| `JOHTO_AZALEA` | Azalea Town | Cidade | BGM ambiente |
| `JOHTO_ROUTE_34` | Route 34 | Rota correspondente | BGM ambiente |
| `JOHTO_GOLDENROD` | Goldenrod City | Cidade | BGM ambiente |
| `JOHTO_NATIONAL_PARK` | National Park | Parque | BGM ambiente |
| `JOHTO_ECRUTEAK` | Ecruteak City | Cidade | BGM ambiente |
| `JOHTO_BURNED_TOWER` | Burned Tower | Torre | BGM ambiente |
| `JOHTO_OLIVINE_LIGHTHOUSE` | Olivine Lighthouse | Farol | BGM ambiente |
| `JOHTO_CIANWOOD` | Cianwood City | Cidade | BGM ambiente |
| `JOHTO_ROCKET_HQ` | Team Rocket HQ | Base Rocket | BGM ambiente |
| `JOHTO_RADIO_TOWER_OCCUPIED` | Radio Tower Occupied! | Somente durante ocupação/roteiro confirmado | BGM de cena |
| `JOHTO_DRAGONS_DEN` | Dragon's Den | Área correspondente | BGM ambiente |
| `JOHTO_BELL_TOWER` | Bell Tower | Torre | BGM ambiente |
| `JOHTO_WILD` | Battle! (Wild Pokémon - Johto) | Encontro selvagem **em Johto** | BGM batalha |
| `JOHTO_TRAINER` | Battle! (Trainer - Johto) | Treinador comum **em Johto** | BGM batalha |
| `JOHTO_RIVAL` | Battle! (Rival) | Classe/identidade real do rival | BGM batalha |
| `JOHTO_ROCKET` | Battle! (Team Rocket) | Membro Rocket identificado | BGM batalha |
| `JOHTO_GYM` | Battle! (Gym Leader - Johto) | Líder local de Johto confirmado | BGM batalha |
| `JOHTO_RAIKOU` | Battle! (Raikou) | Raikou real, com espécie verificada | BGM batalha |
| `JOHTO_ENTEI` | Battle! (Entei) | Entei real, com espécie verificada | BGM batalha |
| `JOHTO_HO_OH` | Battle! (Ho-Oh) | Ho-Oh real, com espécie verificada | BGM batalha |
| `JOHTO_VICTORY_WILD` | Victory! (Wild Pokémon) | Após vitória selvagem, uma vez | BGM vitória |
| `JOHTO_VICTORY_TRAINER` | Victory! (Trainer) | Após vitória treinador, uma vez | BGM vitória |
| `JOHTO_VICTORY_GYM` | Victory! (Gym Leader) | Após vitória líder, uma vez | BGM vitória |
| `JOHTO_RECEIVED_BADGE` | Received a Gym Badge! | Ao **receber** a insígnia; nunca só por entrar no ginásio | ME/vinheta |
| `JOHTO_HEALED` | Pokémon Healed | Depois da cura efetiva | ME/vinheta |
| `JOHTO_RECEIVED_POKEMON` | Received a Pokémon! | Após receber Pokémon com sucesso | ME/vinheta |
| `JOHTO_EVOLUTION` | Evolution | Somente na sequência de evolução | BGM/cena |
| `JOHTO_EVOLUTION_COMPLETE` | Congratulations! Your Pokémon Evolved! | Depois da evolução concluída | ME/vinheta |

**Não atribuir músicas de cidades por semelhança de nomes ou suposição.** Para Olivine, Mahogany, Blackthorn, Ice Path, Whirl Islands, Lake of Rage, Mt. Silver, Lugia, Suicune, Liga, Hall of Fame e créditos, localizar primeiro os títulos exatos no catálogo/fonte autorizada e mapear eventos reais; usar o áudio ambiente atual se a correspondência não puder ser provada. As chaves acima são **propostas simbólicas**; não representam MapIDs existentes ou implementações concluídas.

### Política de áudio por região

- Biblioteca proposta **somente se existirem faixas com uso permitido**: `assets/music/johto/BGM/`, `assets/music/johto/ME/` e `data/johto-music.json` com hash, autor, origem, licença e estado de integração.
- Jogo instalado (se aplicável): `game/Audio/BGM/Johto/` e `game/Audio/ME/Johto/`; o repositório não deve virar um espelho de áudio protegido.
- Usar o mesmo resolver regional e a mesma prioridade que Kanto: **cena explícita > condição especial > regra de mapa/batalha regional > fallback original**. Preferência manual configurada pelo jogador deve ser respeitada conforme o adaptador existente.
- Ao entrar ou voltar em Decades/Kanto, restaurar suas músicas sem substituir as preferências e sem gravar chaves globais (`wild`, `trainer`, `gym`, etc.) de maneira destrutiva.
- Uma vinheta ME só toca no evento **concluído**, não ao abrir diálogo ou recarregar save. Implementar restauração da BGM, controle de fades e proteção contra duplo disparo.
- Arquivos ausentes, eventos não instalados ou faixas não autorizadas devem ser catalogados como **PENDENTE**, e jamais vinculados a uma música aleatória apenas para preencher lacunas.

## 6. Plano de implantação de Johto em fases

**Fase 0 — Auditorar fontes e licenças (sem modificar o jogo).** Obter o Map Pack de sua página original; extrair em workspace isolado e registrar hashes e versão. Contar `MapXXX.rxdata`, tilesets, autotiles, metadados e mapas de Johto por **conteúdo**, não apenas pelo número total do pacote. Inspecionar também 1 build de Grueling Gold **somente como referência técnica/visual**, sem assumir direito de reutilização. Catalogar termos e créditos. Mapear a lista de músicas HG/SS por título sem copiar áudio não autorizado.

**Fase 1 — Criar registro Johto.** Propor `data/regions/johto-source.json`, `data/regions/johto-map-plan.json`, `data/johto-music.json` e `docs/JOHTO_ETAPAS.md`. Definir chaves `JOHTO_*`, estados de obtenção das oito insígnias, conexões com Kanto/Hoenn, local inicial, ponto de chegada e separação local/global de progresso. **Não** declarar a região selecionável antes de instalar/testar os mapas.

**Fase 2 — Importação isolada dos primeiros mapas.** Fazer `dry-run` com New Bark Town, casa do jogador, Elm Lab, Rota 29 e Cherrygrove, sem tocar nos mapas de Decades/Kanto. Alocar MapIDs e tilesets **livres** da base real; remapear conexões, teletransportes, direção inicial, tiles passáveis, portas e colisões. Conferir que cada interior abre e retorna sem posições inválidas.

**Fase 3 — Primeiro núcleo jogável.** Implementar introdução, escolha do inicial de Johto, rival, NPCs, encontros regionais e um ciclo completo de entrada/saída de mapas. Integrar áudio **apenas** para os mapas e eventos comprovados. Testar novo jogo e save/reload tanto no piloto como no jogo instalado, antes de habilitar o destino no seletor.

**Fase 4 — Campanha até os quatro primeiros ginásios.** Violet/Falkner, Azalea/Bugsy, Goldenrod/Whitney, Ecruteak/Morty; incluir Sprout Tower, Union Cave, Slowpoke Well, Ilex Forest, Ruins of Alph e National Park conforme inventário. Usar líderes, equipes e eventos HG/SS auditados, com treinadores originais em tabela e **balanceamento Blue em runtime**. Não transportar a IA de Grueling Gold.

**Fase 5 — Campanha dos quatro últimos ginásios.** Olivine/Jasmine, Cianwood/Chuck, Mahogany/Pryce, Blackthorn/Clair; completar Lighthouse, Whirl Islands, Lake of Rage, Rocket HQ/Radio Tower, Ice Path e Dragon's Den. Validar Surf e demais HMs por requisitos **locais**, encontros especiais, evolução da história e tratamento regional de Roaming Pokémon.

**Fase 6 — Liga, lendários, conexões e pós-jogo.** Construir/autorizar Victory Road e Liga, eventos de Ho-Oh/Lugia/Suicune conforme a política de fusão e **Mt. Silver fora do Map Pack**. Só conceder liberação Kanto + Hoenn depois do encerramento da Liga e habilitar o NPC regional de viagem em New Bark Town. Preservar restrições de party/Box. Separar o pós-jogo global de equipes oficiais mais fortes, que só acontece após as campanhas requeridas no Plano v2.

**Fase 7 — Testes, música e publicação.** Seguir o padrão de Kanto: checagem de documentos e manifests, testes unitários de compilação/IDs/entradas/saves, teste nativo Windows GUI, checagem Android/JoiPlay quando houver ambiente, regressão Decades e Kanto, auditoria de áudio por evento e rollback. Registrar **duas barras independentes**: núcleos implementados/testados automaticamente e etapas **integralmente aceitas em gameplay**, sem inflar contagens com documentação.

## 7. Checklist obrigatório de qualidade

### Mapas

- [ ] Map Pack obtido legitimamente, identificado por versão e hash; direitos e créditos verificados.
- [ ] Inventário real de cidades, rotas, cavernas, interiores e mapas ausentes.
- [ ] `MapInfos.rxdata`, `Tilesets.rxdata`, `Scripts.rxdata` e dados-base de Decades preservados; remapeamento isolado em cópia.
- [ ] Nenhum ID de mapa, tileset, switch, variável, evento ou ponto de Fly colide com conteúdo já instalado.
- [ ] Cidade inicial: jogador **dentro de casa**, com direção e saída corretas.
- [ ] Portas, escadas, passabilidade, transfers bidirecionais e ponto de cura cobertos por testes.
- [ ] Map metadata, map connections, encontros, treinadores e localização no site usam os **MapIDs instalados**.
- [ ] Mt. Silver e todos os interiores ausentes explicitamente pendentes, sem inventar conclusão.

### Músicas

- [ ] Cada áudio possui origem, autorização adequada, hash e categoria BGM/ME correta.
- [ ] Música de cidade, rota, caverna e transporte associada a mapa/estado comprovado.
- [ ] Faixas de batalha condicionadas à classe real de adversário/espécie/chefe; sem substituir sorteios de Decades.
- [ ] ME toca uma vez por evento, pausa/restaura ambiente e não reaparece após reload.
- [ ] Viagem Johto → Kanto → Decades mantém música regional correta e respeita preferências.
- [ ] Testes de loop, fade, volume, música ausente, saves e Android/JoiPlay quando aplicável.

### Regras do jogo

- [ ] Insígnias de Johto alimentam esmeraldas globais **uma vez por conquista**.
- [ ] HMs e restrições de especiais dependem dos oito marcos **locais**.
- [ ] NPC de viagem e destinos liberados respeitam o circuito Johto → Kanto/Hoenn.
- [ ] Treinadores, encontros, espécies e cenas canônicas não sobrescrevem sistemas da base Decades.
- [ ] Pós-jogo mundial não inicia antes de concluir as dez campanhas exigidas.
- [ ] Nenhum progresso/áudio/mapa é marcado como aprovado sem prova correspondente.

## 8. Fontes e referências de consulta (consultadas em 12/11/2026)

### Fontes do repositório

- [Estudo de fangames de todas as regiões](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md)
- [Plano de regiões v2](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/PLANO_REGIOES_DESSASTRE_V2.md)
- [Circuito regional / técnica de importação de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/CIRCUITO_REGIONAL.md)
- [Plano musical de Kanto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/blob/main/docs/KANTO_PLANO_APLICAR_MUSICAS.md)

### Fontes externas

- [Grueling Gold — página de descrição (PokéHarbor)](https://www.pokeharbor.com/2024/02/pokemon-grueling-gold/)
- [GS Vitro — site dos criadores](https://pokemonperseida.blogspot.com/p/gs-vitro-descarga.html) — **atenção a sites de terceiros que imitam o projeto**.
- [Giovanni Origins — página do desenvolvedor](https://eeveeexpo.com/threads/6220/)
- [Fire Ash — página do desenvolvedor](https://eeveeexpo.com/threads/9489/)
- [Infinite Fusion — FAQ da comunidade sobre Johto parcial](https://infinitefusion.fandom.com/wiki/FAQ)
- [Map Pack editável Kanto/Johto — página do autor](https://www.eeveeexpo.com/resources/828/) e [histórico de atualizações](https://www.eeveeexpo.com/resources/828/updates)
- [HeartGold & SoulSilver Super Music Collection — catálogo de faixas (MusicBrainz)](https://musicbrainz.org/release/216a467d-ccdb-4568-93db-b4ff13af8263)

**Decisão final:** **Grueling Gold** vence entre os fangames listados **para estudar Johto**; **Remastered Kanto and Johto Map Pack** é a melhor fonte encontrada **para preparar importação técnica dos mapas**; **HeartGold/SoulSilver** deve orientar a **seleção de músicas**, com áudio próprio ou autorizado para distribuição. Avançar somente após auditoria real dos arquivos de origem e evidências de teste da engine.