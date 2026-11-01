# Primeira etapa do online — experimento separado

## Avanço: comandos remotos autoritativos (protocolo 2)

O novo experimento em `scripts/online/turns.py`, `turn_service.py` e `TurnBridge.rb` liga **dois clientes HTTP independentes às decisões da engine nativa**. Golpes, alvos, trocas voluntárias e substituições após desmaio são oferecidos/validados pelo servidor e validados novamente pelo motor. O cliente não pode enviar dano, HP ou vencedor. A preparação de salas do protocolo 1 abaixo continua independente e compatível.

Foram concluídas duas provas reais: dupla 4×4 com Pikachu/Magikarp (40 comandos remotos, 10 turnos) e individual 4×4 com Cavefang/Magikarp (15 comandos, 5 turnos). Ambas tiveram decisões dos dois lados, troca voluntária, substituições, reenvios idempotentes e vitória calculada pela engine. O ambiente isolado preservou a equipe offline e não abriu o save da campanha.

**Ainda não é uma interface PvP no Hub.** Este avanço é a API/prova de resolução remota. O worker é um processo Windows de `Game.exe`, com inicialização gráfica mas sem cena visual de batalha; não é um servidor Linux pronto para deploy. As quatro mecânicas especiais ficam explicitamente desligadas nessa prova. Faltam integrar as salas/seleção do protocolo 1 ao worker, reproduzir as animações nos dois clientes, tratar todas as mecânicas e validar entre dois computadores antes de disponibilizar o botão no Hub. O instalador, o ZIP e os atalhos offline não instalam o worker.

### Repetir a prova

Com o jogo fechado e o catálogo da etapa anterior em `.blue-work/online/catalog.json`:

```powershell
python scripts/online/turns.py --prepare
python scripts/online/turns.py --demo
```

Enquanto a demonstração aguarda, abra `game/Game.exe` em até 120 segundos. Dois clientes enviam escolhas por HTTP, incluindo uma troca voluntária; o jogo encerra ao terminar. Confira `game/Data/blue-native-turns-validation.txt` (`RESULT=PASS`) e `.blue-work/online-turns/http-validation.json`. O demo usa uma dupla de quatro escolhidos entre seis. Para outra equipe, `--prepare --teams caminho.json` aceita `format` (`single`/`double`), `teams` (duas equipes de seis no contrato 1) e `picks` (duas seleções ordenadas de quatro). Espécies, habilidades, itens, golpes, Nature e IVs/EVs são validados contra o catálogo; o formato continua livre quanto a learnsets competitivos.

Ao terminar e fechar o jogo:

```powershell
python scripts/online/turns.py --cleanup
python scripts/launch_game.py --prepare-only
```

A limpeza remove apenas os três arquivos conhecidos do plugin experimental e o pedido de execução, recusa arquivos inesperados e preserva o cache antigo em backup para forçar uma recompilação sem o worker. Os relatórios permanecem locais. Nunca publique `.blue-work/online-turns/session.json`: contém os tokens dos dois lados para o servidor experimental.

### API de comandos

Para manter o transporte aberto, use `python scripts/online/turn_service.py --session .blue-work/online-turns/session.json`. O endereço padrão é `127.0.0.1:8792`; `--host 0.0.0.0 --lan` deve ser escolhido explicitamente para uma prova em rede local. Não abre portas do roteador, não muda firewall e não faz deploy.

| Operação | Contrato |
|---|---|
| `GET /v2/hello` | Versão, compatibilidade e limites explícitos: sem UI no Hub, mecânicas especiais desligadas |
| `GET /v2/state` | Estado público; opções legais pendentes apenas do próprio lado |
| `POST /v2/command` | Somente `{"seq": 1, "option": 0}`; índice da opção oferecida pela engine |

