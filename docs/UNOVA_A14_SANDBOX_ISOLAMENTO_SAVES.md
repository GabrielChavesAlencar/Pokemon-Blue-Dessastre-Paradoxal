# Unova A14 — teste controlado e isolamento dos saves em Windows Sandbox

Data: 17/11/2026. Base: copia privada A13 com 32.010 arquivos e 1.580.437.187 bytes. Nao foram instalados mapas Unova.

## Limite da entrega

A14 NAO inicia Game.exe no Windows principal. Gera uma configuracao .wsb com script
de teste; o usuario abre o Windows Sandbox separadamente e precisa confirmar
com a tecla S dentro da maquina virtual para rodar o executavel descartavel.
O relatorio de preparacao nao comprova runtime, local real do save, nem jogo funcional.

## Configuracao da VM

- Rede, vGPU, clipboard, redirecionamentos de impressora, audio e video desabilitados.
- Copia A13 do jogo e arquivos de inicializacao mapeados SOMENTE LEITURA.
- Uma nova pasta de relatarios exclusiva e o UNICO compartilhamento gravavel entre VM e host.
- Script CMD no Sandbox faz robocopy da copia QA montada read-only para
  C:\UNOVA_A14_TEST, dentro do disco privado descartavel da maquina virtual.
- O script pergunta se deve executar Game.exe. Nunca usa jogo/saves do host.
- Ao fechar o processo, escreve A14_SANDBOX_RUNTIME.txt no diretorio exclusivo
  de relatorios, com codigo de saida e nomes de arquivos em AppData da VM.
- Windows Sandbox exige sistema compativel e recurso habilitado.
  Ausencia do recurso BLOQUEIA teste nativo, sem execucao direta como alternativa.

Referencia oficial Microsoft Learn:
https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file

## O que e validado antes de gerar a configuracao

1. Caminho da copia corresponde a pasta privada A13 em LOCALAPPDATA.
2. Manifesto A13 valido, sem save real herdado nem permissao de jogabilidade.
3. SHA-256 de Game.exe, MapInfos, Map001, Scripts e System comparados com A13.
4. mkxp.json e Game.ini correspondem ao namespace QA unico criado pela A13.
5. Pastas e arquivos comuns de saves ausentes na copia.
6. Configuracao WSB e launcher criados de forma idempotente, sem sobrescrever
   arquivos ja existentes que tenham sido modificados.
7. Nao instala Unova, nao reserva MapIDs, nao autoriza Windows/Android jogavel.

## Como executar (sem PowerShell)

1. Baixe e extraia RUN_UNOVA_MAPIDS_A14.zip. Execute RUN_UNOVA_MAPIDS.bat.
   Python 3.11 ou superior e necessario.
2. O relatorio LEIA_AQUI_UNOVA_MAPIDS.txt exibira o local de
   ABRIR_A14_WINDOWS_SANDBOX.wsb e de a14-sandbox-preflight-HASH.json.
3. Se Windows Sandbox existir e estiver habilitado, abra o arquivo .wsb
   com dois cliques, em vez de abrir Game.exe diretamente da copia A13.
4. Dentro da VM, o CMD prepara uma copia descartavel e pergunta N/S.
   Somente S inicia Game.exe na VM. N deixa runtime nao executado.
5. No teste, use apenas saves novos descartaveis. Ao sair do Game.exe,
   o script produz A14_SANDBOX_RUNTIME.txt no diretorio exclusivo de relatorios.
6. Envie o TXT A04-A14, JSON de A14 e log runtime da VM, NAO o Game.exe,
   diretoria de jogo ou saves.

Se nao tiver Windows Sandbox, o teste de execucao permanece pendente;
nao oferecer execucao no host como atalho.

**Barras:** A = 0/8, Unova jogavel = 0/32. A configuracao nao comprova
a origem dos MapIDs, os destinos de transferencias computadas ou saves reais.
