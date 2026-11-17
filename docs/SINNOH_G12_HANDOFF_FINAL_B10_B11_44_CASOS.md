# Sinnoh G12 — Fechamento da esteira GitHub e handoff QA real (B10/B11)

**17/11/2026.** A **G12 fecha entregas de engenharia no repositório**; não torna a região jogável no Blue e não libera o clone B09 para execução fora de ambiente isolado. A conclusão G01–G12 representa a esteira GitHub; as barras B/C/D continuam **0/13**, e os **44 casos de QA nativa continuam pendentes** até haver evidência real.

## 1. Arquivos entregues

- [Matriz versionada de 44 casos](../data/regions/sinnoh-g12-native-handoff.json): a lista completa com IDs originais CH20, plataforma, expectativa específica e `native_status: pending`, `observation: null`, `evidence: null`. Não existem IDs de mapa, coordenadas ou capturas inventadas.
- [Auditor de fechamento G12](../scripts/regions/audit_sinnoh_g12_handoff.py): verifica os onze documentos G01–G11, aplica as verificações públicas [G11](../scripts/regions/audit_sinnoh_g11_ci_chain.py) (B07–B11), reusa os [44 IDs CH20](../scripts/regions/audit_sinnoh_android_ch20.py), compara regras do [auditor de evidências reais](../scripts/regions/audit_sinnoh_playtest.py) e protege as [barras de progresso](../data/regions/sinnoh-progress.json).
- [Testes negativos G12](../tests/test_sinnoh_g12_handoff.py): detectam falsas aprovações de Game.exe/JoiPlay, evidências fabricadas, reordenação ou duplicidade dos 44 casos, versões erradas de Barry, quebra do 70/90%, gates L01–L05 burlados, direitos/reservas antecipados e caminhos privados introduzidos via CLI.
- [Workflow G12](../.github/workflows/sinnoh-g12-handoff.yml): gera JSON público, testa G12 e reexecuta suites **CH20, QA do playtest, G11, B10 e B11**. S30 e CH19 também devem passar antes da integração.

O relatório `public-handoff.json` que o CI produz contém **metadados do roteiro**, hashes dos documentos GitHub e requisitos de evidências — não salva nem publica capturas reais, bytes dos saves, `private-baseline.json`, mapas do doador ou Game.exe.

## 2. Os 44 casos nativos, sem afirmar execução

| Tipo (CH20) | Casos | Plataforma prevista | Prova que falta |
| --- | ---: | --- | --- |
| Três Poké Bolas | 3 | Windows | Escolha física de Turtwig/Chimchar/Piplup e rejeição de segunda escolha |
| Barry | 12 | Windows | 3 iniciais × Normal/Master × vitória/derrota, espécie rival e níveis reais 70/90% |
| Save e reload | 3 | Windows | Save de teste no perfil isolado, equipe/Pokédex mantidas |
| Portais de Twinleaf | 16 | Windows | Chegada, retorno, colisão, mapa real e coordenadas verificadas |
| NPCs/eventos | 5 | Windows | Mãe, Barry, Rowan (duas etapas) e callback da batalha corretos |
| Regressões entre regiões | 4 | Windows | Decades, Kanto, Johto e Hoenn sem apropriar save/itens/flags |
| Android/JoiPlay | 1 | Android | Build compatível, perfil próprio, início do jogo, save/reload, logs de execução |

**Resultado atual:** 43/43 casos Windows pendentes; 1/1 caso Android pendente; **0/44 evidências aceitas**. Isso não significa que os testes passaram. A validação humana de provas deve usar o auditor de playtest existente e a cópia isolada previamente aprovada.

## 3. Handoff local seguro, em ordem obrigatória