Estado e comando exigem Bearer token do lado e `X-Blue-Compatibility` igual ao fingerprint da sessão. O índice do Pokémon, o alvo e o golpe efetivos vêm da lista autoritativa, não de campos arbitrários enviados pelo cliente. Repetir o mesmo comando é idempotente; modificar uma decisão confirmada, atuar pelo outro jogador, usar índice inválido ou responder a um pedido antigo é recusado. Os tokens e a lista de golpes legais do adversário não aparecem no estado público. O limite atual é 60 segundos por decisão, 30 turnos e 180 segundos totais do worker diagnóstico; timeout cancela com erro, sem inventar um vencedor. Não há reconexão persistente, ranking ou servidor público nesta etapa.

As seções abaixo descrevem o **protocolo 1 de salas e preparação**, com dois clientes independentes. Esse servidor continua retornando `battleAvailable: false`; confirmar equipes encerra a etapa no estado `prepared`. A prova de batalhas remotas agora existe separadamente no protocolo 2, descrito acima; a integração entre os dois ainda está pendente.

O Hub offline, seus atalhos, o instalador normal, o pacote de download e os plugins de batalha existentes não são alterados por esta etapa. O código fica em `scripts/online/`. O teste nativo opcional instala um plugin próprio temporário; nenhum atalho normal o instala ou cria seu pedido de execução.

## O que já funciona

- Criar sala por código e entrar com um segundo participante. A entrada simultânea de um terceiro é recusada.
- Comparar protocolo, regras, catálogo e identificação dos arquivos da engine. Clientes incompatíveis não entram na mesma sala.
- Validar seis espécies/formas base registradas, habilidades, itens, golpes, Nature, nível 50, IVs e limite de EVs. Formas Mega iniciais são recusadas; a espécie base pode carregar sua pedra. A validação desta etapa permite golpes registrados no formato livre do Hub; **não é um validador competitivo completo de learnsets ou torneios**.
- Confirmar quatro integrantes em ordem, com prazo de **60 segundos imposto pelo servidor**. Sem confirmação, entram os quatro primeiros. A escolha já confirmada pelo outro participante é preservada.
- Repetir uma confirmação após falha de rede sem aplicá-la duas vezes. Alterar uma seleção já confirmada é recusado.
- Retomar o estado com o mesmo token, sem ganhar prazo adicional. O indicador de presença considera 30 segundos sem consulta; ele não reinicia a sala.
- Cancelar a sala, expirar sessões inativas e limitar a quantidade de salas. Tokens e os dados privados do time adversário não são retornados na consulta de estado.

As salas existem apenas na memória do processo. Reiniciar o servidor encerra as salas. Não há conta, ranking, persistência ou hospedagem contratada nesta etapa.

## Prova da engine

`EngineProbe.rb` testa a classe nativa `Battle::DebugSceneNoVisuals` em batalhas automáticas de teste. O objetivo é verificar a resolução de uma batalha sem os sprites e menus de um jogador, incluindo dupla de quatro e uma espécie autoral, antes de ligar decisões humanas ao servidor.

A prova passou nos três casos, e a demonstração HTTP com dois clientes passou com o catálogo exportado dessa instalação. O adaptador mantém apenas os indicadores visuais consultados pelos plugins, sem criar sprites ou bitmaps de batalha, e transforma erros do teste em relatório em vez de caixas de diálogo. Há limite de 20 segundos e de 30 turnos para as simulações diagnósticas.

**Limites da prova:** o processo continua sendo o `Game.exe` existente com seu runtime Windows, inicialização gráfica e arquivos locais. Não prova que o jogo já execute num servidor Linux sem display, nem que duas pessoas consigam enviar comandos de turno. As batalhas desta prova usam a IA e desativam as mecânicas especiais. Um servidor de partidas ainda precisa de um adaptador de decisões, isolamento por partida, testes de Megas/Z-Moves/Terastal/Dynamax e reprodução dos eventos nos clientes.

## Executar o laboratório

