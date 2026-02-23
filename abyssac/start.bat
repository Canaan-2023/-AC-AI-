@echo off
chcp 65001 >nul 2>&1

cd /d "%~dp0"

echo ========================================
echo AbyssAC Startup Script
echo ========================================
echo.

echo Installing dependencies...
python -m pip install requests customtkinter -q
echo Done.
echo.

echo Initializing system...
python init_system.py
echo.

echo Select startup mode:
echo [1] Studio Mode (GUI)
echo [2] CLI Mode (Command Line)
echo [3] Exit
echo.

set /p choice="Please enter your choice (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo Starting Studio mode...
    python main.py
) else if "%choice%"=="2" (
    echo.
    echo Starting CLI mode...
    python main.py --cli
) else if "%choice%"=="3" (
    echo Exit
    exit /b 0
) else (
    echo Invalid choice, starting Studio mode...
    python main.py
)

pause
