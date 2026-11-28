# KD04 — validação, publicação futura e handoff Kalos

Fechamento do planejamento, **sem implementação**. Este documento não
ativa Kalos, não cria workflow de distribuição e não autoriza iniciar
KA00–KA31. A validação desta etapa é apenas documental. Ambas as plataformas deverão usar o mesmo produto. Todos os
cenários de runtime abaixo estão `NOT_RUN`.

## Material de partida

| Entrega | Referência para uma implementação futura |
|---|---|
| KD00 | [Baseline, fronteiras de trabalho e links de CI](KALOS_PESQUISA_E_PLANEJAMENTO.md) |
| KD01 | [Proveniência e direitos, caminho autoral 2D](KALOS_KD01_FONTES_E_DIREITOS.md) |
| KD02 | [Inventário de 16 cidades/vilas, 22 rotas, oito ginásios e progressão X/Y](KALOS_KD02_INVENTARIO_E_PROGRESSAO.md) |
| KD03 | [Primeiro corredor até Viola, grafo, estado e regressões](KALOS_KD03_DESENHO_E_PRIMEIRO_RECORTE.md) |
| KA00–KA31 | [Roadmap de execução futura](KALOS_ROADMAP_CODEX_100_JOGAVEL_WINDOWS_ANDROID.md) |

**Primeira ação autorizável:** numa revisão atualizada, confirmar
autoria das entradas do corredor, inventariar os MapIDs reais e então
preparar um piloto privado de Vaniville → Aquacorde → Santalune/Viola.
Não iniciar por Lumiose, Liga, alocação cega ou um instalador novo.
Mesmo que exista um caminho funcional em outro projeto, não tomar isso
como uma implementação do Blue.

## Contrato de entrega futura em duas plataformas

| Gate | O que comprovar antes de anunciar |
|---|---|
| P01 — produto comum | O SHA funcional **S** trava scripts, mapas, fontes e regras comuns. Registrar CI na revisão exata, baselines efetivamente suportadas e escopo; não usar a release mais recente como prova automática. |
| P02 — Windows | Blue-Story.exe no fluxo principal, sem launcher Kalos separado. Conferir asset publicado na tag de S, tamanho/SHA-256 e revisão realmente instalada. Testar atualização no install existente, instalação limpa, reabertura e recuperação sem arquivos fora do lote. |
| P03 — Android pela fonte | Receita pública com SHA próprio **R** vinculando **S**, origem autorizada e SHA-256 do arquivo, revisão predecessora e manifesto. O atualizador obtém as entradas no lugar indicado e prepara/compila localmente. Publicar só receita/instruções próprias; nenhum ZIP multirregional, patch de jogo, cache ou fonte de terceiros. Separar instalação nova da migração; não trocar o canal de quem já tem jogo. |
| P04 — transação | Fechar o jogo, conferir pasta/versão atual em modo de leitura. Isolar cópia de compilação e saves, validar antes de instalar, comparar inventários e aplicar só arquivos autorizados. Marker de revisão por último; falha reverte. Sem sobrescrever Game.exe/saves ou outras regiões; confirmar reaplicação sem mudanças. |
| P05 — paridade real | Em duas plataformas, testar o mesmo corredor, eventos e retorno físicos, campo, menu, áudio e reabertura. CI, compilação e release são provas diferentes do aparelho. QA física indisponível fica `BLOCKED_ENV`; não elevar barra de jogabilidade. |
| P06 — publicação e avanço | Auditar as duas tags e a qualificação na revisão comum. Um lado ausente, fonte sem direitos, mudança no hash, regressão ou evidência de versão inconclusiva bloqueia próxima entrega jogável. Corrigir o lote atual e rodar só o necessário. |

Modelos existentes, não comandos garantidos de Kalos:
[lançador/instalação Blue](INSTALACAO.md),
[atualização K06 pela fonte](ANDROID_K06_ATUALIZACAO_PELA_FONTE.md) para
instalações existentes, e [instalação nova pelas fontes](ANDROID_INSTALACAO_PELAS_FONTES.md)
para uma pasta nova. O fluxo histórico binário só serve de ponto de
partida quando se provar uma cadeia compatível; não é distribuição de
Kalos. Não recomendar instalar hoje um componente de Kalos: ele não
existe nesta entrega.

## Matriz futura de testes e bloqueios

| Caso | Situação reproduzível | Resultado mínimo esperado nas plataformas aplicáveis |
|---|---|---|
| T01 | Fresh install em pasta vazia; upgrade a partir da revisão predecessora efetivamente publicada. | Kanto/Hoenn e demais registros permanecem válidos; Kalos só aparece se integralmente registrado; versão exibe S. |
| T02 | Origem fora do ar, arquivo truncado, hash divergente ou permissão não comprovada. | Nada instalado; status verificável, origem autorizada preservada; não desativar a verificação. |
| T03 | Interromper entre cópia e compilação e entre primeira gravação e marca final. | Revisão anterior intacta ou recuperação atômica; reaplicar conclui uma vez; nunca usar cache de outra revisão. |
| T04 | Arquivo local modificado, colisão de MapID, pacote parcial/piloto ou disco sem espaço. | Erro claro antes de substituir saves ou arquivo desconhecido; inventário protegido idêntico. |
| T05 | Abrir o jogo normal depois da atualização, compilar, reabrir e repetir update. | Portas, escadas, flags e destinos continuam corretos mesmo que o motor serialize os mapas de novo. |
| T06 | Jogar abertura/Viola e regressões A01–A07 do KD03. | Equipe, badges e progresso legítimos; retorno natural; save/reload; sem reset ou teleporte QA. |
| T07 | JoiPlay em aparelho: toque, áudio, abrir tela de versão, continuar save, atualização e reabertura; Windows equivalente. | Jogabilidade e identificação observadas separadamente; medição e defeitos em recibo sanitizado, sem dados pessoais. |
| T08 | Nenhum pacote Android novo ou falha em paridade entre Windows e Android. | `BLOCKED_RELEASE`: não iniciar outro lote jogável nem anunciar aceitação. |

Registar por caso: S, R (quando aplicável), baseline e versão realmente
instalada, cenário, plataforma e ambiente, passos, esperado, observado,
resultado, data, URL de job/release e hashes relevantes. Guardar somente
recibos sanitizados. Nenhum caso de instalação, gameplay ou publicação
de Kalos foi executado neste projeto documental.

## Entrada e saída do primeiro trabalho posterior

1. Confirmação do mantenedor para **implementar**, além deste pedido
   documental; reavaliar as baselines, direitos e workflow existentes.
2. Evidência de terreno e referências por corredor, análise real de IDs
   disponíveis e plano de rollback. Bloqueios absolutos do primeiro
   corte: autorização de entradas, ausência de colisões e reabertura
   continuando o mesmo save. Não trocar o projeto-base para contorná-los.
3. Entregar só o corte do KD03. Decisões sobre o lendário do clímax,
   equivalentes offline de Friend Safari e detalhes 3D de Lumiose ficam
   no planejamento posterior. Não atrasar o piloto com essas escolhas.
4. Depois dos gates P01–P06, registrar a entrega, publicar evidências e
   repetir o ciclo no corredor seguinte (R04 até o arco Palace/Snorlax).
   O fechamento futuro da campanha exige toda a cobertura do KD02 e os
   gates KA00–KA31, não só o primeiro piloto.

Esta frente termina com o pacote documental validado no GitHub; Kalos
permanece planejada e sem versão jogável publicada.
