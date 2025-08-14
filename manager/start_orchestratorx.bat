@echo off
chcp 65001 >nul
title NextGen Hub - Advanced Process Manager

echo.
echo ========================================
echo    NextGen Hub - Advanced Process Manager
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

:: Check if required packages are installed
echo [INFO] Checking dependencies...
python -c "import fastapi, uvicorn, psutil, pydantic" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages...
    pip install -r backend/requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Create data directory if it doesn't exist
if not exist "data" mkdir data
if not exist "data\runtime" mkdir data\runtime

:: Check if projects.yaml exists, create example if not
if not exist "data\projects.yaml" (
    echo [INFO] Creating example projects configuration...
    copy "data\projects.example.yaml" "data\projects.yaml" >nul 2>&1
)

echo [INFO] Starting NextGen Hub Desktop Application...
echo [INFO] Web Dashboard will be available at: http://localhost:8000/dashboard
echo [INFO] API will be available at: http://localhost:8000/api/
echo.

:: Start the desktop application
python desktop_app.py

echo.
echo [INFO] NextGen Hub has been closed.
pause