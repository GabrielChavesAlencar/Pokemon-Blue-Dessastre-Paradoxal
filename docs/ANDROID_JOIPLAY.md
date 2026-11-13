# Android / JoiPlay — compatibilidade e diagnóstico

O relato de teste usa um Poco C85, JoiPlay e RPG Maker Plugin descritos como as versões mais recentes. Os números exatos dos aplicativos ainda não foram informados. A sequência foi **História → Traditional Starters → Double Starters**.

O diagnóstico enviado do aparelho confirmou `NoMethodError: undefined method clear_rect for Bitmap`, em `StartMouse.rb`, ao desenhar o seletor. O cabeçalho agora usa preenchimento transparente, disponível no RGSS/JoiPlay. O teste nativo remove `Bitmap.clear_rect`, abre o seletor real e executa os comandos originais de um e dois iniciais, verificando a quantidade entregue. Não se suprime o erro de evento nem se pula a escolha.

O ZIP antigo pode continuar disponível quando um teste impede a publicação, mesmo que o site e a main tenham sido atualizados. A página Downloads consulta a release pública e compara sua revisão com a última execução do workflow de distribuição. Ela avisa quando existe uma publicação pendente ou com falha.

## Testar a correção

Antes de substituir a pasta do Android, use **Onde fica meu save?** no menu inicial. Essa opção mostra o diretório usado pelo JoiPlay; copie `File A.rxdata` a `File H.rxdata`, `Auto 1–3.rxdata`, `Game.rxdata` e os `.bak` existentes. O arquivo `Data/blue-save-location.txt` registra o caminho, mas não guarda uma cópia da partida. Veja [encontros e menus Android](ENCONTROS_E_MENUS_ANDROID.md) para as instruções completas.

1. Baixe o pacote Android identificado na página Downloads.
2. Extraia por completo em uma pasta nova e adicione esse `Game.exe` como outra entrada do JoiPlay. Preserve a pasta anterior e os saves.
3. Confira a linha `Revision:` em `LEIA-ME-ANDROID.txt`; ela deve coincidir com a revisão publicada no site.
4. Teste o menu com toque e com os botões virtuais. Abra História → Traditional Starters → Double Starters, confirme as duas escolhas e confira os dois Pokémon na equipe. Confira também Single Starters em um jogo novo.
5. No Álbum de Treinadores, confira a abertura na rota/cidade atual e dentro de um prédio. Cidades sem treinadores continuam selecionadas com um aviso, sem criar recompensa.

O adaptador fornece `Input.mouse_in_window` somente no pacote mobile e quando o runtime não possui essa função. A superfície de toque conta como janela de entrada; não se usa o estado de um mouse físico. Implementações nativas existentes e o Windows são preservados.

Se um evento falhar, `Data/blue-android-event-error.txt` registra a exceção antes de o intérprete transformá-la em `EventScriptError`, incluindo mapa, evento, comando, script, backtrace e revisão. `Data/blue-android-runtime.txt` registra o carregamento do adaptador e as APIs disponíveis. Falhas ao gravar o diagnóstico não substituem o erro original.

Esses registros permitem investigar o caminho tradicional sem ignorar o evento nem conceder Pokémon arbitrários. O teste automatizado de compatibilidade não substitui a confirmação no Poco.

## Verificação da distribuição

O build exige a compilação nativa atual e compara o `Mobile.rb` compilado com seu fonte. O ZIP inclui `Data/blue-mobile-build.txt`, com a revisão e o hash do adaptador. A etapa de release verifica novamente essa revisão contra o commit do workflow antes de publicar. Saves, logs e caminhos do PC não entram no pacote.


## Correção de toque no piloto Kanto — teste em celular (13/11/2026)

A captura real enviada pelo usuário mostra este erro na tela inicial do JoiPlay:

~~~text
Script 'Input' line 28: NoMethodError occurred.
undefined method 'mouse_in_window' for Input:Module
~~~

**Causa identificada no empacotamento:** o piloto Kanto distribuía o plugin compilado `Mobile.rb`, mas não incluía o marcador `Data/blue-mobile.txt` exigido por `BlueMobile.enabled?`. Portanto a correção de toque já existente ficava desativada. Além disso, o script original `Input` pode chamar a função antes do carregamento dos plugins.

**Correção aplicada:** o pacote Kanto passa a incluir o marcador `Data/blue-mobile.txt` com o valor esperado, e a verificação do ZIP exige sua presença. Tanto Kanto quanto Decades também recebem uma proteção antecipada no início da entrada `Input` de `Data/Scripts.rxdata`, antes de qualquer chamada ao método. A proteção só é ativada no Android; o Windows não é alterado. Testes automatizados passam a bloquear pacotes sem esse ajuste.

**Para instalar:** se seu ZIP anterior apresentou este erro, preserve seus saves e instale o novo ZIP corrigido após a publicação da release. Caso o atualizador ofereça um patch compatível, ele pode aplicar a alteração com o JoiPlay fechado. Caso contrário, extraia o ZIP completo em uma nova pasta e adicione o novo `Game.exe` ao JoiPlay, sem sobrepor a instalação antiga.

O guia detalhado está na página `Downloads → Atualizações Android` do site e em [ANDROID_ATUALIZACOES_INCREMENTAIS.md](ANDROID_ATUALIZACOES_INCREMENTAIS.md).

**Validação:** o teste de empacotamento e a simulação Ruby confirmam a correção no código. Isso não substitui novo teste físico no celular com JoiPlay.


### Critério para liberar os novos pacotes corrigidos

A publicação deverá verificar **ambas** as condições: (1) o ZIP contém uma entrada `Input` já corrigida em `Data/Scripts.rxdata`; (2) o piloto Kanto inclui `Data/blue-mobile.txt` para ativar `Mobile.rb`. Nenhum teste que apenas confirma a presença do plugin substitui a verificação do marcador. O fluxo de release usa nomes separados para Kanto e Decades. A última verificação indispensável continua sendo abrir o ZIP novo no aparelho Android, tocar no menu e confirmar que o erro desapareceu.
