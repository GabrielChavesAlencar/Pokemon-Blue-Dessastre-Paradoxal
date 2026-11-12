# Kanto — etapas restantes até a conclusão

**Atualizado em:** 11/11/2026 (horário de Brasília)  
**Escopo:** campanha Kanto completa, de Pallet até a Liga, integrada ao jogo-mestre Decades.  
**Referências obrigatórias:** [Plano v2](PLANO_REGIOES_DESSASTRE_V2.md) (regras de gameplay), [estudo de fontes](ESTUDO_FANGAME_TODAS_AS_REGIOES_POKEMON.md) (importação e créditos) e [roteiro geral](PROXIMOS_PASSOS.md).

## Como ler o contador

Uma etapa só é marcada `[x]` após evidência de funcionamento. `[ ]` = pendente, mesmo que o código já tenha sido enviado e o teste esteja em execução. Não tratar um teste estrutural ou simulado como teste real de controles, batalhas ou caminhada.

**Progresso:** **1/16 etapas concluídas — 15 restantes (6,25%)**. A aprovação da etapa 01 cobre apenas integridade estrutural e smoke test nativo.

**Marco anterior (já entregue):** protótipo isolado Pallet → Pewter com 13 mapas, Oak, rival, encontros, treinadores, Brock e save no teste nativo simulado. Esse marco **não significa Kanto concluída**.

## 16 etapas de fechamento

- [x] **01 — Auditoria estrutural do piloto.** Validar os 13 arquivos de mapa, conexões, limites de transferências, saída de Pallet, eventos de Oak/Blue/treinadores/Brock e execução do teste nativo na CI. O verificador está em [verify_pilot.py](../scripts/regions/verify_pilot.py) e foi aprovado no [GitHub Actions](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43126592145).
- [ ] **02 — Abrir o piloto e caminhar no Windows.** **Em validação:** disponível o [atalho de teste gráfico](../KANTO_TESTAR_WINDOWS.bat), o [diagnóstico com logs](../scripts/regions/gui_diagnostics.py) e o [checklist detalhado](KANTO_TESTE_WINDOWS.md). A verificação de janela na CI não substitui caminhada real. Falta conferir colisões, portas, transições, todos os iniciais, batalhas reais, cura, captura, derrota e save/reload numa sessão interativa.
- [ ] **03 — Fechar os erros do trecho Pallet → Pewter.** **Em implementação:** vitórias de treinadores agora usam chaves estáveis `KANTO_mapa_evento` (com leitura de saves antigos), e o auditor verifica transferências por direção e caminho de retorno. O teste nativo cobre nomes iguais, derrota/repetição e salvamento. Ainda falta validar as mudanças na CI atual e repetir o roteiro manual, incluindo colisões, portas e respawn.
- [ ] **04 — Escolha real de Kanto como região inicial.** Integrar o seletor de região ao fluxo de nova partida, sem iniciar a introdução de Decades, preservando starters/mecânicas e saves antigos.
- [ ] **05 — Viagem Decades ⇄ Kanto com um único save.** NPC após final auditado de Decades, destino/retorno válidos, estado regional persistido, proteção de PC/equipe, dinheiro, Pokédex, missões e restauração de saves anteriores.
- [ ] **06 — Insígnias, esmeraldas, HMs e Pokémon especiais.** Cada insígnia única de Kanto soma uma esmeralda na progressão Blue existente (sem contagem dupla), HMs usam badges locais e Pokémon especiais ficam bloqueados na party/PC antes de oito conquistas de Kanto. Testar falta de Box e falta de equipe utilizável.
- [ ] **07 — Cerulean e Misty.** Integrar rotas posteriores a Pewter, Mt. Moon, Cerulean, treinadores, eventos e Cascade Badge, com navegação, save e testes.
- [ ] **08 — Vermilion e Lt. Surge.** Integrar as rotas, S.S. Anne, eventos de acesso, ginásio e Thunder Badge, com verificações de campo.
- [ ] **09 — Celadon e Erika.** Integrar caminhos de acesso, cidade, ginásio, eventos locais e Rainbow Badge.
- [ ] **10 — Fuchsia e Koga.** Integrar rotas, Safari Zone e eventos relevantes, ginásio e Soul Badge.
- [ ] **11 — Saffron e Sabrina.** Integrar acessos, Silph Co., progressão da cidade, ginásio e Marsh Badge.
- [ ] **12 — Cinnabar e Blaine.** Integrar rotas aquáticas, ilha, Pokémon Mansion, progressão do ginásio e Volcano Badge.
- [ ] **13 — Viridian e Giovanni.** Abrir o ginásio sob as condições corretas, validar chefe, Earth Badge e retorno às rotas necessárias.
- [ ] **14 — Victory Road, Elite Four, Campeão e conclusão de Kanto.** Exigir oito badges locais, concluir eventos da Liga, salvar a conquista uma única vez e desbloquear **Decades e Johto**, sem desbloquear regiões extras ou contar revanches como novo fim.
- [ ] **15 — Conferência canônica FireRed + LeafGreen.** Auditar encontros fundidos por habitat/método com pesos válidos, exclusividades, treinadores originais, variantes de equipe, itens, sprites/sons autorizados e créditos; aplicar escalonamento Blue em memória sem modificar o time-base. A verificação ocorre a cada lote, com fechamento global aqui.
- [ ] **16 — Aceitação final e publicação integrada.** Testar Kanto completa no Windows, compatibilidade de save legado, retorno após derrota, HM/Box/viagem, regressão e JoiPlay em aparelho; sincronizar Pokédex, localizações, treinadores e guias do portal/Blue Studio. Marcar `playable` somente com evidências.

