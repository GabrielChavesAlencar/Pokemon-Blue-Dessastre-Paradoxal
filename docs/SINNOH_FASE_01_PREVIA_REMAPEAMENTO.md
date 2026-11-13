# Sinnoh — Fase 01: planejamento e prévia de remapeamento de MapIDs

**Data:** 13/11/2026  
**Fase:** 01/12 — **PARCIAL**, sem instalação/jogabilidade.  
**Situação:** os scripts de auditoria, grafo, capacidade, planejamento explícito e staging local já estão implementados. **Não há mapas reais importados nem ID definitivo reservado**. A fase 01 **não** está integralmente aprovada.

## 1. O que já pode ser feito pelo GitHub

- [audit_sinnoh_source.py](../scripts/regions/audit_sinnoh_source.py): inventário superficial e preflight de fonte ZIP/pasta.
- [audit_sinnoh_rxdata.py](../scripts/regions/audit_sinnoh_rxdata.py): analisa **dados internos inertes** de MapInfos/Tilesets/mapas, transferências estáticas, comandos dinâmicos não executados, referências gráficas, source hashes, MapIDs físicos e ausentes.
- [graph_sinnoh_maps.py](../scripts/regions/graph_sinnoh_maps.py): compõe grafo dirigido de transferências dos dados reais, componentes isolados, dangling warps e alcance opcional com MapID inicial confirmado.
- [plan_sinnoh_capacity.py](../scripts/regions/plan_sinnoh_capacity.py): estima a capacidade **sem alocar**. Preserva Johto 600–999 e bloqueia a suposição de IDs >=1000.
- [plan_sinnoh_remap.py](../scripts/regions/plan_sinnoh_remap.py): **NOVO**. Gera apenas um plano explícito, amarrado aos hashes de todos os mapas doadores, com símbolos Sinnoh únicos, destinos não ocupados e lista de transferências estáticas a remapear. Rejeita mudanças incompatíveis com o plano anterior.
- [sinnoh_staging_transaction.py](../scripts/regions/sinnoh_staging_transaction.py): dry-run por SHA-256, staging local transacional e rollback validado **dentro de `.blue-work/sinnoh-stage/`**. Não converte mapas, nem instala no jogo.

As 32 entregas e suas barras independentes estão em [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md); **S07 continua parcial**, apesar do planejador de remapeamento já implementado.

## 2. Proteções obrigatórias para a conversão real

1. A auditoria deve partir de **fonte RMXP editável obtida legitimamente e com direitos confirmados para o uso pretendido**. Dados de um jogo compilado sem autorização não são uma fonte de mapas reutilizáveis.
2. A cópia `game/Data` precisa ser auditada no mesmo momento: presença real de `MapInfos.rxdata`, mapas físicos, reservas do circuito Kanto/Johto/Hoenn/Decades e saves protegidos. **Ausência física de MapID não prova disponibilidade**.
3. O planejamento desta fase só aceita **IDs de destino entre 1 e 599**, todos explicitamente informados, não ocupados e não reservados em outras regiões. Isto **não** declara que sejam IDs realmente livres: a homologação depende do Codex/local. A faixa 600–999 permanece de Johto. Destinos >=1000 dependem de teste separado de compatibilidade, portanto o script atual rejeita-os.
4. Cada mapa deve ser informado por `MapID de origem`, `símbolo SINNOH_...` e hash SHA-256 correspondente ao arquivo verdadeiro. Todos os mapas doadores presentes precisam participar do plano, sem referências ocultas. MapInfos órfão, mapa órfão, gráfico faltante ou warp apontando para mapa ausente **bloqueiam a proposta**.
5. Se existe plano anterior, não mudar o ID, símbolo ou o hash da origem de nenhum mapa previamente mapeado sem planejamento formal de migração de saves. O script rejeita qualquer alteração deste tipo.
6. **Nenhuma proposta permite instalar**: `can_install=false`, `may_stage_real_map_data=false`, sem execução de scripts doadores. O plano não altera `game/`, `Plugins/`, PBS, saves, scripts ou outros mapas. As transferências são propostas **declarativas**, não alterações em eventos de um Game.exe.
7. Antes de converter geometria e eventos, o Codex precisa auditar: tileset/autotiles e seus offsets, warps condicionais, eventos comuns, scripts embutidos, BGM, NPCs, gráficos de personagem, encounters, PBS, switches/variáveis e mapa das conexões. Sempre usar motor de batalha do Blue/Decades, nunca copiar scripts da engine do jogo doador.
8. Auditar as reservas de Hoenn e Johto **não instaladas**. O arquivo opcional `--reserved` lista os IDs já conhecidos, mas **não serve como declaração de que todas as reservas futuras estejam verificadas**.

