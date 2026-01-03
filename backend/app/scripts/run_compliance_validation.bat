@echo off
REM Legal AI System Compliance Validation Runner
REM This script runs the comprehensive compliance validation checks

echo ========================================
echo Legal AI System Compliance Validation
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Change to the backend directory
cd /d %~dp0..

REM Set PYTHONPATH to include the app directory
set PYTHONPATH=%cd%;%PYTHONPATH%

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: No virtual environment found, using system Python
)

REM Install required dependencies if needed
echo Checking dependencies...
python -c "import sqlite3, json, re, logging, asyncio" 2>nul
if %errorlevel% neq 0 (
    echo Installing required Python packages...
    pip install sqlite3 asyncio
)

echo.
echo Starting compliance validation...
echo This may take several minutes to complete.
echo.

REM Run the compliance validation script
python scripts\compliance_validation.py

REM Capture exit code
set VALIDATION_RESULT=%errorlevel%

echo.
echo ========================================
if %VALIDATION_RESULT% equ 0 (
    echo ✅ COMPLIANCE VALIDATION COMPLETED SUCCESSFULLY
    echo All systems are compliant with legal requirements
) else if %VALIDATION_RESULT% equ 1 (
    echo ❌ COMPLIANCE VALIDATION FAILED
    echo Critical compliance issues detected
    echo Please review the report and address failures immediately
) else (
    echo ⚠️ COMPLIANCE VALIDATION ERROR
    echo An error occurred during validation
    echo Please check the logs and try again
)
echo ========================================

REM Keep window open to view results
pause

exit /b %VALIDATION_RESULT%