**Critério de Kanto finalizada:** 16/16 itens concluídos, uma campanha acessível de início a fim, oito insígnias únicas, Liga concluída, viagem e save íntegros, dados e portal sincronizados. **Sevii Islands** são conteúdo adicional opcional e devem ser tratadas como escopo separado se forem incluídas.

## Registro de execução

- **11/11/2026 — Etapa 01, implementação:** adicionado `scripts/regions/verify_pilot.py` para auditoria somente leitura; workflow `kanto-pilot-check.yml` executa a verificação antes do teste nativo. Foram criados testes de grafo em `tests/test_kanto_verifier.py`.
- **11/11/2026 — Etapa 01 concluída:** CI de Kanto aprovada, com **13 mapas**, **4 conexões**, **25 transferências**, **10 eventos obrigatórios** e smoke test nativo de compilação/save/reload. [Evidência](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43126592145).
- **11/11/2026 — Etapa 02 iniciada:** criado `KANTO_TESTAR_WINDOWS.bat`, implementado `gui_diagnostics.py` para inspecionar janelas e erros PhysFS e adicionado um teste de abertura do `Game.exe` não modificado no workflow Windows (diagnóstico que pode ser inconclusivo em runners sem desktop interativo). [Procedimento e checklist](KANTO_TESTE_WINDOWS.md).
- **11/11/2026 — Etapa 02, abertura gráfica confirmada no runner Windows:** workflow [43127669413](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43127669413) recompilou o piloto e lançou o `Game.exe` original; o monitor detectou janela visível por 25,31 s (`window_observed_not_gameplay_verified`), sem registro de PhysFS na sondagem. Isso **não valida os controles, batalhas reais ou a sessão local do usuário**.
- **11/11/2026 — Etapa 03 iniciada:** eliminada a chave de vitória baseada apenas no nome em `KantoPilot.rb` e em `pilot.py`, mantida compatibilidade com flags de vitórias antigas; auditoria de alcance agora considera o sentido dos teletransportes e exige caminho de retorno a Pallet. Ampliado `KantoNativeCheck.rb` para testar nomes homônimos, derrota e save/reload. **Aguardando evidência de CI e caminhada real antes de concluir a etapa.**
- **Pendente (etapa 02):** percorrer Kanto numa sessão gráfica Windows, confirmar movimentos e batalhas reais, capturas, derrota e save/reload; registrar evidências. **Contador permanece 1/16; 15 restantes.**
