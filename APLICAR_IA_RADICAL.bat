@echo off
setlocal
cd /d "%~dp0"
python scripts\radical_ai\install.py --apply
if errorlevel 1 (
  pause
  exit /b 1
)
echo IA instalada. Abra TESTAR_BATALHA.bat para compilar e testar.
pause