| Gate | Ferramenta versionada | Condição de avanço |
| --- | --- | --- |
| **L01 / B10** | [SINNOH_B10_ISOLAR_SAVES_SANDBOX.bat](../SINNOH_B10_ISOLAR_SAVES_SANDBOX.bat) e [contrato B10](../data/regions/sinnoh-b10-save-isolation.json) | Confirmar clone B09 físico íntegro, Windows Pro/Enterprise/Education com Sandbox habilitada, duas pastas somente leitura, sem rede/clipboard, **sem autostart**; não iniciar Game.exe no host |
| **L02 / B11** | [SINNOH_B11_AUDITAR_SAVES_QA.bat](../SINNOH_B11_AUDITAR_SAVES_QA.bat) e [contrato B11](../data/regions/sinnoh-b11-host-save-audit.json) | Snapshot antes/depois em diretórios explicitamente monitorados, baseline **privado** e relatório compartilhável **sem paths**; revisão de cobertura real, que permanece parcial mesmo com `watch_unchanged` |
| **L03 / R07–R08** | [Diagnóstico de reservas](../SINNOH_DIAGNOSTICAR_PENDENCIAS.bat) e [mapa G03](SINNOH_G03_MATRIZ_MAPIDS_REGIONAIS.md) | Comprovar reservas Kanto/Johto/Hoenn/Unova e de todas as regiões planejadas; conferir licenças por ativo, 9 mapas, 16 warps, sprites, passabilidade e 14 PNGs reais |
| **L04 / R09 Windows** | [Auditor de evidências nativas](../scripts/regions/audit_sinnoh_playtest.py) e [plano CH20](../scripts/regions/audit_sinnoh_android_ch20.py) | Após os gates de integridade/isolamento/direitos e compilação dos eventos/PBS reais na **cópia QA**, executar somente na VM, registrar e revisar os 43 casos Windows e o Hall of Fame |
| **L05 / Android** | [Pré-voo Android CH20](SINNOH_CH20_JOIPLAY_PREFLIGHT.md) | Build apropriada e autorizada, JoiPlay real em aparelho, save de teste isolado, logs e revisão humana do caso Android |

**Windows Home ou Sandbox indisponível:** não abrir o jogo no sistema principal como alternativa. O B10 bloqueia por segurança. A ferramenta de auditoria B11 não prova automaticamente que toda possível pasta de save foi monitorada.

**Privacidade:** *nunca* publicar ZIPs completos do jogo/QA, `Save*.rxdata`, snapshots privados B11, hashes com identificadores privados associados a caminhos, capturas com dados pessoais, chaves HMAC ou arquivos de terceiros no repositório. Se precisar compartilhar relatórios, utilizar somente os resumos sanitizados permitidos pelo fluxo de QA.

## 4. O que impede Sinnoh de ser jogável, mesmo com G12 encerrada

1. **R07 — reservas físicas de MapID:** os 54 terrenos candidatos `442–495` e as reservas `496–517` exigem verificação real. A cópia QA esperada tem 648+54=702 mapas, mas ela não comprova vinculação dos 9 símbolos de Twinleaf nem ausência de reservas futuras.
2. **R08 — direitos e assets:** fonte autorizada, 14 PNGs reais, imagens e tilesets de altura elevada, sprites de NPCs e licenças individuais; sem inferir aprovação pelas fixtures.
3. **Eventos reais:** mapear 9 símbolos de Twinleaf para mapas existentes com SHA, posições, 16 portais, 5 handlers e 3 Poké Bolas; compilar e vincular os 3 PBS de Barry no motor real.
4. **Progressão jogável:** integrar fisicamente oito ginásios, insígnias/HMs locais, Team Galactic, Liga e Hall of Fame separado de Cynthia, além de pós-jogo e transições regionais, sem alterar o jogo principal.
5. **Segurança do QA Windows:** provar B10/WSB e B11 antes/depois sem regressão de saves e com cobertura auditada da engine.
6. **Teste real:** capturas/logs e observações humanas dos 44 casos, incluindo Android/JoiPlay. O site deve permanecer com `installed=0` e `playable=0` até evidências verificadas.

## 5. Estado final da engenharia GitHub

Ao integrar a G12 com CI aprovado, registrar **G01–G12 12/12 no GitHub** e encerrar a checklist de entrega de código. **Não** encerrar os gates locais L01–L05, não mover B/C/D de 0/13, não liberar execução de Game.exe, nem criar um indicador de Sinnoh jogável no portal.

**Próxima fase segura recomendada: L00 — prontidão física e auditoria de evidências sem execução.** Antes de qualquer Game.exe, produzir uma ferramenta que aceite apenas **relatórios públicos sanitizados** da máquina e valide se existem provas suficientes e coerentes de B09, B10, B11, R07 e R08 para sequer agendar QA em VM. Sua implementação poderá ocorrer no GitHub sem acessar o PC e continuará falhando em modo seguro quando faltarem dados.
