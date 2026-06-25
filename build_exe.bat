@echo off
title Macro Maker — Build .exe
echo.
echo  ========================================
echo   Macro Maker — Build Standalone .exe
echo  ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo  Installing build dependencies...
pip install pyinstaller customtkinter pyautogui pynput pillow --quiet --upgrade

echo.
echo  Building .exe (this takes ~30 seconds)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "MacroMaker" ^
    --icon NONE ^
    --add-data "auto_clicker.py;." ^
    --add-data "macro_runner.py;." ^
    --add-data "hotkeys.py;." ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --collect-all customtkinter ^
    main.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. See output above.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   SUCCESS!
echo   Your .exe is at:  dist\MacroMaker.exe
echo  ========================================
echo.
echo  Share the file at dist\MacroMaker.exe with anyone.
echo  They do NOT need Python installed.
echo.
pause