## 3. Uso pelo Codex quando a fonte real estiver disponível

Executar a partir da raiz do projeto, sem tocar no `game/`:

```powershell
New-Item -ItemType Directory -Force .blue-work/sinnoh | Out-Null

python scripts/regions/audit_sinnoh_rxdata.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/rxdata-report.json

python scripts/regions/graph_sinnoh_maps.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/map-graph.json

python scripts/regions/plan_sinnoh_capacity.py --source "C:\CAMINHO\FONTE_SINNOH_AUTORIZADA.zip" --game-data game/Data > .blue-work/sinnoh/capacity.json

# Criar cópia LOCAL da template; NUNCA preencher com IDs inventados.
Copy-Item data/regions/sinnoh-remap-request.template.json .blue-work/sinnoh/remap-request.json
# Editar .blue-work/sinnoh/remap-request.json somente com todos os IDs e hashes reais.

python scripts/regions/plan_sinnoh_remap.py --audit .blue-work/sinnoh/rxdata-report.json --request .blue-work/sinnoh/remap-request.json --output .blue-work/sinnoh/remap-plan.json
```

**Template:** [sinnoh-remap-request.template.json](../data/regions/sinnoh-remap-request.template.json). Ela vem **vazia de propósito** e deverá falhar caso seja passada diretamente: não temos MapIDs reais validados.

**Como preencher a template sem inventar dados:**

- `source_zip_sha256` = relatório RXDATA `source_zip_sha256`; para diretório local pode ser `null`.
- `source_mapinfos_sha256` e `source_tilesets_sha256` = hashes auditados.
- `source_map_hashes` = objeto `"source_map_id": "sha256"` para **todos** os mapas de `maps[]` do relatório.
- `mapping` = objeto `"source_map_id": destination_id`; definir somente após mapear a ocupação real e reservas externas. Não inventar IDs para satisfazer os testes.
- `symbols` = objeto `"source_map_id": "SINNOH_NOME_DA_AREA"`; nomes únicos, sem colidir com Kanto/Johto/Hoenn.

**Para planos anteriores já auditados**, incluir também:

```powershell
python scripts/regions/plan_sinnoh_remap.py --audit .blue-work/sinnoh/rxdata-report.json --request .blue-work/sinnoh/remap-request.json --previous .blue-work/sinnoh/remap-plan-anterior.json --reserved .blue-work/sinnoh/reservas-outras-regioes.json --output .blue-work/sinnoh/remap-plan-v2.json
```

O arquivo `reservas-outras-regioes.json` tem o formato `{"schema":1,"region":"SINNOH","protected_ids":[...]}` com IDs *reais* de todas as regiões identificadas; **não preencher artificialmente**. Saídas dentro de `.blue-work`, nunca versionar MapInfos/RXDATA da fonte ou o relatório privado.

**Testes do código (não equivalem a gameplay):**

```powershell
python -m unittest discover -s tests -p "test_sinnoh_remap.py" -v
python -m unittest discover -s tests -p "test_sinnoh_graph.py" -v
python -m unittest discover -s tests -p "test_sinnoh_staging_transaction.py" -v
python -m unittest discover -s tests -v
```

## 4. Gates para a fase 01 realmente subir

- [x] Auditor RMXP somente leitura e grafo declarativo de conexões em código.
- [x] Estudo de capacidade conservador com reserva de Johto intocada.
- [x] Planejamento explícito de MapIDs sem colisões e com hashes de origem.
- [x] Staging local transacional com SHA-256 e rollback para **arquivos já transformados**, sem escrever em `game/`.
- [ ] Fonte editável real de Sinnoh com proveniência e direitos.
- [ ] MapInfos, mapas, NPCs, warps, tilesets, gráficos, PBS, áudio e eventos auditados no ZIP real.
- [ ] Reservas Kanto/Johto/Hoenn/Decades e saves físicos conferidos no mesmo baseline; suporte a IDs ≥1000 verificado se necessário.
- [ ] Conversão RXDATA completa com IDs, tilesets, eventos, recursos e ligações adequadas ao motor do Blue.
- [ ] Piloto isolado com início real em Twinleaf e entradas/saídas funcionais.
- [ ] Testes Windows reais e não regressão Decades/Kanto/Johto/Hoenn.

**Conclusão:** o módulo de **plano e segurança** foi publicado. A integração real do jogo depende de materiais externos e provas que não existem neste ambiente; **Fase 01 continua parcial e todas as barras de aceite permanecem 0/13**.
