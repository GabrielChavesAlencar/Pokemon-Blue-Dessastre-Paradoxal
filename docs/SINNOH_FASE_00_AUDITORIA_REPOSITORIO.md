# Sinnoh — Fase 00: auditoria do repositório (parte executável aqui)

**Data:** 13/11/2026  
**Escopo:** repositório GitHub da `main`, seus contratos e scripts. **Não é auditoria de mapa-fonte real nem do `game/` local.**  
**Situação:** **parcial**, sem liberação para importar mapas e sem incremento das barras globais de Sinnoh.

## 1. Verificações realizadas

1. **Estrutura Git:** inspeção da árvore recursiva pública do repositório, incluindo `scripts/regions`, `data/regions`, `docs`, `tests` e `site/public/data`. Foram encontrados os pipelines existentes de Kanto/Johto/Hoenn e **nenhum projeto-fonte Sinnoh importado no GitHub**.
2. **Contrato de região:** `site/public/data/regions.json` já registra `SINNOH` com `status: planned`, circuito Decades → Kanto → Johto → Hoenn → **Sinnoh** → Unova, oito insígnias `COAL, FOREST, COBBLE, RELIC, FEN, MINE, ICICLE, BEACON` e regras de HM de Platinum (`DEFOG: RELIC`, `SURF: FEN`). **Não alterar esses dados como se a região estivesse pronta.**
3. **Menu:** `scripts/battle_polish/TitleKanto.rb` registra `Testar Sinnoh` depois de `Testar Kanto` e `Testar Johto`, com lançador e marcador próprios. `tests/title_kanto_runtime.rb` / `tests/test_title_kanto.py` cobrem a ordenação simbólica, os índices originais do carregador e a prevenção de recursão. **Não existe ainda o pacote real para lançar.**
4. **Proteção de recursos:** `.gitignore` exclui `/game/`, `/.blue-work/`, saves e `*.rxdata`. A proteção existente não é prova de não regressão nativa; em particular, MapIDs e saves **reais** precisam ser conferidos em Windows.
5. **Ferramenta criada:** `scripts/regions/audit_sinnoh_source.py` usa somente leitura: aceita arquivo ZIP ou pasta de projeto local, rejeita caminhos perigosos/symlinks/duplicações, verifica `Data/MapInfos.rxdata` e `Data/Tilesets.rxdata`, conta MapIDs, calcula hash de ZIP e compara os IDs com `game/Data` quando informado. **Não extrai, executa nem instala arquivos da fonte**.
6. **Testes criados:** `tests/test_sinnoh_source_preflight.py` valida o registrador e os contratos do auditor por **fixtures sintéticas**; os casos não são prova de que as cidades de Sinnoh estejam presentes ou jogáveis.
7. **Proveniência:** `data/regions/sinnoh-source.json` aponta Ancient Platinum como candidato e registra falta de hash de fonte real, mapa de IDs, direitos e piloto. Não simula autorização ou content completeness.

## 2. Bloqueios comprovados nesta etapa

| Requisito Fase 00 | Verificação possível pelo GitHub | Resultado |
|---|---|---|
| Fonte Ancient Platinum `.rxdata` legítima | Não anexada e não está no repositório como projeto-fonte editável | **BLOQUEADO** |
| Autorização de uso/redistribuição dos assets doadores | Página pública não substitui licença por recurso | **PENDENTE** |
| Estado real dos MapIDs/tilesets locais de Decades/Kanto/Johto/Hoenn | `game/` excluído do GitHub | **BLOQUEADO sem cópia local** |
| Plano de IDs sem colisão | Precisa da tabela `MapInfos.rxdata` local e teste de 4+ dígitos | **PENDENTE** |
| Twinleaf real, interiores, eventos, NPCs e itemização | Mapas Sinnoh ainda não auditados em dados reais | **BLOQUEADO** |
| `Testar Sinnoh` na documentação e no menu Ruby | Código e testes criados | **IMPLEMENTADO no repositório; instalação/GUI pendente** |
| Piloto Sinnoh real e segregação de saves | Precisa de mapas e `Game.exe` | **PENDENTE** |
| Game.exe/JoiPlay sem regressão | Não executável com os recursos disponíveis neste ambiente | **PENDENTE** |

**Observação sobre The Pokémon World Project - Sinnoh:** o diretório externo foi identificado, mas continha apenas dois arquivos de mapa na verificação anterior. **Não** considerá-lo solução pronta para a região completa.

## 3. Execução reproduzível (sem escrever no jogo)

**Agora, mesmo sem fonte local**, na raiz do repositório:

```powershell
python scripts/regions/audit_sinnoh_source.py
python -m unittest discover -s tests -p "test_sinnoh_source_preflight.py" -v
python -m unittest discover -s tests -p "test_title_kanto.py" -v
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
```

O relatório de preflight sem `--source` registra bloqueios de propósito. Ele **não** declara que a Fase 00 foi aprovada.

**Quando o Codex tiver ZIP legítimo e `game/` local**, usar os comandos detalhados em [SINNOH_CODEX_PENDENCIAS.md](SINNOH_CODEX_PENDENCIAS.md), ID **C00**. Salvar a saída em `.blue-work/sinnoh/preflight.json` e publicar apenas `docs/SINNOH_FASE_00_AUDITORIA_LOCAL.md` (com hashes/relatórios, sem dados de terceiros).

## 4. Conclusão e próximas ações

- **Feito pelo ChatGPT/GitHub:** análise, plano operacional, botão seguro de título, dados de proveniência, auditor pré-instalação e testes estáticos.
- **Codex/local C00:** examinar fonte permitida, validar `MapInfos`/`Tilesets`/`MapXXX` verdadeiros, inventariar os IDs de todas as regiões reais instaladas e gerar auditoria com bloqueios.
- **Codex/local C01–C02:** depois de C00 aprovado, construir importador transacional e o piloto real exclusivo de Sinnoh. Não criar fallback para Johto/Hoenn.
- **ChatGPT permanece responsável** por novas análises, correções e testes de código versionado; o MD do Codex é um backlog de impossibilidades locais, não uma transferência da responsabilidade de todas as tarefas.

**Barras conservadoras:** técnica **0/13**, aceite jogável **0/13**. O progresso parcial da Fase 00 e a opção de menu **não** equivalem a uma fase integral concluída.
