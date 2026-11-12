# Kanto — Correções funcionais MAN-01 e MAN-02

**Implementação e CI aprovadas:** 12/11/2026. **Escopo:** piloto isolado de Kanto, sem alterações diretas nos saves Decades nem nos 61 mapas `preview_only` de Celadon/Fuchsia/Saffron.

Este documento registra trabalho de **gameplay**, não somente expansão de geometria. A aceitação final depende do relatório Windows e de testes manuais em sessão.

## 1. MAN-01 — Entrar e sair dos interiores reais (Pallet → Pewter)

A auditoria de leitura da fonte FRLG, usando `scripts/regions/audit_early_interiors.py` no workflow Windows com SHA-256 verificado, encontrou dez destinos ausentes nos mapas do trecho inicial. **Oito** têm transferência de ida e volta comprovada e foram integrados ao piloto. MapIDs abaixo são **IDs da fonte FRLG**, não os IDs alocados pelo Blue.

| Mapa externo / EventID | Interior FRLG / EventID de saída | Descrição |
| --- | --- | --- |
| Pallet Town **5/2** | **8/1** | Casa do rival, retorno a Pallet |
| Viridian City **10/2** | **14/4** | Casa de Viridian, retorno a Viridian |
| Viridian City **10/3** | **15/3** | Segunda casa de Viridian, retorno |
| Rota 2 **18/8** | **21/4** | Portaria secreta, retorno à Rota 2 |
| Rota 2 **18/2** | **22/4** | Casa escondida, retorno à Rota 2 |
| Pewter City **25/1** | **29/1** | Museu de Pewter, retorno à cidade |
| Pewter City **25/3** | **30/1** | Casa de Pewter, retorno |
| Pewter City **25/7** | **31/1** | Segunda casa de Pewter, retorno |

**Implementação:** oito entradas adicionadas ao manifesto e com nomes no portal, importação apenas de comandos locais de transferência `201` para destinos da lista segura. Os destinos de retorno são inspecionados pela verificação estrutural. Nenhum script Ruby original dos interiores, NPC, item ou diálogo é executado/importado. A ordem dos **101 mapas anteriores** fica congelada; os oito novos são **acrescentados ao final**, sem mudar MapIDs já publicados.

**Fora do lote de segurança:** **13 — Viridian Gym** permanece indisponível até a progressão histórica de Giovanni (warp condicionado); **23 — entrada da Diglett's Cave** aguarda o restante do complexo da caverna e a ida/volta completa. Importar só uma entrada poderia deixar o jogador preso ou liberar história precocemente.

**Pendência MAN-01:** casas e estabelecimentos de outras áreas, NPCs internos, portas condicionais e prova manual de colisão/entrada/saída (inclusive Museus, Centers e lojas). Esta correção é um lote **parcial**, não fechamento global.

## 2. MAN-02 — Linha de visão dos treinadores

A auditoria `scripts/regions/audit_trainer_interactions.py` confirmou **56** eventos de treinador em mapas anteriormente integrados: **50 com `Sight(n)` e trigger Event Touch (2)**, e **6 de interação manual** (incluindo Brock, Misty e Lt. Surge, além de três treinadores opcionais de rota). Os metadados vêm dos eventos da fonte FRLG, **não são distâncias inventadas**.

O importador `scripts/regions/pilot.py` agora:

1. Preserva o nome `Sight(n)`, a distância real da fonte, os sprites e a orientação do NPC; configura **Event Touch (2)** nos 50 eventos de visão. Os seis eventos manuais permanecem **Action Button (0)**.
2. Usa o processamento nativo de detecção do Pokémon Essentials, que considera linha de visão, passabilidade e aproximação. `pbTrainerIntro`, `pbNoticePlayer(get_self)` e `pbTrainerEnd` fazem a animação/abordagem sem importar scripts Ruby desconhecidos.
3. Mantém os IDs estáveis `KANTO_<mapa>_<evento>` do Blue, a batalha e o resultado persistido. A **derrota não marca vitória**, e NPCs com nomes repetidos não compartilham indevidamente conquistas.
4. Após vitória verdadeira, `BlueKantoPilot.sync_trainer_event` ativa **self-switch A local** e a **página 2** do treinador muda para interação manual. O treinador continua visível, com fala de pós-batalha, mas não inicia outra batalha automaticamente. Saves antigos com flags de nome são reconhecidos.
5. Não força bloqueios físicos artificiais para treinadores opcionais. Restrições de progressão específicas exigem auditoria por evento (MAN-02 permanece parcialmente aberta).

