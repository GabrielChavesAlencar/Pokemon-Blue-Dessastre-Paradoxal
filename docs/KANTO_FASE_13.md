# Kanto — fase 13/16: Viridian Gym, Giovanni e Earth Badge

**Data:** 12/11/2026. **Estado:** núcleo funcional implementado no piloto Kanto, sujeito à prova de CI Windows e QA manual. A etapa integral continua aberta.

## Escopo e evidência da fonte

O projeto original **Essentials FRLG 1.1** está fixado pelo SHA-256 do manifesto `data/regions/kanto-source.json`. O inventário somente leitura `scripts/regions/audit_viridian_gym.py` confirma:
- **Map010, evento 1**: porta do Ginásio de Viridian, cujo original dependia de condições globais e transferia para **Map013, (17,22)**.
- **Map013, evento 11**: saída do ginásio para **Map010, (36,11)**, por toque do jogador.
- **Map013, evento 4**: Líder Giovanni com equipe `[LEADER_Giovanni,Giovanni]` no PBS, **diferente** de `[ROCKETBOSS,Giovanni,2]` da Silph Co.
- **Oito treinadores** da fonte: Takashi (2), Samuel (3), Kiyo (5), Cole (6), Yuji (7), Jason (8), Atsushi (9) e Warren (10).
- **Bug original corrigido:** o evento 8 chama a batalha de Cole mesmo sendo rotulado Jason. No Blue o evento luta com o time próprio de `[TAMER,Jason]`, com chave de vitória independente.

Nenhum script estrangeiro, switch global, placa com eventos desconhecidos nem variáveis da fonte é executado no Decades.

## Implementação funcional

1. **IDs preservados:** os 126 mapas anteriores são explicitamente congelados em `audit.py`; o Map013 do ginásio é adicionado após todos eles como a 127ª localização. Salvamentos e teletransportes antigos não mudam de endereço por reordenação.
2. **Porta com trava local:** `BlueKantoPilot.viridian_gym_gate` só libera a ida após obter **Boulder, Cascade, Thunder, Rainbow, Soul, Marsh e Volcano** em **Kanto** e salvar a Silph Co. O cálculo de níveis continua usando **insígnias de todas as regiões + esmeraldas de Decades**, mas esse total agregado **não** desbloqueia um ginásio sem suas próprias insígnias locais.
3. **Treinadores autênticos:** equipes, espécies, golpes e níveis são exportados do PBS FRLG com tipos registrados no Blue e sprites de NPC copiados somente da fonte isolada. A batalha é automática por `Sight(n)` e o estado pós-vitória usa self-switch A e chave `KANTO_<mapa>_<evento>`.
4. **Giovanni independente:** o Giovanni da Silph (ROCKETBOSS versão 2) não libera nem marca a vitória contra Giovanni do ginásio. Até um legado com vitória baseada apenas no nome `Giovanni` é tratado separadamente.
5. **Earth Badge:** prêmio regional via `BlueRegions.award(progress,"KANTO","EARTH")` somente após vitória real. Derrotas não dão insígnia, rematches não duplicam contagem e Earth não é escrita diretamente nos badges nativos de Decades.
6. **Retorno seguro:** a saída do ginásio tem transferência revisada de volta à cidade. O Gym Guide (evento 16) informa sobre condições e recompensa sem executar diálogos/flags do projeto original.
7. **Teste experimental:** acrescentados destinos específicos de Viridian City e Ginásio Giovanni ao menu isolado `Testar Kanto` do executável, totalizando **54 atalhos** (52 + 2). A entrada real da cidade permanece protegida mesmo que se use o teleporte experimental.

## Validações automáticas

- Inventário e white-list de eventos da fonte; nenhum evento não autorizado no ginásio.
- Entrada condicional sem warp direto capaz de ignorar os sete marcos de Kanto.
- Transferência de retorno e coordenadas de entrada dentro dos limites do mapa.
- Nove identidades de batalha (oito treinadores + Giovanni) e gatilho de visão.
- Regressão contra o bug Jason → Cole.
- Teste da porta com 6 insígnias, com 7 e com/sem Silph resgatada.
- Líder inacessível sem requisitos, derrota sem Earth, vitória com Earth, tentativa de revanche sem segunda insígnia.
- Coexistência dos dois Giovannis, correção de flag legado e save/reload de progresso, chave e self-switch.
- Exportação de `site/public/data/kanto.json` com equipe do líder e grupos de treinadores.

**Limite das provas:** os resultados de batalha da CI são **simulados**; a CI pode compilar o `Game.exe`, mas não prova caminhada manual, puzzles de piso, colisões, visuais, movimentação do jogador ou compatibilidade JoiPlay.

## Pendências de aceite integral

- Testar portas, direção e colisões reais no Windows e JoiPlay, inclusive os tiles giratórios/correias do ginásio; não presumir que o motor de Decades reproduz as mecânicas da fonte.
- Confirmar visualmente a linha de visão, oito treinadores, time e dificuldade Master; testar derrota, fuga, cura, salvar/carregar e retorno.
- Revisar ilustrações de batalha provisórias de Cooltrainer masculino e Giovanni sem redistribuir arte sem licença.
- Revisar o caminho canônico do ginásio até a Rota 22, Victory Road e Liga no **núcleo 14**. A Earth Badge **não** libera a Liga automaticamente.
- Atualizar tradução PT-BR dos diálogos, interface e documentação do site após evidência de gameplay real.

**Barras:** desenvolvimento 11/16 antes da aprovação nativa deste núcleo; com CI nativa e regressão aprovadas, registrar **12/16** (restam 4). O aceite integral permanece **1/16** até QA manual.
