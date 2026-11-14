# Auditoria de localização de Kanto (PT-BR e EN)

A opção **Idioma** do jogo escolhe o idioma ao exibir a fala. Os textos originais de mapas e PBS ficam na instalação. O Testar Kanto inclui as traduções revisadas na reconstrução automática, sem baixar modelos. Os nomes de Pokémon, itens e golpes, os códigos de formatação e as variáveis continuam sendo lidos pela engine.

## Cobertura no piloto Windows

| Origem | Resultado |
| --- | --- |
| Mapas da edição montada | 142 examinados, dos quais 97 contêm eventos e 45 são prévias sem eventos. 89 mapas têm texto localizável detectado. |
| NPCs e placas importados | 316 chaves distintas encontradas em 219 eventos ativos, com 316 revisadas, incluindo títulos próprios mantidos no original. |
| História, interações e escolhas autorais | 137 pares PT-BR/EN, incluindo casa, Oak, ginásios, Silph, Victory Road e Liga. |
| Falas de derrota no PBS | 154 ocorrências e 144 falas distintas na instalação auditada. |
| Captura e armazenamento | Aviso na placa, bloqueio em batalha contra treinador, restrições de mira e falta de espaço no PC. A varredura também conferiu 453 chaves estáticas do motor nativo. |

A placa da Viridian Forest usa o comando de janela de placas seguido de “You can't catch a Pokémon that belongs to someone else.”, no mapa 310 do piloto (origem FRLG 24), evento 10, segunda fala. A batalha tem sua própria mensagem, em `Battle_CatchAndStoreMixin#pbThrowPokeBall`. As traduções estão na tabela do piloto. As duas origens já passam a respeitar o idioma.

## Verificação no Game.exe

O executável de Windows confirmou Português e Inglês para a placa de captura da Viridian Forest, o NPC de Pallet, o aviso de Oak, a fala de derrota de Brock e a tentativa de capturar um Pokémon de outro treinador. A verificação também conferiu o valor padrão de uma configuração antiga e a serialização da preferência de idioma. Passaram 206 testes de Kanto e seis testes do empacotador JoiPlay.

## Repetir a auditoria

A construção gera `Data/blue-kanto-locale-audit.json` dentro do novo piloto. Para repetir ou obter um código de saída de erro quando houver pendências detectadas:

```powershell
python scripts/regions/kanto_locale_audit.py "CAMINHO_DO_PILOTO" --strict
```

O relatório identifica mapa, evento e página para falas de NPC, placa, diálogos em comandos, escolhas e scripts rastreáveis. Para derrotas, lista arquivo PBS, linha e treinador. A última auditoria registrou zero ocorrências pendentes nessas fontes. A auditoria usa as chaves que o jogo recebe com seus controles. Compare a mesma interação após alternar o idioma e conserve os códigos da fala ao acrescentar uma tradução. O teste de regressão injeta uma placa, uma escolha e uma fala de derrota novas e verifica se aparecem na lista de pendências.

## Limites

A cobertura é das fontes inventariadas. As 45 prévias sem eventos, funcionalidades ainda não importadas e mensagens construídas apenas durante a execução de plugins compartilhados ficam fora dessa contagem. Uma varredura estrutural não substitui percorrer toda a campanha em ambos os idiomas. O Android também requer uma rodada própria de QA. As abreviações internacionais como PP e nomes de itens como Mega Ring foram preservados.
