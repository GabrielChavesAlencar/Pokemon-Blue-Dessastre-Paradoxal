# Johto — correção de mapas reais do Blue-Story (16/11/2026)

## Origem verificada

A instalação local do usuário foi diagnosticada por `JOHTO_DIAGNOSTICO_MAPAS.zip`, contendo somente `Map600.rxdata`, `Map674.rxdata`, `Map675.rxdata` e os detalhes, **sem saves**. O ZIP foi analisado sem avaliar scripts Ruby. O pacote privado offline-12 continua com SHA-256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49`.

| Arquivo | SHA-256 observado no Game.exe | SHA-256 do manifesto antigo |
| --- | --- | --- |
| Map600.rxdata | `45f3d9060f28890edaa7146ca91d887b76a08b0067cf79197015dd665d6c3397` | `4b7a49f8b4a351214bec3c11dbc0b3b2d6b241c47083716dd8f546c4f692b4d6` |
| Map674.rxdata | `8d837d343087eec13927e601ff3d506c1cb3bbaae696c90211b91111814e12b7` | `4898d06ad5bc6f17a72fa24a5188781b2fda7c0a31643bdaa9da18970318fe0f` |
| Map675.rxdata | `71fa3e6c22a87f6dd2f4ddab0538f9f33586e5cc979a9891b24f9d259e9469c3` | `0d60e2f4e24113094e3b4715b418fa35fe5db6375b3324f9c5464f247f1e9fd8` |

As diferenças de hash não significam automaticamente corrupção. Os 3 arquivos são mapas RMXP interpretáveis. O `Map600` contém entradas da casa do jogador, laboratório do Elm, guardas, Silver e placas. O `Map674` contém o evento `JH_HOME2F_TO_1F` na posição (9,8) e `JH_NEW_GAME_PROFILE` na posição (6,7). O `Map675` mantém a mãe e as portas.

## Causa concreta do reparo recusado

O jogo acrescentou uma sequência de animação à transferência. O evento não começa com `Transfer Player = 201`:

```
250 — Play SE (Exit Door)
223 — Screen Tone
106 — Wait
201 — Transfer Player (destino)
223 — Screen Tone
0   — fim do evento
```

O reparo anterior erroneamente validava `@list[0].@code == 201`, recusando a sequência com som e fade embora a transferência fosse válida.

## Alterações implementadas

1. `johto_visual.py`: procura **exatamente um comando 201** em toda a lista de comandos das páginas do evento, mantém som, fade e wait intactos e muda somente coordenadas da escada e do retorno. Não remove `JH_NEW_GAME_PROFILE`, mãe ou NPCs.
2. `johto_main_preview.py`: aceita **somente o par exato de hashes de Map674/Map675** do diagnóstico real para o reparo específico, além dos hashes originais; edições desconhecidas continuam sendo recusadas. O reparo reserializa os dois mapas, faz backup, atualiza os hashes deles no manifesto e permite rollback se houver falha.
3. `runtime_semantic_preview`: o instalador deixa de concluir que Johto não existe simplesmente por um hash antigo de mapa. Ele exige pacote/marcador privado confiáveis, os 100 mapas RMXP com dimensões/tabelas/tilesets/eventos coerentes, registradores e plugin de Johto. Relata os MapIDs com drift, sem apagar ou reimportar dados de outras regiões. **Isso não certifica jogabilidade dentro do Game.exe**.
4. `auto_integrate_johto.py`: tenta recuperar automaticamente a instalação experimental com alterações do runtime, atualizar o quarto e registrar status `experimental_installed_runtime_modified_not_native_tested` (somente quando os 100 mapas passam na validação estrutural). Não reinstala o ZIP ou sobrepõe saves.
5. `diagnose_johto_bedroom.py` e `VERIFICAR_QUARTO_JOHTO.bat`: reconhecem eventos cujo código 201 vem depois de som/fade e oferecem fallback manual seguro.

## Instalação

1. Fechar `Game.exe` e Blue-Story; atualizar o Blue-Story de https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/tag/blue-story-windows.
2. Rodar Blue-Story para atualizar o projeto; ele tenta recuperar a Johto detectada, **sem pedir o ZIP original novamente**.
3. Se a recuperação geral for bloqueada por outros mapas, rodar `VERIFICAR_QUARTO_JOHTO.bat` na pasta gerenciada `%LOCALAPPDATA%\\PokemonBlueDessastreParadoxal`. A correção de quarto autorizada por SHA não precisa dos PNGs externos.
4. Verificar `.blue-work/johto-main-install-status.json` e `.blue-work/johto-bedroom-diagnostic.json`. Se persistir `existing_install_needs_review`, enviar o status e o primeiro MapID/erro, **não copiar arquivos de mapa manualmente**.
5. Abrir `game/Game.exe` da mesma pasta e confirmar escada no lado esquerdo, descer/subir, sair para New Bark, save/load, Elm e progresso.

**Atenção:** os novos gráficos HGSS externos Akizakura16/DonLawride não fazem parte deste reparo. A mudança de layout usa os tiles já instalados; o visual totalmente fiel requer PNGs originais e permissões adequadas.

## Testes

O CI `Johto - snapshot para teste privado da integracao` inclui testes sintéticos para som/fade/wait + transferência, atualização idempotente com rollback, mudança de mapas no runtime, validação dos 100 mapas, e preservação de Kanto/Hoenn/saves. O ZIP do usuário foi inspecionado para descrever exatamente esses comandos, porém o Game.exe real no Windows **não pode ser executado neste ambiente**.