**Testes automatizados adicionados:** verificador estrutural exige 50 visões, presença de `pbNoticePlayer`, página 2 protegida e sincronização da vitória; teste na engine valida Rick da Viridian Forest (`Sight(5)`) e sua self-switch após vitória, além de um treinador ainda não derrotado.

## 3. Como testar na cópia Windows

Abra **Game.exe → Testar Kanto**. Use a cópia isolada (não a campanha Decades) e grave com outro slot.

- [ ] Em Pallet, entre na **casa do rival** e volte à cidade pelo mesmo caminho.
- [ ] Em Viridian, entre nas **duas casas** e valide o retorno pelas portas.
- [ ] Na Rota 2, teste a **portaria secreta** e a **casa escondida**, sem perder a saída.
- [ ] Em Pewter, entre no **Museu** e nas **duas casas**; retorne sem teleporte experimental.
- [ ] Na Viridian Forest, aproxime-se de **Rick** na direção de visão (até cinco blocos, conforme a fonte), sem pressionar ação. Confira exclamação/abordagem e batalha.
- [ ] **Perca** para um treinador de teste: não deve ganhar flag de vitória, e a próxima tentativa deve continuar possível.
- [ ] **Vença** Rick, afaste-se e aproxime-se novamente: não deve iniciar batalha automaticamente. Interagir manualmente deve mostrar fala de pós-batalha.
- [ ] Salve e recarregue; confira a ausência de repetição de prêmios e de detecção automática dos treinadores já derrotados.
- [ ] Teste em Windows primeiro; depois verifique controles/colisão no JoiPlay.

Os testes da CI compilam a engine e inspecionam estados, mas **não substituem** caminhada e combate reais com controles gráficos. A prova de colisão, efeitos visuais e respawn é responsabilidade do teste manual.

## 4. Critérios de conclusão e métricas

- [x] [CI Kanto 43218959042](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43218959042) **aprovada**: 109 mapas, 61 sem eventos, 8 conexões de interiores bidirecionais, 50 gatilhos de visão, compilação e execução nativa com save/reload; cópia descartável Decades preservada.
- [x] [Regressão 43219637690](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43219637690) **aprovada**: testes unitários, RUN.bat no Windows e navegação Chromium.
- [x] [Site checks 43219637630](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43219637630) **aprovados** com 109 localizações no portal.
- [ ] Os **8 interiores** passam no verificador bidirecional e no teste manual de entrada/saída.
- [ ] Os **50 treinadores de visão** passam na validação da engine e em amostra manual nos mapas do jogador.
- [ ] QA de batalha real/derrota/repetição/save/reload e importação em cópia descartável Decades.
- [ ] Atualizar o portal apenas com os dados realmente presentes e manter fases 09–11 sem eventos.
- [ ] Completar os interiores, bloqueios e diálogos ainda faltantes antes do aceite integral de MAN-01/MAN-02.

**Progresso geral vigente (posterior a este lote):** [Barra 1 **9/16 (56,25%, faltam 7)**; Barra 2 **1/16 (6,25%, faltam 15)**](KANTO_AVANCO_FUNCIONAL_09.md). O lote MAN-01/02 foi o 7º núcleo; Erika o 8º e Koga/Fuchsia o 9º.


**Diálogos EN/PT-BR:** nenhuma transcrição da fonte GBA foi importada automaticamente. Os diálogos internos e pós-batalha finais permanecem no [roadmap de localização](KANTO_ROADMAP_DIALOGOS_EN_PT.md).
