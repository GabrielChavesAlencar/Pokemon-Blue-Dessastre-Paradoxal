# Sinnoh — Fase 01: prévia de geometria isolada (sem eventos doadores)

**Data:** 13/11/2026  
**Status:** conversor disponível no repositório; **ainda não aplicado a mapas reais**, e **não é instalador do Game.exe**. S07 permanece parcial, 6/9. As barras de aceitação continuam 0/13.

## Entrega do ChatGPT

O arquivo [convert_sinnoh_geometry.py](../scripts/regions/convert_sinnoh_geometry.py) implementa a transformação **em memória** da fonte RMXP para uma prévia de terreno. A fonte pode estar em um ZIP legitimamente obtido ou numa pasta local do projeto doador. A entrada exige:

1. [audit_sinnoh_rxdata.py](../scripts/regions/audit_sinnoh_rxdata.py) com `game/Data` real disponível e todos os arquivos/gráficos citados pela fonte presentes.
2. [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py) com IDs, símbolos e hashes reais, incluindo `plan_sha256`. O conversor recria a validação do plano com os dados da fonte e da instalação local.
3. `game/Data/MapInfos.rxdata` e `game/Data/Tilesets.rxdata` para compor **cópias** dos índices nativos; **esses arquivos são apenas lidos**, sem alterar o original.
4. Direitos/autorizações para usar a fonte **no escopo pretendido**. O script é apenas uma ferramenta; não verifica contratos de licença nem autoriza distribuir assets de terceiros.

### O que é realmente gerado

- `Data/MapNNN.rxdata` para os MapIDs **candidatos** do manifesto, com tabela de terreno da origem, largura, altura e tileset renumerado para a **cópia isolada**.
- `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata` **mesclados em memória** com os dados existentes do Blue: não sobrescrevem nem removem mapas anteriores na instalação principal.
- `Graphics/Tilesets/SN_Preview_*.png` e `Graphics/Autotiles/SN_Preview_*.png` apenas para a prévia local, com nomes prefixados e hash para evitar colisões.
- Hash SHA-256 dos índices nativos antes/depois, número de mapas/tilesets/gráficos e provas sintéticas de que os arquivos nativos não foram modificados.
- Modo padrão: **dry-run** com relatório JSON no terminal; modo opcional `--stage` exige explicitamente o SHA-256 retornado pelo dry-run e cria um diretório novo somente em `.blue-work/sinnoh-stage/`.

### O que é sempre removido ou bloqueado

- `@events={}` — não importa scripts Ruby, personagens, diálogos, portas, switches, prêmios nem lógica de batalha dos eventos doadores.
- `@encounter_list=[]` — não importa encounters/níveis do doador; usar o balanceamento do Blue posteriormente.
- `@autoplay_bgm=false`, `@autoplay_bgs=false` e áudio vazio — trilhas precisam passar pelo catálogo musical autorizado e pelo BlueMusic.
- Panoramas, fogs e battlebacks da fonte são desativados na prévia.
- Source transfer maps entram apenas na análise/grafo anterior. **Não existem warps jogáveis nesta prévia**; a reconstrução de eventos com coordenadas reais e handlers próprios do Blue é trabalho de uma fase posterior.
- IDs candidatos **não** são registrados como IDs definitivos; a reserva de Hoenn/Johto que ainda não aparece fisicamente em `game/Data` é um bloqueio pendente.
- Não escreve `System.rxdata`, `Scripts.rxdata`, PBS, arquivos `game/`, saves ou backups.

## Como executar depois de uma auditoria real

Em Windows, dentro da raiz do projeto, apenas quando o ZIP verdadeiro e a instalação local estiverem disponíveis:

```powershell
# 1. Auditar o conteúdo verdadeiro da fonte e do jogo principal
New-Item -ItemType Directory -Force .blue-work/sinnoh | Out-Null
python scripts/regions/audit_sinnoh_rxdata.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/rxdata-report.json

# 2. Após preencher a template só com hashes e IDs verificados
python scripts/regions/plan_sinnoh_remap.py --audit .blue-work/sinnoh/rxdata-report.json --request .blue-work/sinnoh/remap-request.json --output .blue-work/sinnoh/remap-plan.json

# 3. Dry-run da GEOMETRIA, sem criar arquivos
python scripts/regions/convert_sinnoh_geometry.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data --plan .blue-work/sinnoh/remap-plan.json --label sinnoh

# 4. Só se a prévia e direitos estiverem auditados: transação isolada.
# Substituir SHA_DO_DRY_RUN pelo valor real transaction.plan_sha256 do passo 3.
python scripts/regions/convert_sinnoh_geometry.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data --plan .blue-work/sinnoh/remap-plan.json --label sinnoh --stage --expected-dry-run SHA_DO_DRY_RUN
```

**O comando 4 não instala no Blue**; a saída fica em `.blue-work/sinnoh-stage/<label>-<hash-prefix>/` e não deve ser publicada no GitHub sem direitos específicos. Para reverter, executar `rollback(project,label,hash)` de [sinnoh_staging_transaction.py](../scripts/regions/sinnoh_staging_transaction.py), que só remove o stage se os hashes de todos os arquivos forem idênticos àqueles criados pela transação.

## Testes publicados

[tests/test_sinnoh_geometry_converter.py](../tests/test_sinnoh_geometry_converter.py) cria dois mapas RMXP **inteiramente sintéticos**, com uma música de exemplo, um script estrangeiro proibido, conexão fictícia entre mapas e gráficos PNG próprios de teste. Verifica as seguintes condições, sem usar assets do fangame:

- O script estrangeiro não aparece em nenhum `RPG::Map` gerado, pois os eventos são recriados vazios.
- BGM/BGS e encontros da fonte são eliminados.
- A geometria e a numeração de tilesets são preservadas/ajustadas apenas na cópia de prévia.
- Os mapas do Blue, seu `System.rxdata` e seus índices ficam com SHA-256 original.
- Dry-run não cria pastas; a transação pode criar e remover apenas o seu stage.
- Mudanças de plano ou fonte, gráficos faltantes e tabelas de terreno inválidas bloqueiam a transformação.

## Pendências verdadeiras para o Codex

1. Disponibilizar a fonte de Sinnoh com projeto editável e autorização; registrar SHA/MapInfos/tilesets e auditar o mapa real de Twinleaf, incluindo interiores, NPCs, itens, música e warps.
2. Auditar os IDs já instalados **e planejados** pelas outras regiões, inclusive Hoenn/Johto ainda não publicados. Comprovar compatibilidade caso alguma faixa ≥1000 seja necessária.
3. Executar o conversor com a fonte real, estudar os PNGs/tilesets, validar passabilidade, interior/exterior, prioridade de tiles, espaçamento e distância visual.
4. Programar eventos **autorais** e conexões reais na engine do Blue; criar o piloto próprio de Sinnoh, separar saves e assegurar o menu Testar Sinnoh.
5. Testar em `Game.exe` e Android/JoiPlay sem afetar Decades, Kanto, Johto e Hoenn. Documentar logs reais.

**Não** marcar S07/R08, Fase 01, nem nenhuma barra de jogabilidade como aprovada antes dessas comprovações.
