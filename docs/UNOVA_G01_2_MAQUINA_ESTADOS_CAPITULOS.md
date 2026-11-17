# Unova — G01.2: máquina de estados dos capítulos (somente simulação)

**Escopo:** implementação de progressão **offline**, sem instalar scripts no jogo, manipular saves, executar Game.exe, alterar MapInfos, criar MapIDs ou liberar Unova como jogável. Baseia-se estritamente no contrato de estado versionado **G01.1 / schema_version=1**, no catálogo simbólico U03 e nos **13 eventos U07**.

## Entregas

- [Contrato das transições](../data/regions/unova-g01-chapter-transitions.json) — doze transições lineares: inicialização do CH00→CH01, seguida de CH01→CH02 até CH11→CH12. Todos os destinos são capítulos simbólicos preexistentes, **sem MapIDs ou coordenadas**.
- [Motor offline Python](../scripts/regions/audit_unova_g01_chapter_machine.py) — funções `load_project`, `validate_rules`, `validate_progression`, `available`, `step` e `demo`. Cada operação retorna uma cópia do estado; não muta o objeto de entrada.
- [64 testes sintéticos](../tests/test_unova_g01_chapter_machine.py) — negativos para capítulos pulados, missões adiantadas, flags indevidas, ausência de pré-requisitos, eventos repetidos ou fora de ordem, batalhas com resultados inválidos, versões de estado incompatíveis e dados nativos inventados.
- CI Linux/Windows com `--check`, `--simulate-demo`, compilação Python e regressões G01.2. **Nenhum comando lê saves do jogador.**

## Operações disponíveis

| Ação | Condições | Efeito somente no estado simulado |
|---|---|---|
| `begin` | CH00 e nenhuma missão/flag concluída | Ativa CH01, missão de Nuvema e área simbólica de referência |
| `record_u07` | CH01 ativo; evento U07 seguinte e todas as dependências marcadas | Registra a flag de conclusão do evento; para o presente de inicial exige Snivy/Tepig/Oshawott; para batalhas exige resultado explícito |
| `complete` | Missão ativa; sinal `SIMULATED_ONLY_NO_NATIVE_APPROVAL`; CH01 requer todos os 13 U07 concluídos | Marca a missão atual como `completed` e a flag `UNOVA_FLAG_CHXX_COMPLETED` |
| `advance` | Missão e flag do capítulo corrente concluídas; transição seguinte registrada | Ativa apenas o capítulo seguinte e sua missão, sem saltos e sem alterar a instalação |

Para as **duas primeiras batalhas de rivais**, o simulador permite `WIN` ou `LOSS`, conforme U07. A primeira batalha contra **N exige `WIN`**. A escolha do inicial é conferida como entrada sintética, mas a G01.2 **não cria/entrega** Pokémon nem itens reais e não guarda dados de party.

Do CH02 ao CH12 ainda faltam eventos nativos dos ginásios, chefes, Liga e pós-jogo. O motor **não afirma que foram vencidos**: completar essas missões só é possível com um gatilho que se identifica explicitamente como `SIMULATED_ONLY_NO_NATIVE_APPROVAL`. Esse gatilho serve exclusivamente para testar o encadeamento dos capítulos e **não é prova jogável**.

## Validações e integridade

- Somente estados do schema G01.1 v1, `region=UNOVA`, `campaign=WHITE_BW`, `state_status=SIMULATED_ONLY_NOT_GAME_SAVE`.
- Sem campos desconhecidos, missões futuras pré-ativadas, flags de capítulo puladas ou flags U07 não consecutivas.
- Missões anteriores devem constar `completed`; a atual somente `active` ou `completed`; os indicadores de missão e conclusão devem ser coerentes.
- A área de história do checkpoint deve corresponder ao capítulo atual, sem coordenadas físicas, MapID ou declaração de checkpoint verificado no Game.exe.
- Regras de transição, política de batalha, ordem de eventos e desabilitação de instalação são checadas contra os catálogos de referência.
- Ações inválidas lançam `ValueError` e **preservam integralmente o estado original**.
- O estado após CH12 concluído não oferece próxima transição.

## Validação offline

```bash
python scripts/regions/audit_unova_g01_chapter_machine.py --check
python scripts/regions/audit_unova_g01_chapter_machine.py --simulate-demo
python -m unittest discover -s tests -p 'test_unova_g01_chapter_machine.py' -v
```

O demo percorre toda a sequência sintética CH00→CH12, registra os 13 eventos U07 em ordem e não produz arquivos de save. Nunca marque `game_exe_tested=true`, `can_install=true`, `native_save_modified=true` ou `rewards_granted=true` com base nesses testes.

## Progresso e fases seguintes

Após CI aprovado, a G01.2 eleva somente a **barra G** para **10/32 (31%)**. **Barra A=0/8**, **Unova jogável=0/32** e região **planned** permanecem iguais.

- **G01.3:** recompensa única, eventos repetidos, reentrada segura; requer regras específicas e testes próprios.
- **G01.4:** serialização/migração sintética de estado v1 com ida/volta e incompatibilidades; **não é adaptador de save nativo**.
- Importação de mapas, NPCs, conteúdo real e validação do Game.exe/JoiPlay exigem fontes autorizadas e testes nativos separados.
