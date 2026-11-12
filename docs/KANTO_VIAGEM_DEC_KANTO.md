# Etapa 05 — Viagem Decades ↔ Kanto no mesmo save

**Estado:** serviço de viagem implementado; testes de regras Ruby aprovados; aceitação gráfica Windows e teste completo de transferência nativa em validação.  
**Especificação:** [Plano de regiões v2](PLANO_REGIOES_DESSASTRE_V2.md), seções 10, 17 e 18.  
**Barras:** desenvolvimento **05/16 (31,25%)**; etapas plenamente aceitas **01/16 (6,25%)**, **15 pendentes**.

## 1. O que existe no código

O arquivo [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb) centraliza os deslocamentos e foi integrado ao plugin principal do Blue:

- **Decades → Kanto:** fica disponível somente quando o encerramento de Decades é comprovado **simultaneamente** pela Esmeralda Stellar (badge 18), pelo switch 122 pós-Hall da Fama **e** pela auditoria do mapa original. A presença do mapa de Kanto no jogo integrado também é obrigatória. O serviço consulta `BlueRegions.snapshot` e registra a conclusão de Decades apenas quando a viagem é efetivada.
- **Chegada em Kanto:** Pallet Town, usando o mapa e as coordenadas confirmados no marcador gerado pelo importador. Não usa mapa fictício.
- **Kanto → Decades:** retorna ao mapa/coordenadas/direção que foram registrados **antes de sair de Decades**, desde que a região continue desbloqueada e o mapa exista. O retorno fica disponível pelo menu mesmo após salvar e reabrir a partida em Kanto.
- **Demais regiões:** são mostradas como bloqueadas ou em preparação. Não são selecionáveis antes de suas Ligas ou sem mapas instalados.
- **Um único save:** a viagem modifica apenas `blue_regions.current`, o histórico de transporte, a posição do jogador e a party quando exige depósito em Box. Não altera `initial`, não recria jogador, bag, PC, Pokédex ou um segundo diretório de save. **Salve normalmente no mesmo slot após a viagem.** O serviço não grava automaticamente por cima de um slot escolhido por engano.
- **Viajar é opcional:** o menu exige confirmação e permite cancelar sem mudanças.

### Acesso ao agente

Após o final comprovado de Decades, o menu de pausa mostra **Agente de Transporte Regional**. O menu **Circuito de regiões** também exibe e permite usar os destinos realmente jogáveis. O agente oferece consulta aos destinos, organização do PC e permanecer.

**Limitação conhecida:** nesta entrega o agente está no menu de pausa, **não foi inserido como NPC físico na saída da Liga**. A inserção física ainda exige auditar a posição de saída após o Hall da Fama no mapa original, para não interferir na cutscene. O item do menu fica oculto durante batalhas e enquanto o jogador está em transição. Não atribuir a esse menu uma cura grátis disponível de qualquer ponto do mapa.

## 2. Segurança dos Pokémon na viagem

O serviço usa o cálculo de regras de `BlueRegions.transfer_plan`:

1. Verifica o desbloqueio regional e o mapa de destino.
2. Classifica Pokémon especiais pelas flags de espécie (`Legendary`, `Mythical`, `UltraBeast`, `Paradox`); não usa BST e não bloqueia automaticamente toda forma regional/Mega.
3. Se o destino ainda não tiver oito conquistas locais, reserva **vagas livres reais no PC** para especiais da party.
4. **Cancela sem perdas** se a Box não tiver vagas suficientes ou se a party ficar sem Pokémon comum capaz de batalhar.
5. Deposita os especiais, transfere o mapa, grava o estado regional; se a operação lançar exceção, repõe a party, os slots do PC e o estado anterior, e tenta voltar às coordenadas de origem.
6. O organizador de Boxes recebe proteção nas ações básicas de retirar, colocar e trocar um especial para a party quando a região atual não permite.

**Escopo ainda pendente da etapa 06:** cobertura dos *demais caminhos* de entrada na party (trocas, presentes, eventos, captura, evoluções, carregamento de save antigo, plugins externos, batalhas e retirada em massa); classificação de todas as espécies autorais via manifesto e demonstração da política em sessão gráfica. Estes pontos **não são considerados completos** nesta fase.

## 3. Como testar no Windows

1. Atualize a `main`, feche o jogo e prepare a [instalação de Kanto no jogo principal](KANTO_ESCOLHA_REGIAO.md) por `KANTO_INSTALAR_NO_JOGO.bat`, se ainda não estiver integrada.
2. Abra `ABRIR_JOGO.bat` e **carregue um save de Decades que concluiu realmente o arco final**. Não conceda as flags manualmente em um save pessoal.
3. Abra o menu de pausa → **Agente de Transporte Regional** ou **Circuito de regiões**. Kanto deve ser jogável e Johto/Paldea ainda aparecerão em preparação, mesmo que uma Liga tenha sido concluída.
4. Confirme a viagem para Kanto. Conferir Pallet, itens, dinheiro, party, PC, Pokédex, esmeraldas e quests.
5. Abra o menu do agente em Kanto, retorne a Decades e confira o ponto exato do retorno.
6. Salve em seu slot original, feche, reabra e faça outra viagem, verificando se posição, origem e histórico persistiram.
7. Tente com um especial na party (com vaga livre no PC), PC cheio e somente especiais/ovos/desmaiados. A viagem não pode apagar ou sobrescrever Pokémon.

**Um save que ainda não terminou Decades não terá acesso a Kanto por viagem**, mesmo com os mapas instalados. Esse jogador ainda pode iniciar *nova partida* diretamente em Kanto pela etapa 04, sem desbloquear Decades antecipadamente.

## 4. Provas automatizadas

- [Teste Ruby do serviço](../tests/region_travel_runtime.rb): ida/volta, tipo especial, reservas de Box, PC cheio, falta de party utilizável, bloqueio de retirada, preservação de `initial`, histórico persistível e rollback após falha.
- [Prova nativa integrada](../scripts/regions/KantoIntegratedCheck.rb): cenário simulado dentro do `Game.exe` **em runner descartável**. O teste pode marcar uma Liga ficticiamente **somente no runner** para verificar a transferência antes de Kanto ter sua Elite Four; isso nunca altera um save pessoal nem concede insígnias na campanha.
- [GitHub Actions do piloto](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/workflows/kanto-pilot-check.yml).

## 5. Critério de fechamento da etapa 05

- [x] Serviço central de ida/volta publicado e integrado ao plugin Blue.
- [x] Bloqueios de Liga/mapa e cálculo preventivo de slots e equipe.
- [x] Testes Ruby de rollback e preservação do estado do save.
- [ ] Prova nativa da viagem física Kanto↔Decades aprovada no GitHub Actions.
- [ ] Teste interativo Windows: posição, telas, equipe, PC, salvamento e retorno.
- [ ] NPC físico em local pós-Liga auditado, com script chamando o serviço central, sem interferir no encerramento.

**Até os três últimos itens serem concluídos, a fase 05 permanece em validação e não altera a barra de 1/16 etapas aceitas.**
