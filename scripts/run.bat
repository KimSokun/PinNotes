@echo off
cd /d "%~dp0\.."
python app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
