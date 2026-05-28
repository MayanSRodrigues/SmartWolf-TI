@echo off
title SmartWolf TI
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo  ========================================
echo   SmartWolf TI
echo   UniFECAF e ColegioSER
echo  ========================================
echo.
echo  Acesso local:   http://127.0.0.1:5000
echo  Acesso da rede: http://10.0.0.11:5000
echo.
echo  Pressione CTRL+C para encerrar
echo.
python run.py prod
pause