@echo off
title Macro Maker — Setup
echo.
echo  ========================================
echo   Macro Maker — First-time Setup
echo  ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo.
    echo  Download Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo  Installing required packages...
pip install customtkinter pyautogui pynput pillow --quiet --upgrade
if errorlevel 1 (
    echo.
    echo  [ERROR] pip install failed. Try running as Administrator.
    pause
    exit /b 1
)

echo.
echo  Done! Launching Macro Maker...
echo.
python "%~dp0main.py"
