# KD03 — desenho 2D e primeiro recorte implementável de Kalos

Proposta para uma fase futura, condicionada a autorização para mexer no jogo.
Não reserva MapIDs, não altera o portal e não inclui mapas, assets,
save schema, testes de gameplay implementados ou código de runtime.

## Recorte inicial: Vaniville até Viola

| Entrega de desenho | Inclui | Limite que bloqueia promoção |
|---|---|---|
| D01 — casa e Aquacorde | Quarto e térreo, vizinhança com saídas reais, R01 nos dois sentidos, encontro com os amigos, escolha do inicial e volta da carta. | Nenhum encontro que exija batalha antes de haver Pokémon apto. A volta ao quarto e à praça não reedita a escolha. |
| D02 — floresta e Santalune | R02, tutorial, Santalune Forest, R03, Santalune, Centro e a entrada do ginásio. | Grafo transitável nos dois sentidos, encontro/treinador/retorno no caminho natural; Centro torna-se respawn apenas após ativação válida. |
| D03 — Viola e fronteira | Puzzle navegável de Santalune, treinadores, batalha com Viola, badge BUG única e retorno à cidade. Fronteira R04 indica capítulo seguinte, sem falsa passagem. | Derrota conserva possibilidade de retentar; vitória concede em conjunto badge, recompensa e progresso local, sem créditos duplos. |

D01–D03 formam **um corte jogável futuro** para qualificação, não três
releases incompletas: cada módulo tem testemunho próprio e só o corte
integrado pode ser entregue. Não incluir Lumiose, Sycamore, Flare, Mega,
serviços de pós-Liga ou a Liga. R22 não vira atalho; renderizar
explicitamente a fronteira se o terreno for incluído.

### Grafo de aceitação do corredor

Quarto ↔ térreo ↔ Vaniville ↔ R01 ↔ Aquacorde ↔ R02 ↔ Floresta ↔ R03 ↔
Santalune ↔ Ginásio; Santalune ↔ Centro. Reentrar em portas e respectivos
retornos a pé, sem teleporte QA. O gatilho da carta pede volta a
Vaniville e retorno pelo mesmo caminho. Cada nó deve guardar origem,
destino, categoria (borda, porta, escada), posição e direção verificadas
quando houver construção, tiles transitáveis, pré-requisito e condição
de saída segura. Coordenadas permanecem indefinidas até desenho real.

### Estado proposto, não campos novos em produção

| Identidade lógica | Ação que confirma | Transação e repetição |
|---|---|---|
| S00 sem escolha local | Começar/visitar Kalos com estado anterior preservado | Entrar em Kalos não entrega Pokémon automaticamente. Visitante usa a própria equipe; oferta narrativa futura separada de uma recompensa repetível. |
| S01 inicial entregue | Confirmar Chespin, Fennekin ou Froakie na cena correta | Verificar espaço primeiro; registrar espécie e entrega juntos. Cancelar, fechar, erro e reabertura antes da confirmação deixam S00; depois de S01 a oferta não se repete. |
| S02 carta entregue | Retornar à mãe depois da visita à praça | Distinguir escolha, batalha, entrega da carta e autorização para seguir; não trocar itens de região. Lock claro de diálogo, reentrada e rollback. |
| S03 ginásio habilitado | Chegar a Santalune pelo corredor com pré-requisitos | Pode curar no Centro e voltar para Vaniville; derrota não faz avançar marcos. |
| S04 Viola vencida | Resultado conclusivo da batalha e recompensa segura | Una a badge ao progresso e a uma esmeralda global pelo contrato; não duplicar em rematch ou recarga. Se a Bolsa impedir um prêmio, definir cobrança recuperável em vez de softlock. |

Propor integração futura com [viagem regional](VIAGEM_REGIONAL_LIVRE_NPC.md),
[balanceamento](REGIOES_BALANCEAMENTO_PRIMEIRO_DESAFIO_E_FULL_POWER.md),
[respawn existente](../scripts/battle_polish/RegionalRespawn.rb) e
[política regional existente](../scripts/battle_polish/RegionalPolicy.rb).
A decisão vigente é viagem livre **entre regiões instaladas** desde
o começo, pelo agente da cidade inicial (Vaniville para Kalos), não
uma viagem condicionada à Liga. Reutilizar o mesmo save: chave/HM e PC
de itens por região, TMs e itens comuns compartilhados, pré-reserva de
Boxes para especiais, exigir Pokémon apto, rollback completo se destino
ou vaga inválidos. Blackout usa último Centro Kalos verificado, caso
contrário fallback seguro em Vaniville. Sem liberação no menu sem prova
do manifesto; não introduzir segunda política de progressão.

