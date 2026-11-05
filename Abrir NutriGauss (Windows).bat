@echo off
rem Doble clic en Windows: arranca el servidor de NutriGauss y abre el navegador.
cd /d "%~dp0"
python servidor.py
if errorlevel 1 (
  echo.
  echo No se pudo iniciar. Verifica que Python 3 este instalado: https://www.python.org/downloads/
  pause
)
