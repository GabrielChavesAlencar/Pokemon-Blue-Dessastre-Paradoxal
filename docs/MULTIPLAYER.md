# Multiplayer do Hub de Batalha

Dois jogadores, cada um no seu `Game.exe`, lutam com os times que montaram em **MEU TIME**. A batalha é a mesma do modo contra a IA: mesmas animações, menus, regras e geração Dessastre Paradoxal.

## Como jogar

**Quem cria a sala**

1. Monte **MEU TIME** e escolha o formato: individual ou dupla. Duplas exigem seis Pokémon e usam a escolha de quatro.
2. Clique em **MULTIPLAYER → Criar sala (este PC hospeda)** e digite seu nome.
3. Passe o **código** e o **endereço** da tela para o outro jogador. Se o Windows perguntar, permita o Python no firewall.

**Quem entra**

1. Monte **MEU TIME**. A sala define o formato e as mecânicas (Mega, Z-Move, Terastal, Dynamax): valem as opções de quem criou.
2. Clique em **MULTIPLAYER → Entrar na sala de outro jogador** e digite nome, endereço e código.

Ao terminar, os dois voltam ao montador com os times preservados. No menu da batalha, **Fugir** vira **desistir**, com confirmação. O adversário vence.

## Como conectar pela internet

O servidor roda no PC de quem cria a sala, sem custo e sem conta. Ele usa a porta **8793 TCP**.

| Situação | O que fazer | Endereço a usar |
|---|---|---|
| Mesma rede/Wi-Fi | Nada além de permitir no firewall | `192.168.x.x` mostrado na sala |
| Internet, com VPN (mais fácil) | Os dois instalam [Radmin VPN](https://www.radmin-vpn.com/) ou Hamachi e entram na mesma rede | `26.x.x.x` (Radmin) ou `25.x.x.x` (Hamachi) |
| Internet, sem VPN | Quem cria abre a porta 8793 TCP no roteador | IP público de quem criou |

Também dá para deixar um servidor separado no ar com `python scripts/battle_lab/mp_server.py`. O botão **Criar sala** ainda não usa um servidor externo: isso seria o próximo passo para jogar só com o código, sem VPN.

## Como funciona

Os dois jogos simulam a mesma batalha a partir de uma semente sorteada pelo servidor, e a rede só transporta as decisões. É por isso que as animações e as mecânicas especiais aparecem iguais nos dois lados, sem transmitir a tela.

- **Decisões escondidas:** o servidor só revela a escolha de um jogador quando o outro também escolheu.
- **Conferência a cada turno:** cada jogo envia um resumo do estado (HP, status, atributos, itens, PP, campo). Se os resumos diferirem, a partida para **sem vencedor**, em vez de seguir com dois resultados diferentes.
- **Mesma versão:** os dois jogos comparam plugins, PBS e scripts. Versões diferentes não entram na mesma sala.
- **Só os escolhidos:** em duplas, o outro jogo recebe apenas os quatro selecionados; os dois de fora ficam no servidor.

Arquivos: `mp_server.py` (salas e sincronização), `mp_client.py` (rede fora do jogo, para a tela não travar) e `Multiplayer.rb` (botão, sala e batalha), todos em `scripts/battle_lab/`.

### Limites conhecidos

- Testado com duas janelas no mesmo PC (individual, dupla, Mega, Dynamax, desistência e jogo fechado no meio da luta). Ainda faltam uma partida entre dois computadores e testes específicos de Terastal e Z-Move.
- Cada jogo tem o time completo do adversário em memória durante a luta, como é normal nesse modelo. Um jogo modificado poderia ler esses dados. O servidor não valida dano, então isto serve para jogar entre amigos, não para ranking.
- O tráfego é HTTP sem criptografia e as salas ficam só na memória do servidor. Se quem criou a sala fechar o jogo, a partida termina.
- Regras de saída: 3 minutos sem decidir ou 45 segundos sem conexão dão vitória ao outro jogador.

## Testes

`python -m unittest tests.test_online_multiplayer` testa o servidor e o cliente sem precisar do jogo.

`python tests/multiplayer_e2e.py --format double --seeds 1 2 3` abre duas janelas reais do jogo, faz as duas lutarem sozinhas pelo servidor local e compara o estado de cada turno. Precisa do jogo instalado.
