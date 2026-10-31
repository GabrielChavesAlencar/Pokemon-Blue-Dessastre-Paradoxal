# Restauração de Pokémon e golpes — Pokémon Blue

**Estado:** aplicada, compilada e validada em 31/10/2026.

Projeto: `<pasta-do-projeto>`.

A restauração segue o pedido de recuperar os dados e as regras de Pokémon e golpes da geração 9, preservando a campanha e os recursos do fangame. As referências usadas foram o [Pokémon Essentials v21.1](https://github.com/Maruno17/pokemon-essentials/tree/v21.1) e o [Generation 9 Pack original v3.3.3](https://eeveeexpo.com/resources/1101/version/3285/download), a mesma versão do plugin instalado. O pacote básico “Stock Vanilla” do Decades, sozinho, preserva habilidades, evoluções e listas de golpes modificadas; por isso a restauração também utilizou os dados completos e os scripts originais dessas referências.

## Dados restaurados

| Grupo | Registros comparados com referência | Registros com alterações aplicadas |
|---|---:|---:|
| Espécies base | 1.025 | 1.025 |
| Formas com referência disponível | 493 | 319 |
| Golpes com referência disponível | 833 | 822 |
| Definições de habilidades | 310 | 270 |
| Tipos do arquivo principal | 19 | 14 |

Os registros restauram atributos, tipos, habilidades, golpes por nível/tutor/ovo, evoluções, rendimento de EVs, taxas de captura e demais campos presentes nas referências. Os IDs de espécies e formas existentes foram conservados. O compilador acrescentou metadados necessários aos plugins, como flags de Dynamax e compatibilidade com Tera Blast.

Também foram restaurados 29 trechos da engine e as alterações de balanceamento identificadas nos scripts do Generation 9 Pack. Classes de golpes exclusivos do Decades foram conservadas para atender às referências usadas pela campanha.

Exemplos confirmados na engine:

| Exemplo | Resultado |
|---|---|
| Bulbasaur | 45/49/49/45/65/65; Overgrow; habilidade oculta Chlorophyll |
| Charmeleon / Blastoise | Fire / Water |
| Tackle / Torch Song / Electro Drift | Poder 40 / 80 / 100 |
| Stealth Rock | Tipo Rock |
| Tackle usado por Pokémon Fire | Continua Normal |
| Counter | Multiplicador 2× |
| Sharpness | Bônus 1,5× |
| Sleep e Freeze | Condições tradicionais; substituições por Drowsy/Frostbite desativadas |
| Clima de gelo | Snow da geração 9 |
| EVs | Ataque e Ataque Especial independentes; limites 510 no total e 252 por atributo |

Os IVs de Pokémon gerados voltam a usar a geração aleatória da referência. As chances básicas de shiny e Pokérus foram restauradas. A interface de distribuição de EVs continua disponível, adaptada aos limites acima; a injeção automática de EVs ao subir de nível foi removida.

## Campanha e recursos preservados

Foram conferidos os hashes de **265 arquivos protegidos**, incluindo mapas, eventos comuns, configuração da campanha e PBS de treinadores/encontros. Permanecem iguais ao estado anterior à restauração. Gráficos, músicas, sprites e métricas de posicionamento não foram substituídos.

Os arquivos de equipes e eventos permanecem os mesmos. Na execução, alocações de EVs de treinadores são limitadas ao orçamento restaurado, sem trocar espécies, níveis ou golpes das equipes.

As pedras universais de Mega Evolução usadas pelo Decades continuam vinculadas às respectivas formas para preservar o acesso a elas pela campanha.

## Conteúdos próprios e limites do escopo

- **39 formas sem par nas referências usadas** foram preservadas, incluindo combinações Mega/Gigantamax e Shadow Lugia.
- **173 definições adicionais de golpes** continuam disponíveis, incluindo suporte a Dynamax, Z-Moves, Shadow e variantes próprias. A campanha pode continuar usando esses golpes e atribuições explícitas feitas por eventos.
- Formas e mecânicas do pacote são implementações do ecossistema Essentials; formas novas que não possuem uma definição equivalente nas referências continuam sendo conteúdo do fangame.
- Lojas, preços, curas e scripts de itens da campanha foram preservados. A conversão dos itens comuns de aumento de tipo em consumíveis de efeitos de estado foi retirada para recuperar seus efeitos de batalha tradicionais.
- A campanha inteira não foi percorrida. A dificuldade poderá mudar com os atributos e regras restaurados, enquanto equipes, encontros e progressão permanecem os do Decades.

## Validação concluída

- Compilação real de PBS e plugins concluída pela engine.
- **20 verificações executadas no runtime**, incluindo leitura dos dados compilados e chamadas aos métodos reais de cálculo de tipo, Counter e Sharpness com dependências mínimas de teste.
- Inicialização normal e configuração do sistema concluídas, encerrando o diagnóstico antes de carregar uma partida.
- **24 testes de regressão do editor aprovados**, mais validação sintática do JavaScript alterado.
- Salvamento pela API verificado em uma cópia dos PBS restaurados: edição de espécie, criação de espécie, golpes por nível/tutor/ovo, potência de golpe e backups.
- Os **86 PBS reais permaneceram idênticos durante o teste do editor**.
- Referências entre espécies, formas, tipos, habilidades, golpes, itens e evoluções verificadas.

Foi corrigido um problema de quebras de linha no compilador do Deluxe Battle Kit encontrado durante a recompilação. O editor também passou a aceitar **nível 0 = golpe aprendido ao evoluir**, presente em 283 registros restaurados. Níveis negativos continuam rejeitados.

A inicialização temporária do diagnóstico foi retirada e o pedido de verificação automática foi removido após o sucesso.

## Backup e uso

Backup anterior à restauração, incluindo a pasta `Data` completa e os arquivos substituídos:

`<pasta-do-projeto>\.blue-backups\official-rules-20261031T150634Z`

O backup contém `manifest.json` e `final-manifest.json`. Os três arquivos do editor ajustados para nível 0 também têm cópia em `editor/` dentro desse backup.

Para jogar, use `JOGAR.bat` na pasta principal. Para editar, use `RUN.bat`. Os dados restaurados já estão compilados; futuras edições nos PBS precisam ser recompiladas no modo Debug.

O arquivo `restauracao_manifesto.json` registra caminhos, hashes, referências e validações. `verificacao_engine.txt` contém a saída das verificações dentro da engine.

## Reaplicar em outra instalacao

O codigo reproduzivel da restauracao fica em `scripts/official_rules/`. Veja `docs/REAPLICAR_REGRAS_OFICIAIS.md`. O repositorio guarda o procedimento e as verificacoes; os arquivos do jogo, downloads de referencia e backups permanecem locais.
