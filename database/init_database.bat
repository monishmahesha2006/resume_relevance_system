@echo off
echo 🗄️ Resume Relevance System - Database Initialization
echo ============================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Run the database initialization script
python init_database.py

echo.
echo Press any key to exit...
pause >nul
