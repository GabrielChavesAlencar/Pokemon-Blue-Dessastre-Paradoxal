# Próximos passos do Hub — 1 de novembro de 2026

Solicitação de referência: `proximospasso.txt`, fornecido pelo autor nesta data.

## Avaliação da etapa

Não há acesso ao saldo de tokens/créditos da conta pelo ambiente do projeto. Não é possível calcular honestamente quantos tokens ainda estão disponíveis, nem converter o tamanho de uma funcionalidade em um custo exato. A separação abaixo considera o tamanho do trabalho e a possibilidade de concluir testes e publicação nesta entrega.

| Pedido | Etapa | Critério de conclusão |
|---|---|---|
| Seleção de quatro entre seis, em duplas | Offline atual | Tela nativa, ordem de entrada, jogador e IA com quatro; equipes de seis preservadas |
| Cronômetro de 60 segundos | Offline atual | Relógio monotônico; ao expirar, exatamente os quatro primeiros, inclusive após seleção parcial |
| PokéPaste Champions | Offline atual | Escolha explícita de formato, conversão, ajuste para 510 EVs mostrado na prévia |
| Raichu Mega Y | Offline atual | Raichu normal, Raichunite Y equipada, transformação disponível durante a batalha |
| Todos no nível 50 | Offline atual | Editor sem campo de nível; importação, sessão carregada e equipes de batalha normalizadas |
| Abertura e música | Atual | Iron Maeltrom, raios azuis animados, subtítulo Dessastre Paradoxal e faixa de Gym Leader já instalada |
| PvP online | **Preparação experimental iniciada; partidas futuras** | Dois clientes independentes jogam uma batalha sincronizada, com seleção e tratamento de desconexão |

O Hub desta entrega é **offline contra a IA**. Não existe um botão que prometa PvP sem infraestrutura funcionando. As regras implementadas de duplas são as solicitadas: seis inscritos, quatro selecionados, dois em campo e nível 50. Isso não aplica automaticamente uma lista de banimentos de torneio oficial aos Pokémon autorais.

## PvP online: entregas futuras

### Progresso da primeira etapa

O [experimento isolado de online](ONLINE_EXPERIMENTAL.md) já implementa salas por código, identificação de versões, validação de equipes, seleção de quatro com prazo imposto pelo servidor, reconexão por token e cancelamento. A demonstração com dois clientes HTTP passou usando o catálogo real da instalação. O servidor ainda informa `battleAvailable: false`; o fluxo termina na preparação da sala, sem uma partida PvP.

A prova opcional da engine conseguiu terminar batalhas automáticas individuais, uma dupla de quatro contra quatro e um caso com espécie autoral usando uma cena sem interface de batalha. Foram necessários adaptadores de apresentação para plugins que consultam sprites ou fecham diálogos mesmo sem animações. Esses adaptadores ficam somente no experimento; os plugins existentes não foram editados. O runtime Windows e a inicialização gráfica ainda são necessários. Controle dos turnos pelos dois jogadores e mecânicas especiais na execução sem interface continuam pendentes.

Os arquivos principais do offline foram comparados com a main anterior, e as regressões existentes continuam sendo executadas. O plugin opcional é removido após a prova; o instalador e os atalhos normais não o instalam.

### Trabalho restante

**Avanço do protocolo 2:** a resolução autoritativa já recebeu comandos de dois clientes HTTP e concluiu partidas nativas, inclusive uma com Cavefang. Golpes/alvos, trocas, substituições e reenvios foram exercitados. Detalhes e comandos estão em [Online experimental](ONLINE_EXPERIMENTAL.md). Isso conclui a prova do caminho de decisões remotas, não a entrega da interface PvP no Hub; salas, animações e mecânicas ainda precisam ser integradas.

1. **Provar a execução de uma batalha remota.** Definir um servidor que possa manter o estado de uma batalha da engine; avaliar um processo dedicado de Essentials sem interface de jogador. Verificar o suporte da engine antes de escolher hospedagem. O portal Vercel existente não fornece essa execução automaticamente. Se for necessário outro simulador, comparar suas mecânicas com as espécies e habilidades deste projeto antes de adotar uma alternativa.
2. **Definir protocolo e validação.** Versionar regras, catálogo, Pokémon, golpes e habilidades. Validar times e comandos no servidor; detectar clientes com versões incompatíveis. Manter aleatoriedade e resultados sob autoridade do servidor, sem aceitar dano calculado por um cliente.
3. **Salas por código e prévia.** Criar/entrar em sala, identificar os dois participantes, transmitir apenas os dados permitidos e confirmar equipes. O servidor deve impor os 60 segundos de cada jogador, os quatro primeiros no timeout e os quatro integrantes em batalha. Reaproveitar a tela nativa de seleção desta entrega.
4. **Sincronizar a batalha.** Enviar decisões, validar golpes e trocas, resolver turnos em uma ordem única e reproduzir as animações em ambos os jogos. Definir reconexão, abandono, término da partida e limpeza de salas. O tempo de escolha de golpes permanece uma decisão futura; os 60 segundos pedidos aqui são da seleção inicial.
5. **Validar entre dois computadores.** Testar batalhas completas, Megas, Pokémon autorais, dupla, escolhas simultâneas, cancelamento antes de começar, perda de rede, versão divergente e tentativas de repetir comandos. Só então disponibilizar o modo online no menu e documentar a hospedagem.

O PvP é a parte de maior esforço e não foi considerado concluído por existir esta lista. Não há servidor contratado, custo de hospedagem assumido ou credencial criado nesta etapa.

## Conversão Champions adotada pelo autor

O autor escolheu converter para EVs clássicos, ajustar ao limite de 510 e informar a diferença. Para nível 50 e IVs 31, o primeiro ponto corresponde a quatro EVs e cada ponto adicional a oito: `0 → 0`, `1 → 4`, `32 → 252`. Se a soma ultrapassar 510, a redução começa pelo menor investimento, preservando os maiores quando possível. Por exemplo, `32/32/2 → 252/252/6`, com aviso da redução de seis EVs na prévia. A equivalência de atributos não é garantida para distribuições ajustadas ou IVs diferentes de 31.

Um texto sem identificação não permite distinguir com certeza `32 EVs` de `32 pontos`. A importação detecta essa possibilidade e pede a escolha entre Champions e EVs clássicos antes da confirmação do time. Exportação e biblioteca usam os EVs clássicos resultantes, evitando reconversão silenciosa ao carregar uma sessão.

Referência técnica: [cálculo de atributos Champions no Pokémon Showdown](https://github.com/smogon/pokemon-showdown/blob/master/data/mods/champions/scripts.ts).

## Música da abertura

Faixa solicitada: `60 - Battle! (Gym Leader).mp3`. A instalação local já contém a mesma faixa em `game/Audio/BGM/BlueRandom/gym/f5443af556688de93a1fa79f.mp3` (SHA-256 `f5443af556688de93a1fa79fb274e4a31e6374e77aa10ff01de04fc51b99ce52`). O código reutiliza esse arquivo. O MP3 particular continua fora do Git e do ZIP; instalações sem ele usam a música padrão da base até importarem a faixa.
