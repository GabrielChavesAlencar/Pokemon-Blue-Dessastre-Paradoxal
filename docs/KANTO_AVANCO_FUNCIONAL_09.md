# Kanto — 9º núcleo funcional (etapa 10): Fuchsia City, Koga e Safari Gate seguro

**Data:** 12/11/2026. **Situação:** código funcional em `main`, condicionado à aprovação final da CI Windows e regressão para subir a Barra 1. O número **9** se refere ao **nono núcleo entregue** nas duas barras, enquanto a etapa do roteiro original é **10 — Fuchsia/Koga/Safari**. Fases 09 (Erika) e 08 (Surge) já estavam contadas.

## 1. Escopo de gameplay por MapID real da fonte FRLG 1.1

O catálogo permanece em **109 mapas** e todos os MapIDs atuais são preservados. Apenas os cinco mapas abaixo deixam de ser `preview_only` nesta fase:

| MapID origem | Mapa | Eventos adaptados (não scripts originais) |
| ---: | --- | --- |
| **144** | Fuchsia City | **5 ginásio**, **17 Centro**, **18 Mart**, **24 Safari Gate** (entradas em Player Touch) |
| **145** | Centro Pokémon | **1 saída**, **2 enfermeira** (cura) |
| **146** | Poké Mart | **1 saída**, **2 atendente** (loja provisória com itens já suportados) |
| **147** | Ginásio de Fuchsia | **3 Nate, 4 Kayden, 5 Kirk, 6 Edgar, 7 Phil, 8 Shawn, 11 Koga**, **9 saída** |
| **153** | Portão da Safari Zone | **1 guichê**, **2 saída**, **5 guia**. Guichê e guia informam que a captura ainda depende de implementação; não cobram nada nem enviam à zona |

**Quatro pares de porta e retorno** (cidade ⇄ ginásio, Centro, Mart, portão Safari) recebem checagem estrutural de MapID/EventID/warp. Os 15 outros mapas da fase 10 seguem como cenário, inclusive a casa do Warden, Safari Zone South/East/North/West, casas de descanso, Secret House e rotas; Celadon mantém as oito prévias restantes e Saffron 30 prévias. **Total atualizado de mapas `preview_only`: 53.**

**Nenhuma entrada na Safari Zone é ativada**: captura especial, Safari Balls, contagem de passos, taxa de ingresso, reset da sessão, Gold Teeth, Secret House/Surf, Strength/Warden e os encontros da Safari permanecem para a próxima implementação específica. Os três acessos da fonte para a área sul não são copiados para o portão do piloto. Não fingir que os atalhos de inspeção são ingresso real.

## 2. Ginásio: personagens e equipes comprovadas na fonte

A auditoria somente leitura foi executada em [`audit_fuchsia_core.py`](../scripts/regions/audit_fuchsia_core.py) sobre a cópia FRLG pinada no projeto, com IDs exatos de eventos e PBS de treinadores.

| ID de evento | Treinador | Trigger |
| ---: | --- | --- |
| 3 | Juggler Nate | `Sight(4)` |
| 4 | Juggler Kayden | `Sight(4)` |
| 5 | Juggler Kirk | `Sight(3)` |
| 6 | Tamer Edgar | `Sight(2)` |
| 7 | Tamer Phil | `Sight(2)` |
| 8 | Juggler Shawn | `Sight(1)` |
| 11 | **Leader Koga** | Action Button |

**Equipe de Koga (do PBS auditado, não balanceada arbitrariamente):**

| Pokémon | Nível | Moves |
| --- | ---: | --- |
| Koffing | 37 | Sludge, Smokescreen, Toxic, Self-Destruct |
| Muk | 39 | Sludge, Toxic, Minimize, Acid Armor |
| Koffing | 37 | Sludge, Smokescreen, Toxic, Self-Destruct |
| Weezing | 43 | Sludge, Tackle, Toxic, Smokescreen |

