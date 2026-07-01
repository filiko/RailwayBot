@echo off
REM Quick launcher for RailwayBot
REM Usage: railwaybot.bat [watch|check|config|test]
REM
REM Note: After installing with "pip install -e .", you can use the
REM       "railwaybot" command directly instead of this batch file.

set SCRIPT_DIR=%~dp0

if "%1"=="" (
    echo Usage: railwaybot.bat [watch^|check^|config^|test]
    echo.
    echo Commands:
    echo   watch   - Start monitoring Railway deployments
    echo   check   - One-shot check for errors
    echo   config  - Show current configuration
    echo   test    - Test Railway CLI connection
    echo.
    echo Tip: Install with "pip install -e ." to use "railwaybot" command directly
    exit /b 1
)

python -m railwaybot.cli %*
