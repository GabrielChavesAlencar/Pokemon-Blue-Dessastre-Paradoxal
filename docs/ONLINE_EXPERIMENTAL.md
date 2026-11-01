# Primeira etapa do online — experimento separado

Esta etapa implementa **salas e preparação de equipes por HTTP**, com dois clientes independentes. **Ainda não é possível jogar uma batalha PvP.** O servidor retorna `battleAvailable: false`; confirmar equipes encerra a etapa no estado `prepared`, sem inventar um resultado de batalha.

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

Ligar comandos validados dos dois participantes a uma instância autoritativa da engine, resolver os turnos e enviar eventos para os dois jogos. Só depois de validar uma partida completa entre clientes independentes o modo PvP deve aparecer no menu do Hub. O [roadmap](ROADMAP_HUB.md) mantém os critérios dessa entrega futura.