As equipes dos seis outros treinadores usam os Pokémon e níveis reais dos blocos PBS selecionados. O catálogo de treinadores do site passa de **62 para 69** (Koga + seis), com **109 localizações**. A quantidade de eventos com visão ativa passa de **57 para 63**. Nenhum treinador é duplicado ao voltar à área.

## 3. Soul Badge, progresso regional e segurança de save

- Koga tem perfil `BLUE_KANTO_LEADER_KOGA` e chave persistente `KANTO_147_011`.
- Uma derrota simulada no teste nativo não concede Soul, não registra vitória e permite revanche.
- Uma vitória chama `BlueRegions.award(progress, "KANTO", "SOUL")` **uma única vez**, sem tocar nas insígnias globais da campanha Decades.
- O evento registra `self-switch A` após a vitória (página sem batalha). O status e a Soul devem resistir a save/reload.
- O requisito regional para **Surf** fica associado à Soul Badge na política pré-existente, mas **a obtenção do HM Surf não foi implementada nesta entrega**; não inventar item, nem liberar Surf apenas por teletransporte.
- A tabela original de pesca da cidade (Map144) contém **níveis descontínuos**. O normalizador do piloto recusa fabricar níveis intermediários: Fuchsia core fica sem encontros selvagens até um importador que preserve todos os slots verificados.

## 4. Testes automáticos exigidos para contar o 9º núcleo

- [ ] `verify_pilot.py`: 109 mapas, 53 protegidos sem eventos, cinco core, quatro pares bidirecionais, 7 batalhas, 63 eventos `Sight(n)` e 42 atalhos de teste, com bloqueio de entrada Safari sem sessão completa.
- [ ] `KantoNativeCheck.rb`: inicialização, gráfica/portas, eventos por aproximação e Koga, Soul apenas após vitória, ausência de cobro do portão, self-switch A, save/reload e preservação da base Decades.
- [ ] Regressão Python/PBS/Windows/Chromium aprovada, 109 localizações e 69 treinadores confirmados na saída do site.

## 5. QA manual ainda pendente (Barra 2)

- [ ] No `Game.exe → Testar Kanto`, escolher inicial e usar atalho **Fuchsia City**. Entrar/caminhar/voltar de Ginásio, Centro, Mart e Safari Gate.
- [ ] Cura real no Centro, venda no Poké Mart, e conferência de gráficos/colisões e do labirinto de paredes invisíveis do ginásio.
- [ ] Jogar os seis confrontos por visão, testando derrota e vitória; lutar com Koga, perder sem ganhar Soul, vencer e garantir insígnia uma vez.
- [ ] Salvar, sair, recarregar e verificar Koga/treinadores/premiações; garantir que a instalação principal e saves Decades não mudaram.
- [ ] Tentar a entrada da Safari Zone: exibir mensagem de indisponibilidade **sem permitir acesso, cobrança ou Safari Balls**; inspecionar cenários por atalho de teste sem liberar eventos.
- [ ] Verificar HM Surf e Strength *somente depois* que Secret House/Warden forem adaptados, e testar Android/JoiPlay.

## 6. Próximas dependências e regras das barras

Ainda pendentes: Safari com sessão nativa completa, encontro especial e Safari Balls, limite de passos, Gold Teeth/Strength, Secret House/Surf, conexões de Rotas 12–18/Snorlax, pós-ginásio e diálogos EN/PT-BR. Não alterar Pokémon de Koga para time competitivo de pós-jogo antes da conclusão de todas as regiões.

**Ao aprovar CI + regressão:** **Barra 1 = 9/16 (56,25%, faltam 7 passos)**. **Barra 2 = 1/16 (6,25%, faltam 15 aceites)** até concluir checklist humano da etapa inteira. Se uma dessas verificações falhar, manter o contador **8/16 e 1/16** e registrar falha antes de chamar de implementado.
