@echo off
echo ========================================
echo    EduMetric - Student Analytics
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Install requirements if needed
if not exist "venv\" (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run the application
echo Starting EduMetric Application...
echo.
echo Application will open at: http://localhost:5000
echo Login: admin / admin123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python run_edumetric.py

pause