# Johto — 05/12 OFFLINE: casa do jogador (1F) em New Bark

**Entrega: 13/11/2026.** O código da etapa fica na `main` após integração do PR; os RXDATA/PNG privados continuam fora do repositório. **Sem executar o `Game.exe`.**

## Entrega

O gerador `scripts/regions/build_johto_home1f_v1.py` transforma a **sala provisória Map675** da prévia de 77 mapas no primeiro andar autoral da casa do jogador. **Não clona o layout de um Centro Pokémon**: constrói uma grade nova RMXP **16×13×3** usando os tiles de `Inside.png` do Decades. Não contém eventos executáveis, transferência de mapas, músicas estrangeiras ou scripts de origem.

### Móveis e setores

- Cozinha: armários, pia e fogão no canto superior esquerdo.
- Mesa de jantar e cadeiras na área central, aparador para TV.
- Sofá/assentos na parte inferior esquerda.
- Planta decorativa.
- Escada visual na área inferior direita, sem warp nesta etapa.
- Porta visual na parte inferior, sem evento de transferência nesta etapa.
- Espaço livre para o NPC **mãe**, cuja fala será ligada na etapa **08/12**.

### Propostas de coordenadas (não verificadas no motor)

| Elemento | Tile (x,y) | Situação |
|---|---|---|
| Aproximação da escada | (11,9) | Caminho estático livre, sem warp |
| Ponto de chegada descendo do 2F | (11,8) | Candidato, sem transição real |
| Aproximação da porta para New Bark | (7,9) | Candidato, sem warp |
| Ponto de chegada vindo da cidade | (7,8) | Candidato, sem transição real |
| Posição da mãe | (6,8) | Candidato, sem NPC/evento |

**106 tiles conectados no teste de flags estáticas do tileset real**, partindo da posição de chegada do 2F. Isso valida somente os dados de tiles, **não** colisões da engine, porta funcional ou comportamento do NPC.

### Validação realizada com RXDATA nativo

- Fonte privada: `.blue-work/johto-staging-bedroom-v1`, com quarto 2F Map674 já gerado na etapa 04.
- Saída: `.blue-work/johto-staging-home1f-v1`, em pasta nova, preservando a entrada.
- Recriado em **Ruby Marshal** e reaberto sem erros: `Data/Map675.rxdata`; no experimento com os dados nativos fornecidos, SHA-256 = `c63e3a262f1536b2d3359036c1a29f2678c9c9ff898b0604e3de6c3abc7e2347`.
- Auditoria comparativa confirma **somente Map675 alterado**; outros 76 MapNNN, `MapInfos.rxdata` e `Tilesets.rxdata` permanecem byte a byte iguais ao staging de 4/12.
- O gerador Python no GitHub monta o mesmo blueprint em cópia isolada, usa `stage.serialize` para roundtrip de Ruby Marshal e valida o staging com `verify_johto.inspect`. O hash do arquivo Python pode variar em relação à serialização Ruby; conferir o manifesto da saída.
- `tests/test_johto_home1f_v1.py`: **6 testes unitários offline** validados: grade/tabelas; objetos; coordenadas e caminho; piso bloqueado; tabela malformada; tileset insuficiente.

### Uso em uma instalação local atualizada

Com `game/` nativo disponível e as prévias anteriores já geradas de forma auditada (tudo sob `.blue-work/`):

```powershell
python scripts/regions/build_johto_home1f_v1.py
python -m unittest discover -s tests -p "test_johto_home1f_v1.py" -v
```

**O comando não abre Game.exe, não escreve em game/, não altera saves, Kanto, Decades ou Hoenn e rejeita sobrescrita de uma saída existente.** O ZIP contendo a prévia com os RXDATA nativos foi entregue apenas no chat privado.

### Instalação automática ainda PENDENTE

O instalador `Blue-Story.exe` **ainda não chama** esse gerador, e o jogo principal **ainda não recebe Map675** em uma atualização automática. Ao integrar Johto de forma jogável, será necessário orquestrar a obtenção das fontes autorizadas, alocação segura de IDs, geração dos três interiores, compilação dos eventos em cópia isolada, testes de integridade e instalação/atualização com backup. Esse requisito faz parte do aceite final do ciclo; não declarar que a instalação pelo site já está pronta.

## Barras de progresso

| Barra | Progresso |
|---|---|
| **Desenvolvimento OFFLINE** | **5/12 (41,7%)** |
| **Fases JOGÁVEIS no EXE** | **0/13** |
| **Fases TESTADAS no EXE** | **0/13** |

**Próxima etapa: 06/12 — laboratório do Professor Elm**, também com layout próprio, três Poké Bolas visíveis e posições de NPC, sem executar a engine. Conexões da escada, porta e eventos efetivos serão tratados nas etapas 07 e 08.
