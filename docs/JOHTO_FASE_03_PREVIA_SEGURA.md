# Johto — Etapa 03/16: plano de MapIDs e prévia isolada de terreno

**Estado:** infraestrutura técnica implementada na branch main, aguardando arquivo original autorizado de mapas, auditoria real e verificação de jogabilidade. **Etapa 03 ainda PARCIAL.**  
**Regra:** nunca modificar o jogo Decades/Kanto ou os saves só porque uma ferramenta de importação existe.

## Entregas reais

| Arquivo | Objetivo |
|---|---|
| [scripts/regions/plan_johto.py](../scripts/regions/plan_johto.py) | Propor IDs exclusivos 600–999 sem colisões com os mapas já existentes ou MapInfos; aceitar plano anterior para preservar IDs congelados |
| [scripts/regions/stage_johto.py](../scripts/regions/stage_johto.py) | Preparar cópia de *geometria somente*, sem eventos, áudio, Scripts.rxdata ou Game.exe, dentro de .blue-work/ |
| [scripts/regions/verify_johto.py](../scripts/regions/verify_johto.py) | Comprovar que os MapInfos/Tilesets nativos permaneceram idênticos, todos os IDs novos estão livres e nenhum evento/áudio estrangeiro foi importado |
| [tests/test_johto_map_plan.py](../tests/test_johto_map_plan.py) | Validar IDs estáveis, ampliação futura, bloqueios de seleção não auditada e colisões com os mapas de Decades/Kanto |
| [tests/test_johto_stage.py](../tests/test_johto_stage.py) | Criar fonte sintética RMXP e provar importação de terreno, remoção de eventos e músicas, hashes, não modificação do jogo e bloqueio de mapas alterados |

## Por que a prévia não pode ser ativada agora

A referência de mapas é o [Map Pack de Johto](https://www.eeveeexpo.com/resources/828/). **O arquivo original não está presente no GitHub nem foi disponibilizado para auditoria neste atendimento.** Os únicos mapas usados nos testes são *dados RMXP sintéticos gerados pelos próprios testes*, sem a geografia real de Johto.

O manifesto [data/regions/johto-source.json](../data/regions/johto-source.json) continua com mapa simbólico vazio, SHA-256 do pacote ausente, `mapping_verified=false` e `import_enabled=false`. Qualquer tentativa de plan/preview com esses dados deve produzir BLOQUEADO, sem tocar na instalação. Não preencher IDs, licenças ou hashes por suposição.

A prévia criada por `stage_johto.py` é apenas um diretório de dados de terreno: **não abre no Game.exe diretamente**, não contém as casas, eventos HGSS, Professor Elm, treinadores ou música. Ela **não** é o piloto jogável solicitado pela Etapa 04.

## Procedimento exato após obter a fonte válida

1. Colocar o pacote original ZIP/RAR de Johto em uma pasta ignorada pelo Git (por exemplo, `.blue-work/johto-source/original.zip`) e extrair seu projeto RMXP também dentro de `.blue-work/johto-source/`. Não executar o EXE ou scripts que possam estar no pacote.
2. Conferir créditos, permissões de uso de mapas/tiles/autotiles e calcular SHA-256 do arquivo original.
3. Examinar `Data/MapInfos.rxdata` e o relatório da auditoria; selecionar **somente os IDs de mapas que de fato são Johto**, nunca os mapas de Kanto presentes no mesmo pacote. Preencher `data/regions/johto-source.json` com `source.archive_sha256`, `maps` (ID real → nome simbólico JOHTO_...) e `mapping_verified=true` **após validação manual dos IDs**. Manter `import_enabled=false` sempre nessa prévia.
4. Auditar fonte original e cópia instalada para registrar também os IDs existentes do jogo:

```powershell
python scripts/regions/audit_johto.py --source ".blue-work/johto-source" --archive ".blue-work/johto-source/original.zip" --game "game" --output ".blue-work/johto-audit.json"
```

5. Construir o plano **sem escrever no jogo**:

```powershell
python scripts/regions/plan_johto.py --audit ".blue-work/johto-audit.json" --output ".blue-work/johto-map-plan.json"
```

**Muito importante:** em toda atualização posterior de Johto, passar `--previous` com a versão anterior do JSON de plano para preservar MapIDs e saves antigos. Nunca deixar o projeto recalcular IDs sem a tabela histórica.

6. Gerar a prévia de terreno em uma **pasta nova** (o destino anterior não é sobrescrito):

```powershell
python scripts/regions/stage_johto.py --source ".blue-work/johto-source" --game "game" --archive ".blue-work/johto-source/original.zip" --audit ".blue-work/johto-audit.json" --plan ".blue-work/johto-map-plan.json" --output ".blue-work/johto-staging-v1"
```

7. Verificar a prévia contra a instalação original sem modificar nada:

```powershell
python scripts/regions/verify_johto.py --preview ".blue-work/johto-staging-v1" --game "game"
python -m unittest discover -s tests -p "test_johto*.py" -v
```

> Esses comandos são implementados, mas a sequência **não pode completar com o pacote original ausente**. Os testes sintéticos podem ser executados sem pacote nem ROM.

## Gates antirregressão

- Mapeamento de origem e destino é explícito. O primeiro ID previsto parte de 600 **ou de um ID superior, se ocupado**. A atribuição não renumera mapas anteriores; fonte e instalação precisam ser revalidadas antes de cada importação.
- MapInfos e Tilesets existentes são lidos como dados; qualquer mudança em seus hashes entre auditoria e staging provoca bloqueio.
- Nenhum evento Ruby, NPC, texto, música ou mudança de save é importado da fonte. Apenas terreno, tilesets e PNGs necessários são copiados para um diretório **não executável** de prévia.
- Arquivos de gráfico com caminhos suspeitos, PNG inválido, symlinks, destinos existentes, IDs repetidos ou conflito de caixa alta/baixa são rejeitados.
- Se a prévia falhar, só uma pasta nova é descartada; Kanto/Decades não têm rollback necessário porque não receberam alterações.
- A CI de Kanto e as regressões do Blue Studio devem continuar verdes, além dos testes próprios de Johto.

## Critérios pendentes para concluir 03/16

- [ ] Executar o scanner sobre o pacote original e congelar o primeiro conjunto de MapIDs reais.
- [ ] Gerar prévia com mapas reais, sem assets quebrados e com provenance/rights adequados.
- [ ] Confirmar passabilidade e conexões dos mapas em janela real no Windows, sem executar scripts da fonte; a Etapa 04 cuidará do gameplay e dos interiores.
- [ ] Inspecionar o relatório final de todos os mapas, gráficos e dependências e aprovar a integração *somente* em cópia isolada.

**Próximo desenvolvimento:** Etapa 04 (New Bark Town, casa, Elm e começo do jogador), **somente após** obter e auditar os mapas reais, ou construir cenários originais próprios com procedência verificável. O botão `Testar Johto` continuará exibindo preparação enquanto não existir piloto real.

**Barras de Johto:** implementação técnica **0/16**, aceite de jogabilidade **0/16** — nenhuma etapa totalmente aceita.
