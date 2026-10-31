# Laboratório de Batalha local

Na pasta principal do projeto, abra **TESTAR_BATALHA.bat**. É uma sessão limitada do jogo real: batalha individual 1 x 1, sem história ou exploração, usando a engine, os sprites, as animações e os dados compilados da base instalada em `game/`.

## Usar

- O confronto inicial é Miraidon x Koraidon no nível 50.
- Selecione **Escolher meu Pokemon** ou **Escolher adversario** para abrir o catálogo de espécies e formas compiladas. Formas são identificadas pelo número na lista. A tecla de ação alterna a ordenação da lista.
- Ajuste o nível de ambos entre 1 e 100. Ao mudar o nível, os golpes voltam aos quatro últimos da lista de aprendizado disponível naquele nível.
- **Editar meus golpes** e **Editar golpes do adversario** permitem testar até quatro golpes. A lista é livre para experimentos e não valida a legalidade competitiva do moveset.
- Use **Iniciar batalha 1 x 1**. Os menus de batalha e os controles são os próprios do jogo. Ao terminar ou fugir, você volta ao laboratório; os Pokémon são curados entre testes.
- **Teste rapido** prepara Pikachu x Eevee no nível 10.
- Escolha **Sair do laboratorio** para fechar. Para jogar a campanha normalmente, abra **JOGAR.bat**.

A sessão usa IVs 31, EVs 0 e natureza neutra. Não concede experiência ou dinheiro e bloqueia Poké Balls. A interface da batalha mantém o idioma da base do fangame.

## Testar Pokémon e golpes que você criou

Cadastre/edite a espécie no Blue Studio, salve os PBS e abra o laboratório. Ele inicia em modo debug para permitir a compilação necessária. Aguarde a primeira carga e eventuais mensagens do compilador. Uma espécie só entra no catálogo quando a compilação termina com sucesso; o editor salvar o PBS não prova que ela foi compilada. Os sprites e métricas precisam estar instalados na base local. Não é necessário criar uma segunda cópia do jogo.

O laboratório não cria automaticamente Fakémon ou sprites. Ele permite testar as espécies e formas registradas, incluindo as que você cadastrar no editor.

## Isolamento e instalação

O lançador copia apenas o plugin original deste projeto para `game/Plugins/ZZZZ Blue Battle Lab/`. Um pequeno bootstrap optativo é acrescentado ao script `Main` da engine, com backup em `.blue-backups/battle-lab/`. Os outros scripts, mapas e eventos são preservados. O laboratório inicializa um jogador temporário em memória e bloqueia as rotinas de leitura e gravação de save, incluindo autosave; não abre a campanha.

Uma solicitação de abertura vale por 120 segundos e é consumida uma vez. A abertura normal continua sendo a campanha. O atalho precisa ser executado novamente para outra sessão do laboratório. Os arquivos do jogo e os backups continuam ignorados no Git.

Diagnóstico: `game/Data/blue-battle-lab.log`. O teste automatizado usa a mesma cena de batalha, com a IA comandando os dois lados e as confirmações de texto desativadas. Pode ser iniciado com `python scripts/battle_lab/launch.py --smoke-test`. No ambiente isolado de automação, o terminal pode não conseguir abrir uma janela visível; o atalho foi feito para ser usado na sua sessão normal do Windows.

## Portal local

Abra **ABRIR_SITE.bat**, aguarde a mensagem do servidor e visite **http://127.0.0.1:4173**. É necessário Node.js 24. Mantenha a janela aberta enquanto usar o portal; Ctrl+C encerra o servidor. A batalha real abre em uma janela separada pelo atalho do laboratório.
