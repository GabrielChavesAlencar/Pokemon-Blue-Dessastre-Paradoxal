@echo off
setlocal
cd /d "%~dp0"
if not exist "scripts\regions\audit_sinnoh_playable_j11.py" (
 echo SINNOH_J11_BLOQUEADO: auditor nao encontrado.
 exit /b 2
)
echo J11 - auditar cinco originais e salvar somente plano read-only.
echo Nao instala mapas; R07 R08 R09 continuam pendentes.
py -3 "scripts\regions\audit_sinnoh_playable_j11.py" --write-plan
if errorlevel 1 (
 echo Falha segura: nenhum arquivo de jogo ou save foi alterado.
 exit /b 2
)
echo Recibo: .blue-work\sinnoh-j11-readonly-plan.json
exit /b 0
