# Johto — desenvolvimento OFFLINE 11/12: Violet, Torre Sprout, Falkner e Zephyr

**Data:** 13/11/2026. **Estado:** prévia privada real construída com Ruby Marshal e PBS nativos, **sem executar Game.exe, sem atualizar game/ e sem instalar a região pelo Blue-Story.exe**.

## Resumo verificável

A fonte de mapas de Johto forneceu o **exterior real de Violet City (Map602, 70×49)**, mas **não interiores**, NPCs, treinadores, encontros ou sprites da cidade. A implementação desta etapa **não afirma recuperar os interiores oficiais HGSS**: usa layouts de prévia autorais, com tiles já presentes em `Inside.png` do Blue/Decades.

| Ambiente | MapID | Fonte e situação |
|---|---:|---|
| Violet City (exterior) | 602 | Mapa já existente: acrescentadas três portas na cópia privada |
| Ginásio de Falkner | 677 | Novo interior autoral de 20×16 tiles; Falkner posicionado |
| Torre Sprout 1F | 678 | Novo interior autoral de 20×16; Sage Nico |
| Torre Sprout 2F | 679 | Novo interior autoral de 20×16; Sage Troy |
| Torre Sprout 3F | 680 | Novo interior autoral de 20×16; Ancião Li |
| Centro Pokémon | 681 | Novo interior autoral de 20×16; atendente **sem função de cura** |

O gerador `scripts/regions/build_johto_violet_stage11.py` usa a saída privada `.blue-work/johto-staging-routes-v1` da etapa 10, exige **77 mapas**, seus IDs e `BLUE_ROUTE10_PREVIEW_ONLY_NOT_PLAYABLE`, recusa sobrescrita de MapIDs existentes e cria **uma pasta nova** `.blue-work/johto-staging-violet-v1`. Copia os MapNNN existentes e altera apenas **Map602**, acrescentando **Map677–681**. `MapInfos.rxdata` recebe **5 registros novos** vinculados hierarquicamente a Violet e à Torre; **os 284 registros anteriores permanecem iguais**. `Tilesets.rxdata` é preservado integralmente.

### Ligações propostas — não validadas no motor

São **10 eventos reversíveis `RPG::EventCommand(201)`**, com chegadas fora dos tiles que ativam o evento, para reduzir loops de retorno:

- Cidade **(37,21)** ↔ Torre 1F **(9,13)**, chegada na cidade (37,22) e na torre (9,12).
- Cidade **(43,30)** ↔ Ginásio **(9,13)**, chegada na cidade (43,31) e no ginásio (9,12).
- Cidade **(32,30)** ↔ Centro **(9,13)**, chegada na cidade (32,31) e no centro (9,12).
- Torre 1F **(14,5)** ↔ 2F **(5,10)**; chegadas (5,9) e (14,6).
- Torre 2F **(14,5)** ↔ 3F **(5,10)**; chegadas (5,9) e (14,6).

A análise estática dos RXDATA nativos encontrou âncoras na mesma componente caminhável por ambiente: **Violet exterior 427 tiles; ginásio 231; cada sala da Torre 230; Centro 230**. Isso **não prova** a correção visual da fachada, a interpretação de toque, NPCs, colisões dinâmicas ou o posicionamento de spawns no Game.exe. Portas e sprites permanecem propostas.

### NPCs e batalhas preparadas

**5 eventos novos `RPG::EventCommand(355)`:** Falkner no ginásio, Li na Torre 3F, Nico e Troy nos andares inferiores e atendente no Centro. Os handlers são allowlisted em `scripts/regions/JohtoViolet.rb`; o Centro fornece somente um aviso, **não cura Pokémon** antes de integração/QA. Sprout Sage registra vitória por save e não concede Zephyr. Falkner e Li usam versão **1 no Master** e **0 no normal**.

Os dois PBS gerados da base Blue são:

- `PBS/trainer_types_johto_violet.txt`: novos tipos `BLUE_JOHTO_FALKNER` (origem `BIRDKEEPER`), `BLUE_JOHTO_ELDER` e `BLUE_JOHTO_SAGE` (origem `GENTLEMAN`).
- `PBS/trainers_johto_violet.txt`: **4 perfis (Falkner, Li, Nico, Troy) × versões 0/1 = 8 equipes**, duas espécies no normal e quatro no Master. As espécies e os golpes aprendidos até os níveis-base foram conferidos com `PBS/pokemon.txt` e `PBS/moves.txt` do Blue exportado.

