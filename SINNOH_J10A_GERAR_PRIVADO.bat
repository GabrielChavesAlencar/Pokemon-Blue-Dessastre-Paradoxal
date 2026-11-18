@echo off
setlocal
cd /d "%~dp0"
if not exist "scripts\regions\generate_sinnoh_original_j10a.py" (
  echo J10-A bloqueada: execute no codigo do repositorio.
  exit /b 2
)
echo J10-A - gerar cinco mapas originais apenas na pasta .blue-work
echo Nao instala no jogo, nao altera saves, nao aprova R07/R08/R09.
py -3 "scripts\regions\generate_sinnoh_original_j10a.py" --build
if errorlevel 1 (
  echo Falha segura: verifique os erros acima; nenhum dado existente foi sobrescrito.
  exit /b 2
)
echo Arquivos criados em .blue-work\sinnoh-j10a-original
echo Abra previews\*.svg para revisar antes da J11.
exit /b 0
