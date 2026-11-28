# AD04 — validação e entrega futura, Windows e Android

Esta fase só define o que deverá ser provado quando houver autorização
de implementação. Uma passagem verde de Markdown não significa mapa
jogável, pacote publicado, nem QA física.

| Prova | Teste futuro | Falha que impede promoção |
|---|---|---|
| T01 | Conferir origem por mapa, direitos, revisão, hash e escopo; comparar croqui ao [atlas](ALOLA_AD05_ATLAS_VISUAL_E_TILES_KANTO.md). | Mapa doador não aprovado, tile global sobrescrito, ou contexto USUM/SM trocado. |
| T02 | Compilar e caminhar pelo recorte nos dois sentidos, testar cada porta e escada após reabrir. Mostrar marcos da vista sem atalho. | Colisão, transição sem par, entrada em setor não entregue, ou apenas teleporte de QA. |
| T03 | Nova partida e visita, recusa, bag/box cheia, retorno e recarga; prova `ILIMA`, Hala, Tauros e repetição. | Inicial ou esmeralda duplicada, flags de campo/Trial compartilhadas entre regiões, save perdido ou sem saída. |
| T04 | Exercitar pré-requisitos do barco, Mantine Surf e Poké Ride por capítulo e por ilha; simular passagem indevida com montaria de outra região. | Acesso cedo, falsa HM, região anterior quebrada ou requisito externo. |
| T05 | Verificar oito chaves USUM e quatro grandes provas sem esmeraldas extras. A diferença de sete no SM é só referência, não uma regra do Blue. Validar Totem, grande prova, título e defesa separadamente. | Gate de especiais em sete, grande prova duplicando prêmio, defesa repetindo título inicial ou requisito. |
| T06 | Instalação nova e atualização multirregional da versão anterior real, falha sob lock, interrupção, recuperação, reabertura e reaplicação; verificar saves sintéticos e mapas não tocados. | Corrupção, região externa alterada, troca de canal ou instalação manual não prevista. |
| T07 | Windows e Android: mesma revisão funcional, digest do `Blue-Story.exe`, receita Android original por commit exato, prova CI de instalação/atualização, zero assets de terceiros redistribuídos. | Qualquer uma das duas entregas não comprovada, link não publicado ou arquivo incompatível. |
| T08 | QA física futura com o build publicado, save representativo autorizado e passos do recorte. | Não falsear prova física: marcar `BLOCKED_ENV` ou, se adiada pelo usuário, `DELIVERED_WITH_QA_PENDING` com teste pendente. |

Os oito casos estão `NOT_RUN`. Validar primeiro o lote correto; em falha,
corrigir e repetir na mesma fase, reportar a trava relevante e continuar
trabalho independente sem publicar fase parcial.

## Contrato de entrega por lote jogável futuro

1. Conferir main, SHA integral do PR, caminhos permitidos, IDs/flags
   e regressões que protegem as regiões publicadas. Sem duplicar engine,
   fonte de jogo, instalador ou canal.
2. Dar merge só com evidência exata, então obter o SHA funcional da
   main. No Windows, validar o instalador `Blue-Story.exe` e seu digest,
   não só o processo que monta o executável.
3. No Android, o atualizador existente baixa a origem certa e verifica o
   SHA-256 antes de instalar localmente. Conteúdo de autoria própria
   segue a receita do repositório; qualquer insumo externo exige revisão
   por componente e origem provada. Não redistribuir pacote de doador,
   mapas, cache, save, runtime ou ZIP geral; não trocar de canal nem
   pedir para reinstalar por conveniência.
4. Acompanhar no GitHub Actions até concluir; se der erro, corrigir e
   repetir só o necessário. Avisar achados que travam o fluxo e entregas
   verificadas. Divergência Windows/Android é `BLOCKED_RELEASE`.
   Só avançar ao próximo lote jogável depois das duas entregas.
5. Guardar URLs, SHA do produto, SHA da receita, workflows/resultados,
   aparato utilizado, diferenças observadas e teste físico pendente.
   Referências: [roadmap de publicação de Kanto](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md),
   [instalação pela fonte](ANDROID_INSTALACAO_PELAS_FONTES.md),
   [atualização incremental](ANDROID_ATUALIZACOES_INCREMENTAIS.md).

A documentação não dispara publicação nem exige que Gabriel teste hoje.
