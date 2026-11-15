# Hoenn na build principal de Pokémon Blue / Decades

**Data:** 15/11/2026  
**Código:** integração transacional preparada na main; testes automatizados e regressões do código aprovados.  
**Instalação/jogabilidade nativa:** importação do ZIP local e aceite Windows/Android ainda pendentes. Não equivale a 12/12 jogável.

## Objetivo e proteções

Hoenn passa a ter um caminho de integração no **mesmo Game.exe, diretório game/, perfil de save e núcleo de batalha** de Decades/Kanto. Não se deve copiar a cópia isolada de Hoenn por cima do jogo principal: ela inclui inicialização, saves e MapIDs próprios.

O novo instalador usa os **199 mapas de Hoenn** do recorte já preparado contra a revisão fixa da fonte c59233bdbaac4fbeca6aa01c7f05be628da2a92. A contagem representa o recorte da ferramenta de piloto, não certificação de todos os eventos canônicos de Emerald.

Arquivos novos e atualizados:

- **scripts/regions/install_hoenn.py:** prepara os 199 MapIDs a partir dos IDs livres da instalação atual, mantém PBS de Decades/Kanto, faz backup, instala e reverte tudo se houver erro. Nunca copia Game.exe, System.rxdata, Scripts.rxdata, Game.ini, mkxp.json, Hoenn pilot.json ou saves.
- **scripts/regions/auto_integrate_hoenn.py:** só tenta a instalação caso encontre o ZIP privado original localmente. Se não houver fonte, falhar integridade ou faltar arquivo, registra o problema sem bloquear Decades/Kanto e sem declarar Hoenn instalada.
- **scripts/install_game.py:** executa a verificação opcional de Hoenn após Kanto e solicita recompilação PBS quando há novo conteúdo.
- **scripts/battle_polish/RegionStart.rb:** reconhece a seleção **Hoenn** em Novo Jogo apenas depois da instalação auditada. O início acontece na casa do jogador em Littleroot.
- **scripts/battle_polish/TitleKanto.rb:** exibe Hoenn no Novo Jogo da build principal quando está instalada; mantém Testar Hoenn separado caso contrário.
- **scripts/battle_polish/RegionTravel.rb:** adiciona Littleroot e o agente físico de viagem ao mesmo sistema que usa Pallet e Cherryhill. A chegada regional usa um terreno passável auditado, e não o quarto.
- **tests/test_hoenn_main_integration.py**, **tests/hoenn_main_gate_runtime.rb** e **.github/workflows/hoenn-main-integration.yml:** verificam manifestos, MapIDs, colisões, código Ruby/Python e regressões de Decades/Kanto/Johto.

Os recursos da fonte são instalados exclusivamente na máquina local e **não enviados ao GitHub**. Direitos de redistribuição por asset permanecem pendentes: não distribuir o ZIP ou derivados publicamente sem conferir as permissões.

## Instalação no Windows

1. Atualize o clone da main e feche o Game.exe. Guarde também uma cópia dos seus saves antes de qualquer importação de conteúdo.
2. Coloque o arquivo original **The Pokémon World Project - Hoenn.zip** na raiz do projeto, ao lado de TESTAR_HOENN.bat. Não copie RXDATA de origem diretamente para game/Data.
3. Certifique-se de que Kanto já está instalado em game/. Execute o **Blue-Story.exe**. O instalador principal preparará Blue, validará Kanto, identificará o ZIP de Hoenn e montará o overlay sobre os MapIDs livres do jogo principal.
4. Se preferir conferir manualmente com Python 3.11+, execute primeiro a auditoria e depois a instalação:

       py -3 scripts/regions/install_hoenn.py
       py -3 scripts/regions/install_hoenn.py --apply
       py -3 scripts/regions/install_hoenn.py --verify-installed

5. Depois, abra o instalador/launcher principal para compilar os novos PBS e plugins. Se o jogo compilar e encerrar, abra novamente. O perfil de save do Decades é mantido.
6. Em **Novo Jogo**, escolha Hoenn para iniciar na casa de Littleroot; ou use um save existente de Decades/Kanto e fale com o agente de transporte regional na cidade inicial para visitar Hoenn. Se os arquivos não passaram na validação, o menu não habilita a versão compartilhada.
7. A opção **Testar Hoenn** continua abrindo o piloto isolado, com seus próprios saves; não confunda essa cópia com a build principal.