Feche o jogo antes de preparar o teste opcional. Na pasta do projeto, em uma sessão normal do Windows:

```powershell
python scripts/online/probe.py --only
```

Abra `game/Game.exe` em até 120 segundos. O teste usa o ambiente isolado do laboratório, sem ler ou salvar a campanha. Aguarde o jogo fechar sozinho e confira `game/Data/blue-online-engine-validation.txt`: o resultado deve ser `RESULT=PASS`. `--only` executa apenas a prova; sem essa opção, a prova é seguida pela regressão completa offline.

Depois:

```powershell
python scripts/online/probe.py --finalize
python scripts/online/probe.py --cleanup
python scripts/online/demo.py --catalog .blue-work/online/catalog.json
```

`--finalize` gera o catálogo local com a identificação dos arquivos instalados. `--cleanup` remove somente os dois arquivos conhecidos do plugin de teste e seu pedido de execução; recusa a remoção se encontrar arquivos inesperados. A demonstração abre um servidor temporário no próprio computador, conecta dois clientes HTTP, confirma equipes, verifica o estado final e encerra o servidor. Ela não inicia uma batalha nem modifica times do Hub.

Para manter o servidor de preparação aberto:

```powershell
python scripts/online/server.py --catalog .blue-work/online/catalog.json
```

O endereço padrão é `http://127.0.0.1:8791`. Um experimento em rede local exige `--host 0.0.0.0 --lan` e o uso do mesmo catálogo pelos dois clientes. Nenhuma porta de roteador ou regra de firewall é aberta automaticamente. Os comandos não fazem deploy no portal nem instalam um serviço permanente.

O transporte atual é um laboratório local baseado em [`http.server`](https://docs.python.org/3/library/http.server.html), cuja documentação não o recomenda para produção. Hospedagem pública, HTTPS, persistência e limites operacionais precisam ser definidos antes de abrir o serviço ao público. Os tokens usam o módulo [`secrets`](https://docs.python.org/3/library/secrets.html).

## Contrato do protocolo 1

| Operação | Requisição |
|---|---|
| Capacidades e versão | `GET /v1/hello` |
| Criar sala | `POST /v1/rooms` |
| Entrar | `POST /v1/rooms/{codigo}/join` |
| Retomar/consultar | `GET /v1/rooms/{codigo}` com Bearer token |
| Confirmar quatro | `POST /v1/rooms/{codigo}/select` com Bearer token e `{"picks":[5,0,2,3]}` |
| Sair/cancelar | `POST /v1/rooms/{codigo}/leave` com Bearer token |

Inscrição: `protocol`, `compatibility`, `name` e `team`. A compatibilidade deve ser calculada pelo catálogo local, não simplesmente copiada de um servidor desconhecido. O cliente de teste faz essa comparação antes de entrar.

Cada integrante contém `species`, `ability`, `item` (ou `null`), `nature`, `moves`, `evs`, `ivs` e `level`. `evs` e `ivs` usam a ordem **HP, Atk, Def, SpA, SpD, Spe**. Os índices de seleção vão de zero a cinco. As duas primeiras posições confirmadas serão os iniciais da futura partida.

Este contrato mínimo ainda não transporta todos os detalhes do montador, como sexo, shiny e Tera Type personalizado. O mapeamento completo dos Pokémon precisa ser implementado e versionado antes da integração com partidas reais.

Estados: `waiting → selecting → prepared`, com saídas para `cancelled` ou `expired`. Não existe uma rota de dano, vencedor ou resultado enviado pelo cliente.

## Próxima etapa

Integrar as salas e a seleção do protocolo 1 ao worker de comandos do protocolo 2, depois reproduzir os eventos e animações nos dois jogos. A prova da resolução já passou; a interface, as mecânicas e o teste entre computadores continuam pendentes antes de colocar PvP no menu do Hub. O [roadmap](ROADMAP_HUB.md) mantém os critérios dessa entrega futura.
