# Kanto — Etapa 15/16: auditoria canônica dos encontros e treinadores

**Data:** 12/11/2026. **Escopo:** núcleo funcional experimental derivado da fonte **Essentials FRLG 1.1**, fixada pelo SHA-256 do manifesto `data/regions/kanto-source.json`. **Não equivale à certificação de fidelidade 1:1 das ROMs oficiais FireRed e LeafGreen.** Esta distinção é fundamental, especialmente para exclusividades de versão.

## Problema encontrado e correção

O importador de encontros do piloto rejeitava diversos mapas como “níveis não contíguos”, desabilitando encontros de Fuchsia, Pokémon Mansion e Victory Road. O projeto fonte utiliza um formato especial de PBS: depois da espécie vem uma **lista explícita de níveis permitidos**, e não simplesmente um limite mínimo/máximo. Exemplos reais auditados:

- `45,SPEAROW,3,5`: **somente nível 3 ou 5**, não nível 4;
- `5,SLOWPOKE,15,16,17,19,20,…,35`: o nível **18 não é permitido** nesse slot de SuperRod;
- `100,TENTACOOL,5,6,…,40`: lista consecutiva que pode ser compactada para o intervalo inclusivo 5–40.

O `scripts/regions/pbs.py` agora:
1. Compacta apenas listas inteiramente consecutivas em `chance,species,min,max` (formato Essentials v21.1).
2. Expande listas com lacunas/repetições em slots de nível individual. Um multiplicador mínimo via MMC dos comprimentos garante que **todas as probabilidades espécie×nível sejam matematicamente idênticas** às do PBS de origem. Pesos acima de 100 são divididos em slots equivalentes, nunca arredondados.
3. Não inventa espécies, níveis, variações de equipe ou pesos. Falha se a expansão exceder um limite seguro ou tiver campos inválidos.
4. Só ativa encontros em mapas funcionais; os **45 mapas `preview_only`** permanecem sem eventos e sem encounters.
5. Preserva no guia o peso inteiro da engine (`weight`/`weightTotal`) e publica `chance` normalizada em porcentagem, inclusive quando a soma interna dos pesos é maior que 100.

## Inventário efetivamente conferido na CI

A rotina independente `scripts/regions/audit_canonical.py` lê a fonte pinada **de novo**, independentemente do conversor, e compara as distribuições por espécie e nível com frações racionais. Ela verifica também cada linha das equipes de treinador e os limites de versão, sem executar os scripts estrangeiros.

| Medida | Resultado auditado |
|---|---:|
| Seções de encontros presentes na fonte FRLG | 58 |
| Tabelas importadas de forma comprovadamente fiel | **23** |
| Espécies distintas com encontros ativos | **53** |
| Slots originais auditados nos 23 mapas | **303** |
| Slots na representação compilada equivalente | **423** |
| Listas consecutivas compactadas | **158** |
| Listas com lacunas/repetições convertidas sem alteração de probabilidade | **72** |
| Perfis PBS de treinador comparados linha por linha | **153** |
| Mapas em prévia sem encontros | **45** |
| Mapas totais (IDs preservados) | **142** |
| Métodos de encontro verificados nas tabelas | **69** |

O portal exibe **144 treinadores** agrupados por identidade/localização, além de 142 localidades. Os **153 registros PBS** contam também variantes do mesmo treinador, incluindo os três times do Campeão Blue. Nenhum time-base foi alterado por esse processo; o escalonamento existente do Blue/Decades continua sendo aplicado em memória.

## Inconsistência da fonte: Route 23 / Map209

O mapa fonte 209 contém duas cópias idênticas de LandDay. O importador mantém uma cópia e rejeita uma repetição que altere a taxa ou os Pokémon e níveis. A distribuição do bloco original usa pesos relativos que somam 110. O portal calcula as porcentagens sobre essa soma.

A auditoria confrontou as distribuições de grama diurna, surfe e três varas com o PBS gerado. São 23 áreas, 69 métodos e 53 espécies no total. Falta verificar encontros pela interface e comparar independentemente as exclusividades oficiais de FireRed e LeafGreen.

## Regiões/áreas que passaram a ter encontros reais na tabela do piloto

Entre os 23 mapas com tabelas autenticadas estão Pallet/água (fonte 005), Viridian e rotas iniciais, **Route 22 (016) e Route 23 (209)**, Fuchsia City (144), os **quatro andares da Pokémon Mansion (205–208)** e **Victory Road 1F–3F (211–213)**. A disponibilidade de Surf, pescaria, uso de área, passabilidade e demais métodos no gameplay real depende do estado do jogo e permanece no checklist manual.

## Verificações de segurança

- Comparação exata dos métodos, taxa de encontro por passo, distribuição por espécie e cada nível permitido; tabelas de mapa inesperadas levam a erro.
- Comparação literal (sem alterações) das linhas PBS de espécie, nível, movimentos e item de **153 perfis** de treinador.
- Verificação da whitelist de 142 MapIDs e 45 prévias; sem importar scripts originais ou conceder eventos da história.
- Testes unitários para lacunas, duplicações, níveis repetidos, listas longas, versões, probabilidades e entradas inválidas.
- Compilação e teste nativo da engine em Windows; exportação de dados do portal e regressão.
- O trabalho não baixa/distribui os arquivos brutos da fonte FRLG, gráficos, trilhas ou ROMs ao usuário.

## Pendências de **aceite integral** (continuam abertas)

- Comparação **independente com as tabelas oficiais de FireRed e LeafGreen** (incluindo exclusividades como Oddish/Bellsprout, Growlithe/Vulpix, Elekid/Magby quando aplicáveis), confrontando habitat, método e horário em cada versão. A fonte usada aqui **mescla** conteúdo e não prova equivalência oficial.
- Verificar encontros da Rota 23 pela interface.
- Confirmar que todos os métodos, rodadas dia/noite, pesca, Surf, taxas, nível e legendários funcionam **jogando** no Windows/JoiPlay, incluindo Save/Reload, repelentes e HM.
- Auditar todos os itens de chão/TMs/Key Items e sequências de eventos canônicos que ainda estão excluídos por whitelist (Safari, Silph Scope, Rocket, Bill, fósseis e afins). **Importar tabelas não significa liberar esses eventos.**
- Validar autorização individual de sprites, músicas, efeitos e créditos para eventual distribuição pública.
- As equipes mais fortes de líderes/Elite/Campeão nas revanches após **todas** as regiões zeradas continuam como etapa posterior; esta auditoria não substitui a regra já programada.

**Barra 1:** contar este núcleo como aprovado **somente após a CI completa passar** (de 13/16 para 14/16). **Barra 2:** manter 1/16 até QA manual real. **Próximas pendências:** etapa 02 (caminhada real), etapa 16 (aceite e integração final).
