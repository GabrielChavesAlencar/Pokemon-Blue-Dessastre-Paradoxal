# PD04 — validação e entrega futura de Paldea

Critérios para quando a implementação for autorizada, não prova
de que algum mapa já roda. A CI desta fase é só documental.

| Prova | Cenário futuro | Falha bloqueadora |
|---|---|---|
| T01 | Revisar [fontes](PALDEA_PD01_FONTES_E_DIREITOS.md) e [atlas](PALDEA_PD05_ATLAS_VISUAL_E_TILES_KANTO.md), direitos, arquivo, SHA-256, croqui e equivalência de tiles. | Fonte/mapa não aprovado, tilesets globais trocados ou traçado irreconhecível. |
| T02 | Casa–Poco Path–Los Platos–Mesagoza–Cortondo a pé e retorno; portões, margem, caverna e olival após reabrir. | Saída sem par, teleporte de QA, bloqueio artificial ou jogador preso. |
| T03 | Novo jogo e visita; escolher inicial, recusar, reentrar e retentar Katy com save descartável. | Duplicação, perda de party/saves ou primeira esmeralda sem vitória. |
| T04 | Cada capacidade da montaria em seu terreno, antes/depois e no retorno, incluindo acesso de outra região. | HM falso, montaria convertida em espécie de combate cedo, atalho com habilidade externa ou colisão. |
| T05 | Até que os três finais estejam gravados, testar cada ausência e a entrada real na Area Zero. Oito ginásios e especiais, Titãs e Star em estados isolados. | Uma história supre outra; Titã/Star duplica esmeralda; visita remove gate. |
| T06 | Liga, Geeta/Nemona, pós-jogo e os acessos independentes de Kitakami, Blueberry e epílogo. | Blueberry conta como Elite Four de Paldea, DLC bloqueia base, ou atalho de Area Zero original para profundezas DLC. |
| T07 | Windows e Android mesmo SHA funcional; instalação nova, atualização real, interrupção, recuperação, repetição e integridade multirregional. | Sem paridade, SHA/receita não provados, save afetado ou canal trocado. |
| T08 | QA física futura na revisão publicada, teste de percurso e desempenho, estado antigo e novo. | Sem ambiente marcar `BLOCKED_ENV`; adiamento autorizado conserva `DELIVERED_WITH_QA_PENDING`, não conta como teste feito. |

Todos os casos estão `NOT_RUN`. Se falhar, corrigir e repetir a mesma
fase, avisar bloqueio novo e seguir o que não depende dele. Um recorte
não está entregue até validar as duas plataformas.

## Publicação por lote jogável futuro

- Conferir SHA exato, estado do catálogo, teste nativo e escopo antes
  de merge. Conferir no GitHub que o instalador Windows `Blue-Story.exe`
  foi publicado para o produto validado, e guardar o SHA-256 do arquivo.
- Android usa o atualizador atual e a receita pela fonte, em revisão
  correspondente ao mesmo produto. Baixar somente da origem auditada
  e verificada, preparar localmente, proteger sob lock e recuperar após
  falha. Não publicar APK, doador, dados originais, cache, mapa cru,
  save, runtime ou ZIP geral por conveniência.
- Diferenciar evidência nativa em CI de aparelho, com links e versões.
  Divergência ou ausência em Windows/Android é `BLOCKED_RELEASE`.
  [Referência Windows/Android](KANTO_ROADMAP_PUBLICACAO_WINDOWS_ANDROID.md),
  [instalação pela fonte](ANDROID_INSTALACAO_PELAS_FONTES.md) e
  [atualização incremental](ANDROID_ATUALIZACOES_INCREMENTAIS.md).
