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
