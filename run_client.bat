@echo off
REM -----------------------------
REM Inicia o cliente de qualquer lugar
REM -----------------------------
set ROOT=%~dp0
cd /d "%ROOT%"
python -m client.multiplayer
pause