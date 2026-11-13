# Johto — etapa OFFLINE 08/12: mãe, Elm, três Poké Bolas interativas e Silver

**Registro técnico de 13/11/2026.** A prévia privada dos 77 mapas foi atualizada **sem abrir `Game.exe` e sem alterar `game/`, Kanto, Decades, Hoenn, jogos salvos ou dados do instalador.** Os RXDATA/PNG nativos permanecem **somente no ZIP privado** enviado na conversa.

## Resultado da implementação

A fase 07 preparou seis eventos próprios de transferência entre quarto 2F/casa 1F/New Bark/laboratório. A fase 08 **preserva integralmente essas seis transferências** e acrescenta **seis eventos próprios de história** em três mapas.

| Evento | Mapa | Posição (x,y) | Handler próprio |
|---|---|---|---|
| Mãe | `Map675` (casa 1F) | `(6,8)` | `BlueJohtoPilot.mother` |
| Professor Elm | `Map676` (laboratório) | `(10,4)` | `BlueJohtoPilot.elm` |
| Poké Bola de Chikorita | `Map676` | `(7,7)` | `BlueJohtoPilot.choose_starter_from_ball(:CHIKORITA)` |
| Poké Bola de Cyndaquil | `Map676` | `(10,7)` | `BlueJohtoPilot.choose_starter_from_ball(:CYNDAQUIL)` |
| Poké Bola de Totodile | `Map676` | `(13,7)` | `BlueJohtoPilot.choose_starter_from_ball(:TOTODILE)` |
| Rival Silver | `Map625` (Rota 29) | `(71,17)` | `BlueJohtoPilot.rival` |

Os novos eventos contêm **um comando 355 Ruby** chamando somente métodos allowlisted do módulo **`BlueJohtoPilot`**, terminando com código 0. As seis transferências existentes continuam tendo código **201**; nenhum evento externo foi importado.

### Três Poké Bolas: escolha individual, não menu do Elm

O código `scripts/regions/JohtoPilot.rb` agora tem o método `choose_starter_from_ball(species)`. A espécie vem **fixada no próprio evento**, não de um menu de opções. O método:

- exige que o estado da região atual seja `JOHTO`, isolando Decades/Kanto;
- exige que o jogador converse primeiro com o Elm (flag `elm_intro`);
- admite somente `CHIKORITA`, `CYNDAQUIL` ou `TOTODILE`;
- só marca `starter` e `starter_received` após `pbAddPokemonSilent` retornar sucesso;
- recusa uma segunda escolha no mesmo save, mesmo depois de carregar/salvar;
- preserva o balanceamento original do rival: Chikorita → Cyndaquil, Cyndaquil → Totodile, Totodile → Chikorita.

A antiga entrada `choose_starter` permanece como aviso compatível **sem entregar Pokémon**, para não reabrir o menu antigo.

**Correção de alcance dos pedestais:** as três bolas da fase 06 eram tiles gráficos da camada 2 nas posições `(7,6)`, `(10,6)`, `(13,6)`. Os pedestais bloqueiam passagem na linha 7, então uma interação a partir da linha 8 ficaria dois tiles distante. Na fase 08 os três tiles gráficos antigos são removidos e **cada sprite `Object_Ball` vira um evento na borda frontal do pedestal, na linha 7**, alcançável com o botão de ação da linha 8. Isso evita bolas duplicadas. O pedestal permanece no tilemap. A movimentação real e os cliques via mouse ainda requerem prova no motor.

### Silver e sua batalha

O evento de Silver na Rota 29 foi compilado com o sprite nativo `NPC_HGSS_Silver.png`. A coordenada `(71,17)` passou na checagem de flags estáticas e está fora das três linhas principais de saída leste da Rota 29, **mas não foi testada no Game.exe**.

A API `BlueJohtoPilot.rival` existente bloqueia a batalha quando o PBS de treinador não tiver o marcador `BLUE_JOHTO_RIVAL_V1_READY`. **Não presumir combate funcional até a etapa 09/12**, quando os três times e os arquivos PBS serão preparados.

