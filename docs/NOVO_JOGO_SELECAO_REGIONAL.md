# Novo Jogo — seleção da região inicial no projeto principal

Implementação de 15/11/2026.

## Como usar

1. Na raiz do projeto, atualize a `main` e execute `ABRIR_JOGO.bat` (ou `INSTALAR_JOGO.bat` para uma instalação nova).
2. Na tela inicial do **jogo principal Decades**, selecione **New Game / Novo Jogo**.
3. O jogo apresenta **Em qual região deseja começar um novo jogo?**
4. Escolha **Decades** para executar a introdução original, sem alterar o início do jogo, ou selecione **Kanto, Johto, Hoenn ou Sinnoh** para abrir o respectivo piloto de testes **quando ele já estiver instalado/preparado**.
5. **Unova, Kalos, Alola, Galar, Paldea e Hisui** aparecem como indisponíveis; nenhuma campanha inexistente é iniciada. **Voltar ao menu** cancela a escolha sem tocar nos saves.

## Limite da integração atual

Esta alteração implementa **um seletor na interface do jogo principal**, e **não** instala regiões, mapas, eventos, Pokémon iniciais ou viagens que ainda não foram validados. O executável principal continua usando Decades para a campanha nativa; cada piloto experimental é iniciado em **outro executável/cópia**, com save próprio. A escolha de um piloto solicita confirmação pelo lançador existente. Quando ele não está instalado, é exibido o aviso da região, e o usuário pode escolher outra sem iniciar um novo jogo no Decades.

- **Kanto:** usa `KANTO_JOGAR_EXPERIMENTAL.bat` localizado na pasta do projeto para gerar/abrir a cópia isolada, sujeito aos insumos e verificações do montador.
- **Johto:** usa um piloto compilado próprio, ou o lançador experimental existente quando este puder preparar um piloto separado.
- **Hoenn:** exige `Game.exe`, manifesto e marcador de compilação no piloto privado preparado em `.blue-work/`; não há fallback silencioso para o Decades.
- **Sinnoh:** depende de um piloto próprio compilado ou lançador de preparação. Sem mapas reais e integração, fica indisponível.

**Regras preservadas:** nenhuma migração de save, insígnia, Pokémon, Pokémon no PC, mapas da base, escolha de inicial ou progresso regional é gravada pela tela de seleção. O menu **Continue** e os controles do Auto Multi Save mantêm os índices e navegação originais. Os próprios pilotos mantêm seu `New Game` original, sem abrir novamente o seletor.

## Para unificar tudo em um único save futuramente

Antes de permitir uma campanha compartilhada com escolha livre de região, é necessário integrar **mapas reais, MapInfos/Tilesets, eventos, PBS, níveis, bloqueios e transfers**, resolver colisões de MapIDs, disponibilizar os recursos licenciados, proteger save/PC/viagem regional e executar o QA nativo Windows/JoiPlay de cada campanha. A presença de uma região no menu **não** é prova de jogabilidade ou de disponibilidade de ZIP.

## Verificações reproduzíveis

```powershell
ruby -c scripts/battle_polish/TitleKanto.rb
ruby tests/title_kanto_runtime.rb scripts/battle_polish/TitleKanto.rb
ruby tests/region_start_runtime.rb scripts/battle_polish/RegionStart.rb
```

A regressão da CI contém essas verificações. São testes Ruby isolados, sem renderização do menu na janela do Game.exe. O teste visual/funcional no Windows e no JoiPlay **ainda é obrigatório** antes de declarar o seletor aprovado em jogo.

## Teste manual mínimo

- No jogo principal: abra **Novo Jogo → Decades**, confirme que segue a intro nativa e salva no perfil Decades.
- Volte à tela inicial: escolha **Kanto** e confirme que é iniciado somente o piloto separado (ou que o aviso aparece se os arquivos de montagem não existirem).
- Escolha **Johto, Hoenn e Sinnoh** sem o piloto preparado: devem ser exibidos os avisos e permitir tentar outra opção.
- Escolha **Unova** ou outra região indisponível: nenhum save deve ser criado e a seleção deve permanecer aberta.
- Selecione **Voltar**, continue um save Decades antigo e confirme que não sofreu alterações.