| Treinador | Normal (2 Pokémon) | Master (4 Pokémon) |
|---|---|---|
| Falkner | Pidgey 9, Pidgeotto 11 | Pidgey, Pidgeotto, Hoothoot e Spearow (11) |
| Ancião Li | Bellsprout 8, Hoothoot 10 | Bellsprout, Hoothoot, Hoppip e Spearow (10) |
| Sage Nico | Bellsprout e Hoothoot (7) | Bellsprout, Hoothoot, Rattata e Hoppip (7) |
| Sage Troy | Bellsprout e Hoppip (8) | Bellsprout, Hoppip, Hoothoot e Pidgey (8) |

**Balanceamento:** as equipes PBS contêm níveis-base para conferência. O sistema de combate real deverá continuar utilizando o compartilhado `BlueStory.stage`, `BlueCampaign.common_level/wild_level` e `BlueTrainerMoves` (70% normal, 90% Master e 45% selvagem), com esmeraldas somadas globalmente; **essa integração não foi testada no motor**.

### Insígnia Zephyr — sem concessão indevida

A regra Ruby **já existente** em `JohtoViolet.rb` somente chama `BlueRegions.award(state, "JOHTO", "ZEPHYR")` **após `TrainerBattle.start` retornar vitória**. Sem inicial/rival e sem o arquivo de prova `Data/blue-johto-violet-ready.txt`, as batalhas permanecem bloqueadas. A etapa 11 **não cria o arquivo marcador de prontidão**, não concede insígnias e não modifica os flags nativos de Decades/Kanto. Os testes Ruby foram ampliados para Sage, Master, perda, Zephyr única, save/reload e Rock Smash restrito a Johto.

### Auditoria dos dados privados

O estágio foi montado sobre `Johto_Fase10_Staging_Routes_Private`. A serialização Ruby Marshal reabriu os mapas novos e o exterior editado:

- **77 mapas da entrada**; **1 mapa anterior alterado (Map602)**; **76 mapas anteriores preservados byte a byte**.
- **5 MapNNN adicionados (677–681)**, totalizando **82 mapas** na saída.
- `MapInfos` expandido por 5 registros; **todos os anteriores comparados sem alterações**.
- `Tilesets` preservado bit a bit; **10 transferências + 5 NPCs** nos mapas respectivos.
- SHA-256 PBS `trainer_types_johto_violet.txt`: `37958eceade434036f4abca1e58365218b2111bed13ca6cc21237fef2b742da0`.
- SHA-256 PBS `trainers_johto_violet.txt`: `6f18f727350db1ec2e59ed097b63da075d789082b8e08ea556d056b7fd031a18`.

O ZIP privado foi reaberto e validado por CRC sem falhas. Seu conteúdo permanece **fora do GitHub público**.

### Bloqueios para instalar/jogar

1. **Sprites específicos de Falkner, Li, Sage e atendente** não foram encontrados na exportação nativa auditada. Os eventos possuem nomes de sprites simbólicos que precisam de arte autorizada antes da instalação final; a prévia não deve ser considerada visualmente concluída.
2. **Os cinco interiores são layouts próprios provisórios**, não versões fiéis dos interiores HGSS. Fachadas/escadas precisam de revisão visual e gameplay.
3. Falta compilar os **PBS de 8 versões na engine** e testar níveis, combate real, badges/save, NPCs, evolução e HM.
4. O Centro não cura; essa funcionalidade ainda requer implementação antes da liberação de Violet.
5. O **`Blue-Story.exe` ainda não instala automaticamente Johto**. A montagem integral, backups, download lícito de assets e testes reais fazem parte das dependências da etapa 12 e do ciclo jogável.

## Ferramentas e testes

- `data/regions/johto-stage11-violet.json` — contrato de cinco mapas, dez warps, cinco NPCs, quatro perfis PBS e Zephyr.
- `scripts/regions/build_johto_violet_stage11.py` — criação Python reproduzível da prévia isolada com proteção contra overwrites, colisões e supostas aprovações.
- `tests/test_johto_violet_stage11.py` — 10 testes Python sintéticos para layout, warps, MapInfos preservado, Master e PBS.
- `tests/johto_violet_runtime.rb` + `tests/test_johto_violet_runtime.py` — regressão do registro regional real em Ruby sintético, agora incluindo sages e Falkner Master.

```powershell
python scripts/regions/build_johto_violet_stage11.py
python -m unittest discover -s tests -p "test_johto_violet_stage11.py" -v
python -m unittest discover -s tests -p "test_johto_violet_runtime.py" -v
```

**Barra OFFLINE: 11/12 (91,7%). JOGÁVEIS: 0/13. TESTADAS no Game.exe: 0/13.**

**Próxima 12/12:** auditoria de integração/empacotamento de toda a cadeia de Johto, detecção de recursos ausentes e contrato de instalação automática segura pelo `Blue-Story.exe`. O término de 12/12 **não autorizará marcar região jogável** antes do teste de verdade no executável.
