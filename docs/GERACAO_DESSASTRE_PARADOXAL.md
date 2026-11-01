# Geração Dessastre Paradoxal

A geração autoral é identificada pelo nome **Dessastre Paradoxal**, sem substituir as gerações oficiais. Foram importados **59 Pokémon novos** e **12 Mega Evoluções** da [Fan Dex do autor](https://radical-red-compendium.vercel.app/#fan-dex), com os 59 learnsets por nível conferidos contra `Pokedex_Paradoxos_Learnsets_Mestre.md`. As **47 descrições e medidas aprovadas** estão aplicadas ao jogo e ao portal; as outras 12 continuam com descrição **`????`**.

## O que está disponível

| Conteúdo | Portal | Jogo local |
|---|---|---|
| 52 espécies com atributos definidos | Ficha completa e sprites | Compiladas e liberadas para testes |
| 12 Megas autorais | Cartões próprios no filtro da geração e seleção de forma na ficha-base | Formas reais, cada uma com sua pedra DP |
| 7 espécies sem atributos definidos | Fichas e learnsets, atributos `????`, aviso de pendência | Não registradas no catálogo de batalha |

Os sete pendentes são **Horsand, Spinedra, Stingdra, Gillble, Galbite, Garcholt e Witchcap Haze**. Seus zeros da origem são campos não definidos, não atributos de combate. Nenhum atributo foi inventado para liberá-los. Witchcap Haze possui arte conceitual na origem, mas ainda não possui os sete sprites; o portal identifica essa arte. Sua descrição aprovada não libera o cadastro para batalha.

Os 14 nomes que continham Primal foram substituídos pelos nomes aprovados no [documento de descrições](Pokedex_Descricoes_Dessastre_Paradoxal.md). Os IDs internos continuam estáveis para preservar referências, evoluções e equipes. Primatizer mantém seu nome próprio.

Foram aplicados **48 cries WAV** e **12 ícones de Mega Stones**, sem alterar seus bytes. Os PNGs das pedras têm 64×64 e são aceitos pelo ícone estático da engine. O portal mostra o áudio disponível nas fichas e a pedra nas formas Mega. Ainda não foram fornecidos cries para **Canopy Titan, Cinder Coil, Iron Invernose e Iron Matriarch**. Megas mantêm o cry de sua espécie-base. A lista e os hashes estão em `data/fan-assets.json`; o pacote autoral é `site/assets/fan-extras.tar.gz`.

## Testar agora

Abra **`TESTAR_BATALHA.bat`** na pasta principal. Com a geração instalada, o laboratório prepara dois times de seis no nível 50, incluindo **Cave Fang** e **Iron Crusher**. Em **Editar meu time** ou **Editar time rival**, escolha um integrante e selecione **Dessastre Paradoxal** ao trocar sua espécie para ver apenas as espécies e formas autorais compiladas. O catálogo completo continua disponível. Há formatos individual e dupla, com seleção também por clique.

O laboratório permite mudar nível, golpes, habilidade e item equipado. Para testar Mega Sol, escolha Archgutor e selecione essa habilidade. Para ativar uma Mega durante a batalha, escolha a espécie-base e equipe sua pedra DP — por exemplo, **Arbokita DP**. O laboratório fornece um Mega Ring temporário. Também é possível selecionar uma forma Mega diretamente no catálogo.

A sessão não carrega nem grava a campanha. Na campanha, os **37 Paradoxos do passado disponíveis** foram colocados junto aos oficiais na **Prehistoric Grotto (mapa 156)**; os **7 do futuro**, na **Futuristic Grotto (mapa 157)**. Witchcap Haze permanece excluído. A configuração é `data/fan-encounters.json`: 50% da chance total fica com o grupo autoral e 50% com as espécies originais, preservando a proporção relativa dos encontros existentes dentro da precisão inteira dos pesos. Os níveis e a frequência da tabela terrestre foram mantidos; outros métodos e áreas não mudam. Todos os originais continuam presentes, inclusive Delibird. O portal publica esses encontros.

## Mega Sol

A habilidade foi implementada conforme a [definição fornecida pelo autor](https://pokemondb.net/ability/mega-sol): os **golpes do portador** consideram sol, sem alterar o clima do campo ou beneficiar os demais Pokémon. Isso inclui Solar Beam sem turno de carregamento e os multiplicadores de sol usados pela engine. Um golpe de Fogo recebido não recebe bônus causado por Mega Sol. A habilidade respeita supressão, e o contexto é restaurado ao terminar o movimento.

A verificação no runtime testa esses efeitos com as classes de batalha carregadas, além de atributos, tipos, nomes, descrições, medidas, resolução dos 48 cries, ícones das 12 pedras, elegibilidade de Mega Arbok, conexões evolutivas e encontros compilados. Usa os métodos reais de evolução por item e nível, incluindo os limites 41/42 de Ammnoid e 46/47 de Stunfisk. O relatório fica em `game/Data/blue-generation-validation.txt`; a última linha deve ser `RESULT=PASS`.

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
