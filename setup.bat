@echo off
echo ========================================
echo RailwayBot Setup
echo ========================================
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Quick Start:
echo   1. Navigate to your Railway project directory
echo   2. Run: python "%~dp0src\cli.py" watch
echo.
echo For more information, see README.md
echo.
pause
