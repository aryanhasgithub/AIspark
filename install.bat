@echo off
setlocal enabledelayedexpansion

:: Enhanced Voice Assistant Installation Script
:: This script sets up the voice assistant on your Windows system

echo ========================================
echo   Enhanced Voice Assistant Setup
echo ========================================
echo.

:: Check if Python is available
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% found
echo.

:: Create virtual environment
echo [INFO] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)
echo.

:: Activate virtual environment and upgrade pip
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
echo [SUCCESS] Virtual environment activated
echo.

:: Install Python dependencies
echo [INFO] Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [SUCCESS] Python dependencies installed
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
echo.

:: Setup environment file
echo [INFO] Setting up environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo [SUCCESS] Created .env file from template
        echo [WARNING] Please edit .env file with your API keys before running!
    ) else (
        echo [ERROR] .env.example not found
    )
) else (
    echo [WARNING] .env file already exists
)
echo.

:: Create assets directory
echo [INFO] Setting up assets...
if not exist "assets" mkdir assets
echo [SUCCESS] Assets directory ready
echo.

:: Installation complete
echo ========================================
echo [SUCCESS] Installation completed! 🎉
echo ========================================
echo.
echo Next steps:
echo 1. Edit the .env file with your API keys:
echo    notepad .env
echo.
echo 2. Activate the virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 3. Run wake.py
echo.
echo 4. Run the assistant:
echo    python main.py
echo.
echo [WARNING] Don't forget to configure your API keys in .env!
echo.
pause
