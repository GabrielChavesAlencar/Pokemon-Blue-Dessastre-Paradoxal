# Johto dentro do Decades — integração da campanha principal

**Atualizado:** 15/11/2026  
**Situação real:** o Blue-Story.exe agora verifica Johto depois de Kanto/Hoenn e produz relatório local. **Johto ainda NÃO foi instalada, liberada no Novo Jogo ou certificada como jogável.** Os controles de segurança continuam ativos.

## Objetivo

Johto deve compartilhar o Game.exe e o perfil de saves do Decades com Kanto e Hoenn. No futuro, o menu de Novo Jogo inicia no quarto de New Bark e a viagem regional chega **fora** da casa, perto do agente regional. O sistema já existente de Box, itens-chave/HMs regionais, emblemas, nível escalado e retrocesso por derrota não deve ser alterado pelo importador. O piloto isolado não é substituto para esse comportamento.

## Fonte privada já localizada e verificada

- `Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip`, SHA-256 `74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49`.
- 82 mapas `Map600` a `Map681` (74 do terreno e 8 interiores), 44 conexões, 21 equipes PBS, 6 encontros iniciais, 32 eventos e gráficos de campo.
- ZIP de origem de Johto v1: SHA-256 `5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715`. A autorização para redistribuir os assets permanece pendente.
- O manifesto do OFFLINE 12 declara `not_playable=true` e `can_install=false`. É uma **prévia privada de auditoria**; nunca deve ser copiado diretamente sobre `game/`.
- O `johto_qa.py` consegue auditar e preparar **cópia privada** com reparos adicionais de New Bark, Sprout e Violet. O seu overlay QA altera `System.rxdata`, `Scripts.rxdata`, `mkxp.json`, `Game.ini` e cria `Johto pilot.json`: essas alterações de isolamento **NÃO podem ser reaproveitadas** na instalação principal.

## O que foi adicionado ao fluxo de atualização

O `scripts/install_game.py` chama `scripts/regions/auto_integrate_johto.py` **depois** de atualizar Kanto e Hoenn, pelo mesmo `Blue-Story.exe`, sem exigir outro BAT.

O verificador:
1. Não escreve mapas, PBS, plugins, `Game.ini`, `Scripts.rxdata`, saves ou marcadores falsos na pasta `game/`.
2. Identifica um eventual pacote OFFLINE 12 em `.blue-work/johto-offline12-preview.zip` ou caminhos conhecidos, verifica o SHA-256, os 82 mapas, metadados e CRC.
3. Se detectar uma instalação prévia, revalida os 13 critérios documentados de liberação, hashes dos mapas e arquivos essenciais; não aceita um `blue-johto-start.txt` isolado.
4. Registra o status em `.blue-work/johto-main-install-status.json`. Não impede a execução de Decades/Kanto/Hoenn caso Johto continue ausente.
5. Mantém a seleção de Johto e o destino do agente bloqueados até haver prova real.

**Status possíveis:** `awaiting_johto_installable_release`, `offline_preview_not_installable`, `offline_bundle_invalid`, `existing_install_needs_review`, `already_integrated_verified`, `no_game_skipped`, `foreign_game_skipped`.

Verificação local sem instalar:

```powershell
python scripts/regions/auto_integrate_johto.py
python -m unittest discover -s tests -p test_johto_main_auto.py -v
```

## Trabalho restante para JOHTO aparecer diretamente no Decades

1. **Conciliar os metadados com o jogo atual.** `johto_qa.validate_maps` requer que `MapInfos.rxdata` e `Tilesets.rxdata` tenham exatamente os hashes da base usada no OFFLINE 12. Hoje o Decades pode já conter Kanto + Hoenn. Criar um merge por IDs/símbolos em memória, remapear o índice de tilesets e detectar colisões; nunca copiar os dois RXDATA da prévia em cima dos existentes.
2. **Construir overlay jogável para a campanha principal.** Reutilizar os 82 mapas, depois aplicar os reparos privados do `johto_qa.plan` para as cidades, interiores adicionais, pontos de cura, placas, eventos e caminhos. Revalidar cada MapID depois do merge e no motor; não declarar que os 82 mapas equivalem a toda a campanha HGSS.
3. **Mesclar PBS e gráficos sem colisões.** Preservar todos os registros de Kanto/Hoenn/Decades, compilar as 21 equipes e os encontros, registrar os 44 links e instalar os Ruby handlers próprios de Johto no mesmo carregamento do jogo principal. Não usar o override de `JohtoPilotStart.rb` nem a troca de perfil de save.
4. **Instalador transacional real.** Fazer dry-run, backup de cada caminho que pode mudar, escrita atômica, confirmação de SHA após escrita, rollback integral em caso de erro, invalidação de cache e pedido de compilação nativa de PBS/plugins. O `install_johto.py --apply` deve continuar bloqueado até o novo instalador passar pelos testes.
5. **QA nativa e provas.** Testar New Bark → Elm → três bolas → Silver → Rota 29/Cherrygrove → Violet, salvamento, recarga, centro de cura, viagens, Box, insígnias, líderes, Liga e HMs, inclusive Windows e JoiPlay. O sistema atual exige 13 comprovantes reais; não substitua todos por `true` em testes sintéticos.
6. **Publicação.** Apenas após aprovação, criar manifesto/markers `blue-johto-*.json/txt` corretos e compilados, adicionar Johto ao canal Android `multiregion`, ampliar o título/ZIP/manifesto do canal sem confundir com Decades puro ou pilotos isolados, e testar o atualizador Termux conservando saves.

## Critério de aceite

- Ao escolher `Novo Jogo → Johto`, iniciar no quarto de New Bark **sem** perfil de piloto ou diálogo de seleção adicional.
- Viajar Decades ↔ Kanto ↔ Hoenn ↔ Johto, respeitando os desbloqueios, sem repetir introduções ou trocar o save.
- Reabrir um save antigo e confirmar preservação da party/PC, HMs/itens por região, insígnias, level cap e pontos de cura.
- No JoiPlay, nenhuma dependência obrigatória de `JSON`/`Digest` pode bloquear menu ou viagem; segurança do manifesto ainda precisa ser preservada.
- `Game.exe` e Android compilados devem funcionar em teste real; resultado de pytest/unittest/CI isolado não é aprovação de gameplay.

**Referências:** `docs/JOHTO_OFFLINE_FASE_12_AUDITORIA_INTEGRACAO.md`, `docs/JOHTO_PENDENCIAS_APOS_OFFLINE_12_DE_12.md`, `docs/JOHTO_FASE_16_INTEGRACAO_E_ACEITE.md`, `docs/HOENN_INTEGRACAO_DECADES_MAIN.md`.
