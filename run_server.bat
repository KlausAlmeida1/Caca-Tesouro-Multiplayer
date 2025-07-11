@echo off
REM
REM
REM
set ROOT=%~dp0
cd /d "%ROOT%"
start "Servidor Tesouro" /min python -m server.main
exit
