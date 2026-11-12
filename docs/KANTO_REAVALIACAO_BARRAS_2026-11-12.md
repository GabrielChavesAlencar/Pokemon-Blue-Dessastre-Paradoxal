# Reavaliação das duas barras de Kanto — 12/11/2026

**Revisão das 16 etapas com base no código e nas evidências de GitHub Actions, não somente no número da última fase iniciada.** Esta é a referência **atual** dos contadores; números anteriores de 8/16 e 1/16 no histórico dos outros documentos representam o critério usado nas publicações anteriores.

## Barras reavaliadas

**Barra 1 — Desenvolvimento funcional com núcleo comprovado:** **6/16 (37,5%) — faltam 10 etapas** para alcançar 16/16 com núcleo implementado.

`██████░░░░░░░░░░  6 / 16 | 10 restantes`

**Barra 2 — Etapas integralmente aceitas:** **1/16 (6,25%) — faltam 15 etapas** para finalizar/aceitar as 16.

`█░░░░░░░░░░░░░░░  1 / 16 | 15 restantes`

> **Significado:** a primeira barra contabiliza etapas com um **núcleo funcional entregue e testado automaticamente**, mesmo que ainda tenham eventos secundários ou QA manual pendentes; **não** é a contagem de fases perfeitamente concluídas. A segunda é propositalmente rigorosa: requer cumprir os critérios de aceite da etapa. Apenas a etapa 01 tem aceite estrutural conforme a definição do roadmap. A fase 01, por ser uma auditoria, é contabilizada na primeira barra como **marco técnico concluído**, não como conteúdo jogável. A última fase aberta **não** determina o numerador.

## Classificação de todas as 16 etapas

| Etapa | Entrega prevista | Evidência real consultada | Estado reavaliado para a Barra 1 | Aceite da Barra 2 |
|---:|---|---|---|---|
| **01** | Auditoria estrutural e smoke test do piloto | Verificador estrutural e [teste nativo](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43126592145); regressão posterior [43218959042](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43218959042) | **Núcleo entregue** | **Aceita** (escopo estrutural) |
| **02** | Abrir piloto e percorrer caminho real no Windows | Teste nativo confirma inicialização/janela, mas **não** caminhada ou batalha manual completas | Parcial — não conta | Pendente |
| **03** | Correções Pallet → Pewter | [Oito interiores com ida/volta + 50 treinadores Sight(n) aprovados em CI](KANTO_CORRECOES_FUNCIONAIS_MAN01_MAN02.md); demais portas/colisões, evento canônico e teste manual incompletos | Parcial — não conta | Pendente |
| **04** | Seleção de Kanto como região inicial | [RegionStart.rb](../scripts/battle_polish/RegionStart.rb), importação opcional e [CI nativa](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43132795847) | **Núcleo entregue** | Pendente (teste manual) |
| **05** | Viagem Decades ⇄ Kanto / save único | [RegionTravel.rb](../scripts/battle_polish/RegionTravel.rb), [CI ida/volta, Box e reload](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43136257273); NPC físico/QA visual pendentes | **Núcleo entregue** | Pendente |
| **06** | Insígnias, esmeraldas, HMs e especiais | [RegionalPolicy.rb](../scripts/battle_polish/RegionalPolicy.rb), [CI de políticas](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43139789644); cobertura total de caminhos, PC cheio e UI manual pendentes | **Núcleo entregue** | Pendente |
| **07** | Cerulean/Misty | Núcleo experimental com cenários, treinadores, Misty/Cascade, [CI](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43143559422); faltam eventos canônicos e QA | **Núcleo entregue, experimental** | Pendente |
| **08** | Vermilion/Lt. Surge | Núcleo experimental com S.S. Anne, puzzle/Surge/Thunder, [CI](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43198430978); ticket de Bill provisório e QA pendentes | **Núcleo entregue, experimental** | Pendente |
| **09** | Celadon/Erika | 11 mapas **somente cenário**, zero eventos/tratadores, sem Erika/Rainbow | Apenas cenário — não conta | Pendente |
| **10** | Fuchsia/Koga/Safari | 20 mapas **somente cenário**, sem Safari funcional, Koga/Soul ou HM | Apenas cenário — não conta | Pendente |
| **11** | Saffron/Sabrina/Silph | 30 mapas **somente cenário**, sem teletransportes, Silph/Rocket/Sabrina/Marsh | Apenas cenário — não conta | Pendente |
| **12** | Cinnabar/Blaine | Nenhuma entrega funcional documentada da fase | Não iniciada — não conta | Pendente |
| **13** | Viridian/Giovanni | Ginásio final fonte 13 segue fora do lote por depender de eventos | Não iniciada — não conta | Pendente |
| **14** | Victory Road/Liga/campeão | Progressão de oito insígnias e Hall of Fame de Kanto não implementados | Não iniciada — não conta | Pendente |
| **15** | Conferência canônica FRLG | Há auditorias locais, partes do PBS, portal e 54 perfis existentes; faltam conferir todas as áreas, exclusividades, encontros, treinadores, itens e direitos | Parcial transversal — não conta | Pendente |
| **16** | QA final e publicação integrada | [CI e regressão](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43219637690), [site checks](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43219637630); faltam roteiro integral, QA humano e JoiPlay | Parcial de infraestrutura — não conta | Pendente |

