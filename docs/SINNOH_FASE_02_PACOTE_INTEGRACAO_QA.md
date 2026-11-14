# Sinnoh — pacote de integração segura do piloto novo (não jogável)

**Atualização:** 13/11/2026. **Situação:** montador de preparação publicado, sem mapa real de Sinnoh importado, sem instalação no Game.exe e sem fases jogáveis aprovadas. Não versionar recursos externos sem autorização.

## Objetivo

Integrar **apenas numa pasta de preparação privada**, com validação cruzada:

1. [convert_sinnoh_geometry.py](../scripts/regions/convert_sinnoh_geometry.py): stage local de geometria autorizada com MapInfos/Tilesets e imagens do terreno.
2. [build_sinnoh_twinleaf_events.py](../scripts/regions/build_sinnoh_twinleaf_events.py): stage com **24 eventos Blue** nos nove mapas, três Poké Bolas físicas e 16 transições, cada uma com coordenadas conferidas na fonte real.
3. [build_sinnoh_barry_pbs.py](../scripts/regions/build_sinnoh_barry_pbs.py): draft com **três versões PBS de Barry** e golpes existentes no Blue.

O novo montador [prepare_sinnoh_pilot_bundle.py](../scripts/regions/prepare_sinnoh_pilot_bundle.py) confere os três estágios e adiciona o módulo autoral [SinnohPilot.rb](../scripts/regions/SinnohPilot.rb) com um `meta.txt` de plugin numa pasta **privada**. Ele não instala no jogo, não executa código do doador e não valida direitos externos.

## Proteções que o montador aplica

- Rejeita stages que não estejam dentro de `.blue-work/sinnoh-stage/`, symlinks, arquivos extras e arquivos cujo hash ou manifesto não correspondam à transação original.
- Exige nove MapIDs reais e distintos **entre 1 e 599** para o início de Sinnoh; bloqueia IDs em `game/Data`/`MapInfos.rxdata` ou referenciados pelos PBS atuais. **MapIDs futuros reservados de outras regiões exigem auditoria humana separada.**
- Recompila os eventos a partir da geometria e da especificação **local auditada**, conferindo byte a byte com o stage de eventos recebido: não aceita Ruby/script/eventos de terceiros adicionados depois.
- Confirma que o `MapInfos.rxdata` e o `Tilesets.rxdata` da prévia preservam os registros nativos, e que o overlay não contém `System.rxdata`, `Scripts.rxdata`, saves ou o piloto legado `SinnohPreview.rb`.
- Valida os hashes do draft PBS de Barry por [verify_sinnoh_barry_pbs.py](../scripts/regions/verify_sinnoh_barry_pbs.py). **Não compila PBS nem cria `Data/blue-sinnoh-rival-ready.txt`.**
- Modo padrão é **dry-run**, não cria nada. O `--publish` somente cria uma pasta **nova** em `.blue-work` (sem sobrescrever arquivos existentes).
- Não contém `Game.exe`. Um overlay íntegro ainda **não é jogável** até ser integrado e testado numa cópia do jogo, com saves separados.

## Passo a passo local (Codex/Windows)

Depois de obter uma fonte Sinnoh **editável e autorizada**, auditar os arquivos reais e finalizar os MapIDs sem conflito usando [o plano da Fase 01](SINNOH_FASE_01_PREVIA_REMAPEAMENTO.md).

**1.** Fazer uma **cópia privada** da especificação de Twinleaf para preencher apenas posições, sprites e hashes que forem conferidos na fonte real:

```powershell
New-Item -ItemType Directory -Force .blue-work/sinnoh | Out-Null
Copy-Item data/regions/sinnoh-twinleaf-events.json .blue-work/sinnoh/twinleaf-events-local.json
# NÃO inventar MapIDs, x, y, sprite ou flags de verificação.
```

**2.** Gerar primeiro a geometria e depois o stage de eventos próprios do Blue. Os placeholders abaixo são caminhos/hashes reais retornados pelos comandos anteriores, **não** os números de MapIDs do exemplo:

```powershell
python scripts/regions/convert_sinnoh_geometry.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data --plan .blue-work/sinnoh/remap-plan.json --label sinnoh-terreno
python scripts/regions/convert_sinnoh_geometry.py --source "C:\CAMINHO\SINNOH_AUTORIZADA.zip" --game-data game/Data --plan .blue-work/sinnoh/remap-plan.json --label sinnoh-terreno --stage --expected-dry-run SHA_REAL_GEOMETRIA

python scripts/regions/build_sinnoh_twinleaf_events.py --geometry-stage ".blue-work/sinnoh-stage/PASTA_GEOMETRIA_REAL" --spec .blue-work/sinnoh/twinleaf-events-local.json --label sinnoh-story
python scripts/regions/build_sinnoh_twinleaf_events.py --geometry-stage ".blue-work/sinnoh-stage/PASTA_GEOMETRIA_REAL" --spec .blue-work/sinnoh/twinleaf-events-local.json --label sinnoh-story --stage --expected-dry-run SHA_REAL_EVENTOS
```

**3.** Gerar e verificar os PBS do Barry:

```powershell
python scripts/regions/build_sinnoh_barry_pbs.py --game game --output .blue-work/sinnoh-barry-draft-v1
python scripts/regions/verify_sinnoh_barry_pbs.py --game game --draft .blue-work/sinnoh-barry-draft-v1
```

**4.** Validar o pacote integrado primeiro em **dry-run**. O comando falhará se a template mantiver campos `null`/`false`, se os stages não estiverem assinados, se houver conflitos no jogo ou se o PBS mudar:

```powershell
python scripts/regions/prepare_sinnoh_pilot_bundle.py --geometry-stage ".blue-work/sinnoh-stage/PASTA_GEOMETRIA_REAL" --story-stage ".blue-work/sinnoh-stage/PASTA_EVENTOS_REAL" --spec .blue-work/sinnoh/twinleaf-events-local.json --barry-draft .blue-work/sinnoh-barry-draft-v1 --game game
```

**5.** Só após verificar o relatório, repetir o mesmo comando com:

```powershell
--publish --output .blue-work/sinnoh-qa-overlay-v1
```

Isso produz apenas o **overlay privado**. Não copiar automaticamente para `game/`, pois não contém `Game.exe`, salvamento isolado, runtime compilado nem prova de autorização/redistribuição.

## O que falta para um piloto jogável

1. Confirmar direitos de mapas/tilesets/sprites, posições de eventos, colisões, ligação das nove áreas e recursos de personagem em dados **reais**.
2. Auditar as reservas futuras de Johto/Hoenn/Kanto/Decades além dos arquivos físicos locais. **O piloto antigo usa 800–805, dentro da faixa protegida de Johto**, e não deve ser mesclado.
3. Montar **outra instalação QA** em diretório separado com saves isolados, reconciliar os plugins com o motor Blue e compilar as três versões de Barry no Essentials.
4. Testar spawn no quarto, mãe, Rowan, Barry, três Poké Bolas físicas, 16 warps, save/load, vitória/derrota, 70% normal e 90% Master.
5. Validar no Windows e Android/JoiPlay antes de elevar qualquer das 13 fases técnicas/jogáveis/QA. O marcador de Barry continua **desabilitado**.

## Testes de código sem ROM

```powershell
python -m unittest discover -s tests -p "test_sinnoh_pilot_bundle.py" -v
python -m unittest discover -s tests -p "test_sinnoh_*.py" -v
ruby tests/sinnoh_pilot_runtime.rb scripts/regions/SinnohPilot.rb
```

Usam dados inteiramente sintéticos, não comprovam o jogo rodando. O resultado fica registrado em [SINNOH_PROGRESSO.md](SINNOH_PROGRESSO.md) e [sinnoh-progress.json](../data/regions/sinnoh-progress.json).
