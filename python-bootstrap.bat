@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo [INFO] Setting up Python virtual environment for web novel evaluation...

:: --- Check if Python is installed ---
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [X] Python is not installed. Please install Python first.
    echo     Download from https://www.python.org/downloads/windows/
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python found: %PYVER%

:: --- Change to project directory ---
cd /d "%~dp0py-eval-tool"
if %ERRORLEVEL% neq 0 (
    echo [X] Failed to change directory to py-eval-tool
    exit /b 1
)

:: --- Create venv if not exists ---
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [X] Failed to create virtual environment
        exit /b 1
    )
    echo [OK] Virtual environment created successfully
) else (
    echo [OK] Virtual environment already exists
)

:: --- Activate virtual environment ---
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: --- Upgrade pip (optional) ---
:: echo [INFO] Upgrading pip...
:: python -m pip install --upgrade pip

:: --- Install dependencies ---
if exist requirements.txt (
    echo [INFO] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [X] Failed to install some dependencies
        echo     You may need to install system dependencies manually.
        exit /b 1
    )
    echo [OK] Dependencies installed successfully
) else (
    echo [WARN] No requirements.txt found, skipping dependency installation
)

echo.
echo [DONE] Setup complete!
echo.

ENDLOCAL
pause
