# Johto — Etapa OFFLINE 04/12: quarto próprio do jogador em New Bark (2F)

**Concluído na prévia privada (13/11/2026).** Não é uma fase jogável, não executa Game.exe e **não** sobrescreve Decades, Kanto ou saves.

## Entrega real

- Implementado `scripts/regions/build_johto_bedroom_v1.py`, que lê a prévia dos **77 mapas** em `.blue-work/johto-staging-interiors`, localiza o símbolo `JOHTO_NEW_BARK_PLAYER_HOME_2F`, mantém seu MapID alocado e **substitui a geometria provisória da cabana por um novo quarto criado por programação**.
- O quarto novo possui **14×11 tiles** (anteriormente eram 40×40 da cabana usada como template). Usa **somente** peças do tileset `Inside.png` já instalado no Blue/Decades, sem copiar NPCs, eventos ou scripts externos.
- Inclui **cama azul**, escrivaninha, armário, janela na parede e **escada visual**. As três camadas de tiles são geradas no formato RGSS `Table`, reabertas/validadas pelo leitor de Marshal da engine do projeto. Nenhum handler/evento é inserido nesta etapa; portas e escada terão seus eventos em 07/12–08/12.
- **Spawn proposto:** (6,7). **Aproximação da escada proposta:** (9,8). Os bits de direção do tileset não bloqueiam esses pontos, e **81 tiles** são alcançáveis no cálculo estático de vizinhança ortogonal. **Isso não substitui colisão nem caminhada no Game.exe:** flags `verified_in_game=false`.
- O executável Python copia **toda** a prévia de 77 mapas para **um destino NOVO** `.blue-work/johto-staging-bedroom-v1`, troca **apenas** `Data/Map674.rxdata` e `johto-stage.json` (no snapshot com IDs 600–676), verifica preservação dos MapInfos/Tilesets e mantém `can_install=false`, `not_playable=true`.
- No pacote privado gerado a partir dos dados enviados pelo usuário, a serialização nativa Ruby passou no roundtrip; arquivo final `Map674.rxdata` SHA-256 `1ffc5cb06d2350307615ffff4569b1571a991c3177985c6d1ffd9ecc11a4ccf4`. O SHA exato pode mudar se a implementação Python serializar os mesmos dados com outra representação Marshal válida; o relatório do gerador fixa o próprio resultado.

## Comprovação dos testes

`tests/test_johto_bedroom_v1.py` valida **5 cenários automatizados**:

1. Tabela RMXP de 14×11×3, sem eventos importados e sem alegar jogo testado.
2. Presença da cama, mesa, escada e layout **diferente** do template 40×40.
3. Alcance geométrico do ponto de spawn até a escada; coordenadas ainda não aprovadas no motor.
4. Rejeição de piso bloqueado pelos bits de direção do tileset.
5. Rejeição de dados RMXP malformados/índice de tile fora da faixa.

**Os cinco testes passaram localmente.** A prévia RXDATA verdadeira também foi salva e reaberta com Ruby Marshal sem erros. A imagem de prévia e o pacote RXDATA foram entregues de forma privada ao proprietário; **nenhum recurso nativo foi commitado no GitHub**.

## Como gerar sem executar o jogo

Na raiz do projeto, tendo instalado `game/` e extraído o ZIP privado anterior somente em `.blue-work/`:

```powershell
python scripts/regions/build_johto_bedroom_v1.py
python -m unittest discover -s tests -p "test_johto_bedroom_v1.py" -v
```

O comando recusa sobrescrever qualquer preview existente. A prévia de origem precisa ser a versão geométrica auditada dos 77 mapas: a rotina não tenta produzir a fonte original nem aprovar conteúdo de outros autores. O `Game.exe` original não é iniciado.

A imagem privada do quarto deixa visíveis o posicionamento da cama, escrivaninha, armário, janela e escada com os dois pontos candidatos destacados. **Não instalar diretamente o stage sobre `game/`.** O marcador de eventos `.blue-work/johto-new-bark-bound.json` existente da fase anterior ainda aponta ao SHA do **antigo** Map674; deve ser regenerado/atualizado em prévia após a fase 05–07, quando o resto dos interiores e posições estiverem acertados.

## Barra mantida independente

- **Desenvolvimento OFFLINE: 4/12 = 33,3%.**
- **Fases JOGÁVEIS: 0/13.**
- **Fases TESTADAS em Game.exe: 0/13.**

**Próxima etapa offline 05/12:** criar a casa 1F compatível com o quarto novo, depois vincular a escada de forma reversível. A prova real de escada, colisão, spawn e save fica para testes Windows posteriores.