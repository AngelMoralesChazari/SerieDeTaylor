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
echo 2. Empaquetando la aplicacion en modo portable de inicio instantaneo (--onedir)...
echo    (Este modo abre en 1 segundo sin descomprimir a la carpeta Temp)
pyinstaller --clean --noconfirm --name "SerieDeTaylor" --onedir --windowed main.py

echo.
echo ========================================================
echo   Compilacion completada con exito!
echo   Tu aplicacion se encuentra en la carpeta: dist\SerieDeTaylor\
echo   Ejecutable principal: dist\SerieDeTaylor\SerieDeTaylor.exe
echo ========================================================
echo.
pause
