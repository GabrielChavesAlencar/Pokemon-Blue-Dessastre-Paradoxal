@echo off
setlocal
cd /d "%~dp0"
if not exist "scripts\regions\prepare_sinnoh_nine_original_j11c.py" (
 echo J11-C: auditor nao encontrado.
 exit /b 2
)
echo SINNOH J11-C - auditoria somente em memoria. Nao instala mapas.
py -3 "scripts\regions\prepare_sinnoh_nine_original_j11c.py"
if errorlevel 1 (
 echo Operacao bloqueada sem modificar jogo ou saves.
 exit /b 2
)
echo R07 R08 R09 pendentes. 0/9 instalados, 0/44 QA nativa.
exit /b 0
