@echo off
rem Doble clic para instalar, configurar y abrir el agente.
rem Para volver a ingresar las API keys: iniciar.bat --claves
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" goto iniciar
echo Creando el entorno de Python...
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m venv .venv) else (python -m venv .venv)
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo No se encontro Python 3.10 o superior.
    echo Instalalo desde https://www.python.org/downloads/ y marca "Add python.exe to PATH".
    pause
    exit /b 1
)
:iniciar
".venv\Scripts\python.exe" scripts\iniciar.py %*
if errorlevel 1 pause
