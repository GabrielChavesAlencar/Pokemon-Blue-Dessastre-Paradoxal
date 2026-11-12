# Johto — acompanhamento técnico das 16 etapas

**Início:** 12/11/2026  
**Plano mestre:** [JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md](JOHTO_PLANO_IMPLEMENTACAO_PASSO_A_PASSO.md)  
**Fontes:** [JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md](JOHTO_ESCOLHA_FONTES_MAPAS_E_MUSICAS.md)  
**Estado:** preparação técnica iniciada. Nenhum mapa de Johto foi incorporado ou habilitado para jogar.

## Duas barras separadas

- **Barra 1 — Núcleos implementados e comprovados por testes automatizados:** **0/16 (0%)** — faltam 16.
- **Barra 2 — Etapas integralmente aceitas com gameplay real:** **0/16 (0%)** — faltam 16.

Progresso parcial não é etapa concluída. Nenhum teste sintético ou documento concluído autoriza subir a Barra 2.

## Trabalho inicial de Johto entregue ao GitHub

- [x] Fonte de mundo/tiles selecionada: [Map Pack de Johto de AenaonDogsky](https://www.eeveeexpo.com/resources/828/) — overworld e cavernas de Johto; Mt. Silver não incluído.
- [x] Política de não-regressão para Decades, Kanto, Game.exe, slots, saves, músicas, portal e Blue Studio.
- [x] **data/regions/johto-source.json** criado com fonte e créditos, direitos pendentes, import_enabled=false, mapping_verified=false, maps vazio e hash da fonte ainda desconhecido.
- [x] **scripts/regions/audit_johto.py** criado para ler RMXP em modo somente leitura (sem executar Ruby), inventariar mapas, dimensões, tilesets, eventos, transferências, hashes e colisões com IDs atuais.
- [x] **tests/test_johto_source_audit.py** criado com mapas sintéticos, proteção de hashes, referências faltantes, scripts não executados e teste de fonte ausente.
- [x] **Testar Johto** já está no menu principal junto de **Testar Kanto**. Enquanto o piloto estiver ausente, informa que Johto está em preparação sem usar os arquivos de Kanto.
- [ ] Confirmar arquivo original ZIP/RAR e SHA-256 do Map Pack.
- [ ] Auditar mapa real de origem, permissões separadas de cada arte e inventário da instalação game/ local.
- [x] Planejamento seguro de IDs implementado em `scripts/regions/plan_johto.py` (IDs livres ≥600, compatibilidade com mapeamentos anteriores).
- [x] Staging de terreno em `scripts/regions/stage_johto.py`, somente em `.blue-work`, sem eventos nem músicas, com proteção dos arquivos originais.
- [x] Verificador `scripts/regions/verify_johto.py` e testes sintéticos `tests/test_johto_map_plan.py` e `tests/test_johto_stage.py`.
- [x] [Documento detalhado da Etapa 03](JOHTO_FASE_03_PREVIA_SEGURA.md) com comandos, critérios e limites.
- [ ] Gerar cópia isolada a partir dos **mapas reais de Johto**; sem a fonte externa validada o staging real permanece bloqueado.
- [ ] Criar New Bark, casa, laboratório de Elm e inicial jogável após validar a fonte, sem escrever em Decades/Kanto.

**Limitação atual:** o GitHub não inclui os arquivos reais da instalação game/, da fonte RMXP nem dos saves. O pacote é hospedado externamente via Mega e o arquivo não foi obtido nesta etapa. Não foram inventados MapIDs, hashes ou evidências de jogabilidade.

## Estado das 16 etapas

| Etapa | Núcleo | Estado |
|---|---|---|
| 01 | Fonte, direitos e baseline | **PARCIAL**: manifesto criado; fonte real, hash e direitos pendentes |
| 02 | Auditoria RXDATA e dependências | **PARCIAL**: scanner/testes criados; fonte real e validação pendentes |
| 03 | Importador isolado e prévia | **PARCIAL**: código e testes sintéticos; pacote, IDs e prévia reais pendentes |
| 04 | New Bark, casa, Elm e inicial | PENDENTE |
| 05 | Violet e Falkner | PENDENTE |
| 06 | Azalea e Bugsy | PENDENTE |
| 07 | Goldenrod e Whitney | PENDENTE |
| 08 | Ecruteak e Morty | PENDENTE |
| 09 | Cianwood e Chuck | PENDENTE |
| 10 | Olivine e Jasmine | PENDENTE |
| 11 | Mahogany, Rocket e Pryce | PENDENTE |
| 12 | Blackthorn e Clair | PENDENTE |
| 13 | Liga Johto e Lance | PENDENTE |
| 14 | Lendários e pós-jogo | PENDENTE |
| 15 | Música, treinadores e portal | PENDENTE |
| 16 | Instalação, viagem e aceite final | PENDENTE |

## Regras obrigatórias antes de importar qualquer mapa

1. Não alterar nenhum MapID de Kanto/Decades; atribuir IDs de destino livres e fixos para Johto.
2. Não copiar MapInfos.rxdata, Tilesets.rxdata, Scripts.rxdata ou System.rxdata sobre game/. Reconstruir IDs/conexões com logs e rollback.
3. Piloto em .blue-work/johto-pilot, com saves separados. O botão **Testar Johto** nunca pode abrir Kanto como fallback.
4. Só liberar Johto como região inicial quando New Bark, a casa e a introdução estiverem prontas, com testes observáveis.
5. Comparar testes e hashes antes/depois de mudanças em plugins e mapas compartilhados. CI verde de um teste não valida toda a jogabilidade.
6. Não publicar músicas oficiais ou componentes de terceiros sem direitos e créditos verificados.

## Comandos quando a fonte local estiver disponível

Colocar o Map Pack extraído em .blue-work/johto-source (ou em subdiretório com Data/) e executar:

~~~powershell
# Somente leitura: não modifica game/ nem a fonte
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --game "game" --output ".blue-work/johto-audit.json"

# Testes sintéticos offline
python -m unittest discover -s tests -p "test_johto_source_audit.py" -v

# Regressão da tela e do circuito existente
python -m unittest discover -s tests -p "test_title_kanto.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
~~~

O auditor nunca instala conteúdo e grava apenas um JSON em .blue-work/. Se a saída já existir com dados diferentes, não a sobrescreve: use outro nome. Se a fonte real estiver ausente, falha explicitamente em vez de produzir mapa fictício.

## Critérios para aceitar a Etapa 01

- [ ] Fonte RMXP original preservada com SHA-256 e proveniência validada.
- [ ] Créditos e direitos revisados por recurso; sem republicação não autorizada.
- [ ] MapIDs/tile IDs de Johto e do jogo instalado inventariados.
- [ ] Risco de sobrescrita removido, rollback e cópia isolada definidos.
- [ ] Testes automatizados concluídos sem regressão e evidências documentadas.

**Próxima ação:** executar `audit_johto.py`, `plan_johto.py`, `stage_johto.py` e `verify_johto.py` sobre o pacote original e jogo instalados, quando presentes, de acordo com [o guia da Etapa 03](JOHTO_FASE_03_PREVIA_SEGURA.md). Não habilitar a Nova Partida Johto antes da Etapa 04. A fase permanece PARCIAL porque não há mapas reais auditados.
