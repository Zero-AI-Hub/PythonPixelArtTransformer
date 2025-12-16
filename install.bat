@echo off
REM ============================================
REM Pixel Art Transformer - Windows Installer
REM ============================================

echo.
echo ========================================
echo  Pixel Art Transformer - Instalador
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado.
    echo.
    echo Descarga Python desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

REM Check tkinter
echo Verificando tkinter...
python -c "import tkinter" 2>nul
if errorlevel 1 (
    echo [ERROR] tkinter no disponible.
    echo.
    echo tkinter deberia venir incluido con Python en Windows.
    echo Reinstala Python y asegurate de incluir tcl/tk.
    echo.
    pause
    exit /b 1
)
echo [OK] tkinter disponible
echo.

REM Install dependencies
echo Instalando dependencias...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Error instalando dependencias
    pause
    exit /b 1
)

echo.
echo ========================================
echo  [OK] Instalacion completada!
echo ========================================
echo.
echo Para ejecutar la aplicacion:
echo   python pixel_art_gui.py
echo.
echo O ejecuta: run.bat
echo.

set /p choice="Ejecutar ahora? (s/n): "
if /i "%choice%"=="s" (
    python pixel_art_gui.py
)
