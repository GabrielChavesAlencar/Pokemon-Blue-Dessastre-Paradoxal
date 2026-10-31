# IA Blue Radical

Implementação própria em Ruby para a engine Essentials 21.1 da base Decades, inspirada no estudo técnico do autor e nos princípios públicos do CFRU. **Não é o código integral nem uma reprodução exata da IA de Radical Red 4.1.** O código público do CFRU e os comportamentos relatados de Radical Red não são equivalentes; as diferenças apontadas no estudo foram mantidas nesta integração.

## Usar

A instalação local já recebe a política por padrão nas **batalhas contra treinadores**, tanto na campanha quanto no laboratório. Pokémon selvagens conservam o comportamento da base. A IA não altera atributos, níveis, golpes, times dos chefes ou regras de dano para aumentar a dificuldade.

Abra **TESTAR_BATALHA.bat** e selecione **IA** no menu principal para comparar:

| Perfil | Comportamento |
|---|---|
| IA da base | Usa os sistemas originais de Decades, incluindo o Advanced AI System já instalado, sem a política Blue Radical. |
| Blue estratégica | Ativa a avaliação Blue com modificadores reduzidos e sem adaptação a loops de troca. |
| Blue Radical | Avaliação completa, flags de treinador especialista, adaptação ao histórico de trocas e escolha entre os melhores scores. É o padrão. |

Todos funcionam com times completos e nos formatos individual e dupla. O perfil escolhido no laboratório vale apenas para aquela batalha. A configuração global fica em `data/radical-ai.json`; após editá-la, execute **APLICAR_IA_RADICAL.bat** e abra o laboratório para recompilar. Para desativar globalmente a política, altere `defaultProfile` para `engine` e reaplique.

Em outra instalação da mesma base, execute `python scripts/radical_ai/install.py --apply`, ou abra o atalho. O lançador do laboratório também instala as versões atuais dos scripts automaticamente. A primeira abertura após uma atualização pode recompilar os plugins.

## Decisões implementadas

| Área | Implementação |
|---|---|
| Legalidade | A enumeração da engine filtra PP, Choice lock, Encore, Disable, Taunt e demais limitações. Struggle é usado quando não resta ação legal. |
| Dano | Usa o calculador aproximado da engine com tipos, STAB, atributos, boosts, habilidades, itens, clima, terreno, precisão e mecânicas do pacote Gen 9. |
| Nocautes | Diferencia nocaute conservador, possível nocaute e 2HKO aproximado. Considera prioridade, velocidade, Trick Room, Focus Sash e Sturdy. |
| Setup e recuperação | Penaliza setup sob ameaça de nocaute, valoriza preparação segura e considera HP perdido, ordem de ação e ameaça ao pontuar cura. |
| Status e suporte | Usa os handlers de efeitos da engine para evitar ações redundantes ou sem efeito. Acrescenta suporte ao aliado, controle de velocidade e sinergia de clima com a própria equipe. |
| Hazards | Stealth Rock, Spikes, Toxic Spikes e Sticky Web afetam a avaliação de entrada. Heavy-Duty Boots, Magic Guard e imunidades são considerados. Troca voluntária para uma entrada que morre é rejeitada. |
| Trocas | Avalia reservas legais, dano recebido na entrada, ameaça, velocidade e potencial ofensivo. Choice lock inútil, Perish Song, perda ofensiva, Natural Cure, Regenerator e Yawn podem motivar troca. |
| Preservação | Prefere atuar quando há um nocaute antes da resposta; evita trocas em sequência sem ganho; preserva boosts e usa pivot quando consegue fazê-lo com segurança. |
| Substituição após derrota | Escolhe uma reserva elegível pela avaliação de confronto. Se todas morrem para hazards, ainda devolve uma substituição legal; uma reserva segura pode ser usada mesmo quando é o ace reservado. |
| Duplas | Avalia alvos legais, penaliza dano no aliado, considera aliados imunes, suporte e distribuição dos ataques entre inimigos para evitar excesso de dano no mesmo alvo. |
| Megas | Mantém o fluxo de mecânicas especiais da base. Quando a Mega está registrada, projeta atributos, tipo e habilidade reais para pontuar os golpes, sem transformar o Pokémon vivo durante a análise. Inclui as Megas autorais. |
| Mega Sol | O calculador recebe o contexto de sol pessoal do portador, preservando a ausência de efeito no restante do campo. |
| Empates | Sorteia apenas entre ações com o melhor score. O RNG de desempate é separado e pode receber uma seed fixa nos testes. |

As classes de papéis do CFRU não foram copiadas literalmente. Os papéis resultam dos movimentos e das condições atuais: atacante, setup, recuperação, hazards, remoção, clima, controle de velocidade, suporte e pivot.

## Informações e previsão