## Compilação e provas

O script **`scripts/regions/build_johto_story_v1.py`** valida as seis transferências e seus hashes da etapa 07 antes de tocar em qualquer mapa, exige exatamente os NPCs/espécies permitidos, checa sprites PNG reais, pontos e adjacência, e publica apenas uma pasta **nova**:

```
.blue-work/johto-staging-story-v1/
  Data/Map625.rxdata     # Silver
  Data/Map675.rxdata     # Mãe + 2 warps preservados
  Data/Map676.rxdata     # Elm + 3 bolas clicáveis + warp preservado
  Data/Map674.rxdata     # Quarto + warp preservado, inalterado
  Data/Map600.rxdata     # Cidade + 2 warps preservados, inalterado
  Data/MapInfos.rxdata   # preservado
  Data/Tilesets.rxdata   # preservado
  johto-stage.json
  johto-warp-preview.json
  johto-story-preview.json
  ...demais mapas e gráficos privados de Johto
```

**Validação com os RXDATA privados reais:** extraídos do ZIP enviado do Blue/Decades e dos estágios anteriores, os arquivos foram montados em Ruby Marshal, gravados e reabertos com sucesso.

- **6 eventos de história acrescentados** e **6 warps anteriores preservados**.
- Exatamente **3 Poké Bolas estáticas removidas da camada de tiles** e substituídas por eventos de ação.
- Dos **77 MapNNN**, **somente Map625, Map675 e Map676 mudaram**. Os outros **74** permaneceram byte a byte iguais; `MapInfos.rxdata` e `Tilesets.rxdata` também.
- SHA-256 dos arquivos privados desta geração: `Map625 8d990cf6ce98ffa4830587dfc0e4b5123dcbbb2147bfa0a7c5e46949ec2f58b1`; `Map675 9766f7b87550af7e8a820ff929a6893ca9342c7e1559f7a2ff03e698fe4f3dbc`; `Map676 eca8e126650ec584d70333d1e705c041a8953d871d296c596fcab682da60e843`.
- Contrato e regressões sintéticas: `tests/test_johto_story_v1.py` (dez cenários), além do harness `tests/johto_pilot_runtime.rb` atualizado para o novo método individual e verificação de isolamento de regiões, não duplicação e save/reload.

**Importante:** arquivos gerados pelo Python podem ter SHA binário diferente dos gerados por Ruby enquanto representarem os mesmos eventos, pois o Marshal pode serializar referências/strings de maneira diferente. Os resultados devem ser conferidos estruturalmente; cada build mantém seus próprios hashes no manifesto.

### Como reproduzir a prévia OFFLINE

Com a base instalada e as etapas 04–07 preparadas em `.blue-work`:

```powershell
python scripts/regions/build_johto_story_v1.py
python -m unittest discover -s tests -p "test_johto_story_v1.py" -v
python -m unittest discover -s tests -p "test_johto_story_runtime.py" -v
```

Se o Windows não tiver Ruby, o harness Ruby será pulado; isso **não** deve contar como prova de gameplay. Reexecutar o gerador na mesma pasta de saída falha, em vez de sobrescrever testes/saves.

### Limitações intencionais

O `Blue-Story.exe` **ainda não instala automaticamente esses mapas**, e o jogo original `game/` não foi modificado. A etapa 09/12 tratará os PBS de iniciais e times do rival; a 10/12 preparará encontros e treinadores; a 11/12 preparará Violet/Sprout/Falkner; e o 12/12 auditará e empacotará a prévia. A instalação automática e a liberação jogável continuam bloqueadas até a integração segura e os testes reais de engine.

**Progresso: desenvolvimento OFFLINE 8/12 (66,7%) · Fases JOGÁVEIS 0/13 · Fases TESTADAS no Game.exe 0/13.**
