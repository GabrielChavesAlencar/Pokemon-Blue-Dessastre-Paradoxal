# Sinnoh S08 — Integridade cruzada de mapas, gráficos, scripts e dependências

**Entrega 16 da Barra A.** Completar **o código do validador de integridade** reutilizável no piloto Sinnoh, sem afirmar que existem mapas autorizados instalados ou que o Game.exe/Android foi executado.

## O que foi implementado

- [`audit_sinnoh_s08_resources.py`](../scripts/regions/audit_sinnoh_s08_resources.py) reúne as auditorias inertes [RXDATA](../scripts/regions/audit_sinnoh_rxdata.py) e [grafo de mapas](../scripts/regions/graph_sinnoh_maps.py). Com `--source`, identifica arquivos de mapas faltantes/órfãos, transfers estáticos quebrados, nomes e referências gráficas inválidos, possíveis colisões de MapIDs e comandos dinâmicos que exigem revisão manual. **Nunca executa scripts Ruby do doador**.
- Com `--overlay` e `--spec`, reaproveita o verificador transacional dos mapas e PBS do [instalador QA](../scripts/regions/install_sinnoh_qa_copy.py). Confere os **nove mapas e 24 eventos do piloto**, 16 warps, hashes SHA-256 dos arquivos finais, `Tilesets.rxdata`, referências de tilesets/autotiles e seus arquivos PNG (assinatura, IHDR, dimensões), plugins Ruby de introdução/QA e dependências declaradas. Rejeita qualquer arquivo ou recurso de configuração em desacordo com a base auditada.
- A fonte `game/` precisa existir localmente para uma execução com overlay real. O código **não inventa recursos**, não baixa Pokémon Ancient Platinum, não cria mapas e não distribui assets de terceiros. A verificação de PNG é **estrutural mínima**, não um teste de renderização/collision/passabilidade.
- Opcionalmente, `--qa` valida apenas uma cópia privada já existente, incluindo isolamento de saves, integridade dos plugins, hashes e ausência de aprovação de gameplay.
- [`sinnoh_s12_installer.py`](../scripts/regions/sinnoh_s12_installer.py) agora **exige auditoria S08 aprovada** antes de criar uma cópia de teste. O S12 segue com `dry-run` por padrão, e seu BAT continua bloqueando a instalação se faltarem os insumos autorizados.
- A [matriz S30](../scripts/regions/audit_sinnoh_s30_suite.py) passa a exigir o auditor e os [16 testes S08](../tests/test_sinnoh_s08_integrity.py), que incluem recursos e plugins faltantes, grafos com referências quebradas, gráficos inexistentes/PNG corrupto, symlinks, spoof de aprovação e proteção do jogo principal.

## Modos de auditoria

```bash
# Inspeção passiva de fonte RMXP ou ZIP autorizada
python scripts/regions/audit_sinnoh_s08_resources.py --source /caminho/autorizado

# Verificação privada do overlay já montado pelo fluxo de Sinnoh
python scripts/regions/audit_sinnoh_s08_resources.py \
  --overlay .blue-work/sinnoh-integration-v1 \
  --spec .blue-work/sinnoh-qa-spec.json

# Validação adicional de cópia QA previamente instalada, sem abrir Game.exe
python scripts/regions/audit_sinnoh_s08_resources.py \
  --overlay .blue-work/sinnoh-integration-v1 \
  --spec .blue-work/sinnoh-qa-spec.json \
  --qa .blue-work/game-sinnoh-qa-XXXXXXXXXXXX
```

**Política de falhas:** sem fonte/overlay, arquivos faltantes, gráficos malformados, hashes modificados ou dependências não satisfeitas, a ferramenta devolve falha, não um certificado de implantação. Um relatório de fonte com mapas/refs pendentes apresenta `BLOCKED_SOURCE_INTEGRITY` e código de saída diferente de zero. Mesmo uma conferência limpa usa `STATIC_INTEGRITY_VERIFIED_NOT_NATIVE_GAMEPLAY` e marca `native_qa_approved=false`, `import_allowed=false` e `source_rights_verified=false`.

## Critérios de aceite

Concluir S08 no seu **escopo de código e prevenção de regressões** após CI CH19, matriz S30, portal e CH20 aprovados, com merge na `main`. A S08 fica `done` quando essas condições forem atendidas. A Barra A evolui de **15/32 (46%) para 16/32 (50%)**; **5 tarefas parciais e 11 pendentes**. A Barra E permanece **20/20 (100%)** e as barras **B/C/D permanecem 0/13**.

**Não aceito como prova:** execução apenas em fixtures sintéticas, GitHub Actions sem Game.exe, suposta licença dos assets ou 44 casos de QA Windows/JoiPlay ainda não observados. O progresso nativo continua separado.
