# Android / JoiPlay — compatibilidade e diagnóstico

O relato de teste usa um Poco C85, JoiPlay e RPG Maker Plugin descritos como as versões mais recentes. Os números exatos dos aplicativos ainda não foram informados. A seleção escolhida foi **Traditional Starters**.

O ZIP antigo pode continuar disponível quando um teste impede a publicação, mesmo que o site e a main tenham sido atualizados. A página Downloads consulta a release pública e compara sua revisão com a última execução do workflow de distribuição. Ela avisa quando existe uma publicação pendente ou com falha.

## Testar a correção

1. Baixe o pacote Android identificado na página Downloads.
2. Extraia por completo em uma pasta nova e adicione esse `Game.exe` como outra entrada do JoiPlay. Preserve a pasta anterior e os saves.
3. Confira a linha `Revision:` em `LEIA-ME-ANDROID.txt`; ela deve coincidir com a revisão publicada no site.
4. Teste o menu com toque e com os botões virtuais. Abra História, escolha Traditional Starters e confira a seleção do inicial.

O adaptador fornece `Input.mouse_in_window` somente no pacote mobile e quando o runtime não possui essa função. A superfície de toque conta como janela de entrada; não se usa o estado de um mouse físico. Implementações nativas existentes e o Windows são preservados.

Se um evento falhar, `Data/blue-android-event-error.txt` registra a exceção antes de o intérprete transformá-la em `EventScriptError`, incluindo mapa, evento, comando, script, backtrace e revisão. `Data/blue-android-runtime.txt` registra o carregamento do adaptador e as APIs disponíveis. Falhas ao gravar o diagnóstico não substituem o erro original.

Esses registros permitem investigar o caminho tradicional sem ignorar o evento nem conceder Pokémon arbitrários. O teste automatizado de compatibilidade não substitui a confirmação no Poco.

## Verificação da distribuição

O build exige a compilação nativa atual e compara o `Mobile.rb` compilado com seu fonte. O ZIP inclui `Data/blue-mobile-build.txt`, com a revisão e o hash do adaptador. A etapa de release verifica novamente essa revisão contra o commit do workflow antes de publicar. Saves, logs e caminhos do PC não entram no pacote.
