# Johto — Fase 04: gerar insumos privados para construir o primeiro trecho jogável

**13/11/2026 — entrega de infraestrutura.** Objetivo: obter os dados de interiores, mapas nativos e gráficos necessários à montagem de New Bark, sem publicar arquivos da base Decades. **Fases jogáveis: 0/13. Fases testadas no Game.exe: 0/13.**

## Por que é necessário

O ZIP `Remastered Kanto Johto Map Packv1.zip` foi auditado: há o exterior `Map079` de New Bark Town e a conexão real de borda para a Rota 29, mas faltam quarto 2F, casa 1F, laboratório de Elm, sprites, eventos instalados e o jogo `game/` nativo para validar colisões. A cópia isolada só pode usar MapIDs de destino livres no próprio Blue/Decades. A documentação anterior aponta quatro fachadas candidatas do exterior; **não aprovar portas ou identidade da casa a partir delas sem verificação visual e teste**.

O projeto já tem `JOHTO_PREPARAR_PRIMEIRA_FASE.bat` para preparar terreno/conexões e `JOHTO_PREPARAR_NEW_BARK.bat auditar|montar` para examinar templates locais e compor três interiores de rascunho. O novo exportador facilita fornecer os arquivos nativos indispensáveis a essa validação.

## Como preparar o ZIP no Windows

1. Atualize o repositório (`git pull origin main`) e confirme que o jogo Blue/Decades está instalado em `game/` local, junto do `Game.exe`.
2. Execute `JOHTO_EXPORTAR_BASE_PILOTO.bat` na raiz do projeto. Para incluir também sprites de personagens/treinadores, use `JOHTO_EXPORTAR_BASE_PILOTO.bat sprites` (pode aumentar muito o arquivo).
3. Localize `.blue-work/johto-pilot-inputs.zip` e anexe **somente à conversa privada** para auditoria da Fase 04. **Não coloque esse ZIP ou os dados extraídos no GitHub**; imagens e mapas nativos podem pertencer a terceiros.
4. Opcionalmente, no seu PC mantenha o ZIP original do mapa v1 em `.blue-work/johto-source/original.zip` e execute `JOHTO_PREPARAR_PRIMEIRA_FASE.bat`; após preparar o stage, execute `JOHTO_PREPARAR_NEW_BARK.bat auditar`, revise o JSON em `.blue-work` e só use `montar` quando os três templates estiverem efetivamente conferidos.

O exportador copia somente `Data/MapInfos.rxdata`, `Data/Tilesets.rxdata`, `Data/System.rxdata`, `Data/MapNNN.rxdata`, textos `PBS/*.txt` e PNGs `Graphics/Tilesets`, `Graphics/Autotiles`. Com a opção `sprites`, acrescenta `Graphics/Characters` e `Graphics/Trainers`. O ZIP tem manifesto com SHA-256 por arquivo. Bloqueia arquivos inesperados, links simbólicos, tamanho excessivo e sobrescrita. **Não inclui Game.exe, scripts, plugins, variáveis de ambiente ou saves.** O jogo original é somente lido.

## O que faremos com os dados

- Conferir IDs e hashes reais dos mapas e tilesets nativos.
- Auditar e selecionar templates para os três interiores; editar layout/colisões/portas e verificar as quatro fachadas de New Bark.
- Vincular IDs reais e coordenadas aos eventos `mother`, `elm`, `starter` e `rival`, mantendo a conexão de borda New Bark–Rota 29 sem teletransportes duplicados.
- Gerar piloto em cópia isolada, compilar PBS do rival e checar início dentro do quarto, escadas, portas, laboratório, escolha do inicial, caminho até Rota 29 e save/reload.
- Só alterar **Jogáveis para 1/13** com prova de fluxo real no `Game.exe`; **Testadas para 1/13** requer QA nativo completo. Testes automatizados de código, ZIP produzido ou geometria em preview não contam como gameplay.

**Nota:** o ZIP gerado é apenas insumo de auditoria; não carrega o executável e não permite executar Windows/Essentials num ambiente sem o próprio jogo. Direitos dos recursos e autorização de distribuição continuam pendentes.

## Portas, eventos e montagem do primeiro piloto (novo)

Após preparar a geometria em `.blue-work/johto-staging` com `JOHTO_PREPARAR_PRIMEIRA_FASE.bat`, execute `JOHTO_PREPARAR_NEW_BARK.bat auditar`. O relatório recomenda **três templates de interiores**, mas não os aprova automaticamente. Revise em `.blue-work/johto-interior-templates-review.json` os três mapas-base distintos, dimensões, tilesets, IDs livres e hashes. Depois execute `JOHTO_PREPARAR_NEW_BARK.bat montar` para gerar `.blue-work/johto-staging-interiors` e o template de eventos ligado aos MapIDs reais.

Agora existe o comando **`JOHTO_VERIFICAR_PRIMEIRO_PILOTO.bat`**. Ele valida os **12 eventos** (`mother`, `elm`, `starter`, `rival`, escadas e portas), **o spawn do quarto 2F**, sprites, coordenadas de chegada e conexão de borda New Bark–Rota 29 em PBS. Seu relatório `.blue-work/johto-phase04-acceptance.json` lista cada problema com o nome do evento. Mesmo com PBS correto, **as portas não são presumidas passáveis**: coordenadas/chegadas e sprites internos precisam de revisão. O modo de conexão real dispensa os 2 warps artificiais de borda, que são eliminados na cópia pelo montador existente.

Quando o arquivo `.blue-work/johto-new-bark-bound.json` estiver com as posições dos eventos confirmadas e o relatório não apontar pendências, execute **`JOHTO_MONTAR_PRIMEIRO_PILOTO.bat`**. A nova rotina repete a verificação (independe de uma declaração de sucesso editada) e chama `pilot_johto.py` para criar apenas `.blue-work/johto-pilot/`. O jogo original, os saves e o menu principal permanecem intactos. **Não iniciar no original:** testar exclusivamente `.blue-work/johto-pilot/Game.exe`.

**Critério para 1/13:** iniciar no quarto 2F, descer, conversar com a mãe, entrar/sair do laboratório, falar com Elm, escolher Chikorita/Cyndaquil/Totodile, testar rival/PBS quando liberado, atravessar New Bark–Rota 29, voltar, salvar e recarregar no Game.exe da cópia. Sem essa prova, as barras ficam em **Jogáveis 0/13** e **Testadas 0/13**, mesmo que o relatório retorne `READY_FOR_ISOLATED_ASSEMBLY_NOT_PLAYABLE`.

Testes de regressão sem assets externos: `python -m unittest discover -s tests -p 'test_johto_first_playable_readiness.py' -v`. Testar uma rotina em dados sintéticos não certifica game nativo.