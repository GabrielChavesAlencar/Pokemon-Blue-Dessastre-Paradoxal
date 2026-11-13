# Johto — Etapa OFFLINE 12/12: auditoria integrada e pacote PRIVADO de 82 mapas

**Data de auditoria:** 13/11/2026.  
**Estado:** **auditoria offline concluída**, pacote privado criado e íntegro. **NÃO é uma versão instalável/jogável**. Nenhum `Game.exe` foi iniciado; o jogo, as instalações originais de Decades/Kanto e os saves não foram modificados.

## O que entrou no pacote

O pacote de auditoria privada reúne pela primeira vez os produtos das etapas **04–11** e as dependências que estavam separadas:

| Fonte | Arquivos integrados | Verificação |
|---|---|---|
| Staging Johto etapas 04–08 | Geometria e eventos de New Bark/Elm/Silver, 77 mapas intermediários | Eventos e hashes inspecionados |
| Etapa 09 | `trainer_types_johto.txt` e `trainers_johto.txt` | Três versões de Silver, todas nível 5 |
| Etapa 10 | `encounters_johto_routes.txt` e `trainers_johto_routes.txt` | Seis tabelas dia/noite e dez times de cinco treinadores |
| Etapa 11 | `trainer_types_johto_violet.txt` e `trainers_johto_violet.txt` | Oito versões: Falkner, Li, Nico e Troy |
| Conexões | `map_connections_johto_offline12.txt` | 42 linhas originais + 2 inferidas = **44**, sem duplicação |
| Gráficos | 5 tilesets usados, 14 autotiles referenciados, 10 sprites de eventos | Completados com a própria exportação `johto-pilot-inputs.zip` do usuário |

O auditador `scripts/regions/package_johto_offline12.py` verifica **82 MapNNN de IDs 600–681**, **16 warps `code 201`**, **16 eventos de ações `code 355`**, parâmetros de transferência, whitelists exatas dos handlers Ruby, posições, hashes, seções PBS, probabilidade 100% por tabela e ausência de marcadores de `ready`. O código escreve **somente um ZIP novo** em `.blue-work`, recusa overwrite, symlinks, destinos fora do workspace e caminhos inseguros.

**Os arquivos `JohtoPilot.rb`, `JohtoRouteTrainers.rb` e `JohtoViolet.rb` aparecem dentro do ZIP sob `review_only/Ruby/` apenas para revisão**; não são automaticamente adicionados aos plugins da instalação. O arquivo `OFFLINE_ONLY_NOT_INSTALLABLE.txt` declara que a prévia não deve ser instalada.

### Correções de sprites encontradas pela auditoria completa

A auditoria da etapa 11 ocorreu em uma cópia reduzida da base, que não continha `Graphics/Characters`; por isso relatou quatro sprites ausentes. Ao conferir a **exportação completa** `johto-pilot-inputs.zip`, dois nomes já estavam corretos e havia alternativas nativas para os outros dois:

| Evento | Nome antigo (não encontrado) | Sprite comprovado na exportação |
|---|---|---|
| Falkner | `NPC_HGSS_Falkner` | Já existia — nenhuma troca |
| Sage Nico/Troy | `NPC_HGSS_Sage` | Já existia — nenhuma troca |
| Ancião Li — Map680 | `NPC_HGSS_Elder_Li` | `NPC_HGSS_Elder` |
| Atendente — Map681 | `NPC_HGSS_Nurse` | `NPC_DPP_PokeCenter_Nurse` |

Os dois nomes foram corrigidos no **contrato do estágio 11 no GitHub** e no gerador. O empacotador da etapa 12 corrige **somente a cópia privada** de Map680 e Map681, exige que os novos PNG existam e não reescreve os mapas da etapa 11. O visual da enfermeira é da geração DPP, não uma afirmação de fidelidade ao HGSS. Ainda faltam **gráficos de batalha dos novos trainer types**, diferentes dos sprites de personagens do mapa.

### Prova com os arquivos privados reais

Foi criado um ZIP de auditoria **separado** após leitura de `Johto_Fase11_Staging_Violet_Private` e de `johto-pilot-inputs.zip` fornecido pelo usuário:

- **82 mapas** na cópia, com apenas **Map680 e Map681 alterados**, para corrigir o `@character_name` de dois eventos; **80 mapas anteriores byte a byte iguais**.
- `MapInfos.rxdata` com **289 registros** (incluindo os cinco acrescentados na etapa 11), idêntico ao estágio 11; `Tilesets.rxdata` idêntico ao estágio 11.
- Todos os mapas reabertos com **Ruby Marshal**; **32 eventos exclusivos**, **16 transferências** + **16 scripts de NPC/treinador**, nenhum evento externo importado.
- **10 sprites de personagens** selecionados diretamente da exportação nativa, mais `Inside.png`, `water2.png`, `Waterfall2.png` e `Tall Grass.png`, necessários aos tilesets/autotiles anteriores.
- **7 arquivos PBS dentro da cópia privada**: seis drafts das fases 09–11, mais `map_connections_johto_offline12.txt`. O número de times de treinador distintos é **21** (Silver 3, rotas 10 e Violet 8).
- **44 conexões**: 42 originais mais as duas inferidas que ligam Route29–Cherrygrove e Route31–Violet. São candidatas de geometria: **a engine não as validou**.
- ZIP de **1.698.201 bytes**, SHA-256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49`; integridade CRC aprovada, sem `Game.exe`, sem saves e sem arquivos executáveis.

O ZIP privado desta conversa é uma **captura gerada com Ruby Marshal diretamente dos RXDATA do usuário**. O código versionado no GitHub reconstrói o equivalente sobre a instalação do Blue, gerando um ZIP próprio com hashes possivelmente diferentes (o Ruby e o serializador Python podem representar objetos Marshal com bytes diferentes). **Compare os significados dos eventos, seus hashes por build e os bloqueios, não assuma o mesmo SHA-256 de dois builds diferentes.**

## O que a etapa 12 NÃO faz

O avanço **12/12 (100%)** refere-se **somente ao checklist de desenvolvimento e auditoria offline**. **Não marca a etapa jogável** e não prova que a instalação do jogo funcionará sem bugs.

O instalador `scripts/regions/install_johto.py` continua com `--apply` bloqueado por projeto. **Não alterei o `Blue-Story.exe` nem habilitei a opção de instalação de Johto**, porque isso seria prematuro enquanto faltam:

1. Implementar a instalação **transacional** em uma cópia isolada, com backup/rollback de MapInfos, Tilesets, scripts, PBS, gráficos e saves.
2. Confirmar licenças/autorizações de distribuição dos recursos de mapas, música e sprites. O ZIP privado não autoriza publicar recursos no GitHub.
3. Compilar `trainers*.txt`, `trainer_types*.txt` e `encounters*.txt` no Pokémon Essentials real e confirmar todos os IDs, sprites e efeitos de batalha.
4. Implementar cura no Centro Pokémon de Violet; revisar identidade visual dos interiores provisórios.
5. Testar os caminhos, eventos, salvamento/carregamento, escolha de starter, rival, Falkner/Zephyr, Master, insígnias/esmeraldas globais, HM e trocas de região em uma cópia do `Game.exe`.
6. Regressões Windows e JoiPlay com testes nativos sem modificar Kanto/Decades.

O arquivo de contrato `data/regions/johto-stage12-package-contract.json` mantém os estados `can_install=false`, `gameplay_playable=false`, `tested_in_game=false` e `ready_marker_created=false`; os checks de release de `johto-release-proof.schema.json` continuam abertos.

### Como reproduzir o pacote offline

Com o projeto local, `game/` nativo e as prévias anteriores preparadas em `.blue-work/`:

```powershell
python scripts/regions/package_johto_offline12.py ^
  --stage .blue-work/johto-staging-violet-v1 ^
  --rival .blue-work/johto-rival-pbs09-linked ^
  --connections .blue-work/johto-connections-preview.txt ^
  --game game ^
  --output .blue-work/johto-offline12-preview.zip
```

Isso **não executa `Game.exe` e não instala Johto**. Para os testes:

```powershell
python -m unittest discover -s tests -p "test_johto_offline12.py" -v
python -m unittest discover -s tests -p "test_johto_violet_stage11.py" -v
python -m unittest discover -s tests -p "test_johto_violet_runtime.py" -v
```

## Barras independentes

- **Desenvolvimento OFFLINE:** **12/12 — 100%**.
- **Fases JOGÁVEIS no Game.exe:** **0/13 — 0%**.
- **Fases TESTADAS no Game.exe:** **0/13 — 0%**.

**Próxima fase depois da 12/12:** integração para cópia de teste da engine + assets/licenças + compilação dos PBS; depois QA real e somente então liberação de `Blue-Story.exe`. A conclusão do trabalho offline não substitui essas validações.