Esta é uma **IA informada**: considera golpes, atributos, habilidade e item dos Pokémon ativos, além das próprias reservas. A previsão de ameaça assume os melhores ataques legais conhecidos do adversário; em dupla, pode considerar um foco de ataques sobre o mesmo Pokémon. É uma aproximação conservadora, não uma busca exaustiva de todas as sequências possíveis.

O avaliador não consulta o comando atual escolhido pelo jogador. Ele trabalha em uma cópia do estado com a fila de comandos vazia. Os planos já registrados pelos próprios aliados da IA podem orientar a distribuição de alvos. Os testes mudam a escolha oculta do jogador entre ataque e troca e verificam que as pontuações continuam iguais.

A adaptação a trocas usa apenas posições observadas em turnos anteriores. Detecta alternância A–B–A–B, favorece pressão de hazards e cobertura contra a outra espécie já observada. O contador recebe +3 por troca observada, decai em um por turno e é reiniciado após nocaute. **Não há recálculo do ataque depois que a troca do jogador foi revelada**, nem reprodução das probabilidades comunitárias de 25/33/50% do Hardcore. Esses comportamentos não são apresentados como implementação confirmada de Radical Red 4.1.

## Integração com a base

A base já inclui Advanced AI System 2.7.1, DBK e os scripts Gen 9. Para evitar somar duas políticas completas, Blue Radical reutiliza os handlers de legalidade/efeitos e o calculador da engine, mas passa a controlar a pontuação adicional, escolha final e trocas. O perfil `engine` mantém o caminho anterior. O fluxo existente de itens de treinador, eventos e mecânicas especiais é preservado.

O snapshot clona Pokémon, battlers, movimentos, efeitos, campo, lados e posições. Ele não executa os ataques nem eventos de entrada da simulação. A projeção de uma Mega considera seus dados reais, mas a ativação de clima ou efeitos de entrada de uma habilidade continua pertencendo à execução real da engine. O cálculo de dano permanece uma estimativa: não é uma simulação perfeita de críticos, rolagens e todos os efeitos futuros.

O instalador escreve somente o plugin próprio em `game/Plugins/ZZZZZ Blue Radical AI/`. Não reescreve a IA original, PBS, mapas ou saves. Valida a configuração antes de escrever, preserva arquivos anteriores e o cache de plugins em `.blue-backups/radical-ai-*` e reverte os arquivos da instalação se uma escrita falhar. Reaplicar sem mudanças não altera arquivos.

## Logs e validação

`game/Data/blue-radical-ai.log` registra:

- `MOVE_SCORE`: movimento, alvos, score e fatores que alteraram a pontuação.
- `CHOOSE_MOVE`: golpe e alvo selecionados.
- `REPLACEMENT`: candidatos e substituição escolhida.
- `SWITCH`: justificativa e comparação entre ficar e trocar.

A gravação não exige internet e não envia logs a terceiros. Pode ser desativada com `trace: false` na configuração. O arquivo tem um limite de gravação para não crescer indefinidamente.

Execute `python scripts/battle_lab/launch.py --smoke-test --timeout 420` para validar na instalação real. O relatório específico é `game/Data/blue-radical-ai-validation.txt` e termina em `RESULT=PASS` quando todos os cenários passam. O teste também executa confrontos completos no laboratório, além das verificações existentes de HP, mouse, geração autoral e proteção dos saves. Sem os arquivos do jogo, `python -m unittest discover -s tests -v` verifica o instalador e os contratos do projeto.

Os cenários cobrem OHKO, imunidade, PP, Struggle, prioridade, Focus Sash, setup arriscado, status repetido, cura, hazards letais, Boots, Choice lock, troca sem reserva segura, Perish Song, dano no aliado, parceiro imune, Helping Hand, divisão de alvos, projeção Mega, preservação do estado, independência da escolha oculta, seed fixa e memória de trocas.

## Fontes e limites

- Estudo do autor: `Estudo_Tecnico_IA_Pokemon_Radical_Red.md`, SHA-256 registrado em `data/radical-ai.json`.
- [Fluxo público do CFRU](https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/b637a27898b14e25dd24d0f69a3e302f0069deb8/src/Battle_AI/ai_master.c): pontuação e desempate entre melhores opções, caminhos separados para duplas e projeção de Mega.
- [Pesos públicos de substituição do CFRU](https://github.com/Skeli789/Complete-Fire-Red-Upgrade/blob/b637a27898b14e25dd24d0f69a3e302f0069deb8/include/new/ai_switching.h): referência dos coeficientes registrados na configuração.

Os critérios e limiares adicionais são do Blue. Não foram tratados como oficiais os pesos estimados pela comunidade para Radical Red 4.0/4.1. Esta integração não recria os times, limites de nível, restrições de bolsa ou roteiros de chefes de Radical Red e não demonstra superioridade a todas as outras IAs de Pokémon.