O inventário público fixado pode precisar ser recuperado na primeira execução; os dados privados ficam em .blue-work/hoenn-source/. O status real fica em **.blue-work/hoenn-main-install-status.json** e os detalhes em **.blue-work/hoenn-main-install.log**. O backup fica em **.blue-backups/hoenn-<data>/**.

Se o integrador detectar arquivos parciais/modificados, ele bloqueia a importação; não apague marcadores nem force novos MapIDs, pois isso pode invalidar saves regionais existentes.

## Testes obrigatórios no Game.exe (pendentes)

- Confirmar a compilação e abertura dos 199 mapas no jogo principal.
- Novo Jogo → Hoenn → Littleroot → relógio/mãe → Birch → inicial → Rota 101 → Oldale → salvar/recarregar.
- Visitar Hoenn a partir de Decades/Kanto e voltar, preservando party, Box, itens-chave, HMs, insígnias e progressão, sem reexecutar os eventos de início.
- Perca uma batalha em Hoenn depois de visitar um Centro Pokémon de Kanto/Decades e confirme o respawn regional em Oldale ou no último Centro de Hoenn.
- Validar os ginásios, Surf/Dive/Waterfall, eventos Aqua/Magma, clima, Liga/Wallace, Hall da Fama, música, sprites e traduções.
- Carregar saves antigos de Decades/Kanto e verificar que as cópias QA continuam independentes. Testar também no Android/JoiPlay.

**Status de QA:** o GitHub Actions valida código e regressões em ambientes simulados. A execução nativa e a aceitação das 12 fases Hoenn não foram confirmadas. Para lacunas da campanha, consultar HOENN_PENDENCIAS_IMPLEMENTACAO.md.
 

## Correção da opção "Hoenn (em preparação)" — 15/11/2026

**Sintoma real:** no Agente de Transporte Regional, Decades/Kanto disponíveis e Hoenn marcada `em preparação` mesmo depois de atualizar o código. A lista só ativa Hoenn quando a instalação privada dos mapas está presente em `game/` e passou nas verificações. Atualizar apenas a main não instala RXDATA/PNG/OGG de origem que não são distribuídos no GitHub.

**Falha identificada:** o integrador automático anterior verificava exclusivamente `The Pokémon World Project - Hoenn.zip` na raiz e ignorava a fonte já extraída e auditada por `TESTAR_HOENN.bat`. Além disso, o NPC não mostrava a razão do bloqueio.

**Ajustes aplicados:**
- `install_hoenn.py`: reutiliza a fonte em `.blue-work/hoenn-source/<prefixo SHA-256>` somente após conferir a árvore Git fixada, os hashes dos mapas, gráficos e áudios e os 199 MapIDs. Não utiliza mapas inventados, não importa executável do doador e não usa a cópia `Hoenn pilot.json` como prova da instalação principal.
- `auto_integrate_hoenn.py`: tenta a importação quando há o ZIP ou uma fonte local previamente preparada. Grava o status detalhado em `.blue-work/hoenn-main-install-status.json` e um status simples em `game/Data/blue-hoenn-install-status.txt` para os diálogos dentro do jogo.
- `RegionTravel.rb`: ao escolher Hoenn indisponível, explica se falta a fonte, se a importação foi bloqueada ou se há uma instalação parcial. Não libera a viagem sem mapas.
- `INTEGRAR_HOENN_DECADES.bat`: instalador manual para o Windows com verificação do manifesto, backups e solicitação de recompilação dos PBS/plugins.

### Como resolver no Windows

1. Feche o jogo e atualize a `main`. Faça backup dos seus saves.
2. Se você já executou `TESTAR_HOENN.bat` **neste mesmo clone**, pode existir uma cópia de fonte auditada em `.blue-work/hoenn-source/`. Não é necessário repetir a extração caso todos os arquivos permaneçam presentes e os hashes sejam válidos.
3. Se não houver fonte local, coloque o ZIP original `The Pokémon World Project - Hoenn.zip` **na raiz deste clone** (mesma pasta do novo BAT). Alternativamente, **arraste o ZIP para cima do arquivo `INTEGRAR_HOENN_DECADES.bat`**, para fornecer seu caminho exato sem precisar movê-lo.
4. Execute `INTEGRAR_HOENN_DECADES.bat` com o jogo fechado. Quando ele informar `[OK]`, a montagem, verificação e solicitação de recompilação estão concluídas.
5. Abra o Game.exe **da pasta principal game/** novamente (se compilar e fechar, abra de novo) e converse com o Agente Regional. Hoenn deverá mostrar `viajar` em vez de `em preparação`.
6. Se o BAT mostrar `[BLOQUEADO]`, **não edite os marcadores manualmente**. Copie a mensagem de erro da janela e, quando houver, envie os arquivos `.blue-work/hoenn-main-install-status.json` e `.blue-work/hoenn-main-install.log`. O menu continuará bloqueando o transporte até a instalação ser válida.

### Verificação direta

Com Python instalado e o terminal na raiz do projeto:

```powershell
py -3 scripts/regions/install_hoenn.py --verify-installed
```

O comando deve informar `"maps": 199`, `"shared_save": true` e `"status": "integrated_files_ready_for_native_QA"`. Se retornar `HOENN BLOQUEADA`, o problema **é local e está nos arquivos da instalação**; a presença do nome no menu não confirma um mapa jogável.

**O que continua pendente:** teste real de viagem, save, retorno, eventos e batalha dentro do Game.exe Windows/JoiPlay. CI não acessa os arquivos privados do seu computador; teste sintético bem-sucedido não deve ser apresentado como instalação concluída.
