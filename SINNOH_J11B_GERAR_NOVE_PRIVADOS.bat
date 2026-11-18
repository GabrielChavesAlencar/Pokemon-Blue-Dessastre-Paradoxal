@echo off
setlocal
cd /d "%~dp0"
if not exist "scripts\regions\generate_sinnoh_four_exteriors_j11b.py" (
  echo J11-B: execute somente a partir da raiz do codigo.
  exit /b 2
)
echo Sinnoh J11-B - quatro novos exteriores e nove mapas privados.
echo Nao instala, nao altera MapInfos, save, Game.exe ou Android.
py -3 "scripts\regions\generate_sinnoh_four_exteriors_j11b.py" --build
if errorlevel 1 (
 echo Erro: geracao bloqueada sem sobrescrever mapas existentes.
 exit /b 2
)
echo Arquivos: .blue-work\sinnoh-j11b-nine-original-designs
echo REVISAO R07/R08 E TILESETS NATIVOS NECESSARIA ANTES DE JOGAR.
exit /b 0