## Plano de terreno, capacidade e revisão

1. Inventariar a instalação real de cada região e todas as reservas antes
   de alocar: MapInfos, nomes normalizados dos Map.rxdata, imports
   anteriores e referências de eventos, inclusive expressões dinâmicas.
   Diferenciar ocupação, reserva (ainda sem arquivo), omissão e colisão.
   O [relatório histórico](MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md) não
   substitui essa inspeção; não prometer capacidade >999 nem escolher
   faixas provisórias por conveniência.
2. Se não couber, parar a implementação futura para medir compatibilidade
   no editor/compilador, runtime Windows, parser no JoiPlay, viagens,
   manifestos e atualização incremental. Não renumerar regiões e saves
   publicados para encaixar Kalos. Definir chaves estáveis de área/evento
   e manter seu vínculo com IDs após reserva aprovada.
3. Usar desenho autoral 2D: separação visual de bordas, passabilidade,
   escada/porta correspondentes em dois sentidos, travessia medida em
   tile e estabilidade após reabrir. Usar fontes do [KD01](KALOS_KD01_FONTES_E_DIREITOS.md)
   sem importar conteúdo não aprovado; não copiar tile, mapa ou script
   sem direito. Se não houver mapa editável pronto ou quase pronto e
   aprovado, reconstruir com os tilesets de Kanto já usados no Blue.
   O [atlas KD05](KALOS_KD05_ATLAS_VISUAL_E_TILES_KANTO.md) orienta croqui,
   marcos, portas, equivalências visuais e registro de lacunas.
4. Revisar no motor de teste isolado primeiro: caminho real, saídas,
   colisões, segunda abertura, evento idempotente, perfil de saves
   descartável. Fixtures sem testemunho nativo não são aceitação.
5. Para Lumiose depois do primeiro corte, dividir sul/norte, avenidas e
   interiores em setores contíguos. Medir carregamento/memória/transição
   no aparelho, cenário com e sem energia e chegada/retorno por táxi.
   Proibir táxi, estações e portas de atalho de contornar a energia.

## Casos de aceitação previstos

| Caso | Prova esperada quando implementar |
|---|---|
| A01 | Novo jogo legítimo: quarto→praça→carta→quarto; um inicial, nunca dois; reabrir confirmando estado. |
| A02 | Recusar a escolha, espaço insuficiente e interromper antes/depois da gravação; não perder item, não ficar sem Pokémon. |
| A03 | Percorrer R02, floresta, R03, Santalune, Centro e ginásio a pé, validar retorno e pelo menos uma interação por classe de serviço contratada. |
| A04 | Derrotar e ser derrotado por Viola em testes separados; repetir/reabrir não altera o total indevidamente; R04 continua fora do recorte. |
| A05 | Blackout com/sem Centro válido, carregamento de save velho e reentrada na porta após compile sem collider bloqueado. |
| A06 | Entrada/retorno no agente, sem segunda escolha automática; destino inválido/Box cheia sem dano ao inventário, party ou posição. |
| A07 | Reinstalação/atualização em cópia descartável; preservar checksums indicados fora do lote e saves sintéticos em Windows e Android. |

Todos os casos A01–A07 estão `NOT_RUN`.

## Decisões além do recorte

- **Snorlax em R07:** separar passagem liberada de captura já concluída.
  Em X/Y derrotar Snorlax permite seguir; o reencontro depois do Hall da
  Fama não deve reativar retroativamente o gate de campanha no Blue.
  Conferir fuga, derrota do jogador e reencontro como resultados separados
  antes de modelar; [referência de R07](https://bulbapedia.bulbagarden.net/wiki/Kalos_Route_7).
- **Lendário de clímax:** propor um lendário central por variante e
  reservar lógica do outro para arco distinto; requer decisão do
  mantenedor antes desse capítulo, não bloqueia D01–D03.
- **Friend Safari:** o [aviso oficial da Nintendo](https://en-americas-support.nintendo.com/app/answers/detail/a_id/63227/p/603/c/871)
  registra o fim do serviço online padrão do Nintendo 3DS em abril de
  2024. Planejar equivalente offline do Blue, com slots e desbloqueios
  revisados no pós-Liga, sem prometer integração com rede desativada.
- **Custo e gargalos:** priorizar terreno do corredor, eventos de retorno
  e transações de estado antes de geometria decorativa. Arte de Lumiose,
  QA móvel e capacidade de MapIDs têm revisão própria. Se uma dependência
  falhar, reduzir escopo compatível, não relaxar o gate.
