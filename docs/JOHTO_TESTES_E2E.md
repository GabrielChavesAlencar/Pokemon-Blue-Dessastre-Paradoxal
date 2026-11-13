# Johto — testes ponta a ponta, instalação segura e rollback (Etapa 16)

**Estado em 13/11/2026: BLOQUEADO para jogabilidade.** O repositório não contém o pacote de mapas Johto verificado, MapIDs reais, PBS compilado nem a comprovação dos áudios. Os testes sintéticos não substituem Game.exe.

## Comandos existentes, execução segura

Na raiz do repositório:

```powershell
# Diagnóstico da fase 16: read-only, código 0 mesmo com bloqueios conhecidos
python scripts/regions/install_johto.py --dry-run

# O mesmo relatório, código 2 quando ainda faltar algo
python scripts/regions/install_johto.py --strict

# Imprime/gera relatório exclusivo de uma área ignorada do Git
python scripts/regions/install_johto.py --report ".blue-work/johto-release-2026-11-13.json"

# Modo de instalação deliberadamente bloqueado; não altera game/
python scripts/regions/install_johto.py --apply

# Suíte automatizada
python -m unittest discover -s tests -p "test_johto_phase16_release.py" -v
python -m unittest discover -s tests -p "test_regions.py" -v
python -m unittest discover -s tests -p "test_johto*.py" -v
python scripts/music/audit_johto_phase15.py
```

**Importante:** `--apply` ainda **não é um instalador transacional funcional**. Ele sempre falha fechado, pois não há pacote integrado cuja instalação possa ser validada. Não habilitar uma instalação sem primeiro desenvolver o copiador transacional, os testes de rollback e a verificação byte a byte no destino.

## Pré-requisitos reais (ordem)

1. **Fonte e direitos.** Obter localmente ZIP legítimo do Map Pack em `.blue-work/`. Registrar SHA-256 em `data/regions/johto-source.json`; auditar imagens, licenças, créditos e dependências. Não distribuir material de terceiros sem direitos.
2. **Extrair e auditar.** `prepare_johto_source.py` extrai arquivos RMXP/PNG permitidos apenas dentro de `.blue-work/`. `audit_johto.py` inventaria MapInfos, mapa, tileset, eventos, dimensões e vínculos; `plan_johto.py` fixa IDs livres ≥600. Não sobrescrever Kanto/Decades.
3. **Prévia geométrica.** `stage_johto.py` e `verify_johto.py` validam apenas terreno, **sem NPCs, áudio ou eventos**. O relatório de geometria não pode habilitar a região.
4. **Construir piloto executável separado.** Integrar, em uma **cópia do jogo**, casa do jogador e laboratório Elm em New Bark, regiões 05–14, diálogos e NPCs, tiles, conexões, 8 badges, Hall of Fame próprio, liga e lendários. Compilar PBS e equipes normal/Master; cadastrar encontros e HMs reais.
5. **Música.** Aprovar cada faixa legalmente distribuível, com hash, loop, fade e fallback; compilar apenas em MapIDs verificados de Johto. As 53 cues atuais são rótulos, não arquivos.
6. **Regiões e viagem.** Validar New Bark casa (`start`), chegada (`travel_point`) e NPC (`npc_point`) em mapa físico; testar Kanto ↔ Johto, falha no warp, rollback, Box cheia, Pokémon especiais com e sem 8 badges e o mesmo arquivo de save. **Johto → Hoenn não deve teleportar enquanto Hoenn não tiver mapas instalados.**
7. **Prova real.** Passar os 13 campos obrigatórios do [schema de release](../data/regions/johto-release-proof.schema.json) e gravar em uma cópia **somente após a aceitação de gameplay**. Verificar hashes de MapInfos, Tilesets, mapa de início e mapa do NPC. Johto continua bloqueada sem isso.
8. **CI e plataformas.** Confirmar Blue Studio, Kanto nativo, Decades, Windows/Game.exe, JoiPlay, save/reload/PC, transporte, o portal e os testes manuais específicos de cenas e áudio. Não declarar sucesso enquanto qualquer regressão estiver vermelha.

## Matriz de jogo real (evidências por área)

| Área | Ação real obrigatória | Critérios |
|---|---|---|
| New Bark, Route 29, Cherrygrove | Spawn **dentro de casa**, Elm/inicial/rival, portas e retorno | Jogável sem travar, salvar/recarregar |
| Violet, Route 32, Azalea | Falkner/ZEPHYR, Bugsy/HIVE, Cut, Rock Smash | Derrota não dá badge, insígnia única |
| Ilex, Goldenrod | Farfetch'd, Whitney/PLAIN, Rádio | Sem portões invisíveis ou recompensas duplicadas |
| Ecruteak | Burned Tower, rival, Morty/FOG, Surf | Uso de HM condicionado à badge **de Johto** |
| Olivine/Cianwood | Lighthouse, pedido e consumo de SecretPotion, Chuck/STORM, Fly, Jasmine/MINERAL | Ampharos curado uma vez, salvar/recarregar |
| Mahogany/Lake | Red Gyarados, Rocket HQ, três Electrode, Pryce/GLACIER | Fuga não conclui, sem prêmios duplicados |
| Blackthorn | Ice Path com colisão, Strength, Clair, Dragon Master, RISING | Oitava badge **após prova**, Waterfall local |
| Liga | Route 27/26, Tohjo Falls, Victory Road, Will/Koga/Bruno/Karen/Lance | Perda reinicia Elite, Kanto intocada |
| Hall of Fame | Cena, callback e gravação real | Somente **save confirmado** conclui Johto |
| Lendários | HG/SS/Crystal, Bell Tower, Whirl Islands, quatro entradas/saídas | Captura/fuga sem duplicar; não ficar preso |
| Pós-jogo | Ruins/Unown, Suicune, Mt Silver/Red, rematches | Não simular o que não está instalado |
| Portal/Áudio | Locais verdadeiros, equipes e variações PBS, 2 cartões, 53 cues a validar | Nenhum dado ou música ficticiamente aprovado |
| Transporte | NPC New Bark, Kanto↔Johto, party e Boxes, interrupção e rollback | Sem perder Pokémon, sem alterar saves anteriores |

**Todas as linhas estão pendentes de execução no motor real.** Qualquer resultado de um mock Ruby deve ser registrado como *teste sintético*, nunca *jogabilidade aprovada*.

## Checklist de transação e rollback — implementação futura

- [ ] **Dry-run:** comparar hashes originais de `Game.exe`, `Data/MapInfos.rxdata`, `Data/Tilesets.rxdata`, Scripts/PBS e mapas; salvar plano exato de adições/alterações, IDs de Johto e espaço necessário.
- [ ] **Preparar cópia:** nenhum arquivo real de `game/` é editado durante a auditoria. Preferir criar `.blue-work/johto-pilot` como cópia isolada, com backups identificados por SHA e diretório exclusivo.
- [ ] **Conferir hash novamente:** rejeitar aplicação se arquivo original mudou entre o plano e a transação.
- [ ] **Aplicar atomicamente:** criar mapas/arquivos temporários, compilar/importar cada evento/PBS no piloto e substituir apenas os arquivos planejados após verificação. **Jamais copiar `Scripts.rxdata` estrangeiro**, substituir saves ou remover arquivos originais.
- [ ] **Smoke test antes de publicar:** Game.exe inicia, Kanto/Decades funcionam, Johto tem oito ginásios, Hall of Fame real, inventário/Box/saves confiáveis e saída de cada dungeon.
- [ ] **Rollback:** se qualquer teste ou gravação falhar, restaurar byte a byte todos os originais a partir dos backups, remover apenas arquivos novos introduzidos pela transação e verificar os hashes de novo. Registrar relatório de falha.
- [ ] **Release:** somente depois de validação Windows/JoiPlay, atualização do portal e provas por evento, escrever marcador de início e manifesto `VERIFIED_PLAYABLE` no **piloto testado**, e considerar instalação no jogo principal.

Não escrever `Data/blue-johto-install.json` ou `Data/blue-johto-start.txt` no jogo principal por sucesso de uma auditoria. Os hashes e os 13 campos `checks` devem corresponder ao conteúdo efetivamente aprovado, com coordenação entre técnico, gameplay, QA e licenças.

## Observações de integração com código existente

O `BlueRegionStart` já recusa `{ }` no manifesto Johto e exige SHA-256 dos MapInfos/Tilesets/mapas além de `start`, `travel_point` e `npc_point` consistentes. O `BlueRegionTravel` preserva a transação atual de Box/party com rollback, e só anuncia Johto depois de instalação e condições do circuito. O NPC físico de New Bark é criado **somente em memória no mapa validado**, após a Liga de Johto; não altera os RXDATA de Kanto/Decades. São **proteções preparatórias**, não uma certificação do motor real.

O piloto nativo de Kanto pode falhar por razões independentes de Johto. Não desabilitar SHA, CI, lógica da Liga de Kanto nem os controles de saves para obter barra verde.
