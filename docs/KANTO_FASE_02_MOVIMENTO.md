# Kanto — etapa 02/16: movimento físico e verificação da jornada no Windows

**Data:** 12/11/2026. **Status:** prova automática de movimento na engine adicionada; **caminhada visual/controle humano ainda NÃO aceita**. O núcleo funcional da etapa pode avançar pela primeira barra apenas quando a CI Windows executar os passos com sucesso. A segunda barra continua **1/16**, até apresentação de evidências reais de gameplay.

## Por que a auditoria anterior era insuficiente

O projeto já possuía verificações de 142 mapas, 64 destinos de testes, eventos, guerras de badges e ida/volta de portas. Entretanto, verificar que um evento tem `Transfer Player` não garante que o jogador consiga se aproximar da porta com colisões físicas. O novo núcleo acrescenta uma prova no **`Game_Player` real da engine RPG Maker XP/mkxp-z**, usando `passable?(x,y,d)` para detectar passagem e `move_down/up/left/right` para realizar deslocamento efetivo de um tile no mapa. Testa retorno quando permitido.

Os testes são injetados **exclusivamente na cópia descartável de `.blue-work` da CI**; não viram evento do jogo, não concedem insígnias, não modificam o arquivo de save e não são importados ao `game/Game.exe` original. A prova se refere a deslocamento de personagem em **headless**, não a input manual de teclado/joystick nem à renderização.

**Evidência nativa obtida:** a [CI Windows 43272300652](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43272300652) concluiu com sucesso e registrou **16 destinos com passo efetivo do Game_Player**, além de **8 verificações diagnósticas de aproximação às portas**. Os 24 registros não equivalem a 24 percursos de gameplay; o script separa deliberadamente `native_step_verified` de caminhos apenas estimados e de casos não reproduzidos em modo headless. Também foram mantidos os testes de save/reload e Game.exe principal. O usuário ainda precisa validar os eventos no Windows.

## Rotas e eventos prioritários para testes manuais

O usuário já relatou ter visitado Pallet, Route 1/2, Viridian, Viridian Forest, Pewter, lado oeste de Route 4 e Mt. Moon. Isso é evidência parcial de **visita**, não de que todos os comandos, colisões e portas funcionam.

A sequência prioritária de aceitação é:

1. **Casa do jogador, Pallet:** iniciar no quarto superior, mover nas quatro direções, usar escada, sair pela porta; entrar de volta. Também testar casa do rival e laboratório do Oak.
2. **Route 1 → Viridian City:** caminhar sem usar o menu de atalhos; não atravessar obstáculos; verificar encontro selvagem real, batalha/captura e transição de volta.
3. **Viridian:** entrar/sair de ambas as casas, Centro Pokémon e Poké Mart; receber/dar o pacote a Oak; salvar e carregar.
4. **Route 2, portarias, Viridian Forest:** testar portas em ambas as extremidades, bloqueios e treinadores de visão (especialmente Rick), inclusive derrota e vitória única.
5. **Pewter:** Museu pelas duas portas, duas residências, Centro, Mart, Brock; Boulder apenas após vitória real.
6. **Route 3, Mt. Moon e Route 4:** testar escadas por andar, passagem da saída para Cerulean, combates, pedras/itens e ida/volta. A origem observou somente a **parte esquerda** de Route 4, então o trecho leste é prioritário.
7. **Cerulean:** ginásio de Misty, retorno, Cascade Badge, salvar/carregar os flags do local.

Para as fases 08–16, o novo sistema de feedback ainda oferece seções dedicadas a ginásios, Liga, viagem entre regiões/PC e JoiPlay. O teste automático não confere as animações, toques Android, triggers de aproximar NPCs ou os obstáculos físicos de Strength na Victory Road.

## Como executar agora

O novo arquivo **`KANTO_VALIDAR_CAMINHADA.bat`** inicia o mesmo piloto experimental, com saves separados de Decades, e **abre diretamente as perguntas de caminhada após você encerrar o jogo**.

```bat
KANTO_VALIDAR_CAMINHADA.bat
```

Alternativamente, abra `Blue-Story.exe` → `Game.exe` → **Testar Kanto** e, ao fechar o jogo, escolha a seção **caminhada** do formulário local. Não é necessário repetir todos os 16 núcleos para relatar defeitos do trecho inicial.

O formulário apresenta **13 verificações** específicas, com as respostas `S` (passou de verdade), `F` (falhou) e `N` (não testei). Escreva mapa, evento/porta, coordenada aproximada, como reproduzir e resultado esperado/obtido. Os relatórios `.md` e `.json` são gerados em `.blue-work/kanto-gui-reports` **somente no seu computador**.

Para gerar um template não verificado, sem rodar o jogo:

```bat
python scripts\regions\kanto_feedback.py --scope caminhada --no-prompt
```

## Evidências automáticas / limitações

- A prova usa os métodos **reais da engine** `Game_Player`, não o método `move_straight` (inexistente no RPG Maker XP), e verifica a consistência dos passos em locais de chegada registrados pelo piloto.
- A origem Pallet/Quarto precisa de vizinhos transitáveis, e a prova de retorno é executada quando a engine permite.
- O resultado local em `.blue-work/kanto-pilot/Data/blue-kanto-walking-proof.txt` descreve as áreas onde a engine conseguiu se movimentar; carrega a marca `NOT_MANUAL_GAMEPLAY_QA` para impedir falsa certificação.
- Os 142 MapIDs e 45 prévias devem continuar inalterados. O instalador não recebe o script de teste; ele permanece somente na cópia transitória da CI.
- O checklist do usuário **não** é preenchido pelos testes automáticos. O status de Kanto continua `prototype`.

## Critério de aceite

**Barra 1 — núcleo funcional:** prova do deslocamento na engine e CI/regressão verde. A entrega pode contar como núcleo executável, mesmo que não cubra a jornada humana.

**Barra 2 — aceite integral:** **não marcar a etapa 02 como concluída** até revisar relatório **real** de movimento/portas, percurso Pallet–Cerulean, treinadores, batalhas, save/reload e funcionamento no Windows. Correções ainda necessárias bloqueiam esse aceite e o estado `playable`.

Próxima ação recomendada: executar `KANTO_VALIDAR_CAMINHADA.bat` em um computador Windows real e encaminhar os resultados `F` para correção de eventos/tilemaps específicos, sem compartilhar o arquivo de save.