**Conferência da contagem:** 6 com núcleo implementado (01, 04, 05, 06, 07, 08) + 4 parciais (02, 03, 15, 16) + 3 somente terreno (09, 10, 11) + 3 sem implementação de fase (12, 13, 14) = **16**. São **10 etapas sem núcleo completo** na primeira barra (4 + 3 + 3). Apenas 01 está integralmente aceita; **15** aguardam aceite na segunda barra.

## Quanto realmente existe em código

- **109 mapas** no catálogo experimental, dos quais **61 com zero eventos** (11 Celadon + 20 Fuchsia/Safari + 30 Saffron). Os mapas protegidos **não são 61 mapas jogáveis**.
- **40 mapas** dos trechos originalmente integrados e **8 interiores** novos com transferências dirigidas/retorno; [CI estrutural e nativa 43218959042](https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/43218959042) aprovou verificação das oito conexões.
- **50 eventos de treinadores** com `Sight(n)` automático, 6 com ação manual conforme a fonte, página pós-vitória e save isolado. A suíte nativa **simula resultados de batalha**; não substitui testes de movimento.
- O seletor de região, viagem, política de HMs/especiais, líderes iniciais, exportador de portal e parte da interface têm código e testes de integração; **não** há prova de campanha completa Pallet → campeão.
- Os [eventos FireRed](KANTO_ROADMAP_EVENTOS_FIRERED.md) têm uma trilha independente de **12 marcos**, e os [diálogos EN/PT](KANTO_ROADMAP_DIALOGOS_EN_PT.md) têm **10 tarefas**; não adicionar esses 22 itens ao denominador **16**. Tampouco contar as 67 cenas do guia como falas traduzidas.

## O que falta: 10 etapas com núcleo pendente

**Quatro fases parciais:** 02 (caminhada, colisões e batalhas reais); 03 (portas restantes, bloqueios corretos, save/respawn); 15 (auditoria canônica completa); 16 (aceite de ponta a ponta, portal e Android).

**Três fases ainda só de terreno:** 09 (Celadon/Erika/Rocket e Rainbow); 10 (Fuchsia/Koga/Safari/Surf/Strength/Soul); 11 (Saffron/Silph/Dojo/Sabrina/Marsh), com eventos, guardas, elevadores, treinadores e falas em falta.

**Três fases sem núcleo entregue:** 12 (Cinnabar/Blaine), 13 (Viridian/Giovanni) e 14 (Victory Road, Elite Four, campeão e desbloqueio canônico).

**Para liberar os 15 aceites restantes:** somam-se os testes manuais de 02–08, a implementação/QA da história de 09–14 e a validação canônica e de publicação de 15–16. Mesmo os seis núcleos entregues não estão totalmente aceitos, exceto 01.

## Regra permanente de atualização das duas barras

1. **Barra 1:** +1 somente quando a etapa possuir **núcleo executável**, integração mínima real e **CI verde**; para etapas de gameplay, se não houver evento/história jogável (só mapa, MD ou script de auditoria), não contar. **Exceção: a etapa 01 é definida exclusivamente como auditoria estrutural, portanto sua CI verde conclui seu núcleo**. Não contar a mera numeração da fase; usar uma linha de evidência por etapa.
2. **Barra 2:** +1 somente com o checklist de aceite integral da etapa e prova adequada. A etapa 01 é uma auditoria estrutural; as etapas de gameplay exigem sessão de jogo real, estados/saves e ausência de regressão.
3. **Barras independentes e monotônicas por evidência**, exceto correção expressa de classificação, como esta. Registrar as revisões, preservando as contagens históricas como histórico e identificando-as como **obsoletas** para o estado atual.
4. **Não usar percentuais subjetivos de implementação interna das etapas**; registrar claramente o que está parcial sem criar frações inventadas de fase.

**Próxima decisão técnica recomendada:** priorizar **02 e 03** no Windows (caminhada real, interiores, visão do treinador, vitória/derrota e reload). Em paralelo, planejar integração autorizada dos eventos 09–11 antes de aumentar a primeira barra. Se houver histórico de teste manual novo, usar esse material para recalcular o aceite; não presumir aprovação por CI.
