@echo off
title Compilador de Serie de Taylor para Windows (.exe)
echo ========================================================
echo   Compilando Serie de Taylor a Ejecutable de Windows
echo ========================================================
echo.

echo 1. Instalando librerias necesarias y PyInstaller...
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

echo.
echo 2. Empaquetando la aplicacion en un unico archivo .exe...
pyinstaller --clean --name "SerieDeTaylor" --onefile --windowed main.py

echo.
echo ========================================================
echo   Compilacion completada con exito!
echo   Tu ejecutable se encuentra en la carpeta: dist\SerieDeTaylor.exe
echo ========================================================
echo.
pause
