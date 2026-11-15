@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Pokemon Blue - Integrar Kanto no jogo principal

echo.
echo ===== KANTO DENTRO DO DECADES =====
echo [INFO] Instalacao opcional dos 142 mapas catalogados do piloto atual.
echo [INFO] Usa o motor, a progressao regional e os saves do jogo principal.
echo [INFO] Feche o Game.exe e preserve seus arquivos locais.
echo [INFO] Backups automaticos em .blue-backups\kanto-...
echo.

if not exist "game\Game.exe" (
  echo [ERRO] Instale a base com INSTALAR_JOGO.bat antes de integrar Kanto.
  goto :error
)
if exist "game\Data\blue-kanto-start.txt" goto :verify
if not exist ".blue-work\frlg-source\Essentials FRLG\Data\MapInfos.rxdata" (
  echo [ERRO] Fonte editavel FRLG 1.1 nao encontrada.
  echo [DICA] Leia docs\KANTO_ESCOLHA_REGIAO.md; a fonte nao vem no GitHub.
  goto :error
)
call :find_python
if errorlevel 1 goto :error

%PY% -X utf8 "scripts\regions\install_kanto.py"
if errorlevel 1 goto :error
choice /C SN /N /M "Integrar Kanto no Decades principal? [S/N] "
if errorlevel 2 goto :cancel
%PY% -X utf8 "scripts\regions\install_kanto.py" --apply
if errorlevel 1 goto :error
goto :verify

:verify
call :find_python
if errorlevel 1 goto :error
%PY% -X utf8 "scripts\regions\install_kanto.py" --verify-installed
if errorlevel 1 (
  echo [AVISO] Instalacao antiga ou incompleta detectada.
  echo [SEGURANCA] Nao foram apagados mapas ou saves e nenhuma migracao foi aplicada.
  echo [DICA] Preserve a copia e veja docs\KANTO_INTEGRACAO_DECADES.md.
  goto :error
)
echo.
echo [OK] Arquivos atuais de Kanto encontrados dentro do jogo principal.
echo [INFO] Agora execute ABRIR_JOGO.bat para atualizar os plugins e compilar PBS.
echo [AVISO] A validacao jogavel ainda depende do Game.exe no seu Windows.
pause
exit /b 0

:find_python
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
  set "PY=py -3"
  exit /b 0
)
where python >nul 2>&1
if not errorlevel 1 (
  set "PY=python"
  exit /b 0
)
echo [ERRO] Python 3.10+ nao encontrado.
exit /b 1

:cancel
echo [INFO] Instalacao cancelada. Nenhum mapa foi importado.
pause
exit /b 0

:error
echo [PENDENTE] Integracao nao confirmada. Nao tente copiar RXDATA manualmente.
pause
exit /b 1
