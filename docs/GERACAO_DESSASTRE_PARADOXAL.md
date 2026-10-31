# Geração Dessastre Paradoxal

A geração autoral é identificada pelo nome **Dessastre Paradoxal**, sem substituir as gerações oficiais. Foram importados **59 Pokémon novos** e **12 Mega Evoluções** da [Fan Dex do autor](https://radical-red-compendium.vercel.app/#fan-dex), com os 59 learnsets por nível conferidos contra `Pokedex_Paradoxos_Learnsets_Mestre.md`. As descrições da Pokédex começam em **`????`**.

## O que está disponível

| Conteúdo | Portal | Jogo local |
|---|---|---|
| 52 espécies com atributos definidos | Ficha completa e sprites | Compiladas e liberadas para testes |
| 12 Megas autorais | Cartões próprios no filtro da geração e seleção de forma na ficha-base | Formas reais, cada uma com sua pedra DP |
| 7 espécies sem atributos definidos | Fichas e learnsets, atributos `????`, aviso de pendência | Não registradas no catálogo de batalha |

Os sete pendentes são **Horsand, Spinedra, Stingdra, Gillble, Galbite, Garcholt e primal notic**. Seus zeros da origem são campos não definidos, não atributos de combate. Nenhum atributo foi inventado para liberá-los. Primal notic possui arte conceitual na origem, mas ainda não possui os sete sprites; o portal identifica essa arte.

## Testar agora

Abra **`TESTAR_BATALHA.bat`** na pasta principal. Com a geração instalada, o laboratório prepara **Cave Fang x Iron Crusher** no nível 50. Ao escolher seu Pokémon ou o adversário, selecione **Dessastre Paradoxal** para ver apenas as espécies e formas autorais compiladas. O catálogo completo continua disponível.

O laboratório permite mudar nível, golpes, habilidade e item equipado. Para testar Mega Sol, escolha Archgutor e selecione essa habilidade. Para ativar uma Mega durante a batalha, escolha a espécie-base e equipe sua pedra DP — por exemplo, **Arbokita DP**. O laboratório fornece um Mega Ring temporário. Também é possível selecionar uma forma Mega diretamente no catálogo.

A sessão não carrega nem grava a campanha. Espécies novas não foram colocadas automaticamente em encontros selvagens: as rotas previstas para Radical Red não equivalem aos mapas da campanha Decades.

## Mega Sol

A habilidade foi implementada conforme a [definição fornecida pelo autor](https://pokemondb.net/ability/mega-sol): os **golpes do portador** consideram sol, sem alterar o clima do campo ou beneficiar os demais Pokémon. Isso inclui Solar Beam sem turno de carregamento e os multiplicadores de sol usados pela engine. Um golpe de Fogo recebido não recebe bônus causado por Mega Sol. A habilidade respeita supressão, e o contexto é restaurado ao terminar o movimento.

A verificação no runtime testa esses efeitos com as classes de batalha carregadas, além de atributos, tipos, descrições, pedras Mega, elegibilidade de Mega Arbok e conexões evolutivas. O relatório fica em `game/Data/blue-generation-validation.txt`; a última linha deve ser `RESULT=PASS`.

## Evoluções

As oito novas ramificações seguem o plano usado no site do autor, preservando as ramificações existentes:

| Origem | Destino | Método |
|---|---|---|
| Exeggutor | Archgutor | Sun Stone |
| Electrode | Dynamotrode | Fast Ball |
| Magneton | Magnetrix | Shiny Stone |
| Magikarp | Magiscale | Dawn Stone |
| Omanyte | Ammnoid | Dusk Stone |
| Ammnoid | Cephalonid | Nível 42 |
| Stunfisk | Stundrift | Nível 47 |
| Swadloon | Swadloadne | Leaf Stone |

Fast Ball ganhou suporte de evolução no uso fora de batalha e continua funcionando como Poké Ball na batalha. As linhas **Horsand → Spinedra → Stingdra** e **Gillble → Galbite → Garcholt** aparecem no portal conforme o estudo do autor, mas dependem dos atributos pendentes antes de serem compiladas. Escama de Sílica é um item autoral previsto para o ramo de Stingdra.

Megas são formas alternativas, sem adicionar uma espécie-base duplicada. Foram criadas pedras próprias com IDs `DP...ITE`, evitando alterar as condições das formas que já existiam na base.

## Reproduzir em outra instalação

Este repositório contém o manifesto, os scripts próprios e os sprites autorais normalizados. O jogo original, os arquivos compilados e os saves continuam fora do Git.

1. Instale a base local e aplique a restauração de regras já documentada no projeto.
2. Abra **`IMPORTAR_DESSASTRE_PARADOXAL.bat`**, ou execute `python scripts/dessastre_paradoxal/install.py --apply`.
3. Abra **`TESTAR_BATALHA.bat`** e aguarde a compilação em modo debug. A primeira carga pode demorar.
4. Para verificar a engine, execute `python scripts/battle_lab/launch.py --smoke-test`. O relatório confirma a compilação e executa confrontos completos, com a IA nos dois lados.

Sem `--apply`, o importador apenas verifica e mostra o plano. Ele valida IDs, referências, níveis e hashes; preserva ramos evolutivos; não sobrescreve uma espécie de mesmo ID encontrada fora dos arquivos autorais. Reaplicar o manifesto é uma restauração do cadastro importado, com backup em `.blue-backups/dessastre-paradoxal-*`. Faça isso conscientemente se já editou os PBS autorais.

## Editar e atualizar o portal

Os dados de referência ficam em `data/dessastre-paradoxal.json`. O manifesto registra os sete pendentes, learnsets, vínculo das Megas, caminhos e hashes dos sprites e as fontes. O pacote `site/assets/fan-pokemon.tar.gz` contém 491 PNGs de arte autoral, normalizados sem redesenhar o Pokémon e respeitando os espelhamentos da origem. O build extrai esse pacote com checagem de integridade; não precisa acessar o Supabase nem usar tokens.

Após editar Pokémon já importados no Blue Studio, recompile o jogo e execute:

```sh
python scripts/export_site_data.py
npm test --prefix site
npm run build --prefix site
```

O exportador preserva as alterações de atributos, tipos, habilidades e learnsets feitas nos PBS locais. Para liberar um dos sete cadastros pendentes pelo importador, preencha seus seis atributos reais no manifesto, altere `pending` para `false`, reaplique e recompile. Os números das 1.025 espécies oficiais são mantidos por `data/national-species.json`.

A geração usa uma chave textual no portal e a flag `DessastreParadoxal` no PBS. O campo numérico interno de compatibilidade da engine é 0; as interfaces exibem o nome. Cadastros novos feitos pelo editor já oferecem essa geração e começam com descrição `????`.

## Critérios de compatibilidade

- Os stats foram convertidos para a ordem do Essentials: HP, Ataque, Defesa, Velocidade, Ataque Esp., Defesa Esp.
- A origem não informa papéis de habilidades em campos separados: a terceira habilidade, quando presente, é disponibilizada como oculta no Essentials; as duas primeiras permanecem normais.
- TM e tutor continuam separados no portal; ambos alimentam a compatibilidade `TutorMoves` do Essentials. Os números de TM de Scarlet/Violet no documento não foram tratados como números de itens deste fangame.
- As Megas usam os learnsets da espécie-base na referência Radical Red 4.1 disponibilizada pelo site. Seus parâmetros de golpes continuam sendo os da engine local restaurada, sem importar o rebalanceamento do Radical Red.
- As grafias `Vice Grip`, `Drain Kiss` e `Flower Guard` da referência foram conciliadas explicitamente com `VISEGRIP`, `DRAININGKISS` e `FLOWERSHIELD`. Entradas “Evolução” foram convertidas em nível 0.
- Altura, peso, experiência, crescimento e outros campos auxiliares não fornecidos pelo cadastro têm valores técnicos provisórios no PBS. Altura e peso não confirmados aparecem como `????` no portal; resultados dependentes de peso devem ser balanceados quando o autor definir esse dado.

O Supabase e o repositório de referência foram somente consultados; esta integração não modifica o cadastro original.